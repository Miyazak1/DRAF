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
binding
affordance
ritual
communication
observation
recognition
repair
stabilization
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
5. Affordance Events
6. Micro Signal Events
7. RPP Events
8. Relevance Events
9. Ritual Events
10. Communication and Action Events
11. Observation Events
12. Recognition Events
13. Repair and Escalation Events
14. Stabilization Events
15. Irreversibility Events
16. Aggregation and Projection Events
17. Operative Classification Events
18. LLM Events
19. Diagnostic Events
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
- decay_reason
```

### 6.3 LatentRelationEvent

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
- affordance_id
```

Action mode may be:

- enacted
- inhibited
- substituted
- escalated

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
- action_id
- action_mode
- affordance_id
```

Expression selection does not decide the action. It determines the visible, audible, temporal, or bodily form through which the selected action appears.

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

---

## 9. RPP Events

### 9.1 RPPActivationEvent

```text
payload:
- rpp_id
- participating_processes
- activation_score
- triggering_events
- eligibility_evidence
- contraindications_checked
- selected_phase
```

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
- salience_changes
- threat_marker_changes
- opportunity_marker_changes
- memory_activations
- ignored_background_changes
- caused_by_events
```

### 10.2 AffordanceChangeEvent

```text
payload:
- process_id
- action
- previous_availability
- new_availability
- reason
```

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

## 14. Recognition Events

### 14.1 RecognitionEvent

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

### 14.2 MisrecognitionEvent

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

## 15. Repair and Escalation Events

### 15.1 RepairEvent

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

### 15.2 EscalationEvent

```text
payload:
- escalation_type
- participating_processes
- triggering_events
- new_face_risks
- possible_irreversibility
```

### 15.3 AvoidanceEvent

```text
payload:
- avoided_content
- avoiding_process
- method
- short_term_effect
- long_term_pressure
```

---

## 16. Stabilization Events

### 16.1 StabilizationEvent

```text
payload:
- pattern
- affected_processes
- previous_stability
- new_stability
- evidence_refs
- derived_label_candidates
```

### 16.2 DestabilizationEvent

```text
payload:
- pattern
- reason
- affected_views
- future_uncertainty
```

---

## 17. Irreversibility Events

### 17.1 IrreversibilityEvent

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

## 18. Aggregation and Projection Events

### 18.1 AggregationEvent

```text
payload:
- aggregate_name
- aggregate_value
- evidence_refs
- formula_or_rule
- confidence
- uncertainty
```

### 18.2 ProjectionEvent

```text
payload:
- view_type
- target
- generated_view_ref
- evidence_refs
```

These events do not mutate causal state.

---

## 19. Operative Classification Events

### 19.1 OperativeClassificationEvent

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

### 19.2 DownwardConstraintEvent

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

## 20. LLM Events

### 20.1 LLMCandidateEvent

```text
payload:
- prompt_hash
- schema
- candidates
- validation_status
- rejected_items
```

### 20.2 RenderingEvent

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

## 21. Diagnostic Events

### 21.1 InvariantViolationEvent

```text
payload:
- invariant
- severity
- evidence
- action_taken
```

### 21.2 RandomnessTraceEvent

```text
payload:
- random_stream_id
- candidates
- weights
- selected
- seed_state
```

---

## 22. Timeline Requirements

The timeline must support:

- replay
- branching
- causal trace
- aggregation trace
- irreversible history inspection
- scene reconstruction
- LLM rendering comparison

### 22.1 Branching

A branch must record:

```text
parent_simulation_id
parent_tick
parent_event_id
new_seed optional
branch_reason
```

---

## 23. Event Quality Rules

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

## 24. Fate Transition Events

Fate transition events mark the point where accumulated relation structure becomes an operative constraint on future interaction.

### 24.1 OperativeClassificationEvent

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

### 24.2 IrreversibilityEvent

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

## 25. Memory Reconstruction Events

Memory reconstruction events mark the point where a past event is rebuilt as relation history.

### 25.1 MemoryReconstructionEvent

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

Each run writes `memory_trace.json`.

Memory reconstruction text must not be fed directly into causal logic. Later engines consume semantic pressures derived from memory traces, such as `memory_pressure`, `injury_memory`, `defensive_memory`, and `fate_memory`.

