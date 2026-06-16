# RPF Technical Implementation Plan

## 0. Purpose

This document defines a technical implementation plan for RPF: Relational Process Field.

It is a companion to:

```text
docs/relational-process-field-architecture.md
```

The architecture document defines the ontology:

```text
persons are emergent patterns of relational processes
```

This document defines the implementation strategy:

```text
a typed, event-sourced, layered simulator with derived high-level views and constrained LLM rendering
```

The core technical principle is:

```text
The LLM must not be the simulator.
```

The LLM may render, verbalize, summarize, and propose candidates. It must not directly own causal state transitions.

---

## 1. Technical Position

RPF should be implemented as:

```text
structured simulator
+ layered rule engine
+ probabilistic activation
+ event-sourced timeline
+ derived views
+ constrained LLM renderer
```

It should not be implemented as:

```text
two LLM agents chatting with memory
```

or:

```text
character sheets with personality traits and relationship scores
```

The simulator must preserve the central RPF reversal:

```text
Do not simulate how people form relationships.
Simulate how relational processes stabilize into people.
```

---

## 2. Recommended Stack

### 2.1 Core Language

Use:

```text
Python 3.12+
```

Rationale:

- suitable for research simulation
- strong data analysis ecosystem
- easy batch experiments
- compatible with probabilistic and complex-systems libraries
- convenient for structured model validation
- good fit for future visualization and notebooks

### 2.2 Data Modeling

Use:

```text
Pydantic v2
```

For:

- typed simulation state
- event schemas
- validation of LLM output
- derived view schemas
- scenario configuration

### 2.3 Storage

Start with:

```text
PostgreSQL
```

Use:

```text
SQLAlchemy Core or psycopg
```

behind a small storage interface.

Also support:

```text
JSONL timeline export
```

Rationale:

- canonical cloud persistence
- replayable event logs
- JSONB payload indexing
- transactional append-only writes
- inspectable state snapshots
- simple migration to PostgreSQL later

### 2.4 Configuration

Use:

```text
YAML or TOML
```

For:

- simulation scenarios
- initial field conditions
- RPP libraries
- parameter profiles
- experiment settings

### 2.5 Testing

Use:

```text
pytest
```

The most important tests are not UI tests. They are invariants:

- high-level views cannot directly update causal state
- events can be replayed into the same state
- operative classifications require uptake in the simulated world
- LLM output cannot bypass validators
- irreversible events cannot be silently removed

### 2.6 LLM Integration

Use an LLM only behind structured interfaces.

The LLM may produce:

- scene narration
- dialogue candidates
- gesture candidates
- perspective-limited interpretation
- human-readable summaries

The LLM may not produce:

- direct state mutation
- direct trust/intimacy/personality updates
- authoritative relationship outcomes
- unvalidated causal events

---

## 3. System Components

Recommended project structure:

```text
rpf/
  core/
    ids.py
    state.py
    events.py
    types.py

  layers/
    material.py
    field_position.py
    habitus.py
    relevance.py
    binding.py
    ritual.py
    observation.py
    recognition.py
    stabilization.py
    aggregation.py

  engine/
    simulator.py
    scene_crystallizer.py
    rpp_activator.py
    update_pipeline.py
    irreversibility.py
    scheduler.py

  llm/
    renderer.py
    prompts.py
    schemas.py
    validators.py

  storage/
    postgres_store.py
    timeline.py
    snapshots.py
    migrations.py

  experiments/
    scenarios.py
    batch_runner.py
    metrics.py

  cli/
    main.py
```

This structure keeps the simulator independent from narrative rendering.

---

## 4. Core Data Model

### 4.1 Simulation State

```text
SimulationState
- simulation_id
- clock
- field_state
- process_states
- active_bindings
- active_rpps
- irreversibility_register
- timeline_cursor
- random_seed
```

### 4.2 Field State

```text
FieldState
- material_conditions
- institutional_orders
- spatial_arrangements
- temporal_pressures
- class_structure
- cultural_legitimacy_rules
- audience_network
- sanction_systems
- historical_events
- enacted_micro_worlds
```

### 4.3 Process State

`ProcessState` replaces primitive `Person`.

```text
ProcessState
- process_id
- body_position
- field_positions
- embodied_habitus
- relevance_landscape
- recognition_demands
- speech_constraints
- action_affordances
- active_classifications
- stabilized_patterns
```

### 4.4 Relational Process Pattern

```text
RPP
- id
- name
- eligibility_conditions
- triggering_differences
- relevance_effects
- communicative_forms
- recognition_demands
- relational_effects
- stabilization_effects
- irreversibility_effects
```

### 4.5 Event

All meaningful changes should be represented as events.

```text
Event
- event_id
- simulation_id
- tick
- episode_id
- event_type
- source_layer
- payload
- causal_refs
- created_at
```

---

## 5. Event Sourcing

RPF should use event sourcing.

Do not only save current state.

Save:

```text
initial_state
+ ordered event stream
+ periodic snapshots
+ derived views
```

This is required because RPF is fundamentally historical.

The system must be able to answer:

- How did this label become operative?
- When did this repair pattern stop working?
- Which scene made this future impossible?
- Why does this position now appear avoidant?
- Which earlier misrecognition was retrospectively reclassified?

### 5.1 Event Types

```text
MicroSignalEvent
FieldPressureEvent
BindingEvent
SceneCrystallizationEvent
RPPActivationEvent
RelevanceShiftEvent
RitualFrameEvent
CommunicationEvent
ObservationEvent
RecognitionEvent
RepairEvent
StabilizationEvent
AggregationEvent
OperativeClassificationEvent
IrreversibilityEvent
FieldUpdateEvent
RenderingEvent
```

### 5.2 Snapshot Strategy

Use snapshots for speed, not as the source of truth.

```text
Snapshot
- simulation_id
- tick
- state_hash
- serialized_state
- preceding_event_id
```

The event stream remains authoritative.

---

## 6. Simulation Tick

One simulation tick should not mean "A acts, B responds".

It should mean:

```text
one structured update cycle in which a scene may crystallize, processes may couple, and history may become more constrained
```

### 6.1 Tick Pipeline

```text
1. Load current state
2. Evaluate field pressures
3. Evaluate co-presence bindings
4. Crystallize candidate scene
5. Detect micro signals
6. Activate relevant RPPs
7. Update relevance landscapes
8. Establish ritual frame
9. Generate or select communication events
10. Perform second-order observation
11. Evaluate recognition and misrecognition
12. Apply repair, escalation, avoidance, or displacement
13. Update process patterns
14. Update stabilization
15. Update irreversibility register
16. Recompute derived aggregate views
17. Recompute Person / Relationship / Field views
18. Optionally render with LLM
19. Persist events and snapshot
```

### 6.2 Rule

Each layer should emit explicit events.

No single black-box update function should mutate all state at once.

---

## 7. Layered Update Architecture

The simulator should implement the recursive aggregation model:

```text
Micro Signals
-> Generative Parameters
-> Process Patterns
-> Relational Aggregates
-> Person / Relationship Views
-> Narrative and Social Labels
-> Operative Classifications
-> Field and Interaction Constraints
-> Micro Signals
```

### 7.1 Causal State

These can directly participate in updates:

```text
exit_capacity
speech_inhibition
shame_threshold
threat_sensitivity
face_risk_threshold
relevance_trigger_weight
repair_acceptance_threshold
risk_suspension_scope
recognition_dependency
symbolic_capital_gap
material_dependency_chain
bodily_recovery_access
action_reversibility
active_rpps
irreversibility_register
operative_classifications
```

### 7.2 Derived State

These are projections:

```text
trust_view
intimacy_view
dependency_view
resentment_pressure_view
power_asymmetry_view
repair_capacity_view
conflict_pressure_view
person_view
relationship_view
```

Derived state must not directly cause behavior.

### 7.3 Operative Classification Exception

A high-level label may re-enter the causal system only when it becomes operative.

Examples:

```text
"You are cold."
"You never trust me."
"This is not a real relationship anymore."
"Everyone knows you depend on her."
```

These utterances can update causal structures because they are no longer mere summaries. They are events inside the simulated world.

---

## 8. Rules and Probability

RPF should use a hybrid dynamics model:

```text
rule-based eligibility
+ weighted scoring
+ probabilistic selection
+ deterministic event application
```

### 8.1 Rule-Based Eligibility

Rules decide whether something can happen.

Example:

```text
RPP pursuit_withdrawal is eligible if:
- one position has elevated recognition_dependency
- another position has elevated speech_inhibition or autonomy sensitivity
- a micro signal is interpretable as withdrawal
- prior repair is incomplete
```

### 8.2 Weighted Activation

Scores decide how strongly something is likely to happen.

Example:

```text
activation_score =
  abandonment_relevance_weight
+ prior_withdrawal_count
+ low_exit_capacity_weight
+ current_fatigue_weight
- recent_successful_repair_weight
```

### 8.3 Probabilistic Selection

When several eligible patterns compete, sample among them.

Use seeded randomness for reproducibility.

### 8.4 Deterministic Application

Once an event is selected, applying its effects should be deterministic.

This allows replay.

---

## 9. LLM Boundary

The LLM is a renderer and candidate generator, not the state authority.

### 9.1 LLM Inputs

```text
current_scene
field_constraints
active_rpps
person_views
relationship_view
relevance_landscapes
recognition_conflicts
permissible_actions
forbidden_actions
irreversibility_pressure
perspective_limits
```

### 9.2 LLM Outputs

```text
SceneRendering
- narration
- dialogue_candidates
- gesture_candidates
- omitted_thoughts
- perspective_limited_interpretations
```

### 9.3 Validation

LLM outputs must be validated against schemas.

Reject or repair output if it:

- mutates state directly
- invents unavailable actions
- contradicts field constraints
- assigns personality as a cause
- updates trust, intimacy, resentment, or identity directly
- creates irreversible events without simulator authorization

### 9.4 Consequence Ownership

The simulator owns consequences.

The LLM may propose:

```text
B looks away before answering.
```

The simulator decides whether that becomes:

- meaningless background
- a micro signal
- a relevance shift
- a recognition injury
- an RPP trigger
- an irreversible scene marker

---

## 10. Storage Design

### 10.1 Suggested Tables

```text
simulations
- id
- name
- seed
- created_at
- config

events
- id
- simulation_id
- tick
- episode_id
- event_type
- source_layer
- payload_json
- causal_refs_json
- created_at

snapshots
- id
- simulation_id
- tick
- state_hash
- payload_json
- preceding_event_id
- created_at

episodes
- id
- simulation_id
- tick_start
- tick_end
- scene_frame_json
- summary

derived_views
- id
- simulation_id
- tick
- view_type
- payload_json
- created_at

llm_outputs
- id
- simulation_id
- tick
- episode_id
- prompt_hash
- schema_name
- output_json
- validation_status
- created_at
```

### 10.2 Export Format

Support:

```text
timeline.jsonl
snapshots/*.json
derived_views/*.json
rendered_scenes.md
```

This makes simulations inspectable without requiring a database.

---

## 11. Minimal Viable Simulator

The first implementation should be CLI-first.

### 11.1 Inputs

```text
scenario.yaml
rpp_library.yaml
field.yaml
simulation_config.yaml
```

### 11.2 Command

```text
python -m rpf run scenario.yaml --steps 100 --seed 42
```

### 11.3 Outputs

```text
out/
  timeline.jsonl
  snapshots/
  derived_views.json
  rendered_scenes.md
  metrics.json
```

### 11.4 Minimal Features

The first version should support:

- two emergent process positions
- field state
- co-presence binding
- small RPP library
- scene crystallization
- recognition events
- irreversible event register
- derived Person View
- derived Relationship View
- deterministic replay
- optional LLM rendering

Do not start with:

- full UI
- graph database
- autonomous LLM agents
- open-ended chat interface
- large scenario authoring tool

---

## 12. Later Inspector UI

After the simulator works, build a web inspector.

Recommended stack:

```text
FastAPI backend
React + TypeScript frontend
```

The inspector should show:

- timeline
- active scene
- active RPPs
- field pressures
- current relevance landscapes
- recognition conflicts
- irreversibility register
- Person View projections
- Relationship View projections
- aggregation trace from micro signals to labels
- operative classification feedback loops

The inspector is not merely a UI. It is a scientific instrument for seeing whether the simulation is preserving the ontology.

---

## 13. Technical Invariants

The following invariants should be enforced by tests and runtime validators.

### 13.1 No Direct High-Level Causation

Invalid:

```text
trust_view -= 0.2
personality = "avoidant"
```

Valid:

```text
risk_suspension_scope decreases
checking_frequency increases
ambiguity_tolerance decreases
-> trust_view is recomputed
```

### 13.2 Person View Is Derived

Invalid:

```text
PersonView drives action selection directly.
```

Valid:

```text
PersonView is regenerated from process state, RPP history, and operative classifications.
```

### 13.3 Labels Need Uptake

Invalid:

```text
The simulator computes "cold", so speech inhibition increases.
```

Valid:

```text
The label "cold" is spoken, believed, repeated, or socially recorded.
It becomes an OperativeClassificationEvent.
Then it may constrain future action.
```

### 13.4 Irreversibility Is Explicit

Invalid:

```text
A major betrayal silently changes future behavior.
```

Valid:

```text
IrreversibilityEvent records the betrayal, audience, uptake, future constraints, and lost alternatives.
```

### 13.5 Replay Must Be Possible

Given:

```text
initial_state + seed + event stream
```

the simulator must reconstruct the same causal state.

---

## 14. Why Not Use Existing Agent Frameworks as Core

Do not make LangGraph, AutoGen, CrewAI, or similar LLM-agent frameworks the core ontology.

They typically assume:

```text
agent -> message -> response
```

RPF assumes:

```text
field -> process -> coupling -> scene -> observation -> recognition -> stabilization -> person
```

Agent frameworks may be useful around the edges:

- orchestration
- tool calling
- rendering experiments
- prompt pipelines

They should not define the causal model.

---

## 15. Why Not Start With a Graph Database

RPF contains many relational structures, but a graph database is not necessary at the beginning.

Start with:

```text
PostgreSQL + JSONB payloads + event stream
```

Move to graph storage only if the system later needs:

- large multi-person social networks
- multi-hop field queries
- complex institutional relation traversal
- large-scale historical dependency analysis

For the initial two-position simulator, a graph database would add more complexity than value.
See `docs/rpf-postgresql-persistence-plan.md` for the persistence schema and migration path.

---

## 16. Implementation Phases

### Phase 1: Causal Kernel

- define Pydantic models
- implement event stream
- implement snapshots
- implement RPP eligibility and activation
- implement deterministic replay
- implement derived views

### Phase 2: Scene Engine

- implement co-presence binding
- implement scene crystallization
- implement micro signal generation
- implement relevance shift
- implement ritual frame

### Phase 3: Recognition and Irreversibility

- implement recognition demand evaluation
- implement misrecognition events
- implement repair and escalation
- implement irreversibility register
- implement label uptake and operative classification

### Phase 4: LLM Rendering

- implement structured prompts
- implement schema validation
- implement candidate rendering
- implement narration from simulator state
- prevent LLM state mutation

### Phase 5: Experimentation and Inspector

- implement metrics
- implement batch runner
- implement timeline viewer
- implement aggregation trace viewer
- implement debugging dashboard

---

## 17. Summary

The recommended technical architecture is:

```text
Python typed simulator
+ event-sourced timeline
+ layered update pipeline
+ rule/probability hybrid dynamics
+ derived-only high-level views
+ explicit irreversibility
+ constrained LLM renderer
+ later web inspector
```

The implementation must protect the ontology:

```text
Person is an emergent view.
Relationship is an emergent view.
Trust, intimacy, resentment, and personality are derived aggregates.
Labels become causal only when operative in the simulated world.
The LLM renders consequences but does not own them.
```


