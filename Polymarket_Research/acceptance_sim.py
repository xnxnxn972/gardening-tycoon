"""SIMULATING THE TRADEABILITY ACCEPTANCE TEST ON FAVBUY AND GEOBUY.

The test as measured splits a cell by whether the market EVER TRADED AGAIN after the snapshot. That
is post-entry information, so it can gate a FUNDING DECISION but cannot, as written, filter a trade.
This script asks the three questions that decide how much the test is actually worth:

  A. IS THERE A TRADEABLE PROXY? "Has this market traded in the last 24h?" IS observable at entry.
     If recent activity predicts future activity well enough, the research gate becomes a live filter.
     Measured on history: P(goes fossil | fresh at entry) vs P(goes fossil | stale at entry), and the
     edge inside each group.

  B. WHAT WOULD IT HAVE DONE TO THE TRADES WE ACTUALLY PLACED? Fetches hourly history for all 71
     favbuy/geobuy legs and reconstructs, per leg, whether it was fresh at entry and whether it went
     quiet afterwards. Then splits realized PnL by both. This is the only way to know whether the
     filter would have removed our losers or none of them.

  C. WHAT DOES IT DO GOING FORWARD? Applies the gate to the whole band surface and reports which
     cells survive, on which side, and how much throughput each supplies.

Part B is the one that can embarrass the whole idea: our live scanners ALREADY demand a two-sided
book inside a 4c spread, which is itself a liveness filter. If our legs were all live books already,
the test would have changed nothing about what we traded -- and would only have stopped us funding
the books at all.
"""
import csv, json, os, sys, time, math, random, urllib.request, urllib.parse, datetime, collections

CLOB = "https://clob.polymarket.com"; UA = {"User-Agent": "Mozilla/5.0"}
TRADER = r"C:\Users\yaniv\polymarket-paper-trader"
RESD = r"C:\Users\yaniv\OneDrive\Projects\Polymarket_Research"
CACHE = os.path.join(RESD, "accept_sim_px.json")
random.seed(5)


def get(u, tries=3):
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=30) as r:
                return json.load(r)
        except Exception:
            time.sleep(0.3 * (i + 1))
    return None


def fnum(x):
    try: return float(x)
    except Exception: return None


def ts_of(s):
    try:
        return datetime.datetime.fromisoformat((s or "")[:19].replace("Z", "")).replace(
            tzinfo=datetime.timezone.utc).timestamp()
    except Exception:
        return None


# ---------------------------------------------------------------- A. tradeable proxy, on history
print("=" * 100)
print("A.  CAN 'TRADED IN THE LAST 24h' STAND IN FOR 'WILL TRADE AGAIN'?")
print("=" * 100)
H = {k: [(int(t), float(p)) for t, p in v] for k, v in
     json.load(open(os.path.join(RESD, "daily_hist_cache.json"))).items()}
GAMMA = "https://gamma-api.polymarket.com"
TAGS = {"politics": "2", "geopolitics": "100265", "pop-culture": "596", "tweets-markets": "972",
        "elections": "144", "world": "101970", "economy": "100328", "tech": "1401", "business": "107"}
EXCLUDE = {"crypto", "sports", "soccer", "fifa-world-cup", "basketball", "tennis", "nfl", "nba",
           "mlb", "nhl", "baseball", "football", "games"}
PAGES = int(sys.argv[1]) if len(sys.argv) > 1 else 14
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
                en = ts_of(m.get("endDate") or e.get("endDate"))
                if en is None: continue
                seen.add(mid)
                ts = int(en) - 3 * 86400
                s = H.get(str(tk[0]))
                if not s: continue
                prev = pt = None; after = 0
                for t, p in s:
                    if t <= ts: prev, pt = p, t
                    else: after += 1
                if prev is None: continue
                rows.append({"won": 1 if y > 0.5 else 0, "p": prev, "cat": cat,
                             "fresh": (ts - pt) < 86400, "fossil": after == 0})
print(f"  {len(rows)} resolved markets\n")


def px(sel):
    n = len(sel)
    if n < 25: return None
    v = [r["won"] - r["p"] for r in sel]
    m = sum(v) / n
    sd = (sum((x - m) ** 2 for x in v) / (n - 1)) ** 0.5
    return m, (m / (sd / n ** 0.5) if sd else 0), n, sd


for lbl, cell in (("favbuy 0.80-0.90", [r for r in rows if 0.80 <= r["p"] < 0.90]),
                  ("geobuy geo 0.35-0.90",
                   [r for r in rows if r["cat"] == "geopolitics" and 0.35 <= r["p"] < 0.90])):
    fr = [r for r in cell if r["fresh"]]; st = [r for r in cell if not r["fresh"]]
    if not cell: continue
    pf_fr = sum(1 for r in fr if r["fossil"]) / len(fr) if fr else 0
    pf_st = sum(1 for r in st if r["fossil"]) / len(st) if st else 0
    print(f"  {lbl}")
    print(f"    P(goes fossil | FRESH at entry) = {100*pf_fr:5.1f}%   (n={len(fr)})")
    print(f"    P(goes fossil | STALE at entry) = {100*pf_st:5.1f}%   (n={len(st)})")
    for nm, g in (("kept by the filter (fresh)", fr), ("rejected (stale)", st)):
        s = px(g)
        print(f"    {nm:28} gap {100*s[0]:+6.2f}pt z={s[1]:+5.1f} n={s[2]:5d}" if s
              else f"    {nm:28} n<25")
    print()

# ---------------------------------------------------------------- B. our actual legs
print("=" * 100)
print("B.  WHAT WOULD THE FILTER HAVE DONE TO THE 71 LEGS WE ACTUALLY TRADED?")
print("=" * 100)
legs = []
for book in ("favbuy", "geobuy"):
    for r in csv.DictReader(open(os.path.join(TRADER, f"paper_ledger_{book}.csv"), encoding="utf-8")):
        t0, pnl = ts_of(r.get("ts_open")), fnum(r.get("pnl"))
        tok = r.get("no_token")
        if not tok or t0 is None or pnl is None: continue
        iy = fnum(r.get("implied_yes")) or 0
        legs.append({"book": book, "tok": tok, "t0": t0, "pnl": pnl,
                     "cost": fnum(r.get("cost")) or 0, "ask": fnum(r.get("no_ask")) or 0,
                     "mid": (1 - iy) if book == "favbuy" else iy,
                     "won": 1 if pnl > 0 else 0, "eid": r.get("event_id"),
                     "tclose": ts_of(r.get("ts_close")), "q": (r.get("question") or "")[:40]})
print(f"  {len(legs)} closed legs | fetching hourly history for each bought token...")
C = {}
if os.path.exists(CACHE):
    try: C = json.load(open(CACHE))
    except Exception: C = {}
miss = [l["tok"] for l in legs if l["tok"] not in C]
for i, tok in enumerate(dict.fromkeys(miss), 1):
    d = get(f"{CLOB}/prices-history?" + urllib.parse.urlencode(
        {"market": tok, "interval": "max", "fidelity": "60"}))
    C[tok] = [[int(p["t"]), float(p["p"])] for p in (d or {}).get("history", [])] if d else []
    if i % 20 == 0: print(f"    {i}/{len(set(miss))}", flush=True)
json.dump(C, open(CACHE, "w"))
print(f"  cache holds {len(C)} tokens\n")

for l in legs:
    h = C.get(l["tok"]) or []
    before = [t for t, _ in h if t <= l["t0"]]
    end = l["tclose"] or (l["t0"] + 365 * 86400)
    after = [t for t, _ in h if l["t0"] < t <= end]
    l["nbars"] = len(h)
    l["fresh"] = bool(before) and (l["t0"] - max(before)) < 86400
    l["gap_h"] = ((l["t0"] - max(before)) / 3600.0) if before else None
    l["quiet_after"] = len(after) == 0
    l["n_after"] = len(after)

usable = [l for l in legs if l["nbars"] > 0]
print(f"  {len(usable)}/{len(legs)} legs have usable history\n")


def blk(lbl, sel):
    if not sel:
        print(f"    {lbl:34} --"); return
    pnl = sum(l["pnl"] for l in sel); cost = sum(l["cost"] for l in sel)
    wr = sum(l["won"] for l in sel) / len(sel)
    wm = sum(l["won"] - l["mid"] for l in sel) / len(sel)
    print(f"    {lbl:34} {len(sel):3d} legs  PnL {pnl:+8.2f}  on ${cost:8.2f} "
          f"({100*pnl/cost if cost else 0:+6.2f}%)  won {100*wr:5.1f}%  won-mid {100*wm:+6.2f}pt")


print("  BY FRESHNESS AT ENTRY (the filter we could actually apply):")
blk("KEPT: traded within 24h", [l for l in usable if l["fresh"]])
blk("REMOVED: stale at entry", [l for l in usable if not l["fresh"]])
print("\n  BY WHAT HAPPENED AFTER (not knowable at entry -- diagnostic only):")
blk("stayed live after entry", [l for l in usable if not l["quiet_after"]])
blk("went quiet after entry", [l for l in usable if l["quiet_after"]])
print("\n  per book:")
for b in ("favbuy", "geobuy"):
    sub = [l for l in usable if l["book"] == b]
    print(f"   {b}:")
    blk("  kept (fresh)", [l for l in sub if l["fresh"]])
    blk("  removed (stale)", [l for l in sub if not l["fresh"]])

gaps = sorted(l["gap_h"] for l in usable if l["gap_h"] is not None)
if gaps:
    print(f"\n  hours since last trade at our entry: median {gaps[len(gaps)//2]:.1f}h, "
          f"p90 {gaps[int(.9*len(gaps))]:.1f}h, max {gaps[-1]:.1f}h")

# ---------------------------------------------------------------- C. the funding-gate counterfactual
print("\n" + "=" * 100)
print("C.  THE GATE AS A FUNDING DECISION -- what it would have cost us to obey it")
print("=" * 100)
for b in ("favbuy", "geobuy"):
    led = [l for l in legs if l["book"] == b]
    pos = os.path.join(TRADER, f"paper_positions_{b}.csv")
    nopen = sum(1 for _ in csv.DictReader(open(pos, encoding="utf-8"))) if os.path.exists(pos) else 0
    ocost = sum(fnum(r.get("cost")) or 0 for r in csv.DictReader(open(pos, encoding="utf-8"))) \
        if os.path.exists(pos) else 0
    print(f"  {b:8} closed {len(led):3d} legs  realized {sum(l['pnl'] for l in led):+8.2f} | "
          f"still open {nopen:3d} legs, ${ocost:,.2f} committed")
