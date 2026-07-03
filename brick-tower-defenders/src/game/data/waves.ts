export interface WaveEntry {
  enemy: string; // key into ENEMIES
  count: number;
  interval: number; // seconds between spawns within this group
  startDelay: number; // seconds after wave start before this group begins
}

export type Wave = WaveEntry[];

/**
 * 10 waves that ramp gradually. Groups with overlapping delays interleave.
 */
export const WAVES: Wave[] = [
  // 1
  [{ enemy: 'goblin', count: 10, interval: 0.9, startDelay: 0 }],
  // 2
  [
    { enemy: 'goblin', count: 14, interval: 0.8, startDelay: 0 },
    { enemy: 'skeleton', count: 4, interval: 1.4, startDelay: 3 }
  ],
  // 3
  [
    { enemy: 'skeleton', count: 12, interval: 1.1, startDelay: 0 },
    { enemy: 'goblin', count: 6, interval: 0.8, startDelay: 4 }
  ],
  // 4
  [
    { enemy: 'goblin', count: 10, interval: 0.8, startDelay: 0 },
    { enemy: 'bat', count: 6, interval: 1.2, startDelay: 3 }
  ],
  // 5
  [
    { enemy: 'shieldKnight', count: 8, interval: 1.5, startDelay: 0 },
    { enemy: 'skeleton', count: 8, interval: 1.1, startDelay: 4 }
  ],
  // 6
  [
    { enemy: 'goblin', count: 20, interval: 0.6, startDelay: 0 },
    { enemy: 'bat', count: 8, interval: 1.1, startDelay: 5 }
  ],
  // 7
  [
    { enemy: 'shieldKnight', count: 12, interval: 1.3, startDelay: 0 },
    { enemy: 'skeleton', count: 12, interval: 1.0, startDelay: 3 }
  ],
  // 8
  [
    { enemy: 'goblin', count: 20, interval: 0.55, startDelay: 0 },
    { enemy: 'bat', count: 10, interval: 1.0, startDelay: 4 },
    { enemy: 'shieldKnight', count: 8, interval: 1.4, startDelay: 8 }
  ],
  // 9
  [
    { enemy: 'skeleton', count: 15, interval: 0.9, startDelay: 0 },
    { enemy: 'shieldKnight', count: 15, interval: 1.2, startDelay: 5 }
  ],
  // 10 — ogre mini-boss with mixed support
  [
    { enemy: 'goblin', count: 10, interval: 0.7, startDelay: 0 },
    { enemy: 'skeleton', count: 10, interval: 1.0, startDelay: 4 },
    { enemy: 'ogre', count: 1, interval: 1, startDelay: 8 },
    { enemy: 'bat', count: 8, interval: 1.1, startDelay: 12 },
    { enemy: 'shieldKnight', count: 4, interval: 1.6, startDelay: 18 }
  ]
];
