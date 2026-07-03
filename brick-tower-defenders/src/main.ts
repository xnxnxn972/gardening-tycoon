import Phaser from 'phaser';
import { gameConfig } from './game/config';

const game = new Phaser.Game(gameConfig);

// handy for debugging from the browser console
(window as unknown as { game: Phaser.Game }).game = game;
