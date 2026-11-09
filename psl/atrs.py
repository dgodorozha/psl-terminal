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
    pref = ev["preferred"] or ev["best_unconstrained"]
    P = pols[pref]
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
                         "critic and released by a named human at a second gate. Outputs are expected values with intervals on a declared "
                         "set of assumptions; they are not forecasts of named companies or events."),
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
                "detailed_description": ("Monthly agent based simulation over " + f"{arte['horizon']} months on {arte['paths']} Monte Carlo paths per instrument, "
                                         "on common random numbers; a welfare accounting of harm avoided, consumer surplus, output uplift, resident producer "
                                         "surplus, compliance resource cost, enforcement budget, offshore leakage, relocation cost and labour adjustment; "
                                         "a decision metric (expected net social value under the question's constraints) with a bootstrap for the "
                                         "probability that each instrument is best."),
                "scope": "Candidate AI regulatory instruments: " + ", ".join(p["label"] for p in arte["policies"].values()),
                "benefit": "A reproducible, assumption explicit comparison of instruments that no single study provides, with its uncertainty shown.",
                "previous_process": "Narrative impact assessments and expert elicitation without a common counterfactual.",
                "alternatives_considered": "Static cost benefit spreadsheets; econometric event studies alone; expert panels.",
            },
            "decision_making_process": {
                "process_integration": "The policy question enters at the RUN page; the battery is approved at Gate 1; the briefing is released at Gate 2.",
                "provided_information": f"Preferred option {P['label']}: expected net social value {P['net_social_value']['mean']:.1f} $bn "
                                        f"[{P['net_social_value']['lo']:.1f}, {P['net_social_value']['hi']:.1f}]; harm avoided {P['components']['harm_avoided']['mean']:.1f} $bn; "
                                        f"industry value change {P['industry_value_change']['mean']:.0f} $bn; P(best) {P['p_best']:.0%}.",
                "frequency_and_scale": "On demand per question; every run is kept in the registry.",
                "human_decisions_and_review": "Two named human gates with refusal and recorded reasons; an independent critic before Gate 2; the briefing cites every assumption.",
                "required_training": "Familiarity with cost benefit analysis and with the assumptions file.",
                "appeals_and_review": "Any figure can be recomputed from the evidence pack by a second authority; the ledger is replayable.",
            },
            "tool_specification": {
                "system_architecture": "Python; numpy; a Dash terminal; a hash chained HMAC signed ledger; a register of approvers.",
                "phase": "prototype", "maintenance": "versioned; the code fingerprint of each run is recorded",
                "models": "No learned model in the decision path; an optional language model may phrase text and its output is vetted number by number.",
            },
            "data": {
                "source_data": "Synthetic economy by default; optional uploaded price series for calibration and event studies, through a quarantine that refuses personal data.",
                "data_sharing": "The evidence pack carries only public or synthetic rows.",
                "assumptions_hash": arte["assumptions_hash"], "battery_hash": arte["battery_hash"],
            },
            "risks_mitigations_and_impact_assessments": {
                "impact_assessment": "The tornado, structural variants and red team in assurance.json; the decision gap between early appearance and long run value.",
                "risks": [
                    "The harm side rests on declared hazard and tail assumptions; the tornado shows which change the answer.",
                    "The firms are archetypes; mapping onto real companies requires calibration and is labelled as such.",
                    "A domestic instrument can be escaped by relocation; the leakage term depends on the mobility assumed.",
                    "Expected values hide path dependence; the intervals and P(best) must be read with the means.",
                ],
                "mitigations": "Every assumption is declared and bounded; common random numbers; an independent critic; two gates; a replayable ledger; "
                               "the preferred option is reported with the assumptions that would change it.",
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
