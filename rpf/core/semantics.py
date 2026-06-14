from __future__ import annotations

from rpf.core.models import SimulationState


def material_urgency(state: SimulationState) -> float:
    """Generic material/institutional urgency with MVP backward compatibility."""
    return state.field_state.material_pressures.get(
        "material_urgency",
        state.field_state.material_pressures.get("rent_due", 0.0),
    )


def set_material_urgency(state: SimulationState, value: float) -> None:
    state.field_state.material_pressures["material_urgency"] = value


def unrecognized_contribution(state: SimulationState) -> float:
    """Generic unrecognized cost/contribution with MVP backward compatibility."""
    return state.relation_metrics.get(
        "unrecognized_contribution",
        state.relation_metrics.get("unrecognized_sacrifice", 0.0),
    )


def memory_pressure(state: SimulationState) -> float:
    return state.relation_metrics.get("memory_pressure", 0.0)


def memory_bias(state: SimulationState, bias: str) -> float:
    return state.relation_metrics.get(f"memory_bias.{bias}", 0.0)


def injury_memory(state: SimulationState) -> float:
    return memory_bias(state, "injury_reconstruction")


def defensive_memory(state: SimulationState) -> float:
    return memory_bias(state, "defensive_reconstruction")


def fate_memory(state: SimulationState) -> float:
    return memory_bias(state, "fate_lock")
