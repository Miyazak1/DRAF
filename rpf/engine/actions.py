from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from rpf.core.events import Event
from rpf.core.models import SimulationState, TickContext, clamp
from rpf.core.semantics import defensive_memory, fate_memory, injury_memory, memory_pressure
from rpf.engine.affordances import AffordanceCandidate


@dataclass(frozen=True)
class ActionCandidate:
    action_id: str
    action_mode: str
    signal_type: str
    source_process: str
    target_process: str
    score: float
    inhibited_action: str | None
    substituted_for: str | None
    ambiguity: float
    relation_claim: str
    evidence: dict[str, float]


class ActionSelectionEngine:
    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config
        self.last_diagnostics: dict[str, Any] = {}

    def select(
        self,
        state: SimulationState,
        context: TickContext,
        affordance: AffordanceCandidate,
        viability_events: list[Event] | None = None,
    ) -> ActionCandidate:
        viability = self._viability_context(viability_events or [])
        candidates = self._candidates(state, context, affordance, viability)
        selected = max(candidates, key=lambda item: (item.score, item.action_id))
        self._apply(state, selected)
        self.last_diagnostics = {
            "tick": state.tick,
            "tick_type": context.tick_type,
            "affordance_id": affordance.affordance_id,
            "viability_context": viability,
            "selected_action": selected.__dict__,
            "candidates": [candidate.__dict__ for candidate in sorted(candidates, key=lambda item: item.score, reverse=True)],
        }
        return selected

    def _candidates(
        self,
        state: SimulationState,
        context: TickContext,
        affordance: AffordanceCandidate,
        viability: dict[str, Any],
    ) -> list[ActionCandidate]:
        source = affordance.source_process
        source_state = state.processes.get(source)
        direct_speech_block = 0.0
        if source_state:
            direct_speech_block = max(
                source_state.speech_inhibition.get("direct_need", 0.0),
                source_state.speech_inhibition.get("apology", 0.0),
                source_state.speech_inhibition.get("anger", 0.0),
                source_state.speech_inhibition.get("dependency_admission", 0.0),
            )
        audience = max(state.field_state.audience_pressure.values(), default=0.0)
        repair_debt = state.relation_metrics.get("repair_debt", 0.0)
        conflict = state.relation_metrics.get("conflict_pressure", 0.0)
        history = memory_pressure(state)
        injury = injury_memory(state)
        defensive = defensive_memory(state)
        fate = fate_memory(state)
        expectation = self._expectation_context(state, source, affordance.target_process)
        account = self._account_context(state, source)
        normativity = self._normativity_context(state, source, affordance.target_process)
        position = self._position_context(state, source, affordance.target_process)
        weights = self.config.get("weights", {})
        tick_bias = (self.config.get("tick_bias") or {}).get(context.tick_type, 0.0)
        viability_pressure = float(viability["viability_pressure"])
        direct_cost = float(viability["direct_response_cost"])
        affordance_narrowing = float(viability["affordance_narrowing"])
        face_constraint = float(viability["face_constraint"])

        direct = self._candidate(
            "direct_enactment",
            "enacted",
            affordance.signal_type,
            source,
            affordance.target_process,
            affordance.ambiguity,
            affordance.inferred_relation_claim,
            None,
            None,
            tick_bias,
            {
                "affordance_score": affordance.score * weights.get("affordance_score", 0.45),
                "low_inhibition": (1.0 - direct_speech_block) * weights.get("low_inhibition", 0.18),
                "low_fate_memory": (1.0 - fate) * weights.get("low_fate_memory", 0.08),
                "viability_direct_space": (1.0 - direct_cost) * weights.get("viability_direct_space", 0.008),
                "expected_refusal_penalty": -expectation["refusal"] * weights.get("expected_refusal_direct_penalty", 0.08),
                "expected_misrecognition_penalty": -expectation["misrecognition"] * weights.get("expected_misrecognition_direct_penalty", 0.06),
                "account_energy_penalty": -account["energy"] * weights.get("account_energy_direct_penalty", 0.04),
                "account_safety_penalty": -account["safety"] * weights.get("account_safety_direct_penalty", 0.03),
                "norm_claim_entitlement": normativity["claim_entitlement"] * weights.get("norm_claim_direct", 0.05),
                "norm_exit_penalty": -normativity["exit_justification"] * weights.get("norm_exit_direct_penalty", 0.04),
                "position_repair_partner": position["source_repair_partner"] * weights.get("position_repair_direct", 0.03),
                "position_withdrawer_penalty": -position["source_withdrawer"] * weights.get("position_withdrawer_direct_penalty", 0.035),
            },
        )
        inhibited = self._candidate(
            "inhibited_omission",
            "inhibited",
            self._inhibited_signal(affordance),
            source,
            affordance.target_process,
            clamp(affordance.ambiguity + 0.12),
            "the claim is present as avoidance rather than direct action",
            affordance.signal_type,
            None,
            tick_bias,
            {
                "speech_block": direct_speech_block * weights.get("speech_block", 0.28),
                "defensive_memory": defensive * weights.get("defensive_memory", 0.16),
                "fate_memory": fate * weights.get("fate_memory", 0.14),
                "conflict_pressure": conflict * weights.get("conflict_pressure", 0.1),
                "viability_direct_cost": direct_cost * weights.get("viability_inhibition_cost", 0.012),
                "viability_affordance_narrowing": affordance_narrowing * weights.get("viability_inhibition_narrowing", 0.01),
                "expected_refusal": expectation["refusal"] * weights.get("expected_refusal_inhibition", 0.08),
                "expected_withdrawal": expectation["withdrawal"] * weights.get("expected_withdrawal_inhibition", 0.05),
                "account_safety_pressure": account["safety"] * weights.get("account_safety_inhibition", 0.05),
                "account_energy_pressure": account["energy"] * weights.get("account_energy_inhibition", 0.04),
                "norm_legitimacy_contestation": normativity["legitimacy_contestation"] * weights.get("norm_legitimacy_inhibition", 0.04),
                "norm_exit_justification": normativity["exit_justification"] * weights.get("norm_exit_inhibition", 0.04),
                "position_defender": position["source_defender"] * weights.get("position_defender_inhibition", 0.035),
                "position_withdrawer": position["source_withdrawer"] * weights.get("position_withdrawer_inhibition", 0.035),
                "position_trapped": position["source_trapped_party"] * weights.get("position_trapped_inhibition", 0.03),
            },
        )
        practical = self._candidate(
            "practical_substitution",
            "substituted",
            "practical_repair",
            source,
            affordance.target_process,
            clamp(affordance.ambiguity + 0.04),
            "practical action substitutes for direct recognition",
            None,
            affordance.signal_type,
            tick_bias,
            {
                "repair_debt": repair_debt * weights.get("repair_debt", 0.18),
                "speech_block": direct_speech_block * weights.get("substitution_speech_block", 0.12),
                "defensive_memory": defensive * weights.get("substitution_defensive_memory", 0.1),
                "affordance_is_repairable": self._is_repairable(affordance.affordance_id) * weights.get("repairable_affordance", 0.16),
                "viability_direct_cost": direct_cost * weights.get("viability_substitution_cost", 0.01),
                "expected_repair_avoidance": expectation["repair_avoidance"] * weights.get("expected_repair_avoidance_substitution", 0.07),
                "account_relation_pressure": account["relation"] * weights.get("account_relation_substitution", 0.05),
                "norm_repair_obligation": normativity["repair_obligation"] * weights.get("norm_repair_substitution", 0.05),
                "norm_reciprocity_obligation": normativity["reciprocity_obligation"] * weights.get("norm_reciprocity_substitution", 0.035),
                "position_debtor": position["source_debtor"] * weights.get("position_debtor_substitution", 0.035),
                "position_caretaker": position["source_caretaker"] * weights.get("position_caretaker_substitution", 0.04),
            },
        )
        public = self._candidate(
            "public_substitution",
            "substituted",
            "public_politeness",
            source,
            affordance.target_process,
            clamp(affordance.ambiguity + 0.08),
            "publicly safe performance replaces private action",
            None,
            affordance.signal_type,
            tick_bias,
            {
                "audience": audience * weights.get("audience", 0.2),
                "face_risk": state.relation_metrics.get("face_risk_pressure", 0.0) * weights.get("face_risk", 0.16),
                "fate_memory": fate * weights.get("public_fate_memory", 0.08),
                "viability_face_constraint": face_constraint * weights.get("viability_face_constraint", 0.01),
                "expected_public_exposure": expectation["public_exposure"] * weights.get("expected_public_exposure", 0.08),
                "account_control_pressure": account["control"] * weights.get("account_control_public", 0.05),
                "norm_public_face_obligation": normativity["public_face_obligation"] * weights.get("norm_public_face", 0.06),
                "position_public_performer": position["source_public_performer"] * weights.get("position_public_performer", 0.04),
            },
        )
        claim = self._candidate(
            "recognition_claim",
            "escalated",
            "unacknowledged_help",
            "p1",
            "p2",
            clamp(affordance.ambiguity + 0.02),
            "recognition demand becomes explicit enough to alter the scene",
            None,
            affordance.signal_type,
            tick_bias,
            {
                "injury_memory": injury * weights.get("injury_memory", 0.14),
                "repair_debt": repair_debt * weights.get("claim_repair_debt", 0.1),
                "low_public_risk": (1.0 - audience) * weights.get("low_public_risk", 0.06),
                "viability_pressure": viability_pressure * weights.get("viability_claim_pressure", 0.01),
                "expected_refusal_escalation": expectation["refusal"] * weights.get("expected_refusal_escalation", 0.035),
                "account_dignity_pressure": account["dignity"] * weights.get("account_dignity_claim", 0.08),
                "account_meaning_pressure": account["meaning"] * weights.get("account_meaning_claim", 0.05),
                "norm_claim_entitlement": normativity["claim_entitlement"] * weights.get("norm_claim_escalation", 0.08),
                "norm_reciprocity_obligation": normativity["reciprocity_obligation"] * weights.get("norm_reciprocity_claim", 0.05),
                "norm_mutual_obligation": normativity["mutual_obligation"] * weights.get("norm_mutual_claim", 0.035),
                "position_claimant": position["source_claimant"] * weights.get("position_claimant_escalation", 0.04),
                "target_debtor": position["target_debtor"] * weights.get("position_target_debtor_claim", 0.035),
            },
        )
        return [direct, inhibited, practical, public, claim]

    def _candidate(
        self,
        action_id: str,
        action_mode: str,
        signal_type: str,
        source_process: str,
        target_process: str,
        ambiguity: float,
        relation_claim: str,
        inhibited_action: str | None,
        substituted_for: str | None,
        tick_bias: float,
        factors: dict[str, float],
    ) -> ActionCandidate:
        score = clamp(float(self.config.get("base_score", 0.03)) + tick_bias + sum(factors.values()))
        return ActionCandidate(
            action_id=action_id,
            action_mode=action_mode,
            signal_type=signal_type,
            source_process=source_process,
            target_process=target_process,
            score=score,
            inhibited_action=inhibited_action,
            substituted_for=substituted_for,
            ambiguity=ambiguity,
            relation_claim=relation_claim,
            evidence={key: round(value, 4) for key, value in factors.items() if abs(value) > 0.0001},
        )

    def _apply(self, state: SimulationState, action: ActionCandidate) -> None:
        state.relation_metrics["last_action_selection_score"] = action.score
        state.relation_metrics[f"action_mode.{action.action_mode}"] = state.relation_metrics.get(f"action_mode.{action.action_mode}", 0.0) + 1.0
        if action.action_mode == "inhibited" and action.source_process in state.processes:
            process = state.processes[action.source_process]
            process.speech_inhibition["direct_need"] = clamp(process.speech_inhibition.get("direct_need", 0.0) + 0.025)
            state.relation_metrics["conflict_pressure"] = clamp(state.relation_metrics.get("conflict_pressure", 0.0) + 0.015)
        if action.action_mode == "substituted":
            state.relation_metrics["repair_debt"] = clamp(state.relation_metrics.get("repair_debt", 0.0) + 0.01)

    def _inhibited_signal(self, affordance: AffordanceCandidate) -> str:
        if affordance.signal_type in {"delayed_reply", "short_answer"}:
            return "delayed_reply"
        if affordance.signal_type in {"public_politeness", "care_instruction"}:
            return "gaze_avoidance"
        return "short_answer"

    def _is_repairable(self, affordance_id: str) -> float:
        return 1.0 if affordance_id in {"practical_repair_offer", "material_pressure_intrusion", "care_intervention"} else 0.0

    def _expectation_context(self, state: SimulationState, source: str, target: str) -> dict[str, float]:
        prefix = f"expectation.{source}.{target}."
        fallback = "expectation.p1.p2."
        return {
            "refusal": state.relation_metrics.get(prefix + "refusal_expectation", state.relation_metrics.get(fallback + "refusal_expectation", 0.0)),
            "misrecognition": state.relation_metrics.get(prefix + "misrecognition_expectation", state.relation_metrics.get(fallback + "misrecognition_expectation", 0.0)),
            "withdrawal": state.relation_metrics.get(prefix + "withdrawal_expectation", state.relation_metrics.get(fallback + "withdrawal_expectation", 0.0)),
            "public_exposure": state.relation_metrics.get(prefix + "public_exposure_expectation", state.relation_metrics.get(fallback + "public_exposure_expectation", 0.0)),
            "repair_avoidance": state.relation_metrics.get(prefix + "repair_avoidance_expectation", state.relation_metrics.get(fallback + "repair_avoidance_expectation", 0.0)),
        }

    def _account_context(self, state: SimulationState, process_id: str) -> dict[str, float]:
        return {
            account: state.relation_metrics.get(f"account_pressure.{process_id}.{account}", 0.0)
            for account in ["safety", "dignity", "control", "relation", "meaning", "energy"]
        }

    def _normativity_context(self, state: SimulationState, source: str, target: str) -> dict[str, float]:
        prefix = f"norm_pressure.{source}.{target}."
        reverse = f"norm_pressure.{target}.{source}."
        return {
            "claim_entitlement": state.relation_metrics.get(prefix + "claim_entitlement", 0.0),
            "repair_obligation": state.relation_metrics.get(prefix + "repair_obligation", state.relation_metrics.get(reverse + "repair_obligation", 0.0)),
            "legitimacy_contestation": state.relation_metrics.get(prefix + "legitimacy_contestation", state.relation_metrics.get(reverse + "legitimacy_contestation", 0.0)),
            "public_face_obligation": state.relation_metrics.get(prefix + "public_face_obligation", state.relation_metrics.get(reverse + "public_face_obligation", 0.0)),
            "reciprocity_obligation": state.relation_metrics.get(prefix + "reciprocity_obligation", state.relation_metrics.get(reverse + "reciprocity_obligation", 0.0)),
            "exit_justification": state.relation_metrics.get(prefix + "exit_justification", 0.0),
            "mutual_obligation": state.relation_metrics.get(prefix + "mutual_obligation", state.relation_metrics.get(reverse + "mutual_obligation", 0.0)),
            "irreversible_precedent": state.relation_metrics.get(prefix + "irreversible_precedent", state.relation_metrics.get(reverse + "irreversible_precedent", 0.0)),
        }

    def _position_context(self, state: SimulationState, source: str, target: str) -> dict[str, float]:
        positions = [
            "claimant",
            "debtor",
            "defender",
            "caretaker",
            "controlled",
            "public_performer",
            "withdrawer",
            "trapped_party",
            "repair_partner",
            "bound_party",
        ]
        result: dict[str, float] = {}
        for prefix, process_id in (("source", source), ("target", target)):
            for position in positions:
                result[f"{prefix}_{position}"] = state.relation_metrics.get(f"position_field.{process_id}.{position}", 0.0)
        return result

    def _viability_context(self, events: list[Event]) -> dict[str, Any]:
        requirements = [event for event in events if event.event_type == "ViabilityRequirementEvent"]
        widths = [event for event in events if event.event_type == "AffordanceWidthEvent"]
        constraints = [event for event in events if event.event_type == "ConstraintActivationEvent"]
        viability_pressure = max((self._payload_float(event, "urgency") for event in requirements), default=0.0)
        direct_response_cost = max((self._payload_float(event, "direct_response_cost") for event in widths), default=0.0)
        min_width = min((self._payload_float(event, "width", 1.0) for event in widths), default=1.0)
        affordance_narrowing = clamp(1.0 - min_width)
        face_constraint = max(
            (
                self._payload_float(event, "intensity")
                for event in constraints
                if event.payload.get("constraint_type") == "public_face_risk"
            ),
            default=0.0,
        )
        refs = sorted({event.event_id for event in constraints + requirements + widths})
        return {
            "viability_pressure": viability_pressure,
            "direct_response_cost": direct_response_cost,
            "affordance_narrowing": affordance_narrowing,
            "face_constraint": face_constraint,
            "evidence_refs": refs,
        }

    def _payload_float(self, event: Event, key: str, default: float = 0.0) -> float:
        value = event.payload.get(key, default)
        try:
            return clamp(float(value))
        except (TypeError, ValueError):
            return default
