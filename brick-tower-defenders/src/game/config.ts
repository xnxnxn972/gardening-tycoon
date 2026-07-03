import Phaser from 'phaser';
import BattleScene from './scenes/BattleScene';
import BootScene from './scenes/BootScene';
import PreloadScene from './scenes/PreloadScene';
import UIScene from './scenes/UIScene';
import { GAME_HEIGHT, GAME_WIDTH } from './utils/constants';

export const gameConfig: Phaser.Types.Core.GameConfig = {
  type: Phaser.AUTO,
  parent: 'app',
  backgroundColor: '#0d0e12',
  width: GAME_WIDTH,
  height: GAME_HEIGHT,
  scale: {
    mode: Phaser.Scale.FIT,
    autoCenter: Phaser.Scale.CENTER_BOTH
  },
  render: {
    antialias: true,
    roundPixels: false
  },
  scene: [BootScene, PreloadScene, BattleScene, UIScene]
};
