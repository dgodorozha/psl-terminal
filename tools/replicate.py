"""Replication across seeds: is the answer a property of the model or of one set of random numbers?

A single run reports, for every expected value, a standard error and a 95% confidence interval computed from
that run's own paths. This tool checks those statements against independent repetitions of the run:

  the decision     how often each alternative is the preferred one across the seeds, under the expected value
                   rule and under the conservative rule (feasible in at least 90% of resamples)
  the estimates    the spread of each estimate across the seeds beside the standard error a single run reports
                   (their ratio should be near one)
  the intervals    how often a run's 95% interval contains the mean of all the other seeds' paths (it should be
                   near 95%); the exact binomial test of that count against 95% is reported

Each seed is an independent family of random streams, so the seeds are independent replications. Nothing here is
adaptive: every seed runs the same fixed number of paths, so the table describes a run of exactly that size.

    python tools/replicate.py --seeds 20 --paths 480 --horizon 60 --out docs/replication.json
    python tools/replicate.py --question "..." --seeds 10 --paths 240 --first-seed 100
"""

import argparse
import json
import os
import sys
import time

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from psl import __version__  # noqa: E402
from psl import assumptions as AS  # noqa: E402
from psl import welfare as W  # noqa: E402
from psl.evaluate import evaluate  # noqa: E402
from psl.pipeline import make_battery, reference_constraints  # noqa: E402
from psl.question import DEFAULT_QUESTION, parse  # noqa: E402
from psl.reduce import simulate_battery  # noqa: E402
from psl.stats import binomial_coverage  # noqa: E402

QUANTITIES = ("net_social_value", "industry_value_change", "cat_cmc")
LABEL = {"net_social_value": "net social value ($bn)", "industry_value_change": "industry value change ($bn)",
         "cat_cmc": "probability of a catastrophe"}


def replicate(question=DEFAULT_QUESTION, seeds=20, paths=480, horizon=None, first_seed=1, boot=500, assumptions=None, progress=None):
    plan = parse(question)
    bat = make_battery(plan, assumptions=assumptions, budget={"paths": paths, "horizon": horizon or 60})
    a, firms, H = bat["assumptions"], bat["firms"], bat["horizon"]
    policies = {p["name"]: p for p in bat["policies"]}
    names = list(policies)
    d_f = W.discount(H, a["discount_rate"])
    per_seed, means, rows = [], {q: [] for q in QUANTITIES}, []
    for k in range(seeds):
        seed = first_seed + k
        t0 = time.time()
        reds = simulate_battery(policies, firms, a, H, paths, seed, discount_f=d_f)
        cons = reference_constraints(bat["constraints"], reds, a, d_f)
        ev, arr, bt = evaluate(reds, a, cons, boot=boot, seed=seed + 101)
        by = {r["policy"]: r for r in ev["policies"]}
        rec = {"seed": seed, "preferred": ev["preferred"], "preferred_assured": ev["decision"]["preferred_assured"],
               "best_intervention": ev["best_intervention"], "seconds": round(time.time() - t0, 1), "by": {}}
        for n in names:
            r = by[n]
            pc = r["safety"]["p_catastrophe_detail"]
            rec["by"][n] = {"net_social_value": [r["net_social_value"][x] for x in ("mean", "se", "ci_lo", "ci_hi")],
                            "industry_value_change": [r["industry_value_change"][x] for x in ("mean", "se", "ci_lo", "ci_hi")],
                            "cat_cmc": [pc["p"], pc["se"], pc["ci_lo"], pc["ci_hi"]],
                            "feasible": r["feasible"], "p_feasible": r["p_feasible"], "p_best": r["p_best"]}
        for q in QUANTITIES:
            means[q].append([float(np.mean(arr[n][q])) for n in names])
        per_seed.append(rec)
        if progress:
            progress(k + 1, seeds, rec)
    K = len(per_seed)
    for i, n in enumerate(names):
        row = {"policy": n, "label": policies[n]["label"],
               "preferred_share": sum(1 for s in per_seed if s["preferred"] == n) / K,
               "preferred_assured_share": sum(1 for s in per_seed if s["preferred_assured"] == n) / K,
               "feasible_share": sum(1 for s in per_seed if s["by"][n]["feasible"]) / K,
               "p_feasible_mean": float(np.mean([s["by"][n]["p_feasible"] for s in per_seed]))}
        for q in QUANTITIES:
            m = np.array([x[i] for x in means[q]])                     # the K seed means (equal path counts, so the pooled mean is their mean)
            se = np.array([s["by"][n][q][1] for s in per_seed])
            lo = np.array([s["by"][n][q][2] for s in per_seed]); hi = np.array([s["by"][n][q][3] for s in per_seed])
            others = (m.sum() - m) / max(K - 1, 1)                     # the mean of all the other seeds
            inside = int(np.sum((lo <= others + 1e-12) & (others <= hi + 1e-12)))
            sd = float(m.std(ddof=1)) if K > 1 else 0.0
            row[q] = {"pooled_mean": float(m.mean()), "sd_across_seeds": sd, "mean_reported_se": float(se.mean()),
                      "se_ratio": (float(sd / se.mean()) if se.mean() > 1e-12 else None),
                      "min": float(m.min()), "max": float(m.max()),
                      "covered": inside, "of": K, "coverage": inside / K,
                      "p_value": binomial_coverage(inside, K, 0.95) if (n != "baseline" or q == "cat_cmc") else None}
        rows.append(row)
    tot = {q: [sum(r[q]["covered"] for r in rows if r[q]["p_value"] is not None),
               sum(r[q]["of"] for r in rows if r[q]["p_value"] is not None)] for q in QUANTITIES}
    return {"psl_version": __version__, "question": question, "constraints": bat["constraints"], "horizon": H, "paths": paths,
            "seeds": [s["seed"] for s in per_seed], "bootstrap": boot, "assumptions_hash": bat["assumptions_hash"],
            "rows": rows, "per_seed": per_seed,
            "coverage_overall": {q: {"covered": c, "of": n, "coverage": (c / n if n else None)} for q, (c, n) in tot.items()},
            "decision": {"preferred": _tally([s["preferred"] for s in per_seed]),
                         "preferred_assured": _tally([s["preferred_assured"] for s in per_seed])},
            "note": "each seed is an independent run of the same fixed size; coverage is the share of seeds whose 95% interval contains "
                    "the mean of the other seeds; the intervals of one alternative's quantities across seeds are independent, those of "
                    "different alternatives within a seed are not, so the overall coverage is descriptive"}


def _tally(xs):
    out = {}
    for x in xs:
        out[str(x)] = out.get(str(x), 0) + 1
    return dict(sorted(out.items(), key=lambda kv: -kv[1]))


def expected_coverage(k, level=0.95):
    """How often a perfectly calibrated interval at `level` contains the mean of the other k - 1 seeds: a little
    less than `level`, because that mean is itself an estimate with a variance of 1 / (k - 1) of a run's."""
    from scipy.special import ndtr, ndtri
    z = float(ndtri(0.5 + level / 2))
    return float(2 * ndtr(z / np.sqrt(1 + 1 / max(k - 1, 1))) - 1)


def markdown(rep):
    lab = {r["policy"]: r["label"] for r in rep["rows"]}
    name = lambda k: "none" if k in ("None", None) else lab.get(k, k)
    K = len(rep["seeds"])
    exp = expected_coverage(K)
    L = ["# Replication across seeds", "",
         f"The same question run on {K} independent seeds ({rep['seeds'][0]} to {rep['seeds'][-1]}), {rep['paths']} paths each over "
         f"{rep['horizon']} months, version {rep['psl_version']}. Each seed is an independent family of random streams, so the seeds are "
         f"independent replications of a run of exactly this size (no adaptive sampling). Produced by `python tools/replicate.py --seeds {K} "
         f"--paths {rep['paths']}`; the per seed figures are in `replication.json`.", "",
         "Question: " + rep["question"], "",
         "## The decision", "",
         "Under the expected value rule: " + ", ".join(f"{name(k)} in {v} of {K} seeds" for k, v in rep["decision"]["preferred"].items()) + ".", "",
         "Under the conservative rule (within the constraints in at least 90% of resamples): "
         + ", ".join(f"{name(k)} in {v} of {K}" for k, v in rep["decision"]["preferred_assured"].items()) + ".", "",
         "| Alternative | Preferred (share of seeds) | Preferred, conservative rule | Within the constraints (share of seeds) | Mean share of resamples within |",
         "|---|---:|---:|---:|---:|"]
    for r in rep["rows"]:
        L.append(f"| {r['label']} | {r['preferred_share']:.0%} | {r['preferred_assured_share']:.0%} | {r['feasible_share']:.0%} | {r['p_feasible_mean']:.2f} |")
    L += ["", "## The estimates and their intervals", "",
          "Two checks on what a single run reports. The spread of an estimate across seeds (its standard deviation) should equal the standard "
          "error a run reports: a ratio near one. And a run's 95% interval should contain the truth 95% of the time; the truth is not known, "
          f"so the mean of the other {K - 1} seeds stands in for it, and because that mean is itself an estimate a perfectly calibrated "
          f"interval would contain it about {exp:.0%} of the time.", ""]
    for q in QUANTITIES:
        L += [f"**{LABEL[q][0].upper() + LABEL[q][1:]}**", "",
              "| Alternative | Pooled mean | SD across seeds | Mean reported SE | Ratio | Interval contains the mean of the other seeds |",
              "|---|---:|---:|---:|---:|---:|"]
        f = (lambda v: f"{v:.2%}") if q == "cat_cmc" else (lambda v: f"{v:,.2f}")
        for r in rep["rows"]:
            x = r[q]
            if r["policy"] == "baseline" and q != "cat_cmc":
                continue
            ratio = f"{x['se_ratio']:.2f}" if x["se_ratio"] is not None else "n/a"
            L.append(f"| {r['label']} | {f(x['pooled_mean'])} | {f(x['sd_across_seeds'])} | {f(x['mean_reported_se'])} | {ratio} | "
                     f"{x['covered']} of {x['of']} |")
        c = rep["coverage_overall"][q]
        L += ["", f"Overall: {c['covered']} of {c['of']} intervals ({c['coverage']:.0%}) contain the mean of the other seeds, against about "
                  f"{exp:.0%} for a perfectly calibrated interval.", ""]
    L += ["The intervals of one alternative across seeds are independent; those of different alternatives within a seed are not (they share "
          "the seed's random numbers), so the overall shares are descriptive and carry no test."]
    return "\n".join(L) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--question", default=DEFAULT_QUESTION)
    ap.add_argument("--seeds", type=int, default=20)
    ap.add_argument("--first-seed", type=int, default=1)
    ap.add_argument("--paths", type=int, default=480)
    ap.add_argument("--horizon", type=int, default=None, help="months; default: read from the question, else 60")
    ap.add_argument("--boot", type=int, default=500)
    ap.add_argument("--out", default=None, help="write the JSON report here (a .md beside it carries the tables)")
    args = ap.parse_args(argv)

    def progress(k, n, rec):
        print(f"seed {rec['seed']} ({k} of {n}): preferred {rec['preferred']}, conservative {rec['preferred_assured']}, {rec['seconds']}s", flush=True)
    rep = replicate(args.question, args.seeds, args.paths, args.horizon, args.first_seed, args.boot, progress=progress)
    md = markdown(rep)
    print("\n" + md)
    if args.out:
        os.makedirs(os.path.dirname(os.path.abspath(args.out)) or ".", exist_ok=True)
        with open(args.out, "w") as f:
            json.dump(rep, f, indent=1)
        with open(os.path.splitext(args.out)[0] + ".md", "w") as f:
            f.write(md)
        print("written:", args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
