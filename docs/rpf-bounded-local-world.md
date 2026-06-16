# RPF Bounded Local World

## 0. Purpose

This document defines the bounded physical field for RPF.

The core idea is:

```text
RPF simulations should not take place in infinite space and infinite time.
They should take place inside a bounded local world.
```

A bounded local world is not background decoration. It is a causal field that constrains:

- where scenes can occur
- who can encounter whom
- who may observe the encounter
- what resources are available
- what routes are costly, blocked, exposed, or dangerous
- what histories remain attached to places
- what secrets can and cannot stay hidden
- what future actions become impossible because of where and when something happened

This document introduces `LocalWorld` as a core architecture layer for improving realism and dramatic pressure.

---

## 1. Core Position

Drama weakens when the simulated world is spatially and temporally unlimited.

If characters can always go elsewhere, meet anyone, vanish without cost, create new locations, or wait indefinitely, then conflict loses pressure.

RPF should therefore obey:

```text
No Infinite World Rule
```

Meaning:

```text
Every simulation must define a finite physical-social field.
Every scene must occur inside that field or inside an explicitly reachable extension.
Every new location, route, audience, resource, or offscreen event must be licensed by the local world.
```

The local world answers:

```text
Why here?
Why now?
Why can this not simply be avoided?
Who might see?
What does this place remember?
What does it cost to leave?
What becomes impossible if the scene happens here?
```

---

## 2. Why A Small Town Works

A small town is a strong default physical field for RPF because it naturally produces:

```text
finite space
repeated encounters
familiar routes
limited institutions
public observation
rumor circulation
resource scarcity
slowly decaying secrets
place-based memory
exit cost
institutional-personal entanglement
```

In a town, people do not merely interact. They keep crossing paths through shared routes, shared institutions, shared weather, shared debt, shared witnesses, and shared history.

This makes a town suitable for:

- family drama
- cold cases
- care conflict
- class divergence
- public/private splits
- institutional silence
- reputation collapse
- supernatural ambiguity without requiring supernatural causality
- material and natural pressure such as rain, road closure, illness, power outage, or seasonal work

The town is not a setting. It is a repeated constraint generator.

---

## 3. Relationship To Existing RPF Architecture

Existing RPF already has:

```text
FieldState
MaterialConditions
SpatialArrangements
TemporalPressures
AudienceNetwork
InstitutionalOrders
EnactedMicroWorlds
```

`LocalWorld` should organize these into one bounded, inspectable field.

It sits under `FieldState`:

```text
FieldState
-> LocalWorld
   -> Locations
   -> Routes
   -> Rhythms
   -> Resources
   -> Audiences
   -> Institutions
   -> Memory Sites
   -> Weather / Ecology
   -> Boundary Rules
```

It also feeds the dramatic conflict framework:

```text
LocalWorld
-> Constraint Field
-> Blocked Capacity
-> Dramatic Contradiction
-> Action / Expression Deformation
-> Observation
-> Recognition / Misrecognition
-> Irreversibility
```

---

## 4. LocalWorld Schema

### 4.1 Minimal Structure

```text
LocalWorld
- id
- name
- scale
- description
- boundary_rules
- locations
- routes
- rhythms
- resources
- audiences
- institutions
- memory_sites
- ecological_conditions
- offscreen_policy
```

Recommended scales:

```text
household
apartment_building
workplace
school
hospital
village
town
district
island
ship
station
institutional_complex
```

The first full implementation should use:

```text
town
```

---

## 5. Locations

A `Location` is a place where scenes may occur or through which routes pass.

```text
Location
- location_id
- label
- location_type
- access_level
- controlling_institution optional
- public_visibility
- crowd_density
- rumor_density
- surveillance_level
- memory_charge
- material_conditions
- forbidden_topics
- allowed_scene_types
- blocked_scene_types
- linked_processes
- linked_events
- evidence_refs
```

Location types:

```text
home
workplace
institution
public_square
market
street
school
hospital
police_archive
factory
ruin
river
bridge
station
religious_site
graveyard
private_room
threshold
vehicle
remote_edge
```

Important rule:

```text
Locations are not neutral containers.
They alter speech, visibility, risk, memory, access, and repair options.
```

Example:

```yaml
- location_id: police_archive
  label: 派出所档案室
  location_type: police_archive
  access_level: restricted
  public_visibility: low
  crowd_density: low
  rumor_density: medium
  surveillance_level: medium
  memory_charge: high
  allowed_scene_types:
    - evidence_review
    - controlled_disclosure
    - procedural_conflict
  forbidden_topics:
    - unofficial_accusation
    - family_secret
```

---

## 6. Routes

A `Route` defines how locations are connected and what it costs to move between them.

```text
Route
- route_id
- from_location
- to_location
- travel_time_minutes
- access_level
- exposure_level
- danger_level
- weather_sensitivity
- crowd_pattern
- surveillance_points
- memory_charge
- blocked_by_conditions
- route_events
```

Routes matter because many conflicts depend on:

- who can arrive in time
- who can avoid whom
- who is seen traveling where
- what route becomes impossible under rain, night, illness, or public pressure
- whether leaving is easy, humiliating, dangerous, or suspicious

Example:

```yaml
- route_id: market_to_old_factory
  from_location: market_street
  to_location: abandoned_factory
  travel_time_minutes: 35
  exposure_level: low
  danger_level: medium
  weather_sensitivity: high
  blocked_by_conditions:
    - heavy_rain
    - river_rise
  memory_charge: high
```

---

## 7. Rhythms

A `Rhythm` is a recurring temporal pattern in the local world.

```text
Rhythm
- rhythm_id
- label
- time_window
- recurrence
- active_locations
- crowd_density_delta
- rumor_pressure_delta
- mobility_cost_delta
- institutional_pressure_delta
- available_scene_types
- blocked_scene_types
```

Rhythms create realism because a town behaves differently at different times.

Examples:

```text
morning_market
school_dismissal
factory_shift_change
clinic_queue
night_rain
festival_day
funeral_day
payday
inspection_day
case_anniversary
last_bus
power_outage_evening
```

Example:

```yaml
- rhythm_id: morning_market
  label: 早市
  time_window: morning
  recurrence: daily
  active_locations:
    - market_street
    - bus_stop
  crowd_density_delta: 0.45
  rumor_pressure_delta: 0.55
  mobility_cost_delta: 0.10
  available_scene_types:
    - public_performance
    - accidental_encounter
    - rumor_exchange
```

---

## 8. Resources

A `Resource` is anything whose scarcity, control, or access changes what processes can do.

```text
Resource
- resource_id
- label
- resource_type
- quantity_state
- controller
- access_rules
- scarcity_level
- replacement_access
- linked_capacities
- conflict_potential
```

Resource types:

```text
money
housing
medicine
transport
documents
evidence
record_access
job_slot
care_time
phone_signal
electricity
food
social_contact
public_attention
legal_permission
```

Resources should feed:

```text
BlockedCapacityEvent
FieldPressureEvent
AffordanceSelectionEvent
ActionInhibitionEvent
IrreversibilityEvent
```

---

## 9. Audiences

An `Audience` is any person, group, institution, or imagined observer whose possible attention changes action.

```text
Audience
- audience_id
- label
- audience_type
- usual_locations
- visibility_pattern
- rumor_power
- sanction_power
- legitimacy_power
- affected_topics
- relationship_to_processes
```

Audience types:

```text
neighbor
colleague
family
classmate
official
police
doctor
teacher
shopkeeper
reporter
victim_family
local_elder
online_public
imagined_audience
```

Important rule:

```text
A scene can be public even when no audience is physically present,
if an imagined or later-reporting audience constrains action.
```

---

## 10. Institutions

An `Institution` defines permissions, classifications, records, and sanctions.

```text
Institution
- institution_id
- label
- domain
- locations
- recognized_roles
- records
- access_permissions
- sanction_rules
- silence_rules
- legitimacy_rules
- corruption_or_decay
```

Institution domains:

```text
family
police
school
hospital
workplace
market
village_committee
religious
media
legal
housing
transport
```

Institutions should not be abstract labels. They must connect to:

- locations
- records
- audiences
- resources
- permission gates
- operative classifications

---

## 11. Memory Sites

A `MemorySite` is a place where past events alter present relevance.

```text
MemorySite
- site_id
- location_id
- memory_type
- source_events
- affected_processes
- salience
- contamination
- avoidance_pressure
- attraction_pressure
- possible_reclassification
- future_scene_biases
```

Memory site types:

```text
injury_site
sacrifice_site
betrayal_site
care_site
death_site
disappearance_site
promise_site
public_humiliation_site
evidence_site
unsolved_site
forbidden_site
```

Memory sites are central to realism because places do not reset.

Example:

```yaml
- site_id: old_bridge_disappearance
  location_id: river_bridge
  memory_type: disappearance_site
  affected_processes:
    - p1
    - p2
  salience: 0.82
  contamination: 0.44
  avoidance_pressure: 0.60
  attraction_pressure: 0.35
  future_scene_biases:
    - confession_pressure
    - testimony_gap
```

---

## 12. Ecology And Weather

Ecology and weather are not visual flavor. They are constraint sources.

```text
EcologicalCondition
- condition_id
- label
- condition_type
- active_time_window
- affected_routes
- affected_locations
- mobility_delta
- visibility_delta
- bodily_cost_delta
- evidence_degradation_delta
- audience_density_delta
```

Condition types:

```text
rain
fog
heat
cold
flood
power_outage
road_closure
illness_wave
harvest_season
tourist_season
construction
pollution
nightfall
```

These conditions should generate:

```text
FieldPressureEvent
ConstraintFieldEvent
BlockedCapacityEvent
RouteAccessEvent
LocationStateEvent
```

---

## 13. Boundary Rules

Boundary rules prevent the simulator from inventing infinite world content.

```text
BoundaryRules
- max_scene_scope
- new_location_policy
- offscreen_event_policy
- route_required
- travel_time_required
- audience_required_for_public_reclassification
- institution_required_for_record_change
- memory_site_required_for_place_based_reconstruction
```

Recommended defaults:

```yaml
boundary_rules:
  max_scene_scope: local_world_only
  new_location_policy: discovery_required
  offscreen_event_policy: trace_required
  route_required: true
  travel_time_required: true
  audience_required_for_public_reclassification: true
  institution_required_for_record_change: true
  memory_site_required_for_place_based_reconstruction: true
```

Invalid:

```text
A new abandoned clinic appears because the LLM mentioned it.
```

Valid:

```text
A new clinic location is introduced by LocationDiscoveryEvent,
with route, access level, institution, and evidence refs.
```

---

## 14. Event Additions

### 14.1 LocationStateEvent

```text
payload:
- location_id
- previous_state
- new_state
- changed_fields
- cause
- affected_scene_types
- affected_capacities
```

### 14.2 RouteAccessEvent

```text
payload:
- route_id
- access_before
- access_after
- travel_time_before
- travel_time_after
- blocking_condition
- affected_processes
```

### 14.3 RhythmActivationEvent

```text
payload:
- rhythm_id
- active_locations
- time_window
- crowd_density_delta
- rumor_pressure_delta
- mobility_cost_delta
- available_scene_types
```

### 14.4 AudienceExposureEvent

```text
payload:
- audience_id
- location_id
- observed_or_possible
- exposure_level
- sanction_risk
- rumor_risk
- affected_processes
- affected_topics
```

### 14.5 LocationDiscoveryEvent

```text
payload:
- location_id
- introduced_by
- discovery_reason
- route_refs
- access_level
- memory_charge
- allowed_scene_types
```

### 14.6 MemorySiteActivationEvent

```text
payload:
- site_id
- location_id
- source_events
- affected_processes
- salience
- avoidance_pressure
- attraction_pressure
- future_scene_biases
```

---

## 15. Runtime Integration

### 15.1 Tick Pipeline Placement

The local world should be evaluated before scene crystallization.

Recommended pipeline:

```text
1. Load state
2. Advance clock and local rhythm
3. Evaluate ecological conditions
4. Update route and location accessibility
5. Evaluate audience exposure
6. Build local-world constraint field
7. Evaluate bindings and encounter likelihood
8. Select possible location and route
9. Evaluate capacity demands and blocked capacities
10. Crystallize scene
11. Continue ordinary RPF pipeline
```

### 15.2 Scene Crystallization Requirements

Every scene must include:

```text
scene.location_id
scene.route_context optional
scene.time_window
scene.active_rhythm optional
scene.possible_audiences
scene.local_constraints
scene.memory_site_refs
```

Every scene must answer:

```text
why_here
why_now
why_these_processes
why_not_elsewhere
who_might_see
what_this_place_remembers
```

---

## 16. State Update Rules

`LocalWorld` must not remain a static scenario block. It should have lightweight update rules that change location, route, rhythm, audience, resource, and memory-site state over time.

### 16.1 LocalWorld State

At runtime, the simulator should maintain a derived-but-causal `LocalWorldState`.

```text
LocalWorldState
- current_time_window
- active_rhythms
- active_ecological_conditions
- location_states
- route_states
- resource_states
- audience_exposure_states
- active_memory_sites
- local_world_pressure
```

This state is causal because it constrains future scene selection and action availability. It is not a derived human-readable view.

### 16.2 Location Update

Location pressure should update from rhythms, ecology, institutional pressure, memory activation, and recent scene history.

Recommended trace formula:

```text
location_pressure =
  base_memory_charge
+ active_rhythm_pressure
+ ecological_pressure
+ institutional_pressure
+ recent_scene_residue
+ audience_pressure
- access_relief
```

Location state fields:

```text
location_state:
  accessibility
  pressure
  crowd_density
  rumor_density
  surveillance_level
  memory_salience
  contamination
  last_scene_tick
```

Examples:

```text
market_street during morning_market -> crowd_density rises, rumor_density rises
police_archive after evidence review -> memory_salience rises, surveillance relevance rises
abandoned_factory during heavy_rain -> accessibility falls, danger rises
```

### 16.3 Route Update

Routes should update from weather, time window, crowd pattern, surveillance, danger, and institutional blocks.

Recommended trace formula:

```text
route_accessibility =
  base_access
- weather_block
- danger_level
- surveillance_cost
- crowd_obstruction
- institutional_restriction
```

Routes can become:

```text
open
costly
exposed
dangerous
blocked
unknown
```

Blocked routes should emit `RouteAccessEvent` and may feed `BlockedCapacityEvent` for:

```text
exit
care
repair
evidence_access
truth_disclosure
survival
```

### 16.4 Rhythm Update

Rhythms should activate from clock and scenario calendar.

```text
active_rhythm_score =
  time_window_match
+ recurrence_match
+ event_calendar_match
+ institution_schedule_match
```

Rhythms should not force scenes. They alter probabilities and constraints.

Example:

```text
morning_market does not force a market scene.
It raises public visibility, rumor pressure, accidental encounter likelihood, and cost of direct confession.
```

### 16.5 Audience Update

Audience exposure should be computed from:

```text
location visibility
active rhythm
audience usual_locations
topic sensitivity
recent rumor events
institutional attention
```

Audience exposure states:

```text
none
possible
likely
observed
reported
institutionalized
```

Only `observed`, `reported`, or `institutionalized` exposure should be enough for strong public consequences.

### 16.6 Memory Site Update

Memory sites should activate when:

- a scene occurs at the linked location
- a process passes through the route
- an object, phrase, weather condition, or institution references the site
- a related recognition, misrecognition, or irreversibility event occurs

Recommended trace formula:

```text
memory_site_salience =
  base_salience
+ location_presence
+ symbolic_trigger
+ related_event_pressure
+ unresolved_recognition_pressure
- decay
```

Memory sites should decay unless reactivated.

This prevents one early event from infinitely dominating every later scene without renewed evidence.

### 16.7 Resource Update

Resources should update from consumption, replenishment, institutional access, route access, and social permission.

```text
resource_availability =
  quantity_state
+ replenishment
- consumption
- access_restriction
- route_blockage
- legitimacy_cost
```

Resource scarcity should feed capacity blockage, not directly produce drama.

Invalid:

```text
medicine scarce -> dramatic scene
```

Valid:

```text
medicine scarce -> care capacity blocked -> route to clinic becomes urgent -> public exposure risk rises -> scene crystallizes
```

---

## 17. Scene Location Selection

The local world must provide a concrete algorithmic basis for selecting scene locations.

### 17.1 Candidate Generation

Candidate locations should come from:

```text
active bindings
process current or habitual locations
active rhythms
resource locations
institutional obligations
memory sites
routes under pressure
recent unresolved scenes
```

The simulator should not choose from all locations equally.

### 17.2 Location Score

Recommended initial scoring function:

```text
location_score =
  binding_relevance
+ field_pressure_relevance
+ capacity_demand_relevance
+ active_rhythm_relevance
+ memory_site_salience
+ resource_pressure
+ institution_pressure
+ audience_pressure
+ route_accessibility
- travel_cost
- avoidance_capacity
- boundary_violation_penalty
```

Each score component should be written into diagnostics.

### 17.3 Route Score

When a scene requires movement, route score should be computed before location selection is finalized.

```text
route_score =
  accessibility
- travel_time_cost
- danger_cost
- exposure_cost
- weather_cost
+ urgency
+ binding_pressure
```

A high-score route is not always easy. Sometimes the selected route is selected because urgency overwhelms cost.

### 17.4 Scene Type Compatibility

Each candidate location should be checked against:

```text
allowed_scene_types
blocked_scene_types
forbidden_topics
audience exposure
institution permissions
memory site bias
```

Invalid:

```text
private confession in high-crowd market without deformation or inhibition evidence.
```

Valid:

```text
private confession demand in market -> ActionInhibitionEvent -> joke, silence, or public mask.
```

### 17.5 Required Diagnostics

Each non-latent tick should be able to write:

```text
local_world_trace.json
location_selection_trace.json
route_selection_trace.json
audience_exposure_trace.json
```

Each selected location record should include:

```text
selected_location
selected_route optional
candidate_scores
rejected_locations
why_here
why_not_elsewhere
active_boundary_rules
```

---

## 18. Boundary With Existing Systems

`LocalWorld` overlaps with several existing RPF concepts. The boundary must be explicit.

### 18.1 FieldState

```text
LocalWorld is the finite physical-social fact source.
FieldState is the broader causal field that also includes relation metrics, processes, institutions, and pressures.
```

`FieldState` may aggregate from `LocalWorld`, but it should not duplicate the full location graph.

### 18.2 SpatialArrangements

```text
SpatialArrangements should become the current projection of LocalWorld route and location state.
```

It answers:

```text
what is currently reachable, exposed, blocked, crowded, or dangerous?
```

### 18.3 TemporalPressures

```text
TemporalPressures should consume LocalWorld rhythms.
```

It answers:

```text
what is closing, beginning, recurring, delayed, or overdue?
```

### 18.4 AudienceNetwork

```text
AudienceNetwork should consume LocalWorld audience exposure states.
```

It answers:

```text
who may see, report, sanction, legitimize, or remember this scene?
```

### 18.5 EnactedMicroWorlds

```text
EnactedMicroWorlds are relation-specific meanings attached to local-world places and objects.
```

Example:

```text
the kitchen is a LocalWorld location
the unpaid bill on the refrigerator is an enacted micro-world object
```

### 18.6 Case Ledger Locations

For investigative scenarios:

```text
case_ledger.locations are epistemic records about places.
LocalWorld.locations are causal geography.
```

They may refer to the same place, but they answer different questions.

Example:

```text
LocalWorld: abandoned_factory is dangerous and rain-sensitive.
CaseLedger: abandoned_factory contains contested evidence and unreliable testimony.
```

### 18.7 Environment Trace

```text
environment_trace is the event/history log of local-world changes.
LocalWorld is the scenario and runtime state being changed.
```

---

## 19. Yellow Sign Town Template

The first reusable town template should be `yellow_sign_town`.

This template should be small enough to run, but rich enough to test bounded-world realism.

### 19.1 Required Locations

```text
police_archive
police_front_office
market_street
bus_stop
clinic_corridor
river_bridge
abandoned_factory
old_residential_lane
town_school_gate
lin_ya_room
zhou_jibai_office
```

### 19.2 Required Routes

```text
archive_to_front_office
front_office_to_market
market_to_bus_stop
market_to_clinic
market_to_old_lane
old_lane_to_river_bridge
river_bridge_to_abandoned_factory
archive_to_zhou_office
```

### 19.3 Required Rhythms

```text
morning_market
school_dismissal
clinic_queue
police_shift_change
night_rain
last_bus
case_anniversary
county_inspection_day
```

### 19.4 Required Audiences

```text
market_neighbors
police_colleagues
victim_families
clinic_staff
school_parents
county_reporters
retired_factory_workers
imagined_town_public
```

### 19.5 Required Memory Sites

```text
factory_missing_child_case
river_bridge_last_seen
archive_missing_record_shelf
market_rumor_corner
clinic_unfiled_report_window
school_gate_old_witness_spot
```

### 19.6 Required Ecological Conditions

```text
heavy_rain
yellow_fog
power_flicker
river_rise
mildew_season
road_mud
```

### 19.7 Template Acceptance

The template is acceptable when it can produce:

- a private evidence scene in the archive
- a public rumor-pressure scene in the market
- a route-blocked scene during rain
- a memory-site activation at the factory or bridge
- an audience-exposure event involving victim families or police colleagues
- an institutional record constraint in the archive or front office

---

## 20. Scenario Authoring

Add an optional `local_world` block to scenario YAML.

Minimal example:

```yaml
local_world:
  id: yellow_sign_town
  name: 黄印镇
  scale: town
  description: 一个被旧案、雨季、熟人网络和基层制度共同压住的小镇。

  boundary_rules:
    max_scene_scope: local_world_only
    new_location_policy: discovery_required
    offscreen_event_policy: trace_required
    route_required: true
    travel_time_required: true

  locations:
    - location_id: police_archive
      label: 派出所档案室
      location_type: police_archive
      access_level: restricted
      public_visibility: low
      rumor_density: medium
      surveillance_level: medium
      memory_charge: high
      allowed_scene_types:
        - evidence_review
        - controlled_disclosure

    - location_id: market_street
      label: 早市街
      location_type: market
      access_level: open
      public_visibility: high
      crowd_density: high
      rumor_density: high
      memory_charge: medium

    - location_id: abandoned_factory
      label: 废弃炼油厂
      location_type: ruin
      access_level: dangerous
      public_visibility: low
      memory_charge: high
      allowed_scene_types:
        - forbidden_symbol_confrontation
        - evidence_contamination

  routes:
    - route_id: archive_to_market
      from_location: police_archive
      to_location: market_street
      travel_time_minutes: 8
      exposure_level: medium
      danger_level: low

    - route_id: market_to_factory
      from_location: market_street
      to_location: abandoned_factory
      travel_time_minutes: 35
      exposure_level: low
      danger_level: medium
      weather_sensitivity: high
      blocked_by_conditions:
        - heavy_rain

  rhythms:
    - rhythm_id: morning_market
      label: 早市
      time_window: morning
      recurrence: daily
      active_locations:
        - market_street
      crowd_density_delta: 0.45
      rumor_pressure_delta: 0.55

    - rhythm_id: night_rain
      label: 夜雨
      time_window: night
      recurrence: seasonal
      mobility_cost_delta: 0.40
      available_scene_types:
        - delayed_return
        - private_confession

  audiences:
    - audience_id: market_neighbors
      label: 早市熟人
      audience_type: neighbor
      usual_locations:
        - market_street
      rumor_power: 0.72
      sanction_power: 0.35

  memory_sites:
    - site_id: factory_missing_child_case
      location_id: abandoned_factory
      memory_type: disappearance_site
      salience: 0.88
      contamination: 0.50
      avoidance_pressure: 0.66
      future_scene_biases:
        - testimony_gap
        - forbidden_symbol_confrontation
```

---

## 21. First Implementation Slice

The first executable version should be small.

### Phase 1: Trace-Only Local World

Implement:

```text
LocalWorld model
Location model
Route model
Rhythm model
MemorySite model
```

Emit:

```text
RhythmActivationEvent
LocationStateEvent
RouteAccessEvent
AudienceExposureEvent
```

Do not yet change action selection.

Acceptance tests:

```text
test_local_world_schema_loads
test_all_declared_routes_reference_valid_locations
test_active_rhythm_emits_trace
test_weather_can_change_route_state
test_location_state_trace_contains_pressure_components
```

### Phase 2: Scene Crystallization Integration

Use local world data to select:

```text
location
route context
time window
audience exposure
memory site refs
```

Acceptance:

```text
Every scene has a valid location_id.
Every nonlocal move has a route.
Every public reclassification has audience evidence.
No LLM-created location appears without LocationDiscoveryEvent.
```

Acceptance tests:

```text
test_scene_has_valid_location_id
test_scene_location_selection_writes_candidate_scores
test_nonlocal_scene_requires_route_context
test_high_public_visibility_blocks_private_confession_without_deformation
test_public_consequence_requires_audience_exposure
```

### Phase 3: Constraint Integration

Feed local world into the dramatic conflict framework:

```text
route blocked -> exit or care capacity blocked
public visibility high -> speech or recognition capacity blocked
memory site active -> memory integration or avoidance capacity pressured
resource scarce -> survival, care, or repair capacity blocked
```

Acceptance tests:

```text
test_blocked_route_feeds_blocked_capacity
test_active_memory_site_feeds_memory_pressure
test_resource_scarcity_feeds_capacity_demand_not_direct_drama
test_local_world_constraints_feed_affordance_selection
```

### Phase 4: Viewer Support

Add a viewer panel:

```text
Local World
- active location
- route
- rhythm
- audiences
- memory sites
- blocked routes
- local constraints
```

Acceptance tests:

```text
test_viewer_payload_contains_local_world
test_viewer_shows_active_location_and_route
test_viewer_links_local_world_items_to_source_events
```

---

## 22. Evaluation Criteria

The local world model succeeds when:

- scenes feel situated rather than floating
- repeated encounters are explained by routes, rhythms, institutions, and bindings
- public/private differences depend on actual audience exposure
- weather, distance, access, and resources change action availability
- places accumulate memory
- new places are introduced through explicit discovery
- offscreen events leave traceable records
- the LLM cannot freely expand the world

It fails when:

- scenes appear anywhere convenient
- characters avoid conflict by moving without cost
- new locations appear without trace
- public shame occurs without audience
- records change without institution
- weather is only atmosphere
- memory sites have no effect on future scenes
- town scale becomes fake openness

---

## 23. Non-Negotiable Invariants

```text
1. Every simulation has a bounded local world.
2. Every scene has a valid location.
3. Nonlocal movement requires a route.
4. New locations require discovery.
5. Public consequences require audience or institution evidence.
6. Place-based memory requires a memory site or source event.
7. Weather and ecology are constraints, not visual flavor only.
8. Offscreen events require trace.
9. The LLM may render locations but may not invent causal geography.
10. LocalWorld constrains action availability but never mutates derived views directly.
11. Static local-world facts and runtime local-world state must be separated.
12. Location selection must be auditable from candidate scores.
13. Case knowledge about a place must not overwrite causal geography without an event.
```

---

## 24. Summary

The bounded local world gives RPF physical pressure.

It turns the world from:

```text
an unlimited backdrop
```

into:

```text
a finite field of routes, locations, rhythms, audiences, institutions, resources, ecological pressure, and memory sites.
```

This improves realism because human conflict rarely occurs in abstract space.

It occurs somewhere:

```text
under a light,
beside a bill,
at a market,
in a hospital corridor,
on a bridge,
inside a record room,
on a road that rain may close,
in front of people who will remember.
```

RPF should make that somewhere causally real.
