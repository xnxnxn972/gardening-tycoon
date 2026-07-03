import type { DamageType } from '../data/towers';

/**
 * Armor rule: physical damage is reduced by armor (0..1), magic ignores it.
 */
export function computeDamage(base: number, type: DamageType, armor: number): number {
  return type === 'magic' ? base : base * (1 - armor);
}
