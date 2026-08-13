"""THE ONE LEAD IN FAVBUY: FIELD SIZE.

LEG-LEVEL CAVEAT (added 2026-08-13). The z-scores and any months-to-verdict figures below are
computed PER LEG. Legs of one negRisk event share a single outcome draw and are ONE observation, so
z is inflated by roughly sqrt(legs per cluster) and timelines are optimistic. See
clustered_surface.py for the event-clustered version of the same measurements. The DIRECTIONAL
conclusions in this script were checked against the clustered surface and are unchanged; only the
confidence and the timelines move.

salvage_search.py scanned 23 sub-cells and exactly one cleared the bar (cat=economy), which is within
the ~1.2 expected by chance -- not a discovery. But a single cell clearing is the weak evidence; the
strong evidence was a MONOTONE GRADIENT across four ordered field-size buckets:

    N = 1      gap  +10.96pt   net  +9.41pt   n= 39
    N = 2-5    gap   +9.35pt   net  +7.92pt   n= 57
    N = 6-10   gap   +7.67pt   net  +6.19pt   n= 64
    N = 11-40  gap   -1.93pt   net  -3.38pt   n=229   <- 59% of the cell, and it is NEGATIVE

A monotone ordering across four buckets is far less likely to arise by chance than one cell out of 23,
and it is mechanistically sensible: in a 20-outcome negRisk field an 0.85 leg is a different object
from an 0.85 binary -- its complement is spread across 19 other legs, and big fields are exactly where
the surface already knows mispricing lives (that is secondfav's whole thesis).

Three questions decide whether this is real or another fossil:
  1. Does the combined N<=10 cell clear the 12-month bar on its own, with a holdout?
  2. Is it the SAME finding as the economy cell, or two independent ones? Cross-tabbed here, because
     "we found two effects" is the classic way one effect gets double-counted.
  3. DOES IT EXPLAIN OUR LOSSES? favbuy hardcoded N=0 for its whole life, so the ledger cannot answer
     this -- but the event ids are recorded, so the field sizes can be fetched now. If our 50 legs sat
     mostly in N>=11, the live loss stops being a mystery and starts being a prediction we can check.

Question 3 is the one that matters. Everything above it is a hypothesis; only that is a test.
"""
import csv, json, os, sys, time, math, urllib.request, urllib.parse, datetime, collections

GAMMA = "https://gamma-api.polymarket.com"; UA = {"User-Agent": "Mozilla/5.0"}
TRADER = r"C:\Users\yaniv\polymarket-paper-trader"
RESD = r"C:\Users\yaniv\OneDrive\Projects\Polymarket_Research"
PAGES = int(sys.argv[1]) if len(sys.argv) > 1 else 18
TAGS = {"politics": "2", "geopolitics": "100265", "pop-culture": "596", "tweets-markets": "972",
        "elections": "144", "world": "101970", "economy": "100328", "tech": "1401", "business": "107"}
EXCLUDE = {"crypto", "sports", "soccer", "fifa-world-cup", "basketball", "tennis", "nfl", "nba",
           "mlb", "nhl", "baseball", "football", "games"}
FEER = {"politics": .04, "elections": .04, "tech": .04, "tweets-markets": .04,
        "pop-culture": .05, "economy": .05, "business": .05, "world": .0, "geopolitics": .0}
HALF_SPREAD = 0.0095


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
                if prev is None or (ts - pt) >= 86400: continue
                rows.append({"won": 1 if y > 0.5 else 0, "en": en, "p": prev, "cat": cat, "N": len(ms)})

rows.sort(key=lambda r: r["en"])
months = ((rows[-1]["en"] - rows[0]["en"]).days or 1) / 30.44
SPLIT = rows[len(rows) // 2]["en"]
FAV = [r for r in rows if 0.80 <= r["p"] < 0.90]
print(f"  favbuy cell n={len(FAV)} over {months:.1f} months\n")


def ev(lbl, sel, minn=25):
    n = len(sel)
    if n < minn:
        print(f"  {lbl:38} n={n:4d}  (thin)"); return None
    v = [r["won"] - r["p"] for r in sel]
    m = sum(v) / n
    sd = (sum((x - m) ** 2 for x in v) / (n - 1)) ** 0.5
    z = m / (sd / n ** 0.5)
    tr = [r["won"] - r["p"] for r in sel if r["en"] < SPLIT]
    te = [r["won"] - r["p"] for r in sel if r["en"] >= SPLIT]
    mtr = sum(tr) / len(tr) if tr else 0
    mte = sum(te) / len(te) if te else 0
    exc = HALF_SPREAD + sum(FEER.get(r["cat"], .04) * r["p"] * (1 - r["p"]) for r in sel) / n
    net = m - exc
    sup = n / months
    mo = ((2 * sd / net) ** 2) / sup if net > 0 else None
    print(f"  {lbl:38} n={n:4d} gap {100*m:+6.2f}pt z{z:+5.1f} net {100*net:+6.2f}pt "
          f"sup {sup:4.1f}/mo " + (f"{mo:7.0f} mo" if mo else "  never") +
          f"  TRAIN{100*mtr:+6.1f}/TEST{100*mte:+6.1f}")
    return {"gap": m, "net": net, "n": n, "mo": mo, "tr": mtr, "te": mte}


print("=" * 112)
print("1. THE COMBINED SMALL-FIELD CELL")
print("=" * 112)
ev("N<=10  (the candidate)", [r for r in FAV if r["N"] <= 10])
ev("N>=11  (what drags the cell)", [r for r in FAV if r["N"] >= 11])
ev("whole cell", FAV)

print("\n" + "=" * 112)
print("2. IS 'economy' THE SAME FINDING AS 'N<=10'?  (cross-tab)")
print("=" * 112)
ev("economy AND N<=10", [r for r in FAV if r["cat"] == "economy" and r["N"] <= 10])
ev("economy AND N>=11", [r for r in FAV if r["cat"] == "economy" and r["N"] >= 11])
ev("N<=10 EXCLUDING economy", [r for r in FAV if r["N"] <= 10 and r["cat"] != "economy"])
ev("N>=11 EXCLUDING economy", [r for r in FAV if r["N"] >= 11 and r["cat"] != "economy"])
ec = [r for r in FAV if r["cat"] == "economy"]
print(f"  economy field-size mix: " +
      ", ".join(f"N{k}={v}" for k, v in sorted(collections.Counter(
          ("<=10" if r["N"] <= 10 else ">=11") for r in ec).items())))

print("\n" + "=" * 112)
print("3. THE TEST THAT MATTERS: what field sizes did WE actually trade?")
print("=" * 112)
legs = []
for r in csv.DictReader(open(os.path.join(TRADER, "paper_ledger_favbuy.csv"), encoding="utf-8")):
    p, iy = fnum(r.get("pnl")), fnum(r.get("implied_yes"))
    if p is None or iy is None: continue
    legs.append({"eid": r.get("event_id"), "pnl": p, "cost": fnum(r.get("cost")) or 0,
                 "mid": 1 - iy, "won": 1 if p > 0 else 0, "q": (r.get("question") or "")[:40]})
eids = sorted({l["eid"] for l in legs if l["eid"]})
print(f"  {len(legs)} closed legs across {len(eids)} events; fetching field sizes...")
NMAP = {}
for i, eid in enumerate(eids, 1):
    d = get(f"{GAMMA}/events/{eid}")
    NMAP[eid] = len((d or {}).get("markets") or []) if d else None
    if i % 20 == 0: print(f"    {i}/{len(eids)}", flush=True)
for l in legs:
    l["N"] = NMAP.get(l["eid"])
known = [l for l in legs if l["N"]]
print(f"  resolved field size for {len(known)}/{len(legs)} legs\n")


def blk(lbl, sel):
    if not sel:
        print(f"    {lbl:26} --"); return
    pnl = sum(l["pnl"] for l in sel); cost = sum(l["cost"] for l in sel)
    wm = sum(l["won"] - l["mid"] for l in sel) / len(sel)
    print(f"    {lbl:26} {len(sel):3d} legs  PnL {pnl:+8.2f} on ${cost:7.2f} "
          f"({100*pnl/cost if cost else 0:+6.2f}%)  won-mid {100*wm:+6.2f}pt")


blk("N<=10  (predicted GOOD)", [l for l in known if l["N"] <= 10])
blk("N>=11  (predicted BAD)", [l for l in known if l["N"] >= 11])
print()
dist = collections.Counter(("1" if l["N"] == 1 else "2-5" if l["N"] <= 5 else
                            "6-10" if l["N"] <= 10 else "11-40" if l["N"] <= 40 else "41+")
                           for l in known)
print("  our traded field-size mix: " + ", ".join(f"N{k}={v}" for k, v in sorted(dist.items())))
hist = collections.Counter(("<=10" if r["N"] <= 10 else ">=11") for r in FAV)
print(f"  the research cell's mix:   N<=10={hist['<=10']} ({100*hist['<=10']/len(FAV):.0f}%), "
      f"N>=11={hist['>=11']} ({100*hist['>=11']/len(FAV):.0f}%)")
if known:
    share = sum(1 for l in known if l["N"] >= 11) / len(known)
    print(f"  our N>=11 share: {100*share:.0f}%  vs the cell's "
          f"{100*hist['>=11']/len(FAV):.0f}%")
