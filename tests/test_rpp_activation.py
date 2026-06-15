from pathlib import Path

from rpf.engine.simulator import Simulator
from rpf.scenarios.loader import load_scenario


SCENARIO = Path("examples/shared_apartment_unresolved_sacrifice.yaml")


def test_all_mvp_rpps_activate(tmp_path):
    scenario = load_scenario(SCENARIO)
    sim = Simulator.from_scenario(scenario, SCENARIO, seed=42)
    sim.run(steps=30, output_dir=tmp_path / "run")
    activated = {e.payload["rpp_id"] for e in sim.events if e.event_type == "RPPActivationEvent"}
    assert {"pursuit_withdrawal", "repair_avoidance", "contribution_debt_loop"} <= activated
    for event in sim.events:
        if event.event_type == "RPPActivationEvent":
            assert event.payload["eligibility_evidence"]
            assert event.payload["activation_score"] >= 0


def test_future_constraints_can_feed_rpp_activation(tmp_path):
    scenario = load_scenario(SCENARIO)
    sim = Simulator.from_scenario(scenario, SCENARIO, seed=42)
    sim.run(steps=30, output_dir=tmp_path / "run")

    future_constraint_ids = {
        event.event_id
        for event in sim.events
        if event.event_type == "FutureConstraintEvent"
    }
    rpp_events = [event for event in sim.events if event.event_type == "RPPActivationEvent"]

    assert future_constraint_ids
    assert any(future_constraint_ids.intersection(event.causal_refs) for event in rpp_events)
    assert any(
        future_constraint_ids.intersection(event.payload["eligibility_evidence"])
        for event in rpp_events
    )
