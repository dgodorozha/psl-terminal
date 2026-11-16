"""ASK: grounded answers computed from the run's artefacts.

The artefacts are cut into titled chunks (the decision, one per alternative,
the ledger, the incidence table, the safety and news tables, the market by
firm, the gap, each kind of uncertainty and each assurance stage, the
assumptions, the mechanisms, the gates). A question is read into an intent;
the deterministic answer is assembled from the matching chunks with the
figures as stored; a model, when configured, may phrase it and its text is
kept only if every number survives vetting.
"""

import re

from ._common import nice_name as _nice
from . import welfare as W

COMP_LABELS = {"harm_avoided": "harm avoided", "cs_change": "consumer surplus", "productivity_change": "output uplift",
               "producer_surplus_change": "resident producer surplus", "compliance_cost": "compliance cost",
               "enforcement_cost": "enforcement budget", "leakage": "activity lost offshore", "relocation_cost": "relocation cost",
               "labour_change": "labour adjustment", "insurance_admin_cost": "insurance administration"}


def _bn(x, nd=1):
    if x is None:
        return "n/a"
    if abs(x) < 0.5 * 10 ** (-nd):
        x = 0.0
    sign = "-" if x < 0 else ""
    v = abs(x)
    return f"{sign}${v / 1000:,.2f}tn" if v >= 1000 else f"{sign}${v:,.{nd}f}bn"


def _pct(x, nd=0):
    return "n/a" if x is None else f"{x * 100:.{nd}f}%"


def _ci(s, nd=1):
    return f"{_bn(s['mean'], nd)} (95% confidence interval {_bn(s['ci_lo'], nd)} to {_bn(s['ci_hi'], nd)})"


def _lab(pols, name):
    if name == "baseline":
        return "the status quo"
    return pols[name]["label"] if name in pols else (_nice(name) if name else "none")


def firm_text(arte, f):
    """One firm under every instrument (used by the oracle and by the replay site)."""
    rows = []
    for r in arte["results"]["policies"]:
        if r["policy"] == "baseline":
            continue
        fr = next(x for x in r["market"]["firms"] if x["firm"] == f["label"])
        rows.append(f"{r['label']}: {_bn(fr['value_change']['mean'])} (P(gain) {_pct(fr['value_change']['p_positive'])}, "
                    f"earnings {_bn(fr['earnings_change_npv'])}, offshore at end {_pct(fr['offshore_end'])})")
    return f"{f['label']} ({_nice(f['sector'])}) under each instrument, expected value change against the status quo: " + "; ".join(rows) + "."


def assumption_text(arte, r):
    """One declared assumption, with what the screen found for it."""
    text = (f"{_nice(r['assumption'])}: {r['value']} {r['unit']}; {r['meaning']}; plausible range {r['range_low']} to {r['range_high']} "
            f"(accepted bounds {r['low']} to {r['high']}).")
    scr = (arte.get("assurance") or {}).get("screen")
    if scr:
        pols = {x["policy"]: x for x in arte["results"]["policies"]}
        for row in scr["rows"]:
            if row["assumption"] == r["assumption"]:
                text += (f" In the screen the value of {_lab(pols, scr['preferred'])} is {_bn(row['low']['nsv'])} at {row['low']['value']} and "
                         f"{_bn(row['high']['nsv'])} at {row['high']['value']}; the decision is {_lab(pols, row['low']['best'])} at the low end and "
                         f"{_lab(pols, row['high']['best'])} at the high end" + (", so it changes." if row["best_changes"] else ", unchanged."))
    return text


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
    pref = ev["preferred"]
    focus = ev["focus"]
    dec = ev["decision"]
    years = arte["horizon"] / 12
    P = pols[focus]
    pr = ev.get("precision") or {}
    add("answer", "The answer",
        dec["text"] + f" {P['label']}: expected net social value {_ci(P['net_social_value'])} over {years:.0f} years; simulated outcomes "
        f"{_bn(P['net_social_value']['lo'])} to {_bn(P['net_social_value']['hi'])} (10th to 90th percentile); harm avoided "
        f"{_bn(P['components']['harm_avoided']['mean'])}; industry value change {_bn(P['industry_value_change']['mean'], 0)}; within the "
        f"constraints in {_pct(P['p_feasible'])} of resamples; best feasible alternative in {_pct(P['p_best'])} of resamples (ranking "
        f"stability under the model, not the probability of being best in the world)."
        + ("" if pr.get("met", True) else " Short of the precision target: " + "; ".join(x["text"] for x in pr.get("unresolved", [])) + "."))
    cons = {k: v for k, v in (arte.get("constraints") or {}).items() if not k.startswith("_")}
    from .briefing import _constraint_text
    add("constraints", "Constraints", "Constraints: " + ("; ".join(_constraint_text(k, v) for k, v in cons.items()) or "none") + ". "
        + " ".join(f"{r['label']}: {'within' if r['feasible'] else 'fails'}" + (f" ({'; '.join(r['constraint_notes'])})" if r["constraint_notes"] else "") + "."
                   for r in ev["policies"])
        + (f" Under the conservative rule ({dec['assured_rule']}) the preferred option is {_lab(pols, dec['preferred_assured'])}." if cons else ""))
    for r in ev["policies"]:
        s = r["safety"]; pc = s["p_catastrophe_detail"]
        if r["policy"] == "baseline":
            add("pol_baseline", "Status quo", f"Status quo: scores zero by construction and is a decision alternative. Expected harm "
                f"{_bn(s['expected_harm_npv']['mean'])}, {s['incidents_per_year']['mean']:.1f} incidents a year, "
                f"P(major) {_pct(s['p_major'])}, P(catastrophe) {_pct(s['p_catastrophe'], 1)} (95% confidence interval {_pct(pc['ci_lo'], 1)} to "
                f"{_pct(pc['ci_hi'], 1)}; drawn on {pc['k']} of {pc['n']} paths), safety level {s['safety_level_end']:.2f}, trust {s['trust_end']:.2f} at the end.")
            continue
        c = r["components"]; n = r["news"]; v = r["net_social_value"]
        add(f"pol_{r['policy']}", r["label"],
            f"{r['label']}: expected net social value {_ci(v)}; simulated outcomes {_bn(v['lo'])} to {_bn(v['hi'])} (10th to 90th percentile), "
            f"positive on {_pct(v['p_positive'])} of paths; ranking stability {_pct(r['p_best'])}; "
            + "; ".join(f"{COMP_LABELS[k]} {_bn(c[k]['mean'])}" for k in W.COMPONENTS) + f"; gross cost {_bn(r['gross_cost']['mean'])}, gross benefit "
            f"{_bn(r['gross_benefit']['mean'])}; "
            f"industry value change {_bn(r['industry_value_change']['mean'], 0)} (P(gain) {_pct(r['industry_value_change']['p_positive'])}); "
            f"incidents {s['incidents_per_year']['mean']:.1f} a year, P(catastrophe) {_pct(s['p_catastrophe'], 1)}, safety share {_pct(s['safety_share_end'])}, "
            f"offshore {_pct(s['offshore_share_end'])}, compliance {_pct(s['compliance_share'])}; peak news pressure {n['peak_pressure']['mean']:.2f}, "
            f"P(hearing) {_pct(n['p_hearing'])}; headline score {r['headline_score']:+.3f}; ranks: social {r['rank_social']}, headline {r['rank_headline']}, "
            f"harm {r['rank_harm']}, industry {r['rank_industry']}; {'within' if r['feasible'] else 'outside'} the constraints "
            f"({_pct(r['p_feasible'])} of resamples within).")
    d = P["distribution"]
    add("distribution", f"Who gains and who pays under {P['label']}", "; ".join(f"{k} {_bn(v)}" for k, v in d.items())
        + f". The table sums to the net social value plus {_bn(P['nonresident_payments'])} financed by non resident owners, a memorandum item. "
        f"Transfers, excluded from the net: fines {_bn(P['transfers']['fines'])}, liability {_bn(P['transfers']['liability'])}, premiums "
        f"{_bn(P['transfers']['premiums'])}, claims {_bn(P['transfers']['claims'])}.")
    m = P["market"]
    add("market", f"Market under {P['label']}",
        f"Industry value change {_ci(P['industry_value_change'], 0)} on {_bn(m['industry_cap0'], 0)}; index {m['early_reaction']['mean'] * 100:+.1f}% "
        f"in the first six months and {m['end_reaction']['mean'] * 100:+.1f}% at the horizon against the status quo, both measured from the valuation "
        f"before any instrument is announced. By firm: "
        + "; ".join(f"{f['firm']} {_bn(f['value_change']['mean'])} (P(gain) {_pct(f['value_change']['p_positive'])}, price {f['price_end']:.0f} vs {f['price_end_base']:.0f} at the status quo)" for f in m["firms"])
        + ". By sector: " + "; ".join(f"{_nice(x['sector'])} {_bn(x['value_change']['mean'])}" for x in m["sectors"]) + ".")
    for r in ev["policies"]:
        if r["policy"] != focus and r["policy"] != "baseline":
            mm = r["market"]
            add(f"market_{r['policy']}", f"Market under {r['label']}",
                f"{r['label']}: industry value change {_bn(r['industry_value_change']['mean'], 0)}; by firm "
                + "; ".join(f"{f['firm']} {_bn(f['value_change']['mean'])}" for f in mm["firms"]) + ".")
    add("safety", "Safety forecast", " ".join(
        f"{r['label']}: {r['safety']['incidents_per_year']['mean']:.1f} incidents a year, P(major) {_pct(r['safety']['p_major'])}, "
        f"P(catastrophe) {_pct(r['safety']['p_catastrophe'], 1)} ({_pct(r['safety']['p_catastrophe_detail']['ci_lo'], 1)} to "
        f"{_pct(r['safety']['p_catastrophe_detail']['ci_hi'], 1)}), expected harm {_bn(r['safety']['expected_harm_npv']['mean'])}."
        for r in ev["policies"]) + " The catastrophe probability is estimated from the hazard each path accumulates, not from the count of paths "
        "on which the event was drawn.")
    add("news", "News forecast", " ".join(
        f"{r['label']}: minor incident headlines {r['news']['headlines_per_year']['minor incidents']['mean']:.1f} a year, major {r['news']['headlines_per_year']['major incidents']['mean']:.2f}, "
        f"enforcement {r['news']['headlines_per_year']['enforcement actions']['mean']:.2f}, relocations {r['news']['headlines_per_year']['relocations']['mean']:.2f}; "
        f"peak pressure {r['news']['peak_pressure']['mean']:.2f}; P(hearing) {_pct(r['news']['p_hearing'])}; early tone {r['news']['early_tone']:+.2f}."
        for r in ev["policies"]))
    wires = snap.get("news") or {}
    if wires.get(focus):
        worst = sorted(wires[focus], key=lambda w: w["tone"])[:4]
        add("wire", f"Sample wire under {P['label']}", " ".join(f"{w['date']} {w['outlet']}: {w['headline']}." for w in worst))
    g = ev["decision_gap"]
    add("gap", "Decision gap", f"Headline order {', '.join(pols[n]['label'] for n in g['headline_order'])}; social order "
        f"{', '.join(pols[n]['label'] for n in g['social_order'])}; Kendall tau b {g['kendall_tau']:+.2f}; decision gap {g['decision_gap']:.2f}; "
        f"P(inversion) {_pct(g['p_inversion'])}. {g['note']}.")
    asr = arte.get("assurance") or {}
    diffs = [r for r in ev["policies"] if r.get("vs_preferred") and r["feasible"]]
    bt = asr.get("batches"); cv = asr.get("convergence")
    add("uncertainty", "How sure, on these paths",
        f"{arte['paths']} paths per alternative" + (f" (schedule {', '.join(str(x) for x in pr['schedule'])}; ceiling {pr['max_paths']})" if pr else "")
        + f", {ev['bootstrap']} bootstrap resamples. Three things are kept apart: the 95% confidence interval of an expected value (Monte Carlo error), "
        f"the 10th to 90th percentile spread of simulated outcomes, and the range under alternative assumptions (the screen and the joint draw). "
        + (("Every precision target was met. " if pr.get("met") else "Short of the precision target: " + "; ".join(x["text"] for x in pr.get("unresolved", [])) + ". ") if pr else "")
        + (f"{_lab(pols, pref)[:1].upper() + _lab(pols, pref)[1:]} against each other feasible alternative, paired difference in expected net social value: "
           + "; ".join(f"{r['label']} {_bn(r['vs_preferred']['difference'])} ({_bn(r['vs_preferred']['ci_lo'])} to {_bn(r['vs_preferred']['ci_hi'])}, "
                       f"{'told apart' if r['vs_preferred']['distinguishable'] else 'not told apart'})" for r in diffs) + ". " if pref and diffs else "")
        + (f"In {bt['k']} independent batches of {bt['size']} paths the decision is the same in {bt['agree']}. " if bt else "")
        + (("Running estimate: " + "; ".join(f"{r['paths']} paths, decision {_lab(pols, r['preferred'])}, {_lab(pols, cv['focus'])} {_bn(r['focus_nsv'])} "
                                              f"(standard error {r['focus_se']:.2f})" for r in cv["rows"]) + ".") if cv and len(cv["rows"]) > 1 else ""))
    if asr.get("tornado"):
        t = asr["tornado"]; scr = asr["screen"]
        add("tornado", "Screen of every assumption (tornado)", f"All {scr['n_assumptions']} assumptions moved to the ends of their plausible ranges, the "
            f"decision re made under each. {_lab(pols, t['preferred'])[:1].upper() + _lab(pols, t['preferred'])[1:]} is worth {_bn(t['reference_nsv'])} at the run's values. "
            + " ".join(f"{_nice(r['assumption'])}: {_bn(r['low']['nsv'])} at {r['low']['value']} and {_bn(r['high']['nsv'])} at {r['high']['value']}"
                       + (", decision changes" if r["best_changes"] else "") + "." for r in t["rows"])
            + (f" The decision changes at an end of the range of {len(t['flips'])} of the {scr['n_assumptions']} assumptions"
               + ("; those with the largest swings are " if len(t["flips"]) > 12 else ": ") + ", ".join(_nice(k) for k in t["flips"][:12]) + "."
               if t["flips"] else " No single assumption changes the decision."))
    if asr.get("joint"):
        jd = asr["joint"]
        srow = {x["assumption"]: x for x in jd["sensitivity"]}
        top = [srow[k] for k in jd.get("margin_drivers", [])][:6]
        dd = [srow[k] for k in jd.get("decision_drivers", [])][:6]
        add("joint", "Joint draw of all the assumptions", f"{jd['draws']} joint draws over the plausible ranges. " + " ".join(
            f"{_lab(pols, x['policy'])[:1].upper() + _lab(pols, x['policy'])[1:]}: mean {_bn(x['nsv_mean'])} ({_bn(x['nsv_lo'])} to {_bn(x['nsv_hi'])}), the decision in "
            f"{_pct(x['p_best'])} of draws, within the constraints and above the status quo in {_pct(x['p_acceptable'])}, expected regret where it is within the constraints {_bn(x['expected_regret']) if x['expected_regret'] is not None else 'not defined (never within them)'}."
            for x in sorted(jd["alternatives"], key=lambda x: -x["p_best"]))
            + (" The decision margin moves with " + ", ".join(f"{_nice(x['assumption'])} (rank correlation {x['rho_margin']:+.2f})" for x in top)
               + f", the assumptions that pass a {_pct(jd.get('fdr', 0.1))} false discovery rate over all {len(jd['sensitivity'])}." if top
               else f" No assumption's rank correlation with the decision margin passes a {_pct(jd.get('fdr', 0.1))} false discovery rate at this number of draws.")
            + (" The draws in which the focus option is the decision differ from the others most in "
               + ", ".join(f"{_nice(x['assumption'])} (Kolmogorov Smirnov distance {x['ks_decision']:.2f})" for x in dd) + "." if dd else "")
            + (f" Lowest expected regret among the alternatives within the constraints in at least 90% of the draws: {_lab(pols, jd['least_regret'])}."
               if jd.get("least_regret") else "")
            + " " + jd["note"] + ".")
    if asr.get("variance"):
        var = asr["variance"]
        add("variance", "Variance decomposition", f"Sobol indices over {len(var['keys'])} assumptions for {_lab(pols, var['focus'])}, shares with "
            f"interactions and their 90% intervals: " + " ".join(
            f"{_nice(r['assumption'])}: {_pct(r['total_value'])} of the value's variance ({_pct(r['total_value_lo'])} to {_pct(r['total_value_hi'])}) and "
            f"{_pct(r['total_margin'])} of the margin's ({_pct(r['total_margin_lo'])} to {_pct(r['total_margin_hi'])})." for r in var["rows"])
            + " The intervals are wide: the design ranks groups of assumptions and does not order neighbours. " + var["note"] + ".")
    if asr.get("structural"):
        st = asr["structural"]
        add("structural", "Structural variants", f"{_lab(pols, st['preferred'])[:1].upper() + _lab(pols, st['preferred'])[1:]} remains the decision in {st['wins']} of {st['n']} variants and stays "
            f"within the constraints and above the status quo in {st['acceptable']}. " + " ".join(
            f"{_nice(v['variant'])} ({v['note']}): decision {_lab(pols, v['best'])}, focus rank {v['preferred_rank']}, "
            f"{'within' if v['preferred_feasible'] else 'outside'} the constraints." for v in st["variants"]))
    if asr.get("red_team"):
        rt = asr["red_team"]
        add("red_team", "Red team", f"When every instrument is gamed at its worst the best choice is {_lab(pols, rt['maximin'])}. " + " ".join(
            f"{r['label']}: honest {_bn(r['honest']['nsv'])}, worst strategy {_nice(r['worst_strategy'])} gives {_bn(r['worst_nsv'])}, loss {_bn(r['gaming_loss'])}, "
            f"{'acceptable' if r['acceptable_under_all'] else 'not acceptable'} under every strategy." for r in rt["rows"]))
    if asr.get("robustness"):
        rb = asr["robustness"]
        add("robustness", "Robustness", ("Robustly acceptable: " + (", ".join(pols[n]["label"] for n in rb["robustly_acceptable"]) or "no instrument")
            + f" ({rb['rule']}). ") + " ".join(
            f"{r['label']}: central {'yes' if r['central_acceptable'] else 'no'}, joint draws {_pct(r['joint_p_acceptable'])}, structural "
            f"{r['structural_acceptable']} of {r['structural_n']}, gaming {'yes' if r['gaming_acceptable'] else 'no'}." for r in rb["rows"]))
    val = asr.get("validation") or {}
    evs = val.get("events") or []
    mech = arte.get("mechanisms") or []
    vtxt = []
    for x in evs:
        es = x["event_study"]; cm = x.get("comparison")
        vtxt.append(f"{x['dataset']}: abnormal return {es['car'] * 100:+.1f}% (standard error {es['se_car'] * 100:.1f}%) over months 0 to 5, level effect "
                    f"{es['early_reaction'] * 100:+.1f}%"
                    + (f"; model for {_lab(pols, cm['policy'])} {cm['model_mean'] * 100:+.1f}% ({cm['model_lo'] * 100:+.1f}% to {cm['model_hi'] * 100:+.1f}%), "
                       f"observation {'inside' if cm['within_band'] else 'outside'} the band." if cm else "; not mapped to an instrument, so not compared."))
    vb = val.get("benchmarks")
    vsum = ""
    if vb:
        from . import validation as V
        s1, s2, s3 = V.narrative(vb, {n: _lab(pols, n) for n in pols}, {k: _nice(k) for k in arte["assumptions"]})
        vsum = s1 + " " + s2 + " " + s3 + " "
        add("benchmarks", "Benchmarks: the model against published evidence", " ".join(
            f"{r['benchmark']} ({r['kind']}): observed {r['observed']}, model {r['model']}, {r['verdict']}"
            + (f", across the declared ranges {r['ranges']}" if r["ranges"] else "") + "." for r in V.scorecard(vb))
            + " Sources: " + " ".join(f"{r['title']}: {'; '.join(x['cite'] for x in vb['sources'][r['id']]['sources'])}." for r in vb["rows"]))
        add("evidence_gaps", "Evidence examined and set aside", " ".join(f"{x['evidence']}: not used because {x['why_not']}" for x in vb.get("not_used", [])))
    add("validation", "Validation and evidence",
        "The Lab is synthetic: its figures are conditional on the model and its assumptions and are not validated forecasts. " + vsum
        + (" ".join(vtxt) + " " if vtxt else "No price series of an observed event was uploaded on this run. ")
        + ((val["coverage"]["statement"][:1].upper() + val["coverage"]["statement"][1:] + ". ") if val.get("coverage") else "")
        + f"No mechanism is estimated from data; {sum(1 for x in mech if x.get('confronted'))} of {len(mech)} were confronted with a published benchmark.")
    if mech:
        add("mechanisms", "Mechanism register", " ".join(f"{x['mechanism']}: {x['status']}; test: {x['validation_test']}" for x in mech))
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
        f"PSL {pv['psl_version']}, {arte['paths']} paths, horizon {arte['horizon']} months, seed {arte['seed']}, profile {arte.get('profile')}, "
        + (f"figures reused from run {arte['run']['reused_from']['run']} (identical battery and code)." if arte['run'].get('reused_from') else f"{arte['run']['elapsed_s']} s."))
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
    ("constraints", ("constraint", "budget", "feasib", "limit")),
    ("distribution", ("who pays", "who gains", "distribution", "incidence", "consumers", "taxpayers", "workers", "shareholders", "transfer")),
    ("news", ("news", "headline", "press", "wire", "coverage", "hearing", "pressure")),
    ("market", ("stock", "share price", "market", "valuation", "industry", "equity", "investor", "sector", "gain", "loss", "lose", "profit")),
    ("safety", ("safety", "safe ", "safer", "incident", "catastroph", "harm", "accident", "misuse")),
    ("gap", ("gap", "look", "early", "inversion", "tau")),
    ("uncertainty", ("uncertain", "confidence", "interval", "precis", "how sure", "monte carlo", "paths", "sampling", "standard error",
                     "noise", "replicat", "told apart", "distinguish", "significan")),
    ("joint", ("joint", "regret", "parameter uncertainty", "all together", "prior")),
    ("variance", ("variance", "sobol", "decomposition", "interaction")),
    ("tornado", ("tornado", "screen", "sensitiv", "assumption", "value judgement", "discount")),
    ("robustness", ("robust",)),
    ("structural", ("structural", "variant", "model structure")),
    ("red_team", ("red team", "gaming", "game", "evade", "arbitrage", "relocat", "offshore")),
    ("validation", ("validat", "calibrat", "evidence", "real world", "event study", "believe", "trust the model", "forecast")),
    ("mechanisms", ("mechanism", "causal", "identif")),
    ("ledger", ("ledger", "gate", "approv", "critic", "sign", "release")),
    ("firms", ("firm", "archetype", "company", "companies")),
    ("instruments", ("instrument", "what is", "what does", "explain", "describe")),
    ("provenance", ("provenance", "hash", "reproduce", "seed", "fingerprint")),
    ("preferred", ("cost", "expensive", "worth", "buy", "price tag", "society")),
    ("answer", ("which", "recommend", "best", "prefer", "should", "choose", "decision", "status quo", "do nothing")),
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
            return firm_text(arte, f), [by["market"], by["firms"]]
    # a named assumption
    qt = _tok(ql)
    for r in arte["assumption_table"]:
        words = [w for w in r["assumption"].split("_") if len(w) > 2 and w not in ("bn", "share", "base", "rate", "monthly")]
        hit = sum(1 for w in words if w in qt or any(t.startswith(w[:6]) for t in qt))
        if _nice(r["assumption"]).lower() in ql or r["assumption"] in ql or (words and hit >= min(2, len(words))):
            return assumption_text(arte, r), [by["assumptions"]] + ([by["tornado"]] if "tornado" in by else [])
    it = intent_of(q)
    if it == "preferred":
        srcs = [by[f"pol_{ev['focus']}"], by["distribution"]]
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
