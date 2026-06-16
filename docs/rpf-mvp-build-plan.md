# RPF MVP Build Plan

## 0. Purpose

This document defines the first executable implementation slice for RPF.

The goal of the MVP is not to build the full simulator.

The goal is to prove the core architecture:

```text
lower-level field/process/event dynamics
-> recurring RPP activation
-> derived PersonView and RelationshipView
-> operative label feedback
-> irreversible history
```

The MVP must run without an LLM.

LLM rendering may be added only after the deterministic simulator works.

---

## 1. MVP Acceptance Target

The MVP is complete when this command works:

```text
python -m rpf run examples/shared_apartment_unresolved_sacrifice.yaml --steps 30 --seed 42
```

and produces:

```text
out/shared_apartment_unresolved_sacrifice/
  timeline.jsonl
  snapshots/
  derived_views.json
  aggregation_traces.json
  irreversibility_report.json
  metrics.json
```

The run must demonstrate:

```text
1. two ProcessState objects, not primitive Person agents
2. at least two active CoPresenceBindings
3. at least three RPP activations with evidence
4. at least one derived PersonView label
5. at least one derived RelationshipView phase label
6. at least one OperativeClassificationEvent
7. at least one IrreversibilityEvent
8. deterministic replay
9. no direct mutation of derived views
10. no LLM dependency
```

---

## 2. MVP Scope

### 2.1 In Scope

Implement:

- typed state models
- event stream
- deterministic seeded runtime
- simple YAML scenario loader
- tick pipeline
- scene crystallization
- RPP activation
- three RPPs
- recognition evaluation
- repair avoidance
- stabilization
- irreversibility register
- aggregation and projection
- metrics output
- replay test

### 2.2 Out of Scope

Do not implement yet:

- web UI
- graph database
- multi-person social networks
- full LLM rendering
- open-ended chat
- all RPPs
- advanced probabilistic inference
- complex calendar simulation
- long-term scenario editor

---

## 3. Recommended Initial File Tree

```text
rpf/
  __init__.py
  cli/
    __init__.py
    main.py
  core/
    __init__.py
    ids.py
    models.py
    events.py
    views.py
  engine/
    __init__.py
    simulator.py
    pipeline.py
    scene.py
    rpp.py
    recognition.py
    irreversibility.py
    aggregation.py
    metrics.py
  storage/
    __init__.py
    timeline.py
    snapshots.py
  scenarios/
    __init__.py
    loader.py
  rpps/
    __init__.py
    base.py
    pursuit_withdrawal.py
    repair_avoidance.py
    contribution_debt_loop.py

examples/
  shared_apartment_unresolved_sacrifice.yaml

tests/
  test_replay.py
  test_no_direct_derived_mutation.py
  test_rpp_activation.py
  test_operative_classification.py
  test_irreversibility.py
```

---

## 4. MVP Data Model Subset

Implement only the fields needed for the first scenario.

### 4.1 SimulationState

```python
SimulationState
- simulation_id: str
- tick: int
- seed: int
- field_state: FieldState
- processes: dict[str, ProcessState]
- bindings: list[CoPresenceBinding]
- active_rpps: list[ActiveRPP]
- irreversibility_register: IrreversibilityRegister
```

### 4.2 FieldState

```python
FieldState
- material_pressures: dict[str, float]
- spatial_constraints: dict[str, float]
- audience_pressure: dict[str, float]
- enacted_micro_worlds: list[str]
```

### 4.3 ProcessState

```python
ProcessState
- process_id: str
- display_name: str
- fatigue: float
- speech_inhibition: dict[str, float]
- threat_sensitivity: dict[str, float]
- relevance_triggers: dict[str, float]
- recognition_demands: list[RecognitionDemand]
- active_classifications: list[OperativeClassification]
- stabilized_patterns: dict[str, float]
```

### 4.4 CoPresenceBinding

```python
CoPresenceBinding
- binding_id: str
- binding_type: str
- process_ids: list[str]
- strength: float
- exit_cost: dict[str, float]
```

### 4.5 Event

```python
Event
- event_id: str
- tick: int
- event_type: str
- source_layer: str
- payload: dict
- causal_refs: list[str]
- deterministic_order: int
```

### 4.6 Derived Views

```python
PersonView
- process_id
- apparent_labels
- stabilized_response_patterns
- unavailable_actions
- evidence_refs

RelationshipView
- phase_label
- active_bindings
- recurring_rpps
- recognition_conflicts
- repair_patterns
- shared_irreversibles
- evidence_refs
```

---

## 5. MVP RPP Set

Implement exactly three RPPs first.

### 5.1 pursuit_withdrawal

Purpose:

```text
prove that "needy" and "avoidant" can emerge from a recurring loop
```

Activation inputs:

- delayed reply or silence
- abandonment relevance
- autonomy threat
- low exit capacity
- unresolved recognition demand

Effects:

- increase checking tendency
- increase speech inhibition in other process
- strengthen pursuit/withdrawal stabilization
- may generate labels "demanding" or "distant" as derived candidates

### 5.2 repair_avoidance

Purpose:

```text
prove that relation can continue without resolution
```

Activation inputs:

- injury reference
- high apology inhibition
- high face risk
- practical repair option available

Effects:

- reduce immediate conflict pressure
- increase repair debt
- preserve unresolved recognition demand
- raise future resentment pressure

### 5.3 contribution_debt_loop

Purpose:

```text
prove that material history can become moral relation structure
```

Activation inputs:

- historical sacrifice
- low acknowledgment
- repeated practical dependence
- recognition demand to admit what happened

Effects:

- increase resentment pressure
- increase obligation pressure
- may create irreversible record if explicitly named
- may create operative label if spoken

---

## 6. MVP Tick Pipeline

Implement three tick types:

```text
latent
micro_interaction
scene
```

Each tick must record:

```text
tick_type
simulated_time_delta
time_mapping_reason
```

Implement this exact order for a full scene tick:

```text
1. evaluate_field_pressure
2. evaluate_bindings
3. crystallize_scene
4. generate_micro_signals
5. activate_rpps
6. evaluate_recognition
7. apply_rpp_effects
8. evaluate_operative_classification
9. evaluate_irreversibility
10. aggregate_views
11. persist_events
12. maybe_snapshot
```

Each step must return:

```python
StepResult
- events: list[Event]
- state_delta: StateDelta
- diagnostics: dict
```

State deltas are applied by the simulator, not by random step functions mutating global state.

For MVP, it is acceptable to implement latent and micro-interaction ticks as reduced pipelines:

```text
latent:
  field pressure -> binding pressure -> latent relation event -> aggregation

micro_interaction:
  micro signal -> observation -> optional RPP activation -> aggregation
```

---

## 7. MVP Scenario

Use one scenario:

```text
shared_apartment_unresolved_sacrifice
```

### 7.1 Scenario Premise

Two process positions share an apartment.

One previously absorbed a major rent cost.

The other treats it as temporary help, not a sacrifice that changed the relation.

They remain bound by lease, space, and unresolved recognition.

### 7.2 Required Initial Conditions

```yaml
processes:
  p1:
    display_name: A
    fatigue: 0.7
    speech_inhibition:
      direct_need: 0.7
      anger: 0.6
    threat_sensitivity:
      being_used: 0.8
      being_ignored: 0.7
    relevance_triggers:
      unacknowledged_help: 0.9
      delayed_reply: 0.6

  p2:
    display_name: B
    fatigue: 0.5
    speech_inhibition:
      apology: 0.8
      dependency_admission: 0.7
    threat_sensitivity:
      being_controlled: 0.8
    relevance_triggers:
      repeated_questions: 0.8

bindings:
  - binding_id: lease
    binding_type: material
    process_ids: [p1, p2]
    strength: 0.9
    exit_cost:
      p1: 0.8
      p2: 0.6

  - binding_id: unrecognized_contribution
    binding_type: recognition
    process_ids: [p1, p2]
    strength: 0.75
    exit_cost:
      p1: 0.7
      p2: 0.4
```

---

## 8. Event Requirements

The MVP must emit at least:

```text
SimulationInitializedEvent
FieldPressureEvent
BindingActivatedEvent
SceneCrystallizationEvent
MicroSignalEvent
RPPActivationEvent
RecognitionEvent
RepairEvent or AvoidanceEvent
StabilizationEvent
AggregationEvent
ProjectionEvent
OperativeClassificationEvent
IrreversibilityEvent
```

Not every tick needs every event.

Across the 30-step run, all must appear.

---

## 9. Aggregation Requirements

Implement these derived views:

```text
TrustView minimal
ResentmentPressureView minimal
RepairCapacityView minimal
PersonView minimal
RelationshipView minimal
```

### 9.1 Minimal TrustView

Inputs:

- checking tendency
- ambiguity tolerance
- repair debt
- risk suspension scope

### 9.2 Minimal ResentmentPressureView

Inputs:

- unrecognized sacrifice count
- repair avoidance count
- denied recognition count

### 9.3 Minimal PersonView

Derived labels:

- "careful"
- "demanding"
- "distant"
- "withholding"

Each label must include evidence refs.

### 9.4 Minimal RelationshipView

Phase labels:

- fragile
- repair-avoidant
- cold-war
- locked-in

Each phase must include evidence refs.

---

## 10. Operative Classification MVP

Implement one path:

```text
derived label candidate
-> spoken in scene
-> OperativeClassificationEvent
-> DownwardConstraintEvent
```

Example:

```text
"You always make it sound like I owe you."
```

Effects:

- raises p1 speech inhibition around direct need
- raises p2 threat sensitivity around being controlled
- increases future eligibility of repair_avoidance

This proves high-level labels can feed back only through uptake.

---

## 11. Irreversibility MVP

Implement one irreversible path:

```text
unrecognized sacrifice is explicitly named during conflict
-> relation cannot return to pre-naming state
```

Record:

```text
IrreversibilityEvent
- category: spoken_irreversible
- source_events
- affected_processes
- future_constraints
- lost_alternatives
- reversibility: partial
```

Future constraint example:

```text
future practical help is more likely to be interpreted through debt
```

---

## 12. Persistence MVP

Use files first.

```text
timeline.jsonl
snapshots/tick_000.json
snapshots/tick_005.json
derived_views.json
aggregation_traces.json
metrics.json
```

PostgreSQL is the target persistence backend after the file-based MVP. File export remains supported for inspection and sharing.

The event stream is authoritative.

---

## 13. CLI MVP

Required commands:

```text
python -m rpf run examples/shared_apartment_unresolved_sacrifice.yaml --steps 30 --seed 42
python -m rpf replay out/shared_apartment_unresolved_sacrifice/timeline.jsonl
python -m rpf inspect out/shared_apartment_unresolved_sacrifice
```

`inspect` may initially print a text summary.

---

## 14. Tests Required Before MVP Is Accepted

### 14.1 Replay Determinism

```text
initial_state + seed + event stream -> same final state hash
```

### 14.2 No Direct Derived Mutation

Attempting to mutate PersonView or RelationshipView as causal state must fail.

### 14.3 RPP Activation Evidence

Every RPPActivationEvent must include:

- triggering events
- eligibility evidence
- activation score

### 14.4 Operative Classification Requires Uptake

A derived label alone must not affect state.

Only an OperativeClassificationEvent can produce downward constraint.

### 14.5 Irreversibility Requires Future Constraint

Every IrreversibilityEvent must include future constraints.

---

## 15. Milestones

### Milestone 1: Skeleton

Deliver:

- package structure
- Pydantic models
- CLI stub
- scenario loader
- event writer

Acceptance:

```text
python -m rpf run ... --steps 1
```

emits initialization and one tick event.

### Milestone 2: Runtime

Deliver:

- tick pipeline
- field pressure
- binding evaluation
- scene crystallization
- micro signal generation

Acceptance:

- timeline shows scene reasons
- no scene appears without binding or pressure

### Milestone 3: RPP Dynamics

Deliver:

- three MVP RPPs
- activation scoring
- RPP effects
- stabilization events

Acceptance:

- 30-step run activates all three RPPs at least once

### Milestone 4: Aggregation and Views

Deliver:

- TrustView
- ResentmentPressureView
- RepairCapacityView
- PersonView
- RelationshipView
- aggregation traces

Acceptance:

- labels include evidence refs
- views are not causal inputs

### Milestone 5: Feedback and Irreversibility

Deliver:

- OperativeClassificationEvent
- DownwardConstraintEvent
- IrreversibilityEvent
- future constraints

Acceptance:

- label feedback occurs only after uptake
- irreversible event changes future eligibility or interpretation

### Milestone 6: Replay and Validation

Deliver:

- replay command
- final state hash
- metrics
- tests

Acceptance:

- all required tests pass
- LLM is not required

---

## 16. MVP Success Criteria

The MVP succeeds if a reviewer can inspect the output and answer:

```text
Why did these positions keep meeting?
Which lower-level signals activated which RPPs?
How did a person-like label emerge?
When did a label become operative?
What irreversible event changed future scenes?
Can the run be replayed exactly?
Did the simulator work without LLM causality?
```

The MVP fails if:

- personality labels drive behavior
- trust or relationship state is directly updated
- scenes occur for plot convenience
- LLM is needed to explain causality
- event history cannot justify derived views
- replay diverges

