"""IS THERE ANY SALVAGEABLE SUB-CELL INSIDE FAVBUY OR GEOBUY?

LEG-LEVEL CAVEAT (added 2026-08-13). The z-scores and any months-to-verdict figures below are
computed PER LEG. Legs of one negRisk event share a single outcome draw and are ONE observation, so
z is inflated by roughly sqrt(legs per cluster) and timelines are optimistic. See
clustered_surface.py for the event-clustered version of the same measurements. The DIRECTIONAL
conclusions in this script were checked against the clustered surface and are unchanged; only the
confidence and the timelines move.

On the fresh/live-book basis both books are positive but tiny: favbuy +2.60pt gross / +1.10pt net,
geobuy +1.83pt / +0.33pt. Too small to confirm in 292 and 12,929 months respectively.

The obvious hope is that a SUB-CELL carries a much bigger edge. That hope is arithmetically coherent,
which is why it deserves a test rather than an opinion:

    months_to_verdict  =  (2*sigma/net_edge)^2 / supply_per_month

Narrowing cuts supply linearly but the edge enters SQUARED, so doubling the edge at half the supply
is a 2x net improvement. Sub-selection CAN rescue a book -- but only if the sub-cell's edge is
genuinely much larger, not merely positive.

Working backwards from a 12-month verdict at favbuy's supply tells us what we are hunting: with
sigma ~= 0.357 and ~12.6 markets/month in the whole cell, a sub-cell holding a fraction s of supply
needs net edge >= 2*sigma / sqrt(12 * 12.6 * s). At s=1 that is 5.2pt; at s=0.25 it is 10.4pt.
So nothing below ~5pt net can help, and we measured 1.10pt.

This scans every conditioning variable we have -- category, field size, price sub-band, market
volume, question family, market lifetime -- and reports any sub-cell clearing the bar, with:
  - a TRAIN/TEST holdout (same-sign required),
  - honest MULTIPLE-COMPARISONS accounting: scanning k cells at z>=2 yields ~0.05k false positives
    by construction, so the count of survivors is compared against that expectation.

A survivor that is not clearly ahead of the false-positive count is not a discovery, and after the
fossil episode the default has to be that it is noise.
"""
import json, os, sys, time, math, urllib.request, urllib.parse, datetime, collections

GAMMA = "https://gamma-api.polymarket.com"; UA = {"User-Agent": "Mozilla/5.0"}
RESD = r"C:\Users\yaniv\OneDrive\Projects\Polymarket_Research"
PAGES = int(sys.argv[1]) if len(sys.argv) > 1 else 18
TAGS = {"politics": "2", "geopolitics": "100265", "pop-culture": "596", "tweets-markets": "972",
        "elections": "144", "world": "101970", "economy": "100328", "tech": "1401", "business": "107"}
EXCLUDE = {"crypto", "sports", "soccer", "fifa-world-cup", "basketball", "tennis", "nfl", "nba",
           "mlb", "nhl", "baseball", "football", "games"}
# fee = rate * p * (1-p) per share; world and geopolitics are fee-free, which materially changes
# the bar a cell has to clear. Half-spread measured live at ~0.95pt.
FEER = {"politics": .04, "elections": .04, "tech": .04, "tweets-markets": .04,
        "pop-culture": .05, "economy": .05, "business": .05, "world": .0, "geopolitics": .0}
HALF_SPREAD = 0.0095
TARGET_MONTHS = 12.0


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
     json.load(open(os.path.join(RESD, "daily_hist_cache.json"))).items()}
print(f"enumerating {PAGES} pages/tag (fresh-at-entry basis only)...")
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
                try:
                    en = datetime.datetime.fromisoformat(
                        ((m.get("endDate") or e.get("endDate") or "")[:19]).replace("Z", "")
                    ).replace(tzinfo=datetime.timezone.utc)
                except Exception:
                    continue
                seen.add(mid)
                ts = int(en.timestamp()) - 3 * 86400
                s = H.get(str(tk[0]))
                if not s: continue
                prev = pt = None
                for t, p in s:
                    if t <= ts: prev, pt = p, t
                    else: break
                if prev is None or (ts - pt) >= 86400: continue     # FRESH ONLY
                life = (ts - s[0][0]) / 86400.0                     # days of price history at entry
                rows.append({"won": 1 if y > 0.5 else 0, "en": en, "p": prev, "cat": cat,
                             "N": len(ms), "life": life,
                             "vol": fnum(m.get("volumeNum")) or fnum(m.get("volume")) or 0.0})

rows.sort(key=lambda r: r["en"])
months = ((rows[-1]["en"] - rows[0]["en"]).days or 1) / 30.44
SPLIT = rows[len(rows) // 2]["en"]
print(f"  {len(rows)} fresh markets over {months:.1f} months | holdout {SPLIT:%Y-%m-%d}\n")


def evaluate(sel, minn=30):
    n = len(sel)
    if n < minn: return None
    v = [r["won"] - r["p"] for r in sel]
    m = sum(v) / n
    sd = (sum((x - m) ** 2 for x in v) / (n - 1)) ** 0.5
    z = m / (sd / n ** 0.5) if sd else 0.0
    tr = [r["won"] - r["p"] for r in sel if r["en"] < SPLIT]
    te = [r["won"] - r["p"] for r in sel if r["en"] >= SPLIT]
    mtr = sum(tr) / len(tr) if tr else 0.0
    mte = sum(te) / len(te) if te else 0.0
    exec_c = HALF_SPREAD + sum(FEER.get(r["cat"], .04) * r["p"] * (1 - r["p"]) for r in sel) / n
    net = m - exec_c
    sup = n / months
    need = ((2 * sd / net) ** 2) if net > 0 else None
    mo = (need / sup) if need else None
    return {"gap": m, "z": z, "n": n, "sd": sd, "net": net, "sup": sup, "mo": mo,
            "tr": mtr, "te": mte, "exec": exec_c}


def scan(title, base, extra_cuts=()):
    print("=" * 118)
    print(title)
    print("=" * 118)
    whole = evaluate(base)
    if whole:
        print(f"  whole cell: gap {100*whole['gap']:+.2f}pt  net {100*whole['net']:+.2f}pt  "
              f"n={whole['n']}  supply {whole['sup']:.1f}/mo  -> "
              + (f"{whole['mo']:.0f} months" if whole['mo'] else "never"))
        need_edge = 2 * whole["sd"] / math.sqrt(TARGET_MONTHS * whole["sup"])
        print(f"  to reach a {TARGET_MONTHS:.0f}-month verdict at FULL supply a sub-cell needs "
              f"net >= {100*need_edge:.2f}pt; at 1/4 supply, {100*need_edge*2:.2f}pt\n")

    cuts = []
    for c in sorted({r["cat"] for r in base}):
        cuts.append((f"cat = {c}", [r for r in base if r["cat"] == c]))
    cuts.append(("fee-free cats (world/geo)", [r for r in base if FEER.get(r["cat"], .04) == 0]))
    cuts.append(("fee-paying cats", [r for r in base if FEER.get(r["cat"], .04) > 0]))
    for lo, hi in ((1, 2), (2, 6), (6, 11), (11, 41), (41, 10**6)):
        cuts.append((f"field size N {lo}-{hi-1}", [r for r in base if lo <= r["N"] < hi]))
    vs = sorted(r["vol"] for r in base)
    for i, lbl in enumerate(("volume Q1", "volume Q2", "volume Q3", "volume Q4")):
        lo = vs[int(i * len(vs) / 4)]; hi = vs[min(int((i + 1) * len(vs) / 4), len(vs) - 1)]
        cuts.append((f"{lbl} (${lo:,.0f}-${hi:,.0f})", [r for r in base if lo <= r["vol"] <= hi]))
    for lo, hi in ((0, 7), (7, 30), (30, 90), (90, 10**6)):
        cuts.append((f"market age at entry {lo}-{hi}d", [r for r in base if lo <= r["life"] < hi]))
    cuts.extend(extra_cuts)

    tested = 0; hits = []
    for lbl, sel in cuts:
        e = evaluate(sel)
        if not e: continue
        tested += 1
        same_sign = (e["tr"] > 0) == (e["te"] > 0)
        ok = e["mo"] is not None and e["mo"] <= TARGET_MONTHS and same_sign and e["z"] >= 2
        flag = "  <== CLEARS THE BAR" if ok else ""
        if ok: hits.append(lbl)
        print(f"  {lbl:34} n={e['n']:5d} gap {100*e['gap']:+6.2f}pt z{e['z']:+5.1f} "
              f"net {100*e['net']:+6.2f}pt sup {e['sup']:5.1f}/mo "
              + (f"{e['mo']:8.0f} mo" if e['mo'] else "   never") +
              f"  [{100*e['tr']:+5.1f}/{100*e['te']:+5.1f}]{flag}")
    print(f"\n  scanned {tested} sub-cells. At z>=2, ~{0.05*tested:.1f} would clear by chance alone.")
    print(f"  cells clearing the bar: {len(hits)}  {hits if hits else ''}")
    if hits and len(hits) <= 0.05 * tested + 1:
        print("  -> NOT a discovery: the survivor count is within the false-positive expectation.")
    print()


FAV = [r for r in rows if 0.80 <= r["p"] < 0.90]
GEO = [r for r in rows if r["cat"] == "geopolitics" and 0.35 <= r["p"] < 0.90]
scan("FAVBUY CELL  p in [0.80,0.90)  -- BUY YES", FAV,
     extra_cuts=[(f"sub-band {lo:.3f}-{hi:.3f}", [r for r in FAV if lo <= r["p"] < hi])
                 for lo, hi in ((.80, .825), (.825, .85), (.85, .875), (.875, .90))])
scan("GEOBUY CELL  geopolitics p in [0.35,0.90)  -- BUY YES (fee-free)", GEO,
     extra_cuts=[(f"sub-band {lo:.2f}-{hi:.2f}", [r for r in GEO if lo <= r["p"] < hi])
                 for lo, hi in ((.35, .50), (.50, .65), (.65, .80), (.80, .90))])

print("=" * 118)
print("THE EXECUTION LEVER -- the one input that is ours to change")
print("=" * 118)
w = evaluate(FAV)
print(f"  favbuy gross edge {100*w['gap']:+.2f}pt; we hand {100*w['exec']:.2f}pt to spread+fee "
      f"({100*w['exec']/w['gap']:.0f}% of it).")
for lbl, ex in (("take the ask (today)", w["exec"]),
                ("post the bid, pay fee only", w["exec"] - HALF_SPREAD),
                ("post the bid AND capture half-spread", w["exec"] - 2 * HALF_SPREAD)):
    net = w["gap"] - ex
    mo = ((2 * w["sd"] / net) ** 2) / w["sup"] if net > 0 else None
    print(f"    {lbl:38} net {100*net:+5.2f}pt -> "
          + (f"{mo:,.0f} months to verdict" if mo else "never"))
print("  (posting rather than taking introduces fill risk and adverse selection on the fills it does")
print("   get -- measured at ~1.3pt earlier -- which would consume most of the gain.)")
