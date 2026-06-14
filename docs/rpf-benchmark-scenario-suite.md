# RPF Benchmark Scenario Suite

## 0. Purpose

This document defines the benchmark scenario suite for RPF.

The scenarios are not story prompts. They are pressure tests for the simulator.

Each benchmark asks:

```text
Can the same lower-level RPF mechanisms generate plausible relational dynamics in a different field, binding structure, medium, and recognition economy?
```

The suite exists to prevent overfitting to one relationship type.

---

## 1. Benchmark Contract

Every benchmark scenario must define:

- field pressures
- two process positions
- at least two co-presence bindings
- at least one recognition demand
- one primary structural contradiction
- expected RPP susceptibility
- no primitive personality labels
- no plot sequence

Every benchmark run should produce:

- all three tick types over 30 steps
- situated affordance trace for non-latent ticks
- action selection trace for non-latent ticks
- expression trace for non-latent ticks
- recognition outcome trace for scene ticks
- fate transition trace when structural thresholds are crossed
- memory reconstruction trace when events become remembered history
- at least two RPP activations
- non-empty derived PersonView or RelationshipView
- replayable event stream
- scheduler diagnostics
- RPP activation trace
- projection trace
- cumulative RPP activation score sums

---

## 1.1 Scenario-Sensitive Dynamics

Benchmarks should not all converge to the same phase.

Each scenario may define initial relation metrics:

```yaml
relation_metrics:
  unrecognized_contribution: 0.46
  conflict_pressure: 0.08
  repair_debt: 0.0
  repair_debt_growth: 0.2
  irreversibility_threshold: 1.1
  locked_in_repair_threshold: 0.9
  cold_war_repair_threshold: 0.3
```

These values are not personality traits. They define the initial structural pressure and escalation thresholds for the relation.

The suite should contain different trajectories:

- some scenarios become `locked-in`
- some remain `cold-war`
- some stay `repair-avoidant`
- not every scenario should produce an irreversible event

If every scenario converges to the same phase, the benchmark suite is not diagnostic enough.

The same rule applies to RPP dominance. A benchmark suite is weak if every scenario has the same dominant RPP. The current acceptance target is not perfect coverage of every RPP, but multi-attractor differentiation across the suite.

The same rule also applies to affordances. If every scenario selects the same dominant affordance, the simulator has not escaped prompt-like scene generation.

---

## 2. Current Suite

```text
01 shared_apartment_unresolved_sacrifice
02 workplace_public_private_split
03 family_double_bind
04 caretaker_dependency_loop
05 long_distance_silence_interpretation
06 mentor_protege_symbolic_debt
07 ex_partners_shared_social_circle
08 immigrant_parent_child_translation_burden
09 artistic_collaboration_credit_conflict
10 medical_care_decision_conflict
11 secret_affair_public_performance
12 childhood_friends_class_divergence
```

---

## 3. Scenario Matrix

| Scenario | Primary Binding | Primary Field | Core Test |
| --- | --- | --- | --- |
| shared_apartment_unresolved_sacrifice | lease + debt | domestic/material | unrecognized contribution becomes relational debt |
| workplace_public_private_split | project + status | workplace/institutional | public competence hides private resentment |
| family_double_bind | kinship + obligation | family/cultural | incompatible demands block direct speech |
| caretaker_dependency_loop | care + bodily need | domestic/medical | care stabilizes dependence and resentment |
| long_distance_silence_interpretation | message delay + future promise | mediated/intimate | absence and latency become relational signs |
| mentor_protege_symbolic_debt | symbolic capital + career access | education/professional | gratitude becomes control and separation anxiety |
| ex_partners_shared_social_circle | friend network + reputation | social/public | separation fails because audience keeps relation alive |
| immigrant_parent_child_translation_burden | family role + language | migration/cultural | child-position and interpreter-position conflict |
| artistic_collaboration_credit_conflict | shared work + authorship | creative/field | credit, taste, and control become recognition struggle |
| medical_care_decision_conflict | care authority + bodily vulnerability | medical/family | agency and protection conflict |
| secret_affair_public_performance | secrecy + public role | social/moral | private binding and public fiction diverge |
| childhood_friends_class_divergence | old identity + class divergence | class/history | old recognition fails under new social positions |

---

## 4. Expected Cross-Suite Evidence

The suite should show that RPF can represent:

- material binding
- institutional binding
- kinship binding
- care binding
- mediated absence
- symbolic debt
- audience pressure
- translation burden
- authorship conflict
- bodily vulnerability
- secrecy
- class reclassification

The simulator is improving when the same RPPs surface differently across fields.

Example:

```text
pursuit_withdrawal
- apartment: "why won't you talk about what I paid?"
- workplace: "why won't you answer the status question?"
- long distance: "why did you leave me on read?"
- family: "why do you disappear when I ask you to choose?"
```

---

## 5. Acceptance Standard

A benchmark scenario passes MVP-level validation when:

- `python -m rpf run ... --steps 30` completes
- `python -m rpf replay .../timeline.jsonl` succeeds
- output includes `effective_config.json`
- output includes diagnostics and traces
- at least two RPPs activate
- projection events occur for every tick
- derived views contain evidence-backed labels or phase

The current research-kernel suite additionally requires:

- benchmark replay succeeds for every scenario
- dominant affordance distribution contains at least four affordance types across the suite
- dominant recognition outcome distribution contains multiple outcome types across the suite
- dominant RPP distribution contains at least five RPP types across the suite
- dominant composition distribution contains at least five composition types across the suite
- at least one scenario produces irreversibility
- at least one scenario avoids irreversibility
- `rpp_activation_score_sums` is present for every scenario
- `rpp_composition_score_sums` is present for every scenario
- `affordance_trace.json` is present for every scenario
- `action_trace.json` is present for every scenario
- `expression_trace.json` is present for every scenario
- `recognition_trace.json` is present for every scenario
- `fate_transition_trace.json` is present for every scenario
- `memory_trace.json` is present for every scenario
- dominant operative label distribution is non-empty across the suite
- dominant irreversibility category distribution is non-empty across the suite
- dominant memory bias distribution is non-empty across the suite
- dominant action distribution is non-empty across the suite
- dominant action mode distribution is non-empty across the suite
- dominant expression distribution is non-empty across the suite
- dominant expression mode distribution is non-empty across the suite
- at least one scenario produces action inhibition or action substitution
- at least one scenario emits `RPPSuppressionEvent`
- at least one scenario emits `RPPDecayEvent`

Dominant RPP is based on cumulative activation score, not raw activation count.

Dominant composition is based on cumulative composition score.

The benchmark fails if:

- it requires hard-coded plot behavior
- it only works by adding primitive personality labels
- it cannot produce replayable timeline
- it uses PersonView or RelationshipView as causal input

