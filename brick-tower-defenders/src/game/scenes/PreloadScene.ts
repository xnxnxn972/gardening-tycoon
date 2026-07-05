import Phaser from 'phaser';
import { LEVEL_CASTLE } from '../data/levelCastle';
import { makeCastleBackground, makePlaceholderTextures } from '../gfx/placeholders';
import { GAME_HEIGHT, GAME_WIDTH, UI_FONT } from '../utils/constants';

export default class PreloadScene extends Phaser.Scene {
  constructor() {
    super('Preload');
  }

  preload(): void {
    // Real art, loaded under the same texture keys the placeholder generator
    // registers. Any key loaded here wins because generators skip existing
    // textures. See ASSETS.md for the full checklist and sizes.
    this.load.image('bg_castle', 'assets/bg_castle.png');
    this.load.image('tower_shooter', 'assets/tower_shooter.png');
    this.load.image('tower_squad', 'assets/tower_squad.png');
    this.load.image('tower_power', 'assets/tower_power.png');
    this.load.image('tower_smash', 'assets/tower_smash.png');
    this.load.image('enemy_goblin', 'assets/enemy_goblin.png');
    this.load.image('core', 'assets/core.png');
  }

  create(): void {
    const label = this.add
      .text(GAME_WIDTH / 2, GAME_HEIGHT / 2, 'Building the castle…', {
        fontFamily: UI_FONT,
        fontSize: '28px',
        color: '#ffffff'
      })
      .setOrigin(0.5);

    makePlaceholderTextures(this);
    makeCastleBackground(this, LEVEL_CASTLE);

    label.destroy();
    this.scene.start('Battle');
  }
}
