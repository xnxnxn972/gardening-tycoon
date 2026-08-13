"""IS SECONDFAV CHURNING ON MULTI-LEG EVENTS?

Three of secondfav's settled events hold MORE THAN ONE leg, all bought NO in the same partition:
    Elon Musk net worth       +6.26 / -18.12
    Genesee County            +4.73 / -13.64
    Wisconsin Sec of State   +14.25 / -14.89
In a partition exactly one leg wins, so buying NO on k legs of the same event guarantees a loss on
one of them. Buy NO on ALL N legs and you pay N - sum(YES) = N - 1 and collect N - 1: dead even
before fees, pure churn. The edge only exists on a SUBSET that excludes the winner -- so every extra
leg in the same event converts edge into variance and fees.

This is precisely the pathology the res-lag family was fixed for on 2026-08-10 (MAX_LEGS_PER_EVENT=1
plus a global cross-book registry). That fix went into res_harvester ONLY. miner_harvester caps
per-event DOLLARS (per_event: 50.0) but never per-event LEG COUNT, so secondfav/secondfav2/carry
were never protected.

Quantifies the cost across every miner book, and checks what a 1-leg-per-event rule would have done.
"""
import csv, os, collections

OUT = r"C:\Users\yaniv\polymarket-paper-trader"


def f(x, d=0.0):
    try: return float(x)
    except Exception: return d


for book in ("secondfav", "secondfav2", "carry", "counts"):
    p = os.path.join(OUT, f"paper_ledger_{book}.csv")
    if not os.path.exists(p): continue
    rows = list(csv.DictReader(open(p, encoding="utf-8")))
    if not rows: continue
    by = collections.defaultdict(list)
    for r in rows: by[r.get("event_id")].append(r)
    single = [g for g in by.values() if len(g) == 1]
    multi = [g for g in by.values() if len(g) > 1]
    def agg(gs):
        legs = [r for g in gs for r in g]
        pnl = sum(f(r.get("pnl")) for r in legs)
        cost = sum(f(r.get("cost")) for r in legs)
        return len(gs), len(legs), pnl, cost, (100 * pnl / cost if cost else 0)
    print("=" * 100)
    print(f"{book}   {len(rows)} legs / {len(by)} events")
    for lbl, gs in (("single-leg events", single), ("MULTI-leg events", multi)):
        ne, nl, pnl, cost, roi = agg(gs)
        print(f"  {lbl:20} {ne:3d} events {nl:3d} legs   PnL {pnl:+8.2f} on ${cost:8.2f}  ({roi:+6.2f}%)")
    if multi:
        print(f"  multi-leg events in detail:")
        for g in sorted(multi, key=lambda g: sum(f(r.get('pnl')) for r in g)):
            pnl = sum(f(r.get("pnl")) for r in g)
            cost = sum(f(r.get("cost")) for r in g)
            print(f"     {len(g)} legs  PnL {pnl:+8.2f} on ${cost:7.2f}   "
                  f"{(g[0].get('question') or '')[:46]}")
        # counterfactual: keep only the FIRST leg opened per event (what a 1-leg cap would have done)
        kept = [sorted(g, key=lambda r: r.get("ts_open", ""))[0] for g in by.values()]
        pnl_k = sum(f(r.get("pnl")) for r in kept)
        cost_k = sum(f(r.get("cost")) for r in kept)
        pnl_a = sum(f(r.get("pnl")) for r in rows)
        cost_a = sum(f(r.get("cost")) for r in rows)
        print(f"  COUNTERFACTUAL 1 leg/event (keep the first opened):")
        print(f"     actual : {len(rows):3d} legs  PnL {pnl_a:+8.2f} on ${cost_a:8.2f} "
              f"({100*pnl_a/cost_a if cost_a else 0:+6.2f}%)")
        print(f"     capped : {len(kept):3d} legs  PnL {pnl_k:+8.2f} on ${cost_k:8.2f} "
              f"({100*pnl_k/cost_k if cost_k else 0:+6.2f}%)")
        print(f"     -> {pnl_k-pnl_a:+.2f} PnL on {cost_a-cost_k:+.2f} less capital deployed")
    print()

# open exposure right now
print("=" * 100)
print("OPEN multi-leg exposure right now (what the cap would prevent going forward)")
print("=" * 100)
for book in ("secondfav", "secondfav2", "carry"):
    p = os.path.join(OUT, f"paper_positions_{book}.csv")
    if not os.path.exists(p): continue
    pos = list(csv.DictReader(open(p, encoding="utf-8")))
    by = collections.defaultdict(list)
    for r in pos: by[r.get("event_id")].append(r)
    multi = {k: g for k, g in by.items() if len(g) > 1}
    exp = sum(f(r.get("cost")) for g in multi.values() for r in g)
    print(f"  {book:11} {len(pos):3d} open legs / {len(by):3d} events | "
          f"{len(multi)} events hold >1 leg, ${exp:.2f} exposed")
    for k, g in multi.items():
        print(f"       {len(g)} legs ${sum(f(r.get('cost')) for r in g):6.2f}  "
              f"{(g[0].get('question') or '')[:50]}")
