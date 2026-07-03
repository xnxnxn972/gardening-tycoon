export interface EnemyDef {
  id: string;
  name: string;
  hp: number;
  speed: number; // px per second
  armor: number; // 0..1, reduces physical damage
  reward: number; // gold on kill
  livesDamage: number;
  isFlying: boolean;
  meleeDamage: number; // damage per swing against a blocking knight
  texture: string; // sprite key — swap for real art later
  hpBarWidth: number;
}

export const ENEMIES: Record<string, EnemyDef> = {
  goblin: {
    id: 'goblin',
    name: 'Goblin',
    hp: 45,
    speed: 70,
    armor: 0,
    reward: 8,
    livesDamage: 1,
    isFlying: false,
    meleeDamage: 5,
    texture: 'enemy_goblin',
    hpBarWidth: 32
  },
  skeleton: {
    id: 'skeleton',
    name: 'Skeleton',
    hp: 75,
    speed: 50,
    armor: 0,
    reward: 12,
    livesDamage: 1,
    isFlying: false,
    meleeDamage: 7,
    texture: 'enemy_skeleton',
    hpBarWidth: 34
  },
  shieldKnight: {
    id: 'shieldKnight',
    name: 'Shield Knight',
    hp: 110,
    speed: 40,
    armor: 0.5,
    reward: 18,
    livesDamage: 2,
    isFlying: false,
    meleeDamage: 9,
    texture: 'enemy_shieldknight',
    hpBarWidth: 36
  },
  bat: {
    id: 'bat',
    name: 'Bat',
    hp: 40,
    speed: 85,
    armor: 0,
    reward: 10,
    livesDamage: 1,
    isFlying: true,
    meleeDamage: 0,
    texture: 'enemy_bat',
    hpBarWidth: 30
  },
  ogre: {
    id: 'ogre',
    name: 'Ogre Mini-Boss',
    hp: 450,
    speed: 28,
    armor: 0.25,
    reward: 60,
    livesDamage: 5,
    isFlying: false,
    meleeDamage: 22,
    texture: 'enemy_ogre',
    hpBarWidth: 56
  }
};
