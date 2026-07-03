import Phaser from 'phaser';
import type { TowerDef } from '../data/towers';
import {
  DEPTH,
  UPGRADE_COST_FACTOR,
  UPGRADE_DAMAGE_MULT,
  UPGRADE_RANGE_MULT,
  UPGRADE_SPEED_MULT
} from '../utils/constants';
import { dist } from '../utils/math';
import type { Enemy } from './Enemy';
import { SquadUnit } from './SquadUnit';

export class Tower extends Phaser.GameObjects.Container {
  readonly def: TowerDef;
  readonly slotIndex: number;
  level = 1;
  /** Total gold spent on this tower (build + upgrades) — used for the sell refund. */
  invested: number;

  damage: number;
  range: number;
  fireRate: number;
  private cooldown = 0;

  // Squad-specific
  knights: SquadUnit[] = [];
  private knightHp = 0;
  private knightDamage = 0;

  private readonly sprite: Phaser.GameObjects.Image;
  private levelBadge: Phaser.GameObjects.Text | null = null;

  constructor(scene: Phaser.Scene, x: number, y: number, def: TowerDef, slotIndex: number) {
    super(scene, x, y);
    this.def = def;
    this.slotIndex = slotIndex;
    this.invested = def.cost;
    this.damage = def.damage;
    this.range = def.range;
    this.fireRate = def.fireRate;
    if (def.squad) {
      this.knightHp = def.squad.knightHp;
      this.knightDamage = def.squad.knightDamage;
    }

    this.sprite = scene.add.image(0, 0, def.texture);
    this.sprite.setInteractive({ useHandCursor: true });
    this.add(this.sprite);

    this.setDepth(DEPTH.entity + y * 0.001);
    scene.add.existing(this);
  }

  /** The clickable part, so BattleScene can hook pointer events. */
  get hitSprite(): Phaser.GameObjects.Image {
    return this.sprite;
  }

  get upgradeCost(): number {
    return Math.round(this.def.cost * UPGRADE_COST_FACTOR);
  }

  get canUpgrade(): boolean {
    return this.level < 2;
  }

  upgrade(): void {
    if (!this.canUpgrade) return;
    this.level = 2;
    this.invested += this.upgradeCost;
    if (this.def.squad) {
      this.knightHp = Math.round(this.def.squad.knightHp * UPGRADE_DAMAGE_MULT);
      this.knightDamage = Math.round(this.def.squad.knightDamage * UPGRADE_DAMAGE_MULT);
      for (const k of this.knights) {
        k.setStats(this.currentKnightStats());
      }
    } else {
      this.damage = Math.round(this.damage * UPGRADE_DAMAGE_MULT);
      this.range = Math.round(this.range * UPGRADE_RANGE_MULT);
      this.fireRate = this.fireRate / UPGRADE_SPEED_MULT;
    }
    this.levelBadge = this.scene.add.text(14, -26, '★', {
      fontSize: '20px',
      color: '#ffd23f'
    });
    this.levelBadge.setOrigin(0.5);
    this.add(this.levelBadge);
  }

  currentKnightStats() {
    const squad = this.def.squad!;
    return {
      hp: this.knightHp,
      damage: this.knightDamage,
      attackRate: squad.knightAttackRate,
      respawnTime: squad.respawnTime
    };
  }

  reviveKnights(): void {
    for (const k of this.knights) {
      if (!k.alive) k.reviveNow();
    }
  }

  /**
   * Shooting towers pick the in-range enemy that is furthest along the path.
   * Returns the enemy to fire at this frame, or null.
   */
  update(dt: number, enemies: Enemy[]): Enemy | null {
    if (this.def.squad) return null; // barracks don't shoot; knights update separately

    this.cooldown -= dt;
    if (this.cooldown > 0) return null;

    let target: Enemy | null = null;
    for (const enemy of enemies) {
      if (enemy.dead || enemy.reachedEnd) continue;
      if (enemy.def.isFlying && !this.def.canHitFlying) continue;
      if (dist(this.x, this.y, enemy.x, enemy.y) > this.range) continue;
      if (!target || enemy.pathProgress > target.pathProgress) target = enemy;
    }

    if (target) {
      this.cooldown = this.fireRate;
      // Little recoil squish so firing reads visually even with placeholder art.
      this.scene.tweens.add({
        targets: this.sprite,
        scaleX: 1.08,
        scaleY: 0.92,
        duration: 70,
        yoyo: true
      });
    }
    return target;
  }

  destroyTower(): void {
    for (const k of this.knights) {
      if (k.engaged) k.engaged.blockedBy = null;
      k.destroy();
    }
    this.knights = [];
    this.destroy();
  }
}
