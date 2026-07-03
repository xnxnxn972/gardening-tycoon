import Phaser from 'phaser';
import type { DamageType, ProjectileKind } from '../data/towers';
import { DEPTH } from '../utils/constants';
import { dist, lerp } from '../utils/math';
import type { Enemy } from './Enemy';

export interface ProjectileOpts {
  kind: ProjectileKind;
  x: number;
  y: number;
  target: Enemy;
  damage: number;
  damageType: DamageType;
  speed: number;
  splashRadius?: number;
  slowPercent?: number;
  slowDuration?: number;
}

const HIT_DISTANCE = 12;

/**
 * Arrows and bolts home in on their target; rocks lob in an arc to the
 * target's position at launch and splash on impact.
 */
export class Projectile extends Phaser.GameObjects.Image {
  readonly opts: ProjectileOpts;
  done = false;

  // Arc (rock) state
  private readonly startX: number;
  private readonly startY: number;
  private targetX: number;
  private targetY: number;
  private t = 0;
  private readonly flightTime: number;
  private readonly arcHeight: number;

  constructor(scene: Phaser.Scene, opts: ProjectileOpts) {
    const texture = opts.kind === 'arrow' ? 'proj_arrow' : opts.kind === 'bolt' ? 'proj_bolt' : 'proj_rock';
    super(scene, opts.x, opts.y, texture);
    this.opts = opts;
    this.startX = opts.x;
    this.startY = opts.y;
    this.targetX = opts.target.x;
    this.targetY = opts.target.y;
    const d = dist(opts.x, opts.y, this.targetX, this.targetY);
    this.flightTime = Math.max(0.15, d / opts.speed);
    this.arcHeight = Math.min(120, d * 0.35);
    this.setDepth(DEPTH.projectile);
    scene.add.existing(this);
  }

  /** Returns the impact point when the projectile lands this frame, else null. */
  update(dt: number): { x: number; y: number } | null {
    if (this.done) return null;

    if (this.opts.kind === 'rock') {
      this.t += dt / this.flightTime;
      if (this.t >= 1) {
        this.done = true;
        return { x: this.targetX, y: this.targetY };
      }
      this.x = lerp(this.startX, this.targetX, this.t);
      this.y = lerp(this.startY, this.targetY, this.t) - Math.sin(Math.PI * this.t) * this.arcHeight;
      this.rotation += dt * 6;
      return null;
    }

    // Homing arrow/bolt. If the target dies mid-flight, fly to its last position.
    const target = this.opts.target;
    if (!target.dead && !target.reachedEnd) {
      this.targetX = target.x;
      this.targetY = target.y + (target.def.isFlying ? -26 : 0);
    }
    const dx = this.targetX - this.x;
    const dy = this.targetY - this.y;
    const d = Math.sqrt(dx * dx + dy * dy);
    const step = this.opts.speed * dt;
    this.rotation = Math.atan2(dy, dx);
    if (d <= Math.max(step, HIT_DISTANCE)) {
      this.done = true;
      return { x: this.targetX, y: this.targetY };
    }
    this.x += (dx / d) * step;
    this.y += (dy / d) * step;
    return null;
  }
}
