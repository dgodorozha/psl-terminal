"""Transparency record in the structure of the UK Algorithmic Transparency
Recording Standard (ATRS): a tier 1 overview a member of the public can
read, and a tier 2 record of ownership, description, decision making
process, data, risks and impact assessments. Built from the artefacts and
the approvals at release; shipped in the evidence pack.
"""

import datetime

from . import __version__


def _now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


def atrs_record(arte, approvals, run_id, organisation="", team="", contact=""):
    ev = arte["results"]
    pols = {r["policy"]: r for r in ev["policies"]}
    pref = ev["preferred"]
    P = pols[ev["focus"]]
    nsv = P["net_social_value"]
    if pref is None:
        headline = "No alternative satisfies every constraint. Highest expected value: "
    elif pref == "baseline":
        headline = "No tested instrument improves on the status quo. Best instrument: "
    else:
        headline = "Preferred option "
    pr = ev.get("precision") or {}
    g2 = approvals.get("gate2") or {}
    g1 = approvals.get("gate1") or {}
    reg = g2.get("register") or {}
    if g2.get("open_gate") or g1.get("open_gate"):
        owner = "none recorded: public demonstration, gates taken without sign off identities"
        owner_role = ""
        reg = {}
    else:
        owner = g2.get("actor") or g1.get("actor") or ""
        owner_role = g2.get("role") or g1.get("role") or ""
    rec = {
        "tier1": {
            "name": "Policy Scenario Lab (PSL)",
            "description": ("An agent based policy laboratory that compares candidate AI regulatory instruments on a synthetic AI economy: "
                            "firms choosing capability, safety, compliance and location; a regulator; the public; the press; the market. "
                            "Each instrument is scored on expected harm avoided against its economic and social cost, with the industry's "
                            "net gain or loss, the forecast news environment and the market reaction reported beside it."),
            "website": "", "contact": contact,
            "how_used": ("To inform, not to make, a policy choice: the briefing is drafted from the run's artefacts, checked by an independent "
                         "critic and released by a named human at a second gate. Outputs are scenario evaluations conditional on a "
                         "synthetic model and a declared set of assumptions: expected values with the confidence interval of the estimate, "
                         "the spread of simulated outcomes and the sensitivity to the assumptions kept apart. They are not forecasts of named "
                         "companies or events and are not validated against data, except where an uploaded event study is compared with "
                         "the model's market reaction."),
            "run": run_id, "released": _now(), "version": __version__,
        },
        "tier2": {
            "owner_and_responsibility": {
                "organisation": organisation, "team": team,
                "senior_responsible_owner": owner, "senior_responsible_owner_function": owner_role,
                "senior_responsible_owner_register": ({"source": reg.get("source"), "function": reg.get("function"), "reference": reg.get("irn"),
                                                       "checked_at": reg.get("checked_at")} if reg else None),
                "external_supplier": "none; the tool runs on the authority's own infrastructure",
            },
            "description_and_rationale": {
                "detailed_description": ("Monthly agent based simulation over " + f"{arte['horizon']} months on {arte['paths']} Monte Carlo paths per alternative, "
                                         "on common random numbers; a welfare accounting for residents of harm avoided, consumer surplus, output uplift, "
                                         "resident producer surplus, compliance resource cost, enforcement budget, offshore leakage, relocation cost, labour "
                                         "adjustment and insurance administration, with transfers excluded; a decision rule (the highest expected net social "
                                         "value among the alternatives that satisfy the question's constraints, the status quo included); expected values "
                                         "estimated by conditional Monte Carlo with bootstrap confidence intervals; adaptive sampling to declared precision "
                                         "targets; a screen of every assumption, a joint draw of all of them, a variance decomposition, structural variants, "
                                         "a red team and a replication check."),
                "scope": "Candidate AI regulatory instruments: " + ", ".join(p["label"] for p in arte["policies"].values()),
                "benefit": "A reproducible, assumption explicit comparison of instruments that no single study provides, with its uncertainty shown.",
                "previous_process": "Narrative impact assessments and expert elicitation without a common counterfactual.",
                "alternatives_considered": "Static cost benefit spreadsheets; econometric event studies alone; expert panels.",
            },
            "decision_making_process": {
                "process_integration": "The policy question enters at the RUN page; the battery is approved at Gate 1; the briefing is released at Gate 2.",
                "provided_information": f"{headline}{P['label']}: expected net social value {nsv['mean']:.1f} $bn "
                                        f"(95% confidence interval {nsv['ci_lo']:.1f} to {nsv['ci_hi']:.1f}; simulated outcomes {nsv['lo']:.1f} to {nsv['hi']:.1f} "
                                        f"at the 10th and 90th percentiles); harm avoided {P['components']['harm_avoided']['mean']:.1f} $bn; "
                                        f"industry value change {P['industry_value_change']['mean']:.0f} $bn; within the constraints in {P['p_feasible']:.0%} of "
                                        f"resamples; ranking stability {P['p_best']:.0%}. " + ev["decision"]["text"]
                                        + ("" if pr.get("met", True) else " Short of its precision target: " + "; ".join(x["text"] for x in pr.get("unresolved", [])) + "."),
                "frequency_and_scale": "On demand per question; every run is kept in the registry.",
                "human_decisions_and_review": "Two named human gates with refusal and recorded reasons; an independent critic before Gate 2; the briefing cites every assumption.",
                "required_training": "Familiarity with cost benefit analysis and with the assumptions file.",
                "appeals_and_review": "Any figure can be recomputed from the evidence pack by a second authority; the ledger is replayable.",
            },
            "tool_specification": {
                "system_architecture": "Python; numpy and scipy; a Dash terminal; a hash chained HMAC signed ledger; a register of approvers.",
                "phase": "prototype", "maintenance": "versioned; the code fingerprint of each run is recorded",
                "models": "No learned model in the decision path; an optional language model may phrase text and its output is vetted number by number.",
            },
            "data": {
                "source_data": "Synthetic economy by default; optional uploaded price series for calibration and event studies, through a quarantine that refuses personal data.",
                "data_sharing": "The evidence pack carries only public or synthetic rows.",
                "assumptions_hash": arte["assumptions_hash"], "battery_hash": arte["battery_hash"],
            },
            "risks_mitigations_and_impact_assessments": {
                "impact_assessment": "The screen of every assumption, the joint draw, the variance decomposition, the structural variants, the red team "
                                     "and the replication check in assurance.json; the decision gap between early appearance and long run value.",
                "risks": [
                    "The model is synthetic and no mechanism is estimated from data: the mechanism register lists each with the evidence that would "
                    "test it, and the validation layer reports which published benchmarks the model is in tension with or contradicted by" + _bench_note(arte) + ".",
                    "The harm side rests on declared hazard and tail assumptions; the screen and the joint draw show which change the answer.",
                    "The firms are archetypes; mapping onto real companies requires calibration and is labelled as such.",
                    "A domestic instrument can be escaped by relocation; the leakage term depends on the mobility assumed.",
                    "Ranking stability is conditional on the model; it is not the probability that an option is best in the world.",
                    "A constraint is tested on an estimate; an option near a limit may be included or excluded by sampling error, which the share of "
                    "resamples within the constraints reports.",
                ],
                "mitigations": "Every assumption is declared with bounds and a plausible range; common random numbers; conditional estimators for rare "
                               "events; precision targets; an independent critic; two gates; a replayable ledger; the preferred option is reported "
                               "with the assumptions, structures and gaming strategies that would change it.",
            },
        },
    }
    return rec


def render_markdown(rec):
    t1, t2 = rec["tier1"], rec["tier2"]
    L = [f"# Algorithmic transparency record: {t1['name']}", "", "## Tier 1", "",
         f"**Description.** {t1['description']}", "", f"**How it is used.** {t1['how_used']}", "",
         f"Run {t1['run']}, released {t1['released']}, version {t1['version']}.", "", "## Tier 2", ""]
    for section, body in t2.items():
        L.append(f"### {section.replace('_', ' ').capitalize()}")
        L.append("")
        for k, v in body.items():
            if isinstance(v, list):
                L.append(f"**{k.replace('_', ' ').capitalize()}.**")
                for x in v:
                    L.append(f"- {x}")
            elif isinstance(v, dict):
                L.append(f"**{k.replace('_', ' ').capitalize()}.** " + "; ".join(f"{a}: {b}" for a, b in v.items() if b))
            elif v:
                L.append(f"**{k.replace('_', ' ').capitalize()}.** {v}")
        L.append("")
    return "\n".join(L)


def _bench_note(arte):
    vb = ((arte.get("assurance") or {}).get("validation") or {}).get("benchmarks")
    if not vb:
        return ""
    sm = vb["summary"]
    name = {r["id"]: r["title"] for r in vb["rows"]}
    bad = [name[i] for i in sm["in_tension"] + sm["contradicted"]]
    return (f" (on this run {sm['scored']} benchmarks, {len(sm['mechanisms_confronted'])} of {sm['mechanisms']} mechanisms confronted; "
            + ("failing: " + "; ".join(bad) if bad else "none failing") + ")")
