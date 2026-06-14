from __future__ import annotations

from dataclasses import dataclass

from rpf.core.events import Event
from rpf.core.models import SimulationState, TickContext


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
