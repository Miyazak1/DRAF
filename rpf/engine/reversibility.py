from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from rpf.core.events import Event
from rpf.core.models import SimulationState, TickContext, clamp


@dataclass(frozen=True)
class ActionReversibility:
    reversibility_id: str
    process_id: str
    action_id: str
    action_mode: str
    reversibility_width: float
    threshold_proximity: float
    threshold_state: str
    recovery_route: str
    lost_alternative: str
    consequence: str
    affected_requirements: list[str]
    evidence: dict[str, float | str]
    causal_refs: list[str]

    def payload(self) -> dict[str, Any]:
        return {
            "reversibility_id": self.reversibility_id,
            "process_id": self.process_id,
            "action_id": self.action_id,
            "action_mode": self.action_mode,
            "reversibility_width": round(self.reversibility_width, 4),
            "threshold_proximity": round(self.threshold_proximity, 4),
            "threshold_state": self.threshold_state,
            "recovery_route": self.recovery_route,
            "lost_alternative": self.lost_alternative,
            "consequence": self.consequence,
            "affected_requirements": self.affected_requirements,
            "evidence": self.evidence,
            "caused_by_events": self.causal_refs,
        }


class ActionReversibilityEngine:
    """Estimate whether the latest action can still be repaired without becoming history."""

    def update(self, state: SimulationState, context: TickContext, local_events: list[Event]) -> ActionReversibility | None:
        action_event = self._latest_event(local_events, "ActionSelectionEvent")
        if not action_event:
            return None
        action = action_event.payload
        expression = self._latest(local_events, "ExpressionSelectionEvent")
        recognition = self._latest(local_events, "RecognitionEvent")
        opportunity = self._strongest_opportunity(local_events)
        future_load = self._future_constraint_load(local_events)
        active_rpp = max((rpp.intensity for rpp in state.active_rpps), default=0.0)
        repair_debt = float(state.relation_metrics.get("repair_debt", 0.0) or 0.0)
        conflict = float(state.relation_metrics.get("conflict_pressure", 0.0) or 0.0)
        repair_narrowing = float(state.relation_metrics.get("relation_sediment.repair_access_narrowing", 0.0) or 0.0)
        future_lock = float(state.relation_metrics.get("relation_sediment.future_lock_load", 0.0) or 0.0)
        mode = str(action.get("action_mode", ""))
        expression_mode = str(expression.get("expression_mode", ""))
        outcome = str(recognition.get("outcome") or recognition.get("result") or "")
        opportunity_intensity = float(opportunity.get("intensity", 0.0) or 0.0)
        opportunity_type = str(opportunity.get("cost_type", "none"))
        mode_cost = {
            "inhibited": 0.16,
            "substituted": 0.11,
            "escalated": 0.12,
            "enacted": 0.06,
        }.get(mode, 0.04)
        expression_cost = {
            "silence": 0.13,
            "timing_distortion": 0.08,
            "gesture": 0.06,
            "public_performance": 0.09,
            "tonal_shift": 0.07,
        }.get(expression_mode, 0.03)
        recognition_cost = {
            "refused": 0.15,
            "misunderstood": 0.13,
            "unspeakable": 0.18,
            "postponed": 0.1,
            "displaced": 0.08,
            "partial": 0.03,
            "granted": -0.08,
        }.get(outcome, 0.04)
        pressure = clamp(
            repair_debt * 0.2
            + conflict * 0.14
            + repair_narrowing * 0.18
            + future_lock * 0.12
            + active_rpp * 0.1
            + future_load * 0.14
            + opportunity_intensity * 0.24
            + mode_cost
            + expression_cost
            + recognition_cost
        )
        width = clamp(1.0 - pressure)
        threshold_state = self._threshold_state(pressure, width)
        if threshold_state == "recoverable" and pressure < 0.12:
            return None
        result = ActionReversibility(
            reversibility_id=f"rev-{state.tick:04d}-{action.get('action_id', 'action')}",
            process_id=str(action.get("source_process", "relation")),
            action_id=str(action.get("action_id", "")),
            action_mode=mode,
            reversibility_width=width,
            threshold_proximity=pressure,
            threshold_state=threshold_state,
            recovery_route=self._recovery_route(threshold_state, outcome, opportunity_type),
            lost_alternative=self._lost_alternative(threshold_state, opportunity_type),
            consequence=self._consequence(threshold_state),
            affected_requirements=self._affected_requirements(threshold_state, opportunity_type),
            evidence={
                "tick_type": context.tick_type,
                "action_mode": mode,
                "expression_mode": expression_mode,
                "recognition_outcome": outcome or "none",
                "opportunity_cost": opportunity_type,
                "opportunity_intensity": round(opportunity_intensity, 4),
                "future_constraint_load": round(future_load, 4),
                "active_rpp_intensity": round(active_rpp, 4),
                "repair_debt": round(repair_debt, 4),
                "conflict_pressure": round(conflict, 4),
                "repair_access_narrowing": round(repair_narrowing, 4),
                "future_lock_load": round(future_lock, 4),
            },
            causal_refs=self._causal_refs(action_event, local_events),
        )
        self._apply(state, result)
        return result

    def _apply(self, state: SimulationState, result: ActionReversibility) -> None:
        pressure = result.threshold_proximity
        state.relation_metrics["action_reversibility.pressure"] = clamp(
            float(state.relation_metrics.get("action_reversibility.pressure", 0.0) or 0.0) * 0.82
            + pressure * 0.18
        )
        state.relation_metrics[f"action_reversibility.{result.threshold_state}"] = clamp(
            float(state.relation_metrics.get(f"action_reversibility.{result.threshold_state}", 0.0) or 0.0)
            + pressure * 0.045
        )
        if result.threshold_state in {"narrowing", "threshold_crossed", "symbolic_only"}:
            state.relation_metrics["relation_sediment.repair_access_narrowing"] = clamp(
                float(state.relation_metrics.get("relation_sediment.repair_access_narrowing", 0.0) or 0.0)
                + pressure * 0.01
            )
        if result.threshold_state == "symbolic_only":
            state.relation_metrics["relation_sediment.future_lock_load"] = clamp(
                float(state.relation_metrics.get("relation_sediment.future_lock_load", 0.0) or 0.0)
                + pressure * 0.006
            )
        for process in state.processes.values():
            process.risk_suspension_scope = clamp(process.risk_suspension_scope - pressure * 0.002)

    def _threshold_state(self, pressure: float, width: float) -> str:
        if pressure >= 0.76 or width <= 0.18:
            return "symbolic_only"
        if pressure >= 0.62 or width <= 0.32:
            return "threshold_crossed"
        if pressure >= 0.38 or width <= 0.5:
            return "narrowing"
        return "recoverable"

    def _recovery_route(self, threshold_state: str, outcome: str, opportunity_type: str) -> str:
        if threshold_state == "symbolic_only":
            return "only_symbolic_acknowledgement_remains"
        if threshold_state == "threshold_crossed":
            return "repair_requires_explicit_counter_history"
        if outcome == "granted":
            return "ordinary_repair_still_available"
        if opportunity_type in {"repair_window_loss", "trust_window_loss"}:
            return "repair_requires_extra_cost"
        return "direct_repair_still_possible"

    def _lost_alternative(self, threshold_state: str, opportunity_type: str) -> str:
        if opportunity_type == "evidence_window_loss":
            return "low_contamination_truth_route"
        if opportunity_type == "repair_window_loss":
            return "clean_apology_or_acknowledgement"
        if opportunity_type == "trust_window_loss":
            return "low_cost_trust_update"
        if threshold_state in {"threshold_crossed", "symbolic_only"}:
            return "treating_the_action_as_local_and_reversible"
        return "easy_return_to_previous_interaction"

    def _consequence(self, threshold_state: str) -> str:
        return {
            "recoverable": "the action can still be repaired as a local disturbance",
            "narrowing": "later repair must explain why the action happened, not only undo it",
            "threshold_crossed": "the action begins to count as relation history",
            "symbolic_only": "repair can acknowledge the mark but cannot restore the old alternative",
        }[threshold_state]

    def _affected_requirements(self, threshold_state: str, opportunity_type: str) -> list[str]:
        requirements = ["repair_availability", "recognition_access"]
        if threshold_state in {"threshold_crossed", "symbolic_only"}:
            requirements.extend(["memory_integration", "relation_continuation"])
        if opportunity_type == "evidence_window_loss":
            requirements.append("truth_integration")
        if opportunity_type == "social_exposure_cost":
            requirements.append("face_continuation")
        return sorted(set(requirements))

    def _strongest_opportunity(self, events: list[Event]) -> dict[str, Any]:
        opportunities = [event.payload for event in events if event.event_type == "OpportunityCostEvent"]
        if not opportunities:
            return {}
        return max(opportunities, key=lambda item: float(item.get("intensity") or 0.0))

    def _future_constraint_load(self, events: list[Event]) -> float:
        values = [
            float(event.payload.get("intensity") or 0.0)
            for event in events
            if event.event_type == "FutureConstraintEvent"
        ]
        return max(values, default=0.0)

    def _latest_event(self, events: list[Event], event_type: str) -> Event | None:
        for event in reversed(events):
            if event.event_type == event_type:
                return event
        return None

    def _latest(self, events: list[Event], event_type: str) -> dict[str, Any]:
        event = self._latest_event(events, event_type)
        return event.payload if event else {}

    def _causal_refs(self, action_event: Event, events: list[Event]) -> list[str]:
        important = {
            "ActionSelectionEvent",
            "ExpressionSelectionEvent",
            "RecognitionEvent",
            "OpportunityCostEvent",
            "FutureConstraintEvent",
            "RPPActivationEvent",
            "RPPCompositionEvent",
        }
        refs = {action_event.event_id, *action_event.causal_refs}
        refs.update(event.event_id for event in events[-8:] if event.event_type in important)
        return sorted(refs)
