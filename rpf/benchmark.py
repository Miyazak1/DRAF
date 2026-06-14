from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from rpf.engine.simulator import Simulator
from rpf.scenarios.loader import load_scenario
from rpf.storage.timeline import read_timeline


def stable_seed(name: str, seed_base: int) -> int:
    return seed_base + (sum(ord(ch) for ch in name) % 1000)


def run_benchmark_suite(examples_dir: Path, output_dir: Path, *, steps: int, seed_base: int) -> dict[str, Any]:
    scenario_paths = sorted(examples_dir.glob("*.yaml"))
    runs_dir = output_dir / "runs"
    runs_dir.mkdir(parents=True, exist_ok=True)

    scenarios: list[dict[str, Any]] = []
    for scenario_path in scenario_paths:
        scenario = load_scenario(scenario_path)
        seed = stable_seed(scenario_path.stem, seed_base)
        run_dir = runs_dir / scenario["id"]
        sim = Simulator.from_scenario(scenario, scenario_path, seed=seed)
        result = sim.run(steps=steps, output_dir=run_dir)
        views = json.loads((run_dir / "derived_views.json").read_text(encoding="utf-8"))
        timeline = read_timeline(run_dir / "timeline.jsonl")
        expected_hash = timeline[-1]["payload"]["final_state_hash"]
        replay = Simulator.from_scenario(load_scenario(scenario_path), scenario_path, seed=seed)
        replay_result = replay.run(steps=steps, output_dir=run_dir / "_benchmark_replay")
        replay_ok = replay_result["final_state_hash"] == expected_hash
        tick_type_counts: dict[str, int] = {}
        for event in timeline:
            if event["event_type"] == "TickStartedEvent":
                tick_type = event["payload"]["tick_type"]
                tick_type_counts[tick_type] = tick_type_counts.get(tick_type, 0) + 1
        rpp_counts = result["metrics"]["rpp_activation_counts"]
        affordance_counts = result["metrics"].get("affordance_counts", {})
        dominant_affordance = max(affordance_counts.items(), key=lambda item: item[1])[0] if affordance_counts else None
        action_counts = result["metrics"].get("action_counts", {})
        dominant_action = max(action_counts.items(), key=lambda item: item[1])[0] if action_counts else None
        action_mode_counts = result["metrics"].get("action_mode_counts", {})
        dominant_action_mode = max(action_mode_counts.items(), key=lambda item: item[1])[0] if action_mode_counts else None
        expression_counts = result["metrics"].get("expression_counts", {})
        dominant_expression = max(expression_counts.items(), key=lambda item: item[1])[0] if expression_counts else None
        expression_mode_counts = result["metrics"].get("expression_mode_counts", {})
        dominant_expression_mode = max(expression_mode_counts.items(), key=lambda item: item[1])[0] if expression_mode_counts else None
        recognition_outcome_counts = result["metrics"].get("recognition_outcome_counts", {})
        dominant_recognition_outcome = max(recognition_outcome_counts.items(), key=lambda item: item[1])[0] if recognition_outcome_counts else None
        operative_label_counts = result["metrics"].get("operative_label_counts", {})
        dominant_operative_label = max(operative_label_counts.items(), key=lambda item: item[1])[0] if operative_label_counts else None
        irreversibility_category_counts = result["metrics"].get("irreversibility_category_counts", {})
        dominant_irreversibility_category = max(irreversibility_category_counts.items(), key=lambda item: item[1])[0] if irreversibility_category_counts else None
        memory_bias_counts = result["metrics"].get("memory_bias_counts", {})
        dominant_memory_bias = max(memory_bias_counts.items(), key=lambda item: item[1])[0] if memory_bias_counts else None
        rpp_score_sums = result["metrics"].get("rpp_activation_score_sums", {})
        dominant_rpp = max(rpp_score_sums.items(), key=lambda item: item[1])[0] if rpp_score_sums else None
        composition_score_sums = result["metrics"].get("rpp_composition_score_sums", {})
        dominant_composition = max(composition_score_sums.items(), key=lambda item: item[1])[0] if composition_score_sums else None
        scenarios.append(
            {
                "scenario_id": scenario["id"],
                "scenario_path": str(scenario_path),
                "seed": seed,
                "steps": steps,
                "output_dir": str(run_dir),
                "final_state_hash": result["final_state_hash"],
                "event_count": result["metrics"]["event_count"],
                "tick_type_counts": tick_type_counts,
                "affordance_counts": affordance_counts,
                "dominant_affordance": dominant_affordance,
                "action_counts": action_counts,
                "dominant_action": dominant_action,
                "action_mode_counts": action_mode_counts,
                "dominant_action_mode": dominant_action_mode,
                "expression_counts": expression_counts,
                "dominant_expression": dominant_expression,
                "expression_mode_counts": expression_mode_counts,
                "dominant_expression_mode": dominant_expression_mode,
                "recognition_outcome_counts": recognition_outcome_counts,
                "dominant_recognition_outcome": dominant_recognition_outcome,
                "operative_label_counts": operative_label_counts,
                "dominant_operative_label": dominant_operative_label,
                "irreversibility_category_counts": irreversibility_category_counts,
                "dominant_irreversibility_category": dominant_irreversibility_category,
                "memory_bias_counts": memory_bias_counts,
                "dominant_memory_bias": dominant_memory_bias,
                "rpp_activation_counts": result["metrics"]["rpp_activation_counts"],
                "rpp_activation_score_sums": rpp_score_sums,
                "rpp_composition_counts": result["metrics"].get("rpp_composition_counts", {}),
                "rpp_composition_score_sums": composition_score_sums,
                "dominant_rpp": dominant_rpp,
                "dominant_composition": dominant_composition,
                "relationship_phase": views["relationship_view"]["phase_label"],
                "person_labels": {pid: view["apparent_labels"] for pid, view in views["person_views"].items()},
                "operative_classification_count": result["metrics"]["operative_classification_count"],
                "irreversibility_count": result["metrics"]["irreversibility_count"],
                "memory_reconstruction_count": result["metrics"]["memory_reconstruction_count"],
                "action_inhibition_count": result["metrics"]["action_inhibition_count"],
                "action_substitution_count": result["metrics"]["action_substitution_count"],
                "replay_ok": replay_ok,
            }
        )

    phase_distribution = Counter(item["relationship_phase"] for item in scenarios)
    dominant_affordance_distribution = Counter(item["dominant_affordance"] for item in scenarios if item["dominant_affordance"])
    dominant_action_distribution = Counter(item["dominant_action"] for item in scenarios if item["dominant_action"])
    dominant_action_mode_distribution = Counter(item["dominant_action_mode"] for item in scenarios if item["dominant_action_mode"])
    dominant_expression_distribution = Counter(item["dominant_expression"] for item in scenarios if item["dominant_expression"])
    dominant_expression_mode_distribution = Counter(item["dominant_expression_mode"] for item in scenarios if item["dominant_expression_mode"])
    dominant_recognition_outcome_distribution = Counter(item["dominant_recognition_outcome"] for item in scenarios if item["dominant_recognition_outcome"])
    dominant_operative_label_distribution = Counter(item["dominant_operative_label"] for item in scenarios if item["dominant_operative_label"])
    dominant_irreversibility_category_distribution = Counter(item["dominant_irreversibility_category"] for item in scenarios if item["dominant_irreversibility_category"])
    dominant_memory_bias_distribution = Counter(item["dominant_memory_bias"] for item in scenarios if item["dominant_memory_bias"])
    dominant_rpp_distribution = Counter(item["dominant_rpp"] for item in scenarios if item["dominant_rpp"])
    dominant_composition_distribution = Counter(item["dominant_composition"] for item in scenarios if item["dominant_composition"])
    irreversibility_rate = sum(1 for item in scenarios if item["irreversibility_count"] > 0) / max(1, len(scenarios))
    summary = {
        "examples_dir": str(examples_dir),
        "output_dir": str(output_dir),
        "steps": steps,
        "seed_base": seed_base,
        "scenario_count": len(scenarios),
        "all_replay_ok": all(item["replay_ok"] for item in scenarios),
        "phase_distribution": dict(phase_distribution),
        "dominant_affordance_distribution": dict(dominant_affordance_distribution),
        "dominant_action_distribution": dict(dominant_action_distribution),
        "dominant_action_mode_distribution": dict(dominant_action_mode_distribution),
        "dominant_expression_distribution": dict(dominant_expression_distribution),
        "dominant_expression_mode_distribution": dict(dominant_expression_mode_distribution),
        "dominant_recognition_outcome_distribution": dict(dominant_recognition_outcome_distribution),
        "dominant_operative_label_distribution": dict(dominant_operative_label_distribution),
        "dominant_irreversibility_category_distribution": dict(dominant_irreversibility_category_distribution),
        "dominant_memory_bias_distribution": dict(dominant_memory_bias_distribution),
        "dominant_rpp_distribution": dict(dominant_rpp_distribution),
        "dominant_composition_distribution": dict(dominant_composition_distribution),
        "irreversibility_rate": round(irreversibility_rate, 4),
        "scenarios": scenarios,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "benchmark_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (output_dir / "benchmark_summary.md").write_text(render_markdown_summary(summary), encoding="utf-8")
    return summary


def render_markdown_summary(summary: dict[str, Any]) -> str:
    lines = [
        "# RPF Benchmark Summary",
        "",
        f"- Scenarios: {summary['scenario_count']}",
        f"- Steps: {summary['steps']}",
        f"- Seed base: {summary['seed_base']}",
        f"- All replay OK: {summary['all_replay_ok']}",
        f"- Phase distribution: {summary['phase_distribution']}",
        f"- Dominant affordance distribution: {summary['dominant_affordance_distribution']}",
        f"- Dominant action distribution: {summary['dominant_action_distribution']}",
        f"- Dominant action mode distribution: {summary['dominant_action_mode_distribution']}",
        f"- Dominant expression distribution: {summary['dominant_expression_distribution']}",
        f"- Dominant expression mode distribution: {summary['dominant_expression_mode_distribution']}",
        f"- Dominant recognition outcome distribution: {summary['dominant_recognition_outcome_distribution']}",
        f"- Dominant operative label distribution: {summary['dominant_operative_label_distribution']}",
        f"- Dominant irreversibility category distribution: {summary['dominant_irreversibility_category_distribution']}",
        f"- Dominant memory bias distribution: {summary['dominant_memory_bias_distribution']}",
        f"- Dominant RPP distribution: {summary['dominant_rpp_distribution']}",
        f"- Dominant composition distribution: {summary['dominant_composition_distribution']}",
        f"- Irreversibility rate: {summary['irreversibility_rate']}",
        "",
        "| Scenario | Phase | Ticks latent/micro/scene | Affordance | Action | Action Mode | Expression | Expression Mode | Recognition | Fate Label | Irreversible Type | Memory Bias | Dominant RPP | Dominant Composition | Irreversible | Memory | Replay |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for item in summary["scenarios"]:
        ticks = item["tick_type_counts"]
        tick_text = f"{ticks.get('latent', 0)}/{ticks.get('micro_interaction', 0)}/{ticks.get('scene', 0)}"
        rpp_text = ", ".join(f"{k}:{v}" for k, v in item["rpp_activation_counts"].items())
        lines.append(
            f"| {item['scenario_id']} | {item['relationship_phase']} | {tick_text} | {item['dominant_affordance']} | {item['dominant_action']} | {item['dominant_action_mode']} | {item['dominant_expression']} | {item['dominant_expression_mode']} | {item['dominant_recognition_outcome']} | {item['dominant_operative_label']} | {item['dominant_irreversibility_category']} | {item['dominant_memory_bias']} | {item['dominant_rpp']} | {item['dominant_composition']} | {item['irreversibility_count']} | {item['memory_reconstruction_count']} | {item['replay_ok']} |"
        )
    lines.append("")
    return "\n".join(lines)

