"""Statistical regression tests: the properties the decision and its uncertainty statements rest on.

  the decision rule     the status quo is an alternative and is never displaced by an instrument worse than it; ties
                        share a rank and go to the status quo; gross cost is never negative
  the estimators        the conditional estimators have the expectation of the frequencies they replace and a
                        fraction of their variance; correlated catastrophes integrate to the brute force probability
  the intervals         the bootstrap standard error is the analytic one on a known case; a run's interval covers
                        the value from independent seeds about as often as it says; feasibility at a boundary is
                        reported as uncertain, not as a fact
  the designs           Latin hypercube margins, the copula's correlations, Sobol indices on functions whose
                        indices are known
  the event study       one event time convention, the full estimation window or a refusal, a test of the right
                        size, and a data desk that refuses what would corrupt it
"""

import os
import sys

import numpy as np
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from psl import assumptions as AS  # noqa: E402
from psl import stats as ST  # noqa: E402
from psl import welfare as W  # noqa: E402
from psl.evaluate import ASSURED_P, decide, evaluate, precision  # noqa: E402
from psl.firms import default_firms  # noqa: E402
from psl.ingest import quarantine  # noqa: E402
from psl.policies import library_policy  # noqa: E402
from psl.reduce import conditional_catastrophe, simulate_battery  # noqa: E402
from psl.validation import EST_WINDOW, EVENT_WINDOW, event_study  # noqa: E402


def _battery(names, n, h=24, seed=7, a=None, extra=None):
    a = a or AS.defaults()
    pols = {k: library_policy(k) for k in names}
    pols.update(extra or {})
    d = W.discount(h, a["discount_rate"])
    return simulate_battery(pols, default_firms(), a, h, n, seed, discount_f=d), a


# ------------------------------------------------------------ the decision rule --
def test_a_policy_worse_than_the_status_quo_is_never_recommended():
    # on a table of means: the status quo scores zero and wins over every negative option
    M = {k: np.zeros(3) for k in ("net_social_value",) + W.COMPONENTS + ("industry_value_change", "cat_cmc", "major_any", "headline")}
    M["net_social_value"] = np.array([0.0, -77.4, -98.8])
    d = decide(["baseline", "risk_tiering", "moratorium"], M, {})
    assert d["preferred"] == "baseline" and d["best_intervention"] == "risk_tiering"
    # a tie between the status quo and an instrument goes to the status quo
    M["net_social_value"] = np.array([0.0, 0.0, -1.0])
    assert decide(["baseline", "a", "b"], M, {})["preferred"] == "baseline"
    # an infeasible status quo cannot be preferred; nothing feasible gives no preferred alternative
    M["net_social_value"] = np.array([0.0, -5.0, -9.0]); M["cat_cmc"] = np.array([0.2, 0.05, 0.3])
    assert decide(["baseline", "a", "b"], M, {"max_p_catastrophe": 0.1})["preferred"] == "a"
    assert decide(["baseline", "a", "b"], M, {"max_p_catastrophe": 0.01})["preferred"] is None

    # the status quo wins a tie wherever it is listed: an instrument identical to it never displaces it
    a0 = AS.defaults()
    twin = dict(library_policy("baseline"), name="status_quo_twin", label="A copy of the status quo")
    reds0 = simulate_battery({"status_quo_twin": twin, "baseline": library_policy("baseline")}, default_firms(), a0, 12, 8, 7,
                             discount_f=W.discount(12, a0["discount_rate"]))
    ev0, _, _ = evaluate(reds0, a0, {}, boot=50, seed=1)
    assert ev0["names"][0] == "baseline" and ev0["preferred"] == "baseline" and ev0["best_intervention"] == "status_quo_twin"
    assert "is worth no more than the status quo" in ev0["decision"]["text"]

    # end to end: the battery the review used, in which every instrument destroys value
    reds, a = _battery(("baseline", "risk_tiering", "moratorium"), 24)
    ev, arr, bt = evaluate(reds, a, {}, boot=200, seed=1)
    by = {r["policy"]: r for r in ev["policies"]}
    assert by["risk_tiering"]["net_social_value"]["mean"] < 0 and by["moratorium"]["net_social_value"]["mean"] < 0
    assert ev["preferred"] == "baseline" and ev["decision"]["is_status_quo"] and not ev["decision"]["improves_on_status_quo"]
    assert ev["best_intervention"] == "risk_tiering" and ev["focus"] == "risk_tiering"
    assert "No tested instrument improves on the status quo" in ev["decision"]["text"]
    assert "not distinguishable" not in ev["decision"]["text"], "here the best instrument is clearly worse than doing nothing"
    assert by["baseline"]["net_social_value"]["mean"] == 0.0 and by["baseline"]["p_best"] == 1.0
    assert by["risk_tiering"]["net_social_value"]["p_improves"] == 0.0
    assert by["risk_tiering"]["vs_preferred"]["difference"] > 0 and by["risk_tiering"]["vs_preferred"]["distinguishable"]


def test_gross_cost_is_never_negative_and_reconciles_with_the_net_value():
    reds, a = _battery(("baseline", "transparency_disclosure", "strict_liability", "liability_with_safe_harbour", "moratorium"), 16)
    ev, arr, bt = evaluate(reds, a, {}, boot=100, seed=1)
    for r in ev["policies"]:
        gc, gb, nsv = r["gross_cost"]["mean"], r["gross_benefit"]["mean"], r["net_social_value"]["mean"]
        assert gc >= 0 and gb >= 0 and r["gross_cost"]["ci_lo"] >= 0, r["policy"]
        assert abs(gb - gc - nsv) < 1e-8, r["policy"]
        comp = {k: r["components"][k]["mean"] for k in W.COMPONENTS}
        assert abs(W.net_from(comp) - nsv) < 1e-8, r["policy"]
        cost_lines = sum(max(0.0, comp[k]) for k in W.COSTS) + sum(max(0.0, -comp[k]) for k in W.BENEFITS)
        assert abs(cost_lines - gc) < 1e-8, "one definition of gross cost: every line that reduces welfare"
        assert abs(r["incidence_total"] - nsv - r["nonresident_payments"]) < 1e-8, r["policy"]


def test_identical_policies_share_a_rank_and_ties_do_not_move_tau():
    assert list(ST.rank_desc([3.0, 3.0, 1.0])) == [1, 1, 3]
    assert list(ST.rank_desc([1.0, 2.0 + 1e-13, 2.0])) == [3, 1, 1], "equal up to floating point noise is a tie"
    assert ST.kendall_tau_b([1, 2, 3, 4], [1, 2, 3, 4]) == 1.0 and ST.kendall_tau_b([1, 2, 3, 4], [4, 3, 2, 1]) == -1.0
    assert ST.kendall_tau_b([1, 1, 1], [1, 2, 3]) == 0.0, "no variation, no association"
    # tau a would give 5/6 here; tau b corrects for the tie in the first vector: 5 / sqrt(5 x 6)
    assert abs(ST.kendall_tau_b([1, 1, 2, 3], [1, 2, 3, 4]) - 5 / np.sqrt(30)) < 1e-12
    # the order of the tied pair does not matter
    assert abs(ST.kendall_tau_b([1, 1, 2, 3], [2, 1, 3, 4]) - ST.kendall_tau_b([1, 1, 2, 3], [1, 2, 3, 4])) < 1e-12

    twin = dict(library_policy("transparency_disclosure"), name="twin", label="Twin of transparency")
    for order in (("transparency_disclosure", "twin"), ("twin", "transparency_disclosure")):
        pols = {"baseline": library_policy("baseline")}
        for n in order:
            pols[n] = twin if n == "twin" else library_policy(n)
        pols["moratorium"] = library_policy("moratorium")
        a = AS.defaults()
        reds = simulate_battery(pols, default_firms(), a, 24, 16, 7, discount_f=W.discount(24, a["discount_rate"]))
        ev, arr, bt = evaluate(reds, a, {}, boot=100, seed=1)
        by = {r["policy"]: r for r in ev["policies"]}
        t, w = by["transparency_disclosure"], by["twin"]
        assert t["net_social_value"]["mean"] == w["net_social_value"]["mean"]
        for k in ("rank_social", "rank_headline", "rank_harm", "rank_industry"):
            assert t[k] == w[k], (k, order)
        assert t["rank_social"] == 1 and by["moratorium"]["rank_social"] == 3, "competition ranks: 1, 1, 3"
        assert ev["preferred"] == order[0], "a tie is broken by the declared order, and reported as a tie"
        other = by[order[1]]["vs_preferred"]
        assert other["difference"] == 0.0 and not other["distinguishable"] and other["in_confidence_set"]
        assert order[1] in ev["decision"]["confidence_set"]


def test_feasibility_at_a_boundary_is_reported_as_uncertain():
    names = ("baseline", "transparency_disclosure", "liability_with_safe_harbour")
    reds, a = _battery(names, 48, h=36)
    ev0, arr, bt = evaluate(reds, a, {}, boot=400, seed=3)
    by0 = {r["policy"]: r for r in ev0["policies"]}
    loss = -by0["liability_with_safe_harbour"]["industry_value_change"]["mean"]
    assert loss > 50, "the instrument costs the industry something on this sample"
    # the limit placed on the estimate itself: about half the resamples fall on each side
    ev, _, _ = evaluate(reds, a, {"max_industry_loss_bn": loss}, boot=400, seed=3)
    r = {x["policy"]: x for x in ev["policies"]}["liability_with_safe_harbour"]
    assert r["feasible"] and 0.3 < r["p_feasible"] < 0.7
    chk = r["constraint_checks"][0]
    assert chk["constraint"] == "max_industry_loss_bn" and abs(chk["margin"]) < 1e-9 and chk["ci_lo"] < loss < chk["ci_hi"]
    assert "liability_with_safe_harbour" in ev["decision"]["feasibility_uncertain"]
    assert r["p_feasible"] < ASSURED_P and ev["decision"]["preferred_assured"] != "liability_with_safe_harbour"
    if ev["preferred"] == "liability_with_safe_harbour":
        assert any(x["kind"] == "feasibility" and x["policy"] == "liability_with_safe_harbour" for x in precision(ev, {}))
        assert "conservative rule" in ev["decision"]["text"]
    # far inside and far outside the limit the resamples agree
    ev_in, _, _ = evaluate(reds, a, {"max_industry_loss_bn": loss * 3}, boot=400, seed=3)
    ev_out, _, _ = evaluate(reds, a, {"max_industry_loss_bn": loss / 3}, boot=400, seed=3)
    assert {x["policy"]: x for x in ev_in["policies"]}["liability_with_safe_harbour"]["p_feasible"] == 1.0
    out = {x["policy"]: x for x in ev_out["policies"]}["liability_with_safe_harbour"]
    assert out["p_feasible"] == 0.0 and not out["feasible"] and ev_out["preferred"] != "liability_with_safe_harbour"
    # the status quo is within any limit on industry loss, in every resample
    assert {x["policy"]: x for x in ev_out["policies"]}["baseline"]["p_feasible"] == 1.0


# --------------------------------------------------------------- the estimators --
@pytest.fixture(scope="module")
def large():
    """2,400 paths over three years: the status quo and a liability instrument without an insurance mandate, so the
    liability a firm pays is drawn with the incidents."""
    a = AS.defaults()
    uninsured = dict(library_policy("strict_liability"), name="uninsured_liability", label="Strict liability, uninsured", insurance_mandate=False)
    pols = {"baseline": library_policy("baseline"), "uninsured_liability": uninsured}
    return simulate_battery(pols, default_firms(), a, 36, 2400, 21, full=False), a


def _paired_z(x, y):
    d = np.asarray(x) - np.asarray(y)
    return float(d.mean() / (d.std(ddof=1) / np.sqrt(d.size)))


def test_conditional_estimators_are_unbiased_and_far_tighter(large):
    reds, a = large
    for name, R in reds.items():
        assert 60 < R["cat_any"].sum() < 400, "enough catastrophes for the comparison to mean something"
        # P(at least one catastrophe): the accumulated hazard up to the first one against the 0/1 indicator
        assert abs(_paired_z(R["cat_cmc"], R["cat_any"])) < 3.5, name
        assert R["cat_cmc"].var() < 0.02 * R["cat_any"].var(), "the conditional estimator removes most of the variance"
        # expected harm given the state against the harm drawn
        assert abs(_paired_z(R["harm_exp"].sum(axis=1), R["harm"].sum(axis=1))) < 3.5, name
        assert abs(_paired_z(R["cat_harm_exp"].sum(axis=1), R["cat_harm"].sum(axis=1))) < 3.5, name
        assert R["harm_exp"].sum(axis=1).var() < 0.02 * R["harm"].sum(axis=1).var()
    # the liability a firm pays: expected given the state against drawn
    U = reds["uninsured_liability"]
    assert U["liability"].sum() > 0 and not np.allclose(U["earnings_exp"], U["earnings"])
    assert abs(_paired_z(U["earnings_exp"].sum(axis=1), U["earnings"].sum(axis=1))) < 3.5
    assert np.array_equal(reds["baseline"]["earnings_exp"], reds["baseline"]["earnings"]), "no liability, nothing to replace"
    # the estimator counts the hazard of a month only on paths with no catastrophe before it
    n_cat = np.array([[0, 1, 0, 1], [0, 0, 0, 0]]); p = np.array([[0.1, 0.2, 0.3, 0.4], [0.1, 0.2, 0.3, 0.4]])
    assert np.allclose(conditional_catastrophe(n_cat, p), [0.1 + 0.2, 1.0])


def test_wilson_and_bootstrap_intervals_on_known_cases():
    lo, hi = ST.wilson(0, 60)
    assert lo == 0.0 and 0.05 < hi < 0.07, "no events in 60 paths is not a probability of zero"
    lo, hi = ST.wilson(12, 60)
    assert abs(lo - 0.1184) < 2e-3 and abs(hi - 0.3176) < 2e-3
    l2, h2 = ST.wilson(11, 60)
    assert l2 < 12 / 60 < h2 and lo < 11 / 60 < hi, "12 of 60 and 11 of 60 cannot be told apart"
    rng = np.random.default_rng(5)
    x = rng.normal(3.0, 2.0, size=400)
    bt = ST.Boot(400, 2000, seed=1)
    m, se, lo, hi = bt.ci(x)
    assert abs(m - x.mean()) < 1e-12 and abs(se / (x.std(ddof=1) / 20.0) - 1.0) < 0.06
    assert abs((hi - lo) / (2 * 1.96 * se) - 1.0) < 0.08 and lo < m < hi
    assert np.allclose(bt.w.sum(axis=1), 1.0) and bt.means(np.ones(400)).std() < 1e-12
    # one set of resamples for every quantity: the bootstrap of a difference is the difference of the bootstraps
    y = x + rng.normal(0.5, 0.1, size=400)
    assert np.allclose(bt.means(y - x), bt.means(y) - bt.means(x))
    assert bt.means(y - x).std() < 0.1 * bt.means(y).std(), "pairing removes the common variation"


def test_an_interval_covers_independent_seeds_about_as_often_as_it_says():
    a = AS.defaults()
    names = ("baseline", "transparency_disclosure", "liability_with_safe_harbour")
    pols = {n: library_policy(n) for n in names}
    firms = default_firms()
    K, N, H = 14, 60, 36
    est = {n: [] for n in names[1:]}
    for s in range(1, K + 1):
        reds = simulate_battery(pols, firms, a, H, N, 300 + s, full=False)
        bt = ST.Boot(N, 400, seed=s)
        for n in names[1:]:
            est[n].append(bt.ci(W.components(reds[n], reds["baseline"], a)["net_social_value"]))
    covered = total = 0
    for n, rows in est.items():
        m = np.array([r[0] for r in rows]); se = np.array([r[1] for r in rows])
        others = (m.sum() - m) / (K - 1)
        covered += int(sum(r[2] <= o <= r[3] for r, o in zip(rows, others))); total += K
        assert 0.5 < m.std(ddof=1) / se.mean() < 1.6, (n, "the spread across seeds is the standard error a run reports")
    assert covered >= total - 5, f"{covered} of {total} intervals cover the mean of the other seeds"


def test_correlated_catastrophes_integrate_to_the_brute_force_probability():
    p = np.array([0.002, 0.004, 0.001, 0.003, 0.0005, 0.006, 0.002, 0.001]) * 10
    assert abs(ST.any_event_probability(p, 0.0) - (1 - np.prod(1 - p))) < 1e-15
    rng = np.random.default_rng(11)
    n = 1_500_000
    for rho in (0.3, 0.8):
        z = rng.standard_normal((n, 1)); e = rng.standard_normal((n, p.size))
        hit = (np.sqrt(rho) * z + np.sqrt(1 - rho) * e) < ST.ndtri(p)[None, :]
        brute = hit.any(axis=1).mean()
        se = np.sqrt(brute * (1 - brute) / n)
        q = float(ST.any_event_probability(p, rho))
        assert abs(q - brute) < 4 * se, (rho, q, brute)
        assert q < 1 - np.prod(1 - p), "positive correlation: the same marginals, fewer paths with any event"
        assert np.allclose(hit.mean(axis=0), p, atol=4 * np.sqrt(p * (1 - p) / n).max()), "the marginals are untouched"
        # the conditional probabilities average back to the marginals
        x, w = ST.hermite(48)
        cond = np.stack([ST.conditional_event_probability(p, rho, np.array(zz)) for zz in x])
        assert np.allclose(w @ cond, p, rtol=2e-3)
    # one correlation per path, and zero marginals
    P = np.vstack([p, p, np.zeros_like(p)])
    out = ST.any_event_probability(P, np.array([0.3, 0.8, 0.3]))
    assert abs(out[0] - ST.any_event_probability(p, 0.3)) < 1e-12 and abs(out[1] - ST.any_event_probability(p, 0.8)) < 1e-12 and out[2] == 0.0


def test_catastrophe_correlation_changes_clustering_not_the_marginal_rate():
    firms = default_firms()
    pol = {"baseline": library_policy("baseline")}
    out = {}
    for rho in (0.0, 0.8):
        a = AS.defaults(); a["catastrophe_correlation"] = rho; a["catastrophe_prior_monthly"] = 0.01
        out[rho] = simulate_battery(pol, firms, a, 36, 1500, 9, full=False)["baseline"]
    ind, cor = out[0.0], out[0.8]
    # expected catastrophe harm depends on the marginal hazards only
    assert abs(cor["cat_harm_exp"].sum() / ind["cat_harm_exp"].sum() - 1.0) < 0.03
    # with a shared shock the same catastrophes fall on fewer paths, several firms at once
    assert cor["cat_cmc"].mean() < 0.9 * ind["cat_cmc"].mean()
    multi = lambda R: float((R["n_cat"] >= 2).sum() / max((R["n_cat"] >= 1).sum(), 1))
    assert multi(cor) > 3 * max(multi(ind), 0.005)


# ----------------------------------------------------------------- the designs --
def test_latin_hypercube_copula_and_triangular_margins():
    u = ST.latin_hypercube(200, 5, seed=3)
    assert u.shape == (200, 5) and u.min() >= 0 and u.max() <= 1
    for j in range(5):
        assert np.array_equal(np.sort(np.floor(u[:, j] * 200).astype(int)), np.arange(200)), "one point in each stratum"
    corr = np.eye(5); corr[0, 1] = corr[1, 0] = 0.6
    v = ST.gaussian_copula(ST.latin_hypercube(4000, 5, seed=4), corr)
    assert abs(ST.spearman(v[:, 0], v[:, 1]) - 0.58) < 0.05 and abs(ST.spearman(v[:, 0], v[:, 2])) < 0.05
    assert abs(v[:, 1].mean() - 0.5) < 0.02 and abs(np.percentile(v[:, 1], 25) - 0.25) < 0.02, "the margins stay uniform"
    x = ST.triangular_ppf(np.array([0.0, 0.25, 1.0]), 0.0, 1.0, 4.0)
    assert x[0] == 0.0 and x[2] == 4.0 and abs(x[1] - 1.0) < 1e-12, "a quarter of the mass lies below the mode at 1 on [0, 4]"
    draws = ST.triangular_ppf(ST.latin_hypercube(20000, 1, seed=5)[:, 0], 2.0, 3.0, 7.0)
    assert abs(draws.mean() - (2 + 3 + 7) / 3) < 0.01 and draws.min() >= 2.0 and draws.max() <= 7.0


def test_sobol_indices_recover_known_functions():
    # additive: Y = 4 X1 + 2 X2 + X3, X uniform: first order = total = a_i^2 / sum a^2
    A, B, ABs = ST.saltelli(2048, 3, seed=1)
    f = lambda U: 4 * U[:, 0] + 2 * U[:, 1] + U[:, 2]
    s1, st = ST.sobol_indices(f(A), f(B), [f(x) for x in ABs])
    want = np.array([16, 4, 1]) / 21.0
    assert np.allclose(s1, want, atol=0.03) and np.allclose(st, want, atol=0.03)
    # Ishigami (a = 7, b = 0.1): interactions between X1 and X3, none for X2
    A, B, ABs = ST.saltelli(8192, 3, seed=2)
    g = lambda U: (lambda x: np.sin(x[:, 0]) + 7 * np.sin(x[:, 1]) ** 2 + 0.1 * x[:, 2] ** 4 * np.sin(x[:, 0]))(-np.pi + 2 * np.pi * U)
    s1, st = ST.sobol_indices(g(A), g(B), [g(x) for x in ABs])
    assert np.allclose(s1, [0.3139, 0.4424, 0.0], atol=0.03), s1
    assert np.allclose(st, [0.5576, 0.4424, 0.2437], atol=0.03), st
    # a constant output has no variance to share
    s1, st = ST.sobol_indices(np.ones(64), np.ones(64), [np.ones(64)] * 3)
    assert not s1.any() and not st.any()
    # a large mean does not disturb the first order estimator (it is centred)
    A, B, ABs = ST.saltelli(1024, 3, seed=3)
    s1, st = ST.sobol_indices(1e4 + f(A), 1e4 + f(B), [1e4 + f(x) for x in ABs])
    assert np.allclose(s1, want, atol=0.04) and np.allclose(st, want, atol=0.04)
    # bootstrap intervals over the base sample: they bracket the estimates, narrow with the design, and cover the truth
    widths = []
    for m in (128, 2048):
        A, B, ABs = ST.saltelli(m, 3, seed=4)
        out = (f(A), f(B), [f(x) for x in ABs])
        s1, st = ST.sobol_indices(*out)
        l1, h1, lt, ht = ST.sobol_intervals(*out, b=200, seed=1)
        assert np.all(l1 <= s1 + 1e-12) and np.all(s1 <= h1 + 1e-12) and np.all(lt <= st + 1e-12) and np.all(st <= ht + 1e-12)
        assert np.all(lt - 0.02 <= want) and np.all(want <= ht + 0.02)
        widths.append(float((ht - lt).mean()))
    assert widths[1] < 0.5 * widths[0]


def test_false_discovery_control_and_filtering():
    # Benjamini and Hochberg on a worked case: thresholds k q / m = 0.005, 0.010, 0.015, ...
    p = [0.001, 0.008, 0.039, 0.041, 0.042, 0.060, 0.074, 0.205, 0.212, 0.216]
    assert list(ST.benjamini_hochberg(p, q=0.05)) == [True, True] + [False] * 8
    assert list(ST.benjamini_hochberg(p[::-1], q=0.05)) == [False] * 8 + [True, True], "the answer follows the tests, not their order"
    assert not ST.benjamini_hochberg([0.2, 0.5, 0.9], q=0.1).any() and ST.benjamini_hochberg([], 0.1).size == 0
    # a step up procedure: a later p value under its threshold carries the earlier ones with it
    assert list(ST.benjamini_hochberg([0.04, 0.045, 0.05], q=0.05)) == [True, True, True]
    # pure noise: 67 assumptions against an unrelated output; over 200 repetitions a discovery is rare
    rng = np.random.default_rng(8)
    false_alarms = 0
    for _ in range(200):
        y = rng.normal(size=64)
        pv = [ST.spearman_test(rng.normal(size=64), y)[1] for _ in range(67)]
        false_alarms += int(ST.benjamini_hochberg(pv, q=0.10).any())
    assert false_alarms <= 0.16 * 200, false_alarms
    # a real driver is found among them
    x = rng.normal(size=64)
    y = 2.0 * x + rng.normal(size=64)
    pv = [ST.spearman_test(x, y)[1]] + [ST.spearman_test(rng.normal(size=64), y)[1] for _ in range(66)]
    assert ST.benjamini_hochberg(pv, q=0.10)[0]
    assert ST.spearman_test(np.ones(10), np.arange(10.0)) == (0.0, 1.0)
    # Monte Carlo filtering: the assumption that separates the two groups of draws, and not one that does not
    flag = x > 0.3
    ks, pk = ST.ks_split(x, flag)
    assert ks == 1.0 and pk < 1e-6
    ks0, p0 = ST.ks_split(rng.normal(size=64), flag)
    assert ks0 < 0.5 and p0 > 0.01
    assert ST.ks_split(x, x > 10) == (0.0, 1.0), "fewer than five draws in a group: nothing is claimed"


# -------------------------------------------------------------- the event study --
def _series(n=40, event=30, jump=-0.08, drift=0.004, noise=0.0, seed=0, market=False):
    rng = np.random.default_rng(seed)
    m = rng.normal(0.006, 0.04, size=n - 1)
    eps = rng.normal(0.0, noise, size=n - 1) if noise else np.zeros(n - 1)
    r = drift + (1.2 * m if market else 0.0) + eps
    r[event - 1] += jump                              # r[k - 1] is the return of month k
    p = 100.0 * np.exp(np.concatenate([[0.0], np.cumsum(r)]))
    mk = 100.0 * np.exp(np.concatenate([[0.0], np.cumsum(m)]))
    return p, (mk if market else None)


def test_event_study_uses_one_convention_and_the_full_window():
    assert EST_WINDOW == 24 and EVENT_WINDOW == 6
    p, _ = _series()
    es = event_study(p, 30)
    assert es["n_est"] == 24 and es["window_months"] == [0, 5] and es["model"] == "mean adjusted"
    assert abs(es["car"] + 0.08) < 1e-12, "a jump in the event month is in the event window, and all of it"
    assert abs(es["early_reaction"] - (np.exp(-0.08) - 1)) < 1e-12 and abs(es["alpha"] - 0.004) < 1e-12
    # the event month is month 0: a jump one month earlier is in the estimation window, not in the event window
    p2, _ = _series(event=29)
    assert abs(event_study(p2, 30)["car"]) < 0.01 + 6 * 0.08 / 24
    # exactly 24 returns before the event month are required; fewer is a refusal, never a shorter window
    assert "refused" in event_study(p[5:], 24) and "24 monthly returns" in event_study(p[5:], 24)["refused"]
    assert event_study(p[5:], 25)["n_est"] == 24
    assert "refused" in event_study(p[:35], 30), "the event window needs months 0 to 5"
    assert event_study(p[:36], 30)["n_est"] == 24
    # zero, negative and missing prices are refused, not turned into NaN
    for bad in (0.0, -3.0, np.nan, np.inf):
        q = p.copy(); q[10] = bad
        assert "refused" in event_study(q, 30), bad
    # the market model recovers alpha and beta and removes the market from the abnormal return
    pm, mk = _series(market=True)
    em = event_study(pm, 30, market=mk)
    assert em["model"] == "market model" and abs(em["beta"] - 1.2) < 1e-9 and abs(em["alpha"] - 0.004) < 1e-9 and abs(em["car"] + 0.08) < 1e-9
    assert "refused" in event_study(pm, 30, market=mk[:-1])
    # standard errors: the mean adjusted case in closed form
    pn, _ = _series(noise=0.05, seed=3)
    en = event_study(pn, 30)
    assert abs(en["se_car"] - en["resid_sd"] * np.sqrt(6 + 36 / 24)) < 1e-12 and abs(en["t_car"] - en["car"] / en["se_car"]) < 1e-12


def test_event_study_test_has_the_right_size():
    # no event at all: the t statistic should reject at about the nominal rate (a t with 23 degrees of freedom
    # against 1.96 rejects 6.2% of the time)
    rej = {False: 0, True: 0}
    n = 1500
    for s in range(n):
        for market in (False, True):
            p, mk = _series(jump=0.0, noise=0.05, seed=1000 + s, market=market)
            es = event_study(p, 30, market=mk)
            rej[market] += int(abs(es["t_car"]) > 1.96)
    for market, k in rej.items():
        assert 0.04 < k / n < 0.09, (market, k / n)


def _csv(months, prices, market=None):
    rows = ["date,price" + (",market" if market is not None else "")]
    for i, (m, p) in enumerate(zip(months, prices)):
        rows.append(f"{m},{p}" + (f",{market[i]}" if market is not None else ""))
    return ("\n".join(rows) + "\n").encode()


def _months(n, start=(2021, 1)):
    y, m = start
    out = []
    for _ in range(n):
        out.append(f"{y:04d}-{m:02d}")
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return out


def test_the_data_desk_refuses_what_would_corrupt_an_estimate():
    months = _months(40)
    p, mk = _series(noise=0.03, seed=2, market=True)
    good = quarantine("ok.csv", _csv(months, np.round(p, 4), np.round(mk, 4)), classification="synthetic", event_date=months[30],
                      maps_to="chip_designer", analogue_of="risk_tiering")
    assert good["ok"] and good["event_study"]["n_est"] == 24 and good["event_study"]["event_month"] == months[30]
    assert good["analogue_of"] == "risk_tiering"
    # calibration is held out from the event: only the months before it
    assert good["stats"]["held_out_from_event"] and good["stats"]["calibration_months"] == 30 and good["stats"]["n_months"] == 40
    # a zero or negative price
    for bad in ("0", "-12.5", "nan"):
        q = [str(x) for x in np.round(p, 4)]; q[7] = bad
        r = quarantine("bad.csv", _csv(months, q), classification="synthetic")
        assert not r["ok"] and "positive" in r["reason"], bad
    # a gap in the months
    gap = months[:15] + months[16:]
    r = quarantine("gap.csv", _csv(gap, np.round(np.delete(p, 15), 4)), classification="synthetic")
    assert not r["ok"] and "gap" in r["reason"] and months[14] in r["reason"]
    # dates that are not ISO dates (a day first date would silently become another month)
    ambiguous = [f"{m[5:7]}/01/{m[:4]}" for m in months]
    r = quarantine("dates.csv", _csv(ambiguous, np.round(p, 4)), classification="synthetic")
    assert not r["ok"] and "ISO" in r["reason"]
    r = quarantine("ok.csv", _csv(months, np.round(p, 4)), classification="synthetic", event_date="June 2023")
    assert not r["ok"] and "ISO month" in r["reason"]
    # too little history before the event: the series is accepted for calibration and the event study is refused
    r = quarantine("short.csv", _csv(months, np.round(p, 4)), classification="synthetic", event_date=months[20])
    assert r["ok"] and "event_study" not in r and "24 monthly returns" in r["event_note"]
    r = quarantine("late.csv", _csv(months, np.round(p, 4)), classification="synthetic", event_date=months[37])
    assert r["ok"] and "event_study" not in r and "event window" in r["event_note"]
    # daily rows collapse to the last observation of each month
    daily_dates = [f"{m}-{d:02d}" for m in months for d in (5, 20)]
    daily_prices = [x for v in np.round(p, 4) for x in (v * 0.99, v)]
    r = quarantine("daily.csv", _csv(daily_dates, daily_prices), classification="synthetic")
    assert r["ok"] and r["stats"]["n_months"] == 40 and r["monthly"]["price"] == [float(v) for v in np.round(p, 4)]
