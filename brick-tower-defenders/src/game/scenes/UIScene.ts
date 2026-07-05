import Phaser from 'phaser';
import { ABILITIES, type AbilityId } from '../data/abilities';
import type { TowerFamily } from '../data/towers';
import type { Tower } from '../entities/Tower';
import { DEPTH, GAME_HEIGHT, GAME_WIDTH, UI_FONT } from '../utils/constants';
import { playSfx } from '../utils/sfx';
import { AbilityBar } from '../ui/AbilityBar';
import { BuildMenu } from '../ui/BuildMenu';
import { Hud } from '../ui/Hud';
import { TowerCards } from '../ui/TowerCards';
import { TowerInfoPanel } from '../ui/TowerInfoPanel';
import { drawPanel, uiClick } from '../ui/helpers';
import type BattleScene from './BattleScene';
import type { BuildSlot } from './BattleScene';

export default class UIScene extends Phaser.Scene {
  private hud!: Hud;
  private cards!: TowerCards;
  private abilityBar!: AbilityBar;
  private buildMenu!: BuildMenu;
  private infoPanel!: TowerInfoPanel;
  private startBtn!: Phaser.GameObjects.Container;
  private startText!: Phaser.GameObjects.Text;
  private highlightGfx!: Phaser.GameObjects.Graphics;
  private aimHint!: Phaser.GameObjects.Text;
  private pauseOverlay!: Phaser.GameObjects.Container;

  private placementFamily: TowerFamily | null = null;
  private pendingAbility: AbilityId | null = null;
  private abilityUses!: Record<AbilityId, number>;
  private overlay: Phaser.GameObjects.Container | null = null;
  private overlayShown: 'none' | 'victory' | 'defeat' = 'none';
  private paused = false;
  private speedOn = false;
  private speedBg!: Phaser.GameObjects.Graphics;
  private speedText!: Phaser.GameObjects.Text;

  constructor() {
    super('UI');
  }

  private get battle(): BattleScene {
    return this.scene.get('Battle') as BattleScene;
  }

  create(): void {
    this.resetAbilityUses();

    this.hud = new Hud(this);
    this.cards = new TowerCards(this, (family) => this.onCardSelected(family));
    this.abilityBar = new AbilityBar(this, (id) => this.onAbilityClicked(id));
    this.buildMenu = new BuildMenu(this, (slotIndex, family) => this.onBuildChosen(slotIndex, family));
    this.infoPanel = new TowerInfoPanel(
      this,
      (tower) => this.onUpgrade(tower),
      (tower) => this.onSell(tower),
      () => this.closeMenus()
    );
    this.buildMenu.setDepth(DEPTH.ui + 10);
    this.infoPanel.setDepth(DEPTH.ui + 10);
    this.hud.setDepth(DEPTH.ui);
    this.cards.setDepth(DEPTH.ui);
    this.abilityBar.setDepth(DEPTH.ui);

    this.highlightGfx = this.add.graphics().setDepth(DEPTH.ui - 1);

    this.createStartButton();
    this.createPauseButton();
    this.createSpeedButton();
    this.createAimHint();
    this.createPauseOverlay();

    this.input.keyboard?.on('keydown-ESC', () => {
      this.placementFamily = null;
      this.pendingAbility = null;
      this.closeMenus();
    });
  }

  private resetAbilityUses(): void {
    this.abilityUses = { fireball: 0, freeze: 0, heal: 0 };
    for (const a of ABILITIES) this.abilityUses[a.id] = a.uses;
  }

  private createStartButton(): void {
    this.startBtn = this.add.container(GAME_WIDTH / 2, GAME_HEIGHT - 52);

    // The pulse lives on an inner, non-interactive container. The outer
    // startBtn keeps a fixed scale: Phaser's input hit-test intermittently
    // fails on a container whose scale is actively being tweened (points
    // inside it, even the center, miss ~30% of frames), so the clickable
    // container must never be the tween target.
    const visual = this.add.container(0, 0);
    const g = this.add.graphics();
    g.fillStyle(0x2a5c33, 0.95);
    g.fillRoundedRect(-140, -30, 280, 60, 16);
    g.lineStyle(3, 0x5fd66e, 1);
    g.strokeRoundedRect(-140, -30, 280, 60, 16);
    visual.add(g);
    this.startText = this.add
      .text(0, 0, 'START WAVE 1', {
        fontFamily: UI_FONT,
        fontSize: '24px',
        color: '#ffffff',
        fontStyle: 'bold'
      })
      .setOrigin(0.5);
    visual.add(this.startText);
    this.startBtn.add(visual);

    // Hit area sized to the pulse peak (1.05×) so the enlarged visual is
    // always fully clickable.
    this.startBtn.setSize(294, 63);
    this.startBtn.setInteractive(
      new Phaser.Geom.Rectangle(-147, -31.5, 294, 63),
      Phaser.Geom.Rectangle.Contains
    );
    if (this.startBtn.input) this.startBtn.input.cursor = 'pointer';
    this.startBtn.on('pointerdown', uiClick(() => this.battle.startWave()));
    this.startBtn.setDepth(DEPTH.ui);
    this.tweens.add({
      targets: visual,
      scale: 1.05,
      duration: 600,
      yoyo: true,
      repeat: -1,
      ease: 'Sine.easeInOut'
    });
  }

  private createPauseButton(): void {
    const btn = this.add.container(GAME_WIDTH - 46, 43);
    const g = this.add.graphics();
    drawPanel(g, -24, -24, 48, 48, 0x2c3140, 0.9, 10);
    g.fillStyle(0xffffff, 1);
    g.fillRect(-9, -11, 6, 22);
    g.fillRect(3, -11, 6, 22);
    btn.add(g);
    btn.setInteractive(new Phaser.Geom.Rectangle(-24, -24, 48, 48), Phaser.Geom.Rectangle.Contains);
    if (btn.input) btn.input.cursor = 'pointer';
    btn.on('pointerdown', uiClick(() => this.togglePause()));
    btn.setDepth(DEPTH.ui);
  }

  private createSpeedButton(): void {
    const btn = this.add.container(GAME_WIDTH - 102, 43);
    this.speedBg = this.add.graphics();
    btn.add(this.speedBg);
    this.speedText = this.add
      .text(0, 0, '2X', { fontFamily: UI_FONT, fontSize: '19px', color: '#ffffff', fontStyle: 'bold' })
      .setOrigin(0.5);
    btn.add(this.speedText);
    btn.setInteractive(new Phaser.Geom.Rectangle(-24, -24, 48, 48), Phaser.Geom.Rectangle.Contains);
    if (btn.input) btn.input.cursor = 'pointer';
    btn.on('pointerdown', uiClick(() => this.toggleSpeed()));
    btn.setDepth(DEPTH.ui);
    this.redrawSpeedButton();
  }

  private toggleSpeed(): void {
    if (this.overlayShown !== 'none') return;
    this.speedOn = !this.speedOn;
    this.battle.setSpeed(this.speedOn ? 2 : 1);
    this.redrawSpeedButton();
  }

  private redrawSpeedButton(): void {
    this.speedBg.clear();
    drawPanel(this.speedBg, -24, -24, 48, 48, this.speedOn ? 0xffd23f : 0x2c3140, 0.9, 10);
    this.speedText.setColor(this.speedOn ? '#ffd23f' : '#ffffff');
  }

  private createAimHint(): void {
    this.aimHint = this.add
      .text(GAME_WIDTH / 2, 110, 'Click the map to aim the Fireball  (Esc to cancel)', {
        fontFamily: UI_FONT,
        fontSize: '20px',
        color: '#ffc93a',
        backgroundColor: '#171a21ee',
        padding: { x: 14, y: 8 }
      })
      .setOrigin(0.5)
      .setDepth(DEPTH.ui)
      .setVisible(false);
  }

  private createPauseOverlay(): void {
    this.pauseOverlay = this.add.container(0, 0).setDepth(DEPTH.overlay).setVisible(false);
    const dim = this.add.rectangle(GAME_WIDTH / 2, GAME_HEIGHT / 2, GAME_WIDTH, GAME_HEIGHT, 0x000000, 0.55);
    dim.setInteractive();
    dim.on('pointerdown', uiClick(() => this.togglePause()));
    this.pauseOverlay.add(dim);
    this.pauseOverlay.add(
      this.add
        .text(GAME_WIDTH / 2, GAME_HEIGHT / 2, 'PAUSED\n\nclick to resume', {
          fontFamily: UI_FONT,
          fontSize: '44px',
          color: '#ffffff',
          fontStyle: 'bold',
          align: 'center'
        })
        .setOrigin(0.5)
    );
  }

  private togglePause(): void {
    if (this.overlayShown !== 'none') return;
    this.paused = !this.paused;
    if (this.paused) {
      this.scene.pause('Battle');
    } else {
      this.scene.resume('Battle');
    }
    this.pauseOverlay.setVisible(this.paused);
  }

  // ------------------------------------------------- called by BattleScene

  onSlotClicked(slot: BuildSlot): void {
    if (this.paused || this.overlayShown !== 'none') return;
    if (this.pendingAbility === 'fireball') {
      this.castPendingFireball(slot.x, slot.y);
      return;
    }
    this.infoPanel.close();
    this.battle.hideRange();
    if (slot.tower) return;

    if (this.placementFamily) {
      if (this.battle.buildTower(slot, this.placementFamily)) {
        this.placementFamily = null;
        this.buildMenu.close();
      } else {
        this.battle.floatingText(slot.x, slot.y - 40, 'Not enough gold!', '#ff6060');
      }
      return;
    }
    this.buildMenu.open(slot.index, slot.x, slot.y, this.battle.economy.gold);
  }

  onTowerClicked(tower: Tower): void {
    if (this.paused || this.overlayShown !== 'none') return;
    if (this.pendingAbility === 'fireball') {
      this.castPendingFireball(tower.x, tower.y);
      return;
    }
    this.placementFamily = null;
    this.buildMenu.close();
    this.infoPanel.open(tower, this.battle.economy.gold, this.battle.sellRefund(tower));
    this.battle.showRange(tower.x, tower.y, tower.range);
  }

  onBackgroundClicked(pointer: Phaser.Input.Pointer): void {
    if (this.paused || this.overlayShown !== 'none') return;
    if (this.pendingAbility === 'fireball') {
      this.castPendingFireball(pointer.worldX, pointer.worldY);
      return;
    }
    this.closeMenus();
    this.placementFamily = null;
  }

  onWaveStarted(wave: number): void {
    const banner = this.add
      .text(GAME_WIDTH / 2, 260, `WAVE ${wave}`, {
        fontFamily: UI_FONT,
        fontSize: '64px',
        color: '#ffffff',
        fontStyle: 'bold',
        stroke: '#14161c',
        strokeThickness: 8
      })
      .setOrigin(0.5)
      .setDepth(DEPTH.ui + 20)
      .setAlpha(0);
    this.tweens.add({
      targets: banner,
      alpha: 1,
      scale: { from: 0.6, to: 1 },
      duration: 250,
      ease: 'Back.easeOut',
      onComplete: () => {
        this.tweens.add({
          targets: banner,
          alpha: 0,
          delay: 800,
          duration: 400,
          onComplete: () => banner.destroy()
        });
      }
    });
  }

  resetForNewGame(): void {
    this.resetAbilityUses();
    this.placementFamily = null;
    this.pendingAbility = null;
    this.speedOn = false;
    this.redrawSpeedButton();
    this.closeMenus();
    this.overlay?.destroy();
    this.overlay = null;
    this.overlayShown = 'none';
    if (this.paused) this.togglePause();
  }

  // ----------------------------------------------------------- UI handlers

  private onCardSelected(family: TowerFamily): void {
    if (this.paused || this.overlayShown !== 'none') return;
    this.pendingAbility = null;
    this.buildMenu.close();
    this.infoPanel.close();
    this.battle.hideRange();
    this.placementFamily = this.placementFamily === family ? null : family;
  }

  private onBuildChosen(slotIndex: number, family: TowerFamily): void {
    const slot = this.battle.slots[slotIndex];
    if (!slot || slot.tower) return;
    if (this.battle.buildTower(slot, family)) {
      this.buildMenu.close();
    } else {
      this.battle.floatingText(slot.x, slot.y - 40, 'Not enough gold!', '#ff6060');
    }
  }

  private onUpgrade(tower: Tower): void {
    if (this.battle.upgradeTower(tower)) {
      // reopen to refresh level, sell value, and range circle
      this.infoPanel.open(tower, this.battle.economy.gold, this.battle.sellRefund(tower));
      this.battle.showRange(tower.x, tower.y, tower.range);
    }
  }

  private onSell(tower: Tower): void {
    this.battle.sellTower(tower);
    this.closeMenus();
  }

  private onAbilityClicked(id: AbilityId): void {
    if (this.paused || this.overlayShown !== 'none') return;
    if (this.abilityUses[id] <= 0) return;
    const def = ABILITIES.find((a) => a.id === id)!;
    if (def.needsTarget) {
      this.pendingAbility = this.pendingAbility === id ? null : id;
      return;
    }
    this.abilityUses[id]--;
    if (id === 'freeze') this.battle.castFreeze();
    else if (id === 'heal') this.battle.castHeal();
  }

  private castPendingFireball(x: number, y: number): void {
    if (this.abilityUses.fireball <= 0) return;
    this.abilityUses.fireball--;
    this.pendingAbility = null;
    this.battle.castFireball(x, y);
  }

  private closeMenus(): void {
    this.buildMenu.close();
    this.infoPanel.close();
    if (this.battle.scene.isActive() || this.battle.scene.isPaused()) {
      this.battle.hideRange();
    }
  }

  // ---------------------------------------------------------------- update

  update(time: number): void {
    const battle = this.battle;
    if (!battle || !battle.economy) return;
    const eco = battle.economy;

    // during the build phase, show the upcoming wave number
    const displayWave =
      battle.state === 'build'
        ? Math.min(battle.waveSystem.currentWave + 1, battle.waveSystem.totalWaves)
        : battle.waveSystem.currentWave;
    this.hud.refresh(eco.gold, eco.lives, displayWave, battle.waveSystem.totalWaves, battle.enemiesRemaining);
    this.cards.refresh(eco.gold, this.placementFamily);
    this.abilityBar.refresh(this.abilityUses, this.pendingAbility);
    if (this.buildMenu.isOpen) this.buildMenu.refresh(eco.gold);
    if (this.infoPanel.isOpen) this.infoPanel.refresh(eco.gold);

    const showStart = battle.state === 'build' && this.overlayShown === 'none';
    this.startBtn.setVisible(showStart);
    if (showStart) {
      this.startText.setText(`START WAVE ${battle.waveSystem.currentWave + 1}`);
    }

    this.aimHint.setVisible(this.pendingAbility !== null);

    // pulse free slots while placing a tower
    this.highlightGfx.clear();
    if (this.placementFamily) {
      const pulse = 0.25 + 0.2 * Math.sin(time / 180);
      this.highlightGfx.fillStyle(0xffd23f, pulse);
      this.highlightGfx.lineStyle(3, 0xffd23f, 0.8);
      for (const slot of battle.slots) {
        if (!slot.tower) {
          this.highlightGfx.fillCircle(slot.x, slot.y, 40);
          this.highlightGfx.strokeCircle(slot.x, slot.y, 40);
        }
      }
    }

    if (battle.state === 'victory' && this.overlayShown !== 'victory') {
      this.showEndOverlay(true);
    } else if (battle.state === 'defeat' && this.overlayShown !== 'defeat') {
      this.showEndOverlay(false);
    }
  }

  private showEndOverlay(victory: boolean): void {
    this.overlay?.destroy();
    this.overlayShown = victory ? 'victory' : 'defeat';
    this.placementFamily = null;
    this.pendingAbility = null;
    this.closeMenus();
    playSfx(victory ? 'victory' : 'defeat');

    const overlay = this.add.container(0, 0).setDepth(DEPTH.overlay);
    const dim = this.add.rectangle(GAME_WIDTH / 2, GAME_HEIGHT / 2, GAME_WIDTH, GAME_HEIGHT, 0x000000, 0.65);
    dim.setInteractive(); // block clicks to the battlefield
    overlay.add(dim);

    const g = this.add.graphics();
    drawPanel(g, GAME_WIDTH / 2 - 280, GAME_HEIGHT / 2 - 160, 560, 320, victory ? 0xffd23f : 0xc0473e, 0.97, 20);
    overlay.add(g);

    overlay.add(
      this.add
        .text(GAME_WIDTH / 2, GAME_HEIGHT / 2 - 90, victory ? 'Victory!' : 'Defeat!', {
          fontFamily: UI_FONT,
          fontSize: '56px',
          color: victory ? '#ffd23f' : '#ff6060',
          fontStyle: 'bold'
        })
        .setOrigin(0.5)
    );
    overlay.add(
      this.add
        .text(
          GAME_WIDTH / 2,
          GAME_HEIGHT / 2 - 20,
          victory ? 'The Golden Brick is safe.' : 'The enemies stole the Golden Brick.',
          { fontFamily: UI_FONT, fontSize: '24px', color: '#ffffff' }
        )
        .setOrigin(0.5)
    );

    const btn = this.add.container(GAME_WIDTH / 2, GAME_HEIGHT / 2 + 80);
    const bg = this.add.graphics();
    bg.fillStyle(0x2a5c33, 1);
    bg.fillRoundedRect(-120, -28, 240, 56, 14);
    bg.lineStyle(3, 0x5fd66e, 1);
    bg.strokeRoundedRect(-120, -28, 240, 56, 14);
    btn.add(bg);
    btn.add(
      this.add
        .text(0, 0, victory ? 'Play Again' : 'Try Again', {
          fontFamily: UI_FONT,
          fontSize: '24px',
          color: '#ffffff',
          fontStyle: 'bold'
        })
        .setOrigin(0.5)
    );
    btn.setInteractive(new Phaser.Geom.Rectangle(-120, -28, 240, 56), Phaser.Geom.Rectangle.Contains);
    if (btn.input) btn.input.cursor = 'pointer';
    btn.on(
      'pointerdown',
      uiClick(() => {
        this.battle.scene.restart();
      })
    );
    overlay.add(btn);

    this.overlay = overlay;
  }
}
