import json
from pathlib import Path

import pytest

from rpf.engine.simulator import Simulator
from rpf.benchmark import run_benchmark_suite
from rpf.scenarios.loader import load_scenario
from rpf.storage.timeline import read_timeline


SCENARIOS = sorted(Path("examples").glob("*.yaml"))


@pytest.mark.parametrize("scenario_path", SCENARIOS, ids=lambda p: p.stem)
def test_benchmark_scenario_runs_and_replays(scenario_path, tmp_path):
    scenario = load_scenario(scenario_path)
    seed = sum(ord(ch) for ch in scenario_path.stem) % 1000
    sim = Simulator.from_scenario(scenario, scenario_path, seed=seed)
    output_dir = tmp_path / scenario_path.stem
    result = sim.run(steps=30, output_dir=output_dir)

    metrics = result["metrics"]
    tick_types = {
        event.payload["tick_type"]
        for event in sim.events
        if event.event_type == "TickStartedEvent"
    }
    assert {"latent", "micro_interaction", "scene"} <= tick_types
    assert len(metrics["rpp_activation_counts"]) >= 2
    assert metrics["event_type_counts"]["ProjectionEvent"] == 30
    assert (output_dir / "effective_config.json").exists()
    assert (output_dir / "scheduler_diagnostics.json").exists()
    assert (output_dir / "affordance_trace.json").exists()
    assert (output_dir / "action_trace.json").exists()
    assert (output_dir / "expression_trace.json").exists()
    assert (output_dir / "recognition_trace.json").exists()
    assert (output_dir / "fate_transition_trace.json").exists()
    assert (output_dir / "frame_trace.json").exists()
    assert (output_dir / "account_trace.json").exists()
    assert (output_dir / "normativity_trace.json").exists()
    assert (output_dir / "relevance_trace.json").exists()
    assert (output_dir / "position_trace.json").exists()
    assert (output_dir / "binding_trace.json").exists()
    assert (output_dir / "expectation_trace.json").exists()
    assert (output_dir / "memory_trace.json").exists()
    assert (output_dir / "rpp_activation_trace.json").exists()
    assert (output_dir / "projection_trace.json").exists()
    assert (output_dir / "local_world_trace.json").exists()
    assert (output_dir / "location_selection_trace.json").exists()
    assert (output_dir / "route_selection_trace.json").exists()
    assert (output_dir / "audience_exposure_trace.json").exists()

    views = json.loads((output_dir / "derived_views.json").read_text())
    assert views["relationship_view"]["phase_label"]
    assert any(view["apparent_labels"] for view in views["person_views"].values())

    events = read_timeline(output_dir / "timeline.jsonl")
    expected = events[-1]["payload"]["final_state_hash"]
    replay = Simulator.from_scenario(load_scenario(scenario_path), scenario_path, seed=seed)
    replay_result = replay.run(steps=30, output_dir=tmp_path / f"{scenario_path.stem}_replay")
    assert replay_result["final_state_hash"] == expected


def test_benchmark_suite_has_multi_attractor_dominance(tmp_path):
    summary = run_benchmark_suite(Path("examples"), tmp_path / "benchmarks", steps=30, seed_base=1000)

    assert summary["all_replay_ok"] is True
    assert len(summary["dominant_affordance_distribution"]) >= 4
    assert summary["dominant_action_distribution"]
    assert summary["dominant_action_mode_distribution"]
    assert summary["dominant_expression_distribution"]
    assert summary["dominant_expression_mode_distribution"]
    assert len(summary["dominant_recognition_outcome_distribution"]) >= 3
    assert summary["dominant_operative_label_distribution"]
    assert summary["dominant_irreversibility_category_distribution"]
    assert summary["dominant_memory_bias_distribution"]
    assert len(summary["dominant_rpp_distribution"]) >= 5
    assert len(summary["dominant_composition_distribution"]) >= 5
    assert {"locked-in", "cold-war"} <= set(summary["phase_distribution"])
    assert any(item["irreversibility_count"] == 0 for item in summary["scenarios"])
    assert any(item["irreversibility_count"] > 0 for item in summary["scenarios"])
    assert any(item["memory_reconstruction_count"] > 0 for item in summary["scenarios"])
    assert any(item["action_inhibition_count"] > 0 or item["action_substitution_count"] > 0 for item in summary["scenarios"])
    assert all(item["rpp_activation_score_sums"] for item in summary["scenarios"])
    assert all(item["rpp_composition_score_sums"] for item in summary["scenarios"])
    assert any(
        "RPPSuppressionEvent" in json.loads((Path(item["output_dir"]) / "metrics.json").read_text())["event_type_counts"]
        for item in summary["scenarios"]
    )
    assert any(
        "RPPDecayEvent" in json.loads((Path(item["output_dir"]) / "metrics.json").read_text())["event_type_counts"]
        for item in summary["scenarios"]
    )
