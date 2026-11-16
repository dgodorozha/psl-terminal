"""The policy briefing: a regulatory impact assessment drafted only from
artefacts.json, in the order a decision maker reads one.

  1  the question and how it was read
  2  the answer: the decision among the alternatives, the status quo included, and how firm it is
  3  the options compared (one table), and the preferred option against each other one
  4  what the focus option buys and costs (the social ledger)
  5  who gains and who pays (an incidence table that sums to the ledger)
  6  the safety forecast
  7  the news environment to expect
  8  the market: the industry's net gain or loss, by firm and sector
  9  the decision gap: what looks best early against what is best
 10  how sure we are, by kind of uncertainty: Monte Carlo error, parameters, model structure, gaming, validation
 11  the assumptions, every one, with its plausible range
 12  monitoring: what to watch and when to revisit
 13  gates, provenance and reproduction

Three intervals appear and are never mixed: the 95% confidence interval of an expected value (how well the paths
estimate it), the 10th to 90th percentile range of the simulated outcomes (how different one path can be from
another), and, in section 10, the range an expected value takes when the assumptions move.

Every figure is read from the artefacts; the critic vets each number in
the text against them. A model, when configured, may rewrite the prose of
sections 2 and 12 and its draft is accepted only if every number in it
survives the same vetting (llm.py).
"""

import html as html_mod
import re

from ._common import nice_name as _nice
from . import welfare as W

COMP_LABELS = {"harm_avoided": "Harm avoided", "cs_change": "Consumer surplus", "productivity_change": "Output uplift (adoption)",
               "producer_surplus_change": "Resident producer surplus", "compliance_cost": "Compliance (resource cost)",
               "enforcement_cost": "Enforcement budget", "leakage": "Activity lost offshore", "relocation_cost": "Relocation cost",
               "labour_change": "Labour adjustment", "insurance_admin_cost": "Insurance administration (resource cost)"}


def _f(x, nd=1):
    if x is None:
        return "n/a"
    if abs(x) < 0.5 * 10 ** (-nd):
        x = 0.0
    return f"{x:,.{nd}f}"


def _bn(x, nd=1):
    if x is None:
        return "n/a"
    if abs(x) < 0.5 * 10 ** (-nd):
        x = 0.0
    sign = "-" if x < 0 else ""
    v = abs(x)
    if v >= 1000:
        return f"{sign}${v / 1000:,.2f}tn"
    return f"{sign}${v:,.{nd}f}bn"


def _pct(x, nd=0):
    return "n/a" if x is None else f"{x * 100:.{nd}f}%"


def _ci(s, nd=1, money=True):
    """Mean with its 95% confidence interval."""
    if money:
        return f"{_bn(s['mean'], nd)} (95% confidence interval {_bn(s['ci_lo'], nd)} to {_bn(s['ci_hi'], nd)})"
    return f"{_f(s['mean'], nd)} ({_f(s['ci_lo'], nd)} to {_f(s['ci_hi'], nd)})"


def _iv(s, nd=1):
    return f"[{_f(s['ci_lo'], nd)}, {_f(s['ci_hi'], nd)}]"


def _spread(s, nd=1):
    return f"[{_f(s['lo'], nd)}, {_f(s['hi'], nd)}]"


def _label(arte, name):
    if name == "baseline":
        return "the status quo"
    p = (arte.get("policies") or {}).get(name)
    return p["label"] if p else _nice(name) if name else "none"


def _row(r):
    return r


FLIPS_SHOWN = 12


def _tightest(row):
    """The constraint an alternative satisfies with the least room on the central estimate, in words; '' if none."""
    cc = [c for c in row.get("constraint_checks", []) if c["ok"] and c["limit"]]
    if not cc:
        return ""
    i = min(range(len(cc)), key=lambda k: abs(cc[k]["margin"]) / abs(cc[k]["limit"]))
    ix = row["constraint_checks"].index(cc[i])
    return "on the central estimate: " + row["constraint_notes"][ix]


def _num(x):
    return 4 if abs(x) < 0.1 else 2


def draft_briefing(arte, approvals=None, run_id="", critic=None):
    approvals = approvals or {}
    ev = arte["results"]
    pols = {r["policy"]: r for r in ev["policies"]}
    cand = [r for r in ev["policies"] if r["policy"] != "baseline"]
    dec = ev["decision"]
    pref = ev["preferred"]
    focus = ev["focus"]                               # the instrument sections 4 to 8 describe
    P = pols[focus]
    b = pols["baseline"]
    years = arte["horizon"] / 12
    pr = ev.get("precision") or {}
    L = []
    w = L.append
    w(f"# Policy Scenario Lab briefing")
    w("")
    w(f"**Run** {run_id or arte.get('battery_hash', '')[:12]}. **Question.** {arte['question']}")
    w("")
    reading = ", ".join(arte.get("reading", []))
    cons = arte.get("constraints") or {}
    cons_txt = "; ".join(_constraint_text(k, v) for k, v in cons.items() if not k.startswith("_")) or "none"
    grew = (f"{arte['paths']} Monte Carlo paths per alternative (the run started on {arte['initial_paths']} and doubled on the same random "
            f"streams, ceiling {arte['max_paths']})" if arte.get("initial_paths") and arte["paths"] != arte["initial_paths"]
            else f"{arte['paths']} Monte Carlo paths per alternative")
    w(f"**How it was read.** {len(cand)} instruments and the status quo ({reading}); horizon {years:.0f} years; "
      f"{grew}, every alternative on the same random numbers, seed {arte['seed']}; constraints: {cons_txt}.")
    w("")
    if arte.get("unread_conditions"):
        w("**A condition in the question was not applied.** The Lab did not read this as a constraint it can test, so the answer below "
          "does not take it into account: " + "; ".join(f'"{x}"' for x in arte["unread_conditions"]) + ". The constraints it can test are "
          "an industry loss limit, a gross social cost budget, a ceiling on the probability of a major or a catastrophic incident, a "
          "minimum harm reduction and a consumer surplus floor.")
        w("")
    w("**What this is.** A comparison of alternatives inside a synthetic model of the AI economy under declared assumptions. "
      "The figures are conditional on that model: they are scenario evaluations, not forecasts validated against data, and the "
      "preferred option is the model's answer to the question, to be examined, not an established recommendation."
      + _evidence_line(arte))
    w("")
    # ---- 2 the answer
    w("## The answer")
    w("")
    nsv = P["net_social_value"]
    if pref is None:
        w(f"**No alternative satisfies every constraint, the status quo included.** The instrument with the highest expected net social "
          f"value is {P['label']} at {_ci(nsv)}; the constraints each alternative fails are in the options table.")
    elif pref == "baseline":
        if ev["best_intervention"] is None:
            w(f"**No tested instrument satisfies the constraints; the status quo is the only feasible alternative.** The instrument with the "
              f"highest expected net social value is {P['label']} at {_ci(nsv)}; what it fails is in the options table.")
        else:
            w(f"**No tested instrument improves on the status quo.** The status quo scores zero by construction and is the preferred "
              f"alternative. The best instrument within the constraints is {P['label']}, with an expected net social value of {_ci(nsv)} "
              f"over {years:.0f} years: "
              + ("negative, so adopting it would be worse than doing nothing under the model's own objective."
                 if nsv["ci_hi"] < 0 else
                 "not above zero, and with a confidence interval that includes zero, so on these paths it cannot be told apart from "
                 "doing nothing and there is no case for adopting it under the model's own objective."))
    else:
        w(f"**Preferred option: {P['label']}.** Expected net social value {_ci(nsv)} over {years:.0f} years, the highest among the "
          f"alternatives that satisfy the constraints and above the status quo, which scores zero. "
          f"It avoids {_bn(P['components']['harm_avoided']['mean'])} of expected harm "
          f"({_pct(P['components']['harm_avoided']['mean'] / max(arte['baseline_reference']['harm_npv'], 1e-9))} of the status quo's), "
          f"and the industry's expected value change is {_ci(P['industry_value_change'], 0)}.")
    w("")
    w(f"Across the simulated outcomes the net social value of {P['label']} runs from {_bn(nsv['lo'])} (10th percentile) to {_bn(nsv['hi'])} "
      f"(90th percentile) and is positive on {_pct(nsv['p_positive'])} of paths; that range is how different one path can be from another, "
      f"not the uncertainty of the expected value, which the confidence interval gives. "
      + ("The confidence interval excludes zero." if nsv["ci_lo"] > 0 or nsv["ci_hi"] < 0 else
         "The confidence interval includes zero: on these paths the expected value is not distinguishable from the status quo."))
    w("")
    if pref:
        R = pols[pref]
        w(f"**How firm the decision is on these paths.** {R['label'] if pref != 'baseline' else 'The status quo'} is the best feasible "
          f"alternative in {_pct(R['p_best'])} of bootstrap resamples of the paths, with feasibility re assessed in each. That share is "
          f"ranking stability under the model and its assumptions; it is not the probability that the option is best in the world. "
          + (f"It satisfies the constraints in {_pct(R['p_feasible'])} of resamples. " if pref != "baseline" and cons_txt != "none" else "")
          + (f"Under the conservative rule ({dec['assured_rule']}) the preferred option is {_label(arte, dec['preferred_assured'])}. "
             if dec.get("preferred_assured") != pref else ""))
        others = [n for n in dec.get("confidence_set", [])]
        if others:
            w("")
            w(f"It cannot be told apart from {', '.join(_label(arte, n) for n in others)}: the simultaneous 95% interval of the paired "
              f"difference in expected net social value includes zero for {'each of them' if len(others) > 1 else 'it'}.")
        w("")
    unc = [n for n in dec.get("feasibility_uncertain", [])]
    if unc:
        w("**Feasibility that the paths do not settle.** " + "; ".join(
            f"{pols[n]['label']} is within the constraints in {_pct(pols[n]['p_feasible'])} of resamples (expected net social value "
            f"{_bn(pols[n]['net_social_value']['mean'])})" for n in unc)
          + ". A constraint is tested on an estimate; where the limit sits inside the estimate's interval, inclusion or exclusion is not settled.")
        w("")
    if pr:
        if pr.get("met"):
            w(f"Every precision target was met at {pr['paths']} paths.")
        else:
            w(f"**Short of the precision target at the ceiling of {pr['max_paths']} paths:** " + "; ".join(x["text"] for x in pr["unresolved"]) + ".")
        w("")
    bu = ev["best_unconstrained"]
    if pref and bu and bu != pref and bu != "baseline":
        fails = [n for n, c in zip(pols[bu]["constraint_notes"], pols[bu]["constraint_checks"]) if not c["ok"]]
        w(f"With the constraints lifted, {pols[bu]['label']} scores higher ({_bn(pols[bu]['net_social_value']['mean'])})"
          + (" but fails: " + "; ".join(fails) if fails else "") + ".")
        w("")
    # ---- 3 options
    w("## The options compared")
    w("")
    w("| Alternative | Expected net social value, $bn | 95% confidence interval | Outcomes, 10th to 90th percentile | Harm avoided, $bn | Gross social cost, $bn "
      "| Industry value change, $bn | P(catastrophe) | Headline score | Within constraints | Share of resamples within | Ranking stability |")
    w("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for r in sorted(ev["policies"], key=lambda r: -r["net_social_value"]["mean"]):
        tag = " (preferred)" if r["policy"] == pref else ""
        v = r["net_social_value"]
        w(f"| {r['label']}{tag} | {_f(v['mean'])} | {_iv(v)} | {_spread(v)} "
          f"| {_f(r['components']['harm_avoided']['mean'])} | {_f(r['gross_cost']['mean'])} | {_f(r['industry_value_change']['mean'], 0)} "
          f"| {_pct(r['safety']['p_catastrophe'], 1)} | {r['headline_score']:+.3f} | {'yes' if r['feasible'] else 'no'} | {_pct(r['p_feasible'])} | {_pct(r['p_best'])} |")
    w("")
    bs = b["safety"]; pc = bs["p_catastrophe_detail"]
    w(f"The status quo carries an expected harm of {_bn(arte['baseline_reference']['harm_npv'])} over the horizon, "
      f"{_f(bs['incidents_per_year']['mean'])} reportable incidents a year, a {_pct(bs['p_major'])} probability of at least one major "
      f"incident and a {_pct(bs['p_catastrophe'], 1)} probability of a catastrophic one (95% confidence interval {_pct(pc['ci_lo'], 1)} to "
      f"{_pct(pc['ci_hi'], 1)}; a catastrophe was drawn on {pc['k']} of {pc['n']} paths). The probability is estimated from the hazard "
      f"each path accumulates, not from the count of paths on which the event happened to be drawn, which is why it is far more precise "
      f"than that count.")
    w("")
    if pref:
        rows = [r for r in ev["policies"] if r.get("vs_preferred") and r["feasible"]]
        if rows:
            w(f"**{_label(arte, pref)[:1].upper() + _label(arte, pref)[1:]} against each other feasible alternative** (paired on the same paths):")
            w("")
            w("| Against | Difference in expected net social value, $bn | 95% confidence interval | Simultaneous 95% interval | Told apart |")
            w("|---|---|---|---|---|")
            for r in rows:
                v = r["vs_preferred"]
                w(f"| {r['label']} | {_f(v['difference'])} | [{_f(v['ci_lo'])}, {_f(v['ci_hi'])}] | [{_f(v['simultaneous_lo'])}, {_f(v['simultaneous_hi'])}] "
                  f"| {'yes' if v['distinguishable'] else 'no'} |")
            w("")
    # ---- 4 the ledger of the focus option
    w(f"## What {P['label']} buys and costs")
    w("")
    w("| Component | Expected value, $bn present value | 95% confidence interval | Outcomes, 10th to 90th percentile |")
    w("|---|---|---|---|")
    for k in W.BENEFITS:
        c = P["components"][k]
        w(f"| {COMP_LABELS[k]} | {_f(c['mean'])} | {_iv(c)} | {_spread(c)} |")
    for k in W.COSTS:
        c = P["components"][k]
        w(f"| {COMP_LABELS[k]}{'' if 'cost' in COMP_LABELS[k].lower() else ' (cost)'} | {_f(-c['mean'])} | [{_f(-c['ci_hi'])}, {_f(-c['ci_lo'])}] | [{_f(-c['hi'])}, {_f(-c['lo'])}] |")
    w(f"| **Net social value** | **{_f(nsv['mean'])}** | {_iv(nsv)} | {_spread(nsv)} |")
    w("")
    c = P["components"]["harm_avoided"]
    w(f"Expected harm avoided is estimated from the harm expected in each month given the state the path has reached (probability times "
      f"mean severity), which has the same expectation as the harm drawn and far less variance. The outcomes column uses the harm as drawn: "
      f"its median is {_bn(c.get('median'))} and the average of the draws is {_bn(c.get('mean_drawn'))}"
      + (f"; {_pct(c['tail_share'])} of that average comes from the tenth of paths with the largest values, the paths on which a catastrophic "
         f"incident is averted" if c.get("tail_share", 0) >= 0.3 else "") + ".")
    w("")
    cpe = P.get("cost_per_harm_avoided")
    w(f"Gross social cost {_bn(P['gross_cost']['mean'])} (the expected component changes that are costs, never netted against savings), "
      f"gross benefit {_bn(P['gross_benefit']['mean'])}; their difference is the net social value"
      + (f". Gross cost per dollar of expected harm avoided: {_f(cpe, 2)}." if cpe else "."))
    tr = P["transfers"]
    w(f"Transfers, excluded from the net: fines {_bn(tr['fines'])}, liability paid by firms {_bn(tr['liability'])}, insurance premiums "
      f"{_bn(tr['premiums'])}, claims paid to victims {_bn(tr['claims'])}.")
    w("")
    # ---- 5 incidence
    w("## Who gains and who pays")
    w("")
    w("| Party | Change, $bn present value |")
    w("|---|---|")
    for k, v in P["distribution"].items():
        w(f"| {k[:1].upper() + k[1:]} | {_f(v)} |")
    w(f"| **Total** | **{_f(P['incidence_total'])}** |")
    w("")
    w(f"The table follows the money as well as the real effects, so it sums to the net social value ({_bn(nsv['mean'])}) plus what "
      f"non resident owners finance of the firms' payments ({_bn(P['nonresident_payments'])}), a memorandum item the net social value "
      f"does not count. Standing is residents: real resources used in the jurisdiction count in full, income counts for residents, and "
      f"transfers are excluded whoever pays.")
    w("")
    # ---- 6 safety
    w("## Safety forecast")
    w("")
    w("| Alternative | Incidents a year | Major a year | P(major) | P(catastrophe) | 95% confidence interval | Expected harm, $bn | Safety level at end | Frontier capability at end | Trust at end |")
    w("|---|---|---|---|---|---|---|---|---|---|")
    for r in ev["policies"]:
        s = r["safety"]; d = s["p_catastrophe_detail"]
        w(f"| {r['label']} | {_f(s['incidents_per_year']['mean'])} | {_f(s['major_per_year']['mean'], 2)} | {_pct(s['p_major'])} | {_pct(s['p_catastrophe'], 1)} "
          f"| {_pct(d['ci_lo'], 1)} to {_pct(d['ci_hi'], 1)} "
          f"| {_f(s['expected_harm_npv']['mean'])} | {_f(s['safety_level_end'], 2)} | {_f(s['frontier_capability_end'], 2)} | {_f(s['trust_end'], 2)} |")
    s = P["safety"]
    w("")
    w(f"Under {P['label']} the economy runs {_f(s['incidents_per_year']['mean'])} reportable incidents a year "
      f"(misuse {_f(s['incidents_by_category_per_year']['misuse'])}, accidents {_f(s['incidents_by_category_per_year']['accident'])}, "
      f"systemic {_f(s['incidents_by_category_per_year']['systemic'])}), against {_f(b['safety']['incidents_per_year']['mean'])} at the status quo; "
      f"the expected catastrophic harm is {_bn(s['expected_catastrophe_harm_npv'])} against {_bn(b['safety']['expected_catastrophe_harm_npv'])}. "
      f"Firms end with {_pct(s['safety_share_end'])} of R&D on safety, {_pct(s['offshore_share_end'])} of activity offshore and "
      f"{_pct(s['compliance_share'])} compliance. A major incident is a single incident at or above the threshold; catastrophes are counted apart.")
    w("")
    # ---- 7 news
    w("## The news environment to expect")
    w("")
    nP = P["news"]
    w("| Alternative | Minor incident headlines a year | Major incident headlines a year | Enforcement headlines a year | Relocation headlines a year | Peak pressure | P(hearing) | Early tone |")
    w("|---|---|---|---|---|---|---|---|")
    for r in ev["policies"]:
        n = r["news"]; h = n["headlines_per_year"]
        w(f"| {r['label']} | {_f(h['minor incidents']['mean'])} | {_f(h['major incidents']['mean'], 2)} | {_f(h['enforcement actions']['mean'], 2)} "
          f"| {_f(h['relocations']['mean'], 2)} | {_f(n['peak_pressure']['mean'], 2)} | {_pct(n['p_hearing'])} | {n['early_tone']:+.2f} |")
    w("")
    ws = arte["news"][focus]
    worst = ws.get("worst", [])
    w(f"On the representative path the wire under {P['label']} ran {ws.get('headlines', 0)} headlines over the horizon, "
      f"{_pct(ws.get('share_negative', 0))} of them negative. The three worst: " +
      "; ".join(f"\"{x['headline']}\" ({x['outlet']}, {x['date']})" for x in worst) + ".")
    w("")
    # ---- 8 market
    w("## The market")
    w("")
    m = P["market"]
    iv = P["industry_value_change"]
    w(f"Industry net value change under {P['label']}: {_ci(iv, 0)} on a starting value of {_bn(m['industry_cap0'], 0)}; across outcomes "
      f"{_bn(iv['lo'], 0)} to {_bn(iv['hi'], 0)}, and the industry gains on {_pct(iv['p_positive'])} of paths. "
      f"The value weighted index reacts {m['early_reaction']['mean'] * 100:+.1f}% against the status quo over the first six months and "
      f"{m['end_reaction']['mean'] * 100:+.1f}% by the end of the horizon. Every index is measured from the same valuation, the firms as "
      f"they stand before any instrument is announced, so an instrument's immediate effect on fundamentals shows in the first month.")
    w("")
    w("| Firm | Sector | Expected value change, $bn | 95% confidence interval | Outcomes, 10th to 90th | P(gain) | Earnings change, $bn | Offshore at end | Safety share at end |")
    w("|---|---|---|---|---|---|---|---|---|")
    for fr in m["firms"]:
        v = fr["value_change"]
        w(f"| {fr['firm']} | {_nice(fr['sector'])} | {_f(v['mean'])} | {_iv(v)} | {_spread(v)} | {_pct(v['p_positive'])} "
          f"| {_f(fr['earnings_change_npv'])} | {_pct(fr['offshore_end'])} | {_pct(fr['safety_share_end'])} |")
    w("")
    w("| Sector | Expected value change, $bn | Starting value, $bn |")
    w("|---|---|---|")
    for sr in m["sectors"]:
        w(f"| {_nice(sr['sector'])} | {_f(sr['value_change']['mean'])} | {_f(sr['cap0'], 0)} |")
    w("")
    w("The firms are synthetic archetypes of the AI value chain, not companies; the figures are the model's and carry its assumptions. "
      "Shareholder value is a market metric and a constraint; it is not part of the net social value.")
    w("")
    # ---- 9 the gap
    g = ev["decision_gap"]
    w("## The decision gap")
    w("")
    w(f"Ranked by how they look in the first six months (the price reaction and the early tone of the wire), the instruments are "
      f"{', '.join(pols[n]['label'] for n in g['headline_order'])}. Ranked by expected net social value over {years:.0f} years they are "
      f"{', '.join(pols[n]['label'] for n in g['social_order'])}. Kendall tau b between the two is {g['kendall_tau']:+.2f}; the decision gap "
      f"({'(1 - tau) / 2'}) is {_f(g['decision_gap'], 2)}, and the two orders invert in {_pct(g['p_inversion'])} of resamples.")
    w("")
    # ---- 10 assurance
    w("## How sure we are")
    w("")
    asr = arte.get("assurance") or {}
    w(f"**Monte Carlo error.** Every expected value above carries the 95% bootstrap confidence interval of its mean over {ev['bootstrap']} "
      f"resamples of the paths, paired across alternatives. " + (
          f"The run followed its sampling plan: {' then '.join(str(x) for x in pr['schedule'])} paths, stopping when the preferred "
          f"alternative was resolved against every other feasible one to within {_bn(pr['targets']['nsv_gap_bn'])} and the catastrophe "
          f"probabilities to within {_pct(pr['targets']['p_catastrophe_halfwidth'])}, or at the ceiling. The intervals are not adjusted for "
          f"those sequential looks." if pr else ""))
    cv = asr.get("convergence")
    if cv and len(cv["rows"]) > 1:
        w("")
        w("Convergence of the running estimate (the first paths of the run are exactly what a smaller run on this seed reports):")
        w("")
        w(f"| Paths | Decision | Expected net social value of {_label(arte, cv['focus'])}, $bn | Standard error | P(catastrophe), status quo |")
        w("|---|---|---|---|---|")
        for r in cv["rows"]:
            w(f"| {r['paths']:,} | {_label(arte, r['preferred'])} | {_f(r['focus_nsv'])} | {_f(r['focus_se'], 2)} | {_pct(r['p_catastrophe_status_quo'], 1)} |")
        w("")
        w(("The decision is the same over the last doubling of the paths" if cv["decision_stable_over_last_doubling"]
           else "The decision changes over the last doubling of the paths, which is a reason to run more")
          + (", and the final estimate lies inside every earlier interval." if cv["final_inside_earlier_intervals"]
             else "; the final estimate lies outside an earlier interval, as about one in twenty would by chance."))
    bt = asr.get("batches")
    if bt:
        w("")
        w(f"Split into {bt['k']} independent batches of {bt['size']} paths, the run gives the same decision in {bt['agree']} of them "
          f"({', '.join(_label(arte, r['preferred']) for r in bt['rows'])}).")
    w("")
    torn = asr.get("tornado"); scr = asr.get("screen")
    if torn:
        w(f"**Parameters, one at a time.** Each of the {scr['n_assumptions']} declared assumptions was moved to the low and the high end "
          f"of its plausible range, the decision re made under each (feasibility re assessed, the status quo an alternative). "
          f"{_label(arte, torn['preferred'])[:1].upper() + _label(arte, torn['preferred'])[1:]} is worth {_bn(torn['reference_nsv'])} at the run's values. "
          f"The {torn['shown']} largest swings:")
        w("")
        w("| Assumption | Run's value | Low | Value at low, $bn | Decision at low | High | Value at high, $bn | Decision at high |")
        w("|---|---|---|---|---|---|---|---|")
        for r in torn["rows"]:
            w(f"| {_nice(r['assumption'])} | {_f(r['default'], _num(r['default']))} | {_f(r['low']['value'], _num(r['low']['value']))} | {_f(r['low']['nsv'])} "
              f"| {_label(arte, r['low']['best'])} | {_f(r['high']['value'], _num(r['high']['value']))} | {_f(r['high']['nsv'])} | {_label(arte, r['high']['best'])} |")
        w("")
        if torn["flips"]:
            fl = torn["flips"]                       # ordered by swing, largest first
            w(f"The decision changes at an end of the range of {len(fl)} of the {scr['n_assumptions']} assumptions"
              + (f"; the {FLIPS_SHOWN} with the largest swings are " if len(fl) > FLIPS_SHOWN else ": ")
              + ", ".join(_nice(k) for k in fl[:FLIPS_SHOWN])
              + (f" (the screen in the artefacts lists all {len(fl)})" if len(fl) > FLIPS_SHOWN else "")
              + f". The sign of the focus option's value is {'robust' if torn['sign_robust'] else 'not robust'} across the screen. "
              + (f"For {len(scr['flips_by_feasibility'])} of them the cause is feasibility: {_label(arte, scr['reference_best'])} stops "
                 f"satisfying a constraint under the alternative"
                 + (f" ({_tightest(pols[scr['reference_best']])})" if scr["reference_best"] in pols and _tightest(pols[scr["reference_best"]]) else "")
                 + f"; for {len(scr['flips_by_value'])} another alternative within the constraints overtakes it. "
                 if scr.get("flips_by_feasibility") is not None else "")
              + f"Each re simulated assumption ran on the first {scr['resimulated_paths']} paths, paired with the main run: "
              f"{scr.get('n_swing_resolved', 0)} of the {scr['n_assumptions']} swings exceed twice their Monte Carlo standard error, and a "
              f"change of decision inside that error is a warning to look, not a finding.")
        else:
            w("No single assumption at an end of its range changes the decision.")
        w("")
    jd = asr.get("joint")
    if jd:
        w(f"**Parameters, all together.** {jd['draws']} joint draws of every assumption over its plausible range (correlated where they "
          f"plausibly move together). Under that parameter uncertainty:")
        w("")
        w("| Alternative | Mean net social value, $bn | 5th to 95th percentile over the draws | Share of draws it is the decision | Share of draws within constraints | Share within constraints and above the status quo | Expected regret where within constraints, $bn |")
        w("|---|---|---|---|---|---|---|")
        for x in sorted(jd["alternatives"], key=lambda x: -x["p_best"]):
            w(f"| {_label(arte, x['policy'])[:1].upper() + _label(arte, x['policy'])[1:]} | {_f(x['nsv_mean'])} | [{_f(x['nsv_lo'])}, {_f(x['nsv_hi'])}] | {_pct(x['p_best'])} "
              f"| {_pct(x['p_feasible'])} | {_pct(x['p_acceptable'])} | {_f(x['expected_regret']) if x['expected_regret'] is not None else 'n/a'} |")
        w("")
        w("Regret is how far an alternative falls short of the best alternative within the constraints in the same draw, averaged over the "
          "draws in which it is itself within them; it is read beside the share of draws in which it is, because choosing an alternative "
          "where it breaks a constraint is not a cost in $bn."
          + (f" Among the alternatives within the constraints in at least 90% of the draws, {_label(arte, jd['least_regret'])} has the lowest expected regret."
             if jd.get("least_regret") else ""))
        w("")
        srow = {s_["assumption"]: s_ for s_ in jd["sensitivity"]}
        top = [srow[k] for k in jd.get("margin_drivers", [])][:6]
        dd = [srow[k] for k in jd.get("decision_drivers", [])][:6]
        n_ass = len(jd["sensitivity"])
        w("The ranges are declared judgements, a prior over the assumptions and not a posterior estimated from data. "
          + (f"The margin of {_label(arte, jd['focus'])} over the best alternative moves with "
             + ", ".join(f"{_nice(s_['assumption'])} (rank correlation {s_['rho_margin']:+.2f})" for s_ in top)
             + f": of the {n_ass} assumptions, {len(jd['margin_drivers'])} pass a {_pct(jd['fdr'])} false discovery rate on that correlation."
             if top else f"No assumption's rank correlation with the decision margin passes a {_pct(jd.get('fdr', 0.1))} false discovery rate "
                         f"over the {n_ass} assumptions at this number of draws.")
          + (" The draws in which it is the decision differ from the draws in which it is not most in "
             + ", ".join(f"{_nice(s_['assumption'])} (Kolmogorov Smirnov distance {s_['ks_decision']:.2f})" for s_ in dd) + "."
             if dd else ""))
        w("")
    var = asr.get("variance")
    if var:
        w(f"**Which assumptions carry the variance.** A Sobol decomposition over the {len(var['keys'])} assumptions with the largest swings "
          f"({var['evaluations']} evaluations), for the value of {_label(arte, var['focus'])} and for its margin over the best alternative. "
          f"Shares with interactions (total order), with the 90% interval the size of the design allows:")
        w("")
        w("| Assumption | Share of the value's variance, with interactions | 90% interval | Share of the margin's variance, with interactions | 90% interval | Alone (first order), margin |")
        w("|---|---|---|---|---|---|")
        for r in var["rows"]:
            w(f"| {_nice(r['assumption'])} | {_pct(r['total_value'])} | {_pct(r['total_value_lo'])} to {_pct(r['total_value_hi'])} "
              f"| {_pct(r['total_margin'])} | {_pct(r['total_margin_lo'])} to {_pct(r['total_margin_hi'])} | {_pct(r['first_order_margin'])} |")
        w("")
        w(f"The intervals are wide (half width {_pct(var['mean_halfwidth_total_margin'])} on average for the margin): the output is heavy "
          f"tailed in these assumptions, which compound, so a design of this size ranks groups of assumptions and does not order "
          f"neighbours. Shares with interactions add to more than one when the assumptions interact, as these do: first order shares "
          f"sum to {_pct(var['sum_first_order_margin'])} of the margin's variance.")
        w("")
    st = asr.get("structural")
    if st:
        w(f"**Model structure.** Under {st['n']} alternative model structures {_label(arte, st['preferred'])} remains the decision in "
          f"{st['wins']} and stays within the constraints and above the status quo in {st['acceptable']}:")
        w("")
        w("| Variant | What changes | Decision | Focus option's rank among instruments | Its value, $bn | Within constraints |")
        w("|---|---|---|---|---|---|")
        for v in st["variants"]:
            w(f"| {_nice(v['variant'])} | {v['note']} | {_label(arte, v['best'])} | {v['preferred_rank']} | {_f(v['preferred_nsv'])} | {'yes' if v['preferred_feasible'] else 'no'} |")
        w("")
    rt = asr.get("red_team")
    if rt:
        w("**Gaming.** Firms game each instrument four ways; the instrument under its worst strategy, and whether it is then still within "
          "the constraints and above the status quo:")
        w("")
        w("| Instrument | Honest value, $bn | Worst strategy | Value when gamed, $bn | Harm avoided when gamed, $bn | Loss to gaming, $bn | Acceptable under every strategy |")
        w("|---|---|---|---|---|---|---|")
        for r in rt["rows"]:
            ws_ = r["strategies"][r["worst_strategy"]]
            w(f"| {r['label']} | {_f(r['honest']['nsv'])} | {_nice(r['worst_strategy'])} | {_f(r['worst_nsv'])} | {_f(ws_['harm_avoided'])} | {_f(r['gaming_loss'])} "
              f"| {'yes' if r['acceptable_under_all'] else 'no'} |")
        w("")
        w(f"When every instrument is gamed at its worst, the best choice is {_label(arte, rt['maximin'])}. Strategies: " +
          "; ".join(f"{_nice(k)}: {v}" for k, v in rt["strategies"].items()) + ".")
        w("")
    rb = asr.get("robustness")
    if rb:
        ra = rb["robustly_acceptable"]
        w("**Robustly acceptable.** " + (", ".join(pols[n]["label"] for n in ra) if ra else "No instrument") +
          f" {'are' if len(ra) > 1 else 'is'} {rb['rule']}."
          + (f" The preferred option is not among them: it is the best on the central estimate and not robust to the alternatives above."
             if pref and pref != "baseline" and pref not in ra else ""))
        w("")
    val = asr.get("validation") or {}
    evs = val.get("events") or []
    n_mech = len(arte.get("mechanisms", []))
    n_test = sum(1 for m_ in arte.get("mechanisms", []) if m_.get("tested_here"))
    vb = val.get("benchmarks")
    if vb:
        from . import validation as V
        s1, s2, s3 = V.narrative(vb, {n: _label(arte, n) for n in arte["policies"]}, {k: _nice(k) for k in arte["assumptions"]})
        w("**Validation against published evidence.** " + s1)
        w("")
        w("| Benchmark | Kind | Observed (allowance, one sd) | Model at the central assumptions | z | Verdict | Model across the declared ranges, 5th to 95th | Predicted with it held out |")
        w("|---|---|---|---|---|---|---|---|")
        for r in V.scorecard(vb):
            w(f"| {r['benchmark']} | {r['kind']} | {r['observed']} | {r['model']} | {r['z']} | {r['verdict']} | {r['ranges']} | {r['held_out']} |")
        w("")
        w("The allowance is the benchmark's own standard error combined with a declared allowance for the distance between the setting "
          "it was measured in and the model's; z is the gap between model and observation in those units, with the Monte Carlo error of "
          "the model's value added. Not contradicted: within two; in tension: two to three; contradicted: beyond three. A benchmark is "
          "predicted with it held out from the draws weighted by all the others.")
        w("")
        if s2:
            w(s2)
            w("")
        cbm = (vb.get("calibration") or {}).get("assumptions") or []
        if cbm:
            w("| Assumption the benchmarks bear on | Value on this run | Mean of the draws | Weighted mean | Shift, in sd of the draws | Spread kept | Through |")
            w("|---|---|---|---|---|---|---|")
            for m_ in cbm[:10]:
                w(f"| {_nice(m_['assumption'])} | {m_['default']:.4g} | {m_['prior_mean']:.4g} | {m_['posterior_mean']:.4g} | {m_['shift']:+.2f} | "
                  f"{100 * m_['shrink']:.0f}% | {', '.join(e['benchmark'].replace('_', ' ') for e in m_['informed_by'][:3])} |")
            w("")
        w(s3)
        w("")
    if evs:
        for x in evs:
            es = x["event_study"]; cmp_ = x.get("comparison")
            w(f"**Validation against an observed event.** {x['dataset']} ({x['classification']}): abnormal return {es['car'] * 100:+.1f}% "
              f"(standard error {es['se_car'] * 100:.1f}%) over months 0 to 5 from {es.get('event_month', 'the event month')}, an average "
              f"level effect of {es['early_reaction'] * 100:+.1f}%, estimated on the {es['n_est']} monthly returns before the event month. "
              + (f"The model's early reaction for {_label(arte, cmp_['policy'])} at the {x['level']} level is {cmp_['model_mean'] * 100:+.1f}% "
                 f"(10th to 90th percentile {cmp_['model_lo'] * 100:+.1f}% to {cmp_['model_hi'] * 100:+.1f}%); the observation is "
                 f"{'inside' if cmp_['within_band'] else 'outside'} that band."
                 if cmp_ else "It was not mapped to an instrument, so it is reported and not compared."))
            w("")
        cov = val.get("coverage")
        if cov:
            w(cov["statement"][:1].upper() + cov["statement"][1:] + ".")
            w("")
    else:
        w("**Validation against an observed event.** No price series was uploaded on this run, so the market's early reaction was not "
          "compared with an event of the authority's own.")
        w("")
    if vb:
        w(f"No mechanism of the model is estimated from data. The benchmarks above show where its declared assumptions sit against what has "
          f"been measured elsewhere; the mechanism register lists, for each of the {n_mech} mechanisms, the evidence that would test it. "
          f"Common random numbers make the comparison between alternatives precise inside the model; they do not make the model true.")
    else:
        w(f"Of the {n_mech} causal mechanisms in the model, {n_test} can be confronted with data here (the market's early reaction) and none "
          f"is calibrated; the rest are declared assumptions, listed in the mechanism register with the evidence that would test each. "
          f"Common random numbers make the comparison between alternatives precise inside the model; they do not make the model true.")
    w("")
    # ---- 11 assumptions
    w("## Assumptions")
    w("")
    w(f"Every value judgement and behavioural parameter, hash `{arte['assumptions_hash']}`, with the plausible range the screen and the "
      f"joint draw move it over:")
    w("")
    w("| Assumption | Value | Plausible range | Unit | Meaning |")
    w("|---|---|---|---|---|")
    for r in arte["assumption_table"]:
        nd = _num(r["value"]) if r["value"] else 2
        w(f"| {_nice(r['assumption'])} | {_f(r['value'], nd)} | {_f(r['range_low'], _num(r['range_low']) if r['range_low'] else 2)} to "
          f"{_f(r['range_high'], _num(r['range_high']))} | {r['unit']} | {r['meaning']} |")
    w("")
    # ---- 12 monitoring
    vb_ = ((arte.get("assurance") or {}).get("validation") or {}).get("benchmarks")
    if vb_:
        w("## The evidence the model was confronted with")
        w("")
        w("Each benchmark, the model quantity it is compared with, and its source. The set is part of the battery approved at Gate 1 "
          f"(evidence hash `{str(vb_.get('evidence_hash'))[:16]}`); an authority replaces or extends it with its own data.")
        w("")
        for r in vb_["rows"]:
            src = vb_["sources"].get(r["id"], {})
            cites = "; ".join(f"{x['cite']}" + (f" ({x['url']})" if x.get("url") else "") for x in src.get("sources", []))
            w(f"- **{r['title']}** ({r['kind']}). Model quantity: {src.get('mapping')}. Allowance for the distance from the model: "
              f"{src.get('transport_basis')}. Caveat: {src.get('caveat')}. Source: {cites}.")
        w("")
        if vb_.get("not_used"):
            w("Examined and set aside:")
            w("")
            for x in vb_["not_used"]:
                w(f"- {x['evidence']} ({x['source']['cite']}). Bears on {x['bears_on'].replace('_', ' ')}. Not used because {x['why_not']}")
            w("")
    w("## Monitoring and revisiting")
    w("")
    flips = (torn or {}).get("flips", [])
    w(f"Indicators to watch, with the model's expectation under {P['label']}: reportable incidents a year "
      f"({_f(s['incidents_per_year']['lo'])} to {_f(s['incidents_per_year']['hi'])} across outcomes); the share of activity offshore "
      f"({_pct(s['offshore_share_end'])} at the horizon); the news pressure index (peak {_f(nP['peak_pressure']['mean'], 2)}, a hearing in {_pct(nP['p_hearing'])} of paths); "
      f"the industry's value against the status quo ({m['end_reaction']['mean'] * 100:+.1f}% at the horizon). "
      f"Revisit the decision if incidents run above that range for two quarters, if relocation exceeds the forecast, or if any of "
      f"{', '.join(_nice(k) for k in flips[:8]) or 'the tail assumptions'} can be estimated from data.")
    w("")
    # ---- 13 gates and provenance
    w("## Gates, provenance and reproduction")
    w("")
    for key in ("gate1", "gate2"):
        g1 = approvals.get(key)
        if g1 and g1.get("open_gate"):
            w(f"**{'Gate 1 (battery)' if key == 'gate1' else 'Gate 2 (release)'}**: {g1.get('decision')} at {str(g1.get('ts', ''))[:19]} in a "
              f"public demonstration, without a sign off identity; inside an authority a named approver on the register takes this gate"
              + (f"; reason: {g1.get('reason')}" if g1.get("reason") else "") + ".")
        elif g1:
            reg = g1.get("register") or {}
            w(f"**{'Gate 1 (battery)' if key == 'gate1' else 'Gate 2 (release)'}**: {g1.get('decision')} by {g1.get('actor')}"
              + (f", {g1.get('role')}" if g1.get("role") else "") + (f" ({reg.get('source')})" if reg.get("dev_mode") else
                 (f"; on the register as {reg.get('function')} at {reg.get('firm')}, reference {reg.get('irn')}" if reg.get("irn") else ""))
              + f" at {str(g1.get('ts', ''))[:19]}" + (f"; reason: {g1.get('reason')}" if g1.get("reason") else "") + ".")
    if critic:
        w(f"**Critic**: {critic['n_checks'] - critic['n_failed']} of {critic['n_checks']} checks passed before release.")
    pv = arte["provenance"]
    w(f"Battery hash `{arte['battery_hash']}`; code fingerprint `{pv['code_fingerprint']}`; PSL {pv['psl_version']}, numpy {pv['numpy']}{(', scipy ' + pv['scipy']) if pv.get('scipy') else ''}; "
      f"profile {arte.get('profile')}; {_run_time(arte)}. Reproduce with `python -m psl.orchestrator --battery battery.json`.")
    w("")
    return "\n".join(L)


def _constraint_text(k, v):
    return {"max_industry_loss_bn": f"industry loss at most ${v:,.0f}bn", "max_social_cost_bn": f"gross social cost at most ${v:,.0f}bn",
            "max_p_major": f"P(major incident) at most {v:.0%}", "max_p_catastrophe": f"P(catastrophe) at most {v:.0%}",
            "min_harm_reduction_pct": f"harm cut by at least {v:.0f}%", "max_cs_loss_pct": f"consumer surplus loss at most {v:.0f}%"}.get(k, f"{k}={v}")


def to_html(md_text, title="Policy Scenario Lab briefing"):
    """Minimal markdown to HTML for the printable briefing (headings, paragraphs, bold, tables, code spans)."""
    lines = md_text.split("\n")
    out, in_table = [], False
    for ln in lines:
        if ln.startswith("|"):
            cells = [c.strip() for c in ln.strip().strip("|").split("|")]
            if all(set(c) <= set("-: ") for c in cells):
                continue
            if not in_table:
                out.append("<table>")
                in_table = True
                out.append("<tr>" + "".join(f"<th>{_inline(c)}</th>" for c in cells) + "</tr>")
            else:
                out.append("<tr>" + "".join(f"<td>{_inline(c)}</td>" for c in cells) + "</tr>")
            continue
        if in_table:
            out.append("</table>")
            in_table = False
        if ln.startswith("# "):
            out.append(f"<h1>{_inline(ln[2:])}</h1>")
        elif ln.startswith("## "):
            out.append(f"<h2>{_inline(ln[3:])}</h2>")
        elif ln.strip():
            out.append(f"<p>{_inline(ln)}</p>")
    if in_table:
        out.append("</table>")
    css = ("body{font:14px/1.5 Georgia,serif;color:#111;max-width:1040px;margin:32px auto;padding:0 20px}"
           "h1{font-size:22px;border-bottom:2px solid #111;padding-bottom:6px}h2{font-size:16px;margin-top:26px}"
           "table{border-collapse:collapse;font:12px ui-monospace,Menlo,monospace;margin:10px 0}"
           "th,td{border:1px solid #bbb;padding:4px 7px;text-align:left}th{background:#f2f2f2}"
           "code{font:12px ui-monospace,Menlo,monospace;background:#f2f2f2;padding:1px 3px}"
           "@media print{body{margin:0;max-width:none}}")
    return (f"<!doctype html><html><head><meta charset='utf-8'><title>{html_mod.escape(title)}</title>"
            f"<style>{css}</style></head><body>" + "\n".join(out) + "</body></html>")


def _inline(s):
    s = html_mod.escape(s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"`(.+?)`", r"<code>\1</code>", s)
    return s


def _run_time(arte):
    """How long the figures took, and, when they were reused from an identical battery, which run computed them."""
    run = arte.get("run") or {}
    ru = run.get("reused_from")
    if not ru:
        return f"{run.get('elapsed_s')} seconds"
    when = ""
    try:
        import datetime
        when = " on " + datetime.datetime.fromtimestamp(float(ru["computed"]), datetime.timezone.utc).strftime("%Y-%m-%d at %H:%M UTC")
    except (TypeError, ValueError, KeyError):
        pass
    return (f"figures computed in run {ru.get('run')}{when} ({ru.get('computed_elapsed_s')} seconds) and reused here: the approved battery, "
            f"the code, the numerical libraries and the uploaded series are identical, and the critic recomputed them for this run")


def _evidence_line(arte):
    """One sentence for the opening paragraph: what the published evidence says about the model on this run."""
    vb = ((arte.get("assurance") or {}).get("validation") or {}).get("benchmarks")
    if not vb:
        return ""
    sm = vb["summary"]
    name = {r["id"]: r["title"][:1].lower() + r["title"][1:] for r in vb["rows"]}
    bad = [name[i] for i in sm["contradicted"]] + [name[i] for i in sm["in_tension"]]
    out = (f" Confronted with {sm['scored']} published benchmarks, mostly analogues from other regulation, the model is not contradicted by "
           f"{sm['not_contradicted']}")
    if bad:
        out += " and fails or strains on " + "; ".join(bad)
    out += (f". {len(sm['mechanisms_unconfronted'])} of its {sm['mechanisms']} mechanisms have no benchmark at all, and no mechanism is estimated "
            f"from data.")
    return out
