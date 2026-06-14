# RPF Relational Process Pattern Library Specification

## 0. Purpose

This document defines how to design the RPF RPP library.

An RPP is a Relational Process Pattern:

```text
a recurring dynamic form through which relational processes stabilize into recognizable persons, roles, conflicts, and fate-like trajectories
```

RPPs are not personality traits.

They are not plot beats.

They are evidence-based dynamic patterns that become active when field conditions, micro signals, relevance landscapes, and recognition demands align.

---

## 1. RPP Design Contract

Every RPP must define:

```text
id
name
core dynamic
eligible field conditions
participating positions
triggering differences
activation scoring
contraindications
micro signal interpretation
recognition structure
ritual forms
communication forms
stabilization effects
irreversibility risks
repair paths
decay conditions
diagnostic evidence
```

No RPP may say:

```text
A is avoidant, therefore A withdraws.
```

It must say:

```text
Given these field conditions, micro signals, and relevance weights,
withdrawal becomes an available and stabilizing action form for this position.
```

---

## 2. RPP Schema

```text
RPP
- rpp_id
- name
- description
- core_dynamic
- eligible_field_conditions
- participating_position_requirements
- triggering_differences
- activation_weights
- contraindications
- micro_signal_mappings
- relevance_effects
- recognition_structure
- ritual_forms
- communication_forms
- action_forms
- stabilization_effects
- aggregation_effects
- irreversibility_risks
- repair_paths
- decay_conditions
- diagnostics
```

### 2.1 Core Dynamic

A short statement of the pattern's recursive loop.

Example:

```text
One position seeks recognition through contact; the other experiences contact as loss of agency and restores agency through withdrawal; withdrawal intensifies the first position's recognition demand.
```

### 2.2 Eligible Field Conditions

Field conditions are not optional decoration. They decide whether the pattern is sociologically plausible.

Examples:

- exit capacity asymmetry
- unresolved injury
- high face risk
- low repair access
- institutional binding
- resource dependency
- public/private definition gap
- symbolic capital gap

### 2.3 Triggering Differences

Triggering differences are micro signals or field events.

Examples:

- delayed reply
- avoided gaze
- changed greeting
- interruption
- unacknowledged sacrifice
- public correction
- failed repair gesture
- practical request that carries hidden recognition demand

### 2.4 Activation Weights

Activation weights must be explicit.

```text
activation_score =
  trigger_strength
+ relevance_match
+ prior_pattern_frequency
+ recognition_pressure
+ field_pressure
+ fatigue_modifier
- recent_successful_repair
- exit_availability
- ritual_containment
```

### 2.5 Contraindications

Contraindications prevent overactivation.

Examples:

- high explicit trust repair within recent window
- strong third-party containment
- low ambiguity in current communication
- direct recognition already granted
- scene frame makes pattern implausible

---

## 3. Required Base RPPs

The initial RPP library should include at least these patterns:

```text
RPP-001 pursuit_withdrawal
RPP-002 symmetrical_escalation
RPP-003 complementary_dependency
RPP-004 double_bind
RPP-005 meta_communication_failure
RPP-006 face_saving_loop
RPP-007 recognition_pursuit
RPP-008 risk_checking_loop
RPP-009 repair_avoidance
RPP-010 contribution_debt_loop
RPP-011 silence_interpretation_loop
RPP-012 public_private_split
```

These are enough to generate long-term relational drama without relying on predefined personalities.

---

## 4. RPP-001 Pursuit Withdrawal

### Core Dynamic

```text
Contact sought as recognition is received as pressure;
withdrawal used to restore agency is received as abandonment;
abandonment intensifies contact-seeking.
```

### Eligibility

- one position has elevated recognition dependency
- another has elevated autonomy threat sensitivity or speech inhibition
- co-presence binding prevents easy exit
- prior ambiguous withdrawal exists

### Triggering Differences

- delayed response
- shortened answer
- physical turning away
- leaving before closure
- practical busyness during emotional demand

### Activation Weights

```text
+ abandonment relevance
+ prior withdrawal count
+ low exit capacity of pursuing position
+ fatigue in withdrawing position
+ unrepaired recognition demand
- recent explicit reassurance
- high ritual containment
- available third-party mediation
```

### Communication Forms

Pursuing position:

- repeated checking
- accusation disguised as concern
- indirect demand
- forced clarification

Withdrawing position:

- silence
- practical deflection
- spatial exit
- minimal answer
- tiredness claim

### Stabilization Effects

- pursuit becomes expected
- withdrawal becomes expected
- PersonView may later show "clingy", "cold", "needy", or "avoidant" as derived labels
- ambiguity tolerance decreases

### Irreversibility Risks

- "You always leave" becomes operative
- "You are controlling" becomes operative
- a failure to return becomes a relationship marker

### Repair Paths

- explicit naming of the loop
- low-pressure reassurance
- negotiated pause with return commitment
- recognition granted without immediate fusion

---

## 5. RPP-002 Symmetrical Escalation

### Core Dynamic

```text
Each position interprets the other's intensity as domination;
each increases intensity to avoid being subordinated.
```

### Eligibility

- comparable power or contested authority
- high dignity threat
- low ritual containment
- audience or imagined audience increases face stakes

### Triggering Differences

- interruption
- public correction
- raised voice
- dismissive summary
- refusal to yield conversational floor

### Stabilization Effects

- conflict becomes proof of strength
- concession becomes humiliation
- apology threshold rises

### Repair Paths

- frame shift
- audience removal
- third object/task
- delayed apology
- humor that preserves both faces

---

## 6. RPP-003 Complementary Dependency

### Core Dynamic

```text
One position stabilizes self through being needed;
the other stabilizes self through being cared for or managed;
both resist autonomy when it threatens the relation's function.
```

### Eligibility

- asymmetric care labor
- material or emotional dependency
- identity investment in caretaker/dependent roles
- weak outside support

### Triggering Differences

- dependent position shows autonomy
- caretaker position withholds help
- third party offers support
- care is not acknowledged

### Stabilization Effects

- care becomes control
- need becomes currency
- autonomy becomes betrayal

### Irreversibility Risks

- sacrifice debt
- public identity as caretaker
- learned incapacity
- resentment after long invisible labor

---

## 7. RPP-004 Double Bind

### Core Dynamic

```text
A position receives incompatible demands where satisfying one violates another, and naming the contradiction is punished.
```

### Eligibility

- power asymmetry
- dependence or exit constraint
- meta-communication blocked
- prior punishment for direct naming

### Example Forms

- "Be honest, but do not hurt me."
- "Need me, but do not be needy."
- "Change, but remain the person I chose."
- "Choose freely, but prove you choose me."

### Stabilization Effects

- speech inhibition increases
- self-monitoring increases
- action space contracts
- confusion becomes personalized as defect

### Repair Paths

- meta-communication becomes safe
- contradiction is publicly named
- demand source accepts responsibility

---

## 8. RPP-005 Meta-Communication Failure

### Core Dynamic

```text
Participants argue over content while the real conflict concerns what the communication means for the relationship.
```

### Triggering Differences

- "I was just asking."
- "That's not what I meant."
- "Why are you making this about us?"
- practical issue repeatedly returns as relational accusation

### Stabilization Effects

- content topics become contaminated
- repair fails because wrong layer is addressed
- both positions feel misunderstood

---

## 9. RPP-006 Face Saving Loop

### Core Dynamic

```text
Truth is displaced into acceptable performance forms to preserve the scene; displacement prevents full recognition and preserves the underlying tension.
```

### Forms

- joke instead of apology
- practical help instead of confession
- politeness instead of anger
- tiredness instead of fear
- logistics instead of grief

### Stabilization Effects

- relation continues
- injury remains unnamed
- surface peace becomes fragile

---

## 10. RPP-007 Recognition Pursuit

### Core Dynamic

```text
One position repeatedly seeks a specific recognition from the other; the other cannot grant it without threatening its own identity, legitimacy, or power.
```

### Recognition Examples

- admit I mattered
- admit you hurt me
- admit you need me
- allow me to change
- believe what I remember

### Stabilization Effects

- every practical interaction becomes charged with symbolic demand
- refusal becomes evidence of deeper refusal
- substitutes for recognition lose effectiveness

---

## 11. RPP-008 Risk Checking Loop

### Core Dynamic

```text
Uncertainty becomes intolerable; checking behavior reduces short-term uncertainty while increasing long-term distrust and surveillance.
```

### Triggering Differences

- ambiguous message
- unexplained absence
- hidden phone
- changed routine
- inconsistent story

### Stabilization Effects

- checking becomes normalized
- privacy becomes suspicious
- trust_view declines as derived aggregate

---

## 12. RPP-009 Repair Avoidance

### Core Dynamic

```text
Repair would require recognizing an injury, but recognition threatens face, identity, or power; therefore relation uses avoidance to continue.
```

### Forms

- moving on too quickly
- practical kindness without apology
- topic change
- sexual/intimate reset
- gift
- shared task

### Stabilization Effects

- repair debt accumulates
- future conflict reactivates old injury
- resentment pressure rises

---

## 13. RPP-010 contribution debt loop

### Core Dynamic

```text
Sacrifice creates moral credit; unrecognized sacrifice becomes resentment; recognized sacrifice can become control.
```

### Eligibility

- asymmetric labor
- low visibility of cost
- high identity investment in sacrifice
- recipient has limited capacity to reciprocate

### Stabilization Effects

- gratitude becomes obligation
- refusal becomes betrayal
- help becomes morally unsafe

---

## 14. RPP-011 Silence Interpretation Loop

### Core Dynamic

```text
Silence repeatedly receives stable relational meaning, and that meaning becomes harder to disconfirm.
```

### Possible Meanings

- care
- punishment
- contempt
- restraint
- fear
- exhaustion
- abandonment
- superiority

### Rule

Silence has no default meaning. Meaning is assigned by history, relevance, and ritual frame.

---

## 15. RPP-012 Public Private Split

### Core Dynamic

```text
The relation has one public definition and another private operating structure; maintaining the gap consumes energy and produces misrecognition.
```

### Examples

- publicly equal, privately dependent
- publicly affectionate, privately punitive
- publicly separated, privately bound
- publicly casual, privately fate-like

### Irreversibility Risks

- exposure
- reputational collapse
- identity reclassification
- impossible return to prior public fiction

---

## 16. RPP Composition

Multiple RPPs may compose.

Example:

```text
pursuit_withdrawal
+ silence_interpretation_loop
+ repair_avoidance
-> chronic cold-war relation
```

Composition must be explicit in diagnostics.

---

## 17. RPP Decay

An RPP decays when:

- trigger frequency declines
- repair succeeds
- exit capacity changes
- recognition is granted
- field pressure changes
- ritual frame changes
- new RPP replaces its stabilizing function

Emit:

```text
RPPDecayEvent
```

---

## 18. Library Quality Criteria

An RPP is valid only if:

- it has non-personality eligibility conditions
- it defines triggering differences
- it has activation scoring
- it defines repair paths
- it defines stabilization effects
- it defines irreversibility risks
- it can fail to activate
- it can decay

An RPP is invalid if:

- it directly encodes a character trait
- it requires a plot outcome
- it has no field conditions
- it treats labels as causes before uptake
- it cannot be diagnosed from event evidence

---

## 19. Implemented Research Kernel

The current runtime implements a research-kernel subset of the library:

```text
pursuit_withdrawal
repair_avoidance
contribution_debt_loop
double_bind
public_private_split
silence_interpretation_loop
complementary_dependency
face_saving_loop
recognition_pursuit
```

Each implemented RPP is evaluated from state, tick context, and event evidence. No RPP reads derived person labels as causal inputs.

The newer research-kernel RPPs use a primary field gate before scoring. This prevents the simulator from treating every conflict as every pattern. For example:

- `double_bind` requires `double_bind_pressure`
- `public_private_split` requires `public_private_gap`
- `silence_interpretation_loop` requires `silence_charge`
- `complementary_dependency` requires `care_dependency`
- `face_saving_loop` requires `face_risk_pressure`
- `recognition_pursuit` requires `recognition_pursuit_pressure`

This is a conceptual constraint, not merely calibration. An RPP should activate only when the relation has the structural affordance for that pattern.

---

## 20. Dominance Semantics

RPP activation count is diagnostic, but it is not the definition of dominance.

The benchmark suite defines dominant RPP by cumulative activation strength:

```text
dominant_rpp = argmax(sum(activation_score by rpp_id))
```

Reason:

- repeated weak activations should not dominate a scenario
- scene-only mechanisms should not be penalized against micro-interaction mechanisms
- long-term fate is shaped by the attractor that accumulates the most explanatory force

The runtime therefore emits both:

```text
rpp_activation_counts
rpp_activation_score_sums
```

Counts answer: "How often did this pattern appear?"

Score sums answer: "Which pattern absorbed the most relational energy?"

Benchmark dominance uses score sums.

---

## 21. RPP Dynamics Layer

The runtime now contains an explicit RPP dynamics layer after individual RPP activation.

This layer models relations among patterns:

```text
RPP activation
-> RPP composition
-> RPP suppression
-> RPP decay
-> aggregation and projection
```

This prevents the simulator from treating RPPs as independent checkboxes.

### 21.1 Composition

Composition identifies higher-order relational circuits formed by multiple active RPPs.

Implemented compositions:

```text
anxious_silence_circuit
  pursuit_withdrawal + silence_interpretation_loop

debt_lock
  contribution_debt_loop + repair_avoidance

public_face_split
  public_private_split + face_saving_loop

care_bind_double_bind
  complementary_dependency + double_bind

recognition_trap
  recognition_pursuit + repair_avoidance

credit_recognition_lock
  contribution_debt_loop + recognition_pursuit
```

Composition events are emitted as:

```text
RPPCompositionEvent
```

Composition dominance is measured by cumulative composition score, parallel to RPP dominance.

### 21.2 Suppression

Suppression models the fact that one relational pattern can absorb explanatory force from another.

Examples:

- mediated absence can suppress public/private split
- care obligation can suppress pursuit/withdrawal
- double bind can suppress repair avoidance by making avoidance a symptom of blocked meta-communication

Suppression events are emitted as:

```text
RPPSuppressionEvent
```

### 21.3 Decay

Inactive patterns do not remain equally alive forever.

When an active RPP is not reactivated for the configured number of ticks, its intensity decays.

Decay events are emitted as:

```text
RPPDecayEvent
```

Decay is necessary for long simulations. Without it, early transient patterns would permanently contaminate later fate.

### 21.4 Trace Output

Every run writes:

```text
rpp_dynamics_trace.json
```

Each tick records:

- activated RPPs
- active compositions
- suppressions
- decays
- current active RPP intensities


