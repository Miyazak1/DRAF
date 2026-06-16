from pathlib import Path

import pytest

from rpf.config import database_settings, load_env_file
from rpf.storage.base import NullRunStore
from rpf.storage.postgres import DEFAULT_MIGRATIONS_DIR, PostgresRunStore


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
