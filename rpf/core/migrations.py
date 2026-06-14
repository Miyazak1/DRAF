from __future__ import annotations

from typing import Any

from rpf.core.versioning import SCHEMA_VERSION, UnsupportedSchemaVersionError


def migrate_manifest(data: dict[str, Any]) -> dict[str, Any]:
    """Migration hook for future schema versions.

    MVP has one supported schema and no migrations yet.
    """
    if data.get("schema_version") == SCHEMA_VERSION:
        return data
    raise UnsupportedSchemaVersionError(f"No migration path for schema_version: {data.get('schema_version')}")
