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

Read next:

```text
rpf-relational-viability-process-framework.md
```

Defines the deeper substrate beneath conflict: constrained relational viability, viability requirements, affordance width, adaptive response, deformation, stabilization, and derived drama.

### 2. Technical Strategy

Read second:

```text
rpf-technical-implementation-plan.md
```

Defines the recommended stack, event-sourced simulator, LLM boundary, implementation phases, and technical invariants.

### 3. Dramatic Conflict Framework

Read after the core ontology and relational viability framework, before implementing new conflict modes:

```text
rpf-dramatic-conflict-framework.md
```

Defines the unified conflict kernel: constraint fields, blocked capacities, dramatic contradictions, expression deformation, and the first implementable recognition-conflict mode.

### 4. Bounded Local World

Read before expanding environmental realism or local-world scenario design:

```text
rpf-bounded-local-world.md
```

Defines the finite physical-social field: locations, routes, rhythms, resources, audiences, institutions, memory sites, ecological constraints, and boundary rules.

### 5. Object, Record, and Evidence Registry

Read before implementing narrative beats, evidence scenes, or object-grounded rendering:

```text
rpf-object-record-evidence-registry.md
```

Defines durable material anchors: world objects, records, evidence, messages, access tokens, custody, object state, record authority, and evidence access.

### 6. Attention-Gated World Elaboration

Read before using LLMs to generate local environmental details:

```text
rpf-attention-gated-world-elaboration.md
```

Defines attention-gated local detail generation, persistence policy, soft world profiles, causal world details, and controlled prompt injection.

### 7. Narrative Event Realization

Read before trying to render novel-like scenes:

```text
rpf-narrative-event-realization.md
```

Defines the middle layer from causal events to concrete narrative beats: intended action, obstruction, realized action, observation, consequence, and pattern continuation.

### 8. Storyteller Outline Rendering

Read before implementing user-facing story rendering:

```text
rpf-storyteller-outline-rendering.md
```

Defines the intermediate rendering mode between diagnostics and novel prose: narrated outline segments that explain what happened, why it mattered, what changed, and what pressure carries forward.

### 9. Formal Data Model

Read before writing code:

```text
rpf-formal-data-model.md
```

Defines the implementable objects: `SimulationState`, `FieldState`, `ProcessState`, `RPP`, `SceneState`, `Event`, `PersonView`, and `RelationshipView`.

### 10. Runtime

Read before implementing the engine:

```text
rpf-simulation-runtime.md
```

Defines tick lifecycle, episode lifecycle, scene crystallization, RPP activation, recognition evaluation, stabilization, irreversibility, and replay.

### 11. RPP Library

Read before authoring dynamics:

```text
rpf-rpp-library.md
```

Defines how relational process patterns are structured and gives the initial required pattern library.

### 12. Aggregation and Projection

Read before implementing derived views:

```text
rpf-aggregation-projection.md
```

Defines how lower-level process data aggregates into `TrustView`, `IntimacyView`, `DependencyView`, `PersonView`, and `RelationshipView`.

### 13. Event System

Read before implementing persistence:

```text
rpf-event-taxonomy.md
```

Defines event schemas, event categories, payload contracts, timeline requirements, and invalid event patterns.

### 14. LLM Boundary

Read before connecting any model:

```text
rpf-llm-contract.md
```

Defines what the LLM may and may not do, prompt contracts, output schemas, validation rules, and failure handling.

### 15. Scenario Authoring

Read before writing simulations:

```text
rpf-scenario-authoring.md
```

Defines how to author scenarios without predefined personalities or plots.

### 16. Validation and Evaluation

Read before declaring the simulator successful:

```text
rpf-validation-evaluation.md
```

Defines ontological integrity tests, runtime integrity tests, emergence metrics, relational plausibility checks, and MVP acceptance thresholds.

### 17. MVP Build Plan

Read immediately before writing code:

```text
rpf-mvp-build-plan.md
```

Defines the first executable implementation slice: exact MVP scope, initial file tree, model subset, three initial RPPs, one demonstration scenario, CLI commands, tests, milestones, and acceptance criteria.

### 18. Implementation Readiness Audit

Read when deciding whether to code or continue documenting:

```text
rpf-implementation-readiness-audit.md
```

Identifies which documents are sufficient for MVP implementation and which non-blocking documents should be added before research-grade or user-facing expansion.

### 19. Expression and Personhood Extensions

Read after the MVP architecture is understood:

```text
rpf-expression-and-personhood-extensions.md
```

Defines post-MVP mechanisms for generating concrete person-like expression: language style, bodily expression, habits, rituals, desire, taste, relation-specific selves, and expressive continuity.

### 20. Temporal Scheduler and Scene Selection

Read before implementing tick scheduling:

```text
rpf-temporal-scheduler-and-scene-selection.md
```

Defines how the simulator chooses latent, micro-interaction, or scene ticks; how simulated time maps to each tick; and how scenes crystallize from field pressure, bindings, relevance, RPP dynamics, and spatial/temporal constraints.

### 21. Cloud Deployment

Read before putting the web workbench on a cloud server:

```text
cloud-deployment-ubuntu.md
```

Defines the recommended Ubuntu, Python venv, Nginx, systemd, HTTPS, API-key, and output-storage setup for online testing.

---

## Implementation Order

Recommended build sequence:

```text
1. Pydantic data models
2. Event stream and deterministic replay
3. Runtime tick pipeline
4. Trace-only relational viability kernel
5. Trace-only conflict evidence kernel
6. Trace-only local world
7. Read-only object, record, and evidence registry
8. Segment protocol guard and render repetition trace
9. Deterministic storyteller outline renderer
10. Deterministic narrative beat builder
11. Pattern continuation and narrative beat compression
12. Render-only attention-gated detail elaboration
13. LLM outline renderer with contract guard
14. RPP eligibility and activation
15. Scene crystallization
16. Recognition and misrecognition engine
17. Recognition-conflict integration
18. Local-world constraint integration
19. Registry access events and active object/evidence projection
20. Soft world profiles and causal detail activation
21. Stabilization and irreversibility engine
22. Aggregation and projection
23. Scenario loader
24. LLM rendering boundary
25. Metrics and validation
26. Inspector UI
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
examples/yellow_sign_cold_case.yaml
```

Run them with:

```text
python -m rpf run examples/shared_apartment_unresolved_sacrifice.yaml --steps 30 --seed 42
python -m rpf run examples/workplace_public_private_split.yaml --steps 30 --seed 7
python -m rpf run examples/family_double_bind.yaml --steps 30 --seed 101
python -m rpf run examples/yellow_sign_cold_case.yaml --steps 40 --seed 42
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

## Web Workbench

For interactive use, start the local workbench:

```text
start_viewer.bat
```

The page opens at:

```text
http://127.0.0.1:8765/
```

The workbench can:

- list all scenario files under `examples/`
- create custom two-process scenarios from the web workbench
- load a scenario and generate an initial preview run
- keep a run archive instead of overwriting previous web runs
- reopen historical runs from the archive
- compare the current run against archived runs
- generate deterministic run reports as Markdown
- export a run bundle as a zip archive
- run continuous simulation for a real wall-clock duration
- choose deterministic or DeepSeek LLM automatic segment rendering
- append closed narrative segments into the live story stream
- visualize pressure curves and phase trajectories over the whole run
- inspect derived relationship views, RPP dynamics, traces, and raw events

In the continuous simulation panel, duration means real-world runtime. Selecting `18 hours` means the local backend keeps running for 18 real hours unless stopped or the max tick limit is reached. The tick interval controls how often the simulator advances during that wall-clock window.

Web-created runs are stored under:

```text
out/experience/runs/<scenario_id>/<timestamp>_<mode>_seed<seed>_<id>/
```

The workbench writes a `run_metadata.json` file into each run directory. The `运行档案` panel reads those manifests and can reopen older runs without mutating them.

Custom scenarios created in the workbench are written as YAML files under:

```text
examples/custom_<scenario_id>.yaml
```

They contain the same causal fields as handwritten scenarios: render canon, field state, relation metrics, process constraints, bindings, and recognition demands.

The `生成报告` action writes:

```text
run_report.md
```

inside the current run directory. The report is deterministic and does not call an LLM.

The `导出运行包` action writes a zip archive in the current run directory. The bundle includes the deterministic report, event stream, derived views, metrics, traces, render canon, rendered story files when present, and run metadata.

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
9. Conflict must be traceable to constraint and blocked-capacity evidence.
10. Scenario conflict seeds define pressures, not plot outcomes.
11. Viability requirements are process requirements, not character desires.
12. Drama is derived from constrained relational viability.
13. Every simulation must define a bounded local world.
14. New locations, public consequences, and offscreen events require traceable local-world evidence.
15. Durable objects, records, evidence, messages, and custody changes require registry refs or events.
16. Object access is separate from object existence.
17. Record authority is separate from record existence.
18. Evidence access is separate from evidence truth.
19. LLM-generated details are proposals, not causal facts.
20. No attention, no world elaboration.
21. Narrative beats may realize but not change causal outcomes.
22. Narrative beats using durable things should cite registry refs.
23. Novel-like rendering must be grounded in validated narrative beats.
24. Storyteller outline is the default near-term user-facing rendering target.
25. Literary prose must not be the default until detail and beat layers are mature.
```

