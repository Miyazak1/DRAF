from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from rpf.core.events import Event
from rpf.core.models import SimulationState, TickContext, clamp


@dataclass(frozen=True)
class OpportunityCost:
    cost_type: str
    missed_window: str
    process_id: str
    action_id: str
    action_mode: str
    intensity: float
    reversibility: str
    reason: str
    affected_fields: list[str]
    causal_refs: list[str]

    def payload(self) -> dict[str, Any]:
        return {
            "cost_type": self.cost_type,
            "missed_window": self.missed_window,
            "process_id": self.process_id,
            "action_id": self.action_id,
            "action_mode": self.action_mode,
            "intensity": round(self.intensity, 4),
            "reversibility": self.reversibility,
            "reason": self.reason,
            "affected_fields": self.affected_fields,
            "caused_by_events": self.causal_refs,
        }


class OpportunityCostEngine:
    """Track the realistic alternatives lost when one action path is taken."""

    def update(self, state: SimulationState, context: TickContext, local_events: list[Event]) -> list[OpportunityCost]:
        action_event = self._latest_event(local_events, "ActionSelectionEvent")
        if not action_event:
            return []
        action = action_event.payload
        candidates = self._candidate_costs(state, context, local_events, action)
        active = [item for item in candidates if item["intensity"] > 0.035]
        if not active:
            return []
        selected = sorted(active, key=lambda item: item["intensity"], reverse=True)[:2]
        results: list[OpportunityCost] = []
        refs = sorted({action_event.event_id, *action_event.causal_refs, *[event.event_id for event in local_events[-5:]]})
        for item in selected:
            cost = OpportunityCost(
                cost_type=item["cost_type"],
                missed_window=item["missed_window"],
                process_id=str(action.get("source_process", "relation")),
                action_id=str(action.get("action_id", "")),
                action_mode=str(action.get("action_mode", "")),
                intensity=clamp(float(item["intensity"])),
                reversibility=item["reversibility"],
                reason=item["reason"],
                affected_fields=item["affected_fields"],
                causal_refs=refs,
            )
            self._apply(state, cost)
            results.append(cost)
        return results

    def _candidate_costs(
        self,
        state: SimulationState,
        context: TickContext,
        local_events: list[Event],
        action: dict[str, Any],
    ) -> list[dict[str, Any]]:
        daily = self._latest(local_events, "DailyEcologyEvent")
        attention = self._latest(local_events, "AttentionDriftEvent")
        inquiry = self._latest(local_events, "InvestigationUpdateEvent")
        recognition = self._latest(local_events, "RecognitionEvent")
        mode = str(action.get("action_mode", ""))
        action_id = str(action.get("action_id", ""))
        source = str(action.get("source_process", "p1"))
        process = state.processes.get(source)
        fatigue = process.fatigue if process else 0.0
        body_load = self._payload_float(daily, "body_load")
        unfinished = self._payload_float(daily, "unfinished_tasks")
        waiting = self._payload_float(daily, "waiting_pressure")
        attention_focus = str(attention.get("dominant_focus", ""))
        drift = self._payload_float(attention, "drift_intensity")
        inquiry_state = inquiry.get("state_after", {}) if isinstance(inquiry.get("state_after"), dict) else {}
        case_progress = self._payload_float(inquiry_state, "progress")
        case_suppression = self._payload_float(inquiry_state, "suppression")
        repair_debt = float(state.relation_metrics.get("repair_debt", 0.0) or 0.0)
        conflict = float(state.relation_metrics.get("conflict_pressure", 0.0) or 0.0)
        recognition_result = str(recognition.get("outcome") or recognition.get("result") or "")
        inhibited = 1.0 if mode == "inhibited" else 0.0
        substituted = 1.0 if mode == "substituted" else 0.0
        direct = 1.0 if mode == "enacted" else 0.0
        bad_recognition = 1.0 if recognition_result in {"refused", "misunderstood", "unspeakable"} else 0.0
        scene_cost = 1.0 if context.tick_type == "scene" else 0.0
        return [
            {
                "cost_type": "recovery_window_loss",
                "missed_window": "sleep_or_body_recovery",
                "intensity": clamp(fatigue * 0.22 + body_load * 0.26 + direct * 0.05 + waiting * 0.08),
                "reversibility": "decaying",
                "reason": "the chosen action consumes bodily recovery time and leaves fatigue less recoverable",
                "affected_fields": ["processes.*.fatigue", "daily_ecology.body_load"],
            },
            {
                "cost_type": "repair_window_loss",
                "missed_window": "clean_repair_opening",
                "intensity": clamp(repair_debt * 0.18 + inhibited * 0.18 + substituted * 0.1 + (attention_focus == "repair_opportunity") * drift * 0.22),
                "reversibility": "partial",
                "reason": "not taking the available repair route makes later repair less clean",
                "affected_fields": ["repair_debt", "relation_sediment.repair_access_narrowing"],
            },
            {
                "cost_type": "evidence_window_loss",
                "missed_window": "usable_evidence_or_testimony_timing",
                "intensity": clamp(case_progress * 0.1 + case_suppression * 0.22 + inhibited * 0.08 + waiting * 0.08),
                "reversibility": "partial",
                "reason": "the action path lets evidence or testimony become harder to approach in time",
                "affected_fields": ["material_pressures.evidence_window_narrowing", "inquiry.suppression_load"],
            },
            {
                "cost_type": "social_exposure_cost",
                "missed_window": "private_resolution_before_public_reading",
                "intensity": clamp((action_id == "public_substitution") * 0.18 + state.field_state.audience_pressure.get("everyday_visibility", 0.0) * 0.22),
                "reversibility": "decaying",
                "reason": "the action becomes more publicly readable before the relation can resolve it privately",
                "affected_fields": ["audience_pressure.reputational_echo", "face_risk_pressure"],
            },
            {
                "cost_type": "trust_window_loss",
                "missed_window": "low-cost_trust_update",
                "intensity": clamp(conflict * 0.14 + direct * 0.08 + bad_recognition * 0.16),
                "reversibility": "partial",
                "reason": "the interaction spends a low-cost trust update window and makes later trust repair more expensive",
                "affected_fields": ["trust", "ambiguity_tolerance", "conflict_pressure"],
            },
            {
                "cost_type": "ordinary_task_spillover",
                "missed_window": "ordinary_work_or_errand_completion",
                "intensity": clamp(unfinished * 0.2 + body_load * 0.08 + scene_cost * 0.08),
                "reversibility": "decaying",
                "reason": "the relational action spills into ordinary obligations and leaves task debt behind",
                "affected_fields": ["material_pressures.daily_task_debt", "account_pressure.*.energy"],
            },
        ]

    def _apply(self, state: SimulationState, cost: OpportunityCost) -> None:
        intensity = cost.intensity
        state.relation_metrics["opportunity_cost.total"] = clamp(float(state.relation_metrics.get("opportunity_cost.total", 0.0) or 0.0) + intensity * 0.08)
        state.relation_metrics[f"opportunity_cost.{cost.cost_type}"] = clamp(
            float(state.relation_metrics.get(f"opportunity_cost.{cost.cost_type}", 0.0) or 0.0) * 0.82 + intensity * 0.18
        )
        if cost.cost_type == "repair_window_loss":
            state.relation_metrics["repair_debt"] = clamp(float(state.relation_metrics.get("repair_debt", 0.0) or 0.0) + intensity * 0.025)
            state.relation_metrics["relation_sediment.repair_access_narrowing"] = clamp(
                float(state.relation_metrics.get("relation_sediment.repair_access_narrowing", 0.0) or 0.0) + intensity * 0.018
            )
        elif cost.cost_type == "evidence_window_loss":
            state.field_state.material_pressures["evidence_window_narrowing"] = clamp(
                float(state.field_state.material_pressures.get("evidence_window_narrowing", 0.0) or 0.0) + intensity * 0.02
            )
            state.relation_metrics["inquiry.suppression_load"] = clamp(float(state.relation_metrics.get("inquiry.suppression_load", 0.0) or 0.0) + intensity * 0.014)
        elif cost.cost_type == "social_exposure_cost":
            state.field_state.audience_pressure["reputational_echo"] = clamp(
                float(state.field_state.audience_pressure.get("reputational_echo", 0.0) or 0.0) + intensity * 0.018
            )
            state.relation_metrics["face_risk_pressure"] = clamp(float(state.relation_metrics.get("face_risk_pressure", 0.0) or 0.0) + intensity * 0.012)
        elif cost.cost_type == "trust_window_loss":
            state.relation_metrics["conflict_pressure"] = clamp(float(state.relation_metrics.get("conflict_pressure", 0.0) or 0.0) + intensity * 0.014)
            for process in state.processes.values():
                process.ambiguity_tolerance = clamp(process.ambiguity_tolerance - intensity * 0.006)
        elif cost.cost_type == "ordinary_task_spillover":
            state.field_state.material_pressures["daily_task_debt"] = clamp(
                float(state.field_state.material_pressures.get("daily_task_debt", 0.0) or 0.0) + intensity * 0.018
            )
            state.relation_metrics[f"account_pressure.{cost.process_id}.energy"] = clamp(
                float(state.relation_metrics.get(f"account_pressure.{cost.process_id}.energy", 0.0) or 0.0) + intensity * 0.012
            )
        elif cost.cost_type == "recovery_window_loss":
            for process in state.processes.values():
                process.fatigue = clamp(process.fatigue + intensity * 0.006)

    def _latest_event(self, events: list[Event], event_type: str) -> Event | None:
        for event in reversed(events):
            if event.event_type == event_type:
                return event
        return None

    def _latest(self, events: list[Event], event_type: str) -> dict[str, Any]:
        event = self._latest_event(events, event_type)
        return event.payload if event else {}

    def _payload_float(self, payload: dict[str, Any], key: str) -> float:
        try:
            return clamp(float(payload.get(key, 0.0)))
        except (TypeError, ValueError):
            return 0.0
