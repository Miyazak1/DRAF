from pathlib import Path

from rpf.engine.simulator import Simulator
from rpf.scenarios.loader import load_scenario


def test_operative_classification_requires_event_uptake(tmp_path):
    scenario_path = Path("examples/shared_apartment_unresolved_sacrifice.yaml")
    sim = Simulator.from_scenario(load_scenario(scenario_path), scenario_path, seed=42)
    sim.run(steps=30, output_dir=tmp_path / "run")
    labels = [e for e in sim.events if e.event_type == "OperativeClassificationEvent"]
    constraints = [e for e in sim.events if e.event_type == "DownwardConstraintEvent"]
    assert labels
    assert constraints
    assert constraints[0].causal_refs == [labels[0].event_id]
