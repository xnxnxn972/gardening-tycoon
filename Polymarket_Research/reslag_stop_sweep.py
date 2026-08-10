"""FINE SWEEP of the res-lag stop-loss threshold, and WHY the cost column is non-monotonic.

  saved per loser        = th * shares          -> falls monotonically as th falls
  cost per winner hit    = shares * (1 - th)    -> RISES as th falls (you bail at a worse price)
  winners hit            = count(min_px < th)   -> falls as th falls
So total cost = (a falling count) x (a rising per-unit cost) and the product HUMPS. That is why 0.80
can cost more in total than 0.90 despite stopping out fewer winners.
Reads the price cache written by reslag_early_warning.py.
"""
import csv, os, json, datetime, statistics as st

REPO = r"C:\Users\yaniv\polymarket-paper-trader"
CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reslag_px_cache.json")
cache = json.load(open(CACHE, encoding="utf-8"))

def ts(s):
    for f in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S"):
        try: return datetime.datetime.strptime((s or "")[:19], f).replace(tzinfo=datetime.timezone.utc).timestamp()
        except Exception: pass
    return None

legs = []
for b in ("select", "scale", "lagsafe"):
    for r in csv.DictReader(open(os.path.join(REPO, f"paper_ledger_{b}.csv"), encoding="utf-8")):
        if not r.get("ts_close"): continue
        o, c = ts(r["ts_open"]), ts(r["ts_close"])
        h = cache.get(r["no_token"])
        if not (o and c and h): continue
        seg = [p for t, p in h if o <= t <= c]
        if not seg: continue
        legs.append({"loss": float(r["pnl"]) < 0, "pnl": float(r["pnl"]), "cost": float(r["cost"]),
                     "shares": float(r["shares"]), "min_px": min(seg)})
L = [x for x in legs if x["loss"]]; W = [x for x in legs if not x["loss"]]
print(f"{len(L)} losers, {len(W)} winners with price history\n")

print("WHERE DO WINNERS DIP TO? (the distribution that drives the whole trade-off)")
mins = sorted(x["min_px"] for x in W)
for q in (0.02, 0.05, 0.10, 0.25, 0.50):
    print(f"    {int(q*100):>2}th pct of winner min-price: {mins[int(q*len(mins))]:.3f}")
print(f"    losers: all {len(L)} have min-price <= {max(x['min_px'] for x in L):.3f}\n")

rows = []
for i in range(99, 0, -1):
    th = i / 100.0
    hitL = [x for x in L if x["min_px"] < th]
    hitW = [x for x in W if x["min_px"] < th]
    saved = sum((th*x["shares"] - x["cost"]) - x["pnl"] for x in hitL)
    cost = sum(x["pnl"] - (th*x["shares"] - x["cost"]) for x in hitW)
    rows.append((th, len(hitL), saved, len(hitW), cost, saved - cost))

print(f"{'th':>5}{'losers':>8}{'saved$':>10}{'winW':>6}{'cost$':>10}{'per-winner$':>13}{'NET$':>10}")
for th, nl, sv, nw, ct, net in rows:
    if round(th*100) % 5 and not (0.86 <= th <= 0.99): continue
    pw = ct/nw if nw else 0.0
    print(f"{th:>5.2f}{nl:>4}/{len(L):<3}{sv:>10.2f}{nw:>6}{-ct:>10.2f}{-pw:>13.2f}{net:>+10.2f}")

best = max(rows, key=lambda r: r[5])
print(f"\nOPTIMUM: threshold {best[0]:.2f} -> NET {best[5]:+.2f} "
      f"(catches {best[1]}/{len(L)} losers, stops out {best[3]} winners)")
top = sorted(rows, key=lambda r: -r[5])[:8]
print("top 8 thresholds:", ", ".join(f"{r[0]:.2f}({r[5]:+.0f})" for r in top))
lo = min(r[0] for r in top); hi = max(r[0] for r in top)
print(f"  the good region spans {lo:.2f}-{hi:.2f}; a single peak on {len(L)} losers is not a real optimum,")
print(f"  so the honest read is the RANGE, not the argmax.")
