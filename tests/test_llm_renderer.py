from pathlib import Path

import pytest

from rpf.engine.simulator import Simulator
from rpf.llm import renderer
from rpf.llm.renderer import build_render_payload, render_output
from rpf.scenarios.loader import load_scenario


def test_deterministic_renderer_writes_story_markdown(tmp_path):
    scenario_path = Path("examples/shared_apartment_unresolved_sacrifice.yaml")
    sim = Simulator.from_scenario(load_scenario(scenario_path), scenario_path, seed=42)
    output_dir = tmp_path / "run"
    sim.run(steps=12, output_dir=output_dir)

    result = render_output(output_dir)
    rendered = Path(result["output"])

    assert result["mode"] == "deterministic"
    assert rendered.exists()
    text = rendered.read_text(encoding="utf-8")
    assert "# 共享公寓：未解决的牺牲" in text
    assert "## 时间线" in text
    assert "参与者：" in text
    assert "底层依据：" in text
    assert "可存续性压力" in text
    assert "机会成本" in text


def test_render_payload_contains_render_canon(tmp_path):
    scenario_path = Path("examples/shared_apartment_unresolved_sacrifice.yaml")
    sim = Simulator.from_scenario(load_scenario(scenario_path), scenario_path, seed=42)
    output_dir = tmp_path / "run"
    sim.run(steps=3, output_dir=output_dir)

    payload = build_render_payload(output_dir)

    assert payload["render_canon"]["cast"]["p1"]["name"] == "许知遥"
    assert payload["render_canon"]["cast"]["p2"]["name"] == "沈砚"
    assert payload["story"][0]["viability"]
    assert payload["opportunity_trace"]
    assert any(frame["opportunity_cost"] for frame in payload["story"])
    assert "affordance_width" in payload["story"][0]["viability"]


def test_yellow_sign_render_payload_inherits_case_ledger(tmp_path):
    scenario_path = Path("examples/yellow_sign_cold_case.yaml")
    sim = Simulator.from_scenario(load_scenario(scenario_path), scenario_path, seed=42)
    output_dir = tmp_path / "run"
    sim.run(steps=4, output_dir=output_dir)

    payload = build_render_payload(output_dir)
    text = renderer.deterministic_markdown(payload)

    assert payload["case_ledger"]["case_title"] == "黄印镇冷案"
    assert payload["inquiry_trace"]
    assert payload["environment_trace"]
    assert payload["attention_trace"]
    assert payload["opportunity_trace"]
    assert payload["memory_trace"]
    assert any("case_memory_contamination" in item["reconstruction_biases"] for item in payload["memory_trace"])
    assert any(item["label"] == "黄漆符号" for item in payload["case_ledger"]["evidence_items"])
    assert "## 案件账本" in text
    assert "黄漆符号" in text
    assert "调查更新" in text
    assert "制度压力" in text
    assert "证人策略" in text
    assert "日常生态" in text
    assert "注意力漂移" in text
    assert "机会成本" in text
    assert "地点耦合" in text
    assert "证据可达性" in text
    assert "案件记忆" in text


def test_llm_renderer_requires_model_and_key(tmp_path, monkeypatch):
    scenario_path = Path("examples/shared_apartment_unresolved_sacrifice.yaml")
    sim = Simulator.from_scenario(load_scenario(scenario_path), scenario_path, seed=42)
    output_dir = tmp_path / "run"
    sim.run(steps=3, output_dir=output_dir)
    monkeypatch.delenv("RPF_LLM_API_KEY", raising=False)
    monkeypatch.delenv("RPF_LLM_MODEL", raising=False)

    with pytest.raises(RuntimeError, match="Missing API key"):
        render_output(output_dir, use_llm=True)


def test_deepseek_provider_defaults_to_v4_flash(tmp_path, monkeypatch):
    scenario_path = Path("examples/shared_apartment_unresolved_sacrifice.yaml")
    sim = Simulator.from_scenario(load_scenario(scenario_path), scenario_path, seed=42)
    output_dir = tmp_path / "run"
    sim.run(steps=3, output_dir=output_dir)
    captured = {}

    def fake_llm_markdown(render_payload, **kwargs):
        captured.update(kwargs)
        return "# rendered\n"

    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")
    monkeypatch.delenv("RPF_LLM_API_KEY", raising=False)
    monkeypatch.delenv("RPF_LLM_MODEL", raising=False)
    monkeypatch.setattr(renderer, "llm_markdown", fake_llm_markdown)

    result = render_output(output_dir, use_llm=True, provider="deepseek")

    assert result["mode"] == "llm"
    assert captured["api_key"] == "test-key"
    assert captured["base_url"] == "https://api.deepseek.com"
    assert captured["model"] == "deepseek-v4-flash"


def test_deepseek_request_adds_thinking_control(monkeypatch):
    captured = {}

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            return b'{"choices":[{"message":{"content":"ok"}}]}'

    def fake_urlopen(request, timeout):
        captured["body"] = request.data.decode("utf-8")
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr(renderer.urllib.request, "urlopen", fake_urlopen)

    text = renderer.llm_markdown(
        {"story": []},
        api_key="test-key",
        base_url="https://api.deepseek.com",
        model="deepseek-v4-pro",
        provider="deepseek",
        thinking="enabled",
        reasoning_effort="high",
    )
    body = captured["body"]

    assert text == "ok\n"
    assert '"thinking": {"type": "enabled"}' in body
    assert '"reasoning_effort": "high"' in body
    assert "viability" in body
    assert "case_ledger" in body
    assert "inquiry_trace" in body
    assert "environment_trace" in body
    assert "attention_trace" in body
    assert "opportunity_trace" in body
    assert "memory_trace" in body
    assert "changed evidence accessibility state" in body
    assert "changed location-evidence coupling state" in body
    assert "changed institutional pressure state" in body
    assert "changed witness strategy state" in body
    assert "changed daily ecology state" in body
    assert "changed attention drift state" in body
    assert "changed opportunity cost state" in body
    assert "causes not present in viability/action/expression/recognition evidence" in body
