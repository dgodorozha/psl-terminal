"""Assurance: attacking the answer before anyone acts on it.

  tornado      every value judgement in assumptions.TORNADO moved to its low and
               high value, one at a time; the preferred policy's net social value
               under each, and whether the best policy changes. Value judgements
               that only enter the accounting are recomputed from the stored
               aggregates; structural ones re simulate the battery on fewer paths.
  structural   the battery re run under alternative model structures (myopic or
               forward looking firms, a weak regulator, a strong or weak effect of
               safety practice on incidents, lax offshore jurisdictions); which
               policy wins under each, and how often the preferred one survives.
  red_team     firms game the policy: splitting models under the threshold,
               compliance theatre, maximal relocation, relabelling use cases; the
               harm and net social value of every candidate under its worst
               strategy, and the policy design features that survive gaming.
  analogue     an event study on an uploaded price series around a past
               regulatory event, compared with the model's implied early market
               reaction for the policy of similar compliance intensity.
"""

import numpy as np

from . import assumptions as AS
from . import welfare as W
from .economy import Economy, RandomBundle

STRUCTURAL = {
    "myopic_firms": {"plan_months": 6.0, "note": "firms plan six months ahead instead of twelve"},
    "forward_looking_firms": {"plan_months": 24.0, "note": "firms plan two years ahead"},
    "weak_regulator": {"capacity_mult": 0.5, "note": "the regulator has half the stated capacity"},
    "strong_safety_effect": {"assumptions": {"hazard_safety_elasticity": 2.8}, "note": "safety practice cuts incidents faster"},
    "weak_safety_effect": {"assumptions": {"hazard_safety_elasticity": 1.2}, "note": "safety practice cuts incidents more slowly"},
    "lax_offshore": {"assumptions": {"offshore_laxity": 1.2}, "note": "offshore activity is twice as hazardous as at home"},
    "heavy_tail": {"assumptions": {"catastrophe_prior_monthly": 0.005}, "note": "the catastrophic tail is two and a half times more likely"},
}

GAMING = {
    "threshold_splitting": {"threshold_split": 0.8, "note": "models are split so the regulator sees capability 20% below the real level"},
    "compliance_theatre": {"compliance_theatre": True, "note": "mandated safety spend is reported but not spent; evaluations are gamed"},
    "maximal_relocation": {"mobility_boost": 1.6, "relocation_discount": 0.5, "note": "firms are more mobile and moving is cheaper than assumed"},
    "use_case_relabelling": {"relabel": 0.6, "note": "deployments are relabelled into lower tiers, avoiding 60% of tier costs"},
}


def _nsv_table(results, a, boot=0):
    """Expected net social value and harm avoided per candidate from results (dict name -> PolicyResult)."""
    aggs = {n: W.aggregates(r, a) for n, r in results.items()}
    out = {}
    for n in results:
        if n == "baseline":
            continue
        c = W.components(aggs[n], aggs["baseline"], a)
        out[n] = {"nsv": float(c["net_social_value"].mean()), "harm_avoided": float(c["harm_avoided"].mean()),
                  "gross_cost": float(c["gross_cost"].mean())}
    return out


def _best(table, candidates=None):
    """The candidate with the highest expected net social value, among `candidates` when given (the
    instruments that satisfied the question's constraints in the main run)."""
    names = [n for n in table if candidates is None or n in candidates] or list(table)
    return max(names, key=lambda n: table[n]["nsv"])


def _slice_aggs(aggs, n):
    """The main run's aggregates restricted to the first n paths (common random numbers make these the
    paths a smaller re simulation uses)."""
    out = {}
    for name, A in aggs.items():
        out[name] = {k: (v[:n] if isinstance(v, np.ndarray) and v.ndim >= 1 and v.shape[0] >= n else v) for k, v in A.items()}
        out[name]["n_paths"] = n
    return out


def paired_table(resim, a2, aggs, a, paths):
    """A re simulation on the first `paths` paths, paired with the main run: for every candidate the headline
    figure shifted by the path by path change the alternative produces on those same paths,
        adjusted[n] = main_full[n] + (resim[n] - main_first_paths[n]).
    With the default assumptions the shift is zero and the table reproduces the headline figures exactly."""
    full = _nsv_table_from_aggs(aggs, a)
    sub = _nsv_table_from_aggs(_slice_aggs(aggs, paths), a)
    new = _nsv_table(resim, a2)
    out = {}
    for n in full:
        out[n] = {k: full[n][k] + (new[n][k] - sub[n][k]) for k in ("nsv", "harm_avoided", "gross_cost")}
        out[n]["resimulated_paths"] = paths
        out[n]["unpaired_nsv"] = new[n]["nsv"]
    return out


def _nsv_table_from_aggs(aggs, a):
    out = {}
    for n in aggs:
        if n == "baseline":
            continue
        c = W.components(aggs[n], aggs["baseline"], a)
        out[n] = {"nsv": float(c["net_social_value"].mean()), "harm_avoided": float(c["harm_avoided"].mean()),
                  "gross_cost": float(c["gross_cost"].mean())}
    return out


def tornado(aggs, a, policies, firms, horizon, preferred, paths=80, seed=7, progress=None, candidates=None):
    """aggs: stored aggregates per policy (from the main run). policies: dict name -> policy doc.
    Reweightable assumptions are recomputed from the stored paths; the others are re simulated on the first
    `paths` paths with the main run's seed and paired with it (see paired_table)."""
    rows = []
    base_table = _nsv_table_from_aggs(aggs, a)
    ref = base_table[preferred]["nsv"]
    paths = int(min(paths, aggs["baseline"]["n_paths"]))
    eco = None
    for key, (lo, hi) in AS.TORNADO.items():
        vals = {}
        for tag, v in (("low", lo), ("high", hi)):
            a2 = dict(a); a2[key] = v
            if key in AS.REWEIGHTABLE:
                table = _nsv_table_from_aggs(aggs, a2)
            else:
                if eco is None:
                    eco = Economy(firms, a, horizon=horizon, n_paths=paths, seed=seed)
                eco.a = dict(a2)
                res = {n: eco.run(policies[n]) for n in policies}
                table = paired_table(res, a2, aggs, a, paths)
                eco.a = dict(a)
            vals[tag] = {"value": v, "nsv": table[preferred]["nsv"], "best": _best(table, candidates),
                         "best_unconstrained": _best(table)}
        rows.append({"assumption": key, "default": a[key], "unit": AS.SPEC[key][3], "meaning": AS.SPEC[key][4],
                     "low": vals["low"], "high": vals["high"],
                     "swing": abs(vals["high"]["nsv"] - vals["low"]["nsv"]),
                     "resimulated": key not in AS.REWEIGHTABLE,
                     "best_changes": (vals["low"]["best"] != preferred) or (vals["high"]["best"] != preferred)})
        if progress:
            progress(key)
    rows.sort(key=lambda r: -r["swing"])
    flips = [r["assumption"] for r in rows if r["best_changes"]]
    return {"reference_nsv": ref, "preferred": preferred, "rows": rows, "flips": flips,
            "sign_robust": all((r["low"]["nsv"] > 0) == (ref > 0) and (r["high"]["nsv"] > 0) == (ref > 0) for r in rows)}


def structural(policies, firms, a, horizon, preferred, paths=80, seed=7, progress=None, aggs=None, candidates=None):
    """Each variant is run on the first `paths` paths with the main run's seed; when the main run's aggregates
    are given the table is paired with it (see paired_table), so the figures sit on the headline scale."""
    out = []
    if aggs is not None:
        paths = int(min(paths, aggs["baseline"]["n_paths"]))
    eco = Economy(firms, a, horizon=horizon, n_paths=paths, seed=seed)
    for name, var in STRUCTURAL.items():
        var = dict(var)
        res = {n: eco.run(policies[n], variant=var) for n in policies}
        table = paired_table(res, a, aggs, a, paths) if aggs is not None else _nsv_table(res, a)
        order = sorted(table, key=lambda n: -table[n]["nsv"])
        out.append({"variant": name, "note": var["note"], "best": _best(table, candidates), "best_unconstrained": order[0], "order": order,
                    "preferred_rank": order.index(preferred) + 1 if preferred in order else None,
                    "preferred_nsv": table[preferred]["nsv"] if preferred in table else None,
                    "table": table})
        if progress:
            progress(name)
    survives = sum(1 for r in out if r["best"] == preferred)
    top2 = sum(1 for r in out if r["preferred_rank"] and r["preferred_rank"] <= 2)
    return {"variants": out, "preferred": preferred, "wins": survives, "top_two": top2, "n": len(out),
            "survival": survives / max(1, len(out))}


def red_team(policies, firms, a, horizon, paths=80, seed=7, progress=None):
    eco = Economy(firms, a, horizon=horizon, n_paths=paths, seed=seed)
    base = eco.run(policies["baseline"])
    base_agg = W.aggregates(base, a)
    rows = []
    for n, pol in policies.items():
        if n == "baseline":
            continue
        honest = eco.run(pol)
        c0 = W.components(W.aggregates(honest, a), base_agg, a)
        row = {"policy": n, "label": pol["label"], "honest": {"nsv": float(c0["net_social_value"].mean()),
                                                               "harm_avoided": float(c0["harm_avoided"].mean())},
               "strategies": {}}
        for g, spec in GAMING.items():
            gamed = eco.run(pol, gaming=spec)
            c = W.components(W.aggregates(gamed, a), base_agg, a)
            row["strategies"][g] = {"nsv": float(c["net_social_value"].mean()), "harm_avoided": float(c["harm_avoided"].mean()),
                                    "offshore_end": float(gamed.offshore[:, -1, :].mean()),
                                    "nsv_loss": float(c0["net_social_value"].mean() - c["net_social_value"].mean()),
                                    "harm_lost": float(c0["harm_avoided"].mean() - c["harm_avoided"].mean())}
        worst = min(row["strategies"], key=lambda g: row["strategies"][g]["nsv"])
        row["worst_strategy"] = worst
        row["worst_nsv"] = row["strategies"][worst]["nsv"]
        row["gaming_loss"] = row["honest"]["nsv"] - row["worst_nsv"]
        rows.append(row)
        if progress:
            progress(n)
    rows.sort(key=lambda r: -r["worst_nsv"])
    return {"rows": rows, "strategies": {g: s["note"] for g, s in GAMING.items()},
            "most_robust": rows[0]["policy"] if rows else None}


def analogue(prices, event_index, window=(1, 6), market=None):
    """Event study on a price series (list of floats, monthly) around event_index: mean relative return over
    the window after the event against the drift before it; optional market series for an abnormal return."""
    p = np.asarray(prices, dtype=float)
    if len(p) < event_index + window[1] + 1 or event_index < 6:
        return None
    r = np.diff(np.log(p))
    if market is not None:
        m = np.diff(np.log(np.asarray(market, dtype=float)))
        pre = slice(max(0, event_index - 24), event_index - 1)
        X = np.vstack([np.ones(len(m[pre])), m[pre]]).T
        beta = np.linalg.lstsq(X, r[pre], rcond=None)[0]
        ar = r - (beta[0] + beta[1] * m)
    else:
        pre_mean = r[max(0, event_index - 24):event_index - 1].mean()
        ar = r - pre_mean
    # r[k] is the return from month k to month k+1, so the months window[0]..window[1] after the event are
    # r[event_index + window[0] - 1 : event_index + window[1]]
    car = float(ar[event_index + window[0] - 1:event_index + window[1]].sum())
    return {"car": car, "window_months": list(window), "event_index": int(event_index), "n": int(len(p))}
