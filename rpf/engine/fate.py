from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from rpf.core.events import Event
from rpf.core.models import IrreversibleRecord, OperativeClassification, SimulationState, clamp
from rpf.core.semantics import unrecognized_contribution


@dataclass(frozen=True)
class FateTransitionResult:
    transition_id: str
    transition_type: str
    score: float
    evidence: dict[str, float | str]
    classification: OperativeClassification | None = None
    irreversible: IrreversibleRecord | None = None


class FateTransitionEngine:
    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config

    def evaluate(self, state: SimulationState, local_events: list[Event]) -> list[FateTransitionResult]:
        if state.tick < int(self.config.get("min_tick", 6)):
            return []
        source_event_id = local_events[-1].event_id if local_events else "unknown"
        affordance = self._latest_payload(local_events, "AffordanceSelectionEvent", "affordance_id", "none")
        recognition = self._latest_payload(local_events, "RecognitionEvent", "result", "none")
        composition = self._dominant_composition(state)
        audience = max(state.field_state.audience_pressure.values(), default=0.0)
        repair_debt = state.relation_metrics.get("repair_debt", 0.0)
        conflict = state.relation_metrics.get("conflict_pressure", 0.0)
        contribution = unrecognized_contribution(state)
        face_risk = state.relation_metrics.get("face_risk_pressure", 0.0)
        public_gap = state.relation_metrics.get("public_private_gap", 0.0)
        double_bind = state.relation_metrics.get("double_bind_pressure", 0.0)
        care_dependency = state.relation_metrics.get("care_dependency", 0.0)
        silence_charge = state.relation_metrics.get("silence_charge", 0.0)

        evidence: dict[str, float | str] = {
            "affordance": affordance,
            "recognition": recognition,
            "dominant_composition": composition or "none",
            "audience": round(audience, 4),
            "repair_debt": round(repair_debt, 4),
            "conflict_pressure": round(conflict, 4),
            "unrecognized_contribution": round(contribution, 4),
        }
        results: list[FateTransitionResult] = []
        results.extend(
            self._classification_candidates(
                state,
                source_event_id,
                affordance,
                recognition,
                composition,
                evidence,
                {
                    "debt_named": contribution * 0.28 + repair_debt * 0.22 + self._is(composition, {"debt_lock", "credit_recognition_lock"}) * 0.26 + self._is(recognition, {"refused", "misunderstood"}) * 0.12,
                    "controlling_care": care_dependency * 0.28 + double_bind * 0.2 + self._is(composition, {"care_bind_double_bind"}) * 0.28 + conflict * 0.12,
                    "public_mask": public_gap * 0.26 + face_risk * 0.2 + audience * 0.18 + self._is(composition, {"public_face_split"}) * 0.26,
                    "unreachable": silence_charge * 0.32 + self._is(composition, {"anxious_silence_circuit"}) * 0.28 + self._is(affordance, {"mediated_delay"}) * 0.2 + repair_debt * 0.08,
                    "impossible_to_satisfy": double_bind * 0.34 + self._is(affordance, {"double_bind_response"}) * 0.24 + self._is(recognition, {"unspeakable", "misunderstood"}) * 0.16 + conflict * 0.1,
                },
            )
        )
        results.extend(
            self._irreversibility_candidates(
                state,
                source_event_id,
                affordance,
                recognition,
                composition,
                evidence,
                {
                    "symbolic_debt_lock": contribution * 0.24 + repair_debt * 0.24 + self._is(composition, {"credit_recognition_lock", "debt_lock"}) * 0.32 + conflict * 0.12,
                    "public_exposure_risk": public_gap * 0.28 + audience * 0.22 + self._is(composition, {"public_face_split"}) * 0.26 + face_risk * 0.12,
                    "care_role_lock": care_dependency * 0.28 + double_bind * 0.18 + self._is(composition, {"care_bind_double_bind"}) * 0.28 + repair_debt * 0.12,
                    "silence_becomes_history": silence_charge * 0.28 + self._is(composition, {"anxious_silence_circuit"}) * 0.3 + self._is(recognition, {"postponed", "refused"}) * 0.18 + repair_debt * 0.1,
                    "double_bind_identity_mark": double_bind * 0.3 + self._is(affordance, {"double_bind_response"}) * 0.22 + self._is(recognition, {"unspeakable", "misunderstood"}) * 0.18 + conflict * 0.12,
                },
            )
        )
        return [result for result in results if result.score >= self.config.get("threshold", 0.68)]

    def apply(self, state: SimulationState, results: list[FateTransitionResult]) -> None:
        existing_classification_ids = {c.classification_id for p in state.processes.values() for c in p.active_classifications}
        existing_record_ids = {r.record_id for r in state.irreversibility_register.records}
        for result in sorted(results, key=lambda item: item.score, reverse=True):
            if result.classification and result.classification.classification_id not in existing_classification_ids:
                target = result.classification.target_process_id or "p2"
                if target in state.processes:
                    state.processes[target].active_classifications.append(result.classification)
                else:
                    state.processes["p2"].active_classifications.append(result.classification)
                existing_classification_ids.add(result.classification.classification_id)
                state.relation_metrics["operative_label_count"] = state.relation_metrics.get("operative_label_count", 0.0) + 1.0
            if result.irreversible and result.irreversible.record_id not in existing_record_ids:
                state.irreversibility_register.records.append(result.irreversible)
                existing_record_ids.add(result.irreversible.record_id)
        if results:
            state.relation_metrics["last_fate_transition_score"] = max(result.score for result in results)

    def _classification_candidates(
        self,
        state: SimulationState,
        source_event_id: str,
        affordance: str,
        recognition: str,
        composition: str | None,
        evidence: dict[str, float | str],
        scores: dict[str, float],
    ) -> list[FateTransitionResult]:
        specs = {
            "debt_named": ("cls-debt-named", "you_make_it_sound_like_i_owe_you", "p2"),
            "controlling_care": ("cls-controlling-care", "your_help_is_control", "p2"),
            "public_mask": ("cls-public-mask", "we_are_only_fine_in_public", "p1"),
            "unreachable": ("cls-unreachable", "you_are_never_really_here", "p2"),
            "impossible_to_satisfy": ("cls-impossible-to-satisfy", "nothing_i_do_is_right", "p1"),
        }
        existing = {c.classification_id for p in state.processes.values() for c in p.active_classifications}
        results: list[FateTransitionResult] = []
        for key, score in scores.items():
            classification_id, label, target = specs[key]
            if classification_id in existing:
                continue
            classification = OperativeClassification(
                classification_id=classification_id,
                label=label,
                target_process_id=target,
                target_relation_id="p1-p2",
                source_event_id=source_event_id,
                uptake="operative_in_scene",
                legitimacy=clamp(score),
                future_interpretation_bias=clamp(score * 0.25),
            )
            results.append(
                FateTransitionResult(
                    transition_id=classification_id,
                    transition_type="operative_classification",
                    score=clamp(score),
                    evidence={**evidence, "affordance": affordance, "recognition": recognition, "composition": composition or "none"},
                    classification=classification,
                )
            )
        return results

    def _irreversibility_candidates(
        self,
        state: SimulationState,
        source_event_id: str,
        affordance: str,
        recognition: str,
        composition: str | None,
        evidence: dict[str, float | str],
        scores: dict[str, float],
    ) -> list[FateTransitionResult]:
        specs = {
            "symbolic_debt_lock": (
                "irr-symbolic-debt-lock",
                "symbolic_debt_lock",
                "help and recognition became debt-like history",
                ["future help is interpreted through credit and repayment", "return to uncharged generosity is unavailable"],
                ["contribution could have remained unaccounted practical help"],
            ),
            "public_exposure_risk": (
                "irr-public-fiction-fractured",
                "public_reclassification",
                "the public fiction became unstable enough to alter future conduct",
                ["public behavior now carries exposure risk", "private injury can return through audience pressure"],
                ["public normality could have remained unproblematic"],
            ),
            "care_role_lock": (
                "irr-care-role-lock",
                "role_lock",
                "care and agency became mutually defining roles",
                ["care is interpreted as control or abandonment", "autonomy claims reactivate dependence history"],
                ["care could have remained situational rather than identity-defining"],
            ),
            "silence_becomes_history": (
                "irr-silence-history",
                "absence_history",
                "silence became an event with durable relational meaning",
                ["future delays are read through this absence", "neutral non-response is no longer available"],
                ["silence could have remained ambiguous or ordinary"],
            ),
            "double_bind_identity_mark": (
                "irr-double-bind-mark",
                "identity_mark",
                "contradictory demand became a durable identity constraint",
                ["future speech is pre-constrained by the contradiction", "direct naming risks confirming the imposed label"],
                ["the contradiction could have been treated as a local misunderstanding"],
            ),
        }
        existing = {r.record_id for r in state.irreversibility_register.records}
        results: list[FateTransitionResult] = []
        threshold = state.relation_metrics.get("irreversibility_threshold", self.config.get("irreversibility_threshold", 0.72))
        for key, score in scores.items():
            record_id, category, description, future_constraints, lost_alternatives = specs[key]
            if record_id in existing or score < threshold:
                continue
            record = IrreversibleRecord(
                record_id=record_id,
                category=category,
                description=description,
                source_event_id=source_event_id,
                affected_processes=["p1", "p2"],
                future_constraints=future_constraints,
                lost_alternatives=lost_alternatives,
            )
            results.append(
                FateTransitionResult(
                    transition_id=record_id,
                    transition_type="irreversibility",
                    score=clamp(score),
                    evidence={**evidence, "affordance": affordance, "recognition": recognition, "composition": composition or "none"},
                    irreversible=record,
                )
            )
        return results

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
