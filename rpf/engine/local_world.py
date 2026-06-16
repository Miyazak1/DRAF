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


@dataclass
class SceneLocalitySelection:
    scene_context: dict[str, Any] = field(default_factory=dict)
    location_trace: dict[str, Any] = field(default_factory=dict)
    route_trace: dict[str, Any] = field(default_factory=dict)
    audience_trace: dict[str, Any] = field(default_factory=dict)


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

    def select_scene_locality(
        self,
        context: TickContext,
        *,
        scene_type: str,
        evidence: dict[str, Any],
        causal_refs: list[str] | None = None,
    ) -> SceneLocalitySelection:
        if not self.spec or not self.state:
            return SceneLocalitySelection()
        causal_refs = causal_refs or []
        candidate_scores = [self._location_candidate(context, location, scene_type, evidence) for location in self.spec.locations]
        candidate_scores = sorted(candidate_scores, key=lambda item: item["score"], reverse=True)
        selected = candidate_scores[0]
        route = self._select_route_for_location(selected["location_id"], evidence)
        audiences = self._audiences_for_location(selected["location_id"])
        memory_sites = self._memory_sites_for_location(selected["location_id"])
        constraints = self._constraints_for_location(selected["location_id"], route)
        rejected = [
            {
                "location_id": item["location_id"],
                "score": item["score"],
                "reasons": item["rejected_reasons"],
            }
            for item in candidate_scores[1:6]
        ]
        scene_context = {
            "location_id": selected["location_id"],
            "location_label": selected["label"],
            "route_context": route,
            "time_window": self.state.current_time_window,
            "active_rhythm": self.state.active_rhythms[0] if self.state.active_rhythms else None,
            "active_rhythms": list(self.state.active_rhythms),
            "possible_audiences": audiences,
            "local_constraints": constraints,
            "memory_site_refs": [item["site_id"] for item in memory_sites],
            "why_here": selected["why_here"],
            "why_now": self._why_now(),
            "why_these_processes": self._why_these_processes(selected["location_id"]),
            "why_not_elsewhere": self._why_not_elsewhere(rejected),
            "who_might_see": [item["audience_id"] for item in audiences if item["exposure_state"] != "none"],
            "what_this_place_remembers": [item["memory_type"] for item in memory_sites],
            "boundary_rules": self.spec.boundary_rules.model_dump(mode="json"),
        }
        location_trace = {
            "tick": context.tick_index,
            "event_type": "LocationSelectionEvent",
            "selected_location": selected["location_id"],
            "selected_location_label": selected["label"],
            "scene_type": scene_type,
            "candidate_scores": candidate_scores,
            "rejected_locations": rejected,
            "why_here": scene_context["why_here"],
            "why_not_elsewhere": scene_context["why_not_elsewhere"],
            "active_boundary_rules": scene_context["boundary_rules"],
            "caused_by_events": causal_refs,
        }
        route_trace = {
            "tick": context.tick_index,
            "event_type": "RouteSelectionEvent",
            "selected_location": selected["location_id"],
            "selected_route": route.get("route_id") if route else None,
            "route_context": route,
            "candidate_scores": self._route_candidates_for_location(selected["location_id"], evidence),
            "caused_by_events": causal_refs,
        }
        audience_trace = {
            "tick": context.tick_index,
            "event_type": "SceneAudienceContextEvent",
            "location_id": selected["location_id"],
            "possible_audiences": audiences,
            "public_consequence_allowed": any(
                item["exposure_state"] in {"observed", "reported", "institutionalized"}
                for item in audiences
            ),
            "caused_by_events": causal_refs,
        }
        return SceneLocalitySelection(scene_context, location_trace, route_trace, audience_trace)

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

    def _location_candidate(self, context: TickContext, location: LocationSpec, scene_type: str, evidence: dict[str, Any]) -> dict[str, Any]:
        assert self.spec is not None and self.state is not None
        state = self.state.location_states[location.location_id]
        active_rhythm_relevance = 1.0 if any(location.location_id in rhythm.active_locations for rhythm in self.spec.rhythms if rhythm.rhythm_id in self.state.active_rhythms) else 0.0
        memory_site_salience = max(
            [
                self.state.active_memory_sites[site.site_id].salience
                for site in self.spec.memory_sites
                if site.location_id == location.location_id
            ]
            or [0.0]
        )
        audience_pressure = max(
            [
                self.state.audience_exposure_states[audience.audience_id].exposure_level
                for audience in self.spec.audiences
                if location.location_id in audience.usual_locations
            ]
            or [0.0]
        )
        route_accessibility = max(
            [
                route_state.accessibility
                for route_id, route_state in self.state.route_states.items()
                for route in self.spec.routes
                if route.route_id == route_id and location.location_id in {route.from_location, route.to_location}
            ]
            or [state.accessibility]
        )
        travel_cost = min(
            [
                route.travel_time_minutes / 60.0
                for route in self.spec.routes
                if location.location_id in {route.from_location, route.to_location}
            ]
            or [0.0]
        )
        scene_compatibility = _scene_compatibility(location, scene_type)
        institution_pressure = _institution_pressure_for_location(self.spec, location)
        resource_pressure = _resource_pressure_for_location(self.spec, location)
        avoidance_capacity = max(
            [
                normalized_pressure(site.avoidance_pressure)
                for site in self.spec.memory_sites
                if site.location_id == location.location_id
            ]
            or [0.0]
        )
        binding_relevance = 0.65 if location.linked_processes else 0.32
        capacity_demand_relevance = _capacity_match(scene_type, location)
        field_pressure_relevance = state.pressure
        boundary_violation_penalty = 0.55 if scene_type in location.blocked_scene_types else 0.0
        score = clamp(
            binding_relevance * 0.14
            + field_pressure_relevance * 0.18
            + capacity_demand_relevance * 0.13
            + active_rhythm_relevance * 0.12
            + memory_site_salience * 0.14
            + resource_pressure * 0.08
            + institution_pressure * 0.08
            + audience_pressure * 0.08
            + route_accessibility * 0.12
            + scene_compatibility * 0.12
            - travel_cost * 0.06
            - avoidance_capacity * 0.04
            - boundary_violation_penalty
        )
        components = {
            "binding_relevance": round(binding_relevance, 4),
            "field_pressure_relevance": round(field_pressure_relevance, 4),
            "capacity_demand_relevance": round(capacity_demand_relevance, 4),
            "active_rhythm_relevance": round(active_rhythm_relevance, 4),
            "memory_site_salience": round(memory_site_salience, 4),
            "resource_pressure": round(resource_pressure, 4),
            "institution_pressure": round(institution_pressure, 4),
            "audience_pressure": round(audience_pressure, 4),
            "route_accessibility": round(route_accessibility, 4),
            "travel_cost": round(travel_cost, 4),
            "avoidance_capacity": round(avoidance_capacity, 4),
            "boundary_violation_penalty": round(boundary_violation_penalty, 4),
            "scene_compatibility": round(scene_compatibility, 4),
        }
        return {
            "location_id": location.location_id,
            "label": location.label,
            "score": round(score, 4),
            "components": components,
            "rejected_reasons": _rejected_reasons(location, scene_type, components),
            "why_here": _why_here(location, components),
            "tick_type": context.tick_type,
            "scene_type": scene_type,
            "evidence_refs": sorted(str(key) for key, value in evidence.items() if _truthy_score(value))[:8],
        }

    def _select_route_for_location(self, location_id: str, evidence: dict[str, Any]) -> dict[str, Any]:
        candidates = self._route_candidates_for_location(location_id, evidence)
        if not candidates:
            return {}
        selected = max(candidates, key=lambda item: item["route_score"])
        return {
            "route_id": selected["route_id"],
            "from_location": selected["from_location"],
            "to_location": selected["to_location"],
            "access_status": selected["access_status"],
            "travel_time_minutes": selected["travel_time_minutes"],
            "route_score": selected["route_score"],
            "route_costs": selected["components"],
        }

    def _route_candidates_for_location(self, location_id: str, evidence: dict[str, Any]) -> list[dict[str, Any]]:
        assert self.spec is not None and self.state is not None
        urgency = max([float(value) for value in evidence.values() if isinstance(value, (int, float))] or [0.0])
        candidates: list[dict[str, Any]] = []
        for route in self.spec.routes:
            if location_id not in {route.from_location, route.to_location}:
                continue
            state = self.state.route_states[route.route_id]
            travel_time_cost = min(1.0, route.travel_time_minutes / 60.0)
            components = {
                "accessibility": state.accessibility,
                "travel_time_cost": round(travel_time_cost, 4),
                "danger_cost": state.danger,
                "exposure_cost": state.exposure,
                "weather_cost": round(1.0 - state.accessibility, 4),
                "urgency": round(urgency, 4),
                "binding_pressure": 0.35 if self._route_affected_processes(route) else 0.12,
            }
            route_score = clamp(
                state.accessibility * 0.45
                - travel_time_cost * 0.12
                - state.danger * 0.14
                - state.exposure * 0.08
                - (1.0 - state.accessibility) * 0.1
                + urgency * 0.16
                + components["binding_pressure"] * 0.12
            )
            candidates.append(
                {
                    "route_id": route.route_id,
                    "from_location": route.from_location,
                    "to_location": route.to_location,
                    "access_status": state.access_status,
                    "travel_time_minutes": route.travel_time_minutes,
                    "route_score": round(route_score, 4),
                    "components": components,
                    "blocking_conditions": list(state.blocking_conditions),
                }
            )
        return sorted(candidates, key=lambda item: item["route_score"], reverse=True)

    def _audiences_for_location(self, location_id: str) -> list[dict[str, Any]]:
        assert self.spec is not None and self.state is not None
        audiences: list[dict[str, Any]] = []
        for audience in self.spec.audiences:
            if location_id not in audience.usual_locations:
                continue
            state = self.state.audience_exposure_states[audience.audience_id]
            audiences.append(
                {
                    "audience_id": audience.audience_id,
                    "label": audience.label,
                    "exposure_state": state.exposure_state,
                    "exposure_level": state.exposure_level,
                    "rumor_risk": normalized_pressure(audience.rumor_power),
                    "sanction_risk": normalized_pressure(audience.sanction_power),
                }
            )
        return sorted(audiences, key=lambda item: item["exposure_level"], reverse=True)

    def _memory_sites_for_location(self, location_id: str) -> list[dict[str, Any]]:
        assert self.spec is not None and self.state is not None
        sites: list[dict[str, Any]] = []
        for site in self.spec.memory_sites:
            if site.location_id != location_id:
                continue
            state = self.state.active_memory_sites[site.site_id]
            if not state.active:
                continue
            sites.append(
                {
                    "site_id": site.site_id,
                    "memory_type": site.memory_type,
                    "salience": state.salience,
                    "future_scene_biases": list(site.future_scene_biases),
                }
            )
        return sorted(sites, key=lambda item: item["salience"], reverse=True)

    def _constraints_for_location(self, location_id: str, route: dict[str, Any]) -> list[dict[str, Any]]:
        assert self.state is not None
        location_state = self.state.location_states[location_id]
        constraints = [
            {"constraint_type": "location_pressure", "intensity": location_state.pressure},
            {"constraint_type": "public_visibility", "intensity": location_state.crowd_density},
            {"constraint_type": "rumor_density", "intensity": location_state.rumor_density},
            {"constraint_type": "memory_salience", "intensity": location_state.memory_salience},
        ]
        if route:
            constraints.append({"constraint_type": "route_access", "intensity": clamp(1.0 - float(route.get("route_score", 0.0)))})
        return [item for item in constraints if item["intensity"] > 0]

    def _why_now(self) -> str:
        assert self.state is not None
        if self.state.active_rhythms:
            return f"active local rhythm: {', '.join(self.state.active_rhythms)}"
        return f"local time window is {self.state.current_time_window}"

    def _why_these_processes(self, location_id: str) -> str:
        assert self.spec is not None
        linked = [
            location
            for location in self.spec.locations
            if location.location_id == location_id and location.linked_processes
        ]
        if linked:
            return f"location directly links processes: {', '.join(linked[0].linked_processes)}"
        return "co-presence is licensed by active bindings and local-world pressure"

    def _why_not_elsewhere(self, rejected: list[dict[str, Any]]) -> str:
        if not rejected:
            return "no stronger local-world alternative was available"
        top = rejected[0]
        reason = ", ".join(top.get("reasons") or ["lower candidate score"])
        return f"{top['location_id']} was weaker because {reason}"


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


def _scene_compatibility(location: LocationSpec, scene_type: str) -> float:
    if not location.allowed_scene_types:
        return 0.45
    if scene_type in location.allowed_scene_types:
        return 1.0
    if any(scene_type in allowed or allowed in scene_type for allowed in location.allowed_scene_types):
        return 0.62
    return 0.25


def _institution_pressure_for_location(spec: LocalWorldSpec, location: LocationSpec) -> float:
    values = [
        normalized_pressure(institution.corruption_or_decay)
        for institution in spec.institutions
        if location.location_id in institution.locations
        or (location.controlling_institution and institution.institution_id == location.controlling_institution)
    ]
    return max(values or [0.0])


def _resource_pressure_for_location(spec: LocalWorldSpec, location: LocationSpec) -> float:
    if not location.controlling_institution:
        return 0.0
    values = [
        normalized_pressure(resource.scarcity_level) * 0.6 + normalized_pressure(resource.conflict_potential) * 0.4
        for resource in spec.resources
        if resource.controller == location.controlling_institution
    ]
    return max(values or [0.0])


def _capacity_match(scene_type: str, location: LocationSpec) -> float:
    capacity_by_scene = {
        "contaminated_evidence_review": {"evidence_access", "truth_disclosure"},
        "unstable_testimony_probe": {"truth_disclosure", "memory_integration"},
        "forbidden_symbol_confrontation": {"truth_disclosure", "memory_integration"},
        "public_performance": {"face_management"},
        "care_conflict": {"repair"},
        "private_confession": {"repair", "truth_disclosure"},
    }
    required = capacity_by_scene.get(scene_type, {"repair", "truth_disclosure"})
    available = set(_capacities_for_location(location))
    return len(required & available) / max(1, len(required))


def _rejected_reasons(location: LocationSpec, scene_type: str, components: dict[str, float]) -> list[str]:
    reasons: list[str] = []
    if scene_type in location.blocked_scene_types:
        reasons.append("scene_type_blocked_by_location")
    if components["route_accessibility"] < 0.25:
        reasons.append("route_access_too_narrow")
    if components["memory_site_salience"] < 0.25 and components["active_rhythm_relevance"] < 0.25:
        reasons.append("weak_memory_or_rhythm_relevance")
    if components["audience_pressure"] > 0.7 and scene_type in {"private_confession", "controlled_disclosure"}:
        reasons.append("public_exposure_distorts_private_scene")
    if not reasons:
        reasons.append("lower_candidate_score")
    return reasons


def _why_here(location: LocationSpec, components: dict[str, float]) -> str:
    ranked = sorted(
        (
            ("field pressure", components["field_pressure_relevance"]),
            ("active rhythm", components["active_rhythm_relevance"]),
            ("memory site", components["memory_site_salience"]),
            ("institution", components["institution_pressure"]),
            ("audience exposure", components["audience_pressure"]),
            ("route access", components["route_accessibility"]),
        ),
        key=lambda item: item[1],
        reverse=True,
    )
    top = [label for label, value in ranked[:3] if value > 0]
    if not top:
        return f"{location.location_id} was the least violating bounded-world candidate"
    return f"{location.location_id} selected through {', '.join(top)}"


def _truthy_score(value: Any) -> bool:
    if isinstance(value, (int, float)):
        return float(value) > 0
    return bool(value)
