from __future__ import annotations

from typing import Any

from rpf.core.events import Event
from rpf.core.models import SimulationState, TickContext, clamp
from rpf.core.semantics import defensive_memory, fate_memory, memory_pressure, unrecognized_contribution
from rpf.core.viability import (
    AffordanceWidth,
    DeformationTrace,
    FutureConstraintTrace,
    ViabilityConstraint,
    ViabilityRequirement,
    ViabilityTickTrace,
)


class RelationalViabilityEngine:
    """Trace-only kernel for constrained relational viability.

    This engine must not mutate SimulationState. It explains which lower-layer
    pressures make continuation costly, narrow affordances, and produce visible
    deformation.
    """

    def evaluate_pre_response(self, state: SimulationState, context: TickContext, events: list[Event]) -> ViabilityTickTrace:
        future_constraints = self._future_constraints(state, events)
        constraints = self._constraints(state, context, events, future_constraints)
        requirements = self._requirements(state, constraints, events)
        widths = self._affordance_widths(state, constraints, requirements, events)
        tension = self._dramatic_tension(constraints, requirements, widths, [])
        return ViabilityTickTrace(
            tick=state.tick,
            tick_type=context.tick_type,
            constraints=constraints,
            requirements=requirements,
            affordance_widths=widths,
            future_constraints=future_constraints,
            dramatic_tension=tension,
            evidence_refs=[event.event_id for event in events[-8:]],
        )

    def scheduler_preview(self, state: SimulationState) -> dict[str, float]:
        """State-only viability preview for temporal rhythm decisions.

        This runs before tick events exist, so it must not emit evidence events or
        mutate state. It gives the scheduler a bounded sense of whether pressure
        is becoming too costly to remain latent.
        """

        recognition_pressure = max(
            (
                clamp((d.current_pressure + d.vulnerability_cost + d.threat_if_denied + d.identity_dependency) / 4)
                for process in state.processes.values()
                for d in process.recognition_demands
            ),
            default=0.0,
        )
        material_pressure = max(state.field_state.material_pressures.values(), default=0.0)
        spatial_pressure = max(state.field_state.spatial_constraints.values(), default=0.0)
        binding_pressure = max((binding.strength for binding in state.bindings), default=0.0)
        repair_debt = state.relation_metrics.get("repair_debt", 0.0)
        relation_load = self._relation_sediment_load(state)
        memory = max(memory_pressure(state), defensive_memory(state), fate_memory(state))
        speech_block = self._max_speech_block(state)
        face_constraint = max(
            max(state.field_state.audience_pressure.values(), default=0.0),
            state.relation_metrics.get("face_risk_pressure", 0.0),
        )
        future_constraint_load = self._future_constraint_load(state)
        viability_pressure = clamp(
            recognition_pressure * 0.25
            + material_pressure * 0.16
            + spatial_pressure * 0.05
            + binding_pressure * 0.14
            + repair_debt * 0.16
            + memory * 0.12
            + speech_block * 0.08
            + face_constraint * 0.05
            + future_constraint_load * 0.08
            + relation_load * 0.07
        )
        latent_instability = clamp(viability_pressure * 0.7 + repair_debt * 0.15 + memory * 0.15 + relation_load * 0.08)
        micro_readiness = clamp(binding_pressure * 0.35 + viability_pressure * 0.35 + face_constraint * 0.1 + speech_block * 0.2 + relation_load * 0.05)
        scene_readiness = clamp(viability_pressure * 0.45 + material_pressure * 0.2 + recognition_pressure * 0.15 + repair_debt * 0.2 + relation_load * 0.06)
        return {
            "viability_pressure": viability_pressure,
            "latent_instability": latent_instability,
            "micro_readiness": micro_readiness,
            "scene_readiness": scene_readiness,
            "recognition_pressure": recognition_pressure,
            "material_pressure": clamp(material_pressure),
            "spatial_pressure": clamp(spatial_pressure),
            "binding_pressure": clamp(binding_pressure),
            "repair_debt": clamp(repair_debt),
            "memory_pressure": clamp(memory),
            "speech_block": clamp(speech_block),
            "face_constraint": clamp(face_constraint),
            "future_constraint_load": clamp(future_constraint_load),
            "relation_sediment_load": clamp(relation_load),
        }

    def evaluate_post_response(
        self,
        state: SimulationState,
        context: TickContext,
        pre_trace: ViabilityTickTrace,
        events: list[Event],
    ) -> ViabilityTickTrace:
        deformations = self._deformations(state, pre_trace, events)
        tension = self._dramatic_tension(pre_trace.constraints, pre_trace.requirements, pre_trace.affordance_widths, deformations)
        return pre_trace.model_copy(
            update={
                "deformations": deformations,
                "dramatic_tension": tension,
                "evidence_refs": sorted(set(pre_trace.evidence_refs + [event.event_id for event in events[-10:]])),
            }
        )

    def _constraints(
        self,
        state: SimulationState,
        context: TickContext,
        events: list[Event],
        future_constraints: list[FutureConstraintTrace],
    ) -> list[ViabilityConstraint]:
        constraints: list[ViabilityConstraint] = []
        evidence = [event.event_id for event in events[-8:]]
        material = max(state.field_state.material_pressures.values(), default=0.0)
        if material > 0.05:
            constraints.append(
                ViabilityConstraint(
                    constraint_id=f"c-{state.tick:04d}-material",
                    constraint_type="material_pressure",
                    source_layer="field",
                    affected_processes=sorted(state.processes),
                    affected_requirements=["resource_access", "relation_continuation", "repair_availability"],
                    intensity=clamp(material),
                    activation_condition="material pressure is active in field_state.material_pressures",
                    downstream_effects=["narrows practical repair", "raises continuation cost"],
                    evidence_refs=evidence,
                )
            )
        audience = max(state.field_state.audience_pressure.values(), default=0.0)
        face = max(audience, state.relation_metrics.get("face_risk_pressure", 0.0))
        if face > 0.05:
            constraints.append(
                ViabilityConstraint(
                    constraint_id=f"c-{state.tick:04d}-face",
                    constraint_type="public_face_risk",
                    source_layer="field",
                    affected_processes=sorted(state.processes),
                    affected_requirements=["face_continuation", "recognition_access", "truth_integration"],
                    intensity=clamp(face),
                    activation_condition="audience or face-risk pressure makes direct recognition socially costly",
                    downstream_effects=["raises observer risk", "encourages public performance"],
                    evidence_refs=evidence,
                )
            )
        speech_block = self._max_speech_block(state)
        if speech_block > 0.05:
            constraints.append(
                ViabilityConstraint(
                    constraint_id=f"c-{state.tick:04d}-speech",
                    constraint_type="speech_inhibition",
                    source_layer="process",
                    affected_processes=[pid for pid, process in state.processes.items() if process.speech_inhibition],
                    affected_requirements=["recognition_access", "repair_availability", "truth_integration"],
                    intensity=clamp(speech_block),
                    activation_condition="speech inhibition makes direct expression costly",
                    downstream_effects=["narrows direct speech", "encourages silence or substitution"],
                    evidence_refs=evidence,
                )
            )
        spatial = max(state.field_state.spatial_constraints.values(), default=0.0)
        if spatial > 0.05:
            constraints.append(
                ViabilityConstraint(
                    constraint_id=f"c-{state.tick:04d}-spatial",
                    constraint_type="sedimented_spatial_constraint",
                    source_layer="field",
                    affected_processes=sorted(state.processes),
                    affected_requirements=["exit_availability", "speech_access", "repair_availability"],
                    intensity=clamp(spatial),
                    activation_condition="prior relation history has sedimented into spatial constraint",
                    downstream_effects=["narrows neutral co-presence", "makes movement and objects interpretable"],
                    evidence_refs=evidence,
                )
            )
        repair_debt = state.relation_metrics.get("repair_debt", 0.0)
        if repair_debt > 0.05:
            constraints.append(
                ViabilityConstraint(
                    constraint_id=f"c-{state.tick:04d}-repair-debt",
                    constraint_type="historical_repair_debt",
                    source_layer="history",
                    affected_processes=sorted(state.processes),
                    affected_requirements=["repair_availability", "relation_continuation", "memory_integration"],
                    intensity=clamp(repair_debt),
                    activation_condition="unrepaired prior outcomes raise the cost of clean continuation",
                    downstream_effects=["raises failure cost", "biases future interpretation"],
                    evidence_refs=evidence,
                )
            )
        recognition_debt = state.relation_metrics.get("relation_sediment.recognition_debt", 0.0)
        repair_access_narrowing = state.relation_metrics.get("relation_sediment.repair_access_narrowing", 0.0)
        symbolic_accounting = state.relation_metrics.get("relation_sediment.symbolic_accounting_load", 0.0)
        public_definition = state.relation_metrics.get("relation_sediment.public_definition_load", 0.0)
        asymmetry = state.relation_metrics.get("relation_sediment.asymmetry_load", 0.0)
        if recognition_debt > 0.025:
            constraints.append(
                ViabilityConstraint(
                    constraint_id=f"c-{state.tick:04d}-relation-recognition-debt",
                    constraint_type="sedimented_recognition_debt",
                    source_layer="relation_sedimentation",
                    affected_processes=sorted(state.processes),
                    affected_requirements=["recognition_access", "repair_availability", "relation_continuation"],
                    intensity=clamp(recognition_debt),
                    activation_condition="prior relation sediment keeps unsettled recognition claims available",
                    downstream_effects=["raises clean-recognition cost", "biases later ambiguity toward injury"],
                    evidence_refs=self._relation_event_refs(events) or evidence,
                )
            )
        if repair_access_narrowing > 0.025:
            constraints.append(
                ViabilityConstraint(
                    constraint_id=f"c-{state.tick:04d}-relation-repair-access",
                    constraint_type="sedimented_repair_access_narrowing",
                    source_layer="relation_sedimentation",
                    affected_processes=sorted(state.processes),
                    affected_requirements=["repair_availability", "speech_access", "truth_integration"],
                    intensity=clamp(repair_access_narrowing),
                    activation_condition="prior relation sediment narrows which repair routes still feel usable",
                    downstream_effects=["raises direct repair cost", "encourages substitution, delay, or silence"],
                    evidence_refs=self._relation_event_refs(events) or evidence,
                )
            )
        relation_public_or_asymmetric = max(symbolic_accounting, public_definition, asymmetry)
        if relation_public_or_asymmetric > 0.035:
            constraints.append(
                ViabilityConstraint(
                    constraint_id=f"c-{state.tick:04d}-relation-definition",
                    constraint_type="sedimented_relation_definition_pressure",
                    source_layer="relation_sedimentation",
                    affected_processes=sorted(state.processes),
                    affected_requirements=["face_continuation", "role_continuation", "truth_integration"],
                    intensity=clamp(relation_public_or_asymmetric),
                    activation_condition="relation history has sedimented into a public, asymmetric, or accounting-based definition",
                    downstream_effects=["makes neutral interaction harder", "raises role and face pressure"],
                    evidence_refs=self._relation_event_refs(events) or evidence,
                )
            )
        memory = max(memory_pressure(state), defensive_memory(state), fate_memory(state))
        if memory > 0.05:
            constraints.append(
                ViabilityConstraint(
                    constraint_id=f"c-{state.tick:04d}-memory",
                    constraint_type="memory_load",
                    source_layer="memory",
                    affected_processes=sorted(state.processes),
                    affected_requirements=["memory_integration", "identity_continuity", "recognition_access"],
                    intensity=clamp(memory),
                    activation_condition="remembered prior injury constrains what current signals can mean",
                    downstream_effects=["increases defensive interpretation", "reduces memory plasticity"],
                    evidence_refs=evidence,
                )
            )
        for future in future_constraints:
            constraints.append(
                ViabilityConstraint(
                    constraint_id=f"c-{state.tick:04d}-{future.constraint_id}",
                    constraint_type=future.constraint_type,
                    source_layer="future_constraint",
                    affected_processes=future.affected_processes,
                    affected_requirements=future.constrained_requirements,
                    intensity=future.intensity,
                    activation_condition=future.mechanism,
                    duration_policy=future.persistence,
                    decay_rate=0.01 if future.persistence == "decaying" else 0.0,
                    reversibility="none" if future.persistence == "irreversible" else "partial",
                    downstream_effects=future.downstream_effects,
                    evidence_refs=future.evidence_refs,
                )
            )
        return constraints

    def _requirements(
        self,
        state: SimulationState,
        constraints: list[ViabilityConstraint],
        events: list[Event],
    ) -> list[ViabilityRequirement]:
        requirements: list[ViabilityRequirement] = []
        evidence = [event.event_id for event in events[-8:]]
        constraint_pressure = self._avg([constraint.intensity for constraint in constraints])
        for process in state.processes.values():
            for demand in process.recognition_demands:
                pressure = clamp(
                    (demand.current_pressure + demand.vulnerability_cost + demand.threat_if_denied + demand.identity_dependency) / 4
                )
                contribution = unrecognized_contribution(state)
                recognition_debt = state.relation_metrics.get("relation_sediment.recognition_debt", 0.0)
                urgency = clamp(max(pressure, contribution * 0.85, recognition_debt * 0.9))
                requirements.append(
                    ViabilityRequirement(
                        requirement_id=f"vr-{state.tick:04d}-{demand.demand_id}",
                        requirement_type="recognition_access",
                        holder_process_id=demand.holder_process_id,
                        target_process_id=demand.demanded_from,
                        urgency=urgency,
                        negotiability=clamp(1.0 - demand.threat_if_denied),
                        minimum_satisfaction_condition=f"{demand.recognition_type} must be granted, deferred, or transformed enough for relation continuation",
                        failure_cost=clamp(max(demand.threat_if_denied, state.relation_metrics.get("repair_debt", 0.0), recognition_debt)),
                        deformation_tendency="accusation_or_silence",
                        source="recognition_demand",
                        evidence_refs=evidence,
                    )
                )
        for binding in state.bindings:
            requirements.append(
                ViabilityRequirement(
                    requirement_id=f"vr-{state.tick:04d}-{binding.binding_id}-continuation",
                    requirement_type="relation_continuation",
                    holder_process_id=binding.process_ids[0],
                    target_process_id=binding.process_ids[1] if len(binding.process_ids) > 1 else None,
                    urgency=clamp(max(binding.strength, constraint_pressure)),
                    negotiability=clamp(1.0 - max(binding.exit_cost.values(), default=0.0)),
                    minimum_satisfaction_condition="binding must remain livable, be repaired, or become exit-capable",
                    failure_cost=clamp(max(binding.exit_cost.values(), default=0.0)),
                    deformation_tendency="avoidance_or_practical_substitution",
                    source="co_presence_binding",
                    evidence_refs=evidence,
                )
            )
        if state.relation_metrics.get("repair_debt", 0.0) > 0.05:
            repair_narrowing = state.relation_metrics.get("relation_sediment.repair_access_narrowing", 0.0)
            requirements.append(
                ViabilityRequirement(
                    requirement_id=f"vr-{state.tick:04d}-repair-availability",
                    requirement_type="repair_availability",
                    holder_process_id="relation",
                    target_process_id=None,
                    urgency=clamp(max(state.relation_metrics.get("repair_debt", 0.0), repair_narrowing)),
                    negotiability=clamp(0.35 - repair_narrowing * 0.18),
                    minimum_satisfaction_condition="repair route must remain imaginable or the relation stabilizes around debt",
                    failure_cost=clamp(max(state.relation_metrics.get("repair_debt", 0.0), repair_narrowing)),
                    deformation_tendency="practical_help_or_delay",
                    source="relation_metric.repair_debt+relation_sediment.repair_access_narrowing",
                    evidence_refs=sorted(set(evidence + self._relation_event_refs(events))),
                )
            )
        return requirements

    def _affordance_widths(
        self,
        state: SimulationState,
        constraints: list[ViabilityConstraint],
        requirements: list[ViabilityRequirement],
        events: list[Event],
    ) -> list[AffordanceWidth]:
        widths: list[AffordanceWidth] = []
        evidence = [event.event_id for event in events[-8:]]
        for pid in state.processes:
            relevant = [
                constraint
                for constraint in constraints
                if pid in constraint.affected_processes or constraint.affected_processes == sorted(state.processes)
            ]
            requirement_pressure = self._avg([req.urgency for req in requirements if req.holder_process_id in {pid, "relation"}])
            constraint_pressure = self._avg([constraint.intensity for constraint in relevant])
            relation_narrowing = state.relation_metrics.get("relation_sediment.repair_access_narrowing", 0.0)
            relation_asymmetry = state.relation_metrics.get("relation_sediment.asymmetry_load", 0.0)
            direct_cost = clamp(constraint_pressure * 0.6 + requirement_pressure * 0.4 + relation_narrowing * 0.08 + relation_asymmetry * 0.04)
            width = clamp(1.0 - direct_cost)
            widths.append(
                AffordanceWidth(
                    tick=state.tick,
                    process_id=pid,
                    width=width,
                    narrowing_constraints=[constraint.constraint_id for constraint in relevant],
                    direct_response_cost=direct_cost,
                    evidence_refs=evidence,
                )
            )
        return widths

    def _deformations(self, state: SimulationState, pre_trace: ViabilityTickTrace, events: list[Event]) -> list[DeformationTrace]:
        action = self._latest(events, "ActionSelectionEvent")
        expression = self._latest(events, "ExpressionSelectionEvent")
        if not action or not expression:
            return []
        action_mode = str(action.payload.get("action_mode", ""))
        expression_mode = str(expression.payload.get("expression_mode", ""))
        if action_mode == "enacted" and expression_mode == "spoken":
            return []
        source = str(action.payload.get("source_process", "unknown"))
        target = str(action.payload.get("target_process", "unknown"))
        requirement = self._most_relevant_requirement(pre_trace, source)
        visible_form = str(expression.payload.get("surface_signal", action.payload.get("signal_type", "unknown")))
        distance = self._deformation_distance(action_mode, expression_mode)
        ambiguity = clamp(float(expression.payload.get("ambiguity", action.payload.get("ambiguity", 0.0))))
        observer_risk = clamp(max(state.field_state.audience_pressure.values(), default=0.0) + ambiguity * 0.35)
        return [
            DeformationTrace(
                deformation_id=f"d-{state.tick:04d}-{action.payload.get('action_id', 'action')}-{expression.payload.get('expression_id', 'expression')}",
                source_process_id=source,
                target_process_id=target,
                visible_form=visible_form,
                blocked_requirement_id=requirement.requirement_id if requirement else None,
                deformation_type=self._deformation_type(action_mode, expression_mode),
                deformation_distance=distance,
                ambiguity=ambiguity,
                observer_risk=observer_risk,
                expected_recognition_failure_modes=self._failure_modes(action_mode, expression_mode),
                evidence_refs=[action.event_id, expression.event_id],
            )
        ]

    def _dramatic_tension(
        self,
        constraints: list[ViabilityConstraint],
        requirements: list[ViabilityRequirement],
        widths: list[AffordanceWidth],
        deformations: list[DeformationTrace],
    ) -> float:
        viability_pressure = self._avg([requirement.urgency for requirement in requirements])
        constraint_intensity = self._avg([constraint.intensity for constraint in constraints])
        affordance_narrowing = 1.0 - self._avg([width.width for width in widths], default=1.0)
        deformation_distance = self._avg([deformation.deformation_distance for deformation in deformations])
        future_load = self._avg([constraint.intensity for constraint in constraints if constraint.source_layer == "future_constraint"])
        return clamp(
            viability_pressure * 0.3
            + constraint_intensity * 0.25
            + affordance_narrowing * 0.2
            + deformation_distance * 0.15
            + future_load * 0.1
        )

    def _future_constraint_load(self, state: SimulationState) -> float:
        return max((constraint.intensity for constraint in self._future_constraints(state)), default=0.0)

    def _future_constraints(self, state: SimulationState, events: list[Event] | None = None) -> list[FutureConstraintTrace]:
        traces: list[FutureConstraintTrace] = []
        relation_event_refs = self._relation_event_refs(events or [])
        for index, record in enumerate(state.irreversibility_register.records, start=1):
            constrained = self._requirements_for_future_category(record.category)
            traces.append(
                FutureConstraintTrace(
                    constraint_id=f"fc-irr-{index:02d}-{record.record_id}",
                    constraint_type=f"irreversible_{record.category}",
                    source_layer="irreversibility",
                    source_ref_id=record.record_id,
                    affected_processes=record.affected_processes,
                    constrained_requirements=constrained,
                    intensity=self._irreversibility_intensity(record.category),
                    persistence="irreversible",
                    mechanism="irreversibility record narrows future alternatives and changes what direct repair can mean",
                    lost_alternatives=record.lost_alternatives,
                    downstream_effects=record.future_constraints,
                    evidence_refs=[record.source_event_id],
                )
            )
        classification_index = 1
        for process in state.processes.values():
            for classification in process.active_classifications:
                if not classification.active:
                    continue
                traces.append(
                    FutureConstraintTrace(
                        constraint_id=f"fc-cls-{classification_index:02d}-{classification.classification_id}",
                        constraint_type=f"operative_label_{classification.label}",
                        source_layer="classification",
                        source_ref_id=classification.classification_id,
                        affected_processes=[classification.target_process_id or process.process_id],
                        constrained_requirements=self._requirements_for_label(classification.label),
                        intensity=clamp(classification.legitimacy * 0.45 + classification.future_interpretation_bias * 1.4),
                        persistence="operative",
                        mechanism="operative classification biases future interpretation before any new exchange occurs",
                        downstream_effects=["future signals are interpreted through the operative label"],
                        evidence_refs=[classification.source_event_id],
                    )
                )
                classification_index += 1
        memory_candidates = [
            memory
            for process in state.processes.values()
            for memory in process.memory_traces
            if memory.active
        ]
        memory_candidates = sorted(memory_candidates, key=lambda item: item.salience * item.confidence, reverse=True)[:4]
        for index, memory in enumerate(memory_candidates, start=1):
            intensity = clamp(memory.salience * memory.confidence * 0.5)
            if intensity <= 0.05:
                continue
            traces.append(
                FutureConstraintTrace(
                    constraint_id=f"fc-mem-{index:02d}-{memory.memory_id}",
                    constraint_type="reconstructed_memory_constraint",
                    source_layer="memory",
                    source_ref_id=memory.memory_id,
                    affected_processes=[memory.owner_process_id],
                    constrained_requirements=self._requirements_for_memory(memory.reconstruction_biases),
                    intensity=intensity,
                    persistence="decaying",
                    mechanism="reconstructed memory changes which future signals can be treated as neutral",
                    downstream_effects=[f"remembered_as:{memory.remembered_as}"],
                    evidence_refs=[memory.source_event_id],
                )
            )
        relation_specs = [
            (
                "recognition-debt",
                "relation_sediment.recognition_debt",
                "sedimented_recognition_debt_future_constraint",
                ["recognition_access", "repair_availability"],
                ["future ambiguous signals are read through unsettled recognition debt"],
            ),
            (
                "repair-access",
                "relation_sediment.repair_access_narrowing",
                "sedimented_repair_access_future_constraint",
                ["repair_availability", "speech_access"],
                ["direct repair has fewer plausible routes"],
            ),
            (
                "shared-fate",
                "relation_sediment.shared_fate_load",
                "sedimented_shared_fate_future_constraint",
                ["exit_availability", "relation_continuation"],
                ["future choices are interpreted as shared fate decisions"],
            ),
        ]
        for index, (slug, metric, constraint_type, requirements, downstream) in enumerate(relation_specs, start=1):
            value = clamp(state.relation_metrics.get(metric, 0.0))
            if value <= 0.06:
                continue
            traces.append(
                FutureConstraintTrace(
                    constraint_id=f"fc-rel-{index:02d}-{slug}",
                    constraint_type=constraint_type,
                    source_layer="relation_sedimentation",
                    source_ref_id=metric,
                    affected_processes=sorted(state.processes),
                    constrained_requirements=requirements,
                    intensity=clamp(value * 0.75),
                    persistence="decaying",
                    mechanism=f"{metric} narrows future relation viability before the next exchange",
                    downstream_effects=downstream,
                    evidence_refs=relation_event_refs,
                )
            )
        traces.extend(self._opportunity_future_constraints(state))
        traces.extend(self._action_reversibility_future_constraints(state))
        return traces

    def _opportunity_future_constraints(self, state: SimulationState) -> list[FutureConstraintTrace]:
        specs = {
            "repair_window_loss": (
                "opportunity_repair_window_loss",
                ["repair_availability", "recognition_access"],
                ["future repair must work through a narrower and more expensive route"],
            ),
            "evidence_window_loss": (
                "opportunity_evidence_window_loss",
                ["truth_integration", "speech_access"],
                ["future case movement is constrained by a missed evidence or testimony window"],
            ),
            "trust_window_loss": (
                "opportunity_trust_window_loss",
                ["relation_continuation", "recognition_access"],
                ["future trust updates carry a higher baseline cost"],
            ),
            "social_exposure_cost": (
                "opportunity_social_exposure_cost",
                ["face_continuation", "truth_integration"],
                ["future private resolution is filtered through public readability"],
            ),
            "ordinary_task_spillover": (
                "opportunity_ordinary_task_spillover",
                ["resource_access", "relation_continuation"],
                ["future interaction starts with ordinary task debt already active"],
            ),
            "recovery_window_loss": (
                "opportunity_recovery_window_loss",
                ["resource_access", "repair_availability"],
                ["future repair and attention must pass through reduced bodily recovery"],
            ),
        }
        traces: list[FutureConstraintTrace] = []
        metrics = [
            (key.removeprefix("opportunity_cost."), clamp(value))
            for key, value in sorted(state.relation_metrics.items())
            if key.startswith("opportunity_cost.") and key != "opportunity_cost.total"
        ]
        for index, (cost_type, value) in enumerate(metrics, start=1):
            spec = specs.get(cost_type)
            if not spec or value <= 0.035:
                continue
            constraint_type, requirements, downstream = spec
            traces.append(
                FutureConstraintTrace(
                    constraint_id=f"fc-opp-{index:02d}-{cost_type}",
                    constraint_type=constraint_type,
                    source_layer="opportunity_cost",
                    source_ref_id=f"opportunity_cost.{cost_type}",
                    affected_processes=sorted(state.processes),
                    constrained_requirements=requirements,
                    intensity=clamp(value * 0.9),
                    persistence="decaying",
                    mechanism=f"missed {cost_type} window narrows future alternatives after the action path",
                    downstream_effects=downstream,
                    evidence_refs=[],
                )
            )
        return traces

    def _action_reversibility_future_constraints(self, state: SimulationState) -> list[FutureConstraintTrace]:
        pressure = clamp(state.relation_metrics.get("action_reversibility.pressure", 0.0))
        crossed = clamp(state.relation_metrics.get("action_reversibility.threshold_crossed", 0.0))
        symbolic = clamp(state.relation_metrics.get("action_reversibility.symbolic_only", 0.0))
        specs = [
            (
                "reversibility_pressure",
                pressure,
                "action_reversibility_pressure_constraint",
                ["repair_availability", "recognition_access"],
                ["future repair must address the action's residue before it can restore ordinary interaction"],
            ),
            (
                "threshold_crossed",
                crossed,
                "action_threshold_crossed_future_constraint",
                ["memory_integration", "relation_continuation", "repair_availability"],
                ["the action can no longer be treated as a purely local disturbance"],
            ),
            (
                "symbolic_only",
                symbolic,
                "symbolic_only_repair_future_constraint",
                ["identity_continuity", "speech_access", "truth_integration"],
                ["future repair can acknowledge the mark but cannot restore the lost alternative"],
            ),
        ]
        traces: list[FutureConstraintTrace] = []
        for index, (slug, value, constraint_type, requirements, downstream) in enumerate(specs, start=1):
            if value <= 0.04:
                continue
            traces.append(
                FutureConstraintTrace(
                    constraint_id=f"fc-rev-{index:02d}-{slug}",
                    constraint_type=constraint_type,
                    source_layer="action_reversibility",
                    source_ref_id=f"action_reversibility.{slug}",
                    affected_processes=sorted(state.processes),
                    constrained_requirements=requirements,
                    intensity=clamp(value * 0.82),
                    persistence="decaying" if slug == "reversibility_pressure" else "operative",
                    mechanism=f"{slug} narrows what later action can still undo",
                    downstream_effects=downstream,
                    evidence_refs=[],
                )
            )
        return traces

    def _irreversibility_intensity(self, category: str) -> float:
        return {
            "symbolic_debt_lock": 0.82,
            "public_reclassification": 0.72,
            "role_lock": 0.76,
            "absence_history": 0.7,
            "identity_mark": 0.8,
        }.get(category, 0.68)

    def _requirements_for_future_category(self, category: str) -> list[str]:
        return {
            "symbolic_debt_lock": ["recognition_access", "repair_availability", "care_availability"],
            "public_reclassification": ["face_continuation", "truth_disclosure", "public_performance"],
            "role_lock": ["care_availability", "exit_availability", "agency_continuation"],
            "absence_history": ["repair_availability", "memory_integration", "recognition_access"],
            "identity_mark": ["truth_integration", "identity_continuity", "speech_access"],
        }.get(category, ["repair_availability", "identity_continuity", "relation_continuation"])

    def _requirements_for_label(self, label: str) -> list[str]:
        if "owe" in label or "debt" in label:
            return ["recognition_access", "care_availability", "repair_availability"]
        if "control" in label:
            return ["agency_continuation", "care_availability", "exit_availability"]
        if "public" in label or "fine" in label:
            return ["face_continuation", "truth_disclosure", "public_performance"]
        if "never" in label or "unreachable" in label:
            return ["recognition_access", "repair_availability", "presence_continuation"]
        if "right" in label:
            return ["identity_continuity", "speech_access", "repair_availability"]
        return ["recognition_access", "identity_continuity"]

    def _requirements_for_memory(self, biases: list[str]) -> list[str]:
        requirements: set[str] = set()
        for bias in biases:
            if bias == "injury_reconstruction":
                requirements.update({"recognition_access", "repair_availability"})
            elif bias == "defensive_reconstruction":
                requirements.update({"speech_access", "face_continuation"})
            elif bias == "fate_lock":
                requirements.update({"identity_continuity", "exit_availability"})
            elif bias == "operative_label":
                requirements.update({"truth_integration", "recognition_access"})
            else:
                requirements.add("memory_integration")
        return sorted(requirements or {"memory_integration"})

    def _most_relevant_requirement(self, trace: ViabilityTickTrace, source_process: str) -> ViabilityRequirement | None:
        candidates = [req for req in trace.requirements if req.holder_process_id in {source_process, "relation"}]
        if not candidates:
            candidates = trace.requirements
        if not candidates:
            return None
        return max(candidates, key=lambda requirement: (requirement.urgency, requirement.failure_cost, requirement.requirement_id))

    def _deformation_distance(self, action_mode: str, expression_mode: str) -> float:
        action_distance = {
            "enacted": 0.05,
            "escalated": 0.25,
            "substituted": 0.55,
            "inhibited": 0.75,
        }.get(action_mode, 0.35)
        expression_distance = {
            "spoken": 0.05,
            "tonal_shift": 0.25,
            "timing_distortion": 0.45,
            "gesture": 0.55,
            "public_performance": 0.6,
            "silence": 0.8,
        }.get(expression_mode, 0.35)
        return clamp((action_distance + expression_distance) / 2)

    def _deformation_type(self, action_mode: str, expression_mode: str) -> str:
        if action_mode == "inhibited" or expression_mode == "silence":
            return "inhibition"
        if action_mode == "substituted":
            return "substitution"
        if expression_mode in {"gesture", "timing_distortion", "tonal_shift"}:
            return "expression_distortion"
        if expression_mode == "public_performance":
            return "public_mask"
        return "indirect_adaptation"

    def _failure_modes(self, action_mode: str, expression_mode: str) -> list[str]:
        modes: list[str] = []
        if action_mode in {"inhibited", "substituted"}:
            modes.append("displaced")
        if expression_mode in {"silence", "gesture", "timing_distortion"}:
            modes.append("misunderstood")
        if expression_mode == "public_performance":
            modes.append("postponed")
        if not modes:
            modes.append("partial")
        return modes

    def _max_speech_block(self, state: SimulationState) -> float:
        keys = {"direct_need", "apology", "anger", "dependency_admission"}
        values = [
            value
            for process in state.processes.values()
            for key, value in process.speech_inhibition.items()
            if key in keys
        ]
        return clamp(max(values, default=0.0))

    def _relation_sediment_load(self, state: SimulationState) -> float:
        keys = [
            "relation_sediment.recognition_debt",
            "relation_sediment.repair_access_narrowing",
            "relation_sediment.symbolic_accounting_load",
            "relation_sediment.future_lock_load",
            "relation_sediment.shared_fate_load",
            "relation_sediment.public_definition_load",
            "relation_sediment.asymmetry_load",
            "relation_sediment.memory_saturation",
        ]
        return clamp(max((state.relation_metrics.get(key, 0.0) for key in keys), default=0.0))

    def _relation_event_refs(self, events: list[Event]) -> list[str]:
        return sorted(
            {
                event.event_id
                for event in events
                if event.event_type == "RelationSedimentationEvent"
            }
        )

    def _latest(self, events: list[Event], event_type: str) -> Event | None:
        for event in reversed(events):
            if event.event_type == event_type:
                return event
        return None

    def _avg(self, values: list[float], default: float = 0.0) -> float:
        if not values:
            return default
        return clamp(sum(values) / len(values))

    def event_payloads(self, trace: ViabilityTickTrace) -> list[tuple[str, dict[str, Any], list[str]]]:
        events: list[tuple[str, dict[str, Any], list[str]]] = []
        for constraint in trace.constraints:
            events.append(("ConstraintActivationEvent", constraint.model_dump(mode="json"), constraint.evidence_refs))
        for requirement in trace.requirements:
            events.append(("ViabilityRequirementEvent", requirement.model_dump(mode="json"), requirement.evidence_refs))
        for width in trace.affordance_widths:
            events.append(("AffordanceWidthEvent", width.model_dump(mode="json"), width.evidence_refs))
        for deformation in trace.deformations:
            events.append(("DeformationTraceEvent", deformation.model_dump(mode="json"), deformation.evidence_refs))
        for future_constraint in trace.future_constraints:
            events.append(("FutureConstraintEvent", future_constraint.model_dump(mode="json"), future_constraint.evidence_refs))
        events.append(
            (
                "DerivedDramaticTensionEvent",
                {
                    "tick": trace.tick,
                    "tick_type": trace.tick_type,
                    "dramatic_tension": trace.dramatic_tension,
                    "source": "derived_from_relational_viability_trace",
                    "constraint_count": len(trace.constraints),
                    "requirement_count": len(trace.requirements),
                    "deformation_count": len(trace.deformations),
                    "future_constraint_count": len(trace.future_constraints),
                },
                trace.evidence_refs,
            )
        )
        return events
