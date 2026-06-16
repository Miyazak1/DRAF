from __future__ import annotations

import copy
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "defaults.yaml"
DEFAULT_ENV_PATH = Path(__file__).resolve().parent.parent / ".env"


@dataclass(frozen=True)
class DatabaseSettings:
    backend: str
    database_url: str | None = None
    schema: str = "public"

    @property
    def enabled(self) -> bool:
        return self.backend in {"postgres", "postgresql"} and bool(self.database_url)


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


def load_env_file(path: Path = DEFAULT_ENV_PATH) -> dict[str, str]:
    if not path.exists():
        return {}
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            values[key] = value
    return values


def database_settings(
    *,
    env: dict[str, str] | None = None,
    env_path: Path = DEFAULT_ENV_PATH,
) -> DatabaseSettings:
    dotenv = load_env_file(env_path)
    source = {**dotenv, **(env if env is not None else os.environ)}
    database_url = source.get("RPF_DATABASE_URL") or source.get("DATABASE_URL")
    backend = (source.get("RPF_STORAGE_BACKEND") or ("postgres" if database_url else "file")).strip().lower()
    schema = (source.get("RPF_DATABASE_SCHEMA") or "public").strip() or "public"
    return DatabaseSettings(backend=backend, database_url=database_url, schema=schema)
