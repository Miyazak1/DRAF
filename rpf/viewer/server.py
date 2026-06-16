from __future__ import annotations

import json
import mimetypes
import threading
import time
import uuid
import zipfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import yaml

from rpf.core.events import Event
from rpf.core.object_registry import ObjectRegistrySpec
from rpf.engine.simulator import Simulator
from rpf.engine.metrics import compute_metrics
from rpf.scenarios.loader import load_scenario
from rpf.storage import RunStore, configured_run_store


STATIC_DIR = Path(__file__).with_name("static")
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_EXAMPLES_DIR = PROJECT_ROOT / "examples"
DEFAULT_EXPERIENCE_DIR = PROJECT_ROOT / "out" / "experience"
ZH = {
    "material_urgency": "物质紧迫",
    "unacknowledged_help": "未被承认的帮助",
    "practical_repair": "实际补偿",
    "public_politeness": "公开礼貌",
    "delayed_reply": "延迟回应",
    "short_answer": "短促回答",
    "gaze_avoidance": "回避目光",
    "refused": "被拒绝",
    "misunderstood": "被误解",
    "postponed": "被推迟",
    "displaced": "被转移",
    "unspeakable": "变得不可说",
    "granted": "承认成功",
    "partial": "部分承认",
    "shared": "共同现实稳定",
    "fragile": "脆弱",
    "contested": "共同现实争夺",
    "fractured": "共同现实断裂",
    "locked-in": "锁定",
    "cold-war": "冷战",
    "repair-avoidant": "回避修复",
    "cls-debt-named": "债务命名",
    "irr-symbolic-debt-lock": "象征债务锁定",
    "debt_accounting": "债务记账场面",
    "repair_scene": "修复场面",
    "avoidance_scene": "回避场面",
    "public_performance": "公共表演场面",
    "care_control": "照顾-控制场面",
    "double_bind": "双重束缚场面",
    "material_accounting": "物质核算场面",
    "recognition_trial": "承认审判场面",
    "contaminated_evidence_review": "污染线索审阅",
    "unstable_testimony_probe": "不稳定证词追问",
    "forbidden_symbol_confrontation": "禁忌符号对质",
    "evidence_contamination": "证物污染",
    "testimony_gap": "证词断裂",
    "yellow_symbol": "黄漆符号",
    "protective_silence": "保护性沉默",
    "partial_disclosure": "部分透露",
    "probing_counterquestion": "试探性反问",
    "refusal_to_confirm": "拒绝确认",
    "controlled_detail_release": "控制性透露",
    "withholding": "保留细节",
    "limited_disclosure": "有限透露",
    "testing_the_listener": "测试倾听者",
    "denial_boundary": "拒认边界",
    "controlled_disclosure": "控制透露",
    "night_recovery": "夜间恢复",
    "workday_friction": "工作日摩擦",
    "meal_or_errand_overlap": "吃饭或杂事重叠",
    "commute_overlap": "通勤重叠",
    "late_return": "晚归",
    "waiting_time": "等待时间",
    "recovery_window_loss": "恢复窗口损失",
    "repair_window_loss": "修复窗口损失",
    "evidence_window_loss": "证据窗口损失",
    "social_exposure_cost": "公共暴露成本",
    "trust_window_loss": "信任窗口损失",
    "ordinary_task_spillover": "日常任务外溢",
    "sleep_or_body_recovery": "睡眠或身体恢复",
    "clean_repair_opening": "干净修复窗口",
    "usable_evidence_or_testimony_timing": "可用证据或证词时机",
    "private_resolution_before_public_reading": "被公开解读前的私人解决",
    "low-cost_trust_update": "低成本信任更新",
    "ordinary_work_or_errand_completion": "普通工作或杂事完成",
    "recoverable": "仍可修复",
    "narrowing": "可逆性收窄",
    "threshold_crossed": "越过阈值",
    "symbolic_only": "只能象征性修复",
    "ordinary_repair_still_available": "普通修复仍可用",
    "direct_repair_still_possible": "直接修复仍可能",
    "repair_requires_extra_cost": "修复需要额外代价",
    "repair_requires_explicit_counter_history": "修复需要明确改写历史",
    "only_symbolic_acknowledgement_remains": "只剩象征性承认",
    "case_knowledge_asymmetry": "案件知情不对称",
    "testimony_disclosure_risk": "证词披露风险",
    "public_private_knowledge_split": "公私知识分裂",
    "unspeakable_fact_boundary": "不可说事实边界",
    "open_but_costly": "可说但有代价",
    "narrowed": "可说性收窄",
    "sealed": "被封闭",
    "body_management": "身体管理",
    "case_fixation": "案件固着",
    "threat_monitoring": "威胁监控",
    "repair_opportunity": "修复机会",
    "avoidance_route": "回避路径",
    "memory_intrusion": "记忆侵入",
    "claimant": "索取承认者位置",
    "debtor": "负债者位置",
    "defender": "防御者位置",
    "caretaker": "照顾者位置",
    "controlled": "被控制者位置",
    "public_performer": "公共表演者位置",
    "withdrawer": "撤退者位置",
    "trapped_party": "被困者位置",
    "repair_partner": "修复参与者位置",
    "bound_party": "绑定者位置",
}


def _read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return default


def _read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def _read_timeline(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    events: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return events


def build_viewer_payload(output_dir: Path) -> dict[str, Any]:
    run_dir = output_dir.resolve()
    metrics = _read_json(run_dir / "metrics.json", {})
    timeline = _read_timeline(run_dir / "timeline.jsonl")
    manifest = _read_json(run_dir / "timeline_manifest.json", {})
    payload = {
        "run_dir": str(run_dir),
        "manifest": manifest,
        "render_canon": _read_render_canon(run_dir, manifest),
        "case_ledger": _read_case_ledger(run_dir, manifest),
        "derived_views": _read_json(run_dir / "derived_views.json", {}),
        "metrics": metrics,
        "scheduler": _read_json(run_dir / "scheduler_diagnostics.json", []),
        "projection": _read_json(run_dir / "projection_trace.json", []),
        "affordance": _read_json(run_dir / "affordance_trace.json", []),
        "action": _read_json(run_dir / "action_trace.json", []),
        "expression": _read_json(run_dir / "expression_trace.json", []),
        "recognition": _read_json(run_dir / "recognition_trace.json", []),
        "viability": _read_json(run_dir / "viability_trace.json", []),
        "inquiry": _read_json(run_dir / "inquiry_trace.json", []),
        "fate": _read_json(run_dir / "fate_transition_trace.json", []),
        "frame_definition": _read_json(run_dir / "frame_trace.json", []),
        "account": _read_json(run_dir / "account_trace.json", []),
        "normativity": _read_json(run_dir / "normativity_trace.json", []),
        "relevance": _read_json(run_dir / "relevance_trace.json", []),
        "attention": _read_json(run_dir / "attention_trace.json", []),
        "opportunity": _read_json(run_dir / "opportunity_trace.json", []),
        "reversibility": _read_json(run_dir / "reversibility_trace.json", []),
        "position": _read_json(run_dir / "position_trace.json", []),
        "expectation": _read_json(run_dir / "expectation_trace.json", []),
        "memory": _read_json(run_dir / "memory_trace.json", []),
        "binding": _read_json(run_dir / "binding_trace.json", []),
        "common_ground": _read_json(run_dir / "common_ground_trace.json", []),
        "epistemic": _read_json(run_dir / "epistemic_trace.json", []),
        "environment": _read_json(run_dir / "environment_trace.json", []),
        "disposition": _read_json(run_dir / "disposition_trace.json", []),
        "relation": _read_json(run_dir / "relation_trace.json", []),
        "rpp_activation": _read_json(run_dir / "rpp_activation_trace.json", []),
        "rpp_dynamics": _read_json(run_dir / "rpp_dynamics_trace.json", []),
        "local_world": _read_json(run_dir / "local_world_trace.json", []),
        "object_registry": _read_json(run_dir / "object_registry.json", {}),
        "location_selection": _read_json(run_dir / "location_selection_trace.json", []),
        "route_selection": _read_json(run_dir / "route_selection_trace.json", []),
        "audience_exposure": _read_json(run_dir / "audience_exposure_trace.json", []),
        "irreversibility": _read_json(run_dir / "irreversibility_report.json", {}),
        "timeline": timeline,
        "rendered_segments": _read_json(run_dir / "rendered_segments.json", []),
        "render_repetition": _read_json(run_dir / "render_repetition_trace.json", []),
        "rendered_story_stream": _read_text(run_dir / "rendered_story_stream.md"),
    }
    payload["story"] = build_story_frames(payload)
    payload["local_world_view"] = build_local_world_view(payload)
    payload["object_registry_view"] = build_object_registry_view(payload)
    payload["summary"] = {
        "event_count": metrics.get("event_count", len(timeline)),
        "phase": payload["derived_views"].get("relationship_view", {}).get("phase_label", "unknown"),
        "trust": payload["derived_views"].get("trust_view", {}),
        "resentment": payload["derived_views"].get("resentment_pressure_view", {}),
        "repair": payload["derived_views"].get("repair_capacity_view", {}),
        "top_events": _top_counts(metrics.get("event_type_counts", {}), 8),
        "top_rpps": _top_counts(metrics.get("rpp_activation_score_sums", {}), 5),
        "top_compositions": _top_counts(metrics.get("rpp_composition_score_sums", {}), 5),
    }
    return payload


def build_viewer_payload_from_database(run_id: str, store: RunStore | None = None) -> dict[str, Any]:
    resolved_store = store or configured_run_store()
    data = resolved_store.read_viewer_run(run_id=run_id)
    if not data:
        raise ValueError(f"Cannot find database run: {run_id}")
    return build_viewer_payload_from_database_records(data)


def build_viewer_payload_from_database_records(data: dict[str, Any]) -> dict[str, Any]:
    run = data.get("run", {}) or {}
    events = [_db_event_to_timeline(event) for event in data.get("events", [])]
    event_models = [_db_event_to_model(event) for event in data.get("events", [])]
    metrics = compute_metrics(event_models)
    traces = _db_traces_by_payload_key(data.get("traces", []))
    render_canon = run.get("render_canon") or {}
    case_ledger = run.get("case_ledger") or {}
    rendered_segments = data.get("render_segments", []) or []
    payload = {
        "run_id": str(run.get("run_id") or ""),
        "run_dir": str(run.get("output_dir") or ""),
        "storage_backend": "postgres",
        "manifest": run.get("metadata") or {},
        "render_canon": render_canon,
        "case_ledger": case_ledger,
        "derived_views": _db_derived_views(traces),
        "metrics": metrics,
        "scheduler": traces.get("scheduler", []),
        "projection": traces.get("projection", []),
        "affordance": traces.get("affordance", []),
        "action": traces.get("action", []),
        "expression": traces.get("expression", []),
        "recognition": traces.get("recognition", []),
        "viability": traces.get("viability", []),
        "inquiry": traces.get("inquiry", []),
        "fate": traces.get("fate", []),
        "frame_definition": traces.get("frame_definition", []),
        "account": traces.get("account", []),
        "normativity": traces.get("normativity", []),
        "relevance": traces.get("relevance", []),
        "attention": traces.get("attention", []),
        "opportunity": traces.get("opportunity", []),
        "reversibility": traces.get("reversibility", []),
        "position": traces.get("position", []),
        "expectation": traces.get("expectation", []),
        "memory": traces.get("memory", []),
        "binding": traces.get("binding", []),
        "common_ground": traces.get("common_ground", []),
        "epistemic": traces.get("epistemic", []),
        "environment": traces.get("environment", []),
        "disposition": traces.get("disposition", []),
        "relation": traces.get("relation", []),
        "rpp_activation": traces.get("rpp_activation", []),
        "rpp_dynamics": traces.get("rpp_dynamics", []),
        "local_world": traces.get("local_world", []),
        "object_registry": {},
        "location_selection": traces.get("location_selection", []),
        "route_selection": traces.get("route_selection", []),
        "audience_exposure": traces.get("audience_exposure", []),
        "irreversibility": {},
        "timeline": events,
        "rendered_segments": rendered_segments,
        "render_repetition": traces.get("render_repetition", []),
        "rendered_story_stream": _db_rendered_story_stream(render_canon, rendered_segments),
    }
    payload["story"] = build_story_frames(payload)
    payload["local_world_view"] = build_local_world_view(payload)
    payload["object_registry_view"] = build_object_registry_view(payload)
    payload["summary"] = {
        "event_count": metrics.get("event_count", len(events)),
        "phase": payload["derived_views"].get("relationship_view", {}).get("phase_label", "unknown"),
        "trust": payload["derived_views"].get("trust_view", {}),
        "resentment": payload["derived_views"].get("resentment_pressure_view", {}),
        "repair": payload["derived_views"].get("repair_capacity_view", {}),
        "top_events": _top_counts(metrics.get("event_type_counts", {}), 8),
        "top_rpps": _top_counts(metrics.get("rpp_activation_score_sums", {}), 5),
        "top_compositions": _top_counts(metrics.get("rpp_composition_score_sums", {}), 5),
    }
    return payload


def _db_event_to_model(event: dict[str, Any]) -> Event:
    return Event(
        event_id=str(event.get("event_id")),
        tick=int(event.get("tick") or 0),
        event_type=str(event.get("event_type")),
        source_layer=str(event.get("source_layer")),
        payload=event.get("payload") or {},
        causal_refs=list(event.get("causal_refs") or []),
        deterministic_order=int(event.get("event_order") or event.get("deterministic_order") or 0),
    )


def _db_event_to_timeline(event: dict[str, Any]) -> dict[str, Any]:
    model = _db_event_to_model(event)
    return model.model_dump(mode="json")


def _db_traces_by_payload_key(traces: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    layer_map = {
        "fate_transition": "fate",
        "frame": "frame_definition",
    }
    grouped: dict[str, list[dict[str, Any]]] = {}
    for trace in traces:
        key = layer_map.get(str(trace.get("layer")), str(trace.get("layer")))
        payload = trace.get("payload") or {}
        grouped.setdefault(key, []).append(payload)
    return grouped


def _db_derived_views(traces: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    projection = traces.get("projection", [])
    latest = projection[-1] if projection else {}
    return {
        "relationship_view": {
            "phase_label": latest.get("relationship_phase", "unknown"),
            "evidence_refs": latest.get("evidence_refs", []),
        },
        "person_views": latest.get("person_labels", {}),
        "trust_view": {},
        "resentment_pressure_view": {},
        "repair_capacity_view": {},
    }


def _db_rendered_story_stream(render_canon: dict[str, Any], segments: list[dict[str, Any]]) -> str:
    if not segments:
        return ""
    title = render_canon.get("title") or "RPF 持续故事"
    lines = [f"# {title}", "", "## 持续渲染", ""]
    for segment in segments:
        lines.append(str(segment.get("text", "")).strip())
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def scenario_catalog(examples_dir: Path = DEFAULT_EXAMPLES_DIR) -> list[dict[str, Any]]:
    if not examples_dir.exists():
        return []
    scenarios: list[dict[str, Any]] = []
    for path in sorted(examples_dir.glob("*.yaml")):
        try:
            scenario = load_scenario(path)
        except Exception:
            continue
        canon = scenario.get("render_canon", {}) if isinstance(scenario.get("render_canon"), dict) else {}
        scenarios.append(
            {
                "id": scenario.get("id", path.stem),
                "name": scenario.get("name", path.stem),
                "title": canon.get("title") or scenario.get("name", path.stem),
                "description": str(scenario.get("description", "")).strip(),
                "path": str(path),
                "output_dir": str((DEFAULT_EXPERIENCE_DIR / str(scenario.get("id", path.stem))).resolve()),
                "cast": canon.get("cast", {}),
                "setting": canon.get("setting", {}),
            }
        )
    return scenarios


def run_catalog(experience_dir: Path = DEFAULT_EXPERIENCE_DIR) -> list[dict[str, Any]]:
    database_runs = _database_run_catalog()
    if not experience_dir.exists():
        return database_runs
    runs: list[dict[str, Any]] = []
    for manifest_path in sorted(experience_dir.rglob("timeline_manifest.json"), key=lambda item: item.stat().st_mtime, reverse=True):
        output_dir = manifest_path.parent
        manifest = _read_json(manifest_path, {})
        metrics = _read_json(output_dir / "metrics.json", {})
        canon = _read_render_canon(output_dir, manifest)
        metadata = _read_json(output_dir / "run_metadata.json", {})
        runs.append(
            {
                "run_id": metadata.get("run_id") or output_dir.name,
                "scenario_id": metadata.get("scenario_id") or Path(str(manifest.get("scenario_path", ""))).stem,
                "title": metadata.get("title") or canon.get("title") or output_dir.name,
                "output_dir": str(output_dir.resolve()),
                "created_at": metadata.get("created_at") or _mtime_iso(manifest_path),
                "mode": metadata.get("mode") or "unknown",
                "seed": metadata.get("seed") or manifest.get("seed"),
                "tick": metrics.get("event_type_counts", {}).get("TickStartedEvent", manifest.get("steps")),
                "event_count": metrics.get("event_count", 0),
                "phase": _read_json(output_dir / "derived_views.json", {}).get("relationship_view", {}).get("phase_label", "-"),
                "storage_backend": "file",
            }
        )
    return database_runs + runs


def _database_run_catalog() -> list[dict[str, Any]]:
    try:
        store = configured_run_store()
        rows = store.list_runs(limit=50)
    except Exception:
        return []
    runs: list[dict[str, Any]] = []
    for row in rows:
        runs.append(
            {
                "run_id": str(row.get("run_id", "")),
                "scenario_id": row.get("scenario_id"),
                "title": row.get("title"),
                "output_dir": row.get("output_dir") or "",
                "created_at": row.get("started_at"),
                "mode": row.get("mode"),
                "seed": row.get("seed"),
                "tick": row.get("tick_count"),
                "event_count": row.get("event_count"),
                "phase": "-",
                "status": row.get("status"),
                "storage_backend": "postgres",
            }
        )
    return runs


def _health_payload(output_dir: Path, examples_dir: Path = DEFAULT_EXAMPLES_DIR) -> dict[str, Any]:
    run_dir = output_dir.resolve()
    manifest = _read_json(run_dir / "timeline_manifest.json", {})
    metrics = _read_json(run_dir / "metrics.json", {})
    metadata = _read_json(run_dir / "run_metadata.json", {})
    canon = _read_render_canon(run_dir, manifest)
    scenario_path = str(metadata.get("scenario_path") or manifest.get("scenario_path") or "")
    scenario_id = str(
        metadata.get("scenario_id")
        or Path(scenario_path).stem
        or run_dir.name
    )
    scenarios = scenario_catalog(examples_dir)
    available_ids = {str(item.get("id")) for item in scenarios}
    timeline_exists = (run_dir / "timeline.jsonl").exists()
    return {
        "ok": bool(timeline_exists and (run_dir / "timeline_manifest.json").exists()),
        "service": "draf-viewer",
        "run_dir": str(run_dir),
        "scenario_id": scenario_id,
        "title": canon.get("title") or metadata.get("title") or scenario_id,
        "default_experience": "yellow_sign_cold_case",
        "scenario_available": scenario_id in available_ids,
        "event_count": metrics.get("event_count", 0),
        "tick_count": metrics.get("event_type_counts", {}).get("TickStartedEvent", manifest.get("steps", 0)),
        "timeline_exists": timeline_exists,
        "scenario_count": len(scenarios),
    }


def build_run_report(output_dir: Path) -> str:
    payload = build_viewer_payload(output_dir)
    metadata = _read_json(output_dir / "run_metadata.json", {})
    comparison = _comparison_summary_from_payload(payload, run_label=str(output_dir.resolve()), metadata=metadata)
    return build_run_report_from_payload(payload, comparison=comparison)


def build_run_report_from_database(run_id: str, store: RunStore | None = None) -> str:
    payload = build_viewer_payload_from_database(run_id, store=store)
    comparison = _comparison_summary_from_payload(payload, run_label=f"postgres:{run_id}", metadata={"run_id": run_id, "mode": "postgres"})
    return build_run_report_from_payload(payload, comparison=comparison)


def build_run_report_from_payload(payload: dict[str, Any], *, comparison: dict[str, Any]) -> str:
    summary = payload.get("summary", {})
    canon = payload.get("render_canon", {})
    case_ledger = payload.get("case_ledger", {})
    story = payload.get("story", [])
    last_frame = story[-1] if story else {}
    pressure = last_frame.get("pressure", {}) if isinstance(last_frame, dict) else {}
    turns = [
        frame
        for frame in story
        if frame.get("phase_changed")
        or frame.get("recognition")
        or int(frame.get("memory_count", 0)) > 0
        or int(frame.get("fate_count", 0)) > 0
    ]
    lines = [
        f"# {canon.get('title') or comparison.get('title') or 'RPF 运行报告'}",
        "",
        "## 运行档案",
        "",
        f"- 运行来源：{comparison.get('output_dir') or comparison.get('run_id') or '-'}",
        f"- 运行 ID：{comparison.get('run_id', '-')}",
        f"- 案例：{comparison.get('scenario_id', '-')}",
        f"- 模式：{comparison.get('mode', '-')}",
        f"- 随机种子：{comparison.get('seed', '-')}",
        f"- 创建时间：{comparison.get('created_at', '-')}",
        "",
        "## 总览",
        "",
        f"- Tick 数：{comparison.get('tick_count', 0)}",
        f"- 事件数：{comparison.get('event_count', 0)}",
        f"- 当前关系阶段：{_zh(comparison.get('phase', '-'))}",
        f"- 信任：{_fmt_report(comparison.get('trust_score'))}",
        f"- 怨恨压力：{_fmt_report(comparison.get('resentment_score'))}",
        f"- 修复能力：{_fmt_report(comparison.get('repair_score'))}",
        f"- 关键转折数：{comparison.get('turning_point_count', 0)}",
        "",
        "## 案件账本",
        "",
        f"- 案件阶段：{_zh(case_ledger.get('case_phase', '-'))}",
        f"- 已知事实：{len(case_ledger.get('known_facts', []) or [])}",
        f"- 证物：{len(case_ledger.get('evidence_items', []) or [])}",
        f"- 证词：{len(case_ledger.get('testimonies', []) or [])}",
        f"- 矛盾：{len(case_ledger.get('contradictions', []) or [])}",
        f"- 未证实异常：{len(case_ledger.get('unverified_anomalies', []) or [])}",
        f"- 调查更新：{len(payload.get('inquiry', []) or [])}",
        "",
        "## 末端压力",
        "",
        f"- 物质紧迫：{_fmt_report(pressure.get('material_urgency'))}",
        f"- 冲突压力：{_fmt_report(pressure.get('conflict_pressure'))}",
        f"- 修复债：{_fmt_report(pressure.get('repair_debt'))}",
        f"- 承认压力：{_fmt_report(pressure.get('recognition_pressure'))}",
        f"- 记忆压力：{_fmt_report(pressure.get('memory_pressure'))}",
        "",
        "## 主导关系模式",
        "",
    ]
    top_rpps = summary.get("top_rpps", [])
    lines.extend(_report_count_rows(top_rpps) or ["- 暂无"])
    lines.extend(["", "## 主导组合吸引子", ""])
    lines.extend(_report_count_rows(summary.get("top_compositions", [])) or ["- 暂无"])
    lines.extend(["", "## 关键转折", ""])
    if turns:
        for frame in turns[-20:]:
            markers = []
            if frame.get("phase_changed"):
                markers.append(f"阶段={_zh(frame.get('phase'))}")
            if frame.get("recognition"):
                markers.append(f"承认={_zh(frame.get('recognition', {}).get('outcome'))}")
            if frame.get("memory_count"):
                markers.append(f"记忆重构={frame.get('memory_count')}")
            if frame.get("fate_count"):
                markers.append(f"命运转折={frame.get('fate_count')}")
            lines.append(f"- Tick {frame.get('tick')}（{_zh(frame.get('tick_type'))}，{' / '.join(markers)}）：{frame.get('summary', '')}")
    else:
        lines.append("- 暂无")
    lines.extend(
        [
            "",
            "## 输出文件",
            "",
            "- timeline.jsonl：底层事件流",
            "- derived_views.json：派生关系/人物视图",
            "- rendered_story_stream.md：持续渲染故事流，如果已生成",
            "- rendered_segments.json：分段渲染记录，如果已生成",
            "- run_report.md：本报告",
            "",
            "## 边界说明",
            "",
            "本报告由运行输出确定性生成，不调用 LLM，不新增剧情，不改变模拟状态。",
        ]
    )
    return "\n".join(lines).strip() + "\n"


def export_run_bundle(output_dir: Path) -> dict[str, Any]:
    output_dir = output_dir.resolve()
    if not (output_dir / "timeline_manifest.json").exists():
        raise ValueError("Current run does not contain a timeline manifest")
    report = build_run_report(output_dir)
    report_path = output_dir / "run_report.md"
    report_path.write_text(report, encoding="utf-8")
    case_ledger = build_viewer_payload(output_dir).get("case_ledger", {})
    (output_dir / "case_ledger.json").write_text(
        json.dumps(case_ledger, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    bundle_path = output_dir / f"{output_dir.name}_bundle.zip"
    files = _exportable_files(output_dir)
    with zipfile.ZipFile(bundle_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            if path.exists() and path.is_file():
                archive.write(path, arcname=path.relative_to(output_dir))
    return {
        "ok": True,
        "output": str(bundle_path),
        "file_count": len(files),
        "files": [str(path.relative_to(output_dir)) for path in files if path.exists()],
    }


def export_database_run_bundle(run_id: str, store: RunStore | None = None, export_dir: Path | None = None) -> dict[str, Any]:
    payload = build_viewer_payload_from_database(run_id, store=store)
    comparison = _comparison_summary_from_payload(payload, run_label=f"postgres:{run_id}", metadata={"run_id": run_id, "mode": "postgres"})
    report = build_run_report_from_payload(payload, comparison=comparison)
    export_dir = export_dir or (DEFAULT_EXPERIENCE_DIR / "exports")
    export_dir.mkdir(parents=True, exist_ok=True)
    safe_run_id = _safe_filename_part(run_id)
    bundle_path = export_dir / f"{safe_run_id}_bundle.zip"
    files = _database_export_files(payload, report)
    with zipfile.ZipFile(bundle_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, content in files.items():
            archive.writestr(name, content)
    return {
        "ok": True,
        "output": str(bundle_path),
        "file_count": len(files),
        "files": list(files),
    }


def _database_export_files(payload: dict[str, Any], report: str) -> dict[str, str]:
    trace_exports = {
        "scheduler_diagnostics.json": payload.get("scheduler", []),
        "inquiry_trace.json": payload.get("inquiry", []),
        "projection_trace.json": payload.get("projection", []),
        "affordance_trace.json": payload.get("affordance", []),
        "action_trace.json": payload.get("action", []),
        "expression_trace.json": payload.get("expression", []),
        "recognition_trace.json": payload.get("recognition", []),
        "fate_transition_trace.json": payload.get("fate", []),
        "frame_trace.json": payload.get("frame_definition", []),
        "account_trace.json": payload.get("account", []),
        "normativity_trace.json": payload.get("normativity", []),
        "relevance_trace.json": payload.get("relevance", []),
        "attention_trace.json": payload.get("attention", []),
        "opportunity_trace.json": payload.get("opportunity", []),
        "reversibility_trace.json": payload.get("reversibility", []),
        "position_trace.json": payload.get("position", []),
        "expectation_trace.json": payload.get("expectation", []),
        "memory_trace.json": payload.get("memory", []),
        "binding_trace.json": payload.get("binding", []),
        "common_ground_trace.json": payload.get("common_ground", []),
        "epistemic_trace.json": payload.get("epistemic", []),
        "environment_trace.json": payload.get("environment", []),
        "disposition_trace.json": payload.get("disposition", []),
        "relation_trace.json": payload.get("relation", []),
        "rpp_activation_trace.json": payload.get("rpp_activation", []),
        "rpp_dynamics_trace.json": payload.get("rpp_dynamics", []),
        "local_world_trace.json": payload.get("local_world", []),
        "location_selection_trace.json": payload.get("location_selection", []),
        "route_selection_trace.json": payload.get("route_selection", []),
        "audience_exposure_trace.json": payload.get("audience_exposure", []),
        "render_repetition_trace.json": payload.get("render_repetition", []),
    }
    files: dict[str, str] = {
        "run_report.md": report,
        "timeline_manifest.json": json.dumps(payload.get("manifest", {}), ensure_ascii=False, indent=2),
        "render_canon.json": json.dumps(payload.get("render_canon", {}), ensure_ascii=False, indent=2),
        "case_ledger.json": json.dumps(payload.get("case_ledger", {}), ensure_ascii=False, indent=2),
        "object_registry.json": json.dumps(payload.get("object_registry", {}), ensure_ascii=False, indent=2),
        "metrics.json": json.dumps(payload.get("metrics", {}), ensure_ascii=False, indent=2),
        "derived_views.json": json.dumps(payload.get("derived_views", {}), ensure_ascii=False, indent=2),
        "timeline.jsonl": "\n".join(json.dumps(event, ensure_ascii=False) for event in payload.get("timeline", [])) + "\n",
        "rendered_story_stream.md": payload.get("rendered_story_stream", ""),
        "rendered_segments.json": json.dumps(payload.get("rendered_segments", []), ensure_ascii=False, indent=2),
    }
    files.update({name: json.dumps(value, ensure_ascii=False, indent=2) for name, value in trace_exports.items()})
    return files


def _safe_filename_part(value: str) -> str:
    safe = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in value)
    return safe or "run"


def _exportable_files(output_dir: Path) -> list[Path]:
    preferred = [
        "run_metadata.json",
        "timeline_manifest.json",
        "run_report.md",
        "render_canon.json",
        "case_ledger.json",
        "object_registry.json",
        "effective_config.json",
        "metrics.json",
        "derived_views.json",
        "timeline.jsonl",
        "rendered_story.md",
        "rendered_story_llm.md",
        "rendered_story_stream.md",
        "rendered_segments.json",
        "render_repetition_trace.json",
        "scheduler_diagnostics.json",
        "inquiry_trace.json",
        "projection_trace.json",
        "affordance_trace.json",
        "action_trace.json",
        "expression_trace.json",
        "recognition_trace.json",
        "fate_transition_trace.json",
        "frame_trace.json",
        "account_trace.json",
        "normativity_trace.json",
        "relevance_trace.json",
        "attention_trace.json",
        "opportunity_trace.json",
        "reversibility_trace.json",
        "position_trace.json",
        "expectation_trace.json",
        "memory_trace.json",
        "binding_trace.json",
        "common_ground_trace.json",
        "epistemic_trace.json",
        "environment_trace.json",
        "disposition_trace.json",
        "relation_trace.json",
        "rpp_activation_trace.json",
        "rpp_dynamics_trace.json",
        "local_world_trace.json",
        "location_selection_trace.json",
        "route_selection_trace.json",
        "audience_exposure_trace.json",
        "irreversibility_report.json",
        "aggregation_traces.json",
    ]
    return [output_dir / name for name in preferred]


def build_story_frames(payload: dict[str, Any]) -> list[dict[str, Any]]:
    cast = payload.get("render_canon", {}).get("cast", {})
    scheduler = payload.get("scheduler", [])
    projection_by_tick = {item.get("tick"): item for item in payload.get("projection", [])}
    action_by_tick = {item.get("tick"): item.get("selected_action", {}) for item in payload.get("action", [])}
    expression_by_tick = {item.get("tick"): item.get("selected_expression", {}) for item in payload.get("expression", [])}
    recognition_by_tick = {item.get("tick"): item for item in payload.get("recognition", [])}
    inquiry_by_tick = {item.get("tick"): item for item in payload.get("inquiry", [])}
    viability_by_tick = {item.get("tick"): item for item in payload.get("viability", [])}
    frames_by_tick: dict[int, list[dict[str, Any]]] = {}
    for frame_update in payload.get("frame_definition", []):
        frames_by_tick.setdefault(int(frame_update.get("tick", 0)), []).append(frame_update)
    positions_by_tick: dict[int, list[dict[str, Any]]] = {}
    for position_update in payload.get("position", []):
        positions_by_tick.setdefault(int(position_update.get("tick", 0)), []).append(position_update)
    attention_by_tick: dict[int, list[dict[str, Any]]] = {}
    for attention_update in payload.get("attention", []):
        attention_by_tick.setdefault(int(attention_update.get("tick", 0)), []).append(attention_update)
    opportunity_by_tick: dict[int, list[dict[str, Any]]] = {}
    for opportunity_update in payload.get("opportunity", []):
        opportunity_by_tick.setdefault(int(opportunity_update.get("tick", 0)), []).append(opportunity_update)
    reversibility_by_tick: dict[int, list[dict[str, Any]]] = {}
    for reversibility_update in payload.get("reversibility", []):
        reversibility_by_tick.setdefault(int(reversibility_update.get("tick", 0)), []).append(reversibility_update)
    epistemic_by_tick: dict[int, list[dict[str, Any]]] = {}
    for epistemic_update in payload.get("epistemic", []):
        epistemic_by_tick.setdefault(int(epistemic_update.get("tick", 0)), []).append(epistemic_update)
    common_ground_by_tick = {
        int(item.get("tick", 0)): item
        for item in payload.get("common_ground", [])
    }
    daily_ecology_by_tick = {
        int(item.get("tick", 0)): item
        for item in payload.get("environment", [])
        if item.get("event_type") == "DailyEcologyEvent"
    }
    locality_by_tick = {
        int(item.get("tick", 0)): item
        for item in payload.get("location_selection", [])
    }
    memories_by_tick: dict[int, list[dict[str, Any]]] = {}
    for memory in payload.get("memory", []):
        memories_by_tick.setdefault(int(memory.get("tick", 0)), []).append(memory)
    fate_by_tick: dict[int, list[dict[str, Any]]] = {}
    for fate in payload.get("fate", []):
        fate_by_tick.setdefault(int(fate.get("tick", 0)), []).append(fate)
    previous_phase = None
    frames: list[dict[str, Any]] = []
    for tick in scheduler:
        tick_index = int(tick.get("tick_index", 0))
        tick_type = str(tick.get("selected_tick_type", "unknown"))
        projection = projection_by_tick.get(tick_index, {})
        action = action_by_tick.get(tick_index, {})
        expression = expression_by_tick.get(tick_index, {})
        recognition = recognition_by_tick.get(tick_index)
        inquiry = inquiry_by_tick.get(tick_index)
        viability = _viability_summary(viability_by_tick.get(tick_index, {}), tick)
        frame_definition = _frame_definition_summary(frames_by_tick.get(tick_index, []))
        position_field = _position_summary(positions_by_tick.get(tick_index, []))
        attention_drift = _attention_summary(attention_by_tick.get(tick_index, []))
        opportunity_cost = _opportunity_summary(opportunity_by_tick.get(tick_index, []))
        reversibility = _reversibility_summary(reversibility_by_tick.get(tick_index, []))
        epistemic_boundary = _epistemic_summary(epistemic_by_tick.get(tick_index, []))
        common_ground = _common_ground_summary(common_ground_by_tick.get(tick_index, {}))
        daily_ecology = daily_ecology_by_tick.get(tick_index, {})
        locality = _locality_summary(locality_by_tick.get(tick_index, {}))
        memories = memories_by_tick.get(tick_index, [])
        fates = fate_by_tick.get(tick_index, [])
        phase = projection.get("relationship_phase") or previous_phase or "unknown"
        phase_changed = previous_phase is not None and phase != previous_phase
        previous_phase = phase
        summary_parts = [_tick_sentence(tick_type, tick)]
        if action:
            summary_parts.append(_action_sentence(action))
        if expression:
            summary_parts.append(_expression_sentence(expression))
        if viability:
            summary_parts.append(_viability_sentence(viability))
        if frame_definition:
            summary_parts.append(_frame_definition_sentence(frame_definition))
        if position_field:
            summary_parts.append(_position_sentence(position_field))
        if attention_drift:
            summary_parts.append(_attention_sentence(attention_drift))
        if opportunity_cost:
            summary_parts.append(_opportunity_sentence(opportunity_cost))
        if reversibility:
            summary_parts.append(_reversibility_sentence(reversibility))
        if epistemic_boundary:
            summary_parts.append(_epistemic_sentence(epistemic_boundary))
        if common_ground:
            summary_parts.append(_common_ground_sentence(common_ground))
        if daily_ecology:
            summary_parts.append(_daily_ecology_sentence(daily_ecology))
        if locality:
            summary_parts.append(_locality_sentence(locality))
        if recognition:
            summary_parts.append(_recognition_sentence(recognition))
        if inquiry:
            summary_parts.append(_inquiry_sentence(inquiry))
        if fates:
            summary_parts.append(_fate_sentence(fates))
        if memories:
            summary_parts.append(_memory_sentence(memories))
            case_memory = _case_memory_sentence(memories)
            if case_memory:
                summary_parts.append(case_memory)
        frames.append(
            {
                "tick": tick_index,
                "tick_type": tick_type,
                "phase": phase,
                "phase_changed": phase_changed,
                "summary": " ".join(part for part in summary_parts if part),
                "participants": _participants(action, cast),
                "action": action,
                "expression": expression,
                "recognition": recognition or {},
                "inquiry": inquiry or {},
                "viability": viability,
                "frame_definition": frame_definition,
                "position_field": position_field,
                "attention_drift": attention_drift,
                "opportunity_cost": opportunity_cost,
                "reversibility": reversibility,
                "epistemic_boundary": epistemic_boundary,
                "common_ground": common_ground,
                "daily_ecology": daily_ecology,
                "locality": locality,
                "memory_count": len(memories),
                "case_memory_count": _case_memory_count(memories),
                "case_memory_focuses": _case_memory_focuses(memories),
                "fate_count": len(fates),
                "pressure": tick.get("input_factors", {}),
                "time_reason": tick.get("time_mapping_reason", ""),
                "simulated_time_delta_seconds": tick.get("simulated_time_delta_seconds", 0),
            }
        )
    return frames


def build_local_world_view(payload: dict[str, Any]) -> dict[str, Any]:
    local_world = payload.get("local_world", []) or []
    location_selection = payload.get("location_selection", []) or []
    route_selection = payload.get("route_selection", []) or []
    audience_exposure = payload.get("audience_exposure", []) or []
    timeline = payload.get("timeline", []) or []
    update = _last_trace(local_world, "LocalWorldUpdateEvent")
    latest_location = location_selection[-1] if location_selection else {}
    latest_route = route_selection[-1] if route_selection else {}
    latest_audience = audience_exposure[-1] if audience_exposure else {}
    latest_constraints = _last_trace(local_world, "LocalWorldConstraintIntegrationEvent")
    route_states = _latest_by_key(local_world, "RouteAccessEvent", "route_id")
    memory_sites = _latest_by_key(local_world, "MemorySiteActivationEvent", "site_id")
    resources = _latest_by_key(local_world, "ResourceStateEvent", "resource_id")
    return {
        "world_id": update.get("world_id"),
        "time_window": update.get("current_time_window"),
        "local_world_pressure": update.get("local_world_pressure"),
        "active_location": _active_location_view(latest_location, timeline),
        "route": _active_route_view(latest_route, timeline),
        "rhythms": [
            _with_source_links(
                {"rhythm_id": rhythm_id, "event_type": "RhythmActivationEvent", "tick": update.get("tick")},
                timeline,
                caused_by=update.get("caused_by_events", []),
            )
            for rhythm_id in update.get("active_rhythms", [])
        ],
        "audiences": _audience_views(latest_audience, timeline),
        "memory_sites": [_memory_site_view(item, timeline) for item in memory_sites.values()],
        "blocked_routes": [
            _route_state_view(item, timeline)
            for item in route_states.values()
            if item.get("access_after") in {"blocked", "dangerous", "costly", "exposed"}
        ],
        "resources": [_resource_view(item, timeline) for item in resources.values()],
        "local_constraints": _constraint_views(latest_constraints, timeline),
        "boundary_rules": update.get("boundary_rules", {}),
    }


def build_object_registry_view(payload: dict[str, Any]) -> dict[str, Any]:
    registry = ObjectRegistrySpec.model_validate(payload.get("object_registry") or {})
    location_id = (
        payload.get("local_world_view", {})
        .get("active_location", {})
        .get("location_id")
    )
    evidence_refs = _active_evidence_refs(payload)
    excerpt = registry.active_excerpt(location_id=location_id, evidence_refs=evidence_refs)
    excerpt["counts"] = {
        "world_objects": len(registry.world_objects),
        "record_objects": len(registry.record_objects),
        "evidence_objects": len(registry.evidence_objects),
        "message_objects": len(registry.message_objects),
        "access_tokens": len(registry.access_tokens),
        "object_links": len(registry.object_links),
    }
    excerpt["rules"] = {
        "durable_objects_require_registry_refs": True,
        "record_authority_is_not_record_existence": True,
        "evidence_access_is_not_evidence_truth": True,
    }
    return excerpt


def _active_evidence_refs(payload: dict[str, Any]) -> set[str]:
    refs: set[str] = set()
    location_id = (
        payload.get("local_world_view", {})
        .get("active_location", {})
        .get("location_id")
    )
    for item in payload.get("case_ledger", {}).get("evidence_items", []) or []:
        if location_id and item.get("location_id") == location_id and item.get("evidence_id"):
            refs.add(str(item["evidence_id"]))
    for frame in payload.get("story", []) or []:
        inquiry = frame.get("inquiry", {}) or {}
        for ref in inquiry.get("ledger_refs", []) or []:
            if isinstance(ref, str):
                refs.add(ref)
    return refs


def _active_location_view(selection: dict[str, Any], timeline: list[dict[str, Any]]) -> dict[str, Any]:
    if not selection:
        return {}
    top = (selection.get("candidate_scores") or [{}])[0]
    return _with_source_links(
        {
            "tick": selection.get("tick"),
            "event_type": selection.get("event_type", "LocationSelectionEvent"),
            "location_id": selection.get("selected_location"),
            "location_label": selection.get("selected_location_label") or selection.get("selected_location"),
            "scene_type": selection.get("scene_type"),
            "score": top.get("score"),
            "why_here": selection.get("why_here"),
            "why_not_elsewhere": selection.get("why_not_elsewhere"),
            "candidate_count": len(selection.get("candidate_scores") or []),
            "rejected_count": len(selection.get("rejected_locations") or []),
        },
        timeline,
        caused_by=selection.get("caused_by_events", []),
    )


def _active_route_view(selection: dict[str, Any], timeline: list[dict[str, Any]]) -> dict[str, Any]:
    if not selection:
        return {}
    route = selection.get("route_context") or {}
    return _with_source_links(
        {
            "tick": selection.get("tick"),
            "event_type": selection.get("event_type", "RouteSelectionEvent"),
            "route_id": route.get("route_id") or selection.get("selected_route"),
            "from_location": route.get("from_location"),
            "to_location": route.get("to_location"),
            "access_status": route.get("access_status"),
            "travel_time_minutes": route.get("travel_time_minutes"),
            "route_score": route.get("route_score"),
            "route_costs": route.get("route_costs", {}),
        },
        timeline,
        caused_by=selection.get("caused_by_events", []),
    )


def _audience_views(selection: dict[str, Any], timeline: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not selection:
        return []
    caused_by = selection.get("caused_by_events", [])
    return [
        _with_source_links(
            {
                "tick": selection.get("tick"),
                "event_type": "SceneAudienceContextEvent",
                "location_id": selection.get("location_id"),
                "audience_id": audience.get("audience_id"),
                "label": audience.get("label"),
                "exposure_state": audience.get("exposure_state"),
                "exposure_level": audience.get("exposure_level"),
                "rumor_risk": audience.get("rumor_risk"),
                "sanction_risk": audience.get("sanction_risk"),
            },
            timeline,
            caused_by=caused_by,
        )
        for audience in selection.get("possible_audiences", [])
    ]


def _memory_site_view(item: dict[str, Any], timeline: list[dict[str, Any]]) -> dict[str, Any]:
    return _with_source_links(
        {
            "tick": item.get("tick"),
            "event_type": item.get("event_type"),
            "site_id": item.get("site_id"),
            "location_id": item.get("location_id"),
            "salience": item.get("salience"),
            "avoidance_pressure": item.get("avoidance_pressure"),
            "attraction_pressure": item.get("attraction_pressure"),
            "affected_processes": item.get("affected_processes", []),
            "future_scene_biases": item.get("future_scene_biases", []),
        },
        timeline,
        caused_by=item.get("caused_by_events", []),
    )


def _route_state_view(item: dict[str, Any], timeline: list[dict[str, Any]]) -> dict[str, Any]:
    return _with_source_links(
        {
            "tick": item.get("tick"),
            "event_type": item.get("event_type"),
            "route_id": item.get("route_id"),
            "access_after": item.get("access_after"),
            "accessibility": item.get("accessibility"),
            "travel_time_after": item.get("travel_time_after"),
            "blocking_conditions": item.get("blocking_conditions", []),
            "affected_processes": item.get("affected_processes", []),
            "danger": item.get("danger"),
            "exposure": item.get("exposure"),
        },
        timeline,
        caused_by=item.get("caused_by_events", []),
    )


def _resource_view(item: dict[str, Any], timeline: list[dict[str, Any]]) -> dict[str, Any]:
    return _with_source_links(
        {
            "tick": item.get("tick"),
            "event_type": item.get("event_type"),
            "resource_id": item.get("resource_id"),
            "availability": item.get("availability"),
            "scarcity_level": item.get("scarcity_level"),
            "linked_capacities": item.get("linked_capacities", []),
            "conflict_potential": item.get("conflict_potential"),
        },
        timeline,
        caused_by=item.get("caused_by_events", []),
    )


def _constraint_views(trace: dict[str, Any], timeline: list[dict[str, Any]]) -> list[dict[str, Any]]:
    constraints = trace.get("constraints", []) if trace else []
    result = []
    for constraint in constraints:
        event_type = "CapacityDemandEvent" if constraint.get("demand_source") == "resource_scarcity" else "BlockedCapacityEvent"
        result.append(
            _with_source_links(
                {
                    "tick": trace.get("tick"),
                    "event_type": event_type,
                    **constraint,
                },
                timeline,
                caused_by=trace.get("caused_by_events", []),
            )
        )
    return result


def _with_source_links(item: dict[str, Any], timeline: list[dict[str, Any]], *, caused_by: list[str] | None = None) -> dict[str, Any]:
    caused_by = list(caused_by or item.get("caused_by_events") or [])
    source_event_ids = _matching_event_ids(item, timeline)
    linked = sorted({str(value) for value in [*source_event_ids, *caused_by] if value})
    item["source_event_ids"] = linked
    item["caused_by_events"] = caused_by
    return item


def _matching_event_ids(item: dict[str, Any], timeline: list[dict[str, Any]]) -> list[str]:
    event_type = item.get("event_type")
    tick = item.get("tick")
    identities = [
        "route_id",
        "location_id",
        "audience_id",
        "site_id",
        "resource_id",
        "capacity_id",
        "demand_source",
    ]
    matches = []
    for event in timeline:
        if event.get("event_type") != event_type:
            continue
        if tick is not None and event.get("tick") != tick:
            continue
        payload = event.get("payload") or {}
        if any(item.get(key) is not None and payload.get(key) == item.get(key) for key in identities):
            matches.append(str(event.get("event_id")))
    return matches


def _last_trace(rows: list[dict[str, Any]], event_type: str) -> dict[str, Any]:
    for row in reversed(rows):
        if row.get("event_type") == event_type:
            return row
    return {}


def _latest_by_key(rows: list[dict[str, Any]], event_type: str, key: str) -> dict[str, dict[str, Any]]:
    result = {}
    for row in rows:
        if row.get("event_type") == event_type and row.get(key):
            result[str(row.get(key))] = row
    return result


def _viability_summary(trace: dict[str, Any], scheduler_tick: dict[str, Any]) -> dict[str, Any]:
    if not trace and not scheduler_tick.get("viability_rhythm"):
        return {}
    widths = trace.get("affordance_widths", []) or []
    constraints = trace.get("constraints", []) or []
    requirements = trace.get("requirements", []) or []
    deformations = trace.get("deformations", []) or []
    rhythm = scheduler_tick.get("viability_rhythm", {}) or {}
    strongest_constraint = _max_by_metric(constraints, "intensity")
    strongest_requirement = _max_by_metric(requirements, "urgency")
    strongest_deformation = _max_by_metric(deformations, "deformation_distance")
    min_width = _min_metric(widths, "width", 1.0)
    direct_cost = _max_metric(widths, "direct_response_cost", 0.0)
    return {
        "viability_pressure": rhythm.get("viability_pressure", _max_metric(requirements, "urgency", 0.0)),
        "scene_readiness": rhythm.get("scene_readiness"),
        "affordance_width": min_width,
        "direct_response_cost": direct_cost,
        "dramatic_tension": trace.get("dramatic_tension", 0.0),
        "strongest_constraint": {
            "type": strongest_constraint.get("constraint_type"),
            "intensity": strongest_constraint.get("intensity"),
            "activation_condition": strongest_constraint.get("activation_condition"),
        } if strongest_constraint else {},
        "strongest_requirement": {
            "type": strongest_requirement.get("requirement_type"),
            "urgency": strongest_requirement.get("urgency"),
            "minimum_satisfaction_condition": strongest_requirement.get("minimum_satisfaction_condition"),
        } if strongest_requirement else {},
        "deformation": {
            "type": strongest_deformation.get("deformation_type"),
            "distance": strongest_deformation.get("deformation_distance"),
            "visible_form": strongest_deformation.get("visible_form"),
            "failure_modes": strongest_deformation.get("expected_recognition_failure_modes", []),
        } if strongest_deformation else {},
    }


def _max_metric(rows: list[dict[str, Any]], key: str, default: float) -> float:
    values = []
    for row in rows:
        try:
            values.append(float(row.get(key)))
        except (TypeError, ValueError):
            continue
    return max(values) if values else default


def _min_metric(rows: list[dict[str, Any]], key: str, default: float) -> float:
    values = []
    for row in rows:
        try:
            values.append(float(row.get(key)))
        except (TypeError, ValueError):
            continue
    return min(values) if values else default


def _max_by_metric(rows: list[dict[str, Any]], key: str) -> dict[str, Any]:
    candidates = []
    for row in rows:
        try:
            candidates.append((float(row.get(key)), row))
        except (TypeError, ValueError):
            continue
    if not candidates:
        return {}
    return max(candidates, key=lambda item: item[0])[1]


def _tick_sentence(tick_type: str, tick: dict[str, Any]) -> str:
    if tick_type == "latent":
        return "这一段没有直接交锋，压力在关系里继续累积。"
    if tick_type == "micro_interaction":
        return "一次短暂接触变得有意义。"
    if tick_type == "scene":
        return "压力结晶成一个可见场景。"
    return str(tick.get("time_mapping_reason", ""))


def _action_sentence(action: dict[str, Any]) -> str:
    mode = action.get("action_mode")
    signal = _zh(action.get("signal_type", "unknown"))
    if mode == "inhibited":
        return f"原本可能发生的行动被压住，只剩下 {signal}。"
    if mode == "substituted":
        return f"直接行动没有出现，关系改用 {signal} 作为替代。"
    if mode == "escalated":
        return f"行动升级为更明确的 {signal}。"
    return f"关系通过 {signal} 直接显现。"


def _expression_sentence(expression: dict[str, Any]) -> str:
    mode = expression.get("expression_mode")
    signal = _zh(expression.get("surface_signal", "unknown"))
    if mode == "silence":
        return f"这个行动最终表现为沉默或延迟，表层信号是 {signal}。"
    if mode == "public_performance":
        return f"它被包装成公开可接受的表现：{signal}。"
    if mode == "gesture":
        return f"它没有完全说出口，而是通过姿态显现：{signal}。"
    if mode == "timing_distortion":
        return f"它通过停顿和时机变形显现：{signal}。"
    if mode == "tonal_shift":
        return f"它通过语气变化显现：{signal}。"
    return f"它以相对直接的表达出现：{signal}。"


def _viability_sentence(viability: dict[str, Any]) -> str:
    pressure = float(viability.get("viability_pressure") or 0.0)
    width = float(viability.get("affordance_width") or 1.0)
    deformation = viability.get("deformation", {}) or {}
    constraint = viability.get("strongest_constraint", {}) or {}
    if deformation.get("type"):
        return f"底层上，可行动空间收窄到 {width:.2f}，表达发生 {_zh(deformation.get('type'))}。"
    if pressure >= 0.5:
        return f"底层可存续性压力升至 {pressure:.2f}，最强约束来自 {_zh(constraint.get('type', 'unknown'))}。"
    if width < 0.55:
        return f"可行动空间变窄到 {width:.2f}，直接回应成本上升。"
    return ""


def _frame_definition_summary(updates: list[dict[str, Any]]) -> dict[str, Any]:
    positive = [
        update
        for update in updates
        if float(update.get("delta") or 0.0) > 0.0
    ]
    if not positive:
        return {}
    strongest = max(positive, key=lambda item: float(item.get("new_value") or 0.0))
    return {
        "dominant_frame": strongest.get("frame_type"),
        "frame_label": _zh(strongest.get("frame_type")),
        "strength": strongest.get("new_value"),
        "reason": strongest.get("reason"),
        "evidence_event_types": strongest.get("evidence_event_types", []),
    }


def _frame_definition_sentence(frame_definition: dict[str, Any]) -> str:
    label = frame_definition.get("frame_label") or _zh(frame_definition.get("dominant_frame", "unknown"))
    try:
        strength = float(frame_definition.get("strength") or 0.0)
    except (TypeError, ValueError):
        strength = 0.0
    if strength >= 0.35:
        return f"这一轮互动被强烈定义为{label}。"
    return f"这一轮互动开始被定义为{label}。"


def _position_summary(updates: list[dict[str, Any]]) -> dict[str, Any]:
    positive = [
        update
        for update in updates
        if float(update.get("delta") or 0.0) > 0.0
    ]
    if not positive:
        return {}
    strongest = max(positive, key=lambda item: float(item.get("new_value") or 0.0))
    return {
        "process_id": strongest.get("process_id"),
        "dominant_position": strongest.get("position_type"),
        "position_label": _zh(strongest.get("position_type")),
        "strength": strongest.get("new_value"),
        "reason": strongest.get("reason"),
        "evidence_event_types": strongest.get("evidence_event_types", []),
    }


def _position_sentence(position_field: dict[str, Any]) -> str:
    label = position_field.get("position_label") or _zh(position_field.get("dominant_position", "unknown"))
    process_id = position_field.get("process_id", "某一方")
    try:
        strength = float(position_field.get("strength") or 0.0)
    except (TypeError, ValueError):
        strength = 0.0
    if strength >= 0.35:
        return f"关系把 {process_id} 明显推入{label}。"
    return f"关系开始把 {process_id} 推向{label}。"


def _attention_summary(updates: list[dict[str, Any]]) -> dict[str, Any]:
    if not updates:
        return {}
    strongest = max(updates, key=lambda item: float(item.get("drift_intensity") or 0.0))
    return {
        "process_id": strongest.get("process_id"),
        "dominant_focus": strongest.get("dominant_focus"),
        "focus_label": _zh(strongest.get("dominant_focus", "")),
        "previous_focus": strongest.get("previous_focus"),
        "drift_intensity": strongest.get("drift_intensity"),
        "focus_scores": strongest.get("focus_scores", {}),
        "reason": strongest.get("reason"),
    }


def _attention_sentence(attention: dict[str, Any]) -> str:
    if not attention:
        return ""
    process_id = attention.get("process_id", "某一方")
    label = attention.get("focus_label") or _zh(attention.get("dominant_focus", ""))
    intensity = _fmt_report(attention.get("drift_intensity"))
    return f"{process_id} 的注意力漂向{label}，漂移强度 {intensity}。"


def _opportunity_summary(updates: list[dict[str, Any]]) -> dict[str, Any]:
    if not updates:
        return {}
    strongest = max(updates, key=lambda item: float(item.get("intensity") or 0.0))
    return {
        "process_id": strongest.get("process_id"),
        "cost_type": strongest.get("cost_type"),
        "cost_label": _zh(strongest.get("cost_type", "")),
        "missed_window": strongest.get("missed_window"),
        "missed_window_label": _zh(strongest.get("missed_window", "")),
        "intensity": strongest.get("intensity"),
        "reversibility": strongest.get("reversibility"),
        "reason": strongest.get("reason"),
        "affected_fields": strongest.get("affected_fields", []),
    }


def _opportunity_sentence(opportunity: dict[str, Any]) -> str:
    label = opportunity.get("cost_label") or _zh(opportunity.get("cost_type", ""))
    window = opportunity.get("missed_window_label") or _zh(opportunity.get("missed_window", ""))
    intensity = _fmt_report(opportunity.get("intensity"))
    return f"这一步同时付出了{label}：错过{window}，强度 {intensity}。"


def _reversibility_summary(updates: list[dict[str, Any]]) -> dict[str, Any]:
    if not updates:
        return {}
    strongest = max(updates, key=lambda item: float(item.get("threshold_proximity") or 0.0))
    return {
        "process_id": strongest.get("process_id"),
        "action_id": strongest.get("action_id"),
        "threshold_state": strongest.get("threshold_state"),
        "threshold_label": _zh(strongest.get("threshold_state", "")),
        "reversibility_width": strongest.get("reversibility_width"),
        "threshold_proximity": strongest.get("threshold_proximity"),
        "recovery_route": strongest.get("recovery_route"),
        "recovery_route_label": _zh(strongest.get("recovery_route", "")),
        "lost_alternative": strongest.get("lost_alternative"),
        "consequence": strongest.get("consequence"),
        "affected_requirements": strongest.get("affected_requirements", []),
    }


def _reversibility_sentence(reversibility: dict[str, Any]) -> str:
    label = reversibility.get("threshold_label") or _zh(reversibility.get("threshold_state", ""))
    width = _fmt_report(reversibility.get("reversibility_width"))
    route = reversibility.get("recovery_route_label") or _zh(reversibility.get("recovery_route", ""))
    return f"行动可逆性进入{label}，剩余可逆宽度 {width}；修复路径变成{route}。"


def _epistemic_summary(updates: list[dict[str, Any]]) -> dict[str, Any]:
    if not updates:
        return {}
    strongest = max(updates, key=lambda item: float(item.get("pressure") or 0.0))
    return {
        "boundary_type": strongest.get("boundary_type"),
        "boundary_label": _zh(strongest.get("boundary_type", "")),
        "focus_id": strongest.get("focus_id"),
        "focus_label": strongest.get("focus_label"),
        "boundary_state": strongest.get("boundary_state"),
        "boundary_state_label": _zh(strongest.get("boundary_state", "")),
        "knownness_asymmetry": strongest.get("knownness_asymmetry"),
        "speakability_width": strongest.get("speakability_width"),
        "disclosure_risk": strongest.get("disclosure_risk"),
        "contamination_load": strongest.get("contamination_load"),
        "public_readability": strongest.get("public_readability"),
        "pressure": strongest.get("pressure"),
        "consequence": strongest.get("consequence"),
    }


def _epistemic_sentence(epistemic: dict[str, Any]) -> str:
    label = epistemic.get("boundary_label") or _zh(epistemic.get("boundary_type", ""))
    state = epistemic.get("boundary_state_label") or _zh(epistemic.get("boundary_state", ""))
    focus = epistemic.get("focus_label") or epistemic.get("focus_id") or "某个事实"
    speakability = _fmt_report(epistemic.get("speakability_width"))
    risk = _fmt_report(epistemic.get("disclosure_risk"))
    return f"信息边界形成{label}：{focus}处于{state}，可说宽度 {speakability}，披露风险 {risk}。"


def _common_ground_summary(update: dict[str, Any]) -> dict[str, Any]:
    if not update:
        return {}
    return {
        "state": update.get("state"),
        "state_label": _zh(update.get("state", "")),
        "mutual_legibility": update.get("mutual_legibility"),
        "interpretive_gap": update.get("interpretive_gap"),
        "shared_definition_width": update.get("shared_definition_width"),
        "repair_handle_width": update.get("repair_handle_width"),
        "dominant_frame": update.get("dominant_frame"),
        "dominant_frame_label": _zh(update.get("dominant_frame", "")),
        "contested_fact": update.get("contested_fact"),
        "consequence": update.get("consequence"),
    }


def _common_ground_sentence(common_ground: dict[str, Any]) -> str:
    state = common_ground.get("state_label") or _zh(common_ground.get("state", ""))
    legibility = _fmt_report(common_ground.get("mutual_legibility"))
    repair_width = _fmt_report(common_ground.get("repair_handle_width"))
    frame = common_ground.get("dominant_frame_label") or _zh(common_ground.get("dominant_frame", ""))
    contested = common_ground.get("contested_fact") or "当前事实"
    return f"共同现实变为{state}：围绕{contested}，互相可读性 {legibility}，修复抓手宽度 {repair_width}；主导框架是{frame}。"


def _daily_ecology_sentence(daily: dict[str, Any]) -> str:
    phase = _zh(daily.get("routine_phase", "waiting_time"))
    body = _fmt_report(daily.get("body_load"))
    tasks = _fmt_report(daily.get("unfinished_tasks"))
    waiting = _fmt_report(daily.get("waiting_pressure"))
    if daily.get("routine_phase") == "night_recovery":
        return f"日常时间进入{phase}，身体负荷 {body}，但等待压力仍有 {waiting}。"
    return f"日常惯性进入{phase}，未完成杂事 {tasks}，身体负荷 {body}，等待压力 {waiting}。"


def _locality_summary(selection: dict[str, Any]) -> dict[str, Any]:
    if not selection:
        return {}
    top_candidate = (selection.get("candidate_scores") or [{}])[0]
    return {
        "location_id": selection.get("selected_location"),
        "location_label": selection.get("selected_location_label") or selection.get("selected_location"),
        "scene_type": selection.get("scene_type"),
        "score": top_candidate.get("score"),
        "why_here": selection.get("why_here"),
        "why_not_elsewhere": selection.get("why_not_elsewhere"),
        "candidate_count": len(selection.get("candidate_scores") or []),
        "rejected_count": len(selection.get("rejected_locations") or []),
    }


def _locality_sentence(locality: dict[str, Any]) -> str:
    location = locality.get("location_label") or locality.get("location_id") or "某个地点"
    why = locality.get("why_here") or "本地世界约束使这里成为最强候选"
    return f"场景被本地世界限定在{location}：{why}。"


def _recognition_sentence(recognition: dict[str, Any]) -> str:
    outcome = recognition.get("outcome", "unknown")
    if outcome == "refused":
        return "承认请求被拒绝，修复债继续上升。"
    if outcome == "misunderstood":
        return "对方回应了错误层面，承认请求被误解。"
    if outcome == "postponed":
        return "承认被推迟，问题没有真正进入修复。"
    if outcome == "displaced":
        return "承认被转移成别的形式。"
    if outcome == "unspeakable":
        return "承认变得不可说。"
    if outcome == "partial":
        return "出现了部分承认，但仍有残余。"
    if outcome == "granted":
        return "承认被给出，修复暂时变得可能。"
    return ""


def _inquiry_sentence(inquiry: dict[str, Any]) -> str:
    label = inquiry.get("label") or inquiry.get("focus_id") or "案件线索"
    movement = inquiry.get("movement")
    state_after = inquiry.get("state_after", {}) or {}
    location = inquiry.get("location", {}) or {}
    strategy = inquiry.get("witness_strategy", {}) or {}
    location_label = location.get("location_label")
    location_text = f"在{location_label}" if location_label else ""
    progress = _fmt_report(state_after.get("progress"))
    contamination = _fmt_report(state_after.get("contamination"))
    strategy_text = ""
    if strategy:
        strategy_text = (
            f" 证人策略转为{_zh(strategy.get('strategy_id', ''))}"
            f"（保护 {_fmt_report(strategy.get('protective_value'))}，透露 {_fmt_report(strategy.get('disclosure_width'))}）。"
        )
    if movement == "evidence_review_contaminates_relation":
        return f"调查{location_text}推进到“{label}”，但证物污染也在上升（进展 {progress}，污染 {contamination}）。{strategy_text}"
    if movement == "testimony_probe_raises_retraction_pressure":
        return f"调查追问{location_text}触碰到“{label}”，证词可用性提高，同时撤回压力变大。{strategy_text}"
    if movement == "symbol_becomes_speakable_but_unstable":
        return f"“{label}”{location_text}被说出口，却仍不能成为稳定事实。{strategy_text}"
    return f"案件压力{location_text}沉积到“{label}”，它开始改变两人的可行动空间。{strategy_text}"


def _fate_sentence(fates: list[dict[str, Any]]) -> str:
    labels = "，".join(_zh(item.get("transition_id", "")) for item in fates)
    return f"关系跨过命运阈值：{labels}。"


def _memory_sentence(memories: list[dict[str, Any]]) -> str:
    owners = sorted({str(item.get("owner_process_id", "")) for item in memories if item.get("owner_process_id")})
    return f"这一步被重构进记忆，影响到 {'、'.join(owners)}。"


def _case_memory_count(memories: list[dict[str, Any]]) -> int:
    return sum(1 for item in memories if "case_memory_contamination" in (item.get("reconstruction_biases") or []))


def _case_memory_focuses(memories: list[dict[str, Any]]) -> list[str]:
    focuses: list[str] = []
    for item in memories:
        if "case_memory_contamination" not in (item.get("reconstruction_biases") or []):
            continue
        remembered_as = str(item.get("remembered_as", ""))
        parts = remembered_as.split(":")
        if len(parts) >= 4:
            focuses.append(parts[2])
    return sorted(set(focuses))


def _case_memory_sentence(memories: list[dict[str, Any]]) -> str:
    focuses = _case_memory_focuses(memories)
    if not focuses:
        return ""
    return f"案件线索进入人物记忆，焦点包括：{'、'.join(focuses)}。"


def _zh(value: Any) -> str:
    text = str(value)
    return ZH.get(text, text)


def _participants(action: dict[str, Any], cast: dict[str, Any]) -> dict[str, Any]:
    result = {}
    for role, key in (("source", "source_process"), ("target", "target_process")):
        pid = action.get(key)
        if pid:
            result[role] = _participant(pid, cast)
    return result


def _participant(pid: str, cast: dict[str, Any]) -> dict[str, Any]:
    if pid in cast:
        return {
            "process_id": pid,
            "name": cast[pid].get("name", pid),
            "pronoun": cast[pid].get("pronoun", ""),
        }
    if pid == "field":
        return {"process_id": pid, "name": "场域", "pronoun": ""}
    pieces = [piece for piece in pid.replace(",", "-").split("-") if piece]
    if len(pieces) > 1 and all(piece in cast for piece in pieces):
        return {
            "process_id": pid,
            "name": "、".join(cast[piece].get("name", piece) for piece in pieces),
            "pronoun": "",
        }
    return {"process_id": pid, "name": pid, "pronoun": ""}


def _read_render_canon(run_dir: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    direct = _read_json(run_dir / "render_canon.json", None)
    if isinstance(direct, dict):
        return direct
    scenario_path = manifest.get("scenario_path")
    if not scenario_path:
        return {}
    try:
        scenario = load_scenario(Path(scenario_path))
    except Exception:
        return {}
    canon = scenario.get("render_canon", {})
    return canon if isinstance(canon, dict) else {}


def _read_case_ledger(run_dir: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    direct = _read_json(run_dir / "case_ledger.json", None)
    if isinstance(direct, dict):
        return direct
    scenario_path = manifest.get("scenario_path")
    if not scenario_path:
        return {}
    try:
        scenario = load_scenario(Path(scenario_path))
    except Exception:
        return {}
    ledger = scenario.get("case_ledger", {})
    return ledger if isinstance(ledger, dict) else {}


def _top_counts(mapping: dict[str, Any], limit: int) -> list[dict[str, Any]]:
    items = sorted(mapping.items(), key=lambda item: float(item[1]), reverse=True)
    return [{"key": key, "value": value} for key, value in items[:limit]]


def _report_count_rows(rows: list[dict[str, Any]]) -> list[str]:
    return [f"- {_zh(item.get('key', '-'))}：{_fmt_report(item.get('value'))}" for item in rows]


def _fmt_report(value: Any) -> str:
    if value is None:
        return "-"
    if isinstance(value, (int, float)):
        return str(value) if isinstance(value, int) else f"{value:.3f}"
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return str(value)
    return f"{parsed:.3f}"


class ViewerServer(ThreadingHTTPServer):
    def __init__(self, server_address: tuple[str, int], output_dir: Path) -> None:
        self.output_dir = output_dir.resolve()
        self.current_run_id: str | None = None
        self.examples_dir = DEFAULT_EXAMPLES_DIR.resolve()
        self.experience_dir = DEFAULT_EXPERIENCE_DIR.resolve()
        self.session_lock = threading.Lock()
        self.session_stop = threading.Event()
        self.session_thread: threading.Thread | None = None
        self.session_status: dict[str, Any] = {
            "state": "idle",
            "message": "尚未开始持续模拟",
        }
        super().__init__(server_address, ViewerHandler)


class ViewerHandler(BaseHTTPRequestHandler):
    server: ViewerServer

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path in {"/healthz", "/api/health"}:
            self._send_json(_health_payload(self.server.output_dir, self.server.examples_dir))
            return
        if parsed.path == "/api/run":
            self._send_json(self._current_payload())
            return
        if parsed.path == "/api/scenarios":
            self._send_json(
                {
                    "current_output_dir": str(self.server.output_dir),
                    "scenarios": scenario_catalog(self.server.examples_dir),
                }
            )
            return
        if parsed.path == "/api/runs":
            self._send_json(
                {
                    "current_output_dir": str(self.server.output_dir),
                    "current_run_id": self.server.current_run_id,
                    "runs": run_catalog(self.server.experience_dir),
                }
            )
            return
        if parsed.path == "/api/simulate/status":
            self._send_json(self._session_status())
            return
        path = "index.html" if parsed.path in {"/", ""} else parsed.path.lstrip("/")
        target = (STATIC_DIR / path).resolve()
        try:
            target.relative_to(STATIC_DIR.resolve())
        except ValueError:
            self.send_error(404)
            return
        if not target.exists() or not target.is_file():
            self.send_error(404)
            return
        self._send_file(target)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/render":
            self._handle_render()
            return
        if parsed.path == "/api/report":
            self._handle_report()
            return
        if parsed.path == "/api/export":
            self._handle_export()
            return
        if parsed.path == "/api/canon":
            self._handle_canon_save()
            return
        if parsed.path == "/api/simulate/start":
            self._handle_simulate_start()
            return
        if parsed.path == "/api/scenarios/select":
            self._handle_scenario_select()
            return
        if parsed.path == "/api/scenarios/create":
            self._handle_scenario_create()
            return
        if parsed.path == "/api/runs/open":
            self._handle_run_open()
            return
        if parsed.path == "/api/runs/compare":
            self._handle_run_compare()
            return
        if parsed.path == "/api/simulate/stop":
            self.server.session_stop.set()
            with self.server.session_lock:
                if self.server.session_status.get("state") == "running":
                    self.server.session_status["state"] = "stopping"
                    self.server.session_status["message"] = "正在停止..."
            self._send_json(self._session_status())
            return
        self.send_error(404)

    def _handle_scenario_select(self) -> None:
        try:
            request = self._read_json_body()
            with self.server.session_lock:
                running = self.server.session_thread and self.server.session_thread.is_alive()
                if running:
                    self._send_json({"error": "持续模拟运行中，停止后才能切换案例"}, status=409)
                    return
            scenario_path = _resolve_scenario_path(request.get("scenario_path") or request.get("scenario_id"), self.server.examples_dir)
            scenario = load_scenario(scenario_path)
            seed = int(request.get("seed") or 42)
            steps = int(request.get("bootstrap_steps") or 12)
            output_dir = _new_run_dir(self.server.experience_dir, str(scenario["id"]), seed=seed, mode="preview")
            sim = Simulator.from_scenario(scenario, scenario_path, seed=seed)
            sim.run(steps=max(1, steps), output_dir=output_dir)
            _write_run_metadata(
                output_dir,
                scenario_id=str(scenario["id"]),
                scenario_path=scenario_path,
                seed=seed,
                mode="preview",
                title=sim.render_canon.get("title") or scenario.get("name", str(scenario["id"])),
            )
            with self.server.session_lock:
                self.server.output_dir = output_dir.resolve()
                self.server.current_run_id = None
                self.server.session_stop.clear()
                self.server.session_status = {
                    "state": "idle",
                    "message": "案例已载入，可以开始持续模拟",
                    "output_dir": str(self.server.output_dir),
                    "tick": steps,
                    "render_mode": "none",
                    "last_render_output": None,
                    "last_render_error": None,
                }
            self._send_json({"ok": True, "output_dir": str(self.server.output_dir), "payload": build_viewer_payload(self.server.output_dir)})
        except Exception as exc:
            self._send_json({"error": str(exc)}, status=500)

    def _handle_scenario_create(self) -> None:
        try:
            request = self._read_json_body()
            with self.server.session_lock:
                running = self.server.session_thread and self.server.session_thread.is_alive()
                if running:
                    self._send_json({"error": "持续模拟运行中，停止后才能创建案例"}, status=409)
                    return
            scenario = _build_custom_scenario(request)
            scenario_path = _write_custom_scenario(self.server.examples_dir, scenario)
            seed = int(request.get("seed") or 42)
            steps = int(request.get("bootstrap_steps") or 12)
            output_dir = _new_run_dir(self.server.experience_dir, str(scenario["id"]), seed=seed, mode="custom_preview")
            sim = Simulator.from_scenario(scenario, scenario_path, seed=seed)
            sim.run(steps=max(1, steps), output_dir=output_dir)
            _write_run_metadata(
                output_dir,
                scenario_id=str(scenario["id"]),
                scenario_path=scenario_path,
                seed=seed,
                mode="custom_preview",
                title=sim.render_canon.get("title") or scenario.get("name", str(scenario["id"])),
            )
            with self.server.session_lock:
                self.server.output_dir = output_dir.resolve()
                self.server.current_run_id = None
                self.server.session_stop.clear()
                self.server.session_status = {
                    "state": "idle",
                    "message": "自定义案例已创建，可以开始持续模拟",
                    "output_dir": str(self.server.output_dir),
                    "tick": steps,
                    "render_mode": "none",
                    "last_render_output": None,
                    "last_render_error": None,
                }
            self._send_json(
                {
                    "ok": True,
                    "scenario_path": str(scenario_path),
                    "scenario": scenario,
                    "output_dir": str(self.server.output_dir),
                    "payload": build_viewer_payload(self.server.output_dir),
                    "scenarios": scenario_catalog(self.server.examples_dir),
                }
            )
        except Exception as exc:
            self._send_json({"error": str(exc)}, status=400)

    def _handle_run_open(self) -> None:
        try:
            request = self._read_json_body()
            run_id = str(request.get("run_id") or "").strip()
            output_dir = None if run_id else _resolve_run_dir(request.get("output_dir"), self.server.experience_dir)
            with self.server.session_lock:
                running = self.server.session_thread and self.server.session_thread.is_alive()
                if running:
                    self._send_json({"error": "持续模拟运行中，停止后才能打开历史运行"}, status=409)
                    return
                if run_id:
                    self.server.current_run_id = run_id
                else:
                    self.server.current_run_id = None
                    self.server.output_dir = output_dir.resolve()  # type: ignore[union-attr]
                self.server.session_status = {
                    "state": "idle",
                    "message": "已打开数据库运行" if run_id else "已打开历史运行",
                    "output_dir": str(self.server.output_dir),
                    "run_id": run_id or None,
                    "render_mode": "none",
                    "last_render_output": None,
                    "last_render_error": None,
                }
            payload = build_viewer_payload_from_database(run_id) if run_id else build_viewer_payload(self.server.output_dir)
            self._send_json({"ok": True, "output_dir": str(self.server.output_dir), "run_id": run_id or None, "payload": payload})
        except Exception as exc:
            self._send_json({"error": str(exc)}, status=400)

    def _handle_run_compare(self) -> None:
        try:
            request = self._read_json_body()
            other_dir = _resolve_run_dir(request.get("output_dir"), self.server.experience_dir)
            current = _comparison_summary(self.server.output_dir)
            other = _comparison_summary(other_dir)
            self._send_json(
                {
                    "current": current,
                    "other": other,
                    "delta": _comparison_delta(current, other),
                }
            )
        except Exception as exc:
            self._send_json({"error": str(exc)}, status=400)

    def _handle_canon_save(self) -> None:
        try:
            request = self._read_json_body()
            canon = _normalize_render_canon(request.get("render_canon"))
            target = self.server.output_dir / "render_canon.json"
            target.write_text(json.dumps(canon, ensure_ascii=False, indent=2), encoding="utf-8")
            self._send_json({"ok": True, "render_canon": canon, "output": str(target)})
        except Exception as exc:
            self._send_json({"error": str(exc)}, status=400)

    def _handle_render(self) -> None:
        try:
            request = self._read_json_body()
            from rpf.llm.renderer import render_output

            result = render_output(
                self.server.output_dir,
                use_llm=bool(request.get("use_llm", True)),
                provider=request.get("provider") or None,
                model=request.get("model") or None,
                base_url=request.get("base_url") or None,
                api_key=request.get("api_key") or None,
                thinking=request.get("thinking") or None,
                reasoning_effort=request.get("reasoning_effort") or None,
                max_frames=_positive_int(request.get("max_frames")),
            )
            output_path = Path(result["output"])
            self._send_json({
                **result,
                "text": output_path.read_text(encoding="utf-8") if output_path.exists() else "",
            })
        except Exception as exc:
            self._send_json({"error": str(exc)}, status=500)

    def _handle_report(self) -> None:
        try:
            if self.server.current_run_id:
                report = build_run_report_from_database(self.server.current_run_id)
                output = DEFAULT_EXPERIENCE_DIR / "exports" / f"{_safe_filename_part(self.server.current_run_id)}_run_report.md"
                output.parent.mkdir(parents=True, exist_ok=True)
                output.write_text(report, encoding="utf-8")
            else:
                report = build_run_report(self.server.output_dir)
                output = self.server.output_dir / "run_report.md"
                output.write_text(report, encoding="utf-8")
            self._send_json({"ok": True, "output": str(output), "text": report})
        except Exception as exc:
            self._send_json({"error": str(exc)}, status=500)

    def _handle_export(self) -> None:
        try:
            result = export_database_run_bundle(self.server.current_run_id) if self.server.current_run_id else export_run_bundle(self.server.output_dir)
            self._send_json(result)
        except Exception as exc:
            self._send_json({"error": str(exc)}, status=500)

    def _handle_simulate_start(self) -> None:
        try:
            request = self._read_json_body()
            with self.server.session_lock:
                running = self.server.session_thread and self.server.session_thread.is_alive()
                if running:
                    self._send_json({"error": "已有持续模拟正在运行"}, status=409)
                    return
                self.server.session_stop.clear()
                scenario_path = _scenario_path_for_output(self.server.output_dir)
                scenario = load_scenario(scenario_path)
                seed = int(request.get("seed") or _manifest_seed(self.server.output_dir) or 42)
                render_canon = _read_render_canon(self.server.output_dir, _read_json(self.server.output_dir / "timeline_manifest.json", {}))
                if render_canon:
                    scenario["render_canon"] = render_canon
                output_dir = _new_run_dir(self.server.experience_dir, str(scenario["id"]), seed=seed, mode="continuous")
                request = {
                    **request,
                    "seed": seed,
                    "_scenario_path": str(scenario_path),
                    "_scenario_id": str(scenario["id"]),
                    "_render_canon": render_canon,
                    "_run_title": render_canon.get("title") or scenario.get("name", str(scenario["id"])),
                }
                self.server.output_dir = output_dir.resolve()
                self.server.current_run_id = None
                self.server.session_status = _initial_session_status(request, self.server.output_dir)
            thread = threading.Thread(
                target=_run_session,
                args=(self.server, request),
                daemon=True,
            )
            self.server.session_thread = thread
            thread.start()
            self._send_json(self._session_status())
        except Exception as exc:
            self._send_json({"error": str(exc)}, status=500)

    def _session_status(self) -> dict[str, Any]:
        with self.server.session_lock:
            return dict(self.server.session_status)

    def _current_payload(self) -> dict[str, Any]:
        if self.server.current_run_id:
            return build_viewer_payload_from_database(self.server.current_run_id)
        return build_viewer_payload(self.server.output_dir)

    def log_message(self, format: str, *args: Any) -> None:
        return

    def _read_json_body(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0") or "0")
        if length <= 0:
            return {}
        data = self.rfile.read(length).decode("utf-8")
        parsed = json.loads(data)
        if not isinstance(parsed, dict):
            raise ValueError("Request body must be a JSON object")
        return parsed

    def _send_json(self, payload: dict[str, Any], status: int = 200) -> None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _send_file(self, path: Path) -> None:
        data = path.read_bytes()
        content_type = mimetypes.guess_type(str(path))[0] or "application/octet-stream"
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def serve_viewer(output_dir: Path, host: str, port: int) -> str:
    output_dir = _ensure_initial_output(output_dir)
    server = ViewerServer((host, port), output_dir)
    url = f"http://{host}:{server.server_port}"
    print(f"RPF viewer: {url}")
    print(f"Run output: {output_dir.resolve()}")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return url


def _positive_int(value: Any) -> int | None:
    if value in {None, ""}:
        return None
    parsed = int(value)
    return parsed if parsed > 0 else None


def _initial_session_status(request: dict[str, Any], output_dir: Path) -> dict[str, Any]:
    target_seconds = _duration_seconds(request)
    return {
        "state": "running",
        "message": "真实时间持续模拟已启动",
        "output_dir": str(output_dir),
        "target_seconds": target_seconds,
        "elapsed_seconds": 0,
        "tick": 0,
        "render_mode": request.get("render_mode", "deterministic"),
        "last_render_output": None,
        "last_render_error": None,
    }


def _run_session(server: ViewerServer, request: dict[str, Any]) -> None:
    from rpf.engine.simulator import Simulator
    from rpf.llm.segments import next_render_segment, render_and_append_segment

    try:
        scenario_path = Path(request.get("_scenario_path") or _scenario_path_for_output(server.output_dir))
        scenario = load_scenario(scenario_path)
        if isinstance(request.get("_render_canon"), dict) and request["_render_canon"]:
            scenario["render_canon"] = request["_render_canon"]
        seed = int(request.get("seed") or _manifest_seed(server.output_dir) or 42)
        target_seconds = _duration_seconds(request)
        tick_interval_seconds = float(request.get("tick_interval_seconds") or 30)
        write_interval = int(request.get("write_interval_ticks") or 1)
        max_steps = int(request.get("max_steps") or 10000)
        render_mode = str(request.get("render_mode") or "deterministic")
        segment_policy = {
            "micro_count": int(request.get("segment_micro_count") or 3),
            "latent_seconds": int(float(request.get("segment_latent_hours") or 6) * 60 * 60),
            "min_ticks": int(request.get("segment_min_ticks") or 3),
            "max_ticks": int(request.get("segment_max_ticks") or request.get("render_every_ticks") or 8),
            "max_seconds": int(float(request.get("segment_max_days") or 1) * 24 * 60 * 60),
        }

        sim = Simulator.from_scenario(scenario, scenario_path, seed=seed)

        def on_update(update: dict[str, Any]) -> None:
            with server.session_lock:
                server.session_status.update(
                    {
                        "state": "running",
                        "message": "持续模拟中",
                        "elapsed_seconds": update.get("elapsed_seconds", server.session_status.get("elapsed_seconds", 0)),
                        "target_seconds": update.get("target_seconds", target_seconds),
                        "tick": update.get("tick", server.session_status.get("tick", 0)),
                        "event_count": update.get("metrics", {}).get("event_count"),
                        "render_policy": segment_policy,
                    }
                )
            if render_mode == "none":
                return
            try:
                segment = next_render_segment(
                    server.output_dir,
                    policy=segment_policy,
                    force=bool(update.get("completed")),
                )
                if not segment:
                    return
                result = render_and_append_segment(
                    server.output_dir,
                    segment,
                    use_llm=render_mode == "llm",
                    provider="deepseek" if render_mode == "llm" else None,
                    model=request.get("model") or None,
                    api_key=request.get("api_key") or None,
                    thinking=request.get("thinking") or None,
                    reasoning_effort=request.get("reasoning_effort") or None,
                    run_id=update.get("run_id"),
                )
                with server.session_lock:
                    server.session_status["last_render_output"] = result.get("output")
                    server.session_status["last_render_text"] = result.get("segment_text") or result.get("text", "")
                    server.session_status["last_render_segment"] = {
                        "segment_id": result.get("segment_id"),
                        "tick_start": result.get("tick_start"),
                        "tick_end": result.get("tick_end"),
                        "boundary_reason": result.get("boundary_reason"),
                        "segment_count": result.get("segment_count"),
                    }
                    server.session_status["last_render_error"] = None
            except Exception as exc:
                with server.session_lock:
                    server.session_status["last_render_error"] = str(exc)

        result = sim.run_for_wall_clock(
            duration_seconds=target_seconds,
            output_dir=server.output_dir,
            tick_interval_seconds=tick_interval_seconds,
            max_steps=max_steps,
            write_interval_ticks=write_interval,
            on_update=on_update,
            should_stop=server.session_stop.is_set,
        )
        _write_run_metadata(
            server.output_dir,
            scenario_id=str(request.get("_scenario_id") or scenario.get("id", scenario_path.stem)),
            scenario_path=scenario_path,
            seed=seed,
            mode="continuous",
            title=str(request.get("_run_title") or scenario.get("name", scenario.get("id", scenario_path.stem))),
        )
        with server.session_lock:
            stopped = server.session_stop.is_set()
            server.session_status.update(
                {
                    "state": "stopped" if stopped else "completed",
                    "message": "已停止" if stopped else "持续模拟已完成",
                    "elapsed_seconds": result.get("elapsed_seconds"),
                    "target_seconds": result.get("target_seconds"),
                    "tick": result.get("tick"),
                    "event_count": result.get("metrics", {}).get("event_count"),
                    "final_state_hash": result.get("final_state_hash"),
                }
            )
    except Exception as exc:
        with server.session_lock:
            server.session_status.update({"state": "error", "message": str(exc)})


def _duration_seconds(request: dict[str, Any]) -> int:
    value = float(request.get("duration_value") or 1)
    unit = str(request.get("duration_unit") or "hours")
    multipliers = {
        "minutes": 60,
        "hours": 60 * 60,
        "days": 24 * 60 * 60,
    }
    if unit not in multipliers:
        raise ValueError(f"Unsupported duration unit: {unit}")
    seconds = int(value * multipliers[unit])
    if seconds <= 0:
        raise ValueError("Duration must be positive")
    return seconds


def _scenario_path_for_output(output_dir: Path) -> Path:
    manifest = _read_json(output_dir / "timeline_manifest.json", {})
    scenario_path = manifest.get("scenario_path")
    if not scenario_path:
        raise ValueError("Cannot find scenario_path in timeline_manifest.json")
    return Path(scenario_path)


def _manifest_seed(output_dir: Path) -> int | None:
    manifest = _read_json(output_dir / "timeline_manifest.json", {})
    seed = manifest.get("seed")
    return int(seed) if seed is not None else None


def _resolve_scenario_path(value: Any, examples_dir: Path) -> Path:
    text = str(value or "").strip()
    if not text:
        raise ValueError("Missing scenario id or path")
    examples_root = examples_dir.resolve()
    candidate = Path(text)
    if candidate.exists():
        resolved = candidate.resolve()
        try:
            resolved.relative_to(examples_root)
        except ValueError as exc:
            raise ValueError("Scenario path must stay under the examples directory") from exc
        return resolved
    for item in scenario_catalog(examples_dir):
        if item["id"] == text or item["path"] == text:
            return Path(item["path"])
    raise ValueError(f"Unknown scenario: {text}")


def _build_custom_scenario(request: dict[str, Any]) -> dict[str, Any]:
    title = str(request.get("title") or "").strip()
    if not title:
        raise ValueError("案例标题不能为空")
    scenario_id = _slugify(str(request.get("scenario_id") or title))
    p1_name = str(request.get("p1_name") or "甲").strip()
    p2_name = str(request.get("p2_name") or "乙").strip()
    setting_place = str(request.get("place") or "未指定场域").strip()
    binding_label = str(request.get("binding_label") or "共同处境绑定").strip()
    recognition_label = str(request.get("recognition_label") or "未被承认的事实").strip()
    material_urgency_value = _bounded_float(request.get("material_urgency"), 0.45)
    public_pressure_value = _bounded_float(request.get("public_pressure"), 0.35)
    unrecognized_value = _bounded_float(request.get("unrecognized_contribution"), 0.62)
    recognition_pressure_value = _bounded_float(request.get("recognition_pressure"), 0.55)
    conflict_value = _bounded_float(request.get("conflict_pressure"), 0.08)
    repair_debt_value = _bounded_float(request.get("repair_debt"), 0.05)
    binding_strength = _bounded_float(request.get("binding_strength"), 0.82)
    scenario = {
        "id": scenario_id,
        "name": title,
        "description": str(request.get("description") or f"网页创建的 RPF 双人关系模拟案例：{title}").strip(),
        "render_canon": {
            "title": title,
            "setting": {
                "place": setting_place,
                "period": str(request.get("period") or "当代").strip(),
                "atmosphere": str(request.get("atmosphere") or "克制、具体、关系压力持续存在").strip(),
                "material_objects": _lines(request.get("material_objects")) or ["账单", "手机消息", "门口"],
            },
            "cast": {
                "p1": {
                    "name": p1_name,
                    "gender": str(request.get("p1_gender") or "未指定").strip(),
                    "pronoun": str(request.get("p1_pronoun") or "").strip(),
                    "age_band": str(request.get("p1_age_band") or "未指定").strip(),
                    "surface_role": str(request.get("p1_role") or "更常承担或索取承认的一方").strip(),
                    "speech_style": str(request.get("p1_speech_style") or "克制，倾向间接表达").strip(),
                    "allowed_interiority": "只允许从行为、停顿、语气和选择中推断，不允许直接写内心独白",
                },
                "p2": {
                    "name": p2_name,
                    "gender": str(request.get("p2_gender") or "未指定").strip(),
                    "pronoun": str(request.get("p2_pronoun") or "").strip(),
                    "age_band": str(request.get("p2_age_band") or "未指定").strip(),
                    "surface_role": str(request.get("p2_role") or "更常回避确认或承认的一方").strip(),
                    "speech_style": str(request.get("p2_speech_style") or "解释多于承认，倾向拖延或转移").strip(),
                    "allowed_interiority": "只允许写可观察到的迟疑、回避和言语选择",
                },
            },
            "narration": {
                "language": "中文",
                "tense": "过去时",
                "perspective": str(request.get("perspective") or "第三人称限制视角").strip(),
                "style": str(request.get("style") or "克制的现实主义文学").strip(),
                "interiority_level": str(request.get("interiority_level") or "低").strip(),
                "metaphor_level": str(request.get("metaphor_level") or "低到中").strip(),
                "sentence_rhythm": str(request.get("sentence_rhythm") or "短句与中等长度句子交替").strip(),
                "forbidden": _lines(request.get("forbidden")) or [
                    "新增亲属关系",
                    "新增职业",
                    "新增外部地点",
                    "新增童年回忆",
                    "新增恋爱或婚姻状态",
                    "新增未来预告",
                    "直接宣布固定人格本质",
                ],
            },
        },
        "field_state": {
            "material_pressures": {"material_urgency": material_urgency_value},
            "spatial_constraints": {_slugify(setting_place): 0.72},
            "audience_pressure": {"relevant_others": public_pressure_value},
            "enacted_micro_worlds": [_slugify(setting_place), "message_delay"],
        },
        "relation_metrics": {
            "unrecognized_contribution": unrecognized_value,
            "recognition_pursuit_pressure": recognition_pressure_value,
            "public_private_gap": _bounded_float(request.get("public_private_gap"), 0.32),
            "care_dependency": _bounded_float(request.get("care_dependency"), 0.25),
            "double_bind_pressure": _bounded_float(request.get("double_bind_pressure"), 0.2),
            "face_risk_pressure": public_pressure_value,
            "conflict_pressure": conflict_value,
            "repair_debt": repair_debt_value,
            "operative_label_count": 0.0,
            "repair_debt_growth": _bounded_float(request.get("repair_debt_growth"), 0.55),
            "irreversibility_threshold": _bounded_float(request.get("irreversibility_threshold"), 0.78),
            "locked_in_repair_threshold": 0.58,
            "cold_war_repair_threshold": 0.35,
        },
        "processes": {
            "p1": {
                "display_name": p1_name,
                "fatigue": _bounded_float(request.get("p1_fatigue"), 0.58),
                "speech_inhibition": {
                    "direct_need": _bounded_float(request.get("p1_direct_need_inhibition"), 0.68),
                    "anger": _bounded_float(request.get("p1_anger_inhibition"), 0.58),
                },
                "threat_sensitivity": {
                    "being_used": _bounded_float(request.get("p1_being_used_sensitivity"), 0.72),
                    "being_ignored": _bounded_float(request.get("p1_being_ignored_sensitivity"), 0.68),
                },
                "relevance_triggers": {
                    "unacknowledged_help": 0.82,
                    "delayed_reply": 0.58,
                },
            },
            "p2": {
                "display_name": p2_name,
                "fatigue": _bounded_float(request.get("p2_fatigue"), 0.52),
                "speech_inhibition": {
                    "apology": _bounded_float(request.get("p2_apology_inhibition"), 0.72),
                    "dependency_admission": _bounded_float(request.get("p2_dependency_inhibition"), 0.62),
                    "direct_need": _bounded_float(request.get("p2_direct_need_inhibition"), 0.42),
                },
                "threat_sensitivity": {
                    "being_controlled": _bounded_float(request.get("p2_being_controlled_sensitivity"), 0.72),
                },
                "relevance_triggers": {
                    "repeated_questions": 0.74,
                    "delayed_reply": 0.45,
                },
            },
        },
        "bindings": [
            {
                "binding_id": _slugify(binding_label),
                "binding_type": str(request.get("binding_type") or "recognition").strip(),
                "process_ids": ["p1", "p2"],
                "strength": binding_strength,
                "exit_cost": {
                    "p1": _bounded_float(request.get("p1_exit_cost"), 0.72),
                    "p2": _bounded_float(request.get("p2_exit_cost"), 0.56),
                },
            },
            {
                "binding_id": _slugify(recognition_label),
                "binding_type": "recognition",
                "process_ids": ["p1", "p2"],
                "strength": _bounded_float(request.get("recognition_binding_strength"), 0.72),
                "exit_cost": {
                    "p1": _bounded_float(request.get("p1_recognition_exit_cost"), 0.68),
                    "p2": _bounded_float(request.get("p2_recognition_exit_cost"), 0.42),
                },
            },
        ],
        "recognition_demands": [
            {
                "demand_id": "rec_primary_claim",
                "holder_process_id": "p1",
                "demanded_from": "p2",
                "recognition_type": "admit_what_happened",
                "explicitness": _bounded_float(request.get("recognition_explicitness"), 0.2),
                "vulnerability_cost": _bounded_float(request.get("recognition_vulnerability_cost"), 0.76),
                "threat_if_denied": _bounded_float(request.get("recognition_threat_if_denied"), 0.84),
                "identity_dependency": _bounded_float(request.get("recognition_identity_dependency"), 0.65),
                "current_pressure": recognition_pressure_value,
            }
        ],
    }
    return scenario


def _write_custom_scenario(examples_dir: Path, scenario: dict[str, Any]) -> Path:
    examples_dir.mkdir(parents=True, exist_ok=True)
    base = examples_dir / f"custom_{scenario['id']}.yaml"
    path = base
    if path.exists():
        path = examples_dir / f"custom_{scenario['id']}_{time.strftime('%Y%m%d_%H%M%S')}.yaml"
        scenario["id"] = path.stem.removeprefix("custom_")
    path.write_text(
        yaml.safe_dump(scenario, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    return path.resolve()


def _slugify(value: str) -> str:
    text = "".join(ch.lower() if ch.isalnum() else "_" for ch in str(value).strip())
    pieces = [piece for piece in text.split("_") if piece]
    return "_".join(pieces)[:80] or "custom_scenario"


def _bounded_float(value: Any, default: float) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        parsed = default
    return max(0.0, min(1.0, parsed))


def _lines(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return [line.strip() for line in str(value or "").splitlines() if line.strip()]


def _resolve_run_dir(value: Any, experience_dir: Path) -> Path:
    text = str(value or "").strip()
    if not text:
        raise ValueError("Missing output_dir")
    root = experience_dir.resolve()
    resolved = Path(text).resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ValueError("Run path must stay under the experience directory") from exc
    if not (resolved / "timeline_manifest.json").exists():
        raise ValueError("Selected run does not contain a timeline manifest")
    return resolved


def _comparison_summary(output_dir: Path) -> dict[str, Any]:
    payload = build_viewer_payload(output_dir)
    metadata = _read_json(output_dir / "run_metadata.json", {})
    return _comparison_summary_from_payload(payload, run_label=str(output_dir.resolve()), metadata=metadata)


def _comparison_summary_from_payload(payload: dict[str, Any], *, run_label: str, metadata: dict[str, Any]) -> dict[str, Any]:
    story = payload.get("story", [])
    last_frame = story[-1] if story else {}
    pressure = last_frame.get("pressure", {}) if isinstance(last_frame, dict) else {}
    summary = payload.get("summary", {})
    return {
        "output_dir": run_label,
        "run_id": metadata.get("run_id") or payload.get("run_id") or run_label,
        "title": metadata.get("title") or payload.get("render_canon", {}).get("title") or run_label,
        "scenario_id": metadata.get("scenario_id") or Path(str(payload.get("manifest", {}).get("scenario_path", ""))).stem,
        "mode": metadata.get("mode") or "unknown",
        "seed": metadata.get("seed") or payload.get("manifest", {}).get("seed"),
        "created_at": metadata.get("created_at") or payload.get("manifest", {}).get("started_at", "-"),
        "event_count": summary.get("event_count", 0),
        "tick_count": len(payload.get("scheduler", [])),
        "phase": summary.get("phase", "-"),
        "trust_score": _view_score(summary.get("trust")),
        "resentment_score": _view_score(summary.get("resentment")),
        "repair_score": _view_score(summary.get("repair")),
        "pressure": {
            "material_urgency": _optional_float(pressure.get("material_urgency")),
            "conflict_pressure": _optional_float(pressure.get("conflict_pressure")),
            "repair_debt": _optional_float(pressure.get("repair_debt")),
            "recognition_pressure": _optional_float(pressure.get("recognition_pressure")),
            "memory_pressure": _optional_float(pressure.get("memory_pressure")),
        },
        "turning_point_count": sum(
            1
            for frame in story
            if frame.get("phase_changed")
            or frame.get("recognition")
            or int(frame.get("memory_count", 0)) > 0
            or int(frame.get("fate_count", 0)) > 0
        ),
        "top_rpps": summary.get("top_rpps", []),
        "top_compositions": summary.get("top_compositions", []),
    }


def _comparison_delta(current: dict[str, Any], other: dict[str, Any]) -> dict[str, Any]:
    current_rpps = {item.get("key") for item in current.get("top_rpps", [])}
    other_rpps = {item.get("key") for item in other.get("top_rpps", [])}
    return {
        "event_count": _delta_value(current.get("event_count"), other.get("event_count")),
        "tick_count": _delta_value(current.get("tick_count"), other.get("tick_count")),
        "phase_changed": current.get("phase") != other.get("phase"),
        "trust_score": _delta_value(current.get("trust_score"), other.get("trust_score")),
        "resentment_score": _delta_value(current.get("resentment_score"), other.get("resentment_score")),
        "repair_score": _delta_value(current.get("repair_score"), other.get("repair_score")),
        "turning_point_count": _delta_value(current.get("turning_point_count"), other.get("turning_point_count")),
        "pressure": {
            key: _delta_value(current.get("pressure", {}).get(key), other.get("pressure", {}).get(key))
            for key in ("material_urgency", "conflict_pressure", "repair_debt", "recognition_pressure", "memory_pressure")
        },
        "shared_top_rpps": sorted(item for item in current_rpps & other_rpps if item),
        "current_only_top_rpps": sorted(item for item in current_rpps - other_rpps if item),
        "other_only_top_rpps": sorted(item for item in other_rpps - current_rpps if item),
    }


def _view_score(view: Any) -> float | None:
    if isinstance(view, dict):
        return _optional_float(view.get("score"))
    return None


def _optional_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed


def _delta_value(current: Any, other: Any) -> float | int | None:
    if current is None or other is None:
        return None
    if isinstance(current, int) and isinstance(other, int):
        return current - other
    try:
        return round(float(current) - float(other), 6)
    except (TypeError, ValueError):
        return None


def _new_run_dir(experience_dir: Path, scenario_id: str, *, seed: int, mode: str) -> Path:
    stamp = time.strftime("%Y%m%d-%H%M%S")
    suffix = uuid.uuid4().hex[:8]
    safe_scenario = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in scenario_id)
    safe_mode = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in mode)
    return experience_dir / "runs" / safe_scenario / f"{stamp}_{safe_mode}_seed{seed}_{suffix}"


def _write_run_metadata(
    output_dir: Path,
    *,
    scenario_id: str,
    scenario_path: Path,
    seed: int,
    mode: str,
    title: str,
) -> None:
    metadata = {
        "run_id": output_dir.name,
        "scenario_id": scenario_id,
        "scenario_path": str(scenario_path),
        "seed": seed,
        "mode": mode,
        "title": title,
        "created_at": _mtime_iso(output_dir / "timeline_manifest.json"),
    }
    (output_dir / "run_metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")


def _mtime_iso(path: Path) -> str:
    timestamp = path.stat().st_mtime if path.exists() else time.time()
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(timestamp))


def _normalize_render_canon(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError("render_canon must be an object")
    title = str(value.get("title") or "").strip()
    if not title:
        raise ValueError("render_canon.title is required")
    cast = value.get("cast")
    if not isinstance(cast, dict) or not cast:
        raise ValueError("render_canon.cast must contain at least one process")
    normalized_cast: dict[str, dict[str, Any]] = {}
    for pid, item in cast.items():
        if not isinstance(item, dict):
            raise ValueError(f"render_canon.cast.{pid} must be an object")
        normalized_cast[str(pid)] = {
            "name": str(item.get("name") or pid).strip(),
            "gender": str(item.get("gender") or "未指定").strip(),
            "pronoun": str(item.get("pronoun") or "").strip(),
            "age_band": str(item.get("age_band") or "未指定").strip(),
            "surface_role": str(item.get("surface_role") or "").strip(),
            "speech_style": str(item.get("speech_style") or "").strip(),
            "allowed_interiority": str(item.get("allowed_interiority") or "只允许从行为、停顿、语气和选择中推断").strip(),
        }
    setting = value.get("setting") if isinstance(value.get("setting"), dict) else {}
    narration = value.get("narration") if isinstance(value.get("narration"), dict) else {}
    forbidden = narration.get("forbidden", [])
    if isinstance(forbidden, str):
        forbidden = [line.strip() for line in forbidden.splitlines() if line.strip()]
    if not isinstance(forbidden, list):
        forbidden = []
    material_objects = setting.get("material_objects", [])
    if isinstance(material_objects, str):
        material_objects = [line.strip() for line in material_objects.splitlines() if line.strip()]
    if not isinstance(material_objects, list):
        material_objects = []
    return {
        "title": title,
        "setting": {
            "place": str(setting.get("place") or "").strip(),
            "period": str(setting.get("period") or "").strip(),
            "atmosphere": str(setting.get("atmosphere") or "").strip(),
            "material_objects": [str(item).strip() for item in material_objects if str(item).strip()],
        },
        "cast": normalized_cast,
        "narration": {
            "language": str(narration.get("language") or "中文").strip(),
            "tense": str(narration.get("tense") or "过去时").strip(),
            "perspective": str(narration.get("perspective") or "第三人称限制视角").strip(),
            "style": str(narration.get("style") or "克制的现实主义文学").strip(),
            "interiority_level": str(narration.get("interiority_level") or "低").strip(),
            "metaphor_level": str(narration.get("metaphor_level") or "低到中").strip(),
            "sentence_rhythm": str(narration.get("sentence_rhythm") or "").strip(),
            "forbidden": [str(item).strip() for item in forbidden if str(item).strip()],
        },
    }


def _ensure_initial_output(output_dir: Path) -> Path:
    if output_dir.exists() and (output_dir / "timeline_manifest.json").exists():
        return output_dir
    scenarios = scenario_catalog(DEFAULT_EXAMPLES_DIR)
    if not scenarios:
        raise FileNotFoundError(f"No scenario files found in {DEFAULT_EXAMPLES_DIR}")
    preferred = next(
        (item for item in scenarios if item["id"] == "yellow_sign_cold_case"),
        scenarios[0],
    )
    scenario_path = Path(preferred["path"])
    scenario = load_scenario(scenario_path)
    target = output_dir if output_dir.name == str(scenario["id"]) else DEFAULT_EXPERIENCE_DIR / str(scenario["id"])
    sim = Simulator.from_scenario(scenario, scenario_path, seed=42)
    sim.run(steps=12, output_dir=target)
    return target
