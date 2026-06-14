from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from rpf.core.events import Event
from rpf.core.models import RecognitionDemand, SimulationState, clamp
from rpf.core.semantics import defensive_memory, fate_memory, injury_memory, memory_pressure, unrecognized_contribution


RecognitionOutcome = Literal["granted", "partial", "misunderstood", "displaced", "refused", "postponed", "unspeakable"]


@dataclass(frozen=True)
class RecognitionResult:
    demand: RecognitionDemand
    outcome: RecognitionOutcome
    scores: dict[str, float]
    evidence: dict[str, float | str]
    repair_event_type: str
    repair_method: str
    repair_debt_delta: float
    conflict_delta: float
    demand_pressure_delta: float


class RecognitionEngine:
    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config

    def evaluate(self, state: SimulationState, events: list[Event]) -> RecognitionResult:
        demand = max(
            (demand for process in state.processes.values() for demand in process.recognition_demands),
            key=lambda item: item.current_pressure,
        )
        affordance_id = self._latest_payload(events, "AffordanceSelectionEvent", "affordance_id", "none")
        signal_type = self._latest_payload(events, "MicroSignalEvent", "signal_type", "none")
        action_id = self._latest_payload(events, "ActionSelectionEvent", "action_id", "none")
        action_mode = self._latest_payload(events, "ActionSelectionEvent", "action_mode", "none")
        expression_id = self._latest_payload(events, "ExpressionSelectionEvent", "expression_id", "none")
        expression_mode = self._latest_payload(events, "ExpressionSelectionEvent", "expression_mode", "none")
        composition = self._dominant_composition(state)
        p1 = state.processes["p1"]
        p2 = state.processes["p2"]
        audience = max(state.field_state.audience_pressure.values(), default=0.0)
        repair_debt = state.relation_metrics.get("repair_debt", 0.0)
        face_risk = max(
            audience,
            state.relation_metrics.get("face_risk_pressure", 0.0),
            p2.speech_inhibition.get("apology", 0.0),
        )
        pressure = clamp((demand.current_pressure + demand.vulnerability_cost + demand.threat_if_denied + demand.identity_dependency) / 4)
        contribution = unrecognized_contribution(state)
        remembered_history = memory_pressure(state)
        injury_history = injury_memory(state)
        defensive_history = defensive_memory(state)
        fate_history = fate_memory(state)
        speech_block = max(p1.speech_inhibition.get("direct_need", 0.0), p1.speech_inhibition.get("anger", 0.0), p2.speech_inhibition.get("apology", 0.0))
        scores = {
            "granted": clamp((1.0 - repair_debt) * 0.18 + (1.0 - face_risk) * 0.18 + demand.explicitness * 0.24 - remembered_history * 0.03),
            "partial": clamp((1.0 - face_risk) * 0.12 + self._is(affordance_id, {"practical_repair_offer", "care_intervention"}) * 0.28 + demand.explicitness * 0.14 - fate_history * 0.02),
            "misunderstood": clamp(self._is(affordance_id, {"material_pressure_intrusion", "care_intervention", "double_bind_response"}) * 0.26 + pressure * 0.14 + speech_block * 0.16 + injury_history * 0.025),
            "displaced": clamp(self._is(affordance_id, {"practical_repair_offer", "public_performance", "material_pressure_intrusion"}) * 0.28 + face_risk * 0.2 + repair_debt * 0.1 + defensive_history * 0.025),
            "refused": clamp(repair_debt * 0.22 + face_risk * 0.2 + pressure * 0.14 + self._is(composition, {"debt_lock", "credit_recognition_lock"}) * 0.18 + injury_history * 0.03),
            "postponed": clamp(self._is(affordance_id, {"mediated_delay", "public_performance"}) * 0.32 + audience * 0.14 + repair_debt * 0.1 + defensive_history * 0.02),
            "unspeakable": clamp(self._is(affordance_id, {"double_bind_response"}) * 0.28 + self._is(composition, {"care_bind_double_bind", "public_face_split"}) * 0.2 + speech_block * 0.18 + fate_history * 0.03),
        }
        outcome = max(scores.items(), key=lambda item: (item[1], item[0]))[0]
        effects = self.config["effects"][outcome]  # type: ignore[index]
        return RecognitionResult(
            demand=demand,
            outcome=outcome,  # type: ignore[arg-type]
            scores=scores,
            evidence={
                "affordance_id": affordance_id,
                "signal_type": signal_type,
                "action_id": action_id,
                "action_mode": action_mode,
                "expression_id": expression_id,
                "expression_mode": expression_mode,
                "dominant_composition": composition or "none",
                "recognition_pressure": pressure,
                "repair_debt": repair_debt,
                "face_risk": face_risk,
                "unrecognized_contribution": contribution,
                "memory_pressure": remembered_history,
                "injury_memory": injury_history,
                "defensive_memory": defensive_history,
                "fate_memory": fate_history,
                "speech_block": speech_block,
            },
            repair_event_type=str(effects["repair_event_type"]),
            repair_method=str(effects["repair_method"]),
            repair_debt_delta=float(effects["repair_debt_delta"]),
            conflict_delta=float(effects["conflict_delta"]),
            demand_pressure_delta=float(effects["demand_pressure_delta"]),
        )

    def apply(self, state: SimulationState, result: RecognitionResult) -> None:
        growth = state.relation_metrics.get("repair_debt_growth", 1.0)
        state.relation_metrics["repair_debt"] = clamp(state.relation_metrics.get("repair_debt", 0.0) + result.repair_debt_delta * growth)
        state.relation_metrics["conflict_pressure"] = clamp(state.relation_metrics.get("conflict_pressure", 0.0) + result.conflict_delta)
        result.demand.current_pressure = clamp(result.demand.current_pressure + result.demand_pressure_delta)
        state.relation_metrics["last_recognition_outcome_score"] = result.scores[result.outcome]

    def _dominant_composition(self, state: SimulationState) -> str | None:
        composition_scores = {
            key.removeprefix("composition."): value
            for key, value in state.relation_metrics.items()
            if key.startswith("composition.")
        }
        if not composition_scores:
            return None
        return max(composition_scores.items(), key=lambda item: item[1])[0]

    def _latest_payload(self, events: list[Event], event_type: str, key: str, default: str) -> str:
        for event in reversed(events):
            if event.event_type == event_type:
                return str(event.payload.get(key, default))
        return default

    def _is(self, value: str | None, options: set[str]) -> float:
        return 1.0 if value in options else 0.0
