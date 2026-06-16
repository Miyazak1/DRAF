create table if not exists scenarios (
  scenario_id text primary key,
  title text not null,
  source_path text,
  source_yaml text not null,
  render_canon jsonb not null default '{}'::jsonb,
  case_ledger jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists runs (
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
  metadata jsonb not null default '{}'::jsonb,
  started_at timestamptz not null default now(),
  completed_at timestamptz
);

create table if not exists events (
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

create index if not exists events_run_tick_idx on events(run_id, tick, event_order);
create index if not exists events_type_idx on events(run_id, event_type);
create index if not exists events_source_layer_idx on events(run_id, source_layer);
create index if not exists events_payload_gin_idx on events using gin(payload jsonb_path_ops);

create table if not exists snapshots (
  run_id uuid not null references runs(run_id) on delete cascade,
  tick integer not null,
  state_hash text not null,
  state_json jsonb not null,
  created_at timestamptz not null default now(),
  primary key (run_id, tick)
);

create table if not exists traces (
  run_id uuid not null references runs(run_id) on delete cascade,
  trace_id bigserial primary key,
  tick integer not null,
  layer text not null,
  event_type text,
  payload jsonb not null,
  created_at timestamptz not null default now()
);

create index if not exists traces_run_layer_tick_idx on traces(run_id, layer, tick);
create index if not exists traces_payload_gin_idx on traces using gin(payload jsonb_path_ops);

create table if not exists render_segments (
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

create unique index if not exists render_segments_order_idx on render_segments(run_id, segment_index);
