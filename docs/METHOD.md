# Policy Scenario Lab: method

This document states what the Lab computes, equation by equation, so that a reviewer can check the
code against it and a policy team can see where every number comes from. Nothing in it is a forecast
of a named company or event: the economy is synthetic, the firms are archetypes, and the outputs are
expected values with intervals on a declared set of assumptions.

## 1. The question the Lab answers

A policy team asks which of several candidate regulatory instruments is best, under constraints it
cares about (the technology sector's net loss, the gross social cost, the expected harm). The Lab
answers with a *battery*: every candidate instrument, and the status quo, run on the same synthetic AI
economy over the same horizon on the same random numbers. Each instrument is then scored on four
things the team needs beside one another:

1. **Safety**: incident rates, the probability of a major and of a catastrophic incident, expected
   monetised harm, the safety practice firms actually adopt, public trust.
2. **The industry's gain or loss**: each firm's value change against the status quo, paired path by
   path, and the probability it gains; the sector totals; the value weighted index.
3. **The social ledger**: what the instrument buys (harm avoided, consumer surplus, output, resident
   producer surplus) and what it costs (compliance resources, enforcement budget, offshore leakage,
   relocation, labour adjustment), as present values, with who gains and who pays.
4. **The news environment**: the headlines the instrument generates, as a numeric forecast across
   all paths and as a wire of headlines composed by media agents on one representative path.

The decision metric is the expected net social value over the horizon under the question's
constraints. The decision gap measures how far the instruments' early appearance (the first six
months' market reaction and press tone) diverges from their value over the horizon.

## 2. Common random numbers

Every policy in a battery runs on one `RandomBundle`: market shocks, policy uncertainty shocks,
idiosyncratic price shocks, incident draws, severity draws, catastrophe draws, audit draws and news
noise, drawn once per path and reused for every instrument. The difference between two instruments on
a path is therefore the instrument's doing and not the dice, and every "against the baseline" figure
is a paired difference. Each path has its own stream seeded by `(seed, path index)`, so a bundle of
fewer paths is exactly the first paths of a larger one: the assurance re simulations on a smaller
budget are paired with the main run path by path (section 8).

## 3. The agents

### 3.1 Firms

Eight archetypes of the AI value chain by default (the Firm workshop can replace them):

| Firm | Sector | Revenue $bn | Margin | Growth | Capability | Safety | Reach | In scope | Mobility | Culture | Beta | Idio vol | PE |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Frontier Lab (closed weights) | frontier_lab | 15 | 15% | 45% | 1.2 | 0.5 | 0.7 | 90% | 0.4 | 0.55 | 1.4 | 10% | 45 |
| Frontier Lab (open weights) | open_weights | 4 | 5% | 50% | 1.05 | 0.4 | 0.6 | 90% | 0.6 | 0.45 | 1.5 | 12% | 60 |
| Hyperscaler cloud | hyperscaler | 120 | 30% | 18% | 1.1 | 0.6 | 0.9 | 40% | 0.2 | 0.6 | 1.1 | 7% | 28 |
| Chip designer | chips | 90 | 45% | 25% | 0.6 | 0.7 | 0.95 | 15% | 0.3 | 0.6 | 1.6 | 8% | 35 |
| Enterprise software | enterprise_software | 60 | 28% | 14% | 0.8 | 0.6 | 0.85 | 50% | 0.1 | 0.6 | 1.0 | 7% | 30 |
| Consumer AI platform | consumer_ai | 30 | 20% | 30% | 0.95 | 0.45 | 0.8 | 70% | 0.3 | 0.4 | 1.3 | 9% | 38 |
| Autonomy and robotics | autonomy | 8 | 8% | 40% | 0.85 | 0.5 | 0.4 | 80% | 0.3 | 0.5 | 1.5 | 11% | 50 |
| AI start up cohort | startups | 6 | -10% | 60% | 0.7 | 0.35 | 0.3 | 60% | 0.7 | 0.35 | 1.7 | 10% | 60 |

Each month every firm chooses, from a grid, a **safety share of R&D** σ ∈ {0.02, 0.05, 0.10, 0.15,
0.20, 0.30}, an **offshore share** ω ∈ {0, 0.3, 0.6, 0.9} capped by its mobility, and whether to
**comply** χ ∈ {0, 1}, by maximising a one year expected payoff (the planning horizon is a structural
variant):

    U(σ, ω, χ) = growth value − compliance cost − expected fines − relocation cost − offshore haircut
                 − expected liability (or insurance premium) − risk premium + culture term

where the growth value is `growth_value_weight × R × revenue_capability_beta × ΔC(σ, ω) × (1 − delay/plan)`,
with ΔC the capability growth over the planning horizon after safety substitution, export controls and
any moratorium; the compliance cost is the instrument's fixed plus variable cost on the share of
activity bound by it; expected fines are the audit probability times the fine rate on in scope revenue
for a non compliant firm; the expected liability is the firm's own (optimistic, `firm_optimism`) view
of its incident rate and the catastrophic tail, times the instrument's liability multiplier, reduced by
the safe harbour shield when the firm complies; the risk premium is `firm_risk_aversion × ½ × liability`
unless insurance is mandated, in which case the premium carries a loading; the culture term values the
gain in safety level at `culture × 0.6 × R`.

An instrument **binds** the share of a firm's activity that is in scope: all of it under a coordinated
instrument, the share not moved offshore under a domestic one. Scope is a sector test and a capability
threshold on released capability. Liability follows the harm, not the office: a firm cannot escape
liability for harm its systems cause at home by moving.

### 3.2 Dynamics

- Safety level `S_{t+1} = S_t + safety_learning × σ/(σ + 0.1) × (1 − S_t) − safety_decay × S_t`
  (saturating learning, erosion without investment), clipped to [0.02, 0.98].
- Capability `C_{t+1} = C_t × exp(g)`, `g = capability_growth × (1 − safety_substitution × σ) × compute factor
  + diffusion`, halved by `moratorium_research_slowdown` while a moratorium holds for a firm in scope;
  open weights diffuse a tenth of the gap to the open developer into other model sectors.
- Released capability lags capability by the approval delay and is frozen by a moratorium.
- Reach closes at `reach_speed` on a ceiling `(1 − exp(−1.5 C_eff)) × √trust`, slowed by tier friction;
  a frictionless, full trust reference reach is tracked so revenue can be expressed relative to it.
- Revenue grows at a rate that fades from the archetype's starting growth to `long_run_growth`, plus
  `revenue_capability_beta × (Δlog C_eff − g_ref)`, minus the offshore haircut; chips and cloud ride the
  model developers' capability growth through `chip_demand_coupling`; revenue is then scaled by
  `(reach / reference reach)^revenue_reach_beta`.

### 3.3 Hazard

Each month, each firm, each category k ∈ {misuse, accident, systemic} has an incident with probability
`1 − exp(−λ_k)`, where

    λ_k = base_k × C_eff^η_C × exp(−η_S S) × D^η_D × (1 + ω × offshore_laxity) × (1 − eval_catch × χ × unsafe_release_share)

reduced further by transparency for misuse and systemic incidents, and raised by 1.3 for misuse at an
open weights developer unless weights are restricted. Harm is lognormal, `median_k × exp(severity_sigma × z)`.
Above `catastrophe_capability` a catastrophic incident occurs with monthly probability
`catastrophe_prior_monthly × exp(−η_S S) × (1 + ω × laxity) × (1 − ½ eval_catch × χ)` and harm
`catastrophe_harm_bn × exp(0.5 z)`. Compliance theatre (a red team strategy) halves the evaluation effect.

### 3.4 Regulator, public and press

- Enforcement intensity follows public pressure within capacity:
  `e_{t+1} = e_t + enforcement_response × (capacity × (0.4 + 0.6 P) − e_t)`; a firm in scope is audited
  with probability `audit_rate × e` and fined `fine_rate × in scope revenue` if non compliant.
- Public trust `T_{t+1} = T_t + trust_recovery × (1 − T_t) − trust_harm_sensitivity × log(1 + harm)`,
  clipped to [0.3, 1]; trust caps deployment reach and scales the realised adoption benefits.
- News pressure `P_{t+1} = news_memory × P_t + (1 − news_memory) × (1 − exp(−x))`, where x weighs minor
  incidents, major incidents, catastrophes, enforcement actions and relocations (reporting mandates raise
  incident salience by `news_reporting_boost`); tone is the balance of positive (milestones) against
  negative salience. Four media agents (WIRE, TECH, CIVIC, CAPITOL) turn the representative path's
  events into headlines from templates; every figure in a headline is the event's own.

### 3.5 Market

A firm's fundamental value is a revenue multiple plus an earnings multiple on forward earnings with a
smooth floor, `V = ps × R + pe × k × log(1 + exp(FE/k))`, `k = 0.05 R`, where forward earnings are the
run rate (one offs excluded) grown at the trailing twelve month growth. The price is
`100 × V/V_0 × exp(ξ)`, with a sentiment component

    ξ_{t+1} = sentiment_persistence × ξ_t + β × market_vol × z_market + 0.01 × exposure × z_policy
                − news_price_impact × P × (0.3 + exposure) + own incident jump + sector contagion
                + announcement effect (month 0 only) + idiosyncratic noise

The announcement effect is the expected compliance cost and liability over earnings, scaled by
`announcement_impact` and capped at −25%. Fines, realised liability and relocation costs enter as jumps.
Prices are indexed to 100 at the announcement; the market value at the end of the horizon is
`cap_0 × price/100`.

## 4. The instrument library

| Name | Label | Scope | What it does |
|---|---|---|---|
| `baseline` | Status quo (voluntary commitments) | home | enforcement capacity 0.1; domestic scope |
| `transparency_disclosure` | Transparency and disclosure | home | provenance and disclosure; compliance $0.01bn fixed plus 0.2% of revenue; enforcement capacity 0.3, fines 1% of revenue; domestic scope |
| `compute_threshold_reporting` | Compute threshold reporting | home | above capability 1.0; evaluations catch 15% of unsafe releases; compliance $0.03bn fixed plus 0.5% of revenue; enforcement capacity 0.4, fines 2% of revenue; domestic scope |
| `mandatory_third_party_evals` | Mandatory third party evaluation | home | above capability 0.8; safety spend at least 8% of R&D; evaluations catch 45% of unsafe releases; 2 month approval delay; compliance $0.08bn fixed plus 1.0% of revenue; enforcement capacity 0.5, fines 6% of revenue; domestic scope |
| `risk_tiering` | Risk tiering (EU style) | home | safety spend at least 5% of R&D; 1 month approval delay; provenance and disclosure; risk tier conformity for deployers; compliance $0.05bn fixed plus 3.0% of revenue; enforcement capacity 0.6, fines 7% of revenue; domestic scope |
| `frontier_licensing` | Frontier licensing | home | above capability 1.0; safety spend at least 25% of R&D; evaluations catch 60% of unsafe releases; 4 month approval delay; compliance $0.15bn fixed plus 2.0% of revenue; enforcement capacity 0.7, fines 10% of revenue; domestic scope |
| `coordinated_licensing` | Coordinated frontier licensing | coordinated | above capability 1.0; safety spend at least 25% of R&D; evaluations catch 60% of unsafe releases; 4 month approval delay; compliance $0.15bn fixed plus 2.0% of revenue; enforcement capacity 0.7, fines 10% of revenue; coordinated across jurisdictions |
| `strict_liability` | Strict liability | home | liability for 80% of harm; compliance $0.02bn fixed plus 0.5% of revenue; enforcement capacity 0.3; domestic scope |
| `liability_with_safe_harbour` | Liability with a safe harbour | home | safety spend at least 12% of R&D; evaluations catch 35% of unsafe releases; liability for 80% of harm with a safe harbour; compliance $0.08bn fixed plus 1.2% of revenue; enforcement capacity 0.4, fines 3% of revenue; domestic scope |
| `moratorium` | Six month moratorium above the threshold | home | above capability 1.1; evaluations catch 15% of unsafe releases; 6 month moratorium; compliance $0.03bn fixed plus 0.0% of revenue; enforcement capacity 0.5, fines 5% of revenue; domestic scope |
| `export_controls` | Compute export controls | home | above capability 1.0; compute export controls; compliance $0.02bn fixed plus 0.0% of revenue; enforcement capacity 0.4, fines 3% of revenue; domestic scope |
| `open_weights_restriction` | Open weights restriction | home | above capability 0.9; provenance and disclosure; no open weights above the threshold; compliance $0.02bn fixed plus 0.0% of revenue; enforcement capacity 0.4, fines 4% of revenue; domestic scope |
| `sandbox_light_touch` | Sandbox and light touch | home | provenance and disclosure; compliance $0.00bn fixed plus 0.4% of revenue; enforcement capacity 0.3, fines 1% of revenue; domestic scope |
| `eu_style_package` | EU style package | home | safety spend at least 10% of R&D; evaluations catch 45% of unsafe releases; 2 month approval delay; provenance and disclosure; risk tier conformity for deployers; compliance $0.10bn fixed plus 3.0% of revenue; enforcement capacity 0.7, fines 7% of revenue; domestic scope |
| `licensing_plus_liability` | Licensing plus liability | home | above capability 1.0; safety spend at least 25% of R&D; evaluations catch 60% of unsafe releases; 4 month approval delay; liability for 80% of harm with a safe harbour; compliance $0.15bn fixed plus 2.0% of revenue; enforcement capacity 0.7, fines 10% of revenue; domestic scope |

The default battery is `baseline`, `transparency_disclosure`, `compute_threshold_reporting`, `mandatory_third_party_evals`, `risk_tiering`, `frontier_licensing`, `strict_liability`, `liability_with_safe_harbour`, `moratorium`. An instrument is a bounded JSON
document; bounds: `phase_in` 0 to 36, `sunset` 0 to 120, `capability_threshold` 0.0 to 3.0, `fixed_cost` 0.0 to 2.0, `variable_cost` 0.0 to 0.1, `min_safety_share` 0.0 to 0.5, `eval_catch` 0.0 to 0.9, `release_delay` 0 to 12, `moratorium_months` 0 to 24, `liability_multiplier` 0.0 to 1.5, `transparency` 0.0 to 0.3, `enforcement_capacity` 0.0 to 1.0, `fine_rate` 0.0 to 0.2, `export_controls` 0.0 to 1.0, `tier_friction` 0.0 to 0.3. Custom instruments are validated, clamped to the bounds (clamping is
reported), hashed and carried in the battery hash and the ledger.

## 5. Welfare accounting

For policy P against baseline B, per path, with monthly discount factors `d_t = (1 + r)^(−t/12)`
(r = `discount_rate`), all in $bn present value:

| Component | Definition |
|---|---|
| harm avoided | `harm_valuation_multiplier × Σ_t d_t (harm_B − harm_P)` |
| consumer surplus change | `(consumer_surplus_base_bn/12) × Σ_t d_t (Q_P^ε − Q_B^ε)`, ε = `cs_elasticity`, Q the AI service index (capability × reach, revenue weighted, 1 at the start) |
| productivity (output) change | `(productivity_base_bn/12) × Σ_t d_t (Q_P^ε' T_P^τ − Q_B^ε' T_B^τ)`, ε' = `productivity_elasticity`, τ = `trust_elasticity` |
| resident producer surplus | `domestic_ownership_share × Σ_t d_t (operating earnings_P − operating earnings_B)` |
| compliance cost | `compliance_deadweight_share × Σ_t d_t (compliance_P − compliance_B)` |
| enforcement cost | `(enforcement_cost_bn/12) × Σ_t d_t (e_P − e_B)` |
| leakage | `leakage_value_share × Σ_t d_t (offshore revenue_P − offshore revenue_B)` |
| relocation cost | `Σ_t d_t (relocation_P − relocation_B)` |
| labour adjustment | `labour_adjustment_bn × Σ_t d_t (max(ΔQ_P, 0) − max(ΔQ_B, 0))` |

    net social value = harm avoided + consumer surplus + productivity + producer surplus
                       − compliance − enforcement − leakage − relocation − labour

Fines, liability payouts and insurance premiums are transfers and are reported but excluded from the
net. The gross social cost is the sum of the cost components and of any negative benefit components.
The distribution table attributes the components to the public (harm not suffered), consumers, the
wider economy (output), resident shareholders, workers, taxpayers (enforcement net of fines) and
abroad (relocated activity). The industry's value change is the discounted change in earnings over the
horizon plus the discounted change in market value at its end, per firm, paired with the baseline.

Every summary carries the mean, the 10th and 90th percentiles across paths, the share of paths above
zero, the median and the *tail share* (the share of the mean contributed by the top tenth of paths).
When the mean sits above the 90th percentile the panel says so: the expected value is being carried by
the few paths in which a catastrophe is averted, which is a feature of the problem, not an error.

## 6. Decision metrics

- **Preferred option**: the feasible instrument (satisfying every constraint read from the question)
  with the highest expected net social value; the best unconstrained option is reported beside it.
- **P(best)**: in a bootstrap over paths (common random numbers kept), the share of resamples in which
  each instrument has the highest mean net social value; **winner stability** is the maximum.
- **Headline score**: the value weighted price reaction against the baseline over the first six
  months plus a tenth of the early press tone difference.
- **Decision gap** = (1 − τ)/2 where τ is Kendall's tau between the headline ranking and the social
  ranking; **P(inversion)** is the bootstrap share of resamples with τ < 0.
- **Cost per dollar of harm avoided**: gross social cost over harm avoided.

## 7. Assumptions

Every value judgement and calibration constant is declared, bounded and hashed into the battery.

| Assumption | Default | Range | Unit | Meaning |
|---|---|---|---|---|
| `discount_rate` | 0.03 | 0.0 to 0.1 | a year | social discount rate applied to every monthly flow |
| `harm_valuation_multiplier` | 1.0 | 0.25 to 4.0 | multiple | scales the monetised harm of incidents; 1.0 takes the engine's damages at face value |
| `consumer_surplus_base_bn` | 250.0 | 50.0 to 1500.0 | $bn a year | annual consumer surplus from AI services at the starting level of capability and reach |
| `cs_elasticity` | 0.6 | 0.1 to 1.5 | elasticity | proportional change in consumer surplus per proportional change in the AI service index |
| `productivity_base_bn` | 400.0 | 50.0 to 2000.0 | $bn a year | annual output uplift attributable to AI adoption at the starting service index |
| `productivity_elasticity` | 0.8 | 0.1 to 1.5 | elasticity | proportional change in the output uplift per proportional change in the service index |
| `trust_elasticity` | 0.5 | 0.0 to 1.5 | elasticity | proportional change in realised adoption benefits per proportional change in public trust |
| `compliance_deadweight_share` | 0.7 | 0.3 to 1.0 | share | share of compliance spend that is a real resource cost rather than a transfer |
| `enforcement_cost_bn` | 0.4 | 0.05 to 2.0 | $bn a year per unit of capacity | public budget consumed by one unit of enforcement capacity |
| `leakage_value_share` | 0.35 | 0.0 to 1.0 | share | domestic value added lost per dollar of revenue whose activity moves offshore |
| `labour_adjustment_bn` | 2.0 | 0.0 to 10.0 | $bn per index point | short run adjustment cost per point of growth in the AI service index (displacement, retraining) |
| `domestic_ownership_share` | 0.6 | 0.0 to 1.0 | share | share of the firms' operating profit that accrues to residents and counts in national welfare |
| `hazard_base_misuse` | 0.08 | 0.01 to 0.3 | a month per firm | monthly rate of a reportable misuse incident for a firm at capability 1, full reach and no safety practice |
| `hazard_base_accident` | 0.05 | 0.01 to 0.3 | a month per firm | the same for accidents and failures |
| `hazard_base_systemic` | 0.02 | 0.002 to 0.15 | a month per firm | the same for systemic incidents (markets, infrastructure, information) |
| `hazard_capability_elasticity` | 1.3 | 0.5 to 2.5 | elasticity | incident rate scales with capability to this power |
| `hazard_safety_elasticity` | 1.8 | 0.5 to 4.0 | per unit of safety level | incident rate falls as exp(-elasticity x safety level) |
| `hazard_reach_elasticity` | 1.0 | 0.3 to 2.0 | elasticity | incident rate scales with deployment reach to this power |
| `offshore_laxity` | 0.6 | 0.0 to 2.0 | multiple | extra incident rate on activity moved offshore, relative to home |
| `severity_misuse_median_bn` | 0.15 | 0.01 to 2.0 | $bn | median monetised harm of a misuse incident |
| `severity_accident_median_bn` | 0.3 | 0.02 to 3.0 | $bn | median monetised harm of an accident |
| `severity_systemic_median_bn` | 1.0 | 0.1 to 10.0 | $bn | median monetised harm of a systemic incident |
| `severity_sigma` | 1.1 | 0.5 to 2.0 | log scale | lognormal dispersion of incident harm (heavy tail) |
| `major_incident_bn` | 1.0 | 0.2 to 10.0 | $bn | harm above which an incident counts as major |
| `catastrophe_prior_monthly` | 0.002 | 0.0 to 0.02 | a month per firm | monthly probability of a catastrophic incident for a firm above critical capability with no safety practice |
| `catastrophe_capability` | 1.6 | 1.0 to 3.0 | capability index | capability above which the catastrophic tail is live |
| `catastrophe_harm_bn` | 400.0 | 20.0 to 3000.0 | $bn | median monetised harm of a catastrophic incident |
| `unsafe_release_share` | 0.35 | 0.05 to 0.8 | share | share of the incident rate attributable to releases an evaluation could catch |
| `capability_growth` | 0.023 | 0.005 to 0.06 | a month | monthly log growth of the capability index when all R&D goes to capability (a doubling in about 30 months) |
| `safety_learning` | 0.08 | 0.02 to 0.3 | a month | monthly gain in safety practice at saturation; the gain is a x share/(share + 0.1), diminishing in the share |
| `growth_fade_months` | 30.0 | 6.0 to 120.0 | months | time constant over which a firm's growth fades towards the long run rate |
| `safety_substitution` | 0.6 | 0.0 to 1.0 | share | share of safety spend that displaces capability R&D (the rest is additional budget or spills over) |
| `export_control_chip_loss` | 0.1 | 0.0 to 0.4 | a year | annual revenue growth lost by the chip sector under full export controls |
| `long_run_growth` | 0.06 | 0.0 to 0.2 | a year | the growth rate firms fade towards |
| `safety_decay` | 0.02 | 0.0 to 0.08 | a month | monthly erosion of safety practice without investment |
| `revenue_capability_beta` | 0.5 | 0.1 to 1.2 | elasticity | revenue growth per unit of log capability growth |
| `revenue_reach_beta` | 0.8 | 0.1 to 2.0 | elasticity | revenue relative to the frictionless, full trust reach path, to this power |
| `reach_speed` | 0.08 | 0.02 to 0.3 | a month | speed at which reach closes on its capability and trust determined ceiling |
| `growth_value_weight` | 3.0 | 0.5 to 8.0 | years of revenue | how a firm values a year of extra growth against a year of cost |
| `relocation_cost` | 0.08 | 0.0 to 0.5 | share of moved revenue | one off cost of moving a unit of activity offshore |
| `offshore_revenue_haircut` | 0.12 | 0.0 to 0.5 | share | revenue lost per unit of activity offshore (talent, customers, latency) |
| `firm_risk_aversion` | 0.6 | 0.0 to 2.0 | multiple | weight on the variance of expected liability in the firm's choice |
| `firm_optimism` | 0.7 | 0.3 to 1.0 | multiple | the share of its true incident rate a firm believes when it plans |
| `audit_rate` | 0.5 | 0.05 to 1.0 | a month at full capacity | probability a firm in scope is audited in a month at capacity 1 |
| `insurance_loading` | 0.25 | 0.0 to 1.0 | share | premium above expected liability charged by insurers under a mandate |
| `safe_harbour_shield` | 0.7 | 0.0 to 1.0 | share | share of liability a compliant firm avoids under a safe harbour |
| `moratorium_research_slowdown` | 0.5 | 0.0 to 1.0 | share | share of capability growth lost by a firm in scope while a moratorium holds |
| `enforcement_response` | 0.25 | 0.05 to 1.0 | a month | speed at which enforcement intensity follows public pressure |
| `trust_recovery` | 0.05 | 0.01 to 0.2 | a month | monthly recovery of public trust towards 1 |
| `trust_harm_sensitivity` | 0.04 | 0.0 to 0.3 | per log $bn | fall in trust per unit of log monetised harm in a month |
| `news_memory` | 0.75 | 0.3 to 0.95 | a month | persistence of the news pressure index |
| `news_reporting_boost` | 0.35 | 0.0 to 1.0 | share | extra salience of incidents when reporting is mandatory |
| `market_vol` | 0.045 | 0.01 to 0.12 | a month | volatility of the common market factor |
| `sentiment_persistence` | 0.85 | 0.5 to 0.98 | a month | persistence of the price's non fundamental component |
| `news_price_impact` | 0.06 | 0.0 to 0.3 | per unit of pressure | price impact of a unit of news pressure on an exposed firm |
| `incident_jump` | 0.5 | 0.0 to 2.0 | multiple | own incident price jump per log unit of harm relative to revenue |
| `contagion` | 0.3 | 0.0 to 1.0 | share | share of an own incident jump felt by the rest of the sector |
| `announcement_impact` | 0.9 | 0.0 to 3.0 | multiple | price reaction at announcement per unit of expected compliance cost over earnings |
| `chip_demand_coupling` | 0.6 | 0.0 to 1.5 | elasticity | chip and cloud revenue growth per unit of model developers' capability growth |
| `open_weights_diffusion` | 0.1 | 0.0 to 0.8 | share | capability spillover from published weights to the rest of the economy |

## 8. Assurance

**Tornado.** Each declared value judgement is set to the low and the high end of its range and the
preferred option's net social value and the best option recomputed. Valuation parameters are
recomputed from the stored paths; parameters that change behaviour or hazard are re simulated on the
first `variant_paths` paths with the main run's seed and *paired* with the main run:
`adjusted[n] = main_full[n] + (resim[n] − main_first_paths[n])`, so a parameter with no effect leaves the
figure exactly at the reference and the bars sit on the headline scale.

| Assumption | Low | High | How |
|---|---|---|---|
| `harm_valuation_multiplier` | 0.5 | 2.0 | recomputed from the stored paths |
| `discount_rate` | 0.01 | 0.07 | recomputed from the stored paths |
| `consumer_surplus_base_bn` | 150.0 | 600.0 | recomputed from the stored paths |
| `productivity_base_bn` | 200.0 | 800.0 | recomputed from the stored paths |
| `compliance_deadweight_share` | 0.4 | 1.0 | recomputed from the stored paths |
| `leakage_value_share` | 0.1 | 0.7 | recomputed from the stored paths |
| `labour_adjustment_bn` | 0.0 | 5.0 | recomputed from the stored paths |
| `catastrophe_prior_monthly` | 0.0005 | 0.005 | re simulated on common random numbers |
| `catastrophe_harm_bn` | 150.0 | 1200.0 | re simulated on common random numbers |
| `hazard_safety_elasticity` | 1.4 | 3.0 | re simulated on common random numbers |
| `offshore_laxity` | 0.2 | 1.2 | re simulated on common random numbers |
| `safety_substitution` | 0.3 | 1.0 | re simulated on common random numbers |
| `cs_elasticity` | 0.3 | 1.0 | recomputed from the stored paths |
| `trust_elasticity` | 0.2 | 1.0 | recomputed from the stored paths |
| `domestic_ownership_share` | 0.3 | 0.9 | recomputed from the stored paths |

**Structural variants.** The battery under alternative model structures, paired the same way:

| Variant | What changes |
|---|---|
| `myopic_firms` | firms plan six months ahead instead of twelve |
| `forward_looking_firms` | firms plan two years ahead |
| `weak_regulator` | the regulator has half the stated capacity |
| `strong_safety_effect` | safety practice cuts incidents faster |
| `weak_safety_effect` | safety practice cuts incidents more slowly |
| `lax_offshore` | offshore activity is twice as hazardous as at home |
| `heavy_tail` | the catastrophic tail is two and a half times more likely |

**Red team.** Each instrument re run with firms following a gaming strategy, on the main run's paths and
seed, so the honest value equals the headline figure exactly:

| Strategy | What changes |
|---|---|
| `threshold_splitting` | models are split so the regulator sees capability 20% below the real level |
| `compliance_theatre` | mandated safety spend is reported but not spent; evaluations are gamed |
| `maximal_relocation` | firms are more mobile and moving is cheaper than assumed |
| `use_case_relabelling` | deployments are relabelled into lower tiers, avoiding 60% of tier costs |

**Analogue event study.** For an uploaded monthly price series with a past regulatory announcement, the
cumulative abnormal return over months 1 to 6 after the event (market model estimated on the 24 months
before it) is compared with the model's early reaction interval for each instrument.

## 9. Governance

Nothing simulates before a named approver on the register signs the battery off at Gate 1, and nothing
is released before the same kind of approver releases the briefing at Gate 2; both functions are
mandatory, the approver must differ from the preparer, and either gate can be refused with reasons.
Every step is appended to a hash chained, HMAC signed ledger with a replay check. Before Gate 2 an
independent critic recomputes every headline figure from the stored paths, checks the accounting
identity, the rankings, the preferred option, the tornado's reference, the ledger chain, and vets
every number in the briefing against the artefacts (with unit suffixes). The evidence pack carries the
artefacts, the battery, the assumptions, the briefing, the critic's report, the transparency record,
the ledger and a `VERIFY.md` so a second authority can recompute the result. In dev mode
(`PSL_DEV_MODE=on`) `Developer1` and `Developer2` are accepted at the gates and every record says so.

## 10. What the Lab is not

It is not a forecast of real companies or of real events. The archetypes are not companies; mapping
them onto real firms requires calibration through the data desk and is labelled as such in the
briefing. The harm side rests on declared hazard and tail assumptions, and the tornado shows which of
them would change the answer; the briefing names them. The Lab informs a policy choice; it does not
make one.
