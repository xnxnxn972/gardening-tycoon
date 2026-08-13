"""WHY DID MY 'VERIFIED PARTITION' FILTER COLLAPSE THE EDGE TO ~ZERO?

resolve_conflict.py showed the edge is real and that partition-ness was never the issue: 100% of
negRisk 6<=N<=40 events are true partitions, so filtering on partition-ness removes nothing.
The collapse in partition_ev3.py must therefore come from its OTHER two requirements -- >=80% of the
field carrying a fresh bar, and the priced legs summing to 0.90-1.15.

HYPOTHESIS: those requirements preferentially keep NUMERIC events. A numeric threshold ladder (ISM
PMI, JOLTS, "how many jobs") has every rung actively quoted, so it passes a coverage test easily,
while a candidate field has dead longshots that never trade and fails it. Since NUMERIC carries only
+7.50pt against EVENT's +25.70pt, a coverage filter silently swaps the strong half for the weak half.

Measures the NUMERIC share before and after those filters. If it jumps, the mystery is closed.
"""
import json, os, re, sys, time, urllib.request, urllib.parse, datetime, collections

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
    s = H.get(str(tok))
    if not s: return None, False
    prev = pt = None
    for t, p in s:
        if t <= ts: prev, pt = p, t
        else: break
    return (None, False) if prev is None else (prev, (ts - pt) < 86400)


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
            if not (6 <= len(ms) <= 40): continue
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
                p, fr = px(tk[0], int(en.timestamp()) - 3 * 86400)
                if p is None or not fr: continue
                legs.append({"won": 1 if y > 0.5 else 0, "p": p, "en": en,
                             "numeric": bool(NUMFAM.search((m.get("question") or "").lower()))})
            if legs:
                events.append({"legs": legs, "nmk": len(ms)})


def band_legs(evs):
    out = []
    for e in evs:
        out += [l for l in e["legs"] if 0.35 <= l["p"] < 0.50]
    return out


def numeric_share(sel):
    return (100 * sum(1 for l in sel if l["numeric"]) / len(sel)) if sel else 0


def edge(sel):
    if not sel: return 0
    return -100 * sum(l["won"] - l["p"] for l in sel) / len(sel)


allb = band_legs(events)
# partition_ev3's filters, applied in sequence
f1 = [e for e in events if len(e["legs"]) >= max(6, int(0.8 * e["nmk"]))]
f2 = [e for e in f1
      if (max(l["en"] for l in e["legs"]) - min(l["en"] for l in e["legs"])).days <= 1]
f3 = [e for e in f2 if 0.90 <= sum(l["p"] for l in e["legs"]) <= 1.15]

print("=" * 104)
print(f"{'filter applied':44} {'events':>7} {'band legs':>10} {'NUMERIC %':>10} {'NO edge':>9}")
print("=" * 104)
for lbl, evs in (("none (all negRisk 6<=N<=40, fresh legs)", events),
                 ("+ >=80% of the field priced", f1),
                 ("+ shared endDate (span <=1d)", f2),
                 ("+ price sum in [0.90, 1.15]", f3)):
    b = band_legs(evs)
    print(f"  {lbl:42} {len(evs):7d} {len(b):10d} {numeric_share(b):9.0f}% {edge(b):+8.2f}pt")

print("\n  For reference, measured separately on the unfiltered set:")
print(f"    EVENT   band legs: n={sum(1 for l in allb if not l['numeric']):4d}  "
      f"NO edge {edge([l for l in allb if not l['numeric']]):+.2f}pt")
print(f"    NUMERIC band legs: n={sum(1 for l in allb if l['numeric']):4d}  "
      f"NO edge {edge([l for l in allb if l['numeric']]):+.2f}pt")
