from pathlib import Path

from rpf.core.semantics import material_urgency, unrecognized_contribution
from rpf.engine.simulator import Simulator
from rpf.scenarios.loader import load_scenario


def test_new_semantic_fields_are_preferred():
    scenario_path = Path("examples/shared_apartment_unresolved_sacrifice.yaml")
    sim = Simulator.from_scenario(load_scenario(scenario_path), scenario_path, seed=42)
    assert material_urgency(sim.state) == 0.45
    assert unrecognized_contribution(sim.state) == 0.82


def test_legacy_semantic_fields_remain_compatible():
    scenario_path = Path("examples/shared_apartment_unresolved_sacrifice.yaml")
    scenario = load_scenario(scenario_path)
    scenario["field_state"]["material_pressures"] = {"rent_due": 0.33}
    scenario["relation_metrics"] = {"unrecognized_sacrifice": 0.44}
    sim = Simulator.from_scenario(scenario, scenario_path, seed=42)
    assert material_urgency(sim.state) == 0.33
    assert unrecognized_contribution(sim.state) == 0.44
