"""The run pipeline: one approved battery, from simulation to the critic.

Stages, each reported to the rail and the ledger:
  simulate    every policy on the shared random numbers; the representative
              path streams to the wire and the price panel as it runs
  markets     industry and firm value changes, the index paths
  welfare     the social ledger and the decision metrics (evaluate)
  assurance   tornado, structural variants, red team, analogue event study
  critic      independent recomputation of every figure from the stored paths

Artefacts (run directory):
  battery.json       the approved battery (policies, firms, assumptions, horizon, paths, seed) and its hash
  assumptions.json   the declared assumptions
  paths.npz          per policy aggregates, per path and month (the critic's and the tornado's input)
  paths.json         per policy, per path welfare components
  results.json       the scoring (evaluate)
  news_sample.json   the representative path's wire per policy, with its summary
  prices_sample.json representative and mean price paths per policy
  assurance.json     the assurance report
  artefacts.json     everything the briefing may cite, in one document
  critic.json        the critic's report
"""

import json
import os
import time

import numpy as np

from . import __version__, provenance
from . import assumptions as AS
from . import assurance as ASR
from . import welfare as W
from .economy import Economy, battery_hash
from .evaluate import evaluate
from .ledger import NumpyEncoder, plain
from .news import WireComposer, wire_summary
from .policies import library_policy, validate_policy
from .firms import default_firms


class SimulationStopped(Exception):
    pass


def make_battery(plan, firms=None, assumptions=None, budget=None, custom_policies=None, seed=7, profile="full"):
    """plan: output of question.parse plus optional overrides. Returns the battery document."""
    budget = budget or {"paths": 240, "horizon": 60}
    pols = []
    custom = {p["name"]: p for p in (custom_policies or [])}
    for n in plan["policies"]:
        pol = library_policy(n) or custom.get(n)
        if pol is None:
            continue
        pols.append(pol)
    for n, p in custom.items():
        if n not in [x["name"] for x in pols]:
            pols.append(p)
    firms = firms or default_firms()
    a, notes = AS.validate(assumptions or {})
    horizon = int(plan.get("horizon_months") or budget["horizon"])
    bat = {"question": plan["question"], "constraints": plan["constraints"], "policies": pols, "firms": firms,
           "assumptions": a, "assumption_notes": notes, "horizon": horizon, "paths": int(budget["paths"]),
           "seed": int(seed), "profile": profile, "budget": budget, "reading": plan.get("notes", []),
           "psl_version": __version__}
    bat["hash"] = battery_hash({k: bat[k] for k in ("question", "constraints", "policies", "firms", "assumptions",
                                                      "horizon", "paths", "seed")})
    bat["assumptions_hash"] = AS.assumptions_hash(a)
    return bat


def run_battery(bat, outdir, log=None, progress=None, stream=None, stop=None, start_year=2027, start_month=1,
                datasets=None):
    """Run an approved battery. `log(event, **payload)` writes the ledger; `progress(step, phase, **kw)` drives the
    rail; `stream(kind, payload)` feeds the live panels; `stop()` returns True to halt."""
    log = log or (lambda *a, **k: None)
    progress = progress or (lambda *a, **k: None)
    os.makedirs(outdir, exist_ok=True)
    t_start = time.time()
    a = bat["assumptions"]
    firms = bat["firms"]
    policies = {p["name"]: p for p in bat["policies"]}
    H, N, seed = bat["horizon"], bat["paths"], bat["seed"]
    budget = bat.get("budget", {})
    eco = Economy(firms, a, horizon=H, n_paths=N, seed=seed)
    log("battery_started", n_policies=len(policies), horizon=H, paths=N, seed=seed, battery_hash=bat["hash"],
        assumptions_hash=bat["assumptions_hash"])

    # ---------------------------------------------------------------- simulate --
    results, wires, timings = {}, {}, {}
    for i, (name, pol) in enumerate(policies.items()):
        if stop and stop():
            raise SimulationStopped("stopped before " + name)
        progress("simulate", f"Simulating {pol['label']} ({i + 1} of {len(policies)}): {N} paths, {H} months", policy=name)
        wc = WireComposer(eco.labels, pol["label"], start_year, start_month, seed=seed + i)
        wire = []

        def _stream(t, payload, _wc=wc, _wire=wire, _name=name):
            heads = _wc.month(t, payload["events"])
            _wire.extend(heads)
            if stream:
                stream("tick", {"policy": _name, "t": t, "date": _wc.date(t), "prices": payload["prices"],
                                "headlines": heads, "pressure": payload["pressure"], "trust": payload["trust"],
                                "enforcement": payload["enforcement"], "service": payload["service"]})
            if stop and stop() and t % 6 == 0:
                raise SimulationStopped("stopped during " + _name)
        t0 = time.time()
        res = eco.run(pol, stream=_stream)
        timings[name] = time.time() - t0
        results[name] = res
        wires[name] = wire
        summ = wire_summary(wire)
        log("policy_simulated", policy=name, seconds=round(timings[name], 2), headlines=summ.get("headlines", 0),
            incidents_per_year=float(res.incidents.sum() / N / (H / 12)),
            p_catastrophe=float(res.catastrophe.any(axis=(1, 2)).mean()))
        if stream:
            stream("policy_done", {"policy": name, "label": pol["label"], "headlines": summ.get("headlines", 0),
                                   "share_negative": summ.get("share_negative", 0.0),
                                   "price_end": res.prices[0, -1, :].tolist(),
                                   "mean_price_end": res.prices[:, -1, :].mean(axis=0).tolist()})

    # ------------------------------------------------------- markets and welfare --
    progress("markets", "Pricing the industry: value changes, index paths, early reactions")
    progress("welfare", "Social ledger and decision metrics, with the bootstrap")
    constraints = dict(bat.get("constraints") or {})
    # reference quantities for percentage constraints
    base_agg = W.aggregates(results["baseline"], a)
    d = W.discount(H, a["discount_rate"])
    constraints["_harm_base_npv"] = float((base_agg["harm"] * d).sum(axis=1).mean() * a["harm_valuation_multiplier"])
    constraints["_cs_base_npv"] = float((a["consumer_surplus_base_bn"] / 12.0) * ((base_agg["service"] ** a["cs_elasticity"]) * d).sum(axis=1).mean())
    ev, comps, aggs = evaluate(results, a, constraints, boot=int(budget.get("boot", 300)), seed=seed + 101)
    log("battery_evaluated", preferred=ev["preferred"], best_unconstrained=ev["best_unconstrained"],
        decision_gap=ev["decision_gap"]["decision_gap"], winner_stability=ev["winner_stability"])
    if stream:
        stream("evaluated", {"preferred": ev["preferred"]})

    # ------------------------------------------------------------- assurance --
    pref = ev["preferred"] or ev["best_unconstrained"]
    # the assurance stages pick "best" among the instruments that satisfied the question's constraints in the
    # main run, so a change of best option means a change of the decision, not of the unconstrained ranking
    cands = [r["policy"] for r in ev["policies"] if r["policy"] != "baseline" and (r["feasible"] or ev["preferred"] is None)]
    vp = int(budget.get("variant_paths", 80)); rp = int(budget.get("redteam_paths", 80))
    progress("assurance", "Tornado: every value judgement to its low and high value")
    torn = ASR.tornado(aggs, a, policies, firms, H, pref, paths=vp, seed=seed, candidates=cands,
                       progress=lambda k: progress("assurance", f"Tornado: {k}")) if budget.get("tornado", True) else None
    if stop and stop():
        raise SimulationStopped("stopped before the structural variants")
    progress("assurance", "Structural variants: the battery under alternative model structures")
    struct = ASR.structural(policies, firms, a, H, pref, paths=vp, seed=seed, aggs=aggs, candidates=cands,
                            progress=lambda k: progress("assurance", f"Structural variant: {k}"))
    if stop and stop():
        raise SimulationStopped("stopped before the red team")
    progress("assurance", "Red team: firms game every instrument")
    red = ASR.red_team(policies, firms, a, H, paths=rp, seed=seed,
                       progress=lambda k: progress("assurance", f"Red team: {k}"))
    analog = _analogue_from_datasets(datasets, ev)
    assurance = {"tornado": torn, "structural": struct, "red_team": red, "analogue": analog,
                 "budget": {"variant_paths": vp, "redteam_paths": rp}}
    log("assurance_complete", tornado_flips=(torn or {}).get("flips"), structural_survival=struct["survival"],
        red_team_most_robust=red["most_robust"])

    # -------------------------------------------------------------- artefacts --
    progress("critic", "Writing artefacts")
    news_sample = {n: {"wire": wires[n], "summary": wire_summary(wires[n])} for n in policies}
    prices_sample = {n: {"representative": results[n].prices[0].T.tolist(),
                         "mean": results[n].prices.mean(axis=0).T.tolist(),
                         "labels": results[n].labels, "cap0": results[n].cap0.tolist(),
                         "series": {k: results[n].series[k][0].tolist() for k in ("pressure", "trust", "enforcement", "service")}}
                     for n in policies}
    np.savez_compressed(os.path.join(outdir, "paths.npz"),
                        **{f"{n}__{k}": np.asarray(v) for n, agg in aggs.items() for k, v in agg.items()
                           if isinstance(v, np.ndarray)})
    paths_json = {n: {k: np.asarray(v).tolist() for k, v in comps[n].items() if isinstance(v, np.ndarray) and k != "industry_shareholder_value"}
                  | {"industry_shareholder_value": np.asarray(comps[n]["industry_shareholder_value"]).tolist(),
                     "transfers": {k: np.asarray(v).tolist() for k, v in comps[n]["transfers"].items()}}
                  for n in policies}
    arte = {
        "run": {"started": t_start, "elapsed_s": round(time.time() - t_start, 1), "timings_s": {k: round(v, 2) for k, v in timings.items()}},
        "question": bat["question"], "reading": bat.get("reading", []), "constraints": bat.get("constraints", {}),
        "battery_hash": bat["hash"], "assumptions_hash": bat["assumptions_hash"], "horizon": H, "paths": N, "seed": seed,
        "profile": bat.get("profile"), "policies": {n: p for n, p in policies.items()}, "firms": firms,
        "assumptions": a, "assumption_table": AS.table(a),
        "results": ev, "news": {n: news_sample[n]["summary"] for n in policies}, "assurance": assurance,
        "provenance": provenance(), "start_year": start_year, "start_month": start_month,
        "baseline_reference": {"harm_npv": constraints["_harm_base_npv"], "cs_npv": constraints["_cs_base_npv"]},
    }
    arte = plain(arte)
    _write(outdir, "battery.json", bat)
    _write(outdir, "assumptions.json", {"assumptions": a, "table": AS.table(a), "hash": bat["assumptions_hash"]})
    _write(outdir, "results.json", ev)
    _write(outdir, "news_sample.json", news_sample)
    _write(outdir, "prices_sample.json", prices_sample)
    _write(outdir, "assurance.json", assurance)
    _write(outdir, "paths.json", paths_json)
    _write(outdir, "artefacts.json", arte)
    log("artefacts_written", files=["battery.json", "assumptions.json", "paths.npz", "paths.json", "results.json",
                                    "news_sample.json", "prices_sample.json", "assurance.json", "artefacts.json"])
    return arte, results


def _write(outdir, name, obj):
    tmp = os.path.join(outdir, name + ".tmp")
    with open(tmp, "w") as f:
        json.dump(obj, f, indent=1, cls=NumpyEncoder)
    os.replace(tmp, os.path.join(outdir, name))


def _analogue_from_datasets(datasets, ev):
    """Event studies on uploaded price series, compared with the model's early reaction."""
    out = []
    for ds in datasets or []:
        es = ds.get("event_study")
        if not es:
            continue
        rows = []
        for r in ev["policies"]:
            if r["policy"] == "baseline":
                continue
            m = r["market"]
            rows.append({"policy": r["policy"], "model_early_reaction": m["early_reaction"]["mean"],
                         "lo": m["early_reaction"]["lo"], "hi": m["early_reaction"]["hi"],
                         "within_band": m["early_reaction"]["lo"] <= es["car"] <= m["early_reaction"]["hi"]})
        closest = min(rows, key=lambda x: abs(x["model_early_reaction"] - es["car"])) if rows else None
        out.append({"dataset": ds.get("name"), "classification": ds.get("classification"), "event_study": es,
                    "rows": rows, "closest_policy": closest["policy"] if closest else None,
                    "note": ds.get("note", "")})
    return out
