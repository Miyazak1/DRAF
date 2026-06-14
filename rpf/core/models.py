from __future__ import annotations

import hashlib
import json
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from rpf.core.versioning import SCHEMA_VERSION, STATE_VERSION


def clamp(value: float) -> float:
    return max(0.0, min(1.0, round(value, 4)))


class RecognitionDemand(BaseModel):
    model_config = ConfigDict(extra="forbid")

    demand_id: str
    holder_process_id: str
    demanded_from: str
    recognition_type: str
    explicitness: float = 0.0
    vulnerability_cost: float = 0.0
    threat_if_denied: float = 0.0
    identity_dependency: float = 0.0
    current_pressure: float = 0.0


class OperativeClassification(BaseModel):
    model_config = ConfigDict(extra="forbid")

    classification_id: str
    label: str
    target_process_id: str | None = None
    target_relation_id: str | None = None
    source_event_id: str
    uptake: str
    legitimacy: float
    future_interpretation_bias: float
    active: bool = True


class MemoryTrace(BaseModel):
    model_config = ConfigDict(extra="forbid")

    memory_id: str
    owner_process_id: str
    source_event_id: str
    remembered_as: str
    salience: float
    valence: float
    confidence: float
    reconstruction_biases: list[str] = Field(default_factory=list)
    active: bool = True


class ProcessState(BaseModel):
    model_config = ConfigDict(extra="forbid")

    process_id: str
    display_name: str
    fatigue: float = 0.0
    speech_inhibition: dict[str, float] = Field(default_factory=dict)
    threat_sensitivity: dict[str, float] = Field(default_factory=dict)
    relevance_triggers: dict[str, float] = Field(default_factory=dict)
    recognition_demands: list[RecognitionDemand] = Field(default_factory=list)
    active_classifications: list[OperativeClassification] = Field(default_factory=list)
    memory_traces: list[MemoryTrace] = Field(default_factory=list)
    stabilized_patterns: dict[str, float] = Field(default_factory=dict)
    checking_tendency: float = 0.2
    ambiguity_tolerance: float = 0.7
    risk_suspension_scope: float = 0.7
    repair_debt: float = 0.0
    resentment_pressure: float = 0.0

    def adjust(self, field: str, delta: float) -> None:
        setattr(self, field, clamp(float(getattr(self, field)) + delta))


class FieldState(BaseModel):
    model_config = ConfigDict(extra="forbid")

    material_pressures: dict[str, float] = Field(default_factory=dict)
    spatial_constraints: dict[str, float] = Field(default_factory=dict)
    audience_pressure: dict[str, float] = Field(default_factory=dict)
    enacted_micro_worlds: list[str] = Field(default_factory=list)


class CoPresenceBinding(BaseModel):
    model_config = ConfigDict(extra="forbid")

    binding_id: str
    binding_type: str
    process_ids: list[str]
    strength: float
    exit_cost: dict[str, float] = Field(default_factory=dict)


class ActiveRPP(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rpp_id: str
    participating_processes: list[str]
    activation_score: float
    intensity: float
    activation_reason_refs: list[str] = Field(default_factory=list)
    started_tick: int
    last_updated_tick: int


class IrreversibleRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    record_id: str
    category: str
    description: str
    source_event_id: str
    affected_processes: list[str]
    future_constraints: list[str]
    lost_alternatives: list[str]
    reversibility: Literal["none", "partial", "symbolic_only"] = "partial"


class IrreversibilityRegister(BaseModel):
    model_config = ConfigDict(extra="forbid")

    records: list[IrreversibleRecord] = Field(default_factory=list)


class TickContext(BaseModel):
    model_config = ConfigDict(extra="forbid")

    tick_index: int
    tick_type: Literal["latent", "micro_interaction", "scene"]
    simulated_time_delta_seconds: int
    time_mapping_reason: str


class SimulationState(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = SCHEMA_VERSION
    state_version: int = STATE_VERSION
    simulation_id: str
    tick: int = 0
    seed: int
    field_state: FieldState
    processes: dict[str, ProcessState]
    bindings: list[CoPresenceBinding]
    active_rpps: list[ActiveRPP] = Field(default_factory=list)
    irreversibility_register: IrreversibilityRegister = Field(default_factory=IrreversibilityRegister)
    relation_metrics: dict[str, float] = Field(
        default_factory=lambda: {
            "repair_debt": 0.0,
            "conflict_pressure": 0.0,
            "unrecognized_contribution": 0.8,
            "operative_label_count": 0.0,
            "repair_debt_growth": 1.0,
            "irreversibility_threshold": 0.68,
            "locked_in_repair_threshold": 0.55,
            "cold_war_repair_threshold": 0.35,
        }
    )

    def state_hash(self) -> str:
        payload = self.model_dump(mode="json")
        encoded = json.dumps(payload, sort_keys=True, ensure_ascii=True).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

