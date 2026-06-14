from __future__ import annotations

from typing import Any

SCHEMA_VERSION = "rpf-mvp/1"
STATE_VERSION = 1
EVENT_VERSION = 1
SNAPSHOT_VERSION = 1

SUPPORTED_SCHEMA_VERSIONS = {SCHEMA_VERSION}
SUPPORTED_STATE_VERSIONS = {STATE_VERSION}
SUPPORTED_EVENT_VERSIONS = {EVENT_VERSION}
SUPPORTED_SNAPSHOT_VERSIONS = {SNAPSHOT_VERSION}


class UnsupportedSchemaVersionError(ValueError):
    """Raised when a timeline, event, state, or snapshot version is unsupported."""


def manifest() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "state_version": STATE_VERSION,
        "event_version": EVENT_VERSION,
        "snapshot_version": SNAPSHOT_VERSION,
    }


def assert_supported_manifest(data: dict[str, Any]) -> None:
    schema_version = data.get("schema_version")
    state_version = data.get("state_version")
    event_version = data.get("event_version")
    snapshot_version = data.get("snapshot_version")
    if schema_version not in SUPPORTED_SCHEMA_VERSIONS:
        raise UnsupportedSchemaVersionError(f"Unsupported schema_version: {schema_version}")
    if state_version not in SUPPORTED_STATE_VERSIONS:
        raise UnsupportedSchemaVersionError(f"Unsupported state_version: {state_version}")
    if event_version not in SUPPORTED_EVENT_VERSIONS:
        raise UnsupportedSchemaVersionError(f"Unsupported event_version: {event_version}")
    if snapshot_version not in SUPPORTED_SNAPSHOT_VERSIONS:
        raise UnsupportedSchemaVersionError(f"Unsupported snapshot_version: {snapshot_version}")


def assert_supported_event(data: dict[str, Any]) -> None:
    version = data.get("event_version")
    if version not in SUPPORTED_EVENT_VERSIONS:
        raise UnsupportedSchemaVersionError(f"Unsupported event_version: {version}")
