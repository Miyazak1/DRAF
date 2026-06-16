from pathlib import Path

from rpf.engine.simulator import Simulator
from rpf.llm import segments
from rpf.llm.renderer import build_render_payload
from rpf.scenarios.loader import load_scenario
from rpf.viewer.server import _database_export_files, build_viewer_payload
from rpf.world.details import build_world_detail_context


SCENARIO = Path("examples/yellow_sign_cold_case.yaml")


def test_world_detail_context_requires_attention():
    context = build_world_detail_context({"attention": [], "story": []})

    assert context["attention_focuses"] == []
    assert context["ephemeral_details"] == []
    assert context["soft_world_profiles"] == []
    assert context["active_soft_profiles"] == []
    assert context["soft_profile_history"] == []
    assert context["causal_detail_candidates"] == []
    assert context["detail_persistence_decisions"] == []
    assert context["causal_world_details"] == []
    assert context["rules"]["no_attention_no_elaboration"] is True


def test_viewer_payload_builds_attention_gated_world_details(tmp_path):
    output_dir = _run(tmp_path, steps=8)
    payload = build_viewer_payload(output_dir)
    context = payload["world_detail_context"]

    assert context["attention_focuses"]
    assert context["detail_gaps"]
    assert context["ephemeral_details"]
    assert context["soft_world_profiles"]
    assert context["active_soft_profiles"]
    assert context["soft_profile_history"]
    assert context["causal_detail_candidates"]
    assert context["detail_persistence_decisions"]
    assert context["causal_world_details"]
    assert all(item["activation_state"] == "inactive" for item in context["causal_world_details"])
    assert all(item["causal_status"] == "validated_candidate" for item in context["causal_world_details"])
    assert all(decision["activation_allowed"] is False for decision in context["detail_persistence_decisions"])
    assert all(detail["discard_after_render"] is True for detail in context["ephemeral_details"])
    profile = context["active_soft_profiles"][0]
    assert profile["last_reinforced_tick"] >= profile["first_seen_tick"]
    assert profile["reinforcement_count"] >= 1
    assert profile["decay_policy"]["decays_when_scope_not_reinforced"] is True
    assert all(0 <= item["freshness"] <= 1 for item in context["soft_profile_history"])
    assert any(
        ref.startswith("detail:")
        for beat in payload["narrative_beats"]
        for ref in beat.get("local_detail_refs", [])
    )


def test_render_payload_and_segment_include_world_detail_context(tmp_path):
    output_dir = _run(tmp_path, steps=8)
    render_payload = build_render_payload(output_dir)
    segment = segments.next_render_segment(output_dir, force=True)
    llm_payload = segments._segment_llm_payload(segment, output_dir)
    outline = segments.deterministic_segment_markdown(segment)

    assert render_payload["world_detail_context"]["rules"]["ephemeral_details_are_render_only"] is True
    assert segment["world_detail_context"]["ephemeral_details"]
    assert segment["world_detail_context"]["active_soft_profiles"]
    assert segment["world_detail_context"]["soft_profile_history"]
    assert segment["world_detail_context"]["causal_world_details"]
    assert llm_payload["world_detail_context"]["ephemeral_details"]
    assert llm_payload["world_detail_context"]["causal_world_details"]
    assert llm_payload["rules"]["world_detail_context_is_attention_gated"] is True
    assert "注意力只唤醒了当前可感知细节" in outline
    assert "候选因果细节已被验证但尚未激活" in outline


def test_export_files_include_world_detail_context(tmp_path):
    output_dir = _run(tmp_path, steps=6)
    payload = build_viewer_payload(output_dir)
    files = _database_export_files(payload, report="report")

    assert "world_detail_context.json" in files
    assert "soft_world_profiles.json" in files
    assert "active_soft_profiles.json" in files
    assert "soft_profile_history.json" in files
    assert "detail_gap_trace.json" in files
    assert "causal_detail_candidates.json" in files
    assert "detail_persistence_decisions.json" in files
    assert "causal_world_details.json" in files
    assert "ephemeral_details_are_render_only" in files["world_detail_context.json"]


def _run(tmp_path, *, steps: int) -> Path:
    scenario = load_scenario(SCENARIO)
    output_dir = tmp_path / "run"
    sim = Simulator.from_scenario(scenario, SCENARIO, seed=42)
    sim.run(steps=steps, output_dir=output_dir)
    return output_dir
