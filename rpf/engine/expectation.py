from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from rpf.core.events import Event
from rpf.core.models import SimulationState, clamp


@dataclass(frozen=True)
class ExpectationSedimentation:
    expectation_key: str
    previous_value: float
    new_value: float
    reason: str
    causal_refs: list[str]

    def payload(self) -> dict[str, Any]:
        return {
            "expectation_key": self.expectation_key,
            "previous_value": self.previous_value,
            "new_value": self.new_value,
            "delta": round(self.new_value - self.previous_value, 4),
            "reason": self.reason,
            "caused_by_events": self.causal_refs,
        }


class ExpectationSedimentationEngine:
    """Sediment second-order expectations from observable interaction.

    This is not an inner belief model. It records relation-specific expectations
    such as "direct speech will be refused" or "repair will be avoided" that
    are formed by observable events and then constrain later action.
    """

    PREFIX = "expectation."

    def update(self, state: SimulationState, local_events: list[Event]) -> list[ExpectationSedimentation]:
        updates: list[ExpectationSedimentation] = []
        updates.extend(self._decay(state, local_events))
        updates.extend(self._observation_updates(state, local_events))
        updates.extend(self._recognition_updates(state, local_events))
        updates.extend(self._repair_updates(state, local_events))
        updates.extend(self._relation_updates(state, local_events))
        return [update for update in updates if update.previous_value != update.new_value]

    def _decay(self, state: SimulationState, local_events: list[Event]) -> list[ExpectationSedimentation]:
        refs = [event.event_id for event in local_events if event.event_type == "TickStartedEvent"][-1:]
        refs = refs or [event.event_id for event in local_events[:1]]
        updates: list[ExpectationSedimentation] = []
        for key, value in list(state.relation_metrics.items()):
            if not key.startswith(self.PREFIX):
                continue
            current = float(value)
            if current <= 0.0001:
                continue
            updates.append(
                self._set(
                    state,
                    key,
                    current - min(current, 0.002),
                    "second-order expectation decays when not reinforced",
                    refs,
                )
            )
        return updates

    def _observation_updates(self, state: SimulationState, local_events: list[Event]) -> list[ExpectationSedimentation]:
        updates: list[ExpectationSedimentation] = []
        for event in local_events:
            if event.event_type != "ObservationEvent":
                continue
            observer = str(event.payload.get("observer", "p1"))
            target = self._other(observer, state)
            expression_mode = str(event.payload.get("expression_mode", ""))
            confidence = self._payload_float(event, "confidence")
            if expression_mode in {"silence", "timing_distortion", "gesture"}:
                updates.append(
                    self._delta(
                        state,
                        self._key(observer, target, "withdrawal_expectation"),
                        confidence * 0.014,
                        f"observed {expression_mode} raises expectation of withdrawal",
                        [event.event_id],
                    )
                )
            if expression_mode in {"public_performance", "tonal_shift"}:
                updates.append(
                    self._delta(
                        state,
                        self._key(observer, target, "public_exposure_expectation"),
                        confidence * 0.01,
                        f"observed {expression_mode} raises expectation that audience pressure shapes response",
                        [event.event_id],
                    )
                )
        return updates

    def _recognition_updates(self, state: SimulationState, local_events: list[Event]) -> list[ExpectationSedimentation]:
        updates: list[ExpectationSedimentation] = []
        for event in local_events:
            if event.event_type != "RecognitionEvent":
                continue
            holder = str(event.payload.get("holder", "p1"))
            demanded_from = str(event.payload.get("demanded_from", self._other(holder, state)))
            result = str(event.payload.get("result", ""))
            refs = [event.event_id]
            if result in {"refused", "postponed"}:
                updates.append(
                    self._delta(
                        state,
                        self._key(holder, demanded_from, "refusal_expectation"),
                        0.018,
                        f"recognition result {result} raises expectation of refusal",
                        refs,
                    )
                )
            if result in {"misunderstood", "displaced", "unspeakable"}:
                updates.append(
                    self._delta(
                        state,
                        self._key(holder, demanded_from, "misrecognition_expectation"),
                        0.016,
                        f"recognition result {result} raises expectation of misrecognition",
                        refs,
                    )
                )
            if result in {"granted", "partial"}:
                updates.append(
                    self._delta(
                        state,
                        self._key(holder, demanded_from, "refusal_expectation"),
                        -0.012,
                        f"recognition result {result} lowers expectation of refusal",
                        refs,
                    )
                )
        return updates

    def _repair_updates(self, state: SimulationState, local_events: list[Event]) -> list[ExpectationSedimentation]:
        updates: list[ExpectationSedimentation] = []
        for event in local_events:
            if event.event_type in {"AvoidanceEvent", "DisplacementEvent"}:
                updates.append(
                    self._delta(
                        state,
                        self._key("p1", "p2", "repair_avoidance_expectation"),
                        0.014,
                        f"{event.event_type} raises expectation that repair will be avoided",
                        [event.event_id],
                    )
                )
            elif event.event_type == "RepairEvent":
                updates.append(
                    self._delta(
                        state,
                        self._key("p1", "p2", "repair_avoidance_expectation"),
                        -0.018,
                        "repair lowers expectation that repair will be avoided",
                        [event.event_id],
                    )
                )
        return updates

    def _relation_updates(self, state: SimulationState, local_events: list[Event]) -> list[ExpectationSedimentation]:
        updates: list[ExpectationSedimentation] = []
        for event in local_events:
            if event.event_type != "RelationSedimentationEvent":
                continue
            delta = self._payload_float(event, "delta")
            if delta <= 0.0:
                continue
            metric = str(event.payload.get("metric", ""))
            if metric == "relation_sediment.recognition_debt":
                updates.append(
                    self._delta(
                        state,
                        self._key("p1", "p2", "refusal_expectation"),
                        delta * 0.04,
                        "relation recognition debt raises expected refusal",
                        [event.event_id],
                    )
                )
            elif metric == "relation_sediment.repair_access_narrowing":
                updates.append(
                    self._delta(
                        state,
                        self._key("p1", "p2", "repair_avoidance_expectation"),
                        delta * 0.04,
                        "relation repair narrowing raises expected repair avoidance",
                        [event.event_id],
                    )
                )
            elif metric in {"relation_sediment.public_definition_load", "relation_sediment.asymmetry_load"}:
                updates.append(
                    self._delta(
                        state,
                        self._key("p1", "p2", "public_exposure_expectation"),
                        delta * 0.035,
                        "relation definition pressure raises expected public exposure",
                        [event.event_id],
                    )
                )
        return updates

    def _delta(
        self,
        state: SimulationState,
        key: str,
        delta: float,
        reason: str,
        refs: list[str],
    ) -> ExpectationSedimentation:
        previous = float(state.relation_metrics.get(key, 0.0))
        return self._set(state, key, previous + delta, reason, refs)

    def _set(
        self,
        state: SimulationState,
        key: str,
        value: float,
        reason: str,
        refs: list[str],
    ) -> ExpectationSedimentation:
        previous = float(state.relation_metrics.get(key, 0.0))
        new_value = clamp(value)
        state.relation_metrics[key] = new_value
        return ExpectationSedimentation(
            expectation_key=key,
            previous_value=round(previous, 4),
            new_value=new_value,
            reason=reason,
            causal_refs=sorted(set(refs)),
        )

    def _key(self, observer: str, target: str, expectation: str) -> str:
        return f"{self.PREFIX}{observer}.{target}.{expectation}"

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
