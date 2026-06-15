from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from rpf.core.events import Event
from rpf.core.models import SimulationState, clamp


@dataclass(frozen=True)
class EnvironmentSedimentation:
    event_type: str
    payload: dict[str, Any]
    causal_refs: list[str]
    trace: dict[str, Any]


class EnvironmentSedimentationEngine:
    """Let relational history and everyday ecology sediment back into the field.

    This layer must not create new interpersonal outcomes; it makes spaces,
    audiences, objects, and ordinary time carry prior history.
    """

    def update(self, state: SimulationState, local_events: list[Event]) -> list[EnvironmentSedimentation]:
        results: list[EnvironmentSedimentation] = []
        results.extend(self._decay_sediments(state, local_events))
        results.extend(self._daily_ecology_sediments(state, local_events))
        results.extend(self._memory_sediments(state, local_events))
        results.extend(self._rpp_sediments(state, local_events))
        results.extend(self._future_constraint_sediments(state, local_events))
        results.extend(self._relation_sediments(state, local_events))
        return results

    def _decay_sediments(self, state: SimulationState, local_events: list[Event]) -> list[EnvironmentSedimentation]:
        tick_refs = [event.event_id for event in local_events if event.event_type == "TickStartedEvent"]
        refs = tick_refs[-1:] or [event.event_id for event in local_events[:1]]
        decays = {
            "spatial_constraints.avoidance_paths": 0.006,
            "spatial_constraints.memory_saturated_space": 0.004,
            "material_pressures.charged_objects": 0.005,
            "material_pressures.symbolic_debt_objects": 0.005,
            "audience_pressure.imagined_audience": 0.004,
            "audience_pressure.reputational_echo": 0.004,
        }
        results: list[EnvironmentSedimentation] = []
        for path, amount in decays.items():
            field_name, key = path.split(".", 1)
            target = getattr(state.field_state, field_name)
            current = float(target.get(key, 0.0))
            if current <= 0.0:
                continue
            results.append(
                self._field_update(
                    state,
                    path,
                    -amount,
                    "sedimented field pressure decays when not fully renewed",
                    refs,
                )
            )
        return results

    def _daily_ecology_sediments(self, state: SimulationState, local_events: list[Event]) -> list[EnvironmentSedimentation]:
        tick_event = next((event for event in local_events if event.event_type == "TickStartedEvent"), None)
        if not tick_event:
            return []
        tick_type = str(tick_event.payload.get("tick_type", "latent"))
        try:
            elapsed_hours = max(0.0, float(tick_event.payload.get("simulated_time_delta", 0.0) or 0.0) / 3600.0)
        except (TypeError, ValueError):
            elapsed_hours = 0.0
        mean_fatigue = sum(process.fatigue for process in state.processes.values()) / max(1, len(state.processes))
        material = max(state.field_state.material_pressures.values(), default=0.0)
        spatial = max(state.field_state.spatial_constraints.values(), default=0.0)
        audience = max(state.field_state.audience_pressure.values(), default=0.0)
        routine_phase = self._routine_phase(state.tick, tick_type, elapsed_hours)
        body_load = clamp(mean_fatigue * 0.42 + min(elapsed_hours / 10.0, 0.22) + (tick_type == "scene") * 0.05)
        unfinished_tasks = clamp(material * 0.28 + elapsed_hours * 0.018 + (routine_phase in {"workday_friction", "late_return"}) * 0.12)
        route_friction = clamp(spatial * 0.22 + (state.tick % 3 == 1) * 0.16 + (tick_type == "micro_interaction") * 0.1)
        object_friction = clamp(
            state.field_state.material_pressures.get("charged_objects", 0.0) * 0.3
            + state.field_state.material_pressures.get("symbolic_debt_objects", 0.0) * 0.22
            + unfinished_tasks * 0.2
        )
        waiting_pressure = clamp(
            min(elapsed_hours / 12.0, 0.28)
            + state.relation_metrics.get("silence_charge", 0.0) * 0.22
            + state.relation_metrics.get("inquiry.suppression_load", 0.0) * 0.16
            + audience * 0.08
        )
        visibility = clamp(audience * 0.16 + (routine_phase in {"commute_overlap", "workday_friction"}) * 0.12)
        deltas = {
            "fatigue_delta": round(body_load * 0.018 - (routine_phase == "night_recovery") * 0.025, 4),
            "material_delta": round(unfinished_tasks * 0.02 + object_friction * 0.012, 4),
            "spatial_delta": round(route_friction * 0.018 + waiting_pressure * 0.008, 4),
            "audience_delta": round(visibility * 0.012, 4),
            "relation_delta": round((waiting_pressure + object_friction) * 0.012, 4),
        }
        self._apply_daily_ecology(state, deltas, routine_phase, body_load, unfinished_tasks, route_friction, object_friction, waiting_pressure)
        payload = {
            "routine_phase": routine_phase,
            "tick_type": tick_type,
            "elapsed_hours": round(elapsed_hours, 4),
            "body_load": round(body_load, 4),
            "unfinished_tasks": round(unfinished_tasks, 4),
            "route_friction": round(route_friction, 4),
            "object_friction": round(object_friction, 4),
            "waiting_pressure": round(waiting_pressure, 4),
            "visibility": round(visibility, 4),
            "deltas": deltas,
            "affected_fields": [
                "processes.*.fatigue",
                "material_pressures.daily_task_debt",
                "spatial_constraints.routine_overlap",
                "audience_pressure.everyday_visibility",
                "relation_metrics.daily_ecology.*",
            ],
        }
        refs = [tick_event.event_id]
        return [
            EnvironmentSedimentation(
                event_type="DailyEcologyEvent",
                payload=payload,
                causal_refs=refs,
                trace={"event_type": "DailyEcologyEvent", **payload, "caused_by_events": refs},
            )
        ]

    def _routine_phase(self, tick: int, tick_type: str, elapsed_hours: float) -> str:
        if tick_type == "latent" and elapsed_hours >= 7.0:
            return "night_recovery"
        if elapsed_hours >= 4.0:
            return "workday_friction"
        if tick % 5 == 0:
            return "meal_or_errand_overlap"
        if tick % 3 == 1:
            return "commute_overlap"
        if tick_type == "scene":
            return "late_return"
        return "waiting_time"

    def _apply_daily_ecology(
        self,
        state: SimulationState,
        deltas: dict[str, float],
        routine_phase: str,
        body_load: float,
        unfinished_tasks: float,
        route_friction: float,
        object_friction: float,
        waiting_pressure: float,
    ) -> None:
        fatigue_delta = float(deltas["fatigue_delta"])
        for process in state.processes.values():
            process.fatigue = clamp(process.fatigue + fatigue_delta)
            process.relevance_triggers["daily_interruption"] = clamp(
                process.relevance_triggers.get("daily_interruption", 0.0) + (unfinished_tasks + route_friction) * 0.008
            )
        material = state.field_state.material_pressures
        spatial = state.field_state.spatial_constraints
        audience = state.field_state.audience_pressure
        material["daily_task_debt"] = clamp(float(material.get("daily_task_debt", 0.0) or 0.0) + float(deltas["material_delta"]))
        material["object_friction"] = clamp(float(material.get("object_friction", 0.0) or 0.0) + object_friction * 0.012)
        spatial["routine_overlap"] = clamp(float(spatial.get("routine_overlap", 0.0) or 0.0) + float(deltas["spatial_delta"]))
        spatial["route_friction"] = clamp(float(spatial.get("route_friction", 0.0) or 0.0) + route_friction * 0.01)
        audience["everyday_visibility"] = clamp(float(audience.get("everyday_visibility", 0.0) or 0.0) + float(deltas["audience_delta"]))
        state.relation_metrics["daily_ecology.body_load"] = clamp(
            float(state.relation_metrics.get("daily_ecology.body_load", 0.0) or 0.0) * 0.86 + body_load * 0.14
        )
        state.relation_metrics["daily_ecology.unfinished_tasks"] = clamp(
            float(state.relation_metrics.get("daily_ecology.unfinished_tasks", 0.0) or 0.0) * 0.86 + unfinished_tasks * 0.14
        )
        state.relation_metrics["daily_ecology.routine_overlap"] = clamp(
            float(state.relation_metrics.get("daily_ecology.routine_overlap", 0.0) or 0.0) * 0.86 + route_friction * 0.14
        )
        state.relation_metrics["daily_ecology.object_friction"] = clamp(
            float(state.relation_metrics.get("daily_ecology.object_friction", 0.0) or 0.0) * 0.86 + object_friction * 0.14
        )
        state.relation_metrics["daily_ecology.waiting_pressure"] = clamp(
            float(state.relation_metrics.get("daily_ecology.waiting_pressure", 0.0) or 0.0) * 0.86 + waiting_pressure * 0.14
        )
        if routine_phase == "night_recovery":
            state.relation_metrics["silence_charge"] = clamp(float(state.relation_metrics.get("silence_charge", 0.0) or 0.0) + waiting_pressure * 0.006)
        else:
            state.relation_metrics["conflict_pressure"] = clamp(float(state.relation_metrics.get("conflict_pressure", 0.0) or 0.0) + float(deltas["relation_delta"]))

    def _memory_sediments(self, state: SimulationState, local_events: list[Event]) -> list[EnvironmentSedimentation]:
        memory_events = [event for event in local_events if event.event_type == "MemoryReconstructionEvent"]
        pressure = max((self._memory_future_pressure(event) for event in memory_events), default=0.0)
        if pressure <= 0.05:
            return []
        return [
            self._field_update(
                state,
                "spatial_constraints.memory_saturated_space",
                pressure * 0.04,
                "reconstructed memory makes the shared space less neutral",
                [event.event_id for event in memory_events if self._memory_future_pressure(event) > 0.0],
            )
        ]

    def _rpp_sediments(self, state: SimulationState, local_events: list[Event]) -> list[EnvironmentSedimentation]:
        results: list[EnvironmentSedimentation] = []
        for event in local_events:
            if event.event_type != "RPPActivationEvent":
                continue
            rpp_id = str(event.payload.get("rpp_id", ""))
            score = self._payload_float(event, "activation_score")
            if score <= 0.05:
                continue
            if rpp_id in {"pursuit_withdrawal", "silence_interpretation_loop"}:
                results.append(
                    self._field_update(
                        state,
                        "spatial_constraints.avoidance_paths",
                        score * 0.018,
                        "repeated pursuit and withdrawal make avoidance routes part of the field",
                        [event.event_id],
                    )
                )
                results.append(
                    self._micro_world(
                        state,
                        "avoidance_route",
                        "shared_space",
                        "ordinary movement now carries relational avoidance",
                        ["delays and spatial gaps become easier future signals"],
                        [event.event_id],
                    )
                )
            elif rpp_id in {"contribution_debt_loop", "repair_avoidance"}:
                results.append(
                    self._field_update(
                        state,
                        "material_pressures.charged_objects",
                        score * 0.014,
                        "practical objects begin to carry unresolved contribution and repair claims",
                        [event.event_id],
                    )
                )
                results.append(
                    self._micro_world(
                        state,
                        "charged_object_world",
                        "shared_objects",
                        "bills, chores, messages, or tools become carriers of unresolved claims",
                        ["material prompts can re-enter as recognition pressure"],
                        [event.event_id],
                    )
                )
            elif rpp_id in {"public_private_split", "face_saving_loop"}:
                results.append(
                    self._field_update(
                        state,
                        "audience_pressure.imagined_audience",
                        score * 0.018,
                        "public performance history makes an imagined audience active even when absent",
                        [event.event_id],
                    )
                )
                results.append(
                    self._micro_world(
                        state,
                        "public_mask_world",
                        "audience_network",
                        "the public version of the relation becomes a local world",
                        ["future speech is filtered through exposure risk"],
                        [event.event_id],
                    )
                )
        return results

    def _future_constraint_sediments(self, state: SimulationState, local_events: list[Event]) -> list[EnvironmentSedimentation]:
        future_events = [event for event in local_events if event.event_type == "FutureConstraintEvent"]
        if not future_events:
            return []
        public = max((self._payload_float(event, "intensity") for event in future_events if "public" in str(event.payload.get("constraint_type", ""))), default=0.0)
        debt = max((self._payload_float(event, "intensity") for event in future_events if any(term in str(event.payload.get("constraint_type", "")) for term in ["debt", "owe"])), default=0.0)
        results: list[EnvironmentSedimentation] = []
        if public > 0.05:
            results.append(
                self._field_update(
                    state,
                    "audience_pressure.reputational_echo",
                    public * 0.02,
                    "public future constraints echo as audience pressure",
                    [event.event_id for event in future_events if "public" in str(event.payload.get("constraint_type", ""))],
                )
            )
        if debt > 0.05:
            results.append(
                self._field_update(
                    state,
                    "material_pressures.symbolic_debt_objects",
                    debt * 0.02,
                    "debt-like future constraints attach to ordinary material prompts",
                    [
                        event.event_id
                        for event in future_events
                        if any(term in str(event.payload.get("constraint_type", "")) for term in ["debt", "owe"])
                    ],
                )
            )
        return results

    def _relation_sediments(self, state: SimulationState, local_events: list[Event]) -> list[EnvironmentSedimentation]:
        relation_events = [
            event
            for event in local_events
            if event.event_type == "RelationSedimentationEvent" and self._payload_float(event, "delta") > 0.0
        ]
        results: list[EnvironmentSedimentation] = []
        for event in relation_events:
            metric = str(event.payload.get("metric", ""))
            delta = self._payload_float(event, "delta")
            value = self._payload_float(event, "new_value")
            if metric in {"relation_sediment.recognition_debt", "relation_sediment.symbolic_accounting_load"}:
                results.append(
                    self._field_update(
                        state,
                        "material_pressures.symbolic_debt_objects",
                        delta * 0.045 + value * 0.002,
                        "relation sediment attaches unsettled accounting to material prompts",
                        [event.event_id],
                    )
                )
            elif metric == "relation_sediment.repair_access_narrowing":
                results.append(
                    self._field_update(
                        state,
                        "spatial_constraints.avoidance_paths",
                        delta * 0.05 + value * 0.002,
                        "relation sediment makes avoidance routes more available in the field",
                        [event.event_id],
                    )
                )
            elif metric in {"relation_sediment.public_definition_load", "relation_sediment.asymmetry_load"}:
                results.append(
                    self._field_update(
                        state,
                        "audience_pressure.imagined_audience",
                        delta * 0.04 + value * 0.0015,
                        "relation sediment makes the relation's definition feel observable",
                        [event.event_id],
                    )
                )
            elif metric in {"relation_sediment.future_lock_load", "relation_sediment.shared_fate_load", "relation_sediment.memory_saturation"}:
                results.append(
                    self._field_update(
                        state,
                        "spatial_constraints.memory_saturated_space",
                        delta * 0.035 + value * 0.0015,
                        "relation sediment makes shared space carry more historical load",
                        [event.event_id],
                    )
                )
        return [result for result in results if result.payload["previous_value"] != result.payload["new_value"]]

    def _field_update(
        self,
        state: SimulationState,
        path: str,
        delta: float,
        reason: str,
        refs: list[str],
    ) -> EnvironmentSedimentation:
        field_name, key = path.split(".", 1)
        target = getattr(state.field_state, field_name)
        previous = float(target.get(key, 0.0))
        new_value = clamp(previous + delta)
        target[key] = new_value
        payload = {
            "changed_field_path": path,
            "previous_value": round(previous, 4),
            "new_value": new_value,
            "reason": reason,
            "caused_by_events": refs,
        }
        return EnvironmentSedimentation(
            event_type="FieldUpdateEvent",
            payload=payload,
            causal_refs=refs,
            trace={"event_type": "FieldUpdateEvent", **payload},
        )

    def _micro_world(
        self,
        state: SimulationState,
        micro_world_type: str,
        location_or_object: str,
        symbolic_meaning: str,
        future_affordance_changes: list[str],
        refs: list[str],
    ) -> EnvironmentSedimentation:
        if micro_world_type not in state.field_state.enacted_micro_worlds:
            state.field_state.enacted_micro_worlds.append(micro_world_type)
        payload = {
            "micro_world_type": micro_world_type,
            "location_or_object": location_or_object,
            "participating_processes": sorted(state.processes),
            "symbolic_meaning": symbolic_meaning,
            "future_affordance_changes": future_affordance_changes,
        }
        return EnvironmentSedimentation(
            event_type="EnactedMicroWorldEvent",
            payload=payload,
            causal_refs=refs,
            trace={"event_type": "EnactedMicroWorldEvent", **payload, "caused_by_events": refs},
        )

    def _memory_future_pressure(self, event: Event) -> float:
        evidence = event.payload.get("evidence", {})
        if not isinstance(evidence, dict):
            return 0.0
        try:
            return clamp(float(evidence.get("future_constraint_pressure", 0.0)))
        except (TypeError, ValueError):
            return 0.0

    def _payload_float(self, event: Event, key: str) -> float:
        try:
            return clamp(float(event.payload.get(key, 0.0)))
        except (TypeError, ValueError):
            return 0.0
