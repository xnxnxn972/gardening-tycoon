export interface Vec2 {
  x: number;
  y: number;
}

export interface LevelTheme {
  /** Background texture key — a themed background generator registers this key. */
  bgTexture: string;
  pathFill: number;
  pathBorder: number;
  pathStud: number;
}

export interface LevelData {
  id: string;
  name: string;
  path: Vec2[]; // enemy waypoints, entrance → core
  buildSlots: Vec2[];
  core: Vec2; // where the Golden Brick Core sits
  theme: LevelTheme;
}

/**
 * Map 1: Castle Room. More maps/themes later = more LevelData files;
 * the scenes and systems only ever read from a LevelData object.
 */
export const LEVEL_CASTLE: LevelData = {
  id: 'castle',
  name: 'Castle Room',
  path: [
    { x: -50, y: 420 },
    { x: 180, y: 420 },
    { x: 300, y: 280 },
    { x: 520, y: 280 },
    { x: 650, y: 520 },
    { x: 880, y: 520 },
    { x: 1030, y: 340 },
    { x: 1220, y: 340 },
    { x: 1400, y: 450 },
    { x: 1570, y: 450 }
  ],
  buildSlots: [
    { x: 260, y: 300 },
    { x: 410, y: 520 },
    { x: 600, y: 360 },
    { x: 760, y: 620 },
    { x: 930, y: 390 },
    { x: 1110, y: 520 },
    { x: 1260, y: 300 },
    { x: 1350, y: 590 }
  ],
  core: { x: 1520, y: 450 },
  theme: {
    bgTexture: 'bg_castle',
    pathFill: 0xc9a96a,
    pathBorder: 0x8a6f42,
    pathStud: 0xb8985c
  }
};
