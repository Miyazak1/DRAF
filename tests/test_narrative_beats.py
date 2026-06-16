from pathlib import Path

from rpf.engine.simulator import Simulator
from rpf.llm import segments
from rpf.llm.renderer import build_render_payload
from rpf.scenarios.loader import load_scenario
from rpf.viewer.server import _database_export_files, build_viewer_payload


SCENARIO = Path("examples/yellow_sign_cold_case.yaml")


def test_viewer_payload_builds_narrative_beats(tmp_path):
    output_dir = _run(tmp_path, steps=6)
    payload = build_viewer_payload(output_dir)
    beats = payload["narrative_beats"]

    assert beats
    assert all(beat["beat_id"] for beat in beats)
    assert all(beat["beat_type"] for beat in beats)
    assert all("source_events" in beat for beat in beats)
    assert any(beat["intended_action"] for beat in beats if beat["beat_type"] != "pattern_continuation")
    assert any("outcome" in beat for beat in beats)


def test_render_payload_includes_narrative_beats(tmp_path):
    output_dir = _run(tmp_path, steps=6)
    payload = build_render_payload(output_dir)

    assert payload["narrative_beats"]
    assert payload["narrative_beats"][0]["rendering_constraints"]["do_not_change_causal_outcome"] is True


def test_segment_inherits_narrative_beats_and_outline_uses_them(tmp_path):
    output_dir = _run(tmp_path, steps=6)
    segment = segments.next_render_segment(output_dir, force=True)

    assert segment["narrative_beats"]
    text = segments.deterministic_segment_markdown(segment)

    assert "试图发生的是" in text
    assert "实际呈现为" in text
    assert "叙事节拍集中在" in text


def test_export_files_include_narrative_beats(tmp_path):
    output_dir = _run(tmp_path, steps=4)
    payload = build_viewer_payload(output_dir)
    files = _database_export_files(payload, report="report")

    assert "narrative_beats.json" in files
    assert "beat_type" in files["narrative_beats.json"]


def _run(tmp_path, *, steps: int) -> Path:
    scenario = load_scenario(SCENARIO)
    output_dir = tmp_path / "run"
    sim = Simulator.from_scenario(scenario, SCENARIO, seed=42)
    sim.run(steps=steps, output_dir=output_dir)
    return output_dir
