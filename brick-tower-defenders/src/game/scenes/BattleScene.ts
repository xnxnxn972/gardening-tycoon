import Phaser from 'phaser';
import {
  FIREBALL_DAMAGE,
  FIREBALL_RADIUS,
  FREEZE_DURATION,
  FREEZE_SLOW,
  HEAL_LIVES
} from '../data/abilities';
import { ENEMIES } from '../data/enemies';
import { LEVEL_CASTLE, type LevelData } from '../data/levelCastle';
import { TOWERS, type TowerFamily } from '../data/towers';
import { WAVES } from '../data/waves';
import { Enemy } from '../entities/Enemy';
import { Projectile } from '../entities/Projectile';
import { SquadUnit } from '../entities/SquadUnit';
import { Tower } from '../entities/Tower';
import { EconomySystem } from '../systems/EconomySystem';
import { PathSystem } from '../systems/PathSystem';
import { WaveSystem } from '../systems/WaveSystem';
import { DEPTH, type GameState, SELL_REFUND, UI_FONT } from '../utils/constants';
import { dist } from '../utils/math';
import { playSfx } from '../utils/sfx';
import type UIScene from './UIScene';

export interface BuildSlot {
  index: number;
  x: number;
  y: number;
  sprite: Phaser.GameObjects.Image;
  tower: Tower | null;
}

export default class BattleScene extends Phaser.Scene {
  level: LevelData = LEVEL_CASTLE;

  pathSystem!: PathSystem;
  waveSystem!: WaveSystem;
  economy!: EconomySystem;
  state: GameState = 'loading';

  enemies: Enemy[] = [];
  towers: Tower[] = [];
  projectiles: Projectile[] = [];
  slots: BuildSlot[] = [];

  private core!: Phaser.GameObjects.Image;
  private rangeGfx!: Phaser.GameObjects.Graphics;

  constructor() {
    super('Battle');
  }

  private get ui(): UIScene {
    return this.scene.get('UI') as UIScene;
  }

  create(): void {
    // Reset everything explicitly — create() runs again on scene.restart().
    this.enemies = [];
    this.towers = [];
    this.projectiles = [];
    this.slots = [];
    this.pathSystem = new PathSystem(this.level.path);
    this.waveSystem = new WaveSystem(WAVES);
    this.economy = new EconomySystem();
    this.state = 'build';

    this.add.image(0, 0, this.level.theme.bgTexture).setOrigin(0).setDepth(DEPTH.bg);

    // Golden Brick Core with a gentle pulse
    this.core = this.add.image(this.level.core.x, this.level.core.y - 24, 'core').setDepth(DEPTH.core);
    this.tweens.add({
      targets: this.core,
      scale: 1.05,
      alpha: 0.92,
      duration: 900,
      yoyo: true,
      repeat: -1,
      ease: 'Sine.easeInOut'
    });

    // Build slots
    this.level.buildSlots.forEach((pos, index) => {
      const sprite = this.add
        .image(pos.x, pos.y, 'slot_pad')
        .setDepth(DEPTH.slot)
        .setInteractive({ useHandCursor: true });
      const slot: BuildSlot = { index, x: pos.x, y: pos.y, sprite, tower: null };
      sprite.on(
        'pointerdown',
        (_p: Phaser.Input.Pointer, _lx: number, _ly: number, event: Phaser.Types.Input.EventData) => {
          event.stopPropagation();
          this.ui.onSlotClicked(slot);
        }
      );
      this.slots.push(slot);
    });

    // Clicks on empty ground: close menus / aim abilities (UI decides).
    this.input.on(
      'pointerdown',
      (pointer: Phaser.Input.Pointer, over: Phaser.GameObjects.GameObject[]) => {
        if (over.length === 0) this.ui.onBackgroundClicked(pointer);
      }
    );

    this.rangeGfx = this.add.graphics().setDepth(DEPTH.fx);

    if (this.scene.isActive('UI')) {
      this.ui.resetForNewGame();
    } else {
      this.scene.launch('UI');
    }
  }

  // ------------------------------------------------------------------ waves

  get enemiesRemaining(): number {
    return this.enemies.length + this.waveSystem.remainingToSpawn;
  }

  startWave(): void {
    if (this.state !== 'build') return;
    if (!this.waveSystem.startNextWave()) return;
    this.state = 'wave';
    playSfx('wave-start');
    this.ui.onWaveStarted(this.waveSystem.currentWave);
  }

  private spawnEnemy(enemyId: string): void {
    const def = ENEMIES[enemyId];
    if (!def) return;
    this.enemies.push(new Enemy(this, def, this.pathSystem));
  }

  // ----------------------------------------------------------------- towers

  buildTower(slot: BuildSlot, family: TowerFamily): boolean {
    if (this.state === 'victory' || this.state === 'defeat') return false;
    if (slot.tower) return false;
    const def = TOWERS[family];
    if (!this.economy.spend(def.cost)) return false;

    const tower = new Tower(this, slot.x, slot.y - 18, def, slot.index);
    tower.hitSprite.on(
      'pointerdown',
      (_p: Phaser.Input.Pointer, _lx: number, _ly: number, event: Phaser.Types.Input.EventData) => {
        event.stopPropagation();
        this.ui.onTowerClicked(tower);
      }
    );
    slot.tower = tower;
    this.towers.push(tower);

    if (def.squad) {
      this.spawnKnights(tower, slot);
    }

    playSfx('build');
    this.spawnGlow(slot.x, slot.y, 40, 0xffffff, 0.6);
    return true;
  }

  private spawnKnights(tower: Tower, slot: BuildSlot): void {
    const squad = tower.def.squad!;
    const rally = this.pathSystem.closestPoint(slot.x, slot.y);
    const a = this.level.path[rally.segIndex];
    const b = this.level.path[rally.segIndex + 1];
    const len = Math.max(1, dist(a.x, a.y, b.x, b.y));
    // knights stand side by side along the path direction
    const dirX = (b.x - a.x) / len;
    const dirY = (b.y - a.y) / len;
    for (let i = 0; i < squad.spawnCount; i++) {
      const offset = (i - (squad.spawnCount - 1) / 2) * 34;
      const knight = new SquadUnit(
        this,
        rally.x + dirX * offset,
        rally.y + dirY * offset,
        tower.currentKnightStats()
      );
      tower.knights.push(knight);
    }
  }

  upgradeTower(tower: Tower): boolean {
    if (!tower.canUpgrade) return false;
    if (!this.economy.spend(tower.upgradeCost)) return false;
    tower.upgrade();
    playSfx('upgrade');
    this.spawnGlow(tower.x, tower.y, 44, 0xffd23f, 0.7);
    return true;
  }

  sellTower(tower: Tower): void {
    const refund = this.sellRefund(tower);
    this.economy.earn(refund);
    const slot = this.slots[tower.slotIndex];
    slot.tower = null;
    this.towers = this.towers.filter((t) => t !== tower);
    tower.destroyTower();
    this.floatingText(slot.x, slot.y - 30, `+${refund}`, '#ffc93a');
    playSfx('sell');
  }

  sellRefund(tower: Tower): number {
    return Math.floor(tower.invested * SELL_REFUND);
  }

  // -------------------------------------------------------------- abilities

  castFireball(x: number, y: number): void {
    for (const enemy of this.enemies) {
      if (enemy.dead || enemy.reachedEnd) continue;
      if (dist(x, y, enemy.x, enemy.y) <= FIREBALL_RADIUS) {
        enemy.takeDamage(FIREBALL_DAMAGE, 'magic');
      }
    }
    this.spawnExplosion(x, y, FIREBALL_RADIUS, 0xff8030);
    this.cameras.main.shake(200, 0.006);
    playSfx('ability');
  }

  castFreeze(): void {
    for (const enemy of this.enemies) {
      if (!enemy.dead && !enemy.reachedEnd) enemy.applySlow(FREEZE_SLOW, FREEZE_DURATION);
    }
    this.cameras.main.flash(350, 150, 200, 255);
    playSfx('ability');
  }

  castHeal(): void {
    this.economy.addLives(HEAL_LIVES);
    for (const tower of this.towers) tower.reviveKnights();
    this.cameras.main.flash(350, 140, 230, 140);
    this.floatingText(this.level.core.x - 40, this.level.core.y - 80, `+${HEAL_LIVES} ♥`, '#7ce07c');
    playSfx('ability');
  }

  // ------------------------------------------------------------------ range

  showRange(x: number, y: number, range: number): void {
    this.rangeGfx.clear();
    this.rangeGfx.fillStyle(0xffffff, 0.08);
    this.rangeGfx.fillCircle(x, y, range);
    this.rangeGfx.lineStyle(2, 0xffffff, 0.4);
    this.rangeGfx.strokeCircle(x, y, range);
  }

  hideRange(): void {
    this.rangeGfx.clear();
  }

  // ------------------------------------------------------------------- loop

  update(_time: number, delta: number): void {
    if (this.state !== 'wave' && this.state !== 'build') return;
    const dt = Math.min(delta / 1000, 0.05);

    if (this.state === 'wave') {
      this.waveSystem.update(dt, (id) => this.spawnEnemy(id));
    }

    for (const tower of this.towers) {
      const target = tower.update(dt, this.enemies);
      if (target) this.fireAt(tower, target);
      for (const knight of tower.knights) knight.update(dt, this.enemies);
    }

    for (const enemy of this.enemies) enemy.update(dt);

    for (const proj of this.projectiles) {
      const impact = proj.update(dt);
      if (impact) this.resolveImpact(proj, impact.x, impact.y);
    }
    this.projectiles = this.projectiles.filter((p) => {
      if (p.done) {
        p.destroy();
        return false;
      }
      return true;
    });

    // deaths and leaks
    const survivors: Enemy[] = [];
    for (const enemy of this.enemies) {
      if (enemy.dead) {
        this.onEnemyKilled(enemy);
        enemy.destroy();
      } else if (enemy.reachedEnd) {
        this.onEnemyLeaked(enemy);
        enemy.destroy();
      } else {
        survivors.push(enemy);
      }
    }
    this.enemies = survivors;

    if (this.economy.lives <= 0) {
      this.state = 'defeat';
      playSfx('defeat');
      return;
    }

    if (this.state === 'wave' && this.waveSystem.remainingToSpawn === 0 && this.enemies.length === 0) {
      if (this.waveSystem.isLastWave) {
        this.state = 'victory';
        playSfx('victory');
      } else {
        this.state = 'build';
      }
    }
  }

  private fireAt(tower: Tower, target: Enemy): void {
    const def = tower.def;
    if (!def.projectile) return;
    this.projectiles.push(
      new Projectile(this, {
        kind: def.projectile,
        x: tower.x,
        y: tower.y - 30,
        target,
        damage: tower.damage,
        damageType: def.damageType,
        speed: def.projectileSpeed ?? 500,
        splashRadius: def.splashRadius,
        slowPercent: def.slowPercent,
        slowDuration: def.slowDuration
      })
    );
    playSfx(def.projectile === 'rock' ? 'smash' : def.projectile === 'bolt' ? 'magic' : 'shoot');
  }

  private resolveImpact(proj: Projectile, x: number, y: number): void {
    const opts = proj.opts;
    if (opts.kind === 'rock') {
      // splash damage to ground enemies around the impact point
      for (const enemy of this.enemies) {
        if (enemy.dead || enemy.reachedEnd || enemy.def.isFlying) continue;
        if (dist(x, y, enemy.x, enemy.y) <= (opts.splashRadius ?? 0)) {
          enemy.takeDamage(opts.damage, opts.damageType);
        }
      }
      this.spawnExplosion(x, y, opts.splashRadius ?? 70, 0xffa040);
      return;
    }

    const target = opts.target;
    if (!target.dead && !target.reachedEnd) {
      target.takeDamage(opts.damage, opts.damageType);
      if (opts.slowPercent && opts.slowDuration) {
        target.applySlow(opts.slowPercent, opts.slowDuration);
      }
      this.spawnGlow(x, y, 14, opts.kind === 'bolt' ? 0xb07de8 : 0xffffff, 0.8);
    }
  }

  private onEnemyKilled(enemy: Enemy): void {
    this.economy.earn(enemy.def.reward);
    this.floatingText(enemy.x, enemy.y - 24, `+${enemy.def.reward}`, '#ffc93a');
    this.spawnGlow(enemy.x, enemy.y, 22, 0xffe27a, 0.7);
    playSfx('enemy-death');
  }

  private onEnemyLeaked(enemy: Enemy): void {
    this.economy.loseLives(enemy.def.livesDamage);
    this.cameras.main.shake(150, 0.004);
    this.tweens.add({ targets: this.core, alpha: 0.3, duration: 90, yoyo: true, repeat: 2 });
    this.floatingText(this.level.core.x - 40, this.level.core.y - 70, `-${enemy.def.livesDamage} ♥`, '#ff6060');
    playSfx('life-lost');
  }

  // --------------------------------------------------------------------- fx

  private spawnGlow(x: number, y: number, radius: number, tint: number, alpha: number): void {
    const img = this.add.image(x, y, 'fx_glow').setDepth(DEPTH.fx).setTint(tint).setAlpha(alpha);
    img.setScale(radius / 32);
    this.tweens.add({
      targets: img,
      scale: img.scale * 1.6,
      alpha: 0,
      duration: 220,
      onComplete: () => img.destroy()
    });
  }

  private spawnExplosion(x: number, y: number, radius: number, tint: number): void {
    this.spawnGlow(x, y, radius * 0.8, tint, 0.85);
    this.spawnGlow(x, y, radius * 0.4, 0xffe27a, 0.9);
    const ring = this.add.graphics({ x, y }).setDepth(DEPTH.fx);
    ring.lineStyle(4, tint, 0.8);
    ring.strokeCircle(0, 0, radius * 0.4);
    this.tweens.add({
      targets: ring,
      alpha: 0,
      scale: 2,
      duration: 260,
      onComplete: () => ring.destroy()
    });
  }

  floatingText(x: number, y: number, str: string, color: string): void {
    const txt = this.add
      .text(x, y, str, {
        fontFamily: UI_FONT,
        fontSize: '18px',
        color,
        stroke: '#14161c',
        strokeThickness: 4
      })
      .setOrigin(0.5)
      .setDepth(DEPTH.fx);
    this.tweens.add({
      targets: txt,
      y: y - 40,
      alpha: 0,
      duration: 900,
      ease: 'Cubic.easeOut',
      onComplete: () => txt.destroy()
    });
  }
}
