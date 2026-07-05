import Phaser from 'phaser';
import type { EnemyDef } from '../data/enemies';
import type { DamageType } from '../data/towers';
import type { PathSystem } from '../systems/PathSystem';
import { computeDamage } from '../systems/CombatSystem';
import { DEPTH, ENEMY_MELEE_RATE } from '../utils/constants';
import type { SquadUnit } from './SquadUnit';

const FLY_HEIGHT = 26;

export class Enemy extends Phaser.GameObjects.Container {
  readonly def: EnemyDef;
  hp: number;
  readonly maxHp: number;

  /** Distance travelled along the path — towers target the highest value in range. */
  pathProgress = 0;
  private waypointIndex = 1;
  private readonly path: PathSystem;

  slowPercent = 0;
  private slowTimer = 0;

  /** Set by a SquadUnit when it engages this enemy. */
  blockedBy: SquadUnit | null = null;
  private attackTimer = 0;

  dead = false;
  reachedEnd = false;

  private readonly sprite: Phaser.GameObjects.Image;
  private readonly hpBar: Phaser.GameObjects.Graphics;
  private flashTimer = 0;

  // Walk/fly animation. frame2 is an optional second art frame named
  // `<texture>_2` — if it was loaded, the sprite alternates frames while
  // moving. The procedural waddle below works with or without it.
  private walkPhase = 0;
  private readonly frame2: string | null;
  private frameTimer = 0;
  private onFrame2 = false;

  constructor(scene: Phaser.Scene, def: EnemyDef, path: PathSystem) {
    super(scene, path.points[0].x, path.points[0].y);
    this.def = def;
    this.hp = def.hp;
    this.maxHp = def.hp;
    this.path = path;

    if (def.isFlying) {
      const shadow = scene.add.ellipse(0, 4, 22, 8, 0x000000, 0.3);
      this.add(shadow);
    }

    this.sprite = scene.add.image(0, def.isFlying ? -FLY_HEIGHT : 0, def.texture);
    this.add(this.sprite);
    this.frame2 = scene.textures.exists(def.texture + '_2') ? def.texture + '_2' : null;

    if (def.isFlying) {
      scene.tweens.add({
        targets: this.sprite,
        y: -FLY_HEIGHT - 8,
        duration: 420,
        yoyo: true,
        repeat: -1,
        ease: 'Sine.easeInOut'
      });
    }

    this.hpBar = scene.add.graphics();
    this.add(this.hpBar);
    this.drawHpBar();

    scene.add.existing(this);
  }

  private drawHpBar(): void {
    const w = this.def.hpBarWidth;
    const yOff = (this.def.isFlying ? -FLY_HEIGHT : 0) - this.sprite.height / 2 - 10;
    this.hpBar.clear();
    this.hpBar.fillStyle(0x14161c, 0.9);
    this.hpBar.fillRect(-w / 2 - 1, yOff - 1, w + 2, 6);
    const frac = Math.max(0, this.hp / this.maxHp);
    this.hpBar.fillStyle(frac > 0.4 ? 0xd93b3b : 0xe07a1f, 1);
    this.hpBar.fillRect(-w / 2, yOff, w * frac, 4);
  }

  get isSlowed(): boolean {
    return this.slowTimer > 0;
  }

  applySlow(percent: number, duration: number): void {
    this.slowPercent = Math.max(this.slowPercent, percent);
    this.slowTimer = Math.max(this.slowTimer, duration);
    this.sprite.setTint(0x7db8ff);
  }

  takeDamage(amount: number, type: DamageType): void {
    if (this.dead || this.reachedEnd) return;
    this.hp -= computeDamage(amount, type, this.def.armor);
    this.flashTimer = 0.07;
    this.sprite.setTintFill(0xffffff);
    if (this.hp <= 0) {
      this.dead = true;
    }
    this.drawHpBar();
  }

  update(dt: number): void {
    if (this.dead || this.reachedEnd) return;

    if (this.flashTimer > 0) {
      this.flashTimer -= dt;
      if (this.flashTimer <= 0) {
        this.sprite.clearTint();
        if (this.isSlowed) this.sprite.setTint(0x7db8ff);
      }
    }

    if (this.slowTimer > 0) {
      this.slowTimer -= dt;
      if (this.slowTimer <= 0) {
        this.slowPercent = 0;
        if (this.flashTimer <= 0) this.sprite.clearTint();
      }
    }

    // Blocked by a knight: stand and fight instead of moving.
    if (this.blockedBy) {
      if (!this.blockedBy.alive) {
        this.blockedBy = null;
      } else {
        this.attackTimer += dt;
        if (this.attackTimer >= ENEMY_MELEE_RATE) {
          this.attackTimer = 0;
          this.blockedBy.takeDamage(this.def.meleeDamage);
        }
        // stand still while fighting
        this.sprite.rotation = 0;
        if (!this.def.isFlying) this.sprite.y = 0;
        return;
      }
    }

    // Waypoint movement.
    const xBefore = this.x;
    let step = this.def.speed * (1 - this.slowPercent) * dt;
    while (step > 0 && this.waypointIndex < this.path.points.length) {
      const target = this.path.points[this.waypointIndex];
      const dx = target.x - this.x;
      const dy = target.y - this.y;
      const d = Math.sqrt(dx * dx + dy * dy);
      if (d <= step) {
        this.x = target.x;
        this.y = target.y;
        this.pathProgress += d;
        step -= d;
        this.waypointIndex++;
      } else {
        this.x += (dx / d) * step;
        this.y += (dy / d) * step;
        this.pathProgress += step;
        step = 0;
      }
    }
    if (this.waypointIndex >= this.path.points.length) {
      this.reachedEnd = true;
    }

    // Face the walking direction (enemy art faces left natively). On vertical
    // stretches the horizontal delta is ~0 and the last facing is kept.
    const dx = this.x - xBefore;
    if (Math.abs(dx) > 0.01) {
      this.sprite.setFlipX(dx > 0);
    }

    this.animateMovement(dt);

    this.setDepth(DEPTH.entity + this.y * 0.001);
  }

  /** Toy-like walk cycle: a small hop + rocking, plus optional 2-frame art. */
  private animateMovement(dt: number): void {
    const moveSpeed = this.def.speed * (1 - this.slowPercent);

    if (!this.def.isFlying) {
      // waddle in time with actual speed, so slowed enemies visibly trudge
      this.walkPhase += dt * moveSpeed * 0.15;
      this.sprite.rotation = Math.sin(this.walkPhase) * 0.08;
      this.sprite.y = -Math.abs(Math.sin(this.walkPhase)) * 3;
    }

    if (this.frame2) {
      // bats flap fast and constantly; walkers step with their speed
      const interval = this.def.isFlying ? 0.12 : 0.18 * (this.def.speed / Math.max(moveSpeed, 1));
      this.frameTimer += dt;
      if (this.frameTimer >= interval) {
        this.frameTimer = 0;
        this.onFrame2 = !this.onFrame2;
        this.sprite.setTexture(this.onFrame2 ? this.frame2! : this.def.texture);
      }
    }
  }
}
