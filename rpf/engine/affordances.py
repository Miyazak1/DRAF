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
            "local_world_context": self._local_world_context(state),
            "selected_affordance": selected.__dict__,
            "candidates": [candidate.__dict__ for candidate in sorted(candidates, key=lambda item: item.score, reverse=True)],
        }
        state.relation_metrics["last_affordance_score"] = selected.score
        return selected

    def _candidates(self, state: SimulationState, context: TickContext) -> list[AffordanceCandidate]:
        p1 = state.processes["p1"]
        p2 = state.processes["p2"]
        audience = max(state.field_state.audience_pressure.values(), default=0.0)
        spatial = state.field_state.spatial_constraints
        material = state.field_state.material_pressures
        urgency = material_urgency(state)
        avoidance_paths = spatial.get("avoidance_paths", 0.0)
        memory_saturated_space = spatial.get("memory_saturated_space", 0.0)
        charged_objects = max(
            material.get("charged_objects", 0.0),
            material.get("symbolic_debt_objects", 0.0),
        )
        imagined_audience = max(
            state.field_state.audience_pressure.get("imagined_audience", 0.0),
            state.field_state.audience_pressure.get("reputational_echo", 0.0),
        )
        evidence_decay = max(
            material.get("decayed_evidence", 0.0),
            material.get("contamination_trace", 0.0),
            spatial.get("archive_basement", 0.0),
        )
        institutional_silence = max(
            state.field_state.audience_pressure.get("local_police_silence", 0.0),
            state.field_state.audience_pressure.get("victim_families_waiting", 0.0),
        )
        symbol_density = max(
            p1.relevance_triggers.get("yellow_symbol", 0.0),
            p2.relevance_triggers.get("yellow_symbol", 0.0),
            spatial.get("abandoned_refinery_map", 0.0),
            material.get("contamination_trace", 0.0),
        )
        testimony_instability = max(
            p1.speech_inhibition.get("testimony_detail", 0.0),
            p1.threat_sensitivity.get("being_disbelieved", 0.0),
            p2.threat_sensitivity.get("being_misled", 0.0),
        )
        contribution = unrecognized_contribution(state)
        repair_debt = state.relation_metrics.get("repair_debt", 0.0)
        conflict = state.relation_metrics.get("conflict_pressure", 0.0)
        recognition_debt = state.relation_metrics.get("relation_sediment.recognition_debt", 0.0)
        repair_access_narrowing = state.relation_metrics.get("relation_sediment.repair_access_narrowing", 0.0)
        symbolic_accounting = state.relation_metrics.get("relation_sediment.symbolic_accounting_load", 0.0)
        public_definition = state.relation_metrics.get("relation_sediment.public_definition_load", 0.0)
        asymmetry_load = state.relation_metrics.get("relation_sediment.asymmetry_load", 0.0)
        memory_saturation = state.relation_metrics.get("relation_sediment.memory_saturation", 0.0)
        inquiry_progress = state.relation_metrics.get("inquiry.progress_pressure", 0.0)
        inquiry_contamination = state.relation_metrics.get("inquiry.contamination_load", 0.0)
        inquiry_suppression = state.relation_metrics.get("inquiry.suppression_load", 0.0)
        inquiry_relationship_risk = state.relation_metrics.get("inquiry.relationship_risk", 0.0)
        institutional_silencing = state.relation_metrics.get("institutional.silencing_pressure", 0.0)
        institutional_exposure = state.relation_metrics.get("institutional.public_exposure", 0.0)
        institutional_gatekeeping = state.field_state.audience_pressure.get("institutional_gatekeeping", 0.0)
        witness_protective_silence = state.relation_metrics.get("witness_strategy.protective_silence", 0.0)
        witness_disclosure_width = state.relation_metrics.get("witness_strategy.disclosure_width", 0.0)
        witness_confirmation_risk = state.relation_metrics.get("witness_strategy.confirmation_risk", 0.0)
        daily_body_load = state.relation_metrics.get("daily_ecology.body_load", 0.0)
        daily_unfinished_tasks = state.relation_metrics.get("daily_ecology.unfinished_tasks", 0.0)
        daily_routine_overlap = max(
            state.relation_metrics.get("daily_ecology.routine_overlap", 0.0),
            spatial.get("routine_overlap", 0.0),
        )
        daily_object_friction = max(
            state.relation_metrics.get("daily_ecology.object_friction", 0.0),
            material.get("object_friction", 0.0),
        )
        daily_waiting_pressure = state.relation_metrics.get("daily_ecology.waiting_pressure", 0.0)
        attention_body_management = self._attention_focus(state, "body_management")
        attention_case_fixation = self._attention_focus(state, "case_fixation")
        attention_threat_monitoring = self._attention_focus(state, "threat_monitoring")
        attention_repair_opportunity = self._attention_focus(state, "repair_opportunity")
        attention_avoidance_route = self._attention_focus(state, "avoidance_route")
        attention_memory_intrusion = self._attention_focus(state, "memory_intrusion")
        local_world_context = self._local_world_context(state)
        local_route_blockage = local_world_context["blocked_route_pressure"]
        local_public_visibility = local_world_context["public_visibility_pressure"]
        local_memory_site_pressure = local_world_context["memory_site_pressure"]
        local_resource_scarcity = local_world_context["resource_scarcity_pressure"]
        remembered_history = memory_pressure(state)
        injury_history = injury_memory(state)
        defensive_history = defensive_memory(state)
        fate_history = fate_memory(state)
        recognition = max((d.current_pressure for p in state.processes.values() for d in p.recognition_demands), default=0.0)
        binding = max((b.strength for b in state.bindings), default=0.0)
        active = {r.rpp_id: r.intensity for r in state.active_rpps}
        composition = self._dominant_composition(state)
        frame = self._frame_context(state)
        relevance = self._relevance_context(state)
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
                "sedimented_avoidance_paths": avoidance_paths * 0.055,
                "local_world.route_blockage": local_route_blockage * 0.035,
                "relation_repair_access_narrowing": repair_access_narrowing * 0.06,
                "frame_avoidance_scene": frame["avoidance_scene"] * 0.07,
                "relevance_delayed_reply": relevance["delayed_reply"] * 0.08,
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
                "daily_unfinished_tasks": daily_unfinished_tasks * 0.08,
                "daily_object_friction": daily_object_friction * 0.08,
                "attention_repair_opportunity": attention_repair_opportunity * 0.08,
                "local_world.resource_scarcity": local_resource_scarcity * 0.045,
                "local_world.route_blockage": local_route_blockage * 0.025,
                "defensive_memory": defensive_history * 0.02,
                "sedimented_charged_objects": charged_objects * 0.04,
                "relation_repair_access_narrowing": repair_access_narrowing * 0.05,
                "frame_repair_scene": frame["repair_scene"] * 0.065,
                "frame_debt_accounting": frame["debt_accounting"] * 0.035,
                "relevance_repair_opening": relevance["repair_opening"] * 0.07,
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
                "local_world.resource_scarcity": local_resource_scarcity * 0.06,
                "debt_lock": (0.18 if composition == "debt_lock" else 0.0),
                "resentment": p1.resentment_pressure * 0.1,
                "injury_memory": injury_history * 0.025,
                "sedimented_charged_objects": charged_objects * 0.05,
                "memory_saturated_space": memory_saturated_space * 0.025,
                "relation_recognition_debt": recognition_debt * 0.08,
                "relation_symbolic_accounting": symbolic_accounting * 0.06,
                "frame_debt_accounting": frame["debt_accounting"] * 0.075,
                "frame_recognition_trial": frame["recognition_trial"] * 0.05,
                "frame_double_bind_penalty": -frame["double_bind"] * 0.08,
                "frame_care_control_penalty": -frame["care_control"] * 0.05,
                "relevance_recognition_claim": relevance["recognition_claim"] * 0.02,
                "relevance_material_cost": relevance["material_cost"] * 0.01,
                "relevance_double_bind_penalty": -relevance["double_bind"] * 0.07,
                "relevance_being_controlled_penalty": -relevance["being_controlled"] * 0.04,
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
                "local_world.public_visibility": local_public_visibility * 0.08,
                "public_face_split": (0.22 if composition == "public_face_split" else 0.0),
                "fate_memory": fate_history * 0.02,
                "sedimented_imagined_audience": imagined_audience * 0.055,
                "relation_public_definition": public_definition * 0.07,
                "frame_public_performance": frame["public_performance"] * 0.08,
                "relevance_public_exposure": relevance["public_exposure"] * 0.11,
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
                "daily_body_load": daily_body_load * 0.08,
                "daily_routine_overlap": daily_routine_overlap * 0.06,
                "local_world.resource_scarcity": local_resource_scarcity * 0.04,
                "local_world.route_blockage": local_route_blockage * 0.035,
                "attention_body_management": attention_body_management * 0.08,
                "care_bind_double_bind": (0.24 if composition == "care_bind_double_bind" else 0.0),
                "dependency_inhibition": p2.speech_inhibition.get("dependency_admission", 0.0) * 0.12,
                "remembered_history": remembered_history * 0.015,
                "memory_saturated_space": memory_saturated_space * 0.02,
                "relation_asymmetry_load": asymmetry_load * 0.06,
                "frame_care_control": frame["care_control"] * 0.07,
                "relevance_being_controlled": relevance["being_controlled"] * 0.13,
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
                "memory_saturated_space": memory_saturated_space * 0.03,
                "local_world.public_visibility": local_public_visibility * 0.035,
                "local_world.memory_site": local_memory_site_pressure * 0.04,
                "relation_asymmetry_load": asymmetry_load * 0.05,
                "frame_double_bind": frame["double_bind"] * 0.08,
                "relevance_double_bind": relevance["double_bind"] * 0.15,
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
                "daily_unfinished_tasks": daily_unfinished_tasks * 0.14,
                "daily_routine_overlap": daily_routine_overlap * 0.1,
                "daily_object_friction": daily_object_friction * 0.1,
                "attention_body_management": attention_body_management * 0.08,
                "local_world.resource_scarcity": local_resource_scarcity * 0.12,
                "remembered_history": remembered_history * 0.01,
                "sedimented_charged_objects": charged_objects * 0.06,
                "relation_symbolic_accounting": symbolic_accounting * 0.04,
                "frame_material_accounting": frame["material_accounting"] * 0.07,
                "frame_debt_accounting": frame["debt_accounting"] * 0.035,
                "relevance_material_cost": relevance["material_cost"] * 0.1,
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
                "daily_body_load": daily_body_load * 0.08,
                "daily_waiting_pressure": daily_waiting_pressure * 0.08,
                "attention_avoidance_route": attention_avoidance_route * 0.09,
                "local_world.route_blockage": local_route_blockage * 0.065,
                "local_world.memory_site": local_memory_site_pressure * 0.035,
                "attention_threat_monitoring": attention_threat_monitoring * 0.06,
                "recognition_trap": (0.2 if composition == "recognition_trap" else 0.0),
                "pursuit_withdrawal": active.get("pursuit_withdrawal", 0.0) * 0.1,
                "defensive_memory": defensive_history * 0.025,
                "sedimented_avoidance_paths": avoidance_paths * 0.06,
                "memory_saturated_space": memory_saturated_space * 0.02,
                "relation_recognition_debt": recognition_debt * 0.06,
                "relation_memory_saturation": memory_saturation * 0.04,
                "frame_avoidance_scene": frame["avoidance_scene"] * 0.07,
                "frame_recognition_trial": frame["recognition_trial"] * 0.035,
                "relevance_delayed_reply": relevance["delayed_reply"] * 0.075,
                "relevance_exit_threat": relevance["exit_threat"] * 0.035,
            },
            0.7,
            "the claim is felt before it is answerable",
        )
        evidence_review = self._candidate(
            "contaminated_evidence_review",
            "evidence_contamination",
            "cold case evidence review",
            "p2",
            "p1",
            tick_bias,
            {
                "decayed_evidence": evidence_decay * 0.24,
                "institutional_silence": institutional_silence * 0.16,
                "pattern_attraction": p2.threat_sensitivity.get("pattern_attraction", 0.0) * 0.14,
                "procedural_gap": p2.relevance_triggers.get("procedural_gap", 0.0) * 0.12,
                "attention_case_fixation": attention_case_fixation * 0.12,
                "recognition_trial": frame["recognition_trial"] * 0.05,
                "material_accounting": frame["material_accounting"] * 0.04,
                "memory_saturation": memory_saturation * 0.04,
                "relation_public_definition": public_definition * 0.03,
                "inquiry_progress_pressure": inquiry_progress * 0.22,
                "inquiry_contamination_load": inquiry_contamination * 0.16,
                "local_world.route_blockage": local_route_blockage * 0.055,
                "local_world.resource_scarcity": local_resource_scarcity * 0.035,
                "institutional_public_exposure": institutional_exposure * 0.18,
                "institutional_gatekeeping": institutional_gatekeeping * 0.1,
                "witness_strategy_disclosure_width": witness_disclosure_width * 0.12,
                "witness_strategy_confirmation_risk": witness_confirmation_risk * 0.08,
            },
            0.66,
            "the file becomes less like evidence and more like a demand for testimony",
        )
        testimony_probe = self._candidate(
            "unstable_testimony_probe",
            "testimony_gap",
            "witness memory under procedural pressure",
            "p2",
            "p1",
            tick_bias,
            {
                "testimony_instability": testimony_instability * 0.26,
                "recognition": recognition * 0.18,
                "local_silence": institutional_silence * 0.12,
                "double_bind_pressure": state.relation_metrics.get("double_bind_pressure", 0.0) * 0.12,
                "memory_saturated_space": memory_saturated_space * 0.04,
                "local_world.memory_site": local_memory_site_pressure * 0.075,
                "local_world.public_visibility": local_public_visibility * 0.035,
                "relation_recognition_debt": recognition_debt * 0.05,
                "frame_recognition_trial": frame["recognition_trial"] * 0.08,
                "frame_double_bind": frame["double_bind"] * 0.05,
                "relevance_recognition_claim": relevance["recognition_claim"] * 0.04,
                "inquiry_suppression_load": inquiry_suppression * 0.22,
                "inquiry_relationship_risk": inquiry_relationship_risk * 0.16,
                "institutional_silencing_pressure": institutional_silencing * 0.2,
                "institutional_gatekeeping": institutional_gatekeeping * 0.12,
                "witness_strategy_protective_silence": witness_protective_silence * 0.2,
                "witness_strategy_confirmation_risk": witness_confirmation_risk * 0.14,
                "attention_case_fixation": attention_case_fixation * 0.1,
                "attention_threat_monitoring": attention_threat_monitoring * 0.08,
            },
            0.78,
            "your memory is needed, but using it may damage the shared reality",
        )
        forbidden_symbol = self._candidate(
            "forbidden_symbol_confrontation",
            "yellow_symbol",
            "contaminating symbol becomes speakable",
            "p1",
            "p2",
            tick_bias,
            {
                "symbol_density": symbol_density * 0.28,
                "naming_symbol_block": p1.speech_inhibition.get("naming_symbol", 0.0) * 0.12,
                "reality_doubt": p1.threat_sensitivity.get("reality_doubt", 0.0) * 0.12,
                "pattern_attraction": p2.threat_sensitivity.get("pattern_attraction", 0.0) * 0.08,
                "fate_memory": fate_history * 0.03,
                "relation_memory_saturation": memory_saturation * 0.05,
                "local_world.memory_site": local_memory_site_pressure * 0.08,
                "local_world.route_blockage": local_route_blockage * 0.03,
                "frame_double_bind": frame["double_bind"] * 0.07,
                "relevance_double_bind": relevance["double_bind"] * 0.05,
                "inquiry_contamination_load": inquiry_contamination * 0.24,
                "inquiry_relationship_risk": inquiry_relationship_risk * 0.18,
                "institutional_silencing_pressure": institutional_silencing * 0.14,
                "institutional_public_exposure": institutional_exposure * 0.1,
                "witness_strategy_confirmation_risk": witness_confirmation_risk * 0.12,
                "witness_strategy_protective_silence": witness_protective_silence * 0.08,
                "attention_threat_monitoring": attention_threat_monitoring * 0.12,
                "attention_memory_intrusion": attention_memory_intrusion * 0.08,
            },
            0.86,
            "the symbol cannot be verified, but not naming it now changes the case",
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
            evidence_review,
            testimony_probe,
            forbidden_symbol,
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

    def _relevance_context(self, state: SimulationState) -> dict[str, float]:
        markers = [
            "delayed_reply",
            "recognition_claim",
            "public_exposure",
            "being_controlled",
            "double_bind",
            "material_cost",
            "repair_opening",
            "exit_threat",
        ]
        result: dict[str, float] = {}
        for marker in markers:
            dynamic = max(
                (
                    value
                    for key, value in state.relation_metrics.items()
                    if key.startswith("relevance_field.") and key.endswith(f".{marker}")
                ),
                default=0.0,
            )
            basal = max((process.relevance_triggers.get(marker, 0.0) for process in state.processes.values()), default=0.0)
            result[marker] = max(dynamic, basal)
        return result

    def _local_world_context(self, state: SimulationState) -> dict[str, float]:
        return {
            "blocked_route_pressure": state.relation_metrics.get("local_world.blocked_route_pressure", 0.0),
            "public_visibility_pressure": state.relation_metrics.get("local_world.public_visibility_pressure", 0.0),
            "memory_site_pressure": state.relation_metrics.get("local_world.memory_site_pressure", 0.0),
            "resource_scarcity_pressure": state.relation_metrics.get("local_world.resource_scarcity_pressure", 0.0),
        }

    def _attention_focus(self, state: SimulationState, focus: str) -> float:
        return max(
            (
                float(value or 0.0)
                for key, value in state.relation_metrics.items()
                if key.startswith("attention_drift.") and key.endswith(f".{focus}")
            ),
            default=0.0,
        )
