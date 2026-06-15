from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from rpf.core.events import Event
from rpf.core.models import SimulationState, clamp


@dataclass(frozen=True)
class NormativePressureUpdate:
    process_id: str
    target_process_id: str
    norm_type: str
    previous_value: float
    new_value: float
    reason: str
    causal_refs: list[str]

    def payload(self) -> dict[str, Any]:
        return {
            "process_id": self.process_id,
            "target_process_id": self.target_process_id,
            "norm_type": self.norm_type,
            "norm_key": self.key,
            "previous_value": self.previous_value,
            "new_value": self.new_value,
            "delta": round(self.new_value - self.previous_value, 4),
            "reason": self.reason,
            "caused_by_events": self.causal_refs,
        }

    @property
    def key(self) -> str:
        return f"norm_pressure.{self.process_id}.{self.target_process_id}.{self.norm_type}"


class NormativePressureEngine:
    """Project interaction history into relation-specific normative pressures.

    This is not a morality module and not a hidden value system. It records when
    observable interaction makes a claim, refusal, repair, role, or public face
    rule become harder to ignore as a social form.
    """

    PREFIX = "norm_pressure."

    def update(self, state: SimulationState, local_events: list[Event]) -> list[NormativePressureUpdate]:
        updates: list[NormativePressureUpdate] = []
        updates.extend(self._decay(state, local_events))
        updates.extend(self._field_updates(state, local_events))
        updates.extend(self._recognition_updates(state, local_events))
        updates.extend(self._repair_updates(state, local_events))
        updates.extend(self._classification_updates(state, local_events))
        updates.extend(self._expectation_updates(state, local_events))
        updates.extend(self._account_updates(state, local_events))
        updates.extend(self._relation_updates(state, local_events))
        return [update for update in updates if update.previous_value != update.new_value]

    def _decay(self, state: SimulationState, local_events: list[Event]) -> list[NormativePressureUpdate]:
        refs = [event.event_id for event in local_events if event.event_type == "TickStartedEvent"][-1:]
        refs = refs or [event.event_id for event in local_events[:1]]
        updates: list[NormativePressureUpdate] = []
        for key, value in list(state.relation_metrics.items()):
            if not key.startswith(self.PREFIX):
                continue
            parts = key.split(".", 3)
            if len(parts) != 4:
                continue
            _, process_id, target_process_id, norm_type = parts
            current = float(value)
            if current <= 0.0001:
                continue
            updates.append(
                self._set(
                    state,
                    process_id,
                    target_process_id,
                    norm_type,
                    current - min(current, 0.0025),
                    "normative pressure decays when not socially renewed",
                    refs,
                )
            )
        return updates

    def _field_updates(self, state: SimulationState, local_events: list[Event]) -> list[NormativePressureUpdate]:
        updates: list[NormativePressureUpdate] = []
        audience = max(state.field_state.audience_pressure.values(), default=0.0)
        for event in local_events:
            if event.event_type != "FieldPressureEvent":
                continue
            intensity = self._payload_float(event, "intensity")
            if intensity <= 0.05:
                continue
            p1, p2 = self._pair(state)
            updates.append(
                self._delta(
                    state,
                    p1,
                    p2,
                    "reciprocity_obligation",
                    intensity * 0.006,
                    "material pressure makes contribution legible as reciprocal obligation",
                    [event.event_id],
                )
            )
            updates.append(
                self._delta(
                    state,
                    p2,
                    p1,
                    "repair_obligation",
                    intensity * 0.004,
                    "material pressure makes non-response harder to justify",
                    [event.event_id],
                )
            )
            if audience > 0.05:
                for process_id, target_process_id in [(p1, p2), (p2, p1)]:
                    updates.append(
                        self._delta(
                            state,
                            process_id,
                            target_process_id,
                            "public_face_obligation",
                            audience * intensity * 0.008,
                            "audience pressure turns conduct into public face obligation",
                            [event.event_id],
                        )
                    )
        return updates

    def _recognition_updates(self, state: SimulationState, local_events: list[Event]) -> list[NormativePressureUpdate]:
        updates: list[NormativePressureUpdate] = []
        for event in local_events:
            if event.event_type != "RecognitionEvent":
                continue
            holder = str(event.payload.get("holder", "p1"))
            demanded_from = str(event.payload.get("demanded_from", self._other(holder, state)))
            result = str(event.payload.get("result", ""))
            if result in {"refused", "misunderstood", "displaced", "postponed", "unspeakable"}:
                updates.append(
                    self._delta(
                        state,
                        holder,
                        demanded_from,
                        "claim_entitlement",
                        0.022,
                        f"recognition result {result} makes the claim harder to drop as illegitimate",
                        [event.event_id],
                    )
                )
                updates.append(
                    self._delta(
                        state,
                        demanded_from,
                        holder,
                        "repair_obligation",
                        0.018,
                        f"recognition result {result} sediments an obligation to answer or repair",
                        [event.event_id],
                    )
                )
            if result in {"refused", "unspeakable"}:
                updates.append(
                    self._delta(
                        state,
                        demanded_from,
                        holder,
                        "legitimacy_contestation",
                        0.018,
                        f"recognition result {result} contests who has standing to demand what",
                        [event.event_id],
                    )
                )
            if result in {"granted", "partial"}:
                updates.append(
                    self._delta(
                        state,
                        demanded_from,
                        holder,
                        "repair_obligation",
                        -0.018,
                        f"recognition result {result} discharges part of the repair obligation",
                        [event.event_id],
                    )
                )
                updates.append(
                    self._delta(
                        state,
                        holder,
                        demanded_from,
                        "legitimacy_contestation",
                        -0.012,
                        f"recognition result {result} lowers legitimacy contestation",
                        [event.event_id],
                    )
                )
        return updates

    def _repair_updates(self, state: SimulationState, local_events: list[Event]) -> list[NormativePressureUpdate]:
        updates: list[NormativePressureUpdate] = []
        p1, p2 = self._pair(state)
        for event in local_events:
            if event.event_type in {"AvoidanceEvent", "DisplacementEvent", "MisrecognitionEvent"}:
                updates.append(
                    self._delta(
                        state,
                        p1,
                        p2,
                        "claim_entitlement",
                        0.014,
                        f"{event.event_type} makes the unaddressed claim more normatively available",
                        [event.event_id],
                    )
                )
                updates.append(
                    self._delta(
                        state,
                        p2,
                        p1,
                        "repair_obligation",
                        0.016,
                        f"{event.event_type} leaves a repair obligation in the scene",
                        [event.event_id],
                    )
                )
            elif event.event_type == "RepairEvent":
                for process_id, target_process_id in [(p1, p2), (p2, p1)]:
                    updates.append(
                        self._delta(
                            state,
                            process_id,
                            target_process_id,
                            "legitimacy_contestation",
                            -0.01,
                            "repair makes the conflict less dependent on contested standing",
                            [event.event_id],
                        )
                    )
        return updates

    def _classification_updates(self, state: SimulationState, local_events: list[Event]) -> list[NormativePressureUpdate]:
        updates: list[NormativePressureUpdate] = []
        p1, p2 = self._pair(state)
        for event in local_events:
            if event.event_type == "OperativeClassificationEvent":
                label = str(event.payload.get("label", ""))
                target = str(event.payload.get("target_process_id", p2))
                other = self._other(target, state)
                legitimacy = self._payload_float(event, "legitimacy")
                norm_type = self._classification_norm(label)
                if norm_type:
                    updates.append(
                        self._delta(
                            state,
                            other,
                            target,
                            norm_type,
                            max(0.01, legitimacy * 0.035),
                            f"operative label {label} gives the relation a normative reading",
                            [event.event_id],
                        )
                    )
                updates.append(
                    self._delta(
                        state,
                        target,
                        other,
                        "legitimacy_contestation",
                        max(0.008, legitimacy * 0.025),
                        f"operative label {label} constrains later self-justification",
                        [event.event_id],
                    )
                )
            elif event.event_type == "IrreversibilityEvent":
                for process_id, target_process_id in [(p1, p2), (p2, p1)]:
                    updates.append(
                        self._delta(
                            state,
                            process_id,
                            target_process_id,
                            "irreversible_precedent",
                            0.02,
                            "irreversibility turns a local event into precedent",
                            [event.event_id],
                        )
                    )
        return updates

    def _expectation_updates(self, state: SimulationState, local_events: list[Event]) -> list[NormativePressureUpdate]:
        updates: list[NormativePressureUpdate] = []
        for event in local_events:
            if event.event_type != "ExpectationSedimentationEvent":
                continue
            delta = self._payload_float(event, "delta")
            if delta <= 0.0:
                continue
            key = str(event.payload.get("expectation_key", ""))
            parts = key.split(".")
            process_id = parts[1] if len(parts) >= 4 else "p1"
            target_process_id = parts[2] if len(parts) >= 4 else self._other(process_id, state)
            if "refusal_expectation" in key or "misrecognition_expectation" in key:
                updates.append(
                    self._delta(
                        state,
                        process_id,
                        target_process_id,
                        "claim_entitlement",
                        delta * 0.32,
                        "expected refusal or misrecognition makes direct claiming normatively risky but persistent",
                        [event.event_id],
                    )
                )
            if "repair_avoidance_expectation" in key:
                updates.append(
                    self._delta(
                        state,
                        target_process_id,
                        process_id,
                        "repair_obligation",
                        delta * 0.28,
                        "expected repair avoidance sediments obligation as unmet",
                        [event.event_id],
                    )
                )
            if "public_exposure_expectation" in key:
                updates.append(
                    self._delta(
                        state,
                        process_id,
                        target_process_id,
                        "public_face_obligation",
                        delta * 0.26,
                        "expected exposure makes public face a normative constraint",
                        [event.event_id],
                    )
                )
        return updates

    def _account_updates(self, state: SimulationState, local_events: list[Event]) -> list[NormativePressureUpdate]:
        updates: list[NormativePressureUpdate] = []
        for event in local_events:
            if event.event_type != "AccountPressureEvent":
                continue
            delta = self._payload_float(event, "delta")
            if delta <= 0.0:
                continue
            process_id = str(event.payload.get("process_id", "p1"))
            target_process_id = self._other(process_id, state)
            account = str(event.payload.get("account", ""))
            if account in {"dignity", "meaning"}:
                updates.append(
                    self._delta(
                        state,
                        process_id,
                        target_process_id,
                        "claim_entitlement",
                        delta * 0.45,
                        f"{account} pressure turns injury into a standing claim",
                        [event.event_id],
                    )
                )
            if account == "control":
                updates.append(
                    self._delta(
                        state,
                        process_id,
                        target_process_id,
                        "exit_justification",
                        delta * 0.35,
                        "control pressure makes withdrawal or refusal easier to justify",
                        [event.event_id],
                    )
                )
            if account == "relation":
                updates.append(
                    self._delta(
                        state,
                        target_process_id,
                        process_id,
                        "repair_obligation",
                        delta * 0.34,
                        "relation pressure makes repair obligation more legible",
                        [event.event_id],
                    )
                )
        return updates

    def _relation_updates(self, state: SimulationState, local_events: list[Event]) -> list[NormativePressureUpdate]:
        updates: list[NormativePressureUpdate] = []
        p1, p2 = self._pair(state)
        for event in local_events:
            if event.event_type != "RelationSedimentationEvent":
                continue
            delta = self._payload_float(event, "delta")
            if delta <= 0.0:
                continue
            metric = str(event.payload.get("metric", ""))
            if metric in {"relation_sediment.recognition_debt", "relation_sediment.symbolic_accounting_load"}:
                updates.append(
                    self._delta(
                        state,
                        p1,
                        p2,
                        "reciprocity_obligation",
                        delta * 0.26,
                        f"{metric} turns exchange history into normative accounting",
                        [event.event_id],
                    )
                )
                updates.append(
                    self._delta(
                        state,
                        p1,
                        p2,
                        "claim_entitlement",
                        delta * 0.22,
                        f"{metric} strengthens standing to demand recognition",
                        [event.event_id],
                    )
                )
            elif metric in {"relation_sediment.public_definition_load", "relation_sediment.asymmetry_load"}:
                updates.append(
                    self._delta(
                        state,
                        p2,
                        p1,
                        "legitimacy_contestation",
                        delta * 0.24,
                        f"{metric} makes standing and authority contested",
                        [event.event_id],
                    )
                )
            elif metric == "relation_sediment.shared_fate_load":
                for process_id, target_process_id in [(p1, p2), (p2, p1)]:
                    updates.append(
                        self._delta(
                            state,
                            process_id,
                            target_process_id,
                            "mutual_obligation",
                            delta * 0.2,
                            "shared fate sediments a mutual obligation field",
                            [event.event_id],
                        )
                    )
        return updates

    def _delta(
        self,
        state: SimulationState,
        process_id: str,
        target_process_id: str,
        norm_type: str,
        delta: float,
        reason: str,
        refs: list[str],
    ) -> NormativePressureUpdate:
        previous = float(state.relation_metrics.get(self._key(process_id, target_process_id, norm_type), 0.0))
        return self._set(state, process_id, target_process_id, norm_type, previous + delta, reason, refs)

    def _set(
        self,
        state: SimulationState,
        process_id: str,
        target_process_id: str,
        norm_type: str,
        value: float,
        reason: str,
        refs: list[str],
    ) -> NormativePressureUpdate:
        key = self._key(process_id, target_process_id, norm_type)
        previous = float(state.relation_metrics.get(key, 0.0))
        new_value = clamp(value)
        state.relation_metrics[key] = new_value
        return NormativePressureUpdate(
            process_id=process_id,
            target_process_id=target_process_id,
            norm_type=norm_type,
            previous_value=round(previous, 4),
            new_value=new_value,
            reason=reason,
            causal_refs=sorted(set(refs)),
        )

    def _classification_norm(self, label: str) -> str | None:
        return {
            "you_make_it_sound_like_i_owe_you": "reciprocity_obligation",
            "your_help_is_control": "exit_justification",
            "we_are_only_fine_in_public": "public_face_obligation",
            "you_are_never_really_here": "repair_obligation",
            "nothing_i_do_is_right": "legitimacy_contestation",
        }.get(label)

    def _key(self, process_id: str, target_process_id: str, norm_type: str) -> str:
        return f"{self.PREFIX}{process_id}.{target_process_id}.{norm_type}"

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
