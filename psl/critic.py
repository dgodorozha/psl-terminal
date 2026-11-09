"""The critic: an independent recomputation of every figure the briefing
will cite, from the stored paths, before Gate 2 can arm.

It does not trust results.json. It reloads the per path aggregates
(paths.npz), the assumptions and the battery, recomputes the welfare
components, the rankings, the preferred option, the probabilities and the
decision gap, and compares them with what the pipeline wrote. It then
replays the ledger chain and checks that every number in the briefing
appears in the artefacts.
"""

import json
import os
import re

import numpy as np

from . import welfare as W
from . import assumptions as AS
from .economy import battery_hash
from .evaluate import kendall_tau, _rank_desc
from .ledger import verify as ledger_verify

TOL = 1e-6


def _load_paths(run_dir):
    z = np.load(os.path.join(run_dir, "paths.npz"))
    aggs = {}
    for key in z.files:
        n, k = key.split("__", 1)
        aggs.setdefault(n, {})[k] = z[key]
    return aggs


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
    h = battery_hash({k: bat[k] for k in ("question", "constraints", "policies", "firms", "assumptions", "horizon", "paths", "seed")})
    check("battery hash reproduces", h == bat["hash"], f"{h[:12]} vs {bat['hash'][:12]}")
    check("assumptions hash reproduces", AS.assumptions_hash(a) == asm["hash"])
    check("artefacts cite the approved battery", arte["battery_hash"] == bat["hash"])
    # 2 assumptions within bounds
    a2, notes = AS.validate(a)
    check("every assumption within its declared bounds", not notes and all(abs(a2[k] - a[k]) < TOL for k in a2), "; ".join(notes))
    # 3 recompute the accounting
    try:
        aggs = _load_paths(run_dir)
    except Exception as e:  # noqa: BLE001
        check("paths load", False, str(e))
        return _finish(checks)
    for n in aggs:
        aggs[n]["horizon"] = bat["horizon"]
    base = aggs.get("baseline")
    check("baseline paths stored", base is not None)
    if base is None:
        return _finish(checks)
    names = [r["policy"] for r in res["policies"]]
    check("every policy of the battery is scored", set(names) == set(p["name"] for p in bat["policies"]))
    check("path count matches the battery", all(aggs[n]["harm"].shape == (bat["paths"], bat["horizon"]) for n in aggs))
    nsv_re, harm_re, head_ok = {}, {}, True
    worst_dev = 0.0
    for r in res["policies"]:
        n = r["policy"]
        if n not in aggs:
            check(f"paths stored for {n}", False); continue
        c = W.components(aggs[n], base, a)
        nsv_re[n] = float(c["net_social_value"].mean())
        harm_re[n] = float(c["harm_avoided"].mean())
        dev = abs(nsv_re[n] - r["net_social_value"]["mean"])
        worst_dev = max(worst_dev, dev)
        for k in W.COMPONENTS:
            dk = abs(float(c[k].mean()) - r["components"][k]["mean"])
            worst_dev = max(worst_dev, dk)
        ident = abs(float(W.net_from({k: c[k] for k in W.COMPONENTS}).mean()) - nsv_re[n])
        if ident > 1e-6:
            check(f"accounting identity holds for {n}", False, f"{ident:.3g}")
        lo, hi, mean = r["net_social_value"]["lo"], r["net_social_value"]["hi"], r["net_social_value"]["mean"]
        med = r["net_social_value"].get("median", mean)
        if not (lo - 1e-9 <= med <= hi + 1e-9) or lo > hi:
            check(f"interval brackets the median for {n}", False, f"{lo:.2f} {med:.2f} {hi:.2f}")
        if mean > max(hi, 0.0) + 1e-9 and r["net_social_value"].get("tail_share", 0.0) < 0.3:
            check(f"a mean above the 90th percentile is tail driven for {n}", False,
                  f"mean {mean:.2f} above {hi:.2f} with tail share {r['net_social_value'].get('tail_share', 0.0):.2f}")
    check("net social value recomputed from the stored paths", worst_dev < 1e-3, f"largest deviation {worst_dev:.3g} $bn")
    check("baseline scores zero against itself", abs(nsv_re.get("baseline", 0.0)) < TOL)
    # 4 rankings and the preferred option
    cand = [r for r in res["policies"] if r["policy"] != "baseline"]
    if cand:
        order_re = [n for n in sorted(nsv_re, key=lambda k: -nsv_re[k]) if n != "baseline"]
        check("social order reproduces", order_re == res["decision_gap"]["social_order"], f"{order_re[:3]} vs {res['decision_gap']['social_order'][:3]}")
        heads = np.array([r["headline_score"] for r in cand]); nsvs = np.array([nsv_re[r["policy"]] for r in cand])
        tau = kendall_tau(_rank_desc(heads), _rank_desc(nsvs)) if len(cand) > 1 else 1.0
        check("decision gap (Kendall tau) reproduces", abs(tau - res["decision_gap"]["kendall_tau"]) < 1e-9, f"{tau:.3f}")
        feas = [r for r in cand if r.get("feasible")]
        pref_re = max(feas, key=lambda r: nsv_re[r["policy"]])["policy"] if feas else None
        check("preferred option reproduces under the constraints", pref_re == res["preferred"], f"{pref_re} vs {res['preferred']}")
        check("best unconstrained option reproduces", order_re[0] == res["best_unconstrained"])
        pb = sum(r["p_best"] for r in cand)
        check("winner probabilities sum to one", abs(pb - 1.0) < 1e-9, f"{pb:.4f}")
        probs_ok = all(0 <= r["safety"]["p_major"] <= 1 and 0 <= r["safety"]["p_catastrophe"] <= 1 and 0 <= r["p_best"] <= 1 for r in cand)
        check("probabilities within [0, 1]", probs_ok)
        harm_ok = all(r["safety"]["expected_harm_npv"]["mean"] >= 0 for r in res["policies"])
        check("expected harm non negative", harm_ok)
        # harm avoided recomputed from stored incident harm
        dev_h = max(abs(harm_re[r["policy"]] - r["components"]["harm_avoided"]["mean"]) for r in cand)
        check("harm avoided recomputed", dev_h < 1e-3, f"largest deviation {dev_h:.3g}")
        # constraints applied as declared
        cons = {k: v for k, v in (bat.get("constraints") or {}).items()}
        if cons.get("max_industry_loss_bn") is not None:
            viol = [r["policy"] for r in cand if r["feasible"] and -r["industry_value_change"]["mean"] > cons["max_industry_loss_bn"] + 1e-9]
            check("industry loss constraint applied", not viol, ", ".join(viol))
        if cons.get("max_social_cost_bn") is not None:
            viol = [r["policy"] for r in cand if r["feasible"] and r["gross_cost"]["mean"] > cons["max_social_cost_bn"] + 1e-9]
            check("social cost budget applied", not viol, ", ".join(viol))
    # 5 prices start at 100, market caps consistent
    try:
        px = load("prices_sample.json")
        starts = [v["mean"][f][0] for v in px.values() for f in range(len(v["mean"]))]
        check("every price index starts at 100", all(abs(s - 100.0) < 1e-6 for s in starts))
        check("firm count matches the battery", all(len(v["labels"]) == len(bat["firms"]) for v in px.values()))
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
    torn = asr.get("tornado")
    if torn:
        check("tornado covers every declared value judgement", set(r["assumption"] for r in torn["rows"]) == set(AS.TORNADO))
        check("tornado reference matches the preferred option's value", abs(torn["reference_nsv"] - nsv_re.get(torn["preferred"], 0.0)) < 1e-3)
    st = asr.get("structural")
    if st:
        check("structural variants complete", st["n"] == len(st["variants"]) and st["n"] >= 3)
    rt = asr.get("red_team")
    if rt:
        check("red team ran every strategy on every instrument",
              all(set(r["strategies"]) == set(rt["strategies"]) for r in rt["rows"]) and len(rt["rows"]) == len(cand))
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


def _numbers_in(obj, acc):
    if isinstance(obj, bool):
        return
    if isinstance(obj, (int, float)):
        acc.add(round(float(obj), 6))
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
    derived = set()
    for v in list(acc):
        derived.add(round(v * 100, 6)); derived.add(round(-v, 6)); derived.add(round(-v * 100, 6))
        derived.add(round(v / 12.0, 6)); derived.add(round(v * 12.0, 6))
    acc |= derived
    bad = []
    body = re.sub(r"`[^`]*`", "", text)
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
