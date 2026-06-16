# RPF Storyteller Outline Rendering

## 0. Purpose

This document defines an intermediate rendering mode for RPF:

```text
Storyteller Outline Mode
```

It sits between diagnostic traces and literary prose.

The goal is to produce readable story narration without requiring full novel-level scene detail.

This is the recommended near-term rendering target.

---

## 1. Core Position

RPF currently has strong causal structure:

```text
field pressure
binding
affordance
action / inhibition / expression
recognition / misrecognition
memory reconstruction
irreversibility
derived relationship views
```

But full novel prose requires more:

```text
concrete scene actions
rich local details
object continuity
dialogue timing
sensory specificity
paragraph rhythm
scene blocking
```

If the system renders novel prose before those layers are mature, the LLM tends to:

- repeat the same objects and gestures
- add atmosphere without new story movement
- invent details that are not licensed
- turn causal traces into vague literary mood

Therefore, the next stable rendering target should be:

```text
storyteller outline
```

This mode narrates what happened, why it matters, how the relation changed, and what pressure carries forward.

---

## 2. Rendering Ladder

RPF should support three rendering levels.

### 2.1 Diagnostic Mode

Purpose:

```text
debugging, research, causal inspection
```

Output:

```text
events
metrics
traces
state deltas
source refs
```

Style:

```text
technical and explicit
```

### 2.2 Storyteller Outline Mode

Purpose:

```text
readable story understanding
```

Output:

```text
segment summary
what happened
why it happened
recognition / misrecognition
relationship change
memory or irreversible consequence
next pressure
source ticks
```

Style:

```text
clear narrated prose, like a storyteller, recap, or writer's room outline
```

### 2.3 Literary Prose Mode

Purpose:

```text
novel-like scene rendering
```

Output:

```text
scene prose
dialogue
gesture
sensory detail
limited perspective
paragraph rhythm
```

Style:

```text
fictional prose
```

Literary prose mode should depend on:

```text
validated narrative beats
attention-gated details
local-world constraints
segment protocol guard
```

Storyteller outline mode does not need all of these to be mature.

---

## 3. Why Outline First

Storyteller outline mode is better aligned with the current RPF architecture.

RPF already knows:

```text
which pattern activated
which recognition demand failed
which memory was reconstructed
which relationship phase changed
which future constraint appeared
```

It may not yet know:

```text
the exact gesture
the precise line of dialogue
the object condition
the room layout
the paragraph-level scene blocking
```

Outline mode can honestly narrate structure without pretending to have novel-level detail.

It can say:

```text
This segment did not resolve the conflict.
Instead, it made the claim harder to speak and pushed the relation toward repair avoidance.
```

This is more faithful than inventing a detailed scene to hide missing information.

---

## 4. Output Contract

A storyteller outline segment should use this structure:

```text
## Segment title

### What happened
Narrate the concrete event group at a summary level.

### Why it mattered
Explain the causal or relational significance.

### Recognition and misrecognition
Name the demand, response, displacement, refusal, postponement, or misunderstanding.

### Relationship movement
Describe phase movement, RPP stabilization, repair debt, trust/resentment projection, or binding pressure.

### Memory and irreversibility
Describe any memory reconstruction, operative label, lost alternative, or future constraint.

### Carry-forward pressure
Name what remains unresolved and what is likely to pressure the next segment.

(source ticks: ...)
```

Sections may be omitted if not relevant, but the output should always include:

```text
what happened
why it mattered
carry-forward pressure
source ticks
```

---

## 5. Input Contract

Outline rendering should consume:

```text
segment tick range
story frames
event summaries
recognition trace
memory trace
irreversibility trace
RPP activation and composition trace
relationship view
person views
local world summary if available
narrative beats if available
render repetition trace
```

It does not require:

```text
full local world detail
complete narrative beats
dialogue candidates
sensory profiles
causal world details
```

This makes it usable before the full novel-prose stack is implemented.

---

## 6. Style Rules

Storyteller outline should:

- be readable
- be specific about causal movement
- compress repeated events
- preserve uncertainty
- avoid fake novel detail
- avoid technical jargon unless useful
- explain why a segment matters
- name unresolved pressure

It should not:

- invent dialogue
- invent new objects
- invent new locations
- invent new memories
- add new evidence
- write long atmospheric descriptions
- pretend an unresolved matter was resolved
- repeat the same scene as if it were new

---

## 7. Repetition Handling

Outline mode should treat repetition as story information.

If several ticks repeat the same structure:

```text
same location
same active RPP
same recognition outcome
same unresolved claim
minor pressure changes only
```

the renderer should say:

```text
The same pattern continued.
Nothing decisive happened, but the cost of speaking increased.
```

It should not restage:

```text
the same silence
the same object
the same look
the same half-spoken line
```

Recommended repetition labels:

```text
pattern_continued
repair_window_narrowed
claim_remained_unofficial
avoidance_succeeded_short_term
memory_pressure_accumulated
public_risk_prevented_direct_speech
```

---

## 8. Relationship To Narrative Beats

Narrative beats are optional for outline mode.

If available, they improve specificity:

```text
record_not_written
failed_disclosure
interrupted_speech
route_blocked
missed_window
```

If unavailable, outline mode can still render from causal traces.

Recommended behavior:

```text
if narrative_beats exist:
    use them as concrete anchors
else:
    summarize from causal events and traces
```

This lets outline mode become useful immediately while remaining compatible with future novel rendering.

---

## 9. Relationship To LLM

LLM use is allowed, but the output contract is simpler than literary prose.

The LLM should be instructed:

```text
You are producing a narrated story outline, not novel prose.
Do not invent concrete details absent from input.
Compress repetition.
Explain causal movement.
Preserve unresolved uncertainty.
Use source ticks.
```

If the LLM violates the contract, fallback deterministic outline should be used.

Violations:

- new facts
- new dialogue
- new locations
- new evidence
- novel-style scene expansion beyond available detail
- missing source ticks
- repeated full previous segment

---

## 10. Deterministic Outline Fallback

A deterministic renderer should exist.

It should produce:

```text
segment title
tick range
dominant tick types
top RPPs
recognition outcome summary
memory reconstruction count
irreversibility count
relationship phase movement
carry-forward pressure
source ticks
```

This fallback is important because outline mode should be robust even when the LLM fails.

---

## 11. Segment Protocol

Storyteller outline segment output must obey:

```text
no document title unless this is the first full report
no previous segment rewrite
no complete story restart
source ticks must match current segment only
must not include raw JSON
must not include hidden chain-of-thought
```

Invalid:

```text
# Entire Story Title
Overview...
Segment 1...
Segment 2...
```

Valid:

```text
## Segment 4: Claim Remains Unofficial
...
(source ticks: 9-12)
```

---

## 12. Implementation Plan

### Phase 1: Deterministic Storyteller Outline

Use existing story frames and traces.

Acceptance:

```text
each segment has what happened / why it mattered / carry-forward pressure
no LLM required
repeated frames are compressed
source ticks are correct
```

### Phase 2: LLM Outline With Contract Guard

Add LLM rendering for outline mode.

Acceptance:

```text
LLM output follows outline sections
no novel-style invented detail
segment protocol guard rejects bad output
fallback deterministic outline works
```

### Phase 3: Narrative Beat Integration

Use validated beats when available.

Acceptance:

```text
outline mentions concrete beat types
beats cite source events
pattern continuation beats compress repetition
```

### Phase 4: Viewer Mode Selector

Expose render modes:

```text
diagnostic
storyteller_outline
literary_prose
```

Default should be:

```text
storyteller_outline
```

until literary prose mode has enough detail and beat support.

---

## 13. Evaluation Criteria

Outline mode succeeds when:

- users can follow the story
- causal movement is clear
- repetition is compressed
- unresolved pressure is explicit
- no unauthorized details appear
- segments do not restart the whole story
- it reads better than raw diagnostics
- it is more stable than premature novel prose

It fails when:

- it becomes a technical report only
- it invents novel scenes
- it repeats prior segments
- it hides causal uncertainty
- it omits why the segment matters
- it cannot name carry-forward pressure

---

## 14. Summary

RPF should not jump directly from causal traces to novel prose.

The near-term rendering target should be:

```text
Storyteller Outline Mode
```

This mode tells the story at the level the current simulator can support:

```text
what happened
why it mattered
what changed
what remained blocked
what pressure carries forward
```

It gives users a readable story without requiring the system to invent novel-level details before the detail and narrative-beat layers are mature.
