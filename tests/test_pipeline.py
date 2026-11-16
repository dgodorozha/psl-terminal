"""The whole chain on a tiny budget: plan, run, evaluate, assure, critic, briefing, transparency record,
evidence pack. Checks the artefacts are coherent (every assurance stage is paired with the main run on common
random numbers, so an alternative that changes nothing reproduces the headline), the sampling plan grows the
battery on the same random streams, a battery in which every instrument destroys value ends with the status quo,
the critic passes, the briefing's numbers are vetted, the pack verifies, and the replication tool runs."""

import json
import os
import sys
import zipfile

import numpy as np
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tools"))

from psl import assumptions as AS  # noqa: E402
from psl import assurance as ASR  # noqa: E402
from psl.atrs import atrs_record, render_markdown  # noqa: E402
from psl.briefing import draft_briefing, to_html  # noqa: E402
from psl.critic import critic_check, _vet_numbers  # noqa: E402
from psl.evaluate import MEANS, decision_arrays  # noqa: E402
from psl.evidence import build_pack  # noqa: E402
from psl.ledger import Ledger, verify  # noqa: E402
from psl.mechanisms import MECHANISMS  # noqa: E402
from psl.pipeline import HASHED, hash_of, make_battery, run_battery, SimulationStopped  # noqa: E402
from psl.question import parse  # noqa: E402
from psl.reduce import simulate_design  # noqa: E402

TINY = {"paths": 8, "max_paths": 8, "horizon": 18, "boot": 40, "variant_paths": 4, "redteam_paths": 8, "screen_paths": 2,
        "joint_draws": 12, "joint_paths": 2, "sobol_k": 3, "sobol_base": 8, "sobol_paths": 2, "batches": 2, "tornado": True}
APPROVALS = {"preparer": "Developer1", "preparer_role": "Developer1",
             "gate1": {"actor": "Developer2", "role": "Developer2", "ts": "2026-01-01T00:00:00+00:00", "decision": "approved"}}


def _run(out, question, budget, **kw):
    plan = parse(question)
    bat = make_battery(plan, budget=dict(budget), profile="demo", **kw)
    log = Ledger(os.path.join(out, "ledger.jsonl"), "tiny", secret="k")
    events = []
    arte, reds = run_battery(bat, str(out), log=log, progress=lambda s, p, **k: events.append((s, p)))
    return {"dir": str(out), "bat": bat, "arte": arte, "reds": reds, "log": log, "events": events}


@pytest.fixture(scope="module")
def run(tmp_path_factory):
    return _run(tmp_path_factory.mktemp("run"),
                "Compare transparency, strict liability and liability with a safe harbour over two years; industry loss under $900bn", TINY)


def test_battery_and_artefacts(run):
    bat, arte = run["bat"], run["arte"]
    assert [p["name"] for p in bat["policies"]][0] == "baseline" and len(bat["policies"]) == 4
    assert bat["horizon"] == 24 and bat["paths"] == 8 and bat["max_paths"] == 8
    assert arte["battery_hash"] == bat["hash"] == hash_of(bat) and arte["assumptions_hash"] == AS.assumptions_hash(bat["assumptions"])
    # the sampling plan is part of what is approved: changing it changes the hash
    assert {"paths", "max_paths", "precision", "seed"} <= set(HASHED)
    for k, v in (("max_paths", 16), ("precision", {"nsv_gap_bn": 1.0, "p_catastrophe_halfwidth": 0.03}), ("seed", 8)):
        assert hash_of(dict(bat, **{k: v})) != bat["hash"], k
    ev = arte["results"]
    assert set(ev["names"]) == {p["name"] for p in bat["policies"]}
    assert ev["preferred"] in ev["names"] and ev["focus"] in ev["names"] and ev["focus"] != "baseline"
    assert ev["precision"]["schedule"] == [8] and ev["precision"]["paths"] == arte["paths"] == 8
    for r in ev["policies"]:
        s = r["net_social_value"]
        assert s["lo"] <= s["median"] <= s["hi"] and s["ci_lo"] <= s["mean"] <= s["ci_hi"]
        assert 0.0 <= r["p_feasible"] <= 1.0 and 0.0 <= r["p_best"] <= 1.0
        assert len(r["news"]["quarterly_negative"]) == 8
        assert len(r["market"]["index_mean"]) == 25 and len(r["market"]["rel_mean"]) == 25
        assert abs(r["market"]["index_mean"][0] - 100.0) < 1e-9, "every index starts from the same pre intervention valuation"
        assert r["constraint_checks"] and r["constraint_checks"][0]["constraint"] == "max_industry_loss_bn"
    assert abs(sum(r["p_best"] for r in ev["policies"]) + ev["decision"]["p_none_feasible"] - 1.0) < 1e-9
    assert {"simulate", "markets", "welfare", "assurance", "critic"} <= {s for s, _ in run["events"]}
    for name in ("artefacts.json", "results.json", "assurance.json", "battery.json", "paths.npz", "paths.json", "news_sample.json", "prices_sample.json"):
        assert os.path.isfile(os.path.join(run["dir"], name)), name
    # what the briefing may cite about the model itself
    assert len(arte["mechanisms"]) == len(MECHANISMS)
    assert all(m[k] for m in arte["mechanisms"] for k in ("source", "identifying_assumption", "calibration", "validation_test", "status"))
    assert sum(1 for m in arte["mechanisms"] if m["tested_here"]) == 1, "one mechanism can be confronted with data here, and the register says so"
    assert arte["accounting_map"] and arte["constants"] and arte["correlated_assumptions"]
    table = {r["assumption"]: r for r in arte["assumption_table"]}
    assert set(table) == set(AS.SPEC) and all(r["range_low"] <= r["value"] <= r["range_high"] for r in table.values())


def test_assurance_is_paired_with_the_main_run(run):
    arte = run["arte"]; ev = arte["results"]
    pols = {r["policy"]: r for r in ev["policies"]}
    asr = arte["assurance"]
    focus = ev["focus"]
    # the screen covers every declared assumption; the tornado is its largest swings
    scr = asr["screen"]
    assert scr["n_assumptions"] == len(AS.SPEC) and {r["assumption"] for r in scr["rows"]} == set(AS.SPEC)
    assert scr["preferred"] == focus and abs(scr["reference_nsv"] - pols[focus]["net_social_value"]["mean"]) < 1e-6
    assert scr["reference_best"] == ev["preferred"]
    swings = [r["swing"] for r in scr["rows"]]
    assert swings == sorted(swings, reverse=True)
    assert set(scr["flips"]) == {r["assumption"] for r in scr["rows"] if r["best_changes"]}
    by = {r["assumption"]: r for r in scr["rows"]}
    assert all(by[k]["resimulated"] != (k in AS.WELFARE_ONLY) for k in by)
    # an assumption recomputed exactly has no Monte Carlo error; a re simulated one carries the error of its paired shift
    assert all(by[k]["swing_se"] == 0.0 and by[k]["swing_resolved"] == (by[k]["swing"] > 0) for k in AS.WELFARE_ONLY)
    assert all(by[k]["swing_se"] >= 0.0 for k in by) and scr["n_swing_resolved"] == sum(r["swing_resolved"] for r in scr["rows"])
    # why the decision changes: the run's decision leaves the constraints, or another alternative overtakes it
    for r in scr["rows"]:
        for end in (r["low"], r["high"]):
            assert end["flip"] == (None if end["best"] == scr["reference_best"] else ("value" if end["ref_feasible"] else "feasibility"))
    assert set(scr["flips_by_feasibility"]) | set(scr["flips_by_value"]) == set(scr["flips"])
    t = asr["tornado"]
    assert t["n_screened"] == len(AS.SPEC) and t["shown"] == 15 and [r["assumption"] for r in t["rows"]] == [r["assumption"] for r in scr["rows"][:15]]
    # the joint draw: every alternative, probabilities that add up, a regret that is zero only for an option that is always best
    jd = asr["joint"]
    assert jd["draws"] == 12 and {x["policy"] for x in jd["alternatives"]} == set(pols)
    assert abs(sum(x["p_best"] for x in jd["alternatives"]) + jd["p_none_feasible"] - 1.0) < 1e-9
    assert all(x["nsv_lo"] <= x["nsv_mean"] <= x["nsv_hi"] for x in jd["alternatives"])
    # regret is against the best alternative within the constraints, over the draws in which the alternative is within them
    for x in jd["alternatives"]:
        assert (x["expected_regret"] is None) == (x["regret_draws"] == 0) and x["regret_draws"] == round(x["p_feasible"] * jd["draws"])
        assert x["expected_regret"] is None or x["expected_regret"] >= -1e-9
    always = [x for x in jd["alternatives"] if x["p_best"] == 1.0]
    assert all(abs(x["expected_regret"]) < 1e-9 for x in always), "an alternative that is always the decision has no regret"
    assert jd["least_regret"] in {x["policy"] for x in jd["alternatives"] if x["p_feasible"] >= 0.9}
    assert {s["assumption"] for s in jd["sensitivity"]} == set(AS.SPEC)
    assert set(jd["margin_drivers"]) <= set(AS.SPEC) and set(jd["decision_drivers"]) <= set(AS.SPEC) and sum(jd["filter_split"]) == 12
    assert set(jd["margin_drivers"]) == {s["assumption"] for s in jd["sensitivity"] if s["margin_driver"]}
    assert all(0.0 <= s["p_margin"] <= 1.0 and 0.0 <= s["ks_decision"] <= 1.0 for s in jd["sensitivity"])
    # the variance decomposition is over the screen's most influential assumptions
    var = asr["variance"]
    assert var["keys"] == [r["assumption"] for r in scr["rows"][:3]] and var["evaluations"] == (3 + 2) * 8
    assert all(0.0 <= r[k] <= 1.0 for r in var["rows"] for k in ("first_order_value", "total_value", "first_order_margin", "total_margin"))
    assert all(r[k + "_lo"] <= r[k] + 1e-12 and r[k] <= r[k + "_hi"] + 1e-12 for r in var["rows"] for k in ("total_value", "total_margin"))
    assert var["interval_level"] == 0.90 and var["mean_halfwidth_total_margin"] >= 0
    # the red team's honest value is the headline value: same paths, same seed
    for r in asr["red_team"]["rows"]:
        assert abs(r["honest"]["nsv"] - pols[r["policy"]]["net_social_value"]["mean"]) < 1e-6, r["policy"]
        assert r["worst_nsv"] <= max(s["nsv"] for s in r["strategies"].values()) + 1e-9
        assert all(set(s) >= {"nsv", "feasible", "acceptable", "constraint_values"} for s in r["strategies"].values())
        assert r["acceptable_under_all"] == all(s["feasible"] and s["nsv"] > 0 for s in r["strategies"].values())
    assert asr["red_team"]["maximin"] in set(pols)
    st = asr["structural"]
    assert st["n"] == len(st["variants"]) == len(ASR.STRUCTURAL) and st["resimulated_paths"] == 4
    for v in st["variants"]:
        assert v["best"] in pols and 1 <= v["preferred_rank"] <= len(pols) - 1
        assert set(v["table"]) == set(pols) and all(set(x) == {"nsv", "feasible"} for x in v["table"].values())
        assert abs(v["table"]["baseline"]["nsv"]) < 1e-9, "the status quo scores zero under every structure"
    rb = asr["robustness"]
    assert {r["policy"] for r in rb["rows"]} == set(pols) - {"baseline"}
    assert set(rb["robustly_acceptable"]) <= {r["policy"] for r in rb["rows"] if r["central_acceptable"]}
    assert asr["batches"] is None, "eight paths are too few to split into batches"
    assert asr["validation"]["events"] == [] and asr["validation"]["coverage"] is None


def test_an_alternative_that_changes_nothing_reproduces_the_headline(run):
    bat, reds = run["bat"], run["reds"]
    a = bat["assumptions"]
    policies = {p["name"]: p for p in bat["policies"]}
    names = list(policies)
    arr = decision_arrays(reds, a)
    full = ASR.central(names, arr)
    key = "hazard_base_misuse"
    rows = [{}, {key: a[key]}, {key: AS.RANGE[key][1]}]
    dreds, a_des = simulate_design(policies, bat["firms"], a, rows, bat["horizon"], 4, bat["seed"])
    assert dreds["baseline"]["n_paths"] == 12 and np.array_equal(a_des[key][:8], np.full(8, a[key]))
    M = ASR.paired(names, arr, decision_arrays(dreds, a_des), 4, blocks=3)
    for q in MEANS:
        assert np.allclose(M[q][:, 0], full[q], atol=1e-9) and np.allclose(M[q][:, 1], full[q], atol=1e-9), q
    i = names.index("strict_liability")
    assert abs(M["harm_avoided"][i, 2] - full["harm_avoided"][i]) > 1e-6, "a higher hazard changes the harm an instrument avoids"
    assert abs(M["net_social_value"][0, 2]) < 1e-9, "the status quo scores zero under every alternative"


def test_batches_split_the_paths_into_independent_replications():
    rng = np.random.default_rng(1)
    names = ["baseline", "a", "b"]
    arr = {n: {q: np.zeros(120) for q in MEANS} for n in names}
    arr["a"]["net_social_value"] = rng.normal(5.0, 1.0, 120)
    arr["b"]["net_social_value"] = np.concatenate([np.full(30, 50.0), np.full(90, -10.0)])
    arr["b"]["industry_value_change"] = np.full(120, -1.0)
    rep = ASR.batches(names, arr, {}, k=4)
    assert rep["k"] == 4 and rep["size"] == 30 and [r["paths"] for r in rep["rows"]] == [30] * 4
    assert [r["preferred"] for r in rep["rows"]] == ["b", "a", "a", "a"] and rep["preferred"] == "b" and rep["agree"] == 1
    assert abs(np.mean([r["nsv"]["a"] for r in rep["rows"]]) - arr["a"]["net_social_value"].mean()) < 1e-12
    assert ASR.batches(names, {n: {q: v[:40] for q, v in arr[n].items()} for n in names}, {}, k=4) is None
    # the running estimate: what a run of an eighth, a quarter and half the size would have reported
    cv = ASR.convergence(names, arr, {}, "a")
    assert [r["paths"] for r in cv["rows"]] == [15, 30, 60, 120]
    assert [r["preferred"] for r in cv["rows"]] == ["b", "b", "b", "b"] and cv["decision_stable_over_last_doubling"]
    for r in cv["rows"]:
        x = arr["a"]["net_social_value"][:r["paths"]]
        assert abs(r["focus_nsv"] - x.mean()) < 1e-12 and abs(r["focus_se"] - x.std(ddof=1) / np.sqrt(r["paths"])) < 1e-12
    ses = [r["focus_se"] for r in cv["rows"]]
    assert ses[0] > ses[-1] * 2, "the standard error falls with the square root of the paths"
    flip = {n: dict(arr[n]) for n in names}
    flip["b"]["net_social_value"] = np.concatenate([np.full(60, -10.0), np.full(60, 50.0)])
    cf = ASR.convergence(names, flip, {}, "a")
    assert [r["preferred"] for r in cf["rows"]] == ["a", "a", "a", "b"] and not cf["decision_stable_over_last_doubling"]


def test_critic_briefing_record_and_pack(run):
    d, arte, log = run["dir"], run["arte"], run["log"]
    md = draft_briefing(arte, APPROVALS, "tiny")
    assert "status quo" in md and "95% confidence interval" in md and "ranking stability" in md.lower()
    assert _vet_numbers(md, arte) == [], "every number in the briefing must come from the artefacts"
    assert _vet_numbers(md + " The value is $999.123bn, 77.7% of paths.", arte) == ["77.7%", "999.123bn"]
    critic = critic_check(d, secret="k", briefing_text=md)
    failed = [c for c in critic["checks"] if not c["ok"]]
    assert critic["ok"], failed
    assert critic["n_checks"] >= 40
    html = to_html(md)
    assert "<table" in html and "<script" not in html
    rec = atrs_record(arte, APPROVALS, "tiny", organisation="Test Authority")
    assert rec["tier1"]["name"].startswith("Policy Scenario Lab") and "risks" in rec["tier2"]["risks_mitigations_and_impact_assessments"]
    assert render_markdown(rec).startswith("# Algorithmic transparency record")
    with open(os.path.join(d, "briefing.md"), "w") as f:
        f.write(md)
    with open(os.path.join(d, "critic.json"), "w") as f:
        json.dump(critic, f)
    rep = verify(log.path, "k")
    assert rep["ok"] and rep["entries"] >= 8
    assert not verify(log.path, "wrong-key")["ok"], "the signature must bind the key"
    pack, manifest = build_pack(d)
    with zipfile.ZipFile(pack) as z:
        names = set(z.namelist())
        assert {"manifest.json", "VERIFY.md", "artefacts.json", "ledger.jsonl", "briefing.md", "critic.json"} <= names


def test_the_critic_catches_a_tampered_result(run, tmp_path):
    import shutil
    d = str(tmp_path / "copy")
    shutil.copytree(run["dir"], d)
    md = draft_briefing(run["arte"], APPROVALS, "tiny")
    assert critic_check(d, secret="k", briefing_text=md)["ok"]
    path = os.path.join(d, "artefacts.json")
    arte = json.load(open(path))
    row = next(r for r in arte["results"]["policies"] if r["policy"] == arte["results"]["focus"])
    row["net_social_value"]["mean"] += 3.0
    json.dump(arte, open(path, "w"))
    rep = critic_check(d, secret="k", briefing_text=md)
    assert not rep["ok"] and [c["check"] for c in rep["checks"] if not c["ok"]] == ["the artefacts carry the scored results unchanged"]
    # the same change made to both documents is caught by the recomputation from the stored paths
    res = json.load(open(os.path.join(d, "results.json")))
    next(r for r in res["policies"] if r["policy"] == res["focus"])["net_social_value"]["mean"] += 3.0
    json.dump(res, open(os.path.join(d, "results.json"), "w"))
    rep = critic_check(d, secret="k", briefing_text=md)
    failed = [c["check"] for c in rep["checks"] if not c["ok"]]
    assert not rep["ok"] and any("recomputed from the stored paths" in c for c in failed), failed
    # and so is a change to an approved assumption after the fact
    shutil.rmtree(d); shutil.copytree(run["dir"], d)
    asm = json.load(open(os.path.join(d, "assumptions.json")))
    asm["assumptions"]["harm_valuation_multiplier"] = 2.0
    json.dump(asm, open(os.path.join(d, "assumptions.json"), "w"))
    failed = [c["check"] for c in critic_check(d, secret="k", briefing_text=md)["checks"] if not c["ok"]]
    assert "assumptions hash reproduces" in failed and "the artefacts carry the approved assumptions, instruments and firms" in failed


def test_a_second_implementation_agrees_with_the_accounting(run, tmp_path):
    import shutil
    from recompute import recompute
    rep = recompute(run["dir"])
    assert rep["ok"] and rep["failed"] == 0 and rep["checks"] > 100, [r for r in rep["rows"] if not r["ok"]]
    assert rep["largest_deviation_in_tolerances"] < 0.5, "single precision paths, not a different definition"
    what = {r["what"] for r in rep["rows"]}
    assert {"the decision", "the best instrument within the constraints", "strict_liability: gross cost",
            "strict_liability: 95% interval, lower", "strict_liability: max_industry_loss_bn",
            "no instrument worse than a feasible status quo is preferred"} <= what
    # it does not import the Lab
    src = open(os.path.join(ROOT, "tools", "recompute.py")).read()
    assert "import psl" not in src and "from psl" not in src
    # a reported figure that departs from the definition is caught: the size of the gross cost discrepancy the review found
    d = str(tmp_path / "copy")
    shutil.copytree(run["dir"], d)
    res = json.load(open(os.path.join(d, "results.json")))
    row = next(r for r in res["policies"] if r["policy"] == "strict_liability")
    row["gross_cost"]["mean"] -= 0.14
    json.dump(res, open(os.path.join(d, "results.json"), "w"))
    bad = recompute(d)
    assert not bad["ok"] and [r["what"] for r in bad["rows"] if not r["ok"]] == ["strict_liability: gross cost"]
    # and so is a decision that prefers an instrument over a better status quo
    res = json.load(open(os.path.join(run["dir"], "results.json")))
    res["preferred"] = "strict_liability"
    json.dump(res, open(os.path.join(d, "results.json"), "w"))
    failed = [r["what"] for r in recompute(d)["rows"] if not r["ok"]]
    assert "the decision" in failed


def test_a_battery_of_instruments_worse_than_doing_nothing_ends_with_the_status_quo(tmp_path):
    budget = dict(TINY, tornado=False)
    r = _run(tmp_path, "Compare risk tiering and a moratorium over two years", budget)
    ev = r["arte"]["results"]
    by = {x["policy"]: x for x in ev["policies"]}
    assert by["risk_tiering"]["net_social_value"]["mean"] < 0 and by["moratorium"]["net_social_value"]["mean"] < 0
    assert ev["preferred"] == "baseline" and ev["best_intervention"] == "risk_tiering" and ev["focus"] == "risk_tiering"
    assert ev["decision"]["is_status_quo"] and ev["winner_stability"] == 1.0
    asr = r["arte"]["assurance"]
    assert asr["screen"] is None and asr["joint"] is None, "the screen was switched off in this budget"
    assert asr["robustness"]["robustly_acceptable"] == [] and asr["red_team"]["maximin"] == "baseline"
    assert all(v["best"] == "baseline" for v in asr["structural"]["variants"]) and asr["structural"]["survival"] == 1.0
    md = draft_briefing(r["arte"], APPROVALS, "tiny")
    assert "No tested instrument improves on the status quo" in md
    assert _vet_numbers(md, r["arte"]) == []
    critic = critic_check(r["dir"], secret="k", briefing_text=md)
    assert critic["ok"], [c for c in critic["checks"] if not c["ok"]]
    assert any("status quo" in c["check"] and c["ok"] for c in critic["checks"])


def test_adaptive_sampling_grows_the_battery_on_the_same_streams(tmp_path):
    q = "Compare transparency and liability with a safe harbour over three years"      # long enough for the catastrophic tail to be live
    tight = {"nsv_gap_bn": 1e-6, "p_catastrophe_halfwidth": 1e-6}
    grown = _run(tmp_path / "grown", q, dict(TINY, max_paths=32, precision=tight, tornado=False))
    fixed = _run(tmp_path / "fixed", q, dict(TINY, paths=32, max_paths=32, precision=tight, tornado=False))
    pg, pf = grown["arte"]["results"]["precision"], fixed["arte"]["results"]["precision"]
    assert pg["schedule"] == [8, 16, 32] and pg["paths"] == grown["arte"]["paths"] == 32 and grown["arte"]["initial_paths"] == 8
    assert pf["schedule"] == [32]
    assert not pg["met"] and pg["unresolved"] and all(x["kind"] in ("ranking", "catastrophe", "feasibility") for x in pg["unresolved"])
    assert grown["bat"]["hash"] != fixed["bat"]["hash"], "a different sampling plan is a different battery"
    added = [e for e in open(grown["log"].path).read().splitlines() if '"paths_added"' in e]
    assert len(added) == 2, "every extension of the battery is in the ledger"
    assert [x["paths"] for x in pg["looks"]] == [8, 16, 32] and all(x["unresolved"] > 0 for x in pg["looks"])
    assert pg["looks"][-1]["focus_nsv"] == next(r for r in grown["arte"]["results"]["policies"]
                                               if r["policy"] == grown["arte"]["results"]["focus"])["net_social_value"]["mean"]
    assert [r["paths"] for r in grown["arte"]["assurance"]["convergence"]["rows"]] == [8, 16, 32]
    # the grown battery is the fixed one: the same paths, so the same estimates
    for rg, rf in zip(grown["arte"]["results"]["policies"], fixed["arte"]["results"]["policies"]):
        assert rg["policy"] == rf["policy"]
        for k in ("net_social_value", "industry_value_change"):
            assert abs(rg[k]["mean"] - rf[k]["mean"]) < 1e-9, (rg["policy"], k)
        assert abs(rg["safety"]["p_catastrophe"] - rf["safety"]["p_catastrophe"]) < 1e-12
    for n in grown["reds"]:
        assert np.array_equal(grown["reds"][n]["harm_exp"], fixed["reds"][n]["harm_exp"])
    md = draft_briefing(grown["arte"], APPROVALS, "tiny")
    assert "32 paths" in md and "precision" in md.lower()
    # loose targets stop at the first look
    loose = _run(tmp_path / "loose", q, dict(TINY, max_paths=32, precision={"nsv_gap_bn": 1e6, "p_catastrophe_halfwidth": 1.0}, tornado=False))
    pl = loose["arte"]["results"]["precision"]
    assert pl["schedule"] == [8] and pl["met"] and pl["unresolved"] == []


def test_stop_halts_the_run(tmp_path):
    plan = parse("baseline against transparency over two years")
    bat = make_battery(plan, budget=dict(TINY), profile="demo")
    with pytest.raises(SimulationStopped):
        run_battery(bat, str(tmp_path), stop=lambda: True)


def test_replication_across_seeds_reports_spread_and_coverage():
    from replicate import markdown, replicate
    rep = replicate("Compare transparency and strict liability over two years", seeds=4, paths=16, boot=60, first_seed=40)
    assert rep["seeds"] == [40, 41, 42, 43] and rep["horizon"] == 24 and rep["paths"] == 16
    assert sum(rep["decision"]["preferred"].values()) == 4
    rows = {r["policy"]: r for r in rep["rows"]}
    assert set(rows) >= {"baseline", "transparency_disclosure", "strict_liability"}
    for n, r in rows.items():
        x = r["net_social_value"]
        assert x["of"] == 4 and 0 <= x["covered"] <= 4 and x["min"] <= x["pooled_mean"] <= x["max"]
        if n != "baseline":
            assert x["sd_across_seeds"] > 0 and x["mean_reported_se"] > 0 and x["se_ratio"] > 0
        assert 0.0 <= r["preferred_share"] <= 1.0 and 0.0 <= r["p_feasible_mean"] <= 1.0
    assert rows["baseline"]["net_social_value"]["pooled_mean"] == 0.0
    assert abs(sum(r["preferred_share"] for r in rep["rows"]) - 1.0) < 1e-9
    md = markdown(rep)
    assert md.startswith("# Replication across seeds") and "4 independent seeds (40 to 43)" in md and "SD across seeds" in md
    assert "of 4 seeds" in md and "liability" not in md.split("## The estimates")[0].lower().replace("strict liability", "")
    from replicate import expected_coverage
    assert abs(expected_coverage(20) - 0.9439) < 1e-3 and expected_coverage(1000) > 0.949
