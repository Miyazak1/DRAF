# RPF Aggregation and Projection Specification

## 0. Purpose

This document defines how RPF aggregates lower-level structures into higher-level readable concepts.

It answers:

- how "trust" appears without becoming a primitive variable
- how "personality" appears without being predefined
- how "relationship state" appears without being an entity
- when high-level labels can feed back into causal state

The key rule:

```text
aggregate views are read models;
operative classifications are causal events.
```

---

## 1. Layered Aggregation Model

RPF uses recursive layered aggregation:

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

Aggregation runs after each causal update cycle.

---

## 2. Aggregation Contract

Each aggregate must define:

```text
name
source fields
source events
calculation method
confidence
freshness
interpretation
non-causal guarantee
operative conversion conditions
```

No aggregate may be written manually during simulation.

---

## 3. Micro Signal Aggregation

Micro signals are grouped by:

- source process
- target process
- scene
- signal type
- interpreted meaning
- active RPP
- recurrence window

Example:

```text
delayed_reply_count_last_10_scenes
gaze_avoidance_under_recognition_pressure
unacknowledged_help_events
topic_changes_after_injury_reference
```

These become evidence for process patterns.

---

## 4. Relational Aggregate Views

### 4.1 TrustView

Trust is not a number. It is a structured risk-suspension profile.

```text
TrustView
- risk_suspension_by_domain
- checking_frequency
- vulnerability_exposure_permission
- ambiguity_tolerance
- betrayal_expectation
- repair_recovery_speed
- evidence_refs
- confidence
```

Domains:

- emotional disclosure
- material reliance
- bodily safety
- social reputation
- future commitment
- memory truth

Computation:

```text
trust_domain_score =
  risk_suspension_scope
+ ambiguity_tolerance
+ repair_recovery_speed
+ vulnerability_exposure_permission
- checking_frequency
- betrayal_expectation
- unrepaired_injury_weight
```

Output:

```text
high / medium / low / unstable / domain-split
```

Never output only a scalar.

### 4.2 IntimacyView

Intimacy is boundary permeability under safety.

```text
IntimacyView
- unforced_disclosure_range
- tolerated_unmanaged_presence
- bodily_boundary_permeability
- silence_safety
- shame_exposure_capacity
- shared_private_world_density
- evidence_refs
```

Computation:

```text
intimacy_score =
  disclosure_without_repair_need
+ safe_silence_frequency
+ shared_private_references
+ tolerated_unideal_presence
- shame_after_exposure
- surveillance_after_disclosure
```

### 4.3 DependencyView

Dependency is exit capacity structure, not emotional weakness.

```text
DependencyView
- material_exit_cost
- emotional_exit_cost
- social_exit_cost
- institutional_exit_cost
- care_exit_cost
- narrative_exit_cost
- asymmetry
- replacement_access
```

Computation:

```text
dependency_asymmetry =
  weighted_exit_cost_A - weighted_exit_cost_B
```

### 4.4 ResentmentPressureView

Resentment is blocked moral accounting.

```text
ResentmentPressureView
- unrecognized_injuries
- denied_causality_events
- unpaid_sacrifice_debts
- forced_maturity_demands
- repeated_invalidations
- revenge_fantasy_markers
- evidence_refs
```

Computation:

```text
resentment_pressure =
  unrecognized_injury_weight
+ sacrifice_debt_weight
+ denied_causality_weight
+ repair_avoidance_weight
- explicit_acknowledgment_weight
- restitution_weight
```

### 4.5 PowerAsymmetryView

Power is the ability to define, sanction, exit, and make one's interpretation stick.

```text
PowerAsymmetryView
- definition_power
- sanction_power
- exit_power
- resource_power
- narrative_power
- institutional_power
- repair_control
- audience_control
```

### 4.6 RepairCapacityView

Repair capacity measures whether rupture can be metabolized.

```text
RepairCapacityView
- apology_availability
- recognition_grant_capacity
- face_safe_repair_paths
- timing_recovery_window
- audience_containment
- prior_repair_success
- repair_debt
```

### 4.7 ConflictPressureView

```text
ConflictPressureView
- active_recognition_pressure
- incompatible_demands
- RPP_activation_density
- field_pressure
- fatigue_load
- face_risk
- unresolved_irreversibles
```

### 4.8 StabilityView

Stability is not health. Harmful patterns can be stable.

```text
StabilityView
- pattern_predictability
- binding_strength
- repair_sufficiency
- exit_suppression
- public_definition_support
- field_reinforcement
- volatility
```

---

## 5. PersonView Projection

PersonView is generated from:

- stabilized RPPs
- embodied habitus
- field positions
- relation-specific profiles
- operative classifications
- repeated action affordances
- recognition demand history
- irreversibility records

### 5.1 PersonView Fields

```text
PersonView
- apparent_traits
- stabilized_response_patterns
- recognized_roles
- habitual_interpretations
- embodied_defenses
- relational_positions
- self_narratives
- imposed_labels
- unavailable_actions
- possible_transformations
- evidence_refs
```

### 5.2 Apparent Trait Derivation

Example:

```text
"avoidant"
```

may be derived when:

- withdrawal under intimacy pressure is frequent
- speech inhibition rises during recognition demand
- autonomy threat salience is high
- repair is often postponed through distance
- others have begun predicting withdrawal

But "avoidant" cannot cause withdrawal unless it becomes operative.

---

## 6. RelationshipView Projection

RelationshipView is generated from:

- active bindings
- recurring RPPs
- recognition conflicts
- communication loops
- repair patterns
- forbidden truths
- shared irreversibles
- public/private definitions
- exit asymmetry

### 6.1 Relationship Phase Labels

Allowed labels:

- latent
- fragile
- ritual-stable
- escalating
- repair-dependent
- cold-war
- fusion-threatening
- exit-imminent
- locked-in
- transformed

These are derived scene-planning aids, not causal primitives.

---

## 7. Narrative Label Generation

Narrative labels are generated when aggregates cross interpretive thresholds.

Examples:

```text
"They are in a cold war."
"She has become careful around him."
"He treats every question as an accusation."
"They are publicly fine and privately bound by injury."
```

Labels must include:

- evidence
- confidence
- perspective
- whether the label is private, public, or narrator-only

---

## 8. Operative Conversion

A label becomes operative only if uptake occurs.

### 8.1 Uptake Conditions

```text
spoken_in_scene
self_adopted
other_adopted
audience_repeated
institutionally_recorded
used_to_justify_action
used_to_deny_claim
used_to_predict_future
```

### 8.2 Conversion Event

Emit:

```text
OperativeClassificationEvent
```

Payload:

```text
label
source
target
audience
uptake_type
legitimacy
sanction_power
future_interpretation_bias
```

---

## 9. Downward Constraint

Operative classifications affect lower layers through explicit paths:

```text
label
-> face risk
-> speech inhibition
-> relevance trigger weights
-> self-narrative pressure
-> audience expectation
-> action availability
-> future micro-signal interpretation
```

Invalid:

```text
label "cold" -> withdrawal +0.2
```

Valid:

```text
label "cold"
-> face risk rises during tenderness scenes
-> speech inhibition rises when warmth is expected
-> delayed response is interpreted through coldness frame
-> withdrawal RPP becomes more eligible
```

---

## 10. Aggregation Trace

Every aggregate must produce a trace.

```text
AggregationTrace
- aggregate_name
- source_events
- source_parameters
- active_rpps
- formula_or_rule
- confidence
- uncertainty
- generated_label_candidates
```

This trace is required for debugging and scientific inspection.

---

## 11. Update Frequency

Recompute aggregates:

- after each tick
- after episode closure
- after operative classification event
- after irreversibility event
- before LLM rendering

Long-window aggregates should use rolling windows:

```text
last_scene
last_5_scenes
last_20_scenes
whole_history
post_irreversibility_window
```

---

## 12. Quality Criteria

Aggregation is valid when:

- all high-level concepts have evidence refs
- formulas reference causal state or events
- labels are perspective-aware
- operative feedback requires uptake
- aggregate uncertainty is represented

Aggregation is invalid when:

- a label appears without evidence
- trust/intimacy/personality is stored as primitive cause
- derived view is used to mutate state
- confidence is implied but not calculated
- labels feed back without uptake


