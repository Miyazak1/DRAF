from __future__ import annotations

from pathlib import Path

from rpf.core.models import SimulationState
from rpf.core.versioning import SNAPSHOT_VERSION, manifest


def write_snapshot(output_dir: Path, state: SimulationState) -> None:
    snap_dir = output_dir / "snapshots"
    snap_dir.mkdir(parents=True, exist_ok=True)
    path = snap_dir / f"tick_{state.tick:03d}.json"
    payload = {
        "snapshot_version": SNAPSHOT_VERSION,
        "manifest": manifest(),
        "state_hash": state.state_hash(),
        "state": state.model_dump(mode="json"),
    }
    import json

    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
