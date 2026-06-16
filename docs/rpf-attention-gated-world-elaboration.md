# RPF Attention-Gated World Elaboration

## 0. Purpose

This document defines a controlled mechanism for using an LLM to elaborate local-world details only when attention, action, memory, or scene pressure makes those details relevant.

It addresses a core RPF problem:

```text
realism requires detail
but full predefinition is impossible
and unconstrained LLM invention breaks causal integrity
```

The solution is:

```text
Attention-Gated World Elaboration
```

Meaning:

```text
The world begins with bounded coarse parameters.
Only the parts attended to by process positions, actions, memory triggers, or scene constraints are locally elaborated.
LLM-generated details are classified by persistence and causal relevance before they enter future context.
```

The LLM may help generate perceptual and local-world parameters. It may not directly create causal facts, new plot events, new characters, new evidence, or state transitions.

---

## 1. Core Thesis

RPF should not require a fully prewritten town, room, street, archive, hospital, or household.

Instead, it should support progressive world disclosure:

```text
bounded local world
-> attention focus
-> detail gap detection
-> LLM local detail proposal
-> validation
-> persistence policy
-> future prompt injection if relevant
```

This makes the world feel concrete without letting detail state explode.

The guiding rule is:

```text
Only what becomes attended, acted upon, remembered, blocked, or repeated needs to become more detailed.
```

---

## 2. Relationship To LocalWorld

The bounded local world defines coarse geography and constraints:

```text
locations
routes
rhythms
resources
audiences
institutions
memory_sites
ecology
boundary_rules
```

Attention-gated elaboration fills in local detail inside those coarse structures.

Example:

```text
LocalWorld says:
police_archive exists, access is restricted, memory_charge is high.

Attention-gated elaboration may add:
the evidence shelf labels are water-warped,
the fluorescent light has a yellow delay,
the window latch is painted shut,
the corridor carries footsteps from the front office.
```

But these details are not all equal. Most are temporary texture. Some become soft profiles. A few become causal records.

Durable objects, records, evidence items, messages, and access tokens are governed by `rpf-object-record-evidence-registry.md`.

Attention-gated elaboration may propose their perceptual or material properties, but it may not create durable registry items by prose.

---

## 3. Attention As Gate

The LLM should not elaborate arbitrary world regions.

Elaboration requires an attention gate.

### 3.1 Attention Sources

Allowed attention sources:

```text
process gaze or bodily orientation
selected action
inhibited action
expression deformation
object handling
route traversal
memory activation
scene crystallization
recognition demand
blocked capacity
audience exposure
resource search
evidence inspection
repeated environmental cue
```

### 3.2 AttentionFocusEvent

Add an event:

```text
AttentionFocusEvent
payload:
- focus_id
- focus_type
- process_id
- scene_id optional
- location_id
- object_id optional
- route_id optional
- trigger_event
- attention_mode
- intensity
- duration
- reason
- evidence
```

Attention modes:

```text
gaze
listening
touch
smell
avoidance
search
memory_intrusion
practical_use
threat_monitoring
repair_attempt
evidence_review
route_assessment
```

---

## 4. Detail Gap Detection

The system should ask for LLM elaboration only when existing structured context is insufficient for the current scene or action.

### 4.1 DetailGap

```text
DetailGap
- gap_id
- focus_id
- scope_type
- scope_id
- needed_for
- missing_dimensions
- risk_level
- requested_detail_types
- max_detail_budget
```

`needed_for` may be:

```text
rendering_texture
affordance_check
route_assessment
evidence_handling
audience_exposure
memory_trigger
recognition_scene
blocked_capacity_explanation
```

### 4.2 Gap Rules

Do not request elaboration if:

- enough soft profile already exists
- the detail would not be perceived by any process
- the detail would require inventing new facts
- the current scene does not need sensory or affordance grounding
- the detail budget for the scope is exhausted

Request elaboration if:

- action availability depends on missing local properties
- the scene is repeated and needs specific variation
- attention focuses on an object without local parameters
- memory site activation needs perceptual anchor
- public exposure depends on visibility, crowding, sound, or sight lines
- route access depends on weather, surface, lighting, or obstruction

### 4.3 Trigger Thresholds

The first implementation should use explicit thresholds so elaboration does not happen on every tick.

Recommended defaults:

```text
attention_intensity_min: 0.55
same_scope_repeat_min: 2
same_summary_similarity_max: 0.82
soft_profile_freshness_min: 0.35
detail_budget_per_scope_per_run: 12
causal_detail_budget_per_scope_per_run: 4
ephemeral_detail_budget_per_segment: 5
```

Elaboration should trigger when at least one is true:

```text
attention_intensity >= attention_intensity_min
action_or_affordance_check_requires_missing_property
same scope appears repeatedly but current soft profile is stale
rendered frames are too similar and need perceptual variation
memory site activation lacks a local anchor
audience exposure depends on undefined visibility or sound conditions
route access depends on undefined surface, light, weather, or obstruction
```

Elaboration should not trigger when:

```text
same location was elaborated in the previous segment and no new focus appears
soft profile is fresh enough
only generic mood is missing
current tick has no process attention evidence
detail budget is exhausted
```

---

## 5. Detail Types

LLM-generated details should be classified before persistence.

### 5.1 Ephemeral Detail

Used only for current rendering.

Examples:

```text
old paper smell
a faint motorbike sound outside
light dust on a table edge
water sound in a pipe
a dull reflection on a window
```

Rules:

```text
may be rendered
should not be persisted exactly
must not affect future action
must not introduce new facts
```

### 5.2 Soft Persistent Detail

Compressed into an atmospheric or perceptual profile.

Examples:

```text
police_archive tends to feel damp, yellow-lit, and narrow
market_street tends to be noisy, watched, and rumor-heavy in the morning
abandoned_factory tends to be wet, metallic, and spatially confusing
```

Rules:

```text
persist as tags and summary parameters
do not preserve exact prose
inject only when the same scope is relevant
decay or refresh over time
```

### 5.3 Causal Detail

Structured detail that can affect action, route, evidence, memory, audience, resource, or future constraints.

Examples:

```text
window latch is painted shut
archive cabinet lock is loose
old road is blocked by rainwater
market stall creates line-of-sight cover
evidence label is water-damaged
clinic corridor noticeboard exposes a name
```

Rules:

```text
must be validated
must be represented structurally
must cite attention and source context
must not contradict existing local world
becomes causal only through an event
```

### 5.4 Forbidden Detail

LLM may not introduce:

```text
new characters
new relationships
new institutions
new case facts
new evidence
new durable object
new record
new message
new access token
new custody change
new testimony
new culprit
new past event
new location without LocationDiscoveryEvent
new future event
changed recognition outcome
changed irreversible record
```

Forbidden detail should be rejected or downgraded to non-factual atmosphere if possible.

---

## 6. Detail Persistence Policy

Every proposed detail must be assigned one of:

```text
discard_after_render
compress_to_profile
persist_as_causal_record
reject
```

### 6.1 Decision Questions

```text
Does it affect action availability?
Does it affect route access?
Does it affect resource access?
Does it affect evidence condition?
Does it affect audience exposure?
Does it affect memory activation?
Does it affect recognition or misrecognition?
Was it attended to repeatedly?
Was it named by a process?
Did it participate in an event?
Would forgetting it create contradiction later?
Does it introduce forbidden facts?
```

### 6.2 Policy Rules

```text
if introduces forbidden facts:
    reject

elif affects action, route, resource, evidence, audience, memory, recognition, or future constraints:
    persist_as_causal_record

elif recurring sensory pattern or stable mood of a scope:
    compress_to_profile

else:
    discard_after_render
```

### 6.3 Detail Lifetimes

```text
EphemeralDetail:
  lifetime: current render only

SoftPersistentDetail:
  lifetime: until decayed, overwritten, or contradicted

CausalDetail:
  lifetime: event-sourced; may be changed only by later events
```

---

## 7. Data Model

### 7.1 DetailProposal

```text
DetailProposal
- proposal_id
- focus_event_id
- scope_type
- scope_id
- proposed_by
- detail_type
- content
- structured_candidates
- risk_flags
- confidence
```

### 7.2 EphemeralDetail

Ephemeral details may be held only in render context.

```text
EphemeralDetail
- detail_id
- scope_id
- sensory_channel
- text
- used_in_render_id
- discard_after_render: true
```

### 7.3 SoftWorldProfile

```text
SoftWorldProfile
- profile_id
- scope_type
- scope_id
- sensory_tags
- atmosphere_tags
- recurring_material_cues
- visibility_profile
- sound_profile
- smell_profile
- tactile_profile
- stability
- freshness
- source_focus_events
- source_render_refs
```

Soft profile values should be compact:

```yaml
soft_world_profiles:
  police_archive:
    sensory_tags: [mildew, yellow_light, paper_dampness]
    atmosphere_tags: [oppressive, narrow, procedural]
    visibility_profile: dim_but_exposed
    sound_profile: low_machine_hum
    stability: recurring
    freshness: 0.74
```

### 7.4 CausalWorldDetail

```text
CausalWorldDetail
- detail_id
- scope_type
- scope_id
- detail_type
- structural_field
- value
- affects_capacities
- affected_events
- causal_status
- validation_evidence
- created_by_event
- last_updated_by_event
```

`causal_status`:

```text
proposed
validated
persisted
causalized
decayed
superseded
rejected
```

---

## 8. Event Additions

### 8.1 DetailGapDetectedEvent

```text
payload:
- gap_id
- focus_event_id
- scope_type
- scope_id
- needed_for
- missing_dimensions
- risk_level
- requested_detail_types
- max_detail_budget
```

### 8.2 DetailProposalEvent

```text
payload:
- proposal_id
- focus_event_id
- provider
- proposed_details
- risk_flags
- validation_status
```

This event records the proposal. It does not make the details causal.

### 8.3 DetailPersistenceDecisionEvent

```text
payload:
- proposal_id
- decisions:
  - detail_id
  - decision: discard_after_render | compress_to_profile | persist_as_causal_record | reject
  - reason
  - target_record optional
```

### 8.4 SoftWorldProfileUpdatedEvent

```text
payload:
- profile_id
- scope_type
- scope_id
- previous_profile
- new_profile
- source_details
- decay_policy
```

### 8.5 CausalWorldDetailValidatedEvent

```text
payload:
- detail_id
- scope_type
- scope_id
- detail_type
- structural_field
- value
- affects_capacities
- validation_evidence
```

### 8.6 CausalWorldDetailActivatedEvent

Emitted only when a persisted causal detail actually affects simulation.

```text
payload:
- detail_id
- activated_by_event
- affected_layer
- affected_capacity
- previous_availability
- new_availability
- mechanism
```

---

## 9. LLM Contract

### 9.1 LLM Task

The LLM may be called for:

```text
local sensory elaboration
local affordance candidate description
spatial visibility description
route surface description
object condition candidate
atmospheric profile compression
```

It may not decide:

```text
whether an action succeeds
whether a route is blocked
whether evidence is valid
whether a witness exists
whether a past event happened
whether a recognition outcome changes
whether an irreversible event is created
```

### 9.2 Prompt Inputs

```text
local_world scope
active registry excerpt
current scene
attention focus
allowed detail types
forbidden facts
existing soft profile
existing causal details
needed_for
detail budget
render canon
```

### 9.3 Expected Output

The LLM should return structured candidates:

```json
{
  "ephemeral_details": [
    {
      "sensory_channel": "smell",
      "text": "old paper and damp concrete"
    }
  ],
  "soft_profile_candidates": [
    {
      "scope_id": "police_archive",
      "sensory_tags": ["mildew", "yellow_light"],
      "atmosphere_tags": ["procedural", "compressed"]
    }
  ],
  "causal_detail_candidates": [
    {
      "detail_type": "affordance_constraint",
      "scope_id": "police_archive.window_latch",
      "structural_field": "openability",
      "value": "stuck",
      "affects_capacities": ["exit", "ventilation"],
      "evidence_in_prompt": ["attention focused on window during attempted exit"]
    }
  ],
  "rejections_or_uncertainties": []
}
```

If the provider cannot return JSON reliably, the response must be parsed and validated before persistence.

---

## 10. Validation Rules

Reject details that:

- create new people, places, durable objects, records, evidence, messages, testimony, access tokens, custody changes, institutions, or past events
- contradict existing causal details
- alter case ledger facts
- make an action succeed or fail directly
- imply offscreen events without trace
- exceed the scope of attention
- exceed detail budget

Downgrade details when possible:

```text
"a hidden witness watched from the hall"
-> reject as new witness

"the hall carried faint footsteps"
-> ephemeral sound detail
```

Promote details only when structurally needed:

```text
"the label is damp"
-> ephemeral if only visual
-> causal if evidence readability is checked
```

---

## 11. Context Injection

Future prompts should not receive every detail ever generated.

### 11.1 Injection Priority

For a scene at location `L`, inject:

```text
1. causal details in scope L or active route
2. active memory-site details in scope L
3. soft profile summary for L
4. recent relevant attention focus records
5. ephemeral details only from current render pass
```

Do not inject:

- discarded details
- full previous prose
- stale soft details below freshness threshold
- unrelated location profiles
- causal details not reachable from current scope

### 11.2 Compression Rule

Soft profile should remain compact.

Invalid:

```text
store every sentence ever used to describe the archive
```

Valid:

```text
police_archive:
  sensory_tags: mildew, yellow_light, damp_paper
  atmosphere_tags: compressed, procedural, watchful
  recurring_cues: old labels, low machine hum
```

### 11.3 Anti-Repetition Injection

When a segment is rendered after previous segments in the same scope, inject a short repetition summary instead of previous prose.

```text
recent_repetition_summary:
- repeated_scope: police_archive
- repeated_objects: evidence_shelf, yellow_light, transcript_copy
- repeated_actions: looking_without_touching, delayed_note_taking
- instruction: do not restage these; either compress them as sustained pressure or shift attention to a new validated focus.
```

Do not inject full previous segment text unless the current task is continuity repair.

Instead inject:

```text
previous_segment_facts:
- tick_range
- active_location
- active_attention_focus
- causal_details_activated
- soft_profile_used
- prohibited_repetition_patterns
```

This prevents the LLM from copying the style and scene structure of earlier prose.

---

## 12. Runtime Pipeline

Recommended placement:

```text
1. Scene or tick context established
2. AttentionFocusEvent emitted
3. Detail gap detection
4. Optional LLM detail proposal
5. Validate proposal
6. Apply persistence policy
7. Update soft profiles or causal detail records
8. Inject accepted relevant details into rendering or downstream engines
9. Causal details affect simulation only when activated by later events
```

### 12.1 Trace Files

Each run may write:

```text
attention_trace.json
detail_gap_trace.json
world_detail_trace.json
soft_world_profiles.json
causal_world_details.json
render_repetition_trace.json
```

---

## 13. Repetition Control

Attention-gated elaboration is not a replacement for segment-output validation.

It solves:

```text
the model has no new local details to render
the same location/object/gesture appears without variation
the prompt keeps offering the same high-level facts
```

It does not solve:

```text
LLM returns a full story document in segment mode
backend stores full previous stream as a segment
frontend displays a duplicated stream
```

Those require rendering protocol validation.

### 13.1 Repetition Classes

RPF should distinguish three repetition classes:

```text
protocol_repetition:
  caused by invalid segment output, duplicated headings, or stream re-embedding

state_repetition:
  caused by unchanged causal state, same tick outcome, same recognition result, or repeated memory event

expression_repetition:
  caused by insufficient local detail, stale attention focus, or repeated imagery
```

Attention-gated elaboration addresses mostly `expression_repetition` and partially `state_repetition`.

It must not be treated as a fix for `protocol_repetition`.

### 13.2 RenderRepetitionTrace

Add a trace:

```text
RenderRepetitionTrace
- segment_id
- repeated_scope
- repeated_focuses
- repeated_objects
- repeated_actions
- repeated_phrases optional
- summary_similarity
- structural_similarity
- repetition_class
- recommended_action
```

Recommended actions:

```text
reject_invalid_segment_output
compress_as_pattern
request_attention_elaboration
shift_to_new_focus
inject_soft_profile_only
skip_llm_render_until_new_state
```

### 13.3 Segment Protocol Guard

Segment rendering must enforce:

```text
segment output contains no document title
segment output contains no overview
segment output contains no ending_state
segment output does not include previous segments
segment output source ticks match only the current segment
segment text does not begin with "# "
```

If violated:

```text
reject segment output
retry with stricter prompt or fallback deterministic segment
do not append invalid text to rendered_segments.json
```

This guard is mandatory before LLM segment output can be trusted.

### 13.4 State Repetition Compression

If causal frames are genuinely repetitive, the renderer should not invent fake novelty.

Instead it should write:

```text
This pattern continued.
The same object, silence, or route remained active.
Only pressure, access, visibility, or memory salience changed.
```

Compression should be used when:

```text
same location
same active RPP
same recognition outcome
same affordance/action/expression pattern
same attention focus
minor pressure deltas only
```

### 13.5 Detail Elaboration As Repetition Breaker

When expression repetition is detected, the system may open a detail gap:

```text
if repeated_scope and repeated_focus and no fresh soft profile:
    request ephemeral and soft-profile details

if repeated_action depends on undefined object property:
    request causal detail candidate

if repeated memory site lacks perceptual anchor:
    request memory-site sensory anchor
```

If the object is durable, the request must cite an existing registry ref. Otherwise the proposal must be rejected or downgraded to ephemeral texture.

The LLM should be instructed:

```text
Do not create new facts.
Do not restage the previous scene.
Shift perception to the current attention focus.
If nothing materially changes, compress repetition rather than decorate it.
```

---

## 14. MVP Priorities

The mechanism should be implemented in this order:

```text
1. Segment protocol guard
2. Render repetition trace
3. Render-only ephemeral elaboration
4. Soft profile compression and injection
5. Causal detail proposal and validation
6. Causal detail activation
```

Rationale:

```text
Protocol repetition must be blocked before detail elaboration can help.
Otherwise invalid LLM output will continue to duplicate headings and previous prose.
```

### 14.1 Minimal Non-Causal MVP

The first useful version does not need causal details.

It only needs:

```text
AttentionFocusEvent
DetailGapDetectedEvent
ephemeral detail proposal
soft profile update
render repetition trace
segment protocol guard
```

Acceptance:

```text
segments no longer duplicate titles or previous segments
repeated scenes are compressed as patterns
same location gains compact atmospheric continuity
ephemeral details are not persisted
soft profiles stay below a fixed size budget
```

---

## 15. Example

### 15.1 Input Situation

```text
Location: police_archive
Scene: evidence review
Attention: Lin Ya looks at the evidence shelf label before answering
Gap: label condition and shelf sensory details are not defined
Needed for: rendering texture and possible evidence readability
```

### 15.2 LLM Proposal

```text
ephemeral:
- the shelf smells of damp metal and old paper
- the light arrives half a beat late after each flicker

soft profile:
- police_archive gains tags: mildew, yellow_light, damp_labels

causal candidate:
- evidence shelf labels are water-warped, reducing readability
```

### 15.3 Persistence Decision

```text
damp metal smell -> discard_after_render
yellow light + damp labels -> compress_to_profile
water-warped labels -> persist_as_causal_record only if evidence readability is checked
```

### 15.4 Later Activation

If a process tries to read a label:

```text
ActionAttemptEvent(read_label)
-> CausalWorldDetailActivatedEvent(water_warped_label)
-> AffordanceChangeEvent(label_readability decreases)
-> possible MisrecognitionEvent or InvestigationUpdateEvent
```

---

## 16. Implementation Phases

### Phase 1: Render-Only Ephemeral Details

Implement:

```text
AttentionFocusEvent
DetailGapDetectedEvent
LLM detail proposal for ephemeral details
discard_after_render policy
segment protocol guard
render repetition trace
```

Acceptance:

```text
LLM can enrich current scene texture
no generated detail persists after render
no causal state changes
invalid segment output is rejected before append
```

### Phase 2: Soft Profiles

Implement:

```text
SoftWorldProfile
compress_to_profile policy
soft_world_profiles.json
prompt injection for active location profile
```

Acceptance:

```text
recurring location atmosphere becomes stable
exact prose is not stored
profiles remain compact
stale profiles decay
```

### Phase 3: Causal Detail Candidates

Implement:

```text
CausalWorldDetail
validation rules
persist_as_causal_record policy
causal_world_details.json
```

Acceptance:

```text
causal details must cite attention and validation evidence
forbidden details are rejected
causal details do not affect simulation until activated
```

### Phase 4: Causal Activation

Implement:

```text
CausalWorldDetailActivatedEvent
integration with affordance, route, evidence, audience, and memory engines
```

Acceptance:

```text
world details can block or enable action only through events
replay reconstructs detail activation
LLM cannot directly decide consequences
```

### Phase 5: Viewer Support

Add viewer panel:

```text
World Details
- current attention focus
- ephemeral details for current render
- soft profile for current location
- causal details in current scope
- rejected details
- detail persistence decisions
```

---

## 17. Evaluation Criteria

The mechanism succeeds when:

- scenes gain concrete sensory specificity
- the world expands only where attention reaches
- repeated locations develop stable atmosphere
- causal details are structurally validated
- irrelevant detail does not accumulate
- LLM-generated prose does not become hidden state
- later scenes can reuse important details without full prose history
- replay can explain when and why a causal detail became active
- segment rendering does not duplicate titles, previous prose, or stream text
- repeated states are compressed rather than falsely varied

It fails when:

- LLM invents facts that enter state
- every sensory detail is stored permanently
- prompts grow with stale detail
- causal constraints appear without events
- attention does not gate elaboration
- repeated scenes still restage the same generic details
- soft profiles become bloated prose summaries
- invalid segment output is appended to story stream
- detail generation is used to hide protocol or state repetition bugs

---

## 18. Non-Negotiable Invariants

```text
1. No attention, no elaboration.
2. LLM proposals are not causal facts.
3. Ephemeral details are render-only.
4. Soft profiles are compressed, not prose archives.
5. Causal details require validation and source events.
6. Causal details affect simulation only through activation events.
7. Forbidden facts are rejected.
8. Detail context injection is scoped and budgeted.
9. Replay must reconstruct persisted and activated causal details.
10. LLM may enrich perception but may not create plot authority.
11. Segment output must be validated before persistence.
12. Repetition must be classified before requesting more detail.
13. If state genuinely repeats, render compression is preferred over invented novelty.
```

---

## 19. Summary

Attention-gated world elaboration lets RPF avoid two failures:

```text
thin world:
  too few details, scenes feel abstract

bloated world:
  too many permanent details, state and prompts become unmanageable
```

The world becomes detailed only where it is looked at, touched, avoided, searched, remembered, or needed for action.

Most details disappear after rendering.

Repeated atmosphere becomes a compact profile.

Only details that can affect action, route, evidence, audience, memory, recognition, or future constraint become structured records.

This allows LLMs to improve perceptual realism without stealing causal authority from the simulator.

It also gives RPF a principled anti-repetition strategy:

```text
protocol repetition -> reject invalid segment output
state repetition -> compress as sustained pattern
expression repetition -> open attention-gated detail gap
```

This keeps rendered prose from looping while preserving causal truth.
