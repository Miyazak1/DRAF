from __future__ import annotations

import random

from rpf.core.models import SimulationState, TickContext
from rpf.core.semantics import memory_pressure, material_urgency


class TemporalScheduler:
    def __init__(self, config: dict[str, object]) -> None:
        self.config = config
        self.last_diagnostics: dict[str, object] = {}

    def decide(self, state: SimulationState, rng: random.Random, viability_preview: dict[str, float] | None = None) -> TickContext:
        urgency = material_urgency(state)
        binding_urgency = max((b.strength for b in state.bindings), default=0.0)
        conflict = state.relation_metrics.get("conflict_pressure", 0.0)
        repair_debt = state.relation_metrics.get("repair_debt", 0.0)
        remembered_history = memory_pressure(state)
        relevance_load = self._relevance_load(state)
        inquiry_pressure = self._inquiry_pressure(state)
        institutional_pressure = self._institutional_pressure(state)
        daily_ecology_pressure = self._daily_ecology_pressure(state)
        attention_pressure = self._attention_pressure(state)
        opportunity_pressure = self._opportunity_pressure(state)
        reversibility_pressure = self._reversibility_pressure(state)
        fatigue = sum(p.fatigue for p in state.processes.values()) / max(1, len(state.processes))
        recognition = max(
            (d.current_pressure for p in state.processes.values() for d in p.recognition_demands),
            default=0.0,
        )
        weights = self.config["weights"]  # type: ignore[index]
        scene_weights = weights["scene"]  # type: ignore[index]
        micro_weights = weights["micro_interaction"]  # type: ignore[index]
        viability_preview = viability_preview or {}
        rhythm_weights = weights.get("viability_rhythm", {})  # type: ignore[union-attr]
        scene_viability_bias = min(
            0.018,
            viability_preview.get("scene_readiness", 0.0) * float(rhythm_weights.get("scene_readiness", 0.012)),
        )
        micro_viability_bias = min(
            0.014,
            viability_preview.get("micro_readiness", 0.0) * float(rhythm_weights.get("micro_readiness", 0.01)),
        )
        latent_relief = min(
            0.012,
            viability_preview.get("latent_instability", 0.0) * float(rhythm_weights.get("latent_instability", 0.008)),
        )
        scene_score = (
            urgency * scene_weights.get("material_urgency", scene_weights["rent_pressure"])
            + binding_urgency * scene_weights["binding_urgency"]
            + conflict * scene_weights["conflict_pressure"]
            + recognition * scene_weights["recognition_pressure"]
            + repair_debt * scene_weights["repair_debt"]
            + remembered_history * scene_weights.get("memory_pressure", 0.0)
            + relevance_load * scene_weights.get("relevance_load", 0.045)
            + inquiry_pressure * scene_weights.get("inquiry_pressure", 0.075)
            + institutional_pressure * scene_weights.get("institutional_pressure", 0.052)
            + daily_ecology_pressure * scene_weights.get("daily_ecology_pressure", 0.04)
            + attention_pressure * scene_weights.get("attention_pressure", 0.035)
            + opportunity_pressure * scene_weights.get("opportunity_pressure", 0.045)
            + reversibility_pressure * scene_weights.get("reversibility_pressure", 0.025)
            + fatigue * scene_weights["mean_fatigue"]
            + scene_viability_bias
        )
        micro_score = (
            micro_weights["base"]
            + binding_urgency * micro_weights["binding_urgency"]
            + conflict * micro_weights["conflict_pressure"]
            + remembered_history * micro_weights.get("memory_pressure", 0.0)
            + relevance_load * micro_weights.get("relevance_load", 0.035)
            + inquiry_pressure * micro_weights.get("inquiry_pressure", 0.045)
            + institutional_pressure * micro_weights.get("institutional_pressure", 0.028)
            + daily_ecology_pressure * micro_weights.get("daily_ecology_pressure", 0.06)
            + attention_pressure * micro_weights.get("attention_pressure", 0.04)
            + opportunity_pressure * micro_weights.get("opportunity_pressure", 0.032)
            + reversibility_pressure * micro_weights.get("reversibility_pressure", 0.018)
            + (state.tick % 3 == 1) * micro_weights["routine_overlap_bonus"]
            + scene_score * micro_weights["scene_score"]
            + micro_viability_bias
            - latent_relief
        )
        thresholds = self.config["thresholds"]  # type: ignore[index]
        forced_scene = state.tick in set(self.config["forced_scene_ticks"])  # type: ignore[arg-type]
        ranges = self.config["time_ranges_seconds"]  # type: ignore[index]
        if scene_score >= thresholds["scene"] or forced_scene:
            tick_type = "scene"
            delta = rng.randint(*ranges["scene"])
            reason = "field and recognition pressure crystallized into a scene"
            selected_score = scene_score
        elif micro_score >= thresholds["micro_interaction"]:
            tick_type = "micro_interaction"
            delta = rng.randint(*ranges["micro_interaction"])
            reason = "brief co-presence or message-level signal became structurally relevant"
            selected_score = micro_score
        else:
            tick_type = "latent"
            delta = rng.randint(*ranges["latent"])
            reason = "latent time passed while pressure accumulated without direct scene"
            selected_score = 1.0 - max(scene_score, micro_score)
        self.last_diagnostics = {
            "tick_index": state.tick,
            "input_factors": {
                "material_urgency": round(urgency, 4),
                "binding_urgency": round(binding_urgency, 4),
                "conflict_pressure": round(conflict, 4),
                "repair_debt": round(repair_debt, 4),
                "memory_pressure": round(remembered_history, 4),
                "relevance_load": round(relevance_load, 4),
                "inquiry_pressure": round(inquiry_pressure, 4),
                "institutional_pressure": round(institutional_pressure, 4),
                "daily_ecology_pressure": round(daily_ecology_pressure, 4),
                "attention_pressure": round(attention_pressure, 4),
                "opportunity_pressure": round(opportunity_pressure, 4),
                "reversibility_pressure": round(reversibility_pressure, 4),
                "mean_fatigue": round(fatigue, 4),
                "recognition_pressure": round(recognition, 4),
                "viability_pressure": round(viability_preview.get("viability_pressure", 0.0), 4),
                "relation_sediment_load": round(viability_preview.get("relation_sediment_load", 0.0), 4),
            },
            "viability_rhythm": {
                **{key: round(value, 4) for key, value in viability_preview.items()},
                "scene_viability_bias": round(scene_viability_bias, 4),
                "micro_viability_bias": round(micro_viability_bias, 4),
                "latent_relief": round(latent_relief, 4),
            },
            "tick_type_scores": {
                "scene": round(scene_score, 4),
                "micro_interaction": round(micro_score, 4),
                "latent": round(1.0 - max(scene_score, micro_score), 4),
            },
            "thresholds": thresholds,
            "forced_scene": forced_scene,
            "selected_tick_type": tick_type,
            "selected_score": round(selected_score, 4),
            "simulated_time_delta_seconds": delta,
            "time_mapping_reason": reason,
        }
        return TickContext(
            tick_index=state.tick,
            tick_type=tick_type,
            simulated_time_delta_seconds=delta,
            time_mapping_reason=reason,
        )

    def _relevance_load(self, state: SimulationState) -> float:
        values = [
            value
            for key, value in state.relation_metrics.items()
            if key.startswith("relevance_field.")
        ]
        if not values:
            return 0.0
        return min(1.0, sum(values) / max(1, len(state.processes)))

    def _inquiry_pressure(self, state: SimulationState) -> float:
        keys = (
            "inquiry.progress_pressure",
            "inquiry.contamination_load",
            "inquiry.suppression_load",
            "inquiry.relationship_risk",
        )
        values = [float(state.relation_metrics.get(key, 0.0) or 0.0) for key in keys]
        return min(1.0, sum(values))

    def _institutional_pressure(self, state: SimulationState) -> float:
        keys = (
            "institutional.silencing_pressure",
            "institutional.public_exposure",
        )
        values = [float(state.relation_metrics.get(key, 0.0) or 0.0) for key in keys]
        audience = float(state.field_state.audience_pressure.get("institutional_gatekeeping", 0.0) or 0.0)
        return min(1.0, sum(values) + audience)

    def _daily_ecology_pressure(self, state: SimulationState) -> float:
        keys = (
            "daily_ecology.body_load",
            "daily_ecology.unfinished_tasks",
            "daily_ecology.routine_overlap",
            "daily_ecology.object_friction",
            "daily_ecology.waiting_pressure",
        )
        values = [float(state.relation_metrics.get(key, 0.0) or 0.0) for key in keys]
        material = float(state.field_state.material_pressures.get("daily_task_debt", 0.0) or 0.0)
        spatial = float(state.field_state.spatial_constraints.get("routine_overlap", 0.0) or 0.0)
        return min(1.0, sum(values) * 0.45 + material * 0.22 + spatial * 0.18)

    def _attention_pressure(self, state: SimulationState) -> float:
        values = [
            float(value or 0.0)
            for key, value in state.relation_metrics.items()
            if key.startswith("attention_drift.")
        ]
        return min(1.0, sum(values) * 0.35)

    def _opportunity_pressure(self, state: SimulationState) -> float:
        values = [
            float(value or 0.0)
            for key, value in state.relation_metrics.items()
            if key.startswith("opportunity_cost.")
        ]
        return min(1.0, sum(values) * 0.42)

    def _reversibility_pressure(self, state: SimulationState) -> float:
        base = float(state.relation_metrics.get("action_reversibility.pressure", 0.0) or 0.0)
        crossed = float(state.relation_metrics.get("action_reversibility.threshold_crossed", 0.0) or 0.0)
        symbolic = float(state.relation_metrics.get("action_reversibility.symbolic_only", 0.0) or 0.0)
        return min(1.0, base * 0.7 + crossed * 0.55 + symbolic * 0.75)
