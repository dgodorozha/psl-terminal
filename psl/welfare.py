"""Social cost accounting: what a policy costs and what it buys, per path,
paired against the status quo path that shares its random numbers.

The estimand. For a policy P and the status quo SQ, simulated on the same
random numbers,

    net social value  dW(P) = E[ W(P) - W(SQ) ]

is the expected change in residents' welfare over the horizon, in $bn of
present value, under the declared model and assumptions. The status quo
scores zero by construction and is a decision alternative like any other.

Standing and conventions (docs/METHOD.md, section 7):
  standing        residents. Real resources used up in the jurisdiction count in
                  full; income counts for residents only (the resident share of
                  the AI firms' operating profit).
  transfers       fines, liability payments, insurance claims and the part of
                  premiums that covers them move money between parties and are
                  excluded, whoever pays. What non resident owners finance of
                  the firms' payments is reported as a memorandum item
                  (nonresident_payments) and not counted.
  no overlap      each simulated flow enters one component (ACCOUNT_MAP):
                  consumer surplus is households' non market surplus from AI
                  services; the output uplift is value added in the sectors that
                  adopt AI, net of what they pay AI providers; producer surplus is
                  the AI sector's own operating profit, before compliance, fines,
                  liability, premiums and relocation, which are counted once
                  elsewhere or are transfers. The separation between the three
                  benefit components is a definition, not a measurement: the
                  bases are declared, and a declared overlap share
                  (benefit_overlap_share, 0 by default) removes from the output
                  uplift whatever part of it an analyst judges to be already in
                  the other two.
  timing          monthly flows are discounted at the end of their month,
                  (1 + r)^(-t/12) for month t = 1..H; values at the horizon by
                  (1 + r)^(-H/12).
  expected harm   the expected value of harm avoided uses, month by month, the
                  harm expected given the state each path has reached
                  (probability times mean severity) instead of the harm drawn:
                  the same expectation, far less variance (conditional Monte
                  Carlo). The drawn harm gives the spread of outcomes.

Components (present value, $bn):
  harm_avoided             expected monetised harm on the status quo path minus the policy path
  cs_change                change in consumer surplus from the AI service index
  productivity_change      change in the output uplift from adoption, including the trust effect
  producer_surplus_change  change in the resident share of the AI firms' operating profit
  compliance_cost          the resource share of firms' compliance spend
  enforcement_cost         the regulator's budget above the status quo
  leakage                  residents' rents (wage premia, tax base) lost to activity that moved offshore
  relocation_cost          the one off cost of moving it
  labour_change            adjustment cost of faster (or slower) adoption
  insurance_admin_cost     the resource share of the insurance loading under a mandate

  net_social_value = harm_avoided + cs_change + productivity_change + producer_surplus_change
                     - compliance_cost - enforcement_cost - leakage - relocation_cost - labour_change
                     - insurance_admin_cost

  gross_cost     the sum of the expected component changes that are costs: every cost component whose
                 expected change is positive and every benefit component whose expected change is negative.
                 Never negative; savings and gains are not netted against it.
  gross_benefit  the mirror image; net_social_value = gross_benefit - gross_cost.

The accounting works on the reduced paths (reduce.py), so it can be
recomputed for an alternative value judgement, for a bootstrap resample and
by the critic without re simulating.
"""

import numpy as np

from .stats import wilson

BENEFITS = ("harm_avoided", "cs_change", "productivity_change", "producer_surplus_change")
COSTS = ("compliance_cost", "enforcement_cost", "leakage", "relocation_cost", "labour_change", "insurance_admin_cost")
COMPONENTS = BENEFITS + COSTS
TRANSFERS = ("fines", "liability", "premiums", "claims")

# Every monetary flow the economy records, and where it goes in the accounting: exactly one line each.
ACCOUNT_MAP = (
    {"flow": "harm_exp", "enters": "harm_avoided", "kind": "real", "who": "the public at risk",
     "note": "expected monetised harm given the state reached, scaled by the harm valuation multiplier; direct damages only"},
    {"flow": "harm", "enters": "outcome spread of harm_avoided", "kind": "real", "who": "the public at risk",
     "note": "the harm actually drawn; the same expectation as harm_exp; used for percentiles, never added to it"},
    {"flow": "service", "enters": "cs_change", "kind": "real", "who": "consumers",
     "note": "households' non market surplus from AI services, a power of the service index"},
    {"flow": "service, trust", "enters": "productivity_change", "kind": "real", "who": "sectors that adopt AI",
     "note": "value added uplift in adopting sectors net of their payments to AI providers; excludes the AI sector's own profit; "
             "scaled by one minus the declared overlap with the other two benefit components (benefit_overlap_share)"},
    {"flow": "op_earnings", "enters": "producer_surplus_change", "kind": "real", "who": "resident owners of AI firms",
     "note": "operating profit before compliance, fines, liability, premiums and relocation; resident share only"},
    {"flow": "compliance", "enters": "compliance_cost", "kind": "real (resource share)", "who": "firms",
     "note": "the deadweight share is a resource cost; the rest is rent to compliance providers, a transfer"},
    {"flow": "enforcement", "enters": "enforcement_cost", "kind": "real", "who": "taxpayers", "note": "public budget per unit of enforcement intensity"},
    {"flow": "offshore_revenue", "enters": "leakage", "kind": "real", "who": "domestic workers and tax base",
     "note": "residents' rents on activity that moved; the firms' own profit loss from moving is in op_earnings"},
    {"flow": "relocation", "enters": "relocation_cost", "kind": "real", "who": "firms", "note": "one off resource cost of moving"},
    {"flow": "service (first difference)", "enters": "labour_change", "kind": "real", "who": "workers", "note": "adjustment cost of adoption"},
    {"flow": "premium", "enters": "insurance_admin_cost (loading x resource share); the rest is a transfer", "kind": "real and transfer",
     "who": "firms to insurers", "note": "expected claims and the insurer's margin are transfers; underwriting and administration are resources"},
    {"flow": "fines", "enters": "transfer", "kind": "transfer", "who": "firms to taxpayers", "note": "excluded from the net social value"},
    {"flow": "liability", "enters": "transfer", "kind": "transfer", "who": "firms to victims", "note": "excluded; the harm itself is in harm_avoided"},
    {"flow": "claims", "enters": "transfer", "kind": "transfer", "who": "firms or insurers to victims", "note": "what victims are paid, by whoever pays"},
    {"flow": "earnings", "enters": "incidence table and market value only", "kind": "income", "who": "owners",
     "note": "operating profit less every payment above; its components are already counted line by line"},
    {"flow": "cap_end", "enters": "industry value change only", "kind": "valuation", "who": "shareholders",
     "note": "market value at the horizon; a market metric and a constraint, never part of the net social value"},
)


def discount(horizon, rate):
    """Discount factors for months 1..H at the end of each month: (1 + r)^(-t/12). `rate` is a scalar or one value
    per path, giving (H,) or (N, H). The last factor is the horizon's, (1 + r)^(-H/12)."""
    t = np.arange(1, int(horizon) + 1) / 12.0
    r = np.asarray(rate, dtype=float)
    return (1.0 + r[:, None]) ** (-t[None, :]) if r.ndim else (1.0 + float(r)) ** (-t)


def _col(v):
    """An assumption against a (paths, months) array: itself, or a column when it has one value per path."""
    return v[:, None] if np.ndim(v) else v


def components(P, B, a):
    """Per path components (dict of arrays (N,)) for a reduced policy P against the reduced status quo B."""
    H = int(P["horizon"])
    d = discount(H, a["discount_rate"])
    d_end = d[..., -1]

    def pv(x):
        return (x * d).sum(axis=1)
    hv = a["harm_valuation_multiplier"]
    harm_avoided = pv(B["harm_exp"] - P["harm_exp"]) * hv
    harm_drawn = pv(B["harm"] - P["harm"]) * hv
    Qp, Qb, Tp, Tb = P["service"], B["service"], P["trust"], B["trust"]
    cs = (a["consumer_surplus_base_bn"] / 12.0) * pv(Qp ** _col(a["cs_elasticity"]) - Qb ** _col(a["cs_elasticity"]))
    pe, te = _col(a["productivity_elasticity"]), _col(a["trust_elasticity"])
    # the overlap adjustment: the share of the output uplift already counted in consumer surplus or in the AI firms'
    # own profit is removed from it (0 by default: the components are defined not to overlap; the screen and the
    # joint draw move it to 0.5)
    prod = (1.0 - a.get("benefit_overlap_share", 0.0)) * (a["productivity_base_bn"] / 12.0) * pv((Qp ** pe) * (Tp ** te) - (Qb ** pe) * (Tb ** te))
    d_op = pv(P["op_earnings"] - B["op_earnings"])
    d_comp = pv(P["compliance"] - B["compliance"])
    d_fines = pv(P["fines"] - B["fines"]); d_liab = pv(P["liability"] - B["liability"])
    d_prem = pv(P["premium"] - B["premium"]); d_claims = pv(P["claims"] - B["claims"])
    d_reloc = pv(P["relocation"] - B["relocation"])
    own = a["domestic_ownership_share"]
    psur = own * d_op
    comp = a["compliance_deadweight_share"] * d_comp
    enf = a["enforcement_cost_bn"] / 12.0 * pv(P["enforcement"] - B["enforcement"])
    leak = a["leakage_value_share"] * pv(P["offshore_revenue"] - B["offshore_revenue"])
    one = np.ones((Qp.shape[0], 1))
    dQp = np.diff(np.concatenate([one, Qp], axis=1), axis=1)
    dQb = np.diff(np.concatenate([one, Qb], axis=1), axis=1)
    labour = a["labour_adjustment_bn"] * pv(np.maximum(dQp, 0) - np.maximum(dQb, 0))
    load = a["insurance_loading"]
    ins = a["insurance_admin_share"] * load / (1.0 + load) * d_prem
    out = {"harm_avoided": harm_avoided, "cs_change": cs, "productivity_change": prod, "producer_surplus_change": psur,
           "compliance_cost": comp, "enforcement_cost": enf, "leakage": leak, "relocation_cost": d_reloc, "labour_change": labour,
           "insurance_admin_cost": ins}
    out["net_social_value"] = net_from(out)
    out["harm_avoided_drawn"] = harm_drawn
    out["net_social_value_drawn"] = out["net_social_value"] - harm_avoided + harm_drawn
    out["transfers"] = {"fines": d_fines, "liability": d_liab, "premiums": d_prem, "claims": d_claims}
    d_earn = pv(P["earnings"] - B["earnings"])
    out["earnings_change"] = d_earn
    d_cap = (P["cap_end"] - B["cap_end"]) * d_end
    out["industry_value_change"] = pv(P["earnings_exp"] - B["earnings_exp"]) + d_cap      # expected liability: lower variance
    out["industry_value_change_drawn"] = d_earn + d_cap
    out["nonresident_payments"] = (1.0 - own) * (d_comp + d_reloc + d_fines + d_liab + d_prem)
    out["incidence"] = {
        "public at risk (harm not suffered, compensation received)": harm_avoided + d_claims,
        "consumers": cs,
        "sectors that adopt AI (output)": prod,
        "workers (adjustment)": -labour,
        "resident owners of AI firms": own * d_earn,
        "taxpayers (fines less enforcement)": d_fines - enf,
        "insurers": d_prem - (d_claims - d_liab) - ins,
        "compliance providers (rents)": (1.0 - a["compliance_deadweight_share"]) * d_comp,
        "domestic workers and tax base (activity moved offshore)": -leak,
    }
    return out


def net_from(c):
    return sum(c[k] for k in BENEFITS) - sum(c[k] for k in COSTS)


def gross(means):
    """(gross cost, gross benefit) from the expected value of each component: `means` maps component -> a number
    or an array of bootstrap or scenario means. Gross cost is the sum of the expected changes that are costs
    (positive cost components, negative benefit components); gross benefit the mirror image. Both are non
    negative, and gross benefit - gross cost = the expected net social value."""
    cost = sum(np.maximum(means[k], 0.0) for k in COSTS) + sum(np.maximum(-np.asarray(means[k]), 0.0) for k in BENEFITS)
    benefit = sum(np.maximum(means[k], 0.0) for k in BENEFITS) + sum(np.maximum(-np.asarray(means[k]), 0.0) for k in COSTS)
    return cost, benefit


def summarise(x, boot=None, drawn=None, q=(10, 90)):
    """A quantity over paths.

      mean, se, ci_lo, ci_hi   the expected value with its Monte Carlo standard error and 95% bootstrap confidence
                               interval (how well the paths estimate the expectation)
      lo, hi, median           the 10th and 90th percentiles and the median of the simulated outcomes (how different
                               one path can be from another); taken from `drawn` when given, the outcomes as drawn,
                               while the mean comes from the lower variance estimator x
      p_positive               the share of simulated outcomes above zero
      tail_share               the share of the outcomes' mean that the top tenth of paths contributes
    """
    x = np.asarray(x, dtype=float)
    o = x if drawn is None else np.asarray(drawn, dtype=float)
    if boot is not None and boot.n == x.size:
        mean, se, ci_lo, ci_hi = boot.ci(x)
    else:
        mean = float(x.mean())
        se = float(x.std(ddof=1) / np.sqrt(x.size)) if x.size > 1 else 0.0
        ci_lo, ci_hi = mean - 1.96 * se, mean + 1.96 * se
    out = {"mean": mean, "se": se, "ci_lo": ci_lo, "ci_hi": ci_hi,
           "lo": float(np.percentile(o, q[0])), "hi": float(np.percentile(o, q[1])),
           "p_positive": float((o > 0).mean()), "median": float(np.median(o))}
    if drawn is not None:
        out["mean_drawn"] = float(o.mean())
    k = max(1, int(round(0.1 * o.size)))
    top = np.sort(o)[-k:]
    out["tail_share"] = float(top.sum() / o.sum()) if o.sum() > 1e-9 and top.sum() > 0 else 0.0
    return out


def proportion(ind, boot=None, cmc=None):
    """A probability estimated from path indicators: the share with its Wilson interval; when a conditional
    estimator `cmc` (per path, same expectation) is given, its mean and bootstrap interval are the estimate and
    the raw count is reported beside it."""
    ind = np.asarray(ind, dtype=float)
    k, n = int(round(ind.sum())), int(ind.size)
    w_lo, w_hi = wilson(k, n)
    out = {"k": k, "n": n, "share": k / max(n, 1), "wilson_lo": w_lo, "wilson_hi": w_hi}
    if cmc is not None:
        c = np.asarray(cmc, dtype=float)
        if boot is not None and boot.n == c.size:
            m, se, lo, hi = boot.ci(c)
        else:
            m = float(c.mean()); se = float(c.std(ddof=1) / np.sqrt(c.size)) if c.size > 1 else 0.0
            lo, hi = m - 1.96 * se, m + 1.96 * se
        out.update(p=float(m), se=float(se), ci_lo=float(max(0.0, lo)), ci_hi=float(min(1.0, hi)), estimator="conditional")
    else:
        se = float(np.sqrt(out["share"] * (1 - out["share"]) / max(n, 1)))
        out.update(p=out["share"], se=se, ci_lo=w_lo, ci_hi=w_hi, estimator="frequency")
    return out


def safety_metrics(R, a, boot=None):
    """Policy level safety forecast (levels, not differences) from a reduced policy."""
    H = int(R["horizon"]); years = H / 12.0
    d = discount(H, a["discount_rate"])
    hv = a["harm_valuation_multiplier"]
    harm_exp = (R["harm_exp"] * d).sum(axis=1) * hv
    harm_drawn = (R["harm"] * d).sum(axis=1) * hv
    cat_exp = (R["cat_harm_exp"] * d).sum(axis=1) * hv
    pc = proportion(R["cat_any"], boot, cmc=R["cat_cmc"])
    pm = proportion(R["major_any"], boot)
    out = {
        "incidents_per_year": summarise(R["n_incidents"].sum(axis=1) / years, boot),
        "major_per_year": summarise(R["n_major"].sum(axis=1) / years, boot),
        "p_major": pm["p"], "p_major_detail": pm,
        "p_catastrophe": pc["p"], "p_catastrophe_detail": pc,
        "expected_harm_npv": summarise(harm_exp, boot, drawn=harm_drawn),
        "expected_catastrophe_harm_npv": float(cat_exp.mean()),
        "harm_by_year": [float(R["harm_exp"][:, y * 12:(y + 1) * 12].sum(axis=1).mean()) for y in range(H // 12)],
    }
    if "inc_cat" in R:
        out.update({
            "incidents_by_category_per_year": {k: float(R["inc_cat"][:, i].mean() / years) for i, k in enumerate(("misuse", "accident", "systemic"))},
            "safety_level_end": float(R["safety_end"].mean()), "safety_share_end": float(R["sigma_end"].mean()),
            "capability_end": float(R["cap_eff_end"].mean()), "frontier_capability_end": float(R["frontier_end"].mean()),
            "trust_end": float(R["trust"][:, -1].mean()), "offshore_share_end": float(R["offshore_end"].mean()),
            "compliance_share": float(R["comply_end"].mean()), "service_index_end": float(R["service"][:, -1].mean())})
    return out


def news_metrics(R, B=None, boot=None):
    """What the wire will look like under this policy: expected counts a year, pressure, tone."""
    H = int(R["horizon"]); years = H / 12.0
    nc = R["news_counts"]
    names = ("minor incidents", "major incidents", "catastrophes", "enforcement actions", "relocations", "capability milestones")
    counts = {n: summarise(nc[:, :, i].sum(axis=1) / years, boot) for i, n in enumerate(names)}
    P = R["pressure"]
    early = R["tone_early"]
    out = {"headlines_per_year": counts, "peak_pressure": summarise(P.max(axis=1), boot),
           "mean_pressure": float(P.mean()), "p_hearing": float((P.max(axis=1) > 0.45).mean()),
           "share_months_high_pressure": float((P > 0.3).mean()), "early_tone": float(early.mean()),
           "quarterly_negative": [float(nc[:, q * 3:(q + 1) * 3, :4].sum(axis=(1, 2)).mean()) for q in range(H // 3)],
           "quarterly_negative_hi": [float(np.percentile(nc[:, q * 3:(q + 1) * 3, :4].sum(axis=(1, 2)), 90)) for q in range(H // 3)],
           "quarterly_pressure": [float(P[:, q * 3:(q + 1) * 3].mean()) for q in range(H // 3)]}
    if B is not None:
        out["early_tone_vs_baseline"] = float(early.mean() - B["tone_early"].mean())
    return out


def headline_paths(R, B):
    """Per path headline score: the index against the status quo over months 1 to 6 plus a tenth of the early tone
    difference (how the instrument looks in the first half year of prices and coverage)."""
    return (R["idx_early"] / B["idx_early"] - 1.0).mean(axis=1) + 0.1 * (R["tone_early"] - B["tone_early"])


def market_metrics(R, B, a, boot=None):
    """Per firm and industry: value change, probability of gain, early reaction, the AI index. Every index is
    measured from the same pre intervention valuation (cap0), common to the whole battery."""
    H = int(R["horizon"])
    d_end = float(discount(H, a["discount_rate"])[-1])
    cap0 = R["cap0"]
    idx_p, idx_b = R["idx"], B["idx"]
    early = (idx_p[:, 1:7] / idx_b[:, 1:7] - 1.0).mean(axis=1)
    end = idx_p[:, -1] / idx_b[:, -1] - 1.0
    dE = R["earn_exp_f"] - B["earn_exp_f"]             # expected liability in place of the liability drawn
    dE_drawn = R["earn_f"] - B["earn_f"]
    dcap = (R["cap_end_f"] - B["cap_end_f"]) * d_end
    n = R["n_paths"]
    pm, pmb = R["price_sum"] / n, B["price_sum"] / B["n_paths"]
    firms = []
    for f, lab in enumerate(R["labels"]):
        tot = dE[:, f] + dcap[:, f]
        firms.append({"firm": lab, "sector": R["sectors"][f], "cap0": float(cap0[f]),
                      "value_change": summarise(tot, boot, drawn=dE_drawn[:, f] + dcap[:, f]), "earnings_change_npv": float(dE[:, f].mean()),
                      "cap_change": float(dcap[:, f].mean()), "cap_change_pct": float((dcap[:, f] / cap0[f]).mean()),
                      "price_end": float(pm[-1, f]), "price_end_base": float(pmb[-1, f]),
                      "early_reaction": float((R["price_early_f"][:, 1:7, f] / B["price_early_f"][:, 1:7, f] - 1.0).mean()),
                      "offshore_end": float(R["offshore_end_f"][:, f].mean()), "comply_end": float(R["comply_end_f"][:, f].mean()),
                      "safety_share_end": float(R["sigma_end_f"][:, f].mean())})
    sectors = {}
    for f, s in enumerate(R["sectors"]):
        sectors.setdefault(s, []).append(f)
    sector_rows = [{"sector": s, "value_change": summarise((dE[:, ix] + dcap[:, ix]).sum(axis=1), boot,
                                                           drawn=(dE_drawn[:, ix] + dcap[:, ix]).sum(axis=1)), "cap0": float(cap0[ix].sum())}
                   for s, ix in sectors.items()]
    value_change = dE.sum(axis=1) + dcap.sum(axis=1)
    value_drawn = dE_drawn.sum(axis=1) + dcap.sum(axis=1)
    rel = (idx_p / idx_b - 1.0) * 100.0            # the index against the status quo on the same path, in percent
    return {"industry_value_change": summarise(value_change, boot, drawn=value_drawn),
            "rel_mean": rel.mean(axis=0).tolist(), "rel_lo": np.percentile(rel, 10, axis=0).tolist(),
            "rel_hi": np.percentile(rel, 90, axis=0).tolist(),
            "industry_cap_change": summarise(dcap.sum(axis=1), boot),
            "industry_earnings_change": summarise(dE.sum(axis=1), boot, drawn=dE_drawn.sum(axis=1)),
            "industry_cap0": float(cap0.sum()),
            "early_reaction": summarise(early, boot), "end_reaction": summarise(end, boot),
            "index_mean": idx_p.mean(axis=0).tolist(), "index_lo": np.percentile(idx_p, 10, axis=0).tolist(),
            "index_hi": np.percentile(idx_p, 90, axis=0).tolist(), "index_base_mean": idx_b.mean(axis=0).tolist(),
            "firms": firms, "sectors": sector_rows,
            "firm_price_mean": pm.T.tolist()}
