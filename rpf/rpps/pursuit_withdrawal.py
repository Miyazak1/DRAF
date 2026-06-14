from __future__ import annotations

from rpf.core.models import SimulationState, TickContext, clamp
from rpf.core.events import Event
from rpf.core.semantics import defensive_memory, injury_memory
from rpf.rpps.base import Activation, BaseRPP


class PursuitWithdrawalRPP(BaseRPP):
    rpp_id = "pursuit_withdrawal"

    def evaluate(self, state: SimulationState, context: TickContext, events: list[Event]) -> Activation | None:
        p1 = state.processes["p1"]
        p2 = state.processes["p2"]
        delayed = any(e.payload.get("signal_type") in {"delayed_reply", "short_answer", "gaze_avoidance"} for e in events)
        abandonment = p1.relevance_triggers.get("delayed_reply", 0.0)
        autonomy = p2.threat_sensitivity.get("being_controlled", 0.0)
        recognition = max((d.current_pressure for d in p1.recognition_demands), default=0.0)
        weights = self.config["weights"]  # type: ignore[index]
        score = (
            (weights["delayed_signal"] if delayed else 0.0)
            + abandonment * weights["abandonment_relevance"]
            + autonomy * weights["autonomy_threat"]
            + recognition * weights["recognition_pressure"]
            + state.relation_metrics.get("repair_debt", 0.0) * weights["repair_debt"]
            + injury_memory(state) * weights.get("injury_memory", 0.0)
            + defensive_memory(state) * weights.get("defensive_memory", 0.0)
        )
        if context.tick_type in {"micro_interaction", "scene"} and score >= self.config["threshold"]:  # type: ignore[operator]
            return Activation(self.rpp_id, clamp(score), ["p1", "p2"], [e.event_id for e in events[-3:]], "checking and withdrawal reinforce each other")
        return None

    def apply(self, state: SimulationState, activation: Activation) -> None:
        p1 = state.processes["p1"]
        p2 = state.processes["p2"]
        effects = self.config["effects"]  # type: ignore[index]
        p1.adjust("checking_tendency", effects["checking_tendency_delta"])
        p1.adjust("ambiguity_tolerance", effects["ambiguity_tolerance_delta"])
        p2.speech_inhibition["direct_need"] = clamp(p2.speech_inhibition.get("direct_need", 0.3) + effects["p2_direct_need_inhibition_delta"])
        p1.stabilized_patterns[self.rpp_id] = clamp(p1.stabilized_patterns.get(self.rpp_id, 0.0) + effects["stabilization_delta"])
        p2.stabilized_patterns[self.rpp_id] = clamp(p2.stabilized_patterns.get(self.rpp_id, 0.0) + effects["stabilization_delta"])
        state.relation_metrics["conflict_pressure"] = clamp(state.relation_metrics.get("conflict_pressure", 0.0) + effects["conflict_pressure_delta"])
