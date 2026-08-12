"""WHAT ARE THE STALE-BAR MARKETS, REALLY?

leak_proof.py refuted my first guess. I expected stale-bar markets to have moved on by T-3d (a
look-ahead leak). They had not -- almost none of them has ANY bar after T-3d. They are markets that
stopped trading and never traded again before resolving.

So the question becomes: does the surface's edge live in markets that had no order flow? If yes, the
error is not look-ahead, it is TRADABILITY -- the measurement counted markets in which no counterparty
existed, and those markets carried the edge. That is a different bug with a different fix, and it is
worth getting right before writing any of it down.

Splits the favbuy and geobuy cells by whether the market traded again at all after T-3d.
"""
import json, os, sys, time, urllib.request, urllib.parse, datetime

GAMMA = "https://gamma-api.polymarket.com"; UA = {"User-Agent": "Mozilla/5.0"}
RES = r"C:\Users\yaniv\OneDrive\Projects\Polymarket_Research"
PAGES = int(sys.argv[1]) if len(sys.argv) > 1 else 12
TAGS = {"politics": "2", "geopolitics": "100265", "pop-culture": "596", "tweets-markets": "972",
        "elections": "144", "world": "101970", "economy": "100328", "tech": "1401", "business": "107"}
EXCLUDE = {"crypto", "sports", "soccer", "fifa-world-cup", "basketball", "tennis", "nfl", "nba",
           "mlb", "nhl", "baseball", "football", "games"}


def get(u, tries=3):
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=30) as r:
                time.sleep(0.02); return json.load(r)
        except Exception:
            time.sleep(0.25 * (i + 1))
    return None


def fnum(x):
    try: return float(x)
    except Exception: return None


H = {k: [(int(t), float(p)) for t, p in v] for k, v in
     json.load(open(os.path.join(RES, "daily_hist_cache.json"))).items()}

print(f"enumerating {PAGES} pages/tag...")
rows = []; seen = set()
for cat, tid in TAGS.items():
    for off in range(0, PAGES * 100, 100):
        page = get(f"{GAMMA}/events?" + urllib.parse.urlencode(
            {"tag_id": tid, "closed": "true", "limit": "100", "offset": str(off),
             "order": "startDate", "ascending": "false"}))
        if not page: break
        for e in page:
            if {t.get("slug") for t in (e.get("tags") or [])} & EXCLUDE: continue
            for m in (e.get("markets") or []):
                mid = m.get("id")
                if not mid or mid in seen: continue
                try: tk = json.loads(m.get("clobTokenIds") or "[]")
                except Exception: continue
                if not tk: continue
                op = m.get("outcomePrices")
                try: rr = json.loads(op) if isinstance(op, str) else op
                except Exception: rr = None
                y = fnum(rr[0]) if (rr and len(rr) >= 1) else None
                if y is None or 0.02 < y < 0.98: continue
                ed = (m.get("endDate") or e.get("endDate") or "")[:19]
                try: en = datetime.datetime.fromisoformat(ed.replace("Z", "")).replace(tzinfo=datetime.timezone.utc)
                except Exception: continue
                seen.add(mid)
                ts = int(en.timestamp()) - 3 * 86400
                s = H.get(str(tk[0]))
                if not s: continue
                prev = pt = None; nafter = 0
                for t, p in s:
                    if t <= ts: prev, pt = p, t
                    else: nafter += 1
                if prev is None: continue
                rows.append({"won": 1 if y > 0.5 else 0, "p": prev, "age": (ts - pt) / 86400.0,
                             "after": nafter, "nbars": len(s), "cat": cat,
                             "vol": fnum(m.get("volumeNum")) or fnum(m.get("volume")) or 0.0})
print(f"  {len(rows)} resolved markets\n")


def rep(lbl, sel):
    if len(sel) < 25:
        print(f"    {lbl:44} n={len(sel):5d}  (thin)"); return
    n = len(sel)
    m = sum(r["won"] - r["p"] for r in sel) / n
    sd = (sum((r["won"] - r["p"] - m) ** 2 for r in sel) / (n - 1)) ** 0.5
    z = m / (sd / n ** 0.5) if sd else 0
    wr = sum(r["won"] for r in sel) / n
    mp = sum(r["p"] for r in sel) / n
    mv = sorted(r["vol"] for r in sel)[n // 2]
    mb = sum(r["nbars"] for r in sel) / n
    print(f"    {lbl:44} n={n:5d}  gap {100*m:+6.2f}pt z={z:+5.1f} | price {mp:.3f} won {100*wr:5.1f}% "
          f"| median vol ${mv:>9,.0f} | {mb:5.1f} bars of history")


for lbl, base in (("FAVBUY CELL  p in [0.80,0.90)", [r for r in rows if 0.80 <= r["p"] < 0.90]),
                  ("GEOBUY CELL  geopolitics p in [0.35,0.90)",
                   [r for r in rows if r["cat"] == "geopolitics" and 0.35 <= r["p"] < 0.90])):
    print("=" * 118)
    print(lbl)
    print("=" * 118)
    rep("ALL (the original measurement)", base)
    rep("  A. traded again after T-3d  (a live book)", [r for r in base if r["after"] > 0])
    rep("  B. NEVER traded again       (a fossil price)", [r for r in base if r["after"] == 0])
    print()
    rep("  B1. fossil, last trade <1d before T-3d", [r for r in base if r["after"] == 0 and r["age"] < 1])
    rep("  B2. fossil, last trade >1d before T-3d", [r for r in base if r["after"] == 0 and r["age"] >= 1])
    print()
