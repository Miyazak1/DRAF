# RPF Implementation Readiness Audit

## 0. Purpose

This document audits whether the current RPF documentation set is sufficient to begin implementation and identifies remaining gaps.

Audit date:

```text
2026-06-10
```

Conclusion:

```text
RPF is ready to begin MVP implementation.
No additional document is required before coding the MVP kernel.
However, several documents should be added before expanding beyond MVP.
```

---

## 1. Current Documentation Coverage

The current documentation set covers:

```text
ontology
technical architecture
formal data model
simulation runtime
RPP library
aggregation and projection
event taxonomy
LLM boundary
scenario authoring
validation and evaluation
MVP build plan
```

This is enough to start the first executable simulator slice.

---

## 2. MVP-Blocking Gaps

### Result

```text
None.
```

The MVP build can begin with the current documents.

Required MVP decisions are already specified:

- package structure
- model subset
- three initial RPPs
- tick pipeline
- example scenario
- required events
- derived views
- operative classification path
- irreversibility path
- CLI commands
- tests
- milestones

---

## 3. Important Non-Blocking Gaps

These are not required before MVP coding, but they should be documented before the system becomes larger.

---

## 4. Gap: Schema Versioning and Migration

### Why It Matters

RPF is event-sourced. Once simulations exist, schema changes can break replay.

### Missing Document

```text
docs/rpf-schema-versioning-and-migration.md
```

### Should Define

- schema version fields
- event versioning
- snapshot versioning
- migration strategy
- backward-compatible replay
- deprecated fields
- migration tests

### Priority

```text
High after MVP skeleton.
```

Not needed before the first throwaway MVP, but needed before preserving real experiment runs.

---

## 5. Gap: Configuration Reference

### Why It Matters

Scenario authoring exists, but there is no complete config reference with all allowed keys, defaults, ranges, and validation errors.

### Missing Document

```text
docs/rpf-configuration-reference.md
```

### Should Define

- scenario config keys
- runtime config keys
- RPP override keys
- output config keys
- random seed behavior
- default values
- allowed ranges
- validation errors

### Priority

```text
Medium.
```

MVP can start without it because the MVP scenario is narrow.

---

## 6. Gap: Calibration and Parameter Semantics

### Why It Matters

The documents use bounded floats such as `0.7`, but do not yet define what those values mean operationally.

Without calibration, parameters can become arbitrary knobs.

### Missing Document

```text
docs/rpf-calibration-guide.md
```

### Should Define

- what `0.0`, `0.5`, and `1.0` mean for each parameter family
- default distributions
- scenario authoring heuristics
- sensitivity analysis
- calibration examples
- anti-patterns

### Priority

```text
High before serious experiments.
```

MVP can use simple hand-tuned values.

---

## 7. Gap: Observability and Debugging

### Why It Matters

RPF will be hard to debug because behavior emerges through layered aggregation.

The current docs mention diagnostics but do not define a complete observability strategy.

### Missing Document

```text
docs/rpf-observability-debugging.md
```

### Should Define

- required logs
- event trace views
- aggregation trace views
- RPP activation trace
- randomness trace
- replay diff
- state hash comparison
- invariant failure reports
- debugging workflow

### Priority

```text
Medium-high.
```

Useful during MVP, but the current event and metrics specs are enough to begin.

---

## 8. Gap: Ethics, Safety, and Use Boundaries

### Why It Matters

RPF simulates intimate, coercive, dependent, and psychologically charged relations. This creates risks:

- users may treat simulations as diagnoses
- users may model real people without consent
- the system may generate manipulative relationship strategies
- sensitive scenarios may involve abuse, coercion, trauma, or self-harm

### Missing Document

```text
docs/rpf-ethics-and-safety.md
```

### Should Define

- acceptable use
- prohibited use
- consent assumptions
- real-person modeling boundaries
- abuse and coercion handling
- non-diagnostic disclaimer
- data retention guidance
- safe rendering limits

### Priority

```text
High before any user-facing release.
```

Not blocking private MVP kernel development.

---

## 9. Gap: Research Benchmark Set

### Why It Matters

The validation document defines metrics, but there is not yet a benchmark scenario suite.

### Missing Document

```text
docs/rpf-benchmark-scenarios.md
```

### Should Define

At least five benchmark scenarios:

- shared apartment unresolved sacrifice
- workplace dependency and public/private split
- family obligation and double bind
- long-distance silence interpretation
- caretaker/dependent complementary dependency

Each benchmark should define expected emergent patterns, not expected plot.

### Priority

```text
Medium.
```

Needed after the first MVP scenario works.

---

## 10. Gap: Branching and Counterfactual Experiments

### Why It Matters

RPF is especially valuable if it can branch at irreversible moments and compare possible futures.

The event taxonomy mentions branching, but there is no operational design yet.

### Missing Document

```text
docs/rpf-branching-counterfactuals.md
```

### Should Define

- branch creation
- parent-child simulation lineage
- counterfactual intervention
- comparison metrics
- replay divergence analysis
- fate compression measurement

### Priority

```text
Low for MVP, high for research value.
```

---

## 11. Gap: Persistence Backend Design

### Why It Matters

The technical plan now targets PostgreSQL for durable cloud persistence. The schema and migration path are defined, but the runtime still writes files first.

### Reference Document

```text
docs/rpf-postgresql-persistence-plan.md
```

### Implementation Should Add

- PostgreSQL migrations
- a storage interface
- dual-write from file output to PostgreSQL
- indexes
- JSON payload format
- snapshot storage
- event stream storage
- export/import

### Priority

```text
Low before file-based MVP.
Medium before multi-run experiments.
```

---

## 12. Gap: Renderer Style and Narrative Policy

### Why It Matters

The LLM contract defines boundaries but not the intended narrative style.

Without a rendering policy, output may become melodramatic, over-explanatory, diagnostic, or too omniscient.

### Missing Document

```text
docs/rpf-rendering-style-guide.md
```

### Should Define

- perspective discipline
- no omniscient diagnosis
- how to render silence
- how to render ambiguity
- how to avoid explaining the simulator
- scene prose style
- dialogue style
- summary style

### Priority

```text
Low for non-LLM MVP.
High before LLM rendering.
```

---

## 13. Gap: Test Matrix

### Why It Matters

The validation document names important tests, but there is no test matrix mapping features to test files.

### Missing Document

```text
docs/rpf-test-matrix.md
```

### Should Define

- unit tests
- integration tests
- replay tests
- scenario tests
- invariant tests
- LLM contract tests
- regression tests
- required fixtures

### Priority

```text
Medium.
```

Could be written during first implementation pass.

---

## 14. Recommended Next Step

Do not write all non-blocking documents before coding.

Recommended sequence:

```text
1. Start MVP implementation from rpf-mvp-build-plan.md.
2. As soon as event schemas exist in code, add schema versioning.
3. As soon as output traces become hard to inspect, add observability/debugging.
4. Before preserving serious runs, add persistence backend and migration docs.
5. Before any user-facing release, add ethics/safety and rendering style guide.
6. After first scenario works, add benchmark scenarios and calibration guide.
```

---

## 15. Final Readiness Verdict

```text
Implementation readiness for MVP: YES.
Implementation readiness for research-grade system: NOT YET.
Implementation readiness for user-facing product: NO.
```

The current document set is mature enough to begin building the simulator kernel.

The main remaining risk is not missing theory. It is implementation drift:

```text
accidentally letting high-level views, labels, or LLM prose become causal state.
```

The MVP should therefore prioritize invariants, event sourcing, and replay before any visual or narrative polish.


