from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from rpf.core.events import Event
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

    def select(
        self,
        state: SimulationState,
        context: TickContext,
        action: ActionCandidate,
        viability_events: list[Event] | None = None,
    ) -> ExpressionCandidate:
        viability = self._viability_context(viability_events or [], action)
        candidates = self._candidates(state, context, action, viability)
        selected = max(candidates, key=lambda item: (item.score, item.expression_id))
        self._apply(state, selected)
        self.last_diagnostics = {
            "tick": state.tick,
            "tick_type": context.tick_type,
            "action_id": action.action_id,
            "viability_context": viability,
            "selected_expression": selected.__dict__,
            "candidates": [candidate.__dict__ for candidate in sorted(candidates, key=lambda item: item.score, reverse=True)],
        }
        return selected

    def _candidates(
        self,
        state: SimulationState,
        context: TickContext,
        action: ActionCandidate,
        viability: dict[str, Any],
    ) -> list[ExpressionCandidate]:
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
        expectation = self._expectation_context(state, action.source_process, action.target_process)
        account = self._account_context(state, action.source_process)
        normativity = self._normativity_context(state, action.source_process, action.target_process)
        frame = self._frame_context(state)
        weights = self.config.get("weights", {})
        tick_bias = (self.config.get("tick_bias") or {}).get(context.tick_type, 0.0)
        viability_pressure = float(viability["viability_pressure"])
        direct_cost = float(viability["direct_response_cost"])
        affordance_narrowing = float(viability["affordance_narrowing"])
        deformation_pressure = float(viability["deformation_pressure"])
        face_constraint = float(viability["face_constraint"])

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
                "viability_direct_space": (1.0 - deformation_pressure) * weights.get("viability_direct_space", 0.01),
                "expected_misrecognition_penalty": -expectation["misrecognition"] * weights.get("expected_misrecognition_plain_penalty", 0.05),
                "account_energy_penalty": -account["energy"] * weights.get("account_energy_plain_penalty", 0.04),
                "norm_claim_entitlement": normativity["claim_entitlement"] * weights.get("norm_claim_plain", 0.04),
                "norm_public_face_penalty": -normativity["public_face_obligation"] * weights.get("norm_face_plain_penalty", 0.035),
                "frame_repair_scene": frame["repair_scene"] * weights.get("frame_repair_plain", 0.035),
                "frame_avoidance_penalty": -frame["avoidance_scene"] * weights.get("frame_avoidance_plain_penalty", 0.035),
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
                "viability_pressure": viability_pressure * weights.get("viability_pressure", 0.015),
                "viability_direct_cost": direct_cost * weights.get("viability_direct_cost", 0.01),
                "expected_refusal": expectation["refusal"] * weights.get("expected_refusal_tone", 0.05),
                "account_dignity_pressure": account["dignity"] * weights.get("account_dignity_tone", 0.05),
                "account_control_pressure": account["control"] * weights.get("account_control_tone", 0.04),
                "norm_legitimacy_contestation": normativity["legitimacy_contestation"] * weights.get("norm_legitimacy_tone", 0.05),
                "norm_reciprocity_obligation": normativity["reciprocity_obligation"] * weights.get("norm_reciprocity_tone", 0.04),
                "frame_debt_accounting": frame["debt_accounting"] * weights.get("frame_debt_tone", 0.04),
                "frame_recognition_trial": frame["recognition_trial"] * weights.get("frame_trial_tone", 0.04),
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
                "viability_affordance_narrowing": affordance_narrowing * weights.get("viability_affordance_narrowing", 0.015),
                "viability_direct_cost": direct_cost * weights.get("viability_timing_cost", 0.012),
                "expected_misrecognition": expectation["misrecognition"] * weights.get("expected_misrecognition_timing", 0.06),
                "expected_withdrawal": expectation["withdrawal"] * weights.get("expected_withdrawal_timing", 0.04),
                "account_energy_pressure": account["energy"] * weights.get("account_energy_timing", 0.05),
                "norm_exit_justification": normativity["exit_justification"] * weights.get("norm_exit_timing", 0.035),
                "norm_irreversible_precedent": normativity["irreversible_precedent"] * weights.get("norm_precedent_timing", 0.035),
                "frame_avoidance_scene": frame["avoidance_scene"] * weights.get("frame_avoidance_timing", 0.04),
                "frame_double_bind": frame["double_bind"] * weights.get("frame_double_bind_timing", 0.035),
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
                "viability_deformation_pressure": deformation_pressure * weights.get("viability_gesture_pressure", 0.015),
                "expected_repair_avoidance": expectation["repair_avoidance"] * weights.get("expected_repair_avoidance_gesture", 0.05),
                "account_relation_pressure": account["relation"] * weights.get("account_relation_gesture", 0.04),
                "norm_repair_obligation": normativity["repair_obligation"] * weights.get("norm_repair_gesture", 0.04),
                "frame_avoidance_scene": frame["avoidance_scene"] * weights.get("frame_avoidance_gesture", 0.04),
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
                "viability_deformation_pressure": deformation_pressure * weights.get("viability_silence_pressure", 0.015),
                "viability_direct_cost": direct_cost * weights.get("viability_silence_cost", 0.01),
                "expected_refusal": expectation["refusal"] * weights.get("expected_refusal_silence", 0.06),
                "expected_withdrawal": expectation["withdrawal"] * weights.get("expected_withdrawal_silence", 0.05),
                "account_safety_pressure": account["safety"] * weights.get("account_safety_silence", 0.04),
                "account_meaning_pressure": account["meaning"] * weights.get("account_meaning_silence", 0.04),
                "norm_legitimacy_contestation": normativity["legitimacy_contestation"] * weights.get("norm_legitimacy_silence", 0.04),
                "norm_exit_justification": normativity["exit_justification"] * weights.get("norm_exit_silence", 0.035),
                "frame_avoidance_scene": frame["avoidance_scene"] * weights.get("frame_avoidance_silence", 0.05),
                "frame_double_bind": frame["double_bind"] * weights.get("frame_double_bind_silence", 0.035),
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
                "viability_face_constraint": face_constraint * weights.get("viability_face_constraint", 0.015),
                "expected_public_exposure": expectation["public_exposure"] * weights.get("expected_public_exposure_mask", 0.07),
                "account_control_pressure": account["control"] * weights.get("account_control_mask", 0.05),
                "norm_public_face_obligation": normativity["public_face_obligation"] * weights.get("norm_public_face_mask", 0.07),
                "frame_public_performance": frame["public_performance"] * weights.get("frame_public_mask", 0.07),
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

    def _frame_context(self, state: SimulationState) -> dict[str, float]:
        return {
            frame_type: state.relation_metrics.get(f"frame_definition.{frame_type}", 0.0)
            for frame_type in [
                "debt_accounting",
                "repair_scene",
                "avoidance_scene",
                "public_performance",
                "care_control",
                "double_bind",
                "material_accounting",
                "recognition_trial",
            ]
        }

    def _viability_context(self, events: list[Event], action: ActionCandidate) -> dict[str, Any]:
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
        action_deformation = {
            "enacted": 0.05,
            "escalated": 0.25,
            "substituted": 0.55,
            "inhibited": 0.75,
        }.get(action.action_mode, 0.3)
        deformation_pressure = clamp(
            viability_pressure * 0.32
            + direct_response_cost * 0.34
            + affordance_narrowing * 0.18
            + face_constraint * 0.08
            + action_deformation * 0.08
        )
        refs = sorted({event.event_id for event in constraints + requirements + widths})
        return {
            "viability_pressure": viability_pressure,
            "direct_response_cost": direct_response_cost,
            "affordance_narrowing": affordance_narrowing,
            "face_constraint": face_constraint,
            "deformation_pressure": deformation_pressure,
            "evidence_refs": refs,
        }

    def _payload_float(self, event: Event, key: str, default: float = 0.0) -> float:
        value = event.payload.get(key, default)
        try:
            return clamp(float(value))
        except (TypeError, ValueError):
            return default
