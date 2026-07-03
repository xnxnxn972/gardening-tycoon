import Phaser from 'phaser';

export const PANEL_FILL = 0x171a21;
export const PANEL_BORDER = 0x2c3140;

export function drawPanel(
  g: Phaser.GameObjects.Graphics,
  x: number,
  y: number,
  w: number,
  h: number,
  border: number = PANEL_BORDER,
  fillAlpha = 0.88,
  radius = 12
): void {
  g.fillStyle(PANEL_FILL, fillAlpha);
  g.fillRoundedRect(x, y, w, h, radius);
  g.lineStyle(2.5, border, 1);
  g.strokeRoundedRect(x, y, w, h, radius);
}

export type PointerHandler = (
  pointer: Phaser.Input.Pointer,
  localX: number,
  localY: number,
  event: Phaser.Types.Input.EventData
) => void;

/** Wraps a click handler so UI clicks never fall through to the battlefield. */
export function uiClick(handler: () => void): PointerHandler {
  return (_p, _lx, _ly, event) => {
    event.stopPropagation();
    handler();
  };
}
