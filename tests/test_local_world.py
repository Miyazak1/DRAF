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


def test_scene_has_valid_location_id(tmp_path):
    output_dir = _run_yellow_sign(tmp_path, steps=6)
    scenario = load_scenario(SCENARIO)
    location_ids = {item["location_id"] for item in scenario["local_world"]["locations"]}
    events = _read_events(output_dir)
    scene_events = [event for event in events if event["event_type"] == "SceneCrystallizationEvent"]

    assert scene_events
    for event in scene_events:
        payload = event["payload"]
        assert payload["location_id"] in location_ids
        assert payload["scene_context"]["location_id"] == payload["location_id"]
        assert payload["scene_context"]["time_window"]
        assert payload["scene_context"]["why_here"]
        assert payload["scene_context"]["why_not_elsewhere"]
        assert "possible_audiences" in payload["scene_context"]
        assert "memory_site_refs" in payload["scene_context"]


def test_scene_location_selection_writes_candidate_scores(tmp_path):
    output_dir = _run_yellow_sign(tmp_path, steps=6)
    location_selection = json.loads((output_dir / "location_selection_trace.json").read_text(encoding="utf-8"))

    assert location_selection
    selected = location_selection[0]
    assert selected["selected_location"]
    assert selected["candidate_scores"]
    assert selected["rejected_locations"]
    assert selected["why_here"]
    assert selected["why_not_elsewhere"]
    components = selected["candidate_scores"][0]["components"]
    assert "binding_relevance" in components
    assert "field_pressure_relevance" in components
    assert "active_rhythm_relevance" in components
    assert "route_accessibility" in components
    assert "boundary_violation_penalty" in components


def test_nonlocal_scene_requires_route_context(tmp_path):
    output_dir = _run_yellow_sign(tmp_path, steps=6)
    route_selection = json.loads((output_dir / "route_selection_trace.json").read_text(encoding="utf-8"))
    events = _read_events(output_dir)
    scene_events = [event for event in events if event["event_type"] == "SceneCrystallizationEvent"]

    assert route_selection
    assert any(item["selected_route"] for item in route_selection)
    for event in scene_events:
        route_context = event["payload"]["route_context"]
        assert route_context
        assert route_context["route_id"]
        assert route_context["access_status"] in {"open", "costly", "exposed", "dangerous", "blocked", "unknown"}


def test_micro_interaction_also_carries_local_scene_context(tmp_path):
    output_dir = _run_yellow_sign(tmp_path, steps=6)
    events = _read_events(output_dir)
    micro_events = [
        event
        for event in events
        if event["event_type"] == "MicroSignalEvent"
        and event["payload"].get("tick_type") == "micro_interaction"
    ]

    assert micro_events
    assert all(event["payload"]["scene_context"]["location_id"] for event in micro_events)


def test_public_consequence_requires_audience_exposure_context(tmp_path):
    output_dir = _run_yellow_sign(tmp_path, steps=6)
    audience_trace = json.loads((output_dir / "audience_exposure_trace.json").read_text(encoding="utf-8"))

    assert audience_trace
    for item in audience_trace:
        if item["public_consequence_allowed"]:
            assert any(
                audience["exposure_state"] in {"observed", "reported", "institutionalized"}
                for audience in item["possible_audiences"]
            )


def test_viewer_story_frames_include_locality(tmp_path):
    output_dir = _run_yellow_sign(tmp_path, steps=6)
    payload = build_viewer_payload(output_dir)
    situated_frames = [frame for frame in payload["story"] if frame.get("locality")]

    assert situated_frames
    assert situated_frames[0]["locality"]["location_id"]
    assert "场景被本地世界限定在" in situated_frames[0]["summary"]


def test_blocked_route_feeds_blocked_capacity(tmp_path):
    output_dir = _run_yellow_sign(tmp_path, steps=6)
    events = _read_events(output_dir)
    blocked_capacity = [
        event
        for event in events
        if event["event_type"] == "BlockedCapacityEvent"
        and event["payload"].get("blockage_source") == "route_access"
    ]

    assert blocked_capacity
    assert blocked_capacity[0]["payload"]["route_id"]
    assert blocked_capacity[0]["payload"]["capacity_id"] in {"exit", "care", "evidence_access"}
    assert blocked_capacity[0]["payload"]["intensity"] > 0


def test_active_memory_site_feeds_memory_pressure(tmp_path):
    output_dir = _run_yellow_sign(tmp_path, steps=6)
    events = _read_events(output_dir)
    memory_pressure_events = [
        event
        for event in events
        if event["event_type"] == "BlockedCapacityEvent"
        and event["payload"].get("blockage_source") == "memory_site"
    ]
    trace = _read_trace(output_dir)

    assert memory_pressure_events
    assert memory_pressure_events[0]["payload"]["capacity_id"] == "memory_integration"
    assert memory_pressure_events[0]["payload"]["site_id"]
    assert any(item["event_type"] == "LocalWorldConstraintIntegrationEvent" for item in trace)


def test_resource_scarcity_feeds_capacity_demand_not_direct_drama(tmp_path):
    output_dir = _run_yellow_sign(tmp_path, steps=6)
    events = _read_events(output_dir)
    demands = [
        event
        for event in events
        if event["event_type"] == "CapacityDemandEvent"
        and event["payload"].get("demand_source") == "resource_scarcity"
    ]
    scenes = [event for event in events if event["event_type"] == "SceneCrystallizationEvent"]

    assert demands
    assert demands[0]["payload"]["linked_capacities"]
    assert all(scene["payload"].get("affordance_id") != "resource_scarcity" for scene in scenes)


def test_local_world_constraints_feed_affordance_selection(tmp_path):
    output_dir = _run_yellow_sign(tmp_path, steps=6)
    affordance_trace = json.loads((output_dir / "affordance_trace.json").read_text(encoding="utf-8"))
    events = _read_events(output_dir)
    selections = [event for event in events if event["event_type"] == "AffordanceSelectionEvent"]

    assert affordance_trace
    assert any(item.get("local_world_context") for item in affordance_trace)
    assert any(
        key.startswith("local_world.")
        for item in affordance_trace
        for candidate in item.get("candidates", [])
        for key in candidate.get("evidence", {})
    )
    assert any(selection["payload"].get("local_world_context") for selection in selections)


def _run_yellow_sign(tmp_path, *, steps: int) -> Path:
    scenario = load_scenario(SCENARIO)
    output_dir = tmp_path / "run"
    sim = Simulator.from_scenario(scenario, SCENARIO, seed=42)
    sim.run(steps=steps, output_dir=output_dir)
    return output_dir


def _read_trace(output_dir: Path) -> list[dict]:
    return json.loads((output_dir / "local_world_trace.json").read_text(encoding="utf-8"))


def _read_events(output_dir: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in (output_dir / "timeline.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
