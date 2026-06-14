import json
from pathlib import Path

from rpf.benchmark import run_benchmark_suite


def test_benchmark_runner_writes_json_and_markdown_summary(tmp_path):
    output_dir = tmp_path / "benchmarks"
    summary = run_benchmark_suite(Path("examples"), output_dir, steps=8, seed_base=500)

    assert summary["scenario_count"] == len(list(Path("examples").glob("*.yaml")))
    assert summary["all_replay_ok"] is True
    assert (output_dir / "benchmark_summary.json").exists()
    assert (output_dir / "benchmark_summary.md").exists()

    written = json.loads((output_dir / "benchmark_summary.json").read_text())
    assert written["scenario_count"] == summary["scenario_count"]
    assert all(item["replay_ok"] for item in written["scenarios"])
    assert all("tick_type_counts" in item for item in written["scenarios"])
    assert "phase_distribution" in written
    assert "dominant_rpp_distribution" in written
    assert "irreversibility_rate" in written

    markdown = (output_dir / "benchmark_summary.md").read_text()
    assert "| Scenario | Phase |" in markdown
    assert "Dominant RPP" in markdown
    assert "shared_apartment_unresolved_sacrifice" in markdown
