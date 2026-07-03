export type SfxKey =
  | 'shoot'
  | 'magic'
  | 'smash'
  | 'enemy-death'
  | 'wave-start'
  | 'build'
  | 'upgrade'
  | 'sell'
  | 'ability'
  | 'life-lost'
  | 'victory'
  | 'defeat';

/**
 * Placeholder sound hook. Wire real audio later by loading files in
 * PreloadScene and playing them here, e.g. scene.sound.play(key).
 * Every gameplay event already calls this with a stable key.
 */
export function playSfx(_key: SfxKey): void {
  // no-op in the MVP
}
