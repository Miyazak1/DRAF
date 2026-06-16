from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from rpf.core.local_world import (
    AudienceSpec,
    EcologicalConditionSpec,
    LocalWorldSpec,
    LocalWorldState,
    LocationSpec,
    MemorySiteSpec,
    ResourceSpec,
    RouteSpec,
    RhythmSpec,
    normalized_pressure,
)
from rpf.core.models import TickContext, clamp


@dataclass
class LocalWorldUpdate:
    traces: list[dict[str, Any]] = field(default_factory=list)
    events: list[tuple[str, dict[str, Any], list[str]]] = field(default_factory=list)


class LocalWorldEngine:
    def __init__(self, spec: LocalWorldSpec | None) -> None:
        self.spec = spec
        self.state = LocalWorldState.from_spec(spec) if spec else None
        self._last_route_status: dict[str, str] = {}

    def advance(self, context: TickContext, causal_refs: list[str] | None = None) -> LocalWorldUpdate:
        if not self.spec or not self.state:
            return LocalWorldUpdate()
        causal_refs = causal_refs or []
        self.state.elapsed_seconds += max(0, int(context.simulated_time_delta_seconds))
        self.state.current_time_window = _time_window(self.state.elapsed_seconds)
        active_rhythms = self._active_rhythms()
        active_conditions = self._active_ecological_conditions()
        self.state.active_rhythms = [item.rhythm_id for item in active_rhythms]
        self.state.active_ecological_conditions = [item.condition_id for item in active_conditions]

        update = LocalWorldUpdate()
        update.traces.extend(self._rhythm_traces(context, active_rhythms, causal_refs))
        update.traces.extend(self._route_traces(context, active_conditions, causal_refs))
        update.traces.extend(self._location_traces(context, active_rhythms, active_conditions, causal_refs))
        update.traces.extend(self._audience_traces(context, active_rhythms, causal_refs))
        update.traces.extend(self._memory_site_traces(context, active_conditions, causal_refs))
        update.traces.extend(self._resource_traces(context, active_conditions, causal_refs))
        self.state.local_world_pressure = _mean(
            [
                *(item.pressure for item in self.state.location_states.values()),
                *(1.0 - item.accessibility for item in self.state.route_states.values()),
                *(item.exposure_level for item in self.state.audience_exposure_states.values()),
                *(item.salience for item in self.state.active_memory_sites.values()),
            ]
        )
        update.traces.append(
            {
                "tick": context.tick_index,
                "event_type": "LocalWorldUpdateEvent",
                "world_id": self.spec.id,
                "current_time_window": self.state.current_time_window,
                "active_rhythms": list(self.state.active_rhythms),
                "active_ecological_conditions": list(self.state.active_ecological_conditions),
                "local_world_pressure": self.state.local_world_pressure,
                "boundary_rules": self.spec.boundary_rules.model_dump(mode="json"),
                "caused_by_events": causal_refs,
            }
        )
        update.events = [
            (str(trace["event_type"]), {key: value for key, value in trace.items() if key not in {"tick", "event_type", "caused_by_events"}}, causal_refs)
            for trace in update.traces
            if trace.get("event_type") != "LocalWorldUpdateEvent"
        ]
        return update

    def _active_rhythms(self) -> list[RhythmSpec]:
        assert self.spec is not None
        window = self.state.current_time_window if self.state else "morning"
        return [item for item in self.spec.rhythms if item.time_window == window or item.time_window == "any"]

    def _active_ecological_conditions(self) -> list[EcologicalConditionSpec]:
        assert self.spec is not None
        window = self.state.current_time_window if self.state else "morning"
        active: list[EcologicalConditionSpec] = []
        for condition in self.spec.ecological_conditions:
            if condition.active_time_window in {None, "always", window}:
                active.append(condition)
            elif condition.condition_type == "nightfall" and window == "night":
                active.append(condition)
        return active

    def _rhythm_traces(self, context: TickContext, rhythms: list[RhythmSpec], causal_refs: list[str]) -> list[dict[str, Any]]:
        return [
            {
                "tick": context.tick_index,
                "event_type": "RhythmActivationEvent",
                "rhythm_id": rhythm.rhythm_id,
                "label": rhythm.label,
                "active_locations": list(rhythm.active_locations),
                "time_window": self.state.current_time_window if self.state else rhythm.time_window,
                "crowd_density_delta": normalized_pressure(rhythm.crowd_density_delta),
                "rumor_pressure_delta": normalized_pressure(rhythm.rumor_pressure_delta),
                "mobility_cost_delta": normalized_pressure(rhythm.mobility_cost_delta),
                "institutional_pressure_delta": normalized_pressure(rhythm.institutional_pressure_delta),
                "available_scene_types": list(rhythm.available_scene_types),
                "blocked_scene_types": list(rhythm.blocked_scene_types),
                "caused_by_events": causal_refs,
            }
            for rhythm in rhythms
        ]

    def _route_traces(
        self,
        context: TickContext,
        conditions: list[EcologicalConditionSpec],
        causal_refs: list[str],
    ) -> list[dict[str, Any]]:
        assert self.spec is not None and self.state is not None
        condition_ids = {item.condition_id for item in conditions}
        condition_types = {item.condition_type for item in conditions}
        traces: list[dict[str, Any]] = []
        for route in self.spec.routes:
            state = self.state.route_states[route.route_id]
            previous_status = state.access_status
            weather_blockers = [
                condition
                for condition in route.blocked_by_conditions
                if condition in condition_ids or condition in condition_types
            ]
            direct_conditions = [
                condition.condition_id
                for condition in conditions
                if route.route_id in condition.affected_routes
            ]
            weather_cost = max(
                [normalized_pressure(condition.mobility_delta) for condition in conditions if route.route_id in condition.affected_routes]
                or [0.0]
            )
            danger = normalized_pressure(route.danger_level)
            exposure = normalized_pressure(route.exposure_level)
            base_access = normalized_pressure(route.access_level, 1.0)
            accessibility = clamp(base_access - weather_cost - danger * 0.35 - exposure * 0.18)
            blockers = weather_blockers + direct_conditions
            if blockers:
                accessibility = min(accessibility, 0.12)
                status = "blocked"
            elif danger >= 0.65:
                status = "dangerous"
            elif exposure >= 0.65:
                status = "exposed"
            elif accessibility < 0.55:
                status = "costly"
            else:
                status = "open"
            state.accessibility = accessibility
            state.access_status = status  # type: ignore[assignment]
            state.exposure = exposure
            state.danger = danger
            state.blocking_conditions = blockers
            trace = {
                "tick": context.tick_index,
                "event_type": "RouteAccessEvent",
                "route_id": route.route_id,
                "access_before": previous_status,
                "access_after": status,
                "travel_time_before": route.travel_time_minutes,
                "travel_time_after": int(round(route.travel_time_minutes * (1.0 + (1.0 - accessibility)))),
                "blocking_condition": blockers[0] if blockers else None,
                "blocking_conditions": blockers,
                "affected_processes": self._route_affected_processes(route),
                "accessibility": accessibility,
                "exposure": exposure,
                "danger": danger,
                "caused_by_events": causal_refs,
            }
            traces.append(trace)
            self._last_route_status[route.route_id] = status
        return traces

    def _location_traces(
        self,
        context: TickContext,
        rhythms: list[RhythmSpec],
        conditions: list[EcologicalConditionSpec],
        causal_refs: list[str],
    ) -> list[dict[str, Any]]:
        assert self.spec is not None and self.state is not None
        active_locations = {location_id for rhythm in rhythms for location_id in rhythm.active_locations}
        condition_locations = {location_id for condition in conditions for location_id in condition.affected_locations}
        rhythm_pressure_by_location = {
            location_id: clamp(
                max(
                    normalized_pressure(rhythm.crowd_density_delta)
                    + normalized_pressure(rhythm.rumor_pressure_delta)
                    + normalized_pressure(rhythm.institutional_pressure_delta)
                    for rhythm in rhythms
                    if location_id in rhythm.active_locations
                )
                / 3.0
            )
            for location_id in active_locations
        }
        traces: list[dict[str, Any]] = []
        for location in self.spec.locations:
            state = self.state.location_states[location.location_id]
            previous = state.model_dump(mode="json")
            base_memory = normalized_pressure(location.memory_charge)
            rhythm_pressure = rhythm_pressure_by_location.get(location.location_id, 0.0)
            ecological_pressure = max(
                [normalized_pressure(condition.mobility_delta) + normalized_pressure(condition.visibility_delta) for condition in conditions if location.location_id in condition.affected_locations]
                or [0.0]
            )
            audience_pressure = normalized_pressure(location.public_visibility) * 0.35 + normalized_pressure(location.rumor_density) * 0.35
            access_relief = normalized_pressure(location.access_level, 1.0) * 0.16
            pressure = clamp(base_memory * 0.34 + rhythm_pressure * 0.24 + ecological_pressure * 0.18 + audience_pressure * 0.18 - access_relief)
            state.pressure = pressure
            state.crowd_density = clamp(normalized_pressure(location.crowd_density) + rhythm_pressure * 0.45)
            state.rumor_density = clamp(normalized_pressure(location.rumor_density) + rhythm_pressure * 0.5)
            state.surveillance_level = normalized_pressure(location.surveillance_level)
            state.memory_salience = clamp(max(state.memory_salience * 0.92, base_memory) + pressure * 0.08)
            if location.location_id in active_locations or location.location_id in condition_locations:
                state.last_scene_tick = context.tick_index if context.tick_type == "scene" else state.last_scene_tick
            trace = {
                "tick": context.tick_index,
                "event_type": "LocationStateEvent",
                "location_id": location.location_id,
                "previous_state": previous,
                "new_state": state.model_dump(mode="json"),
                "changed_fields": _changed_fields(previous, state.model_dump(mode="json")),
                "cause": {
                    "base_memory_charge": base_memory,
                    "active_rhythm_pressure": rhythm_pressure,
                    "ecological_pressure": ecological_pressure,
                    "audience_pressure": audience_pressure,
                    "access_relief": access_relief,
                },
                "affected_scene_types": list(location.allowed_scene_types or []),
                "affected_capacities": _capacities_for_location(location),
                "caused_by_events": causal_refs,
            }
            traces.append(trace)
        return traces

    def _audience_traces(self, context: TickContext, rhythms: list[RhythmSpec], causal_refs: list[str]) -> list[dict[str, Any]]:
        assert self.spec is not None and self.state is not None
        active_locations = {location_id for rhythm in rhythms for location_id in rhythm.active_locations}
        traces: list[dict[str, Any]] = []
        for audience in self.spec.audiences:
            state = self.state.audience_exposure_states[audience.audience_id]
            overlap = sorted(set(audience.usual_locations) & active_locations)
            location_visibility = max(
                [
                    normalized_pressure(location.public_visibility)
                    for location in self.spec.locations
                    if location.location_id in set(audience.usual_locations)
                ]
                or [0.0]
            )
            exposure_level = clamp(
                location_visibility * 0.4
                + normalized_pressure(audience.rumor_power) * 0.28
                + normalized_pressure(audience.sanction_power) * 0.2
                + (0.12 if overlap else 0.0)
            )
            exposure_state = _exposure_state(exposure_level)
            state.exposure_level = exposure_level
            state.exposure_state = exposure_state  # type: ignore[assignment]
            state.active_locations = overlap
            traces.append(
                {
                    "tick": context.tick_index,
                    "event_type": "AudienceExposureEvent",
                    "audience_id": audience.audience_id,
                    "location_id": overlap[0] if overlap else (audience.usual_locations[0] if audience.usual_locations else None),
                    "observed_or_possible": exposure_state,
                    "exposure_level": exposure_level,
                    "sanction_risk": normalized_pressure(audience.sanction_power),
                    "rumor_risk": normalized_pressure(audience.rumor_power),
                    "affected_processes": sorted(audience.relationship_to_processes.keys()),
                    "affected_topics": list(audience.affected_topics),
                    "caused_by_events": causal_refs,
                }
            )
        return traces

    def _memory_site_traces(
        self,
        context: TickContext,
        conditions: list[EcologicalConditionSpec],
        causal_refs: list[str],
    ) -> list[dict[str, Any]]:
        assert self.spec is not None and self.state is not None
        condition_locations = {location_id for condition in conditions for location_id in condition.affected_locations}
        traces: list[dict[str, Any]] = []
        for site in self.spec.memory_sites:
            runtime = self.state.active_memory_sites[site.site_id]
            base = normalized_pressure(site.salience)
            location_state = self.state.location_states.get(site.location_id)
            location_pressure = location_state.pressure if location_state else 0.0
            symbolic_trigger = 0.12 if site.location_id in condition_locations else 0.0
            salience = clamp(max(base, runtime.salience * 0.9) + location_pressure * 0.16 + symbolic_trigger - 0.025)
            runtime.salience = salience
            runtime.active = salience >= 0.5
            if runtime.active:
                traces.append(
                    {
                        "tick": context.tick_index,
                        "event_type": "MemorySiteActivationEvent",
                        "site_id": site.site_id,
                        "location_id": site.location_id,
                        "source_events": list(site.source_events),
                        "affected_processes": list(site.affected_processes),
                        "salience": salience,
                        "avoidance_pressure": normalized_pressure(site.avoidance_pressure),
                        "attraction_pressure": normalized_pressure(site.attraction_pressure),
                        "future_scene_biases": list(site.future_scene_biases),
                        "caused_by_events": causal_refs,
                    }
                )
        return traces

    def _resource_traces(
        self,
        context: TickContext,
        conditions: list[EcologicalConditionSpec],
        causal_refs: list[str],
    ) -> list[dict[str, Any]]:
        assert self.spec is not None and self.state is not None
        mobility_cost = max([normalized_pressure(condition.mobility_delta) for condition in conditions] or [0.0])
        traces: list[dict[str, Any]] = []
        for resource in self.spec.resources:
            runtime = self.state.resource_states[resource.resource_id]
            scarcity = normalized_pressure(resource.scarcity_level)
            runtime.scarcity_level = clamp(scarcity + mobility_cost * 0.12)
            runtime.availability = clamp(1.0 - runtime.scarcity_level + normalized_pressure(resource.replacement_access) * 0.12)
            traces.append(
                {
                    "tick": context.tick_index,
                    "event_type": "ResourceStateEvent",
                    "resource_id": resource.resource_id,
                    "availability": runtime.availability,
                    "scarcity_level": runtime.scarcity_level,
                    "linked_capacities": list(resource.linked_capacities),
                    "conflict_potential": normalized_pressure(resource.conflict_potential),
                    "caused_by_events": causal_refs,
                }
            )
        return traces

    def _route_affected_processes(self, route: RouteSpec) -> list[str]:
        assert self.spec is not None
        linked: set[str] = set()
        for location in self.spec.locations:
            if location.location_id in {route.from_location, route.to_location}:
                linked.update(location.linked_processes)
        return sorted(linked)


def _time_window(elapsed_seconds: int) -> str:
    minute_of_day = (6 * 60 + elapsed_seconds // 60) % (24 * 60)
    if 5 * 60 <= minute_of_day < 11 * 60:
        return "morning"
    if 11 * 60 <= minute_of_day < 15 * 60:
        return "midday"
    if 15 * 60 <= minute_of_day < 18 * 60:
        return "afternoon"
    if 18 * 60 <= minute_of_day < 22 * 60:
        return "evening"
    return "night"


def _mean(values: list[float]) -> float:
    if not values:
        return 0.0
    return clamp(sum(values) / len(values))


def _changed_fields(before: dict[str, Any], after: dict[str, Any]) -> list[str]:
    return sorted(key for key, value in after.items() if before.get(key) != value)


def _capacities_for_location(location: LocationSpec) -> list[str]:
    capacities = {"exit", "repair", "truth_disclosure"}
    if location.controlling_institution or location.location_type in {"police_archive", "institution", "hospital", "school"}:
        capacities.add("evidence_access")
    if normalized_pressure(location.public_visibility) >= 0.55:
        capacities.add("face_management")
    if normalized_pressure(location.memory_charge) >= 0.55:
        capacities.add("memory_integration")
    return sorted(capacities)


def _exposure_state(value: float) -> str:
    if value >= 0.86:
        return "observed"
    if value >= 0.66:
        return "likely"
    if value >= 0.32:
        return "possible"
    return "none"
