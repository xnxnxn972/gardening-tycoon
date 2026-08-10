"""DOES GEOBUY SURVIVE THE ASK-SIDE RULE? (2026-08-10)

The standing rule adopted after favbuy: no buy-side book ships on a mid-side surface alone — it must
show a positive gap measured on ASK prices, on the population it will actually trade.

The general ask_side_surface.py run used T-7d..T-1d, which is the WRONG window for geobuy: its entire
thesis is that the edge lives in FAST resolvers (tte<=4d) and that draggers (4-14d) flip negative. So
that run both diluted the cohort geobuy trades and clipped the T-0.5d..T-1d slice it lives in.

This mirrors geobuy_harvester's actual rule as closely as the tape allows:
    geopolitics only | tte 0.5-4.0d | YES mid 0.35-0.80 | skip "on <date>" daily-drama
and compares, market-level with a temporal holdout:
    gap vs MID (the surface the book was built on)  vs  gap vs ASK (what a buyer realises)

Prices are converted to YES terms via the outcomeIndex, and "lifting the YES ask" is
(oi=0 & BUY) or (oi=1 & SELL) — buying NO is selling YES. Both corrections were bugs in the first pass.
"""
import csv, os, re, math, datetime, collections, statistics as st

HERE = os.path.dirname(os.path.abspath(__file__))
TAPE = os.path.join(HERE, "tape_event", "tape.csv")
MAN = os.path.join(HERE, "tape_event", "manifest.csv")
TTE_LO, TTE_HI = 0.5, 4.0                       # geobuy_harvester.TTE_LO / TTE_HI
BANDS = [(0.35, 0.50, 0.52), (0.50, 0.65, 0.72), (0.65, 0.80, 0.86)]   # its haircut trues
ONDATE = re.compile(r"\bon\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s*\d", re.I)
MIN_FILLS = 2

man = {}
for r in csv.DictReader(open(MAN, encoding="utf-8")):
    if r.get("cat") != "geopolitics" or r.get("won") not in ("0", "1"): continue
    try: end = datetime.datetime.strptime(r["end"][:10], "%Y-%m-%d").replace(tzinfo=datetime.timezone.utc)
    except Exception: continue
    q = r.get("q", "")
    man[r["mid"]] = {"won": int(r["won"]), "end": end.timestamp(), "q": q, "ondate": bool(ONDATE.search(q))}
print(f"geopolitics markets in the tape: {len(man)}  ({sum(1 for m in man.values() if m['ondate'])} are 'on <date>' daily-drama, excluded by the rule)")

acc = collections.defaultdict(lambda: {"b": [0.0, 0], "a": [0.0, 0]})
with open(TAPE, encoding="utf-8") as fh:
    for row in csv.DictReader(fh):
        m = man.get(row["mid"])
        if not m: continue
        try: ts = float(row["ts"]); p = float(row["price"])
        except Exception: continue
        if not (TTE_LO <= (m["end"] - ts) / 86400.0 <= TTE_HI): continue
        if not (0.0 < p < 1.0): continue
        oi = row["oi"]
        py = p if oi == "0" else 1.0 - p
        lift = (oi == "0" and row["side"] == "BUY") or (oi == "1" and row["side"] == "SELL")
        A = acc[row["mid"]]
        A["a"][0] += py; A["a"][1] += 1
        if lift: A["b"][0] += py; A["b"][1] += 1

rows = []
for mid, A in acc.items():
    if A["a"][1] < MIN_FILLS or A["b"][1] < MIN_FILLS: continue
    m = man[mid]
    if m["ondate"]: continue
    rows.append({"won": m["won"], "end": m["end"], "q": m["q"][:56],
                 "p_all": A["a"][0]/A["a"][1], "p_buy": A["b"][0]/A["b"][1]})
print(f"usable (>= {MIN_FILLS} buy fills inside T-{TTE_HI:g}d..T-{TTE_LO:g}d, non-daily-drama): {len(rows)}")
if not rows: raise SystemExit
mp = st.mean(r["p_all"] for r in rows); wr = st.mean(r["won"] for r in rows)
print(f"SANITY: mean YES price {mp:.3f} vs win rate {wr:.3f} -> "
      f"{'consistent' if abs(mp-wr) < 0.12 else 'MISMATCH'}\n")

rows.sort(key=lambda r: r["end"]); SPLIT = rows[len(rows)//2]["end"]
def stat(v):
    k = len(v)
    if k < 2: return 0.0, 0.0
    m = st.mean(v); sd = st.stdev(v)
    return m, (m/(sd/math.sqrt(k)) if sd > 0 else 0.0)

print("=" * 104)
print(f"GEOBUY'S EXACT CELL, ASK-SIDE   geopolitics | tte {TTE_LO}-{TTE_HI}d | holdout {datetime.datetime.fromtimestamp(SPLIT, datetime.timezone.utc):%Y-%m-%d}")
print("=" * 104)
print(f"  {'band':<12}{'n':>4} {'paid(ask)':>10} {'won':>7} | {'gap vs MID':>16} {'gap vs ASK':>16}  {'book claim':>12}")
allsel = []
for lo, hi, tv in BANDS:
    S = [r for r in rows if lo <= r["p_all"] < hi]
    allsel += S
    if len(S) < 12:
        print(f"  {lo:.2f}-{hi:.2f}   {len(S):>4}  (thin)"); continue
    ga = [r["won"]-r["p_all"] for r in S]; gb = [r["won"]-r["p_buy"] for r in S]
    ma, za = stat(ga); mb, zb = stat(gb)
    tr = [r["won"]-r["p_buy"] for r in S if r["end"] < SPLIT]
    te = [r["won"]-r["p_buy"] for r in S if r["end"] >= SPLIT]
    _, ztr = stat(tr); _, zte = stat(te)
    ok = (zb >= 2.5 and ztr*zte > 0 and abs(zte) >= 1.5 and mb > 0)
    claim = {0.35: "+12.4pt", 0.50: "+16.9pt", 0.65: "+18.4pt"}[lo]
    print(f"  {lo:.2f}-{hi:.2f}   {len(S):>4} {st.mean(r['p_buy'] for r in S):>10.3f} "
          f"{st.mean(r['won'] for r in S):>7.3f} | {100*ma:>+8.2f}pt z{za:>+5.1f} {100*mb:>+8.2f}pt z{zb:>+5.1f}  "
          f"{claim:>12}  {'PASSES' if ok else 'FAILS'}")
if len(allsel) >= 12:
    ga = [r["won"]-r["p_all"] for r in allsel]; gb = [r["won"]-r["p_buy"] for r in allsel]
    ma, za = stat(ga); mb, zb = stat(gb)
    tr = [r["won"]-r["p_buy"] for r in allsel if r["end"] < SPLIT]
    te = [r["won"]-r["p_buy"] for r in allsel if r["end"] >= SPLIT]
    _, ztr = stat(tr); _, zte = stat(te)
    ok = (zb >= 2.5 and ztr*zte > 0 and abs(zte) >= 1.5 and mb > 0)
    print(f"\n  {'0.35-0.80 (whole book)':<22} n={len(allsel)}  gap vs MID {100*ma:+.2f}pt (z{za:+.1f})  "
          f"gap vs ASK {100*mb:+.2f}pt (z{zb:+.1f})  TR z{ztr:+.1f} TE z{zte:+.1f}")
    print(f"  ASK-SIDE RULE: {'PASSES' if ok else 'FAILS'}   (needs gap>0, z>=2.5, same-sign halves, |TEST z|>=1.5)")
    print(f"  rule-level backtest claimed +12.6pt (z+4.7) on 209 clusters")
