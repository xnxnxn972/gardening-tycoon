# Treasure Traitors — Backlog / Future Features

## Security / integrity (deferred from MVP)
- **Move secrecy via RLS.** Right now `tt_actions` is world-readable, so a curious
  player could open dev tools and read others' pending moves before the reveal.
  Lock it down so a player can write only their own action and can't read others'
  until the host flips the phase to `reveal` (Supabase row-level security policies),
  or move resolution into a Supabase Edge Function so clients never see raw actions.
- **Host handoff / auto-resume.** State is durable in `tt_rooms`, so the host tab can
  refresh and resume. Next step: if the host disconnects for good, let another device
  claim the referee role (or run the referee in an Edge Function so no client is special).

## Match tuning
Playtest match length: 10 / 12 / 15 (current) / 18 rounds.

## Space theme (same engine, reskinned)
Planets, spaceships, crystals, Laser Shot (cannon), Hack (sabotage).

## Ship customization
Color, style, sails/flags/skulls/stickers.

## Vessel names
Name your ship (The Sneaky Squid, Gold Goblin, Banana Cannon).

## Additional maps
Central-island, two-cluster, maze, high-conflict small, large 6-player.

## Optional modes
Anonymous cannon on/off, anonymous sabotage on/off, chaotic treasure-refill, team mode, hidden traitor.

## Housekeeping
- Periodic cleanup of stale rooms (a scheduled `delete from tt_rooms where updated_at < now() - interval '1 day'`, plus tt_players/tt_actions).
- Sound effects for cannon / sabotage / treasure.
