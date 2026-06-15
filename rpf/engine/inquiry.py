from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from rpf.core.events import Event
from rpf.core.models import SimulationState, TickContext, clamp


@dataclass(frozen=True)
class InquiryUpdate:
    event_type: str
    payload: dict[str, Any]
    causal_refs: list[str]


class InquiryEngine:
    """Tracks how a case ledger is handled, contaminated, suppressed, and made relationally costly."""

    def __init__(self, case_ledger: dict[str, Any] | None = None) -> None:
        self.case_ledger = case_ledger if isinstance(case_ledger, dict) else {}
        self.item_states: dict[str, dict[str, Any]] = {}
        self.locations = {
            str(item.get("location_id")): item
            for item in self.case_ledger.get("locations", []) or []
            if item.get("location_id")
        }
        self.evidence_locations = {
            str(item.get("evidence_id")): str(item.get("location_id"))
            for item in self.case_ledger.get("evidence_items", []) or []
            if item.get("evidence_id") and item.get("location_id")
        }
        self.location_states: dict[str, dict[str, Any]] = {}
        self.sequence = 0
        self._initialize_states()

    @property
    def enabled(self) -> bool:
        return bool(self.case_ledger)

    def update(self, state: SimulationState, context: TickContext, local_events: list[Event]) -> list[InquiryUpdate]:
        if not self.enabled:
            return []
        self._refresh_accessibility(state, context)
        focus = self._select_focus(state, context, local_events)
        if not focus:
            return []
        self.sequence += 1
        affordance = self._latest(local_events, "AffordanceSelectionEvent")
        action = self._latest(local_events, "ActionSelectionEvent")
        expression = self._latest(local_events, "ExpressionSelectionEvent")
        recognition = self._latest(local_events, "RecognitionEvent")
        movement = self._movement(context, affordance, action, expression, recognition)
        location_before = self._location_payload(focus)
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
        accessibility_before = self._accessibility_payload(focus, item_state)
        item_state["progress"] = clamp(item_state["progress"] + movement["progress_delta"])
        item_state["contamination"] = clamp(item_state["contamination"] + movement["contamination_delta"])
        item_state["suppression"] = clamp(item_state["suppression"] + movement["suppression_delta"])
        item_state["relationship_risk"] = clamp(item_state["relationship_risk"] + movement["relationship_risk_delta"])
        self._update_focus_accessibility(focus, item_state, movement)
        self._update_location_state(focus, movement, context)
        accessibility_after = self._accessibility_payload(focus, item_state)
        location_after = self._location_payload(focus)
        self._apply_feedback(state, focus, movement, item_state)
        payload = {
            "inquiry_id": f"inquiry-{state.tick:03d}-{self.sequence:03d}",
            "case_id": self.case_ledger.get("case_id"),
            "focus_type": focus["type"],
            "focus_id": focus["id"],
            "label": focus["label"],
            "location": location_after,
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
            "state_after": self._numeric_state(item_state),
            "accessibility_before": accessibility_before,
            "accessibility_after": accessibility_after,
            "location_before": location_before,
            "location_after": location_after,
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
        access_payload = {
            "case_id": self.case_ledger.get("case_id"),
            "focus_type": focus["type"],
            "focus_id": focus["id"],
            "label": focus["label"],
            "location": location_after,
            "tick_type": context.tick_type,
            "accessibility_before": accessibility_before,
            "accessibility_after": accessibility_after,
            "accessibility_delta": round(accessibility_after["accessibility"] - accessibility_before["accessibility"], 4),
            "access_status_changed": accessibility_before["access_status"] != accessibility_after["access_status"],
            "access_reason": self._access_reason(accessibility_after),
        }
        location_payload = {
            "case_id": self.case_ledger.get("case_id"),
            "focus_type": focus["type"],
            "focus_id": focus["id"],
            "label": focus["label"],
            "tick_type": context.tick_type,
            "location_before": location_before,
            "location_after": location_after,
            "location_delta": {
                "pressure": round(location_after["location_pressure"] - location_before["location_pressure"], 4),
                "contamination": round(location_after["contamination"] - location_before["contamination"], 4),
                "accessibility": round(location_after["location_accessibility"] - location_before["location_accessibility"], 4),
            },
            "coupling_reason": self._location_reason(focus, location_after),
        }
        return [
            InquiryUpdate(event_type="LocationEvidenceCouplingEvent", payload=location_payload, causal_refs=causal_refs),
            InquiryUpdate(event_type="EvidenceAccessibilityEvent", payload=access_payload, causal_refs=causal_refs),
            InquiryUpdate(event_type="InvestigationUpdateEvent", payload=payload, causal_refs=causal_refs),
        ]

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
                    "accessibility": clamp(1.0 - float(item.get("contamination_risk", 0.0) or 0.0) * 0.35),
                    "blocked_ticks": 0.0,
                    "location_id": self._item_location(collection, item),
                }
        for location_id, location in self.locations.items():
            contamination = float(location.get("contamination_risk", 0.0) or 0.0)
            self.location_states[location_id] = {
                "location_pressure": contamination * 0.35,
                "contamination": contamination,
                "location_accessibility": clamp(1.0 - contamination * 0.25),
                "visit_count": 0.0,
            }

    def _select_focus(self, state: SimulationState, context: TickContext, local_events: list[Event]) -> dict[str, Any] | None:
        affordance_id = str(self._latest(local_events, "AffordanceSelectionEvent").get("affordance_id", ""))
        preferred_location = self._preferred_location(affordance_id)
        if affordance_id == "contaminated_evidence_review":
            return self._highest("evidence_items", "evidence_id", "label", ["contamination_risk", "reliability"], preferred_location)
        if affordance_id == "unstable_testimony_probe":
            return self._highest("testimonies", "testimony_id", "statement", ["pressure_to_retract", "contamination_exposure"], preferred_location)
        if affordance_id == "forbidden_symbol_confrontation":
            return self._symbol_focus()
        if context.tick_type == "latent":
            return self._highest("contradictions", "contradiction_id", "text", ["suppression"], preferred_location)
        if state.tick % 4 == 0:
            return self._highest("unverified_anomalies", "anomaly_id", "text", ["ambiguity"], preferred_location)
        return self._highest("known_facts", "fact_id", "text", ["reliability"], preferred_location)

    def _highest(
        self,
        collection: str,
        id_key: str,
        label_key: str,
        score_keys: list[str],
        preferred_location: str | None = None,
    ) -> dict[str, Any] | None:
        rows = self.case_ledger.get(collection, []) or []
        if not rows:
            return None
        available = [item for item in rows if self._is_accessible(str(item.get(id_key, "")))]
        candidates = available or rows
        if preferred_location:
            located = [item for item in candidates if self._item_location(collection, item) == preferred_location]
            if located:
                candidates = located
        selected = max(candidates, key=lambda item: self._focus_score(item, id_key, score_keys))
        return self._focus(collection, selected, id_key, label_key)

    def _focus_score(self, item: dict[str, Any], id_key: str, score_keys: list[str]) -> float:
        item_id = str(item.get(id_key, ""))
        item_state = self.item_states.get(item_id, {})
        accessibility = float(item_state.get("accessibility", 1.0) or 0.0)
        location_id = str(item_state.get("location_id") or self._item_location("", item))
        location_state = self.location_states.get(location_id, {})
        location_access = float(location_state.get("location_accessibility", 1.0) or 1.0)
        blocked_penalty = 0.35 if item_state.get("access_status") == "blocked" else 0.0
        return sum(float(item.get(key, 0.0) or 0.0) for key in score_keys) + accessibility * 0.25 + location_access * 0.12 - blocked_penalty

    def _is_accessible(self, item_id: str) -> bool:
        item_state = self.item_states.get(item_id, {})
        return item_state.get("access_status") != "blocked" and float(item_state.get("accessibility", 1.0) or 0.0) >= 0.18

    def _symbol_focus(self) -> dict[str, Any] | None:
        evidence = self.case_ledger.get("evidence_items", []) or []
        for item in evidence:
            if "yellow" in str(item.get("evidence_id", "")) or "黄" in str(item.get("label", "")):
                return self._focus("evidence_items", item, "evidence_id", "label")
        return self._highest("unverified_anomalies", "anomaly_id", "text", ["ambiguity"])

    def _focus(self, collection: str, item: dict[str, Any], id_key: str, label_key: str) -> dict[str, Any]:
        item_id = str(item.get(id_key, collection))
        location_id = self._item_location(collection, item)
        location = self.locations.get(location_id, {})
        return {
            "type": collection,
            "id": item_id,
            "label": str(item.get(label_key) or item_id),
            "contamination_risk": float(item.get("contamination_risk", 0.0) or 0.0),
            "location_id": location_id,
            "location_label": str(location.get("label") or location_id or "unknown location"),
            "location_effects": [str(effect) for effect in location.get("field_effects", []) or []],
            "location_scene_biases": [str(bias) for bias in location.get("scene_biases", []) or []],
            "ledger_refs": [item_id, *[str(ref) for ref in item.get("linked_evidence", []) or []]],
        }

    def _item_location(self, collection: str, item: dict[str, Any]) -> str:
        direct = str(item.get("location_id") or "")
        if direct:
            return direct
        linked = [str(ref) for ref in item.get("linked_evidence", []) or []]
        for ref in linked:
            if ref in self.evidence_locations:
                return self.evidence_locations[ref]
        if collection == "testimonies":
            return "evidence_room_yellow_light"
        if collection == "unverified_anomalies":
            return "flooded_road_to_refinery"
        return "archive_basement"

    def _preferred_location(self, affordance_id: str) -> str | None:
        if affordance_id == "contaminated_evidence_review":
            return "archive_basement"
        if affordance_id == "unstable_testimony_probe":
            return "evidence_room_yellow_light"
        if affordance_id == "forbidden_symbol_confrontation":
            return "flooded_road_to_refinery"
        return None

    def _refresh_accessibility(self, state: SimulationState, context: TickContext) -> None:
        fatigue = sum(process.fatigue for process in state.processes.values()) / max(1, len(state.processes))
        institutional_pressure = max(state.field_state.audience_pressure.values(), default=0.0)
        latent_relief = 0.025 if context.tick_type == "latent" else 0.0
        for item_state in self.item_states.values():
            contamination = float(item_state.get("contamination", 0.0) or 0.0)
            suppression = float(item_state.get("suppression", 0.0) or 0.0)
            relationship_risk = float(item_state.get("relationship_risk", 0.0) or 0.0)
            accessibility = float(item_state.get("accessibility", 1.0) or 0.0)
            accessibility = clamp(
                accessibility
                + latent_relief
                - contamination * 0.01
                - suppression * 0.014
                - relationship_risk * 0.012
                - fatigue * 0.004
                - institutional_pressure * 0.003
            )
            item_state["accessibility"] = accessibility
            item_state["access_status"] = self._access_status(accessibility)
            if item_state["access_status"] == "blocked":
                item_state["blocked_ticks"] = float(item_state.get("blocked_ticks", 0.0) or 0.0) + 1.0
            else:
                item_state["blocked_ticks"] = 0.0
        for location_state in self.location_states.values():
            contamination = float(location_state.get("contamination", 0.0) or 0.0)
            pressure = float(location_state.get("location_pressure", 0.0) or 0.0)
            access = float(location_state.get("location_accessibility", 1.0) or 0.0)
            access = clamp(access + latent_relief * 0.5 - contamination * 0.006 - pressure * 0.01 - institutional_pressure * 0.003)
            location_state["location_accessibility"] = access
            location_state["access_status"] = self._access_status(access)

    def _update_focus_accessibility(self, focus: dict[str, Any], item_state: dict[str, float], movement: dict[str, Any]) -> None:
        accessibility = float(item_state.get("accessibility", 1.0) or 0.0)
        accessibility = clamp(
            accessibility
            + movement["progress_delta"] * 0.08
            - movement["contamination_delta"] * 0.42
            - movement["suppression_delta"] * 0.34
            - movement["relationship_risk_delta"] * 0.24
        )
        if focus["type"] in {"known_facts", "contradictions"}:
            accessibility = clamp(accessibility + movement["progress_delta"] * 0.04)
        item_state["accessibility"] = accessibility
        item_state["access_status"] = self._access_status(accessibility)

    def _update_location_state(self, focus: dict[str, Any], movement: dict[str, Any], context: TickContext) -> None:
        location_id = focus.get("location_id")
        if not location_id:
            return
        location_state = self.location_states.setdefault(
            str(location_id),
            {
                "location_pressure": 0.0,
                "contamination": 0.0,
                "location_accessibility": 1.0,
                "visit_count": 0.0,
            },
        )
        scene_multiplier = 1.25 if context.tick_type == "scene" else 0.75 if context.tick_type == "latent" else 1.0
        location_state["visit_count"] = float(location_state.get("visit_count", 0.0) or 0.0) + 1.0
        location_state["location_pressure"] = clamp(
            float(location_state.get("location_pressure", 0.0) or 0.0)
            + movement["relationship_risk_delta"] * 0.4 * scene_multiplier
            + movement["suppression_delta"] * 0.25
        )
        location_state["contamination"] = clamp(
            float(location_state.get("contamination", 0.0) or 0.0)
            + movement["contamination_delta"] * 0.32 * scene_multiplier
        )
        location_state["location_accessibility"] = clamp(
            float(location_state.get("location_accessibility", 1.0) or 0.0)
            + movement["progress_delta"] * 0.04
            - movement["contamination_delta"] * 0.18
            - movement["suppression_delta"] * 0.14
            - movement["relationship_risk_delta"] * 0.12
        )
        location_state["access_status"] = self._access_status(float(location_state["location_accessibility"]))

    def _accessibility_payload(self, focus: dict[str, Any], item_state: dict[str, float]) -> dict[str, Any]:
        accessibility = float(item_state.get("accessibility", 1.0) or 0.0)
        status = str(item_state.get("access_status") or self._access_status(accessibility))
        return {
            "focus_id": focus["id"],
            "focus_type": focus["type"],
            "accessibility": round(accessibility, 4),
            "access_status": status,
            "blocked_ticks": int(item_state.get("blocked_ticks", 0.0) or 0.0),
        }

    def _location_payload(self, focus: dict[str, Any]) -> dict[str, Any]:
        location_id = str(focus.get("location_id") or "")
        state = self.location_states.get(location_id, {})
        accessibility = float(state.get("location_accessibility", 1.0) or 0.0)
        return {
            "location_id": location_id,
            "location_label": focus.get("location_label") or location_id or "unknown location",
            "field_effects": focus.get("location_effects", []),
            "scene_biases": focus.get("location_scene_biases", []),
            "location_pressure": round(float(state.get("location_pressure", 0.0) or 0.0), 4),
            "contamination": round(float(state.get("contamination", 0.0) or 0.0), 4),
            "location_accessibility": round(accessibility, 4),
            "access_status": str(state.get("access_status") or self._access_status(accessibility)),
            "visit_count": int(state.get("visit_count", 0.0) or 0.0),
        }

    def _numeric_state(self, item_state: dict[str, Any]) -> dict[str, float]:
        result: dict[str, float] = {}
        for key, value in item_state.items():
            if isinstance(value, (int, float)):
                result[key] = round(float(value), 4)
        return result

    def _access_status(self, accessibility: float) -> str:
        if accessibility >= 0.66:
            return "available"
        if accessibility >= 0.38:
            return "restricted"
        if accessibility >= 0.18:
            return "fragile"
        return "blocked"

    def _access_reason(self, access: dict[str, Any]) -> str:
        status = access.get("access_status")
        if status == "available":
            return "evidence can be approached without immediate deformation"
        if status == "restricted":
            return "evidence remains reachable, but only through constraint"
        if status == "fragile":
            return "touching this evidence may further damage its usability"
        return "evidence is temporarily blocked by contamination, suppression, or relational risk"

    def _location_reason(self, focus: dict[str, Any], location: dict[str, Any]) -> str:
        effects = "、".join(str(effect) for effect in location.get("field_effects", [])[:3])
        label = location.get("location_label") or focus.get("location_label") or "unknown location"
        status = location.get("access_status", "available")
        if status == "blocked":
            return f"{label} blocks the evidence through {effects or 'accumulated pressure'}"
        if status == "fragile":
            return f"{label} makes the evidence reachable only at risk of further distortion"
        if status == "restricted":
            return f"{label} constrains how the evidence can be approached"
        return f"{label} makes this evidence practically reachable"

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
        state.relation_metrics["inquiry.progress_pressure"] = clamp(
            float(state.relation_metrics.get("inquiry.progress_pressure", 0.0) or 0.0)
            + item_state["progress"] * 0.035
        )
        state.relation_metrics["inquiry.contamination_load"] = clamp(
            float(state.relation_metrics.get("inquiry.contamination_load", 0.0) or 0.0)
            + item_state["contamination"] * 0.025
        )
        state.relation_metrics["inquiry.suppression_load"] = clamp(
            float(state.relation_metrics.get("inquiry.suppression_load", 0.0) or 0.0)
            + item_state["suppression"] * 0.03
        )
        state.relation_metrics["inquiry.relationship_risk"] = clamp(
            float(state.relation_metrics.get("inquiry.relationship_risk", 0.0) or 0.0)
            + item_state["relationship_risk"] * 0.04
        )
        material = state.field_state.material_pressures
        material["case_contamination"] = clamp(float(material.get("case_contamination", 0.0) or 0.0) + movement["contamination_delta"] * 0.12)
        material["case_suppression"] = clamp(float(material.get("case_suppression", 0.0) or 0.0) + movement["suppression_delta"] * 0.1)
        material["evidence_access_narrowing"] = clamp(1.0 - item_state.get("accessibility", 1.0))
        if focus.get("location_id"):
            material[f"location_pressure.{focus['location_id']}"] = self.location_states.get(str(focus["location_id"]), {}).get("location_pressure", 0.0)
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
