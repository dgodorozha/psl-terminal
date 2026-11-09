# Policy Scenario Lab briefing

**Run** 20261109-083921-bb5b. **Question.** Compare strict liability with liability under a safe harbour and mandatory third party evaluations over the next five years; the technology sector's net loss must stay below $300bn and the probability of a catastrophic incident must fall by at least a quarter.

**How it was read.** 3 instruments against the status quo (instruments named in the question); horizon 5 years; 60 Monte Carlo paths per instrument on common random numbers, seed 7; constraints: industry loss at most $300bn.

## The answer

**Preferred option: Mandatory third party evaluation.** Expected net social value $24.5bn [-$43.5bn, $58.7bn] over 5 years, the highest of the instruments that satisfy the constraints; it is the best option in 100% of bootstrap resamples of the paths (41% with the constraints lifted). It avoids $17.7bn of expected harm (16% of the baseline's), and the industry's net value change is -$96bn [-$259bn, $74bn].
With the constraints lifted, Liability with a safe harbour scores higher ($27.1bn) but fails: industry loss $426bn exceeds the $300bn limit.

The interval on the preferred option's value spans zero: the sign depends on the path. The probability that it is positive is 37%.

## The options compared

| Instrument | Net social value, $bn | Harm avoided, $bn | Gross social cost, $bn | Industry value change, $bn | P(catastrophe) | Headline score | P(best) | Within constraints |
|---|---|---|---|---|---|---|---|---|
| Liability with a safe harbour | 27.1 [-25.6, 63.0] | 17.4 | 16.5 | -426 | 18% | -0.001 | 59% | no |
| Mandatory third party evaluation (preferred) | 24.5 [-43.5, 58.7] | 17.7 | 19.7 | -96 | 18% | +0.011 | 41% | yes |
| Strict liability | -4.6 [-19.9, 23.6] | 1.0 | 11.3 | -1,303 | 20% | +0.003 | 0% | no |

The status quo carries an expected harm of $111.7bn over the horizon, 9.2 reportable incidents a year, a 100% probability of at least one major incident and a 20% probability of a catastrophic one.

## What Mandatory third party evaluation buys and costs

| Component | $bn, present value | 10th to 90th percentile |
|---|---|---|
| Harm avoided | 17.7 | [0.2, 5.6] |
| Consumer surplus | -4.1 | [-10.7, 1.8] |
| Output uplift (adoption) | 19.5 | [-22.4, 59.8] |
| Resident producer surplus | -4.9 | [-6.9, -3.1] |
| Compliance (resource cost) | -3.3 | [-3.4, -3.3] |
| Enforcement budget (cost) | -0.4 | [-0.4, -0.3] |
| Activity lost offshore (cost) | 0.0 | [0.0, 0.0] |
| Relocation cost | 0.0 | [0.0, 0.0] |
| Labour adjustment (cost) | 0.0 | [-0.1, 0.1] |
| **Net social value** | **24.5** | [-43.5, 58.7] |

The mean harm avoided ($17.7bn) sits above its 90th percentile ($5.6bn): 91% of it comes from the tenth of paths with the largest values, the paths in which a catastrophic incident is averted; the median is $2.0bn. The expected value is carried by the tail, which is the nature of the problem and not an error.

Gross social cost $19.7bn [$6.8bn, $43.8bn], that is 1.11 of cost per dollar of harm avoided.
Transfers, excluded from the net: fines $25.6bn, liability payouts $0.0bn, insurance premiums $0.0bn.

## Who gains and who pays

| Party | Change, $bn present value |
|---|---|
| abroad (relocated activity) | 0.0 |
| consumers | -4.1 |
| firms (shareholders) | -96.4 |
| public (harm not suffered) | 17.7 |
| taxpayers | 25.2 |
| wider economy (output) | 19.5 |
| workers | 0.0 |

Shareholder value counts the earnings change over the horizon plus the discounted change in market value at its end; it is a valuation effect and only its resident operating profit share enters the social ledger.

## Safety forecast

| Instrument | Incidents a year | Major a year | P(major) | P(catastrophe) | Expected harm, $bn | Safety level at end | Frontier capability at end | Trust at end |
|---|---|---|---|---|---|---|---|---|
| Status quo (voluntary commitments) | 9.2 | 1.34 | 100% | 20% | 111.7 | 0.66 | 4.36 | 0.72 |
| Mandatory third party evaluation | 8.1 | 1.20 | 100% | 18% | 94.0 | 0.66 | 4.11 | 0.75 |
| Strict liability | 8.7 | 1.28 | 100% | 20% | 110.7 | 0.68 | 4.21 | 0.74 |
| Liability with a safe harbour | 7.9 | 1.17 | 98% | 18% | 94.3 | 0.68 | 4.30 | 0.76 |

Under Mandatory third party evaluation the economy runs 8.1 reportable incidents a year (misuse 4.3, accidents 2.6, systemic 1.1), against 9.2 at the status quo; the expected catastrophic harm is $72.5bn against $88.1bn. Firms end with 10% of R&D on safety, 0% of activity offshore and 50% compliance.

## The news environment to expect

| Instrument | Minor incident headlines a year | Major incident headlines a year | Enforcement headlines a year | Relocation headlines a year | Peak pressure | P(hearing) | Early tone |
|---|---|---|---|---|---|---|---|
| Status quo (voluntary commitments) | 7.5 | 1.30 | 2.34 | 0.00 | 0.32 | 0% | -0.14 |
| Mandatory third party evaluation | 6.7 | 1.16 | 1.38 | 0.00 | 0.35 | 2% | +0.00 |
| Strict liability | 7.1 | 1.24 | 6.90 | 0.00 | 0.43 | 33% | +0.00 |
| Liability with a safe harbour | 6.5 | 1.13 | 0.00 | 0.00 | 0.31 | 0% | +0.00 |

On the representative path the wire under Mandatory third party evaluation ran 148 headlines over the horizon, 35% of them negative. The three worst: "Frontier Lab (closed weights) faces $4.2bn fallout after liquidity cascade" (WIRE, 2027-01); "MAJOR: Enterprise software system behind flawed credit decisions; damages reach $1.1bn" (WIRE, 2027-11); "MAJOR: Autonomy and robotics system behind flawed credit decisions; damages reach $1.0bn" (WIRE, 2028-10).

## The market

Industry net value change under Mandatory third party evaluation: -$96bn [-$259bn, $74bn] on a starting value of $6.51tn; the probability the industry gains is 22%. The value weighted index reacts -0.4% against the baseline over the first six months and -0.5% by the end of the horizon.

| Firm | Sector | Value change, $bn | 10th to 90th | P(gain) | Earnings change, $bn | Offshore at end | Safety share at end |
|---|---|---|---|---|---|---|---|
| Frontier Lab (closed weights) | Frontier lab | -33.2 | [-48.0, -19.4] | 0% | -1.9 | 0% | 10% |
| Frontier Lab (open weights) | Open weights | -10.9 | [-16.3, -6.6] | 0% | -0.7 | 0% | 10% |
| Hyperscaler cloud | hyperscaler | -59.2 | [-99.9, -11.1] | 3% | -27.3 | 0% | 10% |
| Chip designer | chips | -24.4 | [-79.1, 43.0] | 30% | -5.6 | 0% | 10% |
| Enterprise software | Enterprise software | 60.7 | [38.2, 91.3] | 100% | 0.5 | 0% | 10% |
| Consumer AI platform | Consumer AI | -35.2 | [-53.1, -17.6] | 0% | -2.6 | 0% | 10% |
| Autonomy and robotics | autonomy | -16.5 | [-24.0, -9.0] | 0% | -1.0 | 0% | 10% |
| AI start up cohort | startups | 22.2 | [12.4, 33.9] | 100% | 0.0 | 0% | 10% |

| Sector | Value change, $bn | Starting value, $bn |
|---|---|---|
| Frontier lab | -33.2 | 277 |
| Open weights | -10.9 | 63 |
| hyperscaler | -59.2 | 1,938 |
| chips | -24.4 | 2,544 |
| Enterprise software | 60.7 | 945 |
| Consumer AI | -35.2 | 519 |
| autonomy | -16.5 | 123 |
| startups | 22.2 | 95 |

The firms are synthetic archetypes of the AI value chain, not companies; the figures are the model's and carry its assumptions.

## The decision gap

Ranked by how they look in the first six months (the price reaction and the early tone of the wire), the order is Mandatory third party evaluation, Strict liability, Liability with a safe harbour. Ranked by net social value over 5 years it is Liability with a safe harbour, Mandatory third party evaluation, Strict liability. Kendall tau between the two is -0.33; the decision gap ((1 - tau) / 2) is 0.67, and the two orders invert in 59% of resamples. The best option is stable in 59% of resamples.

## How sure we are

**Tornado.** The preferred option's expected value is $24.5bn. Moving each value judgement to its low and high value, one at a time (the best option is judged among the instruments that satisfy the question's constraints):

| Assumption | Default | Low value | Value at low, $bn | High value | Value at high, $bn | Best option changes |
|---|---|---|---|---|---|---|
| Catastrophe prior monthly | 0.0020 | 0.0005 | 7.4 | 0.0050 | 62.4 | no |
| Trust elasticity | 0.50 | 0.20 | 7.9 | 1.00 | 47.8 | no |
| Productivity base bn | 400.00 | 200.00 | 14.8 | 800.00 | 44.1 | no |
| Catastrophe harm bn | 400.00 | 150.00 | 17.3 | 1,200.00 | 45.9 | no |
| Harm valuation multiplier | 1.00 | 0.50 | 15.7 | 2.00 | 42.3 | no |
| Safety substitution | 0.60 | 0.30 | 24.1 | 1.00 | 10.8 | no |
| Hazard safety elasticity | 1.80 | 1.40 | 26.8 | 3.00 | 16.4 | no |
| Consumer surplus base bn | 250.00 | 150.00 | 26.2 | 600.00 | 18.8 | no |
| Cs elasticity | 0.60 | 0.30 | 26.8 | 1.00 | 20.4 | no |
| Discount rate | 0.0300 | 0.0100 | 26.4 | 0.0700 | 21.4 | no |
| Domestic ownership share | 0.60 | 0.30 | 27.0 | 0.90 | 22.1 | no |
| Compliance deadweight share | 0.70 | 0.40 | 26.0 | 1.00 | 23.1 | no |
| Labour adjustment bn | 2.00 | 0.0000 | 24.6 | 5.00 | 24.5 | no |
| Leakage value share | 0.35 | 0.10 | 24.5 | 0.70 | 24.5 | no |
| Offshore laxity | 0.60 | 0.20 | 24.5 | 1.20 | 24.5 | no |

No single assumption at the edge of its range changes the decision.

**Structural variants.** Under 7 alternative model structures the preferred option is best in 7 and in the top two in 6:

| Variant | What changes | Best option | Preferred option's rank | Its value, $bn |
|---|---|---|---|---|
| Myopic firms | firms plan six months ahead instead of twelve | Mandatory third party evaluation | 2 | 3.7 |
| Forward looking firms | firms plan two years ahead | Mandatory third party evaluation | 3 | -71.6 |
| Weak regulator | the regulator has half the stated capacity | Mandatory third party evaluation | 2 | 3.5 |
| Strong safety effect | safety practice cuts incidents faster | Mandatory third party evaluation | 2 | -10.1 |
| Weak safety effect | safety practice cuts incidents more slowly | Mandatory third party evaluation | 2 | 50.1 |
| Lax offshore | offshore activity is twice as hazardous as at home | Mandatory third party evaluation | 2 | 24.5 |
| Heavy tail | the catastrophic tail is two and a half times more likely | Mandatory third party evaluation | 1 | 62.4 |

**Red team.** Firms game each instrument four ways; the instrument's value under its worst strategy:

| Instrument | Honest value, $bn | Worst strategy | Value when gamed, $bn | Harm avoided when gamed, $bn | Loss to gaming, $bn |
|---|---|---|---|---|---|
| Liability with a safe harbour | 27.1 | Compliance theatre | 2.4 | -2.4 | 24.8 |
| Strict liability | -4.6 | Threshold splitting | -4.6 | 1.0 | 0.0 |
| Mandatory third party evaluation | 24.5 | Maximal relocation | -124.1 | -1.3 | 148.6 |

The most robust instrument to gaming is Liability with a safe harbour. Strategies: Compliance theatre: mandated safety spend is reported but not spent; evaluations are gamed; Maximal relocation: firms are more mobile and moving is cheaper than assumed; Threshold splitting: models are split so the regulator sees capability 20% below the real level; Use case relabelling: deployments are relabelled into lower tiers, avoiding 60% of tier costs.

**Analogue.** No event study was uploaded; the market module's early reaction has not been compared with a past regulatory event on this run.

## Assumptions

Every value judgement and structural parameter, hash `b85a6faf3ec1a97fe657b8e7da96af2f3039a4d315258cb17a31e425cec538f1`:

| Assumption | Value | Unit | Meaning |
|---|---|---|---|
| Discount rate | 0.0300 | a year | social discount rate applied to every monthly flow |
| Harm valuation multiplier | 1.00 | multiple | scales the monetised harm of incidents; 1.0 takes the engine's damages at face value |
| Consumer surplus base bn | 250.00 | $bn a year | annual consumer surplus from AI services at the starting level of capability and reach |
| Cs elasticity | 0.60 | elasticity | proportional change in consumer surplus per proportional change in the AI service index |
| Productivity base bn | 400.00 | $bn a year | annual output uplift attributable to AI adoption at the starting service index |
| Productivity elasticity | 0.80 | elasticity | proportional change in the output uplift per proportional change in the service index |
| Trust elasticity | 0.50 | elasticity | proportional change in realised adoption benefits per proportional change in public trust |
| Compliance deadweight share | 0.70 | share | share of compliance spend that is a real resource cost rather than a transfer |
| Enforcement cost bn | 0.40 | $bn a year per unit of capacity | public budget consumed by one unit of enforcement capacity |
| Leakage value share | 0.35 | share | domestic value added lost per dollar of revenue whose activity moves offshore |
| Labour adjustment bn | 2.00 | $bn per index point | short run adjustment cost per point of growth in the AI service index (displacement, retraining) |
| Domestic ownership share | 0.60 | share | share of the firms' operating profit that accrues to residents and counts in national welfare |
| Hazard base misuse | 0.0800 | a month per firm | monthly rate of a reportable misuse incident for a firm at capability 1, full reach and no safety practice |
| Hazard base accident | 0.0500 | a month per firm | the same for accidents and failures |
| Hazard base systemic | 0.0200 | a month per firm | the same for systemic incidents (markets, infrastructure, information) |
| Hazard capability elasticity | 1.30 | elasticity | incident rate scales with capability to this power |
| Hazard safety elasticity | 1.80 | per unit of safety level | incident rate falls as exp(-elasticity x safety level) |
| Hazard reach elasticity | 1.00 | elasticity | incident rate scales with deployment reach to this power |
| Offshore laxity | 0.60 | multiple | extra incident rate on activity moved offshore, relative to home |
| Severity misuse median bn | 0.15 | $bn | median monetised harm of a misuse incident |
| Severity accident median bn | 0.30 | $bn | median monetised harm of an accident |
| Severity systemic median bn | 1.00 | $bn | median monetised harm of a systemic incident |
| Severity sigma | 1.10 | log scale | lognormal dispersion of incident harm (heavy tail) |
| Major incident bn | 1.00 | $bn | harm above which an incident counts as major |
| Catastrophe prior monthly | 0.0020 | a month per firm | monthly probability of a catastrophic incident for a firm above critical capability with no safety practice |
| Catastrophe capability | 1.60 | capability index | capability above which the catastrophic tail is live |
| Catastrophe harm bn | 400.00 | $bn | median monetised harm of a catastrophic incident |
| Unsafe release share | 0.35 | share | share of the incident rate attributable to releases an evaluation could catch |
| Capability growth | 0.0230 | a month | monthly log growth of the capability index when all R&D goes to capability (a doubling in about 30 months) |
| Safety learning | 0.0800 | a month | monthly gain in safety practice at saturation; the gain is a x share/(share + 0.1), diminishing in the share |
| Growth fade months | 30.00 | months | time constant over which a firm's growth fades towards the long run rate |
| Safety substitution | 0.60 | share | share of safety spend that displaces capability R&D (the rest is additional budget or spills over) |
| Export control chip loss | 0.10 | a year | annual revenue growth lost by the chip sector under full export controls |
| Long run growth | 0.0600 | a year | the growth rate firms fade towards |
| Safety decay | 0.0200 | a month | monthly erosion of safety practice without investment |
| Revenue capability beta | 0.50 | elasticity | revenue growth per unit of log capability growth |
| Revenue reach beta | 0.80 | elasticity | revenue relative to the frictionless, full trust reach path, to this power |
| Reach speed | 0.0800 | a month | speed at which reach closes on its capability and trust determined ceiling |
| Growth value weight | 3.00 | years of revenue | how a firm values a year of extra growth against a year of cost |
| Relocation cost | 0.0800 | share of moved revenue | one off cost of moving a unit of activity offshore |
| Offshore revenue haircut | 0.12 | share | revenue lost per unit of activity offshore (talent, customers, latency) |
| Firm risk aversion | 0.60 | multiple | weight on the variance of expected liability in the firm's choice |
| Firm optimism | 0.70 | multiple | the share of its true incident rate a firm believes when it plans |
| Audit rate | 0.50 | a month at full capacity | probability a firm in scope is audited in a month at capacity 1 |
| Insurance loading | 0.25 | share | premium above expected liability charged by insurers under a mandate |
| Safe harbour shield | 0.70 | share | share of liability a compliant firm avoids under a safe harbour |
| Moratorium research slowdown | 0.50 | share | share of capability growth lost by a firm in scope while a moratorium holds |
| Enforcement response | 0.25 | a month | speed at which enforcement intensity follows public pressure |
| Trust recovery | 0.0500 | a month | monthly recovery of public trust towards 1 |
| Trust harm sensitivity | 0.0400 | per log $bn | fall in trust per unit of log monetised harm in a month |
| News memory | 0.75 | a month | persistence of the news pressure index |
| News reporting boost | 0.35 | share | extra salience of incidents when reporting is mandatory |
| Market vol | 0.0450 | a month | volatility of the common market factor |
| Sentiment persistence | 0.85 | a month | persistence of the price's non fundamental component |
| News price impact | 0.0600 | per unit of pressure | price impact of a unit of news pressure on an exposed firm |
| Incident jump | 0.50 | multiple | own incident price jump per log unit of harm relative to revenue |
| contagion | 0.30 | share | share of an own incident jump felt by the rest of the sector |
| Announcement impact | 0.90 | multiple | price reaction at announcement per unit of expected compliance cost over earnings |
| Chip demand coupling | 0.60 | elasticity | chip and cloud revenue growth per unit of model developers' capability growth |
| Open weights diffusion | 0.10 | share | capability spillover from published weights to the rest of the economy |

## Monitoring and revisiting

Indicators to watch, with the model's expectation under Mandatory third party evaluation: reportable incidents a year (6.6 to 9.6); the share of activity offshore (0% at the horizon); the news pressure index (peak 0.35, a hearing in 2% of paths); the industry's value against the baseline (-0.5% at the horizon). Revisit the decision if incidents run above the interval for two quarters, if relocation exceeds the forecast, or if any of the tail assumptions can be estimated from data.

## Gates, provenance and reproduction

**Gate 1 (battery)**: approved at 2026-11-09T08:39:21 in a public demonstration, without a sign off identity; inside an authority a named approver on the register takes this gate.
**Gate 2 (release)**: approved at 2026-11-09T08:39:31 in a public demonstration, without a sign off identity; inside an authority a named approver on the register takes this gate.
**Critic**: 28 of 28 checks passed before release.
Battery hash `a4217449df380aaf02a9bd0f1843ba3d9a6cfaecc779f487e3a218af021ce530`; code fingerprint `48be8b6dddb389b8196b0cc5b8204291bf0552cf55efb6314e2713a9e5bd1e02`; PSL 1.0.1, numpy 2.5.3; profile demo; 8.0 seconds. Reproduce with `python -m psl.orchestrator --battery battery.json`.
