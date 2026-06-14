from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from rpf.core.events import Event
from rpf.core.versioning import assert_supported_event, assert_supported_manifest, manifest


class TimelineWriter:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._handle = self.path.open("w", encoding="utf-8")

    def write(self, event: Event) -> None:
        self._handle.write(event.model_dump_json() + "\n")

    def close(self) -> None:
        self._handle.close()

    def __enter__(self) -> "TimelineWriter":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()


def read_timeline(path: Path) -> list[dict[str, Any]]:
    events = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    for event in events:
        assert_supported_event(event)
    manifest_path = path.parent / "timeline_manifest.json"
    if manifest_path.exists():
        assert_supported_manifest(json.loads(manifest_path.read_text(encoding="utf-8")))
    return events


def write_timeline_manifest(output_dir: Path, *, scenario_path: Path, seed: int, steps: int) -> None:
    payload = manifest() | {
        "scenario_path": str(scenario_path),
        "seed": seed,
        "steps": steps,
    }
    (output_dir / "timeline_manifest.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
