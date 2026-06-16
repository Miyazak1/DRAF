# RPF Narrative Event Realization

## 0. Purpose

This document defines the missing middle layer between causal simulation events and literary rendering.

Current RPF can produce strong causal structure:

```text
RecognitionEvent
MemoryReconstructionEvent
FieldPressureEvent
AffordanceSelectionEvent
ExpressionSelectionEvent
IrreversibilityEvent
```

But a novel-like scene cannot be rendered well from abstract causal events alone.

Literary rendering needs concrete narrative action:

```text
who did what
where
with which object
under what interruption
who observed it
what was not said
what changed afterward
```

This layer is called:

```text
Narrative Event Realization
```

Its job is:

```text
causal event -> narrative beat -> prose rendering
```

The LLM should render prose from narrative beats, not directly from raw state summaries.

---

## 1. Core Thesis

RPF should distinguish three levels:

```text
1. Causal Event
   What changed in the simulation.

2. Narrative Beat
   How that change appeared as situated action, omission, interruption, object use, observation, or failed attempt.

3. Literary Rendering
   How the beat is written as prose.
```

Current rendering often jumps from level 1 to level 3.

That causes prose to become:

- abstract
- repetitive
- atmospheric without action
- diagnostic rather than dramatic
- dependent on the same few objects and gestures

The fix is not only "more detail."

The fix is:

```text
give the renderer concrete narrative beats.
```

---

## 2. Relationship To Existing Layers

### 2.1 Causal Runtime

The causal runtime owns:

```text
state changes
event validity
recognition outcomes
RPP activation
memory reconstruction
irreversibility
affordance availability
```

Narrative realization must not change these outcomes.

### 2.2 Attention-Gated World Elaboration

Attention-gated elaboration supplies local perceptual and object detail:

```text
the label is damp
the corridor carries footsteps
the window latch is painted shut
the market crowd blocks a direct conversation
```

Narrative realization uses those details to form beats:

```text
she tries to read the label but the water-warped ink delays her answer
he stops speaking because footsteps pass outside the door
she reaches for the window and finds it stuck
he turns the accusation into a joke because the market crowd is listening
```

### 2.3 Object, Record, and Evidence Registry

Durable things used by narrative beats must come from the registry.

```text
object_refs, record_refs, and evidence_refs are registry references.
They are not free prose nouns.
```

If a beat needs a file, bill, tape, key, note, phone, report, message, weapon, or evidence bag, that item must be:

```text
registered
discovered by event
or validated as a causal world detail before use
```

### 2.4 LLM Rendering

The LLM should receive:

```text
narrative beats
allowed local details
forbidden facts
causal outcomes
perspective constraints
```

The LLM may choose prose rhythm, imagery, sentence order, and surface description.

It may not invent the beat's causal consequence.

---

## 3. Narrative Beat

A `NarrativeBeat` is the smallest renderable dramatic unit.

It is not merely an event summary. It is a situated action or non-action licensed by causal state.

```text
NarrativeBeat
- beat_id
- tick
- beat_type
- source_events
- location_id
- time_window
- participants
- focal_process
- intended_action optional
- realized_action optional
- inhibited_action optional
- substituted_action optional
- object_refs
- record_refs
- evidence_refs
- local_detail_refs
- obstruction
- observation
- recognition_implication
- outcome
- unresolved_remainder
- rendering_constraints
```

The beat must answer:

```text
What tried to happen?
What actually happened?
Why did it take that form?
Who noticed?
What changed or remained blocked?
```

---

## 4. Beat Types

Initial beat types:

```text
failed_disclosure
delayed_answer
object_handling
interrupted_speech
practical_substitution
public_mask
private_withdrawal
route_blocked
evidence_misread
record_not_written
repair_attempt
repair_displaced
recognition_claim
recognition_refusal
memory_intrusion
attention_fixation
audience_pressure_shift
threshold_crossing
irreversible_utterance
missed_window
```

These are not genre tropes. They are renderable forms of causal events.

Example:

```text
RecognitionEvent(result=postponed)
may realize as:
- delayed_answer
- record_not_written
- practical_substitution
- public_mask
```

---

## 5. Beat Realization Rules

### 5.1 From Affordance and Action Events

```text
AffordanceSelectionEvent
ActionSelectionEvent
ExpressionSelectionEvent
```

should map to:

```text
intended_action
realized_action
expression_form
object_refs
surface_signal
```

Example:

```text
action_id: recognition_claim
expression_id: hesitation
surface_signal: pause_before_response
-> beat_type: interrupted_speech or delayed_answer
```

### 5.2 From Action Inhibition

```text
ActionInhibitionEvent
```

should map to:

```text
intended_action
inhibited_action
obstruction
substituted_action optional
```

Example:

```text
intended_action: direct accusation
obstruction: public audience
realized_action: joke
-> beat_type: public_mask
```

### 5.3 From Recognition Events

```text
RecognitionEvent
MisrecognitionEvent
RepairEvent
AvoidanceEvent
DisplacementEvent
```

should map to:

```text
recognition_implication
outcome
unresolved_remainder
```

Example:

```text
recognition outcome: postponed
beat:
  he sees the claim but does not record it
  the notebook remains closed
  the demand stays present without institutional form
```

### 5.4 From Memory Events

```text
MemoryReconstructionEvent
MemorySiteActivationEvent
AttentionFocusEvent
```

should map to:

```text
memory trigger
perceptual anchor
present action deformation
```

Example:

```text
memory reconstruction: old yellow light reclassified as evidence gap
attention focus: damp transcript margin
beat:
  she follows the water mark across the page and stops before the missing line
```

### 5.5 From Irreversibility

```text
IrreversibilityEvent
OperativeClassificationEvent
FutureConstraintEvent
```

should map to:

```text
threshold action
lost alternative
future constraint
```

Example:

```text
operative label: you_are_never_really_here
beat:
  the sentence is spoken in a public corridor
  a third person hears enough to carry it outward
  private conflict becomes reputational material
```

---

## 6. Narrative Beat Schema

Recommended JSON shape:

```json
{
  "beat_id": "beat-0007-01",
  "tick": 7,
  "beat_type": "failed_disclosure",
  "source_events": [
    "evt-0007-ActionSelectionEvent",
    "evt-0007-RecognitionEvent"
  ],
  "location_id": "police_archive",
  "time_window": "afternoon",
  "participants": ["p1", "p2"],
  "focal_process": "p1",
  "intended_action": {
    "action_id": "state_yellow_light_memory",
    "description": "Lin Ya tries to say what she remembers about the yellow light."
  },
  "obstruction": {
    "type": "audience_risk",
    "source": "footsteps_outside_archive",
    "evidence_refs": ["detail-footsteps-001"]
  },
  "realized_action": {
    "action_id": "object_handling",
    "object_ref": "evidence_bag_yellow_symbol",
    "description": "She presses the edge of the evidence bag instead of finishing the sentence."
  },
  "observation": {
    "observer": "p2",
    "observed_signal": "sentence stopped before the claim became recordable",
    "interpretive_risk": "protective silence or unreliable memory"
  },
  "recognition_implication": {
    "demand_id": "rec_testimony_believed",
    "outcome": "postponed"
  },
  "outcome": {
    "record_update": "not_written",
    "pressure_delta_refs": ["evt-0007-RecognitionEvent"]
  },
  "unresolved_remainder": [
    "yellow light memory remains unofficial",
    "archive record still lacks corresponding line"
  ],
  "rendering_constraints": {
    "do_not_add_case_facts": true,
    "do_not_resolve_memory_truth": true,
    "perspective": "third-person limited"
  }
}
```

---

## 7. Beat Selection

Not every causal event needs its own beat.

The beat builder should group events from the same tick into one or more renderable units.

### 7.1 Required Beat Sources

Always consider beat creation for:

```text
ActionSelectionEvent
ActionInhibitionEvent
ActionSubstitutionEvent
ExpressionSelectionEvent
RecognitionEvent
MisrecognitionEvent
RepairEvent
AvoidanceEvent
MemoryReconstructionEvent
IrreversibilityEvent
OperativeClassificationEvent
CausalWorldDetailActivatedEvent
AudienceExposureEvent
RouteAccessEvent
```

### 7.2 Beat Priority

Priority order:

```text
1. irreversible or operative classification beats
2. recognition / misrecognition beats
3. action inhibition or substitution beats
4. memory reconstruction beats
5. route/resource/audience obstruction beats
6. atmospheric attention beats
```

### 7.3 Compression

If several ticks repeat the same structure:

```text
same location
same active RPP
same beat_type
same recognition outcome
same unresolved remainder
```

compress into:

```text
PatternContinuationBeat
```

```text
PatternContinuationBeat
- tick_start
- tick_end
- repeated_beat_type
- stable_objects
- pressure_changes
- what_did_not_change
- what_narrowed
```

This prevents the renderer from restaging the same scene.

---

## 8. LLM Role

The LLM may assist in two different ways.

### 8.1 Beat Realization Candidate

The LLM may propose candidate narrative beats from causal events and local details.

These candidates must be validated.

Allowed:

```text
suggest object handling
suggest interruption form
suggest sensory anchor
suggest how an omitted action appears
suggest compression of repeated pattern
```

Forbidden:

```text
change causal outcome
invent new evidence
invent new character
invent new location
invent new past event
resolve epistemic uncertainty
add future consequence not in causal state
```

### 8.2 Literary Rendering

After beats are validated, the LLM renders prose.

Rendering input should include:

```text
narrative_beats
active local world context
attention details
soft world profile
causal details activated
forbidden facts
style canon
segment repetition trace
```

Rendering output should not include:

```text
new beat
new consequence
new memory
new evidence
new scene location
```

---

## 9. Events And Files

### 9.1 NarrativeBeatCreatedEvent

```text
payload:
- beat_id
- tick
- beat_type
- source_events
- location_id
- participants
- focal_process
- intended_action
- realized_action
- obstruction
- observation
- recognition_implication
- outcome
- unresolved_remainder
```

### 9.2 NarrativeBeatRejectedEvent

```text
payload:
- candidate_beat_id
- rejection_reason
- violated_rule
- source_events
```

### 9.3 PatternContinuationBeatEvent

```text
payload:
- beat_id
- tick_start
- tick_end
- repeated_beat_type
- stable_objects
- pressure_changes
- what_did_not_change
- what_narrowed
```

### 9.4 Trace Files

```text
narrative_beats.json
narrative_realization_trace.json
pattern_continuation_trace.json
```

---

## 10. Runtime Pipeline

Recommended rendering pipeline:

```text
1. Run causal tick pipeline
2. Build attention focus and local-world details
3. Collect causal events for segment
4. Build or propose narrative beats
5. Validate beats against causal events and local-world constraints
6. Compress repeated beats
7. Pass validated beats to LLM renderer
8. Validate segment output protocol
9. Append rendered segment
```

This replaces:

```text
raw causal state -> LLM prose
```

with:

```text
raw causal state -> validated narrative beats -> LLM prose
```

---

## 11. Validation Rules

Reject a beat if it:

- changes recognition outcome
- changes memory truth
- invents evidence
- invents durable objects, records, messages, or access tokens
- invents witness, audience, or institution
- uses a location not in LocalWorld
- uses an object, record, or evidence item not in the registry, scenario, validated local detail, or attention context
- gives success to an action that was inhibited
- removes an obstruction that exists in causal state
- creates irreversible consequence without event
- contradicts case ledger or local-world constraints

Require every beat to cite:

```text
source_events
location_id
participants
outcome or unresolved_remainder
```

Require every durable material anchor to cite:

```text
object_refs
record_refs
evidence_refs
```

---

## 12. Implementation Phases

### Phase 1: Deterministic Beat Builder

Build beats from existing events without LLM assistance.

Acceptance:

```text
every rendered segment receives at least one NarrativeBeat or PatternContinuationBeat
recognition events map to concrete beat types
action inhibition maps to omitted or substituted action
beats cite source events
```

### Phase 2: Pattern Continuation Compression

Compress repeated tick structures.

Acceptance:

```text
three similar consecutive beats become one continuation beat
renderer is told not to restage same object/action
pressure changes are preserved
```

### Phase 3: LLM Beat Candidate Assistance

Allow LLM to propose beats only when deterministic mapping is under-specified.

Acceptance:

```text
LLM candidate beats are validated before use
invalid candidates are rejected
no causal outcome changes
```

### Phase 4: Renderer Uses Beats

Renderer receives validated beats instead of raw story frames alone.

Acceptance:

```text
rendered prose contains concrete actions or omissions
repeated state becomes pattern continuation
segment output does not invent new causal facts
```

### Phase 5: Viewer Support

Add panel:

```text
Narrative Beats
- beat type
- source events
- intended action
- realized action
- obstruction
- observation
- unresolved remainder
```

---

## 13. Evaluation Criteria

The mechanism succeeds when:

- prose reads like scenes rather than relationship diagnostics
- abstract events become concrete situated actions
- omissions and inhibited actions are narratable
- repeated structures are compressed
- local details are used as action anchors, not mere decoration
- LLM rendering has enough material to avoid vague atmosphere
- causal authority remains in simulator events

It fails when:

- prose still only says pressure rose or memory returned
- every beat becomes the same silence/looking/object gesture
- LLM invents new actions not licensed by events
- repeated state is hidden by fake novelty
- local detail does not connect to action, obstruction, observation, or consequence

---

## 14. Non-Negotiable Invariants

```text
1. A narrative beat is not a causal event.
2. A narrative beat must cite causal source events.
3. A narrative beat may realize but not change causal outcomes.
4. LLM-rendered prose must be grounded in validated beats.
5. Repeated causal structures should compress into continuation beats.
6. Local details should anchor beats, not replace events.
7. No new characters, evidence, locations, or past events may enter through beat realization.
8. Segment rendering must validate output protocol before persistence.
```

---

## 15. Summary

RPF needs narrative realization because novels are not made from abstract state changes alone.

The simulator may know:

```text
recognition was postponed
memory pressure rose
speech was inhibited
```

But prose needs:

```text
she started to say the memory
footsteps passed outside
she pressed the evidence bag instead
he did not write the sentence down
the record stayed empty
```

`NarrativeBeat` is the bridge between those two levels.

With this layer, RPF can move from:

```text
structural simulation rendered poetically
```

to:

```text
causally grounded scenes rendered as fiction
```
