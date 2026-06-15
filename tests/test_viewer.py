import http.client
import json
import threading
import time
import zipfile
from pathlib import Path

from rpf.engine.simulator import Simulator
from rpf.scenarios.loader import load_scenario
from rpf.viewer.server import ViewerServer, build_run_report, build_viewer_payload, export_run_bundle, run_catalog, scenario_catalog
from rpf.viewer.server import _ensure_initial_output


def test_viewer_payload_contains_core_traces(tmp_path):
    scenario_path = Path("examples/shared_apartment_unresolved_sacrifice.yaml")
    sim = Simulator.from_scenario(load_scenario(scenario_path), scenario_path, seed=42)
    output_dir = tmp_path / "run"
    sim.run(steps=12, output_dir=output_dir)

    payload = build_viewer_payload(output_dir)

    assert payload["render_canon"]["title"] == "共享公寓：未解决的牺牲"
    assert payload["summary"]["event_count"] > 0
    assert payload["summary"]["phase"]
    assert payload["timeline"]
    assert payload["action"]
    assert payload["expression"]
    assert payload["viability"]
    assert payload["memory"]
    assert payload["environment"]
    assert payload["recognition"]
    assert payload["summary"]["top_rpps"]
    assert payload["story"]
    assert payload["story"][0]["summary"]
    assert "tick" in payload["story"][0]
    assert "participants" in payload["story"][0]
    assert "rendered_segments" in payload
    assert "rendered_story_stream" in payload
    assert payload["viability"][0]["requirements"]
    assert payload["viability"][0]["affordance_widths"]
    assert "future_constraints" in payload["viability"][0]


def test_viewer_static_contains_viability_dynamics_panel():
    html = Path("rpf/viewer/static/index.html").read_text(encoding="utf-8")
    js = Path("rpf/viewer/static/viewer.js").read_text(encoding="utf-8")

    assert "底层动力学" in html
    assert "viabilityChart" in html
    assert "renderViabilityDynamics" in js
    assert "buildViabilityPoints" in js


def test_scenario_catalog_exposes_example_scenarios():
    catalog = scenario_catalog(Path("examples"))

    assert any(item["id"] == "shared_apartment_unresolved_sacrifice" for item in catalog)
    assert any(item["id"] == "yellow_sign_cold_case" for item in catalog)
    shared = next(item for item in catalog if item["id"] == "shared_apartment_unresolved_sacrifice")
    yellow = next(item for item in catalog if item["id"] == "yellow_sign_cold_case")
    assert shared["title"] == "共享公寓：未解决的牺牲"
    assert yellow["title"] == "黄印镇冷案"
    assert Path(shared["path"]).exists()
    assert Path(yellow["path"]).exists()


def test_default_initial_viewer_output_prefers_yellow_sign(tmp_path, monkeypatch):
    import rpf.viewer.server as viewer_server

    monkeypatch.setattr(viewer_server, "DEFAULT_EXPERIENCE_DIR", tmp_path / "experience")

    output_dir = _ensure_initial_output(tmp_path / "experience" / "yellow_sign_cold_case")
    payload = build_viewer_payload(output_dir)

    assert output_dir.name == "yellow_sign_cold_case"
    assert payload["render_canon"]["title"] == "黄印镇冷案"


def test_run_catalog_reads_run_metadata(tmp_path):
    scenario_path = Path("examples/shared_apartment_unresolved_sacrifice.yaml")
    sim = Simulator.from_scenario(load_scenario(scenario_path), scenario_path, seed=42)
    output_dir = tmp_path / "experience" / "runs" / "shared_apartment_unresolved_sacrifice" / "run-1"
    sim.run(steps=3, output_dir=output_dir)
    (output_dir / "run_metadata.json").write_text(
        json.dumps(
            {
                "run_id": "run-1",
                "scenario_id": "shared_apartment_unresolved_sacrifice",
                "mode": "preview",
                "seed": 42,
                "title": "测试运行",
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    runs = run_catalog(tmp_path / "experience")

    assert runs[0]["run_id"] == "run-1"
    assert runs[0]["title"] == "测试运行"
    assert runs[0]["scenario_id"] == "shared_apartment_unresolved_sacrifice"


def test_viewer_render_endpoint_returns_markdown(tmp_path):
    scenario_path = Path("examples/shared_apartment_unresolved_sacrifice.yaml")
    sim = Simulator.from_scenario(load_scenario(scenario_path), scenario_path, seed=42)
    output_dir = tmp_path / "run"
    sim.run(steps=5, output_dir=output_dir)
    server = ViewerServer(("127.0.0.1", 0), output_dir)
    thread = threading.Thread(target=server.serve_forever)
    thread.start()
    try:
        conn = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=5)
        body = json.dumps({"use_llm": False, "max_frames": 3}).encode("utf-8")
        conn.request(
            "POST",
            "/api/render",
            body=body,
            headers={"Content-Type": "application/json", "Content-Length": str(len(body))},
        )
        response = conn.getresponse()
        payload = json.loads(response.read().decode("utf-8"))
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

    assert response.status == 200
    assert payload["mode"] == "deterministic"
    assert "# 共享公寓：未解决的牺牲" in payload["text"]


def test_viewer_health_endpoint_reports_active_run(tmp_path):
    scenario_path = Path("examples/yellow_sign_cold_case.yaml")
    sim = Simulator.from_scenario(load_scenario(scenario_path), scenario_path, seed=42)
    output_dir = tmp_path / "run"
    sim.run(steps=3, output_dir=output_dir)
    server = ViewerServer(("127.0.0.1", 0), output_dir)
    thread = threading.Thread(target=server.serve_forever)
    thread.start()
    try:
        conn = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=5)
        conn.request("GET", "/healthz")
        response = conn.getresponse()
        payload = json.loads(response.read().decode("utf-8"))
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

    assert response.status == 200
    assert payload["ok"] is True
    assert payload["service"] == "draf-viewer"
    assert payload["scenario_id"] == "yellow_sign_cold_case"
    assert payload["title"] == "黄印镇冷案"
    assert payload["timeline_exists"] is True
    assert payload["event_count"] > 0


def test_run_report_contains_deterministic_sections(tmp_path):
    scenario_path = Path("examples/shared_apartment_unresolved_sacrifice.yaml")
    sim = Simulator.from_scenario(load_scenario(scenario_path), scenario_path, seed=42)
    output_dir = tmp_path / "run"
    sim.run(steps=6, output_dir=output_dir)

    report = build_run_report(output_dir)

    assert "# 共享公寓：未解决的牺牲" in report
    assert "## 运行档案" in report
    assert "## 总览" in report
    assert "## 关键转折" in report
    assert "不调用 LLM" in report


def test_viewer_report_endpoint_writes_markdown(tmp_path):
    scenario_path = Path("examples/shared_apartment_unresolved_sacrifice.yaml")
    sim = Simulator.from_scenario(load_scenario(scenario_path), scenario_path, seed=42)
    output_dir = tmp_path / "run"
    sim.run(steps=5, output_dir=output_dir)
    server = ViewerServer(("127.0.0.1", 0), output_dir)
    thread = threading.Thread(target=server.serve_forever)
    thread.start()
    try:
        conn = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=5)
        body = b"{}"
        conn.request(
            "POST",
            "/api/report",
            body=body,
            headers={"Content-Type": "application/json", "Content-Length": str(len(body))},
        )
        response = conn.getresponse()
        payload = json.loads(response.read().decode("utf-8"))
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

    report_path = Path(payload["output"])

    assert response.status == 200
    assert payload["ok"] is True
    assert report_path.exists()
    assert "## 输出文件" in payload["text"]


def test_export_run_bundle_writes_zip(tmp_path):
    scenario_path = Path("examples/shared_apartment_unresolved_sacrifice.yaml")
    sim = Simulator.from_scenario(load_scenario(scenario_path), scenario_path, seed=42)
    output_dir = tmp_path / "run"
    sim.run(steps=5, output_dir=output_dir)

    result = export_run_bundle(output_dir)
    bundle = Path(result["output"])

    assert result["ok"] is True
    assert bundle.exists()
    with zipfile.ZipFile(bundle) as archive:
        names = set(archive.namelist())

    assert "run_report.md" in names
    assert "timeline.jsonl" in names
    assert "derived_views.json" in names


def test_viewer_export_endpoint_writes_bundle(tmp_path):
    scenario_path = Path("examples/shared_apartment_unresolved_sacrifice.yaml")
    sim = Simulator.from_scenario(load_scenario(scenario_path), scenario_path, seed=42)
    output_dir = tmp_path / "run"
    sim.run(steps=5, output_dir=output_dir)
    server = ViewerServer(("127.0.0.1", 0), output_dir)
    thread = threading.Thread(target=server.serve_forever)
    thread.start()
    try:
        conn = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=5)
        body = b"{}"
        conn.request(
            "POST",
            "/api/export",
            body=body,
            headers={"Content-Type": "application/json", "Content-Length": str(len(body))},
        )
        response = conn.getresponse()
        payload = json.loads(response.read().decode("utf-8"))
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

    assert response.status == 200
    assert payload["ok"] is True
    assert Path(payload["output"]).exists()
    assert "run_report.md" in payload["files"]


def test_viewer_can_save_render_canon_from_web(tmp_path):
    scenario_path = Path("examples/shared_apartment_unresolved_sacrifice.yaml")
    sim = Simulator.from_scenario(load_scenario(scenario_path), scenario_path, seed=42)
    output_dir = tmp_path / "run"
    sim.run(steps=4, output_dir=output_dir)
    server = ViewerServer(("127.0.0.1", 0), output_dir)
    thread = threading.Thread(target=server.serve_forever)
    thread.start()
    try:
        canon = build_viewer_payload(output_dir)["render_canon"]
        canon["title"] = "自定义标题"
        canon["cast"]["p1"]["name"] = "林望"
        body = json.dumps({"render_canon": canon}, ensure_ascii=False).encode("utf-8")
        conn = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=5)
        conn.request(
            "POST",
            "/api/canon",
            body=body,
            headers={"Content-Type": "application/json", "Content-Length": str(len(body))},
        )
        response = conn.getresponse()
        save_payload = json.loads(response.read().decode("utf-8"))
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

    updated = build_viewer_payload(output_dir)

    assert response.status == 200
    assert save_payload["ok"] is True
    assert updated["render_canon"]["title"] == "自定义标题"
    assert updated["render_canon"]["cast"]["p1"]["name"] == "林望"
    names = [
        participant["name"]
        for frame in updated["story"]
        for participant in frame["participants"].values()
    ]
    assert any("林望" in name for name in names)


def test_viewer_can_select_scenario_from_web(tmp_path):
    scenario_path = Path("examples/shared_apartment_unresolved_sacrifice.yaml")
    sim = Simulator.from_scenario(load_scenario(scenario_path), scenario_path, seed=42)
    output_dir = tmp_path / "run"
    sim.run(steps=2, output_dir=output_dir)
    server = ViewerServer(("127.0.0.1", 0), output_dir)
    server.experience_dir = tmp_path / "experience"
    thread = threading.Thread(target=server.serve_forever)
    thread.start()
    try:
        conn = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=5)
        conn.request("GET", "/api/scenarios")
        catalog_response = conn.getresponse()
        catalog_payload = json.loads(catalog_response.read().decode("utf-8"))
        assert catalog_response.status == 200
        assert catalog_payload["scenarios"]

        body = json.dumps(
            {
                "scenario_id": "caretaker_dependency_loop",
                "bootstrap_steps": 3,
                "seed": 7,
            }
        ).encode("utf-8")
        conn = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=5)
        conn.request(
            "POST",
            "/api/scenarios/select",
            body=body,
            headers={"Content-Type": "application/json", "Content-Length": str(len(body))},
        )
        select_response = conn.getresponse()
        select_payload = json.loads(select_response.read().decode("utf-8"))

        conn = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=5)
        conn.request("GET", "/api/runs")
        runs_response = conn.getresponse()
        runs_payload = json.loads(runs_response.read().decode("utf-8"))

        open_body = json.dumps({"output_dir": select_payload["output_dir"]}).encode("utf-8")
        conn = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=5)
        conn.request(
            "POST",
            "/api/runs/open",
            body=open_body,
            headers={"Content-Type": "application/json", "Content-Length": str(len(open_body))},
        )
        open_response = conn.getresponse()
        open_payload = json.loads(open_response.read().decode("utf-8"))

        compare_body = json.dumps({"output_dir": select_payload["output_dir"]}).encode("utf-8")
        conn = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=5)
        conn.request(
            "POST",
            "/api/runs/compare",
            body=compare_body,
            headers={"Content-Type": "application/json", "Content-Length": str(len(compare_body))},
        )
        compare_response = conn.getresponse()
        compare_payload = json.loads(compare_response.read().decode("utf-8"))
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

    assert select_response.status == 200
    assert select_payload["ok"] is True
    assert select_payload["payload"]["render_canon"]["title"]
    assert "caretaker_dependency_loop" in select_payload["output_dir"]
    assert "runs" in select_payload["output_dir"]
    assert runs_response.status == 200
    assert any(run["output_dir"] == select_payload["output_dir"] for run in runs_payload["runs"])
    assert open_response.status == 200
    assert open_payload["payload"]["run_dir"] == select_payload["output_dir"]
    assert compare_response.status == 200
    assert compare_payload["current"]["output_dir"] == select_payload["output_dir"]
    assert compare_payload["other"]["output_dir"] == select_payload["output_dir"]
    assert compare_payload["delta"]["event_count"] == 0


def test_viewer_can_create_custom_scenario_from_web(tmp_path):
    scenario_path = Path("examples/shared_apartment_unresolved_sacrifice.yaml")
    sim = Simulator.from_scenario(load_scenario(scenario_path), scenario_path, seed=42)
    output_dir = tmp_path / "run"
    sim.run(steps=2, output_dir=output_dir)
    examples_dir = tmp_path / "examples"
    examples_dir.mkdir()
    server = ViewerServer(("127.0.0.1", 0), output_dir)
    server.examples_dir = examples_dir.resolve()
    server.experience_dir = tmp_path / "experience"
    thread = threading.Thread(target=server.serve_forever)
    thread.start()
    try:
        body = json.dumps(
            {
                "title": "网页自定义案例",
                "place": "测试厨房",
                "p1_name": "林望",
                "p2_name": "陈序",
                "binding_label": "共同租约",
                "recognition_label": "未被承认的帮助",
                "bootstrap_steps": 4,
                "seed": 9,
            },
            ensure_ascii=False,
        ).encode("utf-8")
        conn = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=5)
        conn.request(
            "POST",
            "/api/scenarios/create",
            body=body,
            headers={"Content-Type": "application/json", "Content-Length": str(len(body))},
        )
        response = conn.getresponse()
        payload = json.loads(response.read().decode("utf-8"))
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

    scenario_file = Path(payload["scenario_path"])
    run_dir = Path(payload["output_dir"])

    assert response.status == 200
    assert payload["ok"] is True
    assert scenario_file.exists()
    assert scenario_file.parent == examples_dir.resolve()
    assert payload["scenario"]["render_canon"]["cast"]["p1"]["name"] == "林望"
    assert payload["payload"]["render_canon"]["title"] == "网页自定义案例"
    assert (run_dir / "timeline_manifest.json").exists()
    assert (run_dir / "run_metadata.json").exists()
    assert any(item["title"] == "网页自定义案例" for item in payload["scenarios"])


def test_viewer_can_run_duration_session(tmp_path):
    scenario_path = Path("examples/shared_apartment_unresolved_sacrifice.yaml")
    sim = Simulator.from_scenario(load_scenario(scenario_path), scenario_path, seed=42)
    output_dir = tmp_path / "run"
    sim.run(steps=3, output_dir=output_dir)
    server = ViewerServer(("127.0.0.1", 0), output_dir)
    thread = threading.Thread(target=server.serve_forever)
    thread.start()
    try:
        conn = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=5)
        body = json.dumps(
            {
                "duration_value": 0.02,
                "duration_unit": "minutes",
                "tick_interval_seconds": 0.01,
                "render_mode": "deterministic",
                "render_every_ticks": 1,
                "max_steps": 500,
            }
        ).encode("utf-8")
        conn.request(
            "POST",
            "/api/simulate/start",
            body=body,
            headers={"Content-Type": "application/json", "Content-Length": str(len(body))},
        )
        response = conn.getresponse()
        start_payload = json.loads(response.read().decode("utf-8"))
        assert response.status == 200
        assert start_payload["state"] == "running"

        status_payload = {}
        for _ in range(40):
            conn = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=5)
            conn.request("GET", "/api/simulate/status")
            status_response = conn.getresponse()
            status_payload = json.loads(status_response.read().decode("utf-8"))
            if status_payload.get("state") in {"completed", "stopped", "error"}:
                break
            time.sleep(0.05)
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

    assert status_payload["state"] == "completed"
    assert status_payload["tick"] >= 1
    assert status_payload["elapsed_seconds"] == 1
    assert status_payload["target_seconds"] == 1
    assert status_payload["last_render_output"]
    assert status_payload["last_render_segment"]
    run_output_dir = Path(status_payload["output_dir"])
    assert run_output_dir != output_dir
    assert (run_output_dir / "rendered_story_stream.md").exists()
    assert (run_output_dir / "rendered_segments.json").exists()
    assert (run_output_dir / "run_metadata.json").exists()
