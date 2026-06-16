from __future__ import annotations

import json
import random
import shutil
import time
import uuid
from pathlib import Path
from typing import Any

from rpf.core.events import Event
from rpf.config import effective_config
from rpf.core.models import (
    ActiveRPP,
    CoPresenceBinding,
    FieldState,
    IrreversibleRecord,
    OperativeClassification,
    ProcessState,
    RecognitionDemand,
    SimulationState,
    TickContext,
    clamp,
)
from rpf.core.local_world import LocalWorldSpec
from rpf.engine.aggregation import aggregate_views
from rpf.engine.actions import ActionSelectionEngine
from rpf.engine.account import AccountPressureEngine
from rpf.engine.affordances import AffordanceEngine
from rpf.engine.attention import AttentionDriftEngine
from rpf.engine.binding import BindingEvolutionEngine
from rpf.engine.common_ground import CommonGroundEngine
from rpf.engine.disposition import ProcessDispositionEngine
from rpf.engine.epistemic import EpistemicBoundaryEngine
from rpf.engine.expression import ExpressionEngine
from rpf.engine.environment import EnvironmentSedimentationEngine
from rpf.engine.expectation import ExpectationSedimentationEngine
from rpf.engine.fate import FateTransitionEngine
from rpf.engine.inquiry import InquiryEngine
from rpf.engine.interaction_frame import InteractionFrameEngine
from rpf.engine.local_world import LocalWorldEngine
from rpf.engine.memory import MemoryReconstructionEngine
from rpf.engine.metrics import compute_metrics
from rpf.engine.normativity import NormativePressureEngine
from rpf.engine.opportunity import OpportunityCostEngine
from rpf.engine.positioning import PositioningEngine
from rpf.engine.recognition import RecognitionEngine
from rpf.engine.relevance import RelevanceLandscapeEngine
from rpf.engine.reversibility import ActionReversibilityEngine
from rpf.engine.relation import RelationSedimentationEngine
from rpf.engine.rpp_dynamics import RPPDynamics
from rpf.engine.scheduler import TemporalScheduler
from rpf.engine.viability import RelationalViabilityEngine
from rpf.rpps import (
    ComplementaryDependencyRPP,
    ContributionDebtLoopRPP,
    DoubleBindRPP,
    FaceSavingLoopRPP,
    PublicPrivateSplitRPP,
    PursuitWithdrawalRPP,
    RecognitionPursuitRPP,
    RepairAvoidanceRPP,
    SilenceInterpretationLoopRPP,
)
from rpf.storage.snapshots import write_snapshot
from rpf.storage.timeline import TimelineWriter, write_timeline_manifest
from rpf.storage import RunStore, configured_run_store
from rpf.core.versioning import manifest
from rpf.core.semantics import material_urgency, set_material_urgency, unrecognized_contribution


class Simulator:
    def __init__(
        self,
        state: SimulationState,
        scenario_path: Path,
        config: dict[str, Any],
        render_canon: dict[str, Any] | None = None,
        case_ledger: dict[str, Any] | None = None,
        local_world: dict[str, Any] | None = None,
        object_registry: dict[str, Any] | None = None,
        steps: int | None = None,
        run_store: RunStore | None = None,
        run_id: str | None = None,
    ) -> None:
        self.state = state
        self.scenario_path = scenario_path
        self.config = config
        self.render_canon = render_canon or {}
        self.case_ledger = case_ledger or {}
        self.local_world_spec = local_world or {}
        self.object_registry = object_registry or {}
        local_world_spec = LocalWorldSpec.model_validate(local_world) if local_world else None
        self.local_world = LocalWorldEngine(local_world_spec)
        self.steps = steps
        self.run_id = run_id or str(uuid.uuid4())
        self.run_store = run_store or configured_run_store()
        self.rng = random.Random(state.seed)
        self.scheduler = TemporalScheduler(config["scheduler"])
        self.affordances = AffordanceEngine(config["affordances"])
        self.actions = ActionSelectionEngine(config["action_selection"])
        self.expression = ExpressionEngine(config["expression"])
        self.recognition = RecognitionEngine(config["recognition"])
        self.fate = FateTransitionEngine(config["fate_transitions"])
        self.frame_definition = InteractionFrameEngine()
        self.account = AccountPressureEngine()
        self.binding_evolution = BindingEvolutionEngine()
        self.common_ground = CommonGroundEngine()
        self.epistemic = EpistemicBoundaryEngine()
        self.expectation = ExpectationSedimentationEngine()
        self.memory = MemoryReconstructionEngine(config["memory"])
        self.normativity = NormativePressureEngine()
        self.opportunity = OpportunityCostEngine()
        self.positioning = PositioningEngine()
        self.relevance = RelevanceLandscapeEngine()
        self.reversibility = ActionReversibilityEngine()
        self.attention = AttentionDriftEngine()
        self.environment = EnvironmentSedimentationEngine()
        self.disposition = ProcessDispositionEngine()
        self.relation = RelationSedimentationEngine()
        self.rpp_dynamics = RPPDynamics(config["rpp_dynamics"])
        self.viability = RelationalViabilityEngine()
        self.inquiry = InquiryEngine(self.case_ledger)
        self.rpps = [
            PursuitWithdrawalRPP(config["rpps"]["pursuit_withdrawal"]),
            RepairAvoidanceRPP(config["rpps"]["repair_avoidance"]),
            ContributionDebtLoopRPP(config["rpps"]["contribution_debt_loop"]),
            DoubleBindRPP(config["rpps"]["double_bind"]),
            PublicPrivateSplitRPP(config["rpps"]["public_private_split"]),
            SilenceInterpretationLoopRPP(config["rpps"]["silence_interpretation_loop"]),
            ComplementaryDependencyRPP(config["rpps"]["complementary_dependency"]),
            FaceSavingLoopRPP(config["rpps"]["face_saving_loop"]),
            RecognitionPursuitRPP(config["rpps"]["recognition_pursuit"]),
        ]
        self.events: list[Event] = []
        self.scheduler_diagnostics: list[dict[str, Any]] = []
        self.affordance_trace: list[dict[str, Any]] = []
        self.action_trace: list[dict[str, Any]] = []
        self.expression_trace: list[dict[str, Any]] = []
        self.recognition_trace: list[dict[str, Any]] = []
        self.fate_transition_trace: list[dict[str, Any]] = []
        self.frame_trace: list[dict[str, Any]] = []
        self.account_trace: list[dict[str, Any]] = []
        self.binding_trace: list[dict[str, Any]] = []
        self.common_ground_trace: list[dict[str, Any]] = []
        self.epistemic_trace: list[dict[str, Any]] = []
        self.expectation_trace: list[dict[str, Any]] = []
        self.memory_trace: list[dict[str, Any]] = []
        self.normativity_trace: list[dict[str, Any]] = []
        self.opportunity_trace: list[dict[str, Any]] = []
        self.position_trace: list[dict[str, Any]] = []
        self.relevance_trace: list[dict[str, Any]] = []
        self.reversibility_trace: list[dict[str, Any]] = []
        self.attention_trace: list[dict[str, Any]] = []
        self.environment_trace: list[dict[str, Any]] = []
        self.disposition_trace: list[dict[str, Any]] = []
        self.relation_trace: list[dict[str, Any]] = []
        self.viability_trace: list[dict[str, Any]] = []
        self.inquiry_trace: list[dict[str, Any]] = []
        self.rpp_activation_trace: list[dict[str, Any]] = []
        self.rpp_dynamics_trace: list[dict[str, Any]] = []
        self.projection_trace: list[dict[str, Any]] = []
        self.local_world_trace: list[dict[str, Any]] = []
        self.location_selection_trace: list[dict[str, Any]] = []
        self.route_selection_trace: list[dict[str, Any]] = []
        self.audience_exposure_trace: list[dict[str, Any]] = []
        self._order = 0

    @classmethod
    def from_scenario(
        cls,
        scenario: dict[str, Any],
        scenario_path: Path,
        seed: int,
        run_store: RunStore | None = None,
        run_id: str | None = None,
    ) -> "Simulator":
        processes = {}
        recognition_by_holder: dict[str, list[RecognitionDemand]] = {}
        for item in scenario.get("recognition_demands", []):
            demand = RecognitionDemand(**item)
            recognition_by_holder.setdefault(demand.holder_process_id, []).append(demand)
        for pid, data in scenario["processes"].items():
            processes[pid] = ProcessState(
                process_id=pid,
                display_name=data.get("display_name", pid),
                fatigue=data.get("fatigue", 0.0),
                speech_inhibition=data.get("speech_inhibition", {}),
                threat_sensitivity=data.get("threat_sensitivity", {}),
                relevance_triggers=data.get("relevance_triggers", {}),
                recognition_demands=recognition_by_holder.get(pid, []),
            )
        state = SimulationState(
            simulation_id=scenario["id"],
            seed=seed,
            field_state=FieldState(**scenario.get("field_state", {})),
            processes=processes,
            bindings=[CoPresenceBinding(**b) for b in scenario["bindings"]],
        )
        relation_metrics = scenario.get("relation_metrics", {}) or {}
        state.relation_metrics.update(relation_metrics)
        if "unrecognized_sacrifice" in relation_metrics and "unrecognized_contribution" not in relation_metrics:
            state.relation_metrics["unrecognized_contribution"] = relation_metrics["unrecognized_sacrifice"]
        return cls(
            state,
            scenario_path=scenario_path,
            config=effective_config(scenario),
            render_canon=_render_canon_for_scenario(scenario),
            case_ledger=scenario.get("case_ledger", {}),
            local_world=scenario.get("local_world"),
            object_registry=scenario.get("object_registry", {}),
            run_store=run_store,
            run_id=run_id,
        )

    def _event(self, event_type: str, source_layer: str, payload: dict[str, Any] | None = None, causal_refs: list[str] | None = None) -> Event:
        self._order += 1
        event = Event.make(self.state.tick, self._order, event_type, source_layer, payload, causal_refs)
        self.events.append(event)
        return event

    def run(self, steps: int, output_dir: Path) -> dict[str, Any]:
        self._prepare_output(output_dir, planned_steps=steps, mode="steps")
        for _ in range(steps):
            self.tick()
            if self.state.tick % 5 == 0:
                self._write_snapshot(output_dir)
        return self._complete_output(output_dir)

    def run_for_duration(
        self,
        *,
        target_seconds: int,
        output_dir: Path,
        max_steps: int = 10000,
        write_interval_ticks: int = 1,
        on_update: Any | None = None,
        should_stop: Any | None = None,
    ) -> dict[str, Any]:
        self._prepare_output(output_dir, planned_steps=0, target_seconds=target_seconds, mode="duration")
        elapsed_seconds = 0
        while elapsed_seconds < target_seconds and self.state.tick < max_steps:
            if should_stop and should_stop():
                break
            remaining_seconds = max(1, target_seconds - elapsed_seconds)
            context = self.tick(max_delta_seconds=remaining_seconds)
            elapsed_seconds += context.simulated_time_delta_seconds
            if self.state.tick % 5 == 0:
                self._write_snapshot(output_dir)
            if self.state.tick % max(1, write_interval_ticks) == 0:
                partial = self._write_outputs(output_dir, completed=False)
                if on_update:
                    on_update(partial | {"elapsed_seconds": elapsed_seconds, "target_seconds": target_seconds})
        result = self._complete_output(output_dir)
        result["elapsed_seconds"] = elapsed_seconds
        result["target_seconds"] = target_seconds
        if on_update:
            on_update(result)
        return result

    def run_for_wall_clock(
        self,
        *,
        duration_seconds: int,
        output_dir: Path,
        tick_interval_seconds: float = 30.0,
        max_steps: int = 10000,
        write_interval_ticks: int = 1,
        on_update: Any | None = None,
        should_stop: Any | None = None,
    ) -> dict[str, Any]:
        self._prepare_output(output_dir, planned_steps=0, target_wall_clock_seconds=duration_seconds, mode="wall_clock")
        started = time.monotonic()
        elapsed_seconds = 0.0
        while elapsed_seconds < duration_seconds and self.state.tick < max_steps:
            if should_stop and should_stop():
                break
            tick_started = time.monotonic()
            self.tick()
            elapsed_seconds = min(duration_seconds, time.monotonic() - started)
            if self.state.tick % 5 == 0:
                self._write_snapshot(output_dir)
            if self.state.tick % max(1, write_interval_ticks) == 0:
                partial = self._write_outputs(output_dir, completed=False)
                if on_update:
                    on_update(partial | {"elapsed_seconds": elapsed_seconds, "target_seconds": duration_seconds})
            sleep_for = tick_interval_seconds - (time.monotonic() - tick_started)
            remaining = duration_seconds - (time.monotonic() - started)
            if sleep_for > 0 and remaining > 0:
                time.sleep(min(sleep_for, remaining))
            elapsed_seconds = min(duration_seconds, time.monotonic() - started)
        result = self._complete_output(output_dir)
        result["elapsed_seconds"] = int(round(elapsed_seconds))
        result["target_seconds"] = duration_seconds
        if on_update:
            on_update(result)
        return result

    def _prepare_output(
        self,
        output_dir: Path,
        *,
        planned_steps: int,
        target_seconds: int | None = None,
        target_wall_clock_seconds: int | None = None,
        mode: str = "steps",
    ) -> None:
        if output_dir.exists():
            shutil.rmtree(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        self.steps = planned_steps
        (output_dir / "effective_config.json").write_text(json.dumps(self.config, indent=2), encoding="utf-8")
        (output_dir / "render_canon.json").write_text(
            json.dumps(self.render_canon, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        (output_dir / "object_registry.json").write_text(
            json.dumps(self.object_registry, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        write_timeline_manifest(output_dir, scenario_path=self.scenario_path, seed=self.state.seed, steps=planned_steps)
        self._begin_persistent_run(output_dir, mode=mode, planned_steps=planned_steps)
        self._event(
            "SimulationInitializedEvent",
            "diagnostic",
            {
                "scenario_path": str(self.scenario_path),
                "seed": self.state.seed,
                "steps": planned_steps,
                "target_seconds": target_seconds,
                "target_wall_clock_seconds": target_wall_clock_seconds,
                "initial_state_hash": self.state.state_hash(),
                "manifest": manifest(),
            },
        )
        self._write_outputs(output_dir, completed=False)

    def _complete_output(self, output_dir: Path) -> dict[str, Any]:
        views = aggregate_views(self.state, [e.event_id for e in self.events])
        final_hash = self.state.state_hash()
        self._event("SimulationCompletedEvent", "diagnostic", {"final_state_hash": final_hash, "steps": self.state.tick})
        result = self._write_outputs(output_dir, completed=True, views=views)
        write_timeline_manifest(output_dir, scenario_path=self.scenario_path, seed=self.state.seed, steps=self.state.tick)
        result["final_state_hash"] = final_hash
        return result

    def _write_outputs(
        self,
        output_dir: Path,
        *,
        completed: bool,
        views: Any | None = None,
    ) -> dict[str, Any]:
        output_dir.mkdir(parents=True, exist_ok=True)
        views = views or aggregate_views(self.state, [e.event_id for e in self.events])
        metrics = compute_metrics(self.events)
        with TimelineWriter(output_dir / "timeline.jsonl") as writer:
            for event in self.events:
                writer.write(event)
        (output_dir / "derived_views.json").write_text(views.model_dump_json(indent=2), encoding="utf-8")
        (output_dir / "aggregation_traces.json").write_text(json.dumps(self._aggregation_trace(views), indent=2), encoding="utf-8")
        (output_dir / "scheduler_diagnostics.json").write_text(json.dumps(self.scheduler_diagnostics, indent=2), encoding="utf-8")
        (output_dir / "affordance_trace.json").write_text(json.dumps(self.affordance_trace, indent=2), encoding="utf-8")
        (output_dir / "action_trace.json").write_text(json.dumps(self.action_trace, indent=2), encoding="utf-8")
        (output_dir / "expression_trace.json").write_text(json.dumps(self.expression_trace, indent=2), encoding="utf-8")
        (output_dir / "recognition_trace.json").write_text(json.dumps(self.recognition_trace, indent=2), encoding="utf-8")
        (output_dir / "fate_transition_trace.json").write_text(json.dumps(self.fate_transition_trace, indent=2), encoding="utf-8")
        (output_dir / "frame_trace.json").write_text(json.dumps(self.frame_trace, indent=2), encoding="utf-8")
        (output_dir / "account_trace.json").write_text(json.dumps(self.account_trace, indent=2), encoding="utf-8")
        (output_dir / "binding_trace.json").write_text(json.dumps(self.binding_trace, indent=2), encoding="utf-8")
        (output_dir / "common_ground_trace.json").write_text(json.dumps(self.common_ground_trace, indent=2), encoding="utf-8")
        (output_dir / "epistemic_trace.json").write_text(json.dumps(self.epistemic_trace, indent=2), encoding="utf-8")
        (output_dir / "expectation_trace.json").write_text(json.dumps(self.expectation_trace, indent=2), encoding="utf-8")
        (output_dir / "memory_trace.json").write_text(json.dumps(self.memory_trace, indent=2), encoding="utf-8")
        (output_dir / "normativity_trace.json").write_text(json.dumps(self.normativity_trace, indent=2), encoding="utf-8")
        (output_dir / "opportunity_trace.json").write_text(json.dumps(self.opportunity_trace, indent=2), encoding="utf-8")
        (output_dir / "position_trace.json").write_text(json.dumps(self.position_trace, indent=2), encoding="utf-8")
        (output_dir / "relevance_trace.json").write_text(json.dumps(self.relevance_trace, indent=2), encoding="utf-8")
        (output_dir / "reversibility_trace.json").write_text(json.dumps(self.reversibility_trace, indent=2), encoding="utf-8")
        (output_dir / "attention_trace.json").write_text(json.dumps(self.attention_trace, indent=2), encoding="utf-8")
        (output_dir / "environment_trace.json").write_text(json.dumps(self.environment_trace, indent=2), encoding="utf-8")
        (output_dir / "disposition_trace.json").write_text(json.dumps(self.disposition_trace, indent=2), encoding="utf-8")
        (output_dir / "relation_trace.json").write_text(json.dumps(self.relation_trace, indent=2), encoding="utf-8")
        (output_dir / "viability_trace.json").write_text(json.dumps(self.viability_trace, indent=2), encoding="utf-8")
        (output_dir / "inquiry_trace.json").write_text(json.dumps(self.inquiry_trace, indent=2), encoding="utf-8")
        (output_dir / "rpp_activation_trace.json").write_text(json.dumps(self.rpp_activation_trace, indent=2), encoding="utf-8")
        (output_dir / "rpp_dynamics_trace.json").write_text(json.dumps(self.rpp_dynamics_trace, indent=2), encoding="utf-8")
        (output_dir / "projection_trace.json").write_text(json.dumps(self.projection_trace, indent=2), encoding="utf-8")
        (output_dir / "local_world_trace.json").write_text(json.dumps(self.local_world_trace, indent=2), encoding="utf-8")
        (output_dir / "location_selection_trace.json").write_text(json.dumps(self.location_selection_trace, indent=2), encoding="utf-8")
        (output_dir / "route_selection_trace.json").write_text(json.dumps(self.route_selection_trace, indent=2), encoding="utf-8")
        (output_dir / "audience_exposure_trace.json").write_text(json.dumps(self.audience_exposure_trace, indent=2), encoding="utf-8")
        (output_dir / "irreversibility_report.json").write_text(self.state.irreversibility_register.model_dump_json(indent=2), encoding="utf-8")
        (output_dir / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
        self._persist_outputs(metrics=metrics, completed=completed)
        return {
            "output_dir": str(output_dir),
            "run_id": self.run_id,
            "storage_backend": self.run_store.backend_name,
            "final_state_hash": self.state.state_hash(),
            "completed": completed,
            "tick": self.state.tick,
            "metrics": metrics,
        }

    def _begin_persistent_run(self, output_dir: Path, *, mode: str, planned_steps: int) -> None:
        title = self.render_canon.get("title") or self.state.simulation_id
        source_yaml = self.scenario_path.read_text(encoding="utf-8") if self.scenario_path.exists() else ""
        if hasattr(self.run_store, "apply_migrations"):
            self.run_store.apply_migrations()  # type: ignore[attr-defined]
        self.run_store.upsert_scenario(
            scenario_id=self.state.simulation_id,
            title=str(title),
            source_yaml=source_yaml,
            source_path=self.scenario_path,
            render_canon=self.render_canon,
            case_ledger=self.case_ledger,
        )
        self.run_store.begin_run(
            run_id=self.run_id,
            scenario_id=self.state.simulation_id,
            title=str(title),
            seed=self.state.seed,
            mode=mode,
            output_dir=output_dir,
            metadata={
                "planned_steps": planned_steps,
                "scenario_path": str(self.scenario_path),
                "manifest": manifest(),
            },
        )

    def _write_snapshot(self, output_dir: Path) -> None:
        write_snapshot(output_dir, self.state)
        self.run_store.write_snapshot(run_id=self.run_id, state=self.state)

    def _persist_outputs(self, *, metrics: dict[str, Any], completed: bool) -> None:
        self.run_store.write_events(run_id=self.run_id, events=self.events)
        for layer, records in self._trace_records():
            self.run_store.write_traces(run_id=self.run_id, layer=layer, records=records)
        self.run_store.complete_run(
            run_id=self.run_id,
            status="completed" if completed else "running",
            tick_count=self.state.tick,
            event_count=int(metrics.get("event_count", len(self.events))),
            final_state_hash=self.state.state_hash() if completed else None,
        )

    def _trace_records(self) -> list[tuple[str, list[dict[str, Any]]]]:
        return [
            ("scheduler", self.scheduler_diagnostics),
            ("affordance", self.affordance_trace),
            ("action", self.action_trace),
            ("expression", self.expression_trace),
            ("recognition", self.recognition_trace),
            ("fate_transition", self.fate_transition_trace),
            ("frame", self.frame_trace),
            ("account", self.account_trace),
            ("binding", self.binding_trace),
            ("common_ground", self.common_ground_trace),
            ("epistemic", self.epistemic_trace),
            ("expectation", self.expectation_trace),
            ("memory", self.memory_trace),
            ("normativity", self.normativity_trace),
            ("opportunity", self.opportunity_trace),
            ("position", self.position_trace),
            ("relevance", self.relevance_trace),
            ("reversibility", self.reversibility_trace),
            ("attention", self.attention_trace),
            ("environment", self.environment_trace),
            ("disposition", self.disposition_trace),
            ("relation", self.relation_trace),
            ("viability", self.viability_trace),
            ("inquiry", self.inquiry_trace),
            ("rpp_activation", self.rpp_activation_trace),
            ("rpp_dynamics", self.rpp_dynamics_trace),
            ("projection", self.projection_trace),
            ("local_world", self.local_world_trace),
            ("location_selection", self.location_selection_trace),
            ("route_selection", self.route_selection_trace),
            ("audience_exposure", self.audience_exposure_trace),
        ]

    def tick(self, max_delta_seconds: int | None = None) -> TickContext:
        self.state.tick += 1
        self._order = 0
        viability_preview = self.viability.scheduler_preview(self.state)
        context = self.scheduler.decide(self.state, self.rng, viability_preview=viability_preview)
        if max_delta_seconds is not None and context.simulated_time_delta_seconds > max_delta_seconds:
            context = context.model_copy(update={"simulated_time_delta_seconds": max_delta_seconds})
            self.scheduler.last_diagnostics["simulated_time_delta_seconds"] = max_delta_seconds
            self.scheduler.last_diagnostics["time_clipped_to_target"] = True
        self.scheduler_diagnostics.append(dict(self.scheduler.last_diagnostics))
        tick_event = self._event(
            "TickStartedEvent",
            "diagnostic",
            {
                "tick_type": context.tick_type,
                "simulated_time_delta": context.simulated_time_delta_seconds,
                "time_mapping_reason": context.time_mapping_reason,
                "scheduler_diagnostics": self.scheduler.last_diagnostics,
            },
        )
        local: list[Event] = [tick_event]
        local.extend(self._update_local_world(context, [tick_event.event_id]))
        local.extend(self._field_and_binding_events(context))
        viability_history = local + self._recent_relation_sedimentation_events()
        viability_pre = self.viability.evaluate_pre_response(self.state, context, viability_history)
        local.extend(self._emit_viability_events(viability_pre, phase="pre_response"))
        if context.tick_type == "latent":
            local.append(self._event("LatentTimeEvent", "scene", {"tick_type": "latent", "accumulated_pressures": self.state.relation_metrics.copy()}))
        else:
            local.extend(self._scene_and_signal_events(context, local))
        viability_post = self.viability.evaluate_post_response(self.state, context, viability_pre, local + self._recent_relation_sedimentation_events())
        local.extend(self._emit_viability_events(viability_post, phase="post_response"))
        self.viability_trace.append(viability_post.model_dump(mode="json"))
        local.extend(self._activate_rpps(context, local))
        local.extend(self._update_rpp_dynamics(local))
        if context.tick_type == "scene":
            local.extend(self._recognition_and_repair(local))
        local.extend(self._update_inquiry(context, local))
        local.extend(self._update_epistemic_boundaries(context, local))
        local.extend(self._classification_and_irreversibility(local))
        local.extend(self._update_memory(local))
        prior_relation_events = self._previous_tick_relation_sedimentation_events()
        local.extend(self._update_environment(local + prior_relation_events))
        local.extend(self._update_dispositions(local + prior_relation_events))
        prior_normativity_events = self._previous_tick_normativity_events()
        local.extend(self._update_relation(local + prior_normativity_events))
        local.extend(self._update_bindings(local))
        local.extend(self._update_expectations(local))
        local.extend(self._update_accounts(local))
        local.extend(self._update_normativity(local))
        local.extend(self._update_frames(local))
        local.extend(self._update_common_ground(context, local))
        local.extend(self._update_attention(context, local))
        if context.tick_type != "latent":
            local.extend(self._update_opportunity_costs(context, local))
            local.extend(self._update_action_reversibility(context, local))
        local.extend(self._update_relevance(local))
        local.extend(self._update_positions(local))
        views = aggregate_views(self.state, [e.event_id for e in self.events])
        self._event("AggregationEvent", "aggregation", {"trust_view": views.trust_view, "resentment_pressure_view": views.resentment_pressure_view}, [e.event_id for e in local[-5:]])
        self._event("ProjectionEvent", "projection", {"relationship_phase": views.relationship_view.phase_label, "person_labels": {k: v.apparent_labels for k, v in views.person_views.items()}}, [e.event_id for e in local[-5:]])
        self.projection_trace.append(
            {
                "tick": self.state.tick,
                "tick_type": context.tick_type,
                "relationship_phase": views.relationship_view.phase_label,
                "person_labels": {k: v.apparent_labels for k, v in views.person_views.items()},
                "evidence_refs": views.relationship_view.evidence_refs,
            }
        )
        return context

    def _update_inquiry(self, context: TickContext, local_events: list[Event]) -> list[Event]:
        emitted: list[Event] = []
        for update in self.inquiry.update(self.state, context, local_events):
            payload = update.payload
            self.inquiry_trace.append({"tick": self.state.tick, "event_type": update.event_type, **payload})
            emitted.append(
                self._event(
                    update.event_type,
                    "inquiry",
                    payload,
                    update.causal_refs,
                )
            )
        return emitted

    def _update_epistemic_boundaries(self, context: TickContext, local_events: list[Event]) -> list[Event]:
        emitted: list[Event] = []
        for update in self.epistemic.update(self.state, context, local_events):
            payload = update.payload()
            self.epistemic_trace.append({"tick": self.state.tick, "event_type": "EpistemicBoundaryEvent", **payload})
            emitted.append(
                self._event(
                    "EpistemicBoundaryEvent",
                    "epistemic",
                    payload,
                    update.causal_refs,
                )
            )
        return emitted

    def _recent_relation_sedimentation_events(self, limit: int = 8) -> list[Event]:
        events = [
            event
            for event in reversed(self.events)
            if event.event_type == "RelationSedimentationEvent"
        ]
        return list(reversed(events[:limit]))

    def _previous_tick_relation_sedimentation_events(self) -> list[Event]:
        previous_tick = self.state.tick - 1
        return [
            event
            for event in self.events
            if event.event_type == "RelationSedimentationEvent" and event.tick == previous_tick
        ]

    def _previous_tick_normativity_events(self) -> list[Event]:
        previous_tick = self.state.tick - 1
        return [
            event
            for event in self.events
            if event.event_type == "NormativePressureEvent" and event.tick == previous_tick
        ]

    def _emit_viability_events(self, trace: Any, *, phase: str) -> list[Event]:
        emitted: list[Event] = []
        for event_type, payload, evidence_refs in self.viability.event_payloads(trace):
            if phase == "pre_response" and event_type in {"DeformationTraceEvent", "DerivedDramaticTensionEvent"}:
                continue
            if phase == "post_response" and event_type not in {"DeformationTraceEvent", "DerivedDramaticTensionEvent"}:
                continue
            emitted.append(self._event(event_type, "viability", payload, evidence_refs))
        return emitted

    def _update_local_world(self, context: TickContext, causal_refs: list[str]) -> list[Event]:
        update = self.local_world.advance(context, causal_refs=causal_refs)
        if not update.traces:
            return []
        self._apply_local_world_pressure_snapshot()
        self.local_world_trace.extend(update.traces)
        return [
            self._event(event_type, "local_world", payload, refs)
            for event_type, payload, refs in update.events
        ]

    def _apply_local_world_pressure_snapshot(self) -> None:
        snapshot = self.local_world.pressure_snapshot()
        if not snapshot:
            return
        route_pressure = clamp(float(snapshot.get("blocked_route_pressure") or 0.0))
        public_pressure = clamp(float(snapshot.get("public_visibility_pressure") or 0.0))
        memory_pressure_value = clamp(float(snapshot.get("memory_site_pressure") or 0.0))
        resource_pressure = clamp(float(snapshot.get("resource_scarcity_pressure") or 0.0))
        self.state.relation_metrics.update(
            {
                "local_world.blocked_route_pressure": route_pressure,
                "local_world.public_visibility_pressure": public_pressure,
                "local_world.memory_site_pressure": memory_pressure_value,
                "local_world.resource_scarcity_pressure": resource_pressure,
            }
        )
        self.state.field_state.spatial_constraints["local_world_route_blockage"] = route_pressure
        self.state.field_state.spatial_constraints["local_world_memory_site"] = memory_pressure_value
        self.state.field_state.audience_pressure["local_world_public_visibility"] = public_pressure
        self.state.field_state.material_pressures["local_world_resource_scarcity"] = resource_pressure

    def _field_and_binding_events(self, context: TickContext) -> list[Event]:
        events: list[Event] = []
        urgency = material_urgency(self.state) or 0.35
        set_material_urgency(self.state, clamp(urgency + 0.025))
        for demand in self.state.processes["p1"].recognition_demands:
            demand.current_pressure = clamp(demand.current_pressure + 0.025)
        events.append(self._event("FieldPressureEvent", "material", {"pressure_type": "material_urgency", "intensity": material_urgency(self.state), "tick_type": context.tick_type}))
        for binding in self.state.bindings:
            events.append(self._event("BindingActivatedEvent", "binding", {"binding_id": binding.binding_id, "binding_type": binding.binding_type, "strength": binding.strength, "exit_cost": binding.exit_cost}))
        return events

    def _update_bindings(self, local_events: list[Event]) -> list[Event]:
        emitted: list[Event] = []
        updates = self.binding_evolution.update(self.state, local_events)
        for update in updates:
            payload = update.payload()
            self.binding_trace.append({"tick": self.state.tick, "event_type": update.event_type, **payload})
            emitted.append(
                self._event(
                    update.event_type,
                    "binding",
                    payload,
                    update.causal_refs,
                )
            )
        return emitted

    def _update_expectations(self, local_events: list[Event]) -> list[Event]:
        emitted: list[Event] = []
        updates = self.expectation.update(self.state, local_events)
        for update in updates:
            payload = update.payload()
            self.expectation_trace.append({"tick": self.state.tick, **payload})
            emitted.append(
                self._event(
                    "ExpectationSedimentationEvent",
                    "expectation",
                    payload,
                    update.causal_refs,
                )
            )
        return emitted

    def _update_accounts(self, local_events: list[Event]) -> list[Event]:
        emitted: list[Event] = []
        updates = self.account.update(self.state, local_events)
        for update in updates:
            payload = update.payload()
            self.account_trace.append({"tick": self.state.tick, **payload})
            emitted.append(
                self._event(
                    "AccountPressureEvent",
                    "account",
                    payload,
                    update.causal_refs,
                )
            )
        return emitted

    def _update_normativity(self, local_events: list[Event]) -> list[Event]:
        emitted: list[Event] = []
        updates = self.normativity.update(self.state, local_events)
        for update in updates:
            payload = update.payload()
            self.normativity_trace.append({"tick": self.state.tick, **payload})
            emitted.append(
                self._event(
                    "NormativePressureEvent",
                    "normativity",
                    payload,
                    update.causal_refs,
                )
            )
        return emitted

    def _update_frames(self, local_events: list[Event]) -> list[Event]:
        emitted: list[Event] = []
        updates = self.frame_definition.update(self.state, local_events)
        for update in updates:
            payload = update.payload()
            self.frame_trace.append({"tick": self.state.tick, **payload})
            emitted.append(
                self._event(
                    "FrameDefinitionEvent",
                    "frame",
                    payload,
                    update.causal_refs,
                )
            )
        return emitted

    def _update_common_ground(self, context: TickContext, local_events: list[Event]) -> list[Event]:
        update = self.common_ground.update(self.state, context, local_events)
        if not update:
            return []
        payload = update.payload()
        self.common_ground_trace.append({"tick": self.state.tick, "event_type": "CommonGroundEvent", **payload})
        return [
            self._event(
                "CommonGroundEvent",
                "common_ground",
                payload,
                update.causal_refs,
            )
        ]

    def _update_relevance(self, local_events: list[Event]) -> list[Event]:
        emitted: list[Event] = []
        updates = self.relevance.update(self.state, local_events)
        for update in updates:
            payload = update.payload()
            self.relevance_trace.append({"tick": self.state.tick, **payload})
            emitted.append(
                self._event(
                    "RelevanceShiftEvent",
                    "relevance",
                    payload,
                    update.causal_refs,
                )
            )
        return emitted

    def _update_attention(self, context: TickContext, local_events: list[Event]) -> list[Event]:
        emitted: list[Event] = []
        updates = self.attention.update(self.state, context, local_events)
        for update in updates:
            payload = update.payload()
            self.attention_trace.append({"tick": self.state.tick, "event_type": "AttentionDriftEvent", **payload})
            emitted.append(
                self._event(
                    "AttentionDriftEvent",
                    "attention",
                    payload,
                    update.causal_refs,
                )
            )
        return emitted

    def _update_opportunity_costs(self, context: TickContext, local_events: list[Event]) -> list[Event]:
        emitted: list[Event] = []
        updates = self.opportunity.update(self.state, context, local_events)
        for update in updates:
            payload = update.payload()
            self.opportunity_trace.append({"tick": self.state.tick, "event_type": "OpportunityCostEvent", **payload})
            emitted.append(
                self._event(
                    "OpportunityCostEvent",
                    "opportunity",
                    payload,
                    update.causal_refs,
                )
            )
        return emitted

    def _update_action_reversibility(self, context: TickContext, local_events: list[Event]) -> list[Event]:
        update = self.reversibility.update(self.state, context, local_events)
        if not update:
            return []
        payload = update.payload()
        self.reversibility_trace.append({"tick": self.state.tick, "event_type": "ActionReversibilityEvent", **payload})
        return [
            self._event(
                "ActionReversibilityEvent",
                "reversibility",
                payload,
                update.causal_refs,
            )
        ]

    def _update_positions(self, local_events: list[Event]) -> list[Event]:
        emitted: list[Event] = []
        updates = self.positioning.update(self.state, local_events)
        for update in updates:
            payload = update.payload()
            self.position_trace.append({"tick": self.state.tick, **payload})
            emitted.append(
                self._event(
                    "PositioningEvent",
                    "position",
                    payload,
                    update.causal_refs,
                )
            )
        return emitted

    def _scene_and_signal_events(self, context: TickContext, prior_events: list[Event]) -> list[Event]:
        events: list[Event] = []
        affordance = self.affordances.select(self.state, context)
        self.affordance_trace.append(dict(self.affordances.last_diagnostics))
        affordance_event = self._event(
            "AffordanceSelectionEvent",
            "affordance",
            {
                "affordance_id": affordance.affordance_id,
                "signal_type": affordance.signal_type,
                "frame": affordance.frame,
                "score": affordance.score,
                "evidence": affordance.evidence,
                "local_world_context": self.affordances.last_diagnostics.get("local_world_context", {}),
                "tick_type": context.tick_type,
            },
        )
        events.append(affordance_event)
        viability_events = [event for event in prior_events if event.source_layer == "viability"]
        action = self.actions.select(self.state, context, affordance, viability_events=viability_events)
        self.action_trace.append(dict(self.actions.last_diagnostics))
        action_viability_refs = list(self.actions.last_diagnostics.get("viability_context", {}).get("evidence_refs", []))
        action_event = self._event(
            "ActionSelectionEvent",
            "action",
            {
                "action_id": action.action_id,
                "action_mode": action.action_mode,
                "signal_type": action.signal_type,
                "source_process": action.source_process,
                "target_process": action.target_process,
                "score": action.score,
                "ambiguity": action.ambiguity,
                "inhibited_action": action.inhibited_action,
                "substituted_for": action.substituted_for,
                "relation_claim": action.relation_claim,
                "evidence": action.evidence,
                "viability_evidence_refs": action_viability_refs,
                "affordance_id": affordance.affordance_id,
            },
            sorted(set([affordance_event.event_id] + action_viability_refs)),
        )
        events.append(action_event)
        if action.action_mode == "inhibited":
            events.append(
                self._event(
                    "ActionInhibitionEvent",
                    "action",
                    {
                        "action_id": action.action_id,
                        "inhibited_action": action.inhibited_action,
                        "replacement_signal": action.signal_type,
                        "evidence": action.evidence,
                    },
                    [action_event.event_id],
                )
            )
        elif action.action_mode == "substituted":
            events.append(
                self._event(
                    "ActionSubstitutionEvent",
                    "action",
                    {
                        "action_id": action.action_id,
                        "substituted_for": action.substituted_for,
                        "replacement_signal": action.signal_type,
                        "evidence": action.evidence,
                    },
                    [action_event.event_id],
                )
            )
        expression = self.expression.select(self.state, context, action, viability_events=viability_events)
        self.expression_trace.append(dict(self.expression.last_diagnostics))
        expression_viability_refs = list(self.expression.last_diagnostics.get("viability_context", {}).get("evidence_refs", []))
        expression_event = self._event(
            "ExpressionSelectionEvent",
            "expression",
            {
                "expression_id": expression.expression_id,
                "expression_mode": expression.expression_mode,
                "surface_signal": expression.surface_signal,
                "tone": expression.tone,
                "gesture": expression.gesture,
                "timing": expression.timing,
                "intensity": expression.intensity,
                "ambiguity": expression.ambiguity,
                "relation_claim": expression.relation_claim,
                "score": expression.score,
                "evidence": expression.evidence,
                "viability_evidence_refs": expression_viability_refs,
                "action_id": action.action_id,
                "action_mode": action.action_mode,
                "affordance_id": affordance.affordance_id,
            },
            sorted(set([action_event.event_id] + expression_viability_refs)),
        )
        events.append(expression_event)
        scene_evidence = {**affordance.evidence, **action.evidence, **expression.evidence}
        locality = self.local_world.select_scene_locality(
            context,
            scene_type=affordance.affordance_id,
            evidence=scene_evidence,
            causal_refs=[affordance_event.event_id, action_event.event_id, expression_event.event_id],
        )
        if locality.location_trace:
            self.location_selection_trace.append(locality.location_trace)
        if locality.route_trace:
            self.route_selection_trace.append(locality.route_trace)
        if locality.audience_trace:
            self.audience_exposure_trace.append(locality.audience_trace)
        local_constraint_events: list[Event] = []
        local_constraints = self.local_world.derive_capacity_constraints(
            context,
            locality.scene_context,
            causal_refs=[affordance_event.event_id, action_event.event_id, expression_event.event_id],
        )
        if local_constraints.traces:
            self.local_world_trace.extend(local_constraints.traces)
        for event_type, payload, refs in local_constraints.events:
            local_constraint_events.append(self._event(event_type, "local_world", payload, refs))
        events.extend(local_constraint_events)
        local_constraint_refs = [event.event_id for event in local_constraint_events]
        if context.tick_type == "scene":
            events.append(
                self._event(
                    "SceneCrystallizationEvent",
                    "scene",
                    {
                        "scene_id": f"scene-{self.state.tick:03d}",
                        "frame": affordance.frame,
                        "why_now": context.time_mapping_reason,
                        "why_here": locality.scene_context.get("why_here"),
                        "why_unavoidable": self._why_affordance_unavoidable(scene_evidence),
                        "why_these_processes": locality.scene_context.get("why_these_processes"),
                        "why_not_elsewhere": locality.scene_context.get("why_not_elsewhere"),
                        "who_might_see": locality.scene_context.get("who_might_see", []),
                        "what_this_place_remembers": locality.scene_context.get("what_this_place_remembers", []),
                        "tick_type": "scene",
                        "scene_context": locality.scene_context,
                        "location_id": locality.scene_context.get("location_id"),
                        "route_context": locality.scene_context.get("route_context", {}),
                        "time_window": locality.scene_context.get("time_window"),
                        "active_rhythm": locality.scene_context.get("active_rhythm"),
                        "possible_audiences": locality.scene_context.get("possible_audiences", []),
                        "local_constraints": locality.scene_context.get("local_constraints", []),
                        "memory_site_refs": locality.scene_context.get("memory_site_refs", []),
                        "local_world_constraint_refs": local_constraint_refs,
                        "affordance_id": affordance.affordance_id,
                        "action_id": action.action_id,
                        "expression_id": expression.expression_id,
                    },
                    [affordance_event.event_id, action_event.event_id, expression_event.event_id] + local_constraint_refs,
                )
            )
        events.append(
            self._event(
                "MicroSignalEvent",
                "communication",
                {
                    "tick_type": context.tick_type,
                    "signal_type": expression.surface_signal,
                    "source_process": action.source_process,
                    "target_process": action.target_process,
                    "ambiguity": expression.ambiguity,
                    "affordance_id": affordance.affordance_id,
                    "action_id": action.action_id,
                    "action_mode": action.action_mode,
                    "expression_id": expression.expression_id,
                    "expression_mode": expression.expression_mode,
                    "tone": expression.tone,
                    "gesture": expression.gesture,
                    "timing": expression.timing,
                    "intensity": expression.intensity,
                    "scene_context": locality.scene_context,
                    "location_id": locality.scene_context.get("location_id"),
                    "route_context": locality.scene_context.get("route_context", {}),
                    "local_world_constraint_refs": local_constraint_refs,
                },
                [expression_event.event_id] + local_constraint_refs,
            )
        )
        events.append(
            self._event(
                "ObservationEvent",
                "observation",
                {
                    "observer": "p1",
                    "observed_signal": expression.surface_signal,
                    "inferred_relation_claim": expression.relation_claim,
                    "confidence": clamp(0.45 + expression.score * 0.35),
                    "affordance_id": affordance.affordance_id,
                    "action_id": action.action_id,
                    "expression_id": expression.expression_id,
                    "expression_mode": expression.expression_mode,
                },
                [events[-1].event_id],
            )
        )
        return events

    def _why_affordance_unavoidable(self, evidence: dict[str, float]) -> str:
        if not evidence:
            return "available action space narrowed by current field conditions"
        strongest = max(evidence.items(), key=lambda item: item[1])[0]
        return f"{strongest} made this interaction form structurally available"

    def _activate_rpps(self, context: TickContext, local_events: list[Event]) -> list[Event]:
        emitted: list[Event] = []
        activated_this_tick: set[str] = set()
        for rpp in self.rpps:
            activation = rpp.evaluate(self.state, context, local_events + emitted)
            if not activation:
                continue
            activated_this_tick.add(activation.rpp_id)
            rpp.apply(self.state, activation)
            existing = next((a for a in self.state.active_rpps if a.rpp_id == activation.rpp_id), None)
            if existing:
                existing.intensity = clamp(existing.intensity + 0.08)
                existing.activation_score = activation.score
                existing.last_updated_tick = self.state.tick
                existing.activation_reason_refs = activation.evidence
            else:
                self.state.active_rpps.append(ActiveRPP(rpp_id=activation.rpp_id, participating_processes=activation.participating_processes, activation_score=activation.score, intensity=activation.score, activation_reason_refs=activation.evidence, started_tick=self.state.tick, last_updated_tick=self.state.tick))
            emitted.append(self._event("RPPActivationEvent", "rpp", {"rpp_id": activation.rpp_id, "activation_score": activation.score, "eligibility_evidence": activation.evidence, "effect": activation.effect}, activation.evidence))
            self.rpp_activation_trace.append(
                {
                    "tick": self.state.tick,
                    "rpp_id": activation.rpp_id,
                    "activation_score": activation.score,
                    "participating_processes": activation.participating_processes,
                    "eligibility_evidence": activation.evidence,
                    "effect": activation.effect,
                    "semantic_role": "unrecognized_contribution_debt" if activation.rpp_id == "contribution_debt_loop" else activation.rpp_id,
                    "active_intensity": next(a.intensity for a in self.state.active_rpps if a.rpp_id == activation.rpp_id),
                }
            )
            emitted.append(self._event("StabilizationEvent", "stabilization", {"pattern": activation.rpp_id, "new_stability": max(p.stabilized_patterns.get(activation.rpp_id, 0.0) for p in self.state.processes.values())}, [emitted[-1].event_id]))
        self._activated_rpps_this_tick = activated_this_tick
        return emitted

    def _update_rpp_dynamics(self, local_events: list[Event]) -> list[Event]:
        activated = getattr(self, "_activated_rpps_this_tick", set())
        result = self.rpp_dynamics.update(self.state, activated)
        emitted: list[Event] = []
        for composition in result.compositions:
            emitted.append(
                self._event(
                    "RPPCompositionEvent",
                    "rpp_dynamics",
                    {
                        "composition_id": composition.composition_id,
                        "participating_rpps": composition.participating_rpps,
                        "composition_score": composition.score,
                        "effect": composition.effect,
                    },
                    [e.event_id for e in local_events[-6:] if e.event_type == "RPPActivationEvent"],
                )
            )
        for suppression in result.suppressions:
            emitted.append(
                self._event(
                    "RPPSuppressionEvent",
                    "rpp_dynamics",
                    {
                        "suppressed_rpp": suppression.suppressed_rpp,
                        "suppressed_by": suppression.suppressed_by,
                        "old_intensity": suppression.old_intensity,
                        "new_intensity": suppression.new_intensity,
                        "reason": suppression.reason,
                    },
                )
            )
        for decay in result.decays:
            emitted.append(
                self._event(
                    "RPPDecayEvent",
                    "rpp_dynamics",
                    {
                        "rpp_id": decay.rpp_id,
                        "old_intensity": decay.old_intensity,
                        "new_intensity": decay.new_intensity,
                        "reason": decay.reason,
                    },
                )
            )
        self.rpp_dynamics_trace.append(
            {
                "tick": self.state.tick,
                "activated_rpps": sorted(activated),
                "compositions": [composition.__dict__ for composition in result.compositions],
                "suppressions": [suppression.__dict__ for suppression in result.suppressions],
                "decays": [decay.__dict__ for decay in result.decays],
                "active_rpp_intensities": {r.rpp_id: r.intensity for r in self.state.active_rpps if r.intensity > 0.0},
            }
        )
        return emitted

    def _recognition_and_repair(self, local_events: list[Event]) -> list[Event]:
        emitted: list[Event] = []
        result = self.recognition.evaluate(self.state, local_events)
        self.recognition.apply(self.state, result)
        recognition_refs = self._recognition_causal_refs(local_events)
        emitted.append(
            self._event(
                "RecognitionEvent",
                "recognition",
                {
                    "demand_id": result.demand.demand_id,
                    "holder": result.demand.holder_process_id,
                    "demanded_from": result.demand.demanded_from,
                    "result": result.outcome,
                    "outcome_scores": result.scores,
                    "evidence": result.evidence,
                },
                recognition_refs,
            )
        )
        self.recognition_trace.append(
            {
                "tick": self.state.tick,
                "demand_id": result.demand.demand_id,
                "outcome": result.outcome,
                "scores": result.scores,
                "evidence": result.evidence,
                "repair_event_type": result.repair_event_type,
                "repair_debt": self.state.relation_metrics.get("repair_debt", 0.0),
                "conflict_pressure": self.state.relation_metrics.get("conflict_pressure", 0.0),
                "demand_pressure": result.demand.current_pressure,
            }
        )
        if result.repair_event_type == "RepairEvent":
            emitted.append(
                self._event(
                    "RepairEvent",
                    "repair",
                    {
                        "repair_type": result.repair_method,
                        "success_level": "partial" if result.outcome == "partial" else "substantive",
                        "remaining_debt": self.state.relation_metrics["repair_debt"],
                    },
                    [emitted[-1].event_id],
                )
            )
        elif result.repair_event_type == "MisrecognitionEvent":
            emitted.append(
                self._event(
                    "MisrecognitionEvent",
                    "recognition",
                    {
                        "denied_claim": result.demand.recognition_type,
                        "method": result.repair_method,
                        "future_bias": result.evidence,
                    },
                    [emitted[-1].event_id],
                )
            )
        elif result.repair_event_type == "DisplacementEvent":
            emitted.append(
                self._event(
                    "DisplacementEvent",
                    "repair",
                    {
                        "displaced_content": result.demand.recognition_type,
                        "method": result.repair_method,
                        "long_term_pressure": self.state.relation_metrics["repair_debt"],
                    },
                    [emitted[-1].event_id],
                )
            )
        else:
            emitted.append(
                self._event(
                    "AvoidanceEvent",
                    "repair",
                    {
                        "avoided_content": result.demand.recognition_type,
                        "method": result.repair_method,
                        "long_term_pressure": self.state.relation_metrics["repair_debt"],
                    },
                    [emitted[-1].event_id],
                )
            )
        return emitted

    def _recognition_causal_refs(self, local_events: list[Event]) -> list[str]:
        refs = [event.event_id for event in local_events[-6:]]
        refs.extend(
            event.event_id
            for event in local_events
            if event.source_layer == "viability"
            and event.event_type in {
                "ViabilityRequirementEvent",
                "AffordanceWidthEvent",
                "DeformationTraceEvent",
                "DerivedDramaticTensionEvent",
            }
        )
        return sorted(set(refs))

    def _classification_and_irreversibility(self, local_events: list[Event]) -> list[Event]:
        emitted: list[Event] = []
        results = self.fate.evaluate(self.state, local_events)
        self.fate.apply(self.state, results)
        for result in results:
            self.fate_transition_trace.append(
                {
                    "tick": self.state.tick,
                    "transition_id": result.transition_id,
                    "transition_type": result.transition_type,
                    "score": result.score,
                    "evidence": result.evidence,
                }
            )
            source = local_events[-1].event_id if local_events else ""
            if result.classification:
                emitted.append(
                    self._event(
                        "OperativeClassificationEvent",
                        "classification",
                        {
                            **result.classification.model_dump(),
                            "transition_score": result.score,
                            "transition_evidence": result.evidence,
                        },
                        [source],
                    )
                )
                emitted.append(
                    self._event(
                        "DownwardConstraintEvent",
                        "classification",
                        {
                            "classification_id": result.classification.classification_id,
                            "mechanism": "operative label uptake and future interpretation bias",
                            "constrained_fields": ["speech_inhibition", "threat_sensitivity", "future_interpretation_bias"],
                            "transition_score": result.score,
                        },
                        [emitted[-1].event_id],
                    )
                )
            if result.irreversible:
                emitted.append(
                    self._event(
                        "IrreversibilityEvent",
                        "irreversibility",
                        {
                            **result.irreversible.model_dump(),
                            "transition_score": result.score,
                            "transition_evidence": result.evidence,
                        },
                        [source],
                    )
                )
        return emitted

    def _update_memory(self, local_events: list[Event]) -> list[Event]:
        emitted: list[Event] = []
        reconstructions = self.memory.update(self.state, local_events)
        for reconstruction in reconstructions:
            memory = reconstruction.memory
            self.memory_trace.append(
                {
                    "tick": self.state.tick,
                    "memory_id": memory.memory_id,
                    "owner_process_id": memory.owner_process_id,
                    "source_event_id": memory.source_event_id,
                    "source_event_type": reconstruction.source_event_type,
                    "remembered_as": memory.remembered_as,
                    "salience": memory.salience,
                    "valence": memory.valence,
                    "confidence": memory.confidence,
                    "reconstruction_biases": memory.reconstruction_biases,
                    "evidence": reconstruction.evidence,
                }
            )
            emitted.append(
                self._event(
                    "MemoryReconstructionEvent",
                    "memory",
                    {
                        "memory_id": memory.memory_id,
                        "owner_process_id": memory.owner_process_id,
                        "source_event_id": memory.source_event_id,
                        "source_event_type": reconstruction.source_event_type,
                        "remembered_as": memory.remembered_as,
                        "salience": memory.salience,
                        "valence": memory.valence,
                        "confidence": memory.confidence,
                        "reconstruction_biases": memory.reconstruction_biases,
                        "evidence": reconstruction.evidence,
                    },
                    sorted(set([memory.source_event_id] + list(reconstruction.evidence.get("future_constraint_refs", [])))),
                )
            )
        return emitted

    def _update_environment(self, local_events: list[Event]) -> list[Event]:
        emitted: list[Event] = []
        sediments = self.environment.update(self.state, local_events)
        for sediment in sediments:
            self.environment_trace.append({"tick": self.state.tick, **sediment.trace})
            emitted.append(
                self._event(
                    sediment.event_type,
                    "field",
                    sediment.payload,
                    sediment.causal_refs,
                )
            )
        return emitted

    def _update_dispositions(self, local_events: list[Event]) -> list[Event]:
        emitted: list[Event] = []
        updates = self.disposition.update(self.state, local_events)
        for update in updates:
            payload = update.payload()
            self.disposition_trace.append({"tick": self.state.tick, **payload})
            emitted.append(
                self._event(
                    "DispositionSedimentationEvent",
                    "process",
                    payload,
                    update.causal_refs,
                )
            )
        return emitted

    def _update_relation(self, local_events: list[Event]) -> list[Event]:
        emitted: list[Event] = []
        updates = self.relation.update(self.state, local_events)
        for update in updates:
            payload = update.payload()
            self.relation_trace.append({"tick": self.state.tick, **payload})
            emitted.append(
                self._event(
                    "RelationSedimentationEvent",
                    "relation",
                    payload,
                    update.causal_refs,
                )
            )
        return emitted

    def _aggregation_trace(self, views: Any) -> dict[str, Any]:
        return {
            "trust_view": {"sources": ["risk_suspension_scope", "ambiguity_tolerance", "checking_tendency", "repair_debt"], "value": views.trust_view},
            "resentment_pressure_view": {"sources": ["resentment_pressure", "repair_debt", "unrecognized_contribution"], "value": views.resentment_pressure_view},
            "repair_capacity_view": {"sources": ["repair_debt", "speech_inhibition.apology"], "value": views.repair_capacity_view},
            "rpp_dynamics": {"sources": ["composition.*", "active_rpps.intensity"], "value": {"active_composition_count": self.state.relation_metrics.get("active_composition_count", 0.0), "dominant_composition_score": self.state.relation_metrics.get("dominant_composition_score", 0.0)}},
            "memory_pressure": {"sources": ["memory_traces", "memory_bias.*"], "value": self.state.relation_metrics.get("memory_pressure", 0.0)},
            "field_sedimentation": {"sources": ["environment_trace", "FieldUpdateEvent", "EnactedMicroWorldEvent"], "value": self.state.field_state.model_dump(mode="json")},
            "process_disposition_sedimentation": {"sources": ["disposition_trace", "DispositionSedimentationEvent"], "value": {pid: {"checking_tendency": p.checking_tendency, "ambiguity_tolerance": p.ambiguity_tolerance, "risk_suspension_scope": p.risk_suspension_scope, "speech_inhibition": p.speech_inhibition, "threat_sensitivity": p.threat_sensitivity} for pid, p in self.state.processes.items()}},
            "relation_sedimentation": {"sources": ["relation_trace", "RelationSedimentationEvent"], "value": {key: value for key, value in self.state.relation_metrics.items() if key.startswith("relation_sediment.")}},
            "binding_evolution": {"sources": ["binding_trace", "BindingUpdatedEvent", "BindingDecayedEvent"], "value": [binding.model_dump(mode="json") for binding in self.state.bindings]},
            "expectation_sedimentation": {"sources": ["expectation_trace", "ExpectationSedimentationEvent"], "value": {key: value for key, value in self.state.relation_metrics.items() if key.startswith("expectation.")}},
            "account_pressure": {"sources": ["account_trace", "AccountPressureEvent"], "value": {key: value for key, value in self.state.relation_metrics.items() if key.startswith("account_pressure.")}},
            "normative_pressure": {"sources": ["normativity_trace", "NormativePressureEvent"], "value": {key: value for key, value in self.state.relation_metrics.items() if key.startswith("norm_pressure.")}},
            "frame_definition": {"sources": ["frame_trace", "FrameDefinitionEvent"], "value": {key: value for key, value in self.state.relation_metrics.items() if key.startswith("frame_definition.")}},
            "common_ground": {"sources": ["common_ground_trace", "CommonGroundEvent"], "value": {key: value for key, value in self.state.relation_metrics.items() if key.startswith("common_ground.")}},
            "relevance_landscape": {"sources": ["relevance_trace", "RelevanceShiftEvent"], "value": {key: value for key, value in self.state.relation_metrics.items() if key.startswith("relevance_field.")}},
            "position_field": {"sources": ["position_trace", "PositioningEvent"], "value": {key: value for key, value in self.state.relation_metrics.items() if key.startswith("position_field.")}},
        }


def _render_canon_for_scenario(scenario: dict[str, Any]) -> dict[str, Any]:
    canon = scenario.get("render_canon")
    if isinstance(canon, dict) and canon:
        return canon
    cast = {}
    for pid, process in scenario.get("processes", {}).items():
        cast[pid] = {
            "name": process.get("display_name", pid),
            "gender": "未指定",
            "pronoun": "",
            "age_band": "未指定",
            "surface_role": "由模拟过程逐步显现的位置",
            "speech_style": "由行动、表达和抑制模式约束",
            "allowed_interiority": "只允许从行为、停顿、语气和选择中推断，不允许直接写内心独白",
        }
    return {
        "title": scenario.get("name") or scenario.get("id") or "RPF 案例",
        "setting": {
            "place": "未指定场域",
            "period": "未指定时期",
            "atmosphere": "由场压力、绑定和互动过程决定",
            "material_objects": [],
        },
        "cast": cast,
        "narration": {
            "language": "中文",
            "tense": "过去时",
            "perspective": "第三人称限制视角",
            "style": "克制的现实主义文学",
            "interiority_level": "低",
            "metaphor_level": "低到中",
            "forbidden": [
                "新增亲属关系",
                "新增职业",
                "新增外部地点",
                "新增童年回忆",
                "新增恋爱或婚姻状态",
                "新增未来预告",
                "直接宣布固定人格本质",
            ],
        },
    }
