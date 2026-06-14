from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

import yaml


DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "defaults.yaml"


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = copy.deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = copy.deepcopy(value)
    return merged


def load_default_config() -> dict[str, Any]:
    return yaml.safe_load(DEFAULT_CONFIG_PATH.read_text(encoding="utf-8"))


def effective_config(scenario: dict[str, Any]) -> dict[str, Any]:
    overrides = copy.deepcopy(scenario.get("config_overrides", {}) or {})
    rpp_overrides = overrides.get("rpps", {})
    if "sacrifice_debt_loop" in rpp_overrides and "contribution_debt_loop" not in rpp_overrides:
        rpp_overrides["contribution_debt_loop"] = rpp_overrides.pop("sacrifice_debt_loop")
        overrides["rpps"] = rpp_overrides
    return deep_merge(load_default_config(), overrides)
