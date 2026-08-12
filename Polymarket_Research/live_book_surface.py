"""THE SURFACE, RE-MEASURED ON MARKETS THAT STILL HAD A LIVE BOOK AT ENTRY.

Established by dead_markets.py: splitting each cell by whether the market EVER TRADED AGAIN after the
snapshot separates the edge almost perfectly.

    favbuy cell   live book +3.20pt (z 1.9)   fossil +10.21pt (z 6.8)
    geobuy cell   live book +0.07pt (z 0.0)   fossil +24.98pt (z 14.7)

A market that never trades again is one where the answer became obvious and nobody will pay to close
the last few cents. Its "price" is a fossil, there is no counterparty, and -- decisively -- whether a
market will go quiet is not knowable at entry. The original surface therefore conditioned on
post-entry information, and the edge lived entirely in the part we can neither identify nor trade.

This is the re-measurement that should have been the acceptance test all along. It re-runs the full
band surface restricted to markets with a live book, and settles the two books still being funded:
secondfav (0.35-0.50 x N>=6, our best live performer) and secondfav2 (N>=11, opened this week).

For each cell it reports the edge, the holdout split, and the sample that ACTUALLY supports it.
"""
import json, os, sys, time, urllib.request, urllib.parse, datetime, math

GAMMA = "https://gamma-api.polymarket.com"; UA = {"User-Agent": "Mozilla/5.0"}
RES = r"C:\Users\yaniv\OneDrive\Projects\Polymarket_Research"
PAGES = int(sys.argv[1]) if len(sys.argv) > 1 else 18
TAGS = {"politics": "2", "geopolitics": "100265", "pop-culture": "596", "tweets-markets": "972",
        "elections": "144", "world": "101970", "economy": "100328", "tech": "1401", "business": "107"}
EXCLUDE = {"crypto", "sports", "soccer", "fifa-world-cup", "basketball", "tennis", "nfl", "nba",
           "mlb", "nhl", "baseball", "football", "games"}
BANDS = [(0.03, 0.10), (0.10, 0.20), (0.20, 0.35), (0.35, 0.50), (0.50, 0.65), (0.65, 0.80),
         (0.80, 0.90), (0.90, 0.97)]
EXEC_COST = 0.015


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
            ms = e.get("markets") or []
            for m in ms:
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
                prev = None; nafter = 0
                for t, p in s:
                    if t <= ts: prev = p
                    else: nafter += 1
                if prev is None: continue
                rows.append({"won": 1 if y > 0.5 else 0, "en": en, "p": prev, "after": nafter,
                             "cat": cat, "N": len(ms)})

rows.sort(key=lambda r: r["en"])
SPLIT = rows[len(rows) // 2]["en"]
LIVE = [r for r in rows if r["after"] > 0]
print(f"  {len(rows)} resolved | {len(LIVE)} had a live book at T-3d "
      f"({100*len(LIVE)/len(rows):.0f}%) | holdout {SPLIT:%Y-%m-%d}\n")


def stat(sel):
    n = len(sel)
    if n < 25: return None
    v = [r["won"] - r["p"] for r in sel]
    m = sum(v) / n
    sd = (sum((x - m) ** 2 for x in v) / (n - 1)) ** 0.5
    z = m / (sd / n ** 0.5) if sd else 0.0
    tr = [r["won"] - r["p"] for r in sel if r["en"] < SPLIT]
    te = [r["won"] - r["p"] for r in sel if r["en"] >= SPLIT]
    return m, z, n, (sum(tr) / len(tr) if tr else 0), (sum(te) / len(te) if te else 0), sd


print("=" * 112)
print("BAND SURFACE:  original  vs  live-book-only")
print("=" * 112)
for lo, hi in BANDS:
    a = stat([r for r in rows if lo <= r["p"] < hi])
    b = stat([r for r in LIVE if lo <= r["p"] < hi])
    fa = "n<25" if not a else f"{100*a[0]:+6.2f}pt z{a[1]:+6.1f} n{a[2]:5d}"
    fb = "n<25" if not b else (f"{100*b[0]:+6.2f}pt z{b[1]:+6.1f} n{b[2]:5d} "
                               f"[{100*b[3]:+5.1f}/{100*b[4]:+5.1f}]"
                               + ("  SIGN FLIPS OOS" if (b[3] > 0) != (b[4] > 0) else ""))
    shrink = "" if not (a and b) else f"   edge x{b[0]/a[0]:+.2f}" if abs(a[0]) > 1e-9 else ""
    print(f"  {lo:.2f}-{hi:.2f} | original {fa} | LIVE BOOK {fb}{shrink}")

print("\n" + "=" * 112)
print("THE BOOKS")
print("=" * 112)
CELLS = {
    "favbuy     0.80-0.90 all cats        (RETIRED)": lambda r: 0.80 <= r["p"] < 0.90,
    "geobuy     0.35-0.90 geopolitics     (draining)": lambda r: r["cat"] == "geopolitics" and 0.35 <= r["p"] < 0.90,
    "secondfav  0.35-0.50 x N>=6   (SELL) (funded)": lambda r: 0.35 <= r["p"] < 0.50 and r["N"] >= 6,
    "secondfav2 0.35-0.50 x N>=11  (SELL) (funded)": lambda r: 0.35 <= r["p"] < 0.50 and r["N"] >= 11,
}
for lbl, f in CELLS.items():
    a, b = stat([r for r in rows if f(r)]), stat([r for r in LIVE if f(r)])
    print(f"\n  {lbl}")
    if a: print(f"    original   {100*a[0]:+6.2f}pt  z={a[1]:+6.1f}  n={a[2]:5d}")
    if not b:
        print("    live book  n<25 -- NO MEASUREMENT EXISTS on a tradeable basis"); continue
    m, z, n, mtr, mte, sd = b
    flip = "   SIGN FLIPS OOS" if (mtr > 0) != (mte > 0) else ""
    print(f"    LIVE BOOK  {100*m:+6.2f}pt  z={z:+6.1f}  n={n:5d}  "
          f"TRAIN {100*mtr:+6.2f} / TEST {100*mte:+6.2f}{flip}")
    # a SELL book earns when the gap is negative; a BUY book when it is positive
    sell = "SELL" in lbl
    edge = (-m if sell else m) - EXEC_COST
    print(f"    -> as a {'SELL' if sell else 'BUY'} book, edge net of {100*EXEC_COST:.1f}pt execution: "
          f"{100*edge:+.2f}pt")
    if edge > 0:
        print(f"    -> to confirm at z=2 needs ~{int(math.ceil((2*sd/edge)**2)):,} settled markets "
              f"(cell supplies {n})")
