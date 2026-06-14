from __future__ import annotations

from dataclasses import dataclass
from typing import Any

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

    def select(self, state: SimulationState, context: TickContext, affordance: AffordanceCandidate) -> ActionCandidate:
        candidates = self._candidates(state, context, affordance)
        selected = max(candidates, key=lambda item: (item.score, item.action_id))
        self._apply(state, selected)
        self.last_diagnostics = {
            "tick": state.tick,
            "tick_type": context.tick_type,
            "affordance_id": affordance.affordance_id,
            "selected_action": selected.__dict__,
            "candidates": [candidate.__dict__ for candidate in sorted(candidates, key=lambda item: item.score, reverse=True)],
        }
        return selected

    def _candidates(self, state: SimulationState, context: TickContext, affordance: AffordanceCandidate) -> list[ActionCandidate]:
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
        weights = self.config.get("weights", {})
        tick_bias = (self.config.get("tick_bias") or {}).get(context.tick_type, 0.0)

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
