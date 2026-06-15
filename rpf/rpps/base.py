from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from rpf.core.events import Event
from rpf.core.models import SimulationState, TickContext, clamp


@dataclass(frozen=True)
class Activation:
    rpp_id: str
    score: float
    participating_processes: list[str]
    evidence: list[str]
    effect: str


class BaseRPP:
    rpp_id: str

    def __init__(self, config: dict[str, object]) -> None:
        self.config = config

    def evaluate(self, state: SimulationState, context: TickContext, events: list[Event]) -> Activation | None:
        raise NotImplementedError

    def apply(self, state: SimulationState, activation: Activation) -> None:
        raise NotImplementedError


def future_constraint_pressure(
    events: list[Event],
    *,
    requirements: set[str] | None = None,
    type_terms: set[str] | None = None,
) -> tuple[float, list[str]]:
    """Bounded pressure from history-derived future constraints.

    RPPs may use this as evidence that prior history is making a pattern more
    likely, but it must remain a small score component rather than a plot force.
    """

    matches: list[Event] = []
    for event in events:
        if event.event_type != "FutureConstraintEvent":
            continue
        payload: dict[str, Any] = event.payload
        constrained = {str(item) for item in payload.get("constrained_requirements", [])}
        constraint_type = str(payload.get("constraint_type", ""))
        requirement_match = not requirements or bool(requirements.intersection(constrained))
        term_match = not type_terms or any(term in constraint_type for term in type_terms)
        if requirement_match or term_match:
            matches.append(event)
    if not matches:
        return 0.0, []
    pressure = clamp(max(_payload_float(event, "intensity") for event in matches))
    refs = sorted({event.event_id for event in matches})
    return pressure, refs


def activation_evidence(events: list[Event], future_refs: list[str], *, window: int = 4) -> list[str]:
    return sorted({event.event_id for event in events[-window:]} | set(future_refs))


def _payload_float(event: Event, key: str) -> float:
    try:
        return clamp(float(event.payload.get(key, 0.0)))
    except (TypeError, ValueError):
        return 0.0
