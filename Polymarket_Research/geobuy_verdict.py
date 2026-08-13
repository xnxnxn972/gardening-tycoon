"""GEOBUY: IS THE POSITIVE MARK ON THE TWO OPEN LEGS INFORMATION, AND IS THERE A VIABLE VARIANT?

LEG-LEVEL CAVEAT (added 2026-08-13). The z-scores and any months-to-verdict figures below are
computed PER LEG. Legs of one negRisk event share a single outcome draw and are ONE observation, so
z is inflated by roughly sqrt(legs per cluster) and timelines are optimistic. See
clustered_surface.py for the event-clustered version of the same measurements. The DIRECTIONAL
conclusions in this script were checked against the clustered surface and are unchanged; only the
confidence and the timelines move.

Two things to settle before deciding to retire.

1. THE TWO OPEN LEGS. Both are PAST their end dates (Jul 31 and Aug 8, against today Aug 12), so a
   positive mark is not a live opinion about an unresolved question -- it is either a near-settled
   outcome or a stale print on a book nobody is trading. Which one matters: the first would make the
   record 11W-11L, the second is the fossil pattern all over again. Fetch the live book and find out.

2. THE VARIANT QUESTION -- and a real gap in my earlier scan. geobuy does NOT trade the cell I
   measured. Its universe is narrower on three axes I never applied:
       - EXCLUDES point-in-time "on <date>" markets (ONDATE) as a known-bad subpopulation
       - bands 0.35-0.80, not 0.35-0.90
       - tte 0.5-4.0d
   So my "+1.83pt, 1821 months" was measured on a cell contaminated with markets the book
   deliberately avoids. If the by-date subpopulation is materially better, a variant exists. This is
   the same universe-mismatch error I diagnosed in favbuy, pointing the other way, and it has to be
   ruled out before retiring rather than after.
"""
import csv, json, os, re, sys, time, math, urllib.request, urllib.parse, datetime, collections

GAMMA = "https://gamma-api.polymarket.com"; CLOB = "https://clob.polymarket.com"
UA = {"User-Agent": "Mozilla/5.0"}
TRADER = r"C:\Users\yaniv\polymarket-paper-trader"
RESD = r"C:\Users\yaniv\OneDrive\Projects\Polymarket_Research"
PAGES = int(sys.argv[1]) if len(sys.argv) > 1 else 18
ONDATE = re.compile(r"\bon\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s*\d", re.I)
HALF_SPREAD = 0.0095      # geopolitics is fee-free, so this is the whole execution cost


def get(u, tries=3):
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=30) as r:
                time.sleep(0.02); return json.load(r)
        except Exception:
            time.sleep(0.3 * (i + 1))
    return None


def fnum(x):
    try: return float(x)
    except Exception: return None


def jload(x):
    if isinstance(x, str):
        try: return json.loads(x)
        except Exception: return None
    return x


print("=" * 104)
print("1. THE TWO OPEN LEGS -- settled, or a fossil mark?")
print("=" * 104)
opens = list(csv.DictReader(open(os.path.join(TRADER, "paper_positions_geobuy.csv"), encoding="utf-8")))
tot_cost = 0.0; proj = 0.0
for r in opens:
    tok = r.get("no_token")          # the token geobuy bought
    cost = fnum(r.get("cost")) or 0.0
    sh = fnum(r.get("shares")) or 0.0
    tot_cost += cost
    m = get(f"{GAMMA}/markets?" + urllib.parse.urlencode({"clob_token_ids": tok})) if tok else None
    m = (m or [None])[0] if isinstance(m, list) else None
    bk = get(f"{CLOB}/book?" + urllib.parse.urlencode({"token_id": tok})) if tok else None
    bids = sorted(((float(b["price"]), float(b["size"])) for b in (bk or {}).get("bids", [])),
                  key=lambda x: -x[0])
    asks = sorted(((float(a["price"]), float(a["size"])) for a in (bk or {}).get("asks", [])),
                  key=lambda x: x[0])
    bb = bids[0][0] if bids else None
    ba = asks[0][0] if asks else None
    prices = jload((m or {}).get("outcomePrices"))
    outs = jload((m or {}).get("outcomes"))
    print(f"\n  {(r.get('question') or '')[:66]}")
    print(f"    entry {r.get('no_ask')} x {sh:.0f}sh = ${cost:.2f} | ended {r.get('end_date','')[:10]}")
    if m:
        print(f"    closed={m.get('closed')}  umaStatus={m.get('umaResolutionStatuses')}  "
              f"outcomePrices={prices} outcomes={outs}")
    print(f"    live book: bid {bb} / ask {ba} | depth "
          f"{(bids[0][1] if bids else 0):.0f} x {(asks[0][1] if asks else 0):.0f}")
    if bb is not None:
        mtm = bb * sh - cost
        print(f"    marked at the BID (what we could actually sell into): "
              f"${bb*sh:.2f} -> {mtm:+.2f}")
        proj += bb * sh
    else:
        print(f"    NO BID -- the mark is not sellable")
        proj += 0.0

led = list(csv.DictReader(open(os.path.join(TRADER, "paper_ledger_geobuy.csv"), encoding="utf-8")))
realized = sum(fnum(r.get("pnl")) or 0 for r in led)
w = sum(1 for r in led if (fnum(r.get("pnl")) or 0) > 0)
print(f"\n  closed record: {w}W-{len(led)-w}L, realized {realized:+.2f}")
print(f"  if BOTH open legs win in full: {w+2}W-{len(led)-w}L, "
      f"total {realized + sum(fnum(r.get('shares')) or 0 for r in opens) - tot_cost:+.2f}")
print(f"  if BOTH open legs lose:        {w}W-{len(led)-w+2}L, total {realized - tot_cost:+.2f}")

print("\n" + "=" * 104)
print("2. THE VARIANT: does excluding point-in-time 'on <date>' markets rescue the cell?")
print("=" * 104)
H = {k: [(int(t), float(p)) for t, p in v] for k, v in
     json.load(open(os.path.join(RESD, "daily_hist_cache.json"))).items()}
rows = []; seen = set()
for off in range(0, PAGES * 100, 100):
    page = get(f"{GAMMA}/events?" + urllib.parse.urlencode(
        {"tag_id": "100265", "closed": "true", "limit": "100", "offset": str(off),
         "order": "startDate", "ascending": "false"}))
    if not page: break
    for e in page:
        for mk in (e.get("markets") or []):
            mid = mk.get("id")
            if not mid or mid in seen: continue
            tk, prices = jload(mk.get("clobTokenIds")), jload(mk.get("outcomePrices"))
            if not tk or not prices: continue
            y = fnum(prices[0])
            if y is None or 0.02 < y < 0.98: continue
            try:
                en = datetime.datetime.fromisoformat(
                    ((mk.get("endDate") or e.get("endDate") or "")[:19]).replace("Z", "")
                ).replace(tzinfo=datetime.timezone.utc)
            except Exception:
                continue
            seen.add(mid)
            ts = int(en.timestamp()) - 3 * 86400
            s = H.get(str(tk[0]))
            if not s: continue
            prev = pt = None; after = 0
            for t, p in s:
                if t <= ts: prev, pt = p, t
                else: after += 1
            if prev is None or (ts - pt) >= 86400: continue
            q = mk.get("question") or ""
            rows.append({"won": 1 if y > 0.5 else 0, "en": en, "p": prev, "q": q,
                         "ondate": bool(ONDATE.search(q)), "live": after > 0})
rows.sort(key=lambda r: r["en"])
months = ((rows[-1]["en"] - rows[0]["en"]).days or 1) / 30.44
SPLIT = rows[len(rows) // 2]["en"]
print(f"  {len(rows)} fresh geopolitics markets over {months:.1f} months\n")


def ev(lbl, sel):
    n = len(sel)
    if n < 25:
        print(f"  {lbl:44} n={n:4d}  (thin)"); return
    v = [r["won"] - r["p"] for r in sel]
    m = sum(v) / n
    sd = (sum((x - m) ** 2 for x in v) / (n - 1)) ** 0.5
    z = m / (sd / n ** 0.5) if sd else 0
    tr = [r["won"] - r["p"] for r in sel if r["en"] < SPLIT]
    te = [r["won"] - r["p"] for r in sel if r["en"] >= SPLIT]
    mtr = sum(tr) / len(tr) if tr else 0
    mte = sum(te) / len(te) if te else 0
    net = m - HALF_SPREAD
    sup = n / months
    mo = ((2 * sd / net) ** 2) / sup if net > 0 else None
    flip = "  FLIPS" if (mtr > 0) != (mte > 0) else ""
    print(f"  {lbl:44} n={n:4d} gap {100*m:+6.2f}pt z{z:+5.1f} net {100*net:+6.2f}pt "
          f"sup {sup:4.1f}/mo " + (f"{mo:7.0f} mo" if mo else "  never") +
          f"  [{100*mtr:+5.1f}/{100*mte:+5.1f}]{flip}")


BAND = [r for r in rows if 0.35 <= r["p"] < 0.80]        # geobuy's ACTUAL bands
print("  geobuy's real band 0.35-0.80 (not the 0.35-0.90 I measured before):")
ev("all, fresh", BAND)
ev("BY-DATE only (what geobuy trades)", [r for r in BAND if not r["ondate"]])
ev("ON-DATE only (what geobuy excludes)", [r for r in BAND if r["ondate"]])
print("\n  by-date, split by band:")
for lo, hi in ((.35, .50), (.50, .65), (.65, .80)):
    ev(f"    by-date {lo:.2f}-{hi:.2f}", [r for r in BAND if not r["ondate"] and lo <= r["p"] < hi])
print("\n  and with the fossil filter also applied (live book at entry):")
ev("by-date AND live book", [r for r in BAND if not r["ondate"] and r["live"]])
nd = sum(1 for r in BAND if r["ondate"])
print(f"\n  on-date share of the band: {nd}/{len(BAND)} ({100*nd/len(BAND):.0f}%)")
