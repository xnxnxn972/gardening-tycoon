import Phaser from 'phaser';
import type { LevelData } from '../data/levelCastle';
import { PathSystem } from '../systems/PathSystem';
import { GAME_HEIGHT, GAME_WIDTH } from '../utils/constants';
import { dist } from '../utils/math';

type G = Phaser.GameObjects.Graphics;

/**
 * Every sprite in the game is generated here as a placeholder texture with a
 * stable key. To ship real art later, load PNGs under the SAME keys in
 * PreloadScene (this.load.image('enemy_goblin', ...)) and skip the matching
 * generator — nothing else in the codebase needs to change.
 *
 * Keys: bg_castle, slot_pad, core, tower_shooter, tower_squad, tower_power,
 * tower_smash, knight, enemy_goblin, enemy_skeleton, enemy_shieldknight,
 * enemy_bat, enemy_ogre, proj_arrow, proj_bolt, proj_rock, fx_glow,
 * icon_coin, icon_heart, icon_skull, icon_fireball, icon_freeze, icon_heal.
 */
export function makePlaceholderTextures(scene: Phaser.Scene): void {
  const g = scene.make.graphics({}, false);

  makeSlotPad(g);
  makeCore(g);
  makeTowers(g);
  makeKnight(g);
  makeEnemies(g);
  makeProjectiles(g);
  makeFx(g);
  makeIcons(g);

  g.destroy();
}

function gen(g: G, key: string, w: number, h: number): void {
  // Real art loaded in PreloadScene under the same key takes priority.
  if (!g.scene.textures.exists(key)) {
    g.generateTexture(key, w, h);
  }
  g.clear();
}

/** Little round toy-brick studs — used everywhere for the brick look. */
function stud(g: G, x: number, y: number, r: number, color: number, alpha = 1): void {
  g.fillStyle(color, alpha);
  g.fillCircle(x, y, r);
}

function makeSlotPad(g: G): void {
  g.fillStyle(0x2a2a30, 0.35);
  g.fillCircle(42, 46, 38);
  g.fillStyle(0x74747e, 1);
  g.fillCircle(42, 42, 37);
  g.lineStyle(3, 0x54545e, 1);
  g.strokeCircle(42, 42, 37);
  g.fillStyle(0x86868f, 1);
  g.fillCircle(42, 42, 29);
  for (const [dx, dy] of [
    [-11, -11],
    [11, -11],
    [-11, 11],
    [11, 11]
  ]) {
    stud(g, 42 + dx, 42 + dy, 4.5, 0x97979f);
  }
  gen(g, 'slot_pad', 84, 84);
}

function makeCore(g: G): void {
  // soft glow
  g.fillStyle(0xffd23f, 0.1);
  g.fillCircle(65, 62, 62);
  g.fillStyle(0xffd23f, 0.12);
  g.fillCircle(65, 62, 48);
  // golden stepped ziggurat
  const steps: [number, number, number, number][] = [
    [15, 88, 100, 26],
    [29, 60, 72, 26],
    [43, 32, 44, 26],
    [53, 12, 24, 18]
  ];
  for (const [x, y, w, h] of steps) {
    g.fillStyle(0xffc93a, 1);
    g.fillRoundedRect(x, y, w, h, 4);
    g.lineStyle(3, 0xd99a1a, 1);
    g.strokeRoundedRect(x, y, w, h, 4);
    const studCount = Math.floor(w / 22);
    for (let i = 0; i < studCount; i++) {
      stud(g, x + 12 + i * 22, y + 8, 4, 0xffe27a);
    }
  }
  gen(g, 'core', 130, 122);
}

function towerBase(g: G): void {
  // shared stone base with studs
  g.fillStyle(0x2a2a30, 0.35);
  g.fillEllipse(34, 78, 54, 14);
  g.fillStyle(0x6e6e78, 1);
  g.fillRoundedRect(7, 52, 54, 28, 6);
  g.lineStyle(3, 0x53535c, 1);
  g.strokeRoundedRect(7, 52, 54, 28, 6);
  stud(g, 20, 60, 4, 0x82828c);
  stud(g, 48, 60, 4, 0x82828c);
}

function towerBody(g: G, color: number, dark: number): void {
  g.fillStyle(color, 1);
  g.fillRoundedRect(14, 26, 40, 32, 4);
  g.lineStyle(3, dark, 1);
  g.strokeRoundedRect(14, 26, 40, 32, 4);
}

function makeTowers(g: G): void {
  // SHOOTER — Crossbow Tower (blue)
  towerBase(g);
  towerBody(g, 0x3d7bd9, 0x2b58a3);
  g.fillStyle(0x2b58a3, 1); // crenellations
  g.fillRect(14, 20, 10, 8);
  g.fillRect(29, 20, 10, 8);
  g.fillRect(44, 20, 10, 8);
  g.fillStyle(0x8a5a2b, 1); // crossbow
  g.fillRect(16, 8, 36, 6);
  g.fillRect(31, 2, 6, 20);
  g.lineStyle(2, 0xdcd6c4, 1);
  g.lineBetween(16, 8, 34, 16);
  g.lineBetween(52, 8, 34, 16);
  gen(g, 'tower_shooter', 68, 86);

  // SQUAD — Knight Barracks (green)
  towerBase(g);
  towerBody(g, 0x3d9948, 0x2a7033);
  g.fillStyle(0x26562c, 1); // door
  g.fillRoundedRect(27, 38, 14, 20, { tl: 7, tr: 7, bl: 0, br: 0 });
  g.fillStyle(0x9b9ba5, 1); // flag pole
  g.fillRect(32, 2, 4, 26);
  g.fillStyle(0x5fd66e, 1); // flag
  g.fillTriangle(36, 3, 58, 9, 36, 16);
  gen(g, 'tower_squad', 68, 86);

  // POWER — Wizard Tower (purple)
  towerBase(g);
  towerBody(g, 0x8a4dc8, 0x67399a);
  g.fillStyle(0x67399a, 1); // cone roof
  g.fillTriangle(12, 28, 56, 28, 34, 0);
  g.lineStyle(3, 0x4d2a74, 1);
  g.strokeTriangle(12, 28, 56, 28, 34, 0);
  stud(g, 34, 4, 4.5, 0xffd23f); // glowing tip
  stud(g, 34, 44, 5, 0xd9b8ff); // window orb
  gen(g, 'tower_power', 68, 86);

  // SMASH — Catapult Tower (red)
  towerBase(g);
  towerBody(g, 0xc0473e, 0x8f322c);
  g.lineStyle(7, 0x8a5a2b, 1); // throwing arm
  g.lineBetween(20, 26, 50, 4);
  g.fillStyle(0x6a6a72, 1); // basket with rock
  g.fillCircle(50, 6, 7);
  g.fillStyle(0x8d8d96, 1);
  g.fillCircle(50, 5, 4.5);
  stud(g, 24, 34, 4, 0xd97a72);
  stud(g, 44, 34, 4, 0xd97a72);
  gen(g, 'tower_smash', 68, 86);
}

function makeKnight(g: G): void {
  g.fillStyle(0xc22a2a, 1); // plume
  g.fillRect(11, 0, 6, 7);
  g.fillStyle(0xc7cede, 1); // helmet
  g.fillCircle(14, 13, 9);
  g.lineStyle(2, 0x8b93a3, 1);
  g.strokeCircle(14, 13, 9);
  g.fillStyle(0x2c3140, 1); // visor
  g.fillRect(8, 11, 12, 3);
  g.fillStyle(0x3d7bd9, 1); // tunic
  g.fillRoundedRect(6, 21, 16, 10, 3);
  g.fillStyle(0xdde3ea, 1); // shield
  g.fillRoundedRect(0, 16, 8, 12, 3);
  g.lineStyle(2, 0x9aa2b1, 1);
  g.strokeRoundedRect(0, 16, 8, 12, 3);
  gen(g, 'knight', 28, 32);
}

function makeEnemies(g: G): void {
  // Goblin — small, green, fast
  g.fillStyle(0x3f8f2f, 1); // ears
  g.fillTriangle(1, 8, 10, 12, 6, 18);
  g.fillTriangle(31, 8, 22, 12, 26, 18);
  g.fillStyle(0x63c04f, 1);
  g.fillCircle(16, 17, 11);
  g.lineStyle(2, 0x3f8f2f, 1);
  g.strokeCircle(16, 17, 11);
  g.fillStyle(0xffffff, 1);
  g.fillCircle(12, 15, 3);
  g.fillCircle(20, 15, 3);
  g.fillStyle(0x14161c, 1);
  g.fillCircle(12, 15, 1.5);
  g.fillCircle(20, 15, 1.5);
  gen(g, 'enemy_goblin', 32, 32);

  // Skeleton — bone white
  g.fillStyle(0xe9e9e1, 1);
  g.fillCircle(16, 14, 11);
  g.lineStyle(2, 0xb0b0a6, 1);
  g.strokeCircle(16, 14, 11);
  g.fillStyle(0x14161c, 1);
  g.fillCircle(12, 12, 3);
  g.fillCircle(20, 12, 3);
  g.fillTriangle(16, 16, 14, 20, 18, 20);
  g.fillStyle(0xe9e9e1, 1); // jaw
  g.fillRect(10, 25, 12, 6);
  g.lineStyle(1, 0xb0b0a6, 1);
  g.lineBetween(13, 25, 13, 31);
  g.lineBetween(16, 25, 16, 31);
  g.lineBetween(19, 25, 19, 31);
  gen(g, 'enemy_skeleton', 32, 34);

  // Shield Knight — armored, carries a shield
  g.fillStyle(0xc22a2a, 1); // plume
  g.fillRect(13, 0, 7, 7);
  g.fillStyle(0x5b5f6b, 1); // helmet
  g.fillCircle(17, 17, 12);
  g.lineStyle(2, 0x41444d, 1);
  g.strokeCircle(17, 17, 12);
  g.fillStyle(0x14161c, 1); // visor slit
  g.fillRect(9, 15, 16, 4);
  g.fillStyle(0x3d7bd9, 1); // shield
  g.fillRoundedRect(24, 12, 13, 20, 4);
  g.lineStyle(2, 0xdde3ea, 1);
  g.strokeRoundedRect(24, 12, 13, 20, 4);
  stud(g, 30.5, 22, 3, 0xffd23f);
  gen(g, 'enemy_shieldknight', 38, 38);

  // Bat — small dark flyer
  g.fillStyle(0x4a3a5e, 1); // wings
  g.fillTriangle(0, 4, 13, 10, 7, 20);
  g.fillTriangle(36, 4, 23, 10, 29, 20);
  g.fillStyle(0x352b45, 1); // body
  g.fillCircle(18, 12, 8);
  g.fillTriangle(12, 6, 15, 1, 17, 6); // ears
  g.fillTriangle(19, 6, 21, 1, 24, 6);
  g.fillStyle(0xe04040, 1); // eyes
  g.fillCircle(15, 11, 2);
  g.fillCircle(21, 11, 2);
  g.fillStyle(0xffffff, 1); // fangs
  g.fillTriangle(15, 17, 17, 17, 16, 20);
  g.fillTriangle(19, 17, 21, 17, 20, 20);
  gen(g, 'enemy_bat', 36, 26);

  // Ogre — big mini-boss
  g.fillStyle(0x6a6a72, 1); // horns
  g.fillTriangle(10, 14, 22, 8, 16, 22);
  g.fillTriangle(54, 14, 42, 8, 48, 22);
  g.fillStyle(0x9c4034, 1); // body
  g.fillCircle(32, 34, 26);
  g.lineStyle(3, 0x6d2c24, 1);
  g.strokeCircle(32, 34, 26);
  g.fillStyle(0xb85a48, 1); // belly
  g.fillCircle(32, 44, 13);
  g.fillStyle(0xffd23f, 1); // angry eyes
  g.fillCircle(24, 26, 4.5);
  g.fillCircle(40, 26, 4.5);
  g.fillStyle(0x14161c, 1);
  g.fillCircle(24, 27, 2);
  g.fillCircle(40, 27, 2);
  g.lineStyle(3, 0x6d2c24, 1); // brow
  g.lineBetween(18, 20, 29, 24);
  g.lineBetween(46, 20, 35, 24);
  g.fillStyle(0xffffff, 1); // tusks
  g.fillTriangle(22, 40, 27, 40, 24, 33);
  g.fillTriangle(37, 40, 42, 40, 40, 33);
  gen(g, 'enemy_ogre', 64, 64);
}

function makeProjectiles(g: G): void {
  g.fillStyle(0x8a5a2b, 1);
  g.fillRect(0, 2, 14, 3);
  g.fillStyle(0xdde3ea, 1);
  g.fillTriangle(14, 0, 20, 3.5, 14, 7);
  gen(g, 'proj_arrow', 20, 7);

  g.fillStyle(0x8a4dc8, 0.45);
  g.fillCircle(8, 8, 8);
  g.fillStyle(0xb07de8, 1);
  g.fillCircle(8, 8, 5);
  g.fillStyle(0xffffff, 1);
  g.fillCircle(8, 8, 2.5);
  gen(g, 'proj_bolt', 16, 16);

  g.fillStyle(0x8d8d96, 1);
  g.fillCircle(8, 8, 7.5);
  g.lineStyle(2, 0x6a6a72, 1);
  g.strokeCircle(8, 8, 7.5);
  g.lineBetween(4, 6, 9, 9);
  g.lineBetween(9, 9, 12, 5);
  gen(g, 'proj_rock', 16, 16);
}

function makeFx(g: G): void {
  // soft radial glow, tinted at runtime for explosions / hits
  for (let i = 0; i < 6; i++) {
    g.fillStyle(0xffffff, 0.13);
    g.fillCircle(32, 32, 30 - i * 5);
  }
  gen(g, 'fx_glow', 64, 64);
}

function makeIcons(g: G): void {
  // coin
  g.fillStyle(0xd99a1a, 1);
  g.fillCircle(14, 14, 12);
  g.fillStyle(0xffc93a, 1);
  g.fillCircle(14, 13, 10.5);
  g.fillStyle(0xffe27a, 1);
  g.fillCircle(14, 13, 5);
  gen(g, 'icon_coin', 28, 28);

  // heart
  g.fillStyle(0xd93b3b, 1);
  g.fillCircle(9, 10, 6.5);
  g.fillCircle(19, 10, 6.5);
  g.fillTriangle(3.2, 13, 24.8, 13, 14, 26);
  gen(g, 'icon_heart', 28, 28);

  // skull
  g.fillStyle(0xe9e9e1, 1);
  g.fillCircle(14, 12, 9);
  g.fillRect(10, 17, 8, 7);
  g.fillStyle(0x14161c, 1);
  g.fillCircle(10.5, 11, 2.5);
  g.fillCircle(17.5, 11, 2.5);
  gen(g, 'icon_skull', 28, 28);

  // fireball
  g.fillStyle(0xc0473e, 1);
  g.fillTriangle(2, 24, 14, 4, 18, 22);
  g.fillStyle(0xe07a1f, 1);
  g.fillCircle(16, 15, 9);
  g.fillStyle(0xffc93a, 1);
  g.fillCircle(17, 16, 5);
  gen(g, 'icon_fireball', 28, 28);

  // snowflake
  g.lineStyle(3, 0x9fd4ff, 1);
  for (let i = 0; i < 3; i++) {
    const a = (i * Math.PI) / 3;
    g.lineBetween(14 - Math.cos(a) * 11, 14 - Math.sin(a) * 11, 14 + Math.cos(a) * 11, 14 + Math.sin(a) * 11);
  }
  g.fillStyle(0xdff0ff, 1);
  g.fillCircle(14, 14, 3);
  gen(g, 'icon_freeze', 28, 28);

  // repair cross
  g.fillStyle(0x3d9948, 1);
  g.fillRoundedRect(10, 3, 8, 22, 3);
  g.fillRoundedRect(3, 10, 22, 8, 3);
  gen(g, 'icon_heal', 28, 28);
}

// ---------------------------------------------------------------------------
// Themed background — one big texture per level so runtime rendering is a
// single image draw. Other themes = another generator writing another key.
// ---------------------------------------------------------------------------

export function makeCastleBackground(scene: Phaser.Scene, level: LevelData): void {
  if (scene.textures.exists(level.theme.bgTexture)) return;

  const g = scene.make.graphics({}, false);
  const path = new PathSystem(level.path);
  const W = GAME_WIDTH;
  const H = GAME_HEIGHT;

  // stone floor
  g.fillStyle(0x46464e, 1);
  g.fillRect(0, 0, W, H);
  g.lineStyle(2, 0x3c3c44, 0.7);
  for (let y = 84; y < H; y += 44) {
    g.lineBetween(0, y, W, y);
  }
  let row = 0;
  for (let y = 84; y < H; y += 44) {
    const offset = (row % 2) * 44;
    for (let x = offset; x < W; x += 88) {
      g.lineBetween(x, y, x, Math.min(y + 44, H));
    }
    row++;
  }

  // top castle wall with crenellations
  g.fillStyle(0x35353d, 1);
  g.fillRect(0, 0, W, 84);
  g.lineStyle(2, 0x2b2b32, 0.8);
  for (let y = 20; y < 84; y += 20) g.lineBetween(0, y, W, y);
  for (let x = 20; x < W; x += 46) {
    g.fillStyle(0x35353d, 1);
    g.fillRect(x, 84, 26, 14);
    g.lineStyle(2, 0x2b2b32, 1);
    g.strokeRect(x, 84, 26, 14);
  }

  // banners on the wall
  const bannerXs = [230, 540, 990, 1330];
  bannerXs.forEach((x, i) => {
    const color = i % 2 === 0 ? 0x2d5fb0 : 0xb03030;
    g.fillStyle(color, 1);
    g.fillRect(x, 8, 42, 62);
    g.fillStyle(0x35353d, 1); // notch
    g.fillTriangle(x, 70, x + 42, 70, x + 21, 54);
    g.fillStyle(0xffc93a, 1);
    g.fillCircle(x + 21, 32, 8);
  });

  // torches
  for (const x of [380, 700, 1150, 1480]) {
    g.fillStyle(0x6b4a26, 1);
    g.fillRect(x - 3, 42, 6, 26);
    g.fillStyle(0xe07a1f, 0.35);
    g.fillCircle(x, 34, 16);
    g.fillStyle(0xe07a1f, 1);
    g.fillCircle(x, 34, 8);
    g.fillStyle(0xffc93a, 1);
    g.fillCircle(x, 36, 4);
  }

  // decorations with rejection sampling so they never overlap path/slots/core
  const clearOf = (x: number, y: number, margin: number): boolean => {
    if (y < 120) return false;
    const cp = path.closestPoint(x, y);
    if (dist(x, y, cp.x, cp.y) < margin + 34) return false;
    for (const s of level.buildSlots) {
      if (dist(x, y, s.x, s.y) < margin + 40) return false;
    }
    if (dist(x, y, level.core.x, level.core.y) < margin + 90) return false;
    return true;
  };
  const place = (margin: number): { x: number; y: number } | null => {
    for (let tries = 0; tries < 40; tries++) {
      const x = 40 + Math.random() * (W - 80);
      const y = 130 + Math.random() * (H - 170);
      if (clearOf(x, y, margin)) return { x, y };
    }
    return null;
  };

  // grass patches
  const greens = [0x3f7a35, 0x467f3a, 0x386d30];
  for (let i = 0; i < 26; i++) {
    const p = place(30);
    if (!p) continue;
    const w = 40 + Math.random() * 50;
    const h = 28 + Math.random() * 30;
    g.fillStyle(greens[i % greens.length], 1);
    g.fillRoundedRect(p.x - w / 2, p.y - h / 2, w, h, 10);
    for (let s = 0; s < 3; s++) {
      g.fillStyle(0x5a9b4d, 0.8);
      g.fillCircle(p.x - w / 4 + (s * w) / 4, p.y, 4);
    }
  }

  // toy trees (top-down: stacked circles with studs)
  for (let i = 0; i < 10; i++) {
    const p = place(30);
    if (!p) continue;
    const r = 17 + Math.random() * 8;
    g.fillStyle(0x2a2a30, 0.3);
    g.fillCircle(p.x + 3, p.y + 4, r);
    g.fillStyle(0x2f6b2a, 1);
    g.fillCircle(p.x, p.y, r);
    g.fillStyle(0x3f8f2f, 1);
    g.fillCircle(p.x - r * 0.15, p.y - r * 0.15, r * 0.65);
    g.fillStyle(0x5cae4a, 1);
    g.fillCircle(p.x - r * 0.25, p.y - r * 0.25, r * 0.25);
  }

  // scattered colored toy bricks
  const brickColors = [0xc0473e, 0x3d7bd9, 0x3d9948, 0xd9862d];
  for (let i = 0; i < 14; i++) {
    const p = place(20);
    if (!p) continue;
    const color = brickColors[i % brickColors.length];
    g.fillStyle(color, 1);
    g.fillRoundedRect(p.x - 12, p.y - 8, 24, 16, 3);
    g.lineStyle(2, 0x2b2b32, 0.5);
    g.strokeRoundedRect(p.x - 12, p.y - 8, 24, 16, 3);
    g.fillStyle(0xffffff, 0.35);
    g.fillCircle(p.x - 5, p.y - 2, 3);
    g.fillCircle(p.x + 5, p.y - 2, 3);
  }

  // the path: thick border + fill + round joints, then studs along the middle
  const pts = level.path;
  g.lineStyle(72, level.theme.pathBorder, 1);
  for (let i = 0; i < pts.length - 1; i++) {
    g.lineBetween(pts[i].x, pts[i].y, pts[i + 1].x, pts[i + 1].y);
  }
  g.fillStyle(level.theme.pathBorder, 1);
  for (const p of pts) g.fillCircle(p.x, p.y, 36);
  g.lineStyle(60, level.theme.pathFill, 1);
  for (let i = 0; i < pts.length - 1; i++) {
    g.lineBetween(pts[i].x, pts[i].y, pts[i + 1].x, pts[i + 1].y);
  }
  g.fillStyle(level.theme.pathFill, 1);
  for (const p of pts) g.fillCircle(p.x, p.y, 30);

  // studs along the path centerline
  g.fillStyle(level.theme.pathStud, 0.9);
  for (let i = 0; i < pts.length - 1; i++) {
    const a = pts[i];
    const b = pts[i + 1];
    const segLen = dist(a.x, a.y, b.x, b.y);
    const steps = Math.floor(segLen / 42);
    for (let s = 1; s <= steps; s++) {
      const t = s / (steps + 1);
      g.fillCircle(a.x + (b.x - a.x) * t, a.y + (b.y - a.y) * t, 5);
    }
  }

  // entrance arch on the left where enemies come in
  const entryY = pts[0].y;
  g.fillStyle(0x55555e, 1);
  g.fillRoundedRect(-30, entryY - 86, 96, 172, { tl: 0, bl: 0, tr: 26, br: 26 });
  g.lineStyle(3, 0x3c3c44, 1);
  g.strokeRoundedRect(-30, entryY - 86, 96, 172, { tl: 0, bl: 0, tr: 26, br: 26 });
  g.fillStyle(0x1c1c22, 1);
  g.fillRoundedRect(-30, entryY - 54, 66, 108, { tl: 0, bl: 0, tr: 30, br: 30 });
  g.fillStyle(0xb03030, 1); // little banner over the gate
  g.fillRect(14, entryY - 84, 30, 34);
  g.fillStyle(0x55555e, 1);
  g.fillTriangle(14, entryY - 50, 44, entryY - 50, 29, entryY - 62);

  // red carpet leading to the core
  const last = pts[pts.length - 1];
  g.fillStyle(0xb03030, 0.85);
  g.fillRect(last.x - 130, last.y - 26, 120, 52);
  g.fillStyle(0xffc93a, 0.9);
  g.fillRect(last.x - 130, last.y - 26, 120, 4);
  g.fillRect(last.x - 130, last.y + 22, 120, 4);

  g.generateTexture(level.theme.bgTexture, W, H);
  g.destroy();
}
