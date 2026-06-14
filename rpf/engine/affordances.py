from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from rpf.core.models import SimulationState, TickContext, clamp
from rpf.core.semantics import defensive_memory, fate_memory, injury_memory, material_urgency, memory_pressure, unrecognized_contribution


@dataclass(frozen=True)
class AffordanceCandidate:
    affordance_id: str
    signal_type: str
    frame: str
    source_process: str
    target_process: str
    score: float
    ambiguity: float
    inferred_relation_claim: str
    evidence: dict[str, float]


class AffordanceEngine:
    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config
        self.last_diagnostics: dict[str, Any] = {}

    def select(self, state: SimulationState, context: TickContext) -> AffordanceCandidate:
        candidates = self._candidates(state, context)
        selected = max(candidates, key=lambda item: (item.score, item.affordance_id))
        self.last_diagnostics = {
            "tick": state.tick,
            "tick_type": context.tick_type,
            "selected_affordance": selected.__dict__,
            "candidates": [candidate.__dict__ for candidate in sorted(candidates, key=lambda item: item.score, reverse=True)],
        }
        state.relation_metrics["last_affordance_score"] = selected.score
        return selected

    def _candidates(self, state: SimulationState, context: TickContext) -> list[AffordanceCandidate]:
        p1 = state.processes["p1"]
        p2 = state.processes["p2"]
        audience = max(state.field_state.audience_pressure.values(), default=0.0)
        urgency = material_urgency(state)
        contribution = unrecognized_contribution(state)
        repair_debt = state.relation_metrics.get("repair_debt", 0.0)
        conflict = state.relation_metrics.get("conflict_pressure", 0.0)
        remembered_history = memory_pressure(state)
        injury_history = injury_memory(state)
        defensive_history = defensive_memory(state)
        fate_history = fate_memory(state)
        recognition = max((d.current_pressure for p in state.processes.values() for d in p.recognition_demands), default=0.0)
        binding = max((b.strength for b in state.bindings), default=0.0)
        active = {r.rpp_id: r.intensity for r in state.active_rpps}
        composition = self._dominant_composition(state)
        tick_bias = self.config["tick_bias"][context.tick_type]  # type: ignore[index]

        delayed = self._candidate(
            "mediated_delay",
            "delayed_reply",
            "message latency",
            "p2",
            "p1",
            tick_bias,
            {
                "silence_charge": state.relation_metrics.get("silence_charge", 0.0) * 0.32,
                "delay_relevance": p1.relevance_triggers.get("delayed_reply", 0.0) * 0.26,
                "anxious_silence_circuit": (0.22 if composition == "anxious_silence_circuit" else 0.0),
                "pursuit_withdrawal": active.get("pursuit_withdrawal", 0.0) * 0.12,
                "low_ambiguity_tolerance": (1.0 - p1.ambiguity_tolerance) * 0.1,
                "injury_memory": injury_history * 0.02,
            },
            0.75,
            "absence is treated as evidence about being chosen",
        )
        practical = self._candidate(
            "practical_repair_offer",
            "practical_repair",
            "logistical help instead of explicit repair",
            "p2",
            "p1",
            tick_bias,
            {
                "repair_debt": repair_debt * 0.22,
                "apology_inhibition": p2.speech_inhibition.get("apology", 0.0) * 0.25,
                "contribution": contribution * 0.18,
                "debt_lock": (0.18 if composition == "debt_lock" else 0.0),
                "material_urgency": urgency * 0.12,
                "defensive_memory": defensive_history * 0.02,
            },
            0.58,
            "help appears where acknowledgment is unavailable",
        )
        contribution_claim = self._candidate(
            "unacknowledged_contribution_claim",
            "unacknowledged_help",
            "cost becomes visible through a practical demand",
            "p1",
            "p2",
            tick_bias,
            {
                "contribution": contribution * 0.34,
                "recognition": recognition * 0.22,
                "material_urgency": urgency * 0.16,
                "debt_lock": (0.18 if composition == "debt_lock" else 0.0),
                "resentment": p1.resentment_pressure * 0.1,
                "injury_memory": injury_history * 0.025,
            },
            0.62,
            "my cost is not being recognized",
        )
        public_performance = self._candidate(
            "public_performance",
            "public_politeness",
            "public competence or normality performance",
            "p2",
            "p1",
            tick_bias,
            {
                "public_private_gap": state.relation_metrics.get("public_private_gap", 0.0) * 0.3,
                "face_risk": state.relation_metrics.get("face_risk_pressure", 0.0) * 0.2,
                "audience": audience * 0.22,
                "public_face_split": (0.22 if composition == "public_face_split" else 0.0),
                "fate_memory": fate_history * 0.02,
            },
            0.68,
            "the public version of us is safer than the private one",
        )
        care_intervention = self._candidate(
            "care_intervention",
            "care_instruction",
            "care action that constrains agency",
            "p2",
            "p1",
            tick_bias,
            {
                "care_dependency": state.relation_metrics.get("care_dependency", 0.0) * 0.3,
                "binding": binding * 0.18,
                "fatigue": (p1.fatigue + p2.fatigue) / 2 * 0.14,
                "care_bind_double_bind": (0.24 if composition == "care_bind_double_bind" else 0.0),
                "dependency_inhibition": p2.speech_inhibition.get("dependency_admission", 0.0) * 0.12,
                "remembered_history": remembered_history * 0.015,
            },
            0.5,
            "care protects and controls at the same time",
        )
        double_bind_response = self._candidate(
            "double_bind_response",
            "contradictory_request",
            "answering one demand violates another",
            "p2",
            "p1",
            tick_bias,
            {
                "double_bind_pressure": state.relation_metrics.get("double_bind_pressure", 0.0) * 0.34,
                "speech_inhibition": max(p1.speech_inhibition.get("direct_need", 0.0), p1.speech_inhibition.get("anger", 0.0)) * 0.2,
                "binding": binding * 0.14,
                "care_bind_double_bind": (0.18 if composition == "care_bind_double_bind" else 0.0),
                "conflict": conflict * 0.1,
                "fate_memory": fate_history * 0.025,
            },
            0.72,
            "any available answer will later be usable against me",
        )
        material_pressure = self._candidate(
            "material_pressure_intrusion",
            "material_urgency",
            "resource pressure enters interaction",
            "field",
            "p1-p2",
            tick_bias,
            {
                "material_urgency": urgency * 0.42,
                "binding": binding * 0.18,
                "contribution": contribution * 0.18,
                "conflict": conflict * 0.08,
                "remembered_history": remembered_history * 0.01,
            },
            0.45,
            "the environment forces the relation to account for cost",
        )
        gaze_avoidance = self._candidate(
            "embodied_avoidance",
            "gaze_avoidance",
            "body avoids a claim before speech can",
            "p2",
            "p1",
            tick_bias,
            {
                "repair_debt": repair_debt * 0.2,
                "apology_inhibition": p2.speech_inhibition.get("apology", 0.0) * 0.2,
                "conflict": conflict * 0.16,
                "recognition_trap": (0.2 if composition == "recognition_trap" else 0.0),
                "pursuit_withdrawal": active.get("pursuit_withdrawal", 0.0) * 0.1,
                "defensive_memory": defensive_history * 0.025,
            },
            0.7,
            "the claim is felt before it is answerable",
        )
        return [
            delayed,
            practical,
            contribution_claim,
            public_performance,
            care_intervention,
            double_bind_response,
            material_pressure,
            gaze_avoidance,
        ]

    def _candidate(
        self,
        affordance_id: str,
        signal_type: str,
        frame: str,
        source_process: str,
        target_process: str,
        tick_bias: float,
        factors: dict[str, float],
        ambiguity: float,
        inferred_relation_claim: str,
    ) -> AffordanceCandidate:
        base = float(self.config.get("base_score", 0.04))
        score = clamp(base + tick_bias + sum(factors.values()))
        return AffordanceCandidate(
            affordance_id=affordance_id,
            signal_type=signal_type,
            frame=frame,
            source_process=source_process,
            target_process=target_process,
            score=score,
            ambiguity=ambiguity,
            inferred_relation_claim=inferred_relation_claim,
            evidence={key: round(value, 4) for key, value in factors.items() if abs(value) > 0.0001},
        )

    def _dominant_composition(self, state: SimulationState) -> str | None:
        composition_scores = {
            key.removeprefix("composition."): value
            for key, value in state.relation_metrics.items()
            if key.startswith("composition.")
        }
        if not composition_scores:
            return None
        return max(composition_scores.items(), key=lambda item: item[1])[0]
