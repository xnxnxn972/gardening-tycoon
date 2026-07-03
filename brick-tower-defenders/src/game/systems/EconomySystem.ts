import { MAX_LIVES, STARTING_GOLD, STARTING_LIVES } from '../utils/constants';

export class EconomySystem {
  gold = STARTING_GOLD;
  lives = STARTING_LIVES;

  canAfford(cost: number): boolean {
    return this.gold >= cost;
  }

  /** Returns true and deducts if affordable. */
  spend(cost: number): boolean {
    if (!this.canAfford(cost)) return false;
    this.gold -= cost;
    return true;
  }

  earn(amount: number): void {
    this.gold += amount;
  }

  loseLives(amount: number): void {
    this.lives = Math.max(0, this.lives - amount);
  }

  addLives(amount: number): void {
    this.lives = Math.min(MAX_LIVES, this.lives + amount);
  }
}
