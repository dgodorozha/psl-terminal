"""Core tests: the instrument library, firm templates and assumptions validate and clamp; the question
parser reads instruments, constraints and horizon; the economy is deterministic and its random numbers are
common across policies and prefix consistent across path counts; the welfare accounting identity holds."""

import os
import sys

import numpy as np
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from psl import assumptions as AS  # noqa: E402
from psl import welfare as W  # noqa: E402
from psl.economy import Economy, RandomBundle  # noqa: E402
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
    assert set(AS.TORNADO) <= set(AS.SPEC) and AS.REWEIGHTABLE <= set(AS.TORNADO)
    for k, (lo, hi) in AS.TORNADO.items():
        assert AS.SPEC[k][1] <= lo < hi <= AS.SPEC[k][2], k


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


def test_random_bundle_is_prefix_consistent():
    big = RandomBundle(10, 12, 8, seed=11)
    small = RandomBundle(4, 12, 8, seed=11)
    for k in ("z_market", "z_idio", "u_inc", "z_sev", "u_cat", "u_audit", "z_news"):
        assert np.array_equal(getattr(big, k)[:4], getattr(small, k)), k


def test_welfare_identity_and_baseline_scores_zero():
    eco, a = _small()
    base = eco.run(library_policy("baseline"))
    pol = eco.run(library_policy("strict_liability"))
    B = W.aggregates(base, a); P = W.aggregates(pol, a)
    c = W.components(P, B, a)
    assert np.allclose(c["net_social_value"], W.net_from({k: c[k] for k in W.COMPONENTS}))
    c0 = W.components(B, B, a)
    assert abs(float(c0["net_social_value"].mean())) < 1e-9
    s = W.summarise(c["net_social_value"])
    assert set(s) >= {"mean", "lo", "hi", "p_positive", "median", "tail_share"} and s["lo"] <= s["median"] <= s["hi"]
    saf = W.safety_metrics(pol, a)
    assert 0 <= saf["p_major"] <= 1 and saf["incidents_per_year"]["mean"] >= 0
    mkt, vc = W.market_metrics(pol, base, a)
    assert len(mkt["firms"]) == 8 and vc.shape == (6,)
    assert len(mkt["rel_mean"]) == pol.prices.shape[1] and abs(mkt["rel_mean"][0]) < 1e-9, "the index starts level with the status quo"


def test_moratorium_defers_capability_and_liability_follows_scope():
    eco, a = _small(n=4, h=24)
    base = eco.run(library_policy("baseline"))
    mor = eco.run(library_policy("moratorium"))
    assert mor.capability[:, -1, :].mean() <= base.capability[:, -1, :].mean() + 1e-9
    lic = eco.run(library_policy("frontier_licensing"))
    assert lic.compliance.sum() > base.compliance.sum()
