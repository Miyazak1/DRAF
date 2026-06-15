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
    """Let relational history sediment back into the field.

    This layer mutates only field_state. It must not create new interpersonal
    outcomes; it makes spaces, audiences, and objects carry prior history.
    """

    def update(self, state: SimulationState, local_events: list[Event]) -> list[EnvironmentSedimentation]:
        results: list[EnvironmentSedimentation] = []
        results.extend(self._decay_sediments(state, local_events))
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
