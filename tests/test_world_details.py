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
    assert context["causal_world_details"] == []
    assert all(detail["discard_after_render"] is True for detail in context["ephemeral_details"])
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
    assert llm_payload["world_detail_context"]["ephemeral_details"]
    assert llm_payload["rules"]["world_detail_context_is_attention_gated"] is True
    assert "注意力只唤醒了当前可感知细节" in outline


def test_export_files_include_world_detail_context(tmp_path):
    output_dir = _run(tmp_path, steps=6)
    payload = build_viewer_payload(output_dir)
    files = _database_export_files(payload, report="report")

    assert "world_detail_context.json" in files
    assert "soft_world_profiles.json" in files
    assert "detail_gap_trace.json" in files
    assert "ephemeral_details_are_render_only" in files["world_detail_context.json"]


def _run(tmp_path, *, steps: int) -> Path:
    scenario = load_scenario(SCENARIO)
    output_dir = tmp_path / "run"
    sim = Simulator.from_scenario(scenario, SCENARIO, seed=42)
    sim.run(steps=steps, output_dir=output_dir)
    return output_dir

