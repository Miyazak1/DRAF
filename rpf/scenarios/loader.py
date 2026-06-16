from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from rpf.core.local_world import LocalWorldSpec


def load_scenario(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Scenario must be a mapping: {path}")
    for key in ("id", "processes", "bindings"):
        if key not in data:
            raise ValueError(f"Scenario missing required key: {key}")
    if "local_world" in data:
        data["local_world"] = LocalWorldSpec.model_validate(data["local_world"]).model_dump(mode="json")
    return data
