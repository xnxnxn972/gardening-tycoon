# 🏴‍☠️ Treasure Traitors: Pirate Party

**Sail. Steal. Betray your friends.**

A Jackbox-style, same-room party game for **3–6 players** (ages 10–15). One shared **main screen** (TV / laptop / iPad) shows the pirate map; each player joins from their **own phone** by scanning a QR code. No app install, **no server to run** — it's static web + Supabase.

## How it's wired (serverless)
- **Static frontend** on GitHub Pages — plain HTML + ES modules, no build step.
- **Supabase** holds the game state and pushes realtime updates. There is no Node server; the **host browser tab is the referee** — it runs the game engine and writes each resolved turn back to Supabase. Because state lives in the DB, the host can refresh mid-game and **resume**.
- Reuses the project's existing Supabase project + anon key (same as Flag Collection / Gardening Tycoon).

```
phones  ──upsert move──►  Supabase (tt_rooms / tt_players / tt_actions)  ──realtime──►  everyone
                                          ▲
                              host tab reads moves, runs engine,
                              writes resolved state each turn
```

## One-time setup (Supabase)
1. Open your Supabase project → **SQL editor** → paste & run [`schema.sql`](./schema.sql). It creates the three tables, opens anon RLS (same trust model as the other games), and **enables Realtime** on them.
2. That's it — the URL/anon key are already in [`js/net.js`](./js/net.js).

> Note: open RLS means a determined player could read others' pending moves via dev tools before the reveal. Accepted for this MVP; locking it down with RLS is in [`BACKLOG.md`](./BACKLOG.md).

## Run / deploy
- **Local test:** serve the repo statically and open
  `http://localhost:8000/treasure-traitors/index.html`
  (the repo's `.claude/serve.ps1` static server works for this).
- **Production:** it's served from GitHub Pages at
  `https://xnxnxn972.github.io/gardening-tycoon/treasure-traitors/`.
  The QR code on the main screen points phones straight at `join.html?room=CODE` on whatever origin you're on.

## How to play
1. Main screen → **Start a New Game** → room code + QR appear.
2. Players scan the QR → enter a name, pick a flag color.
3. Captain hits **Start the Voyage** (3–6 pirates).
4. **15 rounds**: secretly **Choose (10s)** → watch the **Reveal (~10s)**. Most treasure wins.

### Actions
⛵ Sail · 💰 Scavenge · 🪙 Loot · 💣 Sabotage *(anonymous)* · 💥 Cannon Shot *(anonymous)* · 🔧 Repair.
The phone only shows the moves that are legal right now; no pick in time → a sensible default.

## Files
```
treasure-traitors/
├── index.html        # landing (create / join)
├── host.html         # main screen — lobby, board, referee loop, end screen
├── join.html         # phone join (name + color)
├── controller.html   # phone controller
├── styles.css
├── schema.sql        # run once in Supabase
├── js/
│   ├── engine.js     # pure game logic + Skull Ring map (ES module)
│   └── net.js        # Supabase client + room/player/action/realtime helpers
├── README.md
└── BACKLOG.md
```

The engine resolves each turn deterministically — **Repair → Sabotage → Cannon → Loot → Scavenge → Sail** — using start-of-round positions for loot/sabotage.
