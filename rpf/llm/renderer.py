from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from rpf.viewer.server import build_viewer_payload


DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEEPSEEK_DEFAULT_MODEL = "deepseek-v4-flash"

LABELS = {
    "locked-in": "锁定",
    "cold-war": "冷战",
    "repair-avoidant": "回避修复",
    "shared": "共同现实稳定",
    "fragile": "脆弱",
    "contested": "共同现实争夺",
    "fractured": "共同现实断裂",
    "available": "可用",
    "restricted": "受限",
    "blocked": "被遮蔽",
    "institutional_silencing": "制度静默",
    "public_exposure_forces_movement": "公共曝光推动调查",
    "procedural_force_opens_access": "程序力量打开权限",
    "micro_interaction": "微交互",
    "scene": "场景",
    "latent": "潜伏",
    "lease": "租约绑定",
    "unrecognized_contribution": "未被承认的付出",
    "contribution_debt_loop": "付出-债务循环",
    "repair_avoidance": "修复回避",
    "recognition_pursuit": "承认追逐",
    "pursuit_withdrawal": "追逐-退缩",
    "admit_what_happened": "承认发生过什么",
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
    "admit_memory_is_not_just_evidence": "承认记忆不只是证据",
    "admit_what_changed_in_the_record": "承认卷宗中改变过的部分",
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
}


SYSTEM_PROMPT = """你是 RPF 的叙事渲染器，不是剧情作者。

硬性规则：
1. 只能渲染输入中已经发生的事实。
2. 不能添加新的事件、动机、因果、回忆、未来预告。
3. 不能把人物标签当作本质人格，只能说“看起来”“呈现为”。
4. 不能改变模拟状态、关系阶段、承认结果、不可逆记录。
5. 不要解释数值机制，不要写成分析报告。
6. 输出中文。
7. 姓名、性别、代词、称谓、地点、文风、禁区只能继承 render_canon。
8. 如果 render_canon 没有提供某个具体事实，不能自行补充。
9. 每个场景必须能追溯到输入 story 中的 source_ticks。
10. viability 字段只能作为底层证据使用，不能被扩写成新的心理动机或未发生事件。

目标：
在不越过事实边界的前提下，把结构化故事底稿渲染为克制、有文学性、清晰可读的关系演化文本。"""


def build_render_payload(output_dir: Path, max_frames: int | None = None) -> dict[str, Any]:
    payload = build_viewer_payload(output_dir)
    story = payload.get("story", [])
    if max_frames is not None and max_frames > 0:
        story = story[:max_frames]
    return {
        "run_dir": payload.get("run_dir"),
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
        "world_detail_context": payload.get("world_detail_context", {}),
        "narrative_beats": payload.get("narrative_beats", []),
        "summary": payload.get("summary"),
        "relationship_view": payload.get("derived_views", {}).get("relationship_view", {}),
        "person_views": payload.get("derived_views", {}).get("person_views", {}),
        "irreversibility": payload.get("irreversibility", {}),
        "story": story,
    }


def deterministic_markdown(render_payload: dict[str, Any]) -> str:
    summary = render_payload.get("summary", {})
    relationship = render_payload.get("relationship_view", {})
    canon = render_payload.get("render_canon", {})
    case_ledger = render_payload.get("case_ledger", {}) or {}
    inquiry_trace = render_payload.get("inquiry_trace", []) or []
    epistemic_trace = render_payload.get("epistemic_trace", []) or []
    environment_trace = render_payload.get("environment_trace", []) or []
    attention_trace = render_payload.get("attention_trace", []) or []
    opportunity_trace = render_payload.get("opportunity_trace", []) or []
    reversibility_trace = render_payload.get("reversibility_trace", []) or []
    common_ground_trace = render_payload.get("common_ground_trace", []) or []
    memory_trace = render_payload.get("memory_trace", []) or []
    local_world_view = render_payload.get("local_world_view", {}) or {}
    object_registry_view = render_payload.get("object_registry_view", {}) or {}
    title = canon.get("title") or "RPF 故事回放"
    lines = [
        f"# {title}",
        "",
        "## 总览",
        "",
        f"- 关系阶段：{_label(summary.get('phase', '-'))}",
        f"- 事件数：{summary.get('event_count', '-')}",
        f"- 活跃绑定：{'，'.join(_label(item) for item in (relationship.get('active_bindings', []) or ['-']))}",
        f"- 反复出现的关系模式：{'，'.join(_label(item) for item in (relationship.get('recurring_rpps', []) or ['-']))}",
        f"- 识别冲突：{'，'.join(_label(item) for item in (relationship.get('recognition_conflicts', []) or ['-']))}",
        "",
        "## 案件账本",
        "",
        _case_ledger_line(case_ledger),
        f"- 调查更新：{len(inquiry_trace)}。最近焦点：{_latest_inquiry_focus(inquiry_trace)}。",
        f"- 制度压力：{_institutional_pressure_summary(inquiry_trace)}",
        f"- 证人策略：{_witness_strategy_summary(inquiry_trace)}",
        f"- 信息边界：{_epistemic_boundary_summary(epistemic_trace)}",
        f"- 日常生态：{_daily_ecology_summary(environment_trace)}",
        f"- 注意力漂移：{_attention_drift_summary(attention_trace)}",
        f"- 机会成本：{_opportunity_cost_summary(opportunity_trace)}",
        f"- 行动可逆性：{_reversibility_summary(reversibility_trace)}",
        f"- 共同现实：{_common_ground_summary(common_ground_trace)}",
        f"- 本地世界：{_local_world_summary(local_world_view)}",
        f"- 物件/记录/证据：{_object_registry_summary(object_registry_view)}",
        f"- 地点耦合：{_location_coupling_summary(inquiry_trace)}",
        f"- 证据可达性：{_evidence_access_summary(inquiry_trace)}",
        f"- 案件记忆：{_case_memory_summary(memory_trace)}",
        "",
        "## 时间线",
        "",
    ]
    for frame in render_payload.get("story", []):
        markers = []
        if frame.get("phase_changed"):
            markers.append("阶段改变")
        if frame.get("fate_count"):
            markers.append("命运转折")
        if frame.get("memory_count"):
            markers.append(f"记忆重构 {frame['memory_count']}")
        marker_text = f" [{' / '.join(markers)}]" if markers else ""
        lines.extend(
            [
                f"### 第 {frame.get('tick')} 步 · {_label(frame.get('tick_type'))} · {_label(frame.get('phase'))}{marker_text}",
                "",
                _participant_line(frame),
                "",
                str(frame.get("summary", "")),
                _viability_line(frame),
                _frame_definition_line(frame),
                "",
            ]
        )
    return "\n".join(lines).strip() + "\n"


def _case_ledger_line(case_ledger: dict[str, Any]) -> str:
    if not case_ledger:
        return "- 当前运行没有案件账本。"
    facts = case_ledger.get("known_facts", []) or []
    evidence = case_ledger.get("evidence_items", []) or []
    testimonies = case_ledger.get("testimonies", []) or []
    contradictions = case_ledger.get("contradictions", []) or []
    anomalies = case_ledger.get("unverified_anomalies", []) or []
    evidence_names = "，".join(str(item.get("label") or item.get("evidence_id")) for item in evidence[:4])
    contradiction_text = "；".join(str(item.get("text", "")) for item in contradictions[:2])
    return (
        f"- 案件阶段：{_label(case_ledger.get('case_phase', '-'))}；"
        f"已知事实 {len(facts)}，证物 {len(evidence)}，证词 {len(testimonies)}，"
        f"矛盾 {len(contradictions)}，未证实异常 {len(anomalies)}。"
        f"核心证物：{evidence_names or '-'}。"
        f"主要矛盾：{contradiction_text or '-'}。"
    )


def _latest_inquiry_focus(inquiry_trace: list[dict[str, Any]]) -> str:
    investigation = [item for item in inquiry_trace if item.get("event_type") == "InvestigationUpdateEvent" or item.get("state_after")]
    if not investigation:
        return "-"
    latest = investigation[-1]
    state = latest.get("state_after", {}) or {}
    return (
        f"{latest.get('label') or latest.get('focus_id') or '-'}，"
        f"进展 {_fmt(state.get('progress'))}，污染 {_fmt(state.get('contamination'))}"
    )


def _evidence_access_summary(inquiry_trace: list[dict[str, Any]]) -> str:
    access = [
        item
        for item in inquiry_trace
        if item.get("event_type") == "EvidenceAccessibilityEvent" or item.get("accessibility_after")
    ]
    if not access:
        return "-"
    latest = access[-1]
    after = latest.get("accessibility_after", {}) or {}
    return (
        f"{latest.get('label') or latest.get('focus_id') or '-'}："
        f"{_label(after.get('access_status', '-'))}，可达 {_fmt(after.get('accessibility'))}"
    )


def _local_world_summary(local_world_view: dict[str, Any]) -> str:
    if not local_world_view:
        return "-"
    location = local_world_view.get("active_location", {}) or {}
    route = local_world_view.get("route", {}) or {}
    audiences = local_world_view.get("audiences", []) or []
    blocked_routes = local_world_view.get("blocked_routes", []) or []
    constraints = local_world_view.get("local_constraints", []) or []
    location_label = location.get("location_label") or location.get("location_id") or "-"
    route_id = route.get("route_id") or "-"
    route_status = _label(route.get("access_status", "-"))
    visible = "，".join(str(item.get("label") or item.get("audience_id")) for item in audiences[:3])
    return (
        f"{location_label}；路线 {route_id}（{route_status}）；"
        f"可见观众：{visible or '-'}；"
        f"阻断路线 {len(blocked_routes)}，本地约束 {len(constraints)}"
    )


def _object_registry_summary(object_registry_view: dict[str, Any]) -> str:
    if not object_registry_view:
        return "-"
    objects = object_registry_view.get("world_objects", []) or []
    records = object_registry_view.get("record_objects", []) or []
    evidence = object_registry_view.get("evidence_objects", []) or []
    tokens = object_registry_view.get("access_tokens", []) or []
    anchors = [
        str(item.get("label") or item.get("object_id") or item.get("record_id") or item.get("evidence_id"))
        for item in [*objects[:2], *records[:2], *evidence[:2]]
    ]
    return (
        f"活跃物件 {len(objects)}，记录 {len(records)}，证据 {len(evidence)}，权限 {len(tokens)}；"
        f"锚点：{'，'.join(anchors) or '-'}"
    )


def _location_coupling_summary(inquiry_trace: list[dict[str, Any]]) -> str:
    couplings = [
        item
        for item in inquiry_trace
        if item.get("event_type") == "LocationEvidenceCouplingEvent" or item.get("location_after")
    ]
    if not couplings:
        return "-"
    latest = couplings[-1]
    after = latest.get("location_after", {}) or {}
    effects = "，".join(str(effect) for effect in (after.get("field_effects", []) or [])[:3])
    return (
        f"{after.get('location_label') or after.get('location_id') or '-'}；"
        f"地点压力 {_fmt(after.get('location_pressure'))}，污染 {_fmt(after.get('contamination'))}，"
        f"地点可达 {_fmt(after.get('location_accessibility'))}；效应：{effects or '-'}"
    )


def _institutional_pressure_summary(inquiry_trace: list[dict[str, Any]]) -> str:
    institutional = [
        item
        for item in inquiry_trace
        if item.get("event_type") == "InstitutionalPressureEvent" or item.get("institutional_effect")
    ]
    if not institutional:
        return "-"
    latest = institutional[-1]
    return (
        f"{_label(latest.get('institutional_effect', '-'))}；"
        f"静默 {_fmt(latest.get('silencing_pressure'))}，"
        f"曝光 {_fmt(latest.get('public_exposure'))}，"
        f"程序 {_fmt(latest.get('procedural_force'))}，"
        f"权限 {_fmt(latest.get('permission_width'))}"
    )


def _witness_strategy_summary(inquiry_trace: list[dict[str, Any]]) -> str:
    strategy_events = [
        item
        for item in inquiry_trace
        if item.get("event_type") == "WitnessStrategyEvent" or item.get("witness_strategy")
    ]
    if not strategy_events:
        return "-"
    latest = strategy_events[-1]
    if latest.get("witness_strategy"):
        latest = latest.get("witness_strategy", {}) or latest
    return (
        f"{_label(latest.get('strategy_id', '-'))}；"
        f"保护 {_fmt(latest.get('protective_value'))}，"
        f"透露宽度 {_fmt(latest.get('disclosure_width'))}，"
        f"确认风险 {_fmt(latest.get('confirmation_risk'))}"
    )


def _epistemic_boundary_summary(epistemic_trace: list[dict[str, Any]]) -> str:
    if not epistemic_trace:
        return "-"
    latest = max(epistemic_trace[-10:], key=lambda item: float(item.get("pressure") or 0.0))
    return (
        f"{_label(latest.get('boundary_type', '-'))}；"
        f"{latest.get('focus_label') or latest.get('focus_id') or '-'}，"
        f"{_label(latest.get('boundary_state', '-'))}，"
        f"可说 {_fmt(latest.get('speakability_width'))}，"
        f"披露风险 {_fmt(latest.get('disclosure_risk'))}"
    )


def _daily_ecology_summary(environment_trace: list[dict[str, Any]]) -> str:
    daily = [item for item in environment_trace if item.get("event_type") == "DailyEcologyEvent"]
    if not daily:
        return "-"
    latest = daily[-1]
    return (
        f"{_label(latest.get('routine_phase', '-'))}；"
        f"身体负荷 {_fmt(latest.get('body_load'))}，"
        f"未完成杂事 {_fmt(latest.get('unfinished_tasks'))}，"
        f"等待压力 {_fmt(latest.get('waiting_pressure'))}"
    )


def _attention_drift_summary(attention_trace: list[dict[str, Any]]) -> str:
    if not attention_trace:
        return "-"
    latest = max(attention_trace[-8:], key=lambda item: float(item.get("drift_intensity") or 0.0))
    return (
        f"{latest.get('process_id', '-')}：{_label(latest.get('dominant_focus', '-'))}；"
        f"漂移 {_fmt(latest.get('drift_intensity'))}"
    )


def _opportunity_cost_summary(opportunity_trace: list[dict[str, Any]]) -> str:
    if not opportunity_trace:
        return "-"
    latest = max(opportunity_trace[-10:], key=lambda item: float(item.get("intensity") or 0.0))
    return (
        f"{latest.get('process_id', '-')}：{_label(latest.get('cost_type', '-'))}；"
        f"错过 {_label(latest.get('missed_window', '-'))}，"
        f"强度 {_fmt(latest.get('intensity'))}，"
        f"可逆性 {_fmt(latest.get('reversibility'))}"
    )


def _reversibility_summary(reversibility_trace: list[dict[str, Any]]) -> str:
    if not reversibility_trace:
        return "-"
    latest = max(reversibility_trace[-10:], key=lambda item: float(item.get("threshold_proximity") or 0.0))
    return (
        f"{latest.get('process_id', '-')}：{_label(latest.get('threshold_state', '-'))}；"
        f"可逆宽度 {_fmt(latest.get('reversibility_width'))}，"
        f"阈值接近 {_fmt(latest.get('threshold_proximity'))}，"
        f"修复路径 {_label(latest.get('recovery_route', '-'))}"
    )


def _common_ground_summary(common_ground_trace: list[dict[str, Any]]) -> str:
    if not common_ground_trace:
        return "-"
    latest = common_ground_trace[-1]
    return (
        f"{_label(latest.get('state', '-'))}；"
        f"互相可读性 {_fmt(latest.get('mutual_legibility'))}，"
        f"解释裂缝 {_fmt(latest.get('interpretive_gap'))}，"
        f"修复抓手 {_fmt(latest.get('repair_handle_width'))}，"
        f"主导框架 {_label(latest.get('dominant_frame', '-'))}"
    )


def _case_memory_summary(memory_trace: list[dict[str, Any]]) -> str:
    case_memories = [
        item
        for item in memory_trace
        if "case_memory_contamination" in (item.get("reconstruction_biases") or [])
    ]
    if not case_memories:
        return "-"
    focuses = []
    for item in case_memories[-6:]:
        remembered_as = str(item.get("remembered_as", ""))
        parts = remembered_as.split(":")
        if len(parts) >= 4:
            focuses.append(parts[2])
    return f"{len(case_memories)} 条；最近焦点：{'，'.join(sorted(set(focuses))) or '-'}。"


def _label(value: Any) -> str:
    text = str(value)
    return LABELS.get(text, text)


def _participant_line(frame: dict[str, Any]) -> str:
    participants = frame.get("participants", {})
    source = participants.get("source", {})
    target = participants.get("target", {})
    names = [item.get("name") for item in (source, target) if item.get("name")]
    if not names:
        return "参与者：-"
    return f"参与者：{'、'.join(names)}"


def _viability_line(frame: dict[str, Any]) -> str:
    viability = frame.get("viability", {}) or {}
    if not viability:
        return ""
    parts = [
        f"可存续性压力 {_fmt(viability.get('viability_pressure'))}",
        f"可行动宽度 {_fmt(viability.get('affordance_width'))}",
        f"直接回应成本 {_fmt(viability.get('direct_response_cost'))}",
        f"派生张力 {_fmt(viability.get('dramatic_tension'))}",
    ]
    deformation = viability.get("deformation", {}) or {}
    if deformation.get("type"):
        parts.append(f"变形：{_label(deformation.get('type'))} {_fmt(deformation.get('distance'))}")
    return "底层依据：" + "；".join(parts)


def _frame_definition_line(frame: dict[str, Any]) -> str:
    frame_definition = frame.get("frame_definition", {}) or {}
    if not frame_definition:
        return ""
    label = frame_definition.get("frame_label") or _label(frame_definition.get("dominant_frame"))
    try:
        strength = float(frame_definition.get("strength") or 0.0)
    except (TypeError, ValueError):
        strength = 0.0
    return f"情境定义：{label} {strength:.2f}"


def _fmt(value: Any) -> str:
    try:
        return f"{float(value):.2f}"
    except (TypeError, ValueError):
        return "-"


def llm_markdown(
    render_payload: dict[str, Any],
    *,
    api_key: str,
    base_url: str,
    model: str,
    provider: str | None = None,
    thinking: str | None = None,
    reasoning_effort: str | None = None,
    timeout: int = 60,
) -> str:
    url = base_url.rstrip("/") + "/chat/completions"
    segment_mode = render_payload.get("render_mode") == "segment"
    user_prompt = {
        "task": "render_rpf_story_segment" if segment_mode else "render_rpf_story",
        "output_format": _segment_output_format() if segment_mode else _story_output_format(),
        "rendering_contract": {
            "must_inherit": [
                "render_canon.title",
                "render_canon.cast.*.name",
                "render_canon.cast.*.gender",
                "render_canon.cast.*.pronoun",
                "render_canon.setting",
                "render_canon.narration",
                "case_ledger.case_title",
                "case_ledger.known_facts",
                "case_ledger.evidence_items",
                "case_ledger.testimonies",
                "case_ledger.contradictions",
                "case_ledger.unverified_anomalies",
                "inquiry_trace",
                "epistemic_trace",
                "environment_trace",
                "attention_trace",
                "opportunity_trace",
                "reversibility_trace",
                "common_ground_trace",
                "memory_trace",
                "local_world_view.world_id",
                "local_world_view.active_location",
                "local_world_view.route",
                "local_world_view.rhythms",
                "local_world_view.audiences",
                "local_world_view.memory_sites",
                "local_world_view.blocked_routes",
                "local_world_view.local_constraints",
                "local_world_view.boundary_rules",
                "object_registry_view.world_objects",
                "object_registry_view.record_objects",
                "object_registry_view.evidence_objects",
                "object_registry_view.access_tokens",
                "object_registry_view.rules",
                "world_detail_context.attention_focuses",
                "world_detail_context.ephemeral_details",
                "world_detail_context.soft_world_profiles",
                "world_detail_context.active_soft_profiles",
                "world_detail_context.soft_profile_history",
                "world_detail_context.causal_detail_candidates",
                "world_detail_context.detail_persistence_decisions",
                "world_detail_context.causal_world_details",
                "world_detail_context.rules",
            ],
            "must_not_invent": [
                "new characters",
                "new relationships",
                "new memories",
                "new motives",
                "new locations",
                "new routes",
                "new institutions",
                "new audiences",
                "new geography",
                "new durable objects",
                "new records",
                "new messages",
                "new access tokens",
                "new custody changes",
                "changed local_world_view",
                "changed object_registry_view",
                "changed world_detail_context into causal state",
                "places not present in local_world_view or story.locality",
                "movement without route evidence",
                "new case facts",
                "new evidence",
                "new testimonies",
                "new witnesses",
                "new culprits",
                "new future events",
                "changed recognition outcomes",
                "changed irreversible records",
                "changed investigation progress or contamination state",
                "changed evidence accessibility state",
                "changed location-evidence coupling state",
                "changed institutional pressure state",
                "changed witness strategy state",
                "changed epistemic boundary state",
                "changed daily ecology state",
                "changed attention drift state",
                "changed opportunity cost state",
                "changed action reversibility state",
                "changed common ground state",
                "changed case memory reconstruction",
                "changed route access, audience exposure, memory site, resource, or local constraint state",
                "causes not present in viability/action/expression/recognition evidence",
            ],
            "literary_freedom": [
                "sentence rhythm",
                "paragraph grouping",
                "observable gesture description",
                "low-to-medium metaphor consistent with render_canon",
                "scene transitions grounded in source_ticks",
                "environmental detail grounded in local_world_view",
                "object handling grounded in object_registry_view",
                "attention-gated sensory detail grounded in world_detail_context",
                "implicit atmosphere derived from viability pressure and deformation evidence",
            ],
            "viability_use": [
                "may use viability pressure to control compression and tension",
                "may use affordance width/direct response cost to render hesitation or constraint",
                "may use deformation evidence to render silence, gesture, tone, or delay",
                "must not state inner motives beyond evidence",
            ],
            "segment_mode_rules": [
                "when render_mode is segment, output only the new segment prose",
                "do not repeat title, overview, ending_state, or boundary_note in segment mode",
                "do not rewrite previous_story_tail",
                "if current frames repeat the same action/outcome pattern, compress them as sustained repetition instead of restaging the same scene",
            ],
            "local_world_rules": [
                "local_world_view is authoritative causal geography",
                "render only active_location, route, audiences, memory_sites, blocked_routes, resources, and local_constraints present in input",
                "do not move a scene to another place unless story.locality or local_world_view.route supports it",
                "do not invent weather, institutions, crowds, rooms, roads, or offscreen places",
                "public shame or public reinterpretation requires local_world_view.audiences or story.who_might_see evidence",
            ],
            "object_registry_rules": [
                "object_registry_view is authoritative durable material context",
                "render only durable objects, records, evidence, and access tokens present in object_registry_view",
                "object existence is separate from object access",
                "record authority is separate from record existence",
                "evidence access is separate from evidence truth",
                "do not invent files, keys, tapes, messages, weapons, reports, or evidence bags",
            ],
            "world_detail_rules": [
                "world_detail_context is attention-gated and non-causal",
                "ephemeral_details may color only current perception and must not become plot facts",
                "soft_world_profiles are compact atmosphere tags, not prose archives",
                "active_soft_profiles may be reused only when their scope matches the current scene and freshness is above threshold",
                "soft_profile_history explains reinforcement and decay; it is not a sequence of plot events",
                "causal_detail_candidates are only proposed material constraints until validated",
                "causal_world_details with activation_state inactive may be mentioned only as possible material constraints, not as active causes",
                "do not make a causal_world_detail affect action, route, evidence, audience, memory, or recognition unless a CausalWorldDetailActivatedEvent exists",
            ],
        },
        "input": render_payload,
    }
    request_body = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps(user_prompt, ensure_ascii=False)},
        ],
        "temperature": 0.4,
    }
    if _is_deepseek(provider, base_url, model):
        resolved_thinking = thinking or "disabled"
        request_body["thinking"] = {"type": resolved_thinking}
        if resolved_thinking == "enabled":
            request_body["reasoning_effort"] = reasoning_effort or "high"
    request = urllib.request.Request(
        url,
        data=json.dumps(request_body, ensure_ascii=False).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"LLM request failed: HTTP {exc.code}: {body}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"LLM request failed: {exc}") from exc
    content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
    if not isinstance(content, str) or not content.strip():
        raise RuntimeError("LLM response did not contain text content")
    return content.strip() + "\n"


def _story_output_format() -> dict[str, Any]:
    return {
        "title": "string",
        "overview": "short paragraph",
        "scenes": [
            {
                "tick_range": "string",
                "text": "rendered prose grounded only in input",
                "source_ticks": ["integer"],
            }
        ],
        "ending_state": "short paragraph",
        "boundary_note": "one sentence saying rendering did not alter causal state",
    }


def _segment_output_format() -> dict[str, Any]:
    return {
        "segment_text_only": "2-6 paragraphs of Chinese literary prose for the current segment only",
        "must_not_include": [
            "story title",
            "overview",
            "ending state",
            "boundary note",
            "markdown document heading",
            "previous segment rewrite",
        ],
        "source_tick_note": "one short parenthetical or final line is allowed, naming only this segment's source ticks",
    }


def render_output(
    output_dir: Path,
    *,
    out_path: Path | None = None,
    use_llm: bool = False,
    model: str | None = None,
    base_url: str | None = None,
    api_key: str | None = None,
    provider: str | None = None,
    thinking: str | None = None,
    reasoning_effort: str | None = None,
    max_frames: int | None = None,
) -> dict[str, Any]:
    render_payload = build_render_payload(output_dir, max_frames=max_frames)
    target = out_path or (output_dir / ("rendered_story_llm.md" if use_llm else "rendered_story.md"))
    if use_llm:
        resolved_provider = provider or os.environ.get("RPF_LLM_PROVIDER")
        provider_defaults = _provider_defaults(resolved_provider)
        resolved_key = (
            api_key
            or os.environ.get("RPF_LLM_API_KEY")
            or (_deepseek_api_key() if resolved_provider == "deepseek" else None)
        )
        resolved_base_url = (
            base_url
            or os.environ.get("RPF_LLM_BASE_URL")
            or provider_defaults.get("base_url")
            or "https://api.openai.com/v1"
        )
        resolved_model = (
            model
            or os.environ.get("RPF_LLM_MODEL")
            or provider_defaults.get("model")
        )
        if not resolved_key:
            raise RuntimeError("Missing API key. Set RPF_LLM_API_KEY or pass --api-key.")
        if not resolved_model:
            raise RuntimeError("Missing model. Set RPF_LLM_MODEL or pass --model.")
        text = llm_markdown(
            render_payload,
            api_key=resolved_key,
            base_url=resolved_base_url,
            model=resolved_model,
            provider=resolved_provider,
            thinking=thinking or os.environ.get("RPF_LLM_THINKING"),
            reasoning_effort=reasoning_effort or os.environ.get("RPF_LLM_REASONING_EFFORT"),
        )
        mode = "llm"
    else:
        text = deterministic_markdown(render_payload)
        mode = "deterministic"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")
    return {
        "mode": mode,
        "output": str(target),
        "source": str(output_dir),
        "frame_count": len(render_payload.get("story", [])),
    }


def _provider_defaults(provider: str | None) -> dict[str, str]:
    if provider == "deepseek":
        return {
            "base_url": DEEPSEEK_BASE_URL,
            "model": DEEPSEEK_DEFAULT_MODEL,
        }
    return {}


def _deepseek_api_key() -> str | None:
    return os.environ.get("DEEPSEEK_API_KEY")


def _is_deepseek(provider: str | None, base_url: str, model: str) -> bool:
    return (
        provider == "deepseek"
        or "deepseek.com" in base_url
        or model.startswith("deepseek-")
    )
