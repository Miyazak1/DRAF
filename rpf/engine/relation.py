from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from rpf.core.events import Event
from rpf.core.models import SimulationState, clamp


@dataclass(frozen=True)
class RelationSedimentation:
    metric: str
    previous_value: float
    new_value: float
    reason: str
    causal_refs: list[str]
    evidence_event_types: list[str]
    reason_details: list[str] | None = None

    def payload(self) -> dict[str, Any]:
        payload = {
            "metric": self.metric,
            "previous_value": self.previous_value,
            "new_value": self.new_value,
            "delta": round(self.new_value - self.previous_value, 4),
            "reason": self.reason,
            "caused_by_events": self.causal_refs,
            "evidence_event_types": self.evidence_event_types,
        }
        if self.reason_details:
            payload["reason_details"] = self.reason_details
        return payload


class RelationSedimentationEngine:
    """Sediment event history into relation-level constraints.

    These metrics are not relationship traits. They are slow relation-process
    residues produced by repeated recognition, repair, memory, field, and future
    constraint evidence.
    """

    PREFIX = "relation_sediment."

    def update(self, state: SimulationState, local_events: list[Event]) -> list[RelationSedimentation]:
        updates: list[RelationSedimentation] = []
        updates.extend(self._decay(state, local_events))
        updates.extend(self._event_updates(state, local_events))
        return self._coalesce(updates)

    def _coalesce(self, updates: list[RelationSedimentation]) -> list[RelationSedimentation]:
        grouped: dict[tuple[str, str], list[RelationSedimentation]] = {}
        decay_reason = "relation sediment decays when not reinforced"
        for update in updates:
            if update.previous_value == update.new_value:
                continue
            kind = "decay" if update.reason == decay_reason else "evidence"
            grouped.setdefault((update.metric, kind), []).append(update)
        coalesced: list[RelationSedimentation] = []
        for (metric, kind), items in grouped.items():
            first = items[0]
            last = items[-1]
            if kind == "decay":
                reason = decay_reason
                details = None
            elif len(items) == 1:
                reason = first.reason
                details = None
            else:
                reason = "relation sediment updated from tick evidence"
                details = sorted({item.reason for item in items})
            coalesced.append(
                RelationSedimentation(
                    metric=metric,
                    previous_value=first.previous_value,
                    new_value=last.new_value,
                    reason=reason,
                    causal_refs=sorted({ref for item in items for ref in item.causal_refs}),
                    evidence_event_types=sorted({event_type for item in items for event_type in item.evidence_event_types}),
                    reason_details=details,
                )
            )
        return coalesced

    def _decay(self, state: SimulationState, local_events: list[Event]) -> list[RelationSedimentation]:
        refs = [event.event_id for event in local_events if event.event_type == "TickStartedEvent"][-1:]
        refs = refs or [event.event_id for event in local_events[:1]]
        updates: list[RelationSedimentation] = []
        for metric, value in list(state.relation_metrics.items()):
            if not metric.startswith(self.PREFIX):
                continue
            previous = float(value)
            if previous <= 0.0001:
                continue
            decay = min(previous, 0.0025)
            updates.append(
                self._set_metric(
                    state,
                    metric,
                    previous - decay,
                    "relation sediment decays when not reinforced",
                    refs,
                    ["TickStartedEvent"],
                )
            )
        return [update for update in updates if update.previous_value != update.new_value]

    def _event_updates(self, state: SimulationState, local_events: list[Event]) -> list[RelationSedimentation]:
        updates: list[RelationSedimentation] = []
        for event in local_events:
            event_type = event.event_type
            refs = sorted(set([event.event_id] + list(event.causal_refs)))
            if event_type == "RecognitionEvent":
                result = str(event.payload.get("result", ""))
                if result in {"refused", "misunderstood", "postponed", "displaced"}:
                    updates.append(
                        self._delta(
                            state,
                            "relation_sediment.recognition_debt",
                            0.01,
                            f"recognition outcome {result} leaves an unsettled relation claim",
                            refs,
                            [event_type],
                        )
                    )
                    updates.append(
                        self._delta(
                            state,
                            "relation_sediment.repair_access_narrowing",
                            0.006,
                            f"recognition outcome {result} narrows later repair access",
                            refs,
                            [event_type],
                        )
                    )
                elif result in {"granted", "partial"}:
                    updates.append(
                        self._delta(
                            state,
                            "relation_sediment.recognition_debt",
                            -0.012,
                            f"recognition outcome {result} reduces unsettled relation debt",
                            refs,
                            [event_type],
                        )
                    )
            elif event_type == "MisrecognitionEvent":
                updates.append(
                    self._delta(
                        state,
                        "relation_sediment.recognition_debt",
                        0.018,
                        "misrecognition sediments as relation-level recognition debt",
                        refs,
                        [event_type],
                    )
                )
            elif event_type in {"AvoidanceEvent", "DisplacementEvent"}:
                updates.append(
                    self._delta(
                        state,
                        "relation_sediment.repair_access_narrowing",
                        0.014,
                        f"{event_type} makes direct repair less available later",
                        refs,
                        [event_type],
                    )
                )
            elif event_type == "RepairEvent":
                updates.append(
                    self._delta(
                        state,
                        "relation_sediment.repair_access_narrowing",
                        -0.018,
                        "repair reopens some relation-level repair access",
                        refs,
                        [event_type],
                    )
                )
                updates.append(
                    self._delta(
                        state,
                        "relation_sediment.recognition_debt",
                        -0.008,
                        "repair reduces unsettled recognition debt",
                        refs,
                        [event_type],
                    )
                )
            elif event_type == "RPPCompositionEvent":
                updates.extend(self._composition_updates(state, event, refs))
            elif event_type == "FutureConstraintEvent":
                intensity = self._payload_float(event, "intensity")
                updates.append(
                    self._delta(
                        state,
                        "relation_sediment.future_lock_load",
                        intensity * 0.01,
                        "future constraint sediments as shared relation lock-in",
                        refs,
                        [event_type],
                    )
                )
                if event.payload.get("source_layer") == "irreversibility":
                    updates.append(
                        self._delta(
                            state,
                            "relation_sediment.shared_fate_load",
                            intensity * 0.012,
                            "irreversible future constraint raises shared fate load",
                            refs,
                            [event_type],
                        )
                    )
            elif event_type == "MemoryReconstructionEvent":
                updates.extend(self._memory_updates(state, event, refs))
            elif event_type == "FieldUpdateEvent":
                path = str(event.payload.get("changed_field_path", ""))
                if "audience_pressure" in path or "imagined_audience" in path:
                    updates.append(
                        self._delta(
                            state,
                            "relation_sediment.public_definition_load",
                            0.006,
                            "field audience pressure makes relation definition more public",
                            refs,
                            [event_type],
                        )
                    )
                if "spatial_constraints" in path:
                    updates.append(
                        self._delta(
                            state,
                            "relation_sediment.repair_access_narrowing",
                            0.004,
                            "sedimented space narrows later repair access",
                            refs,
                            [event_type],
                        )
                    )
            elif event_type == "DispositionSedimentationEvent":
                path = str(event.payload.get("changed_path", ""))
                delta = abs(self._payload_float(event, "delta"))
                if path in {"checking_tendency", "ambiguity_tolerance", "risk_suspension_scope"}:
                    updates.append(
                        self._delta(
                            state,
                            "relation_sediment.mutual_predictability_load",
                            delta * 0.5,
                            "process disposition change stabilizes relation-level expectation",
                            refs,
                            [event_type],
                        )
                    )
                if path.startswith("speech_inhibition.") or path.startswith("threat_sensitivity."):
                    updates.append(
                        self._delta(
                            state,
                            "relation_sediment.asymmetry_load",
                            delta * 0.45,
                            "inhibition and threat sensitivity sediment as relation asymmetry",
                            refs,
                            [event_type],
                        )
                    )
            elif event_type == "NormativePressureEvent":
                updates.extend(self._normative_updates(state, event, refs))
        return [update for update in updates if update.previous_value != update.new_value]

    def _composition_updates(
        self,
        state: SimulationState,
        event: Event,
        refs: list[str],
    ) -> list[RelationSedimentation]:
        composition_id = str(event.payload.get("composition_id", ""))
        score = self._payload_float(event, "composition_score")
        if not score:
            return []
        if composition_id in {"debt_lock", "credit_recognition_lock", "recognition_trap"}:
            return [
                self._delta(
                    state,
                    "relation_sediment.symbolic_accounting_load",
                    score * 0.012,
                    f"{composition_id} sediments moral accounting into the relation",
                    refs,
                    [event.event_type],
                )
            ]
        if composition_id in {"anxious_silence_circuit", "pursuit_withdrawal_lock"}:
            return [
                self._delta(
                    state,
                    "relation_sediment.repair_access_narrowing",
                    score * 0.01,
                    f"{composition_id} narrows direct repair access",
                    refs,
                    [event.event_type],
                )
            ]
        if composition_id in {"care_bind_double_bind", "public_mask_split"}:
            return [
                self._delta(
                    state,
                    "relation_sediment.asymmetry_load",
                    score * 0.012,
                    f"{composition_id} sediments asymmetric role pressure",
                    refs,
                    [event.event_type],
                )
            ]
        return []

    def _memory_updates(
        self,
        state: SimulationState,
        event: Event,
        refs: list[str],
    ) -> list[RelationSedimentation]:
        salience = self._payload_float(event, "salience")
        biases = {str(item) for item in event.payload.get("reconstruction_biases", [])}
        updates = [
            self._delta(
                state,
                "relation_sediment.memory_saturation",
                salience * 0.008,
                "reconstructed memory increases relation-level historical saturation",
                refs,
                [event.event_type],
            )
        ]
        if biases.intersection({"injury_reconstruction", "defensive_reconstruction", "misunderstood"}):
            updates.append(
                self._delta(
                    state,
                    "relation_sediment.recognition_debt",
                    salience * 0.006,
                    "injury or defensive memory keeps recognition debt available",
                    refs,
                    [event.event_type],
                )
            )
        if "fate_lock" in biases:
            updates.append(
                self._delta(
                    state,
                    "relation_sediment.shared_fate_load",
                    salience * 0.008,
                    "fate memory sediments shared fate load",
                    refs,
                    [event.event_type],
                )
            )
        return updates

    def _normative_updates(
        self,
        state: SimulationState,
        event: Event,
        refs: list[str],
    ) -> list[RelationSedimentation]:
        norm_type = str(event.payload.get("norm_type", ""))
        delta = max(0.0, self._payload_float(event, "delta"))
        if delta <= 0.0:
            return []
        event_type = event.event_type
        if norm_type in {"claim_entitlement", "reciprocity_obligation"}:
            return [
                self._delta(
                    state,
                    "relation_sediment.symbolic_accounting_load",
                    delta * 0.28,
                    f"normative {norm_type} sediments as symbolic accounting load",
                    refs,
                    [event_type],
                ),
                self._delta(
                    state,
                    "relation_sediment.recognition_debt",
                    delta * 0.18,
                    f"normative {norm_type} keeps recognition debt claimable",
                    refs,
                    [event_type],
                ),
            ]
        if norm_type == "repair_obligation":
            return [
                self._delta(
                    state,
                    "relation_sediment.repair_access_narrowing",
                    delta * 0.22,
                    "unmet repair obligation sediments as narrowed repair access",
                    refs,
                    [event_type],
                )
            ]
        if norm_type in {"legitimacy_contestation", "exit_justification"}:
            return [
                self._delta(
                    state,
                    "relation_sediment.asymmetry_load",
                    delta * 0.2,
                    f"normative {norm_type} sediments as relation asymmetry",
                    refs,
                    [event_type],
                ),
                self._delta(
                    state,
                    "relation_sediment.repair_access_narrowing",
                    delta * 0.16,
                    f"normative {norm_type} narrows later direct repair",
                    refs,
                    [event_type],
                ),
            ]
        if norm_type == "public_face_obligation":
            return [
                self._delta(
                    state,
                    "relation_sediment.public_definition_load",
                    delta * 0.24,
                    "public face obligation sediments relation definition into audience space",
                    refs,
                    [event_type],
                )
            ]
        if norm_type == "mutual_obligation":
            return [
                self._delta(
                    state,
                    "relation_sediment.shared_fate_load",
                    delta * 0.2,
                    "mutual obligation sediments as shared fate load",
                    refs,
                    [event_type],
                )
            ]
        if norm_type == "irreversible_precedent":
            return [
                self._delta(
                    state,
                    "relation_sediment.future_lock_load",
                    delta * 0.22,
                    "normative precedent sediments as future lock load",
                    refs,
                    [event_type],
                )
            ]
        return []

    def _delta(
        self,
        state: SimulationState,
        metric: str,
        delta: float,
        reason: str,
        refs: list[str],
        event_types: list[str],
    ) -> RelationSedimentation:
        previous = float(state.relation_metrics.get(metric, 0.0))
        return self._set_metric(state, metric, previous + delta, reason, refs, event_types)

    def _set_metric(
        self,
        state: SimulationState,
        metric: str,
        value: float,
        reason: str,
        refs: list[str],
        event_types: list[str],
    ) -> RelationSedimentation:
        previous = float(state.relation_metrics.get(metric, 0.0))
        new_value = clamp(value)
        state.relation_metrics[metric] = new_value
        return RelationSedimentation(
            metric=metric,
            previous_value=round(previous, 4),
            new_value=new_value,
            reason=reason,
            causal_refs=sorted(set(refs)),
            evidence_event_types=sorted(set(event_types)),
        )

    def _payload_float(self, event: Event, key: str) -> float:
        try:
            return float(event.payload.get(key, 0.0))
        except (TypeError, ValueError):
            return 0.0
