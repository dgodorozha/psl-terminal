# Policy Scenario Lab briefing

**Run** 20261116-060426-e27e. **Question.** Would a six month moratorium above the compute threshold or coordinated frontier licensing reduce expected harm more over three years, keeping the gross social cost under $100bn?

**How it was read.** 2 instruments and the status quo (instruments named in the question); horizon 3 years; 120 Monte Carlo paths per alternative, every alternative on the same random numbers, seed 10; constraints: gross social cost at most $100bn.

**What this is.** A comparison of alternatives inside a synthetic model of the AI economy under declared assumptions. The figures are conditional on that model: they are scenario evaluations, not forecasts validated against data, and the preferred option is the model's answer to the question, to be examined, not an established recommendation. Confronted with 11 published benchmarks, mostly analogues from other regulation, the model is not contradicted by 9 and fails or strains on equity return when a horizontal regime becomes enforceable; share of the insurance loading used up by underwriting and administration. 5 of its 15 mechanisms have no benchmark at all, and no mechanism is estimated from data.

## The answer

**No tested instrument improves on the status quo.** The status quo scores zero by construction and is the preferred alternative. The best instrument within the constraints is Coordinated frontier licensing, with an expected net social value of -$1.0bn (95% confidence interval -$2.6bn to $0.9bn) over 3 years: not above zero, and with a confidence interval that includes zero, so on these paths it cannot be told apart from doing nothing and there is no case for adopting it under the model's own objective.

Across the simulated outcomes the net social value of Coordinated frontier licensing runs from -$15.0bn (10th percentile) to $8.2bn (90th percentile) and is positive on 19% of paths; that range is how different one path can be from another, not the uncertainty of the expected value, which the confidence interval gives. The confidence interval includes zero: on these paths the expected value is not distinguishable from the status quo.

**How firm the decision is on these paths.** The status quo is the best feasible alternative in 84% of bootstrap resamples of the paths, with feasibility re assessed in each. That share is ranking stability under the model and its assumptions; it is not the probability that the option is best in the world. 

It cannot be told apart from Coordinated frontier licensing: the simultaneous 95% interval of the paired difference in expected net social value includes zero for it.

Every precision target was met at 120 paths.

## The options compared

| Alternative | Expected net social value, $bn | 95% confidence interval | Outcomes, 10th to 90th percentile | Harm avoided, $bn | Gross social cost, $bn | Industry value change, $bn | P(catastrophe) | Headline score | Within constraints | Share of resamples within | Ranking stability |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Status quo (voluntary commitments) (preferred) | 0.0 | [0.0, 0.0] | [0.0, 0.0] | 0.0 | 0.0 | 0 | 5.5% | +0.000 | yes | 100% | 84% |
| Coordinated frontier licensing | -1.0 | [-2.6, 0.9] | [-15.0, 8.2] | 6.6 | 7.6 | -159 | 4.2% | +0.012 | yes | 100% | 16% |
| Six month moratorium above the threshold | -65.8 | [-67.5, -63.7] | [-77.5, -57.1] | 4.2 | 70.2 | -44 | 4.7% | -0.010 | yes | 100% | 0% |

The status quo carries an expected harm of $33.7bn over the horizon, 6.1 reportable incidents a year, a 86% probability of at least one major incident and a 5.5% probability of a catastrophic one (95% confidence interval 5.4% to 5.5%; a catastrophe was drawn on 5 of 120 paths). The probability is estimated from the hazard each path accumulates, not from the count of paths on which the event happened to be drawn, which is why it is far more precise than that count.

**The status quo against each other feasible alternative** (paired on the same paths):

| Against | Difference in expected net social value, $bn | 95% confidence interval | Simultaneous 95% interval | Told apart |
|---|---|---|---|---|
| Coordinated frontier licensing | 1.0 | [-0.9, 2.6] | [-1.1, 3.1] | no |
| Six month moratorium above the threshold | 65.8 | [63.7, 67.5] | [63.7, 67.9] | yes |

## What Coordinated frontier licensing buys and costs

| Component | Expected value, $bn present value | 95% confidence interval | Outcomes, 10th to 90th percentile |
|---|---|---|---|
| Harm avoided | 6.6 | [6.6, 6.6] | [0.0, 2.2] |
| Consumer surplus | -2.8 | [-3.0, -2.6] | [-3.5, -1.4] |
| Output uplift (adoption) | -1.3 | [-2.7, 0.3] | [-7.8, 10.4] |
| Resident producer surplus | -2.0 | [-2.1, -1.9] | [-2.2, -1.6] |
| Compliance (resource cost) | -1.2 | [-1.2, -1.2] | [-1.2, -1.2] |
| Enforcement budget (cost) | -0.3 | [-0.3, -0.3] | [-0.3, -0.3] |
| Activity lost offshore (cost) | 0.0 | [0.0, 0.0] | [0.0, 0.0] |
| Relocation cost | 0.0 | [0.0, 0.0] | [0.0, 0.0] |
| Labour adjustment (cost) | 0.0 | [0.0, 0.0] | [0.0, 0.0] |
| Insurance administration (resource cost) | 0.0 | [0.0, 0.0] | [0.0, 0.0] |
| **Net social value** | **-1.0** | [-2.6, 0.9] | [-15.0, 8.2] |

Expected harm avoided is estimated from the harm expected in each month given the state the path has reached (probability times mean severity), which has the same expectation as the harm drawn and far less variance. The outcomes column uses the harm as drawn: its median is $0.5bn and the average of the draws is $0.9bn; 45% of that average comes from the tenth of paths with the largest values, the paths on which a catastrophic incident is averted.

Gross social cost $7.6bn (the expected component changes that are costs, never netted against savings), gross benefit $6.6bn; their difference is the net social value. Gross cost per dollar of expected harm avoided: 1.15.
Transfers, excluded from the net: fines $23.7bn, liability paid by firms $0.0bn, insurance premiums $0.0bn, claims paid to victims $0.0bn.

## Who gains and who pays

| Party | Change, $bn present value |
|---|---|
| Compliance providers (rents) | 0.5 |
| Consumers | -2.8 |
| Domestic workers and tax base (activity moved offshore) | 0.0 |
| Insurers | 0.0 |
| Public at risk (harm not suffered, compensation received) | 6.6 |
| Resident owners of AI firms | -17.3 |
| Sectors that adopt AI (output) | -1.3 |
| Taxpayers (fines less enforcement) | 23.4 |
| Workers (adjustment) | 0.0 |
| **Total** | **9.2** |

The table follows the money as well as the real effects, so it sums to the net social value (-$1.0bn) plus what non resident owners finance of the firms' payments ($10.2bn), a memorandum item the net social value does not count. Standing is residents: real resources used in the jurisdiction count in full, income counts for residents, and transfers are excluded whoever pays.

## Safety forecast

| Alternative | Incidents a year | Major a year | P(major) | P(catastrophe) | 95% confidence interval | Expected harm, $bn | Safety level at end | Frontier capability at end | Trust at end |
|---|---|---|---|---|---|---|---|---|---|
| Status quo (voluntary commitments) | 6.1 | 0.79 | 86% | 5.5% | 5.4% to 5.5% | 33.7 | 0.65 | 2.59 | 0.86 |
| Coordinated frontier licensing | 5.5 | 0.71 | 84% | 4.2% | 4.1% to 4.3% | 27.1 | 0.67 | 2.38 | 0.88 |
| Six month moratorium above the threshold | 5.6 | 0.73 | 85% | 4.7% | 4.6% to 4.7% | 29.4 | 0.65 | 2.43 | 0.87 |

Under Coordinated frontier licensing the economy runs 5.5 reportable incidents a year (misuse 2.9, accidents 1.8, systemic 0.8), against 6.1 at the status quo; the expected catastrophic harm is $18.3bn against $24.0bn. Firms end with 13% of R&D on safety, 0% of activity offshore and 25% compliance. A major incident is a single incident at or above the threshold; catastrophes are counted apart.

## The news environment to expect

| Alternative | Minor incident headlines a year | Major incident headlines a year | Enforcement headlines a year | Relocation headlines a year | Peak pressure | P(hearing) | Early tone |
|---|---|---|---|---|---|---|---|
| Status quo (voluntary commitments) | 5.3 | 0.79 | 2.32 | 0.00 | 0.23 | 0% | -0.08 |
| Coordinated frontier licensing | 4.7 | 0.71 | 1.34 | 0.00 | 0.25 | 0% | +0.08 |
| Six month moratorium above the threshold | 4.9 | 0.73 | 0.00 | 0.00 | 0.23 | 0% | -0.07 |

On the representative path the wire under Coordinated frontier licensing ran 77 headlines over the horizon, 31% of them negative. The three worst: "Regulators open inquiry into Hyperscaler cloud after $1.3bn autonomous system failure" (WIRE, 2028-09); "Users report autonomous system failure on Frontier Lab (open weights) services; $144m at stake" (CIVIC, 2028-01); "Users report disinformation operation on Frontier Lab (closed weights) services; $80m at stake" (CIVIC, 2029-04).

## The market

Industry net value change under Coordinated frontier licensing: -$159bn (95% confidence interval -$175bn to -$139bn) on a starting value of $6.38tn; across outcomes -$290bn to -$35bn, and the industry gains on 7% of paths. The value weighted index reacts -0.3% against the status quo over the first six months and -1.5% by the end of the horizon. Every index is measured from the same valuation, the firms as they stand before any instrument is announced, so an instrument's immediate effect on fundamentals shows in the first month.

| Firm | Sector | Expected value change, $bn | 95% confidence interval | Outcomes, 10th to 90th | P(gain) | Earnings change, $bn | Offshore at end | Safety share at end |
|---|---|---|---|---|---|---|---|---|
| Frontier Lab (closed weights) | Frontier lab | -64.7 | [-67.5, -61.7] | [-85.0, -46.6] | 0% | -1.6 | 0% | 25% |
| Frontier Lab (open weights) | Open weights | -22.2 | [-23.4, -21.0] | [-31.2, -14.8] | 0% | -0.6 | 0% | 25% |
| Hyperscaler cloud | hyperscaler | -84.1 | [-92.9, -75.5] | [-138.0, -32.9] | 1% | -24.5 | 0% | 10% |
| Chip designer | chips | -68.9 | [-74.6, -62.6] | [-115.4, -28.6] | 2% | -2.1 | 0% | 10% |
| Enterprise software | Enterprise software | 34.0 | [31.3, 36.8] | [16.1, 54.7] | 99% | 0.1 | 0% | 10% |
| Consumer AI platform | Consumer AI | 29.0 | [26.2, 31.5] | [10.3, 49.0] | 98% | 0.0 | 0% | 10% |
| Autonomy and robotics | autonomy | 9.8 | [8.8, 10.7] | [3.8, 16.1] | 99% | 0.0 | 0% | 10% |
| AI start up cohort | startups | 8.3 | [7.6, 9.0] | [3.2, 14.4] | 98% | 0.0 | 0% | 5% |

| Sector | Expected value change, $bn | Starting value, $bn |
|---|---|---|
| Frontier lab | -64.7 | 267 |
| Open weights | -22.2 | 60 |
| hyperscaler | -84.1 | 1,910 |
| chips | -68.9 | 2,492 |
| Enterprise software | 34.0 | 935 |
| Consumer AI | 29.0 | 507 |
| autonomy | 9.8 | 119 |
| startups | 8.3 | 91 |

The firms are synthetic archetypes of the AI value chain, not companies; the figures are the model's and carry its assumptions. Shareholder value is a market metric and a constraint; it is not part of the net social value.

## The decision gap

Ranked by how they look in the first six months (the price reaction and the early tone of the wire), the instruments are Coordinated frontier licensing, Six month moratorium above the threshold. Ranked by expected net social value over 3 years they are Coordinated frontier licensing, Six month moratorium above the threshold. Kendall tau b between the two is +1.00; the decision gap ((1 - tau) / 2) is 0.00, and the two orders invert in 0% of resamples.

## How sure we are

**Monte Carlo error.** Every expected value above carries the 95% bootstrap confidence interval of its mean over 500 resamples of the paths, paired across alternatives. The run followed its sampling plan: 120 paths, stopping when the preferred alternative was resolved against every other feasible one to within $5.0bn and the catastrophe probabilities to within 3%, or at the ceiling. The intervals are not adjusted for those sequential looks.

Convergence of the running estimate (the first paths of the run are exactly what a smaller run on this seed reports):

| Paths | Decision | Expected net social value of Coordinated frontier licensing, $bn | Standard error | P(catastrophe), status quo |
|---|---|---|---|---|
| 15 | the status quo | -1.6 | 1.29 | 5.1% |
| 30 | the status quo | -0.5 | 1.42 | 5.3% |
| 60 | the status quo | -0.9 | 1.15 | 5.4% |
| 120 | the status quo | -1.0 | 0.91 | 5.5% |

The decision is the same over the last doubling of the paths, and the final estimate lies inside every earlier interval.

Split into 4 independent batches of 30 paths, the run gives the same decision in 4 of them (the status quo, the status quo, the status quo, the status quo).

**Parameters, one at a time.** Each of the 68 declared assumptions was moved to the low and the high end of its plausible range, the decision re made under each (feasibility re assessed, the status quo an alternative). Coordinated frontier licensing is worth -$1.0bn at the run's values. The 15 largest swings:

| Assumption | Run's value | Low | Value at low, $bn | Decision at low | High | Value at high, $bn | Decision at high |
|---|---|---|---|---|---|---|---|
| Audit rate | 0.50 | 0.30 | -1.2 | the status quo | 0.80 | -63.8 | the status quo |
| Revenue response to capability | 0.50 | 0.30 | -54.1 | the status quo | 0.80 | -1.8 | the status quo |
| Weight firms put on growth | 3.00 | 1.50 | -50.0 | the status quo | 5.00 | -3.2 | the status quo |
| Correlation of catastrophes across firms | 0.30 | 0.0000 | 43.1 | Coordinated frontier licensing | 0.60 | -0.9 | the status quo |
| Critical capability | 1.60 | 1.30 | -1.4 | the status quo | 2.00 | 33.8 | Coordinated frontier licensing |
| Capability growth | 0.0230 | 0.0150 | -29.1 | the status quo | 0.0350 | -3.1 | the status quo |
| Safety elasticity of incidents | 1.80 | 1.40 | -9.3 | the status quo | 3.00 | 8.1 | Coordinated frontier licensing |
| Trust sensitivity to harm | 0.0400 | 0.0200 | -6.5 | the status quo | 0.0800 | 9.0 | Coordinated frontier licensing |
| Median harm of a catastrophe | 400.00 | 150.00 | -4.7 | the status quo | 1,200.00 | 10.6 | Coordinated frontier licensing |
| Monthly catastrophe probability | 0.0020 | 0.0005 | -4.3 | the status quo | 0.0050 | 6.7 | Coordinated frontier licensing |
| Safety decay | 0.0200 | 0.0100 | -1.3 | the status quo | 0.0400 | -11.8 | the status quo |
| Harm valuation multiplier | 1.00 | 0.50 | -4.3 | the status quo | 2.00 | 5.6 | Coordinated frontier licensing |
| Capability elasticity of incidents | 1.30 | 0.90 | 1.1 | Coordinated frontier licensing | 1.80 | -8.3 | the status quo |
| Share of incidents an evaluation could catch | 0.35 | 0.20 | -8.8 | the status quo | 0.50 | -0.4 | the status quo |
| Median harm of an accident | 0.30 | 0.15 | -4.4 | the status quo | 0.60 | 3.6 | Coordinated frontier licensing |

The decision changes at an end of the range of 26 of the 68 assumptions; the 12 with the largest swings are Correlation of catastrophes across firms, Critical capability, Safety elasticity of incidents, Trust sensitivity to harm, Median harm of a catastrophe, Monthly catastrophe probability, Harm valuation multiplier, Capability elasticity of incidents, Median harm of an accident, Trust elasticity of adoption benefits, Consumer surplus base, Output uplift elasticity (the screen in the artefacts lists all 26). The sign of the focus option's value is not robust across the screen. For 0 of them the cause is feasibility: the status quo stops satisfying a constraint under the alternative (on the central estimate: gross social cost $0bn within the $100bn budget (satisfied in 100% of resamples)); for 26 another alternative within the constraints overtakes it. Each re simulated assumption ran on the first 4 paths, paired with the main run: 30 of the 68 swings exceed twice their Monte Carlo standard error, and a change of decision inside that error is a warning to look, not a finding.

**Parameters, all together.** 64 joint draws of every assumption over its plausible range (correlated where they plausibly move together). Under that parameter uncertainty:

| Alternative | Mean net social value, $bn | 5th to 95th percentile over the draws | Share of draws it is the decision | Share of draws within constraints | Share within constraints and above the status quo | Expected regret where within constraints, $bn |
|---|---|---|---|---|---|---|
| The status quo | 0.0 | [0.0, 0.0] | 53% | 100% | 100% | 9.2 |
| Coordinated frontier licensing | -3.4 | [-48.7, 39.2] | 47% | 98% | 47% | 11.4 |
| Six month moratorium above the threshold | -65.1 | [-132.7, -17.3] | 0% | 80% | 2% | 60.6 |

Regret is how far an alternative falls short of the best alternative within the constraints in the same draw, averaged over the draws in which it is itself within them; it is read beside the share of draws in which it is, because choosing an alternative where it breaks a constraint is not a cost in $bn. Among the alternatives within the constraints in at least 90% of the draws, the status quo has the lowest expected regret.

The ranges are declared judgements, a prior over the assumptions and not a posterior estimated from data. No assumption's rank correlation with the decision margin passes a 10% false discovery rate over the 68 assumptions at this number of draws.

**Which assumptions carry the variance.** A Sobol decomposition over the 5 assumptions with the largest swings (448 evaluations), for the value of Coordinated frontier licensing and for its margin over the best alternative. Shares with interactions (total order), with the 90% interval the size of the design allows:

| Assumption | Share of the value's variance, with interactions | 90% interval | Share of the margin's variance, with interactions | 90% interval | Alone (first order), margin |
|---|---|---|---|---|---|
| Weight firms put on growth | 55% | 40% to 74% | 55% | 36% to 76% | 31% |
| Revenue response to capability | 43% | 26% to 67% | 43% | 23% to 68% | 6% |
| Audit rate | 25% | 9% to 42% | 25% | 11% to 41% | 0% |
| Correlation of catastrophes across firms | 16% | 10% to 23% | 16% | 11% to 23% | 16% |
| Critical capability | 0% | 0% to 0% | 0% | 0% to 0% | 1% |

The intervals are wide (half width 13% on average for the margin): the output is heavy tailed in these assumptions, which compound, so a design of this size ranks groups of assumptions and does not order neighbours. Shares with interactions add to more than one when the assumptions interact, as these do: first order shares sum to 53% of the margin's variance.

**Model structure.** Under 8 alternative model structures Coordinated frontier licensing remains the decision in 6 and stays within the constraints and above the status quo in 2:

| Variant | What changes | Decision | Focus option's rank among instruments | Its value, $bn | Within constraints |
|---|---|---|---|---|---|
| Myopic firms | firms plan six months ahead instead of twelve | the status quo | 1 | -3.9 | yes |
| Forward looking firms | firms plan two years ahead | the status quo | 2 | -65.9 | yes |
| Weak regulator | the regulator has half the stated capacity | the status quo | 1 | -1.6 | yes |
| Strong safety effect | safety practice cuts incidents faster | the status quo | 1 | -7.8 | yes |
| Weak safety effect | safety practice cuts incidents more slowly | Coordinated frontier licensing | 1 | 3.1 | yes |
| Lax offshore | offshore activity is twice as hazardous as at home | the status quo | 1 | -1.0 | yes |
| Heavy tail | the catastrophic tail is two and a half times more likely | Coordinated frontier licensing | 1 | 9.9 | yes |
| Systemic catastrophes | catastrophic failures are strongly correlated across firms | the status quo | 1 | -0.8 | yes |

**Gaming.** Firms game each instrument four ways; the instrument under its worst strategy, and whether it is then still within the constraints and above the status quo:

| Instrument | Honest value, $bn | Worst strategy | Value when gamed, $bn | Harm avoided when gamed, $bn | Loss to gaming, $bn | Acceptable under every strategy |
|---|---|---|---|---|---|---|
| Coordinated frontier licensing | -1.0 | Compliance theatre | -7.6 | 1.2 | 6.6 | no |
| Six month moratorium above the threshold | -65.8 | Compliance theatre | -67.1 | 3.6 | 1.3 | no |

When every instrument is gamed at its worst, the best choice is the status quo. Strategies: Compliance theatre: mandated safety spend is reported but not spent; evaluations are gamed; Maximal relocation: firms are more mobile and moving is cheaper than assumed; Threshold splitting: models are split so the regulator sees capability 20% below the real level; Use case relabelling: deployments are relabelled into lower tiers, avoiding 60% of tier costs.

**Robustly acceptable.** No instrument is within the constraints and above the status quo on the central estimate, in at least 90% of the joint draws, in every structural variant and under every gaming strategy.

**Validation against published evidence.** The model was confronted with 11 published benchmarks that bear on 10 of its 15 mechanisms. 3 of those mechanisms have a benchmark measured on AI itself; the others rest on analogues from other regulation and other technologies, each compared with an allowance for that distance. At the central assumptions the model is not contradicted by 9, is in tension with 1 (Share of the insurance loading used up by underwriting and administration) and is contradicted by 1 (Equity return when a horizontal regime becomes enforceable). Even the closest tenth of the draws of the assumptions miss Equity return when a horizontal regime becomes enforceable by more than 2 standard deviations: that is a failure of the model's form and not of a parameter value, so it is reported and left out of the weighting below. No benchmark bears on 5 mechanisms: severity, catastrophic tail, safety practice, evaluation, news.

| Benchmark | Kind | Observed (allowance, one sd) | Model at the central assumptions | z | Verdict | Model across the declared ranges, 5th to 95th | Predicted with it held out |
|---|---|---|---|---|---|---|---|
| Annual growth of recorded AI incidents | direct | 56% (sd 26%) | 42% | -0.5 | not contradicted | 26% to 69% | 37% (z -0.7) |
| Annual change in public trust in AI and AI companies | direct | -5.1% (sd 2.3%) | -4.8% | +0.1 | not contradicted | -22.4% to -3.9% | -12.5% (z -1.1) |
| Share of a fall in trust recovered about nine months after a salient incident | analogue | 20% (sd 35%) | 37% | +0.5 | not contradicted | 30% to 56% | 39% (z +0.5) |
| Compliance cost of a high risk regime as a share of development spending in scope | official | 10.8% (sd 6.9%) | 12.4% | +0.2 | not contradicted | 8.9% to 13.7% | 12.5% (z +0.3) |
| Effect of a horizontal compliance regime on the profits of firms in scope | analogue | -3.3% (sd 3.9%) | -7.2% | -1.0 | not contradicted | -8.6% to -6.1% | -7.1% (z -1.0) |
| Equity return when a horizontal regime becomes enforceable | analogue | -0.9% (sd 1.0%) | -4.8% | -3.9 | contradicted; a failure of form, left out of the weights | -5.9% to -3.6% | left out of the weights |
| Equity return of a firm when a regulatory fine is announced | analogue | -0.7% (sd 1.0%) | -0.6% | +0.2 | not contradicted | -2.0% to +1.0% | -1.1% (z -0.2) |
| Equity return of a firm when a serious incident becomes public | analogue | -1.1% (sd 1.1%) | -2.1% | -0.8 | not contradicted | -5.7% to +0.7% | -3.0% (z -0.7) |
| Share of regulated activity displaced abroad by a unilateral regime | analogue | 14.0% (sd 8.6%) | 24.5% | +1.2 | not contradicted | 0.0% to 24.7% | 9.9% (z -0.3) |
| Premium above expected claims in liability insurance | analogue | 31% (sd 15%) | 25% | -0.4 | not contradicted | 16% to 43% | 30% (z -0.1) |
| Share of the insurance loading used up by underwriting and administration | analogue | 107% (sd 25%) | 50% | -2.3 | in tension | 33% to 67% | 50% (z -2.1) |

The allowance is the benchmark's own standard error combined with a declared allowance for the distance between the setting it was measured in and the model's; z is the gap between model and observation in those units, with the Monte Carlo error of the model's value added. Not contradicted: within two; in tension: two to three; contradicted: beyond three. A benchmark is predicted with it held out from the draws weighted by all the others.

Weighting the 64 joint draws of the assumptions by how well each reproduces the 10 benchmarks it can be compared with leaves an effective 8 draws. In the weighted draws the decision is the status quo in 79% (unweighted 53%); Coordinated frontier licensing in 21% (unweighted 47%). 73% of the draws are ruled out by no benchmark at 3 standard deviations. Coordinated frontier licensing is within the constraints and above the status quo in 21% of the weighted draws (47% unweighted). Fewer than 20 effective draws: the weighted shares are indicative only on this budget. The benchmarks bear on 18 of the 68 assumptions drawn; they move most Resource share of the insurance loading (+0.9 sd), Trust sensitivity to harm (-0.7 sd), Capability growth (-0.6 sd), Trust recovery (-0.6 sd), Median harm of a misuse incident (-0.5 sd).

| Assumption the benchmarks bear on | Value on this run | Mean of the draws | Weighted mean | Shift, in sd of the draws | Spread kept | Through |
|---|---|---|---|---|---|---|
| Resource share of the insurance loading | 0.5 | 0.5 | 0.5895 | +0.88 | 97% | insurance resource share |
| Trust sensitivity to harm | 0.04 | 0.04668 | 0.03811 | -0.68 | 66% | trust trend, incident growth |
| Capability growth | 0.023 | 0.02435 | 0.02201 | -0.57 | 86% | profit effect, incident growth, trust trend |
| Trust recovery | 0.05 | 0.05997 | 0.05162 | -0.56 | 96% | trust recovery |
| Median harm of a misuse incident | 0.15 | 0.1767 | 0.1534 | -0.50 | 67% | trust trend |
| Median harm of an accident | 0.3 | 0.3508 | 0.3059 | -0.48 | 75% | incident return |
| Relocation cost | 0.08 | 0.0934 | 0.1046 | +0.44 | 88% | leakage share |
| Safety elasticity of incidents | 1.8 | 2.067 | 2.207 | +0.41 | 92% | trust trend |
| Firm optimism about incidents | 0.7 | 0.7005 | 0.7339 | +0.40 | 85% | incident return |
| Median harm of a systemic incident | 1 | 1.167 | 1.057 | -0.35 | 65% | incident return |

Weighting by benchmarks is a posterior given the allowances declared for each benchmark, not a measurement: most of the evidence is an analogue, and a wide allowance makes a benchmark easy to pass and uninformative. What the benchmarks do not reach is listed with the reasons; in particular nothing here identifies the elasticity of realised adoption to trust.

**Validation against an observed event.** No price series was uploaded on this run, so the market's early reaction was not compared with an event of the authority's own.

No mechanism of the model is estimated from data. The benchmarks above show where its declared assumptions sit against what has been measured elsewhere; the mechanism register lists, for each of the 15 mechanisms, the evidence that would test it. Common random numbers make the comparison between alternatives precise inside the model; they do not make the model true.

## Assumptions

Every value judgement and behavioural parameter, hash `c6c928eedba23618356e89d5a97435ef127d1f3cdffa587947b837c966b1e125`, with the plausible range the screen and the joint draw move it over:

| Assumption | Value | Plausible range | Unit | Meaning |
|---|---|---|---|---|
| Social discount rate | 0.0300 | 0.0100 to 0.0700 | a year | social discount rate applied to every monthly flow |
| Harm valuation multiplier | 1.00 | 0.50 to 2.00 | multiple | scales the monetised harm of incidents; 1.0 takes the engine's damages at face value |
| Consumer surplus base | 250.00 | 150.00 to 600.00 | $bn a year | annual consumer surplus from AI services at the starting level of capability and reach |
| Consumer surplus elasticity | 0.60 | 0.30 to 1.00 | elasticity | proportional change in consumer surplus per proportional change in the AI service index |
| Output uplift base | 400.00 | 200.00 to 800.00 | $bn a year | annual output uplift attributable to AI adoption at the starting service index |
| Output uplift elasticity | 0.80 | 0.50 to 1.10 | elasticity | proportional change in the output uplift per proportional change in the service index |
| Trust elasticity of adoption benefits | 0.50 | 0.20 to 1.00 | elasticity | proportional change in realised adoption benefits per proportional change in public trust |
| Overlap of the output uplift with other benefits | 0.00 | 0.00 to 0.50 | share | share of the output uplift already counted as consumer surplus or as the AI firms' own profit, removed from the output uplift; 0 takes the three benefit components as defined, without overlap |
| Resource share of compliance spend | 0.70 | 0.40 to 1.00 | share | share of compliance spend that is a real resource cost rather than a transfer |
| Enforcement cost | 0.40 | 0.20 to 0.80 | $bn a year per unit of capacity | public budget consumed by one unit of enforcement capacity |
| Value lost per dollar moved offshore | 0.35 | 0.10 to 0.70 | share | domestic value added lost per dollar of revenue whose activity moves offshore |
| Labour adjustment cost | 2.00 | 0.00 to 5.00 | $bn per index point | short run adjustment cost per point of growth in the AI service index (displacement, retraining) |
| Resident ownership share | 0.60 | 0.30 to 0.90 | share | share of the firms' operating profit that accrues to residents and counts in national welfare |
| Resource share of the insurance loading | 0.50 | 0.25 to 0.75 | share | share of the insurance loading that is a real resource cost (underwriting, administration) rather than a transfer to insurers |
| Misuse incident rate | 0.0800 | 0.0500 to 0.13 | a month per firm | monthly rate of a reportable misuse incident for a firm at capability 1, full reach and no safety practice |
| Accident rate | 0.0500 | 0.0300 to 0.0800 | a month per firm | the same for accidents and failures |
| Systemic incident rate | 0.0200 | 0.0100 to 0.0400 | a month per firm | the same for systemic incidents (markets, infrastructure, information) |
| Capability elasticity of incidents | 1.30 | 0.90 to 1.80 | elasticity | incident rate scales with capability to this power |
| Safety elasticity of incidents | 1.80 | 1.40 to 3.00 | per unit of safety level | incident rate falls as exp(-elasticity x safety level) |
| Reach elasticity of incidents | 1.00 | 0.70 to 1.40 | elasticity | incident rate scales with deployment reach to this power |
| Offshore laxity | 0.60 | 0.20 to 1.20 | multiple | extra incident rate on activity moved offshore, relative to home |
| Median harm of a misuse incident | 0.15 | 0.0800 to 0.30 | $bn | median monetised harm of a misuse incident |
| Median harm of an accident | 0.30 | 0.15 to 0.60 | $bn | median monetised harm of an accident |
| Median harm of a systemic incident | 1.00 | 0.50 to 2.00 | $bn | median monetised harm of a systemic incident |
| Dispersion of incident harm | 1.10 | 0.80 to 1.40 | log scale | lognormal dispersion of incident harm (heavy tail) |
| Major incident threshold | 1.00 | 0.50 to 2.00 | $bn | harm above which an incident counts as major |
| Monthly catastrophe probability | 0.0020 | 0.0005 to 0.0050 | a month per firm | monthly probability of a catastrophic incident for a firm above critical capability with no safety practice |
| Critical capability | 1.60 | 1.30 to 2.00 | capability index | capability above which the catastrophic tail is live |
| Median harm of a catastrophe | 400.00 | 150.00 to 1,200.00 | $bn | median monetised harm of a catastrophic incident |
| Share of incidents an evaluation could catch | 0.35 | 0.20 to 0.50 | share | share of the incident rate attributable to releases an evaluation could catch |
| Dispersion of catastrophic harm | 0.50 | 0.25 to 0.90 | log scale | lognormal dispersion of catastrophic harm around its median |
| Correlation of catastrophes across firms | 0.30 | 0.00 to 0.60 | correlation | correlation of catastrophic failures across firms within a month (one factor Gaussian copula): shared models, components and vulnerabilities; 0 makes the firms' catastrophes independent given the state |
| Misuse multiplier for open weights | 1.30 | 1.10 to 1.80 | multiple | misuse rate of a developer that publishes weights, relative to one that does not |
| Capability growth | 0.0230 | 0.0150 to 0.0350 | a month | monthly log growth of the capability index when all R&D goes to capability (a doubling in about 30 months) |
| Safety learning rate | 0.0800 | 0.0500 to 0.12 | a month | monthly gain in safety practice at saturation; the gain is a x share/(share + 0.1), diminishing in the share |
| Growth fade time | 30.00 | 18.00 to 48.00 | months | time constant over which a firm's growth fades towards the long run rate |
| Safety spend that displaces capability R&D | 0.60 | 0.30 to 1.00 | share | share of safety spend that displaces capability R&D (the rest is additional budget or spills over) |
| Chip growth lost to export controls | 0.10 | 0.0500 to 0.20 | a year | annual revenue growth lost by the chip sector under full export controls |
| Long run growth | 0.0600 | 0.0300 to 0.10 | a year | the growth rate firms fade towards |
| Safety decay | 0.0200 | 0.0100 to 0.0400 | a month | monthly erosion of safety practice without investment |
| Revenue response to capability | 0.50 | 0.30 to 0.80 | elasticity | revenue growth per unit of log capability growth |
| Revenue response to reach | 0.80 | 0.50 to 1.20 | elasticity | revenue relative to the frictionless, full trust reach path, to this power |
| Reach adjustment speed | 0.0800 | 0.0500 to 0.12 | a month | speed at which reach closes on its capability and trust determined ceiling |
| Weight firms put on growth | 3.00 | 1.50 to 5.00 | years of revenue | how a firm values a year of extra growth against a year of cost |
| Relocation cost | 0.0800 | 0.0400 to 0.16 | share of moved revenue | one off cost of moving a unit of activity offshore |
| Revenue lost offshore | 0.12 | 0.0600 to 0.24 | share | revenue lost per unit of activity offshore (talent, customers, latency) |
| Firm risk aversion | 0.60 | 0.20 to 1.20 | multiple | weight on the variance of expected liability in the firm's choice |
| Firm optimism about incidents | 0.70 | 0.50 to 0.90 | multiple | the share of its true incident rate a firm believes when it plans |
| Audit rate | 0.50 | 0.30 to 0.80 | a month at full capacity | probability a firm in scope is audited in a month at capacity 1 |
| Insurance loading | 0.25 | 0.10 to 0.50 | share | premium above expected liability charged by insurers under a mandate |
| Safe harbour shield | 0.70 | 0.50 to 0.90 | share | share of liability a compliant firm avoids under a safe harbour |
| Research slowdown under a moratorium | 0.50 | 0.30 to 0.70 | share | share of capability growth lost by a firm in scope while a moratorium holds |
| Weight of safety culture | 0.60 | 0.30 to 1.20 | $bn per unit of revenue | value a firm places on a unit gain in safety practice per unit of revenue, multiplied by its culture score |
| Reach ceiling saturation | 1.50 | 1.00 to 2.20 | per unit of capability | speed at which the reach ceiling 1 - exp(-k C) saturates in capability |
| Growth lost to an open weights restriction | 0.10 | 0.0500 to 0.20 | a year | annual revenue growth lost by an open weights developer while publishing is restricted |
| Enforcement response speed | 0.25 | 0.12 to 0.50 | a month | speed at which enforcement intensity follows public pressure |
| Trust recovery | 0.0500 | 0.0300 to 0.10 | a month | monthly recovery of public trust towards 1 |
| Trust sensitivity to harm | 0.0400 | 0.0200 to 0.0800 | per log $bn | fall in trust per unit of log monetised harm in a month |
| News memory | 0.75 | 0.60 to 0.88 | a month | persistence of the news pressure index |
| Salience boost from mandatory reporting | 0.35 | 0.15 to 0.60 | share | extra salience of incidents when reporting is mandatory |
| Market volatility | 0.0450 | 0.0300 to 0.0650 | a month | volatility of the common market factor |
| Sentiment persistence | 0.85 | 0.70 to 0.93 | a month | persistence of the price's non fundamental component |
| Price impact of news pressure | 0.0600 | 0.0300 to 0.12 | per unit of pressure | price impact of a unit of news pressure on an exposed firm |
| Price jump on an own incident | 0.50 | 0.25 to 1.00 | multiple | own incident price jump per log unit of harm relative to revenue |
| Sector contagion | 0.30 | 0.15 to 0.50 | share | share of an own incident jump felt by the rest of the sector |
| Announcement price impact | 0.90 | 0.45 to 1.80 | multiple | price reaction at announcement per unit of expected compliance cost over earnings |
| Chip demand coupling | 0.60 | 0.30 to 0.90 | elasticity | chip and cloud revenue growth per unit of model developers' capability growth |
| Open weights diffusion | 0.10 | 0.0500 to 0.20 | share | capability spillover from published weights to the rest of the economy |

## The evidence the model was confronted with

Each benchmark, the model quantity it is compared with, and its source. The set is part of the battery approved at Gate 1 (evidence hash `c3cb1266d451b3b9`); an authority replaces or extends it with its own data.

- **Annual growth of recorded AI incidents** (direct). Model quantity: the status quo's expected number of incidents in each year of the horizon; the benchmark is compared with the average annual growth of that count. Allowance for the distance from the model: the database is compiled from media reports and its curators attribute an unknown share of the rise to reporting and attention; the model counts incidents at eight firm archetypes, not in the whole economy. Caveat: growth in recorded incidents is joint growth in harms, deployment and attention. Source: Stanford HAI, AI Index Report 2025, chapter 3 (233 incidents in 2024, up 56.4% on 2023) (https://hai-production.s3.amazonaws.com/files/hai_ai-index-report-2025_chapter3_final.pdf); Stanford HAI, AI Index Report 2026, responsible AI (362 incidents in 2025) (https://hai.stanford.edu/ai-index/2026-ai-index-report/responsible-ai).
- **Annual change in public trust in AI and AI companies** (direct). Model quantity: the status quo's trust index at the end of the horizon, as an annual relative change from its starting value. Allowance for the distance from the model: a survey share is compared with the model's trust index, which starts at one and has no survey counterpart. Caveat: the period measured had no AI specific regulation in most of the countries surveyed, which is what the status quo represents; the fall may have causes other than harm. Source: Edelman Trust Barometer 2024, key insights around AI (https://www.edelman.com/sites/g/files/aatuss191/files/2024-03/Trust%20Tech%20Sector%20Top%20Findings.pdf); Pew Research Center, How Americans view AI and its impact on people and society, September 2025 (https://www.pewresearch.org/wp-content/uploads/sites/20/2025/09/PS_2025.9.15_AI-and-its-impact_report.pdf).
- **Share of a fall in trust recovered about nine months after a salient incident** (analogue). Model quantity: with monthly recovery r and no further incident, the share of a fall recovered after nine months is 1 - (1 - r)^9. Allowance for the distance from the model: another technology, and fear of using it is not trust in the firms that build it; the interval between the two surveys is known to within a few months. Caveat: one episode. Source: AAA, Three in four Americans remain afraid of fully self driving vehicles, March 2019 (https://newsroom.aaa.com/2019/03/americans-fear-self-driving-cars-survey); Smart Cities Dive, AAA poll, March 2019 (the 2018 figure and the crashes) (https://www.smartcitiesdive.com/news/aaa-poll-autonomous-vehicles-fear/550766/).
- **Compliance cost of a high risk regime as a share of development spending in scope** (official). Model quantity: under risk tiering, compliance spending over the R&D spending of the firms in scope on the activity in scope, while in force. Allowance for the distance from the model: an ex ante estimate per system built from a standard cost model, which its authors call a theoretical maximum; the model's cost is an instrument parameter applied to revenue in scope. Caveat: the share of systems that are high risk was never estimated by any party to the assessment. Source: European Commission, SWD(2021) 84 final, impact assessment of the AI Act (https://data.consilium.europa.eu/doc/document/ST-8115-2021-ADD-2/en/pdf); Renda et al. (2021), Study to support an impact assessment of regulatory requirements for AI in Europe (https://artificialintelligenceact.eu/wp-content/uploads/2022/06/AIA-COM-Impact-Assessment-3-21-April.pdf).
- **Effect of a horizontal compliance regime on the profits of firms in scope** (analogue). Model quantity: under risk tiering, the industry's earnings against the status quo on the same paths, over the months in force. Allowance for the distance from the model: data protection, not AI; a broad cross section of firms against eight archetypes that are mostly large. Caveat: the estimates differ in sample, outcome and period; the mean of three is a summary, not a pooled estimate. Source: Chen, Frey and Presidente (2022), Privacy regulation and firm performance, Oxford Martin working paper 2022-1 (https://oms-www.files.svdcdn.com/production/downloads/Privacy-Regulation-and-Firm-Performance-Giorgio-WP-Upload-2022-1.pdf); Johnson (2022), Economic research on privacy regulation: lessons from the GDPR and beyond, NBER working paper 30705 (https://www.nber.org/system/files/working_papers/w30705/w30705.pdf).
- **Equity return when a horizontal regime becomes enforceable** (analogue). Model quantity: under risk tiering, the value weighted index's change in the month the instrument takes effect, less the status quo's on the same path. Allowance for the distance from the model: a week against the model's month; most of the cost of a law announced years earlier is in the price before it applies. Caveat: the enforcement date return understates the total cost capitalised. Source: Motoki and Pinto (2024), Journal of Business Finance and Accounting (press summary) (https://www.eurekalert.org/news-releases/1051661).
- **Equity return of a firm when a regulatory fine is announced** (analogue). Model quantity: under risk tiering, a fined firm's log return in the month of the fine less the index's. Allowance for the distance from the model: data protection fines, most of them small against the firm's size; days against the model's month. Caveat: 25 announcements; windows beyond five days are not significant in the source. Source: Ford et al. (2021), The impact of GDPR infringement fines on the market value of firms, ECCWS (https://repository.uel.ac.uk/download/55420e51e0d25c813c8ab1d701f7b6e5093ba609fac84a9d9a3a874cb19e3a0d/689257/The%20Impact%20of%20GDPR%20Infringement%20Fines%20on%20the%20Market%20Value%20of%20Firms.pdf).
- **Equity return of a firm when a serious incident becomes public** (analogue). Model quantity: under the status quo, the log return of a firm in a month with a major incident at that firm, less the index's. Allowance for the distance from the model: data breaches, not AI incidents; three days against the model's month. Caveat: the model's major incident is defined by monetised harm, a breach by the data lost. Source: Kamiya, Kang, Kim, Milidonis and Stulz, What is the impact of successful cyberattacks on target firms? (authors' summary, Harvard Law School Forum on Corporate Governance, March 2018; Journal of Financial Economics 139(3), 2021) (https://corpgov.law.harvard.edu/2018/03/30/what-is-the-impact-of-successful-cyberattacks-on-target-firms/).
- **Share of regulated activity displaced abroad by a unilateral regime** (analogue). Model quantity: under frontier licensing, the revenue of the firms in scope booked offshore in the last year of the horizon, as a share of their revenue. Allowance for the distance from the model: carbon pricing, and mostly ex ante models; AI activity is divisible in some respects (where a model is trained) and not in others (one set of weights). Caveat: for AI regulation leakage is theorised, surveyed and anecdotal, not measured. Source: Branger and Quirion (2014), Ecological Economics 99 (https://econpapers.repec.org/RePEc:hal:journl:hal-01137932).
- **Premium above expected claims in liability insurance** (analogue). Model quantity: the assumption itself: the premium charged above the expected liability under a mandate. Allowance for the distance from the model: all property and casualty lines; cover for AI liability is not an established line. Caveat: an industry average over lines with very different tails. Source: NAIC, U.S. property and casualty and title insurance industries, 2023 full year results (https://content.naic.org/sites/default/files/industry-snapshot-2023-ye.pdf).
- **Share of the insurance loading used up by underwriting and administration** (analogue). Model quantity: the assumption itself: the share of the loading that is a real resource cost and not a transfer to insurers. Allowance for the distance from the model: all property and casualty lines, in two years with an underwriting loss (the share is above one because expenses exceeded the loading). Caveat: the model's range (0.25 to 0.75) treats part of the loading as insurers' margin; in these two years there was none. Source: NAIC, U.S. property and casualty and title insurance industries, 2023 full year results (https://content.naic.org/sites/default/files/industry-snapshot-2023-ye.pdf).

Examined and set aside:

- Meta analysis of trust and intention to use a technology: r = 0.503 (95% interval 0.470 to 0.535, 128 samples, 50,667 respondents) (Kuen, Westmattelmann, Bruckes and Schewe (2023), Electronic Markets 33:61). Bears on adoption and trust (trust elasticity). Not used because it supports the sign of the trust channel and nothing more: a correlation between stated attitudes in studies of online shopping, banking and e-health is not an elasticity of realised adoption to trust, and cannot be turned into one without the dispersion of both. The elasticity stays unidentified.
- The size of the fall in trust after a salient incident (AAA: afraid to ride rose from 63% to 73% after two fatal crashes) (AAA (2019)). Bears on adoption and trust (trust harm sensitivity). Not used because the model moves trust with monetised harm, and two deaths are a small monetised harm: an incident of that size moves the model's trust by less than a tenth of a percent. The episode says trust answers to salience; the model's form cannot show that. Recorded as a limit of the mechanism, not scored, because the survey question is about using a vehicle.
- Estimates of AI's effect on output: total factor productivity up by no more than 0.66% over ten years (Acemoglu); 7% of global GDP over ten years (Goldman Sachs); $2.6 to $4.4 trillion a year (McKinsey) (Acemoglu (2025), Economic Policy 40(121)). Bears on welfare bases (productivity base bn, consumer surplus base bn). Not used because the model declares its benefit bases in $bn a year and declares no size for the jurisdiction's economy, so there is nothing to divide by; and the estimates span an order of magnitude.
- Elicited probabilities of catastrophic harm from AI (expert and forecaster elicitations (no observed frequency exists)). Bears on catastrophic tail. Not used because elicitations, not observations; they define catastrophe differently from the model and have no validation record.
- A loss distribution for AI incidents (AI Incident Database; MIT AI Incident Tracker; OECD AI Incidents Monitor). Bears on severity. Not used because none has been published: the taxonomies exist, the magnitudes are not recorded.
- GDPR and venture investment: monthly EU deals down 26.1% against US ventures (Jia, Jin and Wagman (2021), Marketing Science 40(4)). Bears on revenue growth. Not used because the model has no entry or investment margin to compare it with.

## Monitoring and revisiting

Indicators to watch, with the model's expectation under Coordinated frontier licensing: reportable incidents a year (4.3 to 7.0 across outcomes); the share of activity offshore (0% at the horizon); the news pressure index (peak 0.25, a hearing in 0% of paths); the industry's value against the status quo (-1.5% at the horizon). Revisit the decision if incidents run above that range for two quarters, if relocation exceeds the forecast, or if any of Correlation of catastrophes across firms, Critical capability, Safety elasticity of incidents, Trust sensitivity to harm, Median harm of a catastrophe, Monthly catastrophe probability, Harm valuation multiplier, Capability elasticity of incidents can be estimated from data.

## Gates, provenance and reproduction

**Gate 1 (battery)**: approved at 2026-11-16T06:04:26 in a public demonstration, without a sign off identity; inside an authority a named approver on the register takes this gate.
**Gate 2 (release)**: approved at 2026-11-16T06:04:34 in a public demonstration, without a sign off identity; inside an authority a named approver on the register takes this gate.
**Critic**: 57 of 57 checks passed before release.
Battery hash `1ba4de2d826af14552d72a1a404921c4c3e7382a3cfee557fd98b984457939c2`; code fingerprint `28b530f37f3d12c48a159a7cb59c0eae091feb07e3b7c4b70029b020889c5c84`; PSL 1.2.0, numpy 2.5.3, scipy 1.18.1; profile demo; 5.0 seconds. Reproduce with `python -m psl.orchestrator --battery battery.json`.
