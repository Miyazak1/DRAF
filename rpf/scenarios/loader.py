from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from rpf.core.local_world import LocalWorldSpec
from rpf.core.object_registry import ObjectRegistrySpec


def load_scenario(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Scenario must be a mapping: {path}")
    for key in ("id", "processes", "bindings"):
        if key not in data:
            raise ValueError(f"Scenario missing required key: {key}")
    if "local_world" not in data:
        data["local_world"] = _default_local_world(data)
    local_world = LocalWorldSpec.model_validate(data["local_world"])
    data["local_world"] = local_world.model_dump(mode="json")
    registry = ObjectRegistrySpec.model_validate(data.get("object_registry") or {})
    registry.validate_against_scenario(
        location_ids={item.location_id for item in local_world.locations},
        institution_ids={item.institution_id for item in local_world.institutions},
        process_ids=set(data.get("processes", {})),
        case_evidence_ids=_case_evidence_ids(data),
        local_world_evidence_refs=_local_world_evidence_refs(data["local_world"]),
        institution_record_refs={record for item in local_world.institutions for record in item.records},
    )
    data["object_registry"] = registry.model_dump(mode="json")
    return data


def _default_local_world(scenario: dict[str, Any]) -> dict[str, Any]:
    scenario_id = str(scenario.get("id") or "scenario")
    canon = scenario.get("render_canon", {}) or {}
    setting = canon.get("setting", {}) or {}
    place = str(setting.get("place") or scenario.get("name") or scenario_id).strip()
    field_state = scenario.get("field_state", {}) or {}
    spatial = field_state.get("spatial_constraints", {}) or {}
    material = field_state.get("material_pressures", {}) or {}
    audiences = field_state.get("audience_pressure", {}) or {}
    relation = scenario.get("relation_metrics", {}) or {}
    primary_location = _safe_id(f"{scenario_id}_primary_location")
    threshold_location = _safe_id(f"{scenario_id}_threshold")
    public_location = _safe_id(f"{scenario_id}_public_edge")
    primary_label = place or "关系现场"
    strongest_spatial = _strongest_key(spatial, "共享空间")
    strongest_audience = _strongest_key(audiences, "可能观众")
    material_pressure = _max_numeric(material, 0.35)
    audience_pressure = _max_numeric(audiences, 0.25)
    memory_charge = max(
        float(relation.get("repair_debt", 0.0) or 0.0),
        float(relation.get("unrecognized_contribution", 0.0) or 0.0),
        0.35,
    )
    scene_types = [
        "mediated_delay",
        "practical_repair_offer",
        "unacknowledged_contribution_claim",
        "public_performance",
        "care_intervention",
        "double_bind_response",
        "material_pressure_intrusion",
        "embodied_avoidance",
        "contaminated_evidence_review",
        "unstable_testimony_probe",
        "forbidden_symbol_confrontation",
    ]
    return {
        "id": _safe_id(f"{scenario_id}_local_world"),
        "name": f"{primary_label}本地世界",
        "scale": _infer_scale(primary_label, scenario_id),
        "description": "Loader-generated bounded local world for scenarios that do not yet define explicit geography.",
        "boundary_rules": {
            "max_scene_scope": "local_world_only",
            "new_location_policy": "discovery_required",
            "offscreen_event_policy": "trace_required",
            "route_required": True,
            "travel_time_required": True,
            "audience_required_for_public_reclassification": True,
            "institution_required_for_record_change": True,
            "memory_site_required_for_place_based_reconstruction": True,
        },
        "locations": [
            {
                "location_id": primary_location,
                "label": primary_label,
                "location_type": "primary_relation_site",
                "access_level": "restricted",
                "public_visibility": audience_pressure,
                "crowd_density": min(0.65, audience_pressure + 0.1),
                "rumor_density": audience_pressure,
                "surveillance_level": audience_pressure * 0.6,
                "memory_charge": memory_charge,
                "material_conditions": {"default_world": True, "strongest_spatial_constraint": strongest_spatial},
                "allowed_scene_types": scene_types,
                "linked_processes": ["p1", "p2"],
            },
            {
                "location_id": threshold_location,
                "label": f"{strongest_spatial}的边界",
                "location_type": "threshold",
                "access_level": "open",
                "public_visibility": max(0.25, audience_pressure * 0.7),
                "crowd_density": 0.25,
                "rumor_density": audience_pressure * 0.5,
                "memory_charge": memory_charge * 0.65,
                "allowed_scene_types": scene_types,
                "linked_processes": ["p1", "p2"],
            },
            {
                "location_id": public_location,
                "label": f"{strongest_audience}可见处",
                "location_type": "public_edge",
                "access_level": "open",
                "public_visibility": max(0.45, audience_pressure),
                "crowd_density": max(0.3, audience_pressure),
                "rumor_density": max(0.35, audience_pressure),
                "memory_charge": memory_charge * 0.35,
                "allowed_scene_types": ["public_performance", "mediated_delay", "embodied_avoidance", "double_bind_response"],
                "linked_processes": ["p1", "p2"],
            },
        ],
        "routes": [
            {
                "route_id": _safe_id(f"{scenario_id}_primary_to_threshold"),
                "from_location": primary_location,
                "to_location": threshold_location,
                "travel_time_minutes": 4,
                "access_level": "restricted",
                "exposure_level": audience_pressure * 0.5,
                "danger_level": 0.0,
                "memory_charge": memory_charge * 0.5,
            },
            {
                "route_id": _safe_id(f"{scenario_id}_threshold_to_public_edge"),
                "from_location": threshold_location,
                "to_location": public_location,
                "travel_time_minutes": 8,
                "access_level": "open",
                "exposure_level": max(0.35, audience_pressure),
                "danger_level": 0.0,
                "memory_charge": memory_charge * 0.25,
            },
        ],
        "rhythms": [
            {
                "rhythm_id": "daily_overlap",
                "label": "日常重叠",
                "time_window": "any",
                "active_locations": [primary_location, threshold_location],
                "crowd_density_delta": 0.12,
                "rumor_pressure_delta": audience_pressure * 0.25,
                "mobility_cost_delta": 0.08,
                "institutional_pressure_delta": audience_pressure * 0.12,
                "available_scene_types": scene_types,
            }
        ],
        "resources": [
            {
                "resource_id": "ordinary_capacity",
                "label": "普通应对余量",
                "resource_type": "time_energy_money",
                "scarcity_level": material_pressure,
                "replacement_access": max(0.1, 1.0 - material_pressure),
                "linked_capacities": ["survival", "care", "repair"],
                "conflict_potential": max(material_pressure, float(relation.get("conflict_pressure", 0.0) or 0.0)),
            }
        ],
        "audiences": [
            {
                "audience_id": _safe_id(strongest_audience),
                "label": strongest_audience,
                "audience_type": "local_observer",
                "usual_locations": [public_location, threshold_location],
                "visibility_pattern": "possible",
                "rumor_power": audience_pressure,
                "sanction_power": audience_pressure * 0.75,
                "legitimacy_power": audience_pressure * 0.45,
                "affected_topics": ["public_face", "recognition", "repair"],
                "relationship_to_processes": {"p1": "observer", "p2": "observer"},
            }
        ],
        "institutions": [
            {
                "institution_id": "local_norms",
                "label": "本地规范",
                "domain": "informal_social_order",
                "locations": [primary_location, public_location],
                "recognized_roles": ["co_present_participants"],
                "sanction_rules": ["public_reclassification_requires_audience"],
                "legitimacy_rules": ["private_repair_must_survive_public_readability"],
                "corruption_or_decay": 0.0,
            }
        ],
        "memory_sites": [
            {
                "site_id": _safe_id(f"{scenario_id}_primary_memory"),
                "location_id": primary_location,
                "memory_type": "relation_sediment",
                "affected_processes": ["p1", "p2"],
                "salience": memory_charge,
                "contamination": material_pressure * 0.35,
                "avoidance_pressure": max(0.25, float(relation.get("repair_debt", 0.0) or 0.0)),
                "attraction_pressure": max(0.25, float(relation.get("recognition_pursuit_pressure", 0.0) or 0.0)),
                "future_scene_biases": ["recognition_claim", "avoidance_scene", "material_accounting"],
            }
        ],
        "ecological_conditions": [
            {
                "condition_id": "routine_friction",
                "label": "日常摩擦",
                "condition_type": "ordinary_friction",
                "active_time_window": "always",
                "affected_routes": [_safe_id(f"{scenario_id}_primary_to_threshold")],
                "affected_locations": [primary_location],
                "mobility_delta": 0.08,
                "visibility_delta": audience_pressure * 0.1,
                "bodily_cost_delta": material_pressure * 0.2,
                "audience_density_delta": audience_pressure * 0.15,
            }
        ],
    }


def _strongest_key(values: dict[str, Any], fallback: str) -> str:
    if not values:
        return fallback
    return max(values, key=lambda key: _numeric(values.get(key), 0.0))


def _max_numeric(values: dict[str, Any], fallback: float) -> float:
    if not values:
        return fallback
    return max(_numeric(value, fallback) for value in values.values())


def _numeric(value: Any, fallback: float) -> float:
    try:
        return max(0.0, min(1.0, float(value)))
    except (TypeError, ValueError):
        return fallback


def _safe_id(value: str) -> str:
    normalized = "".join(ch.lower() if ch.isalnum() else "_" for ch in value.strip())
    normalized = "_".join(part for part in normalized.split("_") if part)
    return normalized or "local_world_item"


def _infer_scale(place: str, scenario_id: str) -> str:
    haystack = f"{place} {scenario_id}".lower()
    if any(token in haystack for token in ["work", "office", "company", "项目", "职场", "办公室"]):
        return "workplace"
    if any(token in haystack for token in ["hospital", "medical", "care", "医院", "医疗"]):
        return "hospital"
    if any(token in haystack for token in ["family", "parent", "公寓", "apartment", "home", "家"]):
        return "apartment_building"
    return "town"


def _case_evidence_ids(scenario: dict[str, Any]) -> set[str]:
    ledger = scenario.get("case_ledger", {}) or {}
    return {
        str(item.get("evidence_id"))
        for item in ledger.get("evidence_items", []) or []
        if item.get("evidence_id")
    }


def _local_world_evidence_refs(value: Any) -> set[str]:
    refs: set[str] = set()
    if isinstance(value, dict):
        for key, item in value.items():
            if key == "evidence_refs" and isinstance(item, list):
                refs.update(str(ref) for ref in item if ref)
            else:
                refs.update(_local_world_evidence_refs(item))
    elif isinstance(value, list):
        for item in value:
            refs.update(_local_world_evidence_refs(item))
    return refs
