"""ASK: grounded answers computed from the run's artefacts.

The artefacts are cut into titled chunks (one per policy card, the
ledger, the distribution, the safety and news tables, the market by firm,
the gap, each assurance stage, the assumptions, the gates). A question is
read into an intent; the deterministic answer is assembled from the
matching chunks with the figures as stored; a model, when configured, may
phrase it and its text is kept only if every number survives vetting.
"""

import re

from ._common import nice_name as _nice
from . import welfare as W

COMP_LABELS = {"harm_avoided": "harm avoided", "cs_change": "consumer surplus", "productivity_change": "output uplift",
               "producer_surplus_change": "resident producer surplus", "compliance_cost": "compliance cost",
               "enforcement_cost": "enforcement budget", "leakage": "activity lost offshore", "relocation_cost": "relocation cost",
               "labour_change": "labour adjustment"}


def _bn(x, nd=1):
    sign = "-" if x < 0 else ""
    v = abs(x)
    return f"{sign}${v / 1000:,.2f}tn" if v >= 1000 else f"{sign}${v:,.{nd}f}bn"


def _pct(x):
    return f"{x * 100:.0f}%"


def chunks(snap):
    """snap: {'artefacts': ..., 'approvals': ..., 'critic': ..., 'ledger': {...}, 'news': {policy: wire}}"""
    arte = snap.get("artefacts") or {}
    out = []

    def add(cid, title, text):
        out.append({"id": cid, "title": title, "text": text})
    if not arte:
        add("none", "No run", "No run has been evaluated yet. Plan a battery and approve it at Gate 1.")
        return out
    ev = arte["results"]
    pols = {r["policy"]: r for r in ev["policies"]}
    pref = ev["preferred"] or ev["best_unconstrained"]
    years = arte["horizon"] / 12
    P = pols[pref]
    add("answer", "The answer",
        f"Preferred option {P['label']}: expected net social value {_bn(P['net_social_value']['mean'])} "
        f"[{_bn(P['net_social_value']['lo'])}, {_bn(P['net_social_value']['hi'])}] over {years:.0f} years, best in {_pct(P['p_best'])} of resamples; "
        f"harm avoided {_bn(P['components']['harm_avoided']['mean'])}; industry value change {_bn(P['industry_value_change']['mean'], 0)}; "
        + ("it satisfies every constraint." if ev["preferred"] else "no instrument satisfies every constraint; this is the best unconstrained option.")
        + (f" Best unconstrained: {pols[ev['best_unconstrained']]['label']}." if ev["best_unconstrained"] != pref else ""))
    cons = {k: v for k, v in (arte.get("constraints") or {}).items() if not k.startswith("_")}
    from .briefing import _constraint_text
    add("constraints", "Constraints", "Constraints: " + ("; ".join(_constraint_text(k, v) for k, v in cons.items()) or "none") + ". "
        + " ".join(f"{r['label']}: {'within' if r['feasible'] else 'fails'} ({'; '.join(r['constraint_notes'])})." for r in ev["policies"] if r["policy"] != "baseline"))
    for r in ev["policies"]:
        if r["policy"] == "baseline":
            s = r["safety"]
            add("pol_baseline", "Status quo", f"Status quo: expected harm {_bn(s['expected_harm_npv']['mean'])}, {s['incidents_per_year']['mean']:.1f} incidents a year, "
                f"P(major) {_pct(s['p_major'])}, P(catastrophe) {_pct(s['p_catastrophe'])}, safety level {s['safety_level_end']:.2f}, trust {s['trust_end']:.2f} at the end.")
            continue
        c = r["components"]; s = r["safety"]; n = r["news"]
        add(f"pol_{r['policy']}", r["label"],
            f"{r['label']}: net social value {_bn(r['net_social_value']['mean'])} [{_bn(r['net_social_value']['lo'])}, {_bn(r['net_social_value']['hi'])}], "
            f"P(positive) {_pct(r['net_social_value']['p_positive'])}, P(best) {_pct(r['p_best'])}; "
            + "; ".join(f"{COMP_LABELS[k]} {_bn(c[k]['mean'])}" for k in W.COMPONENTS) + f"; gross cost {_bn(r['gross_cost']['mean'])}; "
            f"industry value change {_bn(r['industry_value_change']['mean'], 0)} (P(gain) {_pct(r['industry_value_change']['p_positive'])}); "
            f"incidents {s['incidents_per_year']['mean']:.1f} a year, P(catastrophe) {_pct(s['p_catastrophe'])}, safety share {_pct(s['safety_share_end'])}, "
            f"offshore {_pct(s['offshore_share_end'])}, compliance {_pct(s['compliance_share'])}; peak news pressure {n['peak_pressure']['mean']:.2f}, "
            f"P(hearing) {_pct(n['p_hearing'])}; headline score {r['headline_score']:+.3f}; ranks: social {r['rank_social']}, headline {r['rank_headline']}, "
            f"harm {r['rank_harm']}, industry {r['rank_industry']}; {'within' if r['feasible'] else 'outside'} the constraints.")
    d = P["distribution"]
    add("distribution", f"Who gains and who pays under {P['label']}", "; ".join(f"{k} {_bn(v)}" for k, v in d.items())
        + f". Transfers: fines {_bn(P['transfers']['fines'])}, liability {_bn(P['transfers']['liability'])}, premiums {_bn(P['transfers']['premiums'])}.")
    m = P["market"]
    add("market", f"Market under {P['label']}",
        f"Industry value change {_bn(P['industry_value_change']['mean'], 0)} on {_bn(m['industry_cap0'], 0)}; index {m['early_reaction']['mean'] * 100:+.1f}% "
        f"in the first six months and {m['end_reaction']['mean'] * 100:+.1f}% at the horizon against the baseline. By firm: "
        + "; ".join(f"{f['firm']} {_bn(f['value_change']['mean'])} (P(gain) {_pct(f['value_change']['p_positive'])}, price {f['price_end']:.0f} vs {f['price_end_base']:.0f} at baseline)" for f in m["firms"])
        + ". By sector: " + "; ".join(f"{_nice(x['sector'])} {_bn(x['value_change']['mean'])}" for x in m["sectors"]) + ".")
    for r in ev["policies"]:
        if r["policy"] != pref and r["policy"] != "baseline":
            mm = r["market"]
            add(f"market_{r['policy']}", f"Market under {r['label']}",
                f"{r['label']}: industry value change {_bn(r['industry_value_change']['mean'], 0)}; by firm "
                + "; ".join(f"{f['firm']} {_bn(f['value_change']['mean'])}" for f in mm["firms"]) + ".")
    add("safety", "Safety forecast", " ".join(
        f"{r['label']}: {r['safety']['incidents_per_year']['mean']:.1f} incidents a year, P(major) {_pct(r['safety']['p_major'])}, "
        f"P(catastrophe) {_pct(r['safety']['p_catastrophe'])}, expected harm {_bn(r['safety']['expected_harm_npv']['mean'])}."
        for r in ev["policies"]))
    add("news", "News forecast", " ".join(
        f"{r['label']}: minor incident headlines {r['news']['headlines_per_year']['minor incidents']['mean']:.1f} a year, major {r['news']['headlines_per_year']['major incidents']['mean']:.2f}, "
        f"enforcement {r['news']['headlines_per_year']['enforcement actions']['mean']:.2f}, relocations {r['news']['headlines_per_year']['relocations']['mean']:.2f}; "
        f"peak pressure {r['news']['peak_pressure']['mean']:.2f}; P(hearing) {_pct(r['news']['p_hearing'])}; early tone {r['news']['early_tone']:+.2f}."
        for r in ev["policies"]))
    wires = snap.get("news") or {}
    if wires.get(pref):
        worst = sorted(wires[pref], key=lambda w: w["tone"])[:4]
        add("wire", f"Sample wire under {P['label']}", " ".join(f"{w['date']} {w['outlet']}: {w['headline']}." for w in worst))
    g = ev["decision_gap"]
    add("gap", "Decision gap", f"Headline order {', '.join(pols[n]['label'] for n in g['headline_order'])}; social order "
        f"{', '.join(pols[n]['label'] for n in g['social_order'])}; Kendall tau {g['kendall_tau']:+.2f}; decision gap {g['decision_gap']:.2f}; "
        f"P(inversion) {_pct(g['p_inversion'])}; winner stability {_pct(ev['winner_stability'])}. {g['note']}.")
    asr = arte.get("assurance") or {}
    if asr.get("tornado"):
        t = asr["tornado"]
        add("tornado", "Tornado", f"Reference value {_bn(t['reference_nsv'])}. " + " ".join(
            f"{_nice(r['assumption'])}: {_bn(r['low']['nsv'])} at {r['low']['value']} and {_bn(r['high']['nsv'])} at {r['high']['value']}"
            + (", best option changes" if r["best_changes"] else "") + "." for r in t["rows"]) + (f" Flips: {', '.join(_nice(k) for k in t['flips'])}." if t["flips"] else " No flips."))
    if asr.get("structural"):
        st = asr["structural"]
        add("structural", "Structural variants", f"Preferred option best in {st['wins']} of {st['n']} variants, top two in {st['top_two']}. " + " ".join(
            f"{_nice(v['variant'])} ({v['note']}): best {pols[v['best']]['label'] if v['best'] in pols else v['best']}, preferred option rank {v['preferred_rank']}." for v in st["variants"]))
    if asr.get("red_team"):
        rt = asr["red_team"]
        add("red_team", "Red team", f"Most robust to gaming: {pols[rt['most_robust']]['label'] if rt['most_robust'] in pols else rt['most_robust']}. " + " ".join(
            f"{r['label']}: honest {_bn(r['honest']['nsv'])}, worst strategy {_nice(r['worst_strategy'])} gives {_bn(r['worst_nsv'])}, loss {_bn(r['gaming_loss'])}." for r in rt["rows"]))
    add("assumptions", "Assumptions", " ".join(f"{_nice(r['assumption'])} {r['value']} {r['unit']} ({r['meaning']})." for r in arte["assumption_table"]))
    add("firms", "Firms", " ".join(f"{f['label']}: {_nice(f['sector'])}, revenue ${f['revenue']:.0f}bn, margin {f['margin']:.0%}, growth {f['growth']:.0%}, "
                                   f"capability {f['capability']:.2f}, safety {f['safety']:.2f}, mobility {f['mobility']:.1f}." for f in arte["firms"]))
    add("instruments", "Instruments", " ".join(f"{p['label']}: {p['note']}" for p in arte["policies"].values()))
    ap = snap.get("approvals") or {}
    led = snap.get("ledger") or {}
    cr = snap.get("critic") or {}
    add("ledger", "Ledger and gates", f"Ledger {led.get('entries', 0)} entries, head {str(led.get('head', ''))[:12]}, "
        f"{'verified' if led.get('ok') else 'not verified'}. " + " ".join(
            f"{k}: {v.get('decision')} by {v.get('actor')}{(' (' + v.get('role') + ')') if v.get('role') else ''}." for k, v in ap.items() if isinstance(v, dict) and v.get("decision"))
        + (f" Critic: {cr.get('n_checks', 0) - cr.get('n_failed', 0)} of {cr.get('n_checks', 0)} checks passed." if cr else ""))
    pv = arte["provenance"]
    add("provenance", "Provenance", f"Battery hash {arte['battery_hash'][:16]}, assumptions hash {arte['assumptions_hash'][:16]}, code fingerprint {pv['code_fingerprint'][:16]}, "
        f"PSL {pv['psl_version']}, {arte['paths']} paths, horizon {arte['horizon']} months, seed {arte['seed']}, profile {arte.get('profile')}, {arte['run']['elapsed_s']} s.")
    return out


def _tok(s):
    return set(re.findall(r"[a-z][a-z0-9]+", s.lower()))


def retrieve(ch, q, k=6):
    qt = _tok(q)
    scored = []
    for c in ch:
        ct = _tok(c["title"] + " " + c["text"])
        overlap = len(qt & ct)
        scored.append((overlap + (3 if any(w in c["title"].lower() for w in qt) else 0), c))
    scored.sort(key=lambda x: -x[0])
    return [c for s, c in scored[:k] if s > 0] or ch[:k]


INTENTS = (
    ("constraints", ("constraint", "budget", "feasible", "limit")),
    ("distribution", ("who pays", "who gains", "distribution", "consumers", "taxpayers", "workers", "shareholders")),
    ("news", ("news", "headline", "press", "wire", "coverage", "hearing", "pressure")),
    ("market", ("stock", "share price", "market", "valuation", "industry", "equity", "investor", "sector", "gain", "loss", "lose", "profit")),
    ("safety", ("safety", "safe ", "safer", "incident", "catastroph", "harm", "accident", "misuse")),
    ("gap", ("gap", "look", "early", "inversion", "tau")),
    ("tornado", ("tornado", "sensitiv", "assumption", "value judgement", "discount")),
    ("structural", ("structural", "variant", "robust", "model structure")),
    ("red_team", ("red team", "gaming", "game", "evade", "arbitrage", "relocat", "offshore")),
    ("ledger", ("ledger", "gate", "approv", "critic", "sign", "release")),
    ("firms", ("firm", "archetype", "company", "companies")),
    ("instruments", ("instrument", "what is", "what does", "explain", "describe")),
    ("provenance", ("provenance", "hash", "reproduce", "seed", "fingerprint")),
    ("preferred", ("cost", "expensive", "worth", "buy", "price tag", "society")),
    ("answer", ("which", "recommend", "best", "prefer", "should", "choose", "decision")),
)


WEAK = {"instruments": 0.5}


def intent_of(q):
    """The intent with the most keyword hits; generic library words count half, so a decision question that
    mentions an instrument still gets the answer; ties go to the more specific intent (earlier in the table)."""
    ql = q.lower()
    best, score = "answer", 0.0
    for name, keys in INTENTS:
        hits = sum(WEAK.get(name, 1.0) for k in keys if k in ql)
        if hits > score:
            best, score = name, hits
    return best


def deterministic_answer(snap, q):
    ch = chunks(snap)
    by = {c["id"]: c for c in ch}
    if "none" in by:
        return by["none"]["text"], [by["none"]]
    arte = snap["artefacts"]; ev = arte["results"]
    pols = {r["policy"]: r for r in ev["policies"]}
    ql = q.lower()
    # a named policy
    for n, r in pols.items():
        if n != "baseline" and (n.replace("_", " ") in ql or r["label"].lower() in ql or n in ql):
            srcs = [by[f"pol_{n}"]]
            if "market" in ql or "stock" in ql or "share" in ql:
                srcs.append(by.get(f"market_{n}", by["market"]))
            return " ".join(s["text"] for s in srcs), srcs
    # a named firm
    for f in arte["firms"]:
        if f["label"].lower() in ql or f["name"].replace("_", " ") in ql:
            pref = ev["preferred"] or ev["best_unconstrained"]
            rows = []
            for r in ev["policies"]:
                if r["policy"] == "baseline":
                    continue
                fr = next(x for x in r["market"]["firms"] if x["firm"] == f["label"])
                rows.append(f"{r['label']}: {_bn(fr['value_change']['mean'])} (P(gain) {_pct(fr['value_change']['p_positive'])}, "
                            f"earnings {_bn(fr['earnings_change_npv'])}, offshore at end {_pct(fr['offshore_end'])})")
            text = f"{f['label']} ({_nice(f['sector'])}) under each instrument, value change against the baseline: " + "; ".join(rows) + "."
            return text, [by["market"], by["firms"]]
    # a named assumption
    qt = _tok(ql)
    for r in arte["assumption_table"]:
        words = [w for w in r["assumption"].split("_") if len(w) > 2 and w not in ("bn", "share", "base", "rate", "monthly")]
        hit = sum(1 for w in words if w in qt or any(t.startswith(w[:6]) for t in qt))
        if _nice(r["assumption"]).lower() in ql or r["assumption"] in ql or (words and hit >= min(2, len(words))):
            text = f"{_nice(r['assumption'])}: {r['value']} {r['unit']}; {r['meaning']}; bounds {r['low']} to {r['high']}."
            t = (arte.get("assurance") or {}).get("tornado")
            if t:
                for row in t["rows"]:
                    if row["assumption"] == r["assumption"]:
                        text += (f" In the tornado the preferred option's value is {_bn(row['low']['nsv'])} at {row['low']['value']} and "
                                 f"{_bn(row['high']['nsv'])} at {row['high']['value']}" + ("; the best option changes." if row["best_changes"] else "."))
            return text, [by["assumptions"]] + ([by["tornado"]] if "tornado" in by else [])
    it = intent_of(q)
    if it == "preferred":
        pref = ev["preferred"] or ev["best_unconstrained"]
        srcs = [by[f"pol_{pref}"], by["distribution"]]
        return " ".join(s["text"] for s in srcs), srcs
    if it in by:
        srcs = [by[it]]
        if it == "answer":
            srcs += [by["constraints"], by["gap"]]
        return " ".join(s["text"] for s in srcs), srcs
    srcs = retrieve(ch, q, 3)
    return " ".join(s["text"] for s in srcs), srcs


def answer(snap, q, client=None, log=None):
    text, srcs = deterministic_answer(snap, q)
    used = False
    if client is not None and getattr(client, "available", False):
        from .llm import ask_llm
        from .critic import _vet_numbers
        phrased = ask_llm(q, srcs, text, client, log or (lambda *a, **k: None))
        if phrased and not _vet_numbers(phrased, snap.get("artefacts") or {}):
            text, used = phrased, True
    return {"answer": text, "sources": [{"id": s["id"], "title": s["title"], "text": s["text"][:420] + ("…" if len(s["text"]) > 420 else "")} for s in srcs],
            "intent": intent_of(q), "llm": used}
