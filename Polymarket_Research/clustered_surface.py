"""THE BAND SURFACE, RE-MEASURED WITH EVENT-CLUSTERED INFERENCE.

Every band number this project has quoted -- live_book_surface.py, forward_projection.py,
remeasure_bands.py, slice_sweep.py, numfam_split.py -- used a PER-LEG z-score. In a negRisk event
with eight legs in one band, those eight legs share one outcome draw and are ONE observation, not
eight. The z's are therefore inflated by roughly sqrt(legs per cluster), and every downstream
quantity built on them -- "needs 43 settled markets", "4 months to verdict" -- is optimistic in the
same direction.

This re-runs the whole surface on the established tradeable basis (fresh price at entry, i.e. the
market still had a live book) and reports:
  - the point estimate, unchanged
  - the LEG-LEVEL z, so the size of the old error is visible
  - an EVENT-CLUSTERED bootstrap CI, which is the honest one
  - a power calculation in CLUSTER units: sigma is the SD of cluster means, the sample is clusters
    per month, so "months to verdict" finally counts independent observations

Sign convention: gap = won - p. A POSITIVE gap means YES is underpriced (buy YES); a NEGATIVE gap
means YES is overpriced, so the tradeable side is NO. Edges are reported for whichever side is
implied, net of execution.
"""
import json, os, sys, time, math, random, urllib.request, urllib.parse, datetime, collections

GAMMA = "https://gamma-api.polymarket.com"; UA = {"User-Agent": "Mozilla/5.0"}
RESD = r"C:\Users\yaniv\OneDrive\Projects\Polymarket_Research"
PAGES = int(sys.argv[1]) if len(sys.argv) > 1 else 18
TAGS = {"politics": "2", "geopolitics": "100265", "pop-culture": "596", "tweets-markets": "972",
        "elections": "144", "world": "101970", "economy": "100328", "tech": "1401", "business": "107"}
EXCLUDE = {"crypto", "sports", "soccer", "fifa-world-cup", "basketball", "tennis", "nfl", "nba",
           "mlb", "nhl", "baseball", "football", "games"}
BANDS = [(0.03, 0.10), (0.10, 0.20), (0.20, 0.35), (0.35, 0.50), (0.50, 0.65), (0.65, 0.80),
         (0.80, 0.90), (0.90, 0.97)]
FEER = {"politics": .04, "elections": .04, "tech": .04, "tweets-markets": .04,
        "pop-culture": .05, "economy": .05, "business": .05, "world": .0, "geopolitics": .0}
HALF_SPREAD = 0.0095
random.seed(31)


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


def jload(x):
    if isinstance(x, str):
        try: return json.loads(x)
        except Exception: return None
    return x


H = {k: [(int(t), float(p)) for t, p in v] for k, v in
     json.load(open(os.path.join(RESD, "daily_hist_cache.json"))).items()}

print(f"enumerating {PAGES} pages/tag (fresh-price basis)...")
rows = []; seen = set()
for cat, tid in TAGS.items():
    for off in range(0, PAGES * 100, 100):
        page = get(f"{GAMMA}/events?" + urllib.parse.urlencode(
            {"tag_id": tid, "closed": "true", "limit": "100", "offset": str(off),
             "order": "startDate", "ascending": "false"}))
        if not page: break
        for e in page:
            if {t.get("slug") for t in (e.get("tags") or [])} & EXCLUDE: continue
            eid = e.get("id")
            ms = e.get("markets") or []
            for m in ms:
                mid = m.get("id")
                if not mid or mid in seen: continue
                tk, pr = jload(m.get("clobTokenIds")), jload(m.get("outcomePrices"))
                if not tk or not pr: continue
                y = fnum(pr[0])
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
                if prev is None or (ts - pt) >= 86400: continue     # FRESH / live-book basis
                rows.append({"won": 1 if y > 0.5 else 0, "p": prev, "cat": cat, "N": len(ms),
                             "eid": eid, "en": en})

rows.sort(key=lambda r: r["en"])
months = ((rows[-1]["en"] - rows[0]["en"]).days or 1) / 30.44
SPLIT = rows[len(rows) // 2]["en"]
print(f"  {len(rows)} fresh legs over {months:.1f} months | holdout {SPLIT:%Y-%m-%d}\n")


def analyse(sel, minclust=12):
    """Leg-level z (the old basis) plus an event-clustered CI and a cluster-unit power calculation."""
    n = len(sel)
    if n < 20: return None
    v = [r["won"] - r["p"] for r in sel]
    m = sum(v) / n
    sd_leg = (sum((x - m) ** 2 for x in v) / (n - 1)) ** 0.5
    z_leg = m / (sd_leg / n ** 0.5) if sd_leg else 0.0
    by = collections.defaultdict(list)
    for r, x in zip(sel, v): by[r["eid"]].append(x)
    cl = [sum(g) / len(g) for g in by.values()]
    k = len(cl)
    if k < minclust: return None
    mc = sum(cl) / k
    sd_cl = (sum((x - mc) ** 2 for x in cl) / (k - 1)) ** 0.5
    d = sorted(sum(random.choice(cl) for _ in cl) / k for _ in range(8000))
    lo, hi = d[200], d[7799]
    tr = [x for r, x in zip(sel, v) if r["en"] < SPLIT]
    te = [x for r, x in zip(sel, v) if r["en"] >= SPLIT]
    # tradeable side and net edge
    buy_yes = mc > 0
    entry = sum(r["p"] for r in sel) / n if buy_yes else 1 - sum(r["p"] for r in sel) / n
    exec_c = HALF_SPREAD + sum(FEER.get(r["cat"], .04) * r["p"] * (1 - r["p"]) for r in sel) / n
    net = abs(mc) - exec_c
    cl_per_mo = k / months
    need = ((2 * sd_cl / net) ** 2) if net > 0 else None      # in CLUSTERS, using cluster-level SD
    return {"m": mc, "z_leg": z_leg, "n": n, "k": k, "lo": lo, "hi": hi, "sd_cl": sd_cl,
            "net": net, "side": "YES" if buy_yes else "NO", "entry": entry,
            "cl_mo": cl_per_mo, "need": need,
            "mo": (need / cl_per_mo) if need else None,
            "tr": (sum(tr) / len(tr) if tr else 0), "te": (sum(te) / len(te) if te else 0)}


def line(lbl, a):
    if not a:
        print(f"  {lbl:26} -- too few clusters"); return
    sig = "SIG" if (a["lo"] > 0 or a["hi"] < 0) else "   "
    flip = "!" if (a["tr"] > 0) != (a["te"] > 0) else " "
    print(f"  {lbl:26} {a['n']:5d}/{a['k']:4d} {a['n']/a['k']:4.1f}x {100*a['m']:+7.2f} "
          f"{a['z_leg']:+7.1f}  [{100*a['lo']:+6.2f},{100*a['hi']:+6.2f}] {sig} "
          f"{a['side']:>3} {100*a['net']:+6.2f} {a['cl_mo']:6.1f} "
          + (f"{a['need']:7.0f} {a['mo']:7.1f}" if a["need"] else f"{'-':>7} {'never':>7}")
          + f" {flip}")


hdr = (f"  {'cell':26} {'legs/clus':>10} {'x':>4} {'gap pt':>7} {'z_leg':>7}  "
       f"{'clustered CI':>17}     {'sd':>3} {'net':>6} {'cl/mo':>6} {'need':>7} {'months':>7}")
print("=" * 128)
print("BAND SURFACE -- fresh/live-book basis, event-clustered")
print("=" * 128)
print(hdr)
for lo, hi in BANDS:
    line(f"{lo:.2f}-{hi:.2f}", analyse([r for r in rows if lo <= r["p"] < hi]))

print("\n" + "=" * 128)
print("THE BOOK CELLS (and the candidate I flagged as next headroom)")
print("=" * 128)
print(hdr)
CELLS = [
    ("favbuy 0.80-0.90", lambda r: 0.80 <= r["p"] < 0.90),
    ("geobuy geo 0.35-0.80", lambda r: r["cat"] == "geopolitics" and 0.35 <= r["p"] < 0.80),
    ("carry FAR 0.90-0.97", lambda r: 0.90 <= r["p"] <= 0.97),
    ("secondfav 0.35-0.50 N>=6", lambda r: 0.35 <= r["p"] < 0.50 and r["N"] >= 6),
    ("secondfav2 0.35-0.50 N>=11", lambda r: 0.35 <= r["p"] < 0.50 and r["N"] >= 11),
    ("CANDIDATE 0.20-0.35 NO", lambda r: 0.20 <= r["p"] < 0.35),
    ("CANDIDATE 0.50-0.65 NO", lambda r: 0.50 <= r["p"] < 0.65),
]
for lbl, f in CELLS:
    line(lbl, analyse([r for r in rows if f(r)]))

print("\n  x = legs per cluster; the leg-level z is inflated by roughly sqrt(x).")
print("  SIG = the event-clustered 95% CI excludes zero.  ! = TRAIN/TEST sign flip.")
print("  need/months are in CLUSTERS and use the CLUSTER-level SD -- independent observations,")
print("  which is what a verdict actually consumes.")
