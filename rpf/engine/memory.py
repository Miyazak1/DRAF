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
        future_constraints = [event for event in local_events if event.event_type == "FutureConstraintEvent"]
        candidates: list[MemoryReconstruction] = []
        for event in local_events:
            if event.event_type == "IrreversibilityEvent":
                candidates.extend(self._irreversibility_memories(state, event, future_constraints))
            elif event.event_type == "OperativeClassificationEvent":
                candidates.extend(self._classification_memories(state, event, future_constraints))
            elif event.event_type == "RecognitionEvent":
                candidates.extend(self._recognition_memories(state, event, future_constraints))
            elif event.event_type == "InvestigationUpdateEvent":
                candidates.extend(self._inquiry_memories(state, event, future_constraints))
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

    def _irreversibility_memories(
        self,
        state: SimulationState,
        event: Event,
        future_constraints: list[Event],
    ) -> list[MemoryReconstruction]:
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
                        self._future_context(str(owner), future_constraints),
                    )
                )
        return memories

    def _inquiry_memories(
        self,
        state: SimulationState,
        event: Event,
        future_constraints: list[Event],
    ) -> list[MemoryReconstruction]:
        weight = max(self._weight("inquiry"), 0.72)
        payload = event.payload
        focus_id = str(payload.get("focus_id", "case_focus"))
        focus_type = str(payload.get("focus_type", "case"))
        label = str(payload.get("label", focus_id))
        movement = str(payload.get("movement", "case_pressure_sediments"))
        state_after = payload.get("state_after", {}) or {}
        progress = self._dict_float(state_after, "progress")
        contamination = self._dict_float(state_after, "contamination")
        suppression = self._dict_float(state_after, "suppression")
        relationship_risk = self._dict_float(state_after, "relationship_risk")
        salience = clamp(weight * 0.28 + progress * 0.18 + contamination * 0.22 + suppression * 0.14 + relationship_risk * 0.18)
        if salience < self.config.get("min_salience", 0.35):
            return []
        base_biases = ["case_memory_contamination", focus_type, movement]
        if contamination >= 0.68:
            base_biases.append("evidence_contamination_memory")
        if suppression >= 0.28:
            base_biases.append("testimony_retraction_pressure")
        if relationship_risk >= 0.12:
            base_biases.append("relationalized_case_memory")
        memories = []
        if "p1" in state.processes:
            memories.append(
                self._memory(
                    state,
                    "p1",
                    event,
                    f"case_memory:p1:{focus_id}:{label}",
                    salience,
                    -0.62 if focus_type in {"testimonies", "evidence_items"} else -0.48,
                    clamp(0.56 + progress * 0.18 - contamination * 0.16),
                    [*base_biases, "witness_memory_destabilized"],
                    self._future_context("p1", future_constraints, {"memory_integration", "truth_integration", "recognition_access"}),
                )
            )
        if "p2" in state.processes:
            memories.append(
                self._memory(
                    state,
                    "p2",
                    event,
                    f"case_memory:p2:{focus_id}:{label}",
                    clamp(salience * 0.92 + progress * 0.06),
                    -0.36 if focus_type != "unverified_anomalies" else -0.44,
                    clamp(0.62 + progress * 0.16 - contamination * 0.12),
                    [*base_biases, "investigative_fixation"],
                    self._future_context("p2", future_constraints, {"truth_integration", "speech_access", "repair_availability"}),
                )
            )
        return memories

    def _classification_memories(
        self,
        state: SimulationState,
        event: Event,
        future_constraints: list[Event],
    ) -> list[MemoryReconstruction]:
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
                self._future_context(
                    owner,
                    future_constraints,
                    {"truth_integration", "recognition_access", "memory_integration"},
                ),
            )
            for owner in owners
            if owner in state.processes
        ]

    def _recognition_memories(
        self,
        state: SimulationState,
        event: Event,
        future_constraints: list[Event],
    ) -> list[MemoryReconstruction]:
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
                    self._future_context(
                        holder,
                        future_constraints,
                        {"recognition_access", "repair_availability", "memory_integration"},
                    ),
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
                    self._future_context(
                        demanded_from,
                        future_constraints,
                        {"speech_access", "face_continuation", "repair_availability"},
                    ),
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
        future_context: dict[str, Any] | None = None,
    ) -> MemoryReconstruction:
        future_context = future_context or {"future_constraint_pressure": 0.0, "future_constraint_refs": []}
        future_pressure = clamp(float(future_context.get("future_constraint_pressure", 0.0)))
        memory = MemoryTrace(
            memory_id=f"mem-{owner}-{event.event_id}",
            owner_process_id=owner,
            source_event_id=event.event_id,
            remembered_as=remembered_as,
            salience=clamp(salience + future_pressure * 0.06 + self._relevance_pressure(state, owner, biases) * 0.08),
            valence=max(-1.0, min(1.0, round(valence, 4))),
            confidence=clamp(confidence + future_pressure * 0.03 + self._relevance_pressure(state, owner, biases) * 0.035),
            reconstruction_biases=biases,
        )
        relevance_pressure = self._relevance_pressure(state, owner, biases)
        evidence = {
            "tick": state.tick,
            "source_event_type": event.event_type,
            "source_event_id": event.event_id,
            "remembered_as": remembered_as,
            "biases": biases,
            "relevance_pressure": relevance_pressure,
        }
        if future_context.get("future_constraint_refs"):
            evidence["future_constraint_pressure"] = future_pressure
            evidence["future_constraint_refs"] = list(future_context["future_constraint_refs"])
        return MemoryReconstruction(memory=memory, source_event_type=event.event_type, evidence=evidence)

    def _future_context(
        self,
        owner: str,
        future_constraints: list[Event],
        relevant_requirements: set[str] | None = None,
    ) -> dict[str, Any]:
        matches: list[Event] = []
        for event in future_constraints:
            payload = event.payload
            affected = {str(item) for item in payload.get("affected_processes", [])}
            constrained = {str(item) for item in payload.get("constrained_requirements", [])}
            owner_match = owner in affected or "relation" in affected
            requirement_match = not relevant_requirements or bool(constrained.intersection(relevant_requirements))
            if owner_match and requirement_match:
                matches.append(event)
        if not matches:
            return {"future_constraint_pressure": 0.0, "future_constraint_refs": []}
        pressure = max((self._payload_float(event, "intensity") for event in matches), default=0.0)
        return {
            "future_constraint_pressure": clamp(pressure),
            "future_constraint_refs": sorted({event.event_id for event in matches}),
        }

    def _payload_float(self, event: Event, key: str) -> float:
        try:
            return clamp(float(event.payload.get(key, 0.0)))
        except (TypeError, ValueError):
            return 0.0

    def _dict_float(self, data: dict[str, Any], key: str) -> float:
        try:
            return clamp(float(data.get(key, 0.0)))
        except (TypeError, ValueError):
            return 0.0

    def _relevance_pressure(self, state: SimulationState, owner: str, biases: list[str]) -> float:
        markers = set()
        if {"injury_reconstruction", "misunderstood", "refused"}.intersection(biases):
            markers.add("recognition_claim")
        if {"defensive_reconstruction", "postponed", "unspeakable"}.intersection(biases):
            markers.add("exit_threat")
            markers.add("delayed_reply")
        if "fate_lock" in biases:
            markers.add("double_bind")
        values = [
            state.relation_metrics.get(f"relevance_field.{owner}.{marker}", 0.0)
            for marker in markers
        ]
        return clamp(max(values, default=0.0))

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
