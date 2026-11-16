# Policy Scenario Lab: method

This document states what the Lab computes, equation by equation, so that a reviewer can check the
code against it and a policy team can see where every number comes from. Its tables of firms,
instruments, assumptions, constants, variants, strategies, mechanisms and profiles are generated from
the code (`python tools/sync_docs.py`), and the test suite fails if they drift from it.

The Lab is synthetic. Its figures are scenario evaluations conditional on a declared model and a
declared set of assumptions; they are not forecasts validated against data, and its preferred option is
the model's answer to a question, to be examined, not an established recommendation. Section 13 says
which parts of the model could be tested, how, and that almost none has been.

## 1. The chain from question to recommendation

| Step | What is fixed there | Where |
|---|---|---|
| Policy question and estimand | the alternatives (every candidate instrument and the status quo), the objective (expected net social value to residents), the constraints | sections 2 and 10 |
| Evidence and assumptions | every value judgement and behavioural parameter with a plausible range; every mechanism with its source, identifying assumption, calibration and test | sections 11 and 13 |
| Simulation and welfare estimation | one counterfactual for all alternatives (common random numbers, one pre intervention valuation), one timing convention, one unit ($bn present value) | sections 3 to 8 |
| Uncertainty and validation | Monte Carlo error, outcome spread, parameter uncertainty and structural uncertainty, reported apart; external validation where data exists | sections 9, 12 and 13 |
| Decision recommendation | compared with the status quo, feasibility verified with its uncertainty, robustness reported | sections 10 and 12 |

## 2. The estimand

For an instrument P and the status quo SQ, simulated on the same random numbers,

    dW(P) = E[ W(P) - W(SQ) ]

is the expected change in residents' welfare over the horizon, in $bn of present value, under the
declared model and assumptions. It is the **net social value** of P. The status quo scores zero by
construction and is a decision alternative like any other: an instrument is preferred to it only if
its expected net social value is higher.

Every instrument is also scored on things the team needs beside the estimand: its safety forecast
(incident rates, the probability of a major and of a catastrophic incident, expected harm), the
industry's gain or loss (a market metric and a possible constraint, never part of the net social
value), the news environment it generates, and the decision gap between how it looks in the first six
months and what it is worth over the horizon.

## 3. Common random numbers

Every alternative in a battery runs on one set of pre drawn random numbers: market shocks, policy
uncertainty shocks, idiosyncratic price shocks, incident draws, severity draws, catastrophe draws and
their common factor, audit draws and news noise. The difference between two alternatives on a path is
therefore the instrument's doing and not the dice, and every figure "against the status quo" is a
paired difference.

Each path has its own stream seeded by `(seed, path index)`. Three properties follow:

- a run of fewer paths is exactly the first paths of a larger one with the same seed, so a battery can
  grow by adding paths (section 10.4) and a re simulation on fewer paths can be paired with the main run
  path by path (section 12);
- paths are independent, so consecutive batches of a run are independent replications of a smaller run;
- another seed is another family of streams: an independent replication of the whole run
  (`tools/replicate.py`; a question can name its seed, "seed 11").

Common random numbers make a comparison precise inside the model. They say nothing about whether the
model's mechanisms hold in the AI industry (section 13).

## 4. The agents

### 4.1 Firms

Eight archetypes of the AI value chain by default (the Firm workshop can replace them):

<!-- generated:firms -->
| Firm | Sector | Revenue $bn | Margin | Growth | Capability | Safety | Reach | In scope | Mobility | Culture | Beta | Idio vol | PE |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Frontier Lab (closed weights) | `frontier_lab` | 15 | 15% | 45% | 1.2 | 0.5 | 0.7 | 90% | 0.4 | 0.55 | 1.4 | 10% | 45 |
| Frontier Lab (open weights) | `open_weights` | 4 | 5% | 50% | 1.05 | 0.4 | 0.6 | 90% | 0.6 | 0.45 | 1.5 | 12% | 60 |
| Hyperscaler cloud | `hyperscaler` | 120 | 30% | 18% | 1.1 | 0.6 | 0.9 | 40% | 0.2 | 0.6 | 1.1 | 7% | 28 |
| Chip designer | `chips` | 90 | 45% | 25% | 0.6 | 0.7 | 0.95 | 15% | 0.3 | 0.6 | 1.6 | 8% | 35 |
| Enterprise software | `enterprise_software` | 60 | 28% | 14% | 0.8 | 0.6 | 0.85 | 50% | 0.1 | 0.6 | 1 | 7% | 30 |
| Consumer AI platform | `consumer_ai` | 30 | 20% | 30% | 0.95 | 0.45 | 0.8 | 70% | 0.3 | 0.4 | 1.3 | 9% | 38 |
| Autonomy and robotics | `autonomy` | 8 | 8% | 40% | 0.85 | 0.5 | 0.4 | 80% | 0.3 | 0.5 | 1.5 | 11% | 50 |
| AI start up cohort | `startups` | 6 | -10% | 60% | 0.7 | 0.35 | 0.3 | 60% | 0.7 | 0.35 | 1.7 | 10% | 60 |
<!-- /generated:firms -->

Each month every firm chooses, from a grid, a **safety share of R&D** sigma in {0.02, 0.05, 0.10, 0.15,
0.20, 0.30}, an **offshore share** omega in {0, 0.3, 0.6, 0.9} capped by its mobility, and whether to
**comply** chi in {0, 1}, by maximising an expected payoff over a planning horizon of twelve months
(six and twenty four months are structural variants):

    U(sigma, omega, chi) = growth value - compliance cost - expected penalty - relocation cost
                           - offshore haircut - expected liability (or premium) - risk premium + culture term

    growth value       = growth_value_weight x R x revenue_capability_beta x dC x max(0, 1 - delay / plan)
    dC                 = plan x capability_growth x (1 - safety_substitution x sigma') x compute factor
                         (x (1 - moratorium_research_slowdown) for a firm in scope while a moratorium holds)
    sigma'             = max(sigma, the instrument's minimum safety share where the firm complies and is bound)
    compliance cost    = chi x bound share x (fixed + variable x R x scope share) x plan / 12
    expected penalty   = (1 - chi) x bound share x plan x audit_rate x e x fine rate x R x scope share x 1.5
    relocation cost    = relocation_cost x max(0, omega - O) x R
    offshore haircut   = offshore_revenue_haircut x omega x R x max(margin, 0.1) x plan / 12
    expected liability = liability multiplier x in scope x (1 - safe_harbour_shield x chi) x expected harm
    expected harm      = firm_optimism x plan x (sum_k lambda_k(S') x mean severity_k
                         + catastrophe_prior_monthly x 1{C_eff > catastrophe_capability} x exp(-eta_S S') x catastrophe_harm_bn)
    premium            = expected liability x (1 + insurance_loading)       (under an insurance mandate; no risk premium)
    risk premium       = firm_risk_aversion x 0.5 x expected liability      (otherwise)
    culture term       = culture x culture_weight x R x (S' - S)

with S' the safety level the firm would reach over the planning horizon under sigma' and lambda_k(S') its
incident rate at that level (section 4.3, before the effect of evaluations and transparency). The firm's
view of its incident rate is that rate times `firm_optimism`.

An instrument **binds** the share of a firm's activity that is in scope: all of it under a coordinated
instrument, the share not moved offshore under a domestic one. Scope is a sector test and a capability
threshold on released capability. Liability follows the harm, not the office: a firm cannot escape
liability for harm its systems cause at home by moving.

### 4.2 Dynamics

- The offshore share moves towards the chosen share by at most 0.1 a month; moving costs
  `relocation_cost x share moved x R` once.
- Safety level `S' = S + safety_learning x sigma / (sigma + 0.1) x (1 - S) - safety_decay x S`
  (saturating learning, erosion without investment), clipped to [0.02, 0.98].
- Capability `C' = C x exp(g)`, `g = capability_growth x (1 - safety_substitution x sigma) x compute factor
  + diffusion`, reduced by `moratorium_research_slowdown` while a moratorium holds for a firm in scope;
  published weights diffuse `open_weights_diffusion x 0.1` of the gap to the open developer into other
  model sectors, unless publishing is restricted.
- Released capability `C_eff` lags capability by the approval delay and is frozen by a moratorium.
- Reach closes at `reach_speed` on a ceiling `(1 - exp(-reach_ceiling_k x C_eff)) x sqrt(trust)`, slowed
  by tier friction; a frictionless, full trust reference reach is tracked so revenue can be expressed
  relative to it.
- Revenue grows at a rate that fades from the archetype's starting growth to `long_run_growth` over
  `growth_fade_months`, plus `revenue_capability_beta x (dlog C_eff - g_ref)`, minus the offshore haircut;
  chips and cloud ride the model developers' capability growth through `chip_demand_coupling`; export
  controls and an open weights restriction take their declared growth losses; monthly growth is clipped
  to [-20%, +30%]; revenue is then scaled by `(reach / reference reach)^revenue_reach_beta`.
- Earnings are operating profit (`R / 12 x margin`) less compliance, fines, liability paid, premiums and
  relocation cost.

### 4.3 Hazard

Each month, each firm, each category k in {misuse, accident, systemic} has an incident with probability
`p_k = 1 - exp(-lambda_k)`, where

    lambda_k = base_k x C_eff^eta_C x exp(-eta_S S) x D^eta_D x (1 + O x offshore_laxity)
               x (1 - catch rate x chi x in scope x unsafe_release_share)

reduced by the instrument's transparency for misuse (in full) and systemic incidents (by half), and
multiplied by `open_weights_misuse_multiplier` for misuse at a developer that publishes weights (not while
publishing is restricted). The
harm of an incident is lognormal, `median_k x exp(severity_sigma x z)`, with mean
`median_k x exp(severity_sigma^2 / 2)`. An incident is **major** when its own harm is at or above
`major_incident_bn`: every incident is classified on its own harm, so two minor incidents at one firm in
one month are two minor incidents and never one major one. Compliance theatre (a red team strategy)
halves the evaluation effect.

**Catastrophes.** Above `catastrophe_capability` firm f has a catastrophic incident in a month with
probability

    p_f = catastrophe_prior_monthly x exp(-eta_S S) x (1 + O x offshore_laxity) x (1 - 0.5 x catch rate x chi x in scope)

and harm `catastrophe_harm_bn x exp(catastrophe_severity_sigma x z_f)`. Catastrophes are not independent
across firms: shared models, components and vulnerabilities enter through one common factor. With
`rho = catastrophe_correlation` and a standard normal factor `z` drawn once a month per path, firm f
fails when

    u_f < Phi( (Phi^-1(p_f) - sqrt(rho) z) / sqrt(1 - rho) ),        u_f uniform, independent across firms

a one factor Gaussian copula. Each firm's own probability stays `p_f` whatever `rho` is; joint failures
become more likely than independence would make them, and the probability that at least one firm fails
in the month, given the state,

    P_any = 1 - E_z[ prod_f (1 - Phi( (Phi^-1(p_f) - sqrt(rho) z) / sqrt(1 - rho) )) ]

is computed by Gauss Hermite quadrature (24 nodes; tested against brute force simulation). `rho = 0`
gives independent catastrophes; 0.8 is a structural variant.

### 4.4 Liability and insurance

Liability due on a firm is `liability multiplier x in scope x (1 - safe_harbour_shield x chi) x harm`
of the harm its systems cause. Without an insurance mandate the firm pays it. Under a mandate the firm
pays a premium, its own expected liability loaded by `insurance_loading`, and the insurer pays the
claims.

### 4.5 Regulator, public and press

- Enforcement intensity follows public pressure within capacity:
  `e' = e + enforcement_response x (capacity x (0.4 + 0.6 P) - e)`; a firm in scope is audited with
  probability `audit_rate x e` and fined `fine rate x in scope revenue x bound share` if non compliant.
- Public trust `T' = T + trust_recovery x (1 - T) - trust_harm_sensitivity x log(1 + harm in the month)`,
  clipped to [0.3, 1]; trust caps deployment reach and scales the realised adoption benefits.
- News pressure `P' = news_memory x P + (1 - news_memory) x (1 - exp(-x))`, where x weighs the month's
  minor incidents, major incidents, catastrophes, enforcement actions and relocations (reporting mandates
  raise incident salience by `news_reporting_boost`); tone is the balance of positive (release
  milestones) against negative salience. Four media agents (WIRE, TECH, CIVIC, CAPITOL) turn the
  representative path's events into headlines from templates; every figure in a headline is the event's own.

### 4.6 Market

A firm's fundamental value is a revenue multiple plus an earnings multiple on forward earnings with a
smooth floor,

    V = ps x R + pe x k x log(1 + exp(FE / k)),     k = 0.05 R,     FE = 12 x run rate x (1 + g)

where the run rate is operating profit less compliance, premiums and expected liability (one offs
excluded) and g the trailing twelve month revenue growth (the archetype's starting growth in the first
eleven months). The price is

    price_t = 100 x V_t / V_pre x exp(xi_t)

    xi' = sentiment_persistence x xi + beta x market_vol x z_market + 0.01 x exposure x z_policy
          - news_price_impact x P x (0.3 + exposure) + own incident jump + sector contagion
          + anticipation (month 0 only) + idiosyncratic noise

`V_pre` is the valuation of the firm as it stands **before any instrument is announced**, the same for
every alternative of the battery. An instrument in force from the first month therefore shows its effect
on fundamentals in the first month's price, instead of disappearing into a base computed after it. The
anticipation term applies only to an instrument announced at the start and in force later: the market
then prices costs the fundamentals do not carry yet, `-announcement_impact x 0.5 x (expected compliance
cost + 0.3 x liability multiplier) / max(annual earnings, 0.05 R)`, no lower than -25%. Fines, realised
liability and relocation costs enter as jumps. The market value at the horizon is
`V_pre x price_H / 100`.

## 5. The instrument library

<!-- generated:instruments -->
| Name | Label | In force from month | What it does |
|---|---|---|---|
| `baseline` | Status quo (voluntary commitments) | 0 | enforcement capacity 0.1; domestic scope |
| `transparency_disclosure` | Transparency and disclosure | 0 | provenance and disclosure; compliance $0.01bn fixed plus 0.2% of revenue; enforcement capacity 0.3, fines 1% of revenue; domestic scope |
| `compute_threshold_reporting` | Compute threshold reporting | 3 | above capability 1.0; evaluations catch 15% of unsafe releases; compliance $0.03bn fixed plus 0.5% of revenue; enforcement capacity 0.4, fines 2% of revenue; domestic scope |
| `mandatory_third_party_evals` | Mandatory third party evaluation | 6 | above capability 0.8; safety spend at least 8% of R&D; evaluations catch 45% of unsafe releases; 2 month approval delay; compliance $0.08bn fixed plus 1.0% of revenue; enforcement capacity 0.5, fines 6% of revenue; domestic scope |
| `risk_tiering` | Risk tiering (EU style) | 12 | safety spend at least 5% of R&D; 1 month approval delay; provenance and disclosure; risk tier conformity for deployers; compliance $0.05bn fixed plus 3.0% of revenue; enforcement capacity 0.6, fines 7% of revenue; domestic scope |
| `frontier_licensing` | Frontier licensing | 6 | above capability 1.0; safety spend at least 25% of R&D; evaluations catch 60% of unsafe releases; 4 month approval delay; compliance $0.15bn fixed plus 2.0% of revenue; enforcement capacity 0.7, fines 10% of revenue; domestic scope |
| `coordinated_licensing` | Coordinated frontier licensing | 12 | above capability 1.0; safety spend at least 25% of R&D; evaluations catch 60% of unsafe releases; 4 month approval delay; compliance $0.15bn fixed plus 2.0% of revenue; enforcement capacity 0.7, fines 10% of revenue; coordinated across jurisdictions |
| `strict_liability` | Strict liability | 6 | liability for 80% of harm; compliance $0.02bn fixed plus 0.5% of revenue; enforcement capacity 0.3; domestic scope |
| `liability_with_safe_harbour` | Liability with a safe harbour | 6 | safety spend at least 12% of R&D; evaluations catch 35% of unsafe releases; liability for 80% of harm with a safe harbour; compliance $0.08bn fixed plus 1.2% of revenue; enforcement capacity 0.4, fines 3% of revenue; domestic scope |
| `moratorium` | Six month moratorium above the threshold | 1 | above capability 1.1; evaluations catch 15% of unsafe releases; 6 month moratorium; compliance $0.03bn fixed plus 0.0% of revenue; enforcement capacity 0.5, fines 5% of revenue; domestic scope |
| `export_controls` | Compute export controls | 0 | above capability 1.0; compute export controls; compliance $0.02bn fixed plus 0.0% of revenue; enforcement capacity 0.4, fines 3% of revenue; domestic scope |
| `open_weights_restriction` | Open weights restriction | 0 | above capability 0.9; provenance and disclosure; no open weights above the threshold; compliance $0.02bn fixed plus 0.0% of revenue; enforcement capacity 0.4, fines 4% of revenue; domestic scope |
| `sandbox_light_touch` | Sandbox and light touch | 0 | provenance and disclosure; compliance $0.00bn fixed plus 0.4% of revenue; enforcement capacity 0.3, fines 1% of revenue; domestic scope |
| `eu_style_package` | EU style package | 12 | safety spend at least 10% of R&D; evaluations catch 45% of unsafe releases; 2 month approval delay; provenance and disclosure; risk tier conformity for deployers; compliance $0.10bn fixed plus 3.0% of revenue; enforcement capacity 0.7, fines 7% of revenue; domestic scope |
| `licensing_plus_liability` | Licensing plus liability | 6 | above capability 1.0; safety spend at least 25% of R&D; evaluations catch 60% of unsafe releases; 4 month approval delay; liability for 80% of harm with a safe harbour; compliance $0.15bn fixed plus 2.0% of revenue; enforcement capacity 0.7, fines 10% of revenue; domestic scope |

The default battery is `baseline`, `transparency_disclosure`, `compute_threshold_reporting`, `mandatory_third_party_evals`, `risk_tiering`, `frontier_licensing`, `strict_liability`, `liability_with_safe_harbour`, `moratorium`. An instrument is a bounded JSON document; bounds: `phase_in` 0 to 36, `sunset` 0 to 120, `capability_threshold` 0 to 3, `fixed_cost` 0 to 2, `variable_cost` 0 to 0.1, `min_safety_share` 0 to 0.5, `eval_catch` 0 to 0.9, `release_delay` 0 to 12, `moratorium_months` 0 to 24, `liability_multiplier` 0 to 1.5, `transparency` 0 to 0.3, `enforcement_capacity` 0 to 1, `fine_rate` 0 to 0.2, `export_controls` 0 to 1, `tier_friction` 0 to 0.3. Custom instruments are validated, clamped to the bounds (clamping is reported), hashed and carried in the battery hash and the ledger.
<!-- /generated:instruments -->

## 6. What a path records

Beside every realised quantity (revenue, earnings, compliance, fines, liability, premiums, claims,
relocation, the incidents drawn and their harm, catastrophes, prices, enforcement, pressure, trust, the
service index) the engine records what was **expected** of each month given the state the path had
reached:

    expected harm in the month = sum_f sum_k p_k x mean severity_k + sum_f p_f x mean catastrophic harm
    P_any                      = the probability of at least one catastrophe in the month (section 4.3)
    expected liability         = the liability share x expected harm

These conditional expectations are what the expected value estimators use (section 8). Per path results
are reduced as soon as they are simulated to what the accounting needs (monthly flows summed over
firms, the state series, counts, and per firm values for the market panel) and stored in `paths.npz` in
single precision; the critic and the second implementation recompute from that file.

## 7. Welfare accounting

### 7.1 Standing and conventions

- **Standing: residents.** Real resources used up in the jurisdiction count in full; income counts for
  residents only (the resident share of the AI firms' operating profit).
- **Transfers are excluded.** Fines, liability payments, insurance claims and the part of premiums that
  covers them move money between parties; they are reported and not counted, whoever pays. What non
  resident owners finance of the firms' payments is a memorandum item (`nonresident_payments`).
- **One unit.** $bn of present value over the horizon.
- **One timing convention.** A monthly flow is discounted at the end of its month,
  `d_t = (1 + r)^(-t/12)` for month t = 1, ..., H with r the `discount_rate`; a value at the horizon (the
  market value) by `d_H = (1 + r)^(-H/12)`, the same date as the last flow.
- **One counterfactual.** Every component is the alternative's path minus the status quo path that
  shares its random numbers.

### 7.2 Components

<!-- generated:components -->
| Component | Sign in the net | Definition (per path, present value, $bn) |
|---|---|---|
| `harm_avoided` | + | `harm_valuation_multiplier x sum_t d_t (h_SQ,t - h_P,t)`, with `h` the harm expected in the month given the state the path has reached (section 8) |
| `cs_change` | + | `(consumer_surplus_base_bn / 12) x sum_t d_t (Q_P,t^e - Q_SQ,t^e)`, `e = cs_elasticity`, `Q` the AI service index (released capability times reach, revenue weighted, 1 at the start) |
| `productivity_change` | + | `(1 - benefit_overlap_share) x (productivity_base_bn / 12) x sum_t d_t (Q_P,t^e' T_P,t^tau - Q_SQ,t^e' T_SQ,t^tau)`, `e' = productivity_elasticity`, `tau = trust_elasticity`, `T` public trust |
| `producer_surplus_change` | + | `domestic_ownership_share x sum_t d_t (operating profit_P,t - operating profit_SQ,t)`, operating profit before compliance, fines, liability, premiums and relocation |
| `compliance_cost` | - | `compliance_deadweight_share x sum_t d_t (compliance_P,t - compliance_SQ,t)` |
| `enforcement_cost` | - | `(enforcement_cost_bn / 12) x sum_t d_t (e_P,t - e_SQ,t)`, `e` the enforcement intensity |
| `leakage` | - | `leakage_value_share x sum_t d_t (offshore revenue_P,t - offshore revenue_SQ,t)` |
| `relocation_cost` | - | `sum_t d_t (relocation_P,t - relocation_SQ,t)` |
| `labour_change` | - | `labour_adjustment_bn x sum_t d_t (max(Q_P,t - Q_P,t-1, 0) - max(Q_SQ,t - Q_SQ,t-1, 0))`, `Q_0 = 1` |
| `insurance_admin_cost` | - | `insurance_admin_share x loading / (1 + loading) x sum_t d_t (premium_P,t - premium_SQ,t)`, `loading = insurance_loading` |
<!-- /generated:components -->

    net social value = harm_avoided + cs_change + productivity_change + producer_surplus_change
                       - compliance_cost - enforcement_cost - leakage - relocation_cost - labour_change
                       - insurance_admin_cost

### 7.3 The accounting map: one line for every simulated flow

<!-- generated:account_map -->
| Simulated flow | Enters | Kind | Whose | Note |
|---|---|---|---|---|
| `harm_exp` | harm_avoided | real | the public at risk | expected monetised harm given the state reached, scaled by the harm valuation multiplier; direct damages only |
| `harm` | outcome spread of harm_avoided | real | the public at risk | the harm actually drawn; the same expectation as harm_exp; used for percentiles, never added to it |
| `service` | cs_change | real | consumers | households' non market surplus from AI services, a power of the service index |
| `service, trust` | productivity_change | real | sectors that adopt AI | value added uplift in adopting sectors net of their payments to AI providers; excludes the AI sector's own profit; scaled by one minus the declared overlap with the other two benefit components (benefit_overlap_share) |
| `op_earnings` | producer_surplus_change | real | resident owners of AI firms | operating profit before compliance, fines, liability, premiums and relocation; resident share only |
| `compliance` | compliance_cost | real (resource share) | firms | the deadweight share is a resource cost; the rest is rent to compliance providers, a transfer |
| `enforcement` | enforcement_cost | real | taxpayers | public budget per unit of enforcement intensity |
| `offshore_revenue` | leakage | real | domestic workers and tax base | residents' rents on activity that moved; the firms' own profit loss from moving is in op_earnings |
| `relocation` | relocation_cost | real | firms | one off resource cost of moving |
| `service (first difference)` | labour_change | real | workers | adjustment cost of adoption |
| `premium` | insurance_admin_cost (loading x resource share); the rest is a transfer | real and transfer | firms to insurers | expected claims and the insurer's margin are transfers; underwriting and administration are resources |
| `fines` | transfer | transfer | firms to taxpayers | excluded from the net social value |
| `liability` | transfer | transfer | firms to victims | excluded; the harm itself is in harm_avoided |
| `claims` | transfer | transfer | firms or insurers to victims | what victims are paid, by whoever pays |
| `earnings` | incidence table and market value only | income | owners | operating profit less every payment above; its components are already counted line by line |
| `cap_end` | industry value change only | valuation | shareholders | market value at the horizon; a market metric and a constraint, never part of the net social value |
<!-- /generated:account_map -->

**Overlap between the benefit components.** Consumer surplus, the output uplift and producer surplus
could overlap: a productivity gain may already be in a provider's profit or in a consumer's benefit.
The Lab separates them by definition. Consumer surplus is households' non market surplus from AI
services. The output uplift is value added in the sectors that adopt AI, net of what they pay AI
providers, so it excludes the AI sector's own profit. Producer surplus is the AI sector's operating
profit before compliance, fines, liability, premiums and relocation, each of which is counted once
elsewhere or is a transfer. That separation is a declaration, not a measurement: the two bases are
declared annual values, and nothing in the simulation derives one from the other. An analyst who judges
that part of the output uplift is already in the other two components removes it with
`benefit_overlap_share` (0 by default; the screen and the joint draw move it to 0.5).

**Offshore leakage** is residents' rents (wage premia, tax base) on activity that moved; the firms' own
profit loss from moving is in operating profit and is not counted again. **Compliance** spend is a
resource cost for its deadweight share and a rent to compliance providers, a transfer, for the rest.
**The insurance loading** is a resource cost (underwriting, administration) for `insurance_admin_share`
of it and the insurer's margin, a transfer, for the rest; expected claims in the premium are a transfer.
**Relocation** is a one off resource cost.

### 7.4 Gross cost, gross benefit, incidence

- **Gross social cost** is the sum of the expected component changes that are costs: every cost
  component whose expected change is positive and every benefit component whose expected change is
  negative. **Gross benefit** is the mirror image. Both are non negative, a saving is never netted
  against a cost, and `gross benefit - gross cost = net social value`. The net economic cost,
  `harm avoided - net social value`, is reported beside it.
- **Incidence.** The distribution table follows the money as well as the real effects: the public at
  risk (harm not suffered and compensation received), consumers, the sectors that adopt AI, workers,
  resident owners of AI firms (earnings after every payment), taxpayers (fines less enforcement),
  insurers, compliance providers and the domestic tax base. It sums to the net social value plus
  `nonresident_payments`, an identity the critic checks.

### 7.5 Industry value

The industry's value change is the present value of the change in earnings over the horizon plus the
discounted change in market value at its end, per firm, against the status quo on the same path:

    industry value change = sum_t d_t (earnings_P,t - earnings_SQ,t) + d_H x (market value_P,H - market value_SQ,H)

It is a market metric and a possible constraint. It is never part of the net social value.

## 8. Estimators

**Expected values use conditional expectations (conditional Monte Carlo).** The expected value of harm
avoided is estimated from the harm expected in each month given the state the path has reached, not
from the harm drawn. By the law of iterated expectations the two have the same expectation,
`E[harm_t] = E[ E[harm_t | state_t] ]`, and the conditional one has a small fraction of the variance,
because it does not depend on whether a rare, very large loss happened to be drawn. The same is done
for the liability a firm pays where it is not insured.

**The probability of a catastrophe over the horizon** is estimated per path by

    sum over months t of  1{no catastrophe before t on this path} x P_any,t

Since `P(first catastrophe in month t) = E[ 1{none before t} x P(one in month t | state) ]`, the sum has
expectation `P(at least one catastrophe)`. A path contributes the hazard it accumulates up to its first
catastrophe instead of a 0 or a 1. The raw count of paths on which a catastrophe was drawn is reported
beside the estimate, with its Wilson interval.

Both estimators are tested for unbiasedness against the plain frequencies on 2,400 paths, and for their
variance (below 2% of the frequency's), in `tests/test_stats.py`.

**What is still estimated from the draws.** The consequences of the incidents that were drawn (lost
trust, slower adoption, market reactions, liability under no mandate before its expectation is taken)
feed back into the path and are not integrated out. Consumer surplus and the output uplift therefore
carry the variance of the incidents drawn, including the rare ones; that variance is what the
confidence intervals below report and what the sampling plan works on.

**Simulated outcomes** (percentiles, the share of paths above zero, the median, the tail share) use
the harm as drawn: they describe how different one path can be from another. When the expected value
sits above the 90th percentile of the outcomes, the panels say so: the expectation is carried by the few
paths on which a catastrophe is averted.

## 9. Uncertainty: four kinds, never merged

| Kind | What it is | How it is reported |
|---|---|---|
| Outcome spread (aleatoric) | which incidents and market shocks occur on a path | the 10th and 90th percentiles of the simulated outcomes, the share above zero, the median |
| Monte Carlo error | how precisely a finite number of paths estimates an expectation | a standard error and a 95% confidence interval for every expected value, paired for every difference; convergence tables; batches; replication across seeds |
| Parameter uncertainty | where the declared assumptions could plausibly lie | the screen of every assumption, the joint draw of all of them, the variance decomposition (section 12) |
| Structural uncertainty | whether the mechanisms are the right ones | the battery under alternative model structures and under strategic gaming (section 12); the mechanism register (section 13) |

**Bootstrap.** Paths are resampled with replacement (1,000 resamples in the full profile). Each path
carries every alternative on the same random numbers, so resampling paths keeps the pairing, and one
set of resamples is reused for every quantity of a run: the resampled values of two quantities are then
values on the same resampled battery, which is what feasibility inside each resample, paired
differences and the ranking need. Intervals are percentile intervals at 95%.

**Paired differences.** The difference in expected net social value between the preferred alternative
and each other one carries its standard error, its 95% interval and a simultaneous 95% interval over
all the comparisons (the maximum over alternatives of the studentised bootstrap deviation sets the
critical value). The feasible alternatives whose simultaneous interval includes zero form the
preferred alternative's **confidence set**: the paths cannot tell them apart from it.

**Ranking stability.** The share of resamples in which an alternative is the best feasible one, with
feasibility re assessed in each resample. It is conditional on the model and its assumptions. It is not
the probability that the alternative is best in the world, and no panel calls it that.

**Probabilities from counts** carry Wilson intervals: no catastrophe in 60 paths is an interval from 0
to about 6%, not a probability of zero.

**Convergence.** The running estimate on the first eighth, quarter and half of the paths and on all of
them (what a smaller run on the same seed reports), with the decision at each; the decision in each of
several independent batches of the run's paths.

**Measured coverage.** `tools/replicate.py` repeats a run on independent seeds and reports the spread
of each estimate across seeds beside the standard error a single run reports, and how often a run's 95%
interval contains the mean of the other seeds. `docs/replication.md` holds the result for the default
question. The intervals are not adjusted for the sequential looks of the sampling plan (at most four in
the default profiles).

## 10. The decision rule

### 10.1 Alternatives and feasibility

The alternatives are every instrument of the battery and the status quo. A question may set
constraints: a limit on the industry's loss, a budget for gross social cost, a ceiling on the
probability of a major or of a catastrophic incident, a minimum harm reduction, a consumer surplus
floor. A condition in the question that the Lab cannot test is reported before Gate 1 as not applied;
it is never silently dropped.

An alternative is **feasible** when the expected value of each constrained metric is within its limit.
That expected value is an estimate, so every alternative also carries, for each constraint and for all
of them together, the share of bootstrap resamples in which it is within the limits (`p_feasible`) and
the interval of the constrained metric. The two percentage constraints are measured against the status
quo's expected harm and consumer surplus, which are held at their estimates in the resamples.

### 10.2 The preferred alternative

    preferred = the feasible alternative with the highest expected net social value

A tie between the status quo and an instrument goes to the status quo. If no instrument beats it, the
answer is that no tested instrument improves on the status quo, and the best instrument is reported
separately (`best_intervention`). If nothing is feasible, there is no preferred alternative. The best
alternative without the constraints is reported beside these.

**The conservative rule.** The preferred alternative among those within the constraints in at least
90% of resamples is reported beside the preferred alternative under the expected value rule. When they
differ, the briefing says so in its first paragraph.

### 10.3 Ranks and the decision gap

Equal scores share a rank (competition ranks: 1, 1, 3), so the order two identical instruments are
listed in cannot give them different ranks. The **headline score** is the value weighted price reaction
against the status quo over the first six months plus a tenth of the early press tone difference. The
**decision gap** is `(1 - tau) / 2` with tau Kendall's tau b between the headline ranking and the social
ranking, so tied scores neither create nor hide a gap; P(inversion) is the share of resamples with
tau below zero.

### 10.4 The sampling plan

A battery declares the paths it starts on, a ceiling, and precision targets; all three are part of the
battery hash approved at Gate 1. After each look the paths double, on the same random streams, until
every target is met or the ceiling is reached:

- the preferred alternative is resolved against every other feasible one: the 95% interval of their
  paired difference excludes zero, or its half width is within the target (the two are then equivalent
  to within it);
- the half width of the interval of the catastrophe probability, for the preferred alternative and the
  status quo, is within the target;
- no alternative that is the preferred one, or would beat it, has a feasibility the resamples split on
  (between 10% and 90%).

What is still short of its target at the ceiling is listed in the briefing, the ledger and the panels.

<!-- generated:profiles -->
| Profile | Paths (start to ceiling) | Horizon | Resolve the decision to within | Catastrophe probability to within | Bootstrap | Screen paths | Joint draws x paths | Variance: inputs, base, paths | Variant paths | Red team paths | Batches |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `full` | 480 to 3,840 | 60 months | $2.5bn | 1% | 1,000 | 32 | 256 x 8 | 8, 256, 4 | 240 | 240 | 8 |
| `light` | 240 to 960 | 60 months | $5bn | 2% | 1,000 | 12 | 128 x 6 | 6, 128, 3 | 96 | 120 | 4 |
| `demo` | 120 to 480 | 36 months | $5bn | 3% | 500 | 4 | 64 x 4 | 5, 64, 2 | 40 | 60 | 4 |
<!-- /generated:profiles -->

## 11. Assumptions

Every value judgement and behavioural parameter is declared, bounded, given a plausible range, hashed
into the battery at Gate 1 and cited in the briefing. Two intervals attach to an assumption and must
not be confused: the **accepted bounds** are what the Lab will take from a user, a validation limit;
the **plausible range** is where the value could plausibly lie, a declared judgement and a prior, not
an estimate, and it is what the sensitivity analysis moves the assumption over.

<!-- generated:assumptions -->
| Assumption | Key | Value | Plausible range | Accepted bounds | Unit | Meaning | Enters |
|---|---|---|---|---|---|---|---|
| Social discount rate | `discount_rate` | 0.03 | 0.01 to 0.07 | 0 to 0.1 | a year | social discount rate applied to every monthly flow | the accounting only |
| Harm valuation multiplier | `harm_valuation_multiplier` | 1 | 0.5 to 2 | 0.25 to 4 | multiple | scales the monetised harm of incidents; 1.0 takes the engine's damages at face value | the accounting only |
| Consumer surplus base | `consumer_surplus_base_bn` | 250 | 150 to 600 | 50 to 1,500 | $bn a year | annual consumer surplus from AI services at the starting level of capability and reach | the accounting only |
| Consumer surplus elasticity | `cs_elasticity` | 0.6 | 0.3 to 1 | 0.1 to 1.5 | elasticity | proportional change in consumer surplus per proportional change in the AI service index | the accounting only |
| Output uplift base | `productivity_base_bn` | 400 | 200 to 800 | 50 to 2,000 | $bn a year | annual output uplift attributable to AI adoption at the starting service index | the accounting only |
| Output uplift elasticity | `productivity_elasticity` | 0.8 | 0.5 to 1.1 | 0.1 to 1.5 | elasticity | proportional change in the output uplift per proportional change in the service index | the accounting only |
| Trust elasticity of adoption benefits | `trust_elasticity` | 0.5 | 0.2 to 1 | 0 to 1.5 | elasticity | proportional change in realised adoption benefits per proportional change in public trust | the accounting only |
| Overlap of the output uplift with other benefits | `benefit_overlap_share` | 0 | 0 to 0.5 | 0 to 1 | share | share of the output uplift already counted as consumer surplus or as the AI firms' own profit, removed from the output uplift; 0 takes the three benefit components as defined, without overlap | the accounting only |
| Resource share of compliance spend | `compliance_deadweight_share` | 0.7 | 0.4 to 1 | 0.3 to 1 | share | share of compliance spend that is a real resource cost rather than a transfer | the accounting only |
| Enforcement cost | `enforcement_cost_bn` | 0.4 | 0.2 to 0.8 | 0.05 to 2 | $bn a year per unit of capacity | public budget consumed by one unit of enforcement capacity | the accounting only |
| Value lost per dollar moved offshore | `leakage_value_share` | 0.35 | 0.1 to 0.7 | 0 to 1 | share | domestic value added lost per dollar of revenue whose activity moves offshore | the accounting only |
| Labour adjustment cost | `labour_adjustment_bn` | 2 | 0 to 5 | 0 to 10 | $bn per index point | short run adjustment cost per point of growth in the AI service index (displacement, retraining) | the accounting only |
| Resident ownership share | `domestic_ownership_share` | 0.6 | 0.3 to 0.9 | 0 to 1 | share | share of the firms' operating profit that accrues to residents and counts in national welfare | the accounting only |
| Resource share of the insurance loading | `insurance_admin_share` | 0.5 | 0.25 to 0.75 | 0 to 1 | share | share of the insurance loading that is a real resource cost (underwriting, administration) rather than a transfer to insurers | the accounting only |
| Misuse incident rate | `hazard_base_misuse` | 0.08 | 0.05 to 0.13 | 0.01 to 0.3 | a month per firm | monthly rate of a reportable misuse incident for a firm at capability 1, full reach and no safety practice | the simulation |
| Accident rate | `hazard_base_accident` | 0.05 | 0.03 to 0.08 | 0.01 to 0.3 | a month per firm | the same for accidents and failures | the simulation |
| Systemic incident rate | `hazard_base_systemic` | 0.02 | 0.01 to 0.04 | 0.002 to 0.15 | a month per firm | the same for systemic incidents (markets, infrastructure, information) | the simulation |
| Capability elasticity of incidents | `hazard_capability_elasticity` | 1.3 | 0.9 to 1.8 | 0.5 to 2.5 | elasticity | incident rate scales with capability to this power | the simulation |
| Safety elasticity of incidents | `hazard_safety_elasticity` | 1.8 | 1.4 to 3 | 0.5 to 4 | per unit of safety level | incident rate falls as exp(-elasticity x safety level) | the simulation |
| Reach elasticity of incidents | `hazard_reach_elasticity` | 1 | 0.7 to 1.4 | 0.3 to 2 | elasticity | incident rate scales with deployment reach to this power | the simulation |
| Offshore laxity | `offshore_laxity` | 0.6 | 0.2 to 1.2 | 0 to 2 | multiple | extra incident rate on activity moved offshore, relative to home | the simulation |
| Median harm of a misuse incident | `severity_misuse_median_bn` | 0.15 | 0.08 to 0.3 | 0.01 to 2 | $bn | median monetised harm of a misuse incident | the simulation |
| Median harm of an accident | `severity_accident_median_bn` | 0.3 | 0.15 to 0.6 | 0.02 to 3 | $bn | median monetised harm of an accident | the simulation |
| Median harm of a systemic incident | `severity_systemic_median_bn` | 1 | 0.5 to 2 | 0.1 to 10 | $bn | median monetised harm of a systemic incident | the simulation |
| Dispersion of incident harm | `severity_sigma` | 1.1 | 0.8 to 1.4 | 0.5 to 2 | log scale | lognormal dispersion of incident harm (heavy tail) | the simulation |
| Major incident threshold | `major_incident_bn` | 1 | 0.5 to 2 | 0.2 to 10 | $bn | harm above which an incident counts as major | the simulation |
| Monthly catastrophe probability | `catastrophe_prior_monthly` | 0.002 | 0.0005 to 0.005 | 0 to 0.02 | a month per firm | monthly probability of a catastrophic incident for a firm above critical capability with no safety practice | the simulation |
| Critical capability | `catastrophe_capability` | 1.6 | 1.3 to 2 | 1 to 3 | capability index | capability above which the catastrophic tail is live | the simulation |
| Median harm of a catastrophe | `catastrophe_harm_bn` | 400 | 150 to 1,200 | 20 to 3,000 | $bn | median monetised harm of a catastrophic incident | the simulation |
| Share of incidents an evaluation could catch | `unsafe_release_share` | 0.35 | 0.2 to 0.5 | 0.05 to 0.8 | share | share of the incident rate attributable to releases an evaluation could catch | the simulation |
| Dispersion of catastrophic harm | `catastrophe_severity_sigma` | 0.5 | 0.25 to 0.9 | 0 to 1.5 | log scale | lognormal dispersion of catastrophic harm around its median | the simulation |
| Correlation of catastrophes across firms | `catastrophe_correlation` | 0.3 | 0 to 0.6 | 0 to 0.9 | correlation | correlation of catastrophic failures across firms within a month (one factor Gaussian copula): shared models, components and vulnerabilities; 0 makes the firms' catastrophes independent given the state | the simulation |
| Misuse multiplier for open weights | `open_weights_misuse_multiplier` | 1.3 | 1.1 to 1.8 | 1 to 3 | multiple | misuse rate of a developer that publishes weights, relative to one that does not | the simulation |
| Capability growth | `capability_growth` | 0.023 | 0.015 to 0.035 | 0.005 to 0.06 | a month | monthly log growth of the capability index when all R&D goes to capability (a doubling in about 30 months) | the simulation |
| Safety learning rate | `safety_learning` | 0.08 | 0.05 to 0.12 | 0.02 to 0.3 | a month | monthly gain in safety practice at saturation; the gain is a x share/(share + 0.1), diminishing in the share | the simulation |
| Growth fade time | `growth_fade_months` | 30 | 18 to 48 | 6 to 120 | months | time constant over which a firm's growth fades towards the long run rate | the simulation |
| Safety spend that displaces capability R&D | `safety_substitution` | 0.6 | 0.3 to 1 | 0 to 1 | share | share of safety spend that displaces capability R&D (the rest is additional budget or spills over) | the simulation |
| Chip growth lost to export controls | `export_control_chip_loss` | 0.1 | 0.05 to 0.2 | 0 to 0.4 | a year | annual revenue growth lost by the chip sector under full export controls | the simulation |
| Long run growth | `long_run_growth` | 0.06 | 0.03 to 0.1 | 0 to 0.2 | a year | the growth rate firms fade towards | the simulation |
| Safety decay | `safety_decay` | 0.02 | 0.01 to 0.04 | 0 to 0.08 | a month | monthly erosion of safety practice without investment | the simulation |
| Revenue response to capability | `revenue_capability_beta` | 0.5 | 0.3 to 0.8 | 0.1 to 1.2 | elasticity | revenue growth per unit of log capability growth | the simulation |
| Revenue response to reach | `revenue_reach_beta` | 0.8 | 0.5 to 1.2 | 0.1 to 2 | elasticity | revenue relative to the frictionless, full trust reach path, to this power | the simulation |
| Reach adjustment speed | `reach_speed` | 0.08 | 0.05 to 0.12 | 0.02 to 0.3 | a month | speed at which reach closes on its capability and trust determined ceiling | the simulation |
| Weight firms put on growth | `growth_value_weight` | 3 | 1.5 to 5 | 0.5 to 8 | years of revenue | how a firm values a year of extra growth against a year of cost | the simulation |
| Relocation cost | `relocation_cost` | 0.08 | 0.04 to 0.16 | 0 to 0.5 | share of moved revenue | one off cost of moving a unit of activity offshore | the simulation |
| Revenue lost offshore | `offshore_revenue_haircut` | 0.12 | 0.06 to 0.24 | 0 to 0.5 | share | revenue lost per unit of activity offshore (talent, customers, latency) | the simulation |
| Firm risk aversion | `firm_risk_aversion` | 0.6 | 0.2 to 1.2 | 0 to 2 | multiple | weight on the variance of expected liability in the firm's choice | the simulation |
| Firm optimism about incidents | `firm_optimism` | 0.7 | 0.5 to 0.9 | 0.3 to 1 | multiple | the share of its true incident rate a firm believes when it plans | the simulation |
| Audit rate | `audit_rate` | 0.5 | 0.3 to 0.8 | 0.05 to 1 | a month at full capacity | probability a firm in scope is audited in a month at capacity 1 | the simulation |
| Insurance loading | `insurance_loading` | 0.25 | 0.1 to 0.5 | 0 to 1 | share | premium above expected liability charged by insurers under a mandate | the simulation |
| Safe harbour shield | `safe_harbour_shield` | 0.7 | 0.5 to 0.9 | 0 to 1 | share | share of liability a compliant firm avoids under a safe harbour | the simulation |
| Research slowdown under a moratorium | `moratorium_research_slowdown` | 0.5 | 0.3 to 0.7 | 0 to 1 | share | share of capability growth lost by a firm in scope while a moratorium holds | the simulation |
| Weight of safety culture | `culture_weight` | 0.6 | 0.3 to 1.2 | 0 to 2 | $bn per unit of revenue | value a firm places on a unit gain in safety practice per unit of revenue, multiplied by its culture score | the simulation |
| Reach ceiling saturation | `reach_ceiling_k` | 1.5 | 1 to 2.2 | 0.5 to 4 | per unit of capability | speed at which the reach ceiling 1 - exp(-k C) saturates in capability | the simulation |
| Growth lost to an open weights restriction | `open_weights_restriction_growth_loss` | 0.1 | 0.05 to 0.2 | 0 to 0.4 | a year | annual revenue growth lost by an open weights developer while publishing is restricted | the simulation |
| Enforcement response speed | `enforcement_response` | 0.25 | 0.12 to 0.5 | 0.05 to 1 | a month | speed at which enforcement intensity follows public pressure | the simulation |
| Trust recovery | `trust_recovery` | 0.05 | 0.03 to 0.1 | 0.01 to 0.2 | a month | monthly recovery of public trust towards 1 | the simulation |
| Trust sensitivity to harm | `trust_harm_sensitivity` | 0.04 | 0.02 to 0.08 | 0 to 0.3 | per log $bn | fall in trust per unit of log monetised harm in a month | the simulation |
| News memory | `news_memory` | 0.75 | 0.6 to 0.88 | 0.3 to 0.95 | a month | persistence of the news pressure index | the simulation |
| Salience boost from mandatory reporting | `news_reporting_boost` | 0.35 | 0.15 to 0.6 | 0 to 1 | share | extra salience of incidents when reporting is mandatory | the simulation |
| Market volatility | `market_vol` | 0.045 | 0.03 to 0.065 | 0.01 to 0.12 | a month | volatility of the common market factor | the simulation |
| Sentiment persistence | `sentiment_persistence` | 0.85 | 0.7 to 0.93 | 0.5 to 0.98 | a month | persistence of the price's non fundamental component | the simulation |
| Price impact of news pressure | `news_price_impact` | 0.06 | 0.03 to 0.12 | 0 to 0.3 | per unit of pressure | price impact of a unit of news pressure on an exposed firm | the simulation |
| Price jump on an own incident | `incident_jump` | 0.5 | 0.25 to 1 | 0 to 2 | multiple | own incident price jump per log unit of harm relative to revenue | the simulation |
| Sector contagion | `contagion` | 0.3 | 0.15 to 0.5 | 0 to 1 | share | share of an own incident jump felt by the rest of the sector | the simulation |
| Announcement price impact | `announcement_impact` | 0.9 | 0.45 to 1.8 | 0 to 3 | multiple | price reaction at announcement per unit of expected compliance cost over earnings | the simulation |
| Chip demand coupling | `chip_demand_coupling` | 0.6 | 0.3 to 0.9 | 0 to 1.5 | elasticity | chip and cloud revenue growth per unit of model developers' capability growth | the simulation |
| Open weights diffusion | `open_weights_diffusion` | 0.1 | 0.05 to 0.2 | 0 to 0.8 | share | capability spillover from published weights to the rest of the economy | the simulation |

68 assumptions; 14 enter only the welfare accounting and are recomputed exactly from the stored paths when they change, the other 54 change the simulated economy and are re simulated.
<!-- /generated:assumptions -->

Assumptions that plausibly move together are drawn together in the joint draw:

<!-- generated:correlated -->
- `hazard_base_misuse`, `hazard_base_accident`, `hazard_base_systemic`: rank correlation about 0.6 (a world with more incidents of one kind has more of the others).
- `severity_misuse_median_bn`, `severity_accident_median_bn`, `severity_systemic_median_bn`: rank correlation about 0.6 (incident harm scales with how deeply AI is embedded, whatever the category).
- `consumer_surplus_base_bn`, `productivity_base_bn`: rank correlation about 0.6 (both scale with how valuable AI services are).
- `cs_elasticity`, `productivity_elasticity`: rank correlation about 0.5 (both measure how fast benefits grow with the service index).
- `relocation_cost`, `offshore_revenue_haircut`: rank correlation about 0.4 (both are frictions of operating from another jurisdiction).
<!-- /generated:correlated -->

Fixed structural constants of the engine are not assumptions and are not varied:

<!-- generated:constants -->
- **safety share grid**: 0.02, 0.05, 0.10, 0.15, 0.20, 0.30 of R&D (the firm's choice set).
- **offshore share grid**: 0, 0.3, 0.6, 0.9 of activity (capped by the firm's mobility); at most 0.1 moves in a month.
- **reference safety share**: 0.10, the safety share the baseline growth rates already assume.
- **release milestone**: 0.25 capability index points between release headlines.
- **news salience weights**: minor incident 0.12, major incident 0.45, catastrophe 1.2, enforcement action 0.2, relocation 0.15, capability milestone 0.08 (positive), background noise 0.03.
- **hearing threshold**: news pressure above 0.45; high pressure above 0.3.
- **enforcement target**: capacity x (0.4 + 0.6 x news pressure); starting intensity 0.3 x capacity + 0.02.
- **expected penalty factor**: 1.5 x the fine a non compliant firm expects when audited (reputational surcharge).
- **valuation floor**: revenue multiple plus a smooth floor on the earnings multiple at 5% of revenue.
- **trust floor**: 0.3; enforcement intensity and compliance shares are clipped to [0, 1].
- **monthly revenue growth**: clipped to [-20%, +30%].
- **headline score**: the index reaction over months 1 to 6 plus 0.1 x the early tone difference.
<!-- /generated:constants -->

## 12. Assurance: attacking the answer

Every stage re makes the decision under an alternative: feasibility is re assessed against the
question's constraints and the status quo is an alternative. "The decision changes" means exactly
that, and an instrument that stops satisfying a constraint under an alternative stops being acceptable
under it. An alternative is **acceptable** when it is within the constraints and above the status quo.

Re simulations run on the first n paths of the main run and are paired with it,

    adjusted = main run, all paths + (alternative, first n paths - main run, first n paths)

so every figure sits on the headline scale, and an alternative that changes nothing reproduces the
headline exactly (tested).

**Screen.** Every declared assumption, one at a time, at the low and the high end of its plausible
range. Assumptions that enter only the accounting are recomputed exactly from the stored paths; the
others re simulate the battery, all of them in one vectorised pass. Each row carries the focus option's
value and the decision at each end, the Monte Carlo standard error of the swing, and why a decision
changed: by **feasibility** when the run's decision no longer satisfies a constraint under the
alternative, by **value** when another alternative within the constraints overtakes it. The tornado is
the screen's fifteen largest swings.

**Joint draw.** All the assumptions drawn together: a Latin hypercube, a triangular distribution on
each plausible range with its mode at the run's value, and a Gaussian copula for the correlated groups.
For every alternative: the mean and the 5th to 95th percentile of its net social value over the draws,
the share of draws in which it is the decision, the share in which it is within the constraints, the
share in which it is acceptable, and its **expected regret**, how far it falls short of the best
alternative within the constraints in the same draw, averaged over the draws in which it is itself
within them. Which assumptions the answer moves with is reported two ways: the rank correlation of each
with the focus option's margin over the best alternative, and Monte Carlo filtering, the Kolmogorov
Smirnov distance between an assumption's values in the draws where the focus option is the decision and
in those where it is not. Some of that many tests would pass by chance, so an assumption is called a
driver only if it survives a 10% false discovery rate (Benjamini and Hochberg). The distribution over
the ranges is a prior, not a posterior estimated from data.

**Variance decomposition.** Sobol indices over the assumptions the screen found most influential, the
rest held at the run's values: the share of the variance of the focus option's value, and of its margin
over the best alternative, that each explains alone (first order) and with its interactions (total
order). Saltelli's design on scrambled Sobol points; the first order estimator of Saltelli et al.
(2010), centred, and the total order estimator of Jansen (1999); 90% bootstrap intervals over the base
sample. The inputs are drawn independently, as the decomposition requires. The output is heavy tailed
in the assumptions that compound (capability growth and the capability elasticity of incidents), so the
shares converge slowly: the intervals say what the design resolves, which is groups of assumptions and
not the order of neighbours.

**Structural variants.** The battery re run under alternative model structures, with the decision, the
focus option's rank, value and feasibility under each:

<!-- generated:structural -->
| Variant | What changes |
|---|---|
| `myopic_firms` | firms plan six months ahead instead of twelve |
| `forward_looking_firms` | firms plan two years ahead |
| `weak_regulator` | the regulator has half the stated capacity |
| `strong_safety_effect` | safety practice cuts incidents faster |
| `weak_safety_effect` | safety practice cuts incidents more slowly |
| `lax_offshore` | offshore activity is twice as hazardous as at home |
| `heavy_tail` | the catastrophic tail is two and a half times more likely |
| `systemic_catastrophes` | catastrophic failures are strongly correlated across firms |
<!-- /generated:structural -->

**Red team.** Each instrument re run with firms following a gaming strategy. For each strategy: the
instrument's value, the harm it then avoids, whether it is still within the constraints and whether it
is still acceptable. The **maximin** choice is the instrument with the highest value under its own
worst strategy among those that stay within the constraints under every strategy, or the status quo if
none stays above zero.

<!-- generated:gaming -->
| Strategy | What changes |
|---|---|
| `threshold_splitting` | models are split so the regulator sees capability 20% below the real level |
| `compliance_theatre` | mandated safety spend is reported but not spent; evaluations are gamed |
| `maximal_relocation` | firms are more mobile and moving is cheaper than assumed |
| `use_case_relabelling` | deployments are relabelled into lower tiers, avoiding 60% of tier costs |
<!-- /generated:gaming -->

**Robustly acceptable.** An instrument is robustly acceptable when it is acceptable on the central
estimate, in at least 90% of the joint draws, in every structural variant and under every gaming
strategy. The briefing distinguishes the preferred option (the best on the central estimate) from the
robustly acceptable ones, and says when the preferred option is not among them.

## 13. Validation and the status of the mechanisms

The validation layer (`psl/validation.py`, `psl/benchmarks.py`) confronts the model with evidence in
two ways: published benchmarks, on every run, and an event study on a price series the analyst uploads.
Neither validates the model. Validation of a simulation can show where it is a poor description; it
cannot show that it is a true one.

### 13.1 Published benchmarks

A benchmark is one observable quantity with a published value: what was measured, with what standard
error, the model quantity it is compared with, and an allowance for the distance between the setting it
was measured in and the model's. The set in force is part of the battery approved at Gate 1 (its hash is
`evidence` in `battery.json`). The built in set is what the literature could support in November 2026:
two benchmarks measured on AI itself, one official ex ante estimate for an AI law, and eight analogues
from data protection, carbon pricing, cyber incidents, autonomous vehicles and insurance. An authority
with its own data replaces or extends it (`PSL_BENCHMARKS`, a JSON file with the same fields).

<!-- generated:benchmarks -->
| Benchmark | Kind | Observed | Standard error | Allowance for distance | Model quantity | Mechanisms | Source |
|---|---|---|---|---|---|---|---|
| Annual growth of recorded AI incidents (`incident_growth`) | direct | 56% | 8%: Poisson error of the annual counts (about 149, 233 and 362) | 25%: the database is compiled from media reports and its curators attribute an unknown share of the rise to reporting and attention; the model counts incidents at eight firm archetypes, not in the whole economy | the status quo's expected number of incidents in each year of the horizon; the benchmark is compared with the average annual growth of that count | incident hazard, capability and release | [Stanford HAI, AI Index Report 2025, chapter 3 (233 incidents in 2024, up 56.4% on 2023)](https://hai-production.s3.amazonaws.com/files/hai_ai-index-report-2025_chapter3_final.pdf); [Stanford HAI, AI Index Report 2026, responsible AI (362 incidents in 2025)](https://hai.stanford.edu/ai-index/2026-ai-index-report/responsible-ai) |
| Annual change in public trust in AI and AI companies (`trust_trend`) | direct | -5.1% | 1.2%: standard deviation of the three series over root three | 2.0%: a survey share is compared with the model's trust index, which starts at one and has no survey counterpart | the status quo's trust index at the end of the horizon, as an annual relative change from its starting value | adoption and trust | [Edelman Trust Barometer 2024, key insights around AI](https://www.edelman.com/sites/g/files/aatuss191/files/2024-03/Trust%20Tech%20Sector%20Top%20Findings.pdf); [Pew Research Center, How Americans view AI and its impact on people and society, September 2025](https://www.pewresearch.org/wp-content/uploads/sites/20/2025/09/PS_2025.9.15_AI-and-its-impact_report.pdf) |
| Share of a fall in trust recovered about nine months after a salient incident (`trust_recovery`) | analogue | 20% | 29%: each survey has a margin of error of four points at 95% (about 1,000 interviews); delta method on the ratio | 20%: another technology, and fear of using it is not trust in the firms that build it; the interval between the two surveys is known to within a few months | with monthly recovery r and no further incident, the share of a fall recovered after nine months is 1 - (1 - r)^9 | adoption and trust | [AAA, Three in four Americans remain afraid of fully self driving vehicles, March 2019](https://newsroom.aaa.com/2019/03/americans-fear-self-driving-cars-survey); [Smart Cities Dive, AAA poll, March 2019 (the 2018 figure and the crashes)](https://www.smartcitiesdive.com/news/aaa-poll-autonomous-vehicles-fear/550766/) |
| Compliance cost of a high risk regime as a share of development spending in scope (`compliance_cost_share`) | official | 10.8% | 6.2%: standard deviation of the two ex ante estimates over root two | 3.0%: an ex ante estimate per system built from a standard cost model, which its authors call a theoretical maximum; the model's cost is an instrument parameter applied to revenue in scope | under risk tiering, compliance spending over the R&D spending of the firms in scope on the activity in scope, while in force | firm choice, enforcement | [European Commission, SWD(2021) 84 final, impact assessment of the AI Act](https://data.consilium.europa.eu/doc/document/ST-8115-2021-ADD-2/en/pdf); [Renda et al. (2021), Study to support an impact assessment of regulatory requirements for AI in Europe](https://artificialintelligenceact.eu/wp-content/uploads/2022/06/AIA-COM-Impact-Assessment-3-21-April.pdf) |
| Effect of a horizontal compliance regime on the profits of firms in scope (`profit_effect`) | analogue | -3.3% | 2.4%: standard deviation of the three estimates over root three | 3.0%: data protection, not AI; a broad cross section of firms against eight archetypes that are mostly large | under risk tiering, the industry's earnings against the status quo on the same paths, over the months in force | revenue growth, firm choice | [Chen, Frey and Presidente (2022), Privacy regulation and firm performance, Oxford Martin working paper 2022-1](https://oms-www.files.svdcdn.com/production/downloads/Privacy-Regulation-and-Firm-Performance-Giorgio-WP-Upload-2022-1.pdf); [Johnson (2022), Economic research on privacy regulation: lessons from the GDPR and beyond, NBER working paper 30705](https://www.nber.org/system/files/working_papers/w30705/w30705.pdf) |
| Equity return when a horizontal regime becomes enforceable (`enforcement_return`) | analogue | -0.9% | 0.2%: half the published range | 1.0%: a week against the model's month; most of the cost of a law announced years earlier is in the price before it applies | under risk tiering, the value weighted index's change in the month the instrument takes effect, less the status quo's on the same path | market | [Motoki and Pinto (2024), Journal of Business Finance and Accounting (press summary)](https://www.eurekalert.org/news-releases/1051661) |
| Equity return of a firm when a regulatory fine is announced (`fine_return`) | analogue | -0.7% | 0.2%: the published t statistics (about 3 on estimates of about 0.007) | 1.0%: data protection fines, most of them small against the firm's size; days against the model's month | under risk tiering, a fined firm's log return in the month of the fine less the index's | market, enforcement | [Ford et al. (2021), The impact of GDPR infringement fines on the market value of firms, ECCWS](https://repository.uel.ac.uk/download/55420e51e0d25c813c8ab1d701f7b6e5093ba609fac84a9d9a3a874cb19e3a0d/689257/The%20Impact%20of%20GDPR%20Infringement%20Fines%20on%20the%20Market%20Value%20of%20Firms.pdf) |
| Equity return of a firm when a serious incident becomes public (`incident_return`) | analogue | -1.1% | 0.4%: an allowance: the standard error was not in the summary consulted | 1.0%: data breaches, not AI incidents; three days against the model's month | under the status quo, the log return of a firm in a month with a major incident at that firm, less the index's | market | [Kamiya, Kang, Kim, Milidonis and Stulz, What is the impact of successful cyberattacks on target firms? (authors' summary, Harvard Law School Forum on Corporate Governance, March 2018; Journal of Financial Economics 139(3), 2021)](https://corpgov.law.harvard.edu/2018/03/30/what-is-the-impact-of-successful-cyberattacks-on-target-firms/) |
| Share of regulated activity displaced abroad by a unilateral regime (`leakage_share`) | analogue | 14.0% | 5.0%: a quarter of the published range (5% to 25%) | 7.0%: carbon pricing, and mostly ex ante models; AI activity is divisible in some respects (where a model is trained) and not in others (one set of weights) | under frontier licensing, the revenue of the firms in scope booked offshore in the last year of the horizon, as a share of their revenue | relocation | [Branger and Quirion (2014), Ecological Economics 99](https://econpapers.repec.org/RePEc:hal:journl:hal-01137932) |
| Premium above expected claims in liability insurance (`insurance_loading`) | analogue | 31% | 0%: two years of an industry aggregate | 15%: all property and casualty lines; cover for AI liability is not an established line | the assumption itself: the premium charged above the expected liability under a mandate | liability and insurance | [NAIC, U.S. property and casualty and title insurance industries, 2023 full year results](https://content.naic.org/sites/default/files/industry-snapshot-2023-ye.pdf) |
| Share of the insurance loading used up by underwriting and administration (`insurance_resource_share`) | analogue | 107% | 2%: two years of an industry aggregate | 25%: all property and casualty lines, in two years with an underwriting loss (the share is above one because expenses exceeded the loading) | the assumption itself: the share of the loading that is a real resource cost and not a transfer to insurers | liability and insurance, welfare bases | [NAIC, U.S. property and casualty and title insurance industries, 2023 full year results](https://content.naic.org/sites/default/files/industry-snapshot-2023-ye.pdf) |
<!-- /generated:benchmarks -->

**The model quantity.** Each benchmark is compared with a moment of the simulation under a named
instrument (or the status quo), or with a declared assumption. A moment is a function `g` of path
means of a few ingredients, for example the ratio of compliance spending to R&D spending in scope:
`m = g(mean_i X_i)`. Its Monte Carlo variance `v` is a jackknife over paths. An instrument a benchmark
needs and the battery lacks is simulated beside it. A moment that averages over events (a fined firm's
return) is undefined where fewer than two occurred, and says so.

**At the central assumptions.** `z = (m - y)/sqrt(se^2 + t^2 + v)`, with `y` the observed value, `se`
its standard error and `t` the allowance. `|z| <= 2` is reported as not contradicted, `2 < |z| <= 3` as
in tension, `|z| > 3` as contradicted (the three sigma rule of history matching). "Not contradicted" is
the strongest verdict there is: with a wide allowance a benchmark is easy to pass and says little.

**Across the declared ranges.** The joint draw (section 12) evaluates the same moment in every draw of
the assumptions, which gives the model's prior predictive distribution of the benchmark; its 5th to
95th percentiles are reported beside the observation.

**Weighting the draws.** Draw `i`, with moments `m_ik`, is given the weight
`w_i proportional to exp(-1/2 sum_k z_ik^2)`, `z_ik = (m_ik - y_k)/sqrt(se_k^2 + t_k^2 + v_k)`, with
`v_k` the median Monte Carlo variance of the draws: importance sampling from the declared ranges with a
Gaussian likelihood whose variance includes the allowance (the model discrepancy term of Kennedy and
O'Hagan; a synthetic likelihood in the sense of Wood). The weighted draws are a posterior over the
assumptions given the benchmarks and the allowances. Reported from them: the share of weighted draws
in which each alternative is the decision, beside the unweighted share; the share in which the focus
option is within the constraints and above the status quo; the effective number of draws
`1/sum w_i^2` (below 20 the weighted shares are marked indicative only); and the share of draws no
benchmark rules out at three standard deviations, with the decision shares among those.

**A failure of form is not a parameter.** If even the closest tenth of the draws miss a benchmark by
more than two standard deviations, no value of the assumptions inside their ranges reproduces it. It
is reported as a failure of the model's form and left out of the weights, where it would otherwise
decide them for reasons unrelated to what the other benchmarks test. A benchmark whose moment is
defined in fewer than 80% of the draws is left out as well.

**Held out.** Each benchmark in the weights is also predicted from the draws weighted by all the
others, so it is never judged only against a fit that used it.

**Which assumptions the evidence bears on.** An assumption is informed by a benchmark when the
benchmark's moment moves with it across the draws: a rank correlation, at a 10% false discovery rate
over every pair of simulated assumption and benchmark. For those the report gives the weighted mean,
its shift from the unweighted mean in standard deviations of the draws, and the share of the spread
that remains. An assumption that only enters the welfare accounting cannot move a simulated moment and
cannot be informed this way: the elasticity of realised adoption to trust is one.

**What the benchmarks do not reach.** Evidence that was examined and could not be used is part of
the result, with the reason:

<!-- generated:benchmarks_not_used -->
| Evidence examined | Bears on | Why it is not a benchmark |
|---|---|---|
| Meta analysis of trust and intention to use a technology: r = 0.503 (95% interval 0.470 to 0.535, 128 samples, 50,667 respondents) ([Kuen, Westmattelmann, Bruckes and Schewe (2023), Electronic Markets 33:61](https://link.springer.com/content/pdf/10.1007/s12525-023-00672-1.pdf)) | adoption and trust (trust elasticity) | it supports the sign of the trust channel and nothing more: a correlation between stated attitudes in studies of online shopping, banking and e-health is not an elasticity of realised adoption to trust, and cannot be turned into one without the dispersion of both. The elasticity stays unidentified. |
| The size of the fall in trust after a salient incident (AAA: afraid to ride rose from 63% to 73% after two fatal crashes) ([AAA (2019)](https://newsroom.aaa.com/2019/03/americans-fear-self-driving-cars-survey)) | adoption and trust (trust harm sensitivity) | the model moves trust with monetised harm, and two deaths are a small monetised harm: an incident of that size moves the model's trust by less than a tenth of a percent. The episode says trust answers to salience; the model's form cannot show that. Recorded as a limit of the mechanism, not scored, because the survey question is about using a vehicle. |
| Estimates of AI's effect on output: total factor productivity up by no more than 0.66% over ten years (Acemoglu); 7% of global GDP over ten years (Goldman Sachs); $2.6 to $4.4 trillion a year (McKinsey) ([Acemoglu (2025), Economic Policy 40(121)](https://economics.mit.edu/sites/default/files/2024-05/The%20Simple%20Macroeconomics%20of%20AI.pdf)) | welfare bases (productivity base bn, consumer surplus base bn) | the model declares its benefit bases in $bn a year and declares no size for the jurisdiction's economy, so there is nothing to divide by; and the estimates span an order of magnitude. |
| Elicited probabilities of catastrophic harm from AI (expert and forecaster elicitations (no observed frequency exists)) | catastrophic tail | elicitations, not observations; they define catastrophe differently from the model and have no validation record. |
| A loss distribution for AI incidents ([AI Incident Database; MIT AI Incident Tracker; OECD AI Incidents Monitor](https://incidentdatabase.ai)) | severity | none has been published: the taxonomies exist, the magnitudes are not recorded. |
| GDPR and venture investment: monthly EU deals down 26.1% against US ventures ([Jia, Jin and Wagman (2021), Marketing Science 40(4)](https://econpapers.repec.org/RePEc:inm:ormksc:v:40:y:2021:i:4:p:661-684)) | revenue growth | the model has no entry or investment margin to compare it with. |
<!-- /generated:benchmarks_not_used -->

**Reading it.** The posterior is conditional on the allowances, which are judgements stated with their
reasons. Analogues from other sectors are weak evidence and are treated as such. The layer makes the
confrontation routine and its gaps explicit; it does not make any mechanism estimated.

### 13.2 An observed event

The market's early reaction to a regulatory announcement can also be compared with an event of the
authority's own choosing, through an event study on a monthly price series the analyst uploads, maps to
a firm archetype and, optionally, names as an analogue of an instrument.

- **Data desk.** ISO dates only, positive and finite prices, a monthly series without gaps (the last
  observation of each month), a schema check, a formula injection check, a personal identifier scan that
  refuses rather than redacts, a classification with no write down. A file that fails is refused with
  the reason.
- **Event time, one convention.** Monthly closes `p_0, ..., p_T`; the return of month k is
  `r_k = ln(p_k / p_k-1)`; the event month E is the month the announcement falls in. Estimation window:
  the 24 returns `r_E-24, ..., r_E-1`, all 24 required (a shorter history is refused, never shortened).
  Event window: the 6 returns `r_E, ..., r_E+5`. Abnormal return: `r_k` minus the market model
  `alpha + beta m_k` fitted on the estimation window (minus the estimation window mean without a market
  column). The cumulative abnormal return carries a standard error that includes the estimation error of
  alpha and beta; the t test has the right size on simulated series with no event (tested).
- **Held out calibration.** When a series calibrates a firm archetype's volatility and beta and has an
  event month, they are estimated on the returns before it, so the event window never informs the
  parameters it is compared with.
- **Comparison.** For an event named as an analogue of an instrument: the observed level effect against
  the model's predictive distribution of the early reaction for that instrument and firm (its mean, its
  10th to 90th percentile band, the probability integral transform, a z score). One event cannot
  establish calibration, and the output says so. With eight or more mapped events the Lab reports how
  many fall inside the band and the exact binomial test of that count against the band's nominal 80%.

### 13.3 The mechanism register

For every causal mechanism: its form, the assumptions it uses, what it rests on, its identifying
assumption, how it would be calibrated, what observation would test it, and whether either has been
done. The sources bracket magnitudes or motivate a form; none of them is a calibration, and no
parameter of the Lab is estimated from them. The register travels with every run (`artefacts.json`,
`mechanisms`), where each mechanism also carries the benchmarks of that run that bore on it and what
they showed, and the critic checks that every assumption belongs to a mechanism in it.

<!-- generated:mechanisms -->
**1. Reportable incidents arrive at a rate that rises with released capability and deployment reach and falls with safety practice.**

- Form: `lambda_k = h_k x C_eff^eta_C x exp(-eta_S S) x D^eta_D x (1 + O x laxity) x (1 - evaluation catch x unsafe share)`
- Assumptions: `hazard_base_misuse`, `hazard_base_accident`, `hazard_base_systemic`, `hazard_capability_elasticity`, `hazard_safety_elasticity`, `hazard_reach_elasticity`
- Rests on: Public incident counts are media derived and their growth mixes use with reporting (AI Index 2025, chapter 3; AI Incident Database): they bracket orders of magnitude and cannot identify the elasticities.
- Identifying assumption: Given the state, incidents are independent across firms, months and categories; capability, safety and reach act multiplicatively and separably.
- Calibration: None applied. A calibration would fit incident counts with exposure offsets and a reporting rate model to capability and deployment proxies.
- What would test it: Held out incident counts per firm and year inside the model's predictive interval; the sign and size of the safety elasticity from before and after comparisons at firms that adopt evaluation regimes.
- Status: uncalibrated

**2. The monetised harm of an incident is lognormal with a heavy tail; an incident at or above a threshold is major.**

- Form: `harm = median_k x exp(sigma z); major when harm >= threshold (each incident classified on its own harm)`
- Assumptions: `severity_misuse_median_bn`, `severity_accident_median_bn`, `severity_systemic_median_bn`, `severity_sigma`, `major_incident_bn`
- Rests on: Severity is not measured in the public incident record; heavy tailed loss distributions are the standard form for operational and cyber losses.
- Identifying assumption: Severity is independent of the incident's occurrence and of the state given the category.
- Calibration: None applied. A calibration would fit the tail index and scale of documented loss amounts by category.
- What would test it: The empirical tail of documented losses against the lognormal fit; the share of incidents above the major threshold.
- Status: uncalibrated

**3. Above a critical capability a firm faces a small monthly probability of a catastrophic incident, reduced by safety practice and evaluation, and correlated across firms.**

- Form: `p = prior x 1{C_eff > C*} x exp(-eta_S S) x (1 + O x laxity) x (1 - 0.5 x evaluation); joint failures by a one factor Gaussian copula with correlation rho; harm = H x exp(sigma_c z)`
- Assumptions: `catastrophe_prior_monthly`, `catastrophe_capability`, `catastrophe_harm_bn`, `catastrophe_severity_sigma`, `catastrophe_correlation`
- Rests on: Quantified estimates come from elicitation and disagree by about an order of magnitude (Grace et al. 2025, JAIR 84: median 5% for extremely bad outcomes; the 2022 Existential Risk Persuasion Tournament: 3% from domain experts against 0.38% from superforecasters for AI caused extinction by 2100). They motivate a live tail; they do not calibrate it.
- Identifying assumption: The tail is live only above a capability threshold; shared vulnerabilities enter through one common factor and leave each firm's own probability unchanged.
- Calibration: None possible from frequency data: no such event has been observed.
- What would test it: Not testable before the event. Treated by sensitivity: both ends of every range in the screen, the joint draw, and the heavy tail and systemic variants. Near miss frequencies would be partial evidence on the prior.
- Status: uncalibrated, untestable ex ante

**4. The share of R&D spent on safety raises safety practice with diminishing returns and displaces part of capability growth; practice decays without investment.**

- Form: `S' = S + a x sigma / (sigma + 0.1) x (1 - S) - decay x S; capability growth x (1 - substitution x sigma)`
- Assumptions: `safety_learning`, `safety_decay`, `safety_substitution`, `culture_weight`
- Rests on: Structural assumption; the development race literature motivates the trade off between safety and speed without measuring it.
- Identifying assumption: Safety practice is one dimensional and firm specific; returns to safety spend are concave.
- Calibration: None applied.
- What would test it: Firm level safety budgets against evaluation pass rates and incident rates over time.
- Status: uncalibrated

**5. A mandated evaluation catches a share of unsafe releases before deployment.**

- Form: `incident rate x (1 - catch rate x unsafe release share); catastrophe probability x (1 - 0.5 x catch rate)`
- Assumptions: `unsafe_release_share`
- Rests on: The catch rate is a design parameter of each instrument; the share of incidents a pre deployment evaluation could have caught is a judgement.
- Identifying assumption: Evaluations act only on the releases of compliant firms in scope; compliance theatre halves their effect.
- Calibration: None applied.
- What would test it: Post mortems of incidents: the share traceable to failures an evaluation at release would have found.
- Status: uncalibrated

**6. Each month a firm chooses its safety share, offshore share and whether to comply by maximising a one year expected payoff under its own optimistic view of incident risk.**

- Form: `max over the action grid of growth value - compliance - expected penalty - relocation - haircut - liability - risk + culture`
- Assumptions: `growth_value_weight`, `firm_optimism`, `firm_risk_aversion`, `audit_rate`, `revenue_capability_beta`
- Rests on: Compliance cost magnitudes are bracketed by the European Commission's impact assessment for the AI Act (SWD(2021) 84 final: about EUR 6,000 to 7,000 per high risk system, 4 to 5% of its cost); the investment response to a digital regulation by Jia, Jin and Wagman (2021, Marketing Science 40(4): 26.1% fewer venture deals after GDPR).
- Identifying assumption: Firms optimise myopically over twelve months with a common rule; the structural variants replace it with six and twenty four months.
- Calibration: None applied.
- What would test it: Observed compliance rates, safety budgets and release cadence after an instrument takes effect, against the model's.
- Status: uncalibrated

**7. Firms move activity offshore when the instrument binds at home; moved activity is laxer, loses revenue and takes domestic rents with it.**

- Form: `offshore share chosen from the grid, at most 0.1 a month, capped by mobility; leakage = share x offshore revenue`
- Assumptions: `relocation_cost`, `offshore_revenue_haircut`, `offshore_laxity`, `leakage_value_share`
- Rests on: Regulatory arbitrage in AI is theorised and anecdotal; its strength as a constraint is not quantified (Lancieri, Edelson and Bechtold 2025, Theoretical Inquiries in Law 26(1)).
- Identifying assumption: Mobility is a fixed firm trait; a coordinated instrument binds wherever the activity is.
- Calibration: None applied.
- What would test it: Changes in establishment location, hiring and model release geography around regulatory dates, against unaffected sectors.
- Status: uncalibrated

**8. Capability grows with R&D; licensing delays releases; a moratorium freezes released capability and slows research in scope; published weights diffuse capability.**

- Form: `C' = C x exp(g x (1 - substitution x sigma) x compute + diffusion); C_eff lags C by the release delay`
- Assumptions: `capability_growth`, `moratorium_research_slowdown`, `open_weights_diffusion`, `open_weights_misuse_multiplier`, `open_weights_restriction_growth_loss`, `export_control_chip_loss`, `chip_demand_coupling`
- Rests on: Structural assumption.
- Identifying assumption: Capability is a scalar index; a delay shifts releases without changing research.
- Calibration: None applied.
- What would test it: Release cadence and benchmark trajectories before and after a licensing regime.
- Status: uncalibrated

**9. Reach closes on a ceiling set by released capability and public trust; trust falls with harm and recovers slowly; adoption benefits scale with trust.**

- Form: `D' = D + speed x (1 - friction) x (ceiling x sqrt(T) - D); T' = T + recovery x (1 - T) - sensitivity x log(1 + harm)`
- Assumptions: `reach_speed`, `reach_ceiling_k`, `trust_recovery`, `trust_harm_sensitivity`, `trust_elasticity`, `revenue_reach_beta`
- Rests on: The trust channel has no causal estimate in the literature reviewed; survey trust and use move in opposite directions.
- Identifying assumption: Trust is one public index that responds to monetised harm only.
- Calibration: None applied.
- What would test it: Survey trust and adoption series around salient incidents.
- Status: uncalibrated

**10. A firm's revenue grows at a rate that fades from its starting pace towards a long run rate, moves with released capability and reach, and for chip and cloud firms with the developers' growth.**

- Form: `g = long run + (g0 - long run) x exp(-t / fade) + beta_C x (capability growth - reference); R = core x (D / D_ref)^beta_D`
- Assumptions: `growth_fade_months`, `long_run_growth`
- Rests on: Structural assumption; the firms are archetypes with declared starting revenues, margins and growth rates.
- Identifying assumption: Growth responds to capability and reach with constant elasticities common to all firms.
- Calibration: None applied; a firm archetype's revenue, margin and growth are the analyst's inputs.
- What would test it: Revenue growth of listed AI firms against capability releases and adoption series.
- Status: uncalibrated

**11. Enforcement intensity follows news pressure within the regulator's capacity; audits find the non compliant and fine them.**

- Form: `e' = e + response x (capacity x (0.4 + 0.6 P) - e); audit probability = audit rate x e`
- Assumptions: `enforcement_response`, `audit_rate`, `enforcement_cost_bn`
- Rests on: Media attention and regulatory action move together in the agenda setting literature; the functional form is an assumption.
- Identifying assumption: The regulator has no strategy beyond following pressure; fines are collected in full.
- Calibration: None applied.
- What would test it: Enforcement actions against news attention series for an existing regulator.
- Status: uncalibrated

**12. Incidents, enforcement, relocations and releases become a news pressure index with memory, and a wire of headlines on the representative path.**

- Form: `P' = memory x P + (1 - memory) x (1 - exp(-salience)); salience is a weighted count of the month's events`
- Assumptions: `news_memory`, `news_reporting_boost`
- Rests on: Media storms peak within days and decay over about two weeks in the attention literature; the monthly index and its salience weights (fixed constants) are assumptions.
- Identifying assumption: Salience is additive in event counts with fixed weights.
- Calibration: None applied.
- What would test it: Forecast coverage counts for a policy domain against observed counts.
- Status: uncalibrated

**13. A firm's price is a fundamental value (revenue and forward earnings multiples) times a sentiment component driven by the market factor, news pressure, incident jumps and, for an instrument announced before it takes effect, an anticipation term.**

- Form: `price = 100 x V / V_pre x exp(xi), with V_pre the valuation before any instrument is announced, common to the battery`
- Assumptions: `market_vol`, `sentiment_persistence`, `news_price_impact`, `incident_jump`, `contagion`, `announcement_impact`
- Rests on: Measured analogues are small: US firms subject to GDPR lost 0.6 to 1.1% of market value in the week it became enforceable (Motoki and Pinto 2024, Journal of Business Finance and Accounting); event studies of regulation have little power in monthly data and announcements are anticipated (Binder 1985, RAND Journal of Economics 16(2)).
- Identifying assumption: The market prices the state it sees and anticipates an announced instrument only through the announcement term.
- Calibration: A firm archetype's beta and idiosyncratic volatility can be estimated from an uploaded price series, on the returns before the event month.
- What would test it: Implemented: an event study on an uploaded series mapped to a firm and an instrument, against the model's predictive distribution of the early reaction; with eight or more mapped events, the coverage of the 10th to 90th percentile band.
- Status: partly calibrable; one mechanism testable here; tested in the Lab when an event is uploaded

**14. Consumer surplus and the output uplift are powers of the AI service index around declared annual bases.**

- Form: `CS = base_cs x Q^e_cs; output = base_y x Q^e_y x T^e_T`
- Assumptions: `consumer_surplus_base_bn`, `cs_elasticity`, `productivity_base_bn`, `productivity_elasticity`, `trust_elasticity`, `benefit_overlap_share`, `labour_adjustment_bn`, `domestic_ownership_share`, `compliance_deadweight_share`, `harm_valuation_multiplier`, `discount_rate`
- Rests on: Estimates of AI's economic value span about two orders of magnitude (Acemoglu 2025, Economic Policy 40(121): total factor productivity up by no more than 0.66% over ten years; Goldman Sachs 2023: 7% of global GDP).
- Identifying assumption: Benefits depend on the economy only through the service index and trust; the three benefit components do not overlap by definition (welfare.ACCOUNT_MAP), and a declared overlap share removes from the output uplift whatever part of it is judged to be already in the other two.
- Calibration: None applied; the bases are value judgements and the largest swings of the tornado.
- What would test it: Not a testable mechanism: a valuation. Treated by sensitivity.
- Status: declared value judgements

**15. Liability moves a share of harm to the firm in scope; a safe harbour shields the compliant; a mandate replaces realised liability with a premium loaded above expected claims.**

- Form: `liability = multiplier x harm x (1 - shield x comply); premium = expected liability x (1 + loading) / 12`
- Assumptions: `safe_harbour_shield`, `insurance_loading`, `insurance_admin_share`
- Rests on: The law and economics of liability supplies the mechanism; no premium data for AI liability cover was found.
- Identifying assumption: Insurers price on the firm's own expectation; claims are paid in full.
- Calibration: None applied.
- What would test it: Quoted premiums and exclusions for AI liability cover against the model's.
- Status: uncalibrated
<!-- /generated:mechanisms -->

## 14. Governance and verification

Nothing simulates before the battery, with its sampling plan and seed, is approved at Gate 1, and
nothing is released before the briefing is released at Gate 2. With named gates (the default for an
authority) both need a named approver who differs from the preparer and, where a register is
configured, is on it in an approving function; either gate can be refused with reasons. With open gates
(a public demonstration) they are single clicks and every record says so. Every step is appended to a
hash chained, HMAC signed ledger with a replay check.

Three independent checks stand between a run and a reader:

- **The critic** (inside the Lab, before Gate 2 can arm) reloads the stored paths and recomputes the
  welfare components, the accounting identities, the decision with the status quo among the
  alternatives, feasibility, the rankings with ties, the decision gap and the confidence interval of the
  preferred alternative; checks that the sampling plan was followed and that anything short of its
  target is said in the briefing; checks that the artefacts the briefing was drafted from are the
  documents it recomputed; replays the ledger; and vets every number in the briefing against the
  artefacts.
- **A second implementation** (`tools/recompute.py`) recomputes the accounting, the decision,
  feasibility and the intervals from the stored paths with numpy alone, from this document, importing
  nothing from the Lab. The critic checks that the Lab is consistent with itself; this checks that it
  does what this document says.
- **Replication** (`tools/replicate.py`) repeats a run on independent seeds.

The critic also checks the validation layer: that every benchmark carries a source, a mapping and an
allowance; that each verdict follows from the observed and modelled values; that the weighted decision
shares reproduce from the stored draws and weights; that the evidence base is the one approved at Gate
1; and that the briefing names every benchmark the model is in tension with or contradicted by.

**The engine's decision routine has a reference.** Each month every firm chooses among 48 actions (six
safety shares, four offshore shares, comply or not). `Economy._decide_reference` writes the payoff out on
the full grid, every term on every action. `Economy._decide`, which every run uses, computes each term
only on the action axes it depends on, leaves out a term the instrument sets to zero and evaluates the
exponential of the hazard once per distinct safety share; it performs the same floating point
operations in the same order, and a test asserts that the two return the same bits for every library
instrument, structural variant, gaming strategy and for designs with one assumption value per path.

**An identical battery can be reused.** A battery is deterministic. With `PSL_REUSE=on` (off by default;
the public demonstration switches it on) a battery whose key matches a completed run in the registry is
not simulated again: the stored figures are copied, the recorded stream is replayed, and the critic
recomputes every figure of the new run from the copied paths. The key is a hash of the battery hash, the
code fingerprint, the versions of Python, numpy and scipy, the wire's start date and the uploaded
series. The ledger records `battery_reused` with the source run, and the briefing says which run
computed the figures.

The evidence pack carries the artefacts, the battery, the assumptions, the briefing, the critic's
report, the transparency record, the ledger and a `VERIFY.md` so a second authority can do all three.

## 15. What the Lab is not

It is not a forecast of real companies or events. The archetypes are not companies. No mechanism is
estimated from data; ten of the fifteen are confronted with a published benchmark, mostly an analogue,
and five (severity, the catastrophic tail, safety practice, evaluation, the news) with none. The harm
side rests on declared hazard and tail assumptions, and the largest benefit of several instruments is not the harm they avoid directly but the
adoption that higher public trust allows, a channel with no causal estimate behind it: the screen, the
joint draw and the variance decomposition show how far the answer depends on each, and the briefing
names them. The plausible ranges are judgements; the joint draw is a prior. The Lab informs a policy
choice. It does not make one.

## 16. Methods referred to

- Asmussen, S. and Glynn, P. W. (2007). *Stochastic Simulation: Algorithms and Analysis*. Springer. Conditional Monte Carlo; common random numbers.
- Benjamini, Y. and Hochberg, Y. (1995). Controlling the false discovery rate. *Journal of the Royal Statistical Society B* 57(1), 289-300.
- Efron, B. and Tibshirani, R. J. (1993). *An Introduction to the Bootstrap*. Chapman and Hall.
- Hornberger, G. M. and Spear, R. C. (1981). An approach to the preliminary analysis of environmental systems. *Journal of Environmental Management* 12, 7-18. Monte Carlo filtering.
- Jansen, M. J. W. (1999). Analysis of variance designs for model output. *Computer Physics Communications* 117, 35-43.
- Kendall, M. G. (1945). The treatment of ties in ranking problems. *Biometrika* 33(3), 239-251.
- Kennedy, M. C. and O'Hagan, A. (2001). Bayesian calibration of computer models. *Journal of the Royal Statistical Society B* 63(3), 425-464. Model discrepancy.
- Kish, L. (1965). *Survey Sampling*. Wiley. The effective sample size of weighted observations.
- Li, D. X. (2000). On default correlation: a copula function approach. *Journal of Fixed Income* 9(4), 43-54.
- MacKinlay, A. C. (1997). Event studies in economics and finance. *Journal of Economic Literature* 35(1), 13-39.
- McKay, M. D., Beckman, R. J. and Conover, W. J. (1979). A comparison of three methods for selecting values of input variables in the analysis of output from a computer code. *Technometrics* 21(2), 239-245.
- Pukelsheim, F. (1994). The three sigma rule. *The American Statistician* 48(2), 88-91.
- Saltelli, A., Annoni, P., Azzini, I., Campolongo, F., Ratto, M. and Tarantola, S. (2010). Variance based sensitivity analysis of model output. *Computer Physics Communications* 181(2), 259-270.
- Wilson, E. B. (1927). Probable inference, the law of succession, and statistical inference. *Journal of the American Statistical Association* 22(158), 209-212.
- Vernon, I., Goldstein, M. and Bower, R. G. (2010). Galaxy formation: a Bayesian uncertainty analysis. *Bayesian Analysis* 5(4), 619-669. History matching and implausibility.
- Wood, S. N. (2010). Statistical inference for noisy nonlinear ecological dynamic systems. *Nature* 466, 1102-1104. Synthetic likelihood.
