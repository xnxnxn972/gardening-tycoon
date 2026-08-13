"""RESOLVING THE SECONDFAV PARTITION CONFLICT BEFORE THE 30-CLUSTER CHECKPOINT.

TWO MEASUREMENTS OF THE SAME CELL DISAGREE BY 25 POINTS:
  numfam_split.py (2026-07-29, the basis secondfav trades on):
      negRisk x N>=11 x 0.35-0.50, EVENT (non-NUMFAM):  n=323  -26.0pt  z-12.4  SURVIVES holdout
      same cell, NUMERIC (NUMFAM):                      n=229   -7.4pt  z -2.4  fails
  partition_ev3.py (today):
      verified partitions only (negRisk + shared endDate + YES sum 0.90-1.15): -1.26pt  z-0.4

Three candidate explanations, and they are separable:

  H1  NUMFAM != NON-PARTITION. My "verified partition" filter and the NUMFAM text filter are different
      classifiers. The impossible-sum events I found (ISM PMI sum 4.53, JOLTS 4.49) are NUMERIC, so
      NUMFAM should already exclude them -- in which case my partition filter is removing something
      else, and the conflict is not about partitions at all.
  H2  MY COVERAGE FILTER IS THE BIAS. Requiring >=80% of the field to carry a FRESH bar selects events
      where nearly every leg traded in the last 24h, and requiring the sum to reach 0.90 selects events
      whose priced legs carry almost all the probability mass. Both bias toward a strong favourite with
      few live longshots -- exactly the shape where a 0.35-0.50 leg is NOT a mispriced second favourite.
  H3  LEG-LEVEL INFERENCE INFLATED EVERY z EVER QUOTED. All of these numbers -- mine and
      numfam_split's -- are per-LEG. An event contributing 8 band legs is ONE observation, not 8.
      z-12.4 and z-14.3 may be arithmetic on a sample size that does not exist.

DESIGN. Classify partitions by WINNER COUNT (exactly one market resolves YES), which is readable from
outcomePrices for every market and needs no pricing coverage at all -- so it carries none of H2's bias.
Then report the full factorial {EVENT, NUMERIC} x {partition, non-partition} with BOTH leg-level z and
EVENT-CLUSTERED bootstrap CIs, and attempt a direct reproduction of numfam_split's headline cell.
"""
import json, os, re, sys, time, math, random, urllib.request, urllib.parse, datetime, collections

GAMMA = "https://gamma-api.polymarket.com"; UA = {"User-Agent": "Mozilla/5.0"}
RESD = r"C:\Users\yaniv\OneDrive\Projects\Polymarket_Research"
PAGES = int(sys.argv[1]) if len(sys.argv) > 1 else 18
TAGS = {"politics": "2", "geopolitics": "100265", "pop-culture": "596", "tweets-markets": "972",
        "elections": "144", "world": "101970", "economy": "100328", "tech": "1401", "business": "107"}
EXCLUDE = {"crypto", "sports", "soccer", "fifa-world-cup", "basketball", "tennis", "nfl", "nba",
           "mlb", "nhl", "baseball", "football", "games"}
NUMFAM = re.compile(
    r"\d+\s*-\s*[\d,.]+\s*(?:posts|tweets|views|days)|posts? from|tweets from|# of|million views"
    r"|unemployment|jobs in|rate be|market cap|cpi\b|ppi\b|pce\b|gdp\b|inflation|capex|index be"
    r"|deliver between|between [\d$,.]+[km]? and|transits?\b|passengers|box office|netflix"
    r"|#\d+\s+(?:global|us)\b|top\s+(?:us|global|\d)|most.watched", re.I)
random.seed(21)


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


def jload(x):
    if isinstance(x, str):
        try: return json.loads(x)
        except Exception: return None
    return x


H = {k: [(int(t), float(p)) for t, p in v] for k, v in
     json.load(open(os.path.join(RESD, "daily_hist_cache.json"))).items()}


def px(tok, ts):
    """(last bar at or before ts, whether it is fresh (<24h))."""
    s = H.get(str(tok))
    if not s: return None, False
    prev = pt = None
    for t, p in s:
        if t <= ts: prev, pt = p, t
        else: break
    return (None, False) if prev is None else (prev, (ts - pt) < 86400)


print(f"enumerating {PAGES} pages/tag (negRisk events)...")
legs = []; seen = set(); nev = 0
for cat, tid in TAGS.items():
    for off in range(0, PAGES * 100, 100):
        page = get(f"{GAMMA}/events?" + urllib.parse.urlencode(
            {"tag_id": tid, "closed": "true", "limit": "100", "offset": str(off),
             "order": "startDate", "ascending": "false"}))
        if not page: break
        for e in page:
            eid = e.get("id")
            if not eid or eid in seen: continue
            if {t.get("slug") for t in (e.get("tags") or [])} & EXCLUDE: continue
            if e.get("negRisk") is not True: continue
            seen.add(eid)
            ms = e.get("markets") or []
            N = len(ms)
            if not (6 <= N <= 40): continue
            # WINNER COUNT over the WHOLE field -- needs no price data, so no coverage bias
            wins = 0; resolved = 0
            for m in ms:
                pr = jload(m.get("outcomePrices"))
                y = fnum(pr[0]) if pr else None
                if y is None: continue
                resolved += 1
                if y > 0.5: wins += 1
            if resolved < N: continue                 # only fully-resolved events can be classified
            nev += 1
            is_part = (wins == 1)
            for m in ms:
                tk, pr = jload(m.get("clobTokenIds")), jload(m.get("outcomePrices"))
                if not tk or not pr: continue
                y = fnum(pr[0])
                if y is None or 0.02 < y < 0.98: continue
                q = m.get("question") or ""
                try:
                    en = datetime.datetime.fromisoformat(
                        ((m.get("endDate") or e.get("endDate") or "")[:19]).replace("Z", "")
                    ).replace(tzinfo=datetime.timezone.utc)
                except Exception:
                    continue
                p, fr = px(tk[0], int(en.timestamp()) - 3 * 86400)
                if p is None: continue
                legs.append({"eid": eid, "won": 1 if y > 0.5 else 0, "p": p, "fresh": fr, "N": N,
                             "en": en, "numeric": bool(NUMFAM.search(q.lower())),
                             "part": is_part, "wins": wins})

legs.sort(key=lambda r: r["en"])
SPLIT = legs[len(legs) // 2]["en"]
print(f"  {nev} fully-resolved negRisk events with 6<=N<=40 | {len(legs)} priced legs")
wc = collections.Counter(r["wins"] for r in legs)
print(f"  winners-per-event across those legs: {dict(sorted(wc.items())[:6])} ...")
npart = len({r['eid'] for r in legs if r['part']}); nall = len({r['eid'] for r in legs})
print(f"  events that are TRUE partitions (exactly 1 winner): {npart}/{nall} "
      f"({100*npart/nall:.0f}%)\n")


def stat(sel, label, minn=25):
    """NO-side edge = -(won - p). Reports leg-level z (as previously quoted) AND event-clustered CI."""
    n = len(sel)
    if n < minn:
        print(f"  {label:44} n={n:5d}  (thin)"); return
    v = [-(r["won"] - r["p"]) for r in sel]
    m = sum(v) / n
    sd = (sum((x - m) ** 2 for x in v) / (n - 1)) ** 0.5
    zleg = m / (sd / n ** 0.5) if sd else 0
    by = collections.defaultdict(list)
    for r, x in zip(sel, v): by[r["eid"]].append(x)
    cl = [sum(g) / len(g) for g in by.values()]
    if len(cl) >= 3:
        d = sorted(sum(random.choice(cl) for _ in cl) / len(cl) for _ in range(8000))
        lo, hi = d[200], d[7799]
        ci = f"CI[{100*lo:+6.2f},{100*hi:+6.2f}]"
        sig = "  SIG" if lo > 0 or hi < 0 else ""
    else:
        ci, sig = "", ""
    tr = [x for r, x in zip(sel, v) if r["en"] < SPLIT]
    te = [x for r, x in zip(sel, v) if r["en"] >= SPLIT]
    mtr = sum(tr) / len(tr) if tr else 0
    mte = sum(te) / len(te) if te else 0
    print(f"  {label:44} n={n:5d} ({len(cl):4d} ev)  NO edge {100*m:+6.2f}pt  "
          f"z_leg{zleg:+6.1f}  {ci}{sig}  [{100*mtr:+5.1f}/{100*mte:+5.1f}]")


BAND = [r for r in legs if 0.35 <= r["p"] < 0.50]
print("=" * 118)
print("H3 FIRST -- how much of the headline z is leg-level arithmetic?")
print("=" * 118)
stat(BAND, "0.35-0.50, all negRisk N6-40")
stat([r for r in BAND if r["N"] >= 11], "0.35-0.50, N>=11 (numfam_split's cell)")

print("\n" + "=" * 118)
print("H1 -- IS 'NUMERIC' THE SAME THING AS 'NOT A PARTITION'?")
print("=" * 118)
ct = collections.Counter((r["numeric"], r["part"]) for r in BAND)
print(f"  band legs by (NUMERIC, is_partition):")
for k in sorted(ct, key=lambda k: (-ct[k])):
    print(f"     numeric={str(k[0]):5}  partition={str(k[1]):5}  n={ct[k]}")
nn = sum(v for k, v in ct.items() if k[0])
if nn:
    npp = sum(v for k, v in ct.items() if k[0] and k[1])
    print(f"  -> {100*npp/nn:.0f}% of NUMERIC band legs are nonetheless TRUE partitions, so the two "
          f"classifiers are NOT interchangeable")

print("\n" + "=" * 118)
print("THE FACTORIAL: {EVENT, NUMERIC} x {partition, non-partition},  N>=11, band 0.35-0.50")
print("=" * 118)
C = [r for r in BAND if r["N"] >= 11]
stat([r for r in C if not r["numeric"]], "EVENT   (secondfav's rule)  all")
stat([r for r in C if not r["numeric"] and r["part"]], "EVENT   x TRUE partition")
stat([r for r in C if not r["numeric"] and not r["part"]], "EVENT   x non-partition")
stat([r for r in C if r["numeric"]], "NUMERIC (excluded since 07-29)  all")
stat([r for r in C if r["numeric"] and r["part"]], "NUMERIC x TRUE partition")
stat([r for r in C if r["numeric"] and not r["part"]], "NUMERIC x non-partition")

print("\n" + "=" * 118)
print("H2 -- WAS MY COVERAGE/SUM FILTER THE BIAS? same cell, adding my filters one at a time")
print("=" * 118)
E = [r for r in C if not r["numeric"]]
stat(E, "EVENT x N>=11              (no extra filters)")
stat([r for r in E if r["part"]], "  + true partition")
stat([r for r in E if r["part"] and r["fresh"]], "  + true partition + FRESH price")

print("\n  secondfav trades on the LIVE mid with a 4c spread guard, so 'fresh' is the honest basis.")
print("  Read the clustered CI, not z_leg: the CI is the one that respects event clustering.")
