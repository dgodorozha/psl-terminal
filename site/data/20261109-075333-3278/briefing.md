# Policy Scenario Lab briefing

**Run** 20261109-075333-3278. **Question.** Would a six month moratorium above the compute threshold or coordinated frontier licensing reduce expected harm more over three years, keeping the gross social cost under $100bn?

**How it was read.** 4 instruments against the status quo (instruments named in the question); horizon 3 years; 60 Monte Carlo paths per instrument on common random numbers, seed 7; constraints: gross social cost at most $100bn.

## The answer

**Preferred option: Coordinated frontier licensing.** Expected net social value $18.8bn [-$15.1bn, $10.7bn] over 3 years, the highest of the instruments that satisfy the constraints; it is the best option in 90% of bootstrap resamples of the paths (90% with the constraints lifted). It avoids $22.1bn of expected harm (25% of the baseline's), and the industry's net value change is -$129bn [-$275bn, $42bn].

The interval on the preferred option's value spans zero: the sign depends on the path. The probability that it is positive is 28%.

## The options compared

| Instrument | Net social value, $bn | Harm avoided, $bn | Gross social cost, $bn | Industry value change, $bn | P(catastrophe) | Headline score | P(best) | Within constraints |
|---|---|---|---|---|---|---|---|---|
| Coordinated frontier licensing (preferred) | 18.8 [-15.1, 10.7] | 22.1 | 9.1 | -129 | 12% | +0.013 | 90% | yes |
| Compute threshold reporting | 2.4 [-1.1, 9.6] | 0.4 | 1.1 | 117 | 17% | +0.016 | 10% | yes |
| Frontier licensing | -38.0 [-58.2, -42.2] | 7.8 | 49.0 | -297 | 15% | +0.013 | 0% | yes |
| Six month moratorium above the threshold | -47.6 [-77.3, -50.0] | 17.4 | 67.3 | -25 | 13% | -0.011 | 0% | yes |

The status quo carries an expected harm of $89.8bn over the horizon, 6.2 reportable incidents a year, a 92% probability of at least one major incident and a 17% probability of a catastrophic one.

## What Coordinated frontier licensing buys and costs

| Component | $bn, present value | 10th to 90th percentile |
|---|---|---|
| Harm avoided | 22.1 | [0.0, 3.3] |
| Consumer surplus | -2.3 | [-3.5, -1.6] |
| Output uplift (adoption) | 2.4 | [-7.9, 11.1] |
| Resident producer surplus | -1.9 | [-2.2, -1.5] |
| Compliance (resource cost) | -1.2 | [-1.2, -1.2] |
| Enforcement budget (cost) | -0.3 | [-0.3, -0.3] |
| Activity lost offshore (cost) | 0.0 | [0.0, 0.0] |
| Relocation cost | 0.0 | [0.0, 0.0] |
| Labour adjustment (cost) | 0.0 | [0.0, 0.0] |
| **Net social value** | **18.8** | [-15.1, 10.7] |

The mean harm avoided ($22.1bn) sits above its 90th percentile ($3.3bn): 96% of it comes from the tenth of paths with the largest values, the paths in which a catastrophic incident is averted; the median is $0.8bn. The expected value is carried by the tail, which is the nature of the problem and not an error.

The same holds for the net social value: mean $18.8bn against a 90th percentile of $10.7bn and a median of -$7.8bn.

Gross social cost $9.1bn [$4.7bn, $15.2bn], that is 0.41 of cost per dollar of harm avoided.
Transfers, excluded from the net: fines $22.3bn, liability payouts $0.0bn, insurance premiums $0.0bn.

## Who gains and who pays

| Party | Change, $bn present value |
|---|---|
| abroad (relocated activity) | 0.0 |
| consumers | -2.3 |
| firms (shareholders) | -128.7 |
| public (harm not suffered) | 22.1 |
| taxpayers | 22.0 |
| wider economy (output) | 2.4 |
| workers | 0.0 |

Shareholder value counts the earnings change over the horizon plus the discounted change in market value at its end; it is a valuation effect and only its resident operating profit share enters the social ledger.

## Safety forecast

| Instrument | Incidents a year | Major a year | P(major) | P(catastrophe) | Expected harm, $bn | Safety level at end | Frontier capability at end | Trust at end |
|---|---|---|---|---|---|---|---|---|
| Status quo (voluntary commitments) | 6.2 | 0.86 | 92% | 17% | 89.8 | 0.65 | 2.59 | 0.84 |
| Compute threshold reporting | 6.0 | 0.81 | 92% | 17% | 89.4 | 0.65 | 2.59 | 0.85 |
| Frontier licensing | 6.1 | 0.86 | 92% | 15% | 82.0 | 0.66 | 2.44 | 0.85 |
| Coordinated frontier licensing | 5.5 | 0.74 | 92% | 12% | 67.7 | 0.67 | 2.38 | 0.87 |
| Six month moratorium above the threshold | 5.7 | 0.77 | 92% | 13% | 72.3 | 0.65 | 2.43 | 0.86 |

Under Coordinated frontier licensing the economy runs 5.5 reportable incidents a year (misuse 3.0, accidents 1.8, systemic 0.7), against 6.2 at the status quo; the expected catastrophic harm is $59.2bn against $80.3bn. Firms end with 13% of R&D on safety, 0% of activity offshore and 25% compliance.

## The news environment to expect

| Instrument | Minor incident headlines a year | Major incident headlines a year | Enforcement headlines a year | Relocation headlines a year | Peak pressure | P(hearing) | Early tone |
|---|---|---|---|---|---|---|---|
| Status quo (voluntary commitments) | 5.2 | 0.81 | 2.17 | 0.00 | 0.23 | 0% | -0.10 |
| Compute threshold reporting | 5.1 | 0.76 | 0.00 | 0.00 | 0.23 | 0% | +0.06 |
| Frontier licensing | 5.2 | 0.81 | 1.55 | 4.00 | 0.31 | 0% | +0.06 |
| Coordinated frontier licensing | 4.6 | 0.70 | 1.26 | 0.00 | 0.24 | 0% | +0.06 |
| Six month moratorium above the threshold | 4.8 | 0.72 | 0.00 | 0.00 | 0.23 | 0% | -0.10 |

On the representative path the wire under Coordinated frontier licensing ran 77 headlines over the horizon, 35% of them negative. The three worst: "Users report credential harvesting attack on Consumer AI platform services; $13m at stake" (CIVIC, 2028-10); "Automated phishing wave traced to Frontier Lab (closed weights) system, regulator told; $65m in losses" (CIVIC, 2029-12); "Frontier Lab (open weights) slides 23% as investors weigh regulatory costs" (WIRE, 2027-01).

## The market

Industry net value change under Coordinated frontier licensing: -$129bn [-$275bn, $42bn] on a starting value of $6.51tn; the probability the industry gains is 13%. The value weighted index reacts -0.4% against the baseline over the first six months and -1.1% by the end of the horizon.

| Firm | Sector | Value change, $bn | 10th to 90th | P(gain) | Earnings change, $bn | Offshore at end | Safety share at end |
|---|---|---|---|---|---|---|---|
| Frontier Lab (closed weights) | Frontier lab | -64.5 | [-86.4, -43.4] | 0% | -1.6 | 0% | 25% |
| Frontier Lab (open weights) | Open weights | -20.6 | [-28.7, -11.7] | 0% | -0.6 | 0% | 25% |
| Hyperscaler cloud | hyperscaler | -70.0 | [-115.6, -10.8] | 5% | -23.0 | 0% | 10% |
| Chip designer | chips | -61.0 | [-104.2, -20.0] | 8% | -2.0 | 0% | 10% |
| Enterprise software | Enterprise software | 38.2 | [19.7, 67.0] | 100% | 0.1 | 0% | 10% |
| Consumer AI platform | Consumer AI | 30.1 | [9.4, 54.3] | 98% | 0.0 | 0% | 10% |
| Autonomy and robotics | autonomy | 9.7 | [4.0, 18.1] | 100% | 0.0 | 0% | 10% |
| AI start up cohort | startups | 9.3 | [3.3, 15.9] | 100% | 0.0 | 0% | 5% |

| Sector | Value change, $bn | Starting value, $bn |
|---|---|---|
| Frontier lab | -64.5 | 277 |
| Open weights | -20.6 | 63 |
| hyperscaler | -70.0 | 1,938 |
| chips | -61.0 | 2,544 |
| Enterprise software | 38.2 | 945 |
| Consumer AI | 30.1 | 519 |
| autonomy | 9.7 | 123 |
| startups | 9.3 | 95 |

The firms are synthetic archetypes of the AI value chain, not companies; the figures are the model's and carry its assumptions.

## The decision gap

Ranked by how they look in the first six months (the price reaction and the early tone of the wire), the order is Compute threshold reporting, Frontier licensing, Coordinated frontier licensing, Six month moratorium above the threshold. Ranked by net social value over 3 years it is Coordinated frontier licensing, Compute threshold reporting, Frontier licensing, Six month moratorium above the threshold. Kendall tau between the two is +0.33; the decision gap ((1 - tau) / 2) is 0.33, and the two orders invert in 0% of resamples. The best option is stable in 90% of resamples.

## How sure we are

**Tornado.** The preferred option's expected value is $18.8bn. Moving each value judgement to its low and high value, one at a time (the best option is judged among the instruments that satisfy the question's constraints):

| Assumption | Default | Low value | Value at low, $bn | High value | Value at high, $bn | Best option changes |
|---|---|---|---|---|---|---|
| Catastrophe harm bn | 400.00 | 150.00 | 9.1 | 1,200.00 | 49.6 | no |
| Harm valuation multiplier | 1.00 | 0.50 | 7.7 | 2.00 | 40.8 | no |
| Catastrophe prior monthly | 0.0020 | 0.0005 | 32.8 | 0.0050 | 17.3 | no |
| Trust elasticity | 0.50 | 0.20 | 14.2 | 1.00 | 25.5 | no |
| Hazard safety elasticity | 1.80 | 1.40 | 20.2 | 3.00 | 13.3 | no |
| Consumer surplus base bn | 250.00 | 150.00 | 19.7 | 600.00 | 15.5 | no |
| Cs elasticity | 0.60 | 0.30 | 20.1 | 1.00 | 16.3 | no |
| Productivity base bn | 400.00 | 200.00 | 17.6 | 800.00 | 21.1 | no |
| Discount rate | 0.0300 | 0.0100 | 19.6 | 0.0700 | 17.2 | no |
| Domestic ownership share | 0.60 | 0.30 | 19.7 | 0.90 | 17.8 | no |
| Compliance deadweight share | 0.70 | 0.40 | 19.3 | 1.00 | 18.2 | no |
| Safety substitution | 0.60 | 0.30 | 18.3 | 1.00 | 18.7 | no |
| Labour adjustment bn | 2.00 | 0.0000 | 18.7 | 5.00 | 18.8 | no |
| Leakage value share | 0.35 | 0.10 | 18.8 | 0.70 | 18.8 | no |
| Offshore laxity | 0.60 | 0.20 | 18.8 | 1.20 | 18.8 | no |

No single assumption at the edge of its range changes the decision.

**Structural variants.** Under 7 alternative model structures the preferred option is best in 6 and in the top two in 7:

| Variant | What changes | Best option | Preferred option's rank | Its value, $bn |
|---|---|---|---|---|
| Myopic firms | firms plan six months ahead instead of twelve | Coordinated frontier licensing | 1 | 4.6 |
| Forward looking firms | firms plan two years ahead | Compute threshold reporting | 2 | -27.6 |
| Weak regulator | the regulator has half the stated capacity | Coordinated frontier licensing | 1 | 9.2 |
| Strong safety effect | safety practice cuts incidents faster | Coordinated frontier licensing | 1 | 13.1 |
| Weak safety effect | safety practice cuts incidents more slowly | Coordinated frontier licensing | 1 | 4.8 |
| Lax offshore | offshore activity is twice as hazardous as at home | Coordinated frontier licensing | 1 | 18.8 |
| Heavy tail | the catastrophic tail is two and a half times more likely | Coordinated frontier licensing | 1 | 17.3 |

**Red team.** Firms game each instrument four ways; the instrument's value under its worst strategy:

| Instrument | Honest value, $bn | Worst strategy | Value when gamed, $bn | Harm avoided when gamed, $bn | Loss to gaming, $bn |
|---|---|---|---|---|---|
| Coordinated frontier licensing | 18.8 | Compliance theatre | 1.0 | 7.7 | 17.8 |
| Compute threshold reporting | 2.4 | Compliance theatre | 0.0 | 0.1 | 2.4 |
| Six month moratorium above the threshold | -47.6 | Compliance theatre | -48.9 | 17.3 | 1.3 |
| Frontier licensing | -38.0 | Maximal relocation | -80.1 | -0.4 | 42.1 |

The most robust instrument to gaming is Coordinated frontier licensing. Strategies: Compliance theatre: mandated safety spend is reported but not spent; evaluations are gamed; Maximal relocation: firms are more mobile and moving is cheaper than assumed; Threshold splitting: models are split so the regulator sees capability 20% below the real level; Use case relabelling: deployments are relabelled into lower tiers, avoiding 60% of tier costs.

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

Indicators to watch, with the model's expectation under Coordinated frontier licensing: reportable incidents a year (4.0 to 7.0); the share of activity offshore (0% at the horizon); the news pressure index (peak 0.24, a hearing in 0% of paths); the industry's value against the baseline (-1.1% at the horizon). Revisit the decision if incidents run above the interval for two quarters, if relocation exceeds the forecast, or if any of the tail assumptions can be estimated from data.

## Gates, provenance and reproduction

**Gate 1 (battery)**: approved by Developer2, Developer2 (dev mode (PSL_DEV_MODE=on); not a regulated person) at 2026-11-09T07:53:33.
**Gate 2 (release)**: approved by Developer2, Developer2 (dev mode (PSL_DEV_MODE=on); not a regulated person) at 2026-11-09T07:53:41.
**Critic**: 28 of 28 checks passed before release.
Battery hash `92ffca47a8662573eaa0fd18612a7559e695b6ede69a8132649d760d6058833c`; code fingerprint `80b85a3b2d46204ed8528af2d06d292e6f4c002c1ba14a7236e1350d13582fe9`; PSL 1.0.0, numpy 2.5.3; profile demo; 6.4 seconds. Reproduce with `python -m psl.orchestrator --battery battery.json`.
