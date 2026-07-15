-- ============================================================================
--  Glatt Poker — Esti season-1 arc chart: saved positions
--  Paste into the shared Supabase project's SQL editor and run once.
--  Project: hmvxanqkorcfxwsdusuj  (same project as flag_players / the games)
--
--  Stores ONE row (id = 'esti_s1') whose `positions` JSONB holds the arc:
--    { "v": 2, "y": [16,45,28,72, ...] }   (24 numbers, one per event, 0-100)
--
--  Trust model = the same as flag_players: RLS on, but anon read/insert/update
--  are all open. Anyone with the (noindex, unlisted) page URL can overwrite the
--  shared positions. Fine for an internal tool; see the note at the bottom if
--  you ever want to gate writes behind a secret.
-- ============================================================================

create table if not exists public.glatt_arc_positions (
  id          text        primary key,
  positions   jsonb       not null,
  updated_at  timestamptz not null default now()
);

alter table public.glatt_arc_positions enable row level security;

drop policy if exists "glatt_arc anon read"   on public.glatt_arc_positions;
drop policy if exists "glatt_arc anon insert" on public.glatt_arc_positions;
drop policy if exists "glatt_arc anon update" on public.glatt_arc_positions;

create policy "glatt_arc anon read"
  on public.glatt_arc_positions for select
  using (true);

create policy "glatt_arc anon insert"
  on public.glatt_arc_positions for insert
  with check (true);

create policy "glatt_arc anon update"
  on public.glatt_arc_positions for update
  using (true)
  with check (true);

-- (Optional) seed the row with the current default positions so the page shows
-- "synced" immediately instead of "no data yet". The page will overwrite this
-- the first time someone clicks "שמור לכולם".
insert into public.glatt_arc_positions (id, positions)
values ('esti_s1', '{"v":2,"y":[16,45,28,72,58,66,34,30,68,26,24,74,24,36,55,78,86,40,56,76,50,90,40,34]}'::jsonb)
on conflict (id) do nothing;

-- ----------------------------------------------------------------------------
--  If you ever want ONLY-you writes (readers still see it): the clean way is a
--  SECURITY DEFINER function that checks a passphrase and does the update, with
--  the anon UPDATE/INSERT policies above removed so direct writes are denied.
--  Ask me and I'll add it — it needs a matching change in the page's save code.
-- ----------------------------------------------------------------------------
