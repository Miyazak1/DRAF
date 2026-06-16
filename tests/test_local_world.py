import json
from pathlib import Path

import pytest

from rpf.core.local_world import LocalWorldSpec
from rpf.engine.simulator import Simulator
from rpf.scenarios.loader import load_scenario
from rpf.viewer.server import build_viewer_payload


SCENARIO = Path("examples/yellow_sign_cold_case.yaml")


def test_local_world_schema_loads():
    scenario = load_scenario(SCENARIO)
    spec = LocalWorldSpec.model_validate(scenario["local_world"])

    assert spec.id == "yellow_sign_town"
    assert spec.scale == "town"
    assert {location.location_id for location in spec.locations} >= {
        "police_archive",
        "market_street",
        "river_bridge",
        "abandoned_factory",
    }
    assert any(route.route_id == "river_bridge_to_abandoned_factory" for route in spec.routes)


def test_all_declared_routes_reference_valid_locations():
    spec = LocalWorldSpec.model_validate(load_scenario(SCENARIO)["local_world"])
    location_ids = {location.location_id for location in spec.locations}

    for route in spec.routes:
        assert route.from_location in location_ids
        assert route.to_location in location_ids


def test_local_world_rejects_unknown_route_location():
    scenario = load_scenario(SCENARIO)
    local_world = dict(scenario["local_world"])
    local_world["routes"] = [
        {
            "route_id": "bad_route",
            "from_location": "police_archive",
            "to_location": "ghost_clinic",
        }
    ]

    with pytest.raises(ValueError, match="ghost_clinic"):
        LocalWorldSpec.model_validate(local_world)


def test_active_rhythm_emits_trace(tmp_path):
    output_dir = _run_yellow_sign(tmp_path, steps=2)
    trace = _read_trace(output_dir)
    rhythms = [item for item in trace if item["event_type"] == "RhythmActivationEvent"]

    assert any(item["rhythm_id"] == "morning_market" for item in rhythms)
    assert all(item["time_window"] for item in rhythms)
    assert all("active_locations" in item for item in rhythms)


def test_weather_can_change_route_state(tmp_path):
    output_dir = _run_yellow_sign(tmp_path, steps=2)
    trace = _read_trace(output_dir)
    route_events = [
        item
        for item in trace
        if item["event_type"] == "RouteAccessEvent"
        and item["route_id"] == "river_bridge_to_abandoned_factory"
    ]

    assert route_events
    assert any(item["access_after"] == "blocked" for item in route_events)
    assert any("heavy_rain" in item["blocking_conditions"] for item in route_events)


def test_location_state_trace_contains_pressure_components(tmp_path):
    output_dir = _run_yellow_sign(tmp_path, steps=2)
    trace = _read_trace(output_dir)
    location_events = [
        item
        for item in trace
        if item["event_type"] == "LocationStateEvent"
        and item["location_id"] == "police_archive"
    ]

    assert location_events
    cause = location_events[0]["cause"]
    assert "base_memory_charge" in cause
    assert "active_rhythm_pressure" in cause
    assert "ecological_pressure" in cause
    assert "audience_pressure" in cause
    assert location_events[0]["new_state"]["pressure"] >= 0


def test_local_world_events_are_in_timeline(tmp_path):
    output_dir = _run_yellow_sign(tmp_path, steps=2)
    events = [
        json.loads(line)
        for line in (output_dir / "timeline.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    event_types = {event["event_type"] for event in events}

    assert "RhythmActivationEvent" in event_types
    assert "RouteAccessEvent" in event_types
    assert "LocationStateEvent" in event_types
    assert "AudienceExposureEvent" in event_types
    assert "MemorySiteActivationEvent" in event_types


def test_viewer_payload_contains_local_world(tmp_path):
    output_dir = _run_yellow_sign(tmp_path, steps=2)
    payload = build_viewer_payload(output_dir)

    assert payload["local_world"]
    assert any(item["event_type"] == "LocalWorldUpdateEvent" for item in payload["local_world"])


def _run_yellow_sign(tmp_path, *, steps: int) -> Path:
    scenario = load_scenario(SCENARIO)
    output_dir = tmp_path / "run"
    sim = Simulator.from_scenario(scenario, SCENARIO, seed=42)
    sim.run(steps=steps, output_dir=output_dir)
    return output_dir


def _read_trace(output_dir: Path) -> list[dict]:
    return json.loads((output_dir / "local_world_trace.json").read_text(encoding="utf-8"))
