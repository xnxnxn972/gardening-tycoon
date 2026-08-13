"""DOES HOLDING TWO LEGS OF ONE PARTITION COST EXPECTED VALUE, OR ONLY ADD VARIANCE?

I told the user multi-leg partition exposure "converts edge into variance and fees". That is wrong as
stated. EV is ADDITIVE across legs no matter how correlated they are: two legs each carrying +15pt of
edge carry +30pt together. Correlation moves variance, not the mean. secondfav's -26.25% on three
multi-leg events cannot distinguish an EV drain from an unlucky high-variance configuration.

So before changing selection logic, test the EV question on history rather than on 3 events.

THE TEST. In secondfav's cell (0.35-0.50 YES, field size N>=6, fresh price), split resolved legs by
whether their EVENT had ONE leg in the band or SEVERAL. If the band edge is genuinely per-leg, both
groups show the same gap and a cap is only a variance/capital decision. If events with several legs
in the band show a WORSE gap, the edge is per-event rather than per-leg and the cap earns its keep on
EV too.

There is a real mechanism that would produce the second result: in a partition the YES prices sum to
~1, so two legs both sitting at 0.35-0.50 already account for 0.70-1.00 of the whole field. A band
that is "overpriced on average" cannot be overpriced on two legs that between them are nearly the
entire probability mass -- the overpricing has to be coming from somewhere, and in that configuration
there is nowhere for it to come from.
"""
import json, os, sys, time, math, urllib.request, urllib.parse, datetime, collections

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


print(f"enumerating {PAGES} pages/tag, grouping by EVENT...")
events = []
seen = set()
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
            seen.add(eid)
            ms = e.get("markets") or []
            if len(ms) < 6: continue                     # secondfav requires N>=6
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
            if legs: events.append(legs)
print(f"  {len(events)} events with usable fresh legs\n")

# how many legs of each event sit in secondfav's band?
inband = []
for legs in events:
    band = [l for l in legs if 0.35 <= l["p"] < 0.50]
    for l in band:
        l["k_in_band"] = len(band)
        l["band_mass"] = sum(x["p"] for x in band)
    inband += band
inband.sort(key=lambda r: r["en"])
if not inband:
    print("no legs in band"); sys.exit()
SPLIT = inband[len(inband) // 2]["en"]


def rep(lbl, sel):
    n = len(sel)
    if n < 25:
        print(f"  {lbl:38} n={n:5d} (thin)"); return
    # secondfav BUYS NO, so its edge is the NEGATIVE of the YES gap
    v = [r["won"] - r["p"] for r in sel]
    m = sum(v) / n
    sd = (sum((x - m) ** 2 for x in v) / (n - 1)) ** 0.5
    z = m / (sd / n ** 0.5) if sd else 0
    tr = [r["won"] - r["p"] for r in sel if r["en"] < SPLIT]
    te = [r["won"] - r["p"] for r in sel if r["en"] >= SPLIT]
    mtr = sum(tr) / len(tr) if tr else 0
    mte = sum(te) / len(te) if te else 0
    print(f"  {lbl:38} n={n:5d}  YES gap {100*m:+6.2f}pt z{z:+5.1f}  "
          f"-> NO-side edge {-100*m:+6.2f}pt   [{100*mtr:+5.1f}/{100*mte:+5.1f}]")


print("=" * 104)
print("secondfav cell (0.35-0.50, N>=6, fresh): does the edge survive when the EVENT has")
print("more than one leg in the band?")
print("=" * 104)
rep("ALL legs in band", inband)
rep("events with exactly 1 leg in band", [r for r in inband if r["k_in_band"] == 1])
rep("events with 2 legs in band", [r for r in inband if r["k_in_band"] == 2])
rep("events with 3+ legs in band", [r for r in inband if r["k_in_band"] >= 3])
print()
rep("band mass < 0.50", [r for r in inband if r["band_mass"] < 0.50])
rep("band mass 0.50-0.85", [r for r in inband if 0.50 <= r["band_mass"] < 0.85])
rep("band mass >= 0.85", [r for r in inband if r["band_mass"] >= 0.85])

d = collections.Counter(r["k_in_band"] for r in inband)
print(f"\n  distribution of legs-in-band per event: {dict(sorted(d.items()))}")
mult = sum(1 for r in inband if r["k_in_band"] > 1)
print(f"  share of band legs sitting in a multi-leg-in-band event: "
      f"{100*mult/len(inband):.0f}%")
