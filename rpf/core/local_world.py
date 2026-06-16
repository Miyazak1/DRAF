from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from rpf.core.models import clamp


Scale = Literal[
    "household",
    "apartment_building",
    "workplace",
    "school",
    "hospital",
    "village",
    "town",
    "district",
    "island",
    "ship",
    "station",
    "institutional_complex",
]


def normalized_pressure(value: Any, default: float = 0.0) -> float:
    if value is None:
        return default
    if isinstance(value, str):
        mapping = {
            "none": 0.0,
            "low": 0.25,
            "medium": 0.5,
            "high": 0.75,
            "very_high": 0.92,
            "open": 0.9,
            "restricted": 0.38,
            "dangerous": 0.24,
            "blocked": 0.0,
        }
        return mapping.get(value.strip().lower(), default)
    try:
        return clamp(float(value))
    except (TypeError, ValueError):
        return default


class BoundaryRules(BaseModel):
    model_config = ConfigDict(extra="allow")

    max_scene_scope: str = "local_world_only"
    new_location_policy: str = "discovery_required"
    offscreen_event_policy: str = "trace_required"
    route_required: bool = True
    travel_time_required: bool = True
    audience_required_for_public_reclassification: bool = True
    institution_required_for_record_change: bool = True
    memory_site_required_for_place_based_reconstruction: bool = True


class LocationSpec(BaseModel):
    model_config = ConfigDict(extra="allow")

    location_id: str
    label: str
    location_type: str = "unknown"
    access_level: str = "open"
    controlling_institution: str | None = None
    public_visibility: Any = 0.0
    crowd_density: Any = 0.0
    rumor_density: Any = 0.0
    surveillance_level: Any = 0.0
    memory_charge: Any = 0.0
    material_conditions: dict[str, Any] = Field(default_factory=dict)
    forbidden_topics: list[str] = Field(default_factory=list)
    allowed_scene_types: list[str] = Field(default_factory=list)
    blocked_scene_types: list[str] = Field(default_factory=list)
    linked_processes: list[str] = Field(default_factory=list)
    linked_events: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)


class RouteSpec(BaseModel):
    model_config = ConfigDict(extra="allow")

    route_id: str
    from_location: str
    to_location: str
    travel_time_minutes: int = 0
    access_level: str = "open"
    exposure_level: Any = 0.0
    danger_level: Any = 0.0
    weather_sensitivity: Any = 0.0
    crowd_pattern: str | None = None
    surveillance_points: list[str] = Field(default_factory=list)
    memory_charge: Any = 0.0
    blocked_by_conditions: list[str] = Field(default_factory=list)
    route_events: list[str] = Field(default_factory=list)


class RhythmSpec(BaseModel):
    model_config = ConfigDict(extra="allow")

    rhythm_id: str
    label: str
    time_window: str
    recurrence: str = "daily"
    active_locations: list[str] = Field(default_factory=list)
    crowd_density_delta: Any = 0.0
    rumor_pressure_delta: Any = 0.0
    mobility_cost_delta: Any = 0.0
    institutional_pressure_delta: Any = 0.0
    available_scene_types: list[str] = Field(default_factory=list)
    blocked_scene_types: list[str] = Field(default_factory=list)


class ResourceSpec(BaseModel):
    model_config = ConfigDict(extra="allow")

    resource_id: str
    label: str
    resource_type: str
    quantity_state: Any = 1.0
    controller: str | None = None
    access_rules: list[str] = Field(default_factory=list)
    scarcity_level: Any = 0.0
    replacement_access: Any = 0.0
    linked_capacities: list[str] = Field(default_factory=list)
    conflict_potential: Any = 0.0


class AudienceSpec(BaseModel):
    model_config = ConfigDict(extra="allow")

    audience_id: str
    label: str
    audience_type: str = "observer"
    usual_locations: list[str] = Field(default_factory=list)
    visibility_pattern: str = "possible"
    rumor_power: Any = 0.0
    sanction_power: Any = 0.0
    legitimacy_power: Any = 0.0
    affected_topics: list[str] = Field(default_factory=list)
    relationship_to_processes: dict[str, Any] = Field(default_factory=dict)


class InstitutionSpec(BaseModel):
    model_config = ConfigDict(extra="allow")

    institution_id: str
    label: str
    domain: str
    locations: list[str] = Field(default_factory=list)
    recognized_roles: list[str] = Field(default_factory=list)
    records: list[str] = Field(default_factory=list)
    access_permissions: dict[str, Any] = Field(default_factory=dict)
    sanction_rules: list[str] = Field(default_factory=list)
    silence_rules: list[str] = Field(default_factory=list)
    legitimacy_rules: list[str] = Field(default_factory=list)
    corruption_or_decay: Any = 0.0


class MemorySiteSpec(BaseModel):
    model_config = ConfigDict(extra="allow")

    site_id: str
    location_id: str
    memory_type: str
    source_events: list[str] = Field(default_factory=list)
    affected_processes: list[str] = Field(default_factory=list)
    salience: Any = 0.0
    contamination: Any = 0.0
    avoidance_pressure: Any = 0.0
    attraction_pressure: Any = 0.0
    possible_reclassification: list[str] = Field(default_factory=list)
    future_scene_biases: list[str] = Field(default_factory=list)


class EcologicalConditionSpec(BaseModel):
    model_config = ConfigDict(extra="allow")

    condition_id: str
    label: str
    condition_type: str
    active_time_window: str | None = None
    affected_routes: list[str] = Field(default_factory=list)
    affected_locations: list[str] = Field(default_factory=list)
    mobility_delta: Any = 0.0
    visibility_delta: Any = 0.0
    bodily_cost_delta: Any = 0.0
    evidence_degradation_delta: Any = 0.0
    audience_density_delta: Any = 0.0


class LocalWorldSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    scale: Scale
    description: str = ""
    boundary_rules: BoundaryRules = Field(default_factory=BoundaryRules)
    locations: list[LocationSpec] = Field(default_factory=list)
    routes: list[RouteSpec] = Field(default_factory=list)
    rhythms: list[RhythmSpec] = Field(default_factory=list)
    resources: list[ResourceSpec] = Field(default_factory=list)
    audiences: list[AudienceSpec] = Field(default_factory=list)
    institutions: list[InstitutionSpec] = Field(default_factory=list)
    memory_sites: list[MemorySiteSpec] = Field(default_factory=list)
    ecological_conditions: list[EcologicalConditionSpec] = Field(default_factory=list)
    offscreen_policy: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_references(self) -> "LocalWorldSpec":
        _ensure_unique("location", [item.location_id for item in self.locations])
        _ensure_unique("route", [item.route_id for item in self.routes])
        _ensure_unique("rhythm", [item.rhythm_id for item in self.rhythms])
        _ensure_unique("resource", [item.resource_id for item in self.resources])
        _ensure_unique("audience", [item.audience_id for item in self.audiences])
        _ensure_unique("institution", [item.institution_id for item in self.institutions])
        _ensure_unique("memory site", [item.site_id for item in self.memory_sites])
        _ensure_unique("ecological condition", [item.condition_id for item in self.ecological_conditions])
        location_ids = {item.location_id for item in self.locations}
        route_ids = {item.route_id for item in self.routes}
        condition_ids = {item.condition_id for item in self.ecological_conditions}
        condition_types = {item.condition_type for item in self.ecological_conditions}
        for route in self.routes:
            _require_ref("route.from_location", route.route_id, route.from_location, location_ids)
            _require_ref("route.to_location", route.route_id, route.to_location, location_ids)
            for condition in route.blocked_by_conditions:
                if condition not in condition_ids and condition not in condition_types:
                    raise ValueError(f"route {route.route_id} references unknown blocking condition: {condition}")
        for rhythm in self.rhythms:
            for location_id in rhythm.active_locations:
                _require_ref("rhythm.active_locations", rhythm.rhythm_id, location_id, location_ids)
        for audience in self.audiences:
            for location_id in audience.usual_locations:
                _require_ref("audience.usual_locations", audience.audience_id, location_id, location_ids)
        for institution in self.institutions:
            for location_id in institution.locations:
                _require_ref("institution.locations", institution.institution_id, location_id, location_ids)
        for memory_site in self.memory_sites:
            _require_ref("memory_site.location_id", memory_site.site_id, memory_site.location_id, location_ids)
        for condition in self.ecological_conditions:
            for location_id in condition.affected_locations:
                _require_ref("ecological_condition.affected_locations", condition.condition_id, location_id, location_ids)
            for route_id in condition.affected_routes:
                _require_ref("ecological_condition.affected_routes", condition.condition_id, route_id, route_ids)
        return self


class LocationRuntimeState(BaseModel):
    model_config = ConfigDict(extra="forbid")

    location_id: str
    accessibility: float = 1.0
    pressure: float = 0.0
    crowd_density: float = 0.0
    rumor_density: float = 0.0
    surveillance_level: float = 0.0
    memory_salience: float = 0.0
    contamination: float = 0.0
    last_scene_tick: int | None = None


class RouteRuntimeState(BaseModel):
    model_config = ConfigDict(extra="forbid")

    route_id: str
    accessibility: float = 1.0
    access_status: Literal["open", "costly", "exposed", "dangerous", "blocked", "unknown"] = "open"
    travel_time_minutes: int = 0
    exposure: float = 0.0
    danger: float = 0.0
    blocking_conditions: list[str] = Field(default_factory=list)


class AudienceRuntimeState(BaseModel):
    model_config = ConfigDict(extra="forbid")

    audience_id: str
    exposure_state: Literal["none", "possible", "likely", "observed", "reported", "institutionalized"] = "none"
    exposure_level: float = 0.0
    active_locations: list[str] = Field(default_factory=list)


class MemorySiteRuntimeState(BaseModel):
    model_config = ConfigDict(extra="forbid")

    site_id: str
    salience: float = 0.0
    active: bool = False


class ResourceRuntimeState(BaseModel):
    model_config = ConfigDict(extra="forbid")

    resource_id: str
    availability: float = 1.0
    scarcity_level: float = 0.0


class LocalWorldState(BaseModel):
    model_config = ConfigDict(extra="forbid")

    world_id: str
    current_time_window: str = "morning"
    elapsed_seconds: int = 0
    active_rhythms: list[str] = Field(default_factory=list)
    active_ecological_conditions: list[str] = Field(default_factory=list)
    location_states: dict[str, LocationRuntimeState] = Field(default_factory=dict)
    route_states: dict[str, RouteRuntimeState] = Field(default_factory=dict)
    resource_states: dict[str, ResourceRuntimeState] = Field(default_factory=dict)
    audience_exposure_states: dict[str, AudienceRuntimeState] = Field(default_factory=dict)
    active_memory_sites: dict[str, MemorySiteRuntimeState] = Field(default_factory=dict)
    local_world_pressure: float = 0.0

    @classmethod
    def from_spec(cls, spec: LocalWorldSpec) -> "LocalWorldState":
        return cls(
            world_id=spec.id,
            location_states={
                item.location_id: LocationRuntimeState(
                    location_id=item.location_id,
                    accessibility=normalized_pressure(item.access_level, 1.0),
                    crowd_density=normalized_pressure(item.crowd_density),
                    rumor_density=normalized_pressure(item.rumor_density),
                    surveillance_level=normalized_pressure(item.surveillance_level),
                    memory_salience=normalized_pressure(item.memory_charge),
                    contamination=normalized_pressure(item.material_conditions.get("contamination", 0.0)),
                )
                for item in spec.locations
            },
            route_states={
                item.route_id: RouteRuntimeState(
                    route_id=item.route_id,
                    accessibility=normalized_pressure(item.access_level, 1.0),
                    travel_time_minutes=item.travel_time_minutes,
                    exposure=normalized_pressure(item.exposure_level),
                    danger=normalized_pressure(item.danger_level),
                )
                for item in spec.routes
            },
            resource_states={
                item.resource_id: ResourceRuntimeState(
                    resource_id=item.resource_id,
                    availability=clamp(1.0 - normalized_pressure(item.scarcity_level)),
                    scarcity_level=normalized_pressure(item.scarcity_level),
                )
                for item in spec.resources
            },
            audience_exposure_states={
                item.audience_id: AudienceRuntimeState(audience_id=item.audience_id)
                for item in spec.audiences
            },
            active_memory_sites={
                item.site_id: MemorySiteRuntimeState(
                    site_id=item.site_id,
                    salience=normalized_pressure(item.salience),
                    active=normalized_pressure(item.salience) >= 0.5,
                )
                for item in spec.memory_sites
            },
        )


def _ensure_unique(label: str, values: list[str]) -> None:
    seen: set[str] = set()
    for value in values:
        if value in seen:
            raise ValueError(f"Duplicate {label} id: {value}")
        seen.add(value)


def _require_ref(kind: str, owner: str, value: str, allowed: set[str]) -> None:
    if value not in allowed:
        raise ValueError(f"{kind} in {owner} references unknown id: {value}")
