from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from rpf.core.events import Event
from rpf.core.models import SimulationState, TickContext, clamp


@dataclass(frozen=True)
class InquiryUpdate:
    payload: dict[str, Any]
    causal_refs: list[str]


class InquiryEngine:
    """Tracks how a case ledger is handled, contaminated, suppressed, and made relationally costly."""

    def __init__(self, case_ledger: dict[str, Any] | None = None) -> None:
        self.case_ledger = case_ledger if isinstance(case_ledger, dict) else {}
        self.item_states: dict[str, dict[str, float]] = {}
        self.sequence = 0
        self._initialize_states()

    @property
    def enabled(self) -> bool:
        return bool(self.case_ledger)

    def update(self, state: SimulationState, context: TickContext, local_events: list[Event]) -> list[InquiryUpdate]:
        if not self.enabled:
            return []
        focus = self._select_focus(state, context, local_events)
        if not focus:
            return []
        self.sequence += 1
        affordance = self._latest(local_events, "AffordanceSelectionEvent")
        action = self._latest(local_events, "ActionSelectionEvent")
        expression = self._latest(local_events, "ExpressionSelectionEvent")
        recognition = self._latest(local_events, "RecognitionEvent")
        movement = self._movement(context, affordance, action, expression, recognition)
        item_state = self.item_states.setdefault(
            focus["id"],
            {
                "progress": 0.0,
                "contamination": float(focus.get("contamination_risk", 0.0) or 0.0),
                "suppression": 0.0,
                "relationship_risk": 0.0,
            },
        )
        before = dict(item_state)
        item_state["progress"] = clamp(item_state["progress"] + movement["progress_delta"])
        item_state["contamination"] = clamp(item_state["contamination"] + movement["contamination_delta"])
        item_state["suppression"] = clamp(item_state["suppression"] + movement["suppression_delta"])
        item_state["relationship_risk"] = clamp(item_state["relationship_risk"] + movement["relationship_risk_delta"])
        self._apply_feedback(state, focus, movement, item_state)
        payload = {
            "inquiry_id": f"inquiry-{state.tick:03d}-{self.sequence:03d}",
            "case_id": self.case_ledger.get("case_id"),
            "focus_type": focus["type"],
            "focus_id": focus["id"],
            "label": focus["label"],
            "movement": movement["movement"],
            "tick_type": context.tick_type,
            "linked_affordance": affordance.get("affordance_id"),
            "linked_action": action.get("action_id"),
            "linked_expression": expression.get("expression_id"),
            "linked_recognition": recognition.get("result"),
            "ledger_refs": focus.get("ledger_refs", []),
            "deltas": {
                "progress": round(item_state["progress"] - before["progress"], 4),
                "contamination": round(item_state["contamination"] - before["contamination"], 4),
                "suppression": round(item_state["suppression"] - before["suppression"], 4),
                "relationship_risk": round(item_state["relationship_risk"] - before["relationship_risk"], 4),
            },
            "state_after": {key: round(value, 4) for key, value in item_state.items()},
            "relational_feedback": movement["relational_feedback"],
            "narrative_boundary": self._boundary_note(focus, item_state),
        }
        causal_refs = [
            event.event_id
            for event in local_events
            if event.event_type
            in {
                "AffordanceSelectionEvent",
                "ActionSelectionEvent",
                "ExpressionSelectionEvent",
                "RecognitionEvent",
                "MisrecognitionEvent",
                "SceneCrystallizationEvent",
                "LatentTimeEvent",
            }
        ][-5:]
        return [InquiryUpdate(payload=payload, causal_refs=causal_refs)]

    def _initialize_states(self) -> None:
        for collection, id_key in (
            ("evidence_items", "evidence_id"),
            ("testimonies", "testimony_id"),
            ("contradictions", "contradiction_id"),
            ("unverified_anomalies", "anomaly_id"),
            ("known_facts", "fact_id"),
        ):
            for item in self.case_ledger.get(collection, []) or []:
                item_id = str(item.get(id_key, ""))
                if not item_id:
                    continue
                self.item_states[item_id] = {
                    "progress": 0.0,
                    "contamination": float(item.get("contamination_risk", 0.0) or 0.0),
                    "suppression": float(item.get("pressure_to_retract", 0.0) or 0.0) * 0.25,
                    "relationship_risk": 0.0,
                }

    def _select_focus(self, state: SimulationState, context: TickContext, local_events: list[Event]) -> dict[str, Any] | None:
        affordance_id = str(self._latest(local_events, "AffordanceSelectionEvent").get("affordance_id", ""))
        if affordance_id == "contaminated_evidence_review":
            return self._highest("evidence_items", "evidence_id", "label", ["contamination_risk", "reliability"])
        if affordance_id == "unstable_testimony_probe":
            return self._highest("testimonies", "testimony_id", "statement", ["pressure_to_retract", "contamination_exposure"])
        if affordance_id == "forbidden_symbol_confrontation":
            return self._symbol_focus()
        if context.tick_type == "latent":
            return self._highest("contradictions", "contradiction_id", "text", ["suppression"])
        if state.tick % 4 == 0:
            return self._highest("unverified_anomalies", "anomaly_id", "text", ["ambiguity"])
        return self._highest("known_facts", "fact_id", "text", ["reliability"])

    def _highest(self, collection: str, id_key: str, label_key: str, score_keys: list[str]) -> dict[str, Any] | None:
        rows = self.case_ledger.get(collection, []) or []
        if not rows:
            return None
        selected = max(rows, key=lambda item: sum(float(item.get(key, 0.0) or 0.0) for key in score_keys))
        return self._focus(collection, selected, id_key, label_key)

    def _symbol_focus(self) -> dict[str, Any] | None:
        evidence = self.case_ledger.get("evidence_items", []) or []
        for item in evidence:
            if "yellow" in str(item.get("evidence_id", "")) or "黄" in str(item.get("label", "")):
                return self._focus("evidence_items", item, "evidence_id", "label")
        return self._highest("unverified_anomalies", "anomaly_id", "text", ["ambiguity"])

    def _focus(self, collection: str, item: dict[str, Any], id_key: str, label_key: str) -> dict[str, Any]:
        item_id = str(item.get(id_key, collection))
        return {
            "type": collection,
            "id": item_id,
            "label": str(item.get(label_key) or item_id),
            "contamination_risk": float(item.get("contamination_risk", 0.0) or 0.0),
            "ledger_refs": [item_id, *[str(ref) for ref in item.get("linked_evidence", []) or []]],
        }

    def _movement(
        self,
        context: TickContext,
        affordance: dict[str, Any],
        action: dict[str, Any],
        expression: dict[str, Any],
        recognition: dict[str, Any],
    ) -> dict[str, Any]:
        affordance_id = str(affordance.get("affordance_id", ""))
        action_mode = str(action.get("action_mode", ""))
        expression_mode = str(expression.get("expression_mode", ""))
        recognition_result = str(recognition.get("result", ""))
        scene_bias = 0.035 if context.tick_type == "scene" else 0.015 if context.tick_type == "micro_interaction" else 0.006
        progress = scene_bias
        contamination = 0.006
        suppression = 0.004
        relationship_risk = 0.008
        movement = "case_pressure_sediments"
        if affordance_id == "contaminated_evidence_review":
            progress += 0.045
            contamination += 0.035
            relationship_risk += 0.018
            movement = "evidence_review_contaminates_relation"
        elif affordance_id == "unstable_testimony_probe":
            progress += 0.035
            contamination += 0.026
            suppression += 0.028
            relationship_risk += 0.042
            movement = "testimony_probe_raises_retraction_pressure"
        elif affordance_id == "forbidden_symbol_confrontation":
            progress += 0.028
            contamination += 0.048
            relationship_risk += 0.05
            movement = "symbol_becomes_speakable_but_unstable"
        if action_mode == "inhibited":
            progress *= 0.45
            suppression += 0.03
            relationship_risk += 0.018
        elif action_mode == "substituted":
            progress *= 0.72
            contamination += 0.01
        elif action_mode == "enacted":
            progress += 0.018
        if expression_mode == "silence":
            suppression += 0.018
            relationship_risk += 0.018
        if recognition_result in {"misunderstood", "refused", "unspeakable"}:
            contamination += 0.018
            relationship_risk += 0.03
        elif recognition_result in {"partial", "granted"}:
            suppression -= 0.01
            progress += 0.012
        return {
            "movement": movement,
            "progress_delta": clamp(progress),
            "contamination_delta": clamp(contamination),
            "suppression_delta": clamp(suppression),
            "relationship_risk_delta": clamp(relationship_risk),
            "relational_feedback": {
                "conflict_pressure": clamp(relationship_risk * 0.35 + contamination * 0.12),
                "memory_pressure": clamp(contamination * 0.3 + suppression * 0.08),
                "repair_debt": clamp(suppression * 0.18 + relationship_risk * 0.12),
            },
        }

    def _apply_feedback(self, state: SimulationState, focus: dict[str, Any], movement: dict[str, Any], item_state: dict[str, float]) -> None:
        feedback = movement["relational_feedback"]
        for key, delta in feedback.items():
            state.relation_metrics[key] = clamp(float(state.relation_metrics.get(key, 0.0) or 0.0) + float(delta))
        material = state.field_state.material_pressures
        material["case_contamination"] = clamp(float(material.get("case_contamination", 0.0) or 0.0) + movement["contamination_delta"] * 0.12)
        material["case_suppression"] = clamp(float(material.get("case_suppression", 0.0) or 0.0) + movement["suppression_delta"] * 0.1)
        if focus["type"] in {"testimonies", "evidence_items"}:
            p1 = state.processes.get("p1")
            if p1:
                p1.relevance_triggers["case_focus"] = clamp(p1.relevance_triggers.get("case_focus", 0.0) + item_state["relationship_risk"] * 0.04)
        p2 = state.processes.get("p2")
        if p2:
            p2.relevance_triggers["procedural_gap"] = clamp(p2.relevance_triggers.get("procedural_gap", 0.0) + item_state["progress"] * 0.02)

    def _boundary_note(self, focus: dict[str, Any], item_state: dict[str, float]) -> str:
        if item_state["progress"] > 0.42 and item_state["contamination"] > 0.72:
            return f"{focus['label']} has become important, but too contaminated to settle the case."
        if item_state["suppression"] > 0.45:
            return f"{focus['label']} is under pressure to disappear from usable testimony."
        return f"{focus['label']} can be rendered only as investigated pressure, not as solved truth."

    def _latest(self, events: list[Event], event_type: str) -> dict[str, Any]:
        for event in reversed(events):
            if event.event_type == event_type:
                return event.payload
        return {}
