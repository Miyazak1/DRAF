import json
from copy import deepcopy
from pathlib import Path

from rpf.config import effective_config, load_default_config
from rpf.engine.simulator import Simulator
from rpf.scenarios.loader import load_scenario


def test_effective_config_written_and_matches_defaults(tmp_path):
    scenario_path = Path("examples/shared_apartment_unresolved_sacrifice.yaml")
    scenario = load_scenario(scenario_path)
    sim = Simulator.from_scenario(scenario, scenario_path, seed=42)
    sim.run(steps=5, output_dir=tmp_path / "run")

    written = json.loads((tmp_path / "run" / "effective_config.json").read_text())
    assert written == effective_config(scenario)
    assert written["scheduler"]["thresholds"]["scene"] == load_default_config()["scheduler"]["thresholds"]["scene"]


def test_scenario_config_override_changes_effective_config(tmp_path):
    scenario_path = Path("examples/shared_apartment_unresolved_sacrifice.yaml")
    scenario = deepcopy(load_scenario(scenario_path))
    scenario["config_overrides"] = {
        "scheduler": {
            "thresholds": {"scene": 0.99},
            "forced_scene_ticks": [],
        },
        "rpps": {
            "sacrifice_debt_loop": {
                "threshold": 0.99,
                "weights": {"unrecognized_contribution": 0.11},
            }
        },
    }
    config = effective_config(scenario)
    assert config["scheduler"]["thresholds"]["scene"] == 0.99
    assert config["scheduler"]["thresholds"]["micro_interaction"] == 0.45
    assert config["rpps"]["contribution_debt_loop"]["threshold"] == 0.99
    assert config["rpps"]["contribution_debt_loop"]["weights"]["unrecognized_contribution"] == 0.11

    sim = Simulator.from_scenario(scenario, scenario_path, seed=42)
    sim.run(steps=5, output_dir=tmp_path / "override")
    written = json.loads((tmp_path / "override" / "effective_config.json").read_text())
    assert written["scheduler"]["forced_scene_ticks"] == []
