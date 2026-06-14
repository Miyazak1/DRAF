from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from rpf.core.events import Event
from rpf.core.models import MemoryTrace, SimulationState, clamp


@dataclass(frozen=True)
class MemoryReconstruction:
    memory: MemoryTrace
    source_event_type: str
    evidence: dict[str, Any]


class MemoryReconstructionEngine:
    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config

    def update(self, state: SimulationState, local_events: list[Event]) -> list[MemoryReconstruction]:
        self._decay_existing(state)
        candidates: list[MemoryReconstruction] = []
        for event in local_events:
            if event.event_type == "IrreversibilityEvent":
                candidates.extend(self._irreversibility_memories(state, event))
            elif event.event_type == "OperativeClassificationEvent":
                candidates.extend(self._classification_memories(state, event))
            elif event.event_type == "RecognitionEvent":
                candidates.extend(self._recognition_memories(state, event))
        accepted = [candidate for candidate in candidates if candidate.memory.salience >= self.config.get("min_salience", 0.35)]
        self._apply(state, accepted)
        return accepted

    def _decay_existing(self, state: SimulationState) -> None:
        decay = float(self.config.get("decay_per_tick", 0.01))
        for process in state.processes.values():
            for memory in process.memory_traces:
                memory.salience = clamp(memory.salience - decay)
                memory.active = memory.salience > 0.05
        for key in list(state.relation_metrics):
            if key.startswith("memory_bias."):
                state.relation_metrics[key] = clamp(state.relation_metrics[key] - decay)

    def _irreversibility_memories(self, state: SimulationState, event: Event) -> list[MemoryReconstruction]:
        weight = self._weight("irreversibility")
        category = str(event.payload.get("category", "irreversible_relation_shift"))
        description = str(event.payload.get("description", category))
        score = float(event.payload.get("transition_score", weight))
        affected = event.payload.get("affected_processes") or list(state.processes)
        memories = []
        for owner in affected:
            if owner in state.processes:
                memories.append(
                    self._memory(
                        state,
                        owner,
                        event,
                        f"irreversible:{category}:{description}",
                        clamp(weight * 0.55 + score * 0.45),
                        -0.72,
                        clamp(0.62 + score * 0.28),
                        ["fate_lock", category],
                    )
                )
        return memories

    def _classification_memories(self, state: SimulationState, event: Event) -> list[MemoryReconstruction]:
        weight = self._weight("classification")
        label = str(event.payload.get("label", "unnamed_classification"))
        target = str(event.payload.get("target_process_id") or "relation")
        score = float(event.payload.get("transition_score", weight))
        owners = set(state.processes)
        owners.add(target)
        return [
            self._memory(
                state,
                owner,
                event,
                f"classified_as:{label}",
                clamp(weight * 0.5 + score * 0.5),
                -0.48 if owner == target else -0.36,
                clamp(0.54 + score * 0.3),
                ["operative_label", label],
            )
            for owner in owners
            if owner in state.processes
        ]

    def _recognition_memories(self, state: SimulationState, event: Event) -> list[MemoryReconstruction]:
        outcome = str(event.payload.get("result", "none"))
        if outcome in {"granted", "partial"}:
            return []
        weight = self._weight("recognition_failure")
        holder = str(event.payload.get("holder", "p1"))
        demanded_from = str(event.payload.get("demanded_from", "p2"))
        salience_by_outcome = {
            "refused": 0.84,
            "misunderstood": 0.68,
            "unspeakable": 0.76,
            "displaced": 0.62,
            "postponed": 0.52,
        }
        base = salience_by_outcome.get(outcome, 0.45)
        memories = []
        if holder in state.processes:
            memories.append(
                self._memory(
                    state,
                    holder,
                    event,
                    f"recognition_failed:{outcome}",
                    clamp(weight * 0.45 + base * 0.55),
                    -0.58,
                    0.68,
                    ["injury_reconstruction", outcome],
                )
            )
        if demanded_from in state.processes:
            memories.append(
                self._memory(
                    state,
                    demanded_from,
                    event,
                    f"recognition_demand_became_threat:{outcome}",
                    clamp(weight * 0.35 + base * 0.45),
                    -0.34,
                    0.56,
                    ["defensive_reconstruction", outcome],
                )
            )
        return memories

    def _memory(
        self,
        state: SimulationState,
        owner: str,
        event: Event,
        remembered_as: str,
        salience: float,
        valence: float,
        confidence: float,
        biases: list[str],
    ) -> MemoryReconstruction:
        memory = MemoryTrace(
            memory_id=f"mem-{owner}-{event.event_id}",
            owner_process_id=owner,
            source_event_id=event.event_id,
            remembered_as=remembered_as,
            salience=clamp(salience),
            valence=max(-1.0, min(1.0, round(valence, 4))),
            confidence=clamp(confidence),
            reconstruction_biases=biases,
        )
        evidence = {
            "tick": state.tick,
            "source_event_type": event.event_type,
            "source_event_id": event.event_id,
            "remembered_as": remembered_as,
            "biases": biases,
        }
        return MemoryReconstruction(memory=memory, source_event_type=event.event_type, evidence=evidence)

    def _apply(self, state: SimulationState, reconstructions: list[MemoryReconstruction]) -> None:
        existing = {memory.memory_id for process in state.processes.values() for memory in process.memory_traces}
        for reconstruction in reconstructions:
            memory = reconstruction.memory
            if memory.memory_id in existing:
                continue
            state.processes[memory.owner_process_id].memory_traces.append(memory)
            existing.add(memory.memory_id)
            for bias in memory.reconstruction_biases:
                key = f"memory_bias.{bias}"
                state.relation_metrics[key] = clamp(state.relation_metrics.get(key, 0.0) + memory.salience)
        if reconstructions:
            state.relation_metrics["memory_reconstruction_count"] = state.relation_metrics.get("memory_reconstruction_count", 0.0) + len(reconstructions)
            state.relation_metrics["memory_pressure"] = clamp(
                state.relation_metrics.get("memory_pressure", 0.0)
                + sum(item.memory.salience for item in reconstructions) / max(1, len(state.processes)) * 0.1
            )

    def _weight(self, key: str) -> float:
        return float((self.config.get("source_weights") or {}).get(key, 0.5))
