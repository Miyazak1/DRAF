# RPF Simulation Runtime Specification

## 0. Purpose

This document defines how an RPF simulation runs.

It describes the lifecycle of:

- simulation
- tick
- episode
- scene
- RPP activation
- aggregation
- irreversible history

The runtime must preserve the RPF ontology:

```text
processes and relational patterns generate persons;
persons do not drive the simulation as primitive agents.
```

---

## 1. Runtime Overview

The simulator advances by ticks.

A tick is not a turn in a conversation. A tick is a structured update cycle.

```text
Tick
-> field pressure evaluation
-> binding evaluation
-> trace-only constraint activation
-> trace-only viability requirement activation
-> trace-only affordance width measurement
-> derived future-constraint feedback from prior history
-> situated affordance selection
-> scene crystallization
-> trace-only deformation and derived dramatic tension measurement
-> RPP activation
-> relevance update
-> ritual framing
-> communication / action event
-> second-order observation
-> recognition evaluation
-> repair / escalation / avoidance
-> stabilization update
-> irreversibility update
-> memory reconstruction
-> environment sedimentation
-> process disposition sedimentation
-> relation sedimentation
-> binding / expectation / account / norm / frame / relevance / position field refresh
-> aggregation and projection
-> persistence
```

---

## 2. Simulation Lifecycle

```text
created
-> initialized
-> running
-> paused
-> complete
```

### 2.1 Created

The simulation has a configuration but no validated state.

Required inputs:

- scenario file
- RPP library
- simulation config
- seed

### 2.2 Initialized

The simulator has:

- valid `SimulationState`
- at least two `ProcessState` objects
- valid `FieldState`
- at least one possible co-presence binding
- valid RPP library

### 2.3 Running

Ticks are being executed.

Every tick must either:

- emit at least one event, or
- explicitly emit `NoSceneEvent` / `LatentTimeEvent`

Silence and non-encounter are still simulated facts.

### 2.4 Complete

A simulation may complete when:

- max ticks reached
- bindings decay below continuation threshold
- terminal irreversible condition occurs
- user stops experiment
- scenario-defined endpoint is reached

---

## 3. Tick Contract

Each tick must be deterministic given:

```text
previous_state
seed
tick_index
RPP_library
scenario_config
event_history
```

If probabilistic sampling is used, it must use seeded randomness and record the sampled candidates.

### 3.1 Tick Definition

A tick is the smallest replayable causal transaction in the simulator.

It is not necessarily:

- one sentence
- one conversational turn
- one hour
- one scene
- one user-visible event

It is:

```text
one atomic update cycle in which the simulator evaluates whether relational structure has changed
```

Each tick has:

```text
tick_index
tick_type
simulated_time_delta
causal_scope
event_set
state_delta
```

### 3.2 Tick Types

RPF uses three tick types:

```text
latent
micro_interaction
scene
```

These are not merely labels. They determine which runtime stages are required, what time scale is plausible, and what kinds of events are expected.

---

### 3.3 Latent Tick

A latent tick represents relational time passing without direct interaction.

It models:

- waiting
- avoidance
- delayed response
- field pressure accumulation
- fatigue accumulation
- binding decay or intensification
- memory activation without contact
- latent recognition pressure

Typical real-time mapping:

```text
minutes to days
```

Examples:

```text
six hours without a reply
one day before rent is due
a workday in which no one mentions the conflict
a night spent in separate rooms
```

Required evaluations:

```text
field pressure
binding pressure
latent relevance shift
RPP decay or pressure accumulation
aggregation refresh
```

Expected events:

```text
LatentTimeEvent
FieldPressureEvent optional
LatentRelationEvent optional
RelevanceShiftEvent optional
AggregationEvent
ProjectionEvent
```

Latent ticks are essential because many relationships change through non-action.

---

### 3.4 Micro-Interaction Tick

A micro-interaction tick represents a small contact or signal that may or may not become meaningful.

It models:

- eye contact
- message read without reply
- a short answer
- passing in a hallway
- a changed routine
- object placement
- tone shift
- a door closed differently
- practical help without speech

Typical real-time mapping:

```text
seconds to minutes
```

or:

```text
one message exchange
one gesture
one small co-presence moment
```

Required evaluations:

```text
micro signal detection
observation
relevance shift
RPP eligibility
recognition implication optional
aggregation refresh
```

Expected events:

```text
MicroSignalEvent
ObservationEvent
RPPActivationEvent optional
RecognitionEvent optional
AggregationEvent
ProjectionEvent
```

A micro-interaction tick may escalate into a scene tick if the signal crosses scene crystallization threshold.

---

### 3.5 Scene Tick

A scene tick represents a structured interaction episode or a meaningful phase inside one.

It models:

- argument
- apology attempt
- negotiation
- shared task
- public performance
- confession
- confrontation
- departure
- exposure

Typical real-time mapping:

```text
minutes to hours
```

or:

```text
one coherent interaction phase
```

Required evaluations:

```text
scene crystallization
ritual frame
communication/action/omission
second-order observation
recognition/misrecognition
repair/escalation/avoidance
stabilization
irreversibility
aggregation and projection
```

Expected events:

```text
SceneCrystallizationEvent
RitualFrameEvent
CommunicationEvent / ActionEvent / SilenceEvent / OmissionSignalEvent
ObservationEvent
RecognitionEvent / MisrecognitionEvent
RepairEvent / EscalationEvent / AvoidanceEvent
StabilizationEvent
IrreversibilityEvent optional
AggregationEvent
ProjectionEvent
```

---

### 3.6 Time Mapping

RPF uses event-driven ticks with simulated time deltas.

Do not use fixed time steps as the primary runtime.

Instead:

```text
tick_type determines the plausible time delta range
field pressure and bindings determine when the next tick occurs
```

Recommended default ranges:

```text
latent:
  min: 15 minutes
  max: 3 days

micro_interaction:
  min: 1 second
  max: 15 minutes

scene:
  min: 5 minutes
  max: 6 hours
```

Scenarios may override these ranges.

Each tick must record:

```text
simulated_time_start
simulated_time_end
simulated_time_delta
time_mapping_reason
```

Examples:

```text
latent tick:
  delta: 8 hours
  reason: "overnight non-reply while rent pressure increased"

micro_interaction tick:
  delta: 20 seconds
  reason: "kitchen doorway co-presence produced gaze avoidance signal"

scene tick:
  delta: 47 minutes
  reason: "rent discussion became recognition conflict"
```

### 3.7 Tick Upgrade and Downgrade Rules

A latent tick upgrades to micro-interaction when:

- a message arrives
- co-presence occurs
- a routine is disrupted
- a micro signal is generated
- field pressure forces brief contact

A micro-interaction upgrades to scene when:

- recognition pressure crosses threshold
- an active RPP escalates
- communication cannot remain ritual-minimal
- face threat requires repair
- an irreversible utterance/action becomes possible

A scene may downgrade to latent when:

- participants separate
- avoidance succeeds
- ritual closure occurs
- repair lowers immediate pressure
- exhaustion blocks further interaction

A scene may split into multiple scene ticks when:

- the ritual frame changes
- audience changes
- location changes
- the interaction phase changes
- an irreversible event creates a new scene problem

### 3.8 Tick Atomicity

All events in a tick are applied as one transaction.

Invalid:

```text
RPPActivationEvent is persisted but its triggering ObservationEvent is lost.
```

Valid:

```text
all events in tick N are persisted together with state hash after tick N
```

### 3.9 Tick Is Allowed to Be Quiet

A tick may contain no visible interaction.

It may not contain no explanation.

If nothing visible happens, emit:

```text
LatentTimeEvent
```

or:

```text
NoSceneEvent
```

with pressure and binding diagnostics.

### 3.10 Tick Input

```text
TickInput
- simulation_state
- event_history_window
- rpp_library
- runtime_config
- random_stream
- requested_tick_type optional
- simulated_time_context
```

### 3.11 Tick Output

```text
TickOutput
- tick_type
- simulated_time_delta
- events
- new_state
- derived_views
- rendered_output optional
- diagnostics
```

---

## 4. Tick Pipeline

### Step 1: Load and Validate State

Validate:

- all referenced IDs exist
- no derived view is being used as causal input
- open episodes are consistent
- active RPPs refer to valid processes
- irreversible records refer to source events

Emit:

```text
StateValidationEvent
```

only when diagnostics need to be recorded.

### Step 2: Evaluate Field Pressures

Field pressures identify changes in the field that matter for current processes.

Examples:

- rent due
- work deadline
- family obligation
- physical exhaustion
- spatial constraint
- reputational exposure
- institutional demand

Output:

```text
FieldPressureEvent
```

### Step 3: Evaluate Co-Presence Bindings

For each binding, compute:

```text
binding_strength
exit_cost
asymmetry
urgency
encounter_likelihood
```

If no binding crosses threshold:

```text
LatentRelationEvent
```

may be emitted.

Bindings are not static rails.

At the end of a tick, relation history may update binding strength or exit cost. The next tick's scheduler and viability evaluation then consume the changed binding.

Valid binding evolution sources:

- `FieldPressureEvent`
- `RepairEvent`
- `AvoidanceEvent`
- `DisplacementEvent`
- `RelationSedimentationEvent`

Outputs:

```text
BindingUpdatedEvent
BindingDecayedEvent
binding_trace.json
```

Rules:

- binding evolution must cite event evidence
- changes must remain bounded and gradual
- latent time may slightly loosen unrenewed binding strength
- unresolved recognition, symbolic accounting, repair narrowing, public definition, asymmetry, shared fate, and future lock may tighten relevant bindings or raise exit cost
- repair may reduce exit cost without deleting co-presence
- binding changes affect later ticks, not the already selected current tick

This is the runtime mechanism for why two processes continue to cross paths even when neither "chooses" a scene.

### Step 4: Crystallize Candidate Scene

The simulator first selects a situated affordance: the interaction form made most available by the current field, bindings, process constraints, and active RPP/composition ecology.

Sedimented field pressures may also shape affordance selection.

Examples:

- `spatial_constraints.avoidance_paths` makes delay, bodily avoidance, or route-based non-contact more available
- `material_pressures.charged_objects` makes practical repair or material pressure intrusion more available
- `audience_pressure.imagined_audience` makes public performance or face-saving forms more available

Do not ask:

```text
What signal should happen on this tick?
```

Ask:

```text
Which interaction form has become available enough to occur?
```

Emit:

```text
AffordanceSelectionEvent
```

Every non-latent tick writes an affordance diagnostic containing selected affordance and rejected candidates.

### Step 5: Select Action / Inhibition

Affordance is not action.

After an affordance is selected, the runtime evaluates what the process position can actually do with it:

- direct enactment
- inhibited omission
- practical substitution
- public substitution
- explicit recognition claim

Action selection consumes:

- affordance score
- speech inhibition
- repair debt
- conflict pressure
- audience and face risk
- reconstructed memory pressure
- fate memory

Emit:

```text
ActionSelectionEvent
ActionInhibitionEvent optional
ActionSubstitutionEvent optional
```

The selected action determines the actual `MicroSignalEvent`.

This prevents the simulator from assuming that what becomes possible is what a process can straightforwardly do.

Every non-latent tick writes an action diagnostic containing selected action and rejected candidates.

### Step 6: Select Expression

Expression is how a selected action becomes observable.

The same action may appear as:

- plain speech
- tightened tone
- hesitation
- displaced gesture
- charged silence
- public mask

Expression selection consumes:

- action mode
- speech inhibition
- fatigue
- audience and face risk
- repair debt
- conflict pressure
- memory pressure
- fate memory

Emit:

```text
ExpressionSelectionEvent
```

Expression determines the surface signal, tone, gesture, timing, ambiguity, and observable relation claim used by `MicroSignalEvent` and `ObservationEvent`.

Every non-latent tick writes an expression diagnostic containing selected expression and rejected candidates.

### Step 7: Crystallize Candidate Scene

A scene forms when field pressure, binding, and selected affordance produce local co-presence.

Scene crystallization chooses:

- participants
- location
- frame
- declared activity
- hidden activities
- audience
- timing
- active constraints

Emit:

```text
SceneCrystallizationEvent
```

### Step 8: Detect Micro Signals

Micro signals are low-level differences in the scene or micro-interaction.

They are generated from selected expression rather than tick parity, plot sequence, affordance alone, or action alone.

They may be shaped by:

- prior field state
- body state
- ritual frame
- selected communication
- omitted communication
- active RPP composition

Emit:

```text
MicroSignalEvent
```

### Step 9: Activate RPPs

For each RPP:

1. Check eligibility.
2. Compute activation score.
3. Apply contraindications.
4. Sample or select active RPPs.
5. Emit activation evidence.

Emit:

```text
RPPActivationEvent
RPPNonActivationEvent optional
```

### Step 10: Update Relevance Landscapes

For each process position, update event-sourced relevance markers:

- delayed reply / absence salience
- recognition claim salience
- public exposure salience
- being controlled salience
- double bind salience
- material cost salience
- repair opening salience
- exit threat salience

These are not private attention meters. They are relation-and-field-produced markers of what the process can no longer treat as background.

Valid sources include:

- `FieldPressureEvent`
- `AffordanceSelectionEvent`
- `MicroSignalEvent`
- `ObservationEvent`
- `RecognitionEvent`
- `MemoryReconstructionEvent`
- `NormativePressureEvent`
- `FrameDefinitionEvent`
- `RelationSedimentationEvent`

Emit:

```text
RelevanceShiftEvent
relevance_trace.json
```

Rules:

- relevance shifts must cite event evidence.
- relevance markers use the `relevance_field.{process}.{marker}` prefix.
- relevance may influence later scheduler rhythm, affordance selection, RPP activation, and memory reconstruction.
- relevance must decay when not renewed.
- relevance must not be rendered as a private motive unless the lower event chain is cited.

### Step 9: Establish Ritual Frame

Determine:

- front-stage roles
- back-stage knowledge
- face risks
- permissible speech
- forbidden speech
- repair options
- exit routes

Emit:

```text
RitualFrameEvent
```

### Step 10: Produce Communication or Action Event

Action is selected from available action possibilities.

Do not ask:

```text
What does this person want to do?
```

Ask:

```text
Which actions are available to this process position in this scene?
```

Emit:

```text
CommunicationEvent
ActionEvent
OmissionEvent
SilenceEvent
```

### Step 11: Second-Order Observation

Each process interprets:

- content
- utterance form
- timing
- omission
- relationship claim
- how it is being seen
- what the other thinks it sees

Emit:

```text
ObservationEvent
MisinterpretationEvent optional
```

### Step 11.5: Expectation Sedimentation

Observed interaction may sediment into second-order expectations:

- expected refusal
- expected misrecognition
- expected withdrawal
- expected public exposure
- expected repair avoidance

Valid sources:

- `ObservationEvent`
- `RecognitionEvent`
- `RepairEvent`
- `AvoidanceEvent`
- `DisplacementEvent`
- `RelationSedimentationEvent`

Output:

```text
ExpectationSedimentationEvent
expectation_trace.json
```

Rules:

- expectation sedimentation is relation-specific
- it must cite observable events
- it is not private belief, inner monologue, or motive
- it may affect later `ActionSelectionEvent` and `ExpressionSelectionEvent`
- unreinforced expectations decay over time

This is the mechanism by which a process acts not only toward the other, but toward what it expects the other will see, refuse, misunderstand, or avoid.

### Step 11.6: Account Pressure Projection

Observable history may also project into account pressure:

- safety
- dignity
- control
- relation
- meaning
- energy

These are not primitive inner meters. They are bounded, event-sourced viability pressures.

Valid sources:

- `FieldPressureEvent`
- `RecognitionEvent`
- `RepairEvent`
- `AvoidanceEvent`
- `DisplacementEvent`
- `MisrecognitionEvent`
- `ExpectationSedimentationEvent`
- `RelationSedimentationEvent`

Output:

```text
AccountPressureEvent
account_trace.json
```

Rules:

- account pressure must cite event evidence
- it may affect later action, expression, and recognition evaluation
- it must decay when not reinforced
- it must not be rendered as private emotion unless the renderer cites the event chain

This layer explains why the same act can become costly as dignity threat, control threat, meaning collapse, relation strain, safety strain, or energy depletion without making emotion a primitive variable.

### Step 11.7: Normative Pressure Projection

Observable history may also project into normative pressure:

- claim entitlement
- repair obligation
- public face obligation
- legitimacy contestation
- reciprocity obligation
- exit justification
- mutual obligation
- irreversible precedent

These are not moral truths and not hidden values. They are bounded, event-sourced social-form pressures: what the relation has made claimable, owed, contestable, publicly risky, or easier to justify.

Valid sources:

- `FieldPressureEvent`
- `RecognitionEvent`
- `RepairEvent`
- `AvoidanceEvent`
- `DisplacementEvent`
- `MisrecognitionEvent`
- `OperativeClassificationEvent`
- `IrreversibilityEvent`
- `ExpectationSedimentationEvent`
- `AccountPressureEvent`
- `RelationSedimentationEvent`

Output:

```text
NormativePressureEvent
normativity_trace.json
```

Rules:

- normative pressure must cite event evidence.
- it may affect later action, expression, and recognition evaluation.
- it must decay when not socially renewed.
- it must not decide who is morally correct.
- it must not be rendered as narrator judgment unless the renderer cites the event chain.

This layer explains how injury, expectation, audience pressure, and relation sediment become obligations and entitlements without making "morality" a primitive variable.

### Step 11.8: Interaction Frame Definition

Observable history may also sediment a definition of what kind of situation the interaction has become:

- debt accounting
- repair scene
- avoidance scene
- public performance
- care/control
- double bind
- material accounting
- recognition trial

These are not narrative scenes and not private interpretations. They are bounded, event-sourced frame pressures that define which meanings and actions become easier to take up next.

Valid sources:

- `AffordanceSelectionEvent`
- `ExpressionSelectionEvent`
- `RecognitionEvent`
- `NormativePressureEvent`
- `RelationSedimentationEvent`
- `FieldUpdateEvent`
- `RPPCompositionEvent`

Output:

```text
FrameDefinitionEvent
frame_trace.json
```

Rules:

- frame definition must cite event evidence.
- it may affect later affordance, expression, and recognition evaluation.
- it must decay when not renewed.
- it must not invent scenes, motives, or plot beats.
- LLM rendering may use it only as a constraint on wording, not as authority to add events.

This layer explains why the same visible act can become help, control, debt collection, public performance, avoidance, or repair depending on the operative interaction frame.

### Step 11.9: Relation-Generated Positioning

Observable history may also push each process into a relation-generated position:

- claimant
- debtor
- defender
- caretaker
- controlled
- public performer
- withdrawer
- trapped party
- repair partner
- bound party

These are not roles, identities, traits, or motives. They are bounded, event-sourced positions produced by recognition outcomes, obligations, frames, relevance shifts, relation sediment, RPP composition, and binding evolution.

Valid sources:

- `RecognitionEvent`
- `MisrecognitionEvent`
- `RepairEvent`
- `AvoidanceEvent`
- `DisplacementEvent`
- `NormativePressureEvent`
- `FrameDefinitionEvent`
- `RelevanceShiftEvent`
- `RelationSedimentationEvent`
- `RPPCompositionEvent`
- `BindingUpdatedEvent`

Output:

```text
PositioningEvent
position_trace.json
```

Rules:

- positioning must cite event evidence.
- position metrics use the `position_field.{process}.{position_type}` prefix.
- it may affect later action selection and recognition evaluation through bounded `position_*` evidence.
- unreinforced positions decay.
- it must not directly create a scene, personality label, fixed social role, relationship label, or rendered prose.

This layer explains why a process does not merely "choose" an action. The relation may have already made it available as claimant, defensible as defender, costly as debtor, almost unsayable as trapped party, or distorted as caretaker/control.

### Step 12: Recognition Evaluation

Evaluate active recognition demands.

Possible results:

- granted
- partially granted
- refused
- displaced
- mocked
- postponed
- misunderstood
- made unspeakable

Emit:

```text
RecognitionEvent
MisrecognitionEvent
```

Recognition outcome is selected by a dedicated engine from:

- selected affordance
- active RPP composition
- recognition demand pressure
- face risk and audience pressure
- speech inhibition
- repair debt
- unrecognized contribution
- relation-generated position field from prior history

It must emit outcome scores and evidence. It must not use a single repair-debt threshold as the outcome rule.

Each run writes:

```text
recognition_trace.json
```

The trace records:

- demand id
- selected outcome
- all outcome scores
- evidence factors
- repair/misrecognition/avoidance event type
- resulting repair debt and demand pressure

### Step 13: Repair / Escalation / Avoidance

The scene may attempt repair or move into escalation.

Repair forms:

- apology
- joke
- practical help
- silence
- touch
- reframing
- sacrifice
- explicit recognition

Emit:

```text
RepairEvent
EscalationEvent
AvoidanceEvent
DisplacementEvent
```

### Step 14: Stabilization Update

Repeated patterns may become more stable.

Update:

- stabilized RPPs
- habitus tendencies
- relation-specific profiles
- action affordances
- speech constraints

Emit:

```text
StabilizationEvent
DestabilizationEvent
```

### Step 15: Irreversibility Update

Determine whether anything entered irreversible history.

Criteria:

- public commitment
- unretractable utterance
- shared secret
- betrayal
- sacrifice
- institutional record
- lost alternative
- social reclassification

Emit:

```text
IrreversibilityEvent
```

### Step 16: Aggregation and Projection

Recompute:

- relational aggregates
- PersonView
- RelationshipView
- FieldView
- narrative labels

Emit:

```text
AggregationEvent
ProjectionEvent
```

These events record derived changes. They must not mutate causal state directly.

### Step 17: Operative Classification Feedback

If a label has uptake in the simulated world, create or update operative classification.

Emit:

```text
OperativeClassificationEvent
DownwardConstraintEvent
```

Operative classification must be produced by fate transition evaluation, not by a scenario-specific RPP shortcut.

The fate transition engine evaluates:

- affordance
- recognition outcome
- dominant RPP composition
- audience pressure
- repair debt
- conflict pressure
- field-specific pressures such as public/private gap, care dependency, double bind pressure, silence charge, and unrecognized contribution

It may generate labels such as:

- `you_make_it_sound_like_i_owe_you`
- `your_help_is_control`
- `we_are_only_fine_in_public`
- `you_are_never_really_here`
- `nothing_i_do_is_right`

These are operative labels only when emitted as `OperativeClassificationEvent`.

### Step 17.1 Fate Transition / Irreversibility

Irreversibility is not limited to contribution debt being named.

The runtime may create irreversible records for:

- symbolic debt lock
- public reclassification or exposure risk
- care role lock
- silence becoming history
- double bind becoming an identity mark

Each irreversible record must specify:

- source event
- affected processes
- future constraints
- lost alternatives
- transition evidence

Each run writes:

```text
fate_transition_trace.json
```

### Step 17.2 Memory / History Reconstruction

Memory is not a passive store of past events.

The runtime reconstructs remembered history after recognition, classification, and irreversibility have already altered the relation. A memory trace records:

- who reconstructs the event
- which event is being remembered
- what it is remembered as
- salience
- valence
- confidence
- reconstruction biases

This means later conduct is constrained not only by what happened, but by what the relation has made the event mean.

Primary triggers:

- failed recognition
- operative classification
- irreversibility

Future constraints may modulate memory reconstruction.

If a `FutureConstraintEvent` already exists in the tick, and it affects the remembering process plus the relevant requirement type, it may slightly increase the salience and confidence of an already produced memory candidate.

It may not create a memory by itself.

Consumed future constraints are recorded in:

- `memory_trace.json` evidence as `future_constraint_refs`
- `MemoryReconstructionEvent.causal_refs`

Each run writes:

```text
memory_trace.json
```

### Step 17.3 Historical Feedback

Reconstructed memory is causal input on later ticks.

The runtime exposes memory through semantic pressures rather than through raw remembered text:

- `memory_pressure`
- `injury_memory`
- `defensive_memory`
- `fate_memory`

These pressures feed:

- temporal scheduling, making some remembered histories crystallize future scenes sooner
- affordance selection, making some actions more visible or more unavailable
- recognition evaluation, altering whether a claim is granted, refused, displaced, postponed, misunderstood, or unspeakable
- RPP activation, allowing repeated relation patterns to be triggered by history, not only by current signal
- future-constraint generation, allowing remembered history to narrow later viability

Memory bias decays over time. Decay prevents the simulator from turning one early event into an infinite deterministic lock unless later interaction keeps reconstructing the same history.

### Step 17.4 Environment Sedimentation

The field is not only an input.

After memory reconstruction, relation history may sediment back into the environment.

This layer may update:

- `field_state.spatial_constraints`
- `field_state.material_pressures`
- `field_state.audience_pressure`
- `field_state.enacted_micro_worlds`

Valid sources:

- `RPPActivationEvent`
- `RPPCompositionEvent`
- `FutureConstraintEvent`
- `MemoryReconstructionEvent`
- `IrreversibilityEvent`
- prior-tick `RelationSedimentationEvent`

Outputs:

```text
FieldUpdateEvent
EnactedMicroWorldEvent
environment_trace.json
```

Rules:

- environment sedimentation may only cite prior relation events from the same or earlier tick
- it may not create recognition, memory, RPP, or irreversibility by itself
- it must remain bounded and gradual
- sedimented pressures decay when not renewed, so one event cannot permanently monopolize the field
- sedimented spatial pressure may be read by the viability layer on later ticks
- relation sediment may attach recognition debt to objects, repair narrowing to avoidance paths, public definition to imagined audiences, and fate load to memory-saturated spaces
- relation sediment is consumed with a one-tick delay to avoid same-tick self-amplification

This is the mechanism by which rooms, objects, routines, audiences, and avoided paths become part of the relation rather than neutral background.

### Step 17.5 Process Disposition Sedimentation

Process-level tendencies are not primitive personality parameters.

After memory and environment sedimentation, repeated evidence may slightly alter process dispositions:

- checking tendency
- ambiguity tolerance
- risk suspension scope
- speech inhibition
- threat sensitivity
- resentment pressure

Valid sources:

- `MemoryReconstructionEvent`
- `FieldUpdateEvent`
- `RPPActivationEvent`
- consumed `FutureConstraintEvent` refs
- prior-tick `RelationSedimentationEvent`

Output:

```text
DispositionSedimentationEvent
disposition_trace.json
```

Rules:

- disposition sedimentation must cite event evidence
- it must remain bounded and gradual
- only the sedimented contribution decays; scenario baselines are not erased
- unreinforced disposition sediment decays over later ticks
- it must not create PersonView labels directly
- PersonView may later summarize these tendencies as apparent labels
- relation sediment may alter checking tendency, ambiguity tolerance, speech inhibition, exposure sensitivity, and risk suspension with a one-tick delay

### Step 17.6 Relation Sedimentation

The relation is not a primitive object, but the relation process can acquire historical residue.

After process disposition sedimentation, repeated event evidence may sediment into relation-level constraints:

- recognition debt
- repair access narrowing
- symbolic accounting load
- future lock load
- shared fate load
- public definition load
- asymmetry load
- memory saturation
- mutual predictability load

Valid sources:

- `RecognitionEvent`
- `MisrecognitionEvent`
- `RepairEvent`
- `AvoidanceEvent`
- `DisplacementEvent`
- `RPPCompositionEvent`
- `FutureConstraintEvent`
- `MemoryReconstructionEvent`
- `FieldUpdateEvent`
- `DispositionSedimentationEvent`
- `NormativePressureEvent`

Output:

```text
RelationSedimentationEvent
relation_trace.json
```

Rules:

- relation sedimentation must cite event evidence
- it must remain bounded and gradual
- unreinforced relation sediment decays over later ticks
- it may feed later aggregation, viability, affordance, recognition, repair, and fate calculations
- it may feed the next tick's scheduler preview as `relation_sediment_load`
- it may create later relation-sedimentation-backed `FutureConstraintEvent` traces after threshold crossing
- viability events that consume relation sediment should cite recent `RelationSedimentationEvent` ids where available
- multiple same-tick updates to the same sediment metric may be coalesced into one event with `reason_details`
- it must not directly create plot beats, rendered prose, or relationship labels

This is the runtime mechanism by which "relationship" becomes a real evolving constraint without being treated as a primitive entity.

### Step 18: Persist

Persist:

- event stream
- new snapshot if scheduled
- derived views
- diagnostics
- environment trace
- disposition trace
- relation trace
- binding trace
- expectation trace
- account trace
- position trace
- optional rendering

---

### 4.18 Pipeline by Tick Type

Not every tick type runs every pipeline stage with equal weight.

### Latent Tick Pipeline

```text
1. Load and validate state
2. Evaluate field pressures
3. Evaluate co-presence bindings
4. Update latent relevance pressure
5. Decay or intensify active RPPs
6. Update aggregation and projection
7. Persist LatentTimeEvent / NoSceneEvent and diagnostics
```

Latent ticks do not create a full `SceneState` unless pressure crosses scene threshold.

### Micro-Interaction Tick Pipeline

```text
1. Load and validate state
2. Evaluate field and binding context
3. Detect or generate micro signal
4. Evaluate observation
5. Update relevance landscape
6. Check RPP eligibility
7. Emit recognition implication if relevant
8. Aggregate and project
9. Persist
```

Micro-interaction ticks may create a minimal scene context, but they need not create a full episode.

### Scene Tick Pipeline

```text
1. Load and validate state
2. Evaluate field pressures
3. Evaluate co-presence bindings
4. Crystallize scene
5. Select situated affordance
6. Generate micro signal from affordance
7. Activate RPPs
8. Update relevance landscapes
9. Establish ritual frame
10. Produce communication or action event
11. Perform second-order observation
12. Evaluate recognition and misrecognition
13. Apply repair, escalation, avoidance, or displacement
14. Update stabilization
15. Update irreversibility
16. Aggregate and project
17. Evaluate operative classification feedback
18. Persist
```

---

## 5. Episode Lifecycle

An episode is a coherent scene sequence.

```text
latent tension
-> scene crystallization
-> interaction events
-> recognition outcome
-> repair/escalation/avoidance
-> episode closure or continuation
```

### 5.1 Episode Start Conditions

Start an episode when:

- a binding crosses encounter threshold
- a field pressure requires co-presence
- an active RPP requires expression
- an irreversible record demands consequence
- a latent recognition demand reaches pressure threshold

### 5.2 Episode Closure Conditions

Close an episode when:

- participants separate
- ritual frame dissolves
- communication reaches stable temporary settlement
- repair succeeds enough to lower pressure
- escalation creates a new irreversible condition
- avoidance postpones the conflict

Closure does not mean resolution.

---

## 6. Scene Crystallization

Scene selection should be constraint-driven, not plot-driven.

### 6.1 Scene Score

```text
scene_score =
  field_pressure
+ binding_urgency
+ recognition_pressure
+ active_rpp_pressure
+ irreversibility_pressure
+ bounded_viability_rhythm_bias
- avoidance_capacity
- exit_capacity
```

The viability rhythm bias is computed before tick events exist, from current causal state only. It is recorded in scheduler diagnostics and must remain bounded. It may make a near-threshold latent or micro-interaction moment arrive slightly sooner, but it must not force a scene that lacks field pressure, binding, or accumulated relational pressure.

### 6.2 Required Scene Explanation

Every scene must answer:

```text
Why here?
Why now?
Why these positions?
Why can this not simply be avoided?
```

If the answer is weak, the scene should not crystallize.

---

## 7. RPP Activation Runtime

RPP activation must be evidence-based.

### 7.1 Activation Procedure

```text
for each RPP:
  collect triggering differences
  test eligibility conditions
  test contraindications
  compute activation score
  rank candidates
  sample or select
  emit RPPActivationEvent
```

RPPs may consume `FutureConstraintEvent` as bounded eligibility evidence.

This allows irreversibility, operative classification, and reconstructed memory to make a pattern easier to re-enter on later ticks.

It must remain bounded:

- a future constraint is not a command to activate an RPP
- the RPP must still pass its normal field, tick, signal, recognition, memory, or relation-metric gate
- consumed future constraints must appear in `RPPActivationEvent.eligibility_evidence`
- consumed future constraints must appear in `RPPActivationEvent.causal_refs`

### 7.2 Activation Thresholds

Each RPP should define:

- minimum eligibility score
- activation threshold
- escalation threshold
- decay threshold
- stabilization threshold

---

## 8. Derived View Runtime

Derived views are recomputed after causal updates.

They must include:

- source events
- contributing RPPs
- confidence
- freshness
- known ambiguity

A derived view without evidence refs is invalid.

---

## 9. LLM Runtime

The LLM may be called at two points:

### 9.1 Candidate Generation

Before Step 9, the LLM may propose candidate utterances or gestures from constraints.

These candidates must be validated and selected by the simulator.

### 9.2 Rendering

After Step 15, the LLM may render the scene into prose.

Rendering must not change state.

---

## 9.3 Continuous Web Runtime

The viewer may run a continuous simulation session.

The selected duration is wall-clock runtime.

If the user selects `18 hours`, the viewer should keep the simulation session alive for 18 real-world hours unless the user stops it or a configured max-tick safety limit is reached.

Supported duration units:

```text
minutes
hours
days
```

The runtime advances event-driven ticks at a configured wall-clock tick interval.

Example:

```text
duration: 18 hours
tick interval: 30 seconds
approximate max natural ticks: 2160
```

Each tick may still represent its own simulated time delta inside the modeled world, but the session stop condition is real elapsed wall-clock time.

During a continuous session:

- output files are refreshed after configured tick intervals
- the viewer polls run status
- story, traces, metrics, and events update while the session is running
- optional rendering may run every N ticks
- each web-created continuous run receives its own archive directory
- older web-created runs can be reopened without being overwritten

Rendering modes:

```text
none
deterministic
llm
```

Automatic rendering is segment-based, not fixed-tick based.

The viewer waits for a minimum narrative cycle to close.

A cycle may close through:

- weak closure: accumulated latent time or enough micro-interactions
- standard closure: scene crystallization or recognition/misrecognition result
- strong closure: phase change, memory reconstruction, fate transition, or irreversibility
- fallback closure: maximum wait ticks or maximum simulated time span

Default thresholds:

```text
micro_interaction count: 3
latent time: 6 hours
max wait: 8 ticks
max segment span: 1 day
```

Each closed cycle is rendered as one segment and appended to:

```text
rendered_story_stream.md
rendered_segments.json
```

If `llm` is selected, the renderer receives the same controlled render payload as manual rendering:

- render canon
- summary
- relationship view
- person-facing views
- irreversibility
- story frames
- per-frame viability evidence summaries

The LLM still may not mutate simulation state.

Per-frame viability summaries are derived from simulator events. They may describe pressure, narrowed affordances, blocked requirements, response cost, deformation, and evidence refs.

They are not a license for the LLM to add hidden motives, new memories, off-screen events, or future consequences.

Future constraints in the render payload are already derived by the simulator from irreversibility, classification, or memory evidence. The LLM may render their felt pressure, but it may not create additional future constraints.

API keys entered in the browser are stored only in browser local storage for user convenience and are sent to the local viewer backend when a rendering request is made. They are not written into scenario files, run output, or documentation.

Web run archive layout:

```text
out/experience/runs/<scenario_id>/<timestamp>_<mode>_seed<seed>_<id>/
```

Each archived run contains the ordinary simulation outputs plus:

```text
run_metadata.json
```

The metadata records run id, scenario id, scenario path, seed, mode, title, and creation time. It is used only by the viewer workbench; causal authority remains in the event stream and manifest.

---

## 10. Replay Runtime

Replay must reconstruct causal state from:

```text
initial_state
seed
event_stream
```

Derived views may be recomputed or loaded, but they are not authoritative.

Replay failure indicates a simulation integrity bug.

---

## 11. Runtime Diagnostics

Each tick should optionally produce diagnostics:

```text
Diagnostics
- tick_type
- simulated_time_delta
- time_mapping_reason
- eligible_rpps
- rejected_rpps
- scene_candidates
- affordance_candidates
- selected_affordance
- selected_scene_reason
- aggregation_trace
- operative_label_trace
- invariant_warnings
- randomness_trace
```

These diagnostics are essential for research use.

---

## 12. Failure Conditions

The runtime must flag failure when:

- no event is emitted for multiple ticks without latent-time explanation
- tick has no type
- tick has no simulated time mapping
- scenes occur without binding explanation
- high-level views mutate causal state
- LLM output bypasses validation
- RPP activation lacks evidence
- irreversible event lacks future constraint
- derived labels become causal without uptake
- replay diverges from original state


