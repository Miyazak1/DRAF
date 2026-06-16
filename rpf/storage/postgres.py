from __future__ import annotations

from pathlib import Path
from typing import Any

from rpf.config import DatabaseSettings
from rpf.core.events import Event
from rpf.core.models import SimulationState


DEFAULT_MIGRATIONS_DIR = Path(__file__).resolve().parents[2] / "deploy" / "postgres" / "migrations"


class PostgresRunStore:
    backend_name = "postgres"

    def __init__(self, settings: DatabaseSettings) -> None:
        if not settings.database_url:
            raise ValueError("PostgreSQL storage requires RPF_DATABASE_URL.")
        self.settings = settings

    def apply_migrations(self, migrations_dir: Path = DEFAULT_MIGRATIONS_DIR) -> None:
        with self._connect() as conn:
            with conn.cursor() as cur:
                for path in sorted(migrations_dir.glob("*.sql")):
                    cur.execute(path.read_text(encoding="utf-8"))
            conn.commit()

    def upsert_scenario(
        self,
        *,
        scenario_id: str,
        title: str,
        source_yaml: str,
        source_path: Path | None = None,
        render_canon: dict[str, Any] | None = None,
        case_ledger: dict[str, Any] | None = None,
    ) -> None:
        query = """
        insert into scenarios (scenario_id, title, source_path, source_yaml, render_canon, case_ledger)
        values (%s, %s, %s, %s, %s, %s)
        on conflict (scenario_id) do update set
          title = excluded.title,
          source_path = excluded.source_path,
          source_yaml = excluded.source_yaml,
          render_canon = excluded.render_canon,
          case_ledger = excluded.case_ledger
        """
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    query,
                    (
                        scenario_id,
                        title,
                        str(source_path) if source_path else None,
                        source_yaml,
                        self._jsonb(render_canon or {}),
                        self._jsonb(case_ledger or {}),
                    ),
                )
            conn.commit()

    def begin_run(
        self,
        *,
        run_id: str,
        scenario_id: str,
        title: str,
        seed: int,
        mode: str,
        output_dir: Path | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        query = """
        insert into runs (run_id, scenario_id, seed, mode, status, title, output_dir, metadata)
        values (%s, %s, %s, %s, 'running', %s, %s, %s)
        on conflict (run_id) do update set
          status = excluded.status,
          title = excluded.title,
          output_dir = excluded.output_dir,
          metadata = excluded.metadata
        """
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    query,
                    (
                        run_id,
                        scenario_id,
                        seed,
                        mode,
                        title,
                        str(output_dir) if output_dir else None,
                        self._jsonb(metadata or {}),
                    ),
                )
            conn.commit()

    def write_events(self, *, run_id: str, events: list[Event]) -> None:
        if not events:
            return
        rows = [
            (
                run_id,
                event.event_id,
                event.tick,
                event.deterministic_order,
                event.event_type,
                event.source_layer,
                self._jsonb(event.payload),
                event.causal_refs,
            )
            for event in events
        ]
        query = """
        insert into events (run_id, event_id, tick, event_order, event_type, source_layer, payload, causal_refs)
        values (%s, %s, %s, %s, %s, %s, %s, %s)
        on conflict (run_id, event_id) do update set
          payload = excluded.payload,
          causal_refs = excluded.causal_refs
        """
        self._executemany(query, rows)

    def write_traces(self, *, run_id: str, layer: str, records: list[dict[str, Any]]) -> None:
        rows = [
            (
                run_id,
                int(record.get("tick", 0) or 0),
                layer,
                record.get("event_type"),
                self._jsonb(record),
            )
            for record in records
        ]
        query = """
        insert into traces (run_id, tick, layer, event_type, payload)
        values (%s, %s, %s, %s, %s)
        """
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute("delete from traces where run_id = %s and layer = %s", (run_id, layer))
                if rows:
                    cur.executemany(query, rows)
            conn.commit()

    def write_snapshot(self, *, run_id: str, state: SimulationState) -> None:
        query = """
        insert into snapshots (run_id, tick, state_hash, state_json)
        values (%s, %s, %s, %s)
        on conflict (run_id, tick) do update set
          state_hash = excluded.state_hash,
          state_json = excluded.state_json
        """
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (run_id, state.tick, state.state_hash(), self._jsonb(state.model_dump(mode="json"))))
            conn.commit()

    def write_render_segment(self, *, run_id: str, segment: dict[str, Any]) -> None:
        query = """
        insert into render_segments (
          run_id, segment_id, segment_index, tick_start, tick_end,
          source_ticks, boundary_reason, mode, text, prompt_payload, model
        )
        values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        on conflict (run_id, segment_id) do update set
          text = excluded.text,
          prompt_payload = excluded.prompt_payload,
          model = excluded.model
        """
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    query,
                    (
                        run_id,
                        segment["segment_id"],
                        int(segment["segment_index"]),
                        int(segment["tick_start"]),
                        int(segment["tick_end"]),
                        [int(tick) for tick in segment.get("source_ticks", [])],
                        segment.get("boundary_reason", ""),
                        segment.get("mode", ""),
                        segment.get("text", ""),
                        self._jsonb(segment.get("prompt_payload")),
                        segment.get("model"),
                    ),
                )
            conn.commit()

    def read_viewer_run(self, *, run_id: str) -> dict[str, Any]:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    select r.*, s.title as scenario_title, s.render_canon, s.case_ledger, s.source_path
                    from runs r
                    join scenarios s on s.scenario_id = r.scenario_id
                    where r.run_id = %s
                    """,
                    (run_id,),
                )
                run = self._row_dict(cur.fetchone(), cur)
                if not run:
                    return {}
                cur.execute(
                    """
                    select event_id, tick, event_order, event_type, source_layer, payload, causal_refs
                    from events
                    where run_id = %s
                    order by tick, event_order
                    """,
                    (run_id,),
                )
                events = [self._row_dict(row, cur) for row in cur.fetchall()]
                cur.execute(
                    """
                    select tick, layer, event_type, payload
                    from traces
                    where run_id = %s
                    order by tick, trace_id
                    """,
                    (run_id,),
                )
                traces = [self._row_dict(row, cur) for row in cur.fetchall()]
                cur.execute(
                    """
                    select segment_id, segment_index, tick_start, tick_end, source_ticks, boundary_reason, mode, text, model
                    from render_segments
                    where run_id = %s
                    order by segment_index
                    """,
                    (run_id,),
                )
                render_segments = [self._row_dict(row, cur) for row in cur.fetchall()]
        return {
            "run": self._json_ready(run),
            "events": [self._json_ready(event) for event in events],
            "traces": [self._json_ready(trace) for trace in traces],
            "render_segments": [self._json_ready(segment) for segment in render_segments],
        }

    def list_runs(self, *, limit: int = 50) -> list[dict[str, Any]]:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    select r.run_id, r.scenario_id, r.title, r.output_dir, r.mode, r.seed,
                           r.tick_count, r.event_count, r.status, r.started_at, r.completed_at,
                           coalesce(r.final_state_hash, '') as final_state_hash
                    from runs r
                    order by r.started_at desc
                    limit %s
                    """,
                    (limit,),
                )
                rows = [self._row_dict(row, cur) for row in cur.fetchall()]
        return [self._json_ready(row) for row in rows]

    def complete_run(
        self,
        *,
        run_id: str,
        status: str,
        tick_count: int,
        event_count: int,
        final_state_hash: str | None = None,
    ) -> None:
        query = """
        update runs
        set status = %s,
            tick_count = %s,
            event_count = %s,
            final_state_hash = %s,
            completed_at = case when %s in ('completed', 'error', 'stopped') then now() else completed_at end
        where run_id = %s
        """
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (status, tick_count, event_count, final_state_hash, status, run_id))
            conn.commit()

    def _executemany(self, query: str, rows: list[tuple[Any, ...]]) -> None:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.executemany(query, rows)
            conn.commit()

    def _connect(self) -> Any:
        try:
            import psycopg
        except ImportError as exc:
            raise RuntimeError("Install psycopg to use PostgreSQL storage: pip install 'psycopg[binary]>=3.2,<4'.") from exc
        return psycopg.connect(self.settings.database_url)

    def _jsonb(self, value: Any) -> Any:
        try:
            from psycopg.types.json import Jsonb
        except ImportError as exc:
            raise RuntimeError("Install psycopg to use PostgreSQL JSONB support.") from exc
        return Jsonb(value if value is not None else {})

    def _row_dict(self, row: Any, cursor: Any) -> dict[str, Any]:
        if row is None:
            return {}
        columns = [column.name for column in cursor.description]
        return dict(zip(columns, row))

    def _json_ready(self, value: Any) -> Any:
        if isinstance(value, dict):
            return {key: self._json_ready(item) for key, item in value.items()}
        if isinstance(value, list):
            return [self._json_ready(item) for item in value]
        if hasattr(value, "isoformat"):
            return value.isoformat()
        return value
