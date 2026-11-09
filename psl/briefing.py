"""The policy briefing: a regulatory impact assessment drafted only from
artefacts.json, in the order a decision maker reads one.

  1  the question and how it was read
  2  the answer: the preferred option, its value, its probability of being best
  3  the options compared (one table)
  4  what the preferred option buys and costs (the social ledger)
  5  who gains and who pays
  6  the safety forecast
  7  the news environment to expect
  8  the market: the industry's net gain or loss, by firm and sector
  9  the decision gap: what looks best early against what is best
 10  how sure we are: intervals, tornado, structural variants, red team, analogue
 11  the assumptions, every one
 12  monitoring: what to watch and when to revisit
 13  gates, provenance and reproduction

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
               "labour_change": "Labour adjustment"}


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
    if money:
        return f"{_bn(s['mean'], nd)} [{_bn(s['lo'], nd)}, {_bn(s['hi'], nd)}]"
    return f"{_f(s['mean'], nd)} [{_f(s['lo'], nd)}, {_f(s['hi'], nd)}]"


def _label(arte, name):
    p = (arte.get("policies") or {}).get(name)
    return p["label"] if p else _nice(name)


def _row(r):
    return r


def draft_briefing(arte, approvals=None, run_id="", critic=None):
    approvals = approvals or {}
    ev = arte["results"]
    pols = {r["policy"]: r for r in ev["policies"]}
    cand = [r for r in ev["policies"] if r["policy"] != "baseline"]
    pref = ev["preferred"] or ev["best_unconstrained"]
    P = pols[pref]
    years = arte["horizon"] / 12
    L = []
    w = L.append
    w(f"# Policy Scenario Lab briefing")
    w("")
    w(f"**Run** {run_id or arte.get('battery_hash', '')[:12]}. **Question.** {arte['question']}")
    w("")
    reading = ", ".join(arte.get("reading", []))
    cons = arte.get("constraints") or {}
    cons_txt = "; ".join(_constraint_text(k, v) for k, v in cons.items() if not k.startswith("_")) or "none"
    w(f"**How it was read.** {len(cand)} instruments against the status quo ({reading}); horizon {years:.0f} years; "
      f"{arte['paths']} Monte Carlo paths per instrument on common random numbers, seed {arte['seed']}; constraints: {cons_txt}.")
    w("")
    # ---- 2 the answer
    w("## The answer")
    w("")
    nsv = P["net_social_value"]
    if ev["preferred"]:
        w(f"**Preferred option: {P['label']}.** Expected net social value {_ci(nsv)} over {years:.0f} years, "
          f"the highest of the instruments that satisfy the constraints; it is the best option in {_pct(P['p_best_feasible'])} of "
          f"bootstrap resamples of the paths ({_pct(P['p_best'])} with the constraints lifted). "
          f"It avoids {_bn(P['components']['harm_avoided']['mean'])} of expected harm "
          f"({_pct(P['components']['harm_avoided']['mean'] / max(arte['baseline_reference']['harm_npv'], 1e-9))} of the baseline's), "
          f"and the industry's net value change is {_ci(P['industry_value_change'], 0)}.")
    else:
        w(f"**No instrument satisfies every constraint.** The best unconstrained option is {P['label']} with expected net social value "
          f"{_ci(nsv)}; the constraints it fails are listed in the options table.")
    bu = ev["best_unconstrained"]
    if ev["preferred"] and bu != ev["preferred"]:
        w(f"With the constraints lifted, {pols[bu]['label']} scores higher ({_bn(pols[bu]['net_social_value']['mean'])}) but fails: "
          + "; ".join(n for n in pols[bu]["constraint_notes"] if "exceeds" in n or "above" in n or "short" in n or "more than" in n) + ".")
    w("")
    if nsv["lo"] < 0 < nsv["hi"]:
        w(f"The interval on the preferred option's value spans zero: the sign depends on the path. "
          f"The probability that it is positive is {_pct(nsv['p_positive'])}.")
    else:
        w(f"The 10th to 90th percentile interval on its value does not cross zero.")
    w("")
    # ---- 3 options
    w("## The options compared")
    w("")
    w("| Instrument | Net social value, $bn | Harm avoided, $bn | Gross social cost, $bn | Industry value change, $bn | P(catastrophe) | Headline score | P(best) | Within constraints |")
    w("|---|---|---|---|---|---|---|---|---|")
    for r in sorted(cand, key=lambda r: -r["net_social_value"]["mean"]):
        w(f"| {r['label']}{' (preferred)' if r['policy'] == pref else ''} | {_f(r['net_social_value']['mean'])} [{_f(r['net_social_value']['lo'])}, {_f(r['net_social_value']['hi'])}] "
          f"| {_f(r['components']['harm_avoided']['mean'])} | {_f(r['gross_cost']['mean'])} | {_f(r['industry_value_change']['mean'], 0)} "
          f"| {_pct(r['safety']['p_catastrophe'])} | {r['headline_score']:+.3f} | {_pct(r['p_best'])} | {'yes' if r['feasible'] else 'no'} |")
    b = pols["baseline"]
    w("")
    w(f"The status quo carries an expected harm of {_bn(arte['baseline_reference']['harm_npv'])} over the horizon, "
      f"{_f(b['safety']['incidents_per_year']['mean'])} reportable incidents a year, a {_pct(b['safety']['p_major'])} probability of at least one major "
      f"incident and a {_pct(b['safety']['p_catastrophe'])} probability of a catastrophic one.")
    w("")
    # ---- 4 the ledger of the preferred option
    w(f"## What {P['label']} buys and costs")
    w("")
    w("| Component | $bn, present value | 10th to 90th percentile |")
    w("|---|---|---|")
    for k in W.BENEFITS:
        c = P["components"][k]
        w(f"| {COMP_LABELS[k]} | {_f(c['mean'])} | [{_f(c['lo'])}, {_f(c['hi'])}] |")
    for k in W.COSTS:
        c = P["components"][k]
        w(f"| {COMP_LABELS[k]}{'' if 'cost' in COMP_LABELS[k].lower() else ' (cost)'} | {_f(-c['mean'])} | [{_f(-c['hi'])}, {_f(-c['lo'])}] |")
    w(f"| **Net social value** | **{_f(nsv['mean'])}** | [{_f(nsv['lo'])}, {_f(nsv['hi'])}] |")
    w("")
    for key, what in (("harm_avoided", "harm avoided"),):
        c = P["components"][key]
        if c["mean"] > c["hi"] and c.get("tail_share", 0) >= 0.3:
            w(f"The mean {what} ({_bn(c['mean'])}) sits above its 90th percentile ({_bn(c['hi'])}): {_pct(c['tail_share'])} of it comes from the tenth "
              f"of paths with the largest values, the paths in which a catastrophic incident is averted; the median is {_bn(c.get('median'))}. "
              f"The expected value is carried by the tail, which is the nature of the problem and not an error.")
            w("")
    if nsv["mean"] > nsv["hi"] and nsv.get("tail_share", 0) >= 0.3:
        w(f"The same holds for the net social value: mean {_bn(nsv['mean'])} against a 90th percentile of {_bn(nsv['hi'])} and a median of {_bn(nsv.get('median'))}.")
        w("")
    cpe = P.get("cost_per_harm_avoided")
    w(f"Gross social cost {_ci(P['gross_cost'])}" + (f", that is {_f(cpe, 2)} of cost per dollar of harm avoided." if cpe else "."))
    tr = P["transfers"]
    w(f"Transfers, excluded from the net: fines {_bn(tr['fines'])}, liability payouts {_bn(tr['liability'])}, insurance premiums {_bn(tr['premiums'])}.")
    w("")
    # ---- 5 distribution
    w("## Who gains and who pays")
    w("")
    w("| Party | Change, $bn present value |")
    w("|---|---|")
    for k, v in P["distribution"].items():
        w(f"| {k} | {_f(v)} |")
    w("")
    w("Shareholder value counts the earnings change over the horizon plus the discounted change in market value at its end; "
      "it is a valuation effect and only its resident operating profit share enters the social ledger.")
    w("")
    # ---- 6 safety
    w("## Safety forecast")
    w("")
    w("| Instrument | Incidents a year | Major a year | P(major) | P(catastrophe) | Expected harm, $bn | Safety level at end | Frontier capability at end | Trust at end |")
    w("|---|---|---|---|---|---|---|---|---|")
    for r in ev["policies"]:
        s = r["safety"]
        w(f"| {r['label']} | {_f(s['incidents_per_year']['mean'])} | {_f(s['major_per_year']['mean'], 2)} | {_pct(s['p_major'])} | {_pct(s['p_catastrophe'])} "
          f"| {_f(s['expected_harm_npv']['mean'])} | {_f(s['safety_level_end'], 2)} | {_f(s['frontier_capability_end'], 2)} | {_f(s['trust_end'], 2)} |")
    s = P["safety"]
    w("")
    w(f"Under {P['label']} the economy runs {_f(s['incidents_per_year']['mean'])} reportable incidents a year "
      f"(misuse {_f(s['incidents_by_category_per_year']['misuse'])}, accidents {_f(s['incidents_by_category_per_year']['accident'])}, "
      f"systemic {_f(s['incidents_by_category_per_year']['systemic'])}), against {_f(b['safety']['incidents_per_year']['mean'])} at the status quo; "
      f"the expected catastrophic harm is {_bn(s['expected_catastrophe_harm_npv'])} against {_bn(b['safety']['expected_catastrophe_harm_npv'])}. "
      f"Firms end with {_pct(s['safety_share_end'])} of R&D on safety, {_pct(s['offshore_share_end'])} of activity offshore and "
      f"{_pct(s['compliance_share'])} compliance.")
    w("")
    # ---- 7 news
    w("## The news environment to expect")
    w("")
    nb = b["news"]; nP = P["news"]
    w("| Instrument | Minor incident headlines a year | Major incident headlines a year | Enforcement headlines a year | Relocation headlines a year | Peak pressure | P(hearing) | Early tone |")
    w("|---|---|---|---|---|---|---|---|")
    for r in ev["policies"]:
        n = r["news"]; h = n["headlines_per_year"]
        w(f"| {r['label']} | {_f(h['minor incidents']['mean'])} | {_f(h['major incidents']['mean'], 2)} | {_f(h['enforcement actions']['mean'], 2)} "
          f"| {_f(h['relocations']['mean'], 2)} | {_f(n['peak_pressure']['mean'], 2)} | {_pct(n['p_hearing'])} | {n['early_tone']:+.2f} |")
    w("")
    ws = arte["news"][pref]
    worst = ws.get("worst", [])
    w(f"On the representative path the wire under {P['label']} ran {ws.get('headlines', 0)} headlines over the horizon, "
      f"{_pct(ws.get('share_negative', 0))} of them negative. The three worst: " +
      "; ".join(f"\"{x['headline']}\" ({x['outlet']}, {x['date']})" for x in worst) + ".")
    w("")
    # ---- 8 market
    w("## The market")
    w("")
    m = P["market"]
    w(f"Industry net value change under {P['label']}: {_ci(P['industry_value_change'], 0)} on a starting value of {_bn(m['industry_cap0'], 0)}; "
      f"the probability the industry gains is {_pct(P['industry_value_change']['p_positive'])}. "
      f"The value weighted index reacts {m['early_reaction']['mean'] * 100:+.1f}% against the baseline over the first six months and "
      f"{m['end_reaction']['mean'] * 100:+.1f}% by the end of the horizon.")
    w("")
    w("| Firm | Sector | Value change, $bn | 10th to 90th | P(gain) | Earnings change, $bn | Offshore at end | Safety share at end |")
    w("|---|---|---|---|---|---|---|---|")
    for fr in m["firms"]:
        v = fr["value_change"]
        w(f"| {fr['firm']} | {_nice(fr['sector'])} | {_f(v['mean'])} | [{_f(v['lo'])}, {_f(v['hi'])}] | {_pct(v['p_positive'])} "
          f"| {_f(fr['earnings_change_npv'])} | {_pct(fr['offshore_end'])} | {_pct(fr['safety_share_end'])} |")
    w("")
    w("| Sector | Value change, $bn | Starting value, $bn |")
    w("|---|---|---|")
    for sr in m["sectors"]:
        w(f"| {_nice(sr['sector'])} | {_f(sr['value_change']['mean'])} | {_f(sr['cap0'], 0)} |")
    w("")
    w("The firms are synthetic archetypes of the AI value chain, not companies; the figures are the model's and carry its assumptions.")
    w("")
    # ---- 9 the gap
    g = ev["decision_gap"]
    w("## The decision gap")
    w("")
    w(f"Ranked by how they look in the first six months (the price reaction and the early tone of the wire), the order is "
      f"{', '.join(pols[n]['label'] for n in g['headline_order'])}. Ranked by net social value over {years:.0f} years it is "
      f"{', '.join(pols[n]['label'] for n in g['social_order'])}. Kendall tau between the two is {g['kendall_tau']:+.2f}; the decision gap "
      f"({'(1 - tau) / 2'}) is {_f(g['decision_gap'], 2)}, and the two orders invert in {_pct(g['p_inversion'])} of resamples. "
      f"The best option is stable in {_pct(ev['winner_stability'])} of resamples.")
    w("")
    # ---- 10 assurance
    w("## How sure we are")
    w("")
    asr = arte.get("assurance") or {}
    torn = asr.get("tornado")
    if torn:
        w(f"**Tornado.** The preferred option's expected value is {_bn(torn['reference_nsv'])}. Moving each value judgement to its low and high value, "
          f"one at a time (the best option is judged among the instruments that satisfy the question's constraints):")
        w("")
        w("| Assumption | Default | Low value | Value at low, $bn | High value | Value at high, $bn | Best option changes |")
        w("|---|---|---|---|---|---|---|")
        for r in torn["rows"]:
            w(f"| {_nice(r['assumption'])} | {_f(r['default'], 4 if r['default'] < 0.1 else 2)} | {_f(r['low']['value'], 4 if r['low']['value'] < 0.1 else 2)} | {_f(r['low']['nsv'])} "
              f"| {_f(r['high']['value'], 4 if r['high']['value'] < 0.1 else 2)} | {_f(r['high']['nsv'])} | {'yes: ' + ', '.join(sorted(set(_label(arte, x) for x in (r['low']['best'], r['high']['best']) if x != torn['preferred']))) if r['best_changes'] else 'no'} |")
        w("")
        if torn["flips"]:
            w(f"The decision changes when {', '.join(_nice(k) for k in torn['flips'])} {'move' if len(torn['flips']) > 1 else 'moves'} to the edge of "
              f"{'their ranges' if len(torn['flips']) > 1 else 'its range'}; the sign of the preferred option's value is "
              f"{'robust' if torn['sign_robust'] else 'not robust'} across the tornado.")
        else:
            w("No single assumption at the edge of its range changes the decision.")
        w("")
    st = asr.get("structural")
    if st:
        w(f"**Structural variants.** Under {st['n']} alternative model structures the preferred option is best in {st['wins']} and in the top two in {st['top_two']}:")
        w("")
        w("| Variant | What changes | Best option | Preferred option's rank | Its value, $bn |")
        w("|---|---|---|---|---|")
        for v in st["variants"]:
            w(f"| {_nice(v['variant'])} | {v['note']} | {pols[v['best']]['label'] if v['best'] in pols else v['best']} | {v['preferred_rank']} | {_f(v['preferred_nsv'])} |")
        w("")
    rt = asr.get("red_team")
    if rt:
        w("**Red team.** Firms game each instrument four ways; the instrument's value under its worst strategy:")
        w("")
        w("| Instrument | Honest value, $bn | Worst strategy | Value when gamed, $bn | Harm avoided when gamed, $bn | Loss to gaming, $bn |")
        w("|---|---|---|---|---|---|")
        for r in rt["rows"]:
            ws_ = r["strategies"][r["worst_strategy"]]
            w(f"| {r['label']} | {_f(r['honest']['nsv'])} | {_nice(r['worst_strategy'])} | {_f(r['worst_nsv'])} | {_f(ws_['harm_avoided'])} | {_f(r['gaming_loss'])} |")
        w("")
        w(f"The most robust instrument to gaming is {pols[rt['most_robust']]['label'] if rt['most_robust'] in pols else rt['most_robust']}. Strategies: " +
          "; ".join(f"{_nice(k)}: {v}" for k, v in rt["strategies"].items()) + ".")
        w("")
    an = asr.get("analogue") or []
    if an:
        for x in an:
            es = x["event_study"]
            w(f"**Analogue.** Event study on {x['dataset']} ({x['classification']}): cumulative abnormal return {es['car'] * 100:+.1f}% over months "
              f"{es['window_months'][0]} to {es['window_months'][1]} after the event; the model's closest early reaction is {pols[x['closest_policy']]['label']} "
              f"at {pols[x['closest_policy']]['market']['early_reaction']['mean'] * 100:+.1f}%.")
            w("")
    else:
        w("**Analogue.** No event study was uploaded; the market module's early reaction has not been compared with a past regulatory event on this run.")
        w("")
    # ---- 11 assumptions
    w("## Assumptions")
    w("")
    w(f"Every value judgement and structural parameter, hash `{arte['assumptions_hash']}`:")
    w("")
    w("| Assumption | Value | Unit | Meaning |")
    w("|---|---|---|---|")
    for r in arte["assumption_table"]:
        w(f"| {_nice(r['assumption'])} | {_f(r['value'], 4 if abs(r['value']) < 0.1 else 2)} | {r['unit']} | {r['meaning']} |")
    w("")
    # ---- 12 monitoring
    w("## Monitoring and revisiting")
    w("")
    w(f"Indicators to watch, with the model's expectation under {P['label']}: reportable incidents a year "
      f"({_f(s['incidents_per_year']['lo'])} to {_f(s['incidents_per_year']['hi'])}); the share of activity offshore "
      f"({_pct(s['offshore_share_end'])} at the horizon); the news pressure index (peak {_f(nP['peak_pressure']['mean'], 2)}, a hearing in {_pct(nP['p_hearing'])} of paths); "
      f"the industry's value against the baseline ({m['end_reaction']['mean'] * 100:+.1f}% at the horizon). "
      f"Revisit the decision if incidents run above the interval for two quarters, if relocation exceeds the forecast, or if any of "
      f"{', '.join(_nice(k) for k in (torn or {}).get('flips', [])) or 'the tail assumptions'} can be estimated from data.")
    w("")
    # ---- 13 gates and provenance
    w("## Gates, provenance and reproduction")
    w("")
    for key in ("gate1", "gate2"):
        g1 = approvals.get(key)
        if g1:
            reg = g1.get("register") or {}
            w(f"**{'Gate 1 (battery)' if key == 'gate1' else 'Gate 2 (release)'}**: {g1.get('decision')} by {g1.get('actor')}"
              + (f", {g1.get('role')}" if g1.get("role") else "") + (f" ({reg.get('source')})" if reg.get("dev_mode") else
                 (f"; on the register as {reg.get('function')} at {reg.get('firm')}, reference {reg.get('irn')}" if reg.get("irn") else ""))
              + f" at {str(g1.get('ts', ''))[:19]}" + (f"; reason: {g1.get('reason')}" if g1.get("reason") else "") + ".")
    if critic:
        w(f"**Critic**: {critic['n_checks'] - critic['n_failed']} of {critic['n_checks']} checks passed before release.")
    pv = arte["provenance"]
    w(f"Battery hash `{arte['battery_hash']}`; code fingerprint `{pv['code_fingerprint']}`; PSL {pv['psl_version']}, numpy {pv['numpy']}; "
      f"profile {arte.get('profile')}; {arte['run']['elapsed_s']} seconds. Reproduce with `python -m psl.orchestrator --battery battery.json`.")
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
