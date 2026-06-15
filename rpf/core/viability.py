from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ViabilityConstraint(BaseModel):
    model_config = ConfigDict(extra="forbid")

    constraint_id: str
    constraint_type: str
    source_layer: str
    affected_processes: list[str]
    affected_requirements: list[str]
    intensity: float
    activation_condition: str
    duration_policy: str = "tick"
    decay_rate: float = 0.0
    reversibility: str = "partial"
    downstream_effects: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)


class ViabilityRequirement(BaseModel):
    model_config = ConfigDict(extra="forbid")

    requirement_id: str
    requirement_type: str
    holder_process_id: str
    target_process_id: str | None = None
    urgency: float
    negotiability: float
    minimum_satisfaction_condition: str
    failure_cost: float
    deformation_tendency: str
    source: str
    evidence_refs: list[str] = Field(default_factory=list)


class AffordanceWidth(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tick: int
    process_id: str
    width: float
    narrowing_constraints: list[str] = Field(default_factory=list)
    direct_response_cost: float
    evidence_refs: list[str] = Field(default_factory=list)


class DeformationTrace(BaseModel):
    model_config = ConfigDict(extra="forbid")

    deformation_id: str
    source_process_id: str
    target_process_id: str
    visible_form: str
    blocked_requirement_id: str | None = None
    deformation_type: str
    deformation_distance: float
    ambiguity: float
    observer_risk: float
    expected_recognition_failure_modes: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)


class FutureConstraintTrace(BaseModel):
    model_config = ConfigDict(extra="forbid")

    constraint_id: str
    constraint_type: str
    source_layer: str
    source_ref_id: str
    affected_processes: list[str]
    constrained_requirements: list[str]
    intensity: float
    persistence: str
    mechanism: str
    lost_alternatives: list[str] = Field(default_factory=list)
    downstream_effects: list[str] = Field(default_factory=list)
    evidence_refs: list[str] = Field(default_factory=list)


class ViabilityTickTrace(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tick: int
    tick_type: str
    constraints: list[ViabilityConstraint] = Field(default_factory=list)
    requirements: list[ViabilityRequirement] = Field(default_factory=list)
    affordance_widths: list[AffordanceWidth] = Field(default_factory=list)
    deformations: list[DeformationTrace] = Field(default_factory=list)
    future_constraints: list[FutureConstraintTrace] = Field(default_factory=list)
    dramatic_tension: float = 0.0
    evidence_refs: list[str] = Field(default_factory=list)
