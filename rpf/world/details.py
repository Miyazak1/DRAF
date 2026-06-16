from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any


ATTENTION_INTENSITY_MIN = 0.55
REPEATED_ATTENTION_INTENSITY_MIN = 0.08
SAME_FOCUS_REPEAT_MIN = 2
DETAIL_BUDGET_PER_SCOPE = 12
EPHEMERAL_DETAIL_BUDGET = 5
SOFT_PROFILE_FRESHNESS_MIN = 0.35
SOFT_PROFILE_DECAY_PER_TICK = 0.035


FOCUS_LABELS = {
    "body_management": "身体负荷",
    "case_fixation": "案件固着",
    "threat_monitoring": "威胁监测",
    "repair_opportunity": "修复机会",
    "avoidance_route": "回避路线",
    "memory_intrusion": "记忆侵入",
}


ATTENTION_MODES = {
    "body_management": "practical_use",
    "case_fixation": "evidence_review",
    "threat_monitoring": "threat_monitoring",
    "repair_opportunity": "repair_attempt",
    "avoidance_route": "route_assessment",
    "memory_intrusion": "memory_intrusion",
}


MISSING_DIMENSIONS = {
    "body_management": ["body_load_anchor", "resource_surface", "room_pressure"],
    "case_fixation": ["record_surface", "evidence_condition", "inspection_light"],
    "threat_monitoring": ["sight_lines", "sound_leakage", "exposure_boundary"],
    "repair_opportunity": ["interpersonal_distance", "speech_surface", "audience_presence"],
    "avoidance_route": ["route_surface", "exit_visibility", "blocking_conditions"],
    "memory_intrusion": ["memory_site_anchor", "sensory_cue", "avoidance_pressure"],
}


SENSORY_TAGS = {
    "body_management": ["fatigue_surface", "stale_air"],
    "case_fixation": ["paper_trace", "inspection_light"],
    "threat_monitoring": ["thin_walls", "listening_pressure"],
    "repair_opportunity": ["held_distance", "speech_pressure"],
    "avoidance_route": ["route_friction", "exit_line"],
    "memory_intrusion": ["memory_residue", "returning_cue"],
}


ATMOSPHERE_TAGS = {
    "body_management": ["compressed", "draining"],
    "case_fixation": ["procedural", "unstable"],
    "threat_monitoring": ["watched", "narrow"],
    "repair_opportunity": ["hesitant", "exposed"],
    "avoidance_route": ["costly", "deflected"],
    "memory_intrusion": ["returning", "charged"],
}


def build_world_detail_context(payload: dict[str, Any]) -> dict[str, Any]:
    """Build non-causal world detail context gated by attention traces.

    This projection is deterministic. It does not create durable objects,
    case facts, or causal state. It only exposes render-scoped detail anchors
    and compact soft profiles that future render prompts may cite.
    """

    attention = payload.get("attention", []) or []
    story = payload.get("story", []) or []
    local_world = payload.get("local_world_view", {}) or {}
    registry = payload.get("object_registry_view", {}) or {}
    story_by_tick = {int(frame.get("tick", 0) or 0): frame for frame in story}
    selected_attention = _selected_attention(attention)
    focus_records = [
        _focus_record(index, item, story_by_tick, local_world, registry)
        for index, item in enumerate(selected_attention, start=1)
    ]
    focus_records = [record for record in focus_records if record]
    detail_gaps = _detail_gaps(focus_records)
    ephemeral = _ephemeral_details(focus_records, local_world)
    profiles = _soft_profiles(focus_records, local_world)
    current_tick = max(
        [int(frame.get("tick", 0) or 0) for frame in story]
        + [int(record.get("tick", 0) or 0) for record in focus_records]
        + [0]
    )
    profile_history = _soft_profile_history(profiles, focus_records, current_tick)
    active_profiles = [
        profile
        for profile in profiles
        if float(profile.get("freshness") or 0.0) >= SOFT_PROFILE_FRESHNESS_MIN
    ]
    return {
        "rules": {
            "no_attention_no_elaboration": True,
            "ephemeral_details_are_render_only": True,
            "soft_profiles_are_compressed_not_prose": True,
            "causal_details_require_validation_events": True,
            "llm_details_do_not_create_plot_authority": True,
            "attention_intensity_min": ATTENTION_INTENSITY_MIN,
            "repeated_attention_intensity_min": REPEATED_ATTENTION_INTENSITY_MIN,
            "same_focus_repeat_min": SAME_FOCUS_REPEAT_MIN,
            "detail_budget_per_scope": DETAIL_BUDGET_PER_SCOPE,
            "ephemeral_detail_budget": EPHEMERAL_DETAIL_BUDGET,
            "soft_profile_freshness_min": SOFT_PROFILE_FRESHNESS_MIN,
            "soft_profile_decay_per_tick": SOFT_PROFILE_DECAY_PER_TICK,
        },
        "attention_focuses": focus_records,
        "detail_gaps": detail_gaps,
        "ephemeral_details": ephemeral,
        "soft_world_profiles": profiles,
        "active_soft_profiles": active_profiles,
        "soft_profile_history": profile_history,
        "causal_world_details": [],
        "rejected_details": [],
    }


def _selected_attention(attention: list[dict[str, Any]]) -> list[dict[str, Any]]:
    focus_counts = Counter(str(item.get("dominant_focus") or "") for item in attention)
    selected: list[dict[str, Any]] = []
    for item in attention:
        intensity = float(item.get("drift_intensity") or 0.0)
        focus = str(item.get("dominant_focus") or "")
        if intensity >= ATTENTION_INTENSITY_MIN:
            selected.append(item)
        elif (
            intensity >= REPEATED_ATTENTION_INTENSITY_MIN
            and focus
            and focus_counts[focus] >= SAME_FOCUS_REPEAT_MIN
        ):
            selected.append(item)
    return selected


def _focus_record(
    index: int,
    item: dict[str, Any],
    story_by_tick: dict[int, dict[str, Any]],
    local_world: dict[str, Any],
    registry: dict[str, Any],
) -> dict[str, Any]:
    tick = int(item.get("tick", 0) or 0)
    focus = str(item.get("dominant_focus") or "")
    frame = story_by_tick.get(tick, {})
    locality = frame.get("locality", {}) or {}
    location = local_world.get("active_location", {}) or {}
    route = local_world.get("route", {}) or {}
    location_id = locality.get("location_id") or location.get("location_id")
    route_id = locality.get("route_id") or route.get("route_id")
    scope_id = location_id or route_id or "run_scope"
    source_events = [str(ref) for ref in item.get("caused_by_events", []) or [] if ref]
    return {
        "focus_id": f"focus-{tick:04d}-{index:02d}",
        "tick": tick,
        "focus_type": "attention_focus",
        "focus_label": FOCUS_LABELS.get(focus, focus or "attention"),
        "process_id": item.get("process_id"),
        "scene_id": f"tick-{tick:04d}" if tick else None,
        "location_id": location_id,
        "object_id": _object_ref_for_focus(focus, registry),
        "route_id": route_id if focus == "avoidance_route" else None,
        "scope_type": "location" if location_id else "route" if route_id else "run",
        "scope_id": scope_id,
        "attention_mode": ATTENTION_MODES.get(focus, "gaze"),
        "dominant_focus": focus,
        "intensity": round(float(item.get("drift_intensity") or 0.0), 4),
        "duration": 1,
        "reason": item.get("reason"),
        "evidence": source_events,
    }


def _object_ref_for_focus(focus: str, registry: dict[str, Any]) -> str | None:
    if focus == "case_fixation":
        evidence = registry.get("evidence_objects", []) or []
        if evidence:
            return evidence[0].get("evidence_id")
        records = registry.get("record_objects", []) or []
        if records:
            return records[0].get("record_id")
    if focus == "memory_intrusion":
        records = registry.get("record_objects", []) or []
        if records:
            return records[0].get("record_id")
    objects = registry.get("world_objects", []) or []
    if objects and focus in {"body_management", "threat_monitoring", "repair_opportunity"}:
        return objects[0].get("object_id")
    return None


def _detail_gaps(focus_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    gaps: list[dict[str, Any]] = []
    scope_counts = Counter(record["scope_id"] for record in focus_records)
    for index, record in enumerate(focus_records, start=1):
        focus = record.get("dominant_focus")
        missing = MISSING_DIMENSIONS.get(str(focus), ["perceptual_anchor"])
        needed_for = _needed_for(str(focus))
        gaps.append(
            {
                "gap_id": f"gap-{record['tick']:04d}-{index:02d}",
                "focus_id": record["focus_id"],
                "scope_type": record["scope_type"],
                "scope_id": record["scope_id"],
                "needed_for": needed_for,
                "missing_dimensions": missing,
                "risk_level": "medium" if float(record.get("intensity") or 0.0) >= 0.72 else "low",
                "requested_detail_types": ["ephemeral_detail", "soft_profile"],
                "max_detail_budget": min(DETAIL_BUDGET_PER_SCOPE, 2 + scope_counts[record["scope_id"]]),
                "source_events": record.get("evidence", []),
            }
        )
    return gaps


def _needed_for(focus: str) -> str:
    return {
        "case_fixation": "evidence_handling",
        "threat_monitoring": "audience_exposure",
        "repair_opportunity": "recognition_scene",
        "avoidance_route": "route_assessment",
        "memory_intrusion": "memory_trigger",
        "body_management": "blocked_capacity_explanation",
    }.get(focus, "rendering_texture")


def _ephemeral_details(focus_records: list[dict[str, Any]], local_world: dict[str, Any]) -> list[dict[str, Any]]:
    details: list[dict[str, Any]] = []
    for index, record in enumerate(focus_records[:EPHEMERAL_DETAIL_BUDGET], start=1):
        channel, text = _ephemeral_text(record, local_world)
        details.append(
            {
                "detail_id": f"eph-{record['tick']:04d}-{index:02d}",
                "focus_id": record["focus_id"],
                "tick": record["tick"],
                "scope_type": record["scope_type"],
                "scope_id": record["scope_id"],
                "sensory_channel": channel,
                "text": text,
                "discard_after_render": True,
                "source_focus_events": [record["focus_id"]],
                "source_events": record.get("evidence", []),
            }
        )
    return details


def _ephemeral_text(record: dict[str, Any], local_world: dict[str, Any]) -> tuple[str, str]:
    focus = str(record.get("dominant_focus") or "")
    location_label = (
        (local_world.get("active_location", {}) or {}).get("location_label")
        or record.get("location_id")
        or "当前场所"
    )
    location_label = str(location_label).strip()
    route = local_world.get("route", {}) or {}
    route_status = route.get("access_status")
    audience = _strongest_audience(local_world)
    if focus == "case_fixation":
        return "sight", f"{location_label} 里的记录、证物或标记被注意力推到前景，但它们只作为已登记材料的表面被看见。"
    if focus == "threat_monitoring":
        suffix = f"，旁观风险来自 {audience}" if audience else ""
        return "sound", f"{location_label} 的声音边界变窄{suffix}。"
    if focus == "repair_opportunity":
        return "distance", f"{location_label} 中两人之间的距离变得可被感觉到，话语还没有自动变成修复。"
    if focus == "avoidance_route":
        suffix = f"，路线状态是 {route_status}" if route_status else ""
        return "route", f"离开或绕开的路径被注意到{suffix}，但它没有自动打开新的行动结果。"
    if focus == "memory_intrusion":
        return "memory", f"{location_label} 中某个已存在的记忆锚点回到前景，只增强当前感知，不添加新的过去事实。"
    return "body", f"{location_label} 的物质条件压到身体层面，疲惫和可用资源变得更难忽视。"


def _strongest_audience(local_world: dict[str, Any]) -> str:
    audiences = local_world.get("audiences", []) or []
    if not audiences:
        return ""
    strongest = max(audiences, key=lambda item: float(item.get("exposure_level") or 0.0))
    return str(strongest.get("label") or strongest.get("audience_id") or "")


def _soft_profiles(focus_records: list[dict[str, Any]], local_world: dict[str, Any]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in focus_records:
        grouped[str(record["scope_id"])].append(record)
    profiles: list[dict[str, Any]] = []
    for index, (scope_id, records) in enumerate(sorted(grouped.items()), start=1):
        focuses = [str(record.get("dominant_focus") or "") for record in records]
        max_intensity = max(float(record.get("intensity") or 0.0) for record in records)
        last_reinforced_tick = max(int(record.get("tick", 0) or 0) for record in records)
        first_seen_tick = min(int(record.get("tick", 0) or 0) for record in records)
        base_freshness = min(1.0, 0.35 + len(records) * 0.08 + max_intensity * 0.32)
        sensory_tags = _unique(tag for focus in focuses for tag in SENSORY_TAGS.get(focus, []))
        atmosphere_tags = _unique(tag for focus in focuses for tag in ATMOSPHERE_TAGS.get(focus, []))
        profiles.append(
            {
                "profile_id": f"soft-{index:03d}-{_safe_id(scope_id)}",
                "scope_type": records[-1].get("scope_type"),
                "scope_id": scope_id,
                "sensory_tags": sensory_tags[:6],
                "atmosphere_tags": atmosphere_tags[:6],
                "recurring_material_cues": _material_cues(records, local_world),
                "visibility_profile": _visibility_profile(records, local_world),
                "sound_profile": _sound_profile(records, local_world),
                "smell_profile": None,
                "tactile_profile": "body_pressure" if "body_management" in focuses else None,
                "stability": "recurring" if len(records) >= 2 else "emergent",
                "freshness": round(base_freshness, 4),
                "base_freshness": round(base_freshness, 4),
                "first_seen_tick": first_seen_tick,
                "last_reinforced_tick": last_reinforced_tick,
                "reinforcement_count": len(records),
                "decay_policy": {
                    "decay_per_tick": SOFT_PROFILE_DECAY_PER_TICK,
                    "minimum_freshness_for_injection": SOFT_PROFILE_FRESHNESS_MIN,
                    "decays_when_scope_not_reinforced": True,
                },
                "source_focus_events": [record["focus_id"] for record in records],
                "source_events": _unique(ref for record in records for ref in record.get("evidence", [])),
            }
        )
    return profiles


def _soft_profile_history(
    profiles: list[dict[str, Any]],
    focus_records: list[dict[str, Any]],
    current_tick: int,
) -> list[dict[str, Any]]:
    records_by_scope: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in focus_records:
        records_by_scope[str(record.get("scope_id"))].append(record)
    history: list[dict[str, Any]] = []
    for profile in profiles:
        scope_id = str(profile.get("scope_id") or "")
        records = sorted(records_by_scope.get(scope_id, []), key=lambda item: int(item.get("tick", 0) or 0))
        if not records:
            continue
        freshness = 0.0
        last_tick = int(records[0].get("tick", 0) or 0)
        for index, record in enumerate(records, start=1):
            tick = int(record.get("tick", 0) or 0)
            freshness = _decayed_freshness(freshness, tick - last_tick)
            reinforcement = 0.22 + float(record.get("intensity") or 0.0) * 0.38
            freshness = min(1.0, max(freshness, 0.28) + reinforcement)
            history.append(
                {
                    "profile_id": profile.get("profile_id"),
                    "scope_type": profile.get("scope_type"),
                    "scope_id": scope_id,
                    "tick": tick,
                    "update_type": "reinforced",
                    "freshness": round(freshness, 4),
                    "reinforcement_count": index,
                    "source_focus_event": record.get("focus_id"),
                    "decay_policy": profile.get("decay_policy", {}),
                }
            )
            last_tick = tick
        if current_tick > last_tick:
            decayed = _decayed_freshness(freshness, current_tick - last_tick)
            history.append(
                {
                    "profile_id": profile.get("profile_id"),
                    "scope_type": profile.get("scope_type"),
                    "scope_id": scope_id,
                    "tick": current_tick,
                    "update_type": "decayed",
                    "freshness": round(decayed, 4),
                    "reinforcement_count": len(records),
                    "source_focus_event": None,
                    "decay_policy": profile.get("decay_policy", {}),
                }
            )
            profile["freshness"] = round(decayed, 4)
        else:
            profile["freshness"] = round(min(1.0, freshness), 4)
    return history


def _decayed_freshness(freshness: float, tick_delta: int) -> float:
    if tick_delta <= 0:
        return freshness
    return max(0.0, freshness - tick_delta * SOFT_PROFILE_DECAY_PER_TICK)


def _material_cues(records: list[dict[str, Any]], local_world: dict[str, Any]) -> list[str]:
    cues: list[str] = []
    focuses = {record.get("dominant_focus") for record in records}
    if "case_fixation" in focuses:
        cues.append("registered_records_or_evidence_surfaces")
    if "avoidance_route" in focuses and (local_world.get("route", {}) or {}).get("route_id"):
        cues.append("route_edge")
    if "threat_monitoring" in focuses and local_world.get("audiences"):
        cues.append("audience_line_of_sight")
    if "memory_intrusion" in focuses and local_world.get("memory_sites"):
        cues.append("memory_site_anchor")
    if "body_management" in focuses:
        cues.append("fatigue_surface")
    return cues[:5]


def _visibility_profile(records: list[dict[str, Any]], local_world: dict[str, Any]) -> str:
    focuses = {record.get("dominant_focus") for record in records}
    if "threat_monitoring" in focuses or local_world.get("audiences"):
        return "exposure_sensitive"
    if "case_fixation" in focuses:
        return "inspection_dependent"
    return "ordinary_visibility"


def _sound_profile(records: list[dict[str, Any]], local_world: dict[str, Any]) -> str:
    focuses = {record.get("dominant_focus") for record in records}
    if "threat_monitoring" in focuses:
        return "sound_leakage_salient"
    if local_world.get("audiences"):
        return "audience_noise_possible"
    return "not_salient"


def _unique(values: Any) -> list[str]:
    result: list[str] = []
    for value in values:
        if value is None or value == "":
            continue
        text = str(value)
        if text not in result:
            result.append(text)
    return result


def _safe_id(value: str) -> str:
    return "".join(ch if ch.isalnum() or ch in {"-", "_"} else "-" for ch in value)[:48] or "scope"
