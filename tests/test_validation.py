"""The validation layer, the reuse of identical batteries and the optimised engine against its reference."""
import copy
import json
import os

import numpy as np
import pytest

from psl import assumptions as AS
from psl import assurance as ASR
from psl import benchmarks as BM
from psl import stats as ST
from psl import validation as V
from psl.critic import critic_check
from psl.economy import Economy, RandomBundle
from psl.firms import default_firms
from psl.mechanisms import register
from psl.pipeline import make_battery, run_battery
from psl.policies import LIBRARY, library_policy
from psl.question import parse
from psl.briefing import draft_briefing

FIRMS = default_firms()
A = AS.defaults()
SMALL = {"paths": 24, "max_paths": 24, "horizon": 36, "boot": 200, "screen_paths": 2, "joint_draws": 48, "joint_paths": 2,
         "sobol_k": 0, "sobol_base": 0, "variant_paths": 8, "redteam_paths": 8, "batches": 2}


# ------------------------------------------------------------------ the evidence base --
def test_every_built_in_benchmark_is_sourced_and_resolves():
    mech = {m["id"] for m in register()}
    good, problems = BM.validate(BM.load(), mechanism_ids=mech, assumption_keys=set(AS.SPEC), moments=V.MOMENTS)
    assert not problems and len(good) == len(BM.BENCHMARKS) >= 10
    for b in good:
        assert b["sources"] and all(s["cite"] for s in b["sources"]), b["id"]
        assert b["mapping"] and b["caveat"] and b["transport_basis"] and b["se_basis"], b["id"]
        assert b["se"] > 0 and b["transport"] > 0 and abs(b["sd_total"] - np.hypot(b["se"], b["transport"])) < 1e-12
        assert b["instrument"] in (None, "baseline") or library_policy(b["instrument"]), b["id"]
    by = {b["id"]: b for b in good}
    # worked values: the mean of the observations, and their standard error where none is given
    assert abs(by["incident_growth"]["value"] - (0.564 + (362 / 233 - 1)) / 2) < 1e-12
    t = [(53 / 61) ** 0.2 - 1, (35 / 50) ** 0.2 - 1, (50 / 63) ** 0.25 - 1]
    assert abs(by["trust_trend"]["value"] - np.mean(t)) < 1e-12 and abs(by["trust_trend"]["se"] - np.std(t, ddof=1) / np.sqrt(3)) < 1e-12
    assert all(x["why_not"] and x["source"]["cite"] for x in BM.NOT_USED)


def test_a_benchmark_without_a_source_or_with_an_unknown_target_is_refused(tmp_path):
    base = dict(BM.BENCHMARKS[0])
    bad = [dict(base, id="no_source", sources=[]), dict(base, id="bad_moment", moment="nonsense"),
           dict(base, id="bad_mech", mechanisms=["nonsense"]), dict(base, id="one_obs", observations=[{"label": "x", "value": 1.0}], se=None),
           dict(base, id="bad_assumption", moment="assumption", assumption="nonsense"), dict(base, id="ok")]
    good, problems = BM.validate(bad, mechanism_ids={m["id"] for m in register()}, assumption_keys=set(AS.SPEC), moments=V.MOMENTS)
    assert [b["id"] for b in good] == ["ok"] and len(problems) == 5
    # a file extends the built in set by id, or replaces it
    f = tmp_path / "b.json"
    mine = dict(base, id="mine", observations=[{"label": "own data", "value": 0.4}], se=0.05)
    f.write_text(json.dumps({"benchmarks": [mine]}))
    assert {b["id"] for b in BM.load(str(f))} == {b["id"] for b in BM.BENCHMARKS} | {"mine"}
    f.write_text(json.dumps([mine]))
    assert [b["id"] for b in BM.load(str(f))] == ["mine"]
    assert BM.digest(BM.load(str(f))) != BM.digest(BM.load())


# --------------------------------------------------------------------------- moments --
def test_moments_on_known_inputs():
    N, H = 6, 36
    P = {"n_paths": N, "m_inc_exp": np.tile(np.repeat([1.0, 1.5, 2.25], 12) / 12.0, (N, 1)), "trust": np.full((N, H), 0.9 ** 3),
         "compliance": np.full((N, H), 2.0), "m_rd_scope": np.full((N, H), 20.0), "earnings_exp": np.full((N, H), 9.0),
         "m_idx": np.tile(100.0 * 0.99 ** (np.arange(H + 1) >= 13), (N, 1)), "m_fine_ar": np.full(N, -0.03), "m_fine_n": np.full(N, 3.0),
         "m_major_ar": np.zeros(N), "m_major_n": np.zeros(N), "offshore_revenue": np.full((N, H), 1.0), "m_rev_scope": np.full((N, H), 8.0)}
    B = dict(P, earnings_exp=np.full((N, H), 10.0), m_idx=np.full((N, H + 1), 100.0))
    pol = {"phase_in": 12}
    val = lambda name: float(V.moment(name, P, B, pol, H)[0][0])
    assert abs(val("incident_growth") - 0.5) < 1e-12                 # yearly counts 1, 1.5, 2.25
    assert abs(val("trust_trend") - (-0.1)) < 1e-12                  # 0.9 a year
    assert abs(val("compliance_cost_share") - 0.1) < 1e-12
    assert abs(val("profit_effect") - (-0.1)) < 1e-12
    assert abs(val("enforcement_return") - np.log(0.99)) < 1e-12     # the index falls 1% in the month the instrument takes effect
    assert abs(val("fine_return") - (-0.01)) < 1e-12
    assert np.isnan(val("incident_return"))                          # no major incident on these paths: undefined, not zero
    assert abs(val("leakage_share") - 0.125) < 1e-12
    # blocks, and a jackknife variance that is zero for identical paths and positive otherwise
    v, var = V.moment("trust_trend", P, B, pol, H, blocks=3)
    assert v.shape == (3,) and np.allclose(var, 0.0)
    P2 = dict(P, trust=np.linspace(0.6, 0.9, N)[:, None] * np.ones((N, H)))
    assert V.moment("trust_trend", P2, B, pol, H)[1][0] > 0
    assert V.moment("incident_growth", P, B, pol, 12)[0][0] != V.moment("incident_growth", P, B, pol, 12)[0][0]     # one year: NaN
    assert abs(float(V.transform({"name": "recovered_fraction", "months": 9}, 0.05)) - (1 - 0.95 ** 9)) < 1e-12
    assert [V.verdict(z) for z in (0.0, -2.0, 2.5, -3.5, None)] == [V.CONSISTENT, V.CONSISTENT, V.TENSION, V.CONTRADICTED, None]


def _synthetic(D, seed, truth=0.6):
    """A toy posterior with a known answer: one assumption theta drawn uniformly, a moment equal to theta plus noise,
    and a decision that depends on theta alone."""
    rng = np.random.default_rng(seed)
    theta = rng.uniform(0.0, 1.0, D)
    other = rng.uniform(0.0, 1.0, D)
    bench = [BM.resolve({"id": "t", "title": "toy", "mechanisms": ["market"], "kind": "direct", "moment": "trust_trend", "instrument": "baseline",
                         "unit": "share", "observations": [{"label": "o", "value": truth}], "se": 0.05, "transport": 0.0, "sources": [{"cite": "x"}]}),
             BM.resolve({"id": "far", "title": "unreachable", "mechanisms": ["market"], "kind": "analogue", "moment": "profit_effect", "instrument": "baseline",
                         "unit": "share", "observations": [{"label": "o", "value": 9.0}], "se": 0.05, "transport": 0.0, "sources": [{"cite": "x"}]})]
    mom = {"t": (theta + rng.normal(0, 0.02, D), np.full(D, 0.02 ** 2)), "far": (other, np.zeros(D))}
    best = ["a" if t > 0.5 else "b" for t in theta]
    per = {"S": {"theta": theta, "other": other, "acct": rng.uniform(0, 1, D)}, "best": best, "moments": mom,
           "ok": np.ones((2, D), dtype=bool), "nsv": np.stack([theta - 0.5, 0.5 - theta])}
    rows = [{"id": b["id"], "title": b["title"], "mechanisms": b["mechanisms"], "kind": b["kind"], "unit": b["unit"], "observed": b["value"],
             "se": b["se"], "transport": 0.0, "sd_total": b["sd_total"], "model": 0.5, "model_se": 0.0, "z": 0.0, "verdict": V.CONSISTENT,
             "why_not": None} for b in bench]
    return bench, rows, per, theta


def test_weighting_recovers_a_known_parameter_and_leaves_out_what_no_draw_reproduces():
    bench, rows, per, theta = _synthetic(2000, 1)
    rep = V.calibrate(bench, rows, per, ["a", "b"], "a", {"theta": 0.5, "other": 0.5, "acct": 0.5}, accounting_only={"acct"})
    assert rep["used"] == ["t"] and rep["structural"] == ["far"], "the unreachable benchmark is a failure of form and carries no weight"
    w = np.asarray(rep["per_draw"]["weight"])
    assert abs(w.sum() - 1) < 1e-12 and abs(rep["ess"] - 1 / (w ** 2).sum()) < 1e-9 and rep["reliable"]
    post_mean = float((w * theta).sum()); post_sd = float(np.sqrt((w * (theta - post_mean) ** 2).sum()))
    assert abs(post_mean - 0.6) < 0.01 and 0.04 < post_sd < 0.07, (post_mean, post_sd)       # the truth, with the likelihood's spread
    # the decision share moves from one half to nearly one: theta > 0.5 in the posterior
    assert abs(rep["decision_prior"]["a"] - 0.5) < 0.03 and rep["decision_posterior"]["a"] > 0.93
    inf = {m["assumption"]: m for m in rep["assumptions"]}
    assert set(inf) == {"theta"} and inf["theta"]["shrink"] < 0.3, "the benchmark informs theta and nothing else"
    assert rep["not_ruled_out_share"] < 0.5 and rows[0]["held_out"]["ess"] == pytest.approx(2000.0), "held out from itself, the draws are unweighted"
    # the coverage of the posterior over repeated experiments: the truth falls in the 5 to 95% band about nine times in ten
    inside = 0
    for s in range(60):
        truth = 0.2 + 0.6 * (s / 59)
        b2, r2, p2, th = _synthetic(600, 100 + s, truth=truth + np.random.default_rng(s).normal(0, 0.05))
        rr = V.calibrate(b2, r2, p2, ["a", "b"], "a", {"theta": 0.5, "other": 0.5, "acct": 0.5}, accounting_only={"acct"})
        row = next(m for m in rr["assumptions"] if m["assumption"] == "theta")
        inside += int(row["posterior_lo"] <= truth <= row["posterior_hi"])
    assert 46 <= inside <= 60, inside


# -------------------------------------------------------------- through the pipeline --
@pytest.fixture(scope="module")
def run(tmp_path_factory):
    d = tmp_path_factory.mktemp("runs")
    plan = parse("Compare risk tiering, frontier licensing and liability with a safe harbour over three years")
    bat = make_battery(plan, budget=dict(SMALL), profile="test")
    out = str(d / "first")
    events = []
    arte, reds = run_battery(bat, out, log=lambda e, **k: events.append((e, k)))
    return {"dir": str(d), "out": out, "bat": bat, "arte": arte, "events": events}


def test_a_run_reports_every_benchmark_and_the_critic_checks_them(run):
    arte = run["arte"]
    vb = arte["assurance"]["validation"]["benchmarks"]
    assert len(vb["rows"]) == len(BM.BENCHMARKS) and vb["evidence_hash"] == run["bat"]["evidence"] == arte["evidence_hash"]
    assert all((r["verdict"] is None) == (r["model"] is None) and (r["model"] is not None or r["why_not"]) for r in vb["rows"])
    scored = [r for r in vb["rows"] if r["verdict"]]
    assert len(scored) >= 9
    for r in scored:
        z = (r["model"] - r["observed"]) / np.sqrt(r["se"] ** 2 + r["transport"] ** 2 + (r["model_se"] or 0) ** 2)
        assert abs(z - r["z"]) < 1e-9 and r["verdict"] == V.verdict(z)
    cb = vb["calibration"]
    assert cb["draws"] == 48 and abs(sum(cb["per_draw"]["weight"]) - 1) < 1e-9 and 1 <= cb["ess"] <= 48
    assert abs(sum(v for v in cb["decision_posterior"].values() if v) - 1) < 1e-9
    jd = {x["policy"]: x["p_best"] for x in arte["assurance"]["joint"]["alternatives"]}
    assert all(abs(cb["decision_prior"][k] - v) < 1e-12 for k, v in jd.items()), "the unweighted shares are the joint draw's"
    assert "trust_elasticity" not in {m["assumption"] for m in cb["assumptions"]}, "an accounting assumption cannot be informed by a simulated moment"
    # the register carries the evidence; mechanisms without a benchmark say so
    reg = {m["id"]: m for m in arte["mechanisms"]}
    assert reg["adoption_and_trust"]["confronted"] and not reg["severity"]["confronted"] and reg["severity"]["benchmarks"] == []
    assert set(vb["summary"]["mechanisms_unconfronted"]) >= {"severity", "catastrophic_tail"}
    md = draft_briefing(arte, {"preparer": "t"}, "first")
    assert "Validation against published evidence" in md and "The evidence the model was confronted with" in md
    for r in vb["rows"]:
        if r["verdict"] in (V.TENSION, V.CONTRADICTED):
            assert r["title"] in md
    critic = critic_check(run["out"], secret=None, briefing_text=md)
    names = [c["check"] for c in critic["checks"]]
    assert critic["ok"], [c for c in critic["checks"] if not c["ok"]]
    for want in ("benchmark verdicts follow from the observed and modelled values", "weighted decision shares reproduce from the stored draws and weights",
                 "the evidence base is the one approved at Gate 1", "every benchmark carries a source, a mapping and a transport allowance"):
        assert want in names
    # a tampered verdict or weight is caught
    p = os.path.join(run["out"], "artefacts.json")
    orig = open(p).read()
    doc = json.loads(orig)
    doc["assurance"]["validation"]["benchmarks"]["calibration"]["per_draw"]["weight"][0] += 0.2
    open(p, "w").write(json.dumps(doc))
    try:
        assert not critic_check(run["out"], secret=None, briefing_text=md)["ok"]
    finally:
        open(p, "w").write(orig)


def test_an_identical_battery_is_reused_and_a_changed_one_is_not(run):
    second = os.path.join(run["dir"], "second")
    events = []
    ticks = []
    arte2, reds2 = run_battery(run["bat"], second, log=lambda e, **k: events.append(e), stream=lambda kind, p: ticks.append(kind), reuse=True)
    assert reds2 is None and "battery_reused" in events and arte2["run"]["reused_from"]["run"] == "first"
    assert ticks.count("tick") == 4 * 36 and ticks.count("policy_done") == 4 and ticks[-1] == "evaluated"
    for name in ("results.json", "assurance.json", "paths.json", "paths.npz"):
        assert open(os.path.join(run["out"], name), "rb").read() == open(os.path.join(second, name), "rb").read(), name
    md = draft_briefing(arte2, {"preparer": "t"}, "second")
    assert "reused here" in md and critic_check(second, secret=None, briefing_text=md)["ok"]
    # without the switch, or with anything in the battery changed, the run is computed
    third = os.path.join(run["dir"], "third")
    ev3 = []
    bat3 = make_battery(parse("Compare risk tiering, frontier licensing and liability with a safe harbour over three years"),
                        budget=dict(SMALL, joint_draws=16), profile="test", assumptions={"discount_rate": 0.04})
    assert bat3["hash"] != run["bat"]["hash"]
    arte3, reds3 = run_battery(bat3, third, log=lambda e, **k: ev3.append(e), reuse=True)
    assert reds3 is not None and "battery_reused" not in ev3 and "reused_from" not in arte3["run"]
    # another evidence base is another battery
    mine = [dict(BM.BENCHMARKS[0])]
    q = parse("Compare risk tiering over three years")
    assert make_battery(q, budget=dict(SMALL), benchmarks=mine)["hash"] != make_battery(q, budget=dict(SMALL))["hash"]


# ------------------------------------------------------- the engine against its reference --
def _same(r1, r2):
    for k, v in r1.__dict__.items():
        w = r2.__dict__[k]
        if isinstance(v, np.ndarray):
            if not np.array_equal(v, w, equal_nan=True):
                return k
        elif k == "series":
            for kk in v:
                if not np.array_equal(v[kk], w[kk]):
                    return "series." + kk
        elif k == "events0" and v != w:
            return k
    return None


def test_the_optimised_decision_is_the_reference_decision_bit_for_bit():
    """Every library instrument, a structural variant, every gaming strategy and a design with one value per path:
    the routine that computes each term on its own action axes returns exactly what the full grid of 48 actions returns."""
    N, H = 24, 30
    names = list(LIBRARY) if isinstance(LIBRARY, dict) else [p["name"] for p in LIBRARY]
    D = AS.sample(N, seed=3, base=A)
    a_des = dict(A, **{k: np.asarray(v, dtype=float) for k, v in D.items()})
    firms2 = copy.deepcopy(FIRMS)
    firms2[1]["sector"] = firms2[0]["sector"]                        # a shared sector, so contagion is live
    cases = [(nm, FIRMS, A, {}) for nm in names]
    cases += [(nm, firms2, a_des, {}) for nm in ("baseline", "liability_with_safe_harbour", "frontier_licensing", "moratorium", "export_controls")]
    cases += [("liability_with_safe_harbour", FIRMS, A, {"variant": spec}) for spec in ASR.STRUCTURAL.values()]
    cases += [(nm, FIRMS, A, {"gaming": spec}) for spec in ASR.GAMING.values() for nm in ("risk_tiering", "coordinated_licensing")]
    for nm, firms, a, kw in cases:
        rb = RandomBundle(N, H, len(firms), 7)
        new = Economy(firms, a, horizon=H, n_paths=N, seed=7, bundle=rb).run(library_policy(nm), **kw)
        ref = Economy(firms, a, horizon=H, n_paths=N, seed=7, bundle=rb, reference=True).run(library_policy(nm), **kw)
        assert _same(ref, new) is None, (nm, list(kw), _same(ref, new))


def test_the_catastrophe_integral_skips_only_what_is_exactly_zero():
    """any_event_probability evaluates the normal distribution only for firms with a live tail; the result is the
    integral over every firm, bit for bit, for a scalar correlation and for one value per path."""
    from scipy.special import ndtr, ndtri
    rng = np.random.default_rng(4)
    x, w = ST.hermite(24)
    for rho in (0.3, rng.uniform(0.05, 0.8, 200)):
        p = rng.uniform(0, 0.01, (200, 8)) * (rng.random((200, 8)) < 0.4)
        p[rng.random(200) < 0.3] = 0.0
        p[0, 0] = 1.0
        r = np.asarray(rho, dtype=float)
        sr, s1 = np.sqrt(np.clip(r, 0, 0.999999)), np.sqrt(1 - np.clip(r, 0, 0.999999))
        if r.ndim:
            sr, s1 = sr[:, None, None], s1[:, None, None]
        with np.errstate(divide="ignore"):
            full = 1.0 - np.prod(1.0 - ndtr((ndtri(p)[..., None] - sr * x) / s1), axis=-2) @ w
        assert np.array_equal(ST.any_event_probability(p, rho, (x, w)), full)
