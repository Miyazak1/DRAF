import json
from pathlib import Path

from rpf.engine.simulator import Simulator
from rpf.scenarios.loader import load_scenario
from rpf.storage.timeline import read_timeline


def test_replay_determinism(tmp_path):
    scenario_path = Path("examples/shared_apartment_unresolved_sacrifice.yaml")
    scenario = load_scenario(scenario_path)
    first = Simulator.from_scenario(scenario, scenario_path, seed=42)
    result = first.run(steps=30, output_dir=tmp_path / "run")

    events = read_timeline(tmp_path / "run" / "timeline.jsonl")
    expected = events[-1]["payload"]["final_state_hash"]
    assert expected == result["final_state_hash"]

    second = Simulator.from_scenario(load_scenario(scenario_path), scenario_path, seed=42)
    replay_result = second.run(steps=30, output_dir=tmp_path / "replay")
    assert replay_result["final_state_hash"] == expected
    metrics = json.loads((tmp_path / "run" / "metrics.json").read_text())
    assert metrics["irreversibility_count"] >= 1
