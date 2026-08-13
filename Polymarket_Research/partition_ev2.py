"""SAME TEST, RESTRICTED TO REAL PARTITIONS.

partition_ev.py was confounded: it grouped ANY event with >=6 markets, so "22 legs in the 0.35-0.50
band" showed up -- impossible in a partition, where YES prices sum to ~1. Those are bundles of
INDEPENDENT binaries (22 separate questions in one event page), a different animal with no
mutual-exclusivity constraint at all, and they dominated the 3+ bucket that carried the whole effect.

secondfav's thesis is negRisk PARTITIONS. Restrict to negRisk events, verify the YES prices actually
sum to ~1, and only then ask the question: within a real partition, does holding a second band leg
cost expected value?

In a genuine partition at most 2-3 legs can sit in 0.35-0.50 at once (2 legs there already account
for 0.70-1.00 of the field), so the comparison that matters is k=1 vs k=2.
"""
import json, os, sys, time, urllib.request, urllib.parse, datetime, collections

GAMMA = "https://gamma-api.polymarket.com"; UA = {"User-Agent": "Mozilla/5.0"}
RESD = r"C:\Users\yaniv\OneDrive\Projects\Polymarket_Research"
PAGES = int(sys.argv[1]) if len(sys.argv) > 1 else 18
TAGS = {"politics": "2", "geopolitics": "100265", "pop-culture": "596", "tweets-markets": "972",
        "elections": "144", "world": "101970", "economy": "100328", "tech": "1401", "business": "107"}
EXCLUDE = {"crypto", "sports", "soccer", "fifa-world-cup", "basketball", "tennis", "nfl", "nba",
           "mlb", "nhl", "baseball", "football", "games"}


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


def fresh(tok, ts):
    s = H.get(str(tok))
    if not s: return None
    prev = pt = None
    for t, p in s:
        if t <= ts: prev, pt = p, t
        else: break
    return None if (prev is None or (ts - pt) >= 86400) else prev


print(f"enumerating {PAGES} pages/tag, negRisk events only...")
events = []; seen = set(); n_neg = 0
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
            if e.get("negRisk") is not True: continue          # PARTITIONS ONLY
            seen.add(eid); n_neg += 1
            ms = e.get("markets") or []
            if len(ms) < 6: continue                            # secondfav requires N>=6
            legs = []
            for m in ms:
                tk, pr = jload(m.get("clobTokenIds")), jload(m.get("outcomePrices"))
                if not tk or not pr: continue
                y = fnum(pr[0])
                if y is None or 0.02 < y < 0.98: continue
                try:
                    en = datetime.datetime.fromisoformat(
                        ((m.get("endDate") or e.get("endDate") or "")[:19]).replace("Z", "")
                    ).replace(tzinfo=datetime.timezone.utc)
                except Exception:
                    continue
                p = fresh(tk[0], int(en.timestamp()) - 3 * 86400)
                if p is None: continue
                legs.append({"won": 1 if y > 0.5 else 0, "p": p, "en": en, "N": len(ms)})
            # only keep events where we priced MOST of the field, else "legs in band" is meaningless
            if len(legs) >= max(6, int(0.8 * len(ms))):
                events.append(legs)
print(f"  {n_neg} negRisk events seen | {len(events)} with >=80% of the field priced")
if events:
    sums = sorted(sum(l["p"] for l in e) for e in events)
    print(f"  sanity -- YES price sum per event: median {sums[len(sums)//2]:.3f} "
          f"(a real partition sums to ~1.0)")
    wins = [sum(l["won"] for l in e) for e in events]
    print(f"  sanity -- winners per event: {collections.Counter(wins)}  (a partition has exactly 1)\n")

inband = []
for legs in events:
    band = [l for l in legs if 0.35 <= l["p"] < 0.50]
    for l in band:
        l["k"] = len(band)
    inband += band
inband.sort(key=lambda r: r["en"])
if not inband:
    print("no legs in band"); sys.exit()
SPLIT = inband[len(inband) // 2]["en"]


def rep(lbl, sel):
    n = len(sel)
    if n < 20:
        print(f"  {lbl:38} n={n:4d} (thin)"); return
    v = [r["won"] - r["p"] for r in sel]
    m = sum(v) / n
    sd = (sum((x - m) ** 2 for x in v) / (n - 1)) ** 0.5
    z = m / (sd / n ** 0.5) if sd else 0
    tr = [r["won"] - r["p"] for r in sel if r["en"] < SPLIT]
    te = [r["won"] - r["p"] for r in sel if r["en"] >= SPLIT]
    mtr = sum(tr) / len(tr) if tr else 0
    mte = sum(te) / len(te) if te else 0
    print(f"  {lbl:38} n={n:4d}  YES gap {100*m:+6.2f}pt z{z:+5.1f}  "
          f"NO-side edge {-100*m:+6.2f}pt  [{100*mtr:+5.1f}/{100*mte:+5.1f}]")


print("=" * 100)
print("WITHIN REAL PARTITIONS: does a second band leg cost expected value?")
print("=" * 100)
rep("ALL band legs", inband)
rep("event has exactly 1 leg in band", [r for r in inband if r["k"] == 1])
rep("event has 2 legs in band", [r for r in inband if r["k"] == 2])
rep("event has 3+ legs in band", [r for r in inband if r["k"] >= 3])
print(f"\n  legs-in-band distribution: {dict(sorted(collections.Counter(r['k'] for r in inband).items()))}")
mult = sum(1 for r in inband if r["k"] > 1)
print(f"  share of band legs in a multi-band-leg partition: {100*mult/len(inband):.0f}%")
