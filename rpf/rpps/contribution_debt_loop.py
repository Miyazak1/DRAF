from __future__ import annotations

from rpf.core.events import Event
from rpf.core.models import SimulationState, TickContext, clamp
from rpf.core.semantics import injury_memory, material_urgency, unrecognized_contribution
from rpf.rpps.base import Activation, BaseRPP


class ContributionDebtLoopRPP(BaseRPP):
    rpp_id = "contribution_debt_loop"

    def evaluate(self, state: SimulationState, context: TickContext, events: list[Event]) -> Activation | None:
        p1 = state.processes["p1"]
        unrecognized = unrecognized_contribution(state)
        recognition = max((d.current_pressure for d in p1.recognition_demands), default=0.0)
        urgency = material_urgency(state)
        signal = any(e.payload.get("signal_type") in {"material_urgency", "rent_due", "unacknowledged_help", "practical_repair"} for e in events)
        weights = self.config["weights"]  # type: ignore[index]
        score = (
            unrecognized * weights.get("unrecognized_contribution", weights.get("unrecognized_sacrifice", 0.0))
            + recognition * weights["recognition_pressure"]
            + urgency * weights.get("material_urgency", weights.get("rent_pressure", 0.0))
            + (weights["contribution_signal"] if signal else 0.0)
            + injury_memory(state) * weights.get("injury_memory", 0.0)
        )
        if score >= self.config["threshold"]:  # type: ignore[operator]
            return Activation(self.rpp_id, clamp(score), ["p1", "p2"], [e.event_id for e in events[-4:]], "unrecognized contribution becomes relational debt")
        return None

    def apply(self, state: SimulationState, activation: Activation) -> None:
        p1 = state.processes["p1"]
        effects = self.config["effects"]  # type: ignore[index]
        p1.adjust("resentment_pressure", effects["p1_resentment_delta"])
        p1.stabilized_patterns[self.rpp_id] = clamp(p1.stabilized_patterns.get(self.rpp_id, 0.0) + effects["p1_stabilization_delta"])
        state.processes["p2"].stabilized_patterns[self.rpp_id] = clamp(state.processes["p2"].stabilized_patterns.get(self.rpp_id, 0.0) + effects["p2_stabilization_delta"])
        state.relation_metrics["conflict_pressure"] = clamp(state.relation_metrics.get("conflict_pressure", 0.0) + effects["conflict_pressure_delta"])
