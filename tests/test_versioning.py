import json
from pathlib import Path

import pytest

from rpf.core.versioning import EVENT_VERSION, SCHEMA_VERSION, SNAPSHOT_VERSION, STATE_VERSION, UnsupportedSchemaVersionError
from rpf.engine.simulator import Simulator
from rpf.scenarios.loader import load_scenario
from rpf.storage.timeline import read_timeline


def test_timeline_state_event_and_snapshot_versions_are_written(tmp_path):
    scenario_path = Path("examples/shared_apartment_unresolved_sacrifice.yaml")
    sim = Simulator.from_scenario(load_scenario(scenario_path), scenario_path, seed=42)
    sim.run(steps=5, output_dir=tmp_path / "run")

    manifest = json.loads((tmp_path / "run" / "timeline_manifest.json").read_text())
    assert manifest["schema_version"] == SCHEMA_VERSION
    assert manifest["state_version"] == STATE_VERSION
    assert manifest["event_version"] == EVENT_VERSION
    assert manifest["snapshot_version"] == SNAPSHOT_VERSION

    events = read_timeline(tmp_path / "run" / "timeline.jsonl")
    assert all(event["schema_version"] == SCHEMA_VERSION for event in events)
    assert all(event["event_version"] == EVENT_VERSION for event in events)

    snapshot = json.loads((tmp_path / "run" / "snapshots" / "tick_005.json").read_text())
    assert snapshot["snapshot_version"] == SNAPSHOT_VERSION
    assert snapshot["manifest"]["state_version"] == STATE_VERSION
    assert snapshot["state"]["state_version"] == STATE_VERSION
    assert snapshot["state_hash"]


def test_unsupported_manifest_version_is_rejected(tmp_path):
    scenario_path = Path("examples/shared_apartment_unresolved_sacrifice.yaml")
    sim = Simulator.from_scenario(load_scenario(scenario_path), scenario_path, seed=42)
    sim.run(steps=5, output_dir=tmp_path / "run")

    manifest_path = tmp_path / "run" / "timeline_manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["schema_version"] = "future-schema"
    manifest_path.write_text(json.dumps(manifest))

    with pytest.raises(UnsupportedSchemaVersionError):
        read_timeline(tmp_path / "run" / "timeline.jsonl")
