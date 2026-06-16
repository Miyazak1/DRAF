from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from rpf.core.events import Event
from rpf.core.models import SimulationState, TickContext, clamp


@dataclass(frozen=True)
class CommonGroundUpdate:
    common_ground_id: str
    state: str
    mutual_legibility: float
    interpretive_gap: float
    shared_definition_width: float
    repair_handle_width: float
    dominant_frame: str
    contested_fact: str
    consequence: str
    evidence: dict[str, float | str]
    causal_refs: list[str]

    def payload(self) -> dict[str, Any]:
        return {
            "common_ground_id": self.common_ground_id,
            "state": self.state,
            "mutual_legibility": round(self.mutual_legibility, 4),
            "interpretive_gap": round(self.interpretive_gap, 4),
            "shared_definition_width": round(self.shared_definition_width, 4),
            "repair_handle_width": round(self.repair_handle_width, 4),
            "dominant_frame": self.dominant_frame,
            "contested_fact": self.contested_fact,
            "consequence": self.consequence,
            "evidence": self.evidence,
            "caused_by_events": self.causal_refs,
        }


class CommonGroundEngine:
    """Track whether participants can treat the interaction as the same reality."""

    def update(self, state: SimulationState, context: TickContext, local_events: list[Event]) -> CommonGroundUpdate | None:
        recognition = self._latest(local_events, "RecognitionEvent")
        epistemic = self._latest(local_events, "EpistemicBoundaryEvent")
        expression = self._latest(local_events, "ExpressionSelectionEvent")
        action = self._latest(local_events, "ActionSelectionEvent")
        frame_events = [event for event in local_events if event.event_type == "FrameDefinitionEvent"]
        if not recognition and not epistemic and not frame_events:
            return None
        outcome = str(recognition.get("outcome") or recognition.get("result") or "")
        expression_mode = str(expression.get("expression_mode", ""))
        action_mode = str(action.get("action_mode", ""))
        epistemic_pressure = self._float(epistemic, "pressure")
        speakability = self._float(epistemic, "speakability_width", default=1.0)
        public_private_gap = float(state.relation_metrics.get("public_private_gap", 0.0) or 0.0)
        repair_debt = float(state.relation_metrics.get("repair_debt", 0.0) or 0.0)
        recognition_debt = float(state.relation_metrics.get("relation_sediment.recognition_debt", 0.0) or 0.0)
        frame_scores = self._frame_scores(state, frame_events)
        dominant_frame = max(frame_scores.items(), key=lambda item: item[1])[0] if frame_scores else "unknown"
        frame_contention = self._frame_contention(frame_scores)
        expectation_load = self._expectation_load(state)
        bad_recognition = 1.0 if outcome in {"refused", "misunderstood", "displaced", "postponed", "unspeakable"} else 0.0
        repair_recognition = 1.0 if outcome in {"granted", "partial"} else 0.0
        expression_gap = {
            "silence": 0.14,
            "timing_distortion": 0.09,
            "gesture": 0.06,
            "public_performance": 0.1,
            "tonal_shift": 0.07,
        }.get(expression_mode, 0.03)
        action_gap = {
            "inhibited": 0.12,
            "substituted": 0.08,
            "escalated": 0.09,
        }.get(action_mode, 0.03)
        interpretive_gap = clamp(
            bad_recognition * 0.2
            + epistemic_pressure * 0.2
            + (1.0 - speakability) * 0.12
            + frame_contention * 0.18
            + expectation_load * 0.12
            + public_private_gap * 0.12
            + recognition_debt * 0.08
            + expression_gap
            + action_gap
        )
        shared_width = clamp(
            1.0
            - interpretive_gap * 0.55
            - epistemic_pressure * 0.18
            - public_private_gap * 0.12
            + repair_recognition * 0.12
            + frame_scores.get("repair_scene", 0.0) * 0.08
        )
        mutual_legibility = clamp(shared_width - expectation_load * 0.12 - bad_recognition * 0.08 + repair_recognition * 0.08)
        repair_handle_width = clamp(shared_width - repair_debt * 0.28 - recognition_debt * 0.16 + repair_recognition * 0.1)
        cg_state = self._state(interpretive_gap, shared_width, repair_handle_width)
        update = CommonGroundUpdate(
            common_ground_id=f"cg-{state.tick:04d}-{cg_state}",
            state=cg_state,
            mutual_legibility=mutual_legibility,
            interpretive_gap=interpretive_gap,
            shared_definition_width=shared_width,
            repair_handle_width=repair_handle_width,
            dominant_frame=dominant_frame,
            contested_fact=str(epistemic.get("focus_label") or epistemic.get("focus_id") or dominant_frame),
            consequence=self._consequence(cg_state),
            evidence={
                "tick_type": context.tick_type,
                "recognition_outcome": outcome or "none",
                "expression_mode": expression_mode or "none",
                "action_mode": action_mode or "none",
                "epistemic_pressure": round(epistemic_pressure, 4),
                "speakability_width": round(speakability, 4),
                "frame_contention": round(frame_contention, 4),
                "expectation_load": round(expectation_load, 4),
                "public_private_gap": round(public_private_gap, 4),
                "repair_debt": round(repair_debt, 4),
                "recognition_debt": round(recognition_debt, 4),
            },
            causal_refs=self._causal_refs(local_events),
        )
        self._apply(state, update)
        return update

    def _apply(self, state: SimulationState, update: CommonGroundUpdate) -> None:
        gap = update.interpretive_gap
        state.relation_metrics["common_ground.fracture"] = clamp(
            float(state.relation_metrics.get("common_ground.fracture", 0.0) or 0.0) * 0.78 + gap * 0.22
        )
        state.relation_metrics["common_ground.mutual_legibility"] = clamp(
            float(state.relation_metrics.get("common_ground.mutual_legibility", 0.45) or 0.45) * 0.65
            + update.mutual_legibility * 0.35
        )
        state.relation_metrics["common_ground.repair_handle_width"] = clamp(
            float(state.relation_metrics.get("common_ground.repair_handle_width", 0.5) or 0.5) * 0.68
            + update.repair_handle_width * 0.32
        )
        state.relation_metrics[f"common_ground.state.{update.state}"] = clamp(
            float(state.relation_metrics.get(f"common_ground.state.{update.state}", 0.0) or 0.0) * 0.82
            + gap * 0.18
        )
        if update.state in {"contested", "fractured"}:
            state.relation_metrics["relation_sediment.recognition_debt"] = clamp(
                float(state.relation_metrics.get("relation_sediment.recognition_debt", 0.0) or 0.0) + gap * 0.01
            )
            state.relation_metrics["relation_sediment.repair_access_narrowing"] = clamp(
                float(state.relation_metrics.get("relation_sediment.repair_access_narrowing", 0.0) or 0.0) + gap * 0.007
            )
        if update.state == "fractured":
            state.relation_metrics["public_private_gap"] = clamp(float(state.relation_metrics.get("public_private_gap", 0.0) or 0.0) + gap * 0.006)
        if update.state in {"shared", "fragile"}:
            state.relation_metrics["repair_debt"] = clamp(float(state.relation_metrics.get("repair_debt", 0.0) or 0.0) - update.repair_handle_width * 0.004)

    def _state(self, interpretive_gap: float, shared_width: float, repair_width: float) -> str:
        if interpretive_gap >= 0.62 or shared_width <= 0.34:
            return "fractured"
        if interpretive_gap >= 0.42 or repair_width <= 0.34:
            return "contested"
        if interpretive_gap >= 0.24 or shared_width <= 0.62:
            return "fragile"
        return "shared"

    def _consequence(self, state: str) -> str:
        return {
            "shared": "the relation can still use the same facts as repair handles",
            "fragile": "the same words can still work, but only with careful framing",
            "contested": "each side can treat the same scene as evidence for a different reality",
            "fractured": "the relation no longer has a stable shared reality for direct repair",
        }[state]

    def _frame_scores(self, state: SimulationState, frame_events: list[Event]) -> dict[str, float]:
        scores = {
            key.removeprefix("frame_definition."): float(value or 0.0)
            for key, value in state.relation_metrics.items()
            if key.startswith("frame_definition.")
        }
        for event in frame_events:
            frame_type = str(event.payload.get("frame_type", ""))
            if frame_type:
                scores[frame_type] = max(scores.get(frame_type, 0.0), self._float(event.payload, "new_value"))
        return scores

    def _frame_contention(self, scores: dict[str, float]) -> float:
        active = sorted((value for value in scores.values() if value > 0.04), reverse=True)
        if len(active) < 2:
            return active[0] * 0.25 if active else 0.0
        return clamp(min(active[0], active[1]) * 0.55 + len(active[:4]) * 0.035)

    def _expectation_load(self, state: SimulationState) -> float:
        values = [
            float(value or 0.0)
            for key, value in state.relation_metrics.items()
            if key.startswith("expectation.")
        ]
        return clamp(sum(values) / max(1, len(values))) if values else 0.0

    def _causal_refs(self, events: list[Event]) -> list[str]:
        relevant = {
            "RecognitionEvent",
            "EpistemicBoundaryEvent",
            "FrameDefinitionEvent",
            "ExpectationSedimentationEvent",
            "ActionSelectionEvent",
            "ExpressionSelectionEvent",
            "ObservationEvent",
        }
        refs = {event.event_id for event in events[-16:] if event.event_type in relevant}
        if not refs:
            refs = {event.event_id for event in events[-5:]}
        return sorted(refs)

    def _latest(self, events: list[Event], event_type: str) -> dict[str, Any]:
        for event in reversed(events):
            if event.event_type == event_type:
                return event.payload
        return {}

    def _float(self, payload: dict[str, Any], key: str, default: float = 0.0) -> float:
        try:
            return clamp(float(payload.get(key, default)))
        except (TypeError, ValueError):
            return clamp(default)
