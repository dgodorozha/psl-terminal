"""Declared assumptions: every value judgement and behavioural parameter the
welfare, safety and market figures depend on, in one place, with its
default, its validation bounds, its unit, a sentence on what it means and
the plausible range the sensitivity analysis moves it over.

They are written to `assumptions.json` in the run directory, hashed into
the ledger at Gate 1 and cited in the briefing. Every one of them is moved
to the ends of its plausible range in the screen, and all of them are
drawn jointly in the parameter uncertainty analysis (assurance.py). The
structural constants the engine also uses (the firms' action grid, the
salience weights of the news index and a few shape constants) are fixed,
not assumptions, and are listed in CONSTANTS and in docs/METHOD.md.

Two different intervals attach to an assumption and must not be confused:
  bounds (SPEC)   what the Lab will accept from a user; wide, a validation limit
  range (RANGE)   where the value could plausibly lie; a declared judgement, a
                  prior and not an estimate, used by the screen and the joint draw
"""

import copy
import hashlib
import json

import numpy as np

from ._common import NAMES as _NAMES

# key: (default, low, high, unit, meaning)
SPEC = {
    # ---- discounting and valuation ----
    "discount_rate": (0.03, 0.0, 0.10, "a year",
                      "social discount rate applied to every monthly flow"),
    "harm_valuation_multiplier": (1.0, 0.25, 4.0, "multiple",
                                  "scales the monetised harm of incidents; 1.0 takes the engine's damages at face value"),
    "consumer_surplus_base_bn": (250.0, 50.0, 1500.0, "$bn a year",
                                 "annual consumer surplus from AI services at the starting level of capability and reach"),
    "cs_elasticity": (0.6, 0.1, 1.5, "elasticity",
                      "proportional change in consumer surplus per proportional change in the AI service index"),
    "productivity_base_bn": (400.0, 50.0, 2000.0, "$bn a year",
                             "annual output uplift attributable to AI adoption at the starting service index"),
    "productivity_elasticity": (0.8, 0.1, 1.5, "elasticity",
                                "proportional change in the output uplift per proportional change in the service index"),
    "trust_elasticity": (0.5, 0.0, 1.5, "elasticity",
                         "proportional change in realised adoption benefits per proportional change in public trust"),
    "benefit_overlap_share": (0.0, 0.0, 1.0, "share",
                              "share of the output uplift already counted as consumer surplus or as the AI firms' own profit, removed "
                              "from the output uplift; 0 takes the three benefit components as defined, without overlap"),
    "compliance_deadweight_share": (0.7, 0.3, 1.0, "share",
                                    "share of compliance spend that is a real resource cost rather than a transfer"),
    "enforcement_cost_bn": (0.4, 0.05, 2.0, "$bn a year per unit of capacity",
                            "public budget consumed by one unit of enforcement capacity"),
    "leakage_value_share": (0.35, 0.0, 1.0, "share",
                            "domestic value added lost per dollar of revenue whose activity moves offshore"),
    "labour_adjustment_bn": (2.0, 0.0, 10.0, "$bn per index point",
                             "short run adjustment cost per point of growth in the AI service index (displacement, retraining)"),
    "domestic_ownership_share": (0.6, 0.0, 1.0, "share",
                                 "share of the firms' operating profit that accrues to residents and counts in national welfare"),
    "insurance_admin_share": (0.5, 0.0, 1.0, "share",
                              "share of the insurance loading that is a real resource cost (underwriting, administration) rather than a "
                              "transfer to insurers"),
    # ---- hazard ----
    "hazard_base_misuse": (0.08, 0.01, 0.3, "a month per firm",
                           "monthly rate of a reportable misuse incident for a firm at capability 1, full reach and no safety practice"),
    "hazard_base_accident": (0.05, 0.01, 0.3, "a month per firm", "the same for accidents and failures"),
    "hazard_base_systemic": (0.02, 0.002, 0.15, "a month per firm", "the same for systemic incidents (markets, infrastructure, information)"),
    "hazard_capability_elasticity": (1.3, 0.5, 2.5, "elasticity", "incident rate scales with capability to this power"),
    "hazard_safety_elasticity": (1.8, 0.5, 4.0, "per unit of safety level", "incident rate falls as exp(-elasticity x safety level)"),
    "hazard_reach_elasticity": (1.0, 0.3, 2.0, "elasticity", "incident rate scales with deployment reach to this power"),
    "offshore_laxity": (0.6, 0.0, 2.0, "multiple", "extra incident rate on activity moved offshore, relative to home"),
    "severity_misuse_median_bn": (0.15, 0.01, 2.0, "$bn", "median monetised harm of a misuse incident"),
    "severity_accident_median_bn": (0.3, 0.02, 3.0, "$bn", "median monetised harm of an accident"),
    "severity_systemic_median_bn": (1.0, 0.1, 10.0, "$bn", "median monetised harm of a systemic incident"),
    "severity_sigma": (1.1, 0.5, 2.0, "log scale", "lognormal dispersion of incident harm (heavy tail)"),
    "major_incident_bn": (1.0, 0.2, 10.0, "$bn", "harm above which an incident counts as major"),
    "catastrophe_prior_monthly": (0.002, 0.0, 0.02, "a month per firm",
                                  "monthly probability of a catastrophic incident for a firm above critical capability with no safety practice"),
    "catastrophe_capability": (1.6, 1.0, 3.0, "capability index", "capability above which the catastrophic tail is live"),
    "catastrophe_harm_bn": (400.0, 20.0, 3000.0, "$bn", "median monetised harm of a catastrophic incident"),
    "unsafe_release_share": (0.35, 0.05, 0.8, "share", "share of the incident rate attributable to releases an evaluation could catch"),
    "catastrophe_severity_sigma": (0.5, 0.0, 1.5, "log scale", "lognormal dispersion of catastrophic harm around its median"),
    "catastrophe_correlation": (0.3, 0.0, 0.9, "correlation",
                                "correlation of catastrophic failures across firms within a month (one factor Gaussian copula): "
                                "shared models, components and vulnerabilities; 0 makes the firms' catastrophes independent given the state"),
    "open_weights_misuse_multiplier": (1.3, 1.0, 3.0, "multiple",
                                       "misuse rate of a developer that publishes weights, relative to one that does not"),
    # ---- firm behaviour ----
    "capability_growth": (0.023, 0.005, 0.06, "a month",
                          "monthly log growth of the capability index when all R&D goes to capability (a doubling in about 30 months)"),
    "safety_learning": (0.08, 0.02, 0.3, "a month",
                        "monthly gain in safety practice at saturation; the gain is a x share/(share + 0.1), diminishing in the share"),
    "growth_fade_months": (30.0, 6.0, 120.0, "months", "time constant over which a firm's growth fades towards the long run rate"),
    "safety_substitution": (0.6, 0.0, 1.0, "share",
                            "share of safety spend that displaces capability R&D (the rest is additional budget or spills over)"),
    "export_control_chip_loss": (0.10, 0.0, 0.4, "a year", "annual revenue growth lost by the chip sector under full export controls"),
    "long_run_growth": (0.06, 0.0, 0.2, "a year", "the growth rate firms fade towards"),
    "safety_decay": (0.02, 0.0, 0.08, "a month", "monthly erosion of safety practice without investment"),
    "revenue_capability_beta": (0.5, 0.1, 1.2, "elasticity", "revenue growth per unit of log capability growth"),
    "revenue_reach_beta": (0.8, 0.1, 2.0, "elasticity", "revenue relative to the frictionless, full trust reach path, to this power"),
    "reach_speed": (0.08, 0.02, 0.3, "a month", "speed at which reach closes on its capability and trust determined ceiling"),
    "growth_value_weight": (3.0, 0.5, 8.0, "years of revenue", "how a firm values a year of extra growth against a year of cost"),
    "relocation_cost": (0.08, 0.0, 0.5, "share of moved revenue", "one off cost of moving a unit of activity offshore"),
    "offshore_revenue_haircut": (0.12, 0.0, 0.5, "share", "revenue lost per unit of activity offshore (talent, customers, latency)"),
    "firm_risk_aversion": (0.6, 0.0, 2.0, "multiple", "weight on the variance of expected liability in the firm's choice"),
    "firm_optimism": (0.7, 0.3, 1.0, "multiple", "the share of its true incident rate a firm believes when it plans"),
    "audit_rate": (0.5, 0.05, 1.0, "a month at full capacity", "probability a firm in scope is audited in a month at capacity 1"),
    "insurance_loading": (0.25, 0.0, 1.0, "share", "premium above expected liability charged by insurers under a mandate"),
    "safe_harbour_shield": (0.7, 0.0, 1.0, "share", "share of liability a compliant firm avoids under a safe harbour"),
    "moratorium_research_slowdown": (0.5, 0.0, 1.0, "share", "share of capability growth lost by a firm in scope while a moratorium holds"),
    "culture_weight": (0.6, 0.0, 2.0, "$bn per unit of revenue",
                       "value a firm places on a unit gain in safety practice per unit of revenue, multiplied by its culture score"),
    "reach_ceiling_k": (1.5, 0.5, 4.0, "per unit of capability", "speed at which the reach ceiling 1 - exp(-k C) saturates in capability"),
    "open_weights_restriction_growth_loss": (0.10, 0.0, 0.4, "a year",
                                             "annual revenue growth lost by an open weights developer while publishing is restricted"),
    # ---- regulator, trust, news ----
    "enforcement_response": (0.25, 0.05, 1.0, "a month", "speed at which enforcement intensity follows public pressure"),
    "trust_recovery": (0.05, 0.01, 0.2, "a month", "monthly recovery of public trust towards 1"),
    "trust_harm_sensitivity": (0.04, 0.0, 0.3, "per log $bn", "fall in trust per unit of log monetised harm in a month"),
    "news_memory": (0.75, 0.3, 0.95, "a month", "persistence of the news pressure index"),
    "news_reporting_boost": (0.35, 0.0, 1.0, "share", "extra salience of incidents when reporting is mandatory"),
    # ---- markets ----
    "market_vol": (0.045, 0.01, 0.12, "a month", "volatility of the common market factor"),
    "sentiment_persistence": (0.85, 0.5, 0.98, "a month", "persistence of the price's non fundamental component"),
    "news_price_impact": (0.06, 0.0, 0.3, "per unit of pressure", "price impact of a unit of news pressure on an exposed firm"),
    "incident_jump": (0.5, 0.0, 2.0, "multiple", "own incident price jump per log unit of harm relative to revenue"),
    "contagion": (0.3, 0.0, 1.0, "share", "share of an own incident jump felt by the rest of the sector"),
    "announcement_impact": (0.9, 0.0, 3.0, "multiple", "price reaction at announcement per unit of expected compliance cost over earnings"),
    "chip_demand_coupling": (0.6, 0.0, 1.5, "elasticity", "chip and cloud revenue growth per unit of model developers' capability growth"),
    "open_weights_diffusion": (0.1, 0.0, 0.8, "share", "capability spillover from published weights to the rest of the economy"),
}

DEFAULTS = {k: v[0] for k, v in SPEC.items()}

# A short title for every assumption, for tables and sentences (the meaning in SPEC is the definition).
TITLE = {
    "discount_rate": "Social discount rate",
    "harm_valuation_multiplier": "Harm valuation multiplier",
    "consumer_surplus_base_bn": "Consumer surplus base",
    "cs_elasticity": "Consumer surplus elasticity",
    "productivity_base_bn": "Output uplift base",
    "productivity_elasticity": "Output uplift elasticity",
    "trust_elasticity": "Trust elasticity of adoption benefits",
    "benefit_overlap_share": "Overlap of the output uplift with other benefits",
    "compliance_deadweight_share": "Resource share of compliance spend",
    "enforcement_cost_bn": "Enforcement cost",
    "leakage_value_share": "Value lost per dollar moved offshore",
    "labour_adjustment_bn": "Labour adjustment cost",
    "domestic_ownership_share": "Resident ownership share",
    "insurance_admin_share": "Resource share of the insurance loading",
    "hazard_base_misuse": "Misuse incident rate",
    "hazard_base_accident": "Accident rate",
    "hazard_base_systemic": "Systemic incident rate",
    "hazard_capability_elasticity": "Capability elasticity of incidents",
    "hazard_safety_elasticity": "Safety elasticity of incidents",
    "hazard_reach_elasticity": "Reach elasticity of incidents",
    "offshore_laxity": "Offshore laxity",
    "severity_misuse_median_bn": "Median harm of a misuse incident",
    "severity_accident_median_bn": "Median harm of an accident",
    "severity_systemic_median_bn": "Median harm of a systemic incident",
    "severity_sigma": "Dispersion of incident harm",
    "major_incident_bn": "Major incident threshold",
    "catastrophe_prior_monthly": "Monthly catastrophe probability",
    "catastrophe_capability": "Critical capability",
    "catastrophe_harm_bn": "Median harm of a catastrophe",
    "unsafe_release_share": "Share of incidents an evaluation could catch",
    "catastrophe_severity_sigma": "Dispersion of catastrophic harm",
    "catastrophe_correlation": "Correlation of catastrophes across firms",
    "open_weights_misuse_multiplier": "Misuse multiplier for open weights",
    "capability_growth": "Capability growth",
    "safety_learning": "Safety learning rate",
    "growth_fade_months": "Growth fade time",
    "safety_substitution": "Safety spend that displaces capability R&D",
    "export_control_chip_loss": "Chip growth lost to export controls",
    "long_run_growth": "Long run growth",
    "safety_decay": "Safety decay",
    "revenue_capability_beta": "Revenue response to capability",
    "revenue_reach_beta": "Revenue response to reach",
    "reach_speed": "Reach adjustment speed",
    "growth_value_weight": "Weight firms put on growth",
    "relocation_cost": "Relocation cost",
    "offshore_revenue_haircut": "Revenue lost offshore",
    "firm_risk_aversion": "Firm risk aversion",
    "firm_optimism": "Firm optimism about incidents",
    "audit_rate": "Audit rate",
    "insurance_loading": "Insurance loading",
    "safe_harbour_shield": "Safe harbour shield",
    "moratorium_research_slowdown": "Research slowdown under a moratorium",
    "culture_weight": "Weight of safety culture",
    "reach_ceiling_k": "Reach ceiling saturation",
    "open_weights_restriction_growth_loss": "Growth lost to an open weights restriction",
    "enforcement_response": "Enforcement response speed",
    "trust_recovery": "Trust recovery",
    "trust_harm_sensitivity": "Trust sensitivity to harm",
    "news_memory": "News memory",
    "news_reporting_boost": "Salience boost from mandatory reporting",
    "market_vol": "Market volatility",
    "sentiment_persistence": "Sentiment persistence",
    "news_price_impact": "Price impact of news pressure",
    "incident_jump": "Price jump on an own incident",
    "contagion": "Sector contagion",
    "announcement_impact": "Announcement price impact",
    "chip_demand_coupling": "Chip demand coupling",
    "open_weights_diffusion": "Open weights diffusion",
}
assert set(TITLE) == set(SPEC), sorted(set(TITLE) ^ set(SPEC))
assert len(set(TITLE.values())) == len(TITLE)
_NAMES.update(TITLE)


def title(key):
    return TITLE.get(key, key)


def defaults():
    return copy.deepcopy(DEFAULTS)


def validate(doc):
    """Merge a user document over the defaults within bounds; returns (assumptions, notes)."""
    out, notes = defaults(), []
    if not isinstance(doc, dict):
        return out, ["assumptions must be a JSON object; defaults used"]
    for k, v in doc.items():
        if k not in SPEC:
            notes.append(f"{k}: unknown assumption ignored")
            continue
        try:
            x = float(v)
        except (TypeError, ValueError):
            notes.append(f"{k}: not a number, default kept")
            continue
        lo, hi = SPEC[k][1], SPEC[k][2]
        c = min(hi, max(lo, x))
        if c != x:
            notes.append(f"{k}: {x} clamped to {c}")
        out[k] = c
    return out, notes


def assumptions_hash(a):
    return hashlib.sha256(json.dumps(a, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def table(a):
    """Rows for the briefing: key, value, unit, meaning, bounds, plausible range, and whether the assumption enters
    only the welfare accounting."""
    return [{"assumption": k, "title": TITLE[k], "value": a[k], "unit": SPEC[k][3], "meaning": SPEC[k][4],
             "low": SPEC[k][1], "high": SPEC[k][2], "range_low": RANGE[k][0], "range_high": RANGE[k][1],
             "welfare_only": k in WELFARE_ONLY} for k in SPEC]


# ---------------------------------------------------------------- plausible ranges --
# The value judgements, with the alternative values the tornado has always tried.
TORNADO = {
    "harm_valuation_multiplier": (0.5, 2.0),
    "discount_rate": (0.01, 0.07),
    "consumer_surplus_base_bn": (150.0, 600.0),
    "productivity_base_bn": (200.0, 800.0),
    "compliance_deadweight_share": (0.4, 1.0),
    "leakage_value_share": (0.1, 0.7),
    "labour_adjustment_bn": (0.0, 5.0),
    "catastrophe_prior_monthly": (0.0005, 0.005),
    "catastrophe_harm_bn": (150.0, 1200.0),
    "hazard_safety_elasticity": (1.4, 3.0),
    "offshore_laxity": (0.2, 1.2),
    "safety_substitution": (0.3, 1.0),
    "cs_elasticity": (0.3, 1.0),
    "trust_elasticity": (0.2, 1.0),
    "domestic_ownership_share": (0.3, 0.9),
}
# The rest of the declared assumptions. Every range brackets the default and lies inside the bounds.
_OTHER = {
    "productivity_elasticity": (0.5, 1.1),
    "benefit_overlap_share": (0.0, 0.5),
    "enforcement_cost_bn": (0.2, 0.8),
    "insurance_admin_share": (0.25, 0.75),
    "hazard_base_misuse": (0.05, 0.13),
    "hazard_base_accident": (0.03, 0.08),
    "hazard_base_systemic": (0.01, 0.04),
    "hazard_capability_elasticity": (0.9, 1.8),
    "hazard_reach_elasticity": (0.7, 1.4),
    "severity_misuse_median_bn": (0.08, 0.3),
    "severity_accident_median_bn": (0.15, 0.6),
    "severity_systemic_median_bn": (0.5, 2.0),
    "severity_sigma": (0.8, 1.4),
    "major_incident_bn": (0.5, 2.0),
    "catastrophe_capability": (1.3, 2.0),
    "unsafe_release_share": (0.2, 0.5),
    "catastrophe_severity_sigma": (0.25, 0.9),
    "catastrophe_correlation": (0.0, 0.6),
    "open_weights_misuse_multiplier": (1.1, 1.8),
    "capability_growth": (0.015, 0.035),
    "safety_learning": (0.05, 0.12),
    "growth_fade_months": (18.0, 48.0),
    "export_control_chip_loss": (0.05, 0.2),
    "long_run_growth": (0.03, 0.10),
    "safety_decay": (0.01, 0.04),
    "revenue_capability_beta": (0.3, 0.8),
    "revenue_reach_beta": (0.5, 1.2),
    "reach_speed": (0.05, 0.12),
    "growth_value_weight": (1.5, 5.0),
    "relocation_cost": (0.04, 0.16),
    "offshore_revenue_haircut": (0.06, 0.24),
    "firm_risk_aversion": (0.2, 1.2),
    "firm_optimism": (0.5, 0.9),
    "audit_rate": (0.3, 0.8),
    "insurance_loading": (0.1, 0.5),
    "safe_harbour_shield": (0.5, 0.9),
    "moratorium_research_slowdown": (0.3, 0.7),
    "culture_weight": (0.3, 1.2),
    "reach_ceiling_k": (1.0, 2.2),
    "open_weights_restriction_growth_loss": (0.05, 0.2),
    "enforcement_response": (0.12, 0.5),
    "trust_recovery": (0.03, 0.1),
    "trust_harm_sensitivity": (0.02, 0.08),
    "news_memory": (0.6, 0.88),
    "news_reporting_boost": (0.15, 0.6),
    "market_vol": (0.03, 0.065),
    "sentiment_persistence": (0.7, 0.93),
    "news_price_impact": (0.03, 0.12),
    "incident_jump": (0.25, 1.0),
    "contagion": (0.15, 0.5),
    "announcement_impact": (0.45, 1.8),
    "chip_demand_coupling": (0.3, 0.9),
    "open_weights_diffusion": (0.05, 0.2),
}
RANGE = dict(TORNADO, **_OTHER)

# Assumptions that enter only the welfare accounting, never the simulated economy: a change in one of them is
# recomputed exactly from the stored paths; a change in any other needs the battery re simulated.
WELFARE_ONLY = frozenset({
    "discount_rate", "harm_valuation_multiplier", "consumer_surplus_base_bn", "cs_elasticity", "productivity_base_bn",
    "productivity_elasticity", "trust_elasticity", "benefit_overlap_share", "compliance_deadweight_share", "enforcement_cost_bn",
    "leakage_value_share", "labour_adjustment_bn", "domestic_ownership_share", "insurance_admin_share"})
REWEIGHTABLE = WELFARE_ONLY          # the name the earlier releases used

# Assumptions that plausibly move together, drawn with a Gaussian copula in the joint draw (rank correlation
# close to the figure given). Everything else is drawn independently.
CORRELATED = (
    (("hazard_base_misuse", "hazard_base_accident", "hazard_base_systemic"), 0.6,
     "a world with more incidents of one kind has more of the others"),
    (("severity_misuse_median_bn", "severity_accident_median_bn", "severity_systemic_median_bn"), 0.6,
     "incident harm scales with how deeply AI is embedded, whatever the category"),
    (("consumer_surplus_base_bn", "productivity_base_bn"), 0.6, "both scale with how valuable AI services are"),
    (("cs_elasticity", "productivity_elasticity"), 0.5, "both measure how fast benefits grow with the service index"),
    (("relocation_cost", "offshore_revenue_haircut"), 0.4, "both are frictions of operating from another jurisdiction"),
)

# Fixed structural constants of the engine: not assumptions, not varied, documented here and in docs/METHOD.md.
CONSTANTS = {
    "safety share grid": "0.02, 0.05, 0.10, 0.15, 0.20, 0.30 of R&D (the firm's choice set)",
    "offshore share grid": "0, 0.3, 0.6, 0.9 of activity (capped by the firm's mobility); at most 0.1 moves in a month",
    "reference safety share": "0.10, the safety share the baseline growth rates already assume",
    "release milestone": "0.25 capability index points between release headlines",
    "news salience weights": "minor incident 0.12, major incident 0.45, catastrophe 1.2, enforcement action 0.2, "
                             "relocation 0.15, capability milestone 0.08 (positive), background noise 0.03",
    "hearing threshold": "news pressure above 0.45; high pressure above 0.3",
    "enforcement target": "capacity x (0.4 + 0.6 x news pressure); starting intensity 0.3 x capacity + 0.02",
    "expected penalty factor": "1.5 x the fine a non compliant firm expects when audited (reputational surcharge)",
    "valuation floor": "revenue multiple plus a smooth floor on the earnings multiple at 5% of revenue",
    "trust floor": "0.3; enforcement intensity and compliance shares are clipped to [0, 1]",
    "monthly revenue growth": "clipped to [-20%, +30%]",
    "headline score": "the index reaction over months 1 to 6 plus 0.1 x the early tone difference",
}

for _k, (_lo, _hi) in RANGE.items():
    assert SPEC[_k][1] <= _lo <= SPEC[_k][0] <= _hi <= SPEC[_k][2], f"range of {_k} must bracket the default inside the bounds"
assert set(RANGE) == set(SPEC), sorted(set(SPEC) ^ set(RANGE))


def oat_levels():
    """Every assumption at the low and at the high end of its plausible range: [(key, 'low' | 'high', value)]."""
    out = []
    for k, (lo, hi) in RANGE.items():
        out.append((k, "low", float(lo))); out.append((k, "high", float(hi)))
    return out


def correlation_matrix(keys):
    """The copula correlation matrix over `keys` implied by CORRELATED (identity elsewhere)."""
    keys = list(keys)
    C = np.eye(len(keys))
    for group, rho, _ in CORRELATED:
        ix = [keys.index(k) for k in group if k in keys]
        for i in ix:
            for j in ix:
                if i != j:
                    C[i, j] = rho
    return C


def sample(m, seed=0, keys=None, base=None, u=None):
    """m joint draws of the assumptions over their plausible ranges: a Latin hypercube, a Gaussian copula for the
    correlated groups, and a triangular distribution on each range with its mode at the value in `base` (the
    run's assumptions; the defaults when not given). Returns {key: array (m,)} for `keys` (all by default).
    `u` (m, len(keys)) in [0, 1] replaces the hypercube (the variance decomposition supplies its own design)."""
    from .stats import gaussian_copula, latin_hypercube, triangular_ppf
    keys = list(keys) if keys is not None else list(RANGE)
    base = base or DEFAULTS
    if u is None:
        u = gaussian_copula(latin_hypercube(m, len(keys), seed), correlation_matrix(keys))
    out = {}
    for j, k in enumerate(keys):
        lo, hi = RANGE[k]
        mode = min(hi, max(lo, float(base.get(k, DEFAULTS[k]))))
        out[k] = triangular_ppf(u[:, j], lo, mode, hi)
    return out
