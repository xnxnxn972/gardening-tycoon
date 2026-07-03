import Phaser from 'phaser';
import { BLOCK_RADIUS, DEPTH } from '../utils/constants';
import { dist } from '../utils/math';
import type { Enemy } from './Enemy';

export interface KnightStats {
  hp: number;
  damage: number;
  attackRate: number;
  respawnTime: number;
}

/**
 * A knight spawned by the Knight Barracks. Stands at a fixed rally point on
 * the path, blocks one ground enemy at a time, and respawns after death.
 */
export class SquadUnit extends Phaser.GameObjects.Container {
  hp: number;
  maxHp: number;
  damage: number;
  attackRate: number;
  respawnTime: number;

  alive = true;
  engaged: Enemy | null = null;
  private respawnTimer = 0;
  private attackTimer = 0;

  private readonly sprite: Phaser.GameObjects.Image;
  private readonly hpBar: Phaser.GameObjects.Graphics;

  constructor(scene: Phaser.Scene, x: number, y: number, stats: KnightStats) {
    super(scene, x, y);
    this.hp = stats.hp;
    this.maxHp = stats.hp;
    this.damage = stats.damage;
    this.attackRate = stats.attackRate;
    this.respawnTime = stats.respawnTime;

    this.sprite = scene.add.image(0, 0, 'knight');
    this.add(this.sprite);
    this.hpBar = scene.add.graphics();
    this.add(this.hpBar);
    this.drawHpBar();

    this.setDepth(DEPTH.entity + y * 0.001);
    scene.add.existing(this);
  }

  /** Applied on barracks upgrade: stronger stats, full heal. */
  setStats(stats: KnightStats): void {
    this.maxHp = stats.hp;
    this.hp = stats.hp;
    this.damage = stats.damage;
    this.attackRate = stats.attackRate;
    this.respawnTime = stats.respawnTime;
    this.drawHpBar();
  }

  private drawHpBar(): void {
    const w = 28;
    const yOff = -this.sprite.height / 2 - 9;
    this.hpBar.clear();
    this.hpBar.fillStyle(0x14161c, 0.9);
    this.hpBar.fillRect(-w / 2 - 1, yOff - 1, w + 2, 5);
    const frac = Math.max(0, this.hp / this.maxHp);
    this.hpBar.fillStyle(0x3d9948, 1);
    this.hpBar.fillRect(-w / 2, yOff, w * frac, 3);
  }

  takeDamage(amount: number): void {
    if (!this.alive) return;
    this.hp -= amount;
    this.drawHpBar();
    if (this.hp <= 0) this.die();
  }

  private die(): void {
    this.alive = false;
    this.respawnTimer = this.respawnTime;
    if (this.engaged) {
      this.engaged.blockedBy = null;
      this.engaged = null;
    }
    this.setVisible(false);
  }

  reviveNow(): void {
    this.alive = true;
    this.hp = this.maxHp;
    this.attackTimer = 0;
    this.drawHpBar();
    this.setVisible(true);
  }

  update(dt: number, enemies: Enemy[]): void {
    if (!this.alive) {
      this.respawnTimer -= dt;
      if (this.respawnTimer <= 0) this.reviveNow();
      return;
    }

    if (this.engaged && (this.engaged.dead || this.engaged.reachedEnd)) {
      this.engaged = null;
    }

    if (this.engaged) {
      this.attackTimer += dt;
      if (this.attackTimer >= this.attackRate) {
        this.attackTimer = 0;
        this.engaged.takeDamage(this.damage, 'physical');
        if (this.engaged.dead) this.engaged = null;
      }
      return;
    }

    // Grab the first passing ground enemy that nobody else is blocking.
    for (const enemy of enemies) {
      if (enemy.def.isFlying || enemy.dead || enemy.reachedEnd || enemy.blockedBy) continue;
      if (dist(this.x, this.y, enemy.x, enemy.y) <= BLOCK_RADIUS) {
        this.engaged = enemy;
        enemy.blockedBy = this;
        break;
      }
    }
  }
}
