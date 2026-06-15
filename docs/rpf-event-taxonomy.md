# RPF Event Taxonomy and Timeline Specification

## 0. Purpose

This document defines the event taxonomy for RPF.

RPF is event-sourced. The event stream is the authoritative history of the simulation.

Current state is a projection from:

```text
initial_state + seed + ordered_events
```

---

## 1. Event Contract

Every event must include:

```text
Event
- event_id
- simulation_id
- tick
- episode_id
- scene_id
- event_type
- source_layer
- payload
- causal_refs
- deterministic_order
- mutates_causal_state
- creates_irreversibility
- created_at
```

### 1.1 Required Properties

- append-only
- ordered
- replayable
- schema-validated
- source-layer explicit
- causally referenced where possible

### 1.2 Invalid Events

Reject events that:

- mutate derived views directly
- lack required causal references
- create irreversible history without future constraints
- convert labels into operative classifications without uptake evidence
- represent LLM prose as causal fact without validation

---

## 2. Source Layers

Allowed source layers:

```text
material
field_position
habitus
relevance
position
viability
binding
affordance
ritual
communication
observation
normativity
frame
recognition
repair
stabilization
relation
irreversibility
aggregation
projection
llm_rendering
diagnostic
```

---

## 3. Event Categories

```text
1. State Integrity Events
2. Field Events
3. Binding Events
4. Scene Events
5. Micro Signal and Affordance Events
6. RPP Events
7. Relevance Events
8. Positioning Events
9. Ritual Events
10. Communication and Action Events
11. Observation Events
12. Expectation Events
13. Account Pressure Events
14. Normativity Events
15. Frame Definition Events
16. Recognition Events
17. Repair and Escalation Events
18. Stabilization Events
19. Irreversibility Events
20. Aggregation and Projection Events
21. Operative Classification Events
22. Relational Viability Trace Events
23. Relation Sedimentation Events
24. LLM Events
25. Diagnostic Events
26. Timeline Requirements
27. Event Quality Rules
28. Fate Transition Events
29. Memory Reconstruction Events
```

---

## 4. State Integrity Events

### 4.1 SimulationInitializedEvent

Emitted once after scenario validation.

```text
payload:
- initial_state_hash
- scenario_ref
- rpp_library_ref
- seed
```

### 4.2 StateValidationEvent

Emitted when validation warnings or failures must be recorded.

```text
payload:
- severity
- invariant
- message
- affected_refs
```

---

## 5. Field Events

### 5.1 FieldPressureEvent

Represents a field condition becoming active.

```text
payload:
- pressure_type
- affected_processes
- field_source
- intensity
- deadline
- possible_sanctions
- evidence
```

### 5.2 FieldUpdateEvent

Represents causal field change.

```text
payload:
- changed_field_path
- previous_value
- new_value
- reason
- caused_by_events
```

`FieldUpdateEvent` is valid only when `caused_by_events` cites the relation history that sedimented into the field.

For decay of already sedimented field pressure, `caused_by_events` may cite the current `TickStartedEvent`.

It must not be used as a hidden plot shortcut.

### 5.3 EnactedMicroWorldEvent

A relation creates or modifies a local world.

```text
payload:
- micro_world_type
- location_or_object
- participating_processes
- symbolic_meaning
- future_affordance_changes
```

Examples include charged objects, avoided routes, public mask worlds, and memory-saturated shared spaces.

Each run writes `environment_trace.json`.

---

## 6. Binding Events

### 6.1 BindingActivatedEvent

```text
payload:
- binding_id
- binding_type
- affected_processes
- strength
- asymmetry
- exit_cost
- reason
```

### 6.2 BindingDecayedEvent

```text
payload:
- binding_id
- previous_strength
- new_strength
- previous_exit_cost
- new_exit_cost
- strength_delta
- exit_cost_delta
- reason
- caused_by_events
```

### 6.3 BindingUpdatedEvent

Represents a binding becoming tighter, more costly to exit, or otherwise more structurally active.

```text
payload:
- binding_id
- previous_strength
- new_strength
- previous_exit_cost
- new_exit_cost
- strength_delta
- exit_cost_delta
- reason
- caused_by_events
```

Valid sources include field pressure, avoidance/displacement, repair, and prior relation sedimentation.

Binding updates are causal state changes. They are not relationship labels.

### 6.4 LatentRelationEvent

Emitted when relation persists without encounter.

```text
payload:
- affected_processes
- latent_bindings
- non_encounter_reason
- accumulated_pressure
```

Non-encounter is part of the simulation.

---

## 7. Scene Events

### 7.0 LatentTimeEvent

Represents simulated time passing without direct interaction.

```text
payload:
- tick_type: "latent"
- simulated_time_delta
- time_mapping_reason
- affected_processes
- active_bindings
- accumulated_pressures
- latent_relevance_changes
```

### 7.0.1 NoSceneEvent

Represents a tick where no scene crystallizes, with explicit explanation.

```text
payload:
- tick_type
- reason_no_scene
- binding_scores
- field_pressures
- scene_threshold
- strongest_candidate
```

### 7.1 SceneCrystallizationEvent

```text
payload:
- scene_id
- participants
- location
- frame
- declared_activity
- hidden_activities
- present_audience
- imagined_audience
- crystallization_score
- why_here
- why_now
- why_unavoidable
- tick_type: "scene"
```

### 7.2 SceneClosureEvent

```text
payload:
- scene_id
- closure_type
- unresolved_tensions
- carryover_pressures
- next_scene_biases
```

---

## 8. Micro Signal Events

## 8.0 AffordanceSelectionEvent

Emitted before scene crystallization or micro signal emission on non-latent ticks.

```text
payload:
- affordance_id
- signal_type
- frame
- score
- evidence
- tick_type
```

Affordance selection represents situated action availability. It replaces deterministic tick-parity signal generation.

`evidence` may include sedimented field factors such as:

- `sedimented_avoidance_paths`
- `sedimented_charged_objects`
- `sedimented_imagined_audience`
- `memory_saturated_space`

These factors mean prior relation history has changed the field, and the changed field now changes what interaction forms are available.

The selected affordance constrains:

- scene frame
- micro signal type
- source and target positions
- ambiguity
- inferred relational claim

Affordance candidates are also written to `affordance_trace.json`.

### 8.1 MicroSignalEvent

```text
payload:
- tick_type: "micro_interaction" | "scene"
- signal_type
- source_process
- target_process
- scene_context
- raw_observable
- intensity
- ambiguity
- possible_interpretations
```

Micro signals do not have fixed meaning.

### 8.2 ActionSelectionEvent

Represents the action actually selected from a situated affordance.

```text
payload:
- action_id
- action_mode
- signal_type
- source_process
- target_process
- score
- ambiguity
- inhibited_action optional
- substituted_for optional
- relation_claim
- evidence
- viability_evidence_refs
- affordance_id
```

Action mode may be:

- enacted
- inhibited
- substituted
- escalated

When Stage 3 viability authority is enabled, `viability_evidence_refs` must list the pre-response viability events consumed by action selection. These refs may add bounded score adjustments from affordance width, direct response cost, and viability pressure. They must not bypass situated affordance selection or force plot outcomes.

### 8.3 ActionInhibitionEvent

Represents an available action becoming unsayable, unsafe, or practically blocked.

```text
payload:
- action_id
- inhibited_action
- replacement_signal
- evidence
```

### 8.4 ActionSubstitutionEvent

Represents one action form standing in for another.

```text
payload:
- action_id
- substituted_for
- replacement_signal
- evidence
```

### 8.5 ExpressionSelectionEvent

Represents how a selected action becomes observable.

```text
payload:
- expression_id
- expression_mode
- surface_signal
- tone
- gesture
- timing
- intensity
- ambiguity
- relation_claim
- score
- evidence
- viability_evidence_refs
- action_id
- action_mode
- affordance_id
```

Expression selection does not decide the action. It determines the visible, audible, temporal, or bodily form through which the selected action appears.

When Stage 2 viability authority is enabled, `viability_evidence_refs` must list the pre-response viability events consumed by expression selection. These refs may bias expression form within bounded weights; they must not change the selected action or authorize a plot outcome.

### 8.6 OmissionSignalEvent

Used when not doing or not saying something matters.

```text
payload:
- expected_action
- omitted_by
- expected_by
- omission_context
- interpretive_risk
```

### 8.7 DispositionSedimentationEvent

Represents lower-level relational evidence sedimenting into a process-level tendency.

```text
payload:
- process_id
- changed_path
- previous_value
- new_value
- delta
- reason
- caused_by_events
```

Valid changed paths include bounded updates to:

- `checking_tendency`
- `ambiguity_tolerance`
- `risk_suspension_scope`
- `speech_inhibition.*`
- `threat_sensitivity.*`
- `resentment_pressure`

This event must not be treated as a personality primitive.

It records how memory, environment, and recurring RPP evidence have made a future response tendency slightly more or less available.

Decay events use the same event type with reason:

```text
process disposition sediment decays when not reinforced
```

Decay may cite the current `TickStartedEvent`. It must only reduce prior sedimented contribution, not erase scenario baselines.

---

## 9. RPP Events

### 9.1 RPPActivationEvent

```text
payload:
- rpp_id
- activation_score
- eligibility_evidence
- effect
```

`eligibility_evidence` may include `FutureConstraintEvent` ids when prior irreversibility, operative classification, or reconstructed memory raises the likelihood of a pattern recurring.

Future constraints must remain evidence, not direct activation commands. An RPP still needs its ordinary field, signal, recognition, memory, or relation-metric conditions.

### 9.2 RPPDecayEvent

```text
payload:
- rpp_id
- previous_intensity
- new_intensity
- decay_reason
- repair_refs
```

### 9.3 RPPCompositionEvent

```text
payload:
- composed_rpps
- emergent_loop_description
- diagnostic_evidence
```

---

## 10. Relevance Events

### 10.1 RelevanceShiftEvent

```text
payload:
- process_id
- marker
- marker_key
- previous_value
- new_value
- delta
- salience_changes
- threat_marker_changes
- opportunity_marker_changes
- memory_activations
- ignored_background_changes
- reason
- caused_by_events
- evidence_event_types
```

Valid marker keys use the `relevance_field.{process}.{marker}` prefix.

Initial markers include:

- delayed_reply
- recognition_claim
- public_exposure
- being_controlled
- double_bind
- material_cost
- repair_opening
- exit_threat

Relevance shifts are event-sourced attention landscape changes, not hidden motives.

### 10.2 AffordanceChangeEvent

```text
payload:
- process_id
- action
- previous_availability
- new_availability
- reason
```

### 10.3 PositioningEvent

Represents a relation-generated process position becoming more or less operative.

It is not a role, personality trait, motive, social identity, or character function. It records that event history has pushed a process into a position from which some actions, expressions, and recognition outcomes become easier or harder.

```text
payload:
- process_id
- position_type
- position_key
- previous_value
- new_value
- delta
- reason
- caused_by_events
- evidence_event_types
```

Valid position keys use the `position_field.{process}.{position_type}` prefix.

Initial position types:

- claimant
- debtor
- defender
- caretaker
- controlled
- public_performer
- withdrawer
- trapped_party
- repair_partner
- bound_party

Valid sources include:

- `RecognitionEvent`
- `MisrecognitionEvent`
- `RepairEvent`
- `AvoidanceEvent`
- `DisplacementEvent`
- `NormativePressureEvent`
- `FrameDefinitionEvent`
- `RelevanceShiftEvent`
- `RelationSedimentationEvent`
- `RPPCompositionEvent`
- `BindingUpdatedEvent`

Positioning may influence later `ActionSelectionEvent` and `RecognitionEvent` through bounded `position_*` evidence.

It must not directly create scenes, actions, relationship labels, or rendered prose.

Each run writes `position_trace.json`.

---

## 11. Ritual Events

### 11.1 RitualFrameEvent

```text
payload:
- scene_id
- frame
- front_stage_roles
- backstage_knowledge
- face_risks
- permissible_speech
- forbidden_speech
- repair_options
- exit_routes
```

### 11.2 FaceThreatEvent

```text
payload:
- threatened_process
- threat_source
- face_domain
- audience
- severity
- repair_required
```

---

## 12. Communication and Action Events

### 12.1 CommunicationEvent

```text
payload:
- speaker
- addressee
- content_summary
- form
- timing
- directness
- omitted_content
- relation_claim
- candidate_source: "simulator" | "llm_validated" | "scenario"
```

### 12.2 SilenceEvent

```text
payload:
- silent_process
- expected_speech
- duration
- scene_frame
- possible_meanings
```

### 12.3 ActionEvent

```text
payload:
- actor
- action_type
- target
- action_availability_evidence
- face_cost
- recognition_implication
```

---

## 13. Observation Events

### 13.1 ObservationEvent

```text
payload:
- observer
- observed_event
- interpreted_information
- interpreted_utterance
- inferred_intent
- inferred_relation_claim
- self_as_seen_by_other
- confidence
```

### 13.2 MisinterpretationEvent

```text
payload:
- observer
- observed_event
- interpretation
- later_contradicting_evidence optional
- active_rpp_refs
```

Misinterpretation is not a bug. It is often a causal driver.

---

## 14. Expectation Events

### 14.1 ExpectationSedimentationEvent

Represents second-order expectations sedimenting from observed interaction.

It does not reveal private belief. It records relation-specific expectation pressure inferred from observable events.

```text
payload:
- expectation_key
- previous_value
- new_value
- delta
- reason
- caused_by_events
```

Valid expectation keys use:

```text
expectation.{observer}.{target}.{expectation_type}
```

Initial expectation types:

- refusal_expectation
- misrecognition_expectation
- withdrawal_expectation
- public_exposure_expectation
- repair_avoidance_expectation

Valid sources:

- `ObservationEvent`
- `RecognitionEvent`
- `RepairEvent`
- `AvoidanceEvent`
- `DisplacementEvent`
- `RelationSedimentationEvent`

Expectation sedimentation may influence later action and expression selection.

It must not create hidden motives or private thoughts.

Each run writes `expectation_trace.json`.

---

## 15. Account Pressure Events

### 15.1 AccountPressureEvent

Represents derived pressure on a process's viability accounts.

It is not a primitive account bar and not an emotion. It is an event-sourced pressure projection from field, recognition, repair, expectation, and relation-sedimentation history.

```text
payload:
- process_id
- account
- previous_value
- new_value
- delta
- reason
- caused_by_events
```

Initial accounts:

- safety
- dignity
- control
- relation
- meaning
- energy

Valid sources:

- `FieldPressureEvent`
- `RecognitionEvent`
- `RepairEvent`
- `AvoidanceEvent`
- `DisplacementEvent`
- `MisrecognitionEvent`
- `ExpectationSedimentationEvent`
- `RelationSedimentationEvent`

Account pressure may influence later action, expression, and recognition evaluation.

It must not be rendered as a hidden private feeling unless narrative rendering can cite the lower event chain.

Each run writes `account_trace.json`.

---

## 16. Normativity Events

### 16.1 NormativePressureEvent

Represents a derived social-form pressure: claim entitlement, repair obligation, public face obligation, legitimacy contestation, reciprocity obligation, exit justification, mutual obligation, or irreversible precedent.

It is not a morality score and not a hidden value system. It records when observable interaction makes a claim, refusal, role, or repair obligation socially harder to ignore.

```text
payload:
- process_id
- target_process_id
- norm_type
- norm_key
- previous_value
- new_value
- delta
- reason
- caused_by_events
```

Valid sources:

- `FieldPressureEvent`
- `RecognitionEvent`
- `RepairEvent`
- `AvoidanceEvent`
- `DisplacementEvent`
- `MisrecognitionEvent`
- `OperativeClassificationEvent`
- `IrreversibilityEvent`
- `ExpectationSedimentationEvent`
- `AccountPressureEvent`
- `RelationSedimentationEvent`

Normative pressure may influence later action, expression, and recognition evaluation.

It must not decide who is morally correct. It only records which obligations, entitlements, public-face requirements, and legitimacy contests have been made operative by prior events.

Each run writes `normativity_trace.json`.

---

## 17. Frame Definition Events

### 17.1 FrameDefinitionEvent

Represents an event-sourced definition of what kind of interaction is currently becoming operative.

It is not prose scene selection and not private interpretation. It records whether the relation is being defined as debt accounting, repair, avoidance, public performance, care/control, double bind, material accounting, or recognition trial.

```text
payload:
- frame_type
- frame_key
- previous_value
- new_value
- delta
- reason
- caused_by_events
- evidence_event_types
```

Valid frame types:

- debt_accounting
- repair_scene
- avoidance_scene
- public_performance
- care_control
- double_bind
- material_accounting
- recognition_trial

Valid sources:

- `AffordanceSelectionEvent`
- `ExpressionSelectionEvent`
- `RecognitionEvent`
- `NormativePressureEvent`
- `RelationSedimentationEvent`
- `FieldUpdateEvent`
- `RPPCompositionEvent`

Frame definition may influence later affordance, expression, and recognition evaluation.

It must not invent scenes, motives, or plot beats. It only sediments the interaction's operative definition.

Each run writes `frame_trace.json`.

---

## 18. Recognition Events

### 18.1 RecognitionEvent

```text
payload:
- demand_id
- holder
- demanded_from
- result: granted | partial | refused | displaced | postponed | misunderstood | mocked | unspeakable
- evidence
- outcome_scores
- effect_on_process
- effect_on_relation
```

Recognition events must be generated by recognition outcome evaluation, not by a single threshold.

The selected outcome should be auditable from:

- affordance evidence
- RPP or composition evidence
- recognition pressure
- face risk
- repair debt
- speech inhibition
- field or audience pressure

### 18.2 MisrecognitionEvent

```text
payload:
- denied_claim
- imposed_identity
- pain_delegitimized
- responsibility_shifted
- narrative_overwritten
- symbolic_violence
- future_bias
```

---

## 19. Repair and Escalation Events

### 19.1 RepairEvent

```text
payload:
- repair_type
- initiator
- receiver
- explicitness
- recognition_content
- face_safety
- success_level
- remaining_debt
```

### 19.2 EscalationEvent

```text
payload:
- escalation_type
- participating_processes
- triggering_events
- new_face_risks
- possible_irreversibility
```

### 19.3 AvoidanceEvent

```text
payload:
- avoided_content
- avoiding_process
- method
- short_term_effect
- long_term_pressure
```

---

## 20. Stabilization Events

### 20.1 StabilizationEvent

```text
payload:
- pattern
- affected_processes
- previous_stability
- new_stability
- evidence_refs
- derived_label_candidates
```

### 20.2 DestabilizationEvent

```text
payload:
- pattern
- reason
- affected_views
- future_uncertainty
```

---

## 21. Irreversibility Events

### 21.1 IrreversibilityEvent

```text
payload:
- category
- description
- affected_processes
- source_events
- audience_scope
- future_constraints
- lost_alternatives
- reversibility
```

This event must define how the future changed.

---

## 22. Aggregation and Projection Events

### 22.1 AggregationEvent

```text
payload:
- aggregate_name
- aggregate_value
- evidence_refs
- formula_or_rule
- confidence
- uncertainty
```

### 22.2 ProjectionEvent

```text
payload:
- view_type
- target
- generated_view_ref
- evidence_refs
```

These events do not mutate causal state.

---

## 23. Operative Classification Events

### 23.1 OperativeClassificationEvent

```text
payload:
- label
- target
- source
- uptake_type
- audience
- legitimacy
- sanction_power
- future_interpretation_bias
```

### 23.2 DownwardConstraintEvent

```text
payload:
- classification_id
- constrained_layer
- constrained_field
- previous_value
- new_value
- mechanism
```

Allowed mechanisms:

- face risk
- speech inhibition
- relevance trigger
- self-narrative pressure
- audience expectation
- action availability
- micro-signal interpretation

---

## 24. Relational Viability Trace Events

These events are trace-only at first. They expose the lower substrate beneath conflict without mutating causal state.

### 24.1 ConstraintActivationEvent

```text
payload:
- constraint_id
- constraint_type
- source_layer
- affected_processes
- affected_requirements
- intensity
- activation_condition
- duration_policy
- decay_rate
- reversibility
- downstream_effects
- evidence_refs
```

### 24.2 ViabilityRequirementEvent

```text
payload:
- requirement_id
- requirement_type
- holder_process_id
- target_process_id optional
- urgency
- negotiability
- minimum_satisfaction_condition
- failure_cost
- deformation_tendency
- source
- evidence_refs
```

### 24.3 AffordanceWidthEvent

```text
payload:
- tick
- process_id
- width
- narrowing_constraints
- direct_response_cost
- evidence_refs
```

### 24.4 DeformationTraceEvent

```text
payload:
- deformation_id
- source_process_id
- target_process_id
- visible_form
- blocked_requirement_id optional
- deformation_type
- deformation_distance
- ambiguity
- observer_risk
- expected_recognition_failure_modes
- evidence_refs
```

### 24.5 FutureConstraintEvent

```text
payload:
- constraint_id
- constraint_type
- source_layer: irreversibility | classification | memory | relation_sedimentation
- source_ref_id
- affected_processes
- constrained_requirements
- intensity
- persistence
- mechanism
- lost_alternatives
- downstream_effects
- evidence_refs
```

`FutureConstraintEvent` records how prior history now narrows future viability.

It is not a new plot event. It is a derived constraint trace.

Valid sources include:

- irreversibility records
- operative classifications
- reconstructed memories
- relation sedimentation metrics

Every future constraint must cite the event or record that produced it.

### 24.6 DerivedDramaticTensionEvent

```text
payload:
- tick
- tick_type
- dramatic_tension
- source: derived_from_relational_viability_trace
- constraint_count
- requirement_count
- deformation_count
- future_constraint_count
```

These events may be consumed by diagnostics, reports, workbench views, and LLM rendering. They must not authorize plot outcomes.

---

## 25. Relation Sedimentation Events

### 25.1 RelationSedimentationEvent

Represents relation history becoming a slow constraint on later interaction.

It is not a relationship trait and not a derived view. It is a causal sediment produced by event history.

```text
payload:
- metric
- previous_value
- new_value
- delta
- reason
- caused_by_events
- evidence_event_types
- reason_details optional
```

Valid metrics use the `relation_sediment.` prefix, for example:

```text
relation_sediment.recognition_debt
relation_sediment.repair_access_narrowing
relation_sediment.symbolic_accounting_load
relation_sediment.future_lock_load
relation_sediment.shared_fate_load
relation_sediment.public_definition_load
relation_sediment.asymmetry_load
relation_sediment.memory_saturation
relation_sediment.mutual_predictability_load
```

Valid sources include:

- `RecognitionEvent`
- `MisrecognitionEvent`
- `RepairEvent`
- `AvoidanceEvent`
- `DisplacementEvent`
- `RPPCompositionEvent`
- `FutureConstraintEvent`
- `MemoryReconstructionEvent`
- `FieldUpdateEvent`
- `NormativePressureEvent`
- `DispositionSedimentationEvent`

Rules:

- every relation sediment must cite the events that produced it
- relation sediment may affect later aggregation, viability, affordance, recognition, repair, and fate
- relation sediment may produce later `FutureConstraintEvent` only when a sedimented metric crosses an explicit threshold
- relation sediment must remain bounded and gradual
- unreinforced relation sediment decays
- it must not directly create PersonView, RelationshipView, plot beats, or LLM prose

Each run writes `relation_trace.json`.

---

## 26. LLM Events

### 26.1 LLMCandidateEvent

```text
payload:
- prompt_hash
- schema
- candidates
- validation_status
- rejected_items
```

### 26.2 RenderingEvent

```text
payload:
- prompt_hash
- rendered_text
- source_events
- perspective
- validation_status
```

Rendering events never mutate causal state.

---

## 27. Diagnostic Events

### 27.1 InvariantViolationEvent

```text
payload:
- invariant
- severity
- evidence
- action_taken
```

### 27.2 RandomnessTraceEvent

```text
payload:
- random_stream_id
- candidates
- weights
- selected
- seed_state
```

---

## 28. Timeline Requirements

The timeline must support:

- replay
- branching
- causal trace
- aggregation trace
- irreversible history inspection
- scene reconstruction
- LLM rendering comparison

### 28.1 Branching

A branch must record:

```text
parent_simulation_id
parent_tick
parent_event_id
new_seed optional
branch_reason
```

---

## 29. Event Quality Rules

An event is valid if:

- it has a schema
- it has source layer
- it belongs to a typed tick
- it has deterministic order
- it has causal refs where applicable
- it does not smuggle derived state into causal state

An event is invalid if:

- it says "trust decreased" without lower-level evidence
- it says "A became avoidant" as a causal update
- it creates a scene without binding or field pressure
- it makes LLM prose authoritative
- it creates irreversible consequence without future constraint

---

## 30. Fate Transition Events

Fate transition events mark the point where accumulated relation structure becomes an operative constraint on future interaction.

### 30.1 OperativeClassificationEvent

Generated when a relation can no longer treat a label as merely descriptive.

Required payload fields:

- `classification_id`
- `label`
- `target_process_id` or `target_relation_id`
- `source_event_id`
- `uptake`
- `legitimacy`
- `future_interpretation_bias`
- `transition_score`
- `transition_evidence`

### 30.2 IrreversibilityEvent

Generated when a future alternative is structurally lost.

Required payload fields:

- `record_id`
- `category`
- `description`
- `source_event_id`
- `affected_processes`
- `future_constraints`
- `lost_alternatives`
- `reversibility`
- `transition_score`
- `transition_evidence`

Each run writes `fate_transition_trace.json`.

---

## 31. Memory Reconstruction Events

Memory reconstruction events mark the point where a past event is rebuilt as relation history.

### 31.1 MemoryReconstructionEvent

Generated when failed recognition, operative classification, or irreversibility becomes remembered history for a process.

Required payload fields:

- `memory_id`
- `owner_process_id`
- `source_event_id`
- `source_event_type`
- `remembered_as`
- `salience`
- `valence`
- `confidence`
- `reconstruction_biases`
- `evidence`

`evidence` may include:

- `future_constraint_pressure`
- `future_constraint_refs`

These refs mean prior future constraints shaped how salient or confident the reconstructed memory became. They do not mean the future constraint created the memory candidate.

Each run writes `memory_trace.json`.

Memory reconstruction text must not be fed directly into causal logic. Later engines consume semantic pressures derived from memory traces, such as `memory_pressure`, `injury_memory`, `defensive_memory`, and `fate_memory`.

