from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from rpf.core.events import Event
from rpf.core.models import SimulationState, clamp


@dataclass(frozen=True)
class AccountPressureUpdate:
    process_id: str
    account: str
    previous_value: float
    new_value: float
    reason: str
    causal_refs: list[str]

    def payload(self) -> dict[str, Any]:
        return {
            "process_id": self.process_id,
            "account": self.account,
            "previous_value": self.previous_value,
            "new_value": self.new_value,
            "delta": round(self.new_value - self.previous_value, 4),
            "reason": self.reason,
            "caused_by_events": self.causal_refs,
        }


class AccountPressureEngine:
    """Project observable history into bounded viability-account pressure.

    These pressures are not primitive accounts and not emotions. They are event-
    sourced summaries of how much safety, dignity, control, relation, meaning, or
    energy viability is currently strained for a process.
    """

    PREFIX = "account_pressure."

    def update(self, state: SimulationState, local_events: list[Event]) -> list[AccountPressureUpdate]:
        updates: list[AccountPressureUpdate] = []
        updates.extend(self._decay(state, local_events))
        updates.extend(self._field_updates(state, local_events))
        updates.extend(self._recognition_updates(state, local_events))
        updates.extend(self._repair_updates(state, local_events))
        updates.extend(self._expectation_updates(state, local_events))
        updates.extend(self._relation_updates(state, local_events))
        return [update for update in updates if update.previous_value != update.new_value]

    def _decay(self, state: SimulationState, local_events: list[Event]) -> list[AccountPressureUpdate]:
        refs = [event.event_id for event in local_events if event.event_type == "TickStartedEvent"][-1:]
        refs = refs or [event.event_id for event in local_events[:1]]
        updates: list[AccountPressureUpdate] = []
        for key, value in list(state.relation_metrics.items()):
            if not key.startswith(self.PREFIX):
                continue
            parts = key.split(".", 2)
            if len(parts) != 3:
                continue
            _, process_id, account = parts
            current = float(value)
            if current <= 0.0001:
                continue
            updates.append(
                self._set(
                    state,
                    process_id,
                    account,
                    current - min(current, 0.003),
                    "account pressure decays when not reinforced",
                    refs,
                )
            )
        return updates

    def _field_updates(self, state: SimulationState, local_events: list[Event]) -> list[AccountPressureUpdate]:
        updates: list[AccountPressureUpdate] = []
        for event in local_events:
            if event.event_type != "FieldPressureEvent":
                continue
            intensity = self._payload_float(event, "intensity")
            if intensity <= 0.05:
                continue
            for process_id in state.processes:
                updates.append(
                    self._delta(
                        state,
                        process_id,
                        "safety",
                        intensity * 0.006,
                        "field pressure strains safety viability",
                        [event.event_id],
                    )
                )
                updates.append(
                    self._delta(
                        state,
                        process_id,
                        "energy",
                        intensity * 0.004,
                        "field pressure consumes process energy viability",
                        [event.event_id],
                    )
                )
        return updates

    def _recognition_updates(self, state: SimulationState, local_events: list[Event]) -> list[AccountPressureUpdate]:
        updates: list[AccountPressureUpdate] = []
        for event in local_events:
            if event.event_type != "RecognitionEvent":
                continue
            holder = str(event.payload.get("holder", "p1"))
            demanded_from = str(event.payload.get("demanded_from", "p2"))
            result = str(event.payload.get("result", ""))
            if result in {"refused", "misunderstood", "displaced", "postponed", "unspeakable"}:
                updates.append(
                    self._delta(
                        state,
                        holder,
                        "dignity",
                        0.018,
                        f"recognition result {result} strains dignity viability",
                        [event.event_id],
                    )
                )
                updates.append(
                    self._delta(
                        state,
                        holder,
                        "relation",
                        0.012,
                        f"recognition result {result} strains relation viability",
                        [event.event_id],
                    )
                )
            if result in {"refused", "unspeakable"}:
                updates.append(
                    self._delta(
                        state,
                        demanded_from,
                        "control",
                        0.01,
                        f"recognition result {result} increases control pressure for the responding process",
                        [event.event_id],
                    )
                )
            if result in {"granted", "partial"}:
                updates.append(
                    self._delta(
                        state,
                        holder,
                        "dignity",
                        -0.014,
                        f"recognition result {result} relieves dignity pressure",
                        [event.event_id],
                    )
                )
        return updates

    def _repair_updates(self, state: SimulationState, local_events: list[Event]) -> list[AccountPressureUpdate]:
        updates: list[AccountPressureUpdate] = []
        for event in local_events:
            if event.event_type in {"AvoidanceEvent", "DisplacementEvent", "MisrecognitionEvent"}:
                updates.append(
                    self._delta(
                        state,
                        "p1",
                        "meaning",
                        0.012,
                        f"{event.event_type} strains meaning integration",
                        [event.event_id],
                    )
                )
                updates.append(
                    self._delta(
                        state,
                        "p1",
                        "relation",
                        0.01,
                        f"{event.event_type} strains relation viability",
                        [event.event_id],
                    )
                )
            elif event.event_type == "RepairEvent":
                for process_id in state.processes:
                    updates.append(
                        self._delta(
                            state,
                            process_id,
                            "relation",
                            -0.012,
                            "repair relieves relation viability pressure",
                            [event.event_id],
                        )
                    )
        return updates

    def _expectation_updates(self, state: SimulationState, local_events: list[Event]) -> list[AccountPressureUpdate]:
        updates: list[AccountPressureUpdate] = []
        for event in local_events:
            if event.event_type != "ExpectationSedimentationEvent":
                continue
            delta = self._payload_float(event, "delta")
            if delta <= 0.0:
                continue
            key = str(event.payload.get("expectation_key", ""))
            process_id = key.split(".")[1] if key.startswith("expectation.") and len(key.split(".")) > 2 else "p1"
            if "refusal_expectation" in key or "misrecognition_expectation" in key:
                updates.append(
                    self._delta(
                        state,
                        process_id,
                        "dignity",
                        delta * 0.35,
                        "expected refusal or misrecognition strains dignity viability",
                        [event.event_id],
                    )
                )
            if "public_exposure_expectation" in key:
                updates.append(
                    self._delta(
                        state,
                        process_id,
                        "control",
                        delta * 0.3,
                        "expected public exposure strains control viability",
                        [event.event_id],
                    )
                )
        return updates

    def _relation_updates(self, state: SimulationState, local_events: list[Event]) -> list[AccountPressureUpdate]:
        updates: list[AccountPressureUpdate] = []
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
                        "p1",
                        "dignity",
                        delta * 0.28,
                        "relation accounting sediment strains dignity viability",
                        [event.event_id],
                    )
                )
                updates.append(
                    self._delta(
                        state,
                        "p1",
                        "meaning",
                        delta * 0.22,
                        "relation accounting sediment strains meaning viability",
                        [event.event_id],
                    )
                )
            elif metric in {"relation_sediment.asymmetry_load", "relation_sediment.public_definition_load"}:
                updates.append(
                    self._delta(
                        state,
                        "p2",
                        "control",
                        delta * 0.22,
                        "relation definition sediment strains control viability",
                        [event.event_id],
                    )
                )
        return updates

    def _delta(
        self,
        state: SimulationState,
        process_id: str,
        account: str,
        delta: float,
        reason: str,
        refs: list[str],
    ) -> AccountPressureUpdate:
        previous = float(state.relation_metrics.get(self._key(process_id, account), 0.0))
        return self._set(state, process_id, account, previous + delta, reason, refs)

    def _set(
        self,
        state: SimulationState,
        process_id: str,
        account: str,
        value: float,
        reason: str,
        refs: list[str],
    ) -> AccountPressureUpdate:
        key = self._key(process_id, account)
        previous = float(state.relation_metrics.get(key, 0.0))
        new_value = clamp(value)
        state.relation_metrics[key] = new_value
        return AccountPressureUpdate(
            process_id=process_id,
            account=account,
            previous_value=round(previous, 4),
            new_value=new_value,
            reason=reason,
            causal_refs=sorted(set(refs)),
        )

    def _key(self, process_id: str, account: str) -> str:
        return f"{self.PREFIX}{process_id}.{account}"

    def _payload_float(self, event: Event, key: str) -> float:
        try:
            return float(event.payload.get(key, 0.0))
        except (TypeError, ValueError):
            return 0.0
