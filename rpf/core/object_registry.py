from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


RegistryKind = Literal["world", "record", "evidence", "message", "token"]


class WorldObjectSpec(BaseModel):
    model_config = ConfigDict(extra="allow")

    object_id: str
    label: str
    object_type: str = "unknown_object"
    location_id: str | None = None
    container_id: str | None = None
    owner_process_id: str | None = None
    controlling_institution: str | None = None
    access_level: str = "visible"
    visibility: str | float = "possible"
    portability: str = "fixed"
    condition: str = "stable"
    memory_charge: Any = 0.0
    linked_processes: list[str] = Field(default_factory=list)
    linked_events: list[str] = Field(default_factory=list)
    linked_records: list[str] = Field(default_factory=list)
    linked_evidence: list[str] = Field(default_factory=list)
    allowed_actions: list[str] = Field(default_factory=list)
    forbidden_actions: list[str] = Field(default_factory=list)
    current_state: dict[str, Any] = Field(default_factory=dict)


class RecordObjectSpec(BaseModel):
    model_config = ConfigDict(extra="allow")

    record_id: str
    label: str
    record_type: str = "document"
    location_id: str | None = None
    institution_id: str | None = None
    access_level: str = "restricted"
    authority_level: str | float = "unknown"
    legibility: str | float = "unknown"
    completeness: str | float = "unknown"
    alteration_risk: str | float = "unknown"
    official_status: str = "unknown"
    linked_processes: list[str] = Field(default_factory=list)
    linked_events: list[str] = Field(default_factory=list)
    linked_evidence: list[str] = Field(default_factory=list)
    custody_state: str = "unknown"
    current_state: dict[str, Any] = Field(default_factory=dict)


class EvidenceObjectSpec(BaseModel):
    model_config = ConfigDict(extra="allow")

    evidence_id: str
    label: str
    evidence_type: str = "unknown"
    registry_ref: str | None = None
    location_id: str | None = None
    custody_holder: str | None = None
    accessibility: str | float = "unknown"
    reliability: Any = 0.0
    contamination_risk: Any = 0.0
    legibility: str | float = "unknown"
    chain_of_custody_strength: str | float = "unknown"
    interpretive_status: str = "unexamined"
    linked_testimonies: list[str] = Field(default_factory=list)
    linked_records: list[str] = Field(default_factory=list)
    linked_locations: list[str] = Field(default_factory=list)
    forbidden_inferences: list[str] = Field(default_factory=list)
    current_state: dict[str, Any] = Field(default_factory=dict)


class MessageObjectSpec(BaseModel):
    model_config = ConfigDict(extra="allow")

    message_id: str
    message_type: str = "message"
    sender_process_id: str | None = None
    receiver_process_ids: list[str] = Field(default_factory=list)
    created_tick: int | None = None
    delivered_tick: int | None = None
    read_tick: int | None = None
    response_tick: int | None = None
    visibility: str = "private"
    deletion_state: str = "present"
    publicness: str = "private"
    institutional_status: str = "none"
    content_class: str = "unspecified"
    source_event_id: str | None = None


class AccessTokenSpec(BaseModel):
    model_config = ConfigDict(extra="allow")

    token_id: str
    token_type: str = "permission"
    label: str
    holder_process_id: str | None = None
    institution_id: str | None = None
    grants_access_to: list[str] = Field(default_factory=list)
    revocable: bool = True
    legitimacy: str | float = "unknown"
    visibility: str = "private"
    current_state: str = "active"


class ObjectLinkSpec(BaseModel):
    model_config = ConfigDict(extra="allow")

    link_id: str
    source_ref: str
    target_ref: str
    link_type: str
    strength: Any = 1.0
    evidence_refs: list[str] = Field(default_factory=list)


class ObjectRegistrySpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    world_objects: list[WorldObjectSpec] = Field(default_factory=list)
    record_objects: list[RecordObjectSpec] = Field(default_factory=list)
    evidence_objects: list[EvidenceObjectSpec] = Field(default_factory=list)
    message_objects: list[MessageObjectSpec] = Field(default_factory=list)
    access_tokens: list[AccessTokenSpec] = Field(default_factory=list)
    object_links: list[ObjectLinkSpec] = Field(default_factory=list)
    custody_log: list[dict[str, Any]] = Field(default_factory=list)
    state_history: list[dict[str, Any]] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_internal_references(self) -> "ObjectRegistrySpec":
        _ensure_unique("world object", [item.object_id for item in self.world_objects])
        _ensure_unique("record object", [item.record_id for item in self.record_objects])
        _ensure_unique("evidence object", [item.evidence_id for item in self.evidence_objects])
        _ensure_unique("message object", [item.message_id for item in self.message_objects])
        _ensure_unique("access token", [item.token_id for item in self.access_tokens])
        _ensure_unique("object link", [item.link_id for item in self.object_links])

        world_ids = {item.object_id for item in self.world_objects}
        record_ids = {item.record_id for item in self.record_objects}
        evidence_ids = {item.evidence_id for item in self.evidence_objects}
        message_ids = {item.message_id for item in self.message_objects}
        token_ids = {item.token_id for item in self.access_tokens}
        refs = _registry_refs(world_ids, record_ids, evidence_ids, message_ids, token_ids)

        for item in self.world_objects:
            if item.container_id:
                _require_ref("world_object.container_id", item.object_id, item.container_id, world_ids)
            for record_id in item.linked_records:
                _require_ref("world_object.linked_records", item.object_id, record_id, record_ids)
            for evidence_id in item.linked_evidence:
                _require_ref("world_object.linked_evidence", item.object_id, evidence_id, evidence_ids)

        for item in self.record_objects:
            for evidence_id in item.linked_evidence:
                _require_ref("record_object.linked_evidence", item.record_id, evidence_id, evidence_ids)

        for item in self.evidence_objects:
            if item.registry_ref:
                _require_registry_ref("evidence_object.registry_ref", item.evidence_id, item.registry_ref, refs)
            for record_id in item.linked_records:
                _require_ref("evidence_object.linked_records", item.evidence_id, record_id, record_ids)

        for item in self.access_tokens:
            for ref in item.grants_access_to:
                _require_registry_ref("access_token.grants_access_to", item.token_id, ref, refs)

        for item in self.object_links:
            _require_registry_ref("object_link.source_ref", item.link_id, item.source_ref, refs)
            _require_registry_ref("object_link.target_ref", item.link_id, item.target_ref, refs)
            for evidence_ref in item.evidence_refs:
                if evidence_ref in evidence_ids:
                    continue
                _require_registry_ref("object_link.evidence_refs", item.link_id, evidence_ref, refs)
        return self

    def validate_against_scenario(
        self,
        *,
        location_ids: set[str],
        institution_ids: set[str],
        process_ids: set[str],
        case_evidence_ids: set[str],
        local_world_evidence_refs: set[str],
        institution_record_refs: set[str],
    ) -> None:
        record_ids = {item.record_id for item in self.record_objects}
        evidence_ids = {item.evidence_id for item in self.evidence_objects}
        object_ids = {item.object_id for item in self.world_objects}
        token_ids = {item.token_id for item in self.access_tokens}

        for item in self.world_objects:
            _optional_ref("world_object.location_id", item.object_id, item.location_id, location_ids)
            _optional_ref("world_object.controlling_institution", item.object_id, item.controlling_institution, institution_ids)
            _optional_ref("world_object.owner_process_id", item.object_id, item.owner_process_id, process_ids)
            for process_id in item.linked_processes:
                _require_ref("world_object.linked_processes", item.object_id, process_id, process_ids)

        for item in self.record_objects:
            _optional_ref("record_object.location_id", item.record_id, item.location_id, location_ids)
            _optional_ref("record_object.institution_id", item.record_id, item.institution_id, institution_ids)
            for process_id in item.linked_processes:
                _require_ref("record_object.linked_processes", item.record_id, process_id, process_ids)

        for item in self.evidence_objects:
            _optional_ref("evidence_object.location_id", item.evidence_id, item.location_id, location_ids)
            _optional_ref("evidence_object.custody_holder", item.evidence_id, item.custody_holder, institution_ids | process_ids)
            for location_id in item.linked_locations:
                _require_ref("evidence_object.linked_locations", item.evidence_id, location_id, location_ids)

        for item in self.message_objects:
            _optional_ref("message_object.sender_process_id", item.message_id, item.sender_process_id, process_ids)
            for process_id in item.receiver_process_ids:
                _require_ref("message_object.receiver_process_ids", item.message_id, process_id, process_ids)

        for item in self.access_tokens:
            _optional_ref("access_token.holder_process_id", item.token_id, item.holder_process_id, process_ids)
            _optional_ref("access_token.institution_id", item.token_id, item.institution_id, institution_ids)

        missing_local_evidence = sorted(local_world_evidence_refs - evidence_ids - case_evidence_ids)
        if missing_local_evidence:
            raise ValueError(f"local_world evidence_refs missing from object_registry or case_ledger: {missing_local_evidence}")
        missing_records = sorted(institution_record_refs - record_ids)
        if missing_records:
            raise ValueError(f"local_world institution records missing from object_registry.record_objects: {missing_records}")
        registry_only_evidence = evidence_ids - case_evidence_ids
        if case_evidence_ids and registry_only_evidence:
            raise ValueError(f"object_registry evidence not declared in case_ledger.evidence_items: {sorted(registry_only_evidence)}")
        _ = object_ids, token_ids

    def active_excerpt(self, *, location_id: str | None = None, evidence_refs: set[str] | None = None) -> dict[str, Any]:
        evidence_refs = evidence_refs or set()
        active_evidence_ids = {
            item.evidence_id
            for item in self.evidence_objects
            if (location_id and item.location_id == location_id) or item.evidence_id in evidence_refs
        }
        active_record_ids = {
            record_id
            for item in self.evidence_objects
            if item.evidence_id in active_evidence_ids
            for record_id in item.linked_records
        }
        for item in self.record_objects:
            if location_id and item.location_id == location_id:
                active_record_ids.add(item.record_id)
        active_object_ids = {
            item.object_id
            for item in self.world_objects
            if (location_id and item.location_id == location_id)
            or any(evidence_id in active_evidence_ids for evidence_id in item.linked_evidence)
            or any(record_id in active_record_ids for record_id in item.linked_records)
        }
        return {
            "active_location_id": location_id,
            "world_objects": [item.model_dump(mode="json") for item in self.world_objects if item.object_id in active_object_ids],
            "record_objects": [item.model_dump(mode="json") for item in self.record_objects if item.record_id in active_record_ids],
            "evidence_objects": [item.model_dump(mode="json") for item in self.evidence_objects if item.evidence_id in active_evidence_ids],
            "access_tokens": [
                item.model_dump(mode="json")
                for item in self.access_tokens
                if any(_ref_target(ref) in active_object_ids | active_record_ids | active_evidence_ids for ref in item.grants_access_to)
            ],
        }


def _ensure_unique(label: str, values: list[str]) -> None:
    seen: set[str] = set()
    for value in values:
        if value in seen:
            raise ValueError(f"Duplicate {label} id: {value}")
        seen.add(value)


def _registry_refs(
    world_ids: set[str],
    record_ids: set[str],
    evidence_ids: set[str],
    message_ids: set[str],
    token_ids: set[str],
) -> set[str]:
    return (
        {f"world:{item}" for item in world_ids}
        | {f"object:{item}" for item in world_ids}
        | {f"record:{item}" for item in record_ids}
        | {f"evidence:{item}" for item in evidence_ids}
        | {f"message:{item}" for item in message_ids}
        | {f"token:{item}" for item in token_ids}
    )


def _ref_target(ref: str) -> str:
    return ref.split(":", 1)[1] if ":" in ref else ref


def _require_registry_ref(kind: str, owner: str, value: str, allowed: set[str]) -> None:
    if value not in allowed:
        raise ValueError(f"{kind} in {owner} references unknown registry ref: {value}")


def _optional_ref(kind: str, owner: str, value: str | None, allowed: set[str]) -> None:
    if value is not None:
        _require_ref(kind, owner, value, allowed)


def _require_ref(kind: str, owner: str, value: str, allowed: set[str]) -> None:
    if value not in allowed:
        raise ValueError(f"{kind} in {owner} references unknown id: {value}")
