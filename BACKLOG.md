# Gardening Tycoon — Backlog

Living list of ideas. Tags:
- `[S]` ≈ ½ day or less · `[M]` ≈ 1 day · `[L]` ≈ multi-day
- `★` = high-impact pick

## ✅ Shipped

- 3D isometric Three.js diorama with house, trees, fences, path, flowers
- 3×3 plot grid, click to plant / click to harvest
- 14-stage crop growth with smooth within-stage scaling
- 5 starter crops + 4 unlockable premium crops (strawberry, carrot, pineapple, watermelon)
- Trade-off-triangle crops (cucumber = cheap seeds, lettuce = fast, eggplant = high yield)
- Auto-sell toggle per crop
- Spinach + Lettuce as leafy heads (distinct from stem-based crops)
- Bean teepee trellis with climbing leaves and hanging pods
- Day/night cycle synced to 07:00–19:00 game clock
- Sun arc + moon on opposing arc, sun-color shift at horizon
- Tree canopy reshades through day/night + golden-hour tint
- Floating clouds with game-time drift
- Chicken coop (500c) with 3 chickens that wander 07:00–19:00 and sleep inside otherwise
- Daily egg drop at 07:00 sunrise, sells for 8c
- Decorations (9 items, auto-placed in perimeter slots that don't cover plots)
- Store with 4 tabs (Seeds / Produce / Buildings / Decorations)
- Speed controls (1× / 4× / 20× / 100×) with time-warp accumulator
- Global Supabase leaderboard with 5 tabs (Coins Now / 24h / 7d / 30d / All-time)
- Nickname uniqueness check + recovery code flow for cross-browser play
- GitHub Pages deployment + `git push` workflow

## 🎯 Backlog

### Game mechanics — economy depth
- ★ `[M]` **Customer / Truck Orders** — NPC card appears every few game hours: "Need 4 Radish + 2 Tomato → 🪙85 + XP". Solves "what do I do with surplus produce?"
- ★ `[M]` **XP & Levels** — every plant/harvest/sale grants XP; levels gate items (Lv2 Spinach, Lv4 first decoration, Lv6 plot expansion, Lv8 first animal)
- `[S]` **Daily login reward** — 5–50c per real-day open, 7-day streak bonus
- `[L]` **Processing / recipes** — Jam Pot (Tomato → Sauce), Salad Bar (Spinach + Pepper → Salad). Worth more than sum of inputs
- `[S]` **Plot expansion** — buy 4th column 500c, 5th 1500c, up to 5×5
- `[M]` **Lucky harvest** — ~10% chance of premium-quality crop (2× sell + ⭐ badge); requires inventory model change from int → array
- `[M]` **Weather events** — periodic rain (growth boost), drought (penalty), full moon (small coin bonus)

### Animals (passive income)
- `[M]` **Cow** building → milk at 09:00 daily, sells for ~12c
- `[M]` **Sheep** building → wool every 2 game days
- `[S]` **Bee hive** decoration → small honey trickle

### More crops
- `[S each]` Corn, Sunflower, Cabbage, Blueberries, Mushroom, Garlic — each one a new entry in CROPS + a produce visual
- `[M]` **Seasonal-only crops** — pumpkin in fall, snowpea in winter, etc. Hook into existing season system

### 🎬 Ambient detail / charm
- ★ `[S]` **🏠 Homeowner peeks from front window at 09:00** — small silhouetted figure appears behind one of the front windows, slight head bob, visible ~5 real seconds, fades out. Once per game day. *(User-requested.)*
- `[S]` Birds fly across the sky once in a while (small dark crescents)
- `[S]` Butterflies near the plots during summer daytime
- `[S]` Falling leaves in autumn (small color-shifted petal particles drifting down)
- `[M]` Snow particles in winter + slight white dust on the diorama base
- `[M]` Cat/dog wandering near the house (state machine like the chickens)
- `[S]` Decoration tooltips on hover (name + cost paid)

### UX polish
- `[S]` Show "rank #X of Y" below the top 20 on each leaderboard tab
- `[S]` "Next harvest in X" quick-summary in HUD (the soonest-ready plot)
- `[S]` Confirm dialog for purchases over 500c
- `[M]` Achievements panel (first crop sold, 1000c earned, first unlock, etc.)
- `[S]` Hover tooltip for the coop showing time-to-next-egg

### 🔁 Long-haul
- `[L]` **Cross-device sync via Supabase Auth** — magic-link login; cloud-save the full state blob per user
- `[L]` **Visit other gardens** — read-only view, pick from leaderboard → render their state
- `[L]` **Gift produce to other players** — one-time drops to a chosen leaderboard name
- `[XL]` **Server-authoritative game** — anti-cheat for real. Major rewrite (months)
- `[M]` **Mobile-optimized layout** — touch controls, responsive HUD

## Notes / design rules of thumb
- Cozy / single-player feel — no stamina, no IAP, no time-gated paywalls
- New mechanics should compose with existing ones (e.g. orders work with auto-sell, weather works with crops)
- Always keep `index.html` self-contained; no build step
- Anything that talks to Supabase must degrade gracefully when offline
