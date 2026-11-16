"""The run pipeline: one approved battery, from simulation to the critic.

Stages, each reported to the rail and the ledger:
  simulate    every policy on the shared random numbers; the representative
              path streams to the wire and the price panel as it runs. The
              battery then grows by doubling, on the same streams, until the
              declared precision targets are met or the declared ceiling on
              paths is reached (adaptive sampling); what is still short of its
              target at the ceiling is reported, never hidden.
  markets     industry and firm value changes, the index paths
  welfare     the social ledger and the decision (evaluate)
  assurance   the screen of every assumption, the joint draw, the variance
              decomposition, structural variants, red team, batches,
              the validation of the market reaction against uploaded events
  critic      independent recomputation of every figure from the stored paths

Artefacts (run directory):
  battery.json       the approved battery (policies, firms, assumptions, horizon, the sampling plan, seed) and its hash
  assumptions.json   the declared assumptions with their plausible ranges
  paths.npz          per policy reduced paths, per path and month (the critic's input; single precision)
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
from . import benchmarks as BM
from . import validation as V
from . import reuse as RU
from . import welfare as W
from .economy import battery_hash
from .evaluate import evaluate, precision
from .firms import default_firms
from .ledger import NumpyEncoder, plain
from .mechanisms import register as mechanism_register
from .news import WireComposer, wire_summary
from .policies import library_policy, validate_policy  # noqa: F401
from .reduce import STORED, concat, simulate_battery
from .validation import compare as validate_events

HASHED = ("question", "constraints", "policies", "firms", "assumptions", "horizon", "paths", "max_paths", "precision", "seed", "evidence")
DEFAULT_PRECISION = {"nsv_gap_bn": 5.0, "p_catastrophe_halfwidth": 0.03}


class SimulationStopped(Exception):
    pass


def make_battery(plan, firms=None, assumptions=None, budget=None, custom_policies=None, seed=7, profile="full", benchmarks=None):
    """plan: output of question.parse plus optional overrides. Returns the battery document."""
    budget = dict(budget or {"paths": 480, "horizon": 60})
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
    paths = int(budget["paths"])
    bat = {"question": plan["question"], "constraints": plan["constraints"], "policies": pols, "firms": firms,
           "assumptions": a, "assumption_notes": notes, "horizon": horizon, "paths": paths,
           "max_paths": int(max(paths, budget.get("max_paths", paths))),
           "precision": dict(DEFAULT_PRECISION, **(budget.get("precision") or {})),
           "seed": int(seed), "profile": profile, "budget": budget,
           "reading": [n for n in plan.get("notes", []) if not n.startswith("NOT read")], "unread": list(plan.get("unread") or []),
           "psl_version": __version__}
    # the evidence base the validation layer confronts the model with: part of what Gate 1 approves
    bat["benchmarks"] = [dict(b) for b in (BM.load() if benchmarks is None else benchmarks)]
    bat["evidence"] = BM.digest(bat["benchmarks"])
    bat["hash"] = battery_hash({k: bat[k] for k in HASHED})
    bat["assumptions_hash"] = AS.assumptions_hash(a)
    return bat


def reference_constraints(constraints, reds, a, d_f):
    """The question's constraints with the two status quo reference values the percentage constraints are measured
    against (the present value of expected harm and of consumer surplus under the status quo)."""
    cons = dict(constraints or {})
    B = reds["baseline"]
    cons["_harm_base_npv"] = float((B["harm_exp"] * d_f).sum(axis=1).mean() * a["harm_valuation_multiplier"])
    cons["_cs_base_npv"] = float((a["consumer_surplus_base_bn"] / 12.0) * ((B["service"] ** a["cs_elasticity"]) * d_f).sum(axis=1).mean())
    return cons


def hash_of(bat):
    """The battery hash recomputed from the document (the critic's check); batteries written before the sampling
    plan was part of the hash are hashed on the fields they have."""
    return battery_hash({k: bat[k] for k in HASHED if k in bat})


def run_battery(bat, outdir, log=None, progress=None, stream=None, stop=None, start_year=2027, start_month=1,
                datasets=None, reuse=False):
    """Run an approved battery. `log(event, **payload)` writes the ledger; `progress(step, phase, **kw)` drives the
    rail; `stream(kind, payload)` feeds the live panels; `stop()` returns True to halt. With `reuse`, a battery
    whose key matches a completed run in the same registry is not simulated again (reuse.py): its figures are
    copied, its recorded stream replayed, and the second value returned is None instead of the reduced paths."""
    log = log or (lambda *a, **k: None)
    progress = progress or (lambda *a, **k: None)
    os.makedirs(outdir, exist_ok=True)
    t_start = time.time()
    rkey = RU.key(bat, datasets, start_year, start_month)
    if reuse:
        hit = RU.find(os.path.dirname(os.path.abspath(outdir)), rkey, exclude=outdir)
        if hit:
            return _replay(bat, outdir, hit, rkey, log, progress, stream, stop, start_year, start_month, t_start), None
    a = bat["assumptions"]
    firms = bat["firms"]
    policies = {p["name"]: p for p in bat["policies"]}
    labels = {n: p["label"] for n, p in policies.items()}
    H, N0, seed = bat["horizon"], bat["paths"], bat["seed"]
    n_max = int(bat.get("max_paths", N0))
    targets = dict(DEFAULT_PRECISION, **(bat.get("precision") or {}))
    budget = bat.get("budget", {})
    chunk = int(budget.get("chunk", 480))
    d_f = W.discount(H, a["discount_rate"])
    log("battery_started", n_policies=len(policies), horizon=H, paths=N0, max_paths=n_max, precision=targets, seed=seed,
        battery_hash=bat["hash"], assumptions_hash=bat["assumptions_hash"])

    def halted():
        return bool(stop and stop())

    # ---------------------------------------------------------------- simulate --
    wires, timings, composers = {}, {}, {}
    order = list(policies)

    def make_stream(name, i):
        wc = WireComposer([f["label"] for f in firms], policies[name]["label"], start_year, start_month, seed=seed + i)
        composers[name] = wc
        wires[name] = []

        def _stream(t, payload):
            heads = wc.month(t, payload["events"])
            wires[name].extend(heads)
            if stream:
                stream("tick", {"policy": name, "t": t, "date": wc.date(t), "prices": payload["prices"],
                                "headlines": heads, "pressure": payload["pressure"], "trust": payload["trust"],
                                "enforcement": payload["enforcement"], "service": payload["service"]})
            if stop and stop() and t % 6 == 0:
                raise SimulationStopped("stopped during " + name)
        return _stream

    def before(name):
        if halted():
            raise SimulationStopped("stopped before " + name)
        progress("simulate", f"Simulating {policies[name]['label']} ({order.index(name) + 1} of {len(order)}): {min(N0, chunk)} paths, {H} months",
                 policy=name)

    def after(name, R, seconds):
        timings[name] = seconds
        summ = wire_summary(wires[name])
        log("policy_simulated", policy=name, seconds=round(seconds, 2), headlines=summ.get("headlines", 0),
            incidents_per_year=float(R["n_incidents"].sum() / R["n_paths"] / (H / 12)),
            p_catastrophe=float(R["cat_cmc"].mean()))
        if stream:
            stream("policy_done", {"policy": name, "label": policies[name]["label"], "headlines": summ.get("headlines", 0),
                                   "share_negative": summ.get("share_negative", 0.0),
                                   "price_end": R["rep"]["prices"][-1, :].tolist(),
                                   "mean_price_end": (R["price_sum"][-1, :] / R["n_paths"]).tolist()})

    reds = simulate_battery(policies, firms, a, H, N0, seed, chunk=chunk, discount_f=d_f, stop=stop, moments=True,
                            streams={name: make_stream(name, i) for i, name in enumerate(order)}, before=before, after=after)
    if halted() or len(reds) < len(policies):
        raise SimulationStopped("stopped during the simulation")

    # ------------------------------------------- markets, welfare, adaptive sampling --
    progress("markets", "Pricing the industry: value changes, index paths, early reactions")
    boot_b = int(budget.get("boot", 1000))
    N = N0
    schedule = [N0]

    def score():
        cons = reference_constraints(bat.get("constraints"), reds, a, d_f)
        return evaluate(reds, a, cons, boot=boot_b, seed=seed + 101, labels=labels), cons

    looks = []
    while True:
        progress("welfare", f"Social ledger and the decision on {N} paths, with the bootstrap")
        (ev, arr, bt), constraints = score()
        open_items = precision(ev, targets)
        looks.append(_look(ev, N, open_items))
        if not open_items or N >= n_max:
            break
        if halted():
            raise SimulationStopped("stopped before more paths were added")
        add = int(min(N, n_max - N))
        what = "; ".join(x["text"] for x in open_items[:2])
        progress("simulate", f"Adaptive sampling: {N} to {N + add} paths ({len(open_items)} estimate{'s' if len(open_items) != 1 else ''} "
                             f"short of the precision target: {what})")
        log("paths_added", from_paths=N, to_paths=N + add, unresolved=[x["text"] for x in open_items])
        more = simulate_battery(policies, firms, a, H, add, seed, start=N, chunk=chunk, discount_f=d_f, stop=stop, moments=True)
        if halted() or len(more) < len(policies):
            raise SimulationStopped("stopped while adding paths")
        for name in policies:
            reds[name] = concat([reds[name], more[name]])
        N += add
        schedule.append(N)
    ev["precision"] = {"targets": targets, "initial_paths": N0, "max_paths": n_max, "paths": N, "schedule": schedule,
                       "met": not open_items, "unresolved": open_items, "looks": looks,
                       "note": "paths double on the same random streams until every target is met or the ceiling is reached; "
                               "the intervals are not adjusted for the sequential looks, which are at most "
                               f"{max(1, int(np.ceil(np.log2(max(n_max / max(N0, 1), 1)))) + 1)}"}
    log("battery_evaluated", preferred=ev["preferred"], best_intervention=ev["best_intervention"], best_unconstrained=ev["best_unconstrained"],
        decision_gap=ev["decision_gap"]["decision_gap"], winner_stability=ev["winner_stability"], paths=N,
        precision_met=ev["precision"]["met"], unresolved=[x["text"] for x in open_items])
    if stream:
        stream("evaluated", {"preferred": ev["preferred"] or ev["focus"]})

    # ------------------------------------------------------------- assurance --
    focus = ev["focus"]
    names = list(policies)
    mech_ids = [m["id"] for m in mechanism_register()]
    bench, bench_problems = BM.validate(bat.get("benchmarks") or [], mechanism_ids=mech_ids, assumption_keys=set(AS.SPEC), moments=V.MOMENTS)
    extra_pol = {n: library_policy(n) for n in V.instruments_needed(bench) if n not in policies and library_policy(n)}
    per_draw = None
    vp = int(budget.get("variant_paths", 80)); rp = int(budget.get("redteam_paths", 80))
    sp = int(budget.get("screen_paths", 8)); jd_n = int(budget.get("joint_draws", 64)); jp = int(budget.get("joint_paths", 8))
    dchunk = int(budget.get("design_chunk", 960))
    scr = jd = var = None
    if budget.get("tornado", True) and focus:
        progress("assurance", f"Screen: every one of {len(AS.RANGE)} assumptions to the ends of its plausible range")
        scr = ASR.screen(reds, arr, a, policies, firms, H, focus, constraints, paths=sp, seed=seed, chunk=dchunk,
                         progress=lambda k: progress("assurance", f"Screen: {k}"))
        if halted():
            raise SimulationStopped("stopped before the joint draw")
        progress("assurance", f"Joint draw: {jd_n} draws of all the assumptions together")
        jd = ASR.joint_draw(reds, arr, a, policies, firms, H, focus, constraints, draws=jd_n, paths=jp, seed=seed, chunk=dchunk,
                            progress=lambda k: progress("assurance", f"Joint draw: {k}"), extra_policies=extra_pol,
                            on_design=(lambda dreds, S, D: V.draw_moments(bench, dreds, S, dict(policies, **extra_pol), H, D)) if bench else None)
        per_draw = jd.pop("_per_draw", None)
        if halted():
            raise SimulationStopped("stopped before the variance decomposition")
        k_top = int(budget.get("sobol_k", 6))
        if k_top >= 2 and int(budget.get("sobol_base", 32)) > 0:
            keys = [r["assumption"] for r in scr["rows"][:k_top]]
            ranked = sorted((r for r in ev["policies"] if r["policy"] not in ("baseline", focus) and r["feasible"]),
                            key=lambda r: -r["net_social_value"]["mean"])
            challengers = [r["policy"] for r in ranked[:2]]
            progress("assurance", f"Variance decomposition over the {len(keys)} most influential assumptions")
            var = ASR.variance_decomposition(reds, arr, a, policies, firms, H, focus, keys, base=int(budget.get("sobol_base", 32)),
                                             paths=int(budget.get("sobol_paths", 4)), seed=seed, chunk=dchunk, challengers=challengers,
                                             progress=lambda k: progress("assurance", f"Variance: {k}"))
    if halted():
        raise SimulationStopped("stopped before the structural variants")
    struct = red = None
    if focus:
        progress("assurance", "Structural variants: the battery under alternative model structures")
        struct = ASR.structural(reds, arr, a, policies, firms, H, focus, constraints, paths=vp, seed=seed, chunk=chunk,
                                preferred=ev["preferred"], progress=lambda k: progress("assurance", f"Structural variant: {k}"))
        if halted():
            raise SimulationStopped("stopped before the red team")
        progress("assurance", "Red team: firms game every instrument")
        red = ASR.red_team(reds, arr, a, policies, firms, H, constraints, paths=rp, seed=seed, chunk=chunk,
                           progress=lambda k: progress("assurance", f"Red team: {k}"))
    bat_rep = ASR.batches(names, arr, constraints, k=int(budget.get("batches", 4)))
    conv = ASR.convergence(names, arr, constraints, focus) if focus else None
    events, coverage = validate_events(datasets, ev, reds, firms)
    # the validation layer: every benchmark against the model at its central assumptions, then the joint draws weighted
    # by the benchmarks. An instrument a benchmark is defined under and the battery lacks runs beside it on the first paths.
    bench_rep = None
    if bench:
        progress("assurance", f"Validation: {len(bench)} published benchmarks against the model")
        vreds = dict(reds)
        if extra_pol:
            n_ref = int(min(N, max(vp, 120)))
            vreds.update(simulate_battery(extra_pol, firms, a, H, n_ref, seed, chunk=chunk, full=False, discount_f=d_f, moments=True))
        vrows = V.central(bench, vreds, a, dict(policies, **extra_pol), H)
        calib = (V.calibrate(bench, vrows, per_draw, names, focus, a, AS.RANGE, accounting_only=AS.WELFARE_ONLY)
                 if per_draw and per_draw.get("moments") else None)
        mech = V.by_mechanism(vrows, mech_ids)
        bench_rep = {"rows": vrows, "summary": V.summarise(vrows, mech), "mechanisms": mech, "calibration": calib,
                     "evidence_hash": bat.get("evidence"), "problems": bench_problems,
                     "sources": {b["id"]: {"sources": b["sources"], "mapping": b.get("mapping"), "caveat": b.get("caveat"),
                                           "observations": b["observations"], "se_basis": b.get("se_basis"),
                                           "transport_basis": b.get("transport_basis")} for b in bench},
                     "not_used": [dict(x) for x in BM.NOT_USED],
                     "extra_instruments": sorted(extra_pol),
                     "thresholds": {"tension": 2.0, "contradicted": 3.0, "min_defined": V.MIN_DEFINED, "min_ess": V.MIN_ESS, "form_z": V.FORM_Z,
                                    "rule_out": V.RULE_OUT}}
    assurance = {"screen": scr, "tornado": ASR.tornado_view(scr) if scr else None, "joint": jd, "variance": var,
                 "structural": struct, "red_team": red, "batches": bat_rep, "convergence": conv,
                 "robustness": ASR.robustness(ev, scr, jd, struct, red),
                 "validation": {"events": events, "coverage": coverage, "benchmarks": bench_rep,
                                "note": "published benchmarks are confronted with the model's moments and weight the joint draws; an uploaded "
                                        "price series tests the market's early reaction; mechanisms with no benchmark are listed as unconfronted"},
                 "budget": {"variant_paths": vp, "redteam_paths": rp, "screen_paths": sp, "joint_draws": jd_n, "joint_paths": jp}}
    if bench_rep:
        sm, cb = bench_rep["summary"], bench_rep["calibration"] or {}
        log("validation_complete", benchmarks=sm["benchmarks"], scored=sm["scored"], in_tension=sm["in_tension"], contradicted=sm["contradicted"],
            mechanisms_confronted=len(sm["mechanisms_confronted"]), effective_draws=cb.get("ess"), evidence_hash=bat.get("evidence"))
    log("assurance_complete", screen_flips=(scr or {}).get("flips"), joint_p_focus_best=(jd or {}).get("p_focus_best"),
        structural_survival=(struct or {}).get("survival"), red_team_most_robust=(red or {}).get("most_robust"),
        batches_agree=(bat_rep or {}).get("agree"), robustly_acceptable=assurance["robustness"]["robustly_acceptable"])

    # -------------------------------------------------------------- artefacts --
    progress("critic", "Writing artefacts")
    news_sample = {n: {"wire": wires[n], "summary": wire_summary(wires[n])} for n in policies}
    prices_sample = {n: {"representative": reds[n]["rep"]["prices"].T.tolist(),
                         "mean": (reds[n]["price_sum"] / reds[n]["n_paths"]).T.tolist(),
                         "labels": reds[n]["labels"], "cap0": reds[n]["cap0"].tolist(),
                         "series": {k: reds[n]["rep"]["series"][k].tolist() for k in ("pressure", "trust", "enforcement", "service")}}
                     for n in policies}
    np.savez_compressed(os.path.join(outdir, "paths.npz"),
                        **{f"{n}__{k}": np.asarray(reds[n][k], dtype=np.float32) for n in policies for k in STORED})
    per_path = ("net_social_value", "net_social_value_drawn", "harm_avoided_drawn", "industry_value_change", "industry_value_change_drawn",
                "cat_cmc", "cat_any", "major_any") + W.COMPONENTS
    paths_json = {n: {k: np.round(np.asarray(arr[n][k], dtype=float), 4).tolist() for k in per_path}
                  | {"transfers": {k: np.round(np.asarray(v, dtype=float), 4).tolist() for k, v in arr[n]["transfers"].items()}}
                  for n in policies}
    arte = {
        "run": {"started": t_start, "elapsed_s": round(time.time() - t_start, 1), "timings_s": {k: round(v, 2) for k, v in timings.items()}},
        "question": bat["question"], "reading": bat.get("reading", []), "unread_conditions": bat.get("unread", []),
        "constraints": bat.get("constraints", {}),
        "battery_hash": bat["hash"], "assumptions_hash": bat["assumptions_hash"], "horizon": H, "paths": N,
        "initial_paths": N0, "max_paths": n_max, "seed": seed,
        "profile": bat.get("profile"), "policies": {n: p for n, p in policies.items()}, "firms": firms,
        "assumptions": a, "assumption_table": AS.table(a),
        "results": ev, "news": {n: news_sample[n]["summary"] for n in policies}, "assurance": assurance,
        "mechanisms": _register_with_evidence(bench_rep), "accounting_map": list(W.ACCOUNT_MAP), "constants": dict(AS.CONSTANTS),
        "evidence_hash": bat.get("evidence"),
        "correlated_assumptions": [{"assumptions": list(g), "correlation": r, "why": why} for g, r, why in AS.CORRELATED],
        "provenance": provenance(), "start_year": start_year, "start_month": start_month,
        "baseline_reference": {"harm_npv": constraints["_harm_base_npv"], "cs_npv": constraints["_cs_base_npv"]},
    }
    arte = plain(arte)
    _write(outdir, "battery.json", bat)
    _write(outdir, "assumptions.json", {"assumptions": a, "table": AS.table(a), "hash": bat["assumptions_hash"]})
    _write(outdir, "results.json", arte["results"])
    _write(outdir, "news_sample.json", news_sample)
    _write(outdir, "prices_sample.json", prices_sample)
    _write(outdir, "assurance.json", arte["assurance"])
    _write(outdir, "paths.json", paths_json)
    _write(outdir, "artefacts.json", arte)
    log("artefacts_written", files=["battery.json", "assumptions.json", "paths.npz", "paths.json", "results.json",
                                    "news_sample.json", "prices_sample.json", "assurance.json", "artefacts.json"])
    RU.record(outdir, rkey, bat)
    return arte, reds


def _replay(bat, outdir, hit, rkey, log, progress, stream, stop, start_year, start_month, t_start):
    """The run for a battery already computed under the same key: copy the figures, replay the recorded stream."""
    src, mark = hit
    with open(os.path.join(src, "artefacts.json")) as f:
        arte = json.load(f)
    with open(os.path.join(src, "battery.json")) as f:
        if hash_of(json.load(f)) != bat["hash"]:
            raise ValueError("reuse: the stored battery does not hash to the approved one")
    source = mark.get("source") or os.path.basename(src)
    log("battery_started", n_policies=len(bat["policies"]), horizon=bat["horizon"], paths=bat["paths"], max_paths=bat.get("max_paths"),
        precision=bat.get("precision"), seed=bat["seed"], battery_hash=bat["hash"], assumptions_hash=bat["assumptions_hash"])
    log("battery_reused", source_run=source, key=rkey, computed=arte["run"].get("started"),
        note="identical approved battery, code, libraries and uploaded series: the stored figures are copied, not simulated again")
    RU.copy(src, outdir)
    with open(os.path.join(outdir, "news_sample.json")) as f:
        news = json.load(f)
    with open(os.path.join(outdir, "prices_sample.json")) as f:
        prices = json.load(f)
    firms = bat["firms"]
    H = bat["horizon"]
    order = [p["name"] for p in bat["policies"]]
    labels = {p["name"]: p["label"] for p in bat["policies"]}
    progress("simulate", f"Identical to run {source} (same battery hash, same code): replaying its recorded stream; the critic recomputes the figures")
    for i, name in enumerate(order):
        if stop and stop():
            raise SimulationStopped("stopped during " + name)
        progress("simulate", f"Replaying {labels[name]} ({i + 1} of {len(order)})", policy=name)
        if stream:
            wc = WireComposer([f["label"] for f in firms], labels[name], start_year, start_month, seed=bat["seed"] + i)
            by_month = {}
            for h in news[name]["wire"]:
                by_month.setdefault(int(h["t"]), []).append(h)
            rep, ser = prices[name]["representative"], prices[name]["series"]
            for t in range(H):
                stream("tick", {"policy": name, "t": t, "date": wc.date(t), "prices": [row[t + 1] for row in rep],
                                "headlines": by_month.get(t, []), "pressure": ser["pressure"][t], "trust": ser["trust"][t],
                                "enforcement": ser["enforcement"][t], "service": ser["service"][t]})
                if stop and stop() and t % 6 == 0:
                    raise SimulationStopped("stopped during " + name)
            summ = news[name]["summary"]
            stream("policy_done", {"policy": name, "label": labels[name], "headlines": summ.get("headlines", 0),
                                   "share_negative": summ.get("share_negative", 0.0),
                                   "price_end": [row[-1] for row in rep], "mean_price_end": [row[-1] for row in prices[name]["mean"]]})
    ev = arte["results"]
    progress("markets", "Pricing the industry: value changes, index paths, early reactions (stored)")
    progress("welfare", f"Social ledger and the decision on {arte['paths']} paths (stored)")
    log("battery_evaluated", preferred=ev["preferred"], best_intervention=ev["best_intervention"], best_unconstrained=ev["best_unconstrained"],
        decision_gap=ev["decision_gap"]["decision_gap"], winner_stability=ev["winner_stability"], paths=arte["paths"],
        precision_met=ev["precision"]["met"], unresolved=[x["text"] for x in ev["precision"]["unresolved"]], reused_from=source)
    if stream:
        stream("evaluated", {"preferred": ev["preferred"] or ev["focus"]})
    progress("assurance", "Assurance: the stored screen, joint draw, variance decomposition, variants and red team")
    progress("critic", "Writing artefacts")
    arte["run"] = {"started": t_start, "elapsed_s": round(time.time() - t_start, 1), "timings_s": {},
                   "reused_from": {"run": source, "computed": arte["run"].get("started"), "computed_elapsed_s": arte["run"].get("elapsed_s"),
                                   "key": rkey}}
    arte["provenance"] = provenance()
    arte.pop("security", None)
    _write(outdir, "battery.json", bat)
    _write(outdir, "artefacts.json", arte)
    log("artefacts_written", files=["battery.json", "assumptions.json", "paths.npz", "paths.json", "results.json",
                                    "news_sample.json", "prices_sample.json", "assurance.json", "artefacts.json"], reused_from=source)
    RU.record(outdir, rkey, bat, source=source)
    return arte


def _register_with_evidence(bench_rep):
    """The mechanism register with, for each mechanism, the benchmarks of this run that bore on it."""
    reg = mechanism_register()
    by = {m["mechanism"]: m for m in (bench_rep or {}).get("mechanisms", [])}
    for m in reg:
        e = by.get(m["id"])
        m["benchmarks"] = e["benchmarks"] if e else []
        m["confronted"] = bool(e and e["confronted"])
        m["evidence"] = (e or {}).get("worst")
    return reg


def _look(ev, n, open_items):
    """What one look of the sampling plan saw: the decision, the focus option's estimate and what was unresolved."""
    by = {r["policy"]: r for r in ev["policies"]}
    f = by.get(ev["focus"]) if ev.get("focus") else None
    pc = by["baseline"]["safety"]["p_catastrophe_detail"]
    out = {"paths": int(n), "preferred": ev["preferred"], "best_intervention": ev["best_intervention"], "unresolved": len(open_items),
           "kinds": sorted({x["kind"] for x in open_items}),
           "p_catastrophe_status_quo": pc["p"], "p_catastrophe_halfwidth": 0.5 * (pc["ci_hi"] - pc["ci_lo"])}
    if f:
        nsv = f["net_social_value"]
        out.update(focus=ev["focus"], focus_nsv=nsv["mean"], focus_se=nsv["se"], focus_ci_lo=nsv["ci_lo"], focus_ci_hi=nsv["ci_hi"],
                   focus_p_feasible=f["p_feasible"])
    return out


def _write(outdir, name, obj):
    tmp = os.path.join(outdir, name + ".tmp")
    with open(tmp, "w") as f:
        json.dump(obj, f, indent=1, cls=NumpyEncoder)
    os.replace(tmp, os.path.join(outdir, name))
