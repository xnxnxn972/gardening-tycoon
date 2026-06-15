// net.js — Supabase networking for Treasure Traitors
// Reuses the project's existing Supabase project + anon key (same as Flag
// Collection / Gardening Tycoon). The anon key is public by design.
//
// Three tables (see schema.sql): tt_rooms (host-written state),
// tt_players (self-written roster), tt_actions (self-written moves).

import { createClient } from '@supabase/supabase-js';

const SUPABASE_URL      = 'https://hmvxanqkorcfxwsdusuj.supabase.co';
const SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImhtdnhhbnFrb3JjZnh3c2R1c3VqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzk3MjI4OTgsImV4cCI6MjA5NTI5ODg5OH0.7o7OnhikQdgApqPTEIbhjOZ-YcKDU1fBFpcLXPXtEtA';

export const CLOUD_ENABLED = !SUPABASE_URL.startsWith('YOUR_');
export const supabase = CLOUD_ENABLED ? createClient(SUPABASE_URL, SUPABASE_ANON_KEY) : null;

// ---- room code from the URL (?room=ABCD) ----------------------------------
export function roomFromUrl() {
  const u = new URL(location.href);
  return (u.searchParams.get('room') || '').toUpperCase();
}

// Build the absolute join URL for the QR code (works on Pages or localhost).
export function joinUrl(code) {
  const base = location.href.replace(/[^/]*$/, ''); // strip current file name
  return `${base}join.html?room=${code}`;
}

// ---- rooms (host-authoritative state) -------------------------------------
export async function createRoom(code, state) {
  const { error } = await supabase.from('tt_rooms').insert({ code, state });
  if (error) throw error;
}

export async function writeState(code, state) {
  const { error } = await supabase
    .from('tt_rooms')
    .update({ state, updated_at: new Date().toISOString() })
    .eq('code', code);
  if (error) throw error;
}

export async function readState(code) {
  const { data, error } = await supabase.from('tt_rooms').select('state').eq('code', code).maybeSingle();
  if (error) throw error;
  return data ? data.state : null;
}

// ---- players (lobby roster) -----------------------------------------------
export async function joinAsPlayer(code, playerId, name, colorIndex) {
  const { error } = await supabase.from('tt_players').upsert({
    room_code: code, player_id: playerId, name, color_index: colorIndex,
    updated_at: new Date().toISOString(),
  });
  if (error) throw error;
}

export async function readRoster(code) {
  const { data, error } = await supabase
    .from('tt_players').select('player_id, name, color_index')
    .eq('room_code', code).order('updated_at', { ascending: true });
  if (error) throw error;
  return data || [];
}

// ---- actions (this round's secret move) -----------------------------------
export async function submitAction(code, playerId, round, action) {
  const { error } = await supabase.from('tt_actions').upsert({
    room_code: code, player_id: playerId, round, action,
    updated_at: new Date().toISOString(),
  });
  if (error) throw error;
}

export async function readActions(code, round) {
  const { data, error } = await supabase
    .from('tt_actions').select('player_id, action')
    .eq('room_code', code).eq('round', round);
  if (error) throw error;
  const map = {};
  for (const row of data || []) map[row.player_id] = row.action;
  return map;
}

// ---- realtime subscriptions -----------------------------------------------
// Subscribe to a room's state row. cb(state) fires on every change.
export function subscribeRoom(code, cb) {
  const ch = supabase
    .channel(`tt_room_${code}`)
    .on('postgres_changes',
      { event: '*', schema: 'public', table: 'tt_rooms', filter: `code=eq.${code}` },
      (payload) => { if (payload.new && payload.new.state) cb(payload.new.state); })
    .subscribe();
  return () => supabase.removeChannel(ch);
}

// Subscribe to roster changes (host lobby). cb() fires; caller re-reads roster.
export function subscribeRoster(code, cb) {
  const ch = supabase
    .channel(`tt_roster_${code}`)
    .on('postgres_changes',
      { event: '*', schema: 'public', table: 'tt_players', filter: `room_code=eq.${code}` },
      () => cb())
    .subscribe();
  return () => supabase.removeChannel(ch);
}

// Subscribe to action submissions (host shows who's locked in). cb() fires.
export function subscribeActions(code, cb) {
  const ch = supabase
    .channel(`tt_actions_${code}`)
    .on('postgres_changes',
      { event: '*', schema: 'public', table: 'tt_actions', filter: `room_code=eq.${code}` },
      (payload) => cb(payload.new))
    .subscribe();
  return () => supabase.removeChannel(ch);
}

// ---- ids ------------------------------------------------------------------
export function makePlayerId() {
  return (crypto.randomUUID && crypto.randomUUID()) ||
    'p-' + Math.random().toString(36).slice(2) + '-' + Date.now().toString(36);
}
