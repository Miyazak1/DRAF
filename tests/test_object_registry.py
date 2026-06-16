import json
from pathlib import Path

import pytest

from rpf.core.object_registry import ObjectRegistrySpec
from rpf.engine.simulator import Simulator
from rpf.llm.renderer import build_render_payload
from rpf.llm.segments import next_render_segment
from rpf.scenarios.loader import load_scenario
from rpf.viewer.server import build_viewer_payload


SCENARIO = Path("examples/yellow_sign_cold_case.yaml")


def test_object_registry_schema_loads():
    scenario = load_scenario(SCENARIO)
    registry = ObjectRegistrySpec.model_validate(scenario["object_registry"])

    assert {item.evidence_id for item in registry.evidence_objects} >= {
        "yellow_paint_mark",
        "water_damaged_child_drawing",
        "refinery_map_gap",
        "old_tape_yellow_bleed",
    }
    assert any(item.record_id == "old_case_file" for item in registry.record_objects)
    assert any(item.object_id == "yellow_paint_mark_object" for item in registry.world_objects)


def test_loader_supplies_empty_registry_for_legacy_scenarios():
    scenario = load_scenario(Path("examples/shared_apartment_unresolved_sacrifice.yaml"))

    assert scenario["object_registry"] == {
        "world_objects": [],
        "record_objects": [],
        "evidence_objects": [],
        "message_objects": [],
        "access_tokens": [],
        "object_links": [],
        "custody_log": [],
        "state_history": [],
    }


def test_loader_rejects_registry_location_outside_local_world(tmp_path):
    scenario = load_scenario(SCENARIO)
    registry = dict(scenario["object_registry"])
    registry["world_objects"] = list(registry["world_objects"]) + [
        {
            "object_id": "ghost_file",
            "label": "不存在的文件",
            "location_id": "ghost_clinic",
        }
    ]
    scenario["object_registry"] = registry
    tmp = tmp_path / "bad_registry.yaml"
    tmp.write_text(_dump_scenario_like_yaml(scenario), encoding="utf-8")
    with pytest.raises(ValueError, match="ghost_clinic"):
        load_scenario(tmp)


def test_local_world_institution_records_resolve_to_registry():
    scenario = load_scenario(SCENARIO)
    records = {item["record_id"] for item in scenario["object_registry"]["record_objects"]}

    for institution in scenario["local_world"]["institutions"]:
        assert set(institution.get("records", [])) <= records


def test_run_writes_object_registry_and_viewer_excerpt(tmp_path):
    scenario = load_scenario(SCENARIO)
    output_dir = tmp_path / "run"
    sim = Simulator.from_scenario(scenario, SCENARIO, seed=42)
    sim.run(steps=4, output_dir=output_dir)

    registry_file = output_dir / "object_registry.json"
    assert registry_file.exists()
    registry = json.loads(registry_file.read_text(encoding="utf-8"))
    assert registry["evidence_objects"]

    payload = build_viewer_payload(output_dir)
    view = payload["object_registry_view"]
    assert view["counts"]["evidence_objects"] >= 4
    assert view["rules"]["evidence_access_is_not_evidence_truth"] is True
    assert view["world_objects"] or view["record_objects"] or view["evidence_objects"]


def test_llm_render_payload_includes_object_registry_view(tmp_path):
    scenario = load_scenario(SCENARIO)
    output_dir = tmp_path / "run"
    sim = Simulator.from_scenario(scenario, SCENARIO, seed=42)
    sim.run(steps=4, output_dir=output_dir)

    payload = build_render_payload(output_dir)

    assert payload["object_registry_view"]["counts"]["record_objects"] >= 1
    assert payload["object_registry_view"]["rules"]["durable_objects_require_registry_refs"] is True


def test_segment_payload_inherits_object_registry_view(tmp_path):
    scenario = load_scenario(SCENARIO)
    output_dir = tmp_path / "run"
    sim = Simulator.from_scenario(scenario, SCENARIO, seed=42)
    sim.run(steps=4, output_dir=output_dir)

    segment = next_render_segment(output_dir, policy={"max_wait_ticks": 1}, force=True)

    assert segment
    assert segment["object_registry_view"]["counts"]["evidence_objects"] >= 4


def _dump_scenario_like_yaml(data: dict) -> str:
    import yaml

    return yaml.safe_dump(data, allow_unicode=True, sort_keys=False)
