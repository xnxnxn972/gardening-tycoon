// engine.js — Treasure Traitors: Pirate Party
// Pure game logic + Skull Ring map. Runs in the browser (the HOST tab is the
// referee). No networking here — see net.js.

export const TOTAL_ROUNDS = 15;
export const CHOOSE_SECONDS = 15;
export const REVEAL_SECONDS = 10;

// Six pirate colors (supports 3–6 players).
export const COLORS = [
  { name: 'Red',    hex: '#e63946' },
  { name: 'Blue',   hex: '#1d75d0' },
  { name: 'Green',  hex: '#2a9d3a' },
  { name: 'Yellow', hex: '#f4b400' },
  { name: 'Purple', hex: '#8e44ad' },
  { name: 'Orange', hex: '#e8730c' },
];

// ---- Skull Ring map -------------------------------------------------------
// neighbors = adjacency, treasure = starting treasure, x/y = host graph layout
// (SVG viewBox 0 0 1000 700).
export function freshMap() {
  return {
    name: 'Skull Ring',
    islands: {
      'Skull Rock':      { neighbors: ['Rum Bay', 'Cannon Cay'],                          treasure: 2, x: 210, y: 120 },
      'Rum Bay':         { neighbors: ['Skull Rock', 'Gold Cove'],                        treasure: 2, x: 480, y: 95  },
      'Gold Cove':       { neighbors: ['Rum Bay', 'Shark Reef', 'Monkey Isle'],           treasure: 3, x: 660, y: 235 },
      'Cannon Cay':      { neighbors: ['Skull Rock', 'Shark Reef'],                       treasure: 2, x: 140, y: 360 },
      'Shark Reef':      { neighbors: ['Cannon Cay', 'Gold Cove', 'Shipwreck Point'],     treasure: 2, x: 390, y: 385 },
      'Monkey Isle':     { neighbors: ['Gold Cove', 'Shipwreck Point', 'Treasure Atoll'], treasure: 2, x: 840, y: 350 },
      'Shipwreck Point': { neighbors: ['Shark Reef', 'Monkey Isle', 'Treasure Atoll'],    treasure: 2, x: 600, y: 540 },
      'Treasure Atoll':  { neighbors: ['Monkey Isle', 'Shipwreck Point'],                 treasure: 3, x: 850, y: 580 },
    },
  };
}

// Islands players prefer to start on (distinct for 3–6 players).
export const PREFERRED_START = [
  'Skull Rock', 'Rum Bay', 'Cannon Cay',
  'Monkey Isle', 'Shipwreck Point', 'Treasure Atoll',
];

// ---- helpers --------------------------------------------------------------
function shuffle(arr) {
  const a = arr.slice();
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

export function makeRoomCode() {
  const chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'; // no confusing chars
  let code = '';
  for (let i = 0; i < 4; i++) code += chars[Math.floor(Math.random() * chars.length)];
  return code;
}

// ---- state builders -------------------------------------------------------
// The whole game lives in one plain object (mirrors the old server `room`).
// It is JSON-serializable so it can be stored verbatim in tt_rooms.state.

export function lobbyState(code) {
  return {
    code,
    phase: 'lobby',            // lobby | choose | reveal | over
    round: 0,
    totalRounds: TOTAL_ROUNDS,
    deadline: 0,               // epoch ms when the current phase ends
    map: freshMap(),
    players: [],               // [{id,name,color,colorName,island,treasure,damaged,...}]
    messages: [],
    events: [],
    results: null,
  };
}

// Build a player record from a roster row (tt_players).
function newPlayer(id, name, colorIndex) {
  const c = COLORS[colorIndex] || COLORS[0];
  return {
    id, name,
    colorIndex,
    color: c.hex,
    colorName: c.name,
    island: null,
    treasure: 0,
    damaged: false,
    // stats for awards / tie-breakers
    loots: 0, cannonHits: 0, timesDamaged: 0, scavenged: 0,
  };
}

// Start the match from a roster: [{player_id, name, color_index}, ...].
export function startGame(state, roster) {
  state.map = freshMap();
  const slots = shuffle(PREFERRED_START);
  state.players = roster.map((r, i) => {
    const p = newPlayer(r.player_id, r.name, r.color_index);
    p.island = slots[i % slots.length];
    return p;
  });
  state.round = 1;
  state.phase = 'choose';
  state.messages = [];
  state.results = null;
}

// Default action when a player doesn't submit in time.
export function defaultAction(state, p) {
  if (p.damaged) return { type: 'repair' };
  const isl = state.map.islands[p.island];
  if (isl.treasure > 0) return { type: 'scavenge' };
  if (isl.neighbors.length > 0) {
    return { type: 'sail', destination: isl.neighbors[Math.floor(Math.random() * isl.neighbors.length)] };
  }
  return { type: 'none' };
}

// Is a chosen action legal for this player given current public state?
// Used by the controller to show only valid buttons, and as a host-side guard.
export function isLegal(state, p, action) {
  const byId = Object.fromEntries(state.players.map((x) => [x.id, x]));
  const isl = state.map.islands[p.island];
  switch (action.type) {
    case 'repair':
      return p.damaged;
    case 'sail':
      return !p.damaged && isl.neighbors.includes(action.destination);
    case 'scavenge':
      return !p.damaged && isl.treasure > 0;
    case 'loot': {
      const t = byId[action.target];
      return !p.damaged && t && t.id !== p.id && t.island === p.island && t.treasure > 0;
    }
    case 'sabotage': {
      const t = byId[action.target];
      return !p.damaged && t && t.id !== p.id && t.island === p.island;
    }
    case 'cannon': {
      const t = byId[action.target];
      return !p.damaged && t && t.id !== p.id && t.treasure > 0;
    }
    case 'none':
      return true;
    default:
      return false;
  }
}

// ---- simultaneous resolution ---------------------------------------------
// Resolution order: Repair, Sabotage, Cannon, Loot, Scavenge, Sail.
// `actions` is a map of playerId -> action (already defaulted for no-shows).
export function resolveRound(state, actions) {
  const players = state.players;
  const map = state.map;
  const byId = Object.fromEntries(players.map((p) => [p.id, p]));
  const messages = [];
  const events = [];   // structured, for the host's reveal animations
  const act = (p) => actions[p.id] || { type: 'none' };

  // Snapshot start-of-round state (loot/sabotage use start positions).
  for (const p of players) {
    p.startIsland = p.island;
    p.startDamaged = p.damaged;
    p.canceled = false;
  }

  // Step 1: Repair
  for (const p of players) {
    if (p.startDamaged && act(p).type === 'repair') {
      p.damaged = false;
      events.push({ kind: 'repair', id: p.id, island: p.startIsland });
      messages.push({ emoji: '🔧', text: `${p.name} repaired the ship.`, color: p.color });
    }
  }

  // Step 2: Sabotage (compute all from start state, then apply — simultaneous)
  const sabotagedIds = new Set();
  for (const p of players) {
    const a = act(p);
    if (a.type === 'sabotage' && !p.startDamaged) {
      const t = byId[a.target];
      if (t && t.id !== p.id && t.startIsland === p.startIsland) sabotagedIds.add(t.id);
    }
  }
  for (const id of sabotagedIds) {
    const t = byId[id];
    t.damaged = true;
    t.canceled = true; // cancels target's chosen action downstream
    t.timesDamaged += 1;
    events.push({ kind: 'sabotage', target: id, island: t.startIsland });
    messages.push({ emoji: '💣', text: `Someone sabotaged ${t.name}'s ship!`, color: t.color, anon: true });
  }

  // Step 3: Cannon Shot (target's current island = pre-sail island)
  const cannoneers = shuffle(players.filter((p) => act(p).type === 'cannon' && !p.canceled));
  for (const p of cannoneers) {
    const t = byId[act(p).target];
    if (t && t.id !== p.id && t.treasure > 0) {
      t.treasure -= 1;
      map.islands[t.island].treasure += 1;
      p.cannonHits += 1;
      events.push({ kind: 'cannon', target: t.id, island: t.island });
      messages.push({
        emoji: '💥',
        text: `Someone fired a cannon at ${t.name}! ${t.name} dropped 1 treasure on ${t.island}.`,
        color: t.color, anon: true,
      });
    }
  }

  // Step 4: Loot (random order; same-island check uses start positions)
  const looters = shuffle(players.filter((p) => act(p).type === 'loot' && !p.canceled));
  for (const p of looters) {
    const t = byId[act(p).target];
    if (t && t.id !== p.id && t.startIsland === p.startIsland && t.treasure > 0) {
      t.treasure -= 1;
      p.treasure += 1;
      p.loots += 1;
      events.push({ kind: 'loot', actor: p.id, target: t.id, island: p.startIsland });
      messages.push({ emoji: '🪙', text: `${p.name} looted 1 treasure from ${t.name}!`, color: p.color });
    }
  }

  // Step 5: Scavenge (pre-sail island; random share if scarce)
  const byIsland = {};
  for (const p of players) {
    if (act(p).type === 'scavenge' && !p.canceled) {
      (byIsland[p.startIsland] = byIsland[p.startIsland] || []).push(p);
    }
  }
  for (const islandName of Object.keys(byIsland)) {
    const scavengers = shuffle(byIsland[islandName]);
    const avail = map.islands[islandName].treasure;
    const winners = scavengers.slice(0, avail);
    for (const w of winners) {
      map.islands[islandName].treasure -= 1;
      w.treasure += 1;
      w.scavenged += 1;
      events.push({ kind: 'scavenge', id: w.id, island: islandName });
    }
    if (winners.length === 0) {
      messages.push({ emoji: '🗺️', text: `Pirates searched ${islandName} but found nothing!` });
    } else if (scavengers.length === 1) {
      messages.push({ emoji: '💰', text: `${winners[0].name} found treasure on ${islandName}!`, color: winners[0].color });
    } else if (winners.length === scavengers.length) {
      messages.push({ emoji: '💰', text: `Everyone digging on ${islandName} struck gold!` });
    } else {
      messages.push({
        emoji: '💰',
        text: `${scavengers.length} pirates searched ${islandName}… ${winners.map((w) => w.name).join(' & ')} found the treasure!`,
      });
    }
  }

  // Step 6: Sail (movement happens last)
  for (const p of players) {
    const a = act(p);
    if (a.type === 'sail' && !p.canceled) {
      if (map.islands[p.startIsland].neighbors.includes(a.destination)) {
        p.island = a.destination;
        events.push({ kind: 'sail', id: p.id, from: p.startIsland, to: a.destination });
        messages.push({ emoji: '⛵', text: `${p.name} sailed to ${a.destination}.`, color: p.color });
      }
    }
  }

  if (messages.length === 0) messages.push({ emoji: '🌊', text: 'The seas were calm this round…' });

  // Clean transient snapshot fields so the stored state stays tidy.
  for (const p of players) { delete p.startIsland; delete p.startDamaged; delete p.canceled; }

  state.messages = messages;
  state.events = events;
  return messages;
}

// ---- end game -------------------------------------------------------------
export function endGame(state) {
  const players = state.players;
  const ranked = players.slice().sort((a, b) => {
    if (b.treasure !== a.treasure) return b.treasure - a.treasure;                 // most treasure
    if (a.timesDamaged !== b.timesDamaged) return a.timesDamaged - b.timesDamaged;  // least damaged
    if (b.loots !== a.loots) return b.loots - a.loots;                             // most loots
    return Math.random() - 0.5;                                                    // coin toss
  });
  const winner = ranked[0];

  const awards = [];
  const best = (stat) => players.reduce((m, p) => (p[stat] > m[stat] ? p : m), players[0]);
  const sneaky = best('loots');
  if (sneaky.loots > 0) awards.push({ title: 'Sneakiest Pirate', emoji: '🦝', player: sneaky.name, color: sneaky.color, detail: `${sneaky.loots} loots` });
  const danger = best('cannonHits');
  if (danger.cannonHits > 0) awards.push({ title: 'Most Dangerous Pirate', emoji: '💥', player: danger.name, color: danger.color, detail: `${danger.cannonHits} cannon hits` });
  const unlucky = best('timesDamaged');
  if (unlucky.timesDamaged > 0) awards.push({ title: 'Most Unlucky Pirate', emoji: '🩹', player: unlucky.name, color: unlucky.color, detail: `${unlucky.timesDamaged}× damaged` });
  const scavenger = best('scavenged');
  if (scavenger.scavenged > 0) awards.push({ title: 'Best Scavenger', emoji: '🪏', player: scavenger.name, color: scavenger.color, detail: `${scavenger.scavenged} found` });

  state.phase = 'over';
  state.results = {
    winner: { name: winner.name, color: winner.color, treasure: winner.treasure },
    standings: ranked.map((p) => ({ name: p.name, color: p.color, treasure: p.treasure })),
    awards,
  };
}
