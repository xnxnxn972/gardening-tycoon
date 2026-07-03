# Brick Tower Defenders

A kid-friendly, toy-brick castle tower defense MVP. Client-only web app — no backend, no login. Built with **Phaser 3 + TypeScript + Vite**.

## Run it

```bash
npm install
npm run dev      # open the printed localhost URL
```

Other scripts: `npm run build` (production build to `dist/`), `npm run preview`, `npm run typecheck`.

## The game

Defend the **Golden Brick Core** in the castle room. Enemies enter through the left gate and follow the stone path. You start with **500 gold / 20 lives / 10 waves**.

- Click a **stone pad** to open the build menu, or click a **tower card** (bottom-left) and then a pad.
- Click a built tower to see range, **upgrade** (Lv 2: +40% damage, +10% range, 10% faster) or **sell** (70% refund).
- **Abilities** (bottom-right): Fireball (click to aim, area damage), Freeze (slow everything 3s), Repair (+3 lives, revives knights). Limited uses per battle.
- Press **Start Wave** when ready; between waves you can build freely.

| Tower | Name | Cost | Notes |
|---|---|---|---|
| SHOOTER | Crossbow Tower | 120 | Fast single-target, hits flying |
| SQUAD | Knight Barracks | 160 | 2 knights block ground enemies, respawn in 6s |
| POWER | Wizard Tower | 180 | Magic ignores armor, slows 25% |
| SMASH | Catapult Tower | 220 | Splash damage, ground only |

Enemies: Goblin, Skeleton, Shield Knight (50% physical resist), Bat (flying — ignores knights, immune to catapults), Ogre mini-boss (wave 10).

## Architecture

```
src/main.ts                  entry — creates the Phaser game
src/game/config.ts           Phaser config (1600x900, FIT scaling)
src/game/scenes/             Boot → Preload → Battle + UI (parallel scenes)
src/game/systems/            PathSystem, WaveSystem, EconomySystem, CombatSystem
src/game/entities/           Enemy, Tower, Projectile, SquadUnit
src/game/data/               towers, enemies, waves, abilities, levelCastle
src/game/ui/                 Hud, TowerCards, BuildMenu, TowerInfoPanel, AbilityBar
src/game/gfx/placeholders.ts all placeholder textures, generated at boot
```

Everything gameplay-tunable lives in `src/game/data/` — towers, enemies, waves, path, build slots. A new theme (space / pirate / dino / bedroom) is a new `LevelData` file plus a background generator; the scenes and systems are theme-agnostic.

**BattleScene** owns the simulation (enemies, towers, projectiles, knights, game state); **UIScene** renders on top of it, polls its state each frame, and calls its methods (`buildTower`, `startWave`, `castFireball`, …). Scene restart = new game.

## Replacing the placeholder art

Every sprite has a stable texture key (`enemy_goblin`, `tower_shooter`, `core`, `proj_arrow`, … full list at the top of [placeholders.ts](src/game/gfx/placeholders.ts)). Drop PNGs into `public/assets/` and load them in `PreloadScene.preload()` under the same keys — loaded textures win, the generator skips them, and no other code changes.

Sound is stubbed the same way: every gameplay event calls `playSfx('...')` in [sfx.ts](src/game/utils/sfx.ts); wire real audio there.
