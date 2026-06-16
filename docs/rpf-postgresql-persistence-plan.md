# RPF PostgreSQL Persistence Plan

## Decision

RPF will use PostgreSQL as the primary persistence backend once file-only storage is no longer enough.

The current runtime remains file-first for immediate inspectability, but the target database is PostgreSQL, not SQLite or MySQL.

## Why PostgreSQL

RPF is an event-sourced simulation system. Its durable objects are:

- simulation runs
- append-only events
- per-layer traces
- snapshots
- rendered segments
- scenario versions
- run metadata
- future comparison and replay records

PostgreSQL fits this better than MySQL because it has strong JSONB support, indexing over structured payloads, reliable transactional append, generated columns, partial indexes, and good analytical query ergonomics.

SQLite is still useful for local experiments, but it should not become the main persistence contract.

## Storage Principles

1. Events are append-only.
2. Snapshots are cached derived state, not the source of truth.
3. Trace tables are query accelerators over the event stream.
4. Rendered text is versioned output, not causal state.
5. Scenario definitions are immutable once a run starts.
6. Every durable row belongs to a run.
7. Replays must be reconstructable from scenario version, seed, config version, and event stream.

## Core Tables

### `scenarios`

Stores scenario source and canonical identity.

```sql
create table scenarios (
  scenario_id text primary key,
  title text not null,
  source_path text,
  source_yaml text not null,
  render_canon jsonb not null default '{}'::jsonb,
  case_ledger jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);
```

### `runs`

Stores one simulation run.

```sql
create table runs (
  run_id uuid primary key,
  scenario_id text not null references scenarios(scenario_id),
  seed integer not null,
  mode text not null,
  status text not null,
  title text not null,
  output_dir text,
  config_hash text,
  final_state_hash text,
  tick_count integer not null default 0,
  event_count integer not null default 0,
  started_at timestamptz not null default now(),
  completed_at timestamptz
);
```

### `events`

The causal event stream.

```sql
create table events (
  run_id uuid not null references runs(run_id) on delete cascade,
  event_id text not null,
  tick integer not null,
  event_order integer not null,
  event_type text not null,
  source_layer text not null,
  payload jsonb not null,
  causal_refs text[] not null default '{}',
  created_at timestamptz not null default now(),
  primary key (run_id, event_id)
);

create index events_run_tick_idx on events(run_id, tick, event_order);
create index events_type_idx on events(run_id, event_type);
create index events_source_layer_idx on events(run_id, source_layer);
create index events_payload_gin_idx on events using gin(payload jsonb_path_ops);
```

### `snapshots`

Cached state for fast resume and viewer loading.

```sql
create table snapshots (
  run_id uuid not null references runs(run_id) on delete cascade,
  tick integer not null,
  state_hash text not null,
  state_json jsonb not null,
  created_at timestamptz not null default now(),
  primary key (run_id, tick)
);
```

### `traces`

Normalized per-layer observability records. This can start as one generic table before specialized views are added.

```sql
create table traces (
  run_id uuid not null references runs(run_id) on delete cascade,
  trace_id bigserial primary key,
  tick integer not null,
  layer text not null,
  event_type text,
  payload jsonb not null,
  created_at timestamptz not null default now()
);

create index traces_run_layer_tick_idx on traces(run_id, layer, tick);
create index traces_payload_gin_idx on traces using gin(payload jsonb_path_ops);
```

### `render_segments`

Stores append-only LLM or deterministic rendered segments.

```sql
create table render_segments (
  run_id uuid not null references runs(run_id) on delete cascade,
  segment_id text not null,
  segment_index integer not null,
  tick_start integer not null,
  tick_end integer not null,
  source_ticks integer[] not null,
  boundary_reason text not null,
  mode text not null,
  text text not null,
  prompt_payload jsonb,
  model text,
  created_at timestamptz not null default now(),
  primary key (run_id, segment_id)
);

create unique index render_segments_order_idx on render_segments(run_id, segment_index);
```

## Runtime Write Path

During a tick:

1. Append events to `events`.
2. Append layer trace records to `traces`.
3. Periodically write `snapshots`.
4. Update `runs.tick_count`, `runs.event_count`, and `runs.status`.
5. When rendering closes a segment, append one row to `render_segments`.

The file exporter can still write `timeline.jsonl`, `*_trace.json`, and Markdown bundles from PostgreSQL rows.

## Migration Path

Phase 1 keeps current files and adds a PostgreSQL writer behind a storage interface.

Phase 2 lets the viewer read either a run directory or a PostgreSQL `run_id`.

Phase 3 makes PostgreSQL the canonical backend for cloud deployment while preserving file export.

Phase 4 adds comparison queries, replay lineage, and run search.

## What Not To Store As Primary State

Do not make these the source of truth:

- aggregated views
- relationship summaries
- LLM prose
- dashboard cards
- report Markdown

They can be cached, regenerated, or exported, but causal truth remains the event stream plus scenario/config/seed.

