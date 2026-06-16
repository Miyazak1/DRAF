from __future__ import annotations

from typing import Any


def build_narrative_beats(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Project story frames into deterministic, renderable narrative beats."""

    story = payload.get("story", []) or []
    timeline_by_tick = _timeline_event_ids_by_tick(payload.get("timeline", []) or [])
    registry = payload.get("object_registry_view", {}) or {}
    world_detail_context = payload.get("world_detail_context", {}) or {}
    details_by_tick = _world_detail_ids_by_tick(world_detail_context)
    activated_by_tick = _activated_detail_context_by_tick(world_detail_context)
    raw_beats = [
        _beat_from_frame(
            index,
            frame,
            timeline_by_tick.get(int(frame.get("tick", 0) or 0), []),
            registry,
            details_by_tick,
            activated_by_tick,
        )
        for index, frame in enumerate(story, start=1)
        if frame.get("summary")
    ]
    return _compress_pattern_continuations([beat for beat in raw_beats if beat])


def _beat_from_frame(
    index: int,
    frame: dict[str, Any],
    source_events: list[str],
    registry: dict[str, Any],
    details_by_tick: dict[int, list[str]],
    activated_by_tick: dict[int, list[dict[str, Any]]],
) -> dict[str, Any]:
    tick = int(frame.get("tick", 0) or 0)
    action = frame.get("action", {}) or {}
    expression = frame.get("expression", {}) or {}
    recognition = frame.get("recognition", {}) or {}
    locality = frame.get("locality", {}) or {}
    inquiry = frame.get("inquiry", {}) or {}
    beat_type = _beat_type(frame)
    object_refs, record_refs, evidence_refs = _registry_refs_for_frame(registry, inquiry)
    activated_details = activated_by_tick.get(tick, [])
    activated_refs = [str(item["detail_ref"]) for item in activated_details if item.get("detail_ref")]
    intended = _intended_action(action, recognition)
    realized = _realized_action(action, expression)
    inhibited = _inhibited_action(action)
    obstruction = _obstruction(frame)
    observation = _observation(frame, expression, locality)
    outcome = _outcome(frame, recognition)
    unresolved = _unresolved_remainder(frame, recognition, obstruction)
    return {
        "beat_id": f"beat-{tick:04d}-{index:02d}",
        "tick": tick,
        "beat_type": beat_type,
        "source_events": source_events,
        "location_id": locality.get("location_id"),
        "time_window": locality.get("time_window"),
        "participants": _participants(frame),
        "focal_process": _focal_process(action),
        "intended_action": intended,
        "realized_action": realized,
        "inhibited_action": inhibited,
        "substituted_action": _substituted_action(action, intended, realized),
        "object_refs": object_refs,
        "record_refs": record_refs,
        "evidence_refs": evidence_refs,
        "local_detail_refs": _local_detail_refs(frame, details_by_tick.get(tick, []), activated_refs),
        "activated_detail_refs": activated_refs,
        "materialized_constraints": _materialized_constraints(activated_details),
        "obstruction": obstruction,
        "observation": observation,
        "recognition_implication": _recognition_implication(recognition),
        "outcome": outcome,
        "unresolved_remainder": unresolved,
        "rendering_constraints": {
            "do_not_change_causal_outcome": True,
            "do_not_add_unregistered_durable_objects": True,
            "do_not_resolve_uncertainty": bool(frame.get("epistemic_boundary")),
            "activated_details_are_projection_only": bool(activated_details),
        },
    }


def _beat_type(frame: dict[str, Any]) -> str:
    action = frame.get("action", {}) or {}
    expression = frame.get("expression", {}) or {}
    recognition = frame.get("recognition", {}) or {}
    inquiry = frame.get("inquiry", {}) or {}
    outcome = str(recognition.get("outcome") or "")
    action_id = str(action.get("action_id") or action.get("id") or "")
    action_mode = str(action.get("action_mode") or "")
    expression_mode = str(expression.get("expression_mode") or "")
    if int(frame.get("fate_count", 0) or 0) > 0:
        return "threshold_crossing"
    if int(frame.get("memory_count", 0) or 0) > 0:
        return "memory_intrusion"
    if "evidence" in action_id or inquiry:
        return "evidence_misread" if outcome in {"misunderstood", "refused"} else "object_handling"
    if action_mode == "inhibited" or "inhibited" in action_id:
        return "failed_disclosure"
    if expression_mode == "silence":
        return "delayed_answer"
    if outcome in {"refused", "misunderstood", "unspeakable"}:
        return "recognition_refusal"
    if outcome in {"postponed", "displaced"}:
        return "repair_displaced"
    if frame.get("tick_type") == "latent":
        return "missed_window"
    if action_mode == "substituted":
        return "practical_substitution"
    return "recognition_claim" if recognition else "attention_fixation"


def _intended_action(action: dict[str, Any], recognition: dict[str, Any]) -> dict[str, Any]:
    action_id = action.get("action_id") or action.get("id") or "continue_position"
    return {
        "action_id": action_id,
        "description": action.get("label")
        or action.get("description")
        or recognition.get("demand_label")
        or recognition.get("demand_id")
        or action_id,
    }


def _realized_action(action: dict[str, Any], expression: dict[str, Any]) -> dict[str, Any]:
    expression_id = expression.get("expression_id") or expression.get("id") or expression.get("surface_signal")
    action_id = action.get("action_id") or action.get("id") or "visible_continuation"
    return {
        "action_id": action_id,
        "expression_id": expression_id,
        "description": expression.get("label")
        or expression.get("surface_signal")
        or expression.get("description")
        or action.get("label")
        or action_id,
    }


def _inhibited_action(action: dict[str, Any]) -> dict[str, Any] | None:
    if action.get("action_mode") != "inhibited" and "inhibited" not in str(action.get("action_id", "")):
        return None
    return {
        "action_id": action.get("action_id") or "inhibited_action",
        "description": action.get("label") or action.get("reason") or "direct action was inhibited",
    }


def _substituted_action(
    action: dict[str, Any],
    intended: dict[str, Any],
    realized: dict[str, Any],
) -> dict[str, Any] | None:
    if action.get("action_mode") not in {"substituted", "inhibited"}:
        return None
    if intended.get("action_id") == realized.get("action_id") and not realized.get("expression_id"):
        return None
    return realized


def _obstruction(frame: dict[str, Any]) -> dict[str, Any]:
    viability = frame.get("viability", {}) or {}
    locality = frame.get("locality", {}) or {}
    epistemic = frame.get("epistemic_boundary", {}) or {}
    opportunity = frame.get("opportunity_cost", {}) or {}
    return {
        "type": _first_nonempty(
            viability.get("blocked_requirement"),
            epistemic.get("boundary_type"),
            opportunity.get("cost_type"),
            locality.get("why_not_elsewhere"),
            "constraint_pressure",
        ),
        "description": _first_nonempty(
            locality.get("why_not_elsewhere"),
            epistemic.get("boundary_label"),
            opportunity.get("cost_label"),
            "the available action space narrowed",
        ),
        "evidence_refs": _split_refs(viability.get("evidence_refs")),
    }


def _observation(frame: dict[str, Any], expression: dict[str, Any], locality: dict[str, Any]) -> dict[str, Any]:
    audiences = locality.get("who_might_see") or locality.get("possible_audiences") or []
    return {
        "observer": "mutual" if not audiences else ",".join(str(item) for item in audiences[:3]),
        "observed_signal": expression.get("surface_signal") or expression.get("expression_id") or frame.get("summary", ""),
        "interpretive_risk": frame.get("epistemic_boundary", {}).get("boundary_state") or "ambiguous",
    }


def _recognition_implication(recognition: dict[str, Any]) -> dict[str, Any]:
    if not recognition:
        return {}
    return {
        "demand_id": recognition.get("demand_id"),
        "outcome": recognition.get("outcome"),
        "outcome_label": recognition.get("outcome_label"),
    }


def _outcome(frame: dict[str, Any], recognition: dict[str, Any]) -> dict[str, Any]:
    return {
        "recognition_outcome": recognition.get("outcome"),
        "phase": frame.get("phase"),
        "phase_changed": bool(frame.get("phase_changed")),
        "memory_count": int(frame.get("memory_count", 0) or 0),
        "fate_count": int(frame.get("fate_count", 0) or 0),
    }


def _unresolved_remainder(
    frame: dict[str, Any],
    recognition: dict[str, Any],
    obstruction: dict[str, Any],
) -> list[str]:
    items = []
    outcome = recognition.get("outcome")
    if outcome in {"refused", "misunderstood", "postponed", "displaced", "unspeakable"}:
        items.append(f"recognition remains {outcome}")
    if obstruction.get("description"):
        items.append(str(obstruction["description"]))
    if frame.get("summary"):
        items.append(str(frame["summary"])[:180])
    return _unique_nonempty(items)


def _registry_refs_for_frame(registry: dict[str, Any], inquiry: dict[str, Any]) -> tuple[list[str], list[str], list[str]]:
    ledger_refs = {str(ref) for ref in inquiry.get("ledger_refs", []) or []}
    evidence = [
        f"evidence:{item['evidence_id']}"
        for item in registry.get("evidence_objects", []) or []
        if item.get("evidence_id") and (not ledger_refs or item.get("evidence_id") in ledger_refs)
    ]
    records = [
        f"record:{item['record_id']}"
        for item in registry.get("record_objects", []) or []
        if item.get("record_id")
    ][:4]
    objects = [
        f"world:{item['object_id']}"
        for item in registry.get("world_objects", []) or []
        if item.get("object_id")
    ][:4]
    return objects, records, evidence


def _local_detail_refs(
    frame: dict[str, Any],
    world_detail_ids: list[str],
    activated_detail_refs: list[str] | None = None,
) -> list[str]:
    locality = frame.get("locality", {}) or {}
    refs = []
    if locality.get("location_id"):
        refs.append(f"location:{locality['location_id']}")
    if locality.get("route_id"):
        refs.append(f"route:{locality['route_id']}")
    refs.extend(f"detail:{detail_id}" for detail_id in world_detail_ids)
    refs.extend(activated_detail_refs or [])
    return _unique_nonempty(refs)


def _materialized_constraints(activated_details: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "activation_id": item.get("activation_id"),
            "detail_id": item.get("detail_id"),
            "target_ref": item.get("target_ref"),
            "affected_capacity": item.get("affected_capacity"),
            "mechanism": item.get("mechanism"),
            "effect_scope": item.get("effect_scope"),
            "projection_only": bool(item.get("does_not_mutate_simulation_state")),
        }
        for item in activated_details
    ]


def _world_detail_ids_by_tick(context: dict[str, Any]) -> dict[int, list[str]]:
    result: dict[int, list[str]] = {}
    for detail in context.get("ephemeral_details", []) or []:
        detail_id = detail.get("detail_id")
        if not detail_id:
            continue
        tick = int(detail.get("tick", 0) or 0)
        result.setdefault(tick, []).append(str(detail_id))
    for detail in context.get("causal_world_details", []) or []:
        detail_id = detail.get("detail_id")
        if not detail_id:
            continue
        tick = int(detail.get("tick", 0) or 0)
        if tick <= 0:
            continue
        result.setdefault(tick, []).append(str(detail_id))
    return result


def _activated_detail_context_by_tick(context: dict[str, Any]) -> dict[int, list[dict[str, Any]]]:
    result: dict[int, list[dict[str, Any]]] = {}
    for activation in context.get("causal_world_detail_activations", []) or []:
        detail_id = activation.get("detail_id")
        if not detail_id:
            continue
        tick = int(activation.get("tick", 0) or 0)
        if tick <= 0:
            continue
        item = dict(activation)
        item["detail_ref"] = f"activated_detail:{detail_id}"
        result.setdefault(tick, []).append(item)
    return result


def _participants(frame: dict[str, Any]) -> list[str]:
    participants = frame.get("participants", {}) or {}
    result = []
    for key in ("source", "target"):
        item = participants.get(key, {}) or {}
        if item.get("process_id"):
            result.append(str(item["process_id"]))
        elif item.get("name"):
            result.append(str(item["name"]))
    return result


def _focal_process(action: dict[str, Any]) -> str | None:
    return action.get("source_process") or action.get("process_id") or action.get("actor")


def _compress_pattern_continuations(beats: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    index = 0
    while index < len(beats):
        current = beats[index]
        group = [current]
        index += 1
        while index < len(beats) and _beat_signature(beats[index]) == _beat_signature(current):
            group.append(beats[index])
            index += 1
        if len(group) >= 3:
            result.append(_pattern_continuation(group))
        else:
            result.extend(group)
    return result


def _pattern_continuation(group: list[dict[str, Any]]) -> dict[str, Any]:
    first = group[0]
    last = group[-1]
    return {
        "beat_id": f"beat-{first['tick']:04d}-{last['tick']:04d}-continuation",
        "tick": first["tick"],
        "tick_start": first["tick"],
        "tick_end": last["tick"],
        "beat_type": "pattern_continuation",
        "repeated_beat_type": first.get("beat_type"),
        "source_events": [event for beat in group for event in beat.get("source_events", [])],
        "location_id": first.get("location_id"),
        "participants": first.get("participants", []),
        "object_refs": first.get("object_refs", []),
        "record_refs": first.get("record_refs", []),
        "evidence_refs": first.get("evidence_refs", []),
        "local_detail_refs": _unique_nonempty(
            [ref for beat in group for ref in beat.get("local_detail_refs", [])]
        ),
        "activated_detail_refs": _unique_nonempty(
            [ref for beat in group for ref in beat.get("activated_detail_refs", [])]
        ),
        "materialized_constraints": [
            constraint
            for beat in group
            for constraint in beat.get("materialized_constraints", [])
        ],
        "stable_objects": first.get("object_refs", []) + first.get("record_refs", []) + first.get("evidence_refs", []),
        "pressure_changes": [beat.get("outcome", {}) for beat in group],
        "what_did_not_change": first.get("unresolved_remainder", []),
        "what_narrowed": first.get("obstruction", {}).get("description"),
        "outcome": last.get("outcome", {}),
        "unresolved_remainder": last.get("unresolved_remainder", []),
        "rendering_constraints": {
            "compress_repetition": True,
            "do_not_restage_same_scene": True,
            "activated_details_are_projection_only": any(
                beat.get("rendering_constraints", {}).get("activated_details_are_projection_only")
                for beat in group
            ),
        },
    }


def _beat_signature(beat: dict[str, Any]) -> tuple[Any, ...]:
    return (
        beat.get("beat_type"),
        beat.get("location_id"),
        tuple(beat.get("participants", [])),
        beat.get("recognition_implication", {}).get("outcome"),
    )


def _timeline_event_ids_by_tick(timeline: list[dict[str, Any]]) -> dict[int, list[str]]:
    result: dict[int, list[str]] = {}
    for event in timeline:
        try:
            tick = int(event.get("tick", 0) or 0)
        except (TypeError, ValueError):
            continue
        if tick <= 0:
            continue
        event_id = str(event.get("event_id") or event.get("id") or event.get("event_type") or "")
        if event_id:
            result.setdefault(tick, []).append(event_id)
    return result


def _split_refs(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if item]
    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]
    return []


def _first_nonempty(*values: Any) -> str:
    for value in values:
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return text
    return ""


def _unique_nonempty(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = str(value).strip()
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result
