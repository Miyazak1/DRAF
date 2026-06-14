from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def load_scenario(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Scenario must be a mapping: {path}")
    for key in ("id", "processes", "bindings"):
        if key not in data:
            raise ValueError(f"Scenario missing required key: {key}")
    return data
