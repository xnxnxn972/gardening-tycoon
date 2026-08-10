"""IS THERE A LEADING INDICATOR THAT A RES-LAG POSITION IS GOING BAD -- and could we exit cheaply?

The family wins ~$1.48 and loses ~$73, so an exit rule only has to work occasionally to matter. But it
only exists if the price MOVES BEFORE RESOLUTION. If a losing position sits at 0.97 and then snaps to 0
at settlement, there is nothing to react to and no exit is possible at any price.

For every settled leg we pull the bought token's price history between entry and close, and ask:
  1. Did the price fall below a threshold before resolution? (the trigger)
  2. How long before resolution did that happen? (is there time to act)
  3. What would exiting AT THAT PRICE have cost, versus riding it to zero?
Then score each threshold on losers caught vs winners falsely stopped out -- because stopping out a
winner costs the spread plus the ~2c of profit we came for.

Usage: python reslag_early_warning.py
"""
import csv, os, sys, json, math, time, datetime, urllib.request, urllib.parse, statistics as st

REPO = r"C:\Users\yaniv\polymarket-paper-trader"
CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reslag_px_cache.json")
CLOB = "https://clob.polymarket.com"
UA = {"User-Agent": "Mozilla/5.0"}
PACE = 0.30

cache = {}
if os.path.exists(CACHE):
    try: cache = json.load(open(CACHE, encoding="utf-8"))
    except Exception: cache = {}

def hist(tok):
    if tok in cache: return cache[tok]
    d = None
    for i in range(3):
        try:
            u = CLOB + "/prices-history?" + urllib.parse.urlencode(
                {"market": tok, "interval": "max", "fidelity": "10"})
            with urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=30) as r:
                d = json.load(r); break
        except Exception: time.sleep(1.0*(i+1))
    cache[tok] = [[int(x["t"]), float(x["p"])] for x in (d or {}).get("history") or []]
    time.sleep(PACE)
    return cache[tok]

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
        if not (o and c): continue
        legs.append({"book": b, "tok": r["no_token"], "o": o, "c": c, "ask": float(r["no_ask"]),
                     "pnl": float(r["pnl"]), "cost": float(r["cost"]), "shares": float(r["shares"]),
                     "loss": float(r["pnl"]) < 0, "q": r["question"][:52]})
L = [x for x in legs if x["loss"]]; W = [x for x in legs if not x["loss"]]
# price history is the expensive part: take every loser, and a capped sample of winners
W = sorted(W, key=lambda x: -x["cost"])[:140]
print(f"pulling price history for {len(L)} losers + {len(W)} winners (largest by cost)...")

for i, x in enumerate(L + W):
    h = hist(x["tok"])
    seg = [(t, p) for t, p in h if x["o"] <= t <= x["c"]]
    x["seg"] = seg
    x["min_px"] = min((p for _, p in seg), default=None)
    x["min_t"] = min(((p, t) for t, p in seg), default=(None, None))[1]
    if (i+1) % 40 == 0:
        json.dump(cache, open(CACHE, "w")); print(f"  {i+1}/{len(L)+len(W)}")
json.dump(cache, open(CACHE, "w"))

Lh = [x for x in L if x["seg"]]; Wh = [x for x in W if x["seg"]]
print(f"  usable: {len(Lh)}/{len(L)} losers, {len(Wh)}/{len(W)} winners\n")
if not Lh: raise SystemExit("no price history for the losers - cannot answer")

print("DID THE LOSERS TELEGRAPH? (bought token's lowest price between entry and resolution)")
print(f"  {'':<10}{'entry':>7}{'min px':>9}{'drop':>8}{'hrs before close':>18}")
for x in sorted(Lh, key=lambda y: y["pnl"]):
    hrs = (x["c"]-x["min_t"])/3600.0 if x["min_t"] else 0
    print(f"  {x['book']:<10}{x['ask']:>7.3f}{x['min_px']:>9.3f}{x['ask']-x['min_px']:>8.3f}{hrs:>18.1f}   {x['q'][:44]}")
print()
print(f"  losers : median min-price {st.median(x['min_px'] for x in Lh):.3f}")
print(f"  winners: median min-price {st.median(x['min_px'] for x in Wh):.3f}")
print()

print("STOP-LOSS RULE: exit the moment the bought token trades below THRESH")
print(f"  {'thresh':>7}{'losers caught':>15}{'saved$':>10}{'winners hit':>13}{'cost$':>10}{'NET':>10}")
for th in (0.90, 0.85, 0.80, 0.70, 0.60, 0.50):
    sl = sc = 0.0; nl = nw = 0
    for x in Lh:
        if x["min_px"] is not None and x["min_px"] < th:
            nl += 1
            sl += (th*x["shares"] - x["cost"]) - x["pnl"]      # exit at thresh instead of riding to 0
    for x in Wh:
        if x["min_px"] is not None and x["min_px"] < th:
            nw += 1
            sc += x["pnl"] - (th*x["shares"] - x["cost"])      # forgone: we bail on an eventual winner
    print(f"  {th:>7.2f}{nl:>8}/{len(Lh):<6}{sl:>10.2f}{nw:>8}/{len(Wh):<4}{-sc:>10.2f}{sl-sc:>+10.2f}")
print()
print("  'saved$'  = loss avoided by exiting at the threshold rather than settling at zero")
print("  'cost$'   = profit given up on winners that dipped through the threshold and recovered")
print("  NET > 0 means the rule would have paid for itself ON THIS SAMPLE.")
