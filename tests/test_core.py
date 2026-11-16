"""Core tests: the instrument library, firm templates and assumptions validate and clamp; the question
parser reads instruments, constraints and horizon; the economy is deterministic, its random numbers are
common across policies and consistent across path counts and offsets, a run with one value of each
assumption per path is the same computation as a run with scalars, and the assumptions that enter only the
accounting never touch the simulation; the welfare accounting identities hold; every index starts from one
valuation; incidents are classified one by one."""

import os
import sys

import numpy as np
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from psl import assumptions as AS  # noqa: E402
from psl import welfare as W  # noqa: E402
from psl.economy import Economy, RandomBundle  # noqa: E402
from psl.reduce import reduce, concat, head, simulate_battery  # noqa: E402
from psl.firms import default_firms, validate_firm, FirmStore, template as firm_template  # noqa: E402
from psl.policies import (LIBRARY, DEFAULT_BATTERY, validate_policy, library_policy, PolicyStore, template as policy_template,  # noqa: E402
                          describe, policy_hash)
from psl.question import parse, describe as describe_plan, DEFAULT_QUESTION  # noqa: E402


def test_library_is_valid_and_hashes_are_stable():
    for name, pol in LIBRARY.items():
        ok, p, errors, notes = validate_policy(dict(pol, name=name))
        assert ok, (name, errors)
        assert not notes, (name, notes)          # library values sit within their own bounds
        assert policy_hash(p) == policy_hash(library_policy(name))
        assert describe(p)
    assert DEFAULT_BATTERY[0] == "baseline" and all(n in LIBRARY for n in DEFAULT_BATTERY)


def test_custom_policy_is_clamped_and_stored(tmp_path):
    doc = policy_template()
    doc["name"] = "my_instrument"
    doc["fine_rate"] = 99.0                       # far above the bound
    doc["applies_to"] = ["frontier_lab"]
    ok, pol, errors, notes = validate_policy(doc)
    assert ok, errors
    assert pol["fine_rate"] <= 1.0 and any("fine_rate" in n for n in notes)
    assert pol["applies_to"] == ["frontier_lab"]
    ok, _, errors, _ = validate_policy(dict(doc, applies_to=["nonsense_sector"]))
    assert not ok and "unknown sectors" in errors[0]
    bad = dict(doc, name="Bad Name!")
    ok, _, errors, _ = validate_policy(bad)
    assert not ok and errors
    store = PolicyStore(str(tmp_path))
    res = store.add(doc, author="tester")
    assert res["ok"] and store.list()[0]["policy"]["name"] == "my_instrument"
    assert [p["name"] for p in store.enabled()] == ["my_instrument"]
    store.set_enabled("my_instrument", False)
    assert store.enabled() == []
    assert store.remove("my_instrument") and store.list() == []


def test_firms_validate_and_store(tmp_path):
    firms = default_firms()
    assert len(firms) == 8 and len({f["name"] for f in firms}) == 8
    for f in firms:
        ok, _, errors, _ = validate_firm(f)
        assert ok, (f["name"], errors)
    doc = firm_template(); doc["name"] = "lab_x"; doc["revenue"] = 1e9
    ok, f, errors, notes = validate_firm(doc)
    assert ok and f["revenue"] < 1e9 and notes
    store = FirmStore(str(tmp_path))
    assert store.economy()[1] == "default"
    store.add(doc, author="t")
    assert store.economy()[1] == "default", "one template is not an economy"
    doc2 = dict(doc, name="lab_y")
    store.add(doc2, author="t")
    firms2, origin = store.economy()
    assert origin == "custom" and {x["name"] for x in firms2} == {"lab_x", "lab_y"}


def test_assumptions_validate_and_clamp():
    a, notes = AS.validate({"discount_rate": 5.0, "nonsense": 1})
    assert a["discount_rate"] == AS.SPEC["discount_rate"][2] and notes
    assert AS.assumptions_hash(a) != AS.assumptions_hash(AS.defaults())
    # every declared assumption has a plausible range inside its bounds that brackets its default
    assert set(AS.RANGE) == set(AS.SPEC) and set(AS.TORNADO) <= set(AS.SPEC) and AS.WELFARE_ONLY <= set(AS.SPEC)
    for k, (lo, hi) in AS.RANGE.items():
        assert AS.SPEC[k][1] <= lo <= AS.SPEC[k][0] <= hi <= AS.SPEC[k][2] and lo < hi, k
    assert len(AS.oat_levels()) == 2 * len(AS.SPEC)
    # the joint draw stays inside the ranges and carries the declared correlations
    S = AS.sample(400, seed=1)
    assert set(S) == set(AS.SPEC)
    for k, v in S.items():
        assert AS.RANGE[k][0] - 1e-12 <= v.min() and v.max() <= AS.RANGE[k][1] + 1e-12, k
    from psl.stats import spearman
    assert spearman(S["hazard_base_misuse"], S["hazard_base_accident"]) > 0.4
    assert abs(spearman(S["discount_rate"], S["market_vol"])) < 0.2
    from psl.mechanisms import coverage
    cov = coverage(AS.SPEC)
    assert not cov["unlisted"] and not cov["unknown"], "every assumption belongs to a mechanism in the register"


def test_question_parser_reads_instruments_constraints_and_horizon():
    plan = parse(DEFAULT_QUESTION)
    assert plan["policies"][0] == "baseline" and len(plan["policies"]) >= 5
    assert plan["horizon_months"] == 60
    assert plan["constraints"].get("max_industry_loss_bn") == 400
    assert plan["constraints"].get("max_social_cost_bn") == 150
    plan2 = parse("Compare strict liability with a frontier licensing regime over three years; industry loss under $50bn")
    assert "strict_liability" in plan2["policies"] and "frontier_licensing" in plan2["policies"]
    assert "risk_tiering" not in plan2["policies"], "'frontier' must not read as 'tier'"
    assert plan2["horizon_months"] == 36 and plan2["constraints"]["max_industry_loss_bn"] == 50
    assert describe_plan(plan2)
    # the alternatives are the instruments the question asks about, and only those
    inst = lambda q: parse(q)["policies"][1:]
    assert inst("Would a six month moratorium above the compute threshold or coordinated frontier licensing reduce expected harm more "
                "over three years, keeping the gross social cost under $100bn?") == ["coordinated_licensing", "moratorium"]
    assert inst("Compare transparency and liability with a safe harbour over three years") == ["transparency_disclosure", "liability_with_safe_harbour"]
    assert inst("Compare strict liability with liability under a safe harbour and mandatory third party evaluations") == \
        ["mandatory_third_party_evals", "strict_liability", "liability_with_safe_harbour"]
    assert inst("Compare frontier licensing with coordinated licensing and a moratorium") == ["frontier_licensing", "coordinated_licensing", "moratorium"]
    assert inst("Compare compute threshold reporting, risk tiering and a moratorium") == ["compute_threshold_reporting", "risk_tiering", "moratorium"]
    assert "mandatory_third_party_evals" not in inst("Evaluate a moratorium against risk tiering and transparency")
    assert "mandatory_third_party_evals" in inst("Compare mandatory evals, risk tiering and transparency")
    assert inst("Compare liability and insurance rules with a safe harbour regime and transparency")[-2:] == ["strict_liability", "liability_with_safe_harbour"]


def _small(n=6, h=18, seed=3):
    firms = default_firms()
    a = AS.defaults()
    return Economy(firms, a, horizon=h, n_paths=n, seed=seed), a


def test_economy_is_deterministic_and_common_random_numbers_pair_policies():
    eco, a = _small()
    base1 = eco.run(library_policy("baseline"))
    base2 = eco.run(library_policy("baseline"))
    assert np.array_equal(base1.prices, base2.prices) and np.array_equal(base1.harm, base2.harm)
    pol = eco.run(library_policy("transparency_disclosure"))
    assert pol.prices.shape == base1.prices.shape == (6, 19, 8), "prices carry the announcement month plus one per simulated month"
    # the policy's effect is small, so paired paths move together: correlation of the index paths is high
    ib = base1.prices.mean(axis=2)[:, -1]; ip = pol.prices.mean(axis=2)[:, -1]
    assert np.corrcoef(ib, ip)[0, 1] > 0.9


def test_the_method_document_states_what_the_code_does():
    """The tables of docs/METHOD.md (firms, instruments, assumptions, constants, variants, strategies, the accounting
    map, the components, the mechanisms, the profiles) are generated from the code; a definition in the document
    cannot drift from its implementation."""
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    import sync_docs
    for rel in sync_docs.DOCS:
        text = open(os.path.join(ROOT, rel)).read()
        assert set(sync_docs.blocks(text)) == set(sync_docs.GENERATORS), "every generated table has its place in the document"
        assert sync_docs.render(text) == text, f"{rel} is out of date: run python tools/sync_docs.py"
        for key in AS.SPEC:
            assert f"`{key}`" in text, key
        for comp in W.COMPONENTS:
            assert f"`{comp}`" in text, comp


def test_a_condition_the_parser_cannot_apply_is_reported_not_dropped():
    assert parse(DEFAULT_QUESTION)["unread"] == []
    plan = parse("Compare strict liability with liability under a safe harbour over five years; the sector's net loss must stay below "
                 "$300bn and the probability of a catastrophic incident must fall by at least a quarter.")
    assert plan["constraints"] == {"max_industry_loss_bn": 300.0}
    assert plan["unread"] == ["the probability of a catastrophic incident must fall by at least a quarter"]
    assert "NOT read as a constraint" in describe_plan(plan) and any(n.startswith("NOT read") for n in plan["notes"])
    # the same condition in a form the Lab can test is read, and nothing is reported
    plan = parse("Compare strict liability with liability under a safe harbour over five years; the sector's net loss must stay below "
                 "$300bn and the probability of a catastrophe below 14%.")
    assert plan["constraints"] == {"max_industry_loss_bn": 300.0, "max_p_catastrophe": 0.14} and plan["unread"] == []
    assert parse("Which instrument is best over 5 years, keeping unemployment below 4%?")["unread"] == ["keeping unemployment below 4%"]
    # a horizon, a seed and an instrument's own description are not conditions
    for q in ("Would a six month moratorium above the compute threshold reduce harm more over three years, keeping the gross social cost under $100bn?",
              "Compare transparency and strict liability over 2 years, seed 11", "baseline against transparency over two years"):
        assert parse(q)["unread"] == [], q


def test_a_question_can_name_its_seed():
    assert parse(DEFAULT_QUESTION)["seed"] is None
    for text, want in (("Compare transparency and strict liability over two years, seed 11", 11),
                       ("Seed: 23. Which instrument is best?", 23), ("which instrument? (seed=5)", 5)):
        plan = parse(text)
        assert plan["seed"] == want and f"seed {want}" in describe_plan(plan), text
    # the seed is not an instrument, a horizon or a constraint
    plan = parse("Compare transparency and strict liability over two years, seed 11")
    assert plan["horizon_months"] == 24 and plan["constraints"] == {} and "transparency_disclosure" in plan["policies"]


def test_random_bundle_is_consistent_across_sizes_offsets_and_repeats():
    big = RandomBundle(10, 12, 8, seed=11)
    small = RandomBundle(4, 12, 8, seed=11)
    later = RandomBundle(4, 12, 8, seed=11, start=6)
    twice = small.take(np.tile(np.arange(4), 2))
    for k in RandomBundle.NAMES:
        assert np.array_equal(getattr(big, k)[:4], getattr(small, k)), k
        assert np.array_equal(getattr(big, k)[6:], getattr(later, k)), k
        assert np.array_equal(getattr(twice, k)[4:], getattr(small, k)), k
    assert not np.array_equal(RandomBundle(4, 12, 8, seed=12).u_inc, small.u_inc)


def test_one_value_per_path_is_the_same_computation_as_scalars():
    eco, a = _small(n=5, h=14)
    pol = library_policy("liability_with_safe_harbour")
    one = eco.run(pol)
    eco2 = Economy(default_firms(), {k: np.full(5, v) for k, v in a.items()}, horizon=14, n_paths=5, seed=3)
    two = eco2.run(pol)
    for k in ("revenue", "earnings", "harm", "harm_exp", "cat_harm_exp", "compliance", "claims", "liability_exp", "safety", "offshore", "prices"):
        assert np.array_equal(getattr(one, k), getattr(two, k)), k
    assert np.array_equal(one.incidents, two.incidents) and np.array_equal(one.series["p_cat_any"], two.series["p_cat_any"])
    # two blocks of the same paths with different parameters: the first block is the central run
    half = dict(a); half["hazard_base_misuse"] = np.repeat([a["hazard_base_misuse"], 0.2], 5)
    rb = RandomBundle(5, 14, 8, 3).take(np.tile(np.arange(5), 2))
    both = Economy(default_firms(), half, horizon=14, n_paths=10, seed=3, bundle=rb).run(pol)
    assert np.array_equal(both.harm_exp[:5], one.harm_exp) and both.harm_exp[5:].sum() > one.harm_exp.sum()


def test_welfare_only_assumptions_never_reach_the_simulation():
    eco, a = _small(n=4, h=12)
    pol = library_policy("mandatory_third_party_evals")
    ref = eco.run(pol)
    a2 = dict(a)
    for k in AS.WELFARE_ONLY:
        a2[k] = AS.RANGE[k][1]
    alt = Economy(default_firms(), a2, horizon=12, n_paths=4, seed=3).run(pol)
    for k in ("revenue", "earnings", "harm", "harm_exp", "compliance", "premium", "prices", "safety"):
        assert np.array_equal(getattr(ref, k), getattr(alt, k)), k


def test_welfare_identities_and_baseline_scores_zero():
    eco, a = _small()
    d = W.discount(18, a["discount_rate"])
    assert abs(d[0] - (1 + a["discount_rate"]) ** (-1 / 12)) < 1e-12 and abs(d[-1] - (1 + a["discount_rate"]) ** (-18 / 12)) < 1e-12, \
        "monthly flows are discounted at the end of their month; the horizon by (1 + r)^(-H/12)"
    assert W.discount(18, np.array([0.0, 0.05])).shape == (2, 18)
    base = eco.run(library_policy("baseline"))
    pol = eco.run(library_policy("strict_liability"))
    B = reduce(base, discount_f=d); P = reduce(pol, discount_f=d)
    c = W.components(P, B, a)
    assert np.allclose(c["net_social_value"], W.net_from({k: c[k] for k in W.COMPONENTS}))
    assert set(W.COMPONENTS) == set(W.BENEFITS) | set(W.COSTS) and "insurance_admin_cost" in W.COSTS
    c0 = W.components(B, B, a)
    assert abs(float(c0["net_social_value"].mean())) < 1e-9
    # the declared overlap between the output uplift and the other two benefit components scales the output uplift
    # and nothing else, and is zero by default
    assert a["benefit_overlap_share"] == 0.0 and "benefit_overlap_share" in AS.WELFARE_ONLY
    ch = W.components(P, B, dict(a, benefit_overlap_share=0.5))
    assert np.allclose(ch["productivity_change"], 0.5 * c["productivity_change"])
    for k in W.COMPONENTS:
        if k != "productivity_change":
            assert np.array_equal(ch[k], c[k]), k
    assert np.allclose(ch["net_social_value"], c["net_social_value"] - 0.5 * c["productivity_change"])
    # gross cost and gross benefit: never negative, and they differ by the net social value
    means = {k: float(c[k].mean()) for k in W.COMPONENTS}
    gc, gb = W.gross(means)
    assert gc >= 0 and gb >= 0 and abs(gb - gc - float(c["net_social_value"].mean())) < 1e-9
    gc2, _ = W.gross({k: (-5.0 if k in W.COSTS else 0.0) for k in W.COMPONENTS})
    assert gc2 == 0.0, "a saving on a cost line is a benefit, never a negative cost"
    gc3, gb3 = W.gross({k: (-2.0 if k == "harm_avoided" else 0.0) for k in W.COMPONENTS})
    assert gc3 == 2.0 and gb3 == 0.0, "harm that rises is a cost"
    # the incidence table follows the money: it sums to the net social value plus the non resident memorandum item
    inc = sum(float(v.mean()) for v in c["incidence"].values())
    assert abs(inc - float(c["net_social_value"].mean()) - float(c["nonresident_payments"].mean())) < 1e-9
    # every monetary flow the reduction keeps is mapped once in the accounting
    flows = {m["flow"].split(",")[0].split(" ")[0] for m in W.ACCOUNT_MAP}
    assert {"harm_exp", "harm", "service", "op_earnings", "compliance", "enforcement", "offshore_revenue", "relocation", "premium",
            "fines", "liability", "claims", "earnings", "cap_end"} <= flows
    s = W.summarise(c["net_social_value"], drawn=c["net_social_value_drawn"])
    assert set(s) >= {"mean", "se", "ci_lo", "ci_hi", "lo", "hi", "p_positive", "median", "tail_share", "mean_drawn"}
    assert s["lo"] <= s["median"] <= s["hi"] and s["ci_lo"] <= s["mean"] <= s["ci_hi"]
    saf = W.safety_metrics(P, a)
    assert 0 <= saf["p_major"] <= 1 and 0 <= saf["p_catastrophe"] <= 1 and saf["incidents_per_year"]["mean"] >= 0
    assert saf["p_catastrophe_detail"]["n"] == 6 and saf["p_catastrophe_detail"]["estimator"] == "conditional"
    mkt = W.market_metrics(P, B, a)
    assert len(mkt["firms"]) == 8
    assert len(mkt["rel_mean"]) == pol.prices.shape[1] and abs(mkt["rel_mean"][0]) < 1e-9, "the index starts level with the status quo"
    # the industry value from the reduced paths equals the sum over firms
    assert abs(float(c["industry_value_change"].mean()) - mkt["industry_value_change"]["mean"]) < 1e-6


def test_reduction_joins_and_slices_paths():
    firms = default_firms(); a = AS.defaults()
    pols = {n: library_policy(n) for n in ("baseline", "transparency_disclosure")}
    whole = simulate_battery(pols, firms, a, 12, 10, 5)
    first = simulate_battery(pols, firms, a, 12, 6, 5)
    rest = simulate_battery(pols, firms, a, 12, 4, 5, start=6)
    for n in pols:
        joined = concat([first[n], rest[n]])
        for k in ("harm", "harm_exp", "earnings", "service", "cap_end", "cat_cmc", "idx"):
            assert np.allclose(joined[k], whole[n][k]), (n, k)
        assert np.allclose(joined["price_sum"], whole[n]["price_sum"])
        assert np.array_equal(head(whole[n], 6)["harm"], first[n]["harm"])
    chunked = simulate_battery(pols, firms, a, 12, 10, 5, chunk=3)
    assert np.allclose(chunked["transparency_disclosure"]["harm"], whole["transparency_disclosure"]["harm"])


def test_every_index_starts_from_one_pre_intervention_valuation():
    eco, a = _small(n=6, h=12)
    base = eco.run(library_policy("baseline"))
    now = dict(library_policy("risk_tiering")); now["phase_in"] = 0          # in force from the first month
    later = dict(library_policy("risk_tiering")); later["phase_in"] = 6
    r_now, r_later = eco.run(now), eco.run(later)
    assert np.array_equal(base.cap0, r_now.cap0) and np.array_equal(base.cap0, r_later.cap0)
    assert np.all(base.prices[:, 0] == 100.0) and np.all(r_now.prices[:, 0] == 100.0)
    w = base.cap0 / base.cap0.sum()
    idx = lambda r: (r.prices[:, 1] * w).sum(axis=1).mean()
    assert idx(r_now) < idx(base) - 0.5, "an instrument in force at once shows its effect on fundamentals in the first month's price"
    assert idx(r_later) < idx(base), "one announced for later is anticipated"


def test_incidents_are_classified_one_by_one():
    eco, a = _small(n=200, h=36, seed=5)        # large enough to contain firm months with two or more incidents
    res = eco.run(library_policy("baseline"))
    major = res.incidents & (res.harm_cat >= a["major_incident_bn"])
    assert np.array_equal(res.news_counts[:, :, 1], major.sum(axis=(2, 3))), "a major incident is one incident at or above the threshold"
    assert np.array_equal(res.news_counts[:, :, 0], (res.incidents & ~major).sum(axis=(2, 3)))
    assert np.array_equal(res.news_counts[:, :, 2], res.catastrophe.sum(axis=2))
    # a firm month whose total harm passes the threshold only by adding minor incidents is not a major incident
    combined = (res.harm_cat.sum(axis=3) >= a["major_incident_bn"]) & ~major.any(axis=3) & ~res.catastrophe
    assert combined.any(), "the sample should contain such a firm month for the test to bite"
    R = reduce(res)
    assert np.array_equal(R["n_major"], major.sum(axis=(2, 3)).astype(float))


def test_moratorium_defers_capability_and_liability_follows_scope():
    eco, a = _small(n=4, h=24)
    base = eco.run(library_policy("baseline"))
    mor = eco.run(library_policy("moratorium"))
    assert mor.capability[:, -1, :].mean() <= base.capability[:, -1, :].mean() + 1e-9
    lic = eco.run(library_policy("frontier_licensing"))
    assert lic.compliance.sum() > base.compliance.sum()
