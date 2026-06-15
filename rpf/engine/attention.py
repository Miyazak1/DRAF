from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from rpf.core.events import Event
from rpf.core.models import SimulationState, TickContext, clamp


@dataclass(frozen=True)
class AttentionDrift:
    process_id: str
    dominant_focus: str
    previous_focus: str
    drift_intensity: float
    focus_scores: dict[str, float]
    reason: str
    causal_refs: list[str]

    def payload(self) -> dict[str, Any]:
        return {
            "process_id": self.process_id,
            "dominant_focus": self.dominant_focus,
            "previous_focus": self.previous_focus,
            "drift_intensity": round(self.drift_intensity, 4),
            "focus_scores": {key: round(value, 4) for key, value in self.focus_scores.items()},
            "reason": self.reason,
            "caused_by_events": self.causal_refs,
        }


class AttentionDriftEngine:
    """Model how process attention is pulled by competing situated pressures.

    This is not a private motive meter. It records which concerns become
    practically focal because field, relation, body, case, and witness pressures
    make them hard to ignore.
    """

    def __init__(self) -> None:
        self.current_focus: dict[str, str] = {}
        self.focus_strength: dict[str, float] = {}

    def update(self, state: SimulationState, context: TickContext, local_events: list[Event]) -> list[AttentionDrift]:
        refs = [event.event_id for event in local_events if event.event_type in self._evidence_event_types()][-8:]
        if not refs:
            refs = [event.event_id for event in local_events if event.event_type == "TickStartedEvent"][-1:]
        results: list[AttentionDrift] = []
        for process_id in state.processes:
            scores = self._scores(state, process_id, context, local_events)
            if not scores:
                continue
            dominant_focus = max(scores.items(), key=lambda item: (item[1], item[0]))[0]
            previous_focus = self.current_focus.get(process_id, "none")
            previous_strength = self.focus_strength.get(process_id, 0.0)
            dominant_strength = scores[dominant_focus]
            drift_intensity = clamp(abs(dominant_strength - previous_strength) + (0.08 if dominant_focus != previous_focus else 0.0))
            if drift_intensity <= 0.015:
                continue
            self.current_focus[process_id] = dominant_focus
            self.focus_strength[process_id] = dominant_strength
            state.relation_metrics[f"attention_drift.{process_id}.{dominant_focus}"] = clamp(
                float(state.relation_metrics.get(f"attention_drift.{process_id}.{dominant_focus}", 0.0) or 0.0) * 0.72
                + dominant_strength * 0.28
            )
            process = state.processes[process_id]
            process.relevance_triggers[dominant_focus] = max(process.relevance_triggers.get(dominant_focus, 0.0), dominant_strength)
            results.append(
                AttentionDrift(
                    process_id=process_id,
                    dominant_focus=dominant_focus,
                    previous_focus=previous_focus,
                    drift_intensity=drift_intensity,
                    focus_scores=scores,
                    reason=self._reason(dominant_focus, scores, context),
                    causal_refs=refs,
                )
            )
        return results

    def _scores(
        self,
        state: SimulationState,
        process_id: str,
        context: TickContext,
        local_events: list[Event],
    ) -> dict[str, float]:
        process = state.processes[process_id]
        daily = self._latest(local_events, "DailyEcologyEvent")
        witness = self._latest(local_events, "WitnessStrategyEvent")
        inquiry = self._latest(local_events, "InvestigationUpdateEvent")
        recognition = self._latest(local_events, "RecognitionEvent")
        memory_count = sum(1 for event in local_events if event.event_type == "MemoryReconstructionEvent" and event.payload.get("owner_process_id") == process_id)
        body_load = self._payload_float(daily, "body_load")
        unfinished = self._payload_float(daily, "unfinished_tasks")
        waiting = self._payload_float(daily, "waiting_pressure")
        route = self._payload_float(daily, "route_friction")
        confirmation_risk = self._payload_float(witness, "confirmation_risk")
        disclosure = self._payload_float(witness, "disclosure_width")
        case_risk = self._nested_float(inquiry, "state_after", "relationship_risk")
        case_progress = self._nested_float(inquiry, "state_after", "progress")
        scores = {
            "body_management": clamp(process.fatigue * 0.34 + body_load * 0.34 + unfinished * 0.12),
            "case_fixation": clamp(
                process.relevance_triggers.get("case_focus", 0.0) * 0.28
                + process.relevance_triggers.get("procedural_gap", 0.0) * 0.22
                + case_progress * 0.18
                + case_risk * 0.12
            ),
            "threat_monitoring": clamp(
                max(process.threat_sensitivity.values(), default=0.0) * 0.28
                + confirmation_risk * 0.24
                + state.relation_metrics.get("conflict_pressure", 0.0) * 0.14
                + waiting * 0.12
            ),
            "repair_opportunity": clamp(
                process.relevance_triggers.get("repair_opening", 0.0) * 0.24
                + disclosure * 0.18
                + state.relation_metrics.get("repair_debt", 0.0) * 0.12
                + (recognition.get("result") in {"partial", "granted"}) * 0.12
            ),
            "avoidance_route": clamp(
                process.speech_inhibition.get("direct_need", 0.0) * 0.2
                + process.speech_inhibition.get("apology", 0.0) * 0.18
                + route * 0.18
                + (context.tick_type == "latent") * 0.08
            ),
            "memory_intrusion": clamp(
                memory_count * 0.12
                + state.relation_metrics.get("memory_pressure", 0.0) * 0.18
                + state.relation_metrics.get("relation_sediment.memory_saturation", 0.0) * 0.12
            ),
        }
        return {key: value for key, value in scores.items() if value > 0.01}

    def _reason(self, focus: str, scores: dict[str, float], context: TickContext) -> str:
        evidence = ", ".join(f"{key}={value:.2f}" for key, value in sorted(scores.items(), key=lambda item: item[1], reverse=True)[:3])
        return f"{focus} became dominant under {context.tick_type} pressure ({evidence})"

    def _latest(self, events: list[Event], event_type: str) -> dict[str, Any]:
        for event in reversed(events):
            if event.event_type == event_type:
                return event.payload
        return {}

    def _payload_float(self, payload: dict[str, Any], key: str) -> float:
        try:
            return clamp(float(payload.get(key, 0.0)))
        except (TypeError, ValueError):
            return 0.0

    def _nested_float(self, payload: dict[str, Any], parent: str, key: str) -> float:
        value = payload.get(parent, {}) if isinstance(payload, dict) else {}
        if not isinstance(value, dict):
            return 0.0
        return self._payload_float(value, key)

    def _evidence_event_types(self) -> set[str]:
        return {
            "TickStartedEvent",
            "DailyEcologyEvent",
            "WitnessStrategyEvent",
            "InvestigationUpdateEvent",
            "RecognitionEvent",
            "MemoryReconstructionEvent",
            "DispositionSedimentationEvent",
            "FrameDefinitionEvent",
        }
