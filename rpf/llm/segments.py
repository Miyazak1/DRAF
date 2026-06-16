from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from rpf.llm.renderer import llm_markdown
from rpf.storage import configured_run_store
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
    source_ticks = [frame.get("tick") for frame in frames]
    return {
        "segment_id": f"seg-{segment_index:04d}",
        "segment_index": segment_index,
        "tick_start": frames[0].get("tick"),
        "tick_end": frames[-1].get("tick"),
        "boundary_reason": reason,
        "source_ticks": source_ticks,
        "simulated_seconds": _elapsed_seconds(frames),
        "frames": frames,
        "narrative_beats": _beats_for_ticks(payload.get("narrative_beats", []), source_ticks),
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
        "local_world_view": payload.get("local_world_view", {}),
        "object_registry_view": payload.get("object_registry_view", {}),
        "world_detail_context": _world_detail_context_for_ticks(
            payload.get("world_detail_context", {}),
            source_ticks,
            frames,
        ),
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
    run_id: str | None = None,
) -> dict[str, Any]:
    previous_records = load_render_segments(output_dir)
    if use_llm:
        if not api_key:
            raise RuntimeError("Missing API key for segment LLM rendering.")
        raw_text = llm_markdown(
            _segment_llm_payload(segment, output_dir),
            api_key=api_key,
            base_url=base_url,
            model=model,
            provider=provider,
            thinking=thinking,
            reasoning_effort=reasoning_effort,
        )
        normalized_text = normalize_segment_text(raw_text, segment)
        validation = validate_segment_output(raw_text, normalized_text, segment, previous_records)
        if validation["valid"]:
            text = normalized_text
            mode = "llm"
        else:
            text = deterministic_segment_markdown(segment)
            mode = "deterministic_fallback"
    else:
        text = deterministic_segment_markdown(segment)
        mode = "deterministic"
        validation = {"valid": True, "violations": [], "fallback_used": False}
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
        "model": model if use_llm else None,
        "validation": validation,
    }
    records = [*previous_records, record]
    (output_dir / "rendered_segments.json").write_text(
        json.dumps(records, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    stream = render_segment_stream(records, segment.get("render_canon", {}))
    stream_path = output_dir / "rendered_story_stream.md"
    stream_path.write_text(stream, encoding="utf-8")
    repetition_record = build_render_repetition_record(segment, record, previous_records)
    append_render_repetition_trace(output_dir, repetition_record)
    if run_id:
        configured_run_store().write_render_segment(run_id=run_id, segment=record)
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
        "validation": validation,
        "render_repetition": repetition_record,
    }


def validate_segment_output(
    raw_text: str,
    normalized_text: str,
    segment: dict[str, Any],
    previous_records: list[dict[str, Any]],
) -> dict[str, Any]:
    """Validate an LLM segment before it can be persisted."""

    violations: list[str] = []
    raw = _strip_markdown_fence(raw_text).strip()
    normalized = normalized_text.strip()
    source_ticks = {int(tick) for tick in segment.get("source_ticks", []) if str(tick).isdigit()}
    if not normalized:
        violations.append("empty_segment")
    if raw.startswith("# ") or normalized.startswith("# "):
        violations.append("document_title")
    forbidden_headings = ("概述", "总览", "结束状态", "边界说明", "overview", "ending_state", "boundary_note")
    for line in raw.splitlines():
        stripped = line.strip().lower()
        if stripped.startswith("## ") and any(label.lower() in stripped for label in forbidden_headings):
            violations.append("forbidden_full_document_section")
            break
    for line in raw.splitlines():
        stripped = line.strip()
        if not stripped.startswith("###"):
            continue
        ticks = _ticks_from_heading(stripped)
        if source_ticks and ticks and source_ticks.isdisjoint(ticks):
            violations.append("source_tick_mismatch")
            break
    if source_ticks and not _mentions_source_tick(normalized, source_ticks):
        violations.append("missing_source_ticks")
    if _repeats_previous_segment(normalized, previous_records):
        violations.append("previous_segment_repeated")
    return {
        "valid": not violations,
        "violations": sorted(set(violations)),
        "fallback_used": bool(violations),
    }


def build_render_repetition_record(
    segment: dict[str, Any],
    record: dict[str, Any],
    previous_records: list[dict[str, Any]],
) -> dict[str, Any]:
    groups = _compressed_frame_groups(segment.get("frames", []))
    repeated_groups = [group for group in groups if int(group.get("count", 0) or 0) > 1]
    validation = record.get("validation", {}) or {}
    locality = _dominant_locality(segment.get("frames", []))
    structural_similarity = max((group["count"] for group in groups), default=1) / max(len(segment.get("frames", [])) or 1, 1)
    summary_similarity = _summary_similarity(segment.get("frames", []), previous_records)
    if validation.get("violations"):
        repetition_class = "protocol_repetition"
        recommended_action = "reject_invalid_segment_output"
    elif repeated_groups:
        repetition_class = "state_repetition"
        recommended_action = "compress_as_pattern"
    elif summary_similarity >= 0.85:
        repetition_class = "expression_repetition"
        recommended_action = "shift_to_new_focus"
    else:
        repetition_class = "none"
        recommended_action = "append_segment"
    return {
        "segment_id": record.get("segment_id"),
        "tick_start": record.get("tick_start"),
        "tick_end": record.get("tick_end"),
        "mode": record.get("mode"),
        "repeated_scope": locality,
        "repeated_focuses": _unique_nonempty(frame.get("inquiry", {}).get("focus_id") for frame in segment.get("frames", [])),
        "repeated_objects": _active_registry_labels(segment.get("object_registry_view", {})),
        "repeated_actions": _unique_nonempty(
            (frame.get("action", {}) or {}).get("action_id") for frame in segment.get("frames", [])
        ),
        "summary_similarity": round(summary_similarity, 4),
        "structural_similarity": round(structural_similarity, 4),
        "repetition_class": repetition_class,
        "recommended_action": recommended_action,
        "protocol_violations": validation.get("violations", []),
    }


def append_render_repetition_trace(output_dir: Path, record: dict[str, Any]) -> None:
    path = output_dir / "render_repetition_trace.json"
    if path.exists():
        try:
            records = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            records = []
    else:
        records = []
    if not isinstance(records, list):
        records = []
    records.append(record)
    path.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")


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


def _mentions_source_tick(text: str, source_ticks: set[int]) -> bool:
    lower = text.lower()
    if "source tick" in lower or "来源 tick" in lower or "来源：" in text or "来源:" in text:
        numbers = {int(item) for item in re.findall(r"\d+", text)}
        return not numbers.isdisjoint(source_ticks)
    numbers = {int(item) for item in re.findall(r"\d+", text)}
    return not numbers.isdisjoint(source_ticks)


def _repeats_previous_segment(text: str, previous_records: list[dict[str, Any]]) -> bool:
    normalized = _compact_text(text)
    if len(normalized) < 80:
        return False
    for record in previous_records[-3:]:
        previous = _compact_text(str(record.get("text", "")))
        if len(previous) < 80:
            continue
        if normalized in previous or previous in normalized:
            return True
        chunk = previous[: min(240, len(previous))]
        if len(chunk) >= 80 and chunk in normalized:
            return True
    return False


def _compact_text(text: str) -> str:
    return re.sub(r"\s+", "", text.strip())


def _dominant_locality(frames: list[dict[str, Any]]) -> str:
    for frame in reversed(frames):
        locality = frame.get("locality", {}) or {}
        location = locality.get("location_label") or locality.get("location_id")
        if location:
            return str(location)
    return ""


def _summary_similarity(frames: list[dict[str, Any]], previous_records: list[dict[str, Any]]) -> float:
    summaries = [_compact_text(str(frame.get("summary", ""))) for frame in frames if frame.get("summary")]
    if not summaries:
        return 0.0
    current = "".join(summaries)
    if not current:
        return 0.0
    previous_text = _compact_text("\n".join(str(record.get("text", "")) for record in previous_records[-3:]))
    if not previous_text:
        return 0.0
    overlap = sum(1 for summary in summaries if summary and summary in previous_text)
    return overlap / max(len(summaries), 1)


def _active_registry_labels(view: dict[str, Any]) -> list[str]:
    items = []
    for key, id_key in (
        ("world_objects", "object_id"),
        ("record_objects", "record_id"),
        ("evidence_objects", "evidence_id"),
    ):
        for item in view.get(key, []) or []:
            if isinstance(item, dict):
                items.append(str(item.get("label") or item.get(id_key) or ""))
    return _unique_nonempty(items)


def _unique_nonempty(values: Any) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value is None:
            continue
        text = str(value).strip()
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result


def deterministic_segment_markdown(segment: dict[str, Any]) -> str:
    frames = segment.get("frames", []) or []
    title = f"## 第 {segment['segment_index']} 段：{_outline_title(segment)}"
    lines = [
        title,
        "",
        "### 发生了什么",
        "",
        *_outline_what_happened(segment, frames),
        "",
        "### 为什么重要",
        "",
        _outline_why_it_mattered(segment, frames),
        "",
        "### 承认与误认",
        "",
        _outline_recognition(frames),
        "",
        "### 关系移动",
        "",
        _outline_relationship_movement(segment, frames),
        "",
        "### 记忆与不可逆",
        "",
        _outline_memory_and_irreversibility(frames),
        "",
        "### 延续压力",
        "",
        _outline_carry_forward_pressure(segment, frames),
        "",
        f"（来源 tick: {', '.join(str(tick) for tick in segment['source_ticks'])}）",
    ]
    return "\n".join(line for line in lines if line is not None).strip() + "\n"


def _outline_title(segment: dict[str, Any]) -> str:
    reason = str(segment.get("boundary_reason") or "")
    if "记忆" in reason:
        label = "记忆重新压回现场"
    elif "命运" in reason or "不可逆" in reason:
        label = "不可逆的门槛被触动"
    elif "关系阶段" in reason:
        label = "关系阶段发生移动"
    elif "承认" in reason or "误认" in reason:
        label = "承认问题浮出表面"
    elif "场景" in reason:
        label = "场景结晶"
    elif "微交互" in reason:
        label = "微交互连续成形"
    elif "潜伏" in reason:
        label = "沉默时间开始累积"
    else:
        label = "压力闭合为一段"
    return f"{label}（第 {segment['tick_start']} 至 {segment['tick_end']} 步）"


def _outline_what_happened(segment: dict[str, Any], frames: list[dict[str, Any]]) -> list[str]:
    beats = segment.get("narrative_beats", []) or []
    if beats:
        return [_beat_sentence(beat) for beat in beats]
    if not frames:
        return ["本段没有可见场景帧；渲染回退为结构性摘要。"]
    lines: list[str] = []
    for frame_group in _compressed_frame_groups(frames):
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
        prefix = f"第 {tick_label} 步"
        if names:
            prefix += f"，{names}"
        lines.append(f"{prefix}：{frame.get('summary', '')}")
        if frame_group["count"] > 1:
            lines.append(f"同一结构连续出现 {frame_group['count']} 次。这里应被理解为模式持续，而不是新的独立场面。")
    return lines


def _beat_sentence(beat: dict[str, Any]) -> str:
    if beat.get("beat_type") == "pattern_continuation":
        tick_label = f"第 {beat.get('tick_start')} 至 {beat.get('tick_end')} 步"
        constraints = _beat_materialized_constraints(beat)
        constraint_text = f"被激活的材料约束包括：{constraints}。" if constraints else ""
        return (
            f"{tick_label}：{beat.get('repeated_beat_type')} 持续重复。"
            f"未改变的是：{'；'.join(str(item) for item in beat.get('what_did_not_change', [])[:2]) or '-'}。"
            f"收窄处：{beat.get('what_narrowed') or '-'}。"
            f"{constraint_text}"
        )
    tick_label = f"第 {beat.get('tick')} 步"
    intended = (beat.get("intended_action") or {}).get("description") or "-"
    realized = (beat.get("realized_action") or {}).get("description") or "-"
    obstruction = (beat.get("obstruction") or {}).get("description") or "-"
    outcome = (beat.get("outcome") or {}).get("recognition_outcome") or beat.get("beat_type")
    constraints = _beat_materialized_constraints(beat)
    constraint_text = f"被激活的材料约束包括：{constraints}。" if constraints else ""
    return f"{tick_label}：{beat.get('beat_type')}。试图发生的是“{intended}”，实际呈现为“{realized}”；受阻于“{obstruction}”，结果是“{outcome}”。{constraint_text}"


def _beat_materialized_constraints(beat: dict[str, Any]) -> str:
    constraints = beat.get("materialized_constraints", []) or []
    parts = []
    for item in constraints[:3]:
        capacity = item.get("affected_capacity") or "-"
        target = item.get("target_ref") or item.get("detail_id") or "-"
        scope = item.get("effect_scope") or "-"
        parts.append(f"{target} 触碰 {capacity}（{scope}）")
    return "；".join(parts)


def _outline_why_it_mattered(segment: dict[str, Any], frames: list[dict[str, Any]]) -> str:
    parts = [f"本段闭合原因是：{segment.get('boundary_reason', '-')}。"]
    viability = _strongest_brief(frames, _viability_brief)
    if viability:
        parts.append(f"底层压力集中在：{viability}。")
    locality = _dominant_locality(frames)
    if locality:
        parts.append(f"场景被本地世界压在“{locality}”附近，冲突不是抽象发生的。")
    objects = _active_registry_labels(segment.get("object_registry_view", {}) or {})
    if objects:
        parts.append(f"可用的物质锚点包括：{'，'.join(objects[:4])}。")
    world_details = segment.get("world_detail_context", {}) or {}
    details = world_details.get("ephemeral_details", []) or []
    profiles = world_details.get("soft_world_profiles", []) or []
    if details:
        detail_texts = [str(item.get("text") or item.get("detail_id")) for item in details[:3]]
        parts.append(f"注意力只唤醒了当前可感知细节：{'；'.join(detail_texts)}。")
    if profiles:
        tags = _unique_nonempty(tag for item in profiles for tag in (item.get("sensory_tags", []) or []))
        if tags:
            parts.append(f"稳定的本地质地被压缩为：{'，'.join(tags[:5])}。")
    causal_details = world_details.get("causal_world_details", []) or []
    if causal_details:
        active_details = [item for item in causal_details if item.get("activation_state") == "activated"]
        inactive_details = [item for item in causal_details if item.get("activation_state") != "activated"]
        if active_details:
            labels = _unique_nonempty(item.get("detail_type") for item in active_details)
            parts.append(f"本段有因果细节被后续约束触碰并形成投影激活：{'，'.join(labels[:4])}。")
        if inactive_details:
            labels = _unique_nonempty(item.get("detail_type") for item in inactive_details)
            parts.append(f"另有候选因果细节已被验证但尚未激活：{'，'.join(labels[:4])}。")
    beats = segment.get("narrative_beats", []) or []
    if beats:
        beat_types = _unique_nonempty(beat.get("beat_type") for beat in beats)
        parts.append(f"叙事节拍集中在：{'，'.join(beat_types[:5])}。")
    return "".join(parts)


def _outline_recognition(frames: list[dict[str, Any]]) -> str:
    outcomes = _unique_nonempty(
        (frame.get("recognition", {}) or {}).get("outcome_label")
        or (frame.get("recognition", {}) or {}).get("outcome")
        for frame in frames
    )
    epistemic = _strongest_brief(frames, _epistemic_brief)
    common_ground = _strongest_brief(frames, _common_ground_brief)
    parts = []
    if outcomes:
        parts.append(f"承认结果集中表现为：{'，'.join(outcomes)}。")
    else:
        parts.append("本段没有形成新的明确承认结果，但承认压力仍在背景中持续。")
    if epistemic:
        parts.append(f"信息边界显示：{epistemic}。")
    if common_ground:
        parts.append(f"共同现实显示：{common_ground}。")
    return "".join(parts)


def _outline_relationship_movement(segment: dict[str, Any], frames: list[dict[str, Any]]) -> str:
    relationship = segment.get("relationship_view", {}) or {}
    phase = relationship.get("phase_label") or relationship.get("phase") or _last_nonempty(frame.get("phase") for frame in frames)
    rpps = relationship.get("recurring_rpps", []) or []
    changed = any(frame.get("phase_changed") for frame in frames)
    parts = [f"关系阶段现在是：{phase or '-'}。"]
    if rpps:
        parts.append(f"反复出现的关系模式包括：{'，'.join(str(item) for item in rpps[:4])}。")
    if changed:
        parts.append("本段内出现阶段移动，后续互动会在新的关系读法下展开。")
    else:
        parts.append("本段没有彻底改变关系阶段，但延续了已有模式的可预期性。")
    return "".join(parts)


def _outline_memory_and_irreversibility(frames: list[dict[str, Any]]) -> str:
    memory_count = sum(int(frame.get("memory_count", 0) or 0) for frame in frames)
    fate_count = sum(int(frame.get("fate_count", 0) or 0) for frame in frames)
    reversibility = _strongest_brief(frames, _reversibility_brief)
    opportunity = _strongest_brief(frames, _opportunity_brief)
    parts = []
    if memory_count:
        parts.append(f"本段触发了 {memory_count} 次记忆重构，过去没有保持静止。")
    else:
        parts.append("本段没有显式记忆重构。")
    if fate_count:
        parts.append(f"同时出现 {fate_count} 个命运或不可逆转折信号。")
    if reversibility:
        parts.append(f"行动可逆性显示：{reversibility}。")
    if opportunity:
        parts.append(f"机会成本显示：{opportunity}。")
    return "".join(parts)


def _outline_carry_forward_pressure(segment: dict[str, Any], frames: list[dict[str, Any]]) -> str:
    groups = _compressed_frame_groups(frames)
    repeated = [group for group in groups if int(group.get("count", 0) or 0) > 1]
    parts = []
    if repeated:
        parts.append("重复结构没有被当作新剧情处理，而是作为关系模式继续沉积。")
    last_summary = str(frames[-1].get("summary", "")) if frames else ""
    if last_summary:
        parts.append(f"下一段承接的最近压力是：{last_summary}")
    else:
        parts.append("下一段承接的是尚未被具体场景释放的结构压力。")
    parts.append(f"段落边界来自“{segment.get('boundary_reason', '-')}”，因此后续模拟仍应从这个未完全解决的压力继续。")
    return "".join(parts)


def _strongest_brief(frames: list[dict[str, Any]], fn) -> str:
    for frame in reversed(frames):
        value = fn(frame)
        if value:
            return value
    return ""


def _last_nonempty(values: Any) -> str:
    for value in reversed(list(values)):
        if value:
            return str(value)
    return ""


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
        "local_world_view": segment.get("local_world_view", {}),
        "object_registry_view": segment.get("object_registry_view", {}),
        "world_detail_context": segment.get("world_detail_context", {}),
        "narrative_beats": segment.get("narrative_beats", []),
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
            "local_world_view_is_authoritative": True,
            "object_registry_view_is_authoritative": True,
            "world_detail_context_is_attention_gated": True,
            "world_detail_context_is_non_causal_render_context": True,
            "narrative_beats_are_authoritative": True,
            "case_memory_trace_is_authoritative": True,
            "do_not_add_case_facts_evidence_witnesses_or_culprits": True,
            "do_not_add_durable_objects_records_messages_or_custody_changes": True,
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


def _beats_for_ticks(beats: list[dict[str, Any]], source_ticks: list[Any]) -> list[dict[str, Any]]:
    wanted = {int(tick) for tick in source_ticks if str(tick).isdigit()}
    selected = []
    for beat in beats:
        beat_ticks = {int(beat.get("tick", 0) or 0)}
        if beat.get("tick_start") and beat.get("tick_end"):
            start = int(beat.get("tick_start") or 0)
            end = int(beat.get("tick_end") or start)
            beat_ticks = set(range(start, end + 1))
        if wanted and beat_ticks and wanted.isdisjoint(beat_ticks):
            continue
        selected.append(beat)
    return selected


def _world_detail_context_for_ticks(
    context: dict[str, Any],
    source_ticks: list[Any],
    frames: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    wanted = {int(tick) for tick in source_ticks if str(tick).isdigit()}
    if not context:
        return {}
    frame_scope_ids = _frame_scope_ids(frames or [])
    focuses = [
        item
        for item in context.get("attention_focuses", []) or []
        if int(item.get("tick", 0) or 0) in wanted
    ]
    focus_ids = {item.get("focus_id") for item in focuses}
    scope_ids = {item.get("scope_id") for item in focuses} | frame_scope_ids
    details = [
        item
        for item in context.get("ephemeral_details", []) or []
        if int(item.get("tick", 0) or 0) in wanted
    ]
    gaps = [
        item
        for item in context.get("detail_gaps", []) or []
        if item.get("focus_id") in focus_ids
    ]
    profiles = [
        item
        for item in (
            context.get("active_soft_profiles", [])
            or context.get("soft_world_profiles", [])
            or []
        )
        if item.get("scope_id") in scope_ids
    ]
    history = [
        item
        for item in context.get("soft_profile_history", []) or []
        if item.get("scope_id") in scope_ids
        and (not wanted or int(item.get("tick", 0) or 0) <= max(wanted))
    ][-12:]
    candidates = [
        item
        for item in context.get("causal_detail_candidates", []) or []
        if item.get("scope_id") in scope_ids
        and (item.get("focus_id") in focus_ids or item.get("validation_status") == "validated")
    ]
    candidate_ids = {item.get("candidate_id") for item in candidates}
    decisions = [
        item
        for item in context.get("detail_persistence_decisions", []) or []
        if item.get("candidate_id") in candidate_ids
    ]
    causal_details = [
        item
        for item in context.get("causal_world_details", []) or []
        if item.get("scope_id") in scope_ids
    ]
    detail_ids = {item.get("detail_id") for item in causal_details}
    activations = [
        item
        for item in context.get("causal_world_detail_activations", []) or []
        if item.get("detail_id") in detail_ids
    ]
    return {
        "rules": context.get("rules", {}),
        "attention_focuses": focuses,
        "detail_gaps": gaps,
        "ephemeral_details": details,
        "soft_world_profiles": profiles,
        "active_soft_profiles": profiles,
        "soft_profile_history": history,
        "causal_detail_candidates": candidates,
        "detail_persistence_decisions": decisions,
        "causal_world_details": causal_details,
        "causal_world_detail_activations": activations,
        "rejected_details": context.get("rejected_details", []),
    }


def _frame_scope_ids(frames: list[dict[str, Any]]) -> set[str]:
    scope_ids: set[str] = set()
    for frame in frames:
        locality = frame.get("locality", {}) or {}
        if locality.get("location_id"):
            scope_ids.add(str(locality["location_id"]))
        if locality.get("route_id"):
            scope_ids.add(str(locality["route_id"]))
    return scope_ids


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
