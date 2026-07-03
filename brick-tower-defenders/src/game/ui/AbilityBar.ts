import Phaser from 'phaser';
import { ABILITIES, type AbilityId } from '../data/abilities';
import { GAME_HEIGHT, GAME_WIDTH, UI_FONT } from '../utils/constants';
import { uiClick } from './helpers';

const RADIUS = 36;
const GAP = 88;

interface AbilityButton {
  id: AbilityId;
  container: Phaser.GameObjects.Container;
  bg: Phaser.GameObjects.Graphics;
  badge: Phaser.GameObjects.Text;
}

/** Three circular ability buttons in the bottom-right corner. */
export class AbilityBar extends Phaser.GameObjects.Container {
  private readonly buttons: AbilityButton[] = [];
  private readonly tooltip: Phaser.GameObjects.Text;

  constructor(scene: Phaser.Scene, onUse: (id: AbilityId) => void) {
    super(scene, 0, 0);

    const baseX = GAME_WIDTH - ABILITIES.length * GAP - 6;
    const y = GAME_HEIGHT - 62;

    this.tooltip = scene.add
      .text(GAME_WIDTH - 20, y - 62, '', {
        fontFamily: UI_FONT,
        fontSize: '16px',
        color: '#ffffff',
        backgroundColor: '#171a21ee',
        padding: { x: 10, y: 6 }
      })
      .setOrigin(1, 0.5)
      .setVisible(false);

    ABILITIES.forEach((def, i) => {
      const x = baseX + i * GAP + RADIUS;
      const container = scene.add.container(x, y);

      const bg = scene.add.graphics();
      container.add(bg);
      container.add(scene.add.image(0, 0, def.icon).setScale(1.15));

      const badge = scene.add
        .text(RADIUS - 12, RADIUS - 14, `${def.uses}`, {
          fontFamily: UI_FONT,
          fontSize: '16px',
          color: '#ffffff',
          fontStyle: 'bold',
          backgroundColor: '#2d5fb0',
          padding: { x: 6, y: 2 }
        })
        .setOrigin(0.5);
      container.add(badge);

      container.setInteractive(
        new Phaser.Geom.Circle(0, 0, RADIUS),
        Phaser.Geom.Circle.Contains
      );
      if (container.input) container.input.cursor = 'pointer';
      container.on('pointerdown', uiClick(() => onUse(def.id)));
      container.on('pointerover', () => {
        this.tooltip.setText(`${def.name} — ${def.description}`).setVisible(true);
      });
      container.on('pointerout', () => this.tooltip.setVisible(false));

      this.buttons.push({ id: def.id, container, bg, badge });
      this.add(container);
    });

    this.add(this.tooltip);
    scene.add.existing(this);
  }

  refresh(uses: Record<AbilityId, number>, pending: AbilityId | null): void {
    for (const btn of this.buttons) {
      const remaining = uses[btn.id];
      btn.badge.setText(`${remaining}`);
      btn.container.setAlpha(remaining > 0 ? 1 : 0.4);
      btn.bg.clear();
      btn.bg.fillStyle(0x171a21, 0.92);
      btn.bg.fillCircle(0, 0, RADIUS);
      btn.bg.lineStyle(3, pending === btn.id ? 0xffd23f : 0x2d5fb0, 1);
      btn.bg.strokeCircle(0, 0, RADIUS);
    }
  }
}
