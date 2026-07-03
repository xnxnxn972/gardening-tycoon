import Phaser from 'phaser';
import { TOWER_FAMILIES, TOWERS, type TowerFamily } from '../data/towers';
import { GAME_HEIGHT, UI_FONT } from '../utils/constants';
import { drawPanel, uiClick } from './helpers';

const CARD_W = 112;
const CARD_H = 142;
const CARD_GAP = 10;

interface Card {
  family: TowerFamily;
  container: Phaser.GameObjects.Container;
  bg: Phaser.GameObjects.Graphics;
}

/**
 * The four big build buttons in the bottom-left corner. Clicking one enters
 * placement mode: free slots pulse and the next slot click builds there.
 */
export class TowerCards extends Phaser.GameObjects.Container {
  private readonly cards: Card[] = [];
  private lastGold = -1;
  private lastSelected: TowerFamily | null | undefined;

  constructor(scene: Phaser.Scene, onSelect: (family: TowerFamily) => void) {
    super(scene, 0, 0);

    TOWER_FAMILIES.forEach((family, i) => {
      const def = TOWERS[family];
      const x = 20 + i * (CARD_W + CARD_GAP);
      const y = GAME_HEIGHT - CARD_H - 14;

      const container = scene.add.container(x, y);
      const bg = scene.add.graphics();
      container.add(bg);

      const label = scene.add
        .text(CARD_W / 2, 20, def.label, {
          fontFamily: UI_FONT,
          fontSize: '16px',
          color: '#ffffff',
          fontStyle: 'bold'
        })
        .setOrigin(0.5);
      container.add(label);

      const icon = scene.add.image(CARD_W / 2, 74, def.texture).setScale(0.82);
      container.add(icon);

      container.add(scene.add.image(CARD_W / 2 - 24, CARD_H - 22, 'icon_coin').setScale(0.75));
      const cost = scene.add
        .text(CARD_W / 2 - 10, CARD_H - 22, `${def.cost}`, {
          fontFamily: UI_FONT,
          fontSize: '19px',
          color: '#ffc93a',
          fontStyle: 'bold'
        })
        .setOrigin(0, 0.5);
      container.add(cost);

      container.setInteractive(
        new Phaser.Geom.Rectangle(0, 0, CARD_W, CARD_H),
        Phaser.Geom.Rectangle.Contains
      );
      if (container.input) container.input.cursor = 'pointer';
      container.on('pointerdown', uiClick(() => onSelect(family)));

      this.cards.push({ family, container, bg });
      this.add(container);
    });

    scene.add.existing(this);
    this.redraw(0, null);
  }

  refresh(gold: number, selected: TowerFamily | null): void {
    if (gold === this.lastGold && selected === this.lastSelected) return;
    this.lastGold = gold;
    this.lastSelected = selected;
    this.redraw(gold, selected);
  }

  private redraw(gold: number, selected: TowerFamily | null): void {
    for (const card of this.cards) {
      const def = TOWERS[card.family];
      const affordable = gold >= def.cost;
      const border = selected === card.family ? 0xffd23f : def.uiColor;
      card.bg.clear();
      drawPanel(card.bg, 0, 0, CARD_W, CARD_H, border, 0.92, 14);
      card.container.setAlpha(affordable ? 1 : 0.5);
    }
  }
}
