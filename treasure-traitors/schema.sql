-- ============================================================================
--  Treasure Traitors: Pirate Party — Supabase schema
--  Paste this into your Supabase project's SQL editor and run once.
--
--  Trust model: same as Flag Collection / Gardening Tycoon — RLS is on but
--  every anon read/insert/update is allowed. No auth; anyone with the page can
--  write. Fine for a local kids' party game. (Locking down move-secrecy with
--  RLS is a tracked backlog item.)
--
--  Three tables, each row owned by a single writer so concurrent writes never
--  clobber each other:
--    tt_rooms   — full authoritative game state (JSONB). HOST writes only.
--    tt_players — lobby roster. Each phone writes its OWN row.
--    tt_actions — per-round move. Each phone upserts its OWN row.
-- ============================================================================

-- ---- rooms: one row per game, host-authoritative ---------------------------
create table if not exists public.tt_rooms (
  code        text        primary key,
  state       jsonb       not null default '{}'::jsonb,
  updated_at  timestamptz not null default now()
);

-- ---- players: lobby roster, one row per (room, player) ---------------------
create table if not exists public.tt_players (
  room_code    text        not null,
  player_id    text        not null,
  name         text        not null,
  color_index  integer     not null default 0,
  updated_at   timestamptz not null default now(),
  primary key (room_code, player_id)
);
create index if not exists tt_players_room_idx on public.tt_players (room_code);

-- ---- actions: this round's secret move, one row per (room, player, round) --
create table if not exists public.tt_actions (
  room_code   text        not null,
  player_id   text        not null,
  round       integer     not null,
  action      jsonb       not null default '{}'::jsonb,
  updated_at  timestamptz not null default now(),
  primary key (room_code, player_id, round)
);
create index if not exists tt_actions_room_round_idx on public.tt_actions (room_code, round);

-- ---- Row-level security: open anon read/write (matches existing games) -----
alter table public.tt_rooms   enable row level security;
alter table public.tt_players enable row level security;
alter table public.tt_actions enable row level security;

do $$
declare t text;
begin
  foreach t in array array['tt_rooms','tt_players','tt_actions'] loop
    execute format('drop policy if exists "%s anon read"   on public.%I', t, t);
    execute format('drop policy if exists "%s anon insert" on public.%I', t, t);
    execute format('drop policy if exists "%s anon update" on public.%I', t, t);
    execute format('drop policy if exists "%s anon delete" on public.%I', t, t);
    execute format('create policy "%s anon read"   on public.%I for select using (true)', t, t);
    execute format('create policy "%s anon insert" on public.%I for insert with check (true)', t, t);
    execute format('create policy "%s anon update" on public.%I for update using (true) with check (true)', t, t);
    execute format('create policy "%s anon delete" on public.%I for delete using (true)', t, t);
  end loop;
end $$;

-- ---- Realtime: clients subscribe to postgres_changes on these tables -------
-- (New for this project — the other games only upsert/poll.)
alter publication supabase_realtime add table public.tt_rooms;
alter publication supabase_realtime add table public.tt_players;
alter publication supabase_realtime add table public.tt_actions;

-- ---- Housekeeping: drop rooms older than a day (optional, run manually) -----
-- delete from public.tt_rooms   where updated_at < now() - interval '1 day';
-- delete from public.tt_players where updated_at < now() - interval '1 day';
-- delete from public.tt_actions where updated_at < now() - interval '1 day';
