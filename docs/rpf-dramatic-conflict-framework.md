# RPF Dramatic Conflict Framework

## 0. Purpose

This document extends RPF from a relational process simulator into a general dramatic conflict framework.

It should be read as a derived layer over:

```text
rpf-relational-viability-process-framework.md
```

The deeper substrate is constrained relational viability. Dramatic conflict is the visible form this substrate may take when viability requirements are blocked, deformed, observed, misrecognized, stabilized, or made irreversible.

It preserves the core RPF ontology:

```text
persons are emergent views of relational processes
```

and adds a more general conflict kernel:

```text
dramatic conflict emerges when a constraint field blocks, distorts, or makes incompatible a capacity that must still be exercised.
```

This document is executable in the sense that it defines:

- new implementable concepts
- event additions
- runtime stages
- scenario authoring fields
- evaluation rules
- a first concrete conflict mode to implement

The goal is not to list every possible story type. The goal is to define a small set of primitives from which many dramatic conflict forms can be generated, inspected, replayed, and rendered.

This framework must not become a hidden plot engine. Its first responsibility is to make conflict evidence visible. Only after the evidence chain is stable should conflict analysis gain limited causal authority over action, expression, recognition, and irreversibility.

The practical product may look like a dramatic conflict generator.

The bottom layer is not that.

The bottom layer is:

```text
field constraint
-> viability requirement
-> affordance narrowing
-> adaptive response or deformation
-> observation
-> recognition or misrecognition
-> memory reconstruction
-> future constraint
-> field / process / relation sedimentation
-> later constraint activation
```

Drama is the visible upper-layer pattern that appears when this chain becomes observable, repeated, misrecognized, stabilized, or irreversible.

This document must therefore be read as an upper-layer diagnostic and rendering framework.

It must not be used as the project bottom layer.

The lower simulator should first answer:

```text
what relation-process residue did prior events sediment?
what future actions became more or less available?
what later constraints did this sediment create?
```

Only after those questions are answered may the system describe the result as conflict.

---

## 1. Core Position

RPF already reverses the ordinary person-first model:

```text
not: Person -> Interaction -> Relationship
but: Field -> Process -> Coupling -> Scene -> Recognition -> Stabilization -> Person
```

The dramatic conflict framework adds one higher-level unifier over the relational viability substrate:

```text
Conflict = constrained actionability under relational, material, historical, and symbolic pressure.
```

This makes interpersonal conflict and natural/material conflict part of the same architecture.

The central object is therefore not a character goal, a dramatic beat, or a relationship trait. The central object is a viability requirement that becomes difficult to exercise under a field configuration.

Examples:

```text
I want to speak, but speech would destroy the scene.
I want to leave, but leaving would make past sacrifice meaningless.
I want to save both people, but time allows only one rescue.
I want to recognize you, but recognition would damage my public position.
I want to survive, but the body, weather, debt, or institution narrows action space.
```

In every case, the simulator should ask:

```text
Which capacity is blocked?
By which constraint?
Who bears the cost?
How does the blockage become expressed, observed, misrecognized, stabilized, and remembered?
```

---

## 2. Architectural Thesis

The unified RPF conflict architecture is:

```text
Constraint Field
-> Blocked Capacity
-> Action / Expression Deformation
-> Observation and Interpretation
-> Recognition / Misrecognition
-> Repair / Escalation / Avoidance
-> Stabilization
-> Irreversibility
-> Derived Person and Relationship Views
```

This is not a replacement for the existing RPF pipeline. It is a compression layer that explains how the existing components fit together.

Existing RPF terms map into this framework:

```text
FieldPressureEvent
-> constraint becomes active

AffordanceSelectionEvent
-> some action becomes available

ActionInhibitionEvent
-> some action becomes blocked

ExpressionSelectionEvent
-> blocked action appears in distorted form

ObservationEvent
-> distortion is interpreted by another position

RecognitionEvent / MisrecognitionEvent
-> the claim is granted, refused, displaced, postponed, or misunderstood

IrreversibilityEvent
-> the future is changed by the blocked capacity and its handling
```

---

## 3. Primitive Concepts

### 3.1 Constraint Field

A `ConstraintField` is the current set of forces that narrow, redirect, delay, or reshape possible action.

It may contain:

```text
ConstraintField
- interpersonal_constraints
- institutional_constraints
- material_constraints
- bodily_constraints
- temporal_constraints
- spatial_constraints
- historical_constraints
- symbolic_constraints
- informational_constraints
```

Constraint fields are not just obstacles. They define what an action can be.

Example:

```text
The same apology is materially possible in private,
face-threatening in public,
institutionally dangerous at work,
and bodily inaccessible under exhaustion.
```

### 3.2 Capacity

A `Capacity` is something a process position may need to exercise in order to remain viable, recognizable, related, or alive.

Initial capacity types:

```text
Capacity
- action
- expression
- recognition
- refusal
- repair
- exit
- care
- survival
- memory_integration
- identity_continuity
- role_performance
- truth_disclosure
- secrecy_maintenance
```

Capacities must not be modeled as goals owned by a primitive person.

They are process-level requirements that become active under a field configuration.

This is the most important anti-regression rule in the framework:

```text
wrong: A wants recognition.
better: a relational process requires recognition to remain viable, but the field makes direct recognition costly or impossible.
```

A capacity is valid only when it can cite at least one of the following sources:

```text
- an active binding that requires continuation, exit, repair, care, secrecy, role performance, or recognition.
- a field pressure that makes survival, resource access, timing, space, or bodily viability unstable.
- an active RPP that requires a response pattern to remain coherent.
- an irreversibility record that has narrowed future alternatives.
- a memory pressure that makes continuation impossible without integration, repression, or deformation.
- an operative classification that now constrains what can be said, done, denied, or repaired.
```

If a capacity cannot cite such a source, it is probably a disguised desire label and should not enter the conflict kernel.

### 3.3 Blocked Capacity

A `BlockedCapacity` records that a capacity has become impossible, dangerous, costly, contradictory, or unavailable.

```text
BlockedCapacity
- capacity_id
- capacity_type
- holder_process_id
- target_process_id optional
- blockage_type
- blocking_constraints
- intensity
- reversibility
- urgency
- evidence_refs
```

Allowed blockage types:

```text
physically_impossible
materially_unavailable
socially_unsayable
face_threatening
identity_incoherent
relation_damaging
institutionally_sanctioned
temporally_excluded
memory_incompatible
symbolically_forbidden
morally_contradictory
```

A blockage is valid only if it names both:

```text
1. what capacity is demanded.
2. which constraint makes direct exercise impossible, dangerous, costly, or incoherent.
```

Blocked capacity without evidence is not conflict. It is narration.

### 3.4 Deformation

When a needed capacity cannot appear directly, it often appears in deformed form.

```text
Deformation
- direct_speech -> joke
- apology -> practical help
- need -> accusation
- refusal -> delay
- care -> control
- desire -> irritation
- fear -> politeness
- exit -> emotional withdrawal
- recognition claim -> public performance
- confession -> object handling or silence
```

This should be represented by existing `ActionSubstitutionEvent`, `ActionInhibitionEvent`, and `ExpressionSelectionEvent`, with additional fields tying them back to a `BlockedCapacity`.

### 3.5 Dramatic Contradiction

A `DramaticContradiction` occurs when two required capacities cannot be exercised together.

```text
DramaticContradiction
- contradiction_id
- capacity_a
- capacity_b
- incompatibility_type
- affected_processes
- field_conditions
- current_resolution_strategy
- likely_failure_modes
```

Common incompatibility types:

```text
recognition_vs_face
care_vs_autonomy
truth_vs_relation
survival_vs_loyalty
exit_vs_debt
repair_vs_identity
public_role_vs_private_need
memory_vs_continuation
secrecy_vs_intimacy
fairness_vs_attachment
```

---

## 4. Unified Conflict Pipeline

The runtime should add a conflict analysis stage that runs after field pressure and before final action/expression selection.

### 4.1 Pipeline Placement

Recommended tick pipeline:

```text
1. Load and validate state
2. Evaluate field pressures
3. Build constraint field
4. Evaluate co-presence bindings
5. Evaluate active capacities
6. Detect blocked capacities
7. Detect dramatic contradictions
8. Select situated affordance
9. Select action / inhibition / substitution
10. Select expression
11. Crystallize or update scene
12. Emit micro signal
13. Activate RPPs
14. Observation and interpretation
15. Recognition / misrecognition
16. Repair / escalation / avoidance
17. Stabilization
18. Irreversibility
19. Aggregation and projection
20. Persist
```

The conflict stages do not replace RPPs.

They provide a higher-level reason why an RPP becomes eligible, intense, suppressed, or transformed.

However, this authority must be staged. The conflict subsystem should begin as a diagnostic layer. It may explain existing selections before it is allowed to bias future selections.

```text
Stage 0: no causal authority.
         emit traces only.

Stage 1: recognition authority.
         recognition evaluation may cite blocked capacity, viability, deformation, and contradiction evidence.
         this authority is bounded to score adjustments and evidence refs.

Stage 2: expression authority.
         expression selection may prefer direct, inhibited, substituted, or deformed forms using viability/deformation pressure.
         this authority is bounded to expression scoring and evidence refs; it cannot change the selected action.

Stage 3: action authority.
         action selection may consider blocked capacities, affordance width, and direct response cost.
         this authority is narrower than expression authority and cannot create actions outside the affordance-bounded candidate set.

Stage 4: scheduler authority.
         tick type and scene crystallization may consider accumulated viability/conflict pressure.
         this authority is temporal rhythm bias only; it cannot force plot-shaped scenes.
```

No implementation should skip Stage 0.

### 4.2 Conflict Analysis Outputs

Each nontrivial tick should be able to write:

```text
constraint_trace.json
capacity_trace.json
conflict_trace.json
```

These files should explain:

- which constraints were active
- which capacities were demanded
- which capacities were blocked
- which contradictions were active
- which selected action or expression deformed the blocked capacity
- which later event consumed the conflict evidence

If a conflict trace cannot reconstruct this chain, the conflict should be treated as unproven:

```text
constraint -> capacity demand -> blockage -> deformation or failed exercise -> observation -> recognition / misrecognition -> stabilization or irreversibility.
```

---

## 5. Event Additions

The current event taxonomy can support this framework with a few additions.

### 5.1 ConstraintFieldEvent

Emitted when the runtime constructs the current constraint field.

```text
payload:
- constraint_field_id
- tick_type
- interpersonal_constraints
- institutional_constraints
- material_constraints
- bodily_constraints
- temporal_constraints
- spatial_constraints
- historical_constraints
- symbolic_constraints
- informational_constraints
- source_events
- dominant_constraints
```

### 5.2 CapacityDemandEvent

Emitted when a capacity becomes active enough to matter.

```text
payload:
- capacity_id
- capacity_type
- holder_process_id
- target_process_id optional
- demand_source
- urgency
- viability_requirement
- evidence
```

### 5.3 BlockedCapacityEvent

Emitted when an active capacity is blocked.

```text
payload:
- capacity_id
- capacity_type
- holder_process_id
- target_process_id optional
- blockage_type
- blocking_constraints
- intensity
- reversibility
- urgency
- evidence
```

### 5.4 DramaticContradictionEvent

Emitted when two or more active capacities are incompatible under the current field.

```text
payload:
- contradiction_id
- capacities
- incompatibility_type
- affected_processes
- constraint_field_id
- available_resolution_strategies
- selected_resolution_strategy optional
- failure_modes
- evidence
```

### 5.5 DeformationEvent

Emitted when a blocked capacity appears indirectly through action, expression, omission, or substitution.

```text
payload:
- blocked_capacity_id
- deformation_type
- visible_form
- hidden_capacity
- ambiguity
- observer_risk
- action_event_ref optional
- expression_event_ref optional
- omission_event_ref optional
- evidence
```

These events should use `source_layer` values:

```text
constraint
capacity
conflict
deformation
```

The event taxonomy should add these source layers when implemented.

---

## 6. Data Model Additions

Add the following model group under `rpf/core/models.py` or a future `rpf/core/conflict.py`.

### 6.1 Constraint

```python
class Constraint(BaseModel):
    constraint_id: str
    constraint_type: str
    source_layer: str
    affected_processes: list[str]
    affected_capacities: list[str] = []
    intensity: float
    reversibility: str
    activation_condition: str
    duration_policy: str = "tick"
    decay_rate: float = 0.0
    downstream_effects: list[str] = []
    evidence_refs: list[str] = []
```

A constraint without an activation condition and downstream effect is only a label. It should not be allowed to affect capacity, action, expression, recognition, or irreversibility.

### 6.2 CapacityDemand

```python
class CapacityDemand(BaseModel):
    capacity_id: str
    capacity_type: str
    holder_process_id: str
    target_process_id: str | None = None
    urgency: float
    viability_requirement: str
    evidence_refs: list[str] = []
```

### 6.3 BlockedCapacity

```python
class BlockedCapacity(BaseModel):
    capacity_id: str
    capacity_type: str
    holder_process_id: str
    target_process_id: str | None = None
    blockage_type: str
    blocking_constraints: list[str]
    intensity: float
    reversibility: str
    urgency: float
    evidence_refs: list[str] = []
```

### 6.4 DramaticContradiction

```python
class DramaticContradiction(BaseModel):
    contradiction_id: str
    capacities: list[str]
    incompatibility_type: str
    affected_processes: list[str]
    constraint_field_id: str
    available_resolution_strategies: list[str]
    selected_resolution_strategy: str | None = None
    failure_modes: list[str] = []
    evidence_refs: list[str] = []
```

These classes may begin as trace-only diagnostics and later become causal input to action, expression, recognition, and irreversibility engines.

When they become causal input, every downstream decision must cite the conflict event that influenced it. Conflict pressure must never mutate derived views directly.

---

## 7. Engine Additions

Add a conflict subsystem under:

```text
rpf/engine/conflict.py
```

### 7.1 Conflict Engine Responsibilities

```text
ConflictEngine
- build_constraint_field(state, tick_context, recent_events)
- evaluate_capacity_demands(state, constraint_field)
- detect_blocked_capacities(state, capacity_demands, constraint_field)
- detect_contradictions(blocked_capacities, capacity_demands, constraint_field)
- score_conflict_pressure(contradictions, blocked_capacities)
- emit_conflict_events(...)
```

### 7.2 Inputs

The engine consumes:

```text
SimulationState
TickContext
FieldPressureEvent
Binding events
Recognition demands
Active RPPs
Irreversibility records
Memory pressures
Affordance candidates
Audience and face risk
```

### 7.3 Outputs

The engine produces:

```text
ConstraintFieldEvent
CapacityDemandEvent
BlockedCapacityEvent
DramaticContradictionEvent
diagnostic traces
conflict_pressure values for downstream engines
```

### 7.4 Downstream Consumers

Conflict output should feed:

```text
scheduler
affordance selection
action selection
expression selection
RPP activation
recognition evaluation
repair evaluation
irreversibility evaluation
```

It must not directly mutate `PersonView`, `RelationshipView`, trust, intimacy, resentment, or personality.

### 7.5 Authority Boundaries

The `ConflictEngine` must not become the drama director of the simulation.

It may:

```text
- expose hidden constraint/capacity evidence.
- explain why an existing affordance, action, expression, recognition outcome, or irreversible event became likely.
- add bounded score adjustments to downstream engines after trace-only validation.
- supply structured context to LLM rendering.
```

It may not:

```text
- decide that a scene "needs" conflict.
- force a confrontation, confession, apology, rescue, breakup, death, or reconciliation.
- create a plot beat without lower-layer evidence.
- mutate person or relationship views.
- allow the LLM to introduce causes not present in the event stream.
```

The engine's default output should be explanatory. Causal influence must be explicit, limited, and replayable.

---

## 8. Scenario Authoring Additions

Scenarios should eventually allow explicit conflict seeds without defining a plot.

Add optional fields:

```yaml
conflict_seeds:
  - id: rent_due_care_debt
    constraint_sources:
      - material: rent_deadline
      - historical: unacknowledged_sacrifice
    active_capacities:
      - holder: a
        type: recognition
        target: b
        viability_requirement: "must have contribution acknowledged"
      - holder: b
        type: identity_continuity
        viability_requirement: "must not appear dependent"
    expected_contradictions:
      - recognition_vs_face
      - care_vs_autonomy
```

Rules:

- conflict seeds are not plot beats
- they define pressures and incompatibilities
- the simulator still selects scenes, actions, recognition outcomes, and irreversible consequences
- seeds may decay, intensify, transform, or fail to activate

Scenario conflict seeds should be treated as initial field asymmetries, not authorial instructions. A seed is valid when it defines pressure sources and possible incompatibilities. It is invalid when it names a required outcome.

---

## 9. First Implementable Mode: Recognition Conflict

The first concrete mode should be `recognition_conflict`.

Rationale:

- it is already central to RPF
- it connects to existing recognition, repair, memory, and irreversibility engines
- it can express many interpersonal conflicts
- it is easy to evaluate in traces

### 9.1 Recognition Conflict Formula

```text
A needs B to recognize X
but B recognizing X threatens B's face, identity, position, memory, resource control, or survival strategy.
```

### 9.2 Recognition Demand Types

```text
see_me
choose_me
respect_me
thank_me
believe_me
forgive_me
need_me
release_me
admit_what_happened
admit_i_mattered
allow_change
allow_nonchange
```

### 9.3 Recognition Obstacles

```text
face_risk
debt_risk
responsibility_risk
identity_risk
status_risk
dependency_risk
exit_risk
audience_risk
memory_risk
institutional_risk
```

### 9.4 Expression Deformations

```text
direct_claim
indirect_accusation
practical_help
public_performance
silence
delay
joke
body_withdrawal
object_displacement
over_compliance
counter_accusation
```

### 9.5 Outcomes

```text
granted
partial
refused
displaced
postponed
misunderstood
mocked
unspeakable
```

### 9.6 Irreversibility Outcomes

```text
topic_becomes_unsayable
debt_lock
role_lock
identity_mark
public_reclassification
memory_reconstruction
future_interpretation_bias
lost_repair_route
```

### 9.7 Minimal Recognition Conflict Algorithm

```text
1. Collect active recognition demands.
2. For each demand, evaluate obstacles.
3. Emit CapacityDemandEvent for recognition.
4. If obstacle score exceeds threshold, emit BlockedCapacityEvent.
5. If recognition need and obstacle are both high, emit DramaticContradictionEvent.
6. Feed contradiction evidence into action and expression selection.
7. Select direct claim, inhibition, substitution, or deformation.
8. Evaluate recognition outcome using contradiction evidence.
9. If the outcome is refused, displaced, misunderstood, or unspeakable, update repair debt and memory pressure.
10. If thresholds are crossed, emit IrreversibilityEvent or OperativeClassificationEvent.
```

---

## 10. Natural and Material Conflict Integration

Natural or material conflict should not be bolted on as a separate genre engine.

It should enter as constraint source:

```text
weather
illness
injury
distance
scarcity
time pressure
physical danger
spatial enclosure
resource depletion
bodily exhaustion
```

These constraints produce drama when they block capacities:

```text
survival capacity blocked by danger
care capacity blocked by distance
exit capacity blocked by storm
truth disclosure blocked by injury or exhaustion
repair capacity blocked by time pressure
loyalty capacity blocked by scarcity
```

Then the ordinary RPF process continues:

```text
blocked capacity
-> action deformation
-> observation
-> recognition / misrecognition
-> memory
-> irreversibility
```

This is how RPF can unify interpersonal and natural conflict without making a separate ontology for each genre.

Specialized modules may later simulate domains such as:

- disaster physics
- illness progression
- investigation logic
- economic systems
- political institutions
- combat or chase dynamics

But those modules should emit constraints and events into the same RPF conflict pipeline.

---

## 11. Evaluation Criteria

The framework succeeds when:

- conflicts can be traced from constraints to blocked capacities
- actions are selected from availability, not generic desire
- expression deformations are explainable
- misrecognition arises from structure, not random misunderstanding
- natural/material pressures become relational without losing material force
- irreversible outcomes specify lost alternatives
- derived labels remain derived unless operative
- replay reconstructs the same conflict path

The framework fails when:

- the simulator says "conflict happened" without blocked capacity evidence
- a character acts from a trait label
- material conflict becomes only background flavor
- recognition outcomes are selected by one crude threshold
- LLM prose invents causes not present in events
- high-level genre labels bypass the shared conflict kernel
- capacity demand is inferred from a character label instead of a process requirement
- the conflict engine starts selecting plot-shaped outcomes before trace evidence is stable
- constraints have no activation condition, decay rule, affected capacity, or source evidence
- a blocked capacity never deforms, fails, gets observed, or changes future alternatives

---

## 12. Implementation Phases

### Phase 1: Trace-Only Conflict Kernel

Add models and events, but do not let them control behavior yet.

Deliverables:

```text
ConstraintFieldEvent
CapacityDemandEvent
BlockedCapacityEvent
DramaticContradictionEvent
constraint_trace.json
capacity_trace.json
conflict_trace.json
```

Acceptance:

- existing scenarios still run
- traces explain current recognition conflicts
- no derived views mutate causal state
- conflict events are fully reconstructable from existing lower-layer events
- at least one current benchmark scenario can explain its recognition conflict without changing the simulation output

### Phase 2: Recognition Conflict Integration

Use blocked recognition capacity and dramatic contradiction evidence in:

```text
action selection
expression selection
recognition evaluation
repair evaluation
irreversibility evaluation
```

Acceptance:

- recognition outcomes cite contradiction evidence
- expression deformation cites blocked capacity
- failed recognition can produce memory pressure and irreversible outcomes
- every affected recognition decision cites conflict evidence
- removing conflict evidence changes explanations before it changes behavior

### Phase 3: Scenario Authoring Support

Add optional `conflict_seeds` to scenario YAML.

Acceptance:

- seeds influence constraints and capacity demand
- seeds do not force plot outcomes
- benchmark scenarios can define at least one explicit conflict seed each
- seeds can fail to activate without causing validation failure

### Phase 4: Material/Natural Constraint Expansion

Add richer material and bodily constraint sources.

Acceptance:

- at least one benchmark scenario produces conflict primarily from material or bodily constraint
- the conflict still passes through the same blocked-capacity pipeline

### Phase 5: Viewer Support

Add a workbench panel:

```text
Conflict
- dominant constraints
- blocked capacities
- active contradictions
- deformation path
- irreversible consequences
```

Acceptance:

- users can inspect why a scene became conflictual
- every displayed conflict item links to source events

---

## 13. Non-Negotiable Invariants

```text
1. Conflict is not a primitive genre label.
2. Conflict must be traceable to constraint and blocked capacity evidence.
3. A blocked capacity is not automatically dramatic; it becomes dramatic through expression, observation, recognition, stabilization, or irreversibility.
4. Natural/material conflict and interpersonal conflict use the same conflict kernel.
5. PersonView and RelationshipView remain derived.
6. Trust, intimacy, resentment, and personality remain aggregates.
7. LLM rendering may describe conflict but may not authorize it.
8. Irreversibility must define future constraints and lost alternatives.
9. Scenario conflict seeds define pressures, not plot outcomes.
10. Replay must reconstruct the same conflict evidence chain.
11. Capacity is a process requirement, not a character desire.
12. Constraint is invalid without activation condition, affected capacity, downstream effect, and evidence.
13. The conflict kernel begins as explanation before it gains causal authority.
14. Conflict pressure may bias downstream engines only through explicit, replayable evidence refs.
```

---

## 14. Summary

The elegant version of the RPF architecture is:

```text
RPF simulates how constraint fields reshape actionability.
Persons, relationships, identities, and fate are stabilized views of blocked, deformed, observed, recognized, misrecognized, remembered, and irreversible process history.
```

This gives the project a unified dramatic architecture:

```text
Constraint Field
-> Capacity Demand
-> Blocked Capacity
-> Dramatic Contradiction
-> Action / Expression Deformation
-> Observation
-> Recognition / Misrecognition
-> Repair / Escalation / Avoidance
-> Stabilization
-> Irreversibility
-> Derived Views
```

The first mode to implement should be recognition conflict. Once that mode is strong, the same kernel can absorb care conflict, exit conflict, survival conflict, secrecy conflict, institutional conflict, and material/natural conflict without changing the ontology.
