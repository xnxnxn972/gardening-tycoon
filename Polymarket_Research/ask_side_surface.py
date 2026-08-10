"""ASK-SIDE RE-VALIDATION — does the calibration surface survive when measured on prices you could
actually BUY at, rather than on mids?

WHY (2026-08-10). Three buy-side books have now been validated on mid/last-trade price series and have
all failed live in the same direction:
    res-lag 0.90-0.95   predicted 95% wins, realized 25%   (diagnosed as adverse selection, 2026-07-04)
    favbuy  0.80-0.90   predicted +5.9pt,  realized -7.4pt vs the MID, own edge anti-predictive
    geobuy  mid-band    predicted +18.6pt, realized -7.5pt vs the MID
A price is a two-sided object. Our surface answered "what do PRICES predict?" and every buy-side book
assumed that transfers to "what do prices SOMEONE WILL SELL ME predict?" Those are different
populations: the offered subset is chosen by the seller, and we bring no information they lack.

THE MEASUREMENT. From the 9.5M-fill tape (2,501 resolved markets with known outcomes), for each market
take the fills in a horizon window and compute, MARKET-LEVEL (one observation per market, matching the
research method):
    mean price of TAKER-BUY fills   -> what a buyer actually paid (a lifted ask)
    mean price of ALL fills         -> the mid-ish consensus the old surface was built on
    mean price of TAKER-SELL fills  -> what a seller received (a hit bid)
then gap = won - price for each. The DIFFERENCE between gap_all and gap_buy is the adverse-selection
cost, and it is exactly the term every buy-side book has been missing.
"""
import csv, os, sys, math, datetime, collections, statistics as st

HERE = os.path.dirname(os.path.abspath(__file__))
TAPE = os.path.join(HERE, "tape_event", "tape.csv")
MAN = os.path.join(HERE, "tape_event", "manifest.csv")
TTE_LO, TTE_HI = float(os.environ.get("TTE_LO", 1.0)), float(os.environ.get("TTE_HI", 7.0))
BANDS = [(0.05,0.20),(0.20,0.35),(0.35,0.50),(0.50,0.65),(0.65,0.80),(0.80,0.90),(0.90,0.97)]
MIN_FILLS = 3            # per market per side, inside the window

def band_of(p):
    for lo, hi in BANDS:
        if lo <= p < hi: return f"{lo:.2f}-{hi:.2f}"
    return None

man = {}
for r in csv.DictReader(open(MAN, encoding="utf-8")):
    try:
        end = datetime.datetime.strptime(r["end"][:10], "%Y-%m-%d").replace(tzinfo=datetime.timezone.utc)
    except Exception:
        continue
    if r.get("won") not in ("0", "1"): continue
    man[r["mid"]] = {"won": int(r["won"]), "end": end.timestamp(), "cat": r.get("cat", ""), "q": r.get("q", "")[:60]}
print(f"manifest: {len(man)} resolved markets with a known outcome")

acc = collections.defaultdict(lambda: {"b": [0.0, 0], "s": [0.0, 0], "a": [0.0, 0]})
n = kept = 0
with open(TAPE, encoding="utf-8") as fh:
    for row in csv.DictReader(fh):
        n += 1
        m = man.get(row["mid"])
        if not m: continue
        try:
            ts = float(row["ts"]); p = float(row["price"])
        except Exception: continue
        tte = (m["end"] - ts) / 86400.0
        if not (TTE_LO <= tte <= TTE_HI): continue
        if not (0.0 < p < 1.0): continue
        # OUTCOME-INDEX CORRECTION. `oi` is Polymarket's outcomeIndex: 0=YES, 1=NO, and `price` is the
        # price of THAT token. Treating them alike mixes NO prices into a YES probability and produced
        # mean price 0.596 against a 0.191 win rate — caught by the sanity check below before it was
        # reported. Convert everything to YES terms:
        #   YES price   = p (oi=0) or 1-p (oi=1)
        # AND the side inverts with the token: acquiring YES exposure means LIFTING THE YES ASK, which
        # is (oi=0 & BUY) or (oi=1 & SELL) — buying NO is selling YES.
        oi = row["oi"]
        py = p if oi == "0" else 1.0 - p
        lifts_ask = (oi == "0" and row["side"] == "BUY") or (oi == "1" and row["side"] == "SELL")
        kept += 1
        A = acc[row["mid"]]
        A["a"][0] += py; A["a"][1] += 1
        k = "b" if lifts_ask else "s"
        A[k][0] += py; A[k][1] += 1
print(f"tape: {n:,} fills scanned, {kept:,} inside T-{TTE_HI:.0f}d..T-{TTE_LO:.0f}d\n")

rows = []
for mid, A in acc.items():
    if A["b"][1] < MIN_FILLS or A["a"][1] < MIN_FILLS: continue
    m = man[mid]
    rows.append({"mid": mid, "won": m["won"], "cat": m["cat"], "end": m["end"], "q": m["q"],
                 "p_all": A["a"][0]/A["a"][1], "p_buy": A["b"][0]/A["b"][1],
                 "p_sell": (A["s"][0]/A["s"][1]) if A["s"][1] >= MIN_FILLS else None})
print(f"{len(rows)} markets with >= {MIN_FILLS} buy fills in the window")

# convention sanity check: mean price near expiry should approximate the win rate
mp = st.mean(r["p_all"] for r in rows); wr = st.mean(r["won"] for r in rows)
print(f"SANITY: mean all-fill price {mp:.3f} vs realized win rate {wr:.3f} "
      f"-> {'consistent (prices are YES-denominated)' if abs(mp-wr) < 0.12 else 'MISMATCH - check conventions'}\n")

rows.sort(key=lambda r: r["end"])
SPLIT = rows[len(rows)//2]["end"] if rows else 0

def stat(v):
    k = len(v)
    if k < 2: return 0.0, 0.0, k
    m = st.mean(v); sd = st.stdev(v)
    return m, (m/(sd/math.sqrt(k)) if sd > 0 else 0.0), k

def report(title, sel):
    print("=" * 108)
    print(title)
    print("=" * 108)
    print(f"  {'band':<12}{'n':>5}  {'gap vs ALL(mid)':>17}  {'gap vs BUY(ask)':>17}  {'adverse-sel cost':>17}")
    for lo, hi in BANDS:
        bl = f"{lo:.2f}-{hi:.2f}"
        S = [r for r in sel if band_of(r["p_all"]) == bl]
        if len(S) < 25:
            if S: print(f"  {bl:<12}{len(S):>5}  (thin)")
            continue
        ga = [r["won"]-r["p_all"] for r in S]
        gb = [r["won"]-r["p_buy"] for r in S]
        ma, za, _ = stat(ga); mb, zb, _ = stat(gb)
        tr = [r["won"]-r["p_buy"] for r in S if r["end"] < SPLIT]
        te = [r["won"]-r["p_buy"] for r in S if r["end"] >= SPLIT]
        _, ztr, _ = stat(tr); _, zte, _ = stat(te)
        surv = "SURVIVES" if (abs(zb) >= 2.5 and ztr*zte > 0 and abs(zte) >= 1.5 and mb > 0) else ""
        print(f"  {bl:<12}{len(S):>5}  {100*ma:>+8.2f}pt z{za:>+5.1f}  {100*mb:>+8.2f}pt z{zb:>+5.1f}  "
              f"{100*(mb-ma):>+8.2f}pt  {surv}")
    print()

report(f"ALL CATEGORIES   (T-{TTE_HI:.0f}d .. T-{TTE_LO:.0f}d, market-level, holdout {datetime.datetime.fromtimestamp(SPLIT, datetime.timezone.utc):%Y-%m-%d})", rows)
geo = [r for r in rows if r["cat"] in ("geopolitics", "world")]
if len(geo) >= 50:
    report(f"GEOPOLITICS/WORLD ONLY  (geobuy's universe, n={len(geo)})", geo)

print("READ IT LIKE THIS:")
print("  'gap vs ALL(mid)'  reproduces the surface every buy-side book was built on.")
print("  'gap vs BUY(ask)'  is what a BUYER actually realizes, paying prices someone chose to offer.")
print("  'adverse-sel cost' is the difference. If it is large and negative, a positive mid-side surface")
print("  is NOT tradeable from the buy side, and that is the term all three failed books were missing.")
