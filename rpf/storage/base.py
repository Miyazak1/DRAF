from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol

from rpf.core.events import Event
from rpf.core.models import SimulationState


class RunStore(Protocol):
    backend_name: str

    def upsert_scenario(
        self,
        *,
        scenario_id: str,
        title: str,
        source_yaml: str,
        source_path: Path | None = None,
        render_canon: dict[str, Any] | None = None,
        case_ledger: dict[str, Any] | None = None,
    ) -> None:
        ...

    def begin_run(
        self,
        *,
        run_id: str,
        scenario_id: str,
        title: str,
        seed: int,
        mode: str,
        output_dir: Path | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        ...

    def write_events(self, *, run_id: str, events: list[Event]) -> None:
        ...

    def write_traces(self, *, run_id: str, layer: str, records: list[dict[str, Any]]) -> None:
        ...

    def write_snapshot(self, *, run_id: str, state: SimulationState) -> None:
        ...

    def write_render_segment(self, *, run_id: str, segment: dict[str, Any]) -> None:
        ...

    def complete_run(
        self,
        *,
        run_id: str,
        status: str,
        tick_count: int,
        event_count: int,
        final_state_hash: str | None = None,
    ) -> None:
        ...


class NullRunStore:
    backend_name = "none"

    def upsert_scenario(self, **_: Any) -> None:
        return None

    def begin_run(self, **_: Any) -> None:
        return None

    def write_events(self, **_: Any) -> None:
        return None

    def write_traces(self, **_: Any) -> None:
        return None

    def write_snapshot(self, **_: Any) -> None:
        return None

    def write_render_segment(self, **_: Any) -> None:
        return None

    def complete_run(self, **_: Any) -> None:
        return None
