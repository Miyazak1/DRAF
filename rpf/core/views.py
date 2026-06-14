from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class PersonView(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    process_id: str
    apparent_labels: list[str] = Field(default_factory=list)
    stabilized_response_patterns: dict[str, float] = Field(default_factory=dict)
    unavailable_actions: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)


class RelationshipView(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    phase_label: str
    active_bindings: list[str] = Field(default_factory=list)
    recurring_rpps: list[str] = Field(default_factory=list)
    recognition_conflicts: list[str] = Field(default_factory=list)
    repair_patterns: list[str] = Field(default_factory=list)
    shared_irreversibles: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)


class AggregateViews(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    trust_view: dict[str, float | str]
    resentment_pressure_view: dict[str, float | str]
    repair_capacity_view: dict[str, float | str]
    person_views: dict[str, PersonView]
    relationship_view: RelationshipView
