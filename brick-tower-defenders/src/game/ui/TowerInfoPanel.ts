import Phaser from 'phaser';
import type { Tower } from '../entities/Tower';
import { GAME_WIDTH, UI_FONT } from '../utils/constants';
import { clamp } from '../utils/math';
import { drawPanel, uiClick } from './helpers';

const W = 250;
const H = 182;

/** Panel shown when clicking a built tower: name, upgrade, sell. */
export class TowerInfoPanel extends Phaser.GameObjects.Container {
  tower: Tower | null = null;

  private readonly title: Phaser.GameObjects.Text;
  private readonly levelText: Phaser.GameObjects.Text;
  private readonly upgradeBg: Phaser.GameObjects.Graphics;
  private readonly upgradeText: Phaser.GameObjects.Text;
  private readonly sellText: Phaser.GameObjects.Text;
  private lastGold = -1;

  constructor(
    scene: Phaser.Scene,
    onUpgrade: (tower: Tower) => void,
    onSell: (tower: Tower) => void,
    onClose: () => void
  ) {
    super(scene, 0, 0);

    const panel = scene.add.graphics();
    drawPanel(panel, 0, 0, W, H, 0x3a4152, 0.95, 14);
    this.add(panel);

    this.title = scene.add
      .text(16, 16, '', { fontFamily: UI_FONT, fontSize: '19px', color: '#ffffff', fontStyle: 'bold' })
      .setOrigin(0, 0);
    this.add(this.title);

    this.levelText = scene.add
      .text(16, 44, '', { fontFamily: UI_FONT, fontSize: '15px', color: '#9aa2b1' })
      .setOrigin(0, 0);
    this.add(this.levelText);

    // close button
    const closeBtn = scene.add
      .text(W - 20, 18, '✕', { fontFamily: UI_FONT, fontSize: '18px', color: '#9aa2b1' })
      .setOrigin(0.5)
      .setInteractive({ useHandCursor: true });
    closeBtn.on('pointerdown', uiClick(onClose));
    this.add(closeBtn);

    // upgrade button
    this.upgradeBg = scene.add.graphics();
    this.add(this.upgradeBg);
    this.upgradeText = scene.add
      .text(W / 2, 92, '', { fontFamily: UI_FONT, fontSize: '17px', color: '#ffffff', fontStyle: 'bold' })
      .setOrigin(0.5);
    this.add(this.upgradeText);
    const upgradeHit = scene.add
      .zone(W / 2, 92, W - 32, 40)
      .setInteractive({ useHandCursor: true });
    upgradeHit.on(
      'pointerdown',
      uiClick(() => {
        if (this.tower) onUpgrade(this.tower);
      })
    );
    this.add(upgradeHit);

    // sell button
    const sellBg = scene.add.graphics();
    sellBg.fillStyle(0x6b2d28, 1);
    sellBg.fillRoundedRect(16, 132, W - 32, 36, 10);
    sellBg.lineStyle(2, 0xc0473e, 1);
    sellBg.strokeRoundedRect(16, 132, W - 32, 36, 10);
    this.add(sellBg);
    this.sellText = scene.add
      .text(W / 2, 150, '', { fontFamily: UI_FONT, fontSize: '16px', color: '#ffffff', fontStyle: 'bold' })
      .setOrigin(0.5);
    this.add(this.sellText);
    const sellHit = scene.add.zone(W / 2, 150, W - 32, 36).setInteractive({ useHandCursor: true });
    sellHit.on(
      'pointerdown',
      uiClick(() => {
        if (this.tower) onSell(this.tower);
      })
    );
    this.add(sellHit);

    this.setVisible(false);
    scene.add.existing(this);
  }

  get isOpen(): boolean {
    return this.visible;
  }

  open(tower: Tower, gold: number, sellRefund: number): void {
    this.tower = tower;
    this.title.setText(tower.def.name);
    this.sellText.setText(`SELL  +${sellRefund}`);
    const x = clamp(tower.x - W / 2, 12, GAME_WIDTH - W - 12);
    const y = tower.y - H - 70 > 90 ? tower.y - H - 70 : tower.y + 60;
    this.setPosition(x, y);
    this.lastGold = -1;
    this.refresh(gold);
    this.setVisible(true);
  }

  close(): void {
    this.setVisible(false);
    this.tower = null;
  }

  refresh(gold: number): void {
    if (!this.tower || gold === this.lastGold) return;
    this.lastGold = gold;
    const tower = this.tower;
    this.levelText.setText(`Level ${tower.level} / 2`);

    this.upgradeBg.clear();
    if (tower.canUpgrade) {
      const affordable = gold >= tower.upgradeCost;
      this.upgradeBg.fillStyle(affordable ? 0x2a5c33 : 0x22262f, 1);
      this.upgradeBg.fillRoundedRect(16, 72, W - 32, 40, 10);
      this.upgradeBg.lineStyle(2, affordable ? 0x3d9948 : 0x3a4152, 1);
      this.upgradeBg.strokeRoundedRect(16, 72, W - 32, 40, 10);
      this.upgradeText.setText(`UPGRADE  ${tower.upgradeCost}`);
      this.upgradeText.setAlpha(affordable ? 1 : 0.55);
    } else {
      this.upgradeBg.fillStyle(0x22262f, 1);
      this.upgradeBg.fillRoundedRect(16, 72, W - 32, 40, 10);
      this.upgradeText.setText('MAX LEVEL');
      this.upgradeText.setAlpha(0.7);
    }
  }
}
