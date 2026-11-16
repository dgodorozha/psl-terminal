"""A second implementation of the accounting and the decision rule, written from docs/METHOD.md.

This file imports nothing from the Lab. It reads a run directory (battery.json, assumptions.json, paths.npz,
results.json), recomputes from the stored paths with numpy alone

    the discount factors, every welfare component, the net social value and its identity,
    gross cost and gross benefit, the industry value change,
    the conditional estimator of the probability of a catastrophe,
    every constraint, feasibility, the decision with the status quo among the alternatives,
    the bootstrap confidence interval of each expected value, the share of resamples in which each
    alternative is within the constraints and the share in which it is the best feasible one,

and compares each with what the Lab reported. The critic inside the Lab recomputes with the Lab's own functions;
this is the check that the functions do what the method document says. Paths are stored in single precision, so
figures are compared to within 0.005 ($bn or probability points as applicable).

    python tools/recompute.py runs/<run id>            # exit code 0 when everything agrees
"""

import json
import os
import sys

import numpy as np

TOL = 5e-3
BENEFITS = ("harm_avoided", "cs_change", "productivity_change", "producer_surplus_change")
COSTS = ("compliance_cost", "enforcement_cost", "leakage", "relocation_cost", "labour_change", "insurance_admin_cost")


def load(run_dir):
    with open(os.path.join(run_dir, "battery.json")) as f:
        bat = json.load(f)
    with open(os.path.join(run_dir, "assumptions.json")) as f:
        a = json.load(f)["assumptions"]
    with open(os.path.join(run_dir, "results.json")) as f:
        res = json.load(f)
    z = np.load(os.path.join(run_dir, "paths.npz"))
    paths = {}
    for key in z.files:
        name, k = key.split("__", 1)
        paths.setdefault(name, {})[k] = z[key].astype(np.float64)
    return bat, a, res, paths


def components(P, B, a, d):
    """Per path components of policy P against the status quo B (METHOD.md, section 7)."""
    pv = lambda x: (x * d).sum(axis=1)
    c = {}
    c["harm_avoided"] = a["harm_valuation_multiplier"] * pv(B["harm_exp"] - P["harm_exp"])
    c["cs_change"] = a["consumer_surplus_base_bn"] / 12 * pv(P["service"] ** a["cs_elasticity"] - B["service"] ** a["cs_elasticity"])
    e, t = a["productivity_elasticity"], a["trust_elasticity"]
    c["productivity_change"] = ((1 - a.get("benefit_overlap_share", 0.0)) * a["productivity_base_bn"] / 12
                                * pv(P["service"] ** e * P["trust"] ** t - B["service"] ** e * B["trust"] ** t))
    c["producer_surplus_change"] = a["domestic_ownership_share"] * pv(P["op_earnings"] - B["op_earnings"])
    c["compliance_cost"] = a["compliance_deadweight_share"] * pv(P["compliance"] - B["compliance"])
    c["enforcement_cost"] = a["enforcement_cost_bn"] / 12 * pv(P["enforcement"] - B["enforcement"])
    c["leakage"] = a["leakage_value_share"] * pv(P["offshore_revenue"] - B["offshore_revenue"])
    c["relocation_cost"] = pv(P["relocation"] - B["relocation"])

    def growth(Q):                                      # month on month rise of the service index from its starting level of one
        prev = np.concatenate([np.ones((Q.shape[0], 1)), Q[:, :-1]], axis=1)
        return np.maximum(Q - prev, 0.0)
    c["labour_change"] = a["labour_adjustment_bn"] * pv(growth(P["service"]) - growth(B["service"]))
    load_ = a["insurance_loading"]
    c["insurance_admin_cost"] = a["insurance_admin_share"] * load_ / (1 + load_) * pv(P["premium"] - B["premium"])
    c["net_social_value"] = sum(c[k] for k in BENEFITS) - sum(c[k] for k in COSTS)
    c["industry_value_change"] = pv(P["earnings_exp"] - B["earnings_exp"]) + (P["cap_end"] - B["cap_end"]) * d[-1]
    return c


def gross(m):
    cost = sum(np.maximum(m[k], 0) for k in COSTS) + sum(np.maximum(-m[k], 0) for k in BENEFITS)
    benefit = sum(np.maximum(m[k], 0) for k in BENEFITS) + sum(np.maximum(-m[k], 0) for k in COSTS)
    return cost, benefit


def catastrophe_probability(P):
    """Per path: the hazard of each month counted while no catastrophe has yet happened on the path."""
    hit = P["n_cat"] > 0
    earlier = np.cumsum(hit, axis=1) - hit
    return ((earlier == 0) * P["p_cat_any"]).sum(axis=1)


def constraint_values(m, cons, ref):
    """[(name, value per alternative, limit, 'max' or 'min')] for the constraints the question declared."""
    out = []
    if cons.get("max_industry_loss_bn") is not None:
        out.append(("max_industry_loss_bn", -m["industry_value_change"], cons["max_industry_loss_bn"], "max"))
    if cons.get("max_social_cost_bn") is not None:
        out.append(("max_social_cost_bn", gross(m)[0], cons["max_social_cost_bn"], "max"))
    if cons.get("max_cs_loss_pct") is not None:
        out.append(("max_cs_loss_pct", -m["cs_change"] / ref["cs"] * 100, cons["max_cs_loss_pct"], "max"))
    if cons.get("max_p_major") is not None:
        out.append(("max_p_major", m["major_any"], cons["max_p_major"], "max"))
    if cons.get("max_p_catastrophe") is not None:
        out.append(("max_p_catastrophe", m["cat"], cons["max_p_catastrophe"], "max"))
    if cons.get("min_harm_reduction_pct") is not None:
        out.append(("min_harm_reduction_pct", m["harm_avoided"] / ref["harm"] * 100, cons["min_harm_reduction_pct"], "min"))
    return out


def feasible(m, cons, ref):
    ok = np.ones(np.shape(m["net_social_value"]), dtype=bool)
    for _, v, lim, sense in constraint_values(m, cons, ref):
        ok &= (v <= lim + 1e-12) if sense == "max" else (v >= lim - 1e-12)
    return ok


def best(nsv, ok):
    """The feasible alternative with the highest value along axis 0; the first listed wins a tie (the status quo is
    listed first); -1 where nothing is feasible."""
    j = np.argmax(np.where(ok, nsv, -np.inf), axis=0)
    return np.where(ok.any(axis=0), j, -1)


def bootstrap_weights(n, b, seed):
    """The Lab's resamples: b draws of n paths with replacement from the generator seeded [seed, 7919], as a
    (b, n) matrix of multiplicities over n."""
    rng = np.random.default_rng([int(seed), 7919])
    idx = rng.integers(0, n, size=(b, n))
    w = np.zeros((b, n))
    np.add.at(w, (np.arange(b)[:, None], idx), 1.0)
    return w / n


def recompute(run_dir):
    bat, a, res, paths = load(run_dir)
    names = ["baseline"] + [p["name"] for p in bat["policies"] if p["name"] != "baseline"]      # a tie on value goes to the status quo
    H = int(bat["horizon"])
    d = (1 + a["discount_rate"]) ** (-np.arange(1, H + 1) / 12)            # end of month; the horizon is the last factor
    B = paths["baseline"]
    N = B["harm"].shape[0]
    per = {n: components(paths[n], B, a, d) for n in names}
    for n in names:
        per[n]["cat"] = catastrophe_probability(paths[n])
        per[n]["major_any"] = (paths[n]["n_major"].sum(axis=1) > 0).astype(float)
    quantities = BENEFITS + COSTS + ("net_social_value", "industry_value_change", "cat", "major_any")
    X = {q: np.stack([per[n][q] for n in names]) for q in quantities}        # (alternatives, paths)
    m = {q: X[q].mean(axis=1) for q in quantities}
    ref = {"harm": a["harm_valuation_multiplier"] * (B["harm_exp"] * d).sum(axis=1).mean(),
           "cs": a["consumer_surplus_base_bn"] / 12 * ((B["service"] ** a["cs_elasticity"]) * d).sum(axis=1).mean()}
    cons = {k: v for k, v in (bat.get("constraints") or {}).items() if not k.startswith("_")}
    ok = feasible(m, cons, ref)
    j = int(best(m["net_social_value"], ok))
    w = bootstrap_weights(N, int(res["bootstrap"]), int(res["bootstrap_seed"]))
    mb = {q: X[q] @ w.T for q in quantities}                                  # (alternatives, resamples)
    ok_b = feasible(mb, cons, ref)
    best_b = best(mb["net_social_value"], ok_b)
    gc, gb = gross(m)

    by = {r["policy"]: r for r in res["policies"]}
    rows, worst = [], 0.0
    share_tol = 2.01 / int(res["bootstrap"])

    def cmp(what, mine, theirs, tol=TOL):
        nonlocal worst
        dev = abs(float(mine) - float(theirs))
        worst = max(worst, dev / tol)
        rows.append({"what": what, "recomputed": float(mine), "reported": float(theirs), "deviation": dev, "ok": dev <= tol})

    for i, n in enumerate(names):
        r = by[n]
        cmp(f"{n}: net social value", m["net_social_value"][i], r["net_social_value"]["mean"])
        for k in BENEFITS + COSTS:
            cmp(f"{n}: {k}", m[k][i], r["components"][k]["mean"])
        cmp(f"{n}: components sum to the net social value",
            sum(m[k][i] for k in BENEFITS) - sum(m[k][i] for k in COSTS), r["net_social_value"]["mean"])
        cmp(f"{n}: gross cost", gc[i], r["gross_cost"]["mean"])
        cmp(f"{n}: gross benefit", gb[i], r["gross_benefit"]["mean"])
        cmp(f"{n}: gross benefit less gross cost", gb[i] - gc[i], r["net_social_value"]["mean"])
        cmp(f"{n}: industry value change", m["industry_value_change"][i], r["industry_value_change"]["mean"])
        cmp(f"{n}: probability of a catastrophe", m["cat"][i], r["safety"]["p_catastrophe"], 5e-5)
        cmp(f"{n}: probability of a major incident", m["major_any"][i], r["safety"]["p_major"], 5e-5)
        lo, hi = np.percentile(mb["net_social_value"][i], [2.5, 97.5])
        cmp(f"{n}: 95% interval, lower", lo, r["net_social_value"]["ci_lo"])
        cmp(f"{n}: 95% interval, upper", hi, r["net_social_value"]["ci_hi"])
        cmp(f"{n}: standard error", mb["net_social_value"][i].std(ddof=1), r["net_social_value"]["se"])
        # a resample that lands within single precision of a limit may fall on either side of it: allow two of them
        cmp(f"{n}: share of resamples within the constraints", ok_b[i].mean(), r["p_feasible"], share_tol)
        cmp(f"{n}: share of resamples in which it is the best feasible alternative", (best_b == i).mean(), r["p_best"], share_tol)
        rows.append({"what": f"{n}: within the constraints", "recomputed": bool(ok[i]), "reported": bool(r["feasible"]),
                     "deviation": 0.0, "ok": bool(ok[i]) == bool(r["feasible"])})
        for (key, v, lim, sense), chk in zip(constraint_values(m, cons, ref), r["constraint_checks"]):
            cmp(f"{n}: {key}", v[i], chk["value"])
    mine = names[j] if j >= 0 else None
    rows.append({"what": "the decision", "recomputed": mine, "reported": res["preferred"], "deviation": 0.0, "ok": mine == res["preferred"]})
    inter = [i for i, n in enumerate(names) if n != "baseline" and ok[i]]
    bi = names[max(inter, key=lambda i: (m["net_social_value"][i], -i))] if inter else None
    rows.append({"what": "the best instrument within the constraints", "recomputed": bi, "reported": res["best_intervention"],
                 "deviation": 0.0, "ok": bi == res["best_intervention"]})
    rows.append({"what": "no instrument worse than a feasible status quo is preferred", "recomputed": None, "reported": res["preferred"],
                 "deviation": 0.0,
                 "ok": not (res["preferred"] not in (None, "baseline") and ok[names.index("baseline")]
                            and m["net_social_value"][names.index(res["preferred"])] <= 0)})
    failed = [r for r in rows if not r["ok"]]
    return {"run": os.path.basename(os.path.abspath(run_dir)), "paths": int(N), "alternatives": len(names), "checks": len(rows),
            "failed": len(failed), "ok": not failed, "largest_deviation_in_tolerances": worst, "rows": rows}


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 1:
        print(__doc__)
        return 2
    rep = recompute(argv[0])
    for r in rep["rows"]:
        if not r["ok"]:
            print(f"DIFFERS  {r['what']}: recomputed {r['recomputed']}, reported {r['reported']}")
    print(f"{rep['run']}: {rep['checks'] - rep['failed']} of {rep['checks']} figures agree with the second implementation "
          f"({rep['alternatives']} alternatives, {rep['paths']} paths; largest deviation {rep['largest_deviation_in_tolerances']:.2f} of the tolerance)")
    return 0 if rep["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
