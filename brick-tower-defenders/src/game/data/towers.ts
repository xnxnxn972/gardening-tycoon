export type TowerFamily = 'shooter' | 'squad' | 'power' | 'smash';
export type DamageType = 'physical' | 'magic';
export type ProjectileKind = 'arrow' | 'bolt' | 'rock';

export interface SquadConfig {
  spawnCount: number;
  knightHp: number;
  knightDamage: number;
  knightAttackRate: number; // seconds between swings
  respawnTime: number; // seconds until a dead knight returns
  canBlockFlying: boolean;
}

export interface TowerDef {
  family: TowerFamily;
  label: string; // UI family label (SHOOTER / SQUAD / POWER / SMASH)
  name: string; // themed name shown in the info panel
  description: string;
  cost: number;
  range: number;
  damage: number;
  fireRate: number; // seconds between shots (0 = does not shoot)
  canHitFlying: boolean;
  damageType: DamageType;
  projectile?: ProjectileKind;
  projectileSpeed?: number;
  splashRadius?: number;
  slowPercent?: number;
  slowDuration?: number;
  squad?: SquadConfig;
  texture: string; // sprite key — swap for real art later
  uiColor: number; // accent color used across the UI
}

export const TOWERS: Record<TowerFamily, TowerDef> = {
  shooter: {
    family: 'shooter',
    label: 'SHOOTER',
    name: 'Crossbow Tower',
    description: 'Fast single-target arrows. Hits flying.',
    cost: 120,
    range: 180,
    damage: 12,
    fireRate: 0.7,
    canHitFlying: true,
    damageType: 'physical',
    projectile: 'arrow',
    projectileSpeed: 620,
    texture: 'tower_shooter',
    uiColor: 0x3d7bd9
  },
  squad: {
    family: 'squad',
    label: 'SQUAD',
    name: 'Knight Barracks',
    description: 'Spawns knights that block ground enemies.',
    cost: 160,
    range: 120,
    damage: 0,
    fireRate: 0,
    canHitFlying: false,
    damageType: 'physical',
    squad: {
      spawnCount: 2,
      knightHp: 80,
      knightDamage: 6,
      knightAttackRate: 1.0,
      respawnTime: 6,
      canBlockFlying: false
    },
    texture: 'tower_squad',
    uiColor: 0x3d9948
  },
  power: {
    family: 'power',
    label: 'POWER',
    name: 'Wizard Tower',
    description: 'Magic bolts ignore armor and slow enemies.',
    cost: 180,
    range: 170,
    damage: 28,
    fireRate: 1.4,
    canHitFlying: true,
    damageType: 'magic',
    projectile: 'bolt',
    projectileSpeed: 480,
    slowPercent: 0.25,
    slowDuration: 1.5,
    texture: 'tower_power',
    uiColor: 0x8a4dc8
  },
  smash: {
    family: 'smash',
    label: 'SMASH',
    name: 'Catapult Tower',
    description: 'Slow splash damage. Ground only.',
    cost: 220,
    range: 210,
    damage: 35,
    fireRate: 2.2,
    canHitFlying: false,
    damageType: 'physical',
    projectile: 'rock',
    projectileSpeed: 380,
    splashRadius: 70,
    texture: 'tower_smash',
    uiColor: 0xc0473e
  }
};

export const TOWER_FAMILIES: TowerFamily[] = ['shooter', 'squad', 'power', 'smash'];
