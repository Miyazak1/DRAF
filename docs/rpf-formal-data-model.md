# RPF Formal Data Model Specification

## 0. Purpose

This document defines the formal data model for RPF.

It translates the ontology in `relational-process-field-architecture.md` into implementable typed objects.

The main rule is:

```text
causal state is stored in field/process/event structures;
PersonView and RelationshipView are projections;
high-level concepts never mutate causal state directly.
```

---

## 1. Modeling Principles

### 1.1 Primitive Objects

The primitive objects are:

```text
SimulationState
FieldState
ProcessState
RelationalProcessPattern
SceneState
Event
IrreversibilityRegister
```

These may participate directly in simulation updates.

### 1.2 Derived Objects

The derived objects are:

```text
PersonView
RelationshipView
FieldView
RelationalAggregateView
NarrativeLabel
```

These are recomputed from causal state and event history.

They are not authoritative state.

### 1.3 Operative Exception

A derived label becomes causal only when it is represented as:

```text
OperativeClassification
```

This requires uptake inside the simulated world:

- spoken by a process position
- believed or incorporated into self-narrative
- repeated by an audience
- used to justify action
- institutionally recorded
- used to deny recognition

---

## 2. Type Conventions

Recommended implementation:

```python
from pydantic import BaseModel, Field
from typing import Literal, Optional
from uuid import UUID
```

Use stable IDs for all durable objects.

```text
SimulationId
ProcessId
SceneId
EpisodeId
EventId
RppId
FieldId
```

Use normalized bounded numbers for intensities:

```text
float in [0.0, 1.0]
```

Use signed deltas for updates:

```text
float in [-1.0, 1.0]
```

Do not encode meaning as raw floats without naming the structure being measured.

Invalid:

```text
trust = 0.72
```

Valid:

```text
risk_suspension_scope["emotional_disclosure"] = 0.72
```

---

## 3. SimulationState

`SimulationState` is the root causal state.

```text
SimulationState
- simulation_id: SimulationId
- clock: SimulationClock
- seed: int
- field_state: FieldState
- process_states: dict[ProcessId, ProcessState]
- active_bindings: list[CoPresenceBinding]
- active_rpps: list[ActiveRPP]
- irreversibility_register: IrreversibilityRegister
- open_episodes: list[EpisodeId]
- latest_snapshot_id: SnapshotId | null
```

### 3.1 SimulationClock

```text
SimulationClock
- tick: int
- tick_type: Literal["latent", "micro_interaction", "scene"] | null
- calendar_time: string | null
- simulated_time_start: string | null
- simulated_time_end: string | null
- simulated_time_delta_seconds: int | null
- time_mapping_reason: str | null
- phase: Literal["setup", "running", "paused", "complete"]
```

The clock must support deterministic replay by tick.

### 3.2 TickContext

Each runtime transaction should create a `TickContext`.

```text
TickContext
- tick_index
- tick_type: Literal["latent", "micro_interaction", "scene"]
- simulated_time_start
- simulated_time_end
- simulated_time_delta_seconds
- time_mapping_reason
- causal_scope
- upgrade_from: Literal["latent", "micro_interaction"] | null
- downgrade_from: Literal["scene", "micro_interaction"] | null
- parent_episode_id: EpisodeId | null
```

`tick_type` determines which runtime stages are required. It does not directly determine causal outcome.

---

## 4. FieldState

`FieldState` stores world structures that shape possibility.

```text
FieldState
- material_conditions: MaterialConditions
- institutional_orders: list[InstitutionalOrder]
- spatial_arrangements: SpatialArrangements
- temporal_pressures: TemporalPressures
- class_structure: ClassStructure
- cultural_legitimacy_rules: list[LegitimacyRule]
- audience_network: AudienceNetwork
- sanction_systems: list[SanctionSystem]
- historical_events: list[HistoricalEventRef]
- enacted_micro_worlds: list[EnactedMicroWorld]
```

### 4.1 MaterialConditions

```text
MaterialConditions
- resources: dict[str, ResourcePool]
- labor_obligations: list[LaborObligation]
- care_obligations: list[CareObligation]
- debt_relations: list[DebtRelation]
- recovery_access: dict[ProcessId, RecoveryAccess]
```

### 4.2 InstitutionalOrder

```text
InstitutionalOrder
- id
- name
- domain: Literal["family", "work", "law", "school", "religion", "market", "state", "medical", "other"]
- classifications: list[InstitutionalClassification]
- permissions: list[PermissionRule]
- sanctions: list[SanctionRule]
- recognized_roles: list[str]
```

### 4.3 AudienceNetwork

```text
AudienceNetwork
- present_audiences: list[AudienceNode]
- imagined_audiences: list[AudienceNode]
- reputational_channels: list[ReputationalChannel]
```

The audience network matters even when no third person is physically present.

---

## 5. ProcessState

`ProcessState` replaces primitive `Person`.

It represents a stabilized site where embodied, social, and relational processes converge.

```text
ProcessState
- process_id: ProcessId
- display_name: str
- body_position: BodyPosition
- field_positions: list[FieldPosition]
- embodied_habitus: EmbodiedHabitus
- relevance_landscape: RelevanceLandscape
- recognition_demands: list[RecognitionDemand]
- speech_constraints: SpeechConstraints
- action_affordances: ActionAffordanceSet
- active_classifications: list[OperativeClassificationRef]
- stabilized_patterns: list[StabilizedPattern]
- relation_specific_profiles: dict[ProcessId, RelationSpecificProfile]
```

`display_name` is allowed as an interface convenience. It must not imply that the named person is ontologically primitive.

### 5.1 BodyPosition

```text
BodyPosition
- fatigue_level
- arousal_level
- pain_level
- bodily_safety
- mobility
- sensory_load
- recovery_need
```

### 5.2 FieldPosition

```text
FieldPosition
- field_name
- economic_capital
- cultural_capital
- social_capital
- symbolic_capital
- institutional_status
- legitimacy
- stigma
- mobility
- sanction_exposure
```

### 5.3 EmbodiedHabitus

```text
EmbodiedHabitus
- threat_sensitivity: dict[str, float]
- shame_threshold: dict[str, float]
- speech_inhibition: dict[str, float]
- approach_tendency: dict[str, float]
- withdrawal_tendency: dict[str, float]
- authority_posture: dict[str, float]
- dependency_comfort: dict[str, float]
- visibility_comfort: dict[str, float]
- temporal_horizon: float
- bodily_memory_refs: list[EventId]
```

### 5.4 RelevanceLandscape

```text
RelevanceLandscape
- salience_map: dict[str, float]
- threat_markers: dict[str, float]
- opportunity_markers: dict[str, float]
- affordance_map: dict[str, float]
- ignored_background: list[str]
- symbolic_triggers: dict[str, float]
- memory_activated_features: list[EventId]
- attention_capture_points: list[str]
```

---

## 6. CoPresenceBinding

`CoPresenceBinding` explains why process positions continue to encounter each other.

```text
CoPresenceBinding
- binding_id
- process_ids: list[ProcessId]
- binding_type: Literal[
    "material",
    "care",
    "institutional",
    "spatial",
    "temporal",
    "reputational",
    "narrative",
    "debt",
    "secret",
    "trauma",
    "recognition",
    "unresolved_account"
  ]
- strength: float
- asymmetry: dict[ProcessId, float]
- exit_cost: dict[ProcessId, float]
- decay_rule: DecayRule | null
- activation_conditions: list[ConditionRef]
```

If no binding remains above threshold, future encounter generation must become unlikely or latent.

`CoPresenceBinding` is initialized from scenario data but is not fixed.

It may be updated by:

- `BindingUpdatedEvent`
- `BindingDecayedEvent`

Binding evolution may change:

- `strength`
- `exit_cost`

Valid causal sources include field pressure, repair, avoidance, displacement, and relation sedimentation.

---

## 7. RelationalProcessPattern

`RelationalProcessPattern` is the core dynamic unit.

```text
RelationalProcessPattern
- rpp_id
- name
- description
- eligibility_conditions: list[EligibilityCondition]
- triggering_differences: list[TriggeringDifference]
- activation_weights: list[ActivationWeight]
- relevance_effects: list[RelevanceEffect]
- communicative_forms: list[CommunicativeForm]
- recognition_effects: list[RecognitionEffect]
- stabilization_effects: list[StabilizationEffect]
- irreversibility_effects: list[IrreversibilityEffect]
- contraindications: list[ConditionRef]
```

### 7.1 ActiveRPP

```text
ActiveRPP
- rpp_id
- scene_id
- participating_processes: list[ProcessId]
- activation_score
- activation_reason_refs: list[EventId]
- current_phase: Literal["eligible", "activated", "escalating", "repairing", "stabilized", "decayed"]
- intensity
- started_tick
- last_updated_tick
```

---

## 8. SceneState

`SceneState` is a local crystallization of field, binding, ritual, and relevance.

```text
SceneState
- scene_id
- episode_id
- tick_start
- tick_end: int | null
- location
- frame
- declared_activity
- hidden_activities: list[str]
- participating_processes: list[ProcessId]
- present_audience: list[AudienceNode]
- imagined_audience: list[AudienceNode]
- face_risks: dict[ProcessId, list[FaceRisk]]
- permissible_speech: dict[ProcessId, list[str]]
- forbidden_speech: dict[ProcessId, list[str]]
- exit_routes: dict[ProcessId, ExitRoute]
- active_rpps: list[RppId]
```

---

## 9. RecognitionDemand

```text
RecognitionDemand
- demand_id
- holder_process_id
- demanded_from: ProcessId | FieldActorId | null
- recognition_type: Literal[
    "see_me",
    "choose_me",
    "respect_me",
    "forgive_me",
    "need_me",
    "release_me",
    "believe_me",
    "admit_what_happened",
    "admit_i_mattered",
    "allow_change",
    "allow_nonchange"
  ]
- explicitness
- vulnerability_cost
- threat_if_denied
- identity_dependency
- history_of_denial: list[EventId]
- current_pressure
```

Recognition demands may be latent. They need not be consciously represented by the process position.

---

## 10. OperativeClassification

```text
OperativeClassification
- classification_id
- label
- target_process_id: ProcessId | null
- target_relation_id: str | null
- source
- audience
- uptake
- legitimacy
- sanction_power
- identity_pressure
- future_interpretation_bias
- created_by_event: EventId
- active
- decay_rule: DecayRule | null
```

This object is the only path by which high-level labels may become causal.

---

## 11. IrreversibilityRegister

```text
IrreversibilityRegister
- spoken_irreversibles: list[IrreversibleRecord]
- public_commitments: list[IrreversibleRecord]
- debts: list[IrreversibleRecord]
- betrayals: list[IrreversibleRecord]
- sacrifices: list[IrreversibleRecord]
- shared_secrets: list[IrreversibleRecord]
- social_reclassifications: list[IrreversibleRecord]
- institutional_records: list[IrreversibleRecord]
- bodily_changes: list[IrreversibleRecord]
- lost_alternatives: list[IrreversibleRecord]
- narrative_lock_ins: list[IrreversibleRecord]
```

### 11.1 IrreversibleRecord

```text
IrreversibleRecord
- record_id
- category
- description
- source_event
- affected_processes
- affected_bindings
- future_constraints
- audience_scope
- reversibility: Literal["none", "partial", "symbolic_only"]
- created_tick
```

Irreversible does not always mean materially impossible to undo. It means the future cannot be the same as if the event had never occurred.

---

## 12. Event Model

All state mutations must be event-backed.

```text
Event
- event_id
- simulation_id
- tick
- episode_id: EpisodeId | null
- scene_id: SceneId | null
- event_type
- source_layer
- payload
- causal_refs: list[EventId]
- deterministic_order
- created_at
```

The complete event taxonomy is defined in `rpf-event-taxonomy.md`.

---

## 13. Relational Viability Trace Models

These are trace-only models for the deeper substrate beneath conflict. They are append-only evidence, not writable causal state.

```text
ViabilityConstraint
- constraint_id
- constraint_type
- source_layer
- affected_processes
- affected_requirements
- intensity
- activation_condition
- duration_policy
- decay_rate
- reversibility
- downstream_effects
- evidence_refs
```

```text
ViabilityRequirement
- requirement_id
- requirement_type
- holder_process_id
- target_process_id optional
- urgency
- negotiability
- minimum_satisfaction_condition
- failure_cost
- deformation_tendency
- source
- evidence_refs
```

```text
AffordanceWidth
- tick
- process_id
- width
- narrowing_constraints
- direct_response_cost
- evidence_refs
```

```text
DeformationTrace
- deformation_id
- source_process_id
- target_process_id
- visible_form
- blocked_requirement_id optional
- deformation_type
- deformation_distance
- ambiguity
- observer_risk
- expected_recognition_failure_modes
- evidence_refs
```

```text
ViabilityTickTrace
- tick
- tick_type
- constraints
- requirements
- affordance_widths
- deformations
- dramatic_tension
- evidence_refs
```

These models may explain and later gently bias downstream engines, but they must not directly mutate `PersonView`, `RelationshipView`, or other derived views.

---

## 14. Derived Views

### 14.1 PersonView

```text
PersonView
- process_id
- display_name
- apparent_traits: list[DerivedLabel]
- stabilized_response_patterns
- recognized_roles
- habitual_interpretations
- embodied_defenses
- relational_positions
- self_narratives
- externally_imposed_labels
- unavailable_actions
- possible_transformations
- evidence_refs: list[EventId]
```

### 14.2 RelationshipView

```text
RelationshipView
- participating_processes
- active_bindings
- recurring_rpps
- recognition_conflicts
- communication_loops
- repair_patterns
- forbidden_truths
- shared_irreversibles
- public_definition
- private_definition
- exit_asymmetry
- possible_phase_transitions
- evidence_refs
```

### 14.3 RelationalAggregateView

```text
RelationalAggregateView
- trust_view
- intimacy_view
- dependency_view
- resentment_pressure_view
- power_asymmetry_view
- repair_capacity_view
- conflict_pressure_view
- stability_view
- evidence_refs
```

All derived views must include evidence references.

---

## 15. Write Permissions by Object

```text
Writable causal state:
- FieldState
- ProcessState
- CoPresenceBinding
- ActiveRPP
- SceneState
- IrreversibilityRegister
- OperativeClassification

Append-only:
- Event
- EpisodeRecord
- Snapshot
- ViabilityTickTrace

Derived only:
- PersonView
- RelationshipView
- RelationalAggregateView
- NarrativeLabel
```

---

## 16. Validation Rules

The implementation must reject:

- direct mutation of PersonView
- direct mutation of RelationshipView
- direct mutation of trust/intimacy/dependency as primitive variables
- operative classifications without source event
- irreversible records without source event
- RPP activation without eligibility evidence
- LLM output that proposes causal mutation outside event schemas
- viability trace that cannot cite lower-layer event evidence

---

## 17. Minimal Pydantic Skeleton

```python
class SimulationState(BaseModel):
    simulation_id: str
    clock: SimulationClock
    seed: int
    field_state: FieldState
    process_states: dict[str, ProcessState]
    active_bindings: list[CoPresenceBinding] = []
    active_rpps: list[ActiveRPP] = []
    irreversibility_register: IrreversibilityRegister


class ProcessState(BaseModel):
    process_id: str
    display_name: str
    body_position: BodyPosition
    field_positions: list[FieldPosition]
    embodied_habitus: EmbodiedHabitus
    relevance_landscape: RelevanceLandscape
    recognition_demands: list[RecognitionDemand] = []
    active_classifications: list[str] = []
    stabilized_patterns: list[StabilizedPattern] = []


class Event(BaseModel):
    event_id: str
    simulation_id: str
    tick: int
    event_type: str
    source_layer: str
    payload: dict
    causal_refs: list[str] = []
    deterministic_order: int
```

This skeleton is intentionally incomplete. The detailed fields above are authoritative.

