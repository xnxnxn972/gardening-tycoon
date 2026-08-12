"""THE FOSSIL TEST APPLIED TO CARRY AND THE RES-LAG FAMILY.

Established for favbuy/geobuy (dead_markets.py, live_book_surface.py): splitting a research cell by
whether the market EVER TRADED AGAIN after the snapshot separates a real edge from a phantom one.
A market that goes quiet has no counterparty, its last print is a fossil, and the outcome beats that
frozen price far more often than the price implies. Removing fossils moved the measured gap DOWN in
all 8 price bands, so the bias systematically flatters BUY-side theses.

carry and res-lag are BOTH buy-side and BOTH were validated on daily_hist_cache.json -- res_lag_capacity.py
reads the same file. So both are exposed. Their snapshots differ from favbuy's and must be matched:

  CARRY    buys YES at 4-9d to end, live mid 0.90-0.97, non-numeric EVENT questions, true=0.985.
           -> snapshot at T-6d (middle of its window), band on that price.
           (The NEAR band 1-3d x 0.70-0.90 was dropped 2026-07-23; measured separately here anyway,
            because if the fossil test independently condemns it that is a useful confirmation.)

  RES-LAG  buys AFTER endDate, while UMA settlement is pending, at ask >= 0.95, age 0-7d past end.
           -> snapshot at endDate + 1d, and the market must still have been unresolved then
              (closedTime > snapshot), otherwise no lag window existed to trade.
           res-lag's fossil question is sharper than the others': a post-deadline market awaiting
           resolution may be frozen BY DEFAULT. If nearly all of its candidates are fossils, then the
           entire 40.8k-market study rests on prices with no counterparty -- which would be the same
           defect that already produced its documented 0.90-0.95 blowup (25% wins vs 95% predicted,
           diagnosed at the time as adverse selection on last-trade prices).

Reports each cell as ALL / live-book / fossil, with the holdout split preserved.
"""
import json, os, re, sys, time, urllib.request, urllib.parse, datetime, math

GAMMA = "https://gamma-api.polymarket.com"; UA = {"User-Agent": "Mozilla/5.0"}
RESD = r"C:\Users\yaniv\OneDrive\Projects\Polymarket_Research"
PAGES = int(sys.argv[1]) if len(sys.argv) > 1 else 18
TAGS = {"politics": "2", "geopolitics": "100265", "pop-culture": "596", "tweets-markets": "972",
        "elections": "144", "world": "101970", "economy": "100328", "tech": "1401", "business": "107"}
EXCLUDE = {"crypto", "sports", "soccer", "fifa-world-cup", "basketball", "tennis", "nfl", "nba",
           "mlb", "nhl", "baseball", "football", "games"}
MENRX = re.compile(r"announcers? say|anyone say|be said during|said during|say [\"\u201c]", re.I)
NUMFAM = re.compile(
    r"\d+\s*-\s*[\d,.]+\s*(?:posts|tweets|views|days)|posts? from|tweets from|# of|million views"
    r"|unemployment|jobs in|rate be|market cap|cpi\b|ppi\b|pce\b|gdp\b|inflation|capex|index be"
    r"|deliver between|between [\d$,.]+[km]? and|transits?\b|passengers|box office|netflix"
    r"|#\d+\s+(?:global|us)\b|top\s+(?:us|global|\d)|most.watched", re.I)
# per-category taker fee at the relevant price, used to state the edge net of execution
FEER = {"politics": 0.04, "elections": 0.04, "tech": 0.04, "tweets-markets": 0.04,
        "pop-culture": 0.05, "economy": 0.05, "business": 0.05, "world": 0.0, "geopolitics": 0.0}


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


def iso(s):
    try:
        return datetime.datetime.fromisoformat((s or "")[:19].replace("Z", "")).replace(
            tzinfo=datetime.timezone.utc)
    except Exception:
        return None


H = {k: [(int(t), float(p)) for t, p in v] for k, v in
     json.load(open(os.path.join(RESD, "daily_hist_cache.json"))).items()}
print(f"cache {len(H)} tokens | enumerating {PAGES} pages/tag...")


def snap(tok, ts):
    """(last price at or before ts, bar age in days, count of bars strictly after ts)."""
    s = H.get(str(tok))
    if not s: return None, None, 0
    prev = pt = None; after = 0
    for t, p in s:
        if t <= ts: prev, pt = p, t
        else: after += 1
    if prev is None: return None, None, after
    return prev, (ts - pt) / 86400.0, after


rows = []; seen = set(); n_lag = 0
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
                en = iso(m.get("endDate") or e.get("endDate"))
                if en is None: continue
                seen.add(mid)
                won = 1 if y > 0.5 else 0
                q = m.get("question") or ""
                ct = iso(m.get("closedTime"))
                base = {"won": won, "en": en, "cat": cat, "q": q, "tok": tk[0],
                        "lag_h": ((ct - en).total_seconds() / 3600.0) if ct else None}

                # ---- CARRY: snapshot inside its 4-9d window, and inside the dropped 1-3d window
                for tag, dback in (("far", 6), ("near", 2)):
                    p, age, after = snap(tk[0], int(en.timestamp()) - dback * 86400)
                    if p is None: continue
                    rows.append({**base, "book": f"carry_{tag}", "p": p, "age": age, "after": after})

                # ---- RES-LAG: snapshot 1 day past the deadline, only if settlement was still pending
                ts = int(en.timestamp()) + 86400
                if ct and (ct - en).total_seconds() > 86400:
                    p, age, after = snap(tk[0], ts)
                    if p is not None:
                        n_lag += 1
                        rows.append({**base, "book": "reslag", "p": p, "age": age, "after": after})

rows.sort(key=lambda r: r["en"])
SPLIT = rows[len(rows) // 2]["en"]
print(f"  {len(seen)} resolved markets | {n_lag} with a real post-deadline lag window "
      f"| holdout {SPLIT:%Y-%m-%d}\n")


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


def show(lbl, sel, exec_cost):
    s = stat(sel)
    if s is None:
        print(f"    {lbl:34} n={len(sel):5d}   -- too thin to measure"); return None
    m, z, n, mtr, mte, sd = s
    wr = sum(r["won"] for r in sel) / n
    mp = sum(r["p"] for r in sel) / n
    flip = "  SIGN FLIPS OOS" if (mtr > 0) != (mte > 0) else ""
    print(f"    {lbl:34} n={n:5d}  gap {100*m:+6.2f}pt z={z:+6.1f} | price {mp:.3f} won {100*wr:5.1f}% "
          f"| TRAIN {100*mtr:+6.2f}/TEST {100*mte:+6.2f}{flip}")
    return s


def verdict(lbl, sel, exec_cost, cellname):
    print(f"\n  {cellname}")
    a = show("ALL (the original basis)", sel, exec_cost)
    live = [r for r in sel if r["after"] > 0]
    foss = [r for r in sel if r["after"] == 0]
    b = show("  live book at entry", live, exec_cost)
    show("  FOSSIL (never traded again)", foss, exec_cost)
    if sel:
        print(f"    fossil share of the cell: {100*len(foss)/len(sel):.0f}%")
    if a and b:
        print(f"    -> edge on a tradeable basis: {100*a[0]:+.2f}pt -> {100*b[0]:+.2f}pt "
              f"(x{b[0]/a[0]:+.2f})" if abs(a[0]) > 1e-9 else "")
        net = b[0] - exec_cost
        print(f"    -> net of {100*exec_cost:.1f}pt execution: {100*net:+.2f}pt")
        if net > 0:
            print(f"    -> confirming that at z=2 needs ~{int(math.ceil((2*b[5]/net)**2)):,} markets "
                  f"(cell supplies {b[2]})")


print("=" * 116)
print("CARRY  -- buys YES, so a POSITIVE gap is its edge")
print("=" * 116)
carry_far = [r for r in rows if r["book"] == "carry_far" and 0.90 <= r["p"] <= 0.97
             and not NUMFAM.search(r["q"].lower()) and not MENRX.search(r["q"])]
carry_near = [r for r in rows if r["book"] == "carry_near" and 0.70 <= r["p"] < 0.90
              and not NUMFAM.search(r["q"].lower()) and not MENRX.search(r["q"])]
# fee at p=0.93 is ~0.04*0.93*0.07 = 0.26pt; add the ~0.95pt half-spread measured live
verdict("carry", carry_far, 0.012, "FAR band  4-9d x mid 0.90-0.97   (what carry trades today)")
verdict("carry", carry_near, 0.015, "NEAR band 1-3d x mid 0.70-0.90   (dropped 2026-07-23)")

print("\n" + "=" * 116)
print("RES-LAG  -- buys the near-certain side after the deadline, so a POSITIVE gap is its edge")
print("=" * 116)
lag = [r for r in rows if r["book"] == "reslag"]
for lo, hi, lbl in [(0.95, 1.01, "band >=0.95  (what all three books trade)"),
                    (0.90, 0.95, "band 0.90-0.95  (the 2026-07-04 blowup band)"),
                    (0.85, 0.90, "band 0.85-0.90  (never traded, for shape)")]:
    verdict("reslag", [r for r in lag if lo <= r["p"] < hi], 0.006, lbl)

print("\n  res-lag structure check -- is a pending market frozen by default?")
sub = [r for r in lag if r["p"] >= 0.95]
if sub:
    print(f"    {len(sub)} candidates at >=0.95 | fossil share {100*sum(1 for r in sub if r['after']==0)/len(sub):.0f}%")
    med = sorted(r["lag_h"] for r in sub if r["lag_h"])
    if med:
        print(f"    median settlement lag {med[len(med)//2]/24:.1f}d "
              f"(the window the books are paid to sit through)")
