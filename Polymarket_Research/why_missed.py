"""WHY DID FAVBUY AND GEOBUY MISS? Attribute the miss to a specific step in the research process.

Both books were validated on a CALIBRATION SURFACE: "in band X, realized frequency exceeds price by
+Ypt". That surface was measured on a MID (or a daily close) over EVERY market in the cell. We then
traded at the ASK on a SELECTED subset. Every gap between those two sentences is a candidate culprit.

Per-share PnL decomposes EXACTLY:

    won - ask - fee  =  (won - mid)   -   (ask - mid)   -   fee
                        ^^^^^^^^^^^       ^^^^^^^^^^^
                        the research      half-spread
                        quantity          (execution)

If (won - mid) is near the predicted edge -> the surface was RIGHT and we cannot trade it.
If (won - mid) is far below                -> the surface itself does not hold on our live universe,
                                              i.e. the RESEARCH MEASUREMENT was biased.

That fork decides whether the fix is "trade it better" or "measure it differently", so it is worth
more than any further CI on the PnL.
"""
import csv, os, math, random, collections

OUT = r"C:\Users\yaniv\polymarket-paper-trader"
random.seed(7)


def fnum(x):
    try:
        return float(x)
    except Exception:
        return None


def load(book):
    """Closed legs with a usable (mid, ask, outcome) triple. Both books buy YES."""
    rows = []
    for r in csv.DictReader(open(os.path.join(OUT, f"paper_ledger_{book}.csv"), encoding="utf-8")):
        ask, iy, won = fnum(r.get("no_ask")), fnum(r.get("implied_yes")), r.get("yes_won")
        if ask is None or iy is None or won not in ("0", "1"):
            continue
        # favbuy's writer stores implied_yes as 1-mid (NO-side convention); geobuy stores the mid.
        mid = (1.0 - iy) if book == "favbuy" else iy
        if not (0.0 < mid < 1.0):
            continue
        sh = fnum(r.get("shares")) or 0.0
        rows.append({
            "eid": r.get("event_id") or r.get("market_id"),
            "mid": mid, "ask": ask, "won": int(won),
            "edge": fnum(r.get("est_edge")) or 0.0,
            "fee_ps": (fnum(r.get("fee")) or 0.0) / sh if sh else 0.0,
            "pnl": fnum(r.get("pnl")) or 0.0, "cost": fnum(r.get("cost")) or 0.0,
            "q": (r.get("question") or "")[:44],
        })
    return rows


def clustered_ci(rows, key, iters=6000):
    """Bootstrap over EVENTS, not legs: legs in one event share an outcome and are one bet."""
    by = collections.defaultdict(list)
    for r in rows:
        by[r["eid"]].append(key(r))
    cl = [sum(v) / len(v) for v in by.values()]
    if len(cl) < 3:
        return (sum(cl) / len(cl) if cl else 0.0), None, None, len(cl)
    draws = []
    for _ in range(iters):
        s = [cl[random.randrange(len(cl))] for _ in cl]
        draws.append(sum(s) / len(s))
    draws.sort()
    return (sum(cl) / len(cl), draws[int(0.025 * len(draws))], draws[int(0.975 * len(draws))], len(cl))


PRED = {"favbuy": 0.059, "geobuy": 0.06}   # geobuy's claim was a +6..+21pt range; use the floor

for book in ("favbuy", "geobuy"):
    rows = load(book)
    if not rows:
        print(f"\n{book}: no usable rows"); continue
    print("\n" + "=" * 78)
    print(f"{book.upper()}  --  {len(rows)} closed legs, {len({r['eid'] for r in rows})} event-clusters")
    print("=" * 78)

    m_mid, lo_mid, hi_mid, ncl = clustered_ci(rows, lambda r: r["won"] - r["mid"])
    m_spr = sum(r["ask"] - r["mid"] for r in rows) / len(rows)
    m_fee = sum(r["fee_ps"] for r in rows) / len(rows)
    m_net, lo_net, hi_net, _ = clustered_ci(rows, lambda r: r["won"] - r["ask"] - r["fee_ps"])

    def pct(x):
        return f"{100*x:+6.2f}pt"

    print(f"\n  THE RESEARCH QUANTITY   won - mid   = {pct(m_mid)}"
          + (f"  CI[{100*lo_mid:+.1f}, {100*hi_mid:+.1f}]" if lo_mid is not None else ""))
    print(f"  the research PREDICTED               = {pct(PRED[book])}")
    verdict = ("SURFACE HELD -- the loss is execution cost"
               if m_mid >= PRED[book] * 0.5 else
               "SURFACE DID NOT HOLD on the traded universe -- the measurement was biased")
    print(f"  -> {verdict}")
    if lo_mid is not None:
        inside = lo_mid <= PRED[book] <= hi_mid
        print(f"  -> the predicted {100*PRED[book]:+.1f}pt is {'INSIDE' if inside else 'OUTSIDE'} the realized CI")

    print(f"\n  half-spread paid    ask - mid   = {pct(-m_spr)}")
    print(f"  fee                             = {pct(-m_fee)}")
    print(f"  ------------------------------------------")
    print(f"  net per share                   = {pct(m_net)}"
          + (f"  CI[{100*lo_net:+.1f}, {100*hi_net:+.1f}]" if lo_net is not None else ""))
    print(f"  (check: {pct(m_mid)} - {pct(m_spr)} - {pct(m_fee)} = {pct(m_mid - m_spr - m_fee)})")

    # How much of the total miss is execution vs measurement?
    miss = PRED[book] - m_net
    exec_cost = m_spr + m_fee
    meas_err = PRED[book] - m_mid
    print(f"\n  TOTAL MISS vs the promise       = {100*miss:.2f}pt")
    print(f"     of which EXECUTION (spread+fee) = {100*exec_cost:5.2f}pt  ({100*exec_cost/miss:4.0f}%)"
          if miss > 0 else "")
    print(f"     of which MEASUREMENT (surface)  = {100*meas_err:5.2f}pt  ({100*meas_err/miss:4.0f}%)"
          if miss > 0 else "")

    # SELECTION WITHIN THE CELL: does our own gate pick the bad ones?
    srt = sorted(rows, key=lambda r: r["edge"])
    half = len(srt) // 2
    for lbl, grp in (("LOW  est_edge half", srt[:half]), ("HIGH est_edge half", srt[half:])):
        if not grp:
            continue
        gm, _, _, gc = clustered_ci(grp, lambda r: r["won"] - r["mid"])
        wr = sum(r["won"] for r in grp) / len(grp)
        mp = sum(r["mid"] for r in grp) / len(grp)
        print(f"  {lbl}: claimed edge {100*sum(g['edge'] for g in grp)/len(grp):4.1f}pt | "
              f"mid {mp:.3f} | won {100*wr:4.1f}% | won-mid {pct(gm)}")

    # Is the traded price distribution even the cell that was researched?
    band = sum(1 for r in rows if 0.80 <= r["mid"] < 0.90) if book == "favbuy" else \
           sum(1 for r in rows if 0.35 <= r["mid"] < 0.90)
    print(f"\n  legs whose MID sat in the researched band: {band}/{len(rows)}")
    lo = min(r["mid"] for r in rows); hi = max(r["mid"] for r in rows)
    print(f"  traded mid range {lo:.3f} - {hi:.3f}, mean {sum(r['mid'] for r in rows)/len(rows):.3f}")
    print(f"  break-even win rate at the mean ask = "
          f"{100*(sum(r['ask'] for r in rows)/len(rows) + m_fee):.1f}%  vs realized "
          f"{100*sum(r['won'] for r in rows)/len(rows):.1f}%")
