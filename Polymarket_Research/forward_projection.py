"""SUPERSEDED 2026-08-13 by clustered_surface.py -- DO NOT QUOTE THE MONTHS-TO-VERDICT TABLE.

The whole point of this script is months-to-verdict, and it computed that per LEG: it divided a
leg-count requirement by a legs-per-month supply, using a leg-level SD. A verdict consumes
INDEPENDENT observations, and legs of one event are not independent. Every timeline here is
optimistic, several badly so:

    cell                 here (per-leg)      clustered
    secondfav             0.8 months          6.7 months
    secondfav2            0.8 months          4.6 months
    0.20-0.35 NO          4.0 months         17.3 months
    0.50-0.65 NO         12.7 months        758.6 months, and the CI now SPANS ZERO

The "0.20-0.35 NO is the nearest unexploited headroom" and "the gate reveals suppressed sell-side
edges at 0.50-0.65" claims both came from this table. The first is real but far slower than stated;
the second does not survive clustering and is withdrawn.

What DOES survive: the acceptance-gate logic itself -- that a cell must be judged on months to a
verdict at its real supply, and that favbuy/geobuy fail it by orders of magnitude. clustered_surface.py
applies the same gate with the sample size counted correctly.

Kept for provenance. Use clustered_surface.py for decisions.

--- original header ---

WHAT DOES THE ACCEPTANCE GATE DO TO FUTURE PROFITABILITY AND SCALE?

acceptance_sim.py settled the backward-looking half: "traded within 24h" is an almost perfect proxy
for "will trade again" (P(fossil|fresh) = 2.4-6.5%, P(fossil|stale) = 96-98%), but every one of our
71 favbuy/geobuy legs was already fresh -- median 0.6h since the last trade. As a TRADE filter the
gate removes nothing. Its entire value is as a FUNDING gate.

So the forward question is not "how many trades does it block" but "which cells can still be funded
once the phantom edge is removed, and how long would each take to confirm at its real supply rate".

For every band, on the fresh/live-book basis only, this reports:
  - the gap and which SIDE it favours (positive = buy YES, negative = buy NO)
  - the net edge after execution, expressed as return on the capital a cycle actually ties up
  - the supply: qualifying markets per month in the enumeration window
  - markets needed for a z=2 verdict, and therefore MONTHS TO VERDICT at the observed supply

Months-to-verdict is the number that decides scale. A cell with a real edge that needs 20 years of
supply to prove is not a business, and that is precisely the trap favbuy was.
"""
import json, os, sys, time, math, urllib.request, urllib.parse, datetime

GAMMA = "https://gamma-api.polymarket.com"; UA = {"User-Agent": "Mozilla/5.0"}
RESD = r"C:\Users\yaniv\OneDrive\Projects\Polymarket_Research"
PAGES = int(sys.argv[1]) if len(sys.argv) > 1 else 18
TAGS = {"politics": "2", "geopolitics": "100265", "pop-culture": "596", "tweets-markets": "972",
        "elections": "144", "world": "101970", "economy": "100328", "tech": "1401", "business": "107"}
EXCLUDE = {"crypto", "sports", "soccer", "fifa-world-cup", "basketball", "tennis", "nfl", "nba",
           "mlb", "nhl", "baseball", "football", "games"}
BANDS = [(0.03, 0.10), (0.10, 0.20), (0.20, 0.35), (0.35, 0.50), (0.50, 0.65), (0.65, 0.80),
         (0.80, 0.90), (0.90, 0.97)]
EXEC = 0.015          # half-spread + fee, as measured live


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
                if prev is None or (ts - pt) >= 86400: continue      # FRESH ONLY: the tradeable basis
                rows.append({"won": 1 if y > 0.5 else 0, "en": en, "p": prev, "cat": cat, "N": len(ms)})

rows.sort(key=lambda r: r["en"])
span_d = (rows[-1]["en"] - rows[0]["en"]).days or 1
months = span_d / 30.44
SPLIT = rows[len(rows) // 2]["en"]
print(f"  {len(rows)} fresh-at-entry resolved markets over {span_d} days ({months:.1f} months)")
print(f"  holdout {SPLIT:%Y-%m-%d}\n")


def cell(sel):
    n = len(sel)
    if n < 25: return None
    v = [r["won"] - r["p"] for r in sel]
    m = sum(v) / n
    sd = (sum((x - m) ** 2 for x in v) / (n - 1)) ** 0.5
    z = m / (sd / n ** 0.5) if sd else 0
    tr = [r["won"] - r["p"] for r in sel if r["en"] < SPLIT]
    te = [r["won"] - r["p"] for r in sel if r["en"] >= SPLIT]
    return m, z, n, sd, (sum(tr) / len(tr) if tr else 0), (sum(te) / len(te) if te else 0)


print("=" * 118)
print(f"{'band':>11} {'side':>5} {'gap':>9} {'z':>6} {'n':>6} {'net edge':>9} {'ret/cycle':>10} "
      f"{'supply/mo':>10} {'need n':>8} {'months':>8}  holdout")
print("=" * 118)
for lo, hi in BANDS:
    c = cell([r for r in rows if lo <= r["p"] < hi])
    if not c:
        print(f"  {lo:.2f}-{hi:.2f}   n<25"); continue
    m, z, n, sd, mtr, mte = c
    buy_yes = m > 0
    side = "YES" if buy_yes else "NO"
    # buying YES costs p; buying NO costs 1-p. Edge magnitude is |gap|, less execution either way.
    entry = (lo + hi) / 2 if buy_yes else 1 - (lo + hi) / 2
    net = abs(m) - EXEC
    ret = net / entry if entry else 0
    sup = n / months
    need = int(math.ceil((2 * sd / net) ** 2)) if net > 0 else None
    mo = (need / sup) if (need and sup) else None
    flip = "SIGN FLIPS" if (mtr > 0) != (mte > 0) else f"{100*mtr:+5.1f}/{100*mte:+5.1f}"
    print(f"  {lo:.2f}-{hi:.2f} {side:>5} {100*m:+8.2f}pt {z:+6.1f} {n:6d} {100*net:+8.2f}pt "
          f"{100*ret:+9.2f}% {sup:10.1f} "
          + (f"{need:8,d} {mo:8.1f}" if need else f"{'-':>8} {'never':>8}") + f"  {flip}")

print("\n" + "=" * 118)
print("THE TWO BOOKS, AS THE GATE WOULD HAVE SEEN THEM BEFORE FUNDING")
print("=" * 118)
CASES = {
    "favbuy   0.80-0.90 all cats  (BUY YES)":
        ([r for r in rows if 0.80 <= r["p"] < 0.90], True, 0.85),
    "geobuy   geo 0.35-0.90       (BUY YES)":
        ([r for r in rows if r["cat"] == "geopolitics" and 0.35 <= r["p"] < 0.90], True, 0.64),
    "secondfav 0.35-0.50 N>=6     (BUY NO)":
        ([r for r in rows if 0.35 <= r["p"] < 0.50 and r["N"] >= 6], False, 0.58),
    "secondfav2 0.35-0.50 N>=11   (BUY NO)":
        ([r for r in rows if 0.35 <= r["p"] < 0.50 and r["N"] >= 11], False, 0.58),
}
for lbl, (sel, buy_yes, entry) in CASES.items():
    c = cell(sel)
    if not c:
        print(f"  {lbl}\n    n<25 -- REJECT (no measurement exists)"); continue
    m, z, n, sd, mtr, mte = c
    signed = m if buy_yes else -m
    net = signed - EXEC
    sup = n / months
    print(f"\n  {lbl}")
    print(f"    fresh-basis gap {100*m:+.2f}pt (z {z:+.1f}, n={n})  ->  edge for this side "
          f"{100*signed:+.2f}pt, net of execution {100*net:+.2f}pt")
    if net <= 0:
        print(f"    VERDICT: REJECT -- no positive edge after costs"); continue
    need = int(math.ceil((2 * sd / net) ** 2))
    print(f"    return on capital {100*net/entry:+.2f}%/cycle | supply {sup:.1f} markets/month")
    print(f"    needs {need:,} settled markets for a z=2 verdict -> {need/sup:.1f} months at full supply")
    print(f"    VERDICT: {'FUND' if need/sup <= 12 else 'REJECT -- unconfirmable in any useful horizon'}")
