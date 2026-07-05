# Asset replacement checklist

Every sprite in the game is a generated placeholder registered under a **stable texture key**. To replace one: export a transparent PNG, drop it in `public/assets/`, and load it in `PreloadScene.preload()` under the same key. A loaded texture always wins — the placeholder generator skips keys that already exist. No other code changes.

```ts
// src/game/scenes/PreloadScene.ts → preload()
this.load.image('enemy_goblin', 'assets/enemy_goblin.png');
```

**Export at the exact pixel sizes below** — sprites render at their natural texture size (no scaling in code except where noted). If you'd rather work in 512×512 masters like Treasure Traitors, say so and we'll add a display-size config per sprite instead.

All sprites are drawn centered (origin 0.5) unless noted. The path/floor/walls are part of the background image, not separate sprites.

## Enemies (front-facing, no flipping in code; HP bar is drawn by code above the sprite)

| Key | Size | What it is |
|---|---|---|
| `enemy_goblin` | 32×32 | Goblin — small, green, fast |
| `enemy_skeleton` | 32×34 | Skeleton — bone white |
| `enemy_shieldknight` | 38×38 | Shield Knight — armored, carries a shield |
| `enemy_bat` | 36×26 | Bat — flying (code adds a bobbing motion + drop shadow) |
| `enemy_ogre` | 64×64 | Ogre mini-boss — big, red, horns/tusks |

## Towers (base at bottom of canvas; drawn standing on the slot pad)

| Key | Size | What it is |
|---|---|---|
| `tower_shooter` | 68×86 | Crossbow Tower (blue accent) |
| `tower_squad` | 68×86 | Knight Barracks (green accent) |
| `tower_power` | 68×86 | Wizard Tower (purple accent) |
| `tower_smash` | 68×86 | Catapult Tower (red accent) |
| `knight` | 28×32 | Barracks knight unit standing on the path |
| `slot_pad` | 84×84 | Circular stone build pad — **currently hidden** (`slotOpacity: 0` in levelCastle.ts) because the pads are painted into `bg_castle.png`; only needed for maps without painted pads |
| `core` | 130×122 | The Golden Brick Core (glow baked in is fine; code adds a pulse) |

These tower textures are reused in the UI: tower cards show them at 0.82×, the build menu at 0.62× — so keep silhouettes readable when small.

## Projectiles

| Key | Size | Notes |
|---|---|---|
| `proj_arrow` | 20×7 | Must point **right** (+x); code rotates it toward the flight direction |
| `proj_bolt` | 16×16 | Magic bolt, radially symmetric |
| `proj_rock` | 16×16 | Catapult rock; code spins it in flight |

## FX + UI icons

| Key | Size | Notes |
|---|---|---|
| `fx_glow` | 64×64 | Soft **white** radial glow — tinted at runtime for hits/explosions; keep it grayscale/white |
| `icon_coin` | 28×28 | Gold cost / HUD gold |
| `icon_heart` | 28×28 | HUD lives |
| `icon_skull` | 28×28 | HUD enemies-remaining |
| `icon_fireball` | 28×28 | Fireball ability button |
| `icon_freeze` | 28×28 | Freeze ability button |
| `icon_heal` | 28×28 | Repair ability button |

## Background

| Key | Size | Notes |
|---|---|---|
| `bg_castle` | 1600×900 | The whole battlefield: floor, castle wall, banners, torches, decorations, **and the path**. Origin is top-left. |

The path in your painting must follow the waypoints in [levelCastle.ts](src/game/data/levelCastle.ts) (path width ~64 px), the entrance is on the left at y≈420, and the core sits at (1520, 450). Keep the 8 build-slot positions reasonably clear — the slot pads are drawn on top. The top ~80 px is the castle wall; the HUD panels overlay it.

Panels, buttons, cards, health bars, and range circles are drawn in code (`src/game/ui/`), not textures — restyling those means tweaking the drawing code, which is a separate pass.
