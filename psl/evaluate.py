"""Scoring the battery on the decision.

The decision a policymaker faces is: which alternative, the status quo
included, gives the highest expected net social value within whatever
constraints the question sets (an industry loss the economy can bear, a
social cost budget, a ceiling on the probability of a major or a
catastrophic incident, a minimum harm reduction, a consumer surplus floor).

The decision rule
  alternatives   every instrument of the battery and the status quo. The status quo scores zero by
                 construction; an instrument is preferred to it only if its expected net social value
                 is higher. If no instrument beats it, the answer is that no tested instrument
                 improves on the status quo, and the best instrument is reported separately.
  feasibility    a constraint is tested on the expected value of its metric. Because that expected
                 value is an estimate, every alternative also carries the probability that it
                 satisfies each constraint (the share of bootstrap resamples in which it does), and
                 the preferred option under a conservative rule (feasible in at least 90% of
                 resamples) is reported beside the preferred option under the expected value rule.
  ties           equal scores share a rank; a tie between the status quo and an instrument goes to
                 the status quo.

Uncertainty, kept apart (stats.py):
  the spread of simulated outcomes (10th to 90th percentile);
  the Monte Carlo confidence interval of every expected value and of every paired difference
  between the preferred option and each other alternative, with a simultaneous interval over all
  of them (the alternatives that cannot be told apart from the preferred one form its confidence set);
  ranking stability, the share of bootstrap resamples of the paths in which an alternative is
  the best feasible one. It is conditional on the model and its assumptions: it is not the
  probability that the alternative is best in the world. Parameter and structural uncertainty are
  the business of assurance.py.

Every instrument also carries its safety forecast, its market impact, its
news environment and a headline score, the way it would look in the first
six months of prices and coverage. Ranking the instruments by the headline
score and by the net social value gives the decision gap.
"""

import numpy as np

from . import welfare as W
from .stats import Boot, interval, kendall_tau_b, rank_desc

MEANS = ("net_social_value",) + W.COMPONENTS + ("industry_value_change", "cat_cmc", "major_any", "headline")
ASSURED_P = 0.9
kendall_tau = kendall_tau_b            # tie aware (tau b); the name earlier releases imported
_rank_desc = rank_desc


def decision_arrays(reds, a):
    """Per alternative, per path quantities the decision is computed from: name -> {quantity: (N,)}."""
    B = reds["baseline"]
    out = {}
    for name, R in reds.items():
        c = W.components(R, B, a)
        arr = {k: c[k] for k in ("net_social_value", "net_social_value_drawn", "harm_avoided_drawn", "industry_value_change",
                                 "industry_value_change_drawn", "earnings_change", "nonresident_payments") + W.COMPONENTS}
        arr["cat_cmc"] = R["cat_cmc"]; arr["cat_any"] = R["cat_any"]; arr["major_any"] = R["major_any"]
        arr["headline"] = W.headline_paths(R, B) if "idx_early" in R else np.zeros(R["n_paths"])
        arr["transfers"] = c["transfers"]; arr["incidence"] = c["incidence"]
        out[name] = arr
    return out


def stack_means(names, arrays, boot=None):
    """Means of every decision quantity: {quantity: (A,)} and, with a bootstrap, {quantity: (A, B)}."""
    point, draws = {}, {}
    for q in MEANS:
        X = np.stack([np.asarray(arrays[n][q], dtype=float) for n in names], axis=0)        # (A, N)
        point[q] = X.mean(axis=1)
        if boot is not None:
            draws[q] = boot.means(X)
    return point, draws


def constraint_values(M, constraints):
    """Each declared constraint as (key, value, limit, sense) with value an array over alternatives (and
    resamples or scenarios); sense 'max' means value <= limit is required, 'min' means value >= limit."""
    out = []
    c = constraints or {}
    if c.get("max_industry_loss_bn") is not None:
        out.append(("max_industry_loss_bn", -np.asarray(M["industry_value_change"]), float(c["max_industry_loss_bn"]), "max"))
    if c.get("max_social_cost_bn") is not None:
        gc, _ = W.gross(M)
        out.append(("max_social_cost_bn", gc, float(c["max_social_cost_bn"]), "max"))
    if c.get("max_cs_loss_pct") is not None and c.get("_cs_base_npv"):
        out.append(("max_cs_loss_pct", -np.asarray(M["cs_change"]) / c["_cs_base_npv"] * 100.0, float(c["max_cs_loss_pct"]), "max"))
    if c.get("max_p_major") is not None:
        out.append(("max_p_major", np.asarray(M["major_any"]), float(c["max_p_major"]), "max"))
    if c.get("max_p_catastrophe") is not None:
        out.append(("max_p_catastrophe", np.asarray(M["cat_cmc"]), float(c["max_p_catastrophe"]), "max"))
    if c.get("min_harm_reduction_pct") is not None and c.get("_harm_base_npv"):
        out.append(("min_harm_reduction_pct", np.asarray(M["harm_avoided"]) / c["_harm_base_npv"] * 100.0,
                    float(c["min_harm_reduction_pct"]), "min"))
    return out


def feasible_mask(M, constraints):
    """Boolean array, same shape as the means: every constraint satisfied."""
    ok = np.ones(np.shape(M["net_social_value"]), dtype=bool)
    for _, val, lim, sense in constraint_values(M, constraints):
        ok &= (val <= lim + 1e-12) if sense == "max" else (val >= lim - 1e-12)
    return ok


def best_index(nsv, ok):
    """Index of the feasible alternative with the highest expected net social value along axis 0 (ties to the
    lowest index, the status quo first); -1 where nothing is feasible."""
    score = np.where(ok, nsv, -np.inf)
    j = np.argmax(score, axis=0)
    none = ~ok.any(axis=0)
    return np.where(none, -1, j)


def decide(names, M, constraints):
    """The decision on a table of means (a point estimate, a scenario, ...): feasibility, the preferred
    alternative, the best instrument. Returns a dict of names and masks."""
    ok = feasible_mask(M, constraints)
    nsv = np.asarray(M["net_social_value"], dtype=float)
    j = int(best_index(nsv, ok))
    inter = [i for i, n in enumerate(names) if n != "baseline"]
    feas_i = [i for i in inter if ok[i]]
    best_int = max(feas_i, key=lambda i: (nsv[i], -i)) if feas_i else None
    best_unc = int(np.argmax(nsv)) if len(nsv) else None
    best_unc_int = max(inter, key=lambda i: (nsv[i], -i)) if inter else None
    return {"feasible": {n: bool(ok[i]) for i, n in enumerate(names)},
            "preferred": names[j] if j >= 0 else None,
            "best_intervention": names[best_int] if best_int is not None else None,
            "best_unconstrained": names[best_unc] if best_unc is not None else None,
            "best_unconstrained_intervention": names[best_unc_int] if best_unc_int is not None else None}


def _ci(point, draws):
    lo, hi = interval(draws)
    return {"mean": float(point), "se": float(np.std(draws, ddof=1)), "ci_lo": lo, "ci_hi": hi}


def evaluate(reds, a, constraints=None, boot=1000, seed=11, labels=None):
    """reds: ordered dict name -> reduced policy (must contain 'baseline', with full=True).
    Returns (the scoring dictionary, JSON serialisable; the per path decision arrays; the Boot object)."""
    constraints = constraints or {}
    names = ["baseline"] + [n for n in reds if n != "baseline"]      # the status quo first: a tie on value goes to it
    Bz = reds["baseline"]
    N = int(Bz["n_paths"])
    bt = Boot(N, boot, seed)
    arr = decision_arrays(reds, a)
    point, draws = stack_means(names, arr, bt)
    A = len(names)
    labels = labels or {n: reds[n].get("label", n) for n in names}

    # ---- the decision on the point estimates, and in every bootstrap resample
    dec = decide(names, point, constraints)
    ok_b = feasible_mask(draws, constraints)                          # (A, B)
    best_b = best_index(draws["net_social_value"], ok_b)              # (B,)
    best_unc_b = np.argmax(draws["net_social_value"], axis=0)
    gc_p, gb_p = W.gross(point)
    gc_b, gb_b = W.gross(draws)
    cvals = constraint_values(point, constraints)
    cvals_b = constraint_values(draws, constraints)
    pref = dec["preferred"]
    pi = names.index(pref) if pref is not None else None

    rows = []
    for i, n in enumerate(names):
        R = reds[n]; c = arr[n]
        nsv = W.summarise(c["net_social_value"], bt, drawn=c["net_social_value_drawn"])
        nsv["p_improves"] = float((draws["net_social_value"][i] > 0).mean())      # P(the expected value is above zero)
        comps = {k: (W.summarise(c[k], bt, drawn=c["harm_avoided_drawn"]) if k == "harm_avoided" else W.summarise(c[k], bt))
                 for k in W.COMPONENTS}
        harm = float(point["harm_avoided"][i])
        checks, notes = [], []
        for (key, val, lim, sense), (_, val_b, _, _) in zip(cvals, cvals_b):
            v = float(val[i]); vb = val_b[i]
            ok_i = (v <= lim + 1e-12) if sense == "max" else (v >= lim - 1e-12)
            p_ok = float(((vb <= lim + 1e-12) if sense == "max" else (vb >= lim - 1e-12)).mean())
            lo, hi = interval(vb)
            checks.append({"constraint": key, "value": v, "limit": lim, "sense": sense, "ok": bool(ok_i), "p_ok": p_ok,
                           "ci_lo": lo, "ci_hi": hi, "margin": float(lim - v if sense == "max" else v - lim)})
            notes.append(_note(key, v, lim, ok_i, p_ok))
        inc = {k: float(np.mean(v)) for k, v in c["incidence"].items()}
        row = {"policy": n, "label": labels.get(n, n),
               "net_social_value": nsv, "components": comps,
               "gross_cost": _ci(gc_p[i], gc_b[i]), "gross_benefit": _ci(gb_p[i], gb_b[i]),
               "net_economic_cost": float(harm - point["net_social_value"][i]),
               "cost_per_harm_avoided": (float(gc_p[i] / harm) if harm > 1e-6 else None),
               "net_cost_per_harm_avoided": (float((harm - point["net_social_value"][i]) / harm) if harm > 1e-6 else None),
               "industry_value_change": W.summarise(c["industry_value_change"], bt, drawn=c["industry_value_change_drawn"]),
               "transfers": {k: float(np.mean(v)) for k, v in c["transfers"].items()},
               "distribution": inc, "incidence_total": float(sum(inc.values())),
               "nonresident_payments": float(np.mean(c["nonresident_payments"])),
               "safety": W.safety_metrics(R, a, bt), "news": W.news_metrics(R, Bz, bt), "market": W.market_metrics(R, Bz, a, bt),
               "headline_score": float(point["headline"][i]),
               "feasible": bool(dec["feasible"][n]), "p_feasible": float(ok_b[i].mean()),
               "constraint_checks": checks, "constraint_notes": notes,
               "p_best": float((best_b == i).mean()), "p_best_unconstrained": float((best_unc_b == i).mean())}
        rows.append(row)

    # ---- paired differences between the preferred alternative and every other one
    conf_set = []
    if pi is not None:
        d_b = draws["net_social_value"][pi][None, :] - draws["net_social_value"]          # (A, B)
        d_p = point["net_social_value"][pi] - point["net_social_value"]
        se = d_b.std(axis=1, ddof=1)
        others = [i for i in range(A) if i != pi]
        with np.errstate(divide="ignore", invalid="ignore"):
            t = np.abs(d_b[others] - d_p[others, None]) / np.where(se[others, None] > 0, se[others, None], np.inf)
        crit = float(np.percentile(t.max(axis=0), 95)) if others else 0.0
        for i, r in enumerate(rows):
            if i == pi:
                r["vs_preferred"] = None
                continue
            lo, hi = interval(d_b[i])
            s_lo, s_hi = float(d_p[i] - crit * se[i]), float(d_p[i] + crit * se[i])
            r["vs_preferred"] = {"difference": float(d_p[i]), "se": float(se[i]), "ci_lo": lo, "ci_hi": hi,
                                 "simultaneous_lo": s_lo, "simultaneous_hi": s_hi,
                                 "distinguishable": bool(lo > 0 or hi < 0),
                                 "in_confidence_set": bool(s_lo <= 0 <= s_hi)}
            if r["feasible"] and r["vs_preferred"]["in_confidence_set"]:
                conf_set.append(r["policy"])

    # ---- rankings over the instruments (tie aware), and the decision gap
    cand = [r for r in rows if r["policy"] != "baseline"]
    ci = [names.index(r["policy"]) for r in cand]
    if cand:
        r_nsv = rank_desc(point["net_social_value"][ci]); r_hs = rank_desc(point["headline"][ci])
        r_harm = rank_desc(point["harm_avoided"][ci]); r_ind = rank_desc(point["industry_value_change"][ci])
        for k, r in enumerate(cand):
            r["rank_social"] = int(r_nsv[k]); r["rank_headline"] = int(r_hs[k])
            r["rank_harm"] = int(r_harm[k]); r["rank_industry"] = int(r_ind[k])
    tau = kendall_tau_b(point["headline"][ci], point["net_social_value"][ci]) if len(cand) > 1 else 1.0
    inversions = 0
    if len(cand) > 1:
        hb, nb = draws["headline"][ci], draws["net_social_value"][ci]
        inversions = sum(1 for b in range(bt.b) if kendall_tau_b(hb[:, b], nb[:, b]) < 0)
    gap = {"kendall_tau": float(tau), "decision_gap": float((1 - tau) / 2), "p_inversion": inversions / bt.b,
           "headline_order": [r["policy"] for r in sorted(cand, key=lambda r: (r["rank_headline"], names.index(r["policy"])))],
           "social_order": [r["policy"] for r in sorted(cand, key=lambda r: (r["rank_social"], names.index(r["policy"])))],
           "note": "headline score: the value weighted price reaction against the status quo over the first six months plus a "
                   "tenth of the early news tone difference; social order: expected net social value over the horizon; "
                   "Kendall tau b, so tied scores do not create or hide a gap"}

    # ---- the decision, in words the panels, the briefing and the oracle share
    by = {r["policy"]: r for r in rows}
    bi = dec["best_intervention"]
    assured = [r for r in rows if r["p_feasible"] >= ASSURED_P]
    pref_assured = max(assured, key=lambda r: (r["net_social_value"]["mean"], -names.index(r["policy"])))["policy"] if assured else None
    decision = {"preferred": pref, "is_status_quo": pref == "baseline", "best_intervention": bi,
                "improves_on_status_quo": bool(bi is not None and by[bi]["net_social_value"]["mean"] > 0),
                "distinguishable_from_status_quo": bool(bi is not None and by[bi]["net_social_value"]["ci_lo"] > 0),
                "preferred_assured": pref_assured, "assured_rule": f"feasible in at least {ASSURED_P:.0%} of resamples",
                "confidence_set": conf_set,
                "feasibility_uncertain": [r["policy"] for r in rows if 0.1 < r["p_feasible"] < 0.9],
                "p_none_feasible": float((best_b < 0).mean())}
    decision["text"] = _decision_text(decision, by)
    ev = {"policies": rows, "names": names, "preferred": pref, "best_intervention": bi,
          "best_unconstrained": dec["best_unconstrained"], "best_unconstrained_intervention": dec["best_unconstrained_intervention"],
          "focus": bi or dec["best_unconstrained_intervention"],
          "decision": decision, "constraints": constraints, "decision_gap": gap,
          "winner_stability": float(by[pref]["p_best"]) if pref else 0.0,
          "n_paths": N, "horizon": int(Bz["horizon"]), "bootstrap": int(bt.b), "bootstrap_seed": int(seed),
          "estimators": {"expected_values": "conditional Monte Carlo: harm expected given the state each path reached",
                         "intervals": "95% percentile bootstrap over paths, paired across alternatives",
                         "outcome_spread": "10th and 90th percentiles of the simulated outcomes as drawn",
                         "ranking_stability": "share of bootstrap resamples in which the alternative is the best feasible one; "
                                              "conditional on the model and its assumptions"}}
    return ev, arr, bt


def _note(key, v, lim, ok, p_ok):
    p = f" (satisfied in {p_ok:.0%} of resamples)"
    if key == "max_industry_loss_bn":
        return (f"industry loss ${max(v, 0):,.0f}bn within the ${lim:,.0f}bn limit" if ok else f"industry loss ${v:,.0f}bn exceeds the ${lim:,.0f}bn limit") + p
    if key == "max_social_cost_bn":
        return (f"gross social cost ${v:,.0f}bn within the ${lim:,.0f}bn budget" if ok else f"gross social cost ${v:,.0f}bn exceeds the ${lim:,.0f}bn budget") + p
    if key == "max_cs_loss_pct":
        return (f"consumer surplus change {-v:+.1f}% within the {lim:.0f}% allowed" if ok else f"consumer surplus falls {v:.1f}%, more than the {lim:.0f}% allowed") + p
    if key == "max_p_major":
        return (f"probability of a major incident {v:.0%} within the {lim:.0%} ceiling" if ok else f"probability of a major incident {v:.0%} above the {lim:.0%} ceiling") + p
    if key == "max_p_catastrophe":
        return (f"probability of a catastrophe {v:.1%} within the {lim:.0%} ceiling" if ok else f"probability of a catastrophe {v:.1%} above the {lim:.0%} ceiling") + p
    if key == "min_harm_reduction_pct":
        return (f"harm reduction {v:.0f}% meets the {lim:.0f}% required" if ok else f"harm reduction {v:.0f}% short of the {lim:.0f}% required") + p
    return f"{key}: {v:.3g} against {lim:.3g}" + p


def _decision_text(d, by):
    pref, bi = d["preferred"], d["best_intervention"]
    if pref is None:
        return "No alternative, the status quo included, satisfies every constraint."
    if pref == "baseline":
        if bi is None:
            return "No tested instrument satisfies the constraints; the status quo is the only feasible alternative."
        v = by[bi]["net_social_value"]
        s = (f"No tested instrument improves on the status quo: the best instrument within the constraints, {by[bi]['label']}, "
             + ("has a negative expected net social value." if v["mean"] < 0 else "is worth no more than the status quo."))
        if v["mean"] < 0 and v["ci_hi"] >= 0:
            s += " The confidence interval of that value includes zero: on these paths the instrument is not distinguishable from the status quo."
        return s
    s = f"{by[pref]['label']} is preferred: the highest expected net social value among the alternatives that satisfy the constraints, and above the status quo."
    if not d["distinguishable_from_status_quo"] and bi == pref:
        s += " The confidence interval of its expected value includes zero: on these paths it is not distinguishable from the status quo."
    others = [n for n in d["confidence_set"] if n != "baseline"]
    if others:
        s += " It cannot be told apart from " + ", ".join(by[n]["label"] for n in others) + " at this number of paths."
    if d["preferred_assured"] != pref:
        s += (" Under the conservative rule the preferred option is "
              + (by[d["preferred_assured"]]["label"] if d["preferred_assured"] in by else "none") + ".")
    return s


def precision(ev, targets):
    """Which estimates have not reached the declared precision: a list of findings (empty when all targets are met).

    targets: {'nsv_gap_bn': d, 'p_catastrophe_halfwidth': h}. The ranking between the preferred alternative and
    another feasible one is resolved when the 95% interval of their paired difference excludes zero, or when its
    half width is at most d (the two are then equivalent to within d). A catastrophe probability is resolved when
    the half width of its interval is at most h. A feasibility that the resamples split on is reported when it
    bears on the decision."""
    out = []
    by = {r["policy"]: r for r in ev["policies"]}
    pref = ev["preferred"]
    d = float(targets.get("nsv_gap_bn", 5.0)); h = float(targets.get("p_catastrophe_halfwidth", 0.03))
    if pref:
        for r in ev["policies"]:
            v = r.get("vs_preferred")
            if not v or not r["feasible"]:
                continue
            half = 0.5 * (v["ci_hi"] - v["ci_lo"])
            if not v["distinguishable"] and half > d:
                out.append({"kind": "ranking", "policy": r["policy"], "halfwidth": float(half), "target": d,
                            "text": f"{by[pref]['label']} against {r['label']}: difference ${v['difference']:,.1f}bn, "
                                    f"95% interval ${v['ci_lo']:,.1f}bn to ${v['ci_hi']:,.1f}bn"})
    for n in {pref, "baseline"} - {None}:
        pc = by[n]["safety"]["p_catastrophe_detail"]
        half = 0.5 * (pc["ci_hi"] - pc["ci_lo"])
        if half > h:
            out.append({"kind": "catastrophe", "policy": n, "halfwidth": float(half), "target": h,
                        "text": f"probability of a catastrophe under {by[n]['label']}: {pc['p']:.1%}, 95% interval {pc['ci_lo']:.1%} to {pc['ci_hi']:.1%}"})
    pref_nsv = by[pref]["net_social_value"]["mean"] if pref else -np.inf
    for r in ev["policies"]:
        if 0.1 < r["p_feasible"] < 0.9 and (r["policy"] == pref or r["net_social_value"]["mean"] > pref_nsv):
            out.append({"kind": "feasibility", "policy": r["policy"], "p_feasible": r["p_feasible"],
                        "text": f"{r['label']}: within the constraints in {r['p_feasible']:.0%} of resamples"})
    return out
