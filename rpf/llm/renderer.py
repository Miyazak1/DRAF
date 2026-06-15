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
    "fragile": "脆弱",
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
        "memory_trace": payload.get("memory", []),
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
    memory_trace = render_payload.get("memory_trace", []) or []
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
    if not inquiry_trace:
        return "-"
    latest = inquiry_trace[-1]
    state = latest.get("state_after", {}) or {}
    return (
        f"{latest.get('label') or latest.get('focus_id') or '-'}，"
        f"进展 {_fmt(state.get('progress'))}，污染 {_fmt(state.get('contamination'))}"
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
                "memory_trace",
            ],
            "must_not_invent": [
                "new characters",
                "new relationships",
                "new memories",
                "new motives",
                "new locations",
                "new case facts",
                "new evidence",
                "new testimonies",
                "new witnesses",
                "new culprits",
                "new future events",
                "changed recognition outcomes",
                "changed irreversible records",
                "changed investigation progress or contamination state",
                "changed case memory reconstruction",
                "causes not present in viability/action/expression/recognition evidence",
            ],
            "literary_freedom": [
                "sentence rhythm",
                "paragraph grouping",
                "observable gesture description",
                "low-to-medium metaphor consistent with render_canon",
                "scene transitions grounded in source_ticks",
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
