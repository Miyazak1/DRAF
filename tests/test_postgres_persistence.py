from pathlib import Path

import pytest

from rpf.config import database_settings, load_env_file
from rpf.engine.simulator import Simulator
from rpf.llm import segments
from rpf.scenarios.loader import load_scenario
from rpf.storage.base import NullRunStore
from rpf.storage.postgres import DEFAULT_MIGRATIONS_DIR, PostgresRunStore
from rpf.viewer.server import build_viewer_payload_from_database_records


class RecordingStore:
    backend_name = "recording"

    def __init__(self):
        self.calls = []
        self.events = []
        self.traces = []
        self.snapshots = []
        self.render_segments = []

    def upsert_scenario(self, **kwargs):
        self.calls.append(("upsert_scenario", kwargs))

    def begin_run(self, **kwargs):
        self.calls.append(("begin_run", kwargs))

    def write_events(self, **kwargs):
        self.events.append(kwargs)

    def write_traces(self, **kwargs):
        self.traces.append(kwargs)

    def write_snapshot(self, **kwargs):
        self.snapshots.append(kwargs)

    def write_render_segment(self, **kwargs):
        self.render_segments.append(kwargs)

    def complete_run(self, **kwargs):
        self.calls.append(("complete_run", kwargs))


def test_database_settings_defaults_to_file_backend(tmp_path, monkeypatch):
    monkeypatch.delenv("RPF_DATABASE_URL", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("RPF_STORAGE_BACKEND", raising=False)

    settings = database_settings(env={}, env_path=tmp_path / ".env")

    assert settings.backend == "file"
    assert settings.database_url is None
    assert settings.enabled is False


def test_database_settings_reads_dotenv_and_env_override(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "RPF_STORAGE_BACKEND=postgres",
                "RPF_DATABASE_URL=postgresql://file-value/db",
                "RPF_DATABASE_SCHEMA=rpf",
            ]
        ),
        encoding="utf-8",
    )

    assert load_env_file(env_file)["RPF_DATABASE_SCHEMA"] == "rpf"

    settings = database_settings(
        env={"RPF_DATABASE_URL": "postgresql://env-value/db"},
        env_path=env_file,
    )

    assert settings.backend == "postgres"
    assert settings.database_url == "postgresql://env-value/db"
    assert settings.schema == "rpf"
    assert settings.enabled is True


def test_postgres_store_requires_database_url():
    with pytest.raises(ValueError, match="RPF_DATABASE_URL"):
        PostgresRunStore(database_settings(env={"RPF_STORAGE_BACKEND": "postgres"}, env_path=Path("missing.env")))


def test_null_store_implements_run_store_methods():
    store = NullRunStore()

    assert store.backend_name == "none"
    assert store.upsert_scenario(scenario_id="s", title="t", source_yaml="id: s") is None
    assert store.begin_run(run_id="00000000-0000-0000-0000-000000000000", scenario_id="s", title="t", seed=1, mode="test") is None
    assert store.write_events(run_id="r", events=[]) is None
    assert store.write_traces(run_id="r", layer="test", records=[]) is None
    assert store.complete_run(run_id="r", status="completed", tick_count=0, event_count=0) is None


def test_initial_postgres_migration_contains_core_tables_and_indexes():
    migration = (DEFAULT_MIGRATIONS_DIR / "001_initial_schema.sql").read_text(encoding="utf-8")

    for table in ("scenarios", "runs", "events", "snapshots", "traces", "render_segments"):
        assert f"create table if not exists {table}" in migration
    assert "jsonb" in migration
    assert "events_payload_gin_idx" in migration
    assert "render_segments_order_idx" in migration


def test_simulator_writes_run_state_through_store(tmp_path):
    store = RecordingStore()
    scenario_path = Path("examples/shared_apartment_unresolved_sacrifice.yaml")
    sim = Simulator.from_scenario(
        load_scenario(scenario_path),
        scenario_path,
        seed=42,
        run_store=store,
        run_id="00000000-0000-0000-0000-000000000001",
    )

    result = sim.run(steps=5, output_dir=tmp_path / "run")

    assert result["run_id"] == "00000000-0000-0000-0000-000000000001"
    assert result["storage_backend"] == "recording"
    assert ("upsert_scenario", store.calls[0][1]) in store.calls
    assert any(name == "begin_run" for name, _ in store.calls)
    assert any(call["events"] for call in store.events)
    assert any(call["layer"] == "scheduler" for call in store.traces)
    assert store.snapshots
    assert any(name == "complete_run" and data["status"] == "completed" for name, data in store.calls)


def test_segment_renderer_writes_render_segment_to_store(tmp_path, monkeypatch):
    store = RecordingStore()
    monkeypatch.setattr(segments, "configured_run_store", lambda: store)
    segment = {
        "segment_id": "seg-0001",
        "segment_index": 1,
        "tick_start": 1,
        "tick_end": 1,
        "boundary_reason": "测试闭合",
        "source_ticks": [1],
        "simulated_seconds": 1,
        "frames": [],
        "render_canon": {"title": "测试"},
    }

    result = segments.render_and_append_segment(tmp_path, segment, run_id="00000000-0000-0000-0000-000000000001")

    assert result["segment_id"] == "seg-0001"
    assert store.render_segments
    assert store.render_segments[0]["run_id"] == "00000000-0000-0000-0000-000000000001"
    assert store.render_segments[0]["segment"]["segment_id"] == "seg-0001"


def test_database_records_build_viewer_payload():
    data = {
        "run": {
            "run_id": "00000000-0000-0000-0000-000000000001",
            "output_dir": "",
            "metadata": {"seed": 42},
            "render_canon": {"title": "数据库运行", "cast": {}},
            "case_ledger": {},
        },
        "events": [
            {
                "event_id": "tick-1",
                "tick": 1,
                "event_order": 1,
                "event_type": "TickStartedEvent",
                "source_layer": "diagnostic",
                "payload": {"tick_type": "latent"},
                "causal_refs": [],
            }
        ],
        "traces": [
            {
                "tick": 1,
                "layer": "scheduler",
                "event_type": None,
                "payload": {
                    "tick_index": 1,
                    "selected_tick_type": "latent",
                    "input_factors": {},
                    "simulated_time_delta_seconds": 60,
                    "time_mapping_reason": "db test",
                },
            },
            {
                "tick": 1,
                "layer": "projection",
                "event_type": None,
                "payload": {
                    "tick": 1,
                    "relationship_phase": "db-phase",
                    "person_labels": {},
                    "evidence_refs": [],
                },
            },
        ],
        "render_segments": [
            {
                "segment_id": "seg-0001",
                "segment_index": 1,
                "tick_start": 1,
                "tick_end": 1,
                "source_ticks": [1],
                "boundary_reason": "测试",
                "mode": "deterministic",
                "text": "数据库段落",
            }
        ],
    }

    payload = build_viewer_payload_from_database_records(data)

    assert payload["storage_backend"] == "postgres"
    assert payload["run_id"] == "00000000-0000-0000-0000-000000000001"
    assert payload["render_canon"]["title"] == "数据库运行"
    assert payload["summary"]["event_count"] == 1
    assert payload["summary"]["phase"] == "db-phase"
    assert payload["story"][0]["tick"] == 1
    assert "数据库段落" in payload["rendered_story_stream"]
