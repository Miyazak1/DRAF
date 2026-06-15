from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from rpf.core.events import Event
from rpf.core.models import SimulationState, clamp


@dataclass(frozen=True)
class PositionUpdate:
    process_id: str
    position_type: str
    previous_value: float
    new_value: float
    reason: str
    causal_refs: list[str]
    evidence_event_types: list[str]

    def payload(self) -> dict[str, Any]:
        return {
            "process_id": self.process_id,
            "position_type": self.position_type,
            "position_key": self.key,
            "previous_value": self.previous_value,
            "new_value": self.new_value,
            "delta": round(self.new_value - self.previous_value, 4),
            "reason": self.reason,
            "caused_by_events": self.causal_refs,
            "evidence_event_types": self.evidence_event_types,
        }

    @property
    def key(self) -> str:
        return f"position_field.{self.process_id}.{self.position_type}"


class PositioningEngine:
    """Sediment relation-generated process positions.

    Positions are not roles assigned by the author and not personality labels.
    They are event-sourced places a process is pushed into by claims, repair
    failures, public exposure, care/control, double binds, and relation history.
    """

    PREFIX = "position_field."

    def update(self, state: SimulationState, local_events: list[Event]) -> list[PositionUpdate]:
        updates: list[PositionUpdate] = []
        updates.extend(self._decay(state, local_events))
        updates.extend(self._event_updates(state, local_events))
        return self._coalesce(updates)

    def _decay(self, state: SimulationState, local_events: list[Event]) -> list[PositionUpdate]:
        refs = [event.event_id for event in local_events if event.event_type == "TickStartedEvent"][-1:]
        refs = refs or [event.event_id for event in local_events[:1]]
        updates: list[PositionUpdate] = []
        for key, value in list(state.relation_metrics.items()):
            if not key.startswith(self.PREFIX):
                continue
            parts = key.split(".", 2)
            if len(parts) != 3:
                continue
            _, process_id, position_type = parts
            current = float(value)
            if current <= 0.0001:
                continue
            updates.append(
                self._set(
                    state,
                    process_id,
                    position_type,
                    current - min(current, 0.003),
                    "position pressure decays when not renewed",
                    refs,
                    ["TickStartedEvent"],
                )
            )
        return updates

    def _event_updates(self, state: SimulationState, local_events: list[Event]) -> list[PositionUpdate]:
        updates: list[PositionUpdate] = []
        for event in local_events:
            event_type = event.event_type
            refs = sorted(set([event.event_id] + list(event.causal_refs)))
            if event_type == "RecognitionEvent":
                updates.extend(self._recognition_updates(state, event, refs))
            elif event_type in {"AvoidanceEvent", "DisplacementEvent", "MisrecognitionEvent"}:
                p1, p2 = self._pair(state)
                updates.append(self._delta(state, p1, "claimant", 0.014, f"{event_type} keeps one process in claimant position", refs, [event_type]))
                updates.append(self._delta(state, p2, "defender", 0.014, f"{event_type} keeps the other process in defender position", refs, [event_type]))
            elif event_type == "RepairEvent":
                for process_id in state.processes:
                    updates.append(self._delta(state, process_id, "repair_partner", 0.012, "repair opens a repair-partner position", refs, [event_type]))
                    updates.append(self._delta(state, process_id, "defender", -0.01, "repair lowers defensive position pressure", refs, [event_type]))
            elif event_type == "NormativePressureEvent":
                updates.extend(self._normative_updates(state, event, refs))
            elif event_type == "FrameDefinitionEvent":
                updates.extend(self._frame_updates(state, event, refs))
            elif event_type == "RelevanceShiftEvent":
                updates.extend(self._relevance_updates(state, event, refs))
            elif event_type == "RelationSedimentationEvent":
                updates.extend(self._relation_updates(state, event, refs))
            elif event_type == "RPPCompositionEvent":
                updates.extend(self._composition_updates(state, event, refs))
            elif event_type == "BindingUpdatedEvent":
                process_ids = event.payload.get("process_ids", [])
                if not process_ids:
                    process_ids = list(state.processes)
                for process_id in process_ids:
                    if process_id in state.processes:
                        updates.append(self._delta(state, process_id, "bound_party", 0.006, "binding evolution makes co-presence position salient", refs, [event_type]))
        return [update for update in updates if update.previous_value != update.new_value]

    def _recognition_updates(
        self,
        state: SimulationState,
        event: Event,
        refs: list[str],
    ) -> list[PositionUpdate]:
        holder = str(event.payload.get("holder", "p1"))
        demanded_from = str(event.payload.get("demanded_from", self._other(holder, state)))
        result = str(event.payload.get("result", ""))
        updates: list[PositionUpdate] = []
        if result in {"refused", "misunderstood", "displaced", "postponed", "unspeakable"}:
            updates.append(self._delta(state, holder, "claimant", 0.024, f"recognition result {result} stabilizes claimant position", refs, [event.event_type]))
            updates.append(self._delta(state, demanded_from, "defender", 0.02, f"recognition result {result} stabilizes defender position", refs, [event.event_type]))
        if result in {"granted", "partial"}:
            updates.append(self._delta(state, holder, "claimant", -0.014, f"recognition result {result} reduces claimant pressure", refs, [event.event_type]))
            updates.append(self._delta(state, demanded_from, "repair_partner", 0.018, f"recognition result {result} opens repair-partner position", refs, [event.event_type]))
        return updates

    def _normative_updates(
        self,
        state: SimulationState,
        event: Event,
        refs: list[str],
    ) -> list[PositionUpdate]:
        process_id = str(event.payload.get("process_id", "p1"))
        target = str(event.payload.get("target_process_id", self._other(process_id, state)))
        norm_type = str(event.payload.get("norm_type", ""))
        delta = max(0.0, self._payload_float(event, "delta"))
        if delta <= 0.0:
            return []
        updates: list[PositionUpdate] = []
        if norm_type in {"claim_entitlement", "reciprocity_obligation"}:
            updates.append(self._delta(state, process_id, "claimant", delta * 0.45, f"normative {norm_type} gives standing to claim", refs, [event.event_type]))
            updates.append(self._delta(state, target, "debtor", delta * 0.32, f"normative {norm_type} places target under debt position", refs, [event.event_type]))
        elif norm_type == "repair_obligation":
            updates.append(self._delta(state, process_id, "repair_partner", delta * 0.32, "repair obligation creates repair-partner pressure", refs, [event.event_type]))
        elif norm_type == "public_face_obligation":
            updates.append(self._delta(state, process_id, "public_performer", delta * 0.38, "public face obligation places process in public performer position", refs, [event.event_type]))
        elif norm_type == "exit_justification":
            updates.append(self._delta(state, process_id, "withdrawer", delta * 0.36, "exit justification makes withdrawal position available", refs, [event.event_type]))
        elif norm_type == "legitimacy_contestation":
            updates.append(self._delta(state, process_id, "defender", delta * 0.36, "legitimacy contestation makes defensive position available", refs, [event.event_type]))
        return updates

    def _frame_updates(
        self,
        state: SimulationState,
        event: Event,
        refs: list[str],
    ) -> list[PositionUpdate]:
        frame_type = str(event.payload.get("frame_type", ""))
        delta = max(0.0, self._payload_float(event, "delta"))
        if delta <= 0.0:
            return []
        p1, p2 = self._pair(state)
        specs: dict[str, list[tuple[str, str, float]]] = {
            "debt_accounting": [(p1, "claimant", 0.28), (p2, "debtor", 0.24)],
            "repair_scene": [(p1, "repair_partner", 0.2), (p2, "repair_partner", 0.2)],
            "avoidance_scene": [(p2, "withdrawer", 0.24), (p1, "claimant", 0.16)],
            "public_performance": [(p1, "public_performer", 0.2), (p2, "public_performer", 0.22)],
            "care_control": [(p2, "caretaker", 0.24), (p1, "controlled", 0.2)],
            "double_bind": [(p1, "trapped_party", 0.24), (p2, "defender", 0.18)],
            "material_accounting": [(p1, "claimant", 0.16), (p2, "debtor", 0.12)],
        }
        return [
            self._delta(state, process_id, position_type, delta * weight, f"frame {frame_type} organizes relation positions", refs, [event.event_type])
            for process_id, position_type, weight in specs.get(frame_type, [])
            if process_id in state.processes
        ]

    def _relevance_updates(
        self,
        state: SimulationState,
        event: Event,
        refs: list[str],
    ) -> list[PositionUpdate]:
        process_id = str(event.payload.get("process_id", "p1"))
        marker = str(event.payload.get("marker", ""))
        delta = max(0.0, self._payload_float(event, "delta"))
        mapping = {
            "recognition_claim": "claimant",
            "delayed_reply": "withdrawer",
            "public_exposure": "public_performer",
            "being_controlled": "controlled",
            "double_bind": "trapped_party",
            "repair_opening": "repair_partner",
            "exit_threat": "defender",
        }
        position_type = mapping.get(marker)
        if not position_type or delta <= 0.0:
            return []
        return [self._delta(state, process_id, position_type, delta * 0.3, f"relevance marker {marker} makes position {position_type} salient", refs, [event.event_type])]

    def _relation_updates(
        self,
        state: SimulationState,
        event: Event,
        refs: list[str],
    ) -> list[PositionUpdate]:
        metric = str(event.payload.get("metric", ""))
        delta = max(0.0, self._payload_float(event, "delta"))
        if delta <= 0.0:
            return []
        p1, p2 = self._pair(state)
        specs: dict[str, list[tuple[str, str, float]]] = {
            "relation_sediment.recognition_debt": [(p1, "claimant", 0.24), (p2, "defender", 0.12)],
            "relation_sediment.symbolic_accounting_load": [(p1, "claimant", 0.2), (p2, "debtor", 0.2)],
            "relation_sediment.repair_access_narrowing": [(p2, "withdrawer", 0.18)],
            "relation_sediment.public_definition_load": [(p1, "public_performer", 0.16), (p2, "public_performer", 0.18)],
            "relation_sediment.asymmetry_load": [(p2, "caretaker", 0.16), (p1, "controlled", 0.16)],
            "relation_sediment.future_lock_load": [(p1, "trapped_party", 0.16), (p2, "trapped_party", 0.16)],
        }
        return [
            self._delta(state, process_id, position_type, delta * weight, f"{metric} sediments into position pressure", refs, [event.event_type])
            for process_id, position_type, weight in specs.get(metric, [])
            if process_id in state.processes
        ]

    def _composition_updates(
        self,
        state: SimulationState,
        event: Event,
        refs: list[str],
    ) -> list[PositionUpdate]:
        composition = str(event.payload.get("composition_id", ""))
        score = self._payload_float(event, "composition_score")
        p1, p2 = self._pair(state)
        specs: dict[str, list[tuple[str, str, float]]] = {
            "debt_lock": [(p1, "claimant", 0.018), (p2, "debtor", 0.018)],
            "credit_recognition_lock": [(p1, "claimant", 0.018), (p2, "defender", 0.014)],
            "recognition_trap": [(p1, "claimant", 0.016), (p2, "defender", 0.016)],
            "pursuit_withdrawal_lock": [(p1, "claimant", 0.014), (p2, "withdrawer", 0.018)],
            "care_bind_double_bind": [(p2, "caretaker", 0.02), (p1, "trapped_party", 0.018)],
            "public_face_split": [(p1, "public_performer", 0.016), (p2, "public_performer", 0.018)],
        }
        return [
            self._delta(state, process_id, position_type, score * weight, f"RPP composition {composition} stabilizes position {position_type}", refs, [event.event_type])
            for process_id, position_type, weight in specs.get(composition, [])
            if process_id in state.processes
        ]

    def _coalesce(self, updates: list[PositionUpdate]) -> list[PositionUpdate]:
        grouped: dict[tuple[str, str, str], list[PositionUpdate]] = {}
        decay_reason = "position pressure decays when not renewed"
        for update in updates:
            if update.previous_value == update.new_value:
                continue
            kind = "decay" if update.reason == decay_reason else "evidence"
            grouped.setdefault((update.process_id, update.position_type, kind), []).append(update)
        coalesced: list[PositionUpdate] = []
        for (_process_id, _position_type, kind), items in grouped.items():
            first = items[0]
            last = items[-1]
            reason = decay_reason if kind == "decay" else (
                first.reason if len(items) == 1 else "position field updated from tick evidence"
            )
            coalesced.append(
                PositionUpdate(
                    process_id=first.process_id,
                    position_type=first.position_type,
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
        process_id: str,
        position_type: str,
        delta: float,
        reason: str,
        refs: list[str],
        event_types: list[str],
    ) -> PositionUpdate:
        previous = float(state.relation_metrics.get(self._key(process_id, position_type), 0.0))
        return self._set(state, process_id, position_type, previous + delta, reason, refs, event_types)

    def _set(
        self,
        state: SimulationState,
        process_id: str,
        position_type: str,
        value: float,
        reason: str,
        refs: list[str],
        event_types: list[str],
    ) -> PositionUpdate:
        key = self._key(process_id, position_type)
        previous = float(state.relation_metrics.get(key, 0.0))
        new_value = clamp(value)
        state.relation_metrics[key] = new_value
        return PositionUpdate(
            process_id=process_id,
            position_type=position_type,
            previous_value=round(previous, 4),
            new_value=new_value,
            reason=reason,
            causal_refs=sorted(set(refs)),
            evidence_event_types=sorted(set(event_types)),
        )

    def _key(self, process_id: str, position_type: str) -> str:
        return f"{self.PREFIX}{process_id}.{position_type}"

    def _pair(self, state: SimulationState) -> tuple[str, str]:
        process_ids = list(state.processes)
        if len(process_ids) >= 2:
            return process_ids[0], process_ids[1]
        if process_ids:
            return process_ids[0], process_ids[0]
        return "p1", "p2"

    def _other(self, process_id: str, state: SimulationState) -> str:
        for candidate in state.processes:
            if candidate != process_id:
                return candidate
        return process_id

    def _payload_float(self, event: Event, key: str) -> float:
        try:
            return clamp(float(event.payload.get(key, 0.0)))
        except (TypeError, ValueError):
            return 0.0
