# RPF Temporal Scheduler and Scene Selection

## 0. Purpose

This document defines how RPF chooses:

- the next tick type
- the simulated time delta
- whether a scene crystallizes
- which scene crystallizes
- why the scene occurs here and now

It extends:

```text
rpf-simulation-runtime.md
```

The key rule:

```text
time and scenes must emerge from field pressure, binding, relevance, and RPP dynamics;
they must not be scheduled for plot convenience.
```

---

## 1. Scheduler Responsibility

The Temporal Scheduler owns:

```text
next_tick_type
simulated_time_delta
time_mapping_reason
candidate_scene_set
selected_scene
no_scene_reason
```

It does not own:

- RPP consequences
- recognition outcomes
- aggregation results
- irreversible events
- LLM rendering

---

## 2. Scheduler Inputs

```text
SchedulerInput
- current_state
- event_history_window
- active_bindings
- field_pressures
- active_rpps
- recognition_demands
- process_body_states
- relevance_landscapes
- spatial_arrangements
- temporal_obligations
- runtime_config
- random_stream
```

The scheduler must not use `PersonView` or `RelationshipView` as causal input.

It may use causal structures that contributed to those views.

---

## 3. Scheduler Output

```text
SchedulerDecision
- tick_type: latent | micro_interaction | scene
- simulated_time_delta_seconds
- time_mapping_reason
- candidate_scenes
- selected_scene_id optional
- selection_reason
- rejected_scene_reasons
- diagnostics
```

The decision must be persisted through events:

```text
LatentTimeEvent
NoSceneEvent
SceneCrystallizationEvent
RandomnessTraceEvent optional
```

---

## 4. Tick Type Selection

The scheduler computes three scores:

```text
latent_score
micro_interaction_score
scene_score
```

Then selects a tick type by:

```text
rule-based eligibility
+ weighted score
+ seeded probabilistic selection when multiple types are close
```

### 4.1 Latent Eligibility

Latent tick is eligible when:

- no co-presence is required immediately
- field pressures can accumulate without direct contact
- avoidance is available
- spatial or temporal separation is plausible
- active RPPs are below expression threshold

### 4.2 Micro-Interaction Eligibility

Micro-interaction tick is eligible when:

- brief co-presence is likely
- a message, gesture, routine, or object can carry meaning
- full scene pressure is not yet high enough
- a binding creates contact but not prolonged engagement
- a latent RPP can surface through a small signal

### 4.3 Scene Eligibility

Scene tick is eligible when:

- binding pressure requires co-presence
- field pressure crosses urgency threshold
- recognition pressure crosses expression threshold
- active RPP intensity crosses scene threshold
- micro-interaction has escalated
- avoidance capacity is too low
- an irreversible event is likely if pressure is not metabolized

---

## 5. Tick Type Scoring

### 5.1 Latent Score

```text
latent_score =
  avoidance_capacity
+ spatial_separation
+ low_immediate_field_urgency
+ low_RPP_expression_pressure
+ fatigue_blocking_interaction
+ existing_nonreply_window
- binding_urgency
- recognition_expression_pressure
```

### 5.2 Micro-Interaction Score

```text
micro_interaction_score =
  brief_copresence_probability
+ routine_overlap
+ message_probability
+ micro_signal_pressure
+ moderate_binding_urgency
+ active_habit_pattern
- scene_pressure
- full_avoidance_capacity
```

### 5.3 Scene Score

```text
scene_score =
  field_urgency
+ binding_urgency
+ recognition_pressure
+ active_RPP_pressure
+ irreversibility_pressure
+ failed_avoidance_count
+ accumulated_micro_signal_charge
- avoidance_capacity
- exhaustion_block
- ritual_deferral_capacity
```

---

## 6. Time Delta Selection

The scheduler chooses time delta after choosing tick type.

Default ranges:

```text
latent:
  15 minutes to 3 days

micro_interaction:
  1 second to 15 minutes

scene:
  5 minutes to 6 hours
```

### 6.1 Time Compression Rule

Long periods with low event density may be compressed into one latent tick.

Example:

```text
8 hours pass overnight.
No direct interaction occurs.
Rent deadline gets closer.
A waits for a reply.
```

This should be one latent tick, not 32 fifteen-minute ticks.

### 6.2 Time Expansion Rule

A short real-time moment may require a full tick if it changes structure.

Example:

```text
B says "You always make it sound like I owe you."
```

This may occupy seconds but requires a scene or micro-interaction tick because it can create an operative classification.

### 6.3 Delta Formula

```text
time_delta =
  base_range_by_tick_type
  adjusted_by:
    field_deadline_distance
    response_waiting_window
    routine_schedule
    fatigue_recovery_need
    avoidance_duration
    spatial_overlap_probability
    next_obligation_time
```

### 6.4 Required Explanation

Every tick must record:

```text
time_mapping_reason
```

Examples:

```text
"overnight latent interval; no co-presence, rent pressure increased"
"brief kitchen overlap before work"
"rent discussion became recognition conflict"
```

---

## 7. Scene Candidate Generation

A scene candidate is a possible crystallization of pressure into local interaction.

```text
SceneCandidate
- candidate_id
- participants
- location
- frame
- declared_activity
- hidden_activity
- triggering_pressures
- active_bindings
- likely_micro_signals
- eligible_rpps
- audience
- exit_routes
- scene_score
- why_here
- why_now
- why_unavoidable
```

---

## 8. Scene Source Types

Scenes can crystallize from:

```text
field obligation
binding pressure
recognition pressure
RPP escalation
habit disruption
spatial overlap
message exchange
irreversibility pressure
third-party/audience pressure
```

### 8.1 Field Obligation Scene

Example:

```text
rent must be discussed
work deadline requires coordination
family event forces public performance
```

### 8.2 Binding Pressure Scene

Example:

```text
shared lease forces logistical conversation
care obligation requires contact
secret requires coordination
```

### 8.3 Recognition Pressure Scene

Example:

```text
unrecognized sacrifice becomes too charged to remain latent
```

### 8.4 RPP Escalation Scene

Example:

```text
repeated micro-withdrawals make pursuit_withdrawal cross scene threshold
```

---

## 9. Scene Scoring

```text
scene_candidate_score =
  field_urgency
+ binding_strength
+ recognition_pressure
+ active_RPP_intensity
+ spatial_plausibility
+ temporal_plausibility
+ audience_pressure
+ habit_disruption_charge
+ irreversibility_potential
- avoidance_capacity
- exit_route_strength
- ritual_deferral_capacity
- exhaustion_block
```

### 9.1 Minimum Scene Validity

A scene is invalid unless it can answer:

```text
Why these process positions?
Why this location or medium?
Why now?
Why can this not simply be avoided?
What pressure becomes visible here?
```

---

## 10. Location and Medium Selection

The scheduler must select not only whether a scene occurs, but where or through what medium.

Allowed media:

```text
physical co-presence
text message
phone call
voice message
public interaction
third-party mediated interaction
object-mediated interaction
```

### 10.1 Physical Location Factors

```text
shared_space_overlap
privacy_level
exit_route_availability
audience_presence
symbolic_contamination
habitual_use
field_obligation_relevance
```

### 10.2 Message Medium Factors

```text
avoidance_capacity
need_for_distance
urgency
ambiguity_potential
recordability
delay_interpretability
```

### 10.3 Object-Mediated Interaction

Examples:

```text
rent receipt left on table
washed cup
closed door
food placed aside
returned key
unmoved object
```

Object-mediated scenes are especially important for indirect repair and avoidance.

---

## 11. No-Scene Decision

If no scene crystallizes, the scheduler must emit a no-scene explanation.

```text
NoSceneEvent
- reason_no_scene
- strongest_candidate
- missing_thresholds
- accumulated_pressures
- next_likely_tick_type
```

No-scene is not nothing. It can increase pressure.

Examples:

```text
avoidance succeeded but recognition pressure increased
fatigue blocked confrontation
spatial separation prevented contact
both positions waited for the other to initiate
```

---

## 12. Upgrade and Downgrade

### 12.1 Latent to Micro

Upgrade when:

- message arrives
- brief co-presence occurs
- routine signal changes
- object-mediated signal appears
- waiting period produces interpretable sign

### 12.2 Micro to Scene

Upgrade when:

- micro signal is interpreted as recognition refusal
- face threat crosses threshold
- RPP activates above scene threshold
- one process directly names a label
- repair attempt requires response

### 12.3 Scene to Latent

Downgrade when:

- avoidance succeeds
- participants separate
- ritual closure occurs
- fatigue blocks continuation
- repair temporarily lowers pressure

### 12.4 Scene Split

Split one scene into multiple scene ticks when:

- audience changes
- location changes
- frame changes
- hidden activity becomes explicit
- irreversible event changes the problem

---

## 13. Scheduler Diagnostics

Every scheduler decision should optionally output:

```text
SchedulerDiagnostics
- tick_type_scores
- selected_tick_type
- rejected_tick_types
- time_delta_candidates
- selected_time_delta
- viability_rhythm
- candidate_scenes
- selected_scene
- rejected_scene_reasons
- threshold_values
- random_selection_trace
```

Diagnostics are required for debugging and validation.

`viability_rhythm` is a state-only preview used before tick events exist. It may include:

```text
- viability_pressure
- latent_instability
- micro_readiness
- scene_readiness
- scene_viability_bias
- micro_viability_bias
- latent_relief
```

This preview may only bias timing. It must not create a scene, select an action, or authorize a narrative beat.

---

## 14. MVP Scheduler

The MVP scheduler should be simple.

### 14.1 MVP Tick Selection

Use deterministic thresholds:

```text
if scene_score >= 0.65:
  tick_type = scene
elif micro_interaction_score >= 0.45:
  tick_type = micro_interaction
else:
  tick_type = latent
```

The MVP scheduler may add a bounded viability rhythm bias:

```text
scene_score += min(0.018, scene_readiness * tiny_weight)
micro_interaction_score += min(0.014, micro_readiness * tiny_weight)
micro_interaction_score -= min(0.012, latent_instability * tiny_weight)
```

These terms are rhythm controls, not plot controls.

### 14.2 MVP Time Delta

Use fixed sampled ranges:

```text
latent:
  4 to 16 hours

micro_interaction:
  5 seconds to 5 minutes

scene:
  10 to 90 minutes
```

### 14.3 MVP Scene Candidates

For `shared_apartment_unresolved_sacrifice`, support:

```text
kitchen_overlap
rent_message
unanswered_message
practical_repair
rent_discussion
doorway_micro_signal
```

---

## 15. Failure Modes

The scheduler has failed if:

- scenes occur because the plot needs them
- time advances without explanation
- all ticks become scene ticks
- latent time has no causal effect
- micro-interactions are treated as decorative
- physical location does not matter
- message delay has no time semantics
- scene selection uses PersonView labels as causal input

---

## 16. Summary

The scheduler gives RPF temporal realism.

It lets the simulator represent:

- waiting
- missed contact
- compressed uneventful time
- expanded meaningful seconds
- pressure accumulation
- micro-signal escalation
- scene crystallization

The guiding principle is:

```text
time moves when relation structure needs to be reevaluated,
and scenes occur when pressure can no longer remain distributed or latent.
```


