from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from rpf.core.ids import event_id
from rpf.core.versioning import EVENT_VERSION, SCHEMA_VERSION


class Event(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_id: str
    schema_version: str = SCHEMA_VERSION
    event_version: int = EVENT_VERSION
    tick: int
    event_type: str
    source_layer: str
    payload: dict[str, Any] = Field(default_factory=dict)
    causal_refs: list[str] = Field(default_factory=list)
    deterministic_order: int

    @classmethod
    def make(
        cls,
        tick: int,
        order: int,
        event_type: str,
        source_layer: str,
        payload: dict[str, Any] | None = None,
        causal_refs: list[str] | None = None,
    ) -> "Event":
        return cls(
            event_id=event_id(tick, order, event_type),
            tick=tick,
            event_type=event_type,
            source_layer=source_layer,
            payload=payload or {},
            causal_refs=causal_refs or [],
            deterministic_order=order,
        )
