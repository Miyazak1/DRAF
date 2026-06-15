from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from rpf.core.events import Event
from rpf.core.models import SimulationState, clamp


@dataclass(frozen=True)
class FrameDefinitionUpdate:
    frame_type: str
    previous_value: float
    new_value: float
    reason: str
    causal_refs: list[str]
    evidence_event_types: list[str]

    def payload(self) -> dict[str, Any]:
        return {
            "frame_type": self.frame_type,
            "frame_key": self.key,
            "previous_value": self.previous_value,
            "new_value": self.new_value,
            "delta": round(self.new_value - self.previous_value, 4),
            "reason": self.reason,
            "caused_by_events": self.causal_refs,
            "evidence_event_types": self.evidence_event_types,
        }

    @property
    def key(self) -> str:
        return f"frame_definition.{self.frame_type}"


class InteractionFrameEngine:
    """Sediment what-kind-of-situation-this-is definitions.

    Frames are not scenes written by a narrator and not private interpretations.
    They are event-sourced definitions of the current interaction form: whether
    conduct is becoming debt accounting, repair, avoidance, public performance,
    care/control, double bind, material accounting, or recognition trial.
    """

    PREFIX = "frame_definition."

    def update(self, state: SimulationState, local_events: list[Event]) -> list[FrameDefinitionUpdate]:
        updates: list[FrameDefinitionUpdate] = []
        updates.extend(self._decay(state, local_events))
        updates.extend(self._event_updates(state, local_events))
        return self._coalesce(updates)

    def _decay(self, state: SimulationState, local_events: list[Event]) -> list[FrameDefinitionUpdate]:
        refs = [event.event_id for event in local_events if event.event_type == "TickStartedEvent"][-1:]
        refs = refs or [event.event_id for event in local_events[:1]]
        updates: list[FrameDefinitionUpdate] = []
        for key, value in list(state.relation_metrics.items()):
            if not key.startswith(self.PREFIX):
                continue
            frame_type = key.removeprefix(self.PREFIX)
            current = float(value)
            if current <= 0.0001:
                continue
            updates.append(
                self._set(
                    state,
                    frame_type,
                    current - min(current, 0.003),
                    "frame definition decays when not renewed by interaction",
                    refs,
                    ["TickStartedEvent"],
                )
            )
        return updates

    def _event_updates(self, state: SimulationState, local_events: list[Event]) -> list[FrameDefinitionUpdate]:
        updates: list[FrameDefinitionUpdate] = []
        for event in local_events:
            event_type = event.event_type
            refs = sorted(set([event.event_id] + list(event.causal_refs)))
            if event_type == "AffordanceSelectionEvent":
                affordance_id = str(event.payload.get("affordance_id", ""))
                score = self._payload_float(event, "score")
                frame_type = self._frame_from_affordance(affordance_id)
                if frame_type:
                    updates.append(
                        self._delta(
                            state,
                            frame_type,
                            max(0.006, score * 0.018),
                            f"selected affordance {affordance_id} defines the situation as {frame_type}",
                            refs,
                            [event_type],
                        )
                    )
            elif event_type == "ExpressionSelectionEvent":
                expression_mode = str(event.payload.get("expression_mode", ""))
                updates.extend(self._expression_updates(state, expression_mode, refs, event_type))
            elif event_type == "RecognitionEvent":
                result = str(event.payload.get("result", ""))
                updates.extend(self._recognition_updates(state, result, refs, event_type))
            elif event_type == "NormativePressureEvent":
                norm_type = str(event.payload.get("norm_type", ""))
                delta = max(0.0, self._payload_float(event, "delta"))
                updates.extend(self._normative_updates(state, norm_type, delta, refs, event_type))
            elif event_type == "RelationSedimentationEvent":
                metric = str(event.payload.get("metric", ""))
                delta = max(0.0, self._payload_float(event, "delta"))
                updates.extend(self._relation_updates(state, metric, delta, refs, event_type))
            elif event_type == "FieldUpdateEvent":
                path = str(event.payload.get("changed_field_path", ""))
                delta = max(0.0, self._payload_float(event, "delta"))
                if "audience_pressure" in path or "imagined_audience" in path:
                    updates.append(
                        self._delta(
                            state,
                            "public_performance",
                            max(0.004, delta * 0.35),
                            "field audience pressure defines the interaction as publicly observable",
                            refs,
                            [event_type],
                        )
                    )
                if "material_pressures" in path or "spatial_constraints" in path:
                    updates.append(
                        self._delta(
                            state,
                            "material_accounting",
                            max(0.004, delta * 0.28),
                            "field pressure defines the interaction through material accounting",
                            refs,
                            [event_type],
                        )
                    )
            elif event_type == "RPPCompositionEvent":
                composition_id = str(event.payload.get("composition_id", ""))
                score = self._payload_float(event, "composition_score")
                frame_type = self._frame_from_composition(composition_id)
                if frame_type:
                    updates.append(
                        self._delta(
                            state,
                            frame_type,
                            max(0.006, score * 0.02),
                            f"RPP composition {composition_id} stabilizes {frame_type} as situation definition",
                            refs,
                            [event_type],
                        )
                    )
        return [update for update in updates if update.previous_value != update.new_value]

    def _expression_updates(
        self,
        state: SimulationState,
        expression_mode: str,
        refs: list[str],
        event_type: str,
    ) -> list[FrameDefinitionUpdate]:
        mapping = {
            "silence": ("avoidance_scene", 0.014),
            "timing_distortion": ("avoidance_scene", 0.01),
            "gesture": ("avoidance_scene", 0.008),
            "public_performance": ("public_performance", 0.016),
            "tonal_shift": ("recognition_trial", 0.01),
        }
        spec = mapping.get(expression_mode)
        if not spec:
            return []
        frame_type, delta = spec
        return [
            self._delta(
                state,
                frame_type,
                delta,
                f"expression mode {expression_mode} defines what kind of situation this is",
                refs,
                [event_type],
            )
        ]

    def _recognition_updates(
        self,
        state: SimulationState,
        result: str,
        refs: list[str],
        event_type: str,
    ) -> list[FrameDefinitionUpdate]:
        if result in {"refused", "misunderstood", "displaced", "postponed", "unspeakable"}:
            return [
                self._delta(
                    state,
                    "recognition_trial",
                    0.018,
                    f"recognition result {result} defines the scene as a test of recognition",
                    refs,
                    [event_type],
                ),
                self._delta(
                    state,
                    "avoidance_scene",
                    0.01,
                    f"recognition result {result} keeps avoidance available as situation definition",
                    refs,
                    [event_type],
                ),
            ]
        if result in {"granted", "partial"}:
            return [
                self._delta(
                    state,
                    "repair_scene",
                    0.014,
                    f"recognition result {result} defines the situation as partially repairable",
                    refs,
                    [event_type],
                )
            ]
        return []

    def _normative_updates(
        self,
        state: SimulationState,
        norm_type: str,
        delta: float,
        refs: list[str],
        event_type: str,
    ) -> list[FrameDefinitionUpdate]:
        if delta <= 0.0:
            return []
        mapping = {
            "claim_entitlement": "recognition_trial",
            "repair_obligation": "repair_scene",
            "reciprocity_obligation": "debt_accounting",
            "public_face_obligation": "public_performance",
            "legitimacy_contestation": "recognition_trial",
            "exit_justification": "avoidance_scene",
            "mutual_obligation": "care_control",
            "irreversible_precedent": "double_bind",
        }
        frame_type = mapping.get(norm_type)
        if not frame_type:
            return []
        return [
            self._delta(
                state,
                frame_type,
                delta * 0.34,
                f"normative {norm_type} pressure defines the interaction as {frame_type}",
                refs,
                [event_type],
            )
        ]

    def _relation_updates(
        self,
        state: SimulationState,
        metric: str,
        delta: float,
        refs: list[str],
        event_type: str,
    ) -> list[FrameDefinitionUpdate]:
        if delta <= 0.0:
            return []
        mapping = {
            "relation_sediment.recognition_debt": "recognition_trial",
            "relation_sediment.repair_access_narrowing": "avoidance_scene",
            "relation_sediment.symbolic_accounting_load": "debt_accounting",
            "relation_sediment.future_lock_load": "double_bind",
            "relation_sediment.shared_fate_load": "care_control",
            "relation_sediment.public_definition_load": "public_performance",
            "relation_sediment.asymmetry_load": "care_control",
            "relation_sediment.memory_saturation": "recognition_trial",
        }
        frame_type = mapping.get(metric)
        if not frame_type:
            return []
        return [
            self._delta(
                state,
                frame_type,
                delta * 0.26,
                f"{metric} sediments into {frame_type} situation definition",
                refs,
                [event_type],
            )
        ]

    def _frame_from_affordance(self, affordance_id: str) -> str | None:
        return {
            "mediated_delay": "avoidance_scene",
            "practical_repair_offer": "repair_scene",
            "unacknowledged_contribution_claim": "debt_accounting",
            "public_performance": "public_performance",
            "care_intervention": "care_control",
            "double_bind_response": "double_bind",
            "material_pressure_intrusion": "material_accounting",
            "embodied_avoidance": "avoidance_scene",
        }.get(affordance_id)

    def _frame_from_composition(self, composition_id: str) -> str | None:
        return {
            "debt_lock": "debt_accounting",
            "credit_recognition_lock": "debt_accounting",
            "recognition_trap": "recognition_trial",
            "anxious_silence_circuit": "avoidance_scene",
            "pursuit_withdrawal_lock": "avoidance_scene",
            "care_bind_double_bind": "double_bind",
            "public_face_split": "public_performance",
            "public_mask_split": "public_performance",
        }.get(composition_id)

    def _coalesce(self, updates: list[FrameDefinitionUpdate]) -> list[FrameDefinitionUpdate]:
        grouped: dict[tuple[str, str], list[FrameDefinitionUpdate]] = {}
        decay_reason = "frame definition decays when not renewed by interaction"
        for update in updates:
            if update.previous_value == update.new_value:
                continue
            kind = "decay" if update.reason == decay_reason else "evidence"
            grouped.setdefault((update.frame_type, kind), []).append(update)
        coalesced: list[FrameDefinitionUpdate] = []
        for (_frame_type, kind), items in grouped.items():
            first = items[0]
            last = items[-1]
            reason = decay_reason if kind == "decay" else (
                first.reason if len(items) == 1 else "frame definition updated from tick evidence"
            )
            coalesced.append(
                FrameDefinitionUpdate(
                    frame_type=first.frame_type,
                    previous_value=first.previous_value,
                    new_value=last.new_value,
                    reason=reason,
                    causal_refs=sorted({ref for item in items for ref in item.causal_refs}),
                    evidence_event_types=sorted({event_type for item in items for event_type in item.evidence_event_types}),
                )
            )
        return coalesced

    def _delta(
        self,
        state: SimulationState,
        frame_type: str,
        delta: float,
        reason: str,
        refs: list[str],
        event_types: list[str],
    ) -> FrameDefinitionUpdate:
        previous = float(state.relation_metrics.get(self._key(frame_type), 0.0))
        return self._set(state, frame_type, previous + delta, reason, refs, event_types)

    def _set(
        self,
        state: SimulationState,
        frame_type: str,
        value: float,
        reason: str,
        refs: list[str],
        event_types: list[str],
    ) -> FrameDefinitionUpdate:
        key = self._key(frame_type)
        previous = float(state.relation_metrics.get(key, 0.0))
        new_value = clamp(value)
        state.relation_metrics[key] = new_value
        return FrameDefinitionUpdate(
            frame_type=frame_type,
            previous_value=round(previous, 4),
            new_value=new_value,
            reason=reason,
            causal_refs=sorted(set(refs)),
            evidence_event_types=sorted(set(event_types)),
        )

    def _key(self, frame_type: str) -> str:
        return f"{self.PREFIX}{frame_type}"

    def _payload_float(self, event: Event, key: str) -> float:
        try:
            return clamp(float(event.payload.get(key, 0.0)))
        except (TypeError, ValueError):
            return 0.0
