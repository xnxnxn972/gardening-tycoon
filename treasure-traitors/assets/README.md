# Treasure Traitors — Art assets (sprites)

The game is **data-driven**: maps/layouts live in code ([`js/engine.js`](../js/engine.js)),
and art is swapped here by replacing files. You never need to repaint a whole-board
PNG — each island and ship is its own sprite, placed by the game.

## What's here
```
assets/
├── sprites.js                 # manifest: art id -> file path (edit to point at new art)
├── _generate-placeholders.mjs # regenerates the placeholder sprites below
├── islands/  *.svg            # one per island art id (skull-rock, rum-bay, …)
└── ships/    *.svg            # one per player color (red, blue, green, yellow, purple, orange)
```
The files in `islands/` and `ships/` are **placeholders** (simple emoji-on-sand and
tinted vector ships). Replace them with real art to beautify the game.

## How replacing works
1. Make your art (see below), matching the existing **filename** for that slot —
   e.g. overwrite `islands/skull-rock.svg`.
2. If your file is a **PNG** instead of SVG, drop it in (e.g. `islands/skull-rock.png`)
   and update that one line in [`sprites.js`](./sprites.js) to point at the `.png`.
3. Reload the host screen. Missing/typo'd files fall back to the built-in emoji art,
   and you can disable sprites entirely with `SPRITES_ENABLED = false` in `sprites.js`.

The game draws the **treasure count** and the **ship name label** on top of the
sprites, so your art only needs the island/vessel itself.

## Specs
| Sprite | Required size | Notes |
|---|---|---|
| Island | **512 × 512 px**, **transparent** | Square canvas. Island **centered**, occupying ~the middle 70%, with transparent padding all around. Keep the **bottom ~20% clear** — the game draws the treasure count + name label there. |
| Ship   | ~**256 × 280 px**, transparent | Vessel facing forward; centered; no name text (the game adds it). |

- **TRANSPARENCY IS REQUIRED.** Export a PNG-24 with an alpha channel (or SVG).
  A flattened/white background will show up as an ugly white box on the sea — the
  game displays the file exactly as given and cannot strip a baked-in background.
  Verify by viewing the PNG over a dark background or the editor's checkerboard.
  Quick fix if needed: [remove.bg](https://remove.bg) or [Photopea](https://photopea.com).
- **Style:** keep a consistent angle / lighting / scale across all islands so the
  board looks cohesive (top-down ¾ "diorama" view works well). All islands are the
  same 512×512 box, so matching internal scale keeps them visually even.

## Ways to create the art
1. **AI image generators** (fastest): Midjourney / DALL·E / Leonardo / Stable Diffusion.
   Example prompt:
   > "cute cartoon pirate island with a giant skull-shaped rock, palm trees, sandy
   > beach, top-down 3/4 diorama view, vibrant mobile game asset, **transparent
   > background**, soft shadows, no text"
   Then export/cut out with a transparent background (most tools can, or use remove.bg).
   Do one prompt per island/ship, keeping the style words identical for consistency.
2. **Free asset packs:** e.g. [Kenney.nl](https://kenney.nl) (Pirate Pack), itch.io —
   drop in matching island/ship images and rename to the slot filenames.
3. **Commission an illustrator** with the spec table above and the art-id list.

## Art ids (island slots)
`skull-rock, rum-bay, gold-cove, cannon-cay, shark-reef, monkey-isle,
shipwreck-point, treasure-atoll`

## Ship slots (by color index)
`0 red, 1 blue, 2 green, 3 yellow, 4 purple, 5 orange`

## Adding a new map later
Add islands to a new map in `engine.js` with `x`, `y`, `neighbors`, and an `art` id.
Reuse existing art ids, or add a new id + file + a line in `sprites.js`. No board
repaint required.
