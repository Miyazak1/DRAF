from __future__ import annotations

from rpf.core.models import SimulationState, clamp
from rpf.core.semantics import unrecognized_contribution
from rpf.core.views import AggregateViews, PersonView, RelationshipView


def aggregate_views(state: SimulationState, evidence_refs: list[str]) -> AggregateViews:
    p1 = state.processes["p1"]
    p2 = state.processes["p2"]
    recognition_debt = state.relation_metrics.get("relation_sediment.recognition_debt", 0.0)
    repair_access_narrowing = state.relation_metrics.get("relation_sediment.repair_access_narrowing", 0.0)
    symbolic_accounting = state.relation_metrics.get("relation_sediment.symbolic_accounting_load", 0.0)
    future_lock = state.relation_metrics.get("relation_sediment.future_lock_load", 0.0)
    asymmetry = state.relation_metrics.get("relation_sediment.asymmetry_load", 0.0)
    trust_score = clamp(
        (p1.risk_suspension_scope + p1.ambiguity_tolerance) / 2
        - p1.checking_tendency * 0.25
        - state.relation_metrics.get("repair_debt", 0.0) * 0.2
        - recognition_debt * 0.08
        - repair_access_narrowing * 0.06
    )
    resentment = clamp(
        (
            p1.resentment_pressure
            + state.relation_metrics.get("repair_debt", 0.0)
            + unrecognized_contribution(state)
            + recognition_debt * 0.35
            + symbolic_accounting * 0.25
        )
        / 3
    )
    repair_capacity = clamp(
        0.75
        - state.relation_metrics.get("repair_debt", 0.0) * 0.5
        - p2.speech_inhibition.get("apology", 0.0) * 0.25
        - repair_access_narrowing * 0.15
    )

    person_views = {}
    for pid, process in state.processes.items():
        labels: list[str] = []
        if process.checking_tendency > 0.4:
            labels.append("demanding")
        if process.speech_inhibition.get("apology", 0.0) > 0.72 or process.speech_inhibition.get("direct_need", 0.0) > 0.72:
            labels.append("withholding")
        if process.ambiguity_tolerance < 0.55:
            labels.append("careful")
        if process.stabilized_patterns.get("pursuit_withdrawal", 0.0) > 0.25 and pid == "p2":
            labels.append("distant")
        person_views[pid] = PersonView(
            process_id=pid,
            apparent_labels=labels,
            stabilized_response_patterns=process.stabilized_patterns,
            unavailable_actions=["direct apology"] if process.speech_inhibition.get("apology", 0.0) > 0.75 else [],
            evidence_refs=evidence_refs[-8:],
        )

    active = [r.rpp_id for r in state.active_rpps if r.intensity > 0.1]
    locked_threshold = state.relation_metrics.get("locked_in_repair_threshold", 0.55)
    cold_threshold = state.relation_metrics.get("cold_war_repair_threshold", 0.35)
    if state.irreversibility_register.records and state.relation_metrics.get("repair_debt", 0.0) + future_lock * 0.1 > locked_threshold:
        phase = "locked-in"
    elif state.relation_metrics.get("repair_debt", 0.0) > cold_threshold:
        phase = "cold-war"
    elif "repair_avoidance" in active:
        phase = "repair-avoidant"
    else:
        phase = "fragile"
    relationship = RelationshipView(
        phase_label=phase,
        active_bindings=[b.binding_id for b in state.bindings if b.strength > 0.1],
        recurring_rpps=active,
        recognition_conflicts=[d.recognition_type for p in state.processes.values() for d in p.recognition_demands if d.current_pressure > 0.3],
        repair_patterns=["practical_help_without_apology"] if state.relation_metrics.get("repair_debt", 0.0) > 0.0 else [],
        shared_irreversibles=[r.record_id for r in state.irreversibility_register.records],
        evidence_refs=evidence_refs[-10:],
    )
    if asymmetry > 0.08 and "asymmetric_role_pressure" not in relationship.active_bindings:
        relationship = relationship.model_copy(update={"active_bindings": relationship.active_bindings + ["asymmetric_role_pressure"]})
    return AggregateViews(
        trust_view={"score": trust_score, "state": "low" if trust_score < 0.4 else "unstable"},
        resentment_pressure_view={"score": resentment, "state": "high" if resentment > 0.55 else "building"},
        repair_capacity_view={"score": repair_capacity, "state": "fragile" if repair_capacity < 0.5 else "available"},
        person_views=person_views,
        relationship_view=relationship,
    )
