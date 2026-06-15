from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from rpf.core.events import Event
from rpf.core.models import ProcessState, SimulationState, clamp


@dataclass(frozen=True)
class DispositionSedimentation:
    process_id: str
    changed_path: str
    previous_value: float
    new_value: float
    reason: str
    causal_refs: list[str]

    def payload(self) -> dict[str, Any]:
        return {
            "process_id": self.process_id,
            "changed_path": self.changed_path,
            "previous_value": self.previous_value,
            "new_value": self.new_value,
            "delta": round(self.new_value - self.previous_value, 4),
            "reason": self.reason,
            "caused_by_events": self.causal_refs,
        }


class ProcessDispositionEngine:
    """Sediment repeated relational evidence into process-level tendencies.

    These are not personality primitives. They are bounded process dispositions
    formed from memory, field sedimentation, and recurring relation patterns.
    """

    def update(self, state: SimulationState, local_events: list[Event]) -> list[DispositionSedimentation]:
        updates: list[DispositionSedimentation] = []
        updates.extend(self._decay_sediments(state, local_events))
        updates.extend(self._memory_updates(state, local_events))
        updates.extend(self._environment_updates(state, local_events))
        updates.extend(self._rpp_updates(state, local_events))
        updates.extend(self._relation_updates(state, local_events))
        return updates

    def _decay_sediments(self, state: SimulationState, local_events: list[Event]) -> list[DispositionSedimentation]:
        tick_refs = [event.event_id for event in local_events if event.event_type == "TickStartedEvent"]
        refs = tick_refs[-1:] or [event.event_id for event in local_events[:1]]
        updates: list[DispositionSedimentation] = []
        prefix = "disposition_sediment."
        for sediment_key, sediment_value in list(state.relation_metrics.items()):
            if not sediment_key.startswith(prefix):
                continue
            parts = sediment_key.split(".", 2)
            if len(parts) != 3:
                continue
            _, process_id, path = parts
            process = state.processes.get(process_id)
            if not process:
                continue
            sediment = float(sediment_value)
            if abs(sediment) <= 0.0001:
                continue
            decay_amount = min(abs(sediment), 0.0035)
            sediment_delta = decay_amount if sediment < 0 else -decay_amount
            reverse_delta = -sediment_delta
            update = self._path_delta(
                process,
                path,
                reverse_delta,
                "process disposition sediment decays when not reinforced",
                refs,
            )
            state.relation_metrics[sediment_key] = round(sediment + sediment_delta, 4)
            if update.previous_value != update.new_value:
                updates.append(update)
        return updates

    def _memory_updates(self, state: SimulationState, local_events: list[Event]) -> list[DispositionSedimentation]:
        updates: list[DispositionSedimentation] = []
        for event in local_events:
            if event.event_type != "MemoryReconstructionEvent":
                continue
            process_id = str(event.payload.get("owner_process_id", ""))
            process = state.processes.get(process_id)
            if not process:
                continue
            biases = {str(item) for item in event.payload.get("reconstruction_biases", [])}
            salience = self._payload_float(event, "salience")
            refs = [event.event_id]
            evidence = event.payload.get("evidence", {})
            if isinstance(evidence, dict):
                refs.extend(str(ref) for ref in evidence.get("future_constraint_refs", []))
            if "injury_reconstruction" in biases:
                updates.append(
                    self._scalar_update(
                        state,
                        process,
                        "checking_tendency",
                        salience * 0.018,
                        "injury memory increases checking as a process tendency",
                        refs,
                    )
                )
                updates.append(
                    self._scalar_update(
                        state,
                        process,
                        "ambiguity_tolerance",
                        -salience * 0.012,
                        "injury memory narrows tolerance for ambiguous signals",
                        refs,
                    )
                )
            if "defensive_reconstruction" in biases:
                updates.append(
                    self._map_update(
                        state,
                        process,
                        "speech_inhibition",
                        "direct_need",
                        salience * 0.014,
                        "defensive memory raises direct-need inhibition",
                        refs,
                    )
                )
            if "fate_lock" in biases:
                updates.append(
                    self._scalar_update(
                        state,
                        process,
                        "risk_suspension_scope",
                        -salience * 0.01,
                        "fate memory reduces available risk suspension",
                        refs,
                    )
                )
        return [update for update in updates if update.previous_value != update.new_value]

    def _environment_updates(self, state: SimulationState, local_events: list[Event]) -> list[DispositionSedimentation]:
        updates: list[DispositionSedimentation] = []
        for event in local_events:
            if event.event_type != "FieldUpdateEvent":
                continue
            path = str(event.payload.get("changed_field_path", ""))
            if "avoidance_paths" in path:
                for process in state.processes.values():
                    updates.append(
                        self._map_update(
                            state,
                            process,
                            "speech_inhibition",
                            "direct_need",
                            0.004,
                            "sedimented avoidance paths make direct approach slightly less available",
                            [event.event_id],
                        )
                    )
            elif "imagined_audience" in path or "reputational_echo" in path:
                for process in state.processes.values():
                    updates.append(
                        self._map_update(
                            state,
                            process,
                            "threat_sensitivity",
                            "public_exposure",
                            0.004,
                            "sedimented audience pressure increases exposure sensitivity",
                            [event.event_id],
                        )
                    )
            elif "charged_objects" in path or "symbolic_debt_objects" in path:
                p1 = state.processes.get("p1")
                if p1:
                    updates.append(
                        self._scalar_update(
                            state,
                            p1,
                            "resentment_pressure",
                            0.004,
                            "charged objects keep moral accounting available",
                            [event.event_id],
                        )
                    )
        return [update for update in updates if update.previous_value != update.new_value]

    def _rpp_updates(self, state: SimulationState, local_events: list[Event]) -> list[DispositionSedimentation]:
        updates: list[DispositionSedimentation] = []
        for event in local_events:
            if event.event_type != "RPPActivationEvent":
                continue
            rpp_id = str(event.payload.get("rpp_id", ""))
            score = self._payload_float(event, "activation_score")
            refs = [event.event_id]
            refs.extend(str(ref) for ref in event.payload.get("eligibility_evidence", []) if str(ref).endswith("FutureConstraintEvent"))
            if rpp_id == "recognition_pursuit" and "p1" in state.processes:
                updates.append(
                    self._scalar_update(
                        state,
                        state.processes["p1"],
                        "checking_tendency",
                        score * 0.006,
                        "repeated recognition pursuit sediments as checking tendency",
                        refs,
                    )
                )
            elif rpp_id == "repair_avoidance" and "p2" in state.processes:
                updates.append(
                    self._map_update(
                        state,
                        state.processes["p2"],
                        "speech_inhibition",
                        "apology",
                        score * 0.006,
                        "repeated repair avoidance sediments as apology inhibition",
                        refs,
                    )
                )
        return [update for update in updates if update.previous_value != update.new_value]

    def _relation_updates(self, state: SimulationState, local_events: list[Event]) -> list[DispositionSedimentation]:
        updates: list[DispositionSedimentation] = []
        for event in local_events:
            if event.event_type != "RelationSedimentationEvent":
                continue
            delta = self._payload_float(event, "delta")
            if delta <= 0.0:
                continue
            metric = str(event.payload.get("metric", ""))
            refs = [event.event_id]
            if metric == "relation_sediment.recognition_debt" and "p1" in state.processes:
                updates.append(
                    self._scalar_update(
                        state,
                        state.processes["p1"],
                        "checking_tendency",
                        delta * 0.03,
                        "relation-level recognition debt sediments as increased checking",
                        refs,
                    )
                )
                updates.append(
                    self._scalar_update(
                        state,
                        state.processes["p1"],
                        "ambiguity_tolerance",
                        -delta * 0.02,
                        "relation-level recognition debt narrows tolerance for ambiguous signals",
                        refs,
                    )
                )
            elif metric == "relation_sediment.repair_access_narrowing":
                if "p2" in state.processes:
                    updates.append(
                        self._map_update(
                            state,
                            state.processes["p2"],
                            "speech_inhibition",
                            "apology",
                            delta * 0.025,
                            "relation-level repair narrowing sediments as apology inhibition",
                            refs,
                        )
                    )
                for process in state.processes.values():
                    updates.append(
                        self._map_update(
                            state,
                            process,
                            "speech_inhibition",
                            "direct_need",
                            delta * 0.012,
                            "relation-level repair narrowing makes direct need harder to express",
                            refs,
                        )
                    )
            elif metric in {"relation_sediment.public_definition_load", "relation_sediment.asymmetry_load"}:
                for process in state.processes.values():
                    updates.append(
                        self._map_update(
                            state,
                            process,
                            "threat_sensitivity",
                            "public_exposure",
                            delta * 0.02,
                            "relation-level definition pressure sediments as exposure sensitivity",
                            refs,
                        )
                    )
            elif metric in {"relation_sediment.future_lock_load", "relation_sediment.shared_fate_load"}:
                for process in state.processes.values():
                    updates.append(
                        self._scalar_update(
                            state,
                            process,
                            "risk_suspension_scope",
                            -delta * 0.014,
                            "relation-level fate load reduces available risk suspension",
                            refs,
                        )
                    )
        return [update for update in updates if update.previous_value != update.new_value]

    def _scalar_update(
        self,
        state: SimulationState,
        process: ProcessState,
        field: str,
        delta: float,
        reason: str,
        refs: list[str],
    ) -> DispositionSedimentation:
        previous = float(getattr(process, field))
        new_value = clamp(previous + delta)
        setattr(process, field, new_value)
        update = DispositionSedimentation(
            process_id=process.process_id,
            changed_path=field,
            previous_value=round(previous, 4),
            new_value=new_value,
            reason=reason,
            causal_refs=sorted(set(refs)),
        )
        self._record_sediment(state, process, field, update.new_value - update.previous_value)
        return update

    def _map_update(
        self,
        state: SimulationState,
        process: ProcessState,
        field: str,
        key: str,
        delta: float,
        reason: str,
        refs: list[str],
    ) -> DispositionSedimentation:
        target = getattr(process, field)
        previous = float(target.get(key, 0.0))
        new_value = clamp(previous + delta)
        target[key] = new_value
        path = f"{field}.{key}"
        update = DispositionSedimentation(
            process_id=process.process_id,
            changed_path=path,
            previous_value=round(previous, 4),
            new_value=new_value,
            reason=reason,
            causal_refs=sorted(set(refs)),
        )
        self._record_sediment(state, process, path, update.new_value - update.previous_value)
        return update

    def _path_delta(
        self,
        process: ProcessState,
        path: str,
        delta: float,
        reason: str,
        refs: list[str],
    ) -> DispositionSedimentation:
        if "." in path:
            field, key = path.split(".", 1)
            target = getattr(process, field)
            previous = float(target.get(key, 0.0))
            new_value = clamp(previous + delta)
            target[key] = new_value
        else:
            previous = float(getattr(process, path))
            new_value = clamp(previous + delta)
            setattr(process, path, new_value)
        return DispositionSedimentation(
            process_id=process.process_id,
            changed_path=path,
            previous_value=round(previous, 4),
            new_value=new_value,
            reason=reason,
            causal_refs=sorted(set(refs)),
        )

    def _record_sediment(self, state: SimulationState, process: ProcessState, path: str, delta: float) -> None:
        if abs(delta) <= 0.0001:
            return
        key = f"disposition_sediment.{process.process_id}.{path}"
        state.relation_metrics[key] = round(float(state.relation_metrics.get(key, 0.0)) + delta, 4)


    def _payload_float(self, event: Event, key: str) -> float:
        try:
            return clamp(float(event.payload.get(key, 0.0)))
        except (TypeError, ValueError):
            return 0.0
