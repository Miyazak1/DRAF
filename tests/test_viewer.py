import http.client
import json
import threading
import time
from pathlib import Path

from rpf.engine.simulator import Simulator
from rpf.scenarios.loader import load_scenario
from rpf.viewer.server import ViewerServer, build_viewer_payload


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
    assert payload["memory"]
    assert payload["recognition"]
    assert payload["summary"]["top_rpps"]
    assert payload["story"]
    assert payload["story"][0]["summary"]
    assert "tick" in payload["story"][0]
    assert "participants" in payload["story"][0]


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
    assert (output_dir / "rendered_story_stream.md").exists()
    assert (output_dir / "rendered_segments.json").exists()
