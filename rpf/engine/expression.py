from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from rpf.core.models import SimulationState, TickContext, clamp
from rpf.core.semantics import defensive_memory, fate_memory, injury_memory, memory_pressure
from rpf.engine.actions import ActionCandidate


@dataclass(frozen=True)
class ExpressionCandidate:
    expression_id: str
    expression_mode: str
    surface_signal: str
    tone: str
    gesture: str
    timing: str
    intensity: float
    ambiguity: float
    relation_claim: str
    score: float
    evidence: dict[str, float]


class ExpressionEngine:
    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config
        self.last_diagnostics: dict[str, Any] = {}

    def select(self, state: SimulationState, context: TickContext, action: ActionCandidate) -> ExpressionCandidate:
        candidates = self._candidates(state, context, action)
        selected = max(candidates, key=lambda item: (item.score, item.expression_id))
        self._apply(state, selected)
        self.last_diagnostics = {
            "tick": state.tick,
            "tick_type": context.tick_type,
            "action_id": action.action_id,
            "selected_expression": selected.__dict__,
            "candidates": [candidate.__dict__ for candidate in sorted(candidates, key=lambda item: item.score, reverse=True)],
        }
        return selected

    def _candidates(self, state: SimulationState, context: TickContext, action: ActionCandidate) -> list[ExpressionCandidate]:
        source_state = state.processes.get(action.source_process)
        fatigue = source_state.fatigue if source_state else 0.0
        speech_block = 0.0
        if source_state:
            speech_block = max(
                source_state.speech_inhibition.get("direct_need", 0.0),
                source_state.speech_inhibition.get("apology", 0.0),
                source_state.speech_inhibition.get("anger", 0.0),
                source_state.speech_inhibition.get("dependency_admission", 0.0),
            )
        audience = max(state.field_state.audience_pressure.values(), default=0.0)
        conflict = state.relation_metrics.get("conflict_pressure", 0.0)
        repair_debt = state.relation_metrics.get("repair_debt", 0.0)
        history = memory_pressure(state)
        injury = injury_memory(state)
        defensive = defensive_memory(state)
        fate = fate_memory(state)
        weights = self.config.get("weights", {})
        tick_bias = (self.config.get("tick_bias") or {}).get(context.tick_type, 0.0)

        plain = self._candidate(
            "plain_speech",
            "spoken",
            action.signal_type,
            "plain",
            "minimal",
            "direct",
            action.ambiguity,
            action.relation_claim,
            tick_bias,
            {
                "action_score": action.score * weights.get("action_score", 0.35),
                "low_speech_block": (1.0 - speech_block) * weights.get("low_speech_block", 0.18),
                "low_audience": (1.0 - audience) * weights.get("low_audience", 0.05),
            },
        )
        tightened = self._candidate(
            "tightened_tone",
            "tonal_shift",
            action.signal_type,
            "controlled",
            "stillness",
            "slight_delay",
            clamp(action.ambiguity + 0.05),
            f"{action.relation_claim}; control is part of the signal",
            tick_bias,
            {
                "conflict_pressure": conflict * weights.get("conflict_pressure", 0.18),
                "repair_debt": repair_debt * weights.get("repair_debt", 0.12),
                "audience": audience * weights.get("audience", 0.08),
            },
        )
        hesitation = self._candidate(
            "hesitation",
            "timing_distortion",
            "short_answer" if action.signal_type not in {"delayed_reply", "gaze_avoidance"} else action.signal_type,
            "uncertain",
            "interrupted_movement",
            "pause_before_response",
            clamp(action.ambiguity + 0.12),
            f"{action.relation_claim}; the delay becomes meaningful",
            tick_bias,
            {
                "speech_block": speech_block * weights.get("speech_block", 0.2),
                "fatigue": fatigue * weights.get("fatigue", 0.12),
                "memory_pressure": history * weights.get("memory_pressure", 0.1),
            },
        )
        gesture = self._candidate(
            "gesture_displacement",
            "gesture",
            "gaze_avoidance",
            "indirect",
            "looks_away_or_handles_object",
            "before_speech",
            clamp(action.ambiguity + 0.14),
            "the body carries the claim before speech can",
            tick_bias,
            {
                "defensive_memory": defensive * weights.get("defensive_memory", 0.16),
                "fate_memory": fate * weights.get("fate_memory", 0.12),
                "action_inhibited": (1.0 if action.action_mode == "inhibited" else 0.0) * weights.get("inhibited_action", 0.18),
            },
        )
        silence = self._candidate(
            "charged_silence",
            "silence",
            "delayed_reply",
            "silent",
            "no_answer",
            "absence_extends",
            clamp(action.ambiguity + 0.2),
            "non-response becomes a relational act",
            tick_bias,
            {
                "injury_memory": injury * weights.get("injury_memory", 0.12),
                "defensive_memory": defensive * weights.get("silence_defensive_memory", 0.12),
                "fate_memory": fate * weights.get("silence_fate_memory", 0.1),
                "action_inhibited": (1.0 if action.action_mode == "inhibited" else 0.0) * weights.get("silence_inhibited_action", 0.16),
            },
        )
        public = self._candidate(
            "public_mask",
            "public_performance",
            "public_politeness",
            "polite",
            "social_smile",
            "on_time",
            clamp(action.ambiguity + 0.08),
            "public form protects against private exposure",
            tick_bias,
            {
                "audience": audience * weights.get("public_audience", 0.22),
                "face_risk": state.relation_metrics.get("face_risk_pressure", 0.0) * weights.get("face_risk", 0.16),
                "action_substituted": (1.0 if action.action_mode == "substituted" else 0.0) * weights.get("substituted_action", 0.1),
            },
        )
        return [plain, tightened, hesitation, gesture, silence, public]

    def _candidate(
        self,
        expression_id: str,
        expression_mode: str,
        surface_signal: str,
        tone: str,
        gesture: str,
        timing: str,
        ambiguity: float,
        relation_claim: str,
        tick_bias: float,
        factors: dict[str, float],
    ) -> ExpressionCandidate:
        score = clamp(float(self.config.get("base_score", 0.03)) + tick_bias + sum(factors.values()))
        return ExpressionCandidate(
            expression_id=expression_id,
            expression_mode=expression_mode,
            surface_signal=surface_signal,
            tone=tone,
            gesture=gesture,
            timing=timing,
            intensity=score,
            ambiguity=ambiguity,
            relation_claim=relation_claim,
            score=score,
            evidence={key: round(value, 4) for key, value in factors.items() if abs(value) > 0.0001},
        )

    def _apply(self, state: SimulationState, expression: ExpressionCandidate) -> None:
        state.relation_metrics["last_expression_score"] = expression.score
        state.relation_metrics[f"expression_mode.{expression.expression_mode}"] = state.relation_metrics.get(f"expression_mode.{expression.expression_mode}", 0.0) + 1.0
        if expression.expression_mode == "silence":
            state.relation_metrics["silence_charge"] = clamp(state.relation_metrics.get("silence_charge", 0.0) + 0.02)
        if expression.expression_mode in {"gesture", "timing_distortion"}:
            state.relation_metrics["conflict_pressure"] = clamp(state.relation_metrics.get("conflict_pressure", 0.0) + 0.01)
