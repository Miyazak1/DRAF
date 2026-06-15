from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from rpf.core.events import Event
from rpf.core.models import RecognitionDemand, SimulationState, clamp
from rpf.core.semantics import defensive_memory, fate_memory, injury_memory, memory_pressure, unrecognized_contribution


RecognitionOutcome = Literal["granted", "partial", "misunderstood", "displaced", "refused", "postponed", "unspeakable"]


@dataclass(frozen=True)
class RecognitionResult:
    demand: RecognitionDemand
    outcome: RecognitionOutcome
    scores: dict[str, float]
    evidence: dict[str, float | str]
    repair_event_type: str
    repair_method: str
    repair_debt_delta: float
    conflict_delta: float
    demand_pressure_delta: float


class RecognitionEngine:
    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config

    def evaluate(self, state: SimulationState, events: list[Event]) -> RecognitionResult:
        demand = max(
            (demand for process in state.processes.values() for demand in process.recognition_demands),
            key=lambda item: item.current_pressure,
        )
        affordance_id = self._latest_payload(events, "AffordanceSelectionEvent", "affordance_id", "none")
        signal_type = self._latest_payload(events, "MicroSignalEvent", "signal_type", "none")
        action_id = self._latest_payload(events, "ActionSelectionEvent", "action_id", "none")
        action_mode = self._latest_payload(events, "ActionSelectionEvent", "action_mode", "none")
        expression_id = self._latest_payload(events, "ExpressionSelectionEvent", "expression_id", "none")
        expression_mode = self._latest_payload(events, "ExpressionSelectionEvent", "expression_mode", "none")
        viability = self._viability_context(events)
        composition = self._dominant_composition(state)
        p1 = state.processes["p1"]
        p2 = state.processes["p2"]
        audience = max(state.field_state.audience_pressure.values(), default=0.0)
        repair_debt = state.relation_metrics.get("repair_debt", 0.0)
        recognition_debt = state.relation_metrics.get("relation_sediment.recognition_debt", 0.0)
        repair_access_narrowing = state.relation_metrics.get("relation_sediment.repair_access_narrowing", 0.0)
        symbolic_accounting = state.relation_metrics.get("relation_sediment.symbolic_accounting_load", 0.0)
        public_definition = state.relation_metrics.get("relation_sediment.public_definition_load", 0.0)
        asymmetry_load = state.relation_metrics.get("relation_sediment.asymmetry_load", 0.0)
        memory_saturation = state.relation_metrics.get("relation_sediment.memory_saturation", 0.0)
        holder_account = self._account_context(state, demand.holder_process_id)
        responder_account = self._account_context(state, demand.demanded_from)
        normativity = self._normativity_context(state, demand.holder_process_id, demand.demanded_from)
        frame = self._frame_context(state)
        position = self._position_context(state, demand.holder_process_id, demand.demanded_from)
        face_risk = max(
            audience,
            state.relation_metrics.get("face_risk_pressure", 0.0),
            p2.speech_inhibition.get("apology", 0.0),
            public_definition * 0.8,
            responder_account["control"] * 0.6,
            normativity["public_face_obligation"] * 0.5,
            frame["public_performance"] * 0.45,
        )
        pressure = clamp((demand.current_pressure + demand.vulnerability_cost + demand.threat_if_denied + demand.identity_dependency) / 4)
        contribution = unrecognized_contribution(state)
        remembered_history = memory_pressure(state)
        injury_history = injury_memory(state)
        defensive_history = defensive_memory(state)
        fate_history = fate_memory(state)
        speech_block = max(p1.speech_inhibition.get("direct_need", 0.0), p1.speech_inhibition.get("anger", 0.0), p2.speech_inhibition.get("apology", 0.0))
        scores = {
            "granted": clamp((1.0 - repair_debt) * 0.18 + (1.0 - face_risk) * 0.18 + demand.explicitness * 0.24 - remembered_history * 0.03 - recognition_debt * 0.03 - repair_access_narrowing * 0.025 - responder_account["control"] * 0.025 + normativity["repair_obligation"] * 0.035 + normativity["claim_entitlement"] * 0.025 + frame["repair_scene"] * 0.035 + position["responder_repair_partner"] * 0.025),
            "partial": clamp((1.0 - face_risk) * 0.12 + self._is(affordance_id, {"practical_repair_offer", "care_intervention", "contaminated_evidence_review"}) * 0.28 + demand.explicitness * 0.14 - fate_history * 0.02 - repair_access_narrowing * 0.015 + normativity["repair_obligation"] * 0.025 + frame["repair_scene"] * 0.06 + frame["care_control"] * 0.025 + position["responder_debtor"] * 0.02 + position["responder_caretaker"] * 0.018),
            "misunderstood": clamp(self._is(affordance_id, {"material_pressure_intrusion", "care_intervention", "double_bind_response", "unstable_testimony_probe", "forbidden_symbol_confrontation"}) * 0.26 + pressure * 0.14 + speech_block * 0.16 + injury_history * 0.025 + recognition_debt * 0.04 + memory_saturation * 0.025 + holder_account["meaning"] * 0.02 + frame["material_accounting"] * 0.055 + frame["care_control"] * 0.04 + position["holder_controlled"] * 0.02 + position["responder_caretaker"] * 0.018 + viability["misunderstood_bias"]),
            "displaced": clamp(self._is(affordance_id, {"practical_repair_offer", "public_performance", "material_pressure_intrusion", "contaminated_evidence_review"}) * 0.28 + face_risk * 0.2 + repair_debt * 0.1 + defensive_history * 0.025 + repair_access_narrowing * 0.045 + responder_account["control"] * 0.025 + frame["public_performance"] * 0.035 + frame["material_accounting"] * 0.025 + viability["displaced_bias"]),
            "refused": clamp(repair_debt * 0.22 + face_risk * 0.2 + pressure * 0.14 + self._is(composition, {"debt_lock", "credit_recognition_lock"}) * 0.18 + injury_history * 0.03 + recognition_debt * 0.04 + symbolic_accounting * 0.035 + responder_account["control"] * 0.025 + holder_account["dignity"] * 0.015 + normativity["legitimacy_contestation"] * 0.035 + normativity["exit_justification"] * 0.025 + frame["debt_accounting"] * 0.012 + frame["recognition_trial"] * 0.012 + position["responder_defender"] * 0.025 - frame["double_bind"] * 0.07 + viability["refused_bias"]),
            "postponed": clamp(self._is(affordance_id, {"mediated_delay", "public_performance"}) * 0.32 + audience * 0.14 + repair_debt * 0.1 + defensive_history * 0.02 + public_definition * 0.04 + repair_access_narrowing * 0.035 + responder_account["energy"] * 0.02 + normativity["public_face_obligation"] * 0.03 + frame["avoidance_scene"] * 0.03 + frame["public_performance"] * 0.035 + position["responder_withdrawer"] * 0.025 + position["responder_public_performer"] * 0.02 + viability["postponed_bias"]),
            "unspeakable": clamp(self._is(affordance_id, {"double_bind_response", "forbidden_symbol_confrontation"}) * 0.36 + self._is(composition, {"care_bind_double_bind", "public_face_split"}) * 0.28 + speech_block * 0.18 + fate_history * 0.03 + asymmetry_load * 0.035 + repair_access_narrowing * 0.03 + responder_account["control"] * 0.025 + holder_account["relation"] * 0.02 + normativity["irreversible_precedent"] * 0.03 + frame["double_bind"] * 0.13 + frame["avoidance_scene"] * 0.025 + position["holder_trapped_party"] * 0.03 + position["responder_defender"] * 0.012 + viability["unspeakable_bias"]),
        }
        outcome = max(scores.items(), key=lambda item: (item[1], item[0]))[0]
        effects = self.config["effects"][outcome]  # type: ignore[index]
        return RecognitionResult(
            demand=demand,
            outcome=outcome,  # type: ignore[arg-type]
            scores=scores,
            evidence={
                "affordance_id": affordance_id,
                "signal_type": signal_type,
                "action_id": action_id,
                "action_mode": action_mode,
                "expression_id": expression_id,
                "expression_mode": expression_mode,
                "dominant_composition": composition or "none",
                "recognition_pressure": pressure,
                "repair_debt": repair_debt,
                "relation_recognition_debt": recognition_debt,
                "relation_repair_access_narrowing": repair_access_narrowing,
                "relation_symbolic_accounting": symbolic_accounting,
                "relation_public_definition": public_definition,
                "relation_asymmetry_load": asymmetry_load,
                "relation_memory_saturation": memory_saturation,
                "account_holder_dignity": holder_account["dignity"],
                "account_holder_relation": holder_account["relation"],
                "account_holder_meaning": holder_account["meaning"],
                "account_responder_control": responder_account["control"],
                "account_responder_energy": responder_account["energy"],
                "norm_claim_entitlement": normativity["claim_entitlement"],
                "norm_repair_obligation": normativity["repair_obligation"],
                "norm_legitimacy_contestation": normativity["legitimacy_contestation"],
                "norm_public_face_obligation": normativity["public_face_obligation"],
                "norm_exit_justification": normativity["exit_justification"],
                "norm_irreversible_precedent": normativity["irreversible_precedent"],
                "frame_debt_accounting": frame["debt_accounting"],
                "frame_repair_scene": frame["repair_scene"],
                "frame_avoidance_scene": frame["avoidance_scene"],
                "frame_public_performance": frame["public_performance"],
                "frame_care_control": frame["care_control"],
                "frame_double_bind": frame["double_bind"],
                "frame_material_accounting": frame["material_accounting"],
                "frame_recognition_trial": frame["recognition_trial"],
                "position_holder_claimant": position["holder_claimant"],
                "position_holder_controlled": position["holder_controlled"],
                "position_holder_trapped_party": position["holder_trapped_party"],
                "position_responder_debtor": position["responder_debtor"],
                "position_responder_defender": position["responder_defender"],
                "position_responder_caretaker": position["responder_caretaker"],
                "position_responder_public_performer": position["responder_public_performer"],
                "position_responder_withdrawer": position["responder_withdrawer"],
                "position_responder_repair_partner": position["responder_repair_partner"],
                "face_risk": face_risk,
                "unrecognized_contribution": contribution,
                "memory_pressure": remembered_history,
                "injury_memory": injury_history,
                "defensive_memory": defensive_history,
                "fate_memory": fate_history,
                "speech_block": speech_block,
                "viability_dramatic_tension": viability["dramatic_tension"],
                "viability_min_affordance_width": viability["min_affordance_width"],
                "viability_direct_response_cost": viability["direct_response_cost"],
                "viability_deformation_distance": viability["deformation_distance"],
                "viability_blocked_requirement": viability["blocked_requirement"],
                "viability_failure_modes": viability["failure_modes"],
                "viability_evidence_refs": viability["evidence_refs"],
            },
            repair_event_type=str(effects["repair_event_type"]),
            repair_method=str(effects["repair_method"]),
            repair_debt_delta=float(effects["repair_debt_delta"]),
            conflict_delta=float(effects["conflict_delta"]),
            demand_pressure_delta=float(effects["demand_pressure_delta"]),
        )

    def apply(self, state: SimulationState, result: RecognitionResult) -> None:
        growth = state.relation_metrics.get("repair_debt_growth", 1.0)
        state.relation_metrics["repair_debt"] = clamp(state.relation_metrics.get("repair_debt", 0.0) + result.repair_debt_delta * growth)
        state.relation_metrics["conflict_pressure"] = clamp(state.relation_metrics.get("conflict_pressure", 0.0) + result.conflict_delta)
        result.demand.current_pressure = clamp(result.demand.current_pressure + result.demand_pressure_delta)
        state.relation_metrics["last_recognition_outcome_score"] = result.scores[result.outcome]

    def _dominant_composition(self, state: SimulationState) -> str | None:
        composition_scores = {
            key.removeprefix("composition."): value
            for key, value in state.relation_metrics.items()
            if key.startswith("composition.")
        }
        if not composition_scores:
            return None
        return max(composition_scores.items(), key=lambda item: item[1])[0]

    def _latest_payload(self, events: list[Event], event_type: str, key: str, default: str) -> str:
        for event in reversed(events):
            if event.event_type == event_type:
                return str(event.payload.get(key, default))
        return default

    def _is(self, value: str | None, options: set[str]) -> float:
        return 1.0 if value in options else 0.0

    def _account_context(self, state: SimulationState, process_id: str) -> dict[str, float]:
        return {
            account: state.relation_metrics.get(f"account_pressure.{process_id}.{account}", 0.0)
            for account in ["safety", "dignity", "control", "relation", "meaning", "energy"]
        }

    def _normativity_context(self, state: SimulationState, holder: str, demanded_from: str) -> dict[str, float]:
        holder_prefix = f"norm_pressure.{holder}.{demanded_from}."
        responder_prefix = f"norm_pressure.{demanded_from}.{holder}."
        return {
            "claim_entitlement": state.relation_metrics.get(holder_prefix + "claim_entitlement", 0.0),
            "repair_obligation": state.relation_metrics.get(responder_prefix + "repair_obligation", state.relation_metrics.get(holder_prefix + "repair_obligation", 0.0)),
            "legitimacy_contestation": state.relation_metrics.get(responder_prefix + "legitimacy_contestation", state.relation_metrics.get(holder_prefix + "legitimacy_contestation", 0.0)),
            "public_face_obligation": state.relation_metrics.get(holder_prefix + "public_face_obligation", state.relation_metrics.get(responder_prefix + "public_face_obligation", 0.0)),
            "reciprocity_obligation": state.relation_metrics.get(holder_prefix + "reciprocity_obligation", state.relation_metrics.get(responder_prefix + "reciprocity_obligation", 0.0)),
            "exit_justification": state.relation_metrics.get(responder_prefix + "exit_justification", 0.0),
            "mutual_obligation": state.relation_metrics.get(holder_prefix + "mutual_obligation", state.relation_metrics.get(responder_prefix + "mutual_obligation", 0.0)),
            "irreversible_precedent": state.relation_metrics.get(holder_prefix + "irreversible_precedent", state.relation_metrics.get(responder_prefix + "irreversible_precedent", 0.0)),
        }

    def _frame_context(self, state: SimulationState) -> dict[str, float]:
        return {
            frame_type: state.relation_metrics.get(f"frame_definition.{frame_type}", 0.0)
            for frame_type in [
                "debt_accounting",
                "repair_scene",
                "avoidance_scene",
                "public_performance",
                "care_control",
                "double_bind",
                "material_accounting",
                "recognition_trial",
            ]
        }

    def _position_context(self, state: SimulationState, holder: str, demanded_from: str) -> dict[str, float]:
        positions = [
            "claimant",
            "debtor",
            "defender",
            "caretaker",
            "controlled",
            "public_performer",
            "withdrawer",
            "trapped_party",
            "repair_partner",
            "bound_party",
        ]
        result: dict[str, float] = {}
        for prefix, process_id in (("holder", holder), ("responder", demanded_from)):
            for position in positions:
                result[f"{prefix}_{position}"] = state.relation_metrics.get(f"position_field.{process_id}.{position}", 0.0)
        return result

    def _viability_context(self, events: list[Event]) -> dict[str, float | str]:
        tension_event = self._latest_event(events, "DerivedDramaticTensionEvent")
        deformation_event = self._latest_event(events, "DeformationTraceEvent")
        width_events = [event for event in events if event.event_type == "AffordanceWidthEvent"]
        requirement_event = self._latest_event(events, "ViabilityRequirementEvent")

        dramatic_tension = self._payload_float(tension_event, "dramatic_tension")
        deformation_distance = self._payload_float(deformation_event, "deformation_distance")
        direct_response_cost = max((self._payload_float(event, "direct_response_cost") for event in width_events), default=0.0)
        min_affordance_width = min((self._payload_float(event, "width", 1.0) for event in width_events), default=1.0)
        failure_modes = self._failure_modes(deformation_event)
        blocked_requirement = str(
            (deformation_event.payload.get("blocked_requirement_id") if deformation_event else None)
            or (requirement_event.payload.get("requirement_id") if requirement_event else "none")
        )
        evidence_refs = self._viability_refs([tension_event, deformation_event, requirement_event] + width_events)
        narrowing = clamp(1.0 - min_affordance_width)

        return {
            "dramatic_tension": dramatic_tension,
            "deformation_distance": deformation_distance,
            "direct_response_cost": direct_response_cost,
            "min_affordance_width": min_affordance_width,
            "blocked_requirement": blocked_requirement,
            "failure_modes": ",".join(failure_modes) if failure_modes else "none",
            "evidence_refs": ",".join(evidence_refs),
            "misunderstood_bias": clamp(deformation_distance * 0.045 + self._contains(failure_modes, "misunderstood") * 0.035),
            "displaced_bias": clamp(deformation_distance * 0.035 + self._contains(failure_modes, "displaced") * 0.035),
            "refused_bias": clamp(dramatic_tension * 0.035 + direct_response_cost * 0.025),
            "postponed_bias": clamp(narrowing * 0.035 + self._contains(failure_modes, "postponed") * 0.035),
            "unspeakable_bias": clamp(dramatic_tension * 0.025 + direct_response_cost * 0.025 + self._contains(failure_modes, "unspeakable") * 0.02),
        }

    def _latest_event(self, events: list[Event], event_type: str) -> Event | None:
        for event in reversed(events):
            if event.event_type == event_type:
                return event
        return None

    def _payload_float(self, event: Event | None, key: str, default: float = 0.0) -> float:
        if not event:
            return default
        value = event.payload.get(key, default)
        try:
            return clamp(float(value))
        except (TypeError, ValueError):
            return default

    def _failure_modes(self, event: Event | None) -> list[str]:
        if not event:
            return []
        modes = event.payload.get("expected_recognition_failure_modes", [])
        if isinstance(modes, list):
            return [str(mode) for mode in modes]
        return [str(modes)]

    def _contains(self, values: list[str], expected: str) -> float:
        return 1.0 if expected in values else 0.0

    def _viability_refs(self, events: list[Event | None]) -> list[str]:
        refs: list[str] = []
        for event in events:
            if not event:
                continue
            refs.append(event.event_id)
            refs.extend(str(ref) for ref in event.causal_refs)
        return sorted(set(refs))
