import json
from pathlib import Path

from rpf.engine.simulator import Simulator
from rpf.scenarios.loader import load_scenario


def test_observability_outputs_scheduler_rpp_and_projection_traces(tmp_path):
    scenario_path = Path("examples/shared_apartment_unresolved_sacrifice.yaml")
    sim = Simulator.from_scenario(load_scenario(scenario_path), scenario_path, seed=42)
    sim.run(steps=30, output_dir=tmp_path / "run")

    scheduler = json.loads((tmp_path / "run" / "scheduler_diagnostics.json").read_text())
    affordance = json.loads((tmp_path / "run" / "affordance_trace.json").read_text())
    action = json.loads((tmp_path / "run" / "action_trace.json").read_text())
    expression = json.loads((tmp_path / "run" / "expression_trace.json").read_text())
    recognition = json.loads((tmp_path / "run" / "recognition_trace.json").read_text())
    fate = json.loads((tmp_path / "run" / "fate_transition_trace.json").read_text())
    frame_definition = json.loads((tmp_path / "run" / "frame_trace.json").read_text())
    account = json.loads((tmp_path / "run" / "account_trace.json").read_text())
    normativity = json.loads((tmp_path / "run" / "normativity_trace.json").read_text())
    relevance = json.loads((tmp_path / "run" / "relevance_trace.json").read_text())
    attention = json.loads((tmp_path / "run" / "attention_trace.json").read_text())
    opportunity = json.loads((tmp_path / "run" / "opportunity_trace.json").read_text())
    reversibility = json.loads((tmp_path / "run" / "reversibility_trace.json").read_text())
    position = json.loads((tmp_path / "run" / "position_trace.json").read_text())
    binding_trace = json.loads((tmp_path / "run" / "binding_trace.json").read_text())
    expectation = json.loads((tmp_path / "run" / "expectation_trace.json").read_text())
    memory = json.loads((tmp_path / "run" / "memory_trace.json").read_text())
    environment = json.loads((tmp_path / "run" / "environment_trace.json").read_text())
    disposition = json.loads((tmp_path / "run" / "disposition_trace.json").read_text())
    relation = json.loads((tmp_path / "run" / "relation_trace.json").read_text())
    viability = json.loads((tmp_path / "run" / "viability_trace.json").read_text())
    rpp_trace = json.loads((tmp_path / "run" / "rpp_activation_trace.json").read_text())
    rpp_dynamics = json.loads((tmp_path / "run" / "rpp_dynamics_trace.json").read_text())
    projection = json.loads((tmp_path / "run" / "projection_trace.json").read_text())
    timeline_events = [
        json.loads(line)
        for line in (tmp_path / "run" / "timeline.jsonl").read_text().splitlines()
        if line.strip()
    ]

    assert len(scheduler) == 30
    assert [item["tick_index"] for item in scheduler] == list(range(1, 31))
    assert {"scene", "micro_interaction", "latent"} <= {item["selected_tick_type"] for item in scheduler}
    assert all("tick_type_scores" in item for item in scheduler)
    assert all("time_mapping_reason" in item for item in scheduler)
    assert all("memory_pressure" in item["input_factors"] for item in scheduler)
    assert all("relevance_load" in item["input_factors"] for item in scheduler)
    assert all("viability_pressure" in item["input_factors"] for item in scheduler)
    assert all("relation_sediment_load" in item["input_factors"] for item in scheduler)
    assert all("daily_ecology_pressure" in item["input_factors"] for item in scheduler)
    assert all("attention_pressure" in item["input_factors"] for item in scheduler)
    assert all("opportunity_pressure" in item["input_factors"] for item in scheduler)
    assert all("reversibility_pressure" in item["input_factors"] for item in scheduler)
    assert any(item["input_factors"]["daily_ecology_pressure"] > 0 for item in scheduler[1:])
    assert any(item["input_factors"]["attention_pressure"] > 0 for item in scheduler[1:])
    assert any(item["input_factors"]["opportunity_pressure"] > 0 for item in scheduler[1:])
    assert any(item["input_factors"]["reversibility_pressure"] > 0 for item in scheduler[1:])
    assert all("viability_rhythm" in item for item in scheduler)
    assert all("scene_readiness" in item["viability_rhythm"] for item in scheduler)
    assert any(item["viability_rhythm"]["scene_viability_bias"] > 0 for item in scheduler)

    assert affordance
    assert all(item["selected_affordance"]["affordance_id"] for item in affordance)
    assert all(item["candidates"] for item in affordance)
    assert any(
        key.startswith("sedimented_") or key == "memory_saturated_space"
        for item in affordance
        for candidate in item["candidates"]
        for key in candidate["evidence"]
    )
    assert any(
        key.startswith("relation_")
        for item in affordance
        for candidate in item["candidates"]
        for key in candidate["evidence"]
    )
    assert any(
        key.startswith("frame_")
        for item in affordance
        for candidate in item["candidates"]
        for key in candidate["evidence"]
    )
    assert any(
        key.startswith("relevance_")
        for item in affordance
        for candidate in item["candidates"]
        for key in candidate["evidence"]
    )
    assert any(
        key.startswith("daily_")
        for item in affordance
        for candidate in item["candidates"]
        for key in candidate["evidence"]
    )
    assert any(
        key.startswith("attention_")
        for item in affordance
        for candidate in item["candidates"]
        for key in candidate["evidence"]
    )

    assert action
    assert all(item["selected_action"]["action_id"] for item in action)
    assert all(item["selected_action"]["action_mode"] for item in action)
    assert all(item["candidates"] for item in action)
    assert any(item["selected_action"]["action_mode"] in {"inhibited", "substituted", "escalated"} for item in action)
    assert all(item["viability_context"]["evidence_refs"] for item in action)
    assert any(
        key.startswith("viability_")
        for item in action
        for key in item["selected_action"]["evidence"]
    )
    assert any(
        key.startswith("expected_")
        for item in action
        for key in item["selected_action"]["evidence"]
    )
    assert any(
        key.startswith("account_")
        for item in action
        for key in item["selected_action"]["evidence"]
    )
    assert any(
        key.startswith("norm_")
        for item in action
        for key in item["selected_action"]["evidence"]
    )
    assert any(
        key.startswith("position_") or key == "target_debtor"
        for item in action
        for key in item["selected_action"]["evidence"]
    )

    assert expression
    assert all(item["selected_expression"]["expression_id"] for item in expression)
    assert all(item["selected_expression"]["expression_mode"] for item in expression)
    assert all(item["selected_expression"]["surface_signal"] for item in expression)
    assert all(item["candidates"] for item in expression)
    assert any(item["selected_expression"]["expression_mode"] in {"silence", "gesture", "timing_distortion", "tonal_shift"} for item in expression)
    assert all(item["viability_context"]["evidence_refs"] for item in expression)
    assert any(
        key.startswith("viability_")
        for item in expression
        for key in item["selected_expression"]["evidence"]
    )
    assert any(
        key.startswith("expected_")
        for item in expression
        for key in item["selected_expression"]["evidence"]
    )
    assert any(
        key.startswith("account_")
        for item in expression
        for key in item["selected_expression"]["evidence"]
    )
    assert any(
        key.startswith("norm_")
        for item in expression
        for key in item["selected_expression"]["evidence"]
    )
    assert any(
        key.startswith("frame_")
        for item in expression
        for key in item["selected_expression"]["evidence"]
    )

    assert recognition
    assert all(item["outcome"] for item in recognition)
    assert all(item["scores"] for item in recognition)
    assert all(item["evidence"] for item in recognition)
    assert any("memory_pressure" in item["evidence"] for item in recognition)
    assert any("action_mode" in item["evidence"] for item in recognition)
    assert any("expression_mode" in item["evidence"] for item in recognition)
    assert any("viability_dramatic_tension" in item["evidence"] for item in recognition)
    assert any("viability_deformation_distance" in item["evidence"] for item in recognition)
    assert any(item["evidence"].get("viability_evidence_refs") for item in recognition)
    assert any(
        key.startswith("relation_") and item["evidence"].get(key, 0) > 0
        for item in recognition
        for key in item["evidence"]
    )
    assert any(
        key.startswith("account_") and item["evidence"].get(key, 0) > 0
        for item in recognition
        for key in item["evidence"]
    )
    assert any(
        key.startswith("norm_")
        for item in recognition
        for key in item["evidence"]
    )
    assert any(
        key.startswith("frame_")
        for item in recognition
        for key in item["evidence"]
    )
    assert any(
        key.startswith("position_")
        for item in recognition
        for key in item["evidence"]
    )

    assert fate
    assert all(item["transition_id"] for item in fate)
    assert all(item["transition_type"] for item in fate)
    assert all(item["evidence"] for item in fate)

    assert frame_definition
    assert any(item["frame_key"].startswith("frame_definition.") for item in frame_definition)
    assert any(item["frame_type"] in {"debt_accounting", "repair_scene", "avoidance_scene", "public_performance", "recognition_trial"} for item in frame_definition)
    assert all(item["caused_by_events"] for item in frame_definition)

    assert relevance
    assert any(item["marker_key"].startswith("relevance_field.") for item in relevance)
    assert any(item["marker"] in {"delayed_reply", "recognition_claim", "public_exposure", "material_cost", "repair_opening"} for item in relevance)
    assert all(item["caused_by_events"] for item in relevance)
    assert any("AttentionDriftEvent" in item["evidence_event_types"] for item in relevance)
    assert any("OpportunityCostEvent" in item["evidence_event_types"] for item in relevance)
    assert any("ActionReversibilityEvent" in item["evidence_event_types"] for item in relevance)

    assert attention
    assert all(item["event_type"] == "AttentionDriftEvent" for item in attention)
    assert any(item["dominant_focus"] in {"body_management", "case_fixation", "threat_monitoring", "repair_opportunity", "avoidance_route", "memory_intrusion"} for item in attention)
    assert all(item["caused_by_events"] for item in attention)

    assert opportunity
    assert all(item["event_type"] == "OpportunityCostEvent" for item in opportunity)
    assert any(
        item["cost_type"] in {
            "recovery_window_loss",
            "repair_window_loss",
            "evidence_window_loss",
            "social_exposure_cost",
            "trust_window_loss",
            "ordinary_task_spillover",
        }
        for item in opportunity
    )
    assert all(item["caused_by_events"] for item in opportunity)

    assert reversibility
    assert all(item["event_type"] == "ActionReversibilityEvent" for item in reversibility)
    assert all(item["reversibility_id"] for item in reversibility)
    assert any(item["threshold_state"] in {"recoverable", "narrowing", "threshold_crossed", "symbolic_only"} for item in reversibility)
    assert any(item["threshold_state"] in {"narrowing", "threshold_crossed", "symbolic_only"} for item in reversibility)
    assert all(item["caused_by_events"] for item in reversibility)

    assert position
    assert any(item["position_key"].startswith("position_field.") for item in position)
    assert any(item["position_type"] in {"claimant", "debtor", "defender", "caretaker", "controlled", "public_performer", "withdrawer", "trapped_party", "repair_partner", "bound_party"} for item in position)
    assert all(item["caused_by_events"] for item in position)

    assert account
    assert any(item["account"] in {"safety", "dignity", "control", "relation", "meaning", "energy"} for item in account)
    assert all(item["caused_by_events"] for item in account)

    assert normativity
    assert any(item["norm_key"].startswith("norm_pressure.") for item in normativity)
    assert any(item["norm_type"] in {"claim_entitlement", "repair_obligation", "legitimacy_contestation", "reciprocity_obligation"} for item in normativity)
    assert all(item["caused_by_events"] for item in normativity)

    assert binding_trace
    assert any(item["event_type"] == "BindingUpdatedEvent" for item in binding_trace)
    assert any(item["event_type"] == "BindingDecayedEvent" for item in binding_trace)
    assert all(item["caused_by_events"] for item in binding_trace)
    assert any(
        "relation_sediment." in str(item["reason"])
        for item in binding_trace
    )

    assert expectation
    assert any(item["expectation_key"].startswith("expectation.") for item in expectation)
    assert any("refusal_expectation" in item["expectation_key"] for item in expectation)
    assert all(item["caused_by_events"] for item in expectation)

    assert memory
    assert all(item["memory_id"] for item in memory)
    assert all(item["owner_process_id"] for item in memory)
    assert all(item["remembered_as"] for item in memory)
    assert all(item["evidence"] for item in memory)
    assert any(item["reconstruction_biases"] for item in memory)
    assert any(item["evidence"].get("future_constraint_refs") for item in memory)
    assert any(item["evidence"].get("future_constraint_pressure", 0) > 0 for item in memory)
    assert any("relevance_pressure" in item["evidence"] for item in memory)

    assert environment
    assert any(item["event_type"] == "FieldUpdateEvent" for item in environment)
    assert any(item["event_type"] == "EnactedMicroWorldEvent" for item in environment)
    assert any(item["event_type"] == "DailyEcologyEvent" for item in environment)
    assert any("spatial_constraints." in item.get("changed_field_path", "") for item in environment)
    assert any(item.get("caused_by_events") for item in environment)
    assert any(item.get("routine_phase") for item in environment if item["event_type"] == "DailyEcologyEvent")
    assert any(item.get("deltas", {}).get("fatigue_delta") is not None for item in environment if item["event_type"] == "DailyEcologyEvent")
    assert any(
        item.get("reason") == "sedimented field pressure decays when not fully renewed"
        and item.get("new_value", 0) < item.get("previous_value", 0)
        for item in environment
        if item["event_type"] == "FieldUpdateEvent"
    )
    assert any(
        str(item.get("reason", "")).startswith("relation sediment")
        for item in environment
        if item["event_type"] == "FieldUpdateEvent"
    )

    assert disposition
    assert any(item["changed_path"] in {"checking_tendency", "ambiguity_tolerance", "risk_suspension_scope"} for item in disposition)
    assert any(item["changed_path"].startswith(("speech_inhibition.", "threat_sensitivity.")) for item in disposition)
    assert all(item["caused_by_events"] for item in disposition)
    assert any(
        item["reason"] == "process disposition sediment decays when not reinforced"
        for item in disposition
    )
    assert any(
        str(item["reason"]).startswith("relation-level")
        for item in disposition
    )

    assert relation
    assert any(item["metric"].startswith("relation_sediment.") for item in relation)
    assert any(item["metric"] == "relation_sediment.recognition_debt" for item in relation)
    assert any(item["metric"] == "relation_sediment.repair_access_narrowing" for item in relation)
    assert all(item["caused_by_events"] for item in relation)
    assert any(
        item["reason"] == "relation sediment decays when not reinforced"
        for item in relation
    )
    assert any(
        "NormativePressureEvent" in item["evidence_event_types"]
        for item in relation
    )

    assert len(viability) == 30
    assert all(item["constraints"] for item in viability)
    assert all(item["requirements"] for item in viability)
    assert all(item["affordance_widths"] for item in viability)
    assert any(item["deformations"] for item in viability)
    assert any(
        requirement["requirement_type"] == "recognition_access"
        for item in viability
        for requirement in item["requirements"]
    )
    assert any(item["future_constraints"] for item in viability)
    assert any(
        constraint["source_layer"] == "irreversibility"
        for item in viability
        for constraint in item["future_constraints"]
    )
    assert any(
        constraint["source_layer"] in {"classification", "memory"}
        for item in viability
        for constraint in item["future_constraints"]
    )
    assert any(
        constraint["source_layer"] == "future_constraint"
        for item in viability
        for constraint in item["constraints"]
    )
    assert any(
        constraint["constraint_type"] == "sedimented_spatial_constraint"
        for item in viability
        for constraint in item["constraints"]
    )
    assert any(
        constraint["source_layer"] == "relation_sedimentation"
        for item in viability
        for constraint in item["constraints"]
    )
    assert any(
        constraint["source_layer"] == "relation_sedimentation"
        for item in viability
        for constraint in item["future_constraints"]
    )
    assert any(
        constraint["source_layer"] == "opportunity_cost"
        for item in viability
        for constraint in item["future_constraints"]
    )
    assert any(
        constraint["source_layer"] == "action_reversibility"
        for item in viability
        for constraint in item["future_constraints"]
    )
    assert any(item["dramatic_tension"] > 0 for item in viability)
    viability_event_types = {
        "ConstraintActivationEvent",
        "ViabilityRequirementEvent",
        "AffordanceWidthEvent",
        "DeformationTraceEvent",
        "FutureConstraintEvent",
        "DerivedDramaticTensionEvent",
    }
    emitted_viability_events = {event["event_type"] for event in timeline_events if event["source_layer"] == "viability"}
    assert viability_event_types <= emitted_viability_events
    viability_event_ids = {event["event_id"] for event in timeline_events if event["source_layer"] == "viability"}
    action_events = [event for event in timeline_events if event["event_type"] == "ActionSelectionEvent"]
    assert action_events
    assert any(viability_event_ids.intersection(event["causal_refs"]) for event in action_events)
    expression_events = [event for event in timeline_events if event["event_type"] == "ExpressionSelectionEvent"]
    assert expression_events
    assert any(viability_event_ids.intersection(event["causal_refs"]) for event in expression_events)
    recognition_events = [event for event in timeline_events if event["event_type"] == "RecognitionEvent"]
    assert recognition_events
    assert any(viability_event_ids.intersection(event["causal_refs"]) for event in recognition_events)
    future_constraint_event_ids = {
        event["event_id"]
        for event in timeline_events
        if event["event_type"] == "FutureConstraintEvent"
    }
    memory_events = [event for event in timeline_events if event["event_type"] == "MemoryReconstructionEvent"]
    assert memory_events
    assert any(future_constraint_event_ids.intersection(event["causal_refs"]) for event in memory_events)
    field_update_events = [event for event in timeline_events if event["event_type"] == "FieldUpdateEvent"]
    micro_world_events = [event for event in timeline_events if event["event_type"] == "EnactedMicroWorldEvent"]
    disposition_events = [event for event in timeline_events if event["event_type"] == "DispositionSedimentationEvent"]
    relation_events = [event for event in timeline_events if event["event_type"] == "RelationSedimentationEvent"]
    binding_events = [event for event in timeline_events if event["event_type"] in {"BindingUpdatedEvent", "BindingDecayedEvent"}]
    expectation_events = [event for event in timeline_events if event["event_type"] == "ExpectationSedimentationEvent"]
    account_events = [event for event in timeline_events if event["event_type"] == "AccountPressureEvent"]
    normativity_events = [event for event in timeline_events if event["event_type"] == "NormativePressureEvent"]
    frame_events = [event for event in timeline_events if event["event_type"] == "FrameDefinitionEvent"]
    relevance_events = [event for event in timeline_events if event["event_type"] == "RelevanceShiftEvent"]
    position_events = [event for event in timeline_events if event["event_type"] == "PositioningEvent"]
    assert field_update_events
    assert micro_world_events
    assert disposition_events
    assert relation_events
    assert binding_events
    assert expectation_events
    assert account_events
    assert normativity_events
    assert frame_events
    assert relevance_events
    assert position_events
    assert any(event["causal_refs"] for event in field_update_events + micro_world_events)
    assert any(event["causal_refs"] for event in disposition_events)
    assert any(event["causal_refs"] for event in relation_events)
    assert any(event["causal_refs"] for event in binding_events)
    assert any(event["causal_refs"] for event in expectation_events)
    assert any(event["causal_refs"] for event in account_events)
    assert any(event["causal_refs"] for event in normativity_events)
    assert any(event["causal_refs"] for event in frame_events)
    assert any(event["causal_refs"] for event in relevance_events)
    assert any(event["causal_refs"] for event in position_events)
    relation_event_ids = {event["event_id"] for event in relation_events}
    assert any(relation_event_ids.intersection(event["causal_refs"]) for event in field_update_events)
    assert any(relation_event_ids.intersection(event["causal_refs"]) for event in disposition_events)
    assert any(relation_event_ids.intersection(event["causal_refs"]) for event in binding_events)
    assert any(
        event["event_id"] in viability_event["causal_refs"]
        for event in relation_events
        for viability_event in timeline_events
        if viability_event["source_layer"] == "viability"
    )

    assert rpp_trace
    assert {"pursuit_withdrawal", "repair_avoidance", "contribution_debt_loop"} <= {item["rpp_id"] for item in rpp_trace}
    assert all(item["eligibility_evidence"] for item in rpp_trace)
    assert any(
        any(str(ref).endswith("FutureConstraintEvent") for ref in item["eligibility_evidence"])
        for item in rpp_trace
    )
    assert any(item.get("semantic_role") == "unrecognized_contribution_debt" for item in rpp_trace)

    assert len(rpp_dynamics) == 30
    assert all("active_rpp_intensities" in item for item in rpp_dynamics)
    assert any(item["compositions"] for item in rpp_dynamics)

    assert len(projection) == 30
    assert projection[-1]["relationship_phase"] == "locked-in"
    assert projection[-1]["person_labels"]["p1"]

    aggregation = json.loads((tmp_path / "run" / "aggregation_traces.json").read_text())
    assert aggregation["relation_sedimentation"]["value"]
    assert aggregation["binding_evolution"]["value"]
    assert aggregation["expectation_sedimentation"]["value"]
    assert aggregation["account_pressure"]["value"]
    assert aggregation["normative_pressure"]["value"]
    assert aggregation["frame_definition"]["value"]
    assert aggregation["relevance_landscape"]["value"]
    assert aggregation["position_field"]["value"]


def test_yellow_sign_outputs_inquiry_trace_and_events(tmp_path):
    scenario_path = Path("examples/yellow_sign_cold_case.yaml")
    sim = Simulator.from_scenario(load_scenario(scenario_path), scenario_path, seed=42)
    output_dir = tmp_path / "run"
    sim.run(steps=8, output_dir=output_dir)

    inquiry = json.loads((output_dir / "inquiry_trace.json").read_text())
    scheduler = json.loads((output_dir / "scheduler_diagnostics.json").read_text())
    affordance = json.loads((output_dir / "affordance_trace.json").read_text())
    attention = json.loads((output_dir / "attention_trace.json").read_text())
    opportunity = json.loads((output_dir / "opportunity_trace.json").read_text())
    reversibility = json.loads((output_dir / "reversibility_trace.json").read_text())
    timeline_events = [
        json.loads(line)
        for line in (output_dir / "timeline.jsonl").read_text().splitlines()
        if line.strip()
    ]
    investigation_events = [event for event in timeline_events if event["event_type"] == "InvestigationUpdateEvent"]
    institutional_events = [event for event in timeline_events if event["event_type"] == "InstitutionalPressureEvent"]
    witness_events = [event for event in timeline_events if event["event_type"] == "WitnessStrategyEvent"]
    location_events = [event for event in timeline_events if event["event_type"] == "LocationEvidenceCouplingEvent"]
    accessibility_events = [event for event in timeline_events if event["event_type"] == "EvidenceAccessibilityEvent"]
    memory_events = [event for event in timeline_events if event["event_type"] == "MemoryReconstructionEvent"]
    investigation_event_ids = {event["event_id"] for event in investigation_events}
    institutional_trace = [item for item in inquiry if item.get("event_type") == "InstitutionalPressureEvent"]
    witness_trace = [item for item in inquiry if item.get("event_type") == "WitnessStrategyEvent"]
    location_trace = [item for item in inquiry if item.get("event_type") == "LocationEvidenceCouplingEvent"]
    investigation_trace = [item for item in inquiry if item.get("event_type") == "InvestigationUpdateEvent"]
    accessibility_trace = [item for item in inquiry if item.get("event_type") == "EvidenceAccessibilityEvent"]
    case_memory_events = [
        event
        for event in memory_events
        if "case_memory_contamination" in event["payload"].get("reconstruction_biases", [])
    ]

    assert inquiry
    assert institutional_events
    assert institutional_trace
    assert witness_events
    assert witness_trace
    assert location_events
    assert location_trace
    assert investigation_events
    assert accessibility_events
    assert investigation_trace
    assert accessibility_trace
    assert all(item["focus_id"] for item in inquiry)
    assert any(item["silencing_pressure"] > 0 for item in institutional_trace)
    assert any(item["suppression_delta"] >= 0 for item in institutional_trace)
    assert all(item["institutional_effect"] for item in institutional_trace)
    assert all(item["strategy_id"] for item in witness_trace)
    assert all(item["strategy_mode"] for item in witness_trace)
    assert any(item["confirmation_risk"] >= 0 for item in witness_trace)
    assert any("accessibility_delta" in item["effects"] for item in witness_trace)
    assert all(item["location_after"]["location_id"] for item in location_trace)
    assert any(item["location_delta"]["contamination"] >= 0 for item in location_trace)
    assert any(item["location_after"]["field_effects"] for item in location_trace)
    assert all(item["state_after"]["progress"] >= 0 for item in investigation_trace)
    assert any(item["relational_feedback"]["conflict_pressure"] > 0 for item in investigation_trace)
    assert all(item["accessibility_after"]["access_status"] in {"available", "restricted", "fragile", "blocked"} for item in accessibility_trace)
    assert any(item["accessibility_delta"] <= 0 for item in accessibility_trace)
    assert any(event["source_layer"] == "inquiry" for event in investigation_events)
    assert any(event["causal_refs"] for event in investigation_events)
    assert any(event["source_layer"] == "inquiry" for event in institutional_events)
    assert any(event["causal_refs"] for event in institutional_events)
    assert any(event["source_layer"] == "inquiry" for event in witness_events)
    assert any(event["causal_refs"] for event in witness_events)
    assert any(event["source_layer"] == "inquiry" for event in location_events)
    assert any(event["causal_refs"] for event in location_events)
    assert any(event["source_layer"] == "inquiry" for event in accessibility_events)
    assert any(event["causal_refs"] for event in accessibility_events)
    assert case_memory_events
    assert any(investigation_event_ids.intersection(event["causal_refs"]) for event in case_memory_events)
    assert any("investigative_fixation" in event["payload"]["reconstruction_biases"] for event in case_memory_events)
    assert any("witness_memory_destabilized" in event["payload"]["reconstruction_biases"] for event in case_memory_events)
    assert all("inquiry_pressure" in item["input_factors"] for item in scheduler)
    assert all("institutional_pressure" in item["input_factors"] for item in scheduler)
    assert all("daily_ecology_pressure" in item["input_factors"] for item in scheduler)
    assert all("attention_pressure" in item["input_factors"] for item in scheduler)
    assert all("opportunity_pressure" in item["input_factors"] for item in scheduler)
    assert all("reversibility_pressure" in item["input_factors"] for item in scheduler)
    assert any(item["input_factors"]["inquiry_pressure"] > 0 for item in scheduler[1:])
    assert any(item["input_factors"]["institutional_pressure"] > 0 for item in scheduler[1:])
    assert any(item["input_factors"]["daily_ecology_pressure"] > 0 for item in scheduler[1:])
    assert any(item["input_factors"]["attention_pressure"] > 0 for item in scheduler[1:])
    assert any(item["input_factors"]["opportunity_pressure"] > 0 for item in scheduler[1:])
    assert any(item["input_factors"]["reversibility_pressure"] > 0 for item in scheduler[1:])
    assert attention
    assert any(item["dominant_focus"] in {"case_fixation", "threat_monitoring", "memory_intrusion"} for item in attention)
    assert opportunity
    assert any(item["cost_type"] in {"evidence_window_loss", "trust_window_loss", "repair_window_loss", "social_exposure_cost"} for item in opportunity)
    assert reversibility
    assert any(item["threshold_state"] in {"recoverable", "narrowing", "threshold_crossed", "symbolic_only"} for item in reversibility)
    assert any(
        key.startswith("inquiry_")
        for item in affordance
        for candidate in item["candidates"]
        for key in candidate["evidence"]
    )
    assert any(
        key.startswith("institutional_")
        for item in affordance
        for candidate in item["candidates"]
        for key in candidate["evidence"]
    )
    assert any(
        key.startswith("witness_strategy_")
        for item in affordance
        for candidate in item["candidates"]
        for key in candidate["evidence"]
    )
    assert any(
        key.startswith("daily_")
        for item in affordance
        for candidate in item["candidates"]
        for key in candidate["evidence"]
    )
    assert any(
        key.startswith("attention_")
        for item in affordance
        for candidate in item["candidates"]
        for key in candidate["evidence"]
    )
