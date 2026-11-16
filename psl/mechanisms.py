"""The mechanism register: for every causal mechanism in the synthetic economy, what it assumes, what it rests
on, how it would be calibrated, what observation would test it, and whether the Lab has done either.

Common random numbers make a comparison between two policies precise inside the model: the same dice, so the
difference is the policy's. They say nothing about whether the model's mechanisms hold in the AI industry. That
is an empirical question, mechanism by mechanism, and this register is the honest answer to it: one mechanism
(the market's early reaction) can be confronted with data the analyst uploads; the rest are declared
assumptions with plausible ranges, moved in the screen and the joint draw, and untested.

Sources are the literature that motivates a mechanism's form or brackets its magnitudes. None of them is a
calibration: no parameter of the Lab is estimated from them.
"""

MECHANISMS = (
    {"id": "incident_hazard", "mechanism": "Reportable incidents arrive at a rate that rises with released capability and deployment reach "
                                           "and falls with safety practice",
     "equation": "lambda_k = h_k x C_eff^eta_C x exp(-eta_S S) x D^eta_D x (1 + O x laxity) x (1 - evaluation catch x unsafe share)",
     "assumptions": ["hazard_base_misuse", "hazard_base_accident", "hazard_base_systemic", "hazard_capability_elasticity",
                     "hazard_safety_elasticity", "hazard_reach_elasticity"],
     "source": "Public incident counts are media derived and their growth mixes use with reporting (AI Index 2025, chapter 3; AI Incident "
               "Database): they bracket orders of magnitude and cannot identify the elasticities.",
     "identifying_assumption": "Given the state, incidents are independent across firms, months and categories; capability, safety and reach "
                               "act multiplicatively and separably.",
     "calibration": "None applied. A calibration would fit incident counts with exposure offsets and a reporting rate model to capability and "
                    "deployment proxies.",
     "validation_test": "Held out incident counts per firm and year inside the model's predictive interval; the sign and size of the safety "
                        "elasticity from before and after comparisons at firms that adopt evaluation regimes.",
     "status": "uncalibrated", "tested_here": False},
    {"id": "severity", "mechanism": "The monetised harm of an incident is lognormal with a heavy tail; an incident at or above a threshold is major",
     "equation": "harm = median_k x exp(sigma z); major when harm >= threshold (each incident classified on its own harm)",
     "assumptions": ["severity_misuse_median_bn", "severity_accident_median_bn", "severity_systemic_median_bn", "severity_sigma", "major_incident_bn"],
     "source": "Severity is not measured in the public incident record; heavy tailed loss distributions are the standard form for operational and "
               "cyber losses.",
     "identifying_assumption": "Severity is independent of the incident's occurrence and of the state given the category.",
     "calibration": "None applied. A calibration would fit the tail index and scale of documented loss amounts by category.",
     "validation_test": "The empirical tail of documented losses against the lognormal fit; the share of incidents above the major threshold.",
     "status": "uncalibrated", "tested_here": False},
    {"id": "catastrophic_tail", "mechanism": "Above a critical capability a firm faces a small monthly probability of a catastrophic incident, "
                                             "reduced by safety practice and evaluation, and correlated across firms",
     "equation": "p = prior x 1{C_eff > C*} x exp(-eta_S S) x (1 + O x laxity) x (1 - 0.5 x evaluation); joint failures by a one factor "
                 "Gaussian copula with correlation rho; harm = H x exp(sigma_c z)",
     "assumptions": ["catastrophe_prior_monthly", "catastrophe_capability", "catastrophe_harm_bn", "catastrophe_severity_sigma", "catastrophe_correlation"],
     "source": "Quantified estimates come from elicitation and disagree by about an order of magnitude (Grace et al. 2025, JAIR 84: median 5% for "
               "extremely bad outcomes; the 2022 Existential Risk Persuasion Tournament: 3% from domain experts against 0.38% from superforecasters "
               "for AI caused extinction by 2100). They motivate a live tail; they do not calibrate it.",
     "identifying_assumption": "The tail is live only above a capability threshold; shared vulnerabilities enter through one common factor and leave "
                               "each firm's own probability unchanged.",
     "calibration": "None possible from frequency data: no such event has been observed.",
     "validation_test": "Not testable before the event. Treated by sensitivity: both ends of every range in the screen, the joint draw, and the heavy "
                        "tail and systemic variants. Near miss frequencies would be partial evidence on the prior.",
     "status": "uncalibrated, untestable ex ante", "tested_here": False},
    {"id": "safety_practice", "mechanism": "The share of R&D spent on safety raises safety practice with diminishing returns and displaces part of "
                                           "capability growth; practice decays without investment",
     "equation": "S' = S + a x sigma / (sigma + 0.1) x (1 - S) - decay x S; capability growth x (1 - substitution x sigma)",
     "assumptions": ["safety_learning", "safety_decay", "safety_substitution", "culture_weight"],
     "source": "Structural assumption; the development race literature motivates the trade off between safety and speed without measuring it.",
     "identifying_assumption": "Safety practice is one dimensional and firm specific; returns to safety spend are concave.",
     "calibration": "None applied.",
     "validation_test": "Firm level safety budgets against evaluation pass rates and incident rates over time.",
     "status": "uncalibrated", "tested_here": False},
    {"id": "evaluation", "mechanism": "A mandated evaluation catches a share of unsafe releases before deployment",
     "equation": "incident rate x (1 - catch rate x unsafe release share); catastrophe probability x (1 - 0.5 x catch rate)",
     "assumptions": ["unsafe_release_share"],
     "source": "The catch rate is a design parameter of each instrument; the share of incidents a pre deployment evaluation could have caught is a "
               "judgement.",
     "identifying_assumption": "Evaluations act only on the releases of compliant firms in scope; compliance theatre halves their effect.",
     "calibration": "None applied.",
     "validation_test": "Post mortems of incidents: the share traceable to failures an evaluation at release would have found.",
     "status": "uncalibrated", "tested_here": False},
    {"id": "firm_choice", "mechanism": "Each month a firm chooses its safety share, offshore share and whether to comply by maximising a one year "
                                       "expected payoff under its own optimistic view of incident risk",
     "equation": "max over the action grid of growth value - compliance - expected penalty - relocation - haircut - liability - risk + culture",
     "assumptions": ["growth_value_weight", "firm_optimism", "firm_risk_aversion", "audit_rate", "revenue_capability_beta"],
     "source": "Compliance cost magnitudes are bracketed by the European Commission's impact assessment for the AI Act (SWD(2021) 84 final: about "
               "EUR 6,000 to 7,000 per high risk system, 4 to 5% of its cost); the investment response to a digital regulation by Jia, Jin and "
               "Wagman (2021, Marketing Science 40(4): 26.1% fewer venture deals after GDPR).",
     "identifying_assumption": "Firms optimise myopically over twelve months with a common rule; the structural variants replace it with six and "
                               "twenty four months.",
     "calibration": "None applied.",
     "validation_test": "Observed compliance rates, safety budgets and release cadence after an instrument takes effect, against the model's.",
     "status": "uncalibrated", "tested_here": False},
    {"id": "relocation", "mechanism": "Firms move activity offshore when the instrument binds at home; moved activity is laxer, loses revenue and "
                                      "takes domestic rents with it",
     "equation": "offshore share chosen from the grid, at most 0.1 a month, capped by mobility; leakage = share x offshore revenue",
     "assumptions": ["relocation_cost", "offshore_revenue_haircut", "offshore_laxity", "leakage_value_share"],
     "source": "Regulatory arbitrage in AI is theorised and anecdotal; its strength as a constraint is not quantified (Lancieri, Edelson and "
               "Bechtold 2025, Theoretical Inquiries in Law 26(1)).",
     "identifying_assumption": "Mobility is a fixed firm trait; a coordinated instrument binds wherever the activity is.",
     "calibration": "None applied.",
     "validation_test": "Changes in establishment location, hiring and model release geography around regulatory dates, against unaffected sectors.",
     "status": "uncalibrated", "tested_here": False},
    {"id": "capability_and_release", "mechanism": "Capability grows with R&D; licensing delays releases; a moratorium freezes released capability "
                                                  "and slows research in scope; published weights diffuse capability",
     "equation": "C' = C x exp(g x (1 - substitution x sigma) x compute + diffusion); C_eff lags C by the release delay",
     "assumptions": ["capability_growth", "moratorium_research_slowdown", "open_weights_diffusion", "open_weights_misuse_multiplier",
                     "open_weights_restriction_growth_loss", "export_control_chip_loss", "chip_demand_coupling"],
     "source": "Structural assumption.",
     "identifying_assumption": "Capability is a scalar index; a delay shifts releases without changing research.",
     "calibration": "None applied.",
     "validation_test": "Release cadence and benchmark trajectories before and after a licensing regime.",
     "status": "uncalibrated", "tested_here": False},
    {"id": "adoption_and_trust", "mechanism": "Reach closes on a ceiling set by released capability and public trust; trust falls with harm and "
                                              "recovers slowly; adoption benefits scale with trust",
     "equation": "D' = D + speed x (1 - friction) x (ceiling x sqrt(T) - D); T' = T + recovery x (1 - T) - sensitivity x log(1 + harm)",
     "assumptions": ["reach_speed", "reach_ceiling_k", "trust_recovery", "trust_harm_sensitivity", "trust_elasticity", "revenue_reach_beta"],
     "source": "The trust channel has no causal estimate in the literature reviewed; survey trust and use move in opposite directions.",
     "identifying_assumption": "Trust is one public index that responds to monetised harm only.",
     "calibration": "None applied.",
     "validation_test": "Survey trust and adoption series around salient incidents.",
     "status": "uncalibrated", "tested_here": False},
    {"id": "revenue_growth", "mechanism": "A firm's revenue grows at a rate that fades from its starting pace towards a long run rate, moves "
                                          "with released capability and reach, and for chip and cloud firms with the developers' growth",
     "equation": "g = long run + (g0 - long run) x exp(-t / fade) + beta_C x (capability growth - reference); R = core x (D / D_ref)^beta_D",
     "assumptions": ["growth_fade_months", "long_run_growth"],
     "source": "Structural assumption; the firms are archetypes with declared starting revenues, margins and growth rates.",
     "identifying_assumption": "Growth responds to capability and reach with constant elasticities common to all firms.",
     "calibration": "None applied; a firm archetype's revenue, margin and growth are the analyst's inputs.",
     "validation_test": "Revenue growth of listed AI firms against capability releases and adoption series.",
     "status": "uncalibrated", "tested_here": False},
    {"id": "enforcement", "mechanism": "Enforcement intensity follows news pressure within the regulator's capacity; audits find the non compliant "
                                       "and fine them",
     "equation": "e' = e + response x (capacity x (0.4 + 0.6 P) - e); audit probability = audit rate x e",
     "assumptions": ["enforcement_response", "audit_rate", "enforcement_cost_bn"],
     "source": "Media attention and regulatory action move together in the agenda setting literature; the functional form is an assumption.",
     "identifying_assumption": "The regulator has no strategy beyond following pressure; fines are collected in full.",
     "calibration": "None applied.",
     "validation_test": "Enforcement actions against news attention series for an existing regulator.",
     "status": "uncalibrated", "tested_here": False},
    {"id": "news", "mechanism": "Incidents, enforcement, relocations and releases become a news pressure index with memory, and a wire of headlines "
                                "on the representative path",
     "equation": "P' = memory x P + (1 - memory) x (1 - exp(-salience)); salience is a weighted count of the month's events",
     "assumptions": ["news_memory", "news_reporting_boost"],
     "source": "Media storms peak within days and decay over about two weeks in the attention literature; the monthly index and its salience "
               "weights (fixed constants) are assumptions.",
     "identifying_assumption": "Salience is additive in event counts with fixed weights.",
     "calibration": "None applied.",
     "validation_test": "Forecast coverage counts for a policy domain against observed counts.",
     "status": "uncalibrated", "tested_here": False},
    {"id": "market", "mechanism": "A firm's price is a fundamental value (revenue and forward earnings multiples) times a sentiment component driven "
                                  "by the market factor, news pressure, incident jumps and, for an instrument announced before it takes effect, "
                                  "an anticipation term",
     "equation": "price = 100 x V / V_pre x exp(xi), with V_pre the valuation before any instrument is announced, common to the battery",
     "assumptions": ["market_vol", "sentiment_persistence", "news_price_impact", "incident_jump", "contagion", "announcement_impact"],
     "source": "Measured analogues are small: US firms subject to GDPR lost 0.6 to 1.1% of market value in the week it became enforceable (Motoki "
               "and Pinto 2024, Journal of Business Finance and Accounting); event studies of regulation have little power in monthly data and "
               "announcements are anticipated (Binder 1985, RAND Journal of Economics 16(2)).",
     "identifying_assumption": "The market prices the state it sees and anticipates an announced instrument only through the announcement term.",
     "calibration": "A firm archetype's beta and idiosyncratic volatility can be estimated from an uploaded price series, on the returns before "
                    "the event month.",
     "validation_test": "Implemented: an event study on an uploaded series mapped to a firm and an instrument, against the model's predictive "
                        "distribution of the early reaction; with eight or more mapped events, the coverage of the 10th to 90th percentile band.",
     "status": "partly calibrable; one mechanism testable here", "tested_here": True},
    {"id": "welfare_bases", "mechanism": "Consumer surplus and the output uplift are powers of the AI service index around declared annual bases",
     "equation": "CS = base_cs x Q^e_cs; output = base_y x Q^e_y x T^e_T",
     "assumptions": ["consumer_surplus_base_bn", "cs_elasticity", "productivity_base_bn", "productivity_elasticity", "trust_elasticity",
                     "benefit_overlap_share", "labour_adjustment_bn", "domestic_ownership_share", "compliance_deadweight_share",
                     "harm_valuation_multiplier", "discount_rate"],
     "source": "Estimates of AI's economic value span about two orders of magnitude (Acemoglu 2025, Economic Policy 40(121): total factor "
               "productivity up by no more than 0.66% over ten years; Goldman Sachs 2023: 7% of global GDP).",
     "identifying_assumption": "Benefits depend on the economy only through the service index and trust; the three benefit components do not "
                               "overlap by definition (welfare.ACCOUNT_MAP), and a declared overlap share removes from the output uplift "
                               "whatever part of it is judged to be already in the other two.",
     "calibration": "None applied; the bases are value judgements and the largest swings of the tornado.",
     "validation_test": "Not a testable mechanism: a valuation. Treated by sensitivity.",
     "status": "declared value judgements", "tested_here": False},
    {"id": "liability_and_insurance", "mechanism": "Liability moves a share of harm to the firm in scope; a safe harbour shields the compliant; a "
                                                   "mandate replaces realised liability with a premium loaded above expected claims",
     "equation": "liability = multiplier x harm x (1 - shield x comply); premium = expected liability x (1 + loading) / 12",
     "assumptions": ["safe_harbour_shield", "insurance_loading", "insurance_admin_share"],
     "source": "The law and economics of liability supplies the mechanism; no premium data for AI liability cover was found.",
     "identifying_assumption": "Insurers price on the firm's own expectation; claims are paid in full.",
     "calibration": "None applied.",
     "validation_test": "Quoted premiums and exclusions for AI liability cover against the model's.",
     "status": "uncalibrated", "tested_here": False},
)


def register():
    return [dict(m) for m in MECHANISMS]


def coverage(assumption_keys):
    """Which declared assumptions belong to a mechanism in the register, and which do not."""
    listed = {k for m in MECHANISMS for k in m["assumptions"]}
    keys = set(assumption_keys)
    return {"listed": sorted(keys & listed), "unlisted": sorted(keys - listed), "unknown": sorted(listed - keys)}
