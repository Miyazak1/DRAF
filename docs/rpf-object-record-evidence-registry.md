# RPF Object, Record, and Evidence Registry

## 0. Purpose

This document defines the missing material registry layer for RPF:

```text
Object / Record / Evidence Registry
```

RPF already constrains space through `LocalWorld`, constrains detail through attention-gated elaboration, and constrains rendering through LLM contracts.

But stories do not become concrete through locations alone.

They become concrete through things that persist:

```text
bills
keys
phones
notebooks
case files
evidence bags
medical reports
locked doors
water-damaged labels
unfiled forms
record logs
objects someone refuses to touch
```

This registry prevents a common failure:

```text
the simulator has causal events,
the LLM has atmosphere,
but no stable material things connect one scene to the next.
```

The registry gives the system durable objects that can be attended to, moved, damaged, hidden, misread, recorded, exposed, or institutionalized without letting the LLM invent arbitrary facts.

---

## 1. Core Position

Objects, records, and evidence are not decorative props.

They are material-social carriers of constraint.

They can:

- make a past event present again
- make a claim harder or easier to deny
- create public exposure
- block or enable action
- carry institutional authority
- anchor memory reconstruction
- force repeated encounter
- become contested proof
- become a repair object or accusation object

The core rule:

```text
No durable thing may enter causal simulation unless it is registered, discovered, or validated by event.
```

LLM prose may mention ephemeral texture.

It may not silently create durable objects, records, evidence, documents, keys, messages, weapons, witnesses, files, or institutional records.

---

## 2. Relationship To Existing Layers

### 2.1 LocalWorld

`LocalWorld` answers:

```text
Where can something happen?
Who may see it?
What routes, rhythms, institutions, and memory sites constrain it?
```

The object registry answers:

```text
What durable things exist there?
Who can access them?
What state are they in?
What can they prove, obstruct, or remember?
```

LocalWorld should not store every object.

It should reference object IDs when those objects shape access, memory, evidence, public exposure, or action.

### 2.2 Case Ledger

For investigative scenarios, `case_ledger` is epistemic:

```text
what is known, contested, unreliable, or missing about the case
```

The registry is material:

```text
what object or record exists in the world, where it is, who controls it, and what condition it has
```

The same item may appear in both layers:

```text
case_ledger.evidence_items.yellow_paint_mark
object_registry.evidence_objects.yellow_paint_mark
```

But the two layers must not collapse.

The ledger may say evidence is unreliable.

The registry must say where the evidence is, whether it is readable, who can touch it, and what has happened to it.

### 2.3 Attention-Gated World Elaboration

Attention-gated detail may propose object properties:

```text
the label is water-warped
the latch is painted shut
the transcript margin is torn
```

These details become causal only if they are accepted into the registry as:

```text
ObjectStateUpdateEvent
RecordStateUpdateEvent
EvidenceStateUpdateEvent
```

Otherwise they remain render-only or compressed into a soft profile.

### 2.4 Narrative Event Realization

`NarrativeBeat` should reference registered objects when possible:

```text
object_refs
record_refs
evidence_refs
local_detail_refs
```

This prevents repeated vague gestures.

Invalid:

```text
She touched "the file" when no file is registered.
```

Valid:

```text
She touched old_case_file,
whose current state is water_damaged and institutionally controlled by local_police_station.
```

### 2.5 LLM Rendering

The LLM may render registered objects.

It may not create durable objects.

If the LLM mentions an unregistered durable thing:

```text
reject
```

or, if it is harmless texture:

```text
downgrade to ephemeral detail
```

Example:

```text
"a faint dust line on the shelf" -> ephemeral detail
"a hidden second report in the shelf" -> reject unless discovered by event
```

---

## 3. Registry Schema

```text
ObjectRegistry
- world_objects
- record_objects
- evidence_objects
- message_objects
- access_tokens
- object_links
- custody_log
- state_history
```

The registry may be initialized from scenario YAML and then updated only through events.

It is causal state because it constrains later action, access, rendering, memory, and narrative beats.

It is not a derived view.

---

## 4. WorldObject

A `WorldObject` is a durable material object that may be seen, used, moved, damaged, hidden, or remembered.

```text
WorldObject
- object_id
- label
- object_type
- location_id
- container_id optional
- owner_process_id optional
- controlling_institution optional
- access_level
- visibility
- portability
- condition
- memory_charge
- linked_processes
- linked_events
- linked_records
- linked_evidence
- allowed_actions
- forbidden_actions
- current_state
```

Object types:

```text
bill
key
phone
bag
notebook
table
door
window
medicine
clothing
photograph
tool
weapon
vehicle
furniture
personal_item
institutional_item
unknown_object
```

Example:

```yaml
world_objects:
  - object_id: unpaid_power_bill
    label: 未缴电费单
    object_type: bill
    location_id: shared_kitchen
    access_level: visible
    visibility: high
    portability: low
    condition: creased
    memory_charge: 0.68
    linked_processes: [p1, p2]
    allowed_actions: [look_at, move, point_to, ignore, pay]
```

---

## 5. RecordObject

A `RecordObject` is a document, log, institutional file, database entry, form, or recorded statement whose authority depends on institution, custody, and legibility.

```text
RecordObject
- record_id
- label
- record_type
- location_id
- institution_id
- access_level
- authority_level
- legibility
- completeness
- alteration_risk
- official_status
- linked_processes
- linked_events
- linked_evidence
- custody_state
- current_state
```

Record types:

```text
case_file
archive_register
evidence_log
medical_report
school_record
financial_bill
employment_record
attendance_book
message_log
audio_transcript
video_record
inspection_report
unfiled_form
```

Important distinction:

```text
record exists
record is accessible
record is official
record is trusted
record is complete
```

These must be separate.

Example:

```yaml
record_objects:
  - record_id: old_case_file
    label: 旧案卷宗
    record_type: case_file
    location_id: police_archive
    institution_id: local_police_station
    access_level: restricted
    authority_level: high
    legibility: partial
    completeness: incomplete
    alteration_risk: medium
    official_status: recognized_but_contested
```

---

## 6. EvidenceObject

An `EvidenceObject` is an object or record whose significance depends on epistemic status, custody, contamination, and interpretive conflict.

It may wrap a `WorldObject` or `RecordObject`.

```text
EvidenceObject
- evidence_id
- label
- evidence_type
- registry_ref
- location_id
- custody_holder
- accessibility
- reliability
- contamination_risk
- legibility
- chain_of_custody_strength
- interpretive_status
- linked_testimonies
- linked_records
- linked_locations
- forbidden_inferences
- current_state
```

Evidence types:

```text
physical_trace
document
testimony_record
image
audio
video
symbol
map
body_trace
absence
contradiction
damaged_record
```

Interpretive statuses:

```text
unexamined
contested
misread
partially_confirmed
suppressed
institutionalized
contaminated
unreliable
missing_context
```

Example:

```yaml
evidence_objects:
  - evidence_id: old_tape_yellow_bleed
    label: 泛黄录像带
    evidence_type: video
    registry_ref: record:old_tape_yellow_bleed
    location_id: evidence_room_yellow_light
    custody_holder: local_police_station
    accessibility: restricted
    reliability: 0.42
    contamination_risk: 0.73
    legibility: low
    chain_of_custody_strength: weak
    interpretive_status: contested
    forbidden_inferences:
      - culprit_identity
      - supernatural_truth
```

---

## 7. MessageObject

Some relationships turn on messages, missed calls, read receipts, drafts, notes, or public posts.

These should not be treated as generic dialogue.

```text
MessageObject
- message_id
- message_type
- sender_process_id
- receiver_process_ids
- created_tick
- delivered_tick optional
- read_tick optional
- response_tick optional
- visibility
- deletion_state
- publicness
- institutional_status
- content_class
- source_event_id
```

Content should be stored only when it is causally necessary.

Otherwise store a content class:

```text
apology_attempt
recognition_claim
practical_notice
silence_after_read
threat
public_statement
ambiguous_check_in
```

This prevents the simulator from becoming a chat transcript generator.

---

## 8. AccessToken

Some objects matter because access is controlled.

```text
AccessToken
- token_id
- token_type
- label
- holder_process_id optional
- institution_id optional
- grants_access_to
- revocable
- legitimacy
- visibility
- current_state
```

Token types:

```text
key
password
permission
role_badge
form
signature
appointment
relationship_permission
informal_favor
```

Example:

```text
archive key
evidence room permission
clinic appointment number
family account password
```

Access tokens should feed:

```text
AffordanceSelectionEvent
ActionInhibitionEvent
RouteAccessEvent
RecordAccessEvent
EvidenceAccessEvent
```

---

## 9. Object Links

Objects rarely matter alone.

The registry should support explicit links:

```text
ObjectLink
- link_id
- source_ref
- target_ref
- link_type
- strength
- evidence_refs
```

Link types:

```text
stored_in
controls_access_to
documents
contradicts
confirms
contaminates
belongs_to
owed_by
owed_to
remembered_with
seen_with
institutionally_records
symbolically_resembles
```

Example:

```text
archive_register documents old_case_file
old_tape_yellow_bleed contradicts witness_testimony_03
evidence_room_key controls_access_to evidence_room_yellow_light
unpaid_power_bill owed_by p2 and paid_by p1
```

---

## 10. Runtime Events

### 10.1 ObjectRegisteredEvent

Used during initialization or discovery.

```text
payload:
- object_ref
- registry_type
- source
- location_id
- reason
```

### 10.2 ObjectStateUpdateEvent

```text
payload:
- object_id
- previous_state
- new_state
- changed_fields
- cause_event_id
- affected_capacities
```

### 10.3 ObjectAccessEvent

```text
payload:
- object_ref
- process_id
- access_result
- access_reason
- access_token_refs
- institution_refs
- audience_refs
```

Access results:

```text
available
restricted
denied
costly
publicly_exposed
requires_permission
```

### 10.4 RecordStateUpdateEvent

```text
payload:
- record_id
- previous_state
- new_state
- changed_fields
- institution_id
- cause_event_id
```

### 10.5 RecordAccessEvent

```text
payload:
- record_id
- process_id
- access_result
- authority_context
- legibility_context
- source_events
```

### 10.6 EvidenceStateUpdateEvent

```text
payload:
- evidence_id
- previous_state
- new_state
- changed_fields
- contamination_context
- custody_context
- source_events
```

### 10.7 EvidenceAccessEvent

```text
payload:
- evidence_id
- process_id
- access_result
- accessibility
- reliability
- contamination_risk
- legibility
- source_events
```

### 10.8 CustodyChangeEvent

```text
payload:
- registry_ref
- previous_holder
- new_holder
- legitimacy
- visibility
- source_event_id
```

### 10.9 ObjectAttentionEvent

An attention event specialized for durable registry items.

```text
payload:
- registry_ref
- process_id
- location_id
- attention_mode
- reason
- source_event_id
```

It may open a detail gap, but does not create new object state by itself.

---

## 11. State Update Rules

### 11.1 Object State

Object state may change through:

- being moved
- being handled
- being damaged
- being hidden
- being made public
- being institutionally recorded
- being reclassified as evidence
- being repeatedly ignored

State update must cite an event.

Invalid:

```text
the old file becomes unreadable because the LLM described it as wet
```

Valid:

```text
heavy rain activates archive leak
-> ObjectStateUpdateEvent(old_case_file.legibility decreases)
-> later RecordAccessEvent has reduced legibility
```

### 11.2 Record Authority

A record can be:

```text
existent but unofficial
official but incomplete
official but inaccessible
accessible but illegible
legible but institutionally denied
```

These differences are dramatically important and must not be compressed into a single boolean.

### 11.3 Evidence Status

Evidence status must distinguish:

```text
accessibility
reliability
contamination
custody
interpretation
institutional uptake
```

An evidence object may become more visible and less reliable at the same time.

Example:

```text
public attention to a damaged tape increases pressure,
but also increases contamination and rumor risk.
```

### 11.4 Custody

Custody is not ownership.

Custody means:

```text
who can touch, hide, alter, release, deny, or authorize the item
```

Custody changes should be rare, visible, and event-backed.

---

## 12. Runtime Integration

Recommended pipeline placement:

```text
1. Load LocalWorld and ObjectRegistry
2. Advance clock, rhythm, ecology, and route state
3. Update object accessibility from location, route, institution, and custody
4. Evaluate record/evidence access demands
5. Feed blocked object, record, or evidence access into capacity demands
6. Select affordance and action
7. Emit attention/object access events when objects are handled or avoided
8. Build NarrativeBeat using registered object refs
9. Render with object registry excerpt
10. Persist object state updates and access traces
```

Objects should feed simulation through capacities:

```text
evidence_access
truth_disclosure
repair
care
exit
financial_survival
public_legitimacy
institutional_recording
```

They should not directly generate drama.

Invalid:

```text
old_tape_yellow_bleed -> dramatic scene
```

Valid:

```text
old_tape_yellow_bleed restricted and contaminated
-> evidence_access capacity narrows
-> direct testimony becomes riskier
-> recognition claim deforms into avoided speech
```

---

## 13. Rendering Contract

Render payloads may include:

```text
active_object_refs
active_record_refs
active_evidence_refs
object_access_context
record_authority_context
evidence_interpretive_context
forbidden_object_inventions
```

The LLM may:

- describe registered objects
- describe visible state of registered objects
- use object state to ground gesture or omission
- mention access restriction if provided
- mention uncertainty if provided

The LLM may not:

- invent new durable objects
- invent new documents
- invent new messages
- invent new evidence
- invent new custody changes
- change object condition
- make a record official
- make evidence reliable or unreliable
- resolve what evidence proves

Segment validation should reject:

```text
new durable noun phrases not in registry or ephemeral whitelist
new evidence claims
new document claims
new weapon claims
new message claims
new location-object links
new object state changes
```

---

## 14. Viewer Support

The viewer should eventually expose:

```text
Registry
- objects in active location
- records in active institution
- evidence items and current status
- object access results
- custody changes
- object state changes
- narrative beats using each object
```

For investigative scenarios, a useful panel is:

```text
Evidence Board
- evidence item
- physical location
- custody holder
- access status
- reliability
- contamination risk
- linked records
- linked testimonies
- latest source event
```

This panel should show simulation state, not LLM prose.

---

## 15. Implementation Phases

### Phase 1: Scenario Registry Model

Implement:

```text
ObjectRegistrySpec
WorldObjectSpec
RecordObjectSpec
EvidenceObjectSpec
AccessTokenSpec
ObjectLinkSpec
```

Acceptance:

```text
scenario YAML can declare registry objects
all registry location refs exist in LocalWorld
all evidence_refs in LocalWorld resolve to registry evidence objects or case ledger entries
all record refs in institutions resolve to registry record objects
```

### Phase 2: Read-Only Runtime Projection

Implement:

```text
object_registry_view
active objects by scene location
active evidence by scene type
record access summary by institution
```

Acceptance:

```text
viewer payload includes active registry refs
LLM payload receives only relevant registry excerpt
rendering can mention registered objects without inventing them
```

### Phase 3: Access Events

Implement:

```text
ObjectAccessEvent
RecordAccessEvent
EvidenceAccessEvent
```

Acceptance:

```text
restricted evidence emits access result
record access depends on institution and location
access failures feed capacity demands
```

### Phase 4: Narrative Beat Integration

Implement:

```text
NarrativeBeat.object_refs
NarrativeBeat.record_refs
NarrativeBeat.evidence_refs
```

Acceptance:

```text
beats cite registered objects
unregistered durable objects are rejected
repetition compression can identify repeated object use
```

### Phase 5: State Updates and Custody

Implement:

```text
ObjectStateUpdateEvent
RecordStateUpdateEvent
EvidenceStateUpdateEvent
CustodyChangeEvent
```

Acceptance:

```text
object state changes are event-backed
evidence reliability/access/custody changes are auditable
replay reconstructs registry state
```

---

## 16. Evaluation Criteria

The registry succeeds when:

- scenes have stable material anchors
- repeated objects accumulate meaning without becoming vague symbols
- evidence access is separated from evidence truth
- records can be incomplete, inaccessible, unofficial, or illegible in different ways
- LLM prose cannot invent durable props
- narrative beats can cite concrete objects
- viewer can explain why an object mattered
- replay reconstructs object and evidence state

It fails when:

- objects appear only in prose
- evidence status changes without events
- every scene uses generic "file", "phone", "door", or "table" objects
- records are treated as true just because they exist
- case ledger facts mutate object geography
- LLM-created details become hidden state
- object state becomes an unbounded prose archive

---

## 17. Non-Negotiable Invariants

```text
1. Durable objects must be registered, discovered, or event-created.
2. Object existence is separate from object access.
3. Record existence is separate from record authority.
4. Evidence access is separate from evidence truth.
5. Custody is separate from ownership.
6. LLM prose may not create durable objects, records, evidence, messages, or custody changes.
7. Attention may open object detail gaps but may not update object state by itself.
8. Causal object details require event-backed validation.
9. Narrative beats should cite registry refs when using durable things.
10. Registry state must be replayable from scenario plus events.
11. LocalWorld geography and ObjectRegistry material state must not overwrite each other.
12. CaseLedger epistemic claims must not overwrite registry material state without events.
```

---

## 18. Summary

RPF needs a durable material layer between local-world geography and narrative rendering.

Without it, scenes float between abstract causal traces and LLM-generated atmosphere.

With it, the simulator can track:

```text
where the file is,
who can open it,
whether the label is readable,
who touched it,
whether it became official,
why it cannot simply be ignored,
and why seeing it again changes the relation.
```

This layer makes stories more concrete without giving the LLM plot authority.
