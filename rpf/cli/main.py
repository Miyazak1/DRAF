from __future__ import annotations

import argparse
import json
from pathlib import Path

from rpf.benchmark import run_benchmark_suite
from rpf.engine.simulator import Simulator
from rpf.scenarios.loader import load_scenario
from rpf.storage.timeline import read_timeline
from rpf.core.versioning import UnsupportedSchemaVersionError
from rpf.llm.renderer import render_output
from rpf.viewer.server import serve_viewer


def _run(args: argparse.Namespace) -> None:
    scenario_path = Path(args.scenario)
    scenario = load_scenario(scenario_path)
    sim = Simulator.from_scenario(scenario, scenario_path=scenario_path, seed=args.seed)
    output_dir = Path(args.out) / scenario["id"]
    result = sim.run(steps=args.steps, output_dir=output_dir)
    print(json.dumps(result, indent=2, ensure_ascii=False))


def _replay(args: argparse.Namespace) -> None:
    timeline_path = Path(args.timeline)
    try:
        events = read_timeline(timeline_path)
    except UnsupportedSchemaVersionError as exc:
        raise SystemExit(f"Cannot replay timeline: {exc}") from exc
    init = next(event for event in events if event["event_type"] == "SimulationInitializedEvent")
    scenario_path = Path(init["payload"]["scenario_path"])
    steps = int(init["payload"]["steps"])
    seed = int(init["payload"]["seed"])
    expected = events[-1]["payload"].get("final_state_hash")
    scenario = load_scenario(scenario_path)
    sim = Simulator.from_scenario(scenario, scenario_path=scenario_path, seed=seed)
    replay_dir = timeline_path.parent / "_replay"
    result = sim.run(steps=steps, output_dir=replay_dir)
    ok = result["final_state_hash"] == expected
    print(json.dumps({"replay_ok": ok, "expected": expected, "actual": result["final_state_hash"]}, indent=2))


def _inspect(args: argparse.Namespace) -> None:
    output_dir = Path(args.output_dir)
    views = json.loads((output_dir / "derived_views.json").read_text(encoding="utf-8"))
    metrics = json.loads((output_dir / "metrics.json").read_text(encoding="utf-8"))
    effective_config_path = output_dir / "effective_config.json"
    report = {
        "output_dir": str(output_dir),
        "effective_config": str(effective_config_path) if effective_config_path.exists() else None,
        "metrics": metrics,
        "relationship_phase": views["relationship_view"]["phase_label"],
        "person_labels": {
            pid: view["apparent_labels"] for pid, view in views["person_views"].items()
        },
    }
    print(json.dumps(report, indent=2, ensure_ascii=False))


def _benchmark(args: argparse.Namespace) -> None:
    summary = run_benchmark_suite(
        Path(args.examples_dir),
        Path(args.out),
        steps=args.steps,
        seed_base=args.seed_base,
    )
    print(json.dumps({
        "output_dir": summary["output_dir"],
        "scenario_count": summary["scenario_count"],
        "all_replay_ok": summary["all_replay_ok"],
        "summary_json": str(Path(summary["output_dir"]) / "benchmark_summary.json"),
        "summary_md": str(Path(summary["output_dir"]) / "benchmark_summary.md"),
    }, indent=2, ensure_ascii=False))


def _viewer(args: argparse.Namespace) -> None:
    serve_viewer(Path(args.output_dir), host=args.host, port=args.port)


def _render(args: argparse.Namespace) -> None:
    result = render_output(
        Path(args.output_dir),
        out_path=Path(args.out) if args.out else None,
        use_llm=args.llm,
        model=args.model,
        base_url=args.base_url,
        api_key=args.api_key,
        provider=args.provider,
        thinking=args.thinking,
        reasoning_effort=args.reasoning_effort,
        max_frames=args.max_frames,
    )
    print(json.dumps(result, indent=2, ensure_ascii=False))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="rpf", description="RPF MVP simulator")
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run")
    run.add_argument("scenario")
    run.add_argument("--steps", type=int, default=30)
    run.add_argument("--seed", type=int, default=42)
    run.add_argument("--out", default="out")
    run.set_defaults(func=_run)

    replay = sub.add_parser("replay")
    replay.add_argument("timeline")
    replay.set_defaults(func=_replay)

    inspect = sub.add_parser("inspect")
    inspect.add_argument("output_dir")
    inspect.set_defaults(func=_inspect)

    benchmark = sub.add_parser("benchmark")
    benchmark.add_argument("examples_dir")
    benchmark.add_argument("--steps", type=int, default=30)
    benchmark.add_argument("--seed-base", type=int, default=1000)
    benchmark.add_argument("--out", default="out/benchmarks")
    benchmark.set_defaults(func=_benchmark)

    viewer = sub.add_parser("viewer")
    viewer.add_argument("output_dir")
    viewer.add_argument("--host", default="127.0.0.1")
    viewer.add_argument("--port", type=int, default=8765)
    viewer.set_defaults(func=_viewer)

    render = sub.add_parser("render")
    render.add_argument("output_dir")
    render.add_argument("--out")
    render.add_argument("--max-frames", type=int)
    render.add_argument("--llm", action="store_true")
    render.add_argument("--model")
    render.add_argument("--base-url")
    render.add_argument("--api-key")
    render.add_argument("--provider", choices=["deepseek"])
    render.add_argument("--thinking", choices=["enabled", "disabled"])
    render.add_argument("--reasoning-effort", choices=["high", "max"])
    render.set_defaults(func=_render)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)
