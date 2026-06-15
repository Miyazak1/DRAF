from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from rpf.core.events import Event
from rpf.core.models import CoPresenceBinding, SimulationState, clamp


@dataclass(frozen=True)
class BindingEvolution:
    event_type: str
    binding_id: str
    previous_strength: float
    new_strength: float
    previous_exit_cost: dict[str, float]
    new_exit_cost: dict[str, float]
    reason: str
    causal_refs: list[str]

    def payload(self) -> dict[str, Any]:
        return {
            "binding_id": self.binding_id,
            "previous_strength": self.previous_strength,
            "new_strength": self.new_strength,
            "strength_delta": round(self.new_strength - self.previous_strength, 4),
            "previous_exit_cost": self.previous_exit_cost,
            "new_exit_cost": self.new_exit_cost,
            "exit_cost_delta": {
                pid: round(self.new_exit_cost.get(pid, 0.0) - self.previous_exit_cost.get(pid, 0.0), 4)
                for pid in sorted(set(self.previous_exit_cost) | set(self.new_exit_cost))
            },
            "reason": self.reason,
            "caused_by_events": self.causal_refs,
        }


class BindingEvolutionEngine:
    """Let structural co-presence bindings evolve from relation history.

    Bindings explain why processes keep re-entering each other's field. They are
    not fixed scenario rails; relation, field, repair, and avoidance history can
    tighten, loosen, or reprice exit over time.
    """

    def update(self, state: SimulationState, local_events: list[Event]) -> list[BindingEvolution]:
        updates: list[BindingEvolution] = []
        updates.extend(self._latent_drift(state, local_events))
        updates.extend(self._field_updates(state, local_events))
        updates.extend(self._repair_updates(state, local_events))
        updates.extend(self._relation_updates(state, local_events))
        return [update for update in updates if update.previous_strength != update.new_strength or update.previous_exit_cost != update.new_exit_cost]

    def _latent_drift(self, state: SimulationState, local_events: list[Event]) -> list[BindingEvolution]:
        tick = next((event for event in local_events if event.event_type == "TickStartedEvent"), None)
        if not tick or tick.payload.get("tick_type") != "latent":
            return []
        return [
            self._apply(
                binding,
                strength_delta=-0.0015,
                exit_delta=0.0,
                reason="unrenewed latent time slightly loosens co-presence binding",
                refs=[tick.event_id],
            )
            for binding in state.bindings
            if binding.strength > 0.0
        ]

    def _field_updates(self, state: SimulationState, local_events: list[Event]) -> list[BindingEvolution]:
        updates: list[BindingEvolution] = []
        for event in local_events:
            if event.event_type != "FieldPressureEvent":
                continue
            pressure = self._payload_float(event, "intensity")
            if pressure <= 0.05:
                continue
            for binding in state.bindings:
                if binding.binding_type in {"material", "institutional", "spatial"}:
                    updates.append(
                        self._apply(
                            binding,
                            strength_delta=pressure * 0.004,
                            exit_delta=pressure * 0.002,
                            reason="field pressure tightens material or institutional co-presence",
                            refs=[event.event_id],
                        )
                    )
        return updates

    def _repair_updates(self, state: SimulationState, local_events: list[Event]) -> list[BindingEvolution]:
        updates: list[BindingEvolution] = []
        for event in local_events:
            if event.event_type == "RepairEvent":
                for binding in state.bindings:
                    updates.append(
                        self._apply(
                            binding,
                            strength_delta=0.0,
                            exit_delta=-0.006,
                            reason="repair makes exit slightly less costly without erasing co-presence",
                            refs=[event.event_id],
                        )
                    )
            elif event.event_type in {"AvoidanceEvent", "DisplacementEvent"}:
                for binding in state.bindings:
                    updates.append(
                        self._apply(
                            binding,
                            strength_delta=0.002,
                            exit_delta=0.003,
                            reason=f"{event.event_type} preserves co-presence while making clean exit costlier",
                            refs=[event.event_id],
                        )
                    )
        return updates

    def _relation_updates(self, state: SimulationState, local_events: list[Event]) -> list[BindingEvolution]:
        updates: list[BindingEvolution] = []
        for event in local_events:
            if event.event_type != "RelationSedimentationEvent":
                continue
            delta = self._payload_float(event, "delta")
            if delta <= 0.0:
                continue
            metric = str(event.payload.get("metric", ""))
            for binding in state.bindings:
                if self._metric_applies(metric, binding):
                    updates.append(
                        self._apply(
                            binding,
                            strength_delta=delta * 0.035,
                            exit_delta=delta * 0.025,
                            reason=f"{metric} tightens relevant co-presence binding",
                            refs=[event.event_id],
                        )
                    )
                elif metric in {"relation_sediment.future_lock_load", "relation_sediment.shared_fate_load"}:
                    updates.append(
                        self._apply(
                            binding,
                            strength_delta=delta * 0.02,
                            exit_delta=delta * 0.02,
                            reason=f"{metric} raises shared continuation pressure",
                            refs=[event.event_id],
                        )
                    )
        return updates

    def _metric_applies(self, metric: str, binding: CoPresenceBinding) -> bool:
        binding_type = binding.binding_type
        if metric in {"relation_sediment.recognition_debt", "relation_sediment.symbolic_accounting_load"}:
            return binding_type in {"recognition", "debt", "moral", "material"}
        if metric == "relation_sediment.repair_access_narrowing":
            return binding_type in {"recognition", "care", "material", "spatial"}
        if metric in {"relation_sediment.public_definition_load", "relation_sediment.asymmetry_load"}:
            return binding_type in {"social", "reputational", "institutional", "recognition"}
        if metric == "relation_sediment.memory_saturation":
            return binding_type in {"spatial", "recognition", "care"}
        return False

    def _apply(
        self,
        binding: CoPresenceBinding,
        *,
        strength_delta: float,
        exit_delta: float,
        reason: str,
        refs: list[str],
    ) -> BindingEvolution:
        previous_strength = binding.strength
        previous_exit_cost = {pid: round(value, 4) for pid, value in binding.exit_cost.items()}
        binding.strength = clamp(binding.strength + strength_delta)
        for pid, value in list(binding.exit_cost.items()):
            binding.exit_cost[pid] = clamp(value + exit_delta)
        event_type = "BindingDecayedEvent" if binding.strength < previous_strength or exit_delta < 0 else "BindingUpdatedEvent"
        return BindingEvolution(
            event_type=event_type,
            binding_id=binding.binding_id,
            previous_strength=round(previous_strength, 4),
            new_strength=binding.strength,
            previous_exit_cost=previous_exit_cost,
            new_exit_cost={pid: round(value, 4) for pid, value in binding.exit_cost.items()},
            reason=reason,
            causal_refs=sorted(set(refs)),
        )

    def _payload_float(self, event: Event, key: str) -> float:
        try:
            return clamp(float(event.payload.get(key, 0.0)))
        except (TypeError, ValueError):
            return 0.0
