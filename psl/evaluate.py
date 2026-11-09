"""Scoring the battery on the decision.

The decision a policymaker faces is: which instrument buys the most
expected harm reduction for its economic and social cost, within whatever
constraints the question sets (an industry loss the economy can bear, a
social cost budget, a ceiling on the probability of a major incident). The
score is the expected net social value; every policy also carries its
safety forecast, its market impact, its news environment and a headline
score, the way it would look in the first six months of coverage and
prices. Ranking the battery by the headline score and by the net social
value gives the decision gap: how far the policy that looks best early is
from the one that is best.

Uncertainty: percentile intervals over the Monte Carlo paths, and a
bootstrap over paths for the probability that each policy is the best
(winner stability) and for the probability that the two rankings invert.
"""

import numpy as np

from . import welfare as W


def kendall_tau(a, b):
    a = np.asarray(a); b = np.asarray(b)
    n = len(a)
    if n < 2:
        return 0.0
    s = 0
    for i in range(n):
        for j in range(i + 1, n):
            s += np.sign(a[i] - a[j]) * np.sign(b[i] - b[j])
    return float(s / (n * (n - 1) / 2))


def _rank_desc(values):
    """1 = highest."""
    order = np.argsort(-np.asarray(values))
    r = np.empty(len(values), dtype=int)
    r[order] = np.arange(1, len(values) + 1)
    return r


def evaluate(results, a, constraints=None, boot=300, seed=11):
    """results: ordered dict name -> PolicyResult (must contain 'baseline').
    Returns the full scoring dictionary (JSON serialisable) and the per path components."""
    constraints = constraints or {}
    base = results["baseline"]
    aggs = {name: W.aggregates(res, a) for name, res in results.items()}
    comps, rows = {}, []
    for name, res in results.items():
        c = W.components(aggs[name], aggs["baseline"], a)
        saf = W.safety_metrics(res, a)
        news = W.news_metrics(res, base)
        mkt, value_change = W.market_metrics(res, base, a)
        c["industry_shareholder_value"] = value_change
        comps[name] = c
        headline = float(mkt["early_reaction"]["mean"] + 0.1 * news.get("early_tone_vs_baseline", 0.0))
        row = {"policy": name, "label": res.policy["label"],
               "net_social_value": W.summarise(c["net_social_value"]),
               "components": {k: W.summarise(c[k]) for k in W.COMPONENTS},
               "gross_cost": W.summarise(c["gross_cost"]),
               "cost_per_harm_avoided": (float(c["gross_cost"].mean() / c["harm_avoided"].mean()) if c["harm_avoided"].mean() > 1e-6 else None),
               "industry_value_change": W.summarise(value_change),
               "transfers": {k: float(v.mean()) for k, v in c["transfers"].items()},
               "distribution": W.distribution(c, value_change),
               "safety": saf, "news": news, "market": mkt, "headline_score": headline}
        rows.append(row)
    names = [r["policy"] for r in rows]
    cand = [r for r in rows if r["policy"] != "baseline"]
    # rankings over the candidates
    nsv = np.array([r["net_social_value"]["mean"] for r in cand])
    hs = np.array([r["headline_score"] for r in cand])
    harm = np.array([r["components"]["harm_avoided"]["mean"] for r in cand])
    ind = np.array([r["industry_value_change"]["mean"] for r in cand])
    r_nsv, r_hs, r_harm, r_ind = _rank_desc(nsv), _rank_desc(hs), _rank_desc(harm), _rank_desc(ind)
    for i, r in enumerate(cand):
        r["rank_social"] = int(r_nsv[i]); r["rank_headline"] = int(r_hs[i])
        r["rank_harm"] = int(r_harm[i]); r["rank_industry"] = int(r_ind[i])
    tau = kendall_tau(r_hs, r_nsv) if len(cand) > 1 else 1.0
    # constraints and the preferred option
    feas = []
    for r in cand:
        ok, why = feasible(r, constraints)
        r["feasible"] = ok; r["constraint_notes"] = why
        feas.append(ok)
    pref = None
    if any(feas):
        pref = max((r for r in cand if r["feasible"]), key=lambda r: r["net_social_value"]["mean"])["policy"]
    best_unconstrained = cand[int(np.argmax(nsv))]["policy"] if cand else None
    # bootstrap: winner stability and inversion probability
    rng = np.random.default_rng(seed)
    N = base.n_paths
    wins = {r["policy"]: 0 for r in cand}
    wins_feas = {r["policy"]: 0 for r in cand}
    inversions = 0
    cnsv = {r["policy"]: comps[r["policy"]]["net_social_value"] for r in cand}
    chead = {r["policy"]: _headline_paths(results[r["policy"]], base) for r in cand}
    for _ in range(boot):
        ix = rng.integers(0, N, N)
        m = np.array([cnsv[r["policy"]][ix].mean() for r in cand])
        h = np.array([chead[r["policy"]][ix].mean() for r in cand])
        wins[cand[int(np.argmax(m))]["policy"]] += 1
        fe = [i for i, r in enumerate(cand) if r["feasible"]]
        if fe:
            j = fe[int(np.argmax(m[fe]))]
            wins_feas[cand[j]["policy"]] += 1
        if len(cand) > 1 and kendall_tau(_rank_desc(h), _rank_desc(m)) < 0:
            inversions += 1
    for r in cand:
        r["p_best"] = wins[r["policy"]] / boot
        r["p_best_feasible"] = wins_feas[r["policy"]] / boot
    gap = {"kendall_tau": tau, "decision_gap": float((1 - tau) / 2), "p_inversion": inversions / boot,
           "headline_order": [r["policy"] for r in sorted(cand, key=lambda r: r["rank_headline"])],
           "social_order": [r["policy"] for r in sorted(cand, key=lambda r: r["rank_social"])],
           "note": "headline score: the value weighted price reaction against the baseline over the first six months plus a "
                   "tenth of the early news tone difference; social order: expected net social value over the horizon"}
    winner_stability = max((r["p_best"] for r in cand), default=0.0)
    return {"policies": rows, "names": names, "preferred": pref, "best_unconstrained": best_unconstrained,
            "constraints": constraints, "decision_gap": gap, "winner_stability": winner_stability,
            "n_paths": N, "horizon": base.horizon, "bootstrap": boot}, comps, aggs


def _headline_paths(res, base):
    w = res.cap0 / res.cap0.sum()
    idx_p = (res.prices[:, 1:7, :] * w[None, None, :]).sum(axis=2)
    idx_b = (base.prices[:, 1:7, :] * w[None, None, :]).sum(axis=2)
    tone = res.series["tone"][:, :6].mean(axis=1) - base.series["tone"][:, :6].mean(axis=1)
    return (idx_p / idx_b - 1.0).mean(axis=1) + 0.1 * tone


def feasible(row, constraints):
    """Constraint test on expected values. Returns (ok, notes)."""
    notes = []
    ok = True
    mil = constraints.get("max_industry_loss_bn")
    if mil is not None:
        loss = -row["industry_value_change"]["mean"]
        if loss > mil:
            ok = False; notes.append(f"industry loss ${loss:,.0f}bn exceeds the ${mil:,.0f}bn limit")
        else:
            notes.append(f"industry loss ${max(loss, 0):,.0f}bn within the ${mil:,.0f}bn limit")
    msc = constraints.get("max_social_cost_bn")
    if msc is not None:
        gc = row["gross_cost"]["mean"]
        if gc > msc:
            ok = False; notes.append(f"gross social cost ${gc:,.0f}bn exceeds the ${msc:,.0f}bn budget")
        else:
            notes.append(f"gross social cost ${gc:,.0f}bn within the ${msc:,.0f}bn budget")
    mcs = constraints.get("max_cs_loss_pct")
    if mcs is not None:
        cs = row["components"]["cs_change"]["mean"]
        base_cs = constraints.get("_cs_base_npv", None)
        if base_cs:
            pct = -cs / base_cs * 100
            if pct > mcs:
                ok = False; notes.append(f"consumer surplus falls {pct:.1f}%, more than the {mcs:.0f}% allowed")
            else:
                notes.append(f"consumer surplus change {-pct:+.1f}% within the {mcs:.0f}% allowed")
    pmaj = constraints.get("max_p_major")
    if pmaj is not None:
        p = row["safety"]["p_major"]
        if p > pmaj:
            ok = False; notes.append(f"probability of a major incident {p:.0%} above the {pmaj:.0%} ceiling")
        else:
            notes.append(f"probability of a major incident {p:.0%} within the {pmaj:.0%} ceiling")
    pcat = constraints.get("max_p_catastrophe")
    if pcat is not None:
        p = row["safety"]["p_catastrophe"]
        if p > pcat:
            ok = False; notes.append(f"probability of a catastrophe {p:.0%} above the {pcat:.0%} ceiling")
        else:
            notes.append(f"probability of a catastrophe {p:.0%} within the {pcat:.0%} ceiling")
    mhr = constraints.get("min_harm_reduction_pct")
    if mhr is not None:
        hb = constraints.get("_harm_base_npv", None)
        if hb:
            pct = row["components"]["harm_avoided"]["mean"] / hb * 100
            if pct < mhr:
                ok = False; notes.append(f"harm reduction {pct:.0f}% short of the {mhr:.0f}% required")
            else:
                notes.append(f"harm reduction {pct:.0f}% meets the {mhr:.0f}% required")
    return ok, notes
