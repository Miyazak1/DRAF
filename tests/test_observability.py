import json
from pathlib import Path

from rpf.engine.simulator import Simulator
from rpf.scenarios.loader import load_scenario


def test_observability_outputs_scheduler_rpp_and_projection_traces(tmp_path):
    scenario_path = Path("examples/shared_apartment_unresolved_sacrifice.yaml")
    sim = Simulator.from_scenario(load_scenario(scenario_path), scenario_path, seed=42)
    sim.run(steps=30, output_dir=tmp_path / "run")

    scheduler = json.loads((tmp_path / "run" / "scheduler_diagnostics.json").read_text())
    affordance = json.loads((tmp_path / "run" / "affordance_trace.json").read_text())
    action = json.loads((tmp_path / "run" / "action_trace.json").read_text())
    expression = json.loads((tmp_path / "run" / "expression_trace.json").read_text())
    recognition = json.loads((tmp_path / "run" / "recognition_trace.json").read_text())
    fate = json.loads((tmp_path / "run" / "fate_transition_trace.json").read_text())
    memory = json.loads((tmp_path / "run" / "memory_trace.json").read_text())
    rpp_trace = json.loads((tmp_path / "run" / "rpp_activation_trace.json").read_text())
    rpp_dynamics = json.loads((tmp_path / "run" / "rpp_dynamics_trace.json").read_text())
    projection = json.loads((tmp_path / "run" / "projection_trace.json").read_text())

    assert len(scheduler) == 30
    assert [item["tick_index"] for item in scheduler] == list(range(1, 31))
    assert {"scene", "micro_interaction", "latent"} <= {item["selected_tick_type"] for item in scheduler}
    assert all("tick_type_scores" in item for item in scheduler)
    assert all("time_mapping_reason" in item for item in scheduler)
    assert all("memory_pressure" in item["input_factors"] for item in scheduler)

    assert affordance
    assert all(item["selected_affordance"]["affordance_id"] for item in affordance)
    assert all(item["candidates"] for item in affordance)

    assert action
    assert all(item["selected_action"]["action_id"] for item in action)
    assert all(item["selected_action"]["action_mode"] for item in action)
    assert all(item["candidates"] for item in action)
    assert any(item["selected_action"]["action_mode"] in {"inhibited", "substituted", "escalated"} for item in action)

    assert expression
    assert all(item["selected_expression"]["expression_id"] for item in expression)
    assert all(item["selected_expression"]["expression_mode"] for item in expression)
    assert all(item["selected_expression"]["surface_signal"] for item in expression)
    assert all(item["candidates"] for item in expression)
    assert any(item["selected_expression"]["expression_mode"] in {"silence", "gesture", "timing_distortion", "tonal_shift"} for item in expression)

    assert recognition
    assert all(item["outcome"] for item in recognition)
    assert all(item["scores"] for item in recognition)
    assert all(item["evidence"] for item in recognition)
    assert any("memory_pressure" in item["evidence"] for item in recognition)
    assert any("action_mode" in item["evidence"] for item in recognition)
    assert any("expression_mode" in item["evidence"] for item in recognition)

    assert fate
    assert all(item["transition_id"] for item in fate)
    assert all(item["transition_type"] for item in fate)
    assert all(item["evidence"] for item in fate)

    assert memory
    assert all(item["memory_id"] for item in memory)
    assert all(item["owner_process_id"] for item in memory)
    assert all(item["remembered_as"] for item in memory)
    assert all(item["evidence"] for item in memory)
    assert any(item["reconstruction_biases"] for item in memory)

    assert rpp_trace
    assert {"pursuit_withdrawal", "repair_avoidance", "contribution_debt_loop"} <= {item["rpp_id"] for item in rpp_trace}
    assert all(item["eligibility_evidence"] for item in rpp_trace)
    assert any(item.get("semantic_role") == "unrecognized_contribution_debt" for item in rpp_trace)

    assert len(rpp_dynamics) == 30
    assert all("active_rpp_intensities" in item for item in rpp_dynamics)
    assert any(item["compositions"] for item in rpp_dynamics)

    assert len(projection) == 30
    assert projection[-1]["relationship_phase"] == "locked-in"
    assert projection[-1]["person_labels"]["p1"]
