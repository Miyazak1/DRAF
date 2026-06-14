from __future__ import annotations

import random

from rpf.core.models import SimulationState, TickContext
from rpf.core.semantics import memory_pressure, material_urgency


class TemporalScheduler:
    def __init__(self, config: dict[str, object]) -> None:
        self.config = config
        self.last_diagnostics: dict[str, object] = {}

    def decide(self, state: SimulationState, rng: random.Random) -> TickContext:
        urgency = material_urgency(state)
        binding_urgency = max((b.strength for b in state.bindings), default=0.0)
        conflict = state.relation_metrics.get("conflict_pressure", 0.0)
        repair_debt = state.relation_metrics.get("repair_debt", 0.0)
        remembered_history = memory_pressure(state)
        fatigue = sum(p.fatigue for p in state.processes.values()) / max(1, len(state.processes))
        recognition = max(
            (d.current_pressure for p in state.processes.values() for d in p.recognition_demands),
            default=0.0,
        )
        weights = self.config["weights"]  # type: ignore[index]
        scene_weights = weights["scene"]  # type: ignore[index]
        micro_weights = weights["micro_interaction"]  # type: ignore[index]
        scene_score = (
            urgency * scene_weights.get("material_urgency", scene_weights["rent_pressure"])
            + binding_urgency * scene_weights["binding_urgency"]
            + conflict * scene_weights["conflict_pressure"]
            + recognition * scene_weights["recognition_pressure"]
            + repair_debt * scene_weights["repair_debt"]
            + remembered_history * scene_weights.get("memory_pressure", 0.0)
            + fatigue * scene_weights["mean_fatigue"]
        )
        micro_score = (
            micro_weights["base"]
            + binding_urgency * micro_weights["binding_urgency"]
            + conflict * micro_weights["conflict_pressure"]
            + remembered_history * micro_weights.get("memory_pressure", 0.0)
            + (state.tick % 3 == 1) * micro_weights["routine_overlap_bonus"]
            + scene_score * micro_weights["scene_score"]
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
                "mean_fatigue": round(fatigue, 4),
                "recognition_pressure": round(recognition, 4),
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
