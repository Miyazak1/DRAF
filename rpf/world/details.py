from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any


ATTENTION_INTENSITY_MIN = 0.55
REPEATED_ATTENTION_INTENSITY_MIN = 0.08
SAME_FOCUS_REPEAT_MIN = 2
DETAIL_BUDGET_PER_SCOPE = 12
EPHEMERAL_DETAIL_BUDGET = 5
CAUSAL_DETAIL_BUDGET_PER_SCOPE = 4
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
    candidates = _causal_detail_candidates(focus_records, detail_gaps, local_world, registry)
    decisions = _persistence_decisions(candidates)
    causal_details = _validated_causal_details(candidates, decisions)
    activations = _causal_detail_activations(causal_details, local_world, story)
    _apply_causal_detail_activations(causal_details, activations)
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
            "causal_detail_budget_per_scope": CAUSAL_DETAIL_BUDGET_PER_SCOPE,
            "soft_profile_freshness_min": SOFT_PROFILE_FRESHNESS_MIN,
            "soft_profile_decay_per_tick": SOFT_PROFILE_DECAY_PER_TICK,
            "causal_details_do_not_activate_without_activation_event": True,
            "causal_detail_candidates_require_existing_refs": True,
            "activated_causal_details_are_projection_only": True,
            "activation_events_do_not_mutate_simulation_state": True,
        },
        "attention_focuses": focus_records,
        "detail_gaps": detail_gaps,
        "ephemeral_details": ephemeral,
        "soft_world_profiles": profiles,
        "active_soft_profiles": active_profiles,
        "soft_profile_history": profile_history,
        "causal_detail_candidates": candidates,
        "detail_persistence_decisions": decisions,
        "causal_world_details": causal_details,
        "causal_world_detail_activations": activations,
        "rejected_details": [decision for decision in decisions if decision.get("decision") == "reject"],
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


def _causal_detail_candidates(
    focus_records: list[dict[str, Any]],
    detail_gaps: list[dict[str, Any]],
    local_world: dict[str, Any],
    registry: dict[str, Any],
) -> list[dict[str, Any]]:
    gap_by_focus = {gap.get("focus_id"): gap for gap in detail_gaps}
    scope_counts: Counter[str] = Counter()
    candidates: list[dict[str, Any]] = []
    for index, record in enumerate(focus_records, start=1):
        focus = str(record.get("dominant_focus") or "")
        candidate = _candidate_for_focus(index, record, gap_by_focus.get(record.get("focus_id"), {}), local_world, registry)
        if not candidate:
            continue
        scope_id = str(candidate.get("scope_id") or "")
        if scope_counts[scope_id] >= CAUSAL_DETAIL_BUDGET_PER_SCOPE:
            candidate["validation_status"] = "rejected"
            candidate["risk_flags"].append("causal_detail_budget_exhausted")
        scope_counts[scope_id] += 1
        if focus in {"case_fixation", "avoidance_route", "threat_monitoring", "memory_intrusion"}:
            candidates.append(candidate)
    return candidates


def _candidate_for_focus(
    index: int,
    record: dict[str, Any],
    gap: dict[str, Any],
    local_world: dict[str, Any],
    registry: dict[str, Any],
) -> dict[str, Any] | None:
    focus = str(record.get("dominant_focus") or "")
    if focus == "case_fixation":
        target = _registry_target(record, registry)
        if not target:
            return _rejected_candidate(index, record, "case_fixation", "missing_registered_evidence_or_record")
        ref, kind, item = target
        forbidden = list(item.get("forbidden_inferences", []) or [])
        risk_flags = ["do_not_infer_case_truth", *[f"forbidden_inference:{flag}" for flag in forbidden[:3]]]
        field = "legibility" if kind in {"record", "evidence"} else "condition"
        return _candidate(
            index,
            record,
            gap,
            detail_type="evidence_or_record_condition",
            structural_field=field,
            value=_condition_value(item, field),
            affects_capacities=["evidence_access", "memory_integration"],
            target_ref=ref,
            validation_status="validated",
            risk_flags=risk_flags,
            validation_evidence=[ref, *record.get("evidence", [])[:4]],
        )
    if focus == "avoidance_route":
        route = local_world.get("route", {}) or {}
        route_id = record.get("route_id") or route.get("route_id")
        if not route_id:
            return _rejected_candidate(index, record, "route_surface", "missing_route_ref")
        status = route.get("access_status") or "unknown"
        constraints = [
            item
            for item in local_world.get("local_constraints", []) or []
            if item.get("route_id") == route_id
        ]
        return _candidate(
            index,
            record,
            gap,
            detail_type="route_affordance_condition",
            structural_field="access_surface",
            value=f"route_access_is_{status}",
            affects_capacities=["exit", "evidence_access"],
            target_ref=f"route:{route_id}",
            validation_status="validated",
            risk_flags=["does_not_change_route_access", "requires_activation_event"],
            validation_evidence=[*(route.get("source_event_ids", []) or [])[:4], *(item.get("event_type", "") for item in constraints[:2])],
        )
    if focus == "threat_monitoring":
        audience = _audience_target(local_world)
        if not audience:
            return _rejected_candidate(index, record, "audience_exposure_condition", "missing_audience_ref")
        audience_id = audience.get("audience_id") or audience.get("label")
        return _candidate(
            index,
            record,
            gap,
            detail_type="audience_exposure_condition",
            structural_field="visibility_or_sound_boundary",
            value=f"exposure_state:{audience.get('exposure_state') or 'possible'}",
            affects_capacities=["private_speech", "repair_attempt"],
            target_ref=f"audience:{audience_id}",
            validation_status="validated",
            risk_flags=["does_not_create_new_witness", "requires_activation_event"],
            validation_evidence=[*(audience.get("source_event_ids", []) or [])[:4]],
        )
    if focus == "memory_intrusion":
        sites = local_world.get("memory_sites", []) or []
        if not sites:
            return _rejected_candidate(index, record, "memory_site_condition", "missing_memory_site_ref")
        site = max(sites, key=lambda item: float(item.get("salience") or 0.0))
        return _candidate(
            index,
            record,
            gap,
            detail_type="memory_site_condition",
            structural_field="memory_anchor_salience",
            value=f"salience:{site.get('salience')}",
            affects_capacities=["memory_integration", "private_speech"],
            target_ref=f"memory_site:{site.get('site_id')}",
            validation_status="validated",
            risk_flags=["does_not_create_new_memory", "requires_activation_event"],
            validation_evidence=[*(site.get("source_event_ids", []) or [])[:4]],
        )
    return None


def _candidate(
    index: int,
    record: dict[str, Any],
    gap: dict[str, Any],
    *,
    detail_type: str,
    structural_field: str,
    value: Any,
    affects_capacities: list[str],
    target_ref: str,
    validation_status: str,
    risk_flags: list[str],
    validation_evidence: list[str],
) -> dict[str, Any]:
    tick = int(record.get("tick", 0) or 0)
    return {
        "candidate_id": f"cand-{tick:04d}-{index:02d}",
        "focus_id": record.get("focus_id"),
        "gap_id": gap.get("gap_id"),
        "scope_type": record.get("scope_type"),
        "scope_id": record.get("scope_id"),
        "target_ref": target_ref,
        "detail_type": detail_type,
        "structural_field": structural_field,
        "value": value,
        "affects_capacities": affects_capacities,
        "validation_status": validation_status,
        "risk_flags": _unique(risk_flags),
        "confidence": 0.72 if validation_status == "validated" else 0.32,
        "validation_evidence": _unique(validation_evidence),
        "source_focus_events": [str(record.get("focus_id"))],
        "source_events": record.get("evidence", []),
    }


def _rejected_candidate(index: int, record: dict[str, Any], detail_type: str, reason: str) -> dict[str, Any]:
    tick = int(record.get("tick", 0) or 0)
    return {
        "candidate_id": f"cand-{tick:04d}-{index:02d}",
        "focus_id": record.get("focus_id"),
        "gap_id": None,
        "scope_type": record.get("scope_type"),
        "scope_id": record.get("scope_id"),
        "target_ref": None,
        "detail_type": detail_type,
        "structural_field": None,
        "value": None,
        "affects_capacities": [],
        "validation_status": "rejected",
        "risk_flags": [reason, "requires_existing_registered_ref"],
        "confidence": 0.0,
        "validation_evidence": record.get("evidence", []),
        "source_focus_events": [str(record.get("focus_id"))],
        "source_events": record.get("evidence", []),
    }


def _persistence_decisions(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    decisions: list[dict[str, Any]] = []
    for candidate in candidates:
        status = candidate.get("validation_status")
        if status == "validated":
            decision = "persist_as_causal_record"
            reason = "existing registered ref and structural field are present; activation still requires a later event"
            target_record = f"causal:{candidate.get('candidate_id')}"
        elif "requires_existing_registered_ref" in (candidate.get("risk_flags") or []):
            decision = "reject"
            reason = "candidate lacks an existing registered object, route, audience, or memory-site reference"
            target_record = None
        else:
            decision = "compress_to_profile"
            reason = "candidate is perceptual but not structurally validated"
            target_record = None
        decisions.append(
            {
                "candidate_id": candidate.get("candidate_id"),
                "focus_id": candidate.get("focus_id"),
                "decision": decision,
                "reason": reason,
                "target_record": target_record,
                "activation_allowed": False,
            }
        )
    return decisions


def _validated_causal_details(candidates: list[dict[str, Any]], decisions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    decision_by_id = {item.get("candidate_id"): item for item in decisions}
    details: list[dict[str, Any]] = []
    for candidate in candidates:
        decision = decision_by_id.get(candidate.get("candidate_id"), {})
        if decision.get("decision") != "persist_as_causal_record":
            continue
        details.append(
            {
                "detail_id": f"causal-{candidate['candidate_id']}",
                "candidate_id": candidate.get("candidate_id"),
                "scope_type": candidate.get("scope_type"),
                "scope_id": candidate.get("scope_id"),
                "target_ref": candidate.get("target_ref"),
                "detail_type": candidate.get("detail_type"),
                "structural_field": candidate.get("structural_field"),
                "value": candidate.get("value"),
                "affects_capacities": candidate.get("affects_capacities", []),
                "affected_events": [],
                "causal_status": "validated_candidate",
                "activation_state": "inactive",
                "activation_requires_event": "CausalWorldDetailActivatedEvent",
                "validation_evidence": candidate.get("validation_evidence", []),
                "created_by_focus_event": candidate.get("focus_id"),
                "source_events": candidate.get("source_events", []),
            }
        )
    return details


def _causal_detail_activations(
    causal_details: list[dict[str, Any]],
    local_world: dict[str, Any],
    story: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    activations: list[dict[str, Any]] = []
    for index, detail in enumerate(causal_details, start=1):
        signal = _activation_signal(detail, local_world, story)
        if not signal:
            continue
        activation_id = f"act-{_safe_id(str(detail.get('detail_id') or index))}-{index:02d}"
        source_events = _unique([
            signal.get("source_event_id"),
            *(signal.get("source_event_ids") or []),
            *(detail.get("source_events") or []),
        ])
        activations.append(
            {
                "event_type": "CausalWorldDetailActivatedEvent",
                "activation_id": activation_id,
                "detail_id": detail.get("detail_id"),
                "candidate_id": detail.get("candidate_id"),
                "scope_type": detail.get("scope_type"),
                "scope_id": detail.get("scope_id"),
                "target_ref": detail.get("target_ref"),
                "activated_by_event": signal.get("source_event_id") or (source_events[0] if source_events else None),
                "affected_layer": "world_detail_projection",
                "affected_capacity": signal.get("capacity"),
                "previous_availability": "validated_but_inactive",
                "new_availability": "activated_for_render_and_diagnostics",
                "mechanism": signal.get("mechanism"),
                "effect_scope": "projection_only",
                "does_not_mutate_simulation_state": True,
                "source_events": source_events,
            }
        )
    return activations


def _apply_causal_detail_activations(
    causal_details: list[dict[str, Any]],
    activations: list[dict[str, Any]],
) -> None:
    activations_by_detail: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for activation in activations:
        detail_id = str(activation.get("detail_id") or "")
        if detail_id:
            activations_by_detail[detail_id].append(activation)
    for detail in causal_details:
        detail_activations = activations_by_detail.get(str(detail.get("detail_id") or ""), [])
        if not detail_activations:
            continue
        detail["activation_state"] = "activated"
        detail["causal_status"] = "activated_projection"
        detail["affected_events"] = [item.get("activation_id") for item in detail_activations if item.get("activation_id")]
        detail["last_updated_by_event"] = detail["affected_events"][-1] if detail["affected_events"] else None


def _activation_signal(
    detail: dict[str, Any],
    local_world: dict[str, Any],
    story: list[dict[str, Any]],
) -> dict[str, Any] | None:
    capacities = {str(item) for item in detail.get("affects_capacities", []) or []}
    target_ref = str(detail.get("target_ref") or "")
    scope_id = str(detail.get("scope_id") or "")
    signal = _constraint_activation_signal(detail, local_world, capacities, target_ref, scope_id)
    if signal:
        return signal
    signal = _route_activation_signal(detail, local_world, capacities, target_ref, scope_id)
    if signal:
        return signal
    signal = _audience_activation_signal(detail, local_world, capacities, target_ref, scope_id)
    if signal:
        return signal
    signal = _memory_site_activation_signal(detail, local_world, capacities, target_ref, scope_id)
    if signal:
        return signal
    return _story_activation_signal(detail, story, capacities, target_ref, scope_id)


def _constraint_activation_signal(
    detail: dict[str, Any],
    local_world: dict[str, Any],
    capacities: set[str],
    target_ref: str,
    scope_id: str,
) -> dict[str, Any] | None:
    for constraint in local_world.get("local_constraints", []) or []:
        constraint_capacities = _constraint_capacities(constraint)
        if capacities and capacities.isdisjoint(constraint_capacities):
            continue
        if not _same_activation_scope(constraint, target_ref, scope_id):
            continue
        return {
            "capacity": _first_overlap(capacities, constraint_capacities),
            "mechanism": "validated detail touched by local world capacity constraint",
            "source_event_id": (constraint.get("source_event_ids") or [None])[0],
            "source_event_ids": constraint.get("source_event_ids", []),
        }
    return None


def _route_activation_signal(
    detail: dict[str, Any],
    local_world: dict[str, Any],
    capacities: set[str],
    target_ref: str,
    scope_id: str,
) -> dict[str, Any] | None:
    route = local_world.get("route", {}) or {}
    route_id = str(route.get("route_id") or "")
    if not route_id or f"route:{route_id}" != target_ref:
        return None
    if capacities and capacities.isdisjoint({"exit", "evidence_access"}):
        return None
    return {
        "capacity": _first_overlap(capacities, {"exit", "evidence_access"}),
        "mechanism": "validated route detail touched by selected route context",
        "source_event_id": (route.get("source_event_ids") or [None])[0],
        "source_event_ids": route.get("source_event_ids", []),
    }


def _audience_activation_signal(
    detail: dict[str, Any],
    local_world: dict[str, Any],
    capacities: set[str],
    target_ref: str,
    scope_id: str,
) -> dict[str, Any] | None:
    if not target_ref.startswith("audience:"):
        return None
    for audience in local_world.get("audiences", []) or []:
        audience_id = str(audience.get("audience_id") or audience.get("label") or "")
        if target_ref != f"audience:{audience_id}":
            continue
        if capacities and capacities.isdisjoint({"private_speech", "repair_attempt"}):
            continue
        if str(audience.get("exposure_state") or "") not in {"likely", "observed", "reported", "institutionalized"}:
            try:
                if float(audience.get("exposure_level") or 0.0) < 0.66:
                    continue
            except (TypeError, ValueError):
                continue
        return {
            "capacity": _first_overlap(capacities, {"private_speech", "repair_attempt"}),
            "mechanism": "validated audience detail touched by exposure state",
            "source_event_id": (audience.get("source_event_ids") or [None])[0],
            "source_event_ids": audience.get("source_event_ids", []),
        }
    return None


def _memory_site_activation_signal(
    detail: dict[str, Any],
    local_world: dict[str, Any],
    capacities: set[str],
    target_ref: str,
    scope_id: str,
) -> dict[str, Any] | None:
    if not target_ref.startswith("memory_site:"):
        return None
    target_id = target_ref.split(":", 1)[1]
    for site in local_world.get("memory_sites", []) or []:
        if str(site.get("site_id") or "") != target_id:
            continue
        if capacities and capacities.isdisjoint({"memory_integration", "private_speech"}):
            continue
        try:
            if float(site.get("salience") or 0.0) < 0.5:
                continue
        except (TypeError, ValueError):
            continue
        return {
            "capacity": _first_overlap(capacities, {"memory_integration", "private_speech"}),
            "mechanism": "validated memory-site detail touched by active memory salience",
            "source_event_id": (site.get("source_event_ids") or [None])[0],
            "source_event_ids": site.get("source_event_ids", []),
        }
    return None


def _story_activation_signal(
    detail: dict[str, Any],
    story: list[dict[str, Any]],
    capacities: set[str],
    target_ref: str,
    scope_id: str,
) -> dict[str, Any] | None:
    if not story:
        return None
    for frame in reversed(story):
        locality = frame.get("locality", {}) or {}
        if scope_id and scope_id not in {str(locality.get("location_id") or ""), str(locality.get("route_id") or "")}:
            continue
        refs = []
        inquiry = frame.get("inquiry", {}) or {}
        refs.extend(str(ref) for ref in inquiry.get("ledger_refs", []) or [] if ref)
        if target_ref.startswith(("evidence:", "record:")) and target_ref.split(":", 1)[1] not in refs:
            continue
        return {
            "capacity": sorted(capacities)[0] if capacities else None,
            "mechanism": "validated detail touched by story locality or ledger reference",
            "source_event_id": None,
            "source_event_ids": [],
        }
    return None


def _constraint_capacities(constraint: dict[str, Any]) -> set[str]:
    values = set()
    if constraint.get("capacity_id"):
        values.add(str(constraint.get("capacity_id")))
    for key in ("linked_capacities", "affected_capacities"):
        values.update(str(item) for item in constraint.get(key, []) or [] if item)
    return values


def _same_activation_scope(constraint: dict[str, Any], target_ref: str, scope_id: str) -> bool:
    if scope_id and str(constraint.get("location_id") or "") == scope_id:
        return True
    if target_ref.startswith("route:") and str(constraint.get("route_id") or "") == target_ref.split(":", 1)[1]:
        return True
    if target_ref.startswith("memory_site:") and str(constraint.get("site_id") or "") == target_ref.split(":", 1)[1]:
        return True
    if target_ref.startswith("audience:") and str(constraint.get("audience_id") or "") == target_ref.split(":", 1)[1]:
        return True
    if target_ref.startswith(("evidence:", "record:")) and constraint.get("capacity_id") in {"evidence_access", "memory_integration"}:
        return True
    return False


def _first_overlap(left: set[str], right: set[str]) -> str | None:
    overlap = sorted(left & right)
    if overlap:
        return overlap[0]
    if left:
        return sorted(left)[0]
    if right:
        return sorted(right)[0]
    return None


def _registry_target(record: dict[str, Any], registry: dict[str, Any]) -> tuple[str, str, dict[str, Any]] | None:
    object_id = record.get("object_id")
    if object_id:
        for key, id_key, prefix, kind in (
            ("evidence_objects", "evidence_id", "evidence", "evidence"),
            ("record_objects", "record_id", "record", "record"),
            ("world_objects", "object_id", "world", "world"),
        ):
            for item in registry.get(key, []) or []:
                if item.get(id_key) == object_id:
                    return f"{prefix}:{object_id}", kind, item
    evidence = registry.get("evidence_objects", []) or []
    if evidence:
        item = evidence[0]
        return f"evidence:{item.get('evidence_id')}", "evidence", item
    records = registry.get("record_objects", []) or []
    if records:
        item = records[0]
        return f"record:{item.get('record_id')}", "record", item
    objects = registry.get("world_objects", []) or []
    if objects:
        item = objects[0]
        return f"world:{item.get('object_id')}", "world", item
    return None


def _condition_value(item: dict[str, Any], field: str) -> Any:
    value = item.get(field)
    if value is not None and value != "":
        return value
    current = item.get("current_state", {}) or {}
    return current.get(field) or "unknown_but_registered"


def _audience_target(local_world: dict[str, Any]) -> dict[str, Any] | None:
    audiences = local_world.get("audiences", []) or []
    if not audiences:
        return None
    return max(audiences, key=lambda item: float(item.get("exposure_level") or 0.0))


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
