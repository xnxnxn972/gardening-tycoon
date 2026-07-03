import Phaser from 'phaser';
import { MAX_LIVES, UI_FONT } from '../utils/constants';
import { drawPanel } from './helpers';

const TEXT_STYLE: Phaser.Types.GameObjects.Text.TextStyle = {
  fontFamily: UI_FONT,
  fontSize: '24px',
  color: '#ffffff',
  fontStyle: 'bold'
};

/** Top HUD: gold, lives, wave counter, enemies remaining. */
export class Hud extends Phaser.GameObjects.Container {
  private readonly goldText: Phaser.GameObjects.Text;
  private readonly livesText: Phaser.GameObjects.Text;
  private readonly waveText: Phaser.GameObjects.Text;
  private readonly enemiesText: Phaser.GameObjects.Text;

  constructor(scene: Phaser.Scene) {
    super(scene, 0, 0);

    const g = scene.add.graphics();
    drawPanel(g, 20, 16, 200, 54);
    drawPanel(g, 232, 16, 180, 54);
    drawPanel(g, 424, 16, 250, 54);
    drawPanel(g, 686, 16, 170, 54);
    this.add(g);

    this.add(scene.add.image(48, 43, 'icon_coin'));
    this.goldText = scene.add.text(70, 43, '', { ...TEXT_STYLE, color: '#ffc93a' }).setOrigin(0, 0.5);
    this.add(this.goldText);

    this.add(scene.add.image(260, 43, 'icon_heart'));
    this.livesText = scene.add.text(282, 43, '', TEXT_STYLE).setOrigin(0, 0.5);
    this.add(this.livesText);

    this.waveText = scene.add.text(549, 43, '', { ...TEXT_STYLE, fontSize: '22px' }).setOrigin(0.5);
    this.add(this.waveText);

    this.add(scene.add.image(714, 43, 'icon_skull'));
    this.enemiesText = scene.add.text(736, 43, '', TEXT_STYLE).setOrigin(0, 0.5);
    this.add(this.enemiesText);

    scene.add.existing(this);
  }

  refresh(gold: number, lives: number, wave: number, totalWaves: number, enemies: number): void {
    this.goldText.setText(gold.toLocaleString('en-US'));
    this.livesText.setText(`${lives} / ${MAX_LIVES}`);
    this.waveText.setText(`WAVE ${wave} / ${totalWaves}`);
    this.enemiesText.setText(`${enemies}`);
  }
}
