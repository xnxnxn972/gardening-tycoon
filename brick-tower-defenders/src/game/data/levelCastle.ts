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
  /**
   * Opacity of the slot_pad sprite drawn on each build slot. 0 when the
   * background art already paints the pads; 1 for placeholder backgrounds.
   */
  slotOpacity: number;
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
  // Positions measured from the stone pads painted into bg_castle.png —
  // keep these in sync if the background art changes.
  buildSlots: [
    { x: 288, y: 292 },
    { x: 420, y: 522 },
    { x: 612, y: 360 },
    { x: 757, y: 622 },
    { x: 913, y: 387 },
    { x: 1105, y: 532 },
    { x: 1262, y: 302 },
    { x: 1355, y: 594 },
    { x: 987, y: 175 }
  ],
  core: { x: 1520, y: 450 },
  theme: {
    bgTexture: 'bg_castle',
    pathFill: 0xc9a96a,
    pathBorder: 0x8a6f42,
    pathStud: 0xb8985c,
    slotOpacity: 0
  }
};
