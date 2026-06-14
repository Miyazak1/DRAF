# RPF Expression and Personhood Extensions

## 0. Purpose

This document defines how RPF can be extended to produce more concrete person-like expression without returning to personality-card modeling.

The core rule is:

```text
Do not add more traits to people.
Add mechanisms by which relational processes become expressive form.
```

RPF does not delete the person. It relocates the person to a higher emergent layer.

This document specifies optional post-MVP extensions for:

- language style
- bodily expression
- habits and rituals
- desire and fantasy
- taste and class habitus
- relation-specific selves
- expressive continuity

These mechanisms should not block the MVP kernel.

---

## 1. Extension Principle

Every expressive feature must be generated from lower-level structures:

```text
field position
+ embodied habitus
+ relevance landscape
+ recognition pressure
+ ritual frame
+ active RPPs
+ irreversible history
+ operative classifications
-> expressive form
```

Invalid:

```text
A is sarcastic.
A is cold.
B is affectionate.
B is avoidant.
```

Valid:

```text
Under high face risk, A uses humor to avoid direct vulnerability.
When recognition pressure rises, B turns apology into practical help.
When silence has been classified as punishment, delayed speech becomes charged.
```

---

## 2. Expression Layer

Add an optional layer after action availability and before LLM rendering:

```text
Action Possibility
-> Expressive Form Selection
-> Communication / Gesture Candidate
-> Observation and Recognition Effects
```

Expression does not decide what structurally happens.

It decides the form through which an available action appears.

Example:

```text
available action: attempt repair
possible expressive forms:
- direct apology
- joke
- practical help
- food
- touch
- silence plus proximity
- logistical offer
```

The selected form depends on scene and process constraints.

---

## 3. Language Style Mechanism

### 3.1 Purpose

Language style makes process positions recognizable without assigning fixed personality traits.

### 3.2 Source Structures

```text
speech_inhibition
face_risk
recognition_demand
field_position
audience_pressure
active_rpp
operative_classification
fatigue
```

### 3.3 Language Features

```text
LanguageStyleState
- directness
- sentence_length
- pronoun_use
- question_frequency
- hedging
- irony
- practical_deflection
- emotional_specificity
- temporal_reference
- accusation_disguise
- repair_explicitness
```

### 3.4 Generation Rules

Examples:

```text
high speech_inhibition.direct_need
-> lower directness
-> higher practical deflection
-> fewer first-person need statements
```

```text
high face risk + audience present
-> more politeness
-> more ambiguity
-> more joking or understatement
```

```text
active contribution_debt_loop
-> practical topics carry moral charge
-> phrases like "don't worry about it" may become hostile or self-protective
```

### 3.5 Anti-Pattern

Do not store:

```text
A.language_style = cold
```

Store:

```text
language form changes by scene constraint and history
```

---

## 4. Bodily Expression Mechanism

### 4.1 Purpose

Human relation is embodied. A process position should not express only through dialogue.

### 4.2 Source Structures

```text
body_position
arousal_level
fatigue
threat_sensitivity
spatial_constraint
ritual_frame
recognition_pressure
active_rpp
bodily_memory_refs
```

### 4.3 Bodily Expression State

```text
BodilyExpressionState
- posture
- gaze
- distance
- touch_availability
- object_handling
- movement_toward
- movement_away
- stillness
- breath_visibility
- task_absorption
```

### 4.4 Examples

```text
high threat_sensitivity.being_controlled
+ spatial constraint
-> increased distance-seeking
-> doorway orientation
-> shorter gaze duration
```

```text
repair desire + apology inhibition
-> practical care gesture
-> object handling
-> food, cleaning, fixing, carrying
```

```text
recognition demand unspeakable
-> stillness
-> delayed answer
-> gaze drop
```

### 4.5 Principle

Bodily expression can create `MicroSignalEvent`.

It becomes causally significant only if observed or incorporated into the scene.

---

## 5. Habit and Ritual Mechanism

### 5.1 Purpose

People become concrete through repeated small forms.

RPF should track how repeated actions become relation-specific rituals.

### 5.2 Habit Schema

```text
HabitPattern
- habit_id
- participating_processes
- scene_context
- trigger_conditions
- expressive_form
- relational_function
- recognition_function
- repair_function
- repetition_count
- disruption_meaning
- evidence_refs
```

### 5.3 Examples

```text
who makes tea after conflict
who closes the door first
who texts "home?" instead of "are you safe?"
who cleans after refusing apology
who avoids one room after a fight
who uses work as exit route
```

### 5.4 Ritual Disruption

A broken habit can become more meaningful than an explicit statement.

Example:

```text
B usually leaves a cup by A's desk after conflict.
One day B does not.
```

This may generate:

```text
MicroSignalEvent
RelevanceShiftEvent
RecognitionEvent
```

depending on history.

---

## 6. Desire and Fantasy Mechanism

### 6.1 Purpose

Desire should not be modeled as simple goal pursuit.

In RPF, desire is a relation between lack, recognition, imagined future, and self-continuity.

### 6.2 Desire Schema

```text
DesireFormation
- desire_id
- holder_process
- desired_state
- recognition_component
- fantasy_scene
- threat_if_fulfilled
- threat_if_denied
- relation_to_field_position
- relation_to_irreversibility
- explicitness
```

### 6.3 Desire Types

```text
to be chosen
to be released
to be needed
to prove independence
to make the other admit harm
to return to an imagined earlier relation
to become visible without becoming vulnerable
to be forgiven without confessing
```

### 6.4 Rule

Desire must be internally contradictory often enough to be human.

Example:

```text
A wants B to need them,
but if B needs them, A experiences the relation as a trap.
```

This contradiction can activate:

```text
complementary_dependency
pursuit_withdrawal
double_bind
```

---

## 7. Taste and Class Habitus Mechanism

### 7.1 Purpose

Person-like specificity comes from social formation, not just psychology.

Taste determines what feels:

- respectable
- embarrassing
- cheap
- excessive
- mature
- childish
- loyal
- vulgar
- refined
- desperate

### 7.2 Taste Profile

```text
TasteHabitus
- comfort_objects
- shame_objects
- valued_speech_forms
- disallowed_speech_forms
- respectability_markers
- vulgarity_markers
- gift_interpretation_rules
- money_talk_rules
- care_style_preferences
- conflict_style_legitimacy
```

### 7.3 Examples

```text
For one position, discussing rent directly is responsible.
For another, it is humiliating and relationship-contaminating.
```

```text
For one position, expensive gifts repair.
For another, they create debt or insult.
```

Taste should alter:

- relevance
- face risk
- speech availability
- gift interpretation
- repair form selection

---

## 8. Relation-Specific Self Mechanism

### 8.1 Purpose

A process position does not express the same self everywhere.

The person-like interface should include relation-specific selves.

### 8.2 Schema

```text
RelationSpecificSelf
- process_id
- relation_target
- activated_roles
- speech_forms
- unavailable_actions
- expected_injuries
- expected_repairs
- self_narrative_in_relation
- imposed_labels_in_relation
- stabilization_strength
```

### 8.3 Examples

```text
with B: caretaker, creditor, unrecognized one
with friends: competent, humorous, not needy
with family: dutiful, silent, child-positioned
with work: reliable, self-erasing
```

### 8.4 Rule

A contradiction between relation-specific selves can generate drama.

Example:

```text
A's public self is competent and self-contained.
B has seen A's dependency.
This gives B recognition power and face-threatening knowledge.
```

---

## 9. Expressive Continuity

### 9.1 Purpose

Person-like realism requires continuity without fixed traits.

### 9.2 Continuity Sources

```text
repeated expressive forms
habit patterns
stable speech constraints
body memory
operative classifications
relation-specific expectations
field-position continuity
```

### 9.3 Continuity Rule

The same deep pattern may surface differently.

Example:

```text
repair avoidance
-> joke in public
-> cooking at home
-> work message in professional scene
-> silence in high-shame scene
```

The person feels continuous because the relational function is continuous, not because the surface behavior repeats exactly.

---

## 10. Integration With Existing RPF Layers

### 10.1 Runtime Placement

Expression extension runs after:

```text
action affordance evaluation
```

and before:

```text
communication event finalization
```

### 10.2 Event Types

Possible additional events:

```text
ExpressiveFormSelectedEvent
HabitPatternActivatedEvent
HabitPatternDisruptedEvent
DesireFormationEvent
TasteInterpretationEvent
RelationSpecificSelfUpdateEvent
```

These should be added only after MVP event sourcing is stable.

### 10.3 Aggregation Impact

Expression data may contribute to:

- PersonView
- RelationshipView
- TrustView
- IntimacyView
- RepairCapacityView
- NarrativeLabel candidates

It must not bypass the aggregation system.

---

## 11. MVP Boundary

Do not implement this extension in the first MVP kernel.

The MVP should prove:

- event sourcing
- RPP activation
- recognition and misrecognition
- derived views
- operative classification
- irreversibility
- replay

Expression extensions should begin after the MVP can already run without them.

---

## 12. Failure Modes

The extension has failed if:

- language style becomes a fixed personality field
- body gestures are decorative only
- habits do not affect future relevance
- desire becomes simple goal pursuit
- taste becomes aesthetic trivia
- relation-specific selves are treated as masks over a true core self
- LLM invents expression without simulator constraints

---

## 13. Summary

RPF can become more person-specific by adding expressive mechanisms.

But the rule remains:

```text
Concrete personhood is generated expression,
not prewritten character detail.
```

The system should eventually make a process position recognizable through:

- what it can say
- what it cannot say
- how it repairs
- what it notices
- what it avoids
- what it repeats
- what it finds shameful
- what it turns into a habit
- who it becomes in each relation

This is how RPF can grow from structural realism into lived relational realism.


