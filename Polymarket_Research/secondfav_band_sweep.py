"""
NUMFAM SPLIT of the band x field-size finding (2026-07-29) — the split I should have run first.

GAP THIS CLOSES: slice_sweep/remeasure_bands checked mention-style, multi-winner vs true-ME, and
category — but NEVER numeric-vs-event family, despite that being the split our own prior work says
matters most (it is the whole basis of base-vs-model: model is EVENT-only and is the healthier fade
book, while base's NUMERIC legs bled). secondfav is 98% NUMERIC by leg count, so the book I widened on
2026-07-27 lives almost entirely in the untested half — and it has since lost on exactly that family
(post-count ladders: NYC Mayor 40-59, Zelenskyy 60-79, Ted Cruz 80-99).

TENSION TO RESOLVE: the surface predicts this cell returns ~+26% on deployed (a ~15pt gap on a ~0.58
entry). secondfav's 50 event-clusters say [-31.5%, +5.6%] — an interval that does NOT contain +26%.

Same established method: market-level, gap = mean(won - p), temporal holdout, bar = |z|>=2.5 overall
AND same-sign halves AND |TEST z|>=1.5.
Usage: python numfam_split.py [pages]
"""
import json, os, sys, re, time, urllib.request, urllib.parse, datetime, collections
GAMMA="https://gamma-api.polymarket.com"; UA={"User-Agent":"Mozilla/5.0"}
OUT=os.path.dirname(os.path.abspath(__file__)); CACHE=os.path.join(OUT,"daily_hist_cache.json")
PAGES=int(sys.argv[1]) if len(sys.argv)>1 else 18
TAGS={"politics":"2","geopolitics":"100265","pop-culture":"596","tweets-markets":"972",
      "elections":"144","world":"101970","economy":"100328","tech":"1401","business":"107"}
EXCLUDE={"crypto","sports","soccer","fifa-world-cup","basketball","tennis","nfl","nba","mlb","nhl","baseball","football","games"}
# EXACT regex the books use (miner_harvester.NUMFAM), so the split matches what secondfav/carry gate on
NUMFAM=re.compile(r"\d+\s*-\s*[\d,.]+\s*(?:posts|tweets|views|days)|posts? from|tweets from|# of|million views"
                  r"|unemployment|jobs in|rate be|market cap|cpi\b|ppi\b|pce\b|gdp\b|inflation|capex|index be"
                  r"|deliver between|between [\d$,.]+[km]? and|transits?\b|passengers|box office|netflix|#\d+\s+(?:global|us)\b|top\s+(?:us|global|\d)|most.watched",re.I)
BANDS=[(0.03,0.10),(0.10,0.20),(0.20,0.35),(0.35,0.50),(0.50,0.65),(0.65,0.80),(0.80,0.90),(0.90,0.97)]
def band_of(p):
    for lo,hi in BANDS:
        if lo<=p<hi: return f"{lo:.2f}-{hi:.2f}"
    return None
def get(u,tries=2,pause=0.02):
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(u,headers=UA),timeout=25) as r:
                time.sleep(pause); return json.load(r)
        except Exception: time.sleep(0.2*(i+1))
    return None
def fnum(x):
    try: return float(x)
    except: return None
H={k:[(int(t),float(p)) for t,p in v] for k,v in json.load(open(CACHE)).items()}
def px_at(tok,ts):
    s=H.get(str(tok))
    if not s: return None
    best=None
    for t,p in s:
        if t<=ts: best=p
        else: break
    return best
print(f"cache {len(H)} tokens | enumerating ({PAGES} pages/tag)...")
rows=[]; seen=set()
for cat,tid in TAGS.items():
    for off in range(0,PAGES*100,100):
        page=get(f"{GAMMA}/events?"+urllib.parse.urlencode(
            {"tag_id":tid,"closed":"true","limit":"100","offset":str(off),"order":"startDate","ascending":"false"}))
        if not page: break
        for e in page:
            if {t.get("slug") for t in (e.get("tags") or [])} & EXCLUDE: continue
            ms=e.get("markets") or []; N=len(ms)
            wins=0
            for m in ms:
                op=m.get("outcomePrices")
                try: rr=json.loads(op) if isinstance(op,str) else op
                except Exception: rr=None
                v=fnum(rr[0]) if (rr and len(rr)>=1) else None
                if v is not None and v>0.5: wins+=1
            for m in ms:
                mid=m.get("id")
                if not mid or mid in seen: continue
                try: tk=json.loads(m.get("clobTokenIds") or "[]")
                except Exception: continue
                if not tk: continue
                op=m.get("outcomePrices")
                try: rr=json.loads(op) if isinstance(op,str) else op
                except Exception: rr=None
                y=fnum(rr[0]) if (rr and len(rr)>=1) else None
                if y is None or 0.02<y<0.98: continue
                ed=(m.get("endDate") or e.get("endDate") or "")[:19]
                try: en=datetime.datetime.fromisoformat(ed.replace("Z","")).replace(tzinfo=datetime.timezone.utc)
                except Exception: continue
                seen.add(mid)
                p=px_at(tk[0],int(en.timestamp())-3*86400)
                if p is None: continue
                b=band_of(p)
                if b is None: continue
                q=m.get("question") or ""
                rows.append({"won":1 if y>0.5 else 0,"p":p,"band":b,"en":en,"N":N,"wins":wins,
                             "num":bool(NUMFAM.search(q)),"cat":cat,"q":q[:52]})
print(f"  usable: {len(rows)}")
nnum=sum(1 for r in rows if r["num"])
print(f"  NUMERIC {nnum} ({100*nnum/len(rows):.0f}%) | EVENT {len(rows)-nnum}\n")
rows.sort(key=lambda r:r["en"]); SPLIT=rows[len(rows)//2]["en"]
def zc(v):
    n=len(v)
    if n<2: return 0.0,0.0,n
    m=sum(v)/n; sd=(sum((x-m)**2 for x in v)/(n-1))**0.5
    return m,(m/(sd/n**0.5) if sd>0 else 0.0),n
def gap(lab,sel,minn=40):
    v=[r["won"]-r["p"] for r in sel]
    tr=[r["won"]-r["p"] for r in sel if r["en"]<SPLIT]; te=[r["won"]-r["p"] for r in sel if r["en"]>=SPLIT]
    m,z,n=zc(v)
    if n<minn: print(f"  {lab:38} n={n:5d} (thin)"); return
    _,ztr,_=zc(tr); _,zte,_=zc(te)
    fl="  <== SURVIVES" if (abs(z)>=2.5 and ztr*zte>0 and abs(zte)>=1.5) else ""
    ret=(-m/(1-sum(r['p'] for r in sel)/n)) if n else 0     # NO-side return on cost, for comparability
    print(f"  {lab:38} n={n:5d} gap {m*100:+6.1f}pt (z{z:+6.1f}) | TR z{ztr:+5.1f} TE z{zte:+5.1f}"
          f" | NO-side ret {ret*100:+5.1f}%{fl}")

# ============================================================================================
# SECONDFAV BAND SWEEP (2026-08-10) — added to answer "on which dimension should secondfav2 expand?"
#
# The live headroom probe showed the ONLY dimensions that add throughput are the price band and the
# time window; field size N>40 adds literally zero legs (no such events exist in the cell). But the
# surface was only ever measured at 0.35-0.50, so extending the band would leave the measured region.
# This runs secondfav's EXACT cell (EVENT, true-ME, N>=11) across every band, so the expansion is
# chosen on holdout-tested evidence rather than on where supply happens to be.
# ============================================================================================
print("="*112)
print(f"SECONDFAV'S EXACT CELL ACROSS BANDS  (EVENT, true-ME single winner, N>=11)   holdout {SPLIT:%Y-%m-%d}")
print("  bar: |z|>=2.5 AND train/test same sign AND |TEST z|>=1.5")
print("="*112)
for lo,hi in BANDS:
    bl=f"{lo:.2f}-{hi:.2f}"
    sel=[r for r in rows if r["band"]==bl and r["N"]>=11 and r["wins"]==1 and not r["num"]]
    gap(f"{bl} EVENT ME N>=11", sel, minn=30)
print()
print("  same cell, N>=6 (secondfav's actual floor, not the N>=11 research restriction):")
for lo,hi in BANDS:
    bl=f"{lo:.2f}-{hi:.2f}"
    sel=[r for r in rows if r["band"]==bl and r["N"]>=6 and r["wins"]==1 and not r["num"]]
    gap(f"{bl} EVENT ME N>=6", sel, minn=30)
