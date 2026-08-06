"""BID-SIDE (NO-basket) ARB SCAN — the mirror of the harvester's ask-side arb.

THE TRADE. In a negRisk event with n mutually-exclusive outcomes, buy 1 NO share of EVERY outcome.
Exactly one YES resolves true, so its NO pays $0 and the other n-1 NOs pay $1 each:
    payoff  = n - 1              (guaranteed)
    cost    = Sum ask(NO_i)
    profit  = (n-1) - Sum ask(NO_i)
and because NO and YES are complementary on the same market, ask(NO_i) = 1 - bid(YES_i), so
    profit  = Sum bid(YES_i) - 1
i.e. the arb exists whenever the YES BIDS sum above $1 — the exact mirror of the ask-side's Sum ask < 1.

WHY IT IS STRUCTURALLY SAFER THAN THE ASK SIDE. The ask-side basket needs EXACTLY ONE winner: with zero
winners, buying every YES pays $0 and we lose the lot. The NO basket pays n - (winners), so with
exclusivity alone (at most one winner) the payoff is >= n-1 GUARANTEED — zero winners pays MORE. So it
needs mutual exclusivity but not exhaustiveness, a strictly weaker assumption.

WHY IT MAY STILL BE WORSE IN PRACTICE. Cost is ~(n-1) per set instead of ~1, so the same absolute edge
sits on (n-1)x the capital: return on capital is roughly edge/(n-1). It strongly prefers FEW legs. The
$1 marketable-BUY floor is easier though — NO legs are expensive exactly where YES legs are dust.
The taker fee is IDENTICAL (p(1-p) is symmetric in p), so the fee hurdle is unchanged in absolute terms.

Read-only research scan. Places nothing, writes nothing but its own report.
"""
import json, sys, os, math, time, urllib.parse
sys.path.insert(0, r"C:\Users\yaniv\polymarket-paper-trader")
import arb_harvest as ah

GAMMA, CLOB = ah.GAMMA, ah.CLOB
MIN_EDGE = 0.005          # $ per set of GROSS edge required before we bother reading the book
FEE = ah.FEE_RATE_DEFAULT

def scan():
    seen = set(); cands = []
    for cat, tid in ah.SELF_TAGS.items():
        try:
            page = ah.get(f"{GAMMA}/events?" + urllib.parse.urlencode(
                {"tag_id": tid, "closed": "false", "limit": "100", "order": "volume24hr", "ascending": "false"}))
        except Exception: continue
        for e in page:
            eid = e.get("id")
            if eid in seen or e.get("negRisk") is not True: continue
            if {t.get("slug") for t in (e.get("tags") or [])} & ah.EXCLUDE: continue
            seen.add(eid)
            legs = []; ok = True
            for m in (e.get("markets") or []):
                if m.get("closed") or not m.get("enableOrderBook"): continue
                try:
                    if json.loads(m.get("outcomes") or "[]") != ["Yes", "No"]: continue
                    tk = json.loads(m["clobTokenIds"])
                except Exception: continue
                bb = ah.fnum(m.get("bestBid"))
                if bb is None or bb <= 0: ok = False; break
                fsch = m.get("feeSchedule") or {}
                fr = 0.0 if m.get("feesEnabled") is False else (ah.fnum(fsch.get("rate")) or FEE)
                legs.append({"no": tk[1], "ybid": bb, "frate": fr, "q": (m.get("question") or "")[:32]})
            if ok and len(legs) >= 3:
                sb = sum(l["ybid"] for l in legs)
                if sb > 1.0 + MIN_EDGE:
                    cands.append({"eid": eid, "cat": cat, "title": (e.get("title") or "")[:44],
                                  "legs": legs, "sumbid": sb,
                                  "end": ((e.get("endDate") or "") or "")[:10]})
    print(f"scanned {len(seen)} negRisk events | {len(cands)} with Sum(YES bids) > {1+MIN_EDGE:.3f}\n")

    out = []
    for c in cands:
        n = len(c["legs"]); ladders = []; ok = True
        for l in c["legs"]:
            try: b = ah.get(f"{CLOB}/book?" + urllib.parse.urlencode({"token_id": l["no"]}))
            except Exception: ok = False; break
            asks = sorted(((float(a["price"]), float(a["size"])) for a in (b.get("asks") or [])),
                          key=lambda x: x[0])
            if not asks: ok = False; break
            ladders.append(asks)
            time.sleep(0.15)
        if not ok:
            print(f"-- {c['title']}: NO-side book unavailable"); continue
        # worst-case cost per set must stay under the guaranteed payoff (n-1), with a margin
        cap = (n - 1) - MIN_EDGE
        k, limits = ah._size_basket(ladders, cap=cap)
        if k <= 0 or not limits:
            print(f"-- {c['title']}: verified Sum bid {c['sumbid']:.4f} but NO asks leave no profitable size")
            continue
        allowed = min(ah.DEPTH_FRAC * ah._depth_at(L, lim) for L, lim in zip(ladders, limits))
        k = min(k, allowed)
        if k <= 0:
            print(f"-- {c['title']}: no size after depth headroom"); continue
        need = ah._min_shares_for_notional(min(limits))
        cost_set = sum(limits)
        gross_set = (n - 1) - cost_set
        fee_set = ah._fee_per_set([l["frate"] for l in c["legs"]], limits)
        net_set = gross_set - fee_set
        blocked = "" if need <= k + 1e-9 else f"BLOCKED: needs {need:.0f} sh, depth allows {k:.1f}"
        kk = math.floor(max(k, need) / ah.STEP) * ah.STEP if not blocked else 0.0
        roc = net_set / cost_set if cost_set > 0 else 0.0
        hold = ah._hold_days(c["end"])
        print(f"-- {c['title']}  [{c['cat']}] {n} legs, ends {c['end']}")
        print(f"   Sum YES bid {c['sumbid']:.4f} | NO-basket cost/set {cost_set:.4f} of {n-1} payoff "
              f"-> gross {gross_set:+.4f}, fee {fee_set:.4f}, NET {net_set:+.4f}/set")
        print(f"   return on capital {100*roc:+.3f}%"
              + (f" | {100*roc*365/hold:+.1f}%/yr over {hold:.1f}d" if hold else " | no end date"))
        print(f"   cheapest NO leg {min(limits):.4f} -> need {need:.0f} sh | depth allows {k:.1f}"
              + (f"  ** {blocked}" if blocked else f" -> tradeable {kk:.0f} sh = ${kk*cost_set:.2f} capital"))
        if not blocked and kk > 0:
            out.append(dict(title=c["title"], n=n, net=kk * net_set, cap=kk * cost_set,
                            roc=roc, hold=hold or 0))
        print()

    print("=" * 78)
    if out:
        print(f"{len(out)} TRADEABLE bid-side arbs:")
        for o in sorted(out, key=lambda x: -x["net"]):
            print(f"   NET ${o['net']:+.2f} on ${o['cap']:.2f} capital ({o['n']} legs, "
                  f"{100*o['roc']:+.3f}% RoC, {o['hold']:.0f}d)  {o['title']}")
        print(f"   TOTAL net ${sum(o['net'] for o in out):+.2f} on ${sum(o['cap'] for o in out):.2f}")
    else:
        print("NO tradeable bid-side arbs in this snapshot.")

if __name__ == "__main__":
    scan()
