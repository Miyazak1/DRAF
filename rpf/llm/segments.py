from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from rpf.llm.renderer import llm_markdown
from rpf.viewer.server import build_viewer_payload


DEFAULT_SEGMENT_POLICY = {
    "micro_count": 3,
    "latent_seconds": 6 * 60 * 60,
    "min_ticks": 3,
    "max_ticks": 8,
    "max_seconds": 24 * 60 * 60,
}


def load_render_segments(output_dir: Path) -> list[dict[str, Any]]:
    path = output_dir / "rendered_segments.json"
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    return data if isinstance(data, list) else []


def next_render_segment(
    output_dir: Path,
    *,
    policy: dict[str, Any] | None = None,
    force: bool = False,
) -> dict[str, Any] | None:
    policy = {**DEFAULT_SEGMENT_POLICY, **(policy or {})}
    payload = build_viewer_payload(output_dir)
    rendered = load_render_segments(output_dir)
    last_tick = max((int(item.get("tick_end", 0)) for item in rendered), default=0)
    frames = [frame for frame in payload.get("story", []) if int(frame.get("tick", 0)) > last_tick]
    if not frames:
        return None
    selected_frames = frames
    reason = None
    for index in range(len(frames)):
        prefix = frames[: index + 1]
        reason = _boundary_reason(prefix, policy, force=False)
        if reason:
            selected_frames = prefix
            break
    if not reason and force:
        reason = _boundary_reason(frames, policy, force=True)
        selected_frames = frames
    if not reason:
        return None
    frames = selected_frames
    segment_index = len(rendered) + 1
    return {
        "segment_id": f"seg-{segment_index:04d}",
        "segment_index": segment_index,
        "tick_start": frames[0].get("tick"),
        "tick_end": frames[-1].get("tick"),
        "boundary_reason": reason,
        "source_ticks": [frame.get("tick") for frame in frames],
        "simulated_seconds": _elapsed_seconds(frames),
        "frames": frames,
        "render_canon": payload.get("render_canon", {}),
        "case_ledger": payload.get("case_ledger", {}),
        "inquiry_trace": payload.get("inquiry", []),
        "epistemic_trace": payload.get("epistemic", []),
        "environment_trace": payload.get("environment", []),
        "attention_trace": payload.get("attention", []),
        "opportunity_trace": payload.get("opportunity", []),
        "reversibility_trace": payload.get("reversibility", []),
        "common_ground_trace": payload.get("common_ground", []),
        "memory_trace": payload.get("memory", []),
        "summary": payload.get("summary", {}),
        "relationship_view": payload.get("derived_views", {}).get("relationship_view", {}),
        "person_views": payload.get("derived_views", {}).get("person_views", {}),
        "irreversibility": payload.get("irreversibility", {}),
    }


def render_and_append_segment(
    output_dir: Path,
    segment: dict[str, Any],
    *,
    use_llm: bool = False,
    api_key: str | None = None,
    base_url: str = "https://api.deepseek.com",
    model: str = "deepseek-v4-flash",
    provider: str | None = "deepseek",
    thinking: str | None = None,
    reasoning_effort: str | None = None,
) -> dict[str, Any]:
    if use_llm:
        if not api_key:
            raise RuntimeError("Missing API key for segment LLM rendering.")
        text = llm_markdown(
            _segment_llm_payload(segment, output_dir),
            api_key=api_key,
            base_url=base_url,
            model=model,
            provider=provider,
            thinking=thinking,
            reasoning_effort=reasoning_effort,
        )
        text = normalize_segment_text(text, segment)
        mode = "llm"
    else:
        text = deterministic_segment_markdown(segment)
        mode = "deterministic"
    record = {
        "segment_id": segment["segment_id"],
        "segment_index": segment["segment_index"],
        "tick_start": segment["tick_start"],
        "tick_end": segment["tick_end"],
        "boundary_reason": segment["boundary_reason"],
        "source_ticks": segment["source_ticks"],
        "simulated_seconds": segment["simulated_seconds"],
        "mode": mode,
        "text": text,
    }
    records = load_render_segments(output_dir)
    records.append(record)
    (output_dir / "rendered_segments.json").write_text(
        json.dumps(records, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    stream = render_segment_stream(records, segment.get("render_canon", {}))
    stream_path = output_dir / "rendered_story_stream.md"
    stream_path.write_text(stream, encoding="utf-8")
    return {
        "mode": mode,
        "output": str(stream_path),
        "segment_id": record["segment_id"],
        "tick_start": record["tick_start"],
        "tick_end": record["tick_end"],
        "boundary_reason": record["boundary_reason"],
        "text": text,
        "segment_text": text,
        "stream_text": stream,
        "segment_count": len(records),
    }


def normalize_segment_text(text: str, segment: dict[str, Any]) -> str:
    """Keep an LLM response scoped to the current render segment."""

    text = _extract_segment_text_from_json(text, segment) or text
    text = _strip_markdown_fence(text).strip()
    if not text:
        return text
    lines = text.splitlines()
    lines = _extract_scene_lines(lines)
    lines = _filter_lines_to_segment_ticks(lines, segment.get("source_ticks", []))
    lines = _drop_forbidden_segment_sections(lines)
    normalized = "\n".join(lines).strip()
    return normalized + "\n" if normalized else text.strip() + "\n"


def _extract_segment_text_from_json(text: str, segment: dict[str, Any]) -> str:
    raw = _strip_markdown_fence(text).strip()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return ""
    if isinstance(data, dict):
        for key in ("segment_text_only", "segment_text", "text"):
            value = data.get(key)
            if isinstance(value, str) and value.strip():
                return value
        scenes = data.get("scenes")
        if isinstance(scenes, list):
            source_ticks = {int(tick) for tick in segment.get("source_ticks", []) if str(tick).isdigit()}
            selected: list[str] = []
            for scene in scenes:
                if not isinstance(scene, dict):
                    continue
                ticks = {int(tick) for tick in scene.get("source_ticks", []) if str(tick).isdigit()}
                if source_ticks and ticks and source_ticks.isdisjoint(ticks):
                    continue
                scene_text = scene.get("text")
                if isinstance(scene_text, str) and scene_text.strip():
                    selected.append(scene_text.strip())
            if selected:
                return "\n\n".join(selected)
    return ""


def _strip_markdown_fence(text: str) -> str:
    stripped = text.strip()
    if not stripped.startswith("```"):
        return stripped
    lines = stripped.splitlines()
    if len(lines) >= 2 and lines[-1].strip() == "```":
        return "\n".join(lines[1:-1]).strip()
    return stripped


def _extract_scene_lines(lines: list[str]) -> list[str]:
    start = None
    for index, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("## ") and any(label in stripped for label in ("场景", "时间线", "Scenes")):
            start = index + 1
            break
    if start is None:
        return lines
    end = len(lines)
    for index in range(start, len(lines)):
        stripped = lines[index].strip()
        if stripped.startswith("## ") and any(label in stripped for label in ("结束状态", "边界说明", "Ending", "Boundary")):
            end = index
            break
    return lines[start:end]


def _filter_lines_to_segment_ticks(lines: list[str], source_ticks: list[Any]) -> list[str]:
    wanted = {int(tick) for tick in source_ticks if str(tick).isdigit()}
    if not wanted or not any(line.lstrip().startswith("###") for line in lines):
        return lines
    kept: list[str] = []
    include = True
    saw_segment_heading = False
    for line in lines:
        if line.lstrip().startswith("###"):
            ticks = _ticks_from_heading(line)
            include = not ticks or not wanted.isdisjoint(ticks)
            saw_segment_heading = True
        if include:
            kept.append(line)
    return kept if saw_segment_heading and kept else lines


def _ticks_from_heading(line: str) -> set[int]:
    numbers = [int(item) for item in re.findall(r"\d+", line)]
    if len(numbers) >= 2:
        start, end = numbers[0], numbers[1]
        if start <= end and end - start <= 200:
            return set(range(start, end + 1))
    return set(numbers[:1])


def _drop_forbidden_segment_sections(lines: list[str]) -> list[str]:
    forbidden = ("概述", "总览", "结束状态", "边界说明", "boundary_note", "ending_state", "overview")
    kept: list[str] = []
    skipping = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("# "):
            continue
        if stripped.startswith("## ") and any(label in stripped for label in forbidden):
            skipping = True
            continue
        if stripped.startswith(("## ", "### ")):
            skipping = False
        if skipping:
            continue
        if stripped == "---":
            continue
        kept.append(line)
    while kept and not kept[0].strip():
        kept.pop(0)
    while kept and not kept[-1].strip():
        kept.pop()
    return kept


def deterministic_segment_markdown(segment: dict[str, Any]) -> str:
    title = f"## 第 {segment['segment_index']} 段：第 {segment['tick_start']} 至 {segment['tick_end']} 步"
    lines = [
        title,
        "",
        f"- 闭合原因：{segment['boundary_reason']}",
        f"- 来源 tick：{', '.join(str(tick) for tick in segment['source_ticks'])}",
        "",
    ]
    for frame_group in _compressed_frame_groups(segment.get("frames", [])):
        frame = frame_group["frame"]
        participants = frame.get("participants", {})
        names = "、".join(
            item.get("name", "")
            for item in (participants.get("source", {}), participants.get("target", {}))
            if item.get("name")
        )
        tick_label = str(frame.get("tick"))
        if frame_group["count"] > 1:
            tick_label = f"{frame_group['tick_start']} 至 {frame_group['tick_end']}"
        if names:
            lines.append(f"第 {tick_label} 步，{names}：{frame.get('summary', '')}")
        else:
            lines.append(f"第 {tick_label} 步：{frame.get('summary', '')}")
        if frame_group["count"] > 1:
            lines.append(f"  - 重复模式：该结构连续出现 {frame_group['count']} 次，渲染时应压缩为关系模式持续，而不是重演同一场面。")
        viability = _viability_brief(frame)
        if viability:
            lines.append(f"  - 底层依据：{viability}")
        opportunity = _opportunity_brief(frame)
        if opportunity:
            lines.append(f"  - 机会成本：{opportunity}")
        reversibility = _reversibility_brief(frame)
        if reversibility:
            lines.append(f"  - 行动可逆性：{reversibility}")
        epistemic = _epistemic_brief(frame)
        if epistemic:
            lines.append(f"  - 信息边界：{epistemic}")
        common_ground = _common_ground_brief(frame)
        if common_ground:
            lines.append(f"  - 共同现实：{common_ground}")
    return "\n".join(lines).strip() + "\n"


def render_segment_stream(records: list[dict[str, Any]], canon: dict[str, Any]) -> str:
    title = canon.get("title") or "RPF 持续故事"
    lines = [f"# {title}", "", "## 持续渲染", ""]
    for record in records:
        lines.append(str(record.get("text", "")).strip())
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def _viability_brief(frame: dict[str, Any]) -> str:
    viability = frame.get("viability", {}) or {}
    if not viability:
        return ""
    parts = []
    for label, key in (
        ("可存续性压力", "viability_pressure"),
        ("可行动宽度", "affordance_width"),
        ("直接回应成本", "direct_response_cost"),
        ("派生张力", "dramatic_tension"),
    ):
        value = viability.get(key)
        if value is None:
            continue
        try:
            parts.append(f"{label} {float(value):.2f}")
        except (TypeError, ValueError):
            continue
    deformation = viability.get("deformation", {}) or {}
    if deformation.get("type"):
        parts.append(f"变形 {deformation.get('type')} {float(deformation.get('distance') or 0.0):.2f}")
    return "；".join(parts)


def _opportunity_brief(frame: dict[str, Any]) -> str:
    opportunity = frame.get("opportunity_cost", {}) or {}
    if not opportunity:
        return ""
    label = opportunity.get("cost_label") or opportunity.get("cost_type")
    window = opportunity.get("missed_window_label") or opportunity.get("missed_window")
    try:
        intensity = f"{float(opportunity.get('intensity') or 0.0):.2f}"
    except (TypeError, ValueError):
        intensity = "-"
    return f"{label}，错过{window}，强度 {intensity}"


def _reversibility_brief(frame: dict[str, Any]) -> str:
    reversibility = frame.get("reversibility", {}) or {}
    if not reversibility:
        return ""
    label = reversibility.get("threshold_label") or reversibility.get("threshold_state")
    route = reversibility.get("recovery_route_label") or reversibility.get("recovery_route")
    try:
        width = f"{float(reversibility.get('reversibility_width') or 0.0):.2f}"
    except (TypeError, ValueError):
        width = "-"
    return f"{label}，剩余可逆宽度 {width}，修复路径：{route}"


def _epistemic_brief(frame: dict[str, Any]) -> str:
    epistemic = frame.get("epistemic_boundary", {}) or {}
    if not epistemic:
        return ""
    label = epistemic.get("boundary_label") or epistemic.get("boundary_type")
    state = epistemic.get("boundary_state_label") or epistemic.get("boundary_state")
    focus = epistemic.get("focus_label") or epistemic.get("focus_id")
    try:
        speakability = f"{float(epistemic.get('speakability_width') or 0.0):.2f}"
    except (TypeError, ValueError):
        speakability = "-"
    return f"{label}，{focus}处于{state}，可说宽度 {speakability}"


def _common_ground_brief(frame: dict[str, Any]) -> str:
    common_ground = frame.get("common_ground", {}) or {}
    if not common_ground:
        return ""
    state = common_ground.get("state_label") or common_ground.get("state")
    frame_label = common_ground.get("dominant_frame_label") or common_ground.get("dominant_frame")
    try:
        legibility = f"{float(common_ground.get('mutual_legibility') or 0.0):.2f}"
    except (TypeError, ValueError):
        legibility = "-"
    try:
        repair_width = f"{float(common_ground.get('repair_handle_width') or 0.0):.2f}"
    except (TypeError, ValueError):
        repair_width = "-"
    return f"{state}，互相可读性 {legibility}，修复抓手 {repair_width}，主导框架：{frame_label}"


def _segment_llm_payload(segment: dict[str, Any], output_dir: Path) -> dict[str, Any]:
    previous = load_render_segments(output_dir)[-2:]
    return {
        "render_mode": "segment",
        "render_canon": segment.get("render_canon", {}),
        "case_ledger": segment.get("case_ledger", {}),
        "inquiry_trace": [
            item
            for item in segment.get("inquiry_trace", [])[-12:]
            if int(item.get("tick", 0) or 0) <= int(segment.get("tick_end", 0) or 0)
        ],
        "epistemic_trace": [
            item
            for item in segment.get("epistemic_trace", [])[-16:]
            if int(item.get("tick", 0) or 0) <= int(segment.get("tick_end", 0) or 0)
        ],
        "case_memory_trace": [
            item
            for item in segment.get("memory_trace", [])[-16:]
            if "case_memory_contamination" in (item.get("reconstruction_biases") or [])
            and int(item.get("tick", 0) or 0) <= int(segment.get("tick_end", 0) or 0)
        ],
        "daily_ecology_trace": [
            item
            for item in segment.get("environment_trace", [])[-16:]
            if item.get("event_type") == "DailyEcologyEvent"
            and int(item.get("tick", 0) or 0) <= int(segment.get("tick_end", 0) or 0)
        ],
        "attention_trace": [
            item
            for item in segment.get("attention_trace", [])[-16:]
            if int(item.get("tick", 0) or 0) <= int(segment.get("tick_end", 0) or 0)
        ],
        "opportunity_trace": [
            item
            for item in segment.get("opportunity_trace", [])[-16:]
            if int(item.get("tick", 0) or 0) <= int(segment.get("tick_end", 0) or 0)
        ],
        "reversibility_trace": [
            item
            for item in segment.get("reversibility_trace", [])[-16:]
            if int(item.get("tick", 0) or 0) <= int(segment.get("tick_end", 0) or 0)
        ],
        "common_ground_trace": [
            item
            for item in segment.get("common_ground_trace", [])[-16:]
            if int(item.get("tick", 0) or 0) <= int(segment.get("tick_end", 0) or 0)
        ],
        "previous_story_tail": [
            {
                "segment_id": item.get("segment_id"),
                "tick_range": [item.get("tick_start"), item.get("tick_end")],
                "text": item.get("text", "")[-1200:],
            }
            for item in previous
        ],
        "segment": {
            "segment_id": segment.get("segment_id"),
            "tick_range": [segment.get("tick_start"), segment.get("tick_end")],
            "boundary_reason": segment.get("boundary_reason"),
            "source_ticks": segment.get("source_ticks"),
            "simulated_seconds": segment.get("simulated_seconds"),
            "frames": segment.get("frames", []),
            "compressed_frames": _compressed_frame_groups(segment.get("frames", [])),
        },
        "ending_state": {
            "summary": segment.get("summary", {}),
            "relationship_view": segment.get("relationship_view", {}),
            "person_views": segment.get("person_views", {}),
            "irreversibility": segment.get("irreversibility", {}),
        },
        "rules": {
            "only_render_this_segment": True,
            "do_not_rewrite_previous_segments": True,
            "must_include_source_ticks": True,
            "append_mode": True,
            "compress_repeated_frames": True,
            "case_ledger_is_authoritative": True,
            "inquiry_trace_is_authoritative": True,
            "epistemic_trace_is_authoritative": True,
            "witness_strategy_is_authoritative": True,
            "daily_ecology_trace_is_authoritative": True,
            "attention_trace_is_authoritative": True,
            "opportunity_trace_is_authoritative": True,
            "reversibility_trace_is_authoritative": True,
            "common_ground_trace_is_authoritative": True,
            "case_memory_trace_is_authoritative": True,
            "do_not_add_case_facts_evidence_witnesses_or_culprits": True,
            "if_multiple_frames_have_the_same_summary": "write them as a sustained pattern with small pressure changes; do not restage the same dialogue or objects repeatedly",
        },
    }


def _boundary_reason(frames: list[dict[str, Any]], policy: dict[str, Any], *, force: bool) -> str | None:
    if force:
        return "模拟结束，收束未渲染片段"
    if not _minimum_segment_reached(frames, policy):
        return None
    if any(frame.get("phase_changed") for frame in frames):
        return "强闭合：关系阶段变化"
    if any(int(frame.get("fate_count", 0)) > 0 for frame in frames):
        return "强闭合：命运或不可逆变化"
    if any(int(frame.get("memory_count", 0)) > 0 for frame in frames):
        return "强闭合：记忆重构"
    if any(frame.get("recognition") for frame in frames):
        return "标准闭合：承认或误认结果出现"
    if any(frame.get("tick_type") == "scene" for frame in frames):
        return "标准闭合：场景结晶"
    micro_count = sum(1 for frame in frames if frame.get("tick_type") == "micro_interaction")
    if micro_count >= int(policy["micro_count"]):
        return f"弱闭合：连续微交互达到 {micro_count} 次"
    latent_seconds = sum(
        int(frame.get("simulated_time_delta_seconds") or 0)
        for frame in frames
        if frame.get("tick_type") == "latent"
    )
    if latent_seconds >= int(policy["latent_seconds"]):
        return "弱闭合：潜伏时间累积达到阈值"
    if len(frames) >= int(policy["max_ticks"]):
        return "兜底闭合：达到最大等待 tick"
    if _elapsed_seconds(frames) >= int(policy["max_seconds"]):
        return "兜底闭合：达到最大模拟时间跨度"
    return None


def _elapsed_seconds(frames: list[dict[str, Any]]) -> int:
    return sum(int(frame.get("simulated_time_delta_seconds") or 0) for frame in frames)


def _minimum_segment_reached(frames: list[dict[str, Any]], policy: dict[str, Any]) -> bool:
    min_ticks = max(1, int(policy.get("min_ticks") or 1))
    if len(frames) >= min_ticks:
        return True
    return _elapsed_seconds(frames) >= int(policy.get("latent_seconds") or 0)


def _compressed_frame_groups(frames: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: list[dict[str, Any]] = []
    for frame in frames:
        signature = _frame_signature(frame)
        if groups and groups[-1]["signature"] == signature:
            groups[-1]["count"] += 1
            groups[-1]["tick_end"] = frame.get("tick")
            groups[-1]["source_ticks"].append(frame.get("tick"))
            continue
        groups.append(
            {
                "signature": signature,
                "count": 1,
                "tick_start": frame.get("tick"),
                "tick_end": frame.get("tick"),
                "source_ticks": [frame.get("tick")],
                "frame": frame,
            }
        )
    return groups


def _frame_signature(frame: dict[str, Any]) -> tuple[Any, ...]:
    recognition = frame.get("recognition", {}) or {}
    action = frame.get("action", {}) or {}
    expression = frame.get("expression", {}) or {}
    return (
        frame.get("tick_type"),
        frame.get("phase"),
        frame.get("summary"),
        action.get("action_id"),
        action.get("action_mode"),
        expression.get("expression_id"),
        expression.get("expression_mode"),
        recognition.get("outcome"),
        int(frame.get("memory_count", 0)),
        int(frame.get("fate_count", 0)),
    )
