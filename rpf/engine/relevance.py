from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from rpf.core.events import Event
from rpf.core.models import SimulationState, clamp


@dataclass(frozen=True)
class RelevanceShift:
    process_id: str
    marker: str
    previous_value: float
    new_value: float
    reason: str
    causal_refs: list[str]
    evidence_event_types: list[str]

    def payload(self) -> dict[str, Any]:
        delta = round(self.new_value - self.previous_value, 4)
        return {
            "process_id": self.process_id,
            "marker": self.marker,
            "marker_key": self.key,
            "previous_value": self.previous_value,
            "new_value": self.new_value,
            "delta": delta,
            "salience_changes": {self.marker: delta},
            "threat_marker_changes": self._threat_changes(delta),
            "opportunity_marker_changes": self._opportunity_changes(delta),
            "memory_activations": [],
            "ignored_background_changes": {},
            "reason": self.reason,
            "caused_by_events": self.causal_refs,
            "evidence_event_types": self.evidence_event_types,
        }

    @property
    def key(self) -> str:
        return f"relevance_field.{self.process_id}.{self.marker}"

    def _threat_changes(self, delta: float) -> dict[str, float]:
        if self.marker in {"delayed_reply", "public_exposure", "being_controlled", "double_bind", "exit_threat"}:
            return {self.marker: delta}
        return {}

    def _opportunity_changes(self, delta: float) -> dict[str, float]:
        if self.marker in {"repair_opening", "recognition_claim", "material_cost"}:
            return {self.marker: delta}
        return {}


class RelevanceLandscapeEngine:
    """Sediment what becomes relevant enough to guide later perception.

    Relevance is not a motive and not attention as an inner meter. It is an
    event-sourced landscape that gates which signals become noticeable, threatening,
    promising, or repeatedly available for memory reconstruction.
    """

    PREFIX = "relevance_field."

    def update(self, state: SimulationState, local_events: list[Event]) -> list[RelevanceShift]:
        updates: list[RelevanceShift] = []
        updates.extend(self._decay(state, local_events))
        updates.extend(self._event_updates(state, local_events))
        result = self._coalesce(updates)
        self._mirror_to_process_triggers(state, result)
        return result

    def _decay(self, state: SimulationState, local_events: list[Event]) -> list[RelevanceShift]:
        refs = [event.event_id for event in local_events if event.event_type == "TickStartedEvent"][-1:]
        refs = refs or [event.event_id for event in local_events[:1]]
        updates: list[RelevanceShift] = []
        for key, value in list(state.relation_metrics.items()):
            if not key.startswith(self.PREFIX):
                continue
            parts = key.split(".", 2)
            if len(parts) != 3:
                continue
            _, process_id, marker = parts
            current = float(value)
            if current <= 0.0001:
                continue
            updates.append(
                self._set(
                    state,
                    process_id,
                    marker,
                    current - min(current, 0.004),
                    "relevance salience decays when not renewed",
                    refs,
                    ["TickStartedEvent"],
                )
            )
        return updates

    def _event_updates(self, state: SimulationState, local_events: list[Event]) -> list[RelevanceShift]:
        updates: list[RelevanceShift] = []
        for event in local_events:
            event_type = event.event_type
            refs = sorted(set([event.event_id] + list(event.causal_refs)))
            if event_type == "FieldPressureEvent":
                intensity = self._payload_float(event, "intensity")
                for process_id in state.processes:
                    updates.append(
                        self._delta(
                            state,
                            process_id,
                            "material_cost",
                            intensity * 0.018,
                            "field pressure makes material cost salient",
                            refs,
                            [event_type],
                        )
                    )
            elif event_type == "AffordanceSelectionEvent":
                updates.extend(self._affordance_updates(state, event, refs))
            elif event_type == "MicroSignalEvent":
                signal_type = str(event.payload.get("signal_type", ""))
                updates.extend(self._signal_updates(state, signal_type, refs, event_type))
            elif event_type == "ObservationEvent":
                observer = str(event.payload.get("observer", "p1"))
                expression_mode = str(event.payload.get("expression_mode", ""))
                confidence = self._payload_float(event, "confidence")
                if expression_mode in {"silence", "timing_distortion", "gesture"}:
                    updates.append(
                        self._delta(
                            state,
                            observer,
                            "delayed_reply",
                            max(0.006, confidence * 0.02),
                            f"observed {expression_mode} makes absence salient",
                            refs,
                            [event_type],
                        )
                    )
            elif event_type == "RecognitionEvent":
                updates.extend(self._recognition_updates(state, event, refs))
            elif event_type == "MemoryReconstructionEvent":
                owner = str(event.payload.get("owner_process_id", "p1"))
                salience = self._payload_float(event, "salience")
                biases = {str(item) for item in event.payload.get("reconstruction_biases", [])}
                marker = "recognition_claim" if "injury_reconstruction" in biases else "exit_threat"
                updates.append(
                    self._delta(
                        state,
                        owner,
                        marker,
                        salience * 0.018,
                        "reconstructed memory renews relevance landscape",
                        refs,
                        [event_type],
                    )
                )
            elif event_type == "NormativePressureEvent":
                process_id = str(event.payload.get("process_id", "p1"))
                norm_type = str(event.payload.get("norm_type", ""))
                delta = max(0.0, self._payload_float(event, "delta"))
                marker = {
                    "claim_entitlement": "recognition_claim",
                    "repair_obligation": "repair_opening",
                    "public_face_obligation": "public_exposure",
                    "exit_justification": "exit_threat",
                    "legitimacy_contestation": "recognition_claim",
                }.get(norm_type)
                if marker:
                    updates.append(
                        self._delta(
                            state,
                            process_id,
                            marker,
                            delta * 0.42,
                            f"normative {norm_type} pressure changes what is relevant",
                            refs,
                            [event_type],
                        )
                    )
            elif event_type == "FrameDefinitionEvent":
                frame_type = str(event.payload.get("frame_type", ""))
                delta = max(0.0, self._payload_float(event, "delta"))
                marker = {
                    "avoidance_scene": "delayed_reply",
                    "public_performance": "public_exposure",
                    "care_control": "being_controlled",
                    "double_bind": "double_bind",
                    "debt_accounting": "recognition_claim",
                    "repair_scene": "repair_opening",
                    "material_accounting": "material_cost",
                }.get(frame_type)
                if marker:
                    for process_id in state.processes:
                        updates.append(
                            self._delta(
                                state,
                                process_id,
                                marker,
                                delta * 0.24,
                                f"frame {frame_type} makes {marker} more relevant",
                                refs,
                                [event_type],
                            )
                        )
            elif event_type == "RelationSedimentationEvent":
                updates.extend(self._relation_updates(state, event, refs))
            elif event_type == "AttentionDriftEvent":
                updates.extend(self._attention_updates(state, event, refs))
            elif event_type == "OpportunityCostEvent":
                updates.extend(self._opportunity_updates(state, event, refs))
            elif event_type == "ActionReversibilityEvent":
                updates.extend(self._reversibility_updates(state, event, refs))
            elif event_type == "EpistemicBoundaryEvent":
                updates.extend(self._epistemic_updates(state, event, refs))
        return [update for update in updates if update.previous_value != update.new_value]

    def _affordance_updates(
        self,
        state: SimulationState,
        event: Event,
        refs: list[str],
    ) -> list[RelevanceShift]:
        affordance_id = str(event.payload.get("affordance_id", ""))
        source = str(event.payload.get("source_process") or self._source_from_affordance(affordance_id))
        marker = {
            "mediated_delay": "delayed_reply",
            "unacknowledged_contribution_claim": "recognition_claim",
            "public_performance": "public_exposure",
            "care_intervention": "being_controlled",
            "double_bind_response": "double_bind",
            "material_pressure_intrusion": "material_cost",
            "practical_repair_offer": "repair_opening",
            "embodied_avoidance": "delayed_reply",
        }.get(affordance_id)
        if not marker:
            return []
        target_processes = list(state.processes) if source not in state.processes else [source]
        return [
            self._delta(
                state,
                process_id,
                marker,
                0.016,
                f"affordance {affordance_id} enters the relevance landscape",
                refs,
                [event.event_type],
            )
            for process_id in target_processes
        ]

    def _signal_updates(
        self,
        state: SimulationState,
        signal_type: str,
        refs: list[str],
        event_type: str,
    ) -> list[RelevanceShift]:
        marker = {
            "delayed_reply": "delayed_reply",
            "short_answer": "delayed_reply",
            "gaze_avoidance": "delayed_reply",
            "unacknowledged_help": "recognition_claim",
            "public_politeness": "public_exposure",
            "care_instruction": "being_controlled",
            "contradictory_request": "double_bind",
            "material_urgency": "material_cost",
            "practical_repair": "repair_opening",
        }.get(signal_type)
        if not marker:
            return []
        return [
            self._delta(
                state,
                process_id,
                marker,
                0.014,
                f"micro signal {signal_type} becomes relevant",
                refs,
                [event_type],
            )
            for process_id in state.processes
        ]

    def _recognition_updates(
        self,
        state: SimulationState,
        event: Event,
        refs: list[str],
    ) -> list[RelevanceShift]:
        result = str(event.payload.get("outcome") or event.payload.get("result") or "")
        holder = str(event.payload.get("holder", "p1"))
        demanded_from = str(event.payload.get("demanded_from", "p2"))
        updates: list[RelevanceShift] = []
        if result in {"refused", "misunderstood", "displaced", "postponed", "unspeakable"}:
            updates.append(
                self._delta(
                    state,
                    holder,
                    "recognition_claim",
                    0.026,
                    f"recognition result {result} makes recognition claim salient",
                    refs,
                    [event.event_type],
                )
            )
            updates.append(
                self._delta(
                    state,
                    demanded_from,
                    "exit_threat",
                    0.016,
                    f"recognition result {result} makes exit or refusal salient",
                    refs,
                    [event.event_type],
                )
            )
        if result in {"granted", "partial"}:
            for process_id in {holder, demanded_from}.intersection(state.processes):
                updates.append(
                    self._delta(
                        state,
                        process_id,
                        "repair_opening",
                        0.018,
                        f"recognition result {result} makes repair opening salient",
                        refs,
                        [event.event_type],
                    )
                )
        return updates

    def _relation_updates(
        self,
        state: SimulationState,
        event: Event,
        refs: list[str],
    ) -> list[RelevanceShift]:
        metric = str(event.payload.get("metric", ""))
        delta = max(0.0, self._payload_float(event, "delta"))
        marker = {
            "relation_sediment.recognition_debt": "recognition_claim",
            "relation_sediment.repair_access_narrowing": "delayed_reply",
            "relation_sediment.public_definition_load": "public_exposure",
            "relation_sediment.asymmetry_load": "being_controlled",
            "relation_sediment.future_lock_load": "double_bind",
            "relation_sediment.symbolic_accounting_load": "material_cost",
        }.get(metric)
        if not marker or delta <= 0.0:
            return []
        return [
            self._delta(
                state,
                process_id,
                marker,
                delta * 0.22,
                f"{metric} changes what becomes relevant",
                refs,
                [event.event_type],
            )
            for process_id in state.processes
        ]

    def _attention_updates(
        self,
        state: SimulationState,
        event: Event,
        refs: list[str],
    ) -> list[RelevanceShift]:
        process_id = str(event.payload.get("process_id", ""))
        if process_id not in state.processes:
            return []
        focus = str(event.payload.get("dominant_focus", ""))
        drift = self._payload_float(event, "drift_intensity")
        marker = {
            "body_management": "material_cost",
            "case_fixation": "recognition_claim",
            "threat_monitoring": "exit_threat",
            "repair_opportunity": "repair_opening",
            "avoidance_route": "delayed_reply",
            "memory_intrusion": "recognition_claim",
        }.get(focus)
        if not marker or drift <= 0.0:
            return []
        return [
            self._delta(
                state,
                process_id,
                marker,
                drift * 0.16,
                f"attention drift toward {focus} makes {marker} more relevant",
                refs,
                [event.event_type],
            )
        ]

    def _opportunity_updates(
        self,
        state: SimulationState,
        event: Event,
        refs: list[str],
    ) -> list[RelevanceShift]:
        process_id = str(event.payload.get("process_id", ""))
        if process_id not in state.processes:
            return []
        cost_type = str(event.payload.get("cost_type", ""))
        intensity = self._payload_float(event, "intensity")
        marker = {
            "recovery_window_loss": "material_cost",
            "repair_window_loss": "repair_opening",
            "evidence_window_loss": "recognition_claim",
            "social_exposure_cost": "public_exposure",
            "trust_window_loss": "exit_threat",
            "ordinary_task_spillover": "material_cost",
        }.get(cost_type)
        if not marker or intensity <= 0.0:
            return []
        return [
            self._delta(
                state,
                process_id,
                marker,
                intensity * 0.18,
                f"opportunity cost {cost_type} makes {marker} more salient",
                refs,
                [event.event_type],
            )
        ]

    def _reversibility_updates(
        self,
        state: SimulationState,
        event: Event,
        refs: list[str],
    ) -> list[RelevanceShift]:
        process_id = str(event.payload.get("process_id", ""))
        if process_id not in state.processes:
            return []
        threshold_state = str(event.payload.get("threshold_state", ""))
        pressure = self._payload_float(event, "threshold_proximity")
        if pressure <= 0.0:
            return []
        marker = {
            "recoverable": "repair_opening",
            "narrowing": "delayed_reply",
            "threshold_crossed": "recognition_claim",
            "symbolic_only": "exit_threat",
        }.get(threshold_state)
        if not marker:
            return []
        updates = [
            self._delta(
                state,
                process_id,
                marker,
                pressure * 0.15,
                f"action reversibility state {threshold_state} makes {marker} more salient",
                refs,
                [event.event_type],
            )
        ]
        if threshold_state in {"threshold_crossed", "symbolic_only"}:
            for other in set(state.processes) - {process_id}:
                updates.append(
                    self._delta(
                        state,
                        other,
                        "recognition_claim",
                        pressure * 0.08,
                        "crossed reversibility threshold makes counter-recognition salient",
                        refs,
                        [event.event_type],
                    )
                )
        return updates

    def _epistemic_updates(
        self,
        state: SimulationState,
        event: Event,
        refs: list[str],
    ) -> list[RelevanceShift]:
        boundary_type = str(event.payload.get("boundary_type", ""))
        pressure = self._payload_float(event, "pressure")
        if pressure <= 0.0:
            return []
        marker = {
            "case_knowledge_asymmetry": "recognition_claim",
            "testimony_disclosure_risk": "public_exposure",
            "public_private_knowledge_split": "public_exposure",
            "unspeakable_fact_boundary": "double_bind",
        }.get(boundary_type)
        if not marker:
            return []
        updates = [
            self._delta(
                state,
                process_id,
                marker,
                pressure * 0.14,
                f"epistemic boundary {boundary_type} makes {marker} salient",
                refs,
                [event.event_type],
            )
            for process_id in state.processes
        ]
        if boundary_type in {"case_knowledge_asymmetry", "unspeakable_fact_boundary"}:
            updates.append(
                self._delta(
                    state,
                    "p1" if "p1" in state.processes else next(iter(state.processes)),
                    "exit_threat",
                    pressure * 0.07,
                    "knowledge boundary makes refusal or withdrawal more salient",
                    refs,
                    [event.event_type],
                )
            )
        return updates

    def _coalesce(self, updates: list[RelevanceShift]) -> list[RelevanceShift]:
        grouped: dict[tuple[str, str, str], list[RelevanceShift]] = {}
        decay_reason = "relevance salience decays when not renewed"
        for update in updates:
            if update.previous_value == update.new_value:
                continue
            kind = "decay" if update.reason == decay_reason else "evidence"
            grouped.setdefault((update.process_id, update.marker, kind), []).append(update)
        coalesced: list[RelevanceShift] = []
        for (_process_id, _marker, kind), items in grouped.items():
            first = items[0]
            last = items[-1]
            reason = decay_reason if kind == "decay" else (
                first.reason if len(items) == 1 else "relevance landscape updated from tick evidence"
            )
            coalesced.append(
                RelevanceShift(
                    process_id=first.process_id,
                    marker=first.marker,
                    previous_value=first.previous_value,
                    new_value=last.new_value,
                    reason=reason,
                    causal_refs=sorted({ref for item in items for ref in item.causal_refs}),
                    evidence_event_types=sorted({event_type for item in items for event_type in item.evidence_event_types}),
                )
            )
        return coalesced

    def _mirror_to_process_triggers(self, state: SimulationState, updates: list[RelevanceShift]) -> None:
        for update in updates:
            process = state.processes.get(update.process_id)
            if not process:
                continue
            process.relevance_triggers[update.marker] = max(
                process.relevance_triggers.get(update.marker, 0.0),
                update.new_value,
            )

    def _delta(
        self,
        state: SimulationState,
        process_id: str,
        marker: str,
        delta: float,
        reason: str,
        refs: list[str],
        event_types: list[str],
    ) -> RelevanceShift:
        previous = float(state.relation_metrics.get(self._key(process_id, marker), 0.0))
        return self._set(state, process_id, marker, previous + delta, reason, refs, event_types)

    def _set(
        self,
        state: SimulationState,
        process_id: str,
        marker: str,
        value: float,
        reason: str,
        refs: list[str],
        event_types: list[str],
    ) -> RelevanceShift:
        key = self._key(process_id, marker)
        previous = float(state.relation_metrics.get(key, 0.0))
        new_value = clamp(value)
        state.relation_metrics[key] = new_value
        return RelevanceShift(
            process_id=process_id,
            marker=marker,
            previous_value=round(previous, 4),
            new_value=new_value,
            reason=reason,
            causal_refs=sorted(set(refs)),
            evidence_event_types=sorted(set(event_types)),
        )

    def _key(self, process_id: str, marker: str) -> str:
        return f"{self.PREFIX}{process_id}.{marker}"

    def _source_from_affordance(self, affordance_id: str) -> str:
        if affordance_id in {"unacknowledged_contribution_claim", "material_pressure_intrusion"}:
            return "p1"
        return "p2"

    def _payload_float(self, event: Event, key: str) -> float:
        try:
            return clamp(float(event.payload.get(key, 0.0)))
        except (TypeError, ValueError):
            return 0.0
