"""Assurance: attacking the answer before anyone acts on it.

Every stage re decides the question under an alternative: feasibility is re assessed against the question's
constraints and the status quo is an alternative, so "the best option changes" means the decision changes,
and an instrument that stops satisfying a constraint under an alternative stops being acceptable under it.

  screen       every declared assumption, one at a time, at the low and the high end of its plausible range
               (assumptions.RANGE). Assumptions that enter only the welfare accounting are recomputed exactly
               from the stored paths; the others re simulate the battery, all of them in one vectorised pass on
               the first paths of the run. The tornado is the screen's largest swings.
  joint draw   all the assumptions drawn together over their plausible ranges (a Latin hypercube, correlated
               where they plausibly move together): the net social value of every alternative under parameter
               uncertainty, the probability each is the decision, its expected regret, the probability it
               satisfies the constraints and is worth doing, and which assumptions the answer moves with.
  variance     a Sobol decomposition (Saltelli's design) over the assumptions the screen found most influential:
               the share of the variance of the focus option's value, and of its margin over the best
               alternative, that each explains alone and with its interactions.
  structural   the battery re run under alternative model structures.
  red_team     firms game each instrument; whether it is still within the constraints and still worth doing
               under its worst strategy, and which instrument is best when every one is gamed at its worst.
  batches      the run's paths split into independent batches (each path has its own random stream): the
               decision in each batch, a replication check that needs no extra simulation.

Re simulations run on the first n paths of the main run (common random numbers make a smaller bundle exactly
the first paths of a larger one) and are paired with it:

    adjusted = main, all paths + (alternative, first n paths - main, first n paths),

so every figure sits on the headline scale and an alternative that changes nothing reproduces the headline.
"""

import numpy as np

from . import assumptions as AS
from .evaluate import MEANS, best_index, constraint_values, decide, decision_arrays, feasible_mask
from .reduce import head, simulate_battery, simulate_design, simulate_gamed
from .stats import benjamini_hochberg, interval, ks_split, saltelli, sobol_indices, sobol_intervals, spearman, spearman_test
from . import welfare as W

QUANT = tuple(q for q in MEANS if q != "headline")
FDR = 0.10          # false discovery rate at which an assumption is called a driver in the joint draw

STRUCTURAL = {
    "myopic_firms": {"plan_months": 6.0, "note": "firms plan six months ahead instead of twelve"},
    "forward_looking_firms": {"plan_months": 24.0, "note": "firms plan two years ahead"},
    "weak_regulator": {"capacity_mult": 0.5, "note": "the regulator has half the stated capacity"},
    "strong_safety_effect": {"assumptions": {"hazard_safety_elasticity": 2.8}, "note": "safety practice cuts incidents faster"},
    "weak_safety_effect": {"assumptions": {"hazard_safety_elasticity": 1.2}, "note": "safety practice cuts incidents more slowly"},
    "lax_offshore": {"assumptions": {"offshore_laxity": 1.2}, "note": "offshore activity is twice as hazardous as at home"},
    "heavy_tail": {"assumptions": {"catastrophe_prior_monthly": 0.005}, "note": "the catastrophic tail is two and a half times more likely"},
    "systemic_catastrophes": {"assumptions": {"catastrophe_correlation": 0.8}, "note": "catastrophic failures are strongly correlated across firms"},
}

GAMING = {
    "threshold_splitting": {"threshold_split": 0.8, "note": "models are split so the regulator sees capability 20% below the real level"},
    "compliance_theatre": {"compliance_theatre": True, "note": "mandated safety spend is reported but not spent; evaluations are gamed"},
    "maximal_relocation": {"mobility_boost": 1.6, "relocation_discount": 0.5, "note": "firms are more mobile and moving is cheaper than assumed"},
    "use_case_relabelling": {"relabel": 0.6, "note": "deployments are relabelled into lower tiers, avoiding 60% of tier costs"},
}


# ------------------------------------------------------------------ tables --
def central(names, arr, n=None):
    """Means of the decision quantities on the main run: {quantity: (A,)}; on the first n paths when n is given."""
    return {q: np.array([float(np.mean(arr[nm][q] if n is None else arr[nm][q][:n])) for nm in names]) for q in MEANS}


def paired(names, arr_main, arr_alt, n, blocks=1):
    """Means under an alternative simulated on the first n paths, shifted onto the headline scale:
    {quantity: (A, blocks)}. arr_alt holds blocks x n paths per alternative."""
    full, sub = central(names, arr_main), central(names, arr_main, n)
    out = {}
    for q in QUANT:
        X = np.stack([np.asarray(arr_alt[nm][q], dtype=float) for nm in names], axis=0)
        scen = X.reshape(len(names), blocks, n).mean(axis=2)
        out[q] = full[q][:, None] + scen - sub[q][:, None]
    out["headline"] = np.repeat(full["headline"][:, None], blocks, axis=1)
    return out


def _decisions(names, M, constraints):
    """The decision in each column of a table of means (A, S): lists of the preferred alternative, and masks."""
    ok = feasible_mask(M, constraints)
    nsv = np.asarray(M["net_social_value"])
    j = best_index(nsv, ok)
    best = [names[k] if k >= 0 else None for k in np.atleast_1d(j)]
    return best, ok, nsv


def _cell(names, M, col, focus, constraints, ref=None):
    """The decision in one column of a table of means. With `ref` (the run's decision), also whether that alternative
    still satisfies the constraints here, and why the decision changed if it did: 'feasibility' when the run's
    decision is no longer within the constraints, 'value' when another alternative within them overtakes it."""
    nsv = np.asarray(M["net_social_value"])[:, col]
    ok = feasible_mask({k: np.asarray(v)[:, col] for k, v in M.items()}, constraints)
    j = int(best_index(nsv, ok))
    fi = names.index(focus)
    out = {"nsv": float(nsv[fi]), "best": names[j] if j >= 0 else None, "focus_feasible": bool(ok[fi]),
           "best_unconstrained": names[int(np.argmax(nsv))]}
    if ref is not None and ref in names:
        rf = bool(ok[names.index(ref)])
        out["ref_feasible"] = rf
        out["flip"] = None if out["best"] == ref else ("value" if rf else "feasibility")
    return out


# ------------------------------------------------------------------ screen --
def screen(reds, arr, a, policies, firms, horizon, focus, constraints, paths=8, seed=7, chunk=960, progress=None):
    """Every assumption at the two ends of its plausible range. reds, arr: the main run's reduced policies and
    decision arrays. Returns rows for all assumptions, sorted by the swing of the focus option's value."""
    names = list(policies)
    n = int(min(paths, reds["baseline"]["n_paths"]))
    levels = AS.oat_levels()
    c0 = central(names, arr)
    base_M = {q: c0[q][:, None] for q in MEANS}
    ref = _cell(names, base_M, 0, focus, constraints)
    rb = ref["best"]
    cells = {}
    # exact, on every path, for the assumptions that only enter the accounting
    for key, tag, v in levels:
        if key in AS.WELFARE_ONLY:
            a2 = dict(a); a2[key] = v
            c2 = central(names, decision_arrays(reds, a2))
            M = {q: c2[q][:, None] for q in MEANS}
            cells[(key, tag)] = dict(_cell(names, M, 0, focus, constraints, ref=rb), value=v, se=0.0)
    # one vectorised re simulation for the rest
    sim = [(key, tag, v) for key, tag, v in levels if key not in AS.WELFARE_ONLY]
    if sim:
        rows = [{key: v} for key, tag, v in sim]
        dreds, a_des = simulate_design(policies, firms, a, rows, horizon, n, seed, chunk=chunk,
                                       progress=(lambda done, tot: progress(f"screen {done} of {tot}")) if progress else None)
        da = decision_arrays(dreds, a_des)
        M = paired(names, arr, da, n, blocks=len(rows))
        # Monte Carlo standard error of each cell's shift: the alternative minus the main run, path by path, on the n paths
        shift = (np.asarray(da[focus]["net_social_value"], dtype=float).reshape(len(rows), n)
                 - np.asarray(arr[focus]["net_social_value"][:n], dtype=float)[None, :])
        se = shift.std(axis=1, ddof=1) / np.sqrt(n) if n > 1 else np.zeros(len(rows))
        for col, (key, tag, v) in enumerate(sim):
            cells[(key, tag)] = dict(_cell(names, M, col, focus, constraints, ref=rb), value=v, se=float(se[col]))
    out = []
    for key in AS.RANGE:
        lo, hi = cells[(key, "low")], cells[(key, "high")]
        swing = abs(hi["nsv"] - lo["nsv"])
        sse = float(np.hypot(lo["se"], hi["se"]))
        out.append({"assumption": key, "default": float(a[key]), "unit": AS.SPEC[key][3], "meaning": AS.SPEC[key][4],
                    "low": lo, "high": hi, "swing": swing, "swing_se": sse, "swing_resolved": bool(swing > 2.0 * sse),
                    "resimulated": key not in AS.WELFARE_ONLY,
                    "best_changes": (lo["best"] != rb) or (hi["best"] != rb),
                    "focus_feasibility_changes": (lo["focus_feasible"] != ref["focus_feasible"]) or (hi["focus_feasible"] != ref["focus_feasible"])})
    out.sort(key=lambda r: -r["swing"])
    flips = [r["assumption"] for r in out if r["best_changes"]]
    by_feas = [r["assumption"] for r in out if "feasibility" in (r["low"].get("flip"), r["high"].get("flip"))]
    by_value = [r["assumption"] for r in out if "value" in (r["low"].get("flip"), r["high"].get("flip"))]
    return {"reference_nsv": ref["nsv"], "reference_best": rb, "preferred": focus, "rows": out, "flips": flips,
            "flips_by_feasibility": by_feas, "flips_by_value": by_value,
            "n_assumptions": len(out), "resimulated_paths": n, "n_swing_resolved": int(sum(r["swing_resolved"] for r in out)),
            "sign_robust": all((r["low"]["nsv"] > 0) == (ref["nsv"] > 0) and (r["high"]["nsv"] > 0) == (ref["nsv"] > 0) for r in out),
            "note": "a change of decision is by feasibility when the run's decision no longer satisfies a constraint under the alternative, "
                    "and by value when another alternative within the constraints overtakes it; the standard error of a swing is the "
                    "Monte Carlo error of the paired re simulation and is zero where the assumption is recomputed exactly"}


def tornado_view(scr, top=15):
    """The screen's largest swings, in the shape the tornado has always had."""
    return {"reference_nsv": scr["reference_nsv"], "reference_best": scr["reference_best"], "preferred": scr["preferred"],
            "rows": scr["rows"][:top], "flips": scr["flips"], "sign_robust": scr["sign_robust"],
            "flips_by_feasibility": scr.get("flips_by_feasibility", []), "flips_by_value": scr.get("flips_by_value", []),
            "n_screened": scr["n_assumptions"], "shown": min(top, len(scr["rows"]))}


# -------------------------------------------------------------- joint draw --
def joint_draw(reds, arr, a, policies, firms, horizon, focus, constraints, draws=64, paths=8, seed=7, chunk=960, progress=None,
               extra_policies=None, on_design=None):
    """All the assumptions drawn together. Returns the parameter uncertainty summary per alternative and the
    rank correlation of every assumption with the focus option's value and with its margin.

    extra_policies: instruments outside the battery to simulate in the same draws (the validation layer's benchmarks
    may be defined under one); on_design(reduced design, drawn assumptions, draws) is called while the design is in
    memory and its result is returned under "_per_draw" with each draw's decision, for the calibration."""
    names = list(policies)
    n = int(min(paths, reds["baseline"]["n_paths"]))
    S = AS.sample(draws, seed=seed + 31, base=a)
    keys = list(S)
    rows = [{k: float(S[k][m]) for k in keys} for m in range(draws)]
    sim = dict(policies)
    sim.update({k: v for k, v in (extra_policies or {}).items() if k not in sim})
    dreds, a_des = simulate_design(sim, firms, a, rows, horizon, n, seed, chunk=chunk, moments=on_design is not None,
                                   progress=(lambda done, tot: progress(f"joint draw {done} of {tot}")) if progress else None)
    per_draw_moments = on_design(dreds, S, draws) if on_design is not None else None
    M = paired(names, arr, decision_arrays({nm: dreds[nm] for nm in names}, a_des), n, blocks=draws)
    best, ok, nsv = _decisions(names, M, constraints)
    # regret is measured against the decision: the best alternative within the constraints in the draw. It is defined
    # for an alternative in the draws where it is itself within the constraints (choosing it elsewhere breaks a
    # constraint, which is not a cost in $bn), so it is read beside the share of draws in which it is.
    top = np.where(ok, nsv, -np.inf).max(axis=0)
    fi = names.index(focus)
    others = np.delete(nsv, fi, axis=0)
    margin = nsv[fi] - others.max(axis=0)
    alts = []
    for i, nm in enumerate(names):
        lo, hi = interval(nsv[i], 0.90)
        m = ok[i] & np.isfinite(top)
        alts.append({"policy": nm, "nsv_mean": float(nsv[i].mean()), "nsv_lo": lo, "nsv_hi": hi,
                     "p_best": float(np.mean([b == nm for b in best])),
                     "p_feasible": float(ok[i].mean()), "p_positive": float((nsv[i] > 0).mean()),
                     "p_acceptable": float((ok[i] & (nsv[i] > 0)).mean()) if nm != "baseline" else float(ok[i].mean()),
                     "expected_regret": float((top[m] - nsv[i][m]).mean()) if m.any() else None,
                     "regret_draws": int(m.sum())})
    # which assumptions the answer moves with: the rank correlation of each with the focus option's value and with its
    # margin, and Monte Carlo filtering, the difference between an assumption's values in the draws where the focus
    # option is the decision and in those where it is not (a two sample Kolmogorov Smirnov statistic). Sixty odd tests
    # against one output will flag some by chance, so what is called a driver is what survives a 10% false discovery rate.
    decided = np.array([b == focus for b in best])
    sens = []
    for k in keys:
        rm, pm = spearman_test(S[k], margin)
        ks, pk = ks_split(S[k], decided)
        sens.append({"assumption": k, "rho_value": spearman(S[k], nsv[fi]), "rho_margin": rm, "p_margin": pm,
                     "ks_decision": ks, "p_decision": pk})
    for row, fm, fd in zip(sens, benjamini_hochberg([r["p_margin"] for r in sens], FDR), benjamini_hochberg([r["p_decision"] for r in sens], FDR)):
        row["margin_driver"] = bool(fm); row["decision_driver"] = bool(fd)
    sens.sort(key=lambda r: -abs(r["rho_margin"]))
    by = {x["policy"]: x for x in alts}
    safe = [x for x in alts if x["p_feasible"] >= 0.9 and x["expected_regret"] is not None]
    least = min(safe, key=lambda x: x["expected_regret"]) if safe else None
    return {"_per_draw": {"S": S, "best": best, "ok": ok, "nsv": nsv, "moments": per_draw_moments} if per_draw_moments is not None else None,
            "draws": int(draws), "paths": n, "focus": focus, "alternatives": alts,
            "p_none_feasible": float(np.mean([b is None for b in best])),
            "p_focus_best": by[focus]["p_best"], "p_focus_acceptable": by[focus]["p_acceptable"],
            "least_regret": least["policy"] if least else None,
            "least_regret_rule": "the lowest expected regret among the alternatives within the constraints in at least 90% of the draws",
            "margin_mean": float(margin.mean()), "p_margin_positive": float((margin > 0).mean()),
            "sensitivity": sens, "rho_noise": float(1.96 / np.sqrt(max(draws - 1, 1))), "fdr": FDR,
            "margin_drivers": [r["assumption"] for r in sens if r["margin_driver"]],
            "decision_drivers": [r["assumption"] for r in sorted(sens, key=lambda r: -r["ks_decision"]) if r["decision_driver"]],
            "filter_split": [int(decided.sum()), int((~decided).sum())],
            "note": "triangular distributions on the declared plausible ranges with the mode at the run's value, correlated groups "
                    "joined by a Gaussian copula; a prior over the assumptions, not a posterior estimated from data"}


# ---------------------------------------------------------------- variance --
def variance_decomposition(reds, arr, a, policies, firms, horizon, focus, keys, base=32, paths=4, seed=7, chunk=960,
                           challengers=None, progress=None):
    """Sobol indices of the focus option's value and of its margin over the best challenger, over `keys`
    (the most influential assumptions; the rest held at the run's values). The inputs are drawn independently
    over their plausible ranges, as the decomposition requires."""
    k = len(keys)
    if k < 2:
        return None
    sub = {nm: policies[nm] for nm in policies if nm in ({"baseline", focus} | set(challengers or []))}
    names = list(sub)
    n = int(min(paths, reds["baseline"]["n_paths"]))
    A, B, ABs = saltelli(int(base), k, seed=seed + 53)
    mats = [A, B] + ABs
    rows = []
    for U in mats:
        S = AS.sample(len(U), keys=keys, base=a, u=U)
        rows += [{kk: float(S[kk][m]) for kk in keys} for m in range(len(U))]
    dreds, a_des = simulate_design(sub, firms, a, rows, horizon, n, seed, chunk=chunk,
                                   progress=(lambda done, tot: progress(f"variance {done} of {tot}")) if progress else None)
    sub_arr = {nm: arr[nm] for nm in names}
    M = paired(names, sub_arr, decision_arrays(dreds, a_des), n, blocks=len(rows))
    nsv = M["net_social_value"]
    fi = names.index(focus)
    y_val = nsv[fi]
    y_mar = nsv[fi] - np.delete(nsv, fi, axis=0).max(axis=0)
    m = int(base)

    def split(y):
        return y[:m], y[m:2 * m], [y[(2 + i) * m:(3 + i) * m] for i in range(k)]
    s1v, stv = sobol_indices(*split(y_val))
    s1m, stm = sobol_indices(*split(y_mar))
    iv = sobol_intervals(*split(y_val), b=200, seed=seed + 59)
    im = sobol_intervals(*split(y_mar), b=200, seed=seed + 61)
    rows_out = []
    for i in range(k):
        rows_out.append({"assumption": keys[i], "first_order_value": float(s1v[i]), "total_value": float(stv[i]),
                         "first_order_margin": float(s1m[i]), "total_margin": float(stm[i]),
                         "first_order_value_lo": float(iv[0][i]), "first_order_value_hi": float(iv[1][i]),
                         "total_value_lo": float(iv[2][i]), "total_value_hi": float(iv[3][i]),
                         "first_order_margin_lo": float(im[0][i]), "first_order_margin_hi": float(im[1][i]),
                         "total_margin_lo": float(im[2][i]), "total_margin_hi": float(im[3][i]),
                         # an input matters for the margin when its total share is clear of zero at this design size
                         "resolved": bool(im[2][i] > 0.01)})
    rows_out.sort(key=lambda r: -r["total_margin"])
    half = float(np.mean([0.5 * (r["total_margin_hi"] - r["total_margin_lo"]) for r in rows_out]))
    return {"focus": focus, "keys": list(keys), "base": m, "evaluations": len(rows), "paths": n, "against": [x for x in names if x != focus],
            "rows": rows_out, "sum_first_order_value": float(s1v.sum()), "sum_first_order_margin": float(s1m.sum()),
            "interaction_share_value": float(max(0.0, 1.0 - s1v.sum())), "interaction_share_margin": float(max(0.0, 1.0 - s1m.sum())),
            "sd_value": float(np.std(y_val[:2 * m], ddof=1)), "sd_margin": float(np.std(y_mar[:2 * m], ddof=1)),
            "interval_level": 0.90, "mean_halfwidth_total_margin": half, "bootstrap": 200,
            "note": "Saltelli's design on scrambled Sobol points; first order by Saltelli (2010), total order by Jansen (1999); 90% "
                    "bootstrap intervals over the base sample; the other assumptions are held at the run's values, so the shares are "
                    "of the variance these inputs produce, and the inputs are drawn independently, as the decomposition requires"}


# -------------------------------------------------------------- structural --
def structural(reds, arr, a, policies, firms, horizon, focus, constraints, paths=80, seed=7, chunk=480, progress=None, preferred=None):
    names = list(policies)
    n = int(min(paths, reds["baseline"]["n_paths"]))
    preferred = preferred if preferred is not None else focus
    out = []
    for name, var in STRUCTURAL.items():
        var = dict(var)
        a2 = dict(a); a2.update(var.get("assumptions", {}))
        vreds = simulate_battery(policies, firms, a, horizon, n, seed, chunk=chunk, full=False, variant=var)
        M = paired(names, arr, decision_arrays(vreds, a2), n, blocks=1)
        best, ok, nsv = _decisions(names, M, constraints)
        nsv = nsv[:, 0]; ok = ok[:, 0]
        order = [names[i] for i in np.argsort(-nsv, kind="stable") if names[i] != "baseline"]
        fi = names.index(focus)
        out.append({"variant": name, "note": var["note"], "best": best[0], "best_unconstrained": order[0] if order else None, "order": order,
                    "preferred_rank": order.index(focus) + 1 if focus in order else None,
                    "preferred_nsv": float(nsv[fi]), "preferred_feasible": bool(ok[fi]),
                    "preferred_acceptable": bool(ok[fi] and nsv[fi] > 0),
                    "table": {nm: {"nsv": float(nsv[i]), "feasible": bool(ok[i])} for i, nm in enumerate(names)}})
        if progress:
            progress(name)
    survives = sum(1 for r in out if r["best"] == preferred)
    top2 = sum(1 for r in out if r["preferred_rank"] and r["preferred_rank"] <= 2)
    accept = sum(1 for r in out if r["preferred_acceptable"])
    return {"variants": out, "preferred": focus, "decision": preferred, "wins": survives, "top_two": top2, "acceptable": accept, "n": len(out),
            "survival": survives / max(1, len(out)), "resimulated_paths": n}


# ---------------------------------------------------------------- red team --
def red_team(reds, arr, a, policies, firms, horizon, constraints, paths=80, seed=7, chunk=480, progress=None):
    """Each instrument under each gaming strategy, on the first paths of the run and paired with it. An instrument
    is acceptable under a strategy when it still satisfies the question's constraints and still beats the status
    quo."""
    names = list(policies)
    n = int(min(paths, reds["baseline"]["n_paths"]))
    base_n = head(reds["baseline"], n)
    full, sub = central(names, arr), central(names, arr, n)
    rows = []
    for i, nm in enumerate(names):
        if nm == "baseline":
            continue
        pol = policies[nm]
        honest = {q: float(full[q][i]) for q in QUANT}
        ok_h = bool(feasible_mask({q: np.array([honest[q]]) for q in QUANT}, constraints)[0])
        row = {"policy": nm, "label": pol["label"],
               "honest": {"nsv": honest["net_social_value"], "harm_avoided": honest["harm_avoided"], "feasible": ok_h},
               "strategies": {}}
        gamed_all = simulate_gamed(pol, GAMING, firms, a, horizon, n, seed)
        for g, spec in GAMING.items():
            gamed = gamed_all[g]
            ga = decision_arrays({"baseline": base_n, nm: gamed}, a)[nm]
            m = {q: np.array([full[q][i] + float(np.mean(ga[q])) - sub[q][i]]) for q in QUANT}
            ok = bool(feasible_mask(m, constraints)[0])
            cv = {key: float(val[0]) for key, val, lim, sense in constraint_values(m, constraints)}
            nsv_g = float(m["net_social_value"][0])
            row["strategies"][g] = {"nsv": nsv_g, "harm_avoided": float(m["harm_avoided"][0]),
                                    "industry_value_change": float(m["industry_value_change"][0]),
                                    "feasible": ok, "acceptable": bool(ok and nsv_g > 0), "constraint_values": cv,
                                    "nsv_loss": honest["net_social_value"] - nsv_g,
                                    "harm_lost": honest["harm_avoided"] - float(m["harm_avoided"][0])}
        worst = min(row["strategies"], key=lambda g: row["strategies"][g]["nsv"])
        row["worst_strategy"] = worst
        row["worst_nsv"] = row["strategies"][worst]["nsv"]
        row["gaming_loss"] = row["honest"]["nsv"] - row["worst_nsv"]
        row["acceptable_under_all"] = all(s["acceptable"] for s in row["strategies"].values())
        row["feasible_under_all"] = all(s["feasible"] for s in row["strategies"].values())
        rows.append(row)
        if progress:
            progress(nm)
    rows.sort(key=lambda r: -r["worst_nsv"])
    ok_rows = [r for r in rows if r["feasible_under_all"] and r["honest"]["feasible"]]
    maximin = max(ok_rows, key=lambda r: r["worst_nsv"]) if ok_rows else None
    return {"rows": rows, "strategies": {g: s["note"] for g, s in GAMING.items()},
            "most_robust": rows[0]["policy"] if rows else None,
            "maximin": (maximin["policy"] if maximin and maximin["worst_nsv"] > 0 else "baseline") if rows else None,
            "acceptable_under_all": [r["policy"] for r in rows if r["acceptable_under_all"] and r["honest"]["feasible"]],
            "resimulated_paths": n,
            "note": "maximin: the instrument with the highest value under its own worst gaming strategy among those that stay within "
                    "the constraints under every strategy; the status quo when none of them stays above zero"}


# ------------------------------------------------------------------ batches --
def batches(names, arr, constraints, k=4, min_size=30):
    """The run's paths split into k consecutive batches of independent paths: the decision and the focus values in
    each. Paths are independent draws with their own streams, so batches are replications of a smaller run."""
    N = len(arr["baseline"]["net_social_value"])
    k = int(max(2, min(k, N // max(1, min_size)))) if N >= 2 * min_size else 0
    if k < 2:
        return None
    size = N // k
    rows = []
    for b in range(k):
        sl = slice(b * size, (b + 1) * size)
        M = {q: np.array([float(np.mean(arr[nm][q][sl])) for nm in names]) for q in MEANS}
        d = decide(names, M, constraints)
        rows.append({"batch": b + 1, "paths": size, "preferred": d["preferred"], "best_intervention": d["best_intervention"],
                     "nsv": {nm: float(M["net_social_value"][i]) for i, nm in enumerate(names)}})
    full = decide(names, central(names, arr), constraints)
    agree = sum(1 for r in rows if r["preferred"] == full["preferred"])
    return {"k": k, "size": size, "rows": rows, "preferred": full["preferred"], "agree": agree,
            "note": "consecutive batches of the run's own paths; each path has its own random stream, so the batches are independent"}


# -------------------------------------------------------------- convergence --
def convergence(names, arr, constraints, focus, fractions=(0.125, 0.25, 0.5, 1.0), min_paths=8):
    """The running estimate: the decision and the focus option's expected value on the first eighth, quarter and
    half of the run's paths and on all of them. A smaller run on the same seed uses exactly those first paths, so
    each row is what a run of that size would have reported; the standard error should fall as one over the square
    root of the paths and the estimate should settle inside its earlier intervals."""
    N = len(arr["baseline"]["net_social_value"])
    fi = names.index(focus) if focus in names else None
    rows, seen = [], set()
    for f in fractions:
        n = int(max(min_paths, round(N * f)))
        if n > N or n in seen:
            continue
        seen.add(n)
        M = central(names, arr, n)
        d = decide(names, M, constraints)
        row = {"paths": n, "preferred": d["preferred"], "best_intervention": d["best_intervention"]}
        if fi is not None:
            x = np.asarray(arr[focus]["net_social_value"][:n], dtype=float)
            se = float(x.std(ddof=1) / np.sqrt(n)) if n > 1 else 0.0
            row.update(focus_nsv=float(x.mean()), focus_se=se, focus_lo=float(x.mean() - 1.96 * se), focus_hi=float(x.mean() + 1.96 * se))
        row["p_catastrophe_status_quo"] = float(np.mean(arr["baseline"]["cat_cmc"][:n]))
        rows.append(row)
    final = rows[-1] if rows else None
    stable = bool(final and all(r["preferred"] == final["preferred"] for r in rows[-2:]))
    inside = bool(final and fi is not None and all(r["focus_lo"] - 1e-9 <= final["focus_nsv"] <= r["focus_hi"] + 1e-9 for r in rows))
    return {"focus": focus, "rows": rows, "decision_stable_over_last_doubling": stable, "final_inside_earlier_intervals": inside,
            "note": "running estimates on the first paths of the run (what a smaller run on the same seed reports); intervals here are "
                    "the normal approximation, mean plus or minus 1.96 standard errors"}


# --------------------------------------------------------------- robustness --
def robustness(ev, scr, jd, st, rt):
    """One row per alternative: acceptable (within the constraints and above the status quo) on the central
    estimate and under each family of alternatives. 'robustly acceptable' needs all of: the central estimate,
    at least 90% of the joint draws, every structural variant in which it was the focus, and every gaming strategy."""
    by_jd = {x["policy"]: x for x in (jd or {}).get("alternatives", [])}
    by_rt = {r["policy"]: r for r in (rt or {}).get("rows", [])}
    rows = []
    for r in ev["policies"]:
        nm = r["policy"]
        if nm == "baseline":
            continue
        central_ok = bool(r["feasible"] and r["net_social_value"]["mean"] > 0)
        st_ok = [v["table"][nm]["feasible"] and v["table"][nm]["nsv"] > 0 for v in (st or {}).get("variants", []) if nm in v.get("table", {})]
        st_best = [v["best"] == nm for v in (st or {}).get("variants", [])]
        row = {"policy": nm, "label": r["label"], "central_acceptable": central_ok, "p_feasible": r["p_feasible"],
               "joint_p_acceptable": by_jd.get(nm, {}).get("p_acceptable"), "joint_p_best": by_jd.get(nm, {}).get("p_best"),
               "expected_regret": by_jd.get(nm, {}).get("expected_regret"),
               "structural_acceptable": int(sum(st_ok)), "structural_best": int(sum(st_best)), "structural_n": len(st_ok),
               "gaming_acceptable": by_rt.get(nm, {}).get("acceptable_under_all"),
               "gaming_worst_nsv": by_rt.get(nm, {}).get("worst_nsv")}
        row["robustly_acceptable"] = bool(central_ok and (row["joint_p_acceptable"] or 0) >= 0.9
                                          and (not st_ok or all(st_ok)) and bool(row["gaming_acceptable"]))
        rows.append(row)
    return {"rows": rows, "robustly_acceptable": [r["policy"] for r in rows if r["robustly_acceptable"]],
            "rule": "within the constraints and above the status quo on the central estimate, in at least 90% of the joint draws, "
                    "in every structural variant and under every gaming strategy"}
