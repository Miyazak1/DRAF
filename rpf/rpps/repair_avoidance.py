from __future__ import annotations

from rpf.core.models import SimulationState, TickContext, clamp
from rpf.core.events import Event
from rpf.core.semantics import defensive_memory, unrecognized_contribution
from rpf.rpps.base import Activation, BaseRPP


class RepairAvoidanceRPP(BaseRPP):
    rpp_id = "repair_avoidance"

    def evaluate(self, state: SimulationState, context: TickContext, events: list[Event]) -> Activation | None:
        p2 = state.processes["p2"]
        apology_inhibition = p2.speech_inhibition.get("apology", 0.0)
        face_risk = p2.threat_sensitivity.get("being_controlled", 0.0)
        injury_present = unrecognized_contribution(state)
        practical_signal = any(e.payload.get("signal_type") in {"practical_repair", "topic_change"} for e in events)
        weights = self.config["weights"]  # type: ignore[index]
        score = (
            apology_inhibition * weights["apology_inhibition"]
            + face_risk * weights["face_risk"]
            + injury_present * weights["injury_present"]
            + (weights["practical_signal"] if practical_signal else 0.0)
            + state.relation_metrics.get("conflict_pressure", 0.0) * weights["conflict_pressure"]
            + defensive_memory(state) * weights.get("defensive_memory", 0.0)
        )
        if context.tick_type == "scene" and score >= self.config["threshold"]:  # type: ignore[operator]
            return Activation(self.rpp_id, clamp(score), ["p1", "p2"], [e.event_id for e in events[-4:]], "repair pressure displaced into avoidance or practical help")
        return None

    def apply(self, state: SimulationState, activation: Activation) -> None:
        effects = self.config["effects"]  # type: ignore[index]
        growth = state.relation_metrics.get("repair_debt_growth", 1.0)
        state.relation_metrics["repair_debt"] = clamp(state.relation_metrics.get("repair_debt", 0.0) + effects["repair_debt_delta"] * growth)
        state.relation_metrics["conflict_pressure"] = clamp(state.relation_metrics.get("conflict_pressure", 0.0) + effects["conflict_pressure_delta"])
        for p in state.processes.values():
            p.stabilized_patterns[self.rpp_id] = clamp(p.stabilized_patterns.get(self.rpp_id, 0.0) + effects["stabilization_delta"])
        state.processes["p1"].adjust("resentment_pressure", effects["p1_resentment_delta"])
