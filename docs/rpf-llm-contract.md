# RPF LLM Boundary and Prompt Contract

## 0. Purpose

This document defines how LLMs may be used in RPF.

The core rule:

```text
The LLM renders and proposes.
The simulator decides and mutates state.
```

The LLM must never be allowed to become the causal authority of the simulation.

---

## 1. Allowed LLM Roles

The LLM may:

- render a scene into prose
- generate dialogue candidates
- generate gesture candidates
- summarize event history for a human
- produce perspective-limited interpretations
- translate structured state into readable descriptions
- help author scenario drafts that are then validated

The LLM may not:

- update causal state directly
- decide final consequences
- create irreversible events on its own
- modify trust, intimacy, resentment, personality, or relationship state
- invent unavailable actions
- override field constraints
- treat PersonView as primitive personality

---

## 2. LLM Call Types

```text
1. Scene Rendering
2. Dialogue Candidate Generation
3. Gesture Candidate Generation
4. Perspective-Limited Interpretation
5. Human Summary
6. Scenario Authoring Assistant
```

Each call type requires a schema.

---

## 3. Common Input Envelope

Every LLM call receives:

```json
{
  "call_type": "scene_rendering",
  "simulation_id": "sim-001",
  "tick": 12,
  "scene_id": "scene-004",
  "allowed_task": "render_only",
  "state_authority": "simulator",
  "perspective_limits": {},
  "forbidden_outputs": [
    "state mutation",
    "direct trait causation",
    "unlicensed irreversible event"
  ],
  "context": {}
}
```

---

## 3.1 Render Canon

Scene rendering calls also receive `render_canon`.

`render_canon` is not causal simulation state.

It is the locked surface reality used for literary rendering:

```json
{
  "title": "共享公寓：未解决的牺牲",
  "setting": {
    "place": "共享公寓",
    "period": "当代城市",
    "atmosphere": "克制、逼仄、日常压力持续存在"
  },
  "cast": {
    "p1": {
      "name": "许知遥",
      "gender": "女",
      "pronoun": "她",
      "surface_role": "更常承担日常事务和费用垫付的人",
      "speech_style": "克制、短句、很少直接索取"
    },
    "p2": {
      "name": "沈砚",
      "gender": "男",
      "pronoun": "他",
      "surface_role": "更常回避确认与承认的人",
      "speech_style": "解释多于承认，倾向拖延或转移"
    }
  },
  "narration": {
    "style": "克制的现实主义文学",
    "perspective": "第三人称限制视角",
    "forbidden": ["新增亲属关系", "新增职业", "新增未来预告"]
  }
}
```

The LLM must inherit:

- names
- genders
- pronouns
- setting
- narrative style
- forbidden facts

The LLM may not invent these at render time.

This resolves the main tension:

```text
literary specificity comes from render_canon
causal facts come from simulation events
style realization comes from the LLM
```

---

## 4. Scene Rendering Contract

### 4.1 Input

```json
{
  "call_type": "scene_rendering",
  "render_canon": {},
  "current_scene": {},
  "source_events": [],
  "active_rpps": [],
  "person_views": [],
  "relationship_view": {},
  "relevance_landscapes": {},
  "recognition_conflicts": [],
  "forbidden_knowledge": [],
  "style_constraints": {
    "no_exposition_of_hidden_state": true,
    "perspective": "limited"
  }
}
```

### 4.2 Output

```json
{
  "narration": "string",
  "visible_actions": ["string"],
  "spoken_lines": [
    {
      "speaker": "process_id",
      "line": "string",
      "source_event_ref": "event_id"
    }
  ],
  "unspoken_tensions": ["string"],
  "rendering_notes": ["string"]
}
```

### 4.3 Hard Limits

Rendering may not introduce:

- new causal events
- new facts not present in source events
- new names, genders, occupations, locations, or relationships not present in render_canon
- hidden motives outside perspective limits
- future predictions
- direct explanations like "because his trust score fell"

---

## 5. Dialogue Candidate Contract

### 5.1 Input

```json
{
  "call_type": "dialogue_candidates",
  "scene_frame": {},
  "speaker_process": "process_id",
  "addressee_process": "process_id",
  "permissible_speech": [],
  "forbidden_speech": [],
  "active_rpps": [],
  "face_risks": [],
  "recognition_pressure": [],
  "candidate_count": 5
}
```

### 5.2 Output

```json
{
  "candidates": [
    {
      "line": "string",
      "directness": 0.0,
      "face_risk": 0.0,
      "recognition_implication": "string",
      "compatible_rpps": ["rpp_id"],
      "violates_constraints": false
    }
  ]
}
```

The simulator selects or rejects candidates.

---

## 6. Gesture Candidate Contract

```json
{
  "candidates": [
    {
      "gesture": "string",
      "visibility": "private|public|ambiguous",
      "face_risk": 0.0,
      "possible_interpretations": ["string"],
      "compatible_micro_signal_types": ["string"]
    }
  ]
}
```

Gestures become `MicroSignalEvent` only if accepted by the simulator.

---

## 7. Perspective-Limited Interpretation Contract

The LLM may help verbalize how a process position might experience an event.

It must stay within the provided relevance landscape and memory activations.

```json
{
  "process_id": "process_id",
  "observed_event": "event_id",
  "possible_interpretations": [
    {
      "interpretation": "string",
      "confidence": 0.0,
      "evidence_refs": ["event_id"],
      "unsupported_additions": []
    }
  ]
}
```

The simulator decides which interpretation becomes an `ObservationEvent`.

---

## 8. Prompt Rules

Every prompt must state:

```text
You are not the simulator.
You may not update state.
You may not decide consequences.
You may only operate within supplied constraints.
Return only the requested schema.
```

Prompts must include:

- allowed task
- forbidden outputs
- available facts
- perspective limits
- schema
- examples of invalid output

---

## 9. Validation Rules

Reject LLM output if:

- schema invalid
- mentions direct state mutation
- invents unavailable scene facts
- introduces hidden motive as fact
- creates irreversible consequence
- uses high-level aggregate as causal explanation
- violates perspective limits
- ignores forbidden speech/action constraints

Validation result must be stored as:

```text
LLMCandidateEvent
```

or:

```text
RenderingEvent
```

---

## 10. Repair Strategy

If LLM output fails validation:

1. reject invalid fields
2. optionally retry with validation errors
3. if retry fails, use deterministic fallback
4. record rejection

Do not silently accept invalid output.

---

## 11. Deterministic Fallbacks

Fallbacks should exist for:

- no dialogue candidate
- no rendering
- invalid gesture
- over-invented interpretation

Example fallback:

```text
render event summaries directly from event payloads
```

The simulator must remain functional without LLM.

---

## 12. Security of Ontology

The LLM is the most likely place where the system will regress into DRAF-like behavior.

Therefore enforce:

- no direct trait causation
- no hidden omniscience
- no relationship score explanations
- no plot invention
- no unlicensed psychology
- no causal consequences outside event system

---

## 13. Example Invalid Output

Invalid:

```json
{
  "narration": "Because A's trust dropped, she became avoidant."
}
```

Valid:

```json
{
  "narration": "She paused before answering. When she finally spoke, she kept the sentence practical.",
  "visible_actions": ["pause before answering"],
  "spoken_lines": []
}
```


