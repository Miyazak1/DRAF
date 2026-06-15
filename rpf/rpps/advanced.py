from __future__ import annotations

from rpf.core.events import Event
from rpf.core.models import SimulationState, TickContext, clamp
from rpf.core.semantics import defensive_memory, fate_memory, injury_memory, memory_pressure, unrecognized_contribution
from rpf.rpps.base import Activation, BaseRPP, activation_evidence, future_constraint_pressure


def _audience_pressure(state: SimulationState) -> float:
    return max(state.field_state.audience_pressure.values(), default=0.0)


def _binding_urgency(state: SimulationState) -> float:
    if not state.bindings:
        return 0.0
    return clamp(sum(b.strength + max(b.exit_cost.values(), default=0.0) for b in state.bindings) / (2 * len(state.bindings)))


def _recognition_pressure(state: SimulationState) -> float:
    return max((d.current_pressure for p in state.processes.values() for d in p.recognition_demands), default=0.0)


def _history_pressure(state: SimulationState) -> float:
    return memory_pressure(state)


def _signal_seen(events: list[Event], signals: set[str]) -> bool:
    return any(e.payload.get("signal_type") in signals for e in events)


class DoubleBindRPP(BaseRPP):
    rpp_id = "double_bind"

    def evaluate(self, state: SimulationState, context: TickContext, events: list[Event]) -> Activation | None:
        if context.tick_type != "scene":
            return None
        if state.relation_metrics.get("double_bind_pressure", 0.0) < self.config.get("primary_gate", 0.0):
            return None
        p1 = state.processes["p1"]
        weights = self.config["weights"]  # type: ignore[index]
        inhibition = max(p1.speech_inhibition.get("direct_need", 0.0), p1.speech_inhibition.get("anger", 0.0))
        future_pressure, future_refs = future_constraint_pressure(
            events,
            requirements={"truth_integration", "identity_continuity", "speech_access"},
            type_terms={"identity", "double_bind", "right"},
        )
        score = (
            state.relation_metrics.get("double_bind_pressure", 0.0) * weights["double_bind_pressure"]
            + inhibition * weights["speech_inhibition"]
            + _binding_urgency(state) * weights["binding_urgency"]
            + _recognition_pressure(state) * weights["recognition_pressure"]
            + future_pressure * weights.get("future_constraint_pressure", 0.04)
        )
        if score >= self.config["threshold"]:  # type: ignore[operator]
            return Activation(self.rpp_id, clamp(score), ["p1", "p2"], activation_evidence(events, future_refs), "contradictory demands make any answer costly")
        return None

    def apply(self, state: SimulationState, activation: Activation) -> None:
        effects = self.config["effects"]  # type: ignore[index]
        state.processes["p1"].speech_inhibition["direct_need"] = clamp(state.processes["p1"].speech_inhibition.get("direct_need", 0.0) + effects["p1_direct_need_inhibition_delta"])
        state.processes["p2"].threat_sensitivity["being_disobeyed"] = clamp(state.processes["p2"].threat_sensitivity.get("being_disobeyed", 0.0) + effects["p2_disobedience_threat_delta"])
        state.relation_metrics["conflict_pressure"] = clamp(state.relation_metrics.get("conflict_pressure", 0.0) + effects["conflict_pressure_delta"])
        state.relation_metrics["double_bind_pressure"] = clamp(state.relation_metrics.get("double_bind_pressure", 0.0) + effects["self_reinforcement_delta"])
        for p in state.processes.values():
            p.stabilized_patterns[self.rpp_id] = clamp(p.stabilized_patterns.get(self.rpp_id, 0.0) + effects["stabilization_delta"])


class PublicPrivateSplitRPP(BaseRPP):
    rpp_id = "public_private_split"

    def evaluate(self, state: SimulationState, context: TickContext, events: list[Event]) -> Activation | None:
        if context.tick_type != "scene":
            return None
        if state.relation_metrics.get("public_private_gap", 0.0) < self.config.get("primary_gate", 0.0):
            return None
        weights = self.config["weights"]  # type: ignore[index]
        future_pressure, future_refs = future_constraint_pressure(
            events,
            requirements={"face_continuation", "truth_disclosure", "public_performance"},
            type_terms={"public", "fine"},
        )
        score = (
            state.relation_metrics.get("public_private_gap", 0.0) * weights["public_private_gap"]
            + _audience_pressure(state) * weights["audience_pressure"]
            + unrecognized_contribution(state) * weights["unrecognized_contribution"]
            + _signal_seen(events, {"unacknowledged_help", "practical_repair"}) * weights["public_performance_signal"]
            + future_pressure * weights.get("future_constraint_pressure", 0.045)
        )
        if score >= self.config["threshold"]:  # type: ignore[operator]
            return Activation(self.rpp_id, clamp(score), ["p1", "p2"], activation_evidence(events, future_refs), "public performance and private injury diverge")
        return None

    def apply(self, state: SimulationState, activation: Activation) -> None:
        effects = self.config["effects"]  # type: ignore[index]
        state.relation_metrics["public_private_gap"] = clamp(state.relation_metrics.get("public_private_gap", 0.0) + effects["gap_delta"])
        state.relation_metrics["repair_debt"] = clamp(state.relation_metrics.get("repair_debt", 0.0) + effects["repair_debt_delta"])
        state.processes["p1"].adjust("resentment_pressure", effects["p1_resentment_delta"])
        state.processes["p2"].speech_inhibition["apology"] = clamp(state.processes["p2"].speech_inhibition.get("apology", 0.0) + effects["p2_apology_inhibition_delta"])
        for p in state.processes.values():
            p.stabilized_patterns[self.rpp_id] = clamp(p.stabilized_patterns.get(self.rpp_id, 0.0) + effects["stabilization_delta"])


class SilenceInterpretationLoopRPP(BaseRPP):
    rpp_id = "silence_interpretation_loop"

    def evaluate(self, state: SimulationState, context: TickContext, events: list[Event]) -> Activation | None:
        if context.tick_type not in {"micro_interaction", "scene"}:
            return None
        if state.relation_metrics.get("silence_charge", 0.0) < self.config.get("primary_gate", 0.0):
            return None
        p1 = state.processes["p1"]
        weights = self.config["weights"]  # type: ignore[index]
        silence_signal = _signal_seen(events, {"delayed_reply", "gaze_avoidance", "short_answer"})
        future_pressure, future_refs = future_constraint_pressure(
            events,
            requirements={"presence_continuation", "repair_availability", "memory_integration"},
            type_terms={"absence", "unreachable", "memory"},
        )
        score = (
            state.relation_metrics.get("silence_charge", 0.0) * weights["silence_charge"]
            + p1.relevance_triggers.get("delayed_reply", 0.0) * weights["delay_relevance"]
            + (weights["silence_signal"] if silence_signal else 0.0)
            + (1.0 - p1.ambiguity_tolerance) * weights["low_ambiguity_tolerance"]
            + state.relation_metrics.get("repair_debt", 0.0) * weights["repair_debt"]
            + injury_memory(state) * weights.get("injury_memory", 0.0)
            + future_pressure * weights.get("future_constraint_pressure", 0.045)
        )
        if score >= self.config["threshold"]:  # type: ignore[operator]
            return Activation(self.rpp_id, clamp(score), ["p1", "p2"], activation_evidence(events, future_refs, window=3), "absence becomes communicative evidence")
        return None

    def apply(self, state: SimulationState, activation: Activation) -> None:
        effects = self.config["effects"]  # type: ignore[index]
        state.processes["p1"].adjust("checking_tendency", effects["checking_tendency_delta"])
        state.processes["p1"].adjust("ambiguity_tolerance", effects["ambiguity_tolerance_delta"])
        state.processes["p2"].speech_inhibition["direct_need"] = clamp(state.processes["p2"].speech_inhibition.get("direct_need", 0.0) + effects["p2_direct_need_inhibition_delta"])
        state.relation_metrics["silence_charge"] = clamp(state.relation_metrics.get("silence_charge", 0.0) + effects["silence_charge_delta"])
        for p in state.processes.values():
            p.stabilized_patterns[self.rpp_id] = clamp(p.stabilized_patterns.get(self.rpp_id, 0.0) + effects["stabilization_delta"])


class ComplementaryDependencyRPP(BaseRPP):
    rpp_id = "complementary_dependency"

    def evaluate(self, state: SimulationState, context: TickContext, events: list[Event]) -> Activation | None:
        if context.tick_type not in {"latent", "scene"}:
            return None
        if state.relation_metrics.get("care_dependency", 0.0) < self.config.get("primary_gate", 0.0):
            return None
        p1 = state.processes["p1"]
        p2 = state.processes["p2"]
        weights = self.config["weights"]  # type: ignore[index]
        future_pressure, future_refs = future_constraint_pressure(
            events,
            requirements={"care_availability", "agency_continuation", "exit_availability"},
            type_terms={"care", "control", "role"},
        )
        score = (
            state.relation_metrics.get("care_dependency", 0.0) * weights["care_dependency"]
            + p1.fatigue * weights["caretaker_fatigue"]
            + p2.speech_inhibition.get("dependency_admission", 0.0) * weights["dependency_admission_inhibition"]
            + _binding_urgency(state) * weights["binding_urgency"]
            + unrecognized_contribution(state) * weights["unrecognized_contribution"]
            + _history_pressure(state) * weights.get("memory_pressure", 0.0)
            + future_pressure * weights.get("future_constraint_pressure", 0.045)
        )
        if score >= self.config["threshold"]:  # type: ignore[operator]
            return Activation(self.rpp_id, clamp(score), ["p1", "p2"], activation_evidence(events, future_refs), "help preserves safety while stabilizing asymmetry")
        return None

    def apply(self, state: SimulationState, activation: Activation) -> None:
        effects = self.config["effects"]  # type: ignore[index]
        state.relation_metrics["care_dependency"] = clamp(state.relation_metrics.get("care_dependency", 0.0) + effects["dependency_delta"])
        state.relation_metrics["conflict_pressure"] = clamp(state.relation_metrics.get("conflict_pressure", 0.0) + effects["conflict_pressure_delta"])
        state.processes["p1"].adjust("resentment_pressure", effects["p1_resentment_delta"])
        state.processes["p2"].speech_inhibition["dependency_admission"] = clamp(state.processes["p2"].speech_inhibition.get("dependency_admission", 0.0) + effects["p2_dependency_inhibition_delta"])
        for p in state.processes.values():
            p.stabilized_patterns[self.rpp_id] = clamp(p.stabilized_patterns.get(self.rpp_id, 0.0) + effects["stabilization_delta"])


class FaceSavingLoopRPP(BaseRPP):
    rpp_id = "face_saving_loop"

    def evaluate(self, state: SimulationState, context: TickContext, events: list[Event]) -> Activation | None:
        if context.tick_type != "scene":
            return None
        if state.relation_metrics.get("face_risk_pressure", 0.0) < self.config.get("primary_gate", 0.0):
            return None
        p2 = state.processes["p2"]
        weights = self.config["weights"]  # type: ignore[index]
        future_pressure, future_refs = future_constraint_pressure(
            events,
            requirements={"face_continuation", "speech_access", "repair_availability"},
            type_terms={"public", "identity", "control"},
        )
        score = (
            state.relation_metrics.get("face_risk_pressure", 0.0) * weights["face_risk_pressure"]
            + _audience_pressure(state) * weights["audience_pressure"]
            + p2.speech_inhibition.get("apology", 0.0) * weights["apology_inhibition"]
            + state.relation_metrics.get("repair_debt", 0.0) * weights["repair_debt"]
            + defensive_memory(state) * weights.get("defensive_memory", 0.0)
            + _signal_seen(events, {"public_politeness"}) * weights.get("public_performance_signal", 0.0)
            + future_pressure * weights.get("future_constraint_pressure", 0.045)
        )
        if score >= self.config["threshold"]:  # type: ignore[operator]
            return Activation(self.rpp_id, clamp(score), ["p1", "p2"], activation_evidence(events, future_refs), "saving face displaces repair into performance")
        return None

    def apply(self, state: SimulationState, activation: Activation) -> None:
        effects = self.config["effects"]  # type: ignore[index]
        state.relation_metrics["face_risk_pressure"] = clamp(state.relation_metrics.get("face_risk_pressure", 0.0) + effects["face_risk_delta"])
        state.relation_metrics["repair_debt"] = clamp(state.relation_metrics.get("repair_debt", 0.0) + effects["repair_debt_delta"])
        state.processes["p2"].speech_inhibition["apology"] = clamp(state.processes["p2"].speech_inhibition.get("apology", 0.0) + effects["p2_apology_inhibition_delta"])
        for p in state.processes.values():
            p.stabilized_patterns[self.rpp_id] = clamp(p.stabilized_patterns.get(self.rpp_id, 0.0) + effects["stabilization_delta"])


class RecognitionPursuitRPP(BaseRPP):
    rpp_id = "recognition_pursuit"

    def evaluate(self, state: SimulationState, context: TickContext, events: list[Event]) -> Activation | None:
        if context.tick_type not in {"micro_interaction", "scene"}:
            return None
        if state.relation_metrics.get("recognition_pursuit_pressure", 0.0) < self.config.get("primary_gate", 0.0):
            return None
        p1 = state.processes["p1"]
        weights = self.config["weights"]  # type: ignore[index]
        future_pressure, future_refs = future_constraint_pressure(
            events,
            requirements={"recognition_access", "repair_availability", "memory_integration"},
            type_terms={"recognition", "debt", "absence"},
        )
        score = (
            state.relation_metrics.get("recognition_pursuit_pressure", 0.0) * weights["recognition_pursuit_pressure"]
            + _recognition_pressure(state) * weights["recognition_pressure"]
            + p1.checking_tendency * weights["checking_tendency"]
            + unrecognized_contribution(state) * weights["unrecognized_contribution"]
            + injury_memory(state) * weights.get("injury_memory", 0.0)
            + future_pressure * weights.get("future_constraint_pressure", 0.045)
        )
        if score >= self.config["threshold"]:  # type: ignore[operator]
            return Activation(self.rpp_id, clamp(score), ["p1", "p2"], activation_evidence(events, future_refs), "recognition demand becomes repeated pursuit")
        return None

    def apply(self, state: SimulationState, activation: Activation) -> None:
        effects = self.config["effects"]  # type: ignore[index]
        state.relation_metrics["recognition_pursuit_pressure"] = clamp(state.relation_metrics.get("recognition_pursuit_pressure", 0.0) + effects["recognition_pursuit_delta"])
        state.relation_metrics["conflict_pressure"] = clamp(state.relation_metrics.get("conflict_pressure", 0.0) + effects["conflict_pressure_delta"])
        state.processes["p1"].adjust("checking_tendency", effects["checking_tendency_delta"])
        state.processes["p2"].threat_sensitivity["being_controlled"] = clamp(state.processes["p2"].threat_sensitivity.get("being_controlled", 0.0) + effects["p2_control_threat_delta"])
        for p in state.processes.values():
            p.stabilized_patterns[self.rpp_id] = clamp(p.stabilized_patterns.get(self.rpp_id, 0.0) + effects["stabilization_delta"])
