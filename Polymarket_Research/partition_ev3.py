"""WHAT ARE THE 'events with 3+ legs in 0.35-0.50' ACTUALLY?

In a partition the YES prices sum to ~1, so three legs at 0.35-0.50 (>=1.05 on their own) is close to
impossible and eight is flatly impossible. Yet that bucket exists, holds 164 legs, and carries the
ENTIRE measured edge (-24.99pt z-8.4) while k=1 and k=2 show ~nothing (-1.15pt, -2.54pt).

Either those events are not really partitions, or the prices I am reading for them are not
contemporaneous -- each leg is snapshotted at ITS OWN endDate minus 3d, so an event whose markets
resolve on different dates is priced at different moments and the "sum" is not a real book state.
Both would matter well beyond the leg-cap question, because that bucket is where the measured edge lives.

Prints price sum, leg count and endDate spread per bucket.
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


events = []; seen = set()
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
            if len(ms) < 6: continue
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
                legs.append({"won": 1 if y > 0.5 else 0, "p": p, "en": en})
            if len(legs) >= max(6, int(0.8 * len(ms))):
                events.append({"legs": legs, "title": (e.get("title") or "")[:50]})

buckets = collections.defaultdict(list)
for ev in events:
    k = sum(1 for l in ev["legs"] if 0.35 <= l["p"] < 0.50)
    if k:
        buckets[min(k, 3)].append(ev)

print("=" * 100)
print(f"{'k in band':12} {'events':>7} {'median sum':>12} {'max sum':>9} {'median endDate spread':>22}")
print("=" * 100)
for k in sorted(buckets):
    evs = buckets[k]
    sums = sorted(sum(l["p"] for l in e["legs"]) for e in evs)
    spans = sorted((max(l["en"] for l in e["legs"]) - min(l["en"] for l in e["legs"])).days for e in evs)
    lbl = f"k = {k}" if k < 3 else "k >= 3"
    print(f"  {lbl:10} {len(evs):7d} {sums[len(sums)//2]:12.3f} {sums[-1]:9.2f} {spans[len(spans)//2]:19d}d")

print()
for k in sorted(buckets):
    evs = sorted(buckets[k], key=lambda e: -sum(l["p"] for l in e["legs"]))
    lbl = f"k = {k}" if k < 3 else "k >= 3"
    print(f"  {lbl} -- largest price sums (a real partition cannot exceed ~1.05):")
    for e in evs[:3]:
        s = sum(l["p"] for l in e["legs"])
        nb = sum(1 for l in e["legs"] if 0.35 <= l["p"] < 0.50)
        span = (max(l["en"] for l in e["legs"]) - min(l["en"] for l in e["legs"])).days
        print(f"     sum {s:6.2f}  {len(e['legs'])} legs, {nb} in band, endDates span {span:3d}d  {e['title']}")
    print()

# The clean test: partitions whose legs all share an endDate (so the snapshot IS contemporaneous)
tight = [e for e in events
         if (max(l["en"] for l in e["legs"]) - min(l["en"] for l in e["legs"])).days <= 1
         and 0.90 <= sum(l["p"] for l in e["legs"]) <= 1.15]
print("=" * 100)
print(f"CLEAN SUBSET: {len(tight)} partitions with a shared endDate AND a price sum in [0.90,1.15]")
print("=" * 100)
inb = []
for e in tight:
    band = [l for l in e["legs"] if 0.35 <= l["p"] < 0.50]
    for l in band: l["k"] = len(band)
    inb += band
if inb:
    inb.sort(key=lambda r: r["en"])
    SPLIT = inb[len(inb) // 2]["en"]
    def rep(lbl, sel):
        n = len(sel)
        if n < 20:
            print(f"  {lbl:34} n={n:4d} (thin)"); return
        v = [r["won"] - r["p"] for r in sel]
        m = sum(v) / n
        sd = (sum((x - m) ** 2 for x in v) / (n - 1)) ** 0.5
        tr = [r["won"] - r["p"] for r in sel if r["en"] < SPLIT]
        te = [r["won"] - r["p"] for r in sel if r["en"] >= SPLIT]
        print(f"  {lbl:34} n={n:4d}  YES gap {100*m:+6.2f}pt z{m/(sd/n**0.5):+5.1f}  "
              f"NO edge {-100*m:+6.2f}pt  [{100*(sum(tr)/len(tr) if tr else 0):+5.1f}/"
              f"{100*(sum(te)/len(te) if te else 0):+5.1f}]")
    rep("all band legs", inb)
    rep("k = 1", [r for r in inb if r["k"] == 1])
    rep("k = 2", [r for r in inb if r["k"] == 2])
    rep("k >= 3", [r for r in inb if r["k"] >= 3])
    print(f"\n  k distribution: {dict(sorted(collections.Counter(r['k'] for r in inb).items()))}")
