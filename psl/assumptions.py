"""Declared assumptions: every value judgement and structural parameter the
welfare, safety and market figures depend on, in one place, with its
default, its bounds, its unit and a sentence on where it comes from.

They are written to `assumptions.json` in the run directory, hashed into
the ledger at Gate 1, cited in the briefing and varied one at a time in the
tornado. Nothing in the engine reads a magic number that is not here.
"""

import copy
import hashlib
import json

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
    """Rows for the briefing: key, value, unit, meaning, bounds."""
    return [{"assumption": k, "value": a[k], "unit": SPEC[k][3], "meaning": SPEC[k][4],
             "low": SPEC[k][1], "high": SPEC[k][2]} for k in SPEC]


# the value judgements the tornado varies, with the alternative values it tries
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
# which can be recomputed from the stored aggregates (no re simulation)
REWEIGHTABLE = {"harm_valuation_multiplier", "discount_rate", "consumer_surplus_base_bn", "cs_elasticity",
                "productivity_base_bn", "compliance_deadweight_share", "leakage_value_share", "labour_adjustment_bn",
                "trust_elasticity", "domestic_ownership_share"}
