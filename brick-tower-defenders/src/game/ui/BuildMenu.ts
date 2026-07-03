import Phaser from 'phaser';
import { TOWER_FAMILIES, TOWERS, type TowerFamily } from '../data/towers';
import { GAME_WIDTH, UI_FONT } from '../utils/constants';
import { clamp } from '../utils/math';
import { drawPanel, uiClick } from './helpers';

const BTN_W = 84;
const BTN_H = 104;
const GAP = 8;
const MENU_W = TOWER_FAMILIES.length * (BTN_W + GAP) + GAP;
const MENU_H = BTN_H + 16;

interface Option {
  family: TowerFamily;
  container: Phaser.GameObjects.Container;
  bg: Phaser.GameObjects.Graphics;
}

/** Contextual build menu that pops up next to a clicked empty slot. */
export class BuildMenu extends Phaser.GameObjects.Container {
  slotIndex = -1;
  private readonly options: Option[] = [];
  private lastGold = -1;

  constructor(scene: Phaser.Scene, onChoose: (slotIndex: number, family: TowerFamily) => void) {
    super(scene, 0, 0);

    const panel = scene.add.graphics();
    drawPanel(panel, 0, 0, MENU_W, MENU_H, 0x3a4152, 0.95, 14);
    this.add(panel);

    TOWER_FAMILIES.forEach((family, i) => {
      const def = TOWERS[family];
      const container = scene.add.container(GAP + i * (BTN_W + GAP), 8);

      const bg = scene.add.graphics();
      container.add(bg);

      container.add(
        scene.add
          .text(BTN_W / 2, 12, def.label, {
            fontFamily: UI_FONT,
            fontSize: '12px',
            color: '#ffffff',
            fontStyle: 'bold'
          })
          .setOrigin(0.5)
      );
      container.add(scene.add.image(BTN_W / 2, 52, def.texture).setScale(0.62));
      container.add(scene.add.image(BTN_W / 2 - 20, BTN_H - 14, 'icon_coin').setScale(0.6));
      container.add(
        scene.add
          .text(BTN_W / 2 - 8, BTN_H - 14, `${def.cost}`, {
            fontFamily: UI_FONT,
            fontSize: '15px',
            color: '#ffc93a',
            fontStyle: 'bold'
          })
          .setOrigin(0, 0.5)
      );

      container.setInteractive(
        new Phaser.Geom.Rectangle(0, 0, BTN_W, BTN_H),
        Phaser.Geom.Rectangle.Contains
      );
      if (container.input) container.input.cursor = 'pointer';
      container.on('pointerdown', uiClick(() => onChoose(this.slotIndex, family)));

      this.options.push({ family, container, bg });
      this.add(container);
    });

    this.setVisible(false);
    scene.add.existing(this);
  }

  get isOpen(): boolean {
    return this.visible;
  }

  open(slotIndex: number, slotX: number, slotY: number, gold: number): void {
    this.slotIndex = slotIndex;
    const x = clamp(slotX - MENU_W / 2, 12, GAME_WIDTH - MENU_W - 12);
    const y = slotY - MENU_H - 56 > 90 ? slotY - MENU_H - 56 : slotY + 56;
    this.setPosition(x, y);
    this.lastGold = -1;
    this.refresh(gold);
    this.setVisible(true);
  }

  close(): void {
    this.setVisible(false);
    this.slotIndex = -1;
  }

  refresh(gold: number): void {
    if (gold === this.lastGold) return;
    this.lastGold = gold;
    for (const opt of this.options) {
      const def = TOWERS[opt.family];
      const affordable = gold >= def.cost;
      opt.bg.clear();
      opt.bg.fillStyle(affordable ? 0x232836 : 0x1a1d26, 1);
      opt.bg.fillRoundedRect(0, 0, BTN_W, BTN_H, 10);
      opt.bg.lineStyle(2, affordable ? def.uiColor : 0x3a4152, 1);
      opt.bg.strokeRoundedRect(0, 0, BTN_W, BTN_H, 10);
      opt.container.setAlpha(affordable ? 1 : 0.55);
    }
  }
}
