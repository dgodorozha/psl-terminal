"""Social cost accounting: what a policy costs and what it buys, per path,
paired against the baseline path that shares its random numbers.

Everything is a present value in $bn at the declared discount rate over
the simulated horizon. Transfers (fines, liability payouts, insurance
premiums) are shown in the distributional table and excluded from the net
social value; only resource costs and real benefits enter it.

  harm_avoided             monetised harm on the baseline path minus the policy path
  cs_change                change in consumer surplus from the AI service index
  productivity_change      change in the output uplift from adoption, including the trust effect
  producer_surplus_change  change in the resident share of firms' operating profit (revenue and margin effects,
                           before compliance, fines, liability and premiums, which are counted elsewhere or are transfers)
  compliance_cost          the resource share of firms' compliance spend
  enforcement_cost         the regulator's budget above the baseline
  leakage                  domestic value added lost to activity that moved offshore
  relocation_cost          the one off cost of moving it
  labour_change            adjustment cost of faster (or slower) adoption

  net_social_value = harm_avoided + cs_change + productivity_change + producer_surplus_change
                     - compliance_cost - enforcement_cost - leakage - relocation_cost - labour_change

The accounting works on aggregates (sums over firms, per path and month)
so that it can be recomputed from the stored paths for the tornado and by
the critic, without re simulating.
"""

import numpy as np

COMPONENTS = ("harm_avoided", "cs_change", "productivity_change", "producer_surplus_change",
              "compliance_cost", "enforcement_cost", "leakage", "relocation_cost", "labour_change")
BENEFITS = ("harm_avoided", "cs_change", "productivity_change", "producer_surplus_change")
COSTS = ("compliance_cost", "enforcement_cost", "leakage", "relocation_cost", "labour_change")
AGG_KEYS = ("harm", "cat_harm", "compliance", "fines", "liability", "premium", "relocation", "offshore_revenue",
            "op_earnings", "earnings", "service", "trust", "enforcement", "pressure", "tone", "n_incidents", "n_major")


def discount(horizon, rate):
    t = np.arange(horizon)
    return (1.0 / (1.0 + rate)) ** (t / 12.0)


def aggregates(res, a):
    """Per path, per month aggregates (N, H) of one policy result, enough for the accounting."""
    margin = np.array([f for f in res.margins]) if hasattr(res, "margins") else None
    agg = {
        "harm": res.harm.sum(axis=2), "cat_harm": res.cat_harm.sum(axis=2),
        "compliance": res.compliance.sum(axis=2), "fines": res.fines.sum(axis=2),
        "liability": res.liability.sum(axis=2), "premium": res.premium.sum(axis=2),
        "relocation": res.relocation.sum(axis=2), "offshore_revenue": (res.offshore * res.revenue / 12.0).sum(axis=2),
        "op_earnings": res.op_earnings.sum(axis=2), "earnings": res.earnings.sum(axis=2),
        "service": res.series["service"], "trust": res.series["trust"], "enforcement": res.series["enforcement"],
        "pressure": res.series["pressure"], "tone": res.series["tone"],
        "n_incidents": res.incidents.sum(axis=(2, 3)).astype(float),
        "n_major": (res.harm >= a["major_incident_bn"]).sum(axis=2).astype(float),
        "catastrophe": res.catastrophe.any(axis=2).astype(float),
    }
    agg["horizon"] = res.horizon
    agg["n_paths"] = res.n_paths
    return agg


def components(P, B, a):
    """Per path components (dict of arrays (N,)) for policy aggregates P against baseline aggregates B."""
    H = int(P["horizon"])
    d = discount(H, a["discount_rate"])
    harm_avoided = ((B["harm"] - P["harm"]) * d).sum(axis=1) * a["harm_valuation_multiplier"]
    Qp, Qb, Tp, Tb = P["service"], B["service"], P["trust"], B["trust"]
    cs = (a["consumer_surplus_base_bn"] / 12.0) * ((Qp ** a["cs_elasticity"] - Qb ** a["cs_elasticity"]) * d).sum(axis=1)
    prod = (a["productivity_base_bn"] / 12.0) * (((Qp ** a["productivity_elasticity"]) * (Tp ** a["trust_elasticity"])
                                                 - (Qb ** a["productivity_elasticity"]) * (Tb ** a["trust_elasticity"])) * d).sum(axis=1)
    psur = a["domestic_ownership_share"] * ((P["op_earnings"] - B["op_earnings"]) * d).sum(axis=1)
    comp = a["compliance_deadweight_share"] * ((P["compliance"] - B["compliance"]) * d).sum(axis=1)
    enf = a["enforcement_cost_bn"] / 12.0 * ((P["enforcement"] - B["enforcement"]) * d).sum(axis=1)
    leak = a["leakage_value_share"] * ((P["offshore_revenue"] - B["offshore_revenue"]) * d).sum(axis=1)
    reloc = ((P["relocation"] - B["relocation"]) * d).sum(axis=1)
    one = np.ones((Qp.shape[0], 1))
    dQp = np.diff(np.concatenate([one, Qp], axis=1), axis=1)
    dQb = np.diff(np.concatenate([one, Qb], axis=1), axis=1)
    labour = a["labour_adjustment_bn"] * ((np.maximum(dQp, 0) - np.maximum(dQb, 0)) * d).sum(axis=1)
    out = {"harm_avoided": harm_avoided, "cs_change": cs, "productivity_change": prod, "producer_surplus_change": psur,
           "compliance_cost": comp, "enforcement_cost": enf, "leakage": leak, "relocation_cost": reloc, "labour_change": labour}
    out["net_social_value"] = net_from(out)
    out["gross_cost"] = (comp + enf + leak + reloc + np.maximum(labour, 0) + np.maximum(-cs, 0) + np.maximum(-prod, 0)
                         + np.maximum(-psur, 0))
    out["transfers"] = {"fines": ((P["fines"] - B["fines"]) * d).sum(axis=1),
                        "liability": ((P["liability"] - B["liability"]) * d).sum(axis=1),
                        "premiums": ((P["premium"] - B["premium"]) * d).sum(axis=1)}
    out["earnings_change"] = ((P["earnings"] - B["earnings"]) * d).sum(axis=1)
    return out


def net_from(c):
    return (c["harm_avoided"] + c["cs_change"] + c["productivity_change"] + c["producer_surplus_change"]
            - c["compliance_cost"] - c["enforcement_cost"] - c["leakage"] - c["relocation_cost"] - c["labour_change"])


def distribution(c, value_change):
    """Who gains and who pays (means), given the components and the shareholder value change."""
    return {
        "firms (shareholders)": float(np.mean(value_change)),
        "consumers": float(c["cs_change"].mean()),
        "public (harm not suffered)": float(c["harm_avoided"].mean()),
        "wider economy (output)": float(c["productivity_change"].mean()),
        "workers": float(-c["labour_change"].mean()),
        "taxpayers": float((-c["enforcement_cost"] + c["transfers"]["fines"]).mean()),
        "abroad (relocated activity)": float(c["leakage"].mean()),
    }


def summarise(x, q=(10, 90)):
    """Mean, the 10th and 90th percentiles, the share of paths above zero, the median, and the share of the
    mean that the top tenth of paths contributes (a heavy tail reads as a mean above the 90th percentile)."""
    x = np.asarray(x, dtype=float)
    out = {"mean": float(x.mean()), "lo": float(np.percentile(x, q[0])), "hi": float(np.percentile(x, q[1])),
           "p_positive": float((x > 0).mean()), "median": float(np.median(x))}
    k = max(1, int(round(0.1 * x.size)))
    top = np.sort(x)[-k:]
    out["tail_share"] = float(top.sum() / x.sum()) if x.sum() > 1e-9 and top.sum() > 0 else 0.0
    return out


def safety_metrics(res, a):
    """Policy level safety forecast (not a difference): rates, probabilities, levels."""
    H = res.horizon; years = H / 12.0
    d = discount(H, a["discount_rate"])
    harm = res.harm.sum(axis=2)
    inc = res.incidents.sum(axis=(2, 3))
    major = (res.harm >= a["major_incident_bn"]).sum(axis=2)
    by_cat = res.incidents.sum(axis=(1, 2))
    return {
        "incidents_per_year": summarise(inc.sum(axis=1) / years),
        "incidents_by_category_per_year": {k: float(by_cat[:, i].mean() / years) for i, k in enumerate(("misuse", "accident", "systemic"))},
        "major_per_year": summarise(major.sum(axis=1) / years),
        "p_major": float((major.sum(axis=1) > 0).mean()),
        "p_catastrophe": float(res.catastrophe.any(axis=(1, 2)).mean()),
        "expected_harm_npv": summarise((harm * d).sum(axis=1) * a["harm_valuation_multiplier"]),
        "expected_catastrophe_harm_npv": float(((res.cat_harm.sum(axis=2) * d).sum(axis=1) * a["harm_valuation_multiplier"]).mean()),
        "safety_level_end": float(res.safety[:, -1, :].mean()),
        "safety_share_end": float(res.sigma[:, -1, :].mean()),
        "capability_end": float(res.cap_eff[:, -1, :].mean()),
        "frontier_capability_end": float(res.cap_eff[:, -1, :].max(axis=1).mean()),
        "trust_end": float(res.series["trust"][:, -1].mean()),
        "offshore_share_end": float(res.offshore[:, -1, :].mean()),
        "compliance_share": float(res.comply[:, -1, :].mean()),
        "service_index_end": float(res.series["service"][:, -1].mean()),
        "harm_by_year": [float(harm[:, y * 12:(y + 1) * 12].sum(axis=1).mean()) for y in range(H // 12)],
    }


def news_metrics(res, base=None):
    """What the wire will look like under this policy: expected counts a year, pressure, tone."""
    H = res.horizon; years = H / 12.0
    nc = res.news_counts
    names = ("minor incidents", "major incidents", "catastrophes", "enforcement actions", "relocations", "capability milestones")
    counts = {n: summarise(nc[:, :, i].sum(axis=1) / years) for i, n in enumerate(names)}
    P = res.series["pressure"]
    early = res.series["tone"][:, :6].mean(axis=1)
    out = {"headlines_per_year": counts, "peak_pressure": summarise(P.max(axis=1)),
           "mean_pressure": float(P.mean()), "p_hearing": float((P.max(axis=1) > 0.45).mean()),
           "share_months_high_pressure": float((P > 0.3).mean()), "early_tone": float(early.mean()),
           "quarterly_negative": [float(nc[:, q * 3:(q + 1) * 3, :4].sum(axis=(1, 2)).mean()) for q in range(H // 3)],
           "quarterly_negative_hi": [float(np.percentile(nc[:, q * 3:(q + 1) * 3, :4].sum(axis=(1, 2)), 90)) for q in range(H // 3)],
           "quarterly_pressure": [float(P[:, q * 3:(q + 1) * 3].mean()) for q in range(H // 3)]}
    if base is not None:
        out["early_tone_vs_baseline"] = float(early.mean() - base.series["tone"][:, :6].mean(axis=1).mean())
    return out


def market_metrics(res, base, a):
    """Per firm and industry: value change, probability of gain, early reaction, the AI index."""
    H = res.horizon
    d = discount(H, a["discount_rate"])
    w = res.cap0 / res.cap0.sum()
    idx_p = (res.prices * w[None, None, :]).sum(axis=2)
    idx_b = (base.prices * w[None, None, :]).sum(axis=2)
    early = (idx_p[:, 1:7] / idx_b[:, 1:7] - 1.0).mean(axis=1)
    end = idx_p[:, -1] / idx_b[:, -1] - 1.0
    dE = ((res.earnings - base.earnings) * d[None, :, None]).sum(axis=1)
    dcap = (res.cap_end - base.cap_end) * d[-1]
    firms = []
    for f, lab in enumerate(res.labels):
        tot = dE[:, f] + dcap[:, f]
        firms.append({"firm": lab, "sector": res.sectors[f], "cap0": float(res.cap0[f]),
                      "value_change": summarise(tot), "earnings_change_npv": float(dE[:, f].mean()),
                      "cap_change": float(dcap[:, f].mean()), "cap_change_pct": float((dcap[:, f] / res.cap0[f]).mean()),
                      "price_end": float(res.prices[:, -1, f].mean()), "price_end_base": float(base.prices[:, -1, f].mean()),
                      "offshore_end": float(res.offshore[:, -1, f].mean()), "comply_end": float(res.comply[:, -1, f].mean()),
                      "safety_share_end": float(res.sigma[:, -1, f].mean())})
    sectors = {}
    for f, s in enumerate(res.sectors):
        sectors.setdefault(s, []).append(f)
    sector_rows = [{"sector": s, "value_change": summarise((dE[:, ix] + dcap[:, ix]).sum(axis=1)), "cap0": float(res.cap0[ix].sum())}
                   for s, ix in sectors.items()]
    value_change = dE.sum(axis=1) + dcap.sum(axis=1)
    rel = (idx_p / idx_b - 1.0) * 100.0            # the index against the status quo on the same path, in percent
    return {"industry_value_change": summarise(value_change),
            "rel_mean": rel.mean(axis=0).tolist(), "rel_lo": np.percentile(rel, 10, axis=0).tolist(),
            "rel_hi": np.percentile(rel, 90, axis=0).tolist(),
            "industry_cap_change": summarise(dcap.sum(axis=1)), "industry_earnings_change": summarise(dE.sum(axis=1)),
            "industry_cap0": float(res.cap0.sum()),
            "early_reaction": summarise(early), "end_reaction": summarise(end),
            "index_mean": idx_p.mean(axis=0).tolist(), "index_lo": np.percentile(idx_p, 10, axis=0).tolist(),
            "index_hi": np.percentile(idx_p, 90, axis=0).tolist(), "index_base_mean": idx_b.mean(axis=0).tolist(),
            "firms": firms, "sectors": sector_rows,
            "firm_price_mean": res.prices.mean(axis=0).T.tolist()}, value_change
