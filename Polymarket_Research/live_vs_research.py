"""LIVE REALIZATION vs RESEARCH CLAIM, on matched terms, for carry and the res-lag family.

fossil_carry_reslag.py measured what the HISTORY says about these cells on a tradeable basis.
This measures what the PAPER BOOKS actually realized, using the identical decomposition applied to
favbuy/geobuy so the two are directly comparable:

    won - ask - fee  =  (won - mid)  -  (ask - mid)  -  fee

(won - mid) is the research quantity. Anything left over is execution. All of these books record the
bought side in the "NO" role: no_ask = entry ask, implied_yes = 1 - our side's mid.

Event-clustered bootstrap throughout -- legs of one event resolve together and are one bet.
"""
import csv, os, math, random, collections

OUT = r"C:\Users\yaniv\polymarket-paper-trader"
random.seed(11)
BOOKS = {"carry": 0.012, "select": 0.006, "scale": 0.006, "lagsafe": 0.006}   # exec cost assumption


def fnum(x):
    try: return float(x)
    except Exception: return None


def load(book):
    """WHOSE outcome is `yes_won`? The market's YES token -- NOT necessarily the side we bought.
    res-lag buys whichever side is near-certain, frequently the NO token, so yes_won is the wrong
    indicator there and using it produced an impossible -64pt. Derive our side's outcome from the
    settlement itself: a winning leg pays `shares` (pnl = shares - cost > 0), a losing leg pays 0
    (pnl = -cost). Also cross-check against yes_won so any disagreement is visible rather than silent.
    """
    rows = []; agree = tot = 0
    p = os.path.join(OUT, f"paper_ledger_{book}.csv")
    if not os.path.exists(p): return rows, 0.0
    for r in csv.DictReader(open(p, encoding="utf-8")):
        ask, iy, pnl = fnum(r.get("no_ask")), fnum(r.get("implied_yes")), fnum(r.get("pnl"))
        if ask is None or iy is None or pnl is None: continue
        mid = 1.0 - iy                      # our side's mid (the books store 1 - it)
        if not (0.0 < mid < 1.0): continue
        sh = fnum(r.get("shares")) or 0.0
        won = 1 if pnl > 0 else 0
        if r.get("yes_won") in ("0", "1"):
            tot += 1; agree += (int(r["yes_won"]) == won)
        rows.append({"eid": r.get("event_id") or r.get("market_id"), "mid": mid, "ask": ask,
                     "won": won, "fee_ps": (fnum(r.get("fee")) or 0.0) / sh if sh else 0.0,
                     "pnl": pnl, "cost": fnum(r.get("cost")) or 0.0})
    return rows, (agree / tot if tot else 0.0)


def cl_ci(rows, key, iters=6000):
    by = collections.defaultdict(list)
    for r in rows: by[r["eid"]].append(key(r))
    cl = [sum(v) / len(v) for v in by.values()]
    if len(cl) < 3: return (sum(cl) / len(cl) if cl else 0.0), None, None, len(cl)
    d = []
    for _ in range(iters):
        s = [cl[random.randrange(len(cl))] for _ in cl]
        d.append(sum(s) / len(s))
    d.sort()
    return sum(cl) / len(cl), d[int(.025 * len(d))], d[int(.975 * len(d))], len(cl)


print("=" * 104)
print(f"{'book':10} {'legs':>5} {'clust':>6} {'PnL':>9} | {'won-mid (research qty)':>34} | "
      f"{'spread':>7} {'fee':>6} | {'net/share':>10}")
print("=" * 104)
for b, ec in BOOKS.items():
    rows, agree = load(b)
    if not rows:
        print(f"{b:10}  (no closed legs)"); continue
    m, lo, hi, nc = cl_ci(rows, lambda r: r["won"] - r["mid"])
    spr = sum(r["ask"] - r["mid"] for r in rows) / len(rows)
    fee = sum(r["fee_ps"] for r in rows) / len(rows)
    nm, nlo, nhi, _ = cl_ci(rows, lambda r: r["won"] - r["ask"] - r["fee_ps"])
    pnl = sum(r["pnl"] for r in rows)
    ci = f"CI[{100*lo:+6.1f},{100*hi:+6.1f}]" if lo is not None else " " * 20
    print(f"{b:10} {len(rows):5d} {nc:6d} {pnl:+9.2f} | {100*m:+7.2f}pt {ci} | "
          f"{100*spr:6.2f} {100*fee:5.2f} | {100*nm:+7.2f}pt   (yes_won agrees {100*agree:.0f}%)")

print("\n" + "=" * 104)
print("RESEARCH CLAIM  vs  LIVE-BOOK HISTORY  vs  WHAT THE PAPER BOOK REALIZED   (all on won - mid)")
print("=" * 104)
CLAIM = {
    "carry":   ("+4..+7pt (far band 0.90-0.97)", +4.54),
    "select":  ("+0.99..+2.99%/cycle",            +0.27),
    "scale":   ("+0.99..+2.99%/cycle",            +0.27),
    "lagsafe": ("+0.99..+2.99%/cycle",            +0.27),
}
for b, ec in BOOKS.items():
    rows, _ = load(b)
    if not rows: continue
    m, lo, hi, nc = cl_ci(rows, lambda r: r["won"] - r["mid"])
    claim, hist = CLAIM[b]
    inside = (lo is not None and lo <= hist / 100.0 <= hi)
    print(f"  {b:9} claimed {claim:30} | live-book history {hist:+5.2f}pt | "
          f"realized {100*m:+6.2f}pt  -> history is {'INSIDE' if inside else 'OUTSIDE'} the realized CI")
