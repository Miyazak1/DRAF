from __future__ import annotations

from rpf.config import DatabaseSettings, database_settings
from rpf.storage.base import NullRunStore, RunStore
from rpf.storage.postgres import PostgresRunStore


def configured_run_store(settings: DatabaseSettings | None = None) -> RunStore:
    resolved = settings or database_settings()
    if resolved.enabled:
        return PostgresRunStore(resolved)
    return NullRunStore()
