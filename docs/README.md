# RPF Documentation Index

This folder contains the design documents for RPF: Relational Process Field.

RPF replaces a person-first simulation model with a process-first model:

```text
Field
-> Process
-> Coupling
-> Scene
-> Observation
-> Recognition
-> Stabilization
-> Person
-> Fate
```

The implementation must preserve one invariant:

```text
Person, Relationship, Trust, Intimacy, Resentment, and Personality are derived views.
They are not primitive causal variables.
```

---

## Reading Order

### 1. Theory and Ontology

Read first:

```text
relational-process-field-architecture.md
```

Defines the RPF ontology, recursive layered aggregation, and the reversal from "people form relationships" to "relational processes stabilize into people".

### 2. Technical Strategy

Read second:

```text
rpf-technical-implementation-plan.md
```

Defines the recommended stack, event-sourced simulator, LLM boundary, implementation phases, and technical invariants.

### 3. Formal Data Model

Read before writing code:

```text
rpf-formal-data-model.md
```

Defines the implementable objects: `SimulationState`, `FieldState`, `ProcessState`, `RPP`, `SceneState`, `Event`, `PersonView`, and `RelationshipView`.

### 4. Runtime

Read before implementing the engine:

```text
rpf-simulation-runtime.md
```

Defines tick lifecycle, episode lifecycle, scene crystallization, RPP activation, recognition evaluation, stabilization, irreversibility, and replay.

### 5. RPP Library

Read before authoring dynamics:

```text
rpf-rpp-library.md
```

Defines how relational process patterns are structured and gives the initial required pattern library.

### 6. Aggregation and Projection

Read before implementing derived views:

```text
rpf-aggregation-projection.md
```

Defines how lower-level process data aggregates into `TrustView`, `IntimacyView`, `DependencyView`, `PersonView`, and `RelationshipView`.

### 7. Event System

Read before implementing persistence:

```text
rpf-event-taxonomy.md
```

Defines event schemas, event categories, payload contracts, timeline requirements, and invalid event patterns.

### 8. LLM Boundary

Read before connecting any model:

```text
rpf-llm-contract.md
```

Defines what the LLM may and may not do, prompt contracts, output schemas, validation rules, and failure handling.

### 9. Scenario Authoring

Read before writing simulations:

```text
rpf-scenario-authoring.md
```

Defines how to author scenarios without predefined personalities or plots.

### 10. Validation and Evaluation

Read before declaring the simulator successful:

```text
rpf-validation-evaluation.md
```

Defines ontological integrity tests, runtime integrity tests, emergence metrics, relational plausibility checks, and MVP acceptance thresholds.

### 11. MVP Build Plan

Read immediately before writing code:

```text
rpf-mvp-build-plan.md
```

Defines the first executable implementation slice: exact MVP scope, initial file tree, model subset, three initial RPPs, one demonstration scenario, CLI commands, tests, milestones, and acceptance criteria.

### 12. Implementation Readiness Audit

Read when deciding whether to code or continue documenting:

```text
rpf-implementation-readiness-audit.md
```

Identifies which documents are sufficient for MVP implementation and which non-blocking documents should be added before research-grade or user-facing expansion.

### 13. Expression and Personhood Extensions

Read after the MVP architecture is understood:

```text
rpf-expression-and-personhood-extensions.md
```

Defines post-MVP mechanisms for generating concrete person-like expression: language style, bodily expression, habits, rituals, desire, taste, relation-specific selves, and expressive continuity.

### 14. Temporal Scheduler and Scene Selection

Read before implementing tick scheduling:

```text
rpf-temporal-scheduler-and-scene-selection.md
```

Defines how the simulator chooses latent, micro-interaction, or scene ticks; how simulated time maps to each tick; and how scenes crystallize from field pressure, bindings, relevance, RPP dynamics, and spatial/temporal constraints.

---

## Implementation Order

Recommended build sequence:

```text
1. Pydantic data models
2. Event stream and deterministic replay
3. Runtime tick pipeline
4. RPP eligibility and activation
5. Scene crystallization
6. Recognition and misrecognition engine
7. Stabilization and irreversibility engine
8. Aggregation and projection
9. Scenario loader
10. LLM rendering boundary
11. Metrics and validation
12. Inspector UI
```

---

## Current Runnable Benchmarks

The repository currently includes these runnable MVP benchmark scenarios:

```text
examples/shared_apartment_unresolved_sacrifice.yaml
examples/workplace_public_private_split.yaml
examples/family_double_bind.yaml
examples/caretaker_dependency_loop.yaml
examples/long_distance_silence_interpretation.yaml
examples/mentor_protege_symbolic_debt.yaml
examples/ex_partners_shared_social_circle.yaml
examples/immigrant_parent_child_translation_burden.yaml
examples/artistic_collaboration_credit_conflict.yaml
examples/medical_care_decision_conflict.yaml
examples/secret_affair_public_performance.yaml
examples/childhood_friends_class_divergence.yaml
```

Run them with:

```text
python -m rpf run examples/shared_apartment_unresolved_sacrifice.yaml --steps 30 --seed 42
python -m rpf run examples/workplace_public_private_split.yaml --steps 30 --seed 7
python -m rpf run examples/family_double_bind.yaml --steps 30 --seed 101
```

Replay outputs with:

```text
python -m rpf replay out/shared_apartment_unresolved_sacrifice/timeline.jsonl
python -m rpf replay out/workplace_public_private_split/timeline.jsonl
```

Run the full benchmark suite with:

```text
python -m rpf benchmark examples --steps 30 --out out/benchmarks
```

This writes:

```text
out/benchmarks/benchmark_summary.json
out/benchmarks/benchmark_summary.md
out/benchmarks/runs/<scenario_id>/
```

---

## Non-Negotiable Invariants

```text
1. PersonView is derived.
2. RelationshipView is derived.
3. Trust, intimacy, dependency, resentment, power asymmetry, and personality are aggregates.
4. Labels become causal only through OperativeClassificationEvent.
5. LLM rendering never mutates causal state.
6. Scenes require binding, field pressure, or latent tension.
7. Irreversible events must define future constraints.
8. Replay from initial state and event stream must reconstruct causal state.
```

