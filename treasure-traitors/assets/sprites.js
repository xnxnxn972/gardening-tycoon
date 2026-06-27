// sprites.js — art manifest for Treasure Traitors.
//
// This is the single place that maps the game's stable "art ids" to image
// files. Layout/maps stay data-driven (see engine.js `art` fields); art is
// swapped here. To beautify the game, replace the placeholder files in
// assets/islands and assets/ships with your own (PNG or SVG), keeping the
// same filename — OR change the path here to point at a new file.
//
// Set SPRITES_ENABLED = false to fall back to the built-in emoji/vector art.

export const SPRITES_ENABLED = true;

// Island art id (from engine map `art`) -> image file.
export const ISLAND_SPRITES = {
  'skull-rock':      'assets/islands/skull-rock.png',
  'rum-bay':         'assets/islands/rum-bay.png',
  'gold-cove':       'assets/islands/gold-cove.png',
  'cannon-cay':      'assets/islands/cannon-cay.png',
  'shark-reef':      'assets/islands/shark-reef.png',
  'monkey-isle':     'assets/islands/monkey-isle.png',
  'shipwreck-point': 'assets/islands/shipwreck-point.png',
  'treasure-atoll':  'assets/islands/treasure-atoll.png',
};

// Ship art by player color index (0=Red,1=Blue,2=Green,3=Yellow,4=Purple,5=Orange).
// The game still draws the name label + damage marker on top, so the sprite is
// just the vessel art.
export const SHIP_SPRITES = [
  'assets/ships/red.png',
  'assets/ships/blue.png',
  'assets/ships/green.png',
  'assets/ships/yellow.png',
  'assets/ships/purple.png',
  'assets/ships/orange.png',
];
