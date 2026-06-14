import json
from pathlib import Path

from rpf.engine.simulator import Simulator
from rpf.scenarios.loader import load_scenario
from rpf.storage.timeline import read_timeline


SCENARIO = Path("examples/workplace_public_private_split.yaml")


def test_workplace_benchmark_runs_with_transferable_dynamics(tmp_path):
    scenario = load_scenario(SCENARIO)
    sim = Simulator.from_scenario(scenario, SCENARIO, seed=7)
    result = sim.run(steps=30, output_dir=tmp_path / "workplace")

    metrics = result["metrics"]
    tick_types = {
        event.payload["tick_type"]
        for event in sim.events
        if event.event_type == "TickStartedEvent"
    }
    assert {"latent", "micro_interaction", "scene"} <= tick_types
    assert len(metrics["rpp_activation_counts"]) >= 2
    assert metrics["event_type_counts"]["ProjectionEvent"] == 30

    views = json.loads((tmp_path / "workplace" / "derived_views.json").read_text())
    assert views["relationship_view"]["phase_label"] in {"repair-avoidant", "cold-war", "locked-in", "fragile"}
    assert any(view["apparent_labels"] for view in views["person_views"].values())

    events = read_timeline(tmp_path / "workplace" / "timeline.jsonl")
    expected = events[-1]["payload"]["final_state_hash"]
    replay = Simulator.from_scenario(load_scenario(SCENARIO), SCENARIO, seed=7)
    replay_result = replay.run(steps=30, output_dir=tmp_path / "workplace_replay")
    assert replay_result["final_state_hash"] == expected
