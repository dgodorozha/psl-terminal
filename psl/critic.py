"""The critic: an independent recomputation of every figure the briefing
will cite, from the stored paths, before Gate 2 can arm.

It does not trust results.json. It reloads the reduced paths (paths.npz),
the assumptions and the battery, recomputes the welfare components, the
accounting identities, the decision with the status quo among the
alternatives, feasibility, the rankings, the decision gap and the
confidence intervals, and compares them with what the pipeline wrote. It
checks that the two estimators of every expected value (the conditional one
and the plain average of the draws) agree within their Monte Carlo error,
that the sampling plan was followed and that anything short of its
precision target is said so in the briefing. It then replays the ledger
chain and checks that every number in the briefing appears in the
artefacts.

The paths are stored in single precision; recomputed figures are compared
with a tolerance of 0.005 ($bn), far below the precision anything is
printed at.
"""

import json
import os
import re

import numpy as np

from . import assumptions as AS
from . import welfare as W
from .assurance import GAMING, STRUCTURAL
from .economy import battery_hash
from .evaluate import MEANS, decide
from .ledger import verify as ledger_verify
from .stats import Boot, kendall_tau_b

TOL = 1e-6
PTOL = 5e-3          # recomputation from single precision paths, $bn
MIN_EVENTS = 20      # paths with (and without) a catastrophe before a sample standard error is compared with anything
HASHED = ("question", "constraints", "policies", "firms", "assumptions", "horizon", "paths", "max_paths", "precision", "seed", "evidence")


def _same(x, y):
    """Two JSON documents are the same document."""
    return json.dumps(x, sort_keys=True) == json.dumps(y, sort_keys=True)


def _load_paths(run_dir):
    z = np.load(os.path.join(run_dir, "paths.npz"))
    reds = {}
    for key in z.files:
        n, k = key.split("__", 1)
        reds.setdefault(n, {})[k] = z[key].astype(np.float64)
    return reds


def critic_check(run_dir, secret=None, briefing_text=None):
    checks = []

    def check(name, ok, detail=""):
        checks.append({"check": name, "ok": bool(ok), "detail": str(detail)[:300]})

    def load(name):
        with open(os.path.join(run_dir, name)) as f:
            return json.load(f)

    try:
        bat = load("battery.json"); res = load("results.json"); arte = load("artefacts.json")
        asm = load("assumptions.json")
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "checks": [{"check": "artefacts present", "ok": False, "detail": str(e)}], "n_checks": 1, "n_failed": 1}
    a = asm["assumptions"]
    # 1 hashes
    h = battery_hash({k: bat[k] for k in HASHED if k in bat})
    check("battery hash reproduces", h == bat["hash"], f"{h[:12]} vs {bat['hash'][:12]}")
    check("assumptions hash reproduces", AS.assumptions_hash(a) == asm["hash"])
    check("artefacts cite the approved battery", arte["battery_hash"] == bat["hash"])
    # the briefing is drafted from artefacts.json; the figures recomputed below are compared with results.json, so the
    # two must be the same document, as must the assurance report and what was approved
    check("the artefacts carry the scored results unchanged", _same(arte.get("results"), res))
    try:
        check("the artefacts carry the assurance report unchanged", _same(arte.get("assurance"), load("assurance.json")))
    except Exception as e:  # noqa: BLE001
        check("assurance report readable", False, str(e))
    check("the artefacts carry the approved assumptions, instruments and firms",
          _same(arte.get("assumptions"), a) and _same(arte.get("policies"), {q["name"]: q for q in bat["policies"]})
          and _same(arte.get("firms"), bat["firms"]) and arte.get("assumptions_hash") == asm["hash"] == bat.get("assumptions_hash"))
    # 2 assumptions within bounds, every one with a plausible range
    a2, notes = AS.validate(a)
    check("every assumption within its declared bounds", not notes and all(abs(a2[k] - a[k]) < TOL for k in a2), "; ".join(notes))
    check("every assumption has a plausible range that brackets its default", set(AS.RANGE) == set(AS.SPEC) == set(a))
    # 3 recompute the accounting
    try:
        reds = _load_paths(run_dir)
    except Exception as e:  # noqa: BLE001
        check("paths load", False, str(e))
        return _finish(checks)
    names = [r["policy"] for r in res["policies"]]
    base = reds.get("baseline")
    check("status quo paths stored", base is not None)
    if base is None:
        return _finish(checks)
    for n in reds:
        reds[n]["horizon"] = bat["horizon"]; reds[n]["n_paths"] = int(reds[n]["harm"].shape[0])
    N = int(base["harm"].shape[0])
    check("every policy of the battery is scored", set(names) == set(p["name"] for p in bat["policies"]) == set(reds))
    pr = res.get("precision") or {}
    check("path count follows the sampling plan",
          all(reds[n]["harm"].shape == (N, bat["horizon"]) for n in reds) and N == res["n_paths"] == arte["paths"]
          and bat["paths"] <= N <= bat.get("max_paths", bat["paths"]) and (pr.get("schedule") or [N])[-1] == N,
          f"{N} paths; plan {bat['paths']} to {bat.get('max_paths', bat['paths'])}; schedule {pr.get('schedule')}")
    sched = pr.get("schedule") or [N]
    check("paths were added by doubling up to the ceiling",
          all(b == min(2 * x, bat.get("max_paths", N)) for x, b in zip(sched, sched[1:])), str(sched))
    comps = {n: W.components(reds[n], base, a) for n in names if n in reds}
    by = {r["policy"]: r for r in res["policies"]}
    worst_dev, ident, gross_ok, inc_dev = 0.0, 0.0, True, 0.0
    for n, c in comps.items():
        r = by[n]
        worst_dev = max(worst_dev, abs(float(c["net_social_value"].mean()) - r["net_social_value"]["mean"]))
        for k in W.COMPONENTS:
            worst_dev = max(worst_dev, abs(float(c[k].mean()) - r["components"][k]["mean"]))
        worst_dev = max(worst_dev, abs(float(c["industry_value_change"].mean()) - r["industry_value_change"]["mean"]))
        ident = max(ident, abs(float(W.net_from({k: c[k] for k in W.COMPONENTS}).mean()) - float(c["net_social_value"].mean())))
        gc, gb = W.gross({k: float(c[k].mean()) for k in W.COMPONENTS})
        gross_ok &= (gc >= -TOL and gb >= -TOL and abs(gb - gc - float(c["net_social_value"].mean())) < 1e-6
                     and abs(gc - r["gross_cost"]["mean"]) < PTOL and r["gross_cost"]["mean"] >= -TOL)
        inc_dev = max(inc_dev, abs(r["incidence_total"] - r["net_social_value"]["mean"] - r["nonresident_payments"]))
        nsv = r["net_social_value"]
        if not (nsv["lo"] - 1e-9 <= nsv["median"] <= nsv["hi"] + 1e-9) or not (nsv["ci_lo"] - nsv["se"] - 1e-9 <= nsv["mean"] <= nsv["ci_hi"] + nsv["se"] + 1e-9):
            check(f"intervals bracket their centres for {n}", False,
                  f"outcomes {nsv['lo']:.2f} {nsv['median']:.2f} {nsv['hi']:.2f}; mean {nsv['mean']:.2f} in {nsv['ci_lo']:.2f} to {nsv['ci_hi']:.2f}")
    check("net social value, its components and the industry value recomputed from the stored paths", worst_dev < PTOL,
          f"largest deviation {worst_dev:.3g} $bn")
    check("accounting identity: the components sum to the net social value", ident < 1e-9, f"{ident:.3g}")
    check("gross cost and gross benefit are non negative and differ by the net social value", gross_ok)
    check("incidence table sums to the net social value plus the non resident memorandum item", inc_dev < 1e-6, f"{inc_dev:.3g}")
    check("status quo scores zero against itself", abs(float(comps["baseline"]["net_social_value"].mean())) < TOL)
    # The conditional estimators and the plain averages of the draws estimate the same expectations. The comparison is
    # made on each alternative's own level of harm (not on differences between alternatives, where the drawn events
    # that differ are too rare for a sample variance to mean anything) and only where enough catastrophes were drawn
    # for the standard error to be trusted; the test suite establishes the estimators' unbiasedness on a large sample.
    d_f0 = W.discount(bat["horizon"], a["discount_rate"])
    zs, zc, assessed = 0.0, 0.0, 0
    for n in names:
        R = reds[n]
        k = int(R["cat_any"].sum())
        live = float(R["cat_harm_exp"].sum()) > 0
        if N < 30 or (live and (k < MIN_EVENTS or N - k < MIN_EVENTS)):
            continue
        assessed += 1
        dh = ((R["harm"] - R["harm_exp"]) * d_f0).sum(axis=1)
        se = float(dh.std(ddof=1) / np.sqrt(N))
        if se > 0:
            zs = max(zs, abs(float(dh.mean())) / se)
        dc = R["cat_any"] - R["cat_cmc"]
        se = float(dc.std(ddof=1) / np.sqrt(N))
        if se > 0:
            zc = max(zc, abs(float(dc.mean())) / se)
    note = (f"{assessed} of {len(names)} alternatives assessable" if assessed else
            f"not assessable on {N} paths: fewer than {MIN_EVENTS} paths with a catastrophe; unbiasedness is established in the test suite")
    check("expected harm from the conditional estimator agrees with the average of the harm drawn", zs < 4.0, f"largest z {zs:.2f}; {note}")
    check("the conditional catastrophe probability agrees with the frequency of catastrophes", zc < 4.0, f"largest z {zc:.2f}; {note}")
    check("major incidents are individual incidents", all(np.all(reds[n]["n_major"] <= reds[n]["n_incidents"] + 1e-6) for n in names))
    # 4 the decision
    d_f = W.discount(bat["horizon"], a["discount_rate"])
    cons = dict(bat.get("constraints") or {})
    cons["_harm_base_npv"] = float((base["harm_exp"] * d_f).sum(axis=1).mean() * a["harm_valuation_multiplier"])
    cons["_cs_base_npv"] = float((a["consumer_surplus_base_bn"] / 12.0) * ((base["service"] ** a["cs_elasticity"]) * d_f).sum(axis=1).mean())
    M = {q: np.array([float(np.mean(comps[n][q])) if q in comps[n] else float(reds[n][q].mean()) if q in reds[n] else by[n]["headline_score"]
                      for n in names]) for q in MEANS}
    dec = decide(names, M, cons)
    check("the status quo is a decision alternative", "baseline" in names and "baseline" in dec["feasible"])
    check("preferred alternative reproduces under the constraints", dec["preferred"] == res["preferred"], f"{dec['preferred']} vs {res['preferred']}")
    check("best instrument reproduces", dec["best_intervention"] == res["best_intervention"], f"{dec['best_intervention']} vs {res['best_intervention']}")
    check("feasibility reproduces for every alternative", all(dec["feasible"][n] == by[n]["feasible"] for n in names),
          ", ".join(n for n in names if dec["feasible"][n] != by[n]["feasible"]))
    pref = res["preferred"]
    worse = (pref not in (None, "baseline") and dec["feasible"].get("baseline") and by[pref]["net_social_value"]["mean"] <= 0)
    check("no instrument with a non positive expected value is preferred to a feasible status quo", not worse,
          f"{pref}: {by[pref]['net_social_value']['mean']:.2f}" if pref else "")
    cand = [r for r in res["policies"] if r["policy"] != "baseline"]
    if cand:
        ci = [names.index(r["policy"]) for r in cand]
        order_re = [cand[i]["policy"] for i in sorted(range(len(cand)), key=lambda i: (-round(M["net_social_value"][ci[i]], 6), ci[i]))]
        order_st = res["decision_gap"]["social_order"]
        same = all(abs(M["net_social_value"][names.index(x)] - M["net_social_value"][names.index(y)]) < PTOL for x, y in zip(order_re, order_st))
        check("social order reproduces", order_re == order_st or same, f"{order_re[:3]} vs {order_st[:3]}")
        tau = kendall_tau_b([by[n]["headline_score"] for n in (r["policy"] for r in cand)], M["net_social_value"][ci]) if len(cand) > 1 else 1.0
        check("decision gap (Kendall tau b) reproduces", abs(tau - res["decision_gap"]["kendall_tau"]) < 1e-6, f"{tau:.3f}")
        ranks = sorted((r["rank_social"], round(r["net_social_value"]["mean"], 6)) for r in cand)
        check("equal scores share a rank", all((x[1] != y[1]) or (x[0] == y[0]) for x, y in zip(ranks, ranks[1:])))
    pb = sum(r["p_best"] for r in res["policies"]) + res["decision"].get("p_none_feasible", 0.0)
    check("ranking stability shares sum to one over the alternatives", abs(pb - 1.0) < 1e-9, f"{pb:.4f}")
    probs_ok = all(0 <= r["safety"]["p_major"] <= 1 and 0 <= r["safety"]["p_catastrophe"] <= 1 and 0 <= r["p_best"] <= 1
                   and 0 <= r["p_feasible"] <= 1 for r in res["policies"])
    check("probabilities within [0, 1]", probs_ok)
    check("expected harm non negative", all(r["safety"]["expected_harm_npv"]["mean"] >= 0 for r in res["policies"]))
    cons_ok = all(c["ok"] == ((c["value"] <= c["limit"] + 1e-12) if c["sense"] == "max" else (c["value"] >= c["limit"] - 1e-12))
                  and 0 <= c["p_ok"] <= 1 for r in res["policies"] for c in r["constraint_checks"])
    check("every constraint is applied as declared, with the probability it holds", cons_ok)
    check("feasible means every constraint holds", all(r["feasible"] == all(c["ok"] for c in r["constraint_checks"]) for r in res["policies"]))
    # the confidence interval of the preferred alternative, recomputed with the recorded bootstrap
    if pref and res.get("bootstrap") and res.get("bootstrap_seed") is not None:
        m, se, lo, hi = Boot(N, int(res["bootstrap"]), int(res["bootstrap_seed"])).ci(comps[pref]["net_social_value"])
        st = by[pref]["net_social_value"]
        check("confidence interval of the preferred alternative reproduces", abs(lo - st["ci_lo"]) < PTOL and abs(hi - st["ci_hi"]) < PTOL,
              f"{lo:.2f} to {hi:.2f} against {st['ci_lo']:.2f} to {st['ci_hi']:.2f}")
    # precision: what is short of its target must be said
    if pr:
        check("precision report is consistent", pr.get("met") == (not pr.get("unresolved")) and pr.get("paths") == N)
        if briefing_text and not pr.get("met"):
            check("the briefing says which estimates are short of their precision target", "precision target" in briefing_text)
    # 5 prices start at 100 from one valuation
    try:
        px = load("prices_sample.json")
        starts = [v["mean"][f][0] for v in px.values() for f in range(len(v["mean"]))]
        check("every price index starts at 100", all(abs(s - 100.0) < 1e-6 for s in starts))
        check("firm count matches the battery", all(len(v["labels"]) == len(bat["firms"]) for v in px.values()))
        caps = [v["cap0"] for v in px.values()]
        check("one pre intervention valuation for the whole battery", all(np.allclose(c, caps[0]) for c in caps))
    except Exception as e:  # noqa: BLE001
        check("price sample readable", False, str(e))
    # 6 news sample consistent with the counts
    try:
        news = load("news_sample.json")
        ok = all(news[n]["summary"]["headlines"] == len(news[n]["wire"]) for n in news)
        check("wire summaries match the wires", ok)
        nums_ok = True
        for n in news:
            for w in news[n]["wire"]:
                if w["type"] in ("incident", "catastrophe") and "$" not in w["headline"]:
                    nums_ok = False
        check("every incident headline carries its damages", nums_ok)
    except Exception as e:  # noqa: BLE001
        check("news sample readable", False, str(e))
    # 7 assurance coverage
    asr = arte.get("assurance") or {}
    scr = asr.get("screen")
    if scr:
        check("the screen covers every declared assumption", set(r["assumption"] for r in scr["rows"]) == set(AS.RANGE))
        ref = float(comps[scr["preferred"]]["net_social_value"].mean()) if scr["preferred"] in comps else None
        check("the screen's reference is the focus option's value", ref is not None and abs(scr["reference_nsv"] - ref) < PTOL)
        check("the screen's reference decision is the run's decision", scr.get("reference_best") == res["preferred"])
    jd = asr.get("joint")
    if jd:
        tot = sum(x["p_best"] for x in jd["alternatives"]) + jd.get("p_none_feasible", 0.0)
        check("joint draw: decision shares sum to one and every assumption is ranked",
              abs(tot - 1.0) < 1e-9 and set(s_["assumption"] for s_ in jd["sensitivity"]) == set(AS.RANGE), f"{tot:.4f}")
    # 7b the validation layer: the verdicts follow from the stored figures, the weighted shares from the stored draws
    vb = (asr.get("validation") or {}).get("benchmarks")
    if vb:
        rows_v = vb["rows"]
        src = vb.get("sources") or {}
        check("every benchmark carries a source, a mapping and a transport allowance",
              all(src.get(r["id"], {}).get("sources") and src[r["id"]].get("mapping") and r["transport"] >= 0 for r in rows_v))
        zs_ok = True
        for r in rows_v:
            if r["model"] is None:
                zs_ok = zs_ok and r["verdict"] is None and bool(r["why_not"])
                continue
            den = float(np.sqrt(r["se"] ** 2 + r["transport"] ** 2 + (r["model_se"] or 0.0) ** 2))
            z = (r["model"] - r["observed"]) / den
            want = "not contradicted" if abs(z) <= 2 else ("in tension" if abs(z) <= 3 else "contradicted")
            zs_ok = zs_ok and abs(z - r["z"]) < 1e-9 and r["verdict"] == want
        check("benchmark verdicts follow from the observed and modelled values", zs_ok)
        check("the evidence base is the one approved at Gate 1", vb.get("evidence_hash") == bat.get("evidence") and
              (not bat.get("benchmarks") or len(rows_v) + len(vb.get("problems") or []) == len(bat["benchmarks"])))
        cb = vb.get("calibration")
        if cb and cb.get("used"):
            wts = np.asarray(cb["per_draw"]["weight"], dtype=float)
            dec = cb["per_draw"]["decision"]
            sh = {k: float(sum(wts[j] for j, d_ in enumerate(dec) if d_ == k)) for k in cb["decision_posterior"]}
            ok_w = (abs(wts.sum() - 1.0) < 1e-9 and abs(1.0 / float((wts ** 2).sum()) - cb["ess"]) < 1e-6
                    and all(abs(sh[k] - (cb["decision_posterior"][k] or 0.0)) < 1e-9 for k in sh)
                    and cb["reliable"] == (cb["ess"] >= cb["min_ess"]) and len(dec) == cb["draws"])
            check("weighted decision shares reproduce from the stored draws and weights", ok_w, f"effective draws {cb['ess']:.1f} of {cb['draws']}")
            if jd:
                pj = {x["policy"]: x["p_best"] for x in jd["alternatives"]}
                check("the unweighted shares are the joint draw's", all(abs((cb["decision_prior"].get(k) or 0.0) - v) < 1e-9 for k, v in pj.items()))
        failing = [r for r in rows_v if r["verdict"] in ("in tension", "contradicted")]
        if briefing_text and failing:
            check("the briefing names every benchmark the model is in tension with or contradicted by",
                  all(r["title"] in briefing_text for r in failing), ", ".join(r["id"] for r in failing))
    var = asr.get("variance")
    if var:
        check("variance shares within [0, 1]", all(0 <= r[k] <= 1 for r in var["rows"] for k in ("first_order_value", "total_value", "first_order_margin", "total_margin")))
    st = asr.get("structural")
    if st:
        check("structural variants complete", st["n"] == len(st["variants"]) == len(STRUCTURAL))
    rt = asr.get("red_team")
    if rt:
        check("red team ran every strategy on every instrument",
              all(set(r["strategies"]) == set(GAMING) for r in rt["rows"]) and len(rt["rows"]) == len(cand))
    rb = asr.get("robustness")
    if rb:
        check("robustness table covers every instrument", set(r["policy"] for r in rb["rows"]) == set(r["policy"] for r in cand))
    check("mechanism register covers every assumption",
          set(k for m in arte.get("mechanisms", []) for k in m["assumptions"]) == set(AS.SPEC))
    # 8 the ledger
    lp = os.path.join(run_dir, "ledger.jsonl")
    if os.path.isfile(lp):
        rep = ledger_verify(lp, secret=secret)
        check("ledger chain verifies" + (" and every record is signed" if secret else ""), rep.get("ok"),
              f"{rep.get('entries')} entries" + ("" if rep.get("ok") else f": {'; '.join(rep.get('errors', [])[:3])}"))
    # 9 the briefing's numbers
    if briefing_text:
        bad = _vet_numbers(briefing_text, arte)
        check("every figure in the briefing appears in the artefacts", not bad, f"unmatched: {bad[:8]}")
    return _finish(checks)


def _finish(checks):
    failed = [c for c in checks if not c["ok"]]
    return {"ok": not failed, "n_checks": len(checks), "n_failed": len(failed), "checks": checks}


def _numbers_in_text(obj, acc):
    """The numbers written inside the strings of a document (the evidence base's own wording)."""
    if isinstance(obj, str):
        for m in re.finditer(r"-?\d{1,3}(?:,\d{3})+(?:\.\d+)?|-?\d+(?:\.\d+)?", re.sub(r"https?://[^\s)]+", "", obj)):
            try:
                acc.add(float(m.group(0).replace(",", "")))
            except ValueError:
                pass
    elif isinstance(obj, dict):
        for v in obj.values():
            _numbers_in_text(v, acc)
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            _numbers_in_text(v, acc)


def _numbers_in(obj, acc):
    if isinstance(obj, bool):
        return
    if isinstance(obj, (int, float)):
        acc.add(float(obj))            # unrounded: a figure printed to five decimals is checked against the value itself
    elif isinstance(obj, dict):
        for v in obj.values():
            _numbers_in(v, acc)
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            _numbers_in(v, acc)


def _vet_numbers(text, arte):
    """Every number printed in the briefing (outside code and hashes) must round to a number in the artefacts
    at one of the printed precisions, or be a count, a year, a percentage of one, or a month."""
    acc = set()
    _numbers_in(arte, acc)
    # the evidence base is text: a figure quoted from a benchmark's title, observations, source or caveat is in the artefacts too
    vb = ((arte.get("assurance") or {}).get("validation") or {}).get("benchmarks") or {}
    _numbers_in_text([vb.get("sources"), vb.get("not_used"), [r.get("title") for r in vb.get("rows", [])]], acc)
    derived = set()
    for v in list(acc):
        derived.add(v * 100); derived.add(-v); derived.add(-v * 100)
        derived.add(v / 12.0); derived.add(v * 12.0)
    acc |= derived
    bad = []
    body = re.sub(r"`[^`]*`", "", text)
    body = re.sub(r"https?://[^\s)]+", "", body)                    # a link is not a figure
    body = re.sub(r"\b[0-9a-f]{12,64}\b", "", body)
    body = re.sub(r"\b\d{8}-\d{6}-[0-9a-f]{4}\b", "", body)           # run identifiers
    body = re.sub(r"\b20\d\d-\d\d(?:-\d\d)?(?:T[0-9:+.]+)?\b", "", body)
    scale = {"tn": 1e-3, "bn": 1.0, "m": 1e3, "k": 1e6, "": 1.0, "%": 1.0, "x": 1.0, "pp": 1.0}
    for m in re.finditer(r"(?<![\w.])(-?\d{1,3}(?:,\d{3})*(?:\.\d+)?|-?\d+(?:\.\d+)?)(tn|bn|m|k|pp|%|x)?(?!\w|\.\d)", body):
        s, unit = m.group(1).replace(",", ""), m.group(2) or ""
        try:
            v = float(s)
        except ValueError:
            continue
        if abs(v) <= 120 and float(v).is_integer() and unit in ("", "%", "x", "pp"):
            continue                      # counts, months, years of horizon, small integers, whole percentages
        if 1900 <= v <= 2200 and unit == "":
            continue
        nd = len(s.split(".")[1]) if "." in s else 0
        f = scale[unit]
        ok = any(abs(round(x * f, nd) - v) < 0.5 * 10 ** (-nd) + 1e-9 for x in acc)
        if not ok:
            bad.append(s + unit)
    return sorted(set(bad))
