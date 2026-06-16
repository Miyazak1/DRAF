from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from rpf.core.events import Event
from rpf.core.models import SimulationState, TickContext, clamp


@dataclass(frozen=True)
class EpistemicBoundary:
    boundary_id: str
    boundary_type: str
    focus_id: str
    focus_label: str
    knownness_asymmetry: float
    speakability_width: float
    disclosure_risk: float
    contamination_load: float
    public_readability: float
    pressure: float
    boundary_state: str
    consequence: str
    evidence: dict[str, float | str]
    causal_refs: list[str]

    def payload(self) -> dict[str, Any]:
        return {
            "boundary_id": self.boundary_id,
            "boundary_type": self.boundary_type,
            "focus_id": self.focus_id,
            "focus_label": self.focus_label,
            "knownness_asymmetry": round(self.knownness_asymmetry, 4),
            "speakability_width": round(self.speakability_width, 4),
            "disclosure_risk": round(self.disclosure_risk, 4),
            "contamination_load": round(self.contamination_load, 4),
            "public_readability": round(self.public_readability, 4),
            "pressure": round(self.pressure, 4),
            "boundary_state": self.boundary_state,
            "consequence": self.consequence,
            "evidence": self.evidence,
            "caused_by_events": self.causal_refs,
        }


class EpistemicBoundaryEngine:
    """Track relation-produced knowledge boundaries without modeling private belief."""

    def update(self, state: SimulationState, context: TickContext, local_events: list[Event]) -> list[EpistemicBoundary]:
        candidates = self._candidates(state, context, local_events)
        active = [candidate for candidate in candidates if candidate["pressure"] >= 0.045]
        if not active:
            return []
        selected = sorted(active, key=lambda item: item["pressure"], reverse=True)[:2]
        results: list[EpistemicBoundary] = []
        refs = self._causal_refs(local_events)
        for index, item in enumerate(selected, start=1):
            pressure = clamp(float(item["pressure"]))
            boundary = EpistemicBoundary(
                boundary_id=f"epi-{state.tick:04d}-{index:02d}-{item['boundary_type']}",
                boundary_type=str(item["boundary_type"]),
                focus_id=str(item["focus_id"]),
                focus_label=str(item["focus_label"]),
                knownness_asymmetry=clamp(float(item["knownness_asymmetry"])),
                speakability_width=clamp(float(item["speakability_width"])),
                disclosure_risk=clamp(float(item["disclosure_risk"])),
                contamination_load=clamp(float(item["contamination_load"])),
                public_readability=clamp(float(item["public_readability"])),
                pressure=pressure,
                boundary_state=self._state(pressure, float(item["speakability_width"])),
                consequence=str(item["consequence"]),
                evidence=item["evidence"],
                causal_refs=refs,
            )
            self._apply(state, boundary)
            results.append(boundary)
        return results

    def _candidates(self, state: SimulationState, context: TickContext, local_events: list[Event]) -> list[dict[str, Any]]:
        inquiry = self._latest(local_events, "InvestigationUpdateEvent")
        institutional = self._latest(local_events, "InstitutionalPressureEvent")
        witness = self._latest(local_events, "WitnessStrategyEvent")
        access = self._latest(local_events, "EvidenceAccessibilityEvent")
        location = self._latest(local_events, "LocationEvidenceCouplingEvent")
        action = self._latest(local_events, "ActionSelectionEvent")
        expression = self._latest(local_events, "ExpressionSelectionEvent")
        recognition = self._latest(local_events, "RecognitionEvent")
        public_private_gap = float(state.relation_metrics.get("public_private_gap", 0.0) or 0.0)
        public_definition = float(state.relation_metrics.get("relation_sediment.public_definition_load", 0.0) or 0.0)
        shared_secret = self._secret_binding(state)
        audience = max(state.field_state.audience_pressure.values(), default=0.0)
        recognition_result = str(recognition.get("outcome") or recognition.get("result") or "")
        expression_mode = str(expression.get("expression_mode", ""))
        action_id = str(action.get("action_id", ""))
        focus_id = str(inquiry.get("focus_id") or access.get("focus_id") or "relation")
        focus_label = str(inquiry.get("label") or access.get("label") or "关系事实")
        state_after = inquiry.get("state_after", {}) if isinstance(inquiry.get("state_after"), dict) else {}
        accessibility_after = access.get("accessibility_after", {}) if isinstance(access.get("accessibility_after"), dict) else {}
        location_after = location.get("location_after", {}) if isinstance(location.get("location_after"), dict) else {}
        progress = self._float(state_after, "progress")
        contamination = max(
            self._float(state_after, "contamination"),
            self._float(location_after, "contamination"),
        )
        suppression = max(
            self._float(state_after, "suppression"),
            self._float(institutional, "silencing_pressure"),
        )
        relationship_risk = self._float(state_after, "relationship_risk")
        accessibility = self._float(accessibility_after, "accessibility", default=1.0)
        witness_risk = max(
            self._float(witness, "confirmation_risk"),
            self._float(witness, "protective_value"),
            self._float(witness, "pressure_to_retract"),
        )
        public_exposure = max(
            self._float(institutional, "public_exposure"),
            audience,
            public_definition,
            0.18 if expression_mode == "public_performance" or action_id == "public_substitution" else 0.0,
        )
        case_pressure = max(progress, contamination, suppression, relationship_risk, witness_risk)
        base_speakability = clamp(1.0 - max(suppression * 0.55, public_exposure * 0.35, contamination * 0.3))
        candidates = [
            {
                "boundary_type": "case_knowledge_asymmetry",
                "focus_id": focus_id,
                "focus_label": focus_label,
                "knownness_asymmetry": clamp((1.0 - accessibility) * 0.34 + progress * 0.2 + witness_risk * 0.22),
                "speakability_width": base_speakability,
                "disclosure_risk": clamp(public_exposure * 0.22 + relationship_risk * 0.3 + witness_risk * 0.18),
                "contamination_load": contamination,
                "public_readability": public_exposure,
                "pressure": clamp(case_pressure * 0.28 + (1.0 - accessibility) * 0.16 + public_exposure * 0.1),
                "consequence": "who can safely know or say the case fact becomes uneven",
                "evidence": self._evidence(context, inquiry, institutional, witness, access, expression_mode, recognition_result),
            },
            {
                "boundary_type": "testimony_disclosure_risk",
                "focus_id": focus_id,
                "focus_label": focus_label,
                "knownness_asymmetry": clamp(witness_risk * 0.42 + suppression * 0.22),
                "speakability_width": clamp(1.0 - witness_risk * 0.5 - suppression * 0.22),
                "disclosure_risk": clamp(witness_risk * 0.55 + public_exposure * 0.12),
                "contamination_load": contamination,
                "public_readability": public_exposure,
                "pressure": clamp(witness_risk * 0.34 + suppression * 0.14 + relationship_risk * 0.12),
                "consequence": "testimony can move the relation only through a narrowed disclosure channel",
                "evidence": self._evidence(context, inquiry, institutional, witness, access, expression_mode, recognition_result),
            },
            {
                "boundary_type": "public_private_knowledge_split",
                "focus_id": "public_private_relation",
                "focus_label": "公开版本与私下事实",
                "knownness_asymmetry": clamp(public_private_gap * 0.38 + shared_secret * 0.22),
                "speakability_width": clamp(1.0 - public_private_gap * 0.45 - public_exposure * 0.2),
                "disclosure_risk": clamp(public_private_gap * 0.4 + public_exposure * 0.32 + shared_secret * 0.14),
                "contamination_load": clamp(contamination * 0.3 + public_definition * 0.18),
                "public_readability": public_exposure,
                "pressure": clamp(public_private_gap * 0.24 + public_exposure * 0.18 + shared_secret * 0.16),
                "consequence": "the public account and the private operating truth diverge",
                "evidence": self._evidence(context, inquiry, institutional, witness, access, expression_mode, recognition_result),
            },
            {
                "boundary_type": "unspeakable_fact_boundary",
                "focus_id": focus_id,
                "focus_label": focus_label,
                "knownness_asymmetry": clamp(suppression * 0.32 + (1.0 - base_speakability) * 0.28),
                "speakability_width": base_speakability,
                "disclosure_risk": clamp(public_exposure * 0.18 + suppression * 0.28),
                "contamination_load": contamination,
                "public_readability": public_exposure,
                "pressure": clamp((1.0 - base_speakability) * 0.24 + (0.18 if recognition_result == "unspeakable" else 0.0)),
                "consequence": "the relation can circle the fact but cannot name it cleanly",
                "evidence": self._evidence(context, inquiry, institutional, witness, access, expression_mode, recognition_result),
            },
        ]
        return candidates

    def _apply(self, state: SimulationState, boundary: EpistemicBoundary) -> None:
        pressure = boundary.pressure
        state.relation_metrics["epistemic_boundary.pressure"] = clamp(
            float(state.relation_metrics.get("epistemic_boundary.pressure", 0.0) or 0.0) * 0.78
            + pressure * 0.22
        )
        state.relation_metrics[f"epistemic_boundary.{boundary.boundary_type}"] = clamp(
            float(state.relation_metrics.get(f"epistemic_boundary.{boundary.boundary_type}", 0.0) or 0.0) * 0.84
            + pressure * 0.16
        )
        if boundary.boundary_type == "public_private_knowledge_split":
            state.relation_metrics["public_private_gap"] = clamp(float(state.relation_metrics.get("public_private_gap", 0.0) or 0.0) + pressure * 0.012)
            state.relation_metrics["relation_sediment.public_definition_load"] = clamp(
                float(state.relation_metrics.get("relation_sediment.public_definition_load", 0.0) or 0.0) + pressure * 0.009
            )
        elif boundary.boundary_type == "testimony_disclosure_risk":
            state.relation_metrics["inquiry.suppression_load"] = clamp(float(state.relation_metrics.get("inquiry.suppression_load", 0.0) or 0.0) + pressure * 0.012)
        elif boundary.boundary_type == "case_knowledge_asymmetry":
            state.relation_metrics["relation_sediment.asymmetry_load"] = clamp(
                float(state.relation_metrics.get("relation_sediment.asymmetry_load", 0.0) or 0.0) + pressure * 0.008
            )
        elif boundary.boundary_type == "unspeakable_fact_boundary":
            state.relation_metrics["double_bind_pressure"] = clamp(float(state.relation_metrics.get("double_bind_pressure", 0.0) or 0.0) + pressure * 0.01)
            for process in state.processes.values():
                process.speech_inhibition["unspeakable_fact"] = clamp(process.speech_inhibition.get("unspeakable_fact", 0.0) + pressure * 0.006)
        for process in state.processes.values():
            process.ambiguity_tolerance = clamp(process.ambiguity_tolerance - pressure * 0.003)

    def _state(self, pressure: float, speakability_width: float) -> str:
        if pressure >= 0.58 or speakability_width <= 0.25:
            return "sealed"
        if pressure >= 0.34 or speakability_width <= 0.45:
            return "narrowed"
        return "open_but_costly"

    def _secret_binding(self, state: SimulationState) -> float:
        return max((binding.strength for binding in state.bindings if binding.binding_type in {"secret", "shared_secret"}), default=0.0)

    def _evidence(
        self,
        context: TickContext,
        inquiry: dict[str, Any],
        institutional: dict[str, Any],
        witness: dict[str, Any],
        access: dict[str, Any],
        expression_mode: str,
        recognition_result: str,
    ) -> dict[str, float | str]:
        state_after = inquiry.get("state_after", {}) if isinstance(inquiry.get("state_after"), dict) else {}
        accessibility_after = access.get("accessibility_after", {}) if isinstance(access.get("accessibility_after"), dict) else {}
        return {
            "tick_type": context.tick_type,
            "focus_type": str(inquiry.get("focus_type") or access.get("focus_type") or "relation"),
            "movement": str(inquiry.get("movement") or "none"),
            "institutional_effect": str(institutional.get("institutional_effect") or "none"),
            "witness_strategy": str(witness.get("strategy_id") or "none"),
            "access_status": str(accessibility_after.get("access_status") or "unknown"),
            "expression_mode": expression_mode or "none",
            "recognition_result": recognition_result or "none",
            "progress": round(self._float(state_after, "progress"), 4),
            "contamination": round(self._float(state_after, "contamination"), 4),
            "suppression": round(self._float(state_after, "suppression"), 4),
            "relationship_risk": round(self._float(state_after, "relationship_risk"), 4),
            "accessibility": round(self._float(accessibility_after, "accessibility", default=1.0), 4),
        }

    def _causal_refs(self, events: list[Event]) -> list[str]:
        relevant = {
            "TickStartedEvent",
            "FieldPressureEvent",
            "BindingActivatedEvent",
            "LatentTimeEvent",
            "AffordanceSelectionEvent",
            "ActionSelectionEvent",
            "ExpressionSelectionEvent",
            "RecognitionEvent",
            "InstitutionalPressureEvent",
            "WitnessStrategyEvent",
            "EvidenceAccessibilityEvent",
            "InvestigationUpdateEvent",
            "LocationEvidenceCouplingEvent",
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
