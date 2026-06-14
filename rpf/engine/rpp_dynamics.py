from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from rpf.core.models import ActiveRPP, SimulationState, clamp


@dataclass(frozen=True)
class CompositionResult:
    composition_id: str
    participating_rpps: list[str]
    score: float
    effect: str


@dataclass(frozen=True)
class SuppressionResult:
    suppressed_rpp: str
    suppressed_by: str
    old_intensity: float
    new_intensity: float
    reason: str


@dataclass(frozen=True)
class DecayResult:
    rpp_id: str
    old_intensity: float
    new_intensity: float
    reason: str


@dataclass(frozen=True)
class RPPDynamicsResult:
    compositions: list[CompositionResult] = field(default_factory=list)
    suppressions: list[SuppressionResult] = field(default_factory=list)
    decays: list[DecayResult] = field(default_factory=list)


class RPPDynamics:
    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config

    def update(self, state: SimulationState, activated_this_tick: set[str]) -> RPPDynamicsResult:
        result = RPPDynamicsResult(
            compositions=self._compose(state),
            suppressions=self._suppress(state),
            decays=self._decay(state, activated_this_tick),
        )
        self._write_relation_metrics(state, result)
        return result

    def _compose(self, state: SimulationState) -> list[CompositionResult]:
        active = {r.rpp_id: r for r in state.active_rpps if r.intensity >= self.config.get("composition_min_intensity", 0.25)}
        results: list[CompositionResult] = []
        for rule in self.config.get("compositions", []):
            members = list(rule["members"])
            if not all(member in active for member in members):
                continue
            base_score = sum(active[member].intensity for member in members) / len(members)
            relation_support = sum(
                state.relation_metrics.get(str(metric), 0.0) * float(weight)
                for metric, weight in (rule.get("relation_metric_weights") or {}).items()
            )
            score = clamp(base_score + relation_support)
            if score < rule.get("threshold", 0.45):
                continue
            composition_id = str(rule["composition_id"])
            state.relation_metrics[f"composition.{composition_id}"] = score
            results.append(
                CompositionResult(
                    composition_id=composition_id,
                    participating_rpps=members,
                    score=score,
                    effect=str(rule["effect"]),
                )
            )
        return results

    def _suppress(self, state: SimulationState) -> list[SuppressionResult]:
        active = {r.rpp_id: r for r in state.active_rpps}
        results: list[SuppressionResult] = []
        for rule in self.config.get("suppressions", []):
            dominant_id = str(rule["dominant"])
            suppressed_id = str(rule["suppressed"])
            dominant = active.get(dominant_id)
            suppressed = active.get(suppressed_id)
            if not dominant or not suppressed:
                continue
            gap = dominant.intensity - suppressed.intensity
            if dominant.intensity < rule.get("dominant_min_intensity", 0.55) or gap < rule.get("min_gap", 0.08):
                continue
            old = suppressed.intensity
            suppressed.intensity = clamp(suppressed.intensity - rule.get("suppression_delta", 0.05))
            results.append(
                SuppressionResult(
                    suppressed_rpp=suppressed_id,
                    suppressed_by=dominant_id,
                    old_intensity=old,
                    new_intensity=suppressed.intensity,
                    reason=str(rule["reason"]),
                )
            )
        return results

    def _decay(self, state: SimulationState, activated_this_tick: set[str]) -> list[DecayResult]:
        results: list[DecayResult] = []
        decay_after = int(self.config.get("decay_after_ticks", 3))
        decay_delta = float(self.config.get("decay_delta", 0.04))
        floor = float(self.config.get("decay_floor", 0.03))
        for active in state.active_rpps:
            if active.rpp_id in activated_this_tick:
                continue
            inactive_for = state.tick - active.last_updated_tick
            if inactive_for < decay_after:
                continue
            old = active.intensity
            active.intensity = clamp(active.intensity - decay_delta)
            if active.intensity <= floor:
                active.intensity = 0.0
            results.append(
                DecayResult(
                    rpp_id=active.rpp_id,
                    old_intensity=old,
                    new_intensity=active.intensity,
                    reason=f"inactive_for_{inactive_for}_ticks",
                )
            )
        return results

    def _write_relation_metrics(self, state: SimulationState, result: RPPDynamicsResult) -> None:
        state.relation_metrics["active_composition_count"] = float(len(result.compositions))
        state.relation_metrics["suppression_count_last_tick"] = float(len(result.suppressions))
        state.relation_metrics["decay_count_last_tick"] = float(len(result.decays))
        if result.compositions:
            strongest = max(result.compositions, key=lambda item: item.score)
            state.relation_metrics["dominant_composition_score"] = strongest.score
