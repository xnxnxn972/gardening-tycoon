export type AbilityId = 'fireball' | 'freeze' | 'heal';

export interface AbilityDef {
  id: AbilityId;
  name: string;
  description: string;
  uses: number; // uses per battle
  icon: string; // texture key
  needsTarget: boolean; // true = click the map after selecting
}

export const ABILITIES: AbilityDef[] = [
  {
    id: 'fireball',
    name: 'Fireball',
    description: 'Click the map: big area damage.',
    uses: 3,
    icon: 'icon_fireball',
    needsTarget: true
  },
  {
    id: 'freeze',
    name: 'Freeze',
    description: 'Slows all enemies for 3 seconds.',
    uses: 2,
    icon: 'icon_freeze',
    needsTarget: false
  },
  {
    id: 'heal',
    name: 'Repair',
    description: '+3 lives and revives fallen knights.',
    uses: 2,
    icon: 'icon_heal',
    needsTarget: false
  }
];

export const FIREBALL_DAMAGE = 100;
export const FIREBALL_RADIUS = 150;
export const FREEZE_SLOW = 0.6;
export const FREEZE_DURATION = 3;
export const HEAL_LIVES = 3;
