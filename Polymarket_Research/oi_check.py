"""DOES THE OUTCOME-INDEX PROBLEM CONTAMINATE THE FAVBUY / GEOBUY SURFACE MEASUREMENTS?

`oi` (outcomeIndex) already caused one silent error this month: the ask-side tape analysis assumed
index 0 = YES, and half the prices were NO-denominated. It was only caught by a sanity check.

Every surface script I wrote (live_book_surface, fossil_carry_reslag, dead_markets, salvage_search,
favbuy_fieldsize) takes clobTokenIds[0] and outcomePrices[0] with NO check on `outcomes`. The live
books do check -- geobuy_harvester.py:146 and miner_harvester both skip anything that is not exactly
["Yes","No"]. So the research universe and the traded universe may not be the same universe, and the
research prices may not even be YES-denominated.

THREE DISTINCT FAILURES ARE POSSIBLE, and they need separating because only some would matter:

  1. INDEX MISALIGNMENT. If outcomePrices[i], clobTokenIds[i] and outcomes[i] are not parallel, then
     `won` and `p` describe different tokens and every number I have reported is garbage.

  2. DENOMINATION. If outcomes is ["No","Yes"], index 0 is the NO price. A market with NO at 0.85 has
     YES at 0.15 -- it enters my 0.80-0.90 band, but the live book bands on the YES mid and would
     never see it there. My cell and favbuy's cell would then contain different markets.

  3. UNIVERSE. Markets whose outcomes are neither Yes nor No (candidate names, Up/Down, teams) are in
     my measurement and excluded from every live book.

Test: recover the TRUE yes index from the `outcomes` labels, rebuild the cells YES-denominated and
restricted to the traded universe, and compare against what I reported. If the numbers hold, the
earlier conclusions stand; if they move, they move.
"""
import json, os, sys, time, math, urllib.request, urllib.parse, datetime, collections

GAMMA = "https://gamma-api.polymarket.com"; UA = {"User-Agent": "Mozilla/5.0"}
RESD = r"C:\Users\yaniv\OneDrive\Projects\Polymarket_Research"
PAGES = int(sys.argv[1]) if len(sys.argv) > 1 else 18
TAGS = {"politics": "2", "geopolitics": "100265", "pop-culture": "596", "tweets-markets": "972",
        "elections": "144", "world": "101970", "economy": "100328", "tech": "1401", "business": "107"}
EXCLUDE = {"crypto", "sports", "soccer", "fifa-world-cup", "basketball", "tennis", "nfl", "nba",
           "mlb", "nhl", "baseball", "football", "games"}
FEER = {"politics": .04, "elections": .04, "tech": .04, "tweets-markets": .04,
        "pop-culture": .05, "economy": .05, "business": .05, "world": .0, "geopolitics": .0}
HALF_SPREAD = 0.0095


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


def fresh_px(tok, ts):
    s = H.get(str(tok))
    if not s: return None
    prev = pt = None
    for t, p in s:
        if t <= ts: prev, pt = p, t
        else: break
    if prev is None or (ts - pt) >= 86400: return None
    return prev


print(f"enumerating {PAGES} pages/tag...")
rows = []; seen = set()
labels = collections.Counter(); nlab = collections.Counter()
for cat, tid in TAGS.items():
    for off in range(0, PAGES * 100, 100):
        page = get(f"{GAMMA}/events?" + urllib.parse.urlencode(
            {"tag_id": tid, "closed": "true", "limit": "100", "offset": str(off),
             "order": "startDate", "ascending": "false"}))
        if not page: break
        for e in page:
            if {t.get("slug") for t in (e.get("tags") or [])} & EXCLUDE: continue
            ms = e.get("markets") or []
            for m in ms:
                mid = m.get("id")
                if not mid or mid in seen: continue
                tk, outs, prices = jload(m.get("clobTokenIds")), jload(m.get("outcomes")), \
                    jload(m.get("outcomePrices"))
                if not tk or not outs or not prices: continue
                if not (len(tk) == len(outs) == len(prices)):
                    nlab["ARRAY LENGTH MISMATCH"] += 1
                    continue
                seen.add(mid)
                labels[tuple(str(o) for o in outs)] += 1
                y0 = fnum(prices[0])
                if y0 is None or 0.02 < y0 < 0.98: continue
                try:
                    en = datetime.datetime.fromisoformat(
                        ((m.get("endDate") or e.get("endDate") or "")[:19]).replace("Z", "")
                    ).replace(tzinfo=datetime.timezone.utc)
                except Exception:
                    continue
                ts = int(en.timestamp()) - 3 * 86400
                # index 0 view (what every surface script used)
                p0 = fresh_px(tk[0], ts)
                if p0 is None: continue
                # TRUE yes view: find the outcome literally labelled "Yes"
                yi = next((i for i, o in enumerate(outs) if str(o).strip().lower() == "yes"), None)
                is_yn = sorted(str(o).strip().lower() for o in outs) == ["no", "yes"]
                py = fresh_px(tk[yi], ts) if yi is not None else None
                wy = (1 if (fnum(prices[yi]) or 0) > 0.5 else 0) if yi is not None else None
                rows.append({"cat": cat, "en": en, "N": len(ms),
                             "p0": p0, "w0": 1 if y0 > 0.5 else 0,
                             "py": py, "wy": wy, "yes_idx": yi, "is_yn": is_yn,
                             "n_out": len(outs)})

rows.sort(key=lambda r: r["en"])
months = ((rows[-1]["en"] - rows[0]["en"]).days or 1) / 30.44
SPLIT = rows[len(rows) // 2]["en"]
print(f"  {len(rows)} fresh resolved markets\n")

print("=" * 104)
print("WHAT ARE THE OUTCOME LABELS?")
print("=" * 104)
for lab, c in labels.most_common(8):
    print(f"  {c:7d}  {lab}")
tot = sum(labels.values())
yn = sum(c for lab, c in labels.items()
         if sorted(s.strip().lower() for s in lab) == ["no", "yes"])
rev = sum(c for lab, c in labels.items()
          if [s.strip().lower() for s in lab] == ["no", "yes"])
print(f"\n  Yes/No markets (either order): {yn}/{tot} ({100*yn/tot:.1f}%)")
print(f"  REVERSED ['No','Yes'] ordering: {rev} ({100*rev/tot:.2f}%)")
print(f"  non-binary / other labels     : {tot-yn} ({100*(tot-yn)/tot:.1f}%)")
for k, v in nlab.items():
    print(f"  {k}: {v}")

print("\n" + "=" * 104)
print("FAILURE 1 -- INDEX MISALIGNMENT: does the index-0 view agree with the true-YES view?")
print("=" * 104)
both = [r for r in rows if r["py"] is not None and r["yes_idx"] is not None]
agree_w = sum(1 for r in both if (r["yes_idx"] == 0) == (r["w0"] == r["wy"]))
disagree_p = [r for r in both if r["yes_idx"] == 0 and abs(r["p0"] - r["py"]) > 1e-9]
print(f"  markets with a literal 'Yes' outcome and both prices available: {len(both)}")
print(f"  where yes_idx==0, price[0] != price[yes]: {len(disagree_p)}  "
      f"(any non-zero here means the arrays are NOT parallel)")
print(f"  -> arrays parallel: {'YES' if not disagree_p else 'NO -- STOP AND FIX'}")


def ev(lbl, sel, pk, wk):
    n = len(sel)
    if n < 25:
        print(f"  {lbl:44} n={n:5d} (thin)"); return
    v = [r[wk] - r[pk] for r in sel]
    m = sum(v) / n
    sd = (sum((x - m) ** 2 for x in v) / (n - 1)) ** 0.5
    z = m / (sd / n ** 0.5) if sd else 0
    tr = [r[wk] - r[pk] for r in sel if r["en"] < SPLIT]
    te = [r[wk] - r[pk] for r in sel if r["en"] >= SPLIT]
    exc = HALF_SPREAD + sum(FEER.get(r["cat"], .04) * r[pk] * (1 - r[pk]) for r in sel) / n
    net = m - exc
    sup = n / months
    mo = ((2 * sd / net) ** 2) / sup if net > 0 else None
    print(f"  {lbl:44} n={n:5d} gap {100*m:+6.2f}pt z{z:+5.1f} net {100*net:+6.2f}pt "
          + (f"{mo:7.0f} mo" if mo else "  never")
          + f"  [{100*(sum(tr)/len(tr) if tr else 0):+5.1f}/{100*(sum(te)/len(te) if te else 0):+5.1f}]")


print("\n" + "=" * 104)
print("FAILURES 2 & 3 -- DENOMINATION AND UNIVERSE: rebuild the cells the way the books see them")
print("=" * 104)
print("\n  FAVBUY cell, 0.80-0.90:")
ev("index-0 view (what I reported)", [r for r in rows if 0.80 <= r["p0"] < 0.90], "p0", "w0")
ev("...restricted to Yes/No markets", [r for r in rows if r["is_yn"] and 0.80 <= r["p0"] < 0.90], "p0", "w0")
ev("TRUE-YES price, Yes/No markets only",
   [r for r in rows if r["is_yn"] and r["py"] is not None and 0.80 <= r["py"] < 0.90], "py", "wy")
print("\n  GEOBUY cell, geopolitics 0.35-0.90:")
G = [r for r in rows if r["cat"] == "geopolitics"]
ev("index-0 view (what I reported)", [r for r in G if 0.35 <= r["p0"] < 0.90], "p0", "w0")
ev("...restricted to Yes/No markets", [r for r in G if r["is_yn"] and 0.35 <= r["p0"] < 0.90], "p0", "w0")
ev("TRUE-YES price, Yes/No markets only",
   [r for r in G if r["is_yn"] and r["py"] is not None and 0.35 <= r["py"] < 0.90], "py", "wy")

print("\n  the field-size lead, re-checked on the traded universe:")
YN = [r for r in rows if r["is_yn"] and r["py"] is not None and 0.80 <= r["py"] < 0.90]
ev("N<=10, TRUE-YES, Yes/No only", [r for r in YN if r["N"] <= 10], "py", "wy")
ev("N>=11, TRUE-YES, Yes/No only", [r for r in YN if r["N"] >= 11], "py", "wy")
