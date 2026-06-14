from pathlib import Path

from rpf.engine.simulator import Simulator
from rpf.scenarios.loader import load_scenario


def test_irreversibility_has_future_constraints(tmp_path):
    scenario_path = Path("examples/shared_apartment_unresolved_sacrifice.yaml")
    sim = Simulator.from_scenario(load_scenario(scenario_path), scenario_path, seed=42)
    sim.run(steps=30, output_dir=tmp_path / "run")
    events = [e for e in sim.events if e.event_type == "IrreversibilityEvent"]
    assert events
    assert events[0].payload["future_constraints"]
    assert events[0].payload["lost_alternatives"]
