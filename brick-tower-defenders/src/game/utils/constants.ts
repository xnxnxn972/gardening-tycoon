export const GAME_WIDTH = 1600;
export const GAME_HEIGHT = 900;

export const STARTING_GOLD = 500;
export const STARTING_LIVES = 20;
export const MAX_LIVES = 20;

// Selling a tower refunds this fraction of everything invested in it.
export const SELL_REFUND = 0.7;
// Upgrading costs this fraction of the tower's base cost.
export const UPGRADE_COST_FACTOR = 0.5;
export const UPGRADE_DAMAGE_MULT = 1.4;
export const UPGRADE_RANGE_MULT = 1.1;
export const UPGRADE_SPEED_MULT = 1.1; // fireRate divided by this (10% faster)

// Distance (px) at which an idle squad knight grabs a passing ground enemy.
export const BLOCK_RADIUS = 42;
// Seconds between melee swings for a blocked enemy.
export const ENEMY_MELEE_RATE = 1.0;

export type GameState = 'loading' | 'build' | 'wave' | 'victory' | 'defeat';

// Render depths. Battlefield entities add y * 0.001 for a cheap 2.5D sort.
export const DEPTH = {
  bg: 0,
  core: 4,
  slot: 5,
  entity: 10, // enemies / knights / towers, +y*0.001
  projectile: 30,
  fx: 40,
  ui: 100,
  overlay: 200
} as const;

export const UI_FONT = 'Arial Black, Arial, sans-serif';
