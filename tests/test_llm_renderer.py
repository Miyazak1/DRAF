import json
from pathlib import Path

import pytest

from rpf.engine.simulator import Simulator
from rpf.llm import renderer, segments
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
    assert "信息边界" in text
    assert "机会成本" in text
    assert "行动可逆性" in text
    assert "共同现实" in text


def test_render_payload_contains_render_canon(tmp_path):
    scenario_path = Path("examples/shared_apartment_unresolved_sacrifice.yaml")
    sim = Simulator.from_scenario(load_scenario(scenario_path), scenario_path, seed=42)
    output_dir = tmp_path / "run"
    sim.run(steps=3, output_dir=output_dir)

    payload = build_render_payload(output_dir)

    assert payload["render_canon"]["cast"]["p1"]["name"] == "许知遥"
    assert payload["render_canon"]["cast"]["p2"]["name"] == "沈砚"
    assert payload["epistemic_trace"]
    assert payload["story"][0]["viability"]
    assert any(frame["epistemic_boundary"] for frame in payload["story"])
    assert payload["opportunity_trace"]
    assert payload["reversibility_trace"]
    assert payload["common_ground_trace"]
    assert payload["local_world_view"]
    assert payload["local_world_view"]["active_location"]["location_id"]
    assert payload["local_world_view"]["route"]["route_id"]
    assert any(frame["opportunity_cost"] for frame in payload["story"])
    assert any(frame["reversibility"] for frame in payload["story"])
    assert any(frame["common_ground"] for frame in payload["story"])
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
    assert payload["epistemic_trace"]
    assert payload["environment_trace"]
    assert payload["attention_trace"]
    assert payload["opportunity_trace"]
    assert payload["reversibility_trace"]
    assert payload["common_ground_trace"]
    assert payload["memory_trace"]
    assert any("case_memory_contamination" in item["reconstruction_biases"] for item in payload["memory_trace"])
    assert any(item["label"] == "黄漆符号" for item in payload["case_ledger"]["evidence_items"])
    assert "## 案件账本" in text
    assert "黄漆符号" in text
    assert "调查更新" in text
    assert "制度压力" in text
    assert "证人策略" in text
    assert "信息边界" in text
    assert "日常生态" in text
    assert "注意力漂移" in text
    assert "机会成本" in text
    assert "行动可逆性" in text
    assert "共同现实" in text
    assert "本地世界" in text
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
    assert "epistemic_trace" in body
    assert "environment_trace" in body
    assert "attention_trace" in body
    assert "opportunity_trace" in body
    assert "reversibility_trace" in body
    assert "common_ground_trace" in body
    assert "memory_trace" in body
    assert "local_world_view" in body
    assert "local_world_view is authoritative causal geography" in body
    assert "movement without route evidence" in body
    assert "changed route access, audience exposure, memory site, resource, or local constraint state" in body
    assert "changed evidence accessibility state" in body
    assert "changed location-evidence coupling state" in body
    assert "changed institutional pressure state" in body
    assert "changed witness strategy state" in body
    assert "changed epistemic boundary state" in body
    assert "changed daily ecology state" in body
    assert "changed attention drift state" in body
    assert "changed opportunity cost state" in body
    assert "changed action reversibility state" in body
    assert "changed common ground state" in body
    assert "causes not present in viability/action/expression/recognition evidence" in body


def test_segment_renderer_sanitizes_full_story_llm_response(tmp_path, monkeypatch):
    def fake_llm_markdown(render_payload, **kwargs):
        return """# 共享公寓：未解决的牺牲

## 概述

这是一段不该进入分段记录的总览。

## 场景

### tick 1-3

旧段落内容，不应该被追加进新的 segment。

---

### tick 4-5

新的段落内容，应该被保留。

*来源：tick 4-5*

---

## 结束状态

这也是完整文档尾部，不应该进入 segment。

## 边界说明

渲染未改变因果状态。
"""

    monkeypatch.setattr(segments, "llm_markdown", fake_llm_markdown)
    segment = {
        "segment_id": "seg-0002",
        "segment_index": 2,
        "tick_start": 4,
        "tick_end": 5,
        "boundary_reason": "弱闭合：潜伏时间累积达到阈值",
        "source_ticks": [4, 5],
        "simulated_seconds": 120,
        "frames": [],
        "render_canon": {"title": "共享公寓：未解决的牺牲"},
    }

    result = segments.render_and_append_segment(
        tmp_path,
        segment,
        use_llm=True,
        api_key="test-key",
    )
    records = segments.load_render_segments(tmp_path)
    text = records[0]["text"]

    assert result["text"] == result["segment_text"]
    assert "stream_text" in result
    assert result["mode"] == "deterministic_fallback"
    assert result["validation"]["fallback_used"] is True
    assert "document_title" in result["validation"]["violations"]
    assert "forbidden_full_document_section" in result["validation"]["violations"]
    assert "source_tick_mismatch" in result["validation"]["violations"]
    assert "新的段落内容" not in text
    assert "旧段落内容" not in text
    assert "## 概述" not in text
    assert "## 结束状态" not in text
    assert "## 边界说明" not in text
    assert not text.startswith("# 共享公寓")
    trace = (tmp_path / "render_repetition_trace.json").read_text(encoding="utf-8")
    assert "protocol_repetition" in trace
    assert "reject_invalid_segment_output" in trace


def test_segment_renderer_accepts_valid_segment_json(tmp_path, monkeypatch):
    def fake_llm_markdown(render_payload, **kwargs):
        return '{"segment_text_only":"## 第 2 段：门口的停顿\\n\\n新的段落内容。\\n\\n*来源 tick: 4-5*"}'

    monkeypatch.setattr(segments, "llm_markdown", fake_llm_markdown)
    segment = {
        "segment_id": "seg-0002",
        "segment_index": 2,
        "tick_start": 4,
        "tick_end": 5,
        "boundary_reason": "弱闭合：潜伏时间累积达到阈值",
        "source_ticks": [4, 5],
        "simulated_seconds": 120,
        "frames": [],
        "render_canon": {"title": "共享公寓：未解决的牺牲"},
    }

    result = segments.render_and_append_segment(
        tmp_path,
        segment,
        use_llm=True,
        api_key="test-key",
    )
    records = segments.load_render_segments(tmp_path)

    assert result["mode"] == "llm"
    assert result["validation"]["valid"] is True
    assert "新的段落内容" in records[0]["text"]
    assert records[0]["validation"]["violations"] == []


def test_segment_guard_rejects_previous_story_repetition(tmp_path, monkeypatch):
    previous_text = "## 第 1 段：旧段落\n\n" + "这是一段已经写过的内容。" * 12 + "\n\n*来源 tick: 1-3*"
    (tmp_path / "rendered_segments.json").write_text(
        json.dumps(
            [
                {
                    "segment_id": "seg-0001",
                    "segment_index": 1,
                    "tick_start": 1,
                    "tick_end": 3,
                    "source_ticks": [1, 2, 3],
                    "boundary_reason": "test",
                    "mode": "llm",
                    "text": previous_text,
                }
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    def fake_llm_markdown(render_payload, **kwargs):
        return previous_text + "\n\n*来源 tick: 4-5*"

    monkeypatch.setattr(segments, "llm_markdown", fake_llm_markdown)
    segment = {
        "segment_id": "seg-0002",
        "segment_index": 2,
        "tick_start": 4,
        "tick_end": 5,
        "boundary_reason": "弱闭合",
        "source_ticks": [4, 5],
        "simulated_seconds": 120,
        "frames": [],
        "render_canon": {"title": "共享公寓：未解决的牺牲"},
    }

    result = segments.render_and_append_segment(tmp_path, segment, use_llm=True, api_key="test-key")
    records = segments.load_render_segments(tmp_path)

    assert result["mode"] == "deterministic_fallback"
    assert "previous_segment_repeated" in result["validation"]["violations"]
    assert records[-1]["mode"] == "deterministic_fallback"
    assert "这是一段已经写过的内容。" not in records[-1]["text"]


def test_segment_payload_inherits_local_world_view(tmp_path):
    scenario_path = Path("examples/yellow_sign_cold_case.yaml")
    sim = Simulator.from_scenario(load_scenario(scenario_path), scenario_path, seed=42)
    output_dir = tmp_path / "run"
    sim.run(steps=5, output_dir=output_dir)

    segment = segments.next_render_segment(output_dir, force=True)
    payload = segments._segment_llm_payload(segment, output_dir)

    assert segment["local_world_view"]["active_location"]["location_id"]
    assert payload["local_world_view"]["route"]["route_id"]
    assert payload["rules"]["local_world_view_is_authoritative"] is True
