# RPF Validation and Evaluation Specification

## 0. Purpose

This document defines how to evaluate whether an RPF implementation is working.

The question is not:

```text
Did it produce an interesting story?
```

The question is:

```text
Did it generate person-like, relation-like, and fate-like structures from lower-level relational processes without smuggling them in as primitives?
```

---

## 1. Evaluation Levels

```text
1. Ontological Integrity
2. Runtime Integrity
3. Emergence Quality
4. Relational Plausibility
5. Dramatic Durability
6. Historical Irreversibility
7. LLM Boundary Integrity
8. Replay and Auditability
```

---

## 2. Ontological Integrity

The implementation passes if:

- PersonView is derived
- RelationshipView is derived
- trust/intimacy/dependency are aggregates
- labels become causal only through OperativeClassificationEvent
- RPPs are not personality traits
- scenes require binding or field pressure

Failure examples:

- `person.personality = avoidant`
- `relationship.trust -= 0.2`
- LLM says "A became jealous" and state changes
- scene appears because plot needs it

---

## 3. Runtime Integrity

Pass criteria:

- every tick emits events or latent-time explanation
- every state mutation has event source
- replay reconstructs same state
- randomness is seeded and recorded
- derived views include evidence refs
- irreversible records define future constraints

Tests:

```text
test_replay_determinism
test_no_direct_view_mutation
test_event_refs_valid
test_irreversibility_has_constraints
test_scene_has_binding_reason
```

---

## 4. Emergence Quality

The system should produce:

- recognizable person-like patterns not fully predefined
- relation-specific selves
- stable response tendencies
- labels that arise after repeated evidence
- changed action spaces after history

Metrics:

```text
trait_predefinition_ratio
stabilized_pattern_count
label_evidence_depth
relation_specific_variance
unavailable_action_growth
```

### 4.1 Trait Predefinition Ratio

```text
trait_predefinition_ratio =
  number_of_person_labels_in_initial_scenario
  / number_of_person_labels_after_simulation
```

Lower is better.

Initial scenarios should avoid trait labels entirely.

---

## 5. Relational Plausibility

A relation is plausible when:

- continued encounter has structural explanation
- misunderstandings are patterned, not random
- repair exists but is limited
- power and exit asymmetry matter
- public/private definitions may diverge
- field conditions shape perception and speech

Metrics:

```text
binding_explanation_rate
misrecognition_recurrence_score
repair_attempt_rate
repair_success_rate
exit_asymmetry_effect_size
field_to_relevance_trace_rate
```

---

## 6. Dramatic Durability

Long-term drama should emerge from contradictions, not forced plot.

Evaluate:

- recognition demands remain active across episodes
- repair lowers pressure without erasing history
- repeated RPPs evolve rather than loop mechanically
- conflict can go latent and return
- scenes remain necessary

Metrics:

```text
recognition_pressure_persistence
repair_debt_carryover
rpp_phase_variation
latent_tension_duration
scene_necessity_score
```

---

## 7. Historical Irreversibility

The simulation should show path dependency.

Pass criteria:

- irreversible events reduce or reshape future options
- past events can be reclassified
- labels can lock in
- public commitments matter
- lost alternatives are tracked

Metrics:

```text
irreversibility_count
future_constraint_density
lost_alternative_count
reclassification_count
lock_in_strength
```

---

## 8. LLM Boundary Integrity

Pass criteria:

- all LLM output is schema-validated
- invalid LLM output is rejected or repaired
- rendering never mutates causal state
- dialogue candidates are selected by simulator
- LLM does not invent unavailable facts

Tests:

```text
test_llm_cannot_mutate_state
test_invalid_llm_output_rejected
test_rendering_event_noncausal
test_candidate_selection_owned_by_simulator
```

---

## 9. Evaluation Artifacts

Each simulation run should produce:

```text
timeline.jsonl
snapshots/
derived_views.json
aggregation_traces.json
irreversibility_report.json
operative_classification_report.json
metrics.json
rendered_scenes.md optional
```

---

## 10. Human Review Questions

Human evaluators should ask:

- Did this person-like pattern feel produced rather than assigned?
- Can I trace a label back to repeated evidence?
- Did the relationship continue for structural reasons?
- Did the environment enter perception and action?
- Did repair change the future without deleting injury?
- Did the same event mean different things to different positions?
- Did irreversible history actually narrow future scenes?
- Did the LLM merely render, or did it secretly author causality?

---

## 11. Red Flags

The simulation is failing if:

- characters behave according to fixed labels
- scenes feel scheduled by plot
- relationship variables explain behavior
- conflict always escalates
- repair is impossible or magical
- memory is a passive log
- field is just background
- labels have no social uptake but still change behavior
- LLM prose introduces facts that later become state

---

## 12. Acceptance Threshold for MVP

An MVP passes if it can demonstrate:

```text
1. Two process positions remain co-present for structural reasons.
2. At least three RPPs activate with evidence.
3. At least one derived PersonView label emerges from repeated patterns.
4. At least one label becomes operative through uptake.
5. At least one irreversible event changes future action availability.
6. Replay reconstructs the same state.
7. LLM rendering can be disabled without breaking simulation.
```

---

## 13. Scientific Attitude

Do not evaluate the system by whether it flatters the theory.

Evaluate whether it resists its own easiest failure mode:

```text
turning emergent social processes back into character traits.
```


