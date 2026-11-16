# Policy Scenario Lab briefing

**Run** 20261116-060409-cc82. **Question.** Compare strict liability with liability under a safe harbour and mandatory third party evaluations over the next five years; the technology sector's net loss must stay below $300bn and the probability of a catastrophe below 14%.

**How it was read.** 3 instruments and the status quo (instruments named in the question); horizon 5 years; 120 Monte Carlo paths per alternative, every alternative on the same random numbers, seed 9; constraints: industry loss at most $300bn; P(catastrophe) at most 14%.

**What this is.** A comparison of alternatives inside a synthetic model of the AI economy under declared assumptions. The figures are conditional on that model: they are scenario evaluations, not forecasts validated against data, and the preferred option is the model's answer to the question, to be examined, not an established recommendation. Confronted with 11 published benchmarks, mostly analogues from other regulation, the model is not contradicted by 9 and fails or strains on equity return when a horizontal regime becomes enforceable; share of the insurance loading used up by underwriting and administration. 5 of its 15 mechanisms have no benchmark at all, and no mechanism is estimated from data.

## The answer

**Preferred option: Mandatory third party evaluation.** Expected net social value $23.2bn (95% confidence interval $12.9bn to $35.0bn) over 5 years, the highest among the alternatives that satisfy the constraints and above the status quo, which scores zero. It avoids $14.2bn of expected harm (15% of the status quo's), and the industry's expected value change is -$41bn (95% confidence interval -$72bn to -$11bn).

Across the simulated outcomes the net social value of Mandatory third party evaluation runs from -$37.2bn (10th percentile) to $78.3bn (90th percentile) and is positive on 41% of paths; that range is how different one path can be from another, not the uncertainty of the expected value, which the confidence interval gives. The confidence interval excludes zero.

**How firm the decision is on these paths.** Mandatory third party evaluation is the best feasible alternative in 100% of bootstrap resamples of the paths, with feasibility re assessed in each. That share is ranking stability under the model and its assumptions; it is not the probability that the option is best in the world. It satisfies the constraints in 100% of resamples. 

Every precision target was met at 120 paths.

With the constraints lifted, Liability with a safe harbour scores higher ($39.0bn) but fails: industry loss $371bn exceeds the $300bn limit (satisfied in 0% of resamples).

## The options compared

| Alternative | Expected net social value, $bn | 95% confidence interval | Outcomes, 10th to 90th percentile | Harm avoided, $bn | Gross social cost, $bn | Industry value change, $bn | P(catastrophe) | Headline score | Within constraints | Share of resamples within | Ranking stability |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Liability with a safe harbour | 39.0 | [29.4, 49.2] | [-26.2, 80.6] | 17.6 | 12.8 | -371 | 12.0% | +0.000 | no | 0% | 0% |
| Mandatory third party evaluation (preferred) | 23.2 | [12.9, 35.0] | [-37.2, 78.3] | 14.2 | 12.9 | -41 | 12.6% | +0.012 | yes | 100% | 100% |
| Status quo (voluntary commitments) | 0.0 | [0.0, 0.0] | [0.0, 0.0] | 0.0 | 0.0 | 0 | 14.7% | +0.000 | no | 3% | 0% |
| Strict liability | -4.7 | [-8.2, -1.1] | [-25.2, 20.3] | 4.2 | 10.9 | -1,232 | 14.1% | +0.005 | no | 0% | 0% |

The status quo carries an expected harm of $93.1bn over the horizon, 9.4 reportable incidents a year, a 100% probability of at least one major incident and a 14.7% probability of a catastrophic one (95% confidence interval 14.0% to 15.4%; a catastrophe was drawn on 21 of 120 paths). The probability is estimated from the hazard each path accumulates, not from the count of paths on which the event happened to be drawn, which is why it is far more precise than that count.

## What Mandatory third party evaluation buys and costs

| Component | Expected value, $bn present value | 95% confidence interval | Outcomes, 10th to 90th percentile |
|---|---|---|---|
| Harm avoided | 14.2 | [14.2, 14.2] | [0.4, 8.9] |
| Consumer surplus | -4.2 | [-5.5, -2.7] | [-10.0, 3.8] |
| Output uplift (adoption) | 21.9 | [13.3, 31.7] | [-17.8, 70.9] |
| Resident producer surplus | -5.0 | [-5.3, -4.5] | [-6.6, -2.7] |
| Compliance (resource cost) | -3.3 | [-3.3, -3.3] | [-3.4, -3.3] |
| Enforcement budget (cost) | -0.4 | [-0.4, -0.3] | [-0.4, -0.3] |
| Activity lost offshore (cost) | 0.0 | [0.0, 0.0] | [0.0, 0.0] |
| Relocation cost | 0.0 | [0.0, 0.0] | [0.0, 0.0] |
| Labour adjustment (cost) | 0.0 | [-0.1, 0.0] | [-0.1, 0.1] |
| Insurance administration (resource cost) | 0.0 | [0.0, 0.0] | [0.0, 0.0] |
| **Net social value** | **23.2** | [12.9, 35.0] | [-37.2, 78.3] |

Expected harm avoided is estimated from the harm expected in each month given the state the path has reached (probability times mean severity), which has the same expectation as the harm drawn and far less variance. The outcomes column uses the harm as drawn: its median is $2.3bn and the average of the draws is $18.0bn; 88% of that average comes from the tenth of paths with the largest values, the paths on which a catastrophic incident is averted.

Gross social cost $12.9bn (the expected component changes that are costs, never netted against savings), gross benefit $36.1bn; their difference is the net social value. Gross cost per dollar of expected harm avoided: 0.91.
Transfers, excluded from the net: fines $24.2bn, liability paid by firms $0.0bn, insurance premiums $0.0bn, claims paid to victims $0.0bn.

## Who gains and who pays

| Party | Change, $bn present value |
|---|---|
| Compliance providers (rents) | 1.4 |
| Consumers | -4.2 |
| Domestic workers and tax base (activity moved offshore) | 0.0 |
| Insurers | 0.0 |
| Public at risk (harm not suffered, compensation received) | 14.2 |
| Resident owners of AI firms | -22.4 |
| Sectors that adopt AI (output) | 21.9 |
| Taxpayers (fines less enforcement) | 23.9 |
| Workers (adjustment) | 0.0 |
| **Total** | **34.8** |

The table follows the money as well as the real effects, so it sums to the net social value ($23.2bn) plus what non resident owners finance of the firms' payments ($11.6bn), a memorandum item the net social value does not count. Standing is residents: real resources used in the jurisdiction count in full, income counts for residents, and transfers are excluded whoever pays.

## Safety forecast

| Alternative | Incidents a year | Major a year | P(major) | P(catastrophe) | 95% confidence interval | Expected harm, $bn | Safety level at end | Frontier capability at end | Trust at end |
|---|---|---|---|---|---|---|---|---|---|
| Status quo (voluntary commitments) | 9.4 | 1.26 | 100% | 14.7% | 14.0% to 15.4% | 93.1 | 0.66 | 4.36 | 0.72 |
| Mandatory third party evaluation | 8.2 | 1.11 | 100% | 12.6% | 12.0% to 13.1% | 78.9 | 0.66 | 4.11 | 0.76 |
| Strict liability | 8.9 | 1.18 | 100% | 14.1% | 13.4% to 14.7% | 88.9 | 0.68 | 4.21 | 0.74 |
| Liability with a safe harbour | 8.0 | 1.07 | 99% | 12.0% | 11.5% to 12.4% | 75.5 | 0.68 | 4.30 | 0.77 |

Under Mandatory third party evaluation the economy runs 8.2 reportable incidents a year (misuse 4.4, accidents 2.7, systemic 1.1), against 9.4 at the status quo; the expected catastrophic harm is $57.8bn against $69.1bn. Firms end with 10% of R&D on safety, 0% of activity offshore and 50% compliance. A major incident is a single incident at or above the threshold; catastrophes are counted apart.

## The news environment to expect

| Alternative | Minor incident headlines a year | Major incident headlines a year | Enforcement headlines a year | Relocation headlines a year | Peak pressure | P(hearing) | Early tone |
|---|---|---|---|---|---|---|---|
| Status quo (voluntary commitments) | 8.1 | 1.26 | 2.32 | 0.00 | 0.32 | 1% | -0.11 |
| Mandatory third party evaluation | 7.1 | 1.11 | 1.32 | 0.00 | 0.34 | 3% | +0.05 |
| Strict liability | 7.7 | 1.18 | 6.96 | 0.00 | 0.42 | 31% | +0.05 |
| Liability with a safe harbour | 7.0 | 1.07 | 0.00 | 0.00 | 0.32 | 2% | +0.05 |

On the representative path the wire under Mandatory third party evaluation ran 151 headlines over the horizon, 34% of them negative. The three worst: "Regulators open inquiry into Frontier Lab (closed weights) after $1.1bn autonomous system failure" (WIRE, 2027-10); "MAJOR: Frontier Lab (closed weights) system behind information ecosystem shock; damages reach $8.3bn" (WIRE, 2029-11); "Frontier Lab (closed weights) faces $12bn fallout after correlated model outage" (WIRE, 2031-09).

## The market

Industry net value change under Mandatory third party evaluation: -$41bn (95% confidence interval -$72bn to -$11bn) on a starting value of $6.38tn; across outcomes -$197bn to $135bn, and the industry gains on 31% of paths. The value weighted index reacts -0.4% against the status quo over the first six months and +0.0% by the end of the horizon. Every index is measured from the same valuation, the firms as they stand before any instrument is announced, so an instrument's immediate effect on fundamentals shows in the first month.

| Firm | Sector | Expected value change, $bn | 95% confidence interval | Outcomes, 10th to 90th | P(gain) | Earnings change, $bn | Offshore at end | Safety share at end |
|---|---|---|---|---|---|---|---|---|
| Frontier Lab (closed weights) | Frontier lab | -26.9 | [-29.3, -24.8] | [-39.8, -13.0] | 2% | -1.9 | 0% | 10% |
| Frontier Lab (open weights) | Open weights | -9.7 | [-10.5, -8.9] | [-14.7, -4.8] | 2% | -0.7 | 0% | 10% |
| Hyperscaler cloud | hyperscaler | -41.9 | [-50.8, -33.2] | [-86.9, 14.5] | 16% | -26.0 | 0% | 10% |
| Chip designer | chips | -6.7 | [-17.4, 4.6] | [-64.0, 61.8] | 36% | -5.7 | 0% | 10% |
| Enterprise software | Enterprise software | 63.9 | [59.6, 68.5] | [38.9, 92.2] | 100% | 0.5 | 0% | 10% |
| Consumer AI platform | Consumer AI | -29.3 | [-32.7, -26.1] | [-48.4, -11.0] | 6% | -2.6 | 0% | 10% |
| Autonomy and robotics | autonomy | -14.0 | [-15.2, -12.9] | [-19.6, -7.1] | 2% | -1.0 | 0% | 10% |
| AI start up cohort | startups | 23.2 | [21.3, 25.0] | [12.2, 37.0] | 100% | 0.0 | 0% | 10% |

| Sector | Expected value change, $bn | Starting value, $bn |
|---|---|---|
| Frontier lab | -26.9 | 267 |
| Open weights | -9.7 | 60 |
| hyperscaler | -41.9 | 1,910 |
| chips | -6.7 | 2,492 |
| Enterprise software | 63.9 | 935 |
| Consumer AI | -29.3 | 507 |
| autonomy | -14.0 | 119 |
| startups | 23.2 | 91 |

The firms are synthetic archetypes of the AI value chain, not companies; the figures are the model's and carry its assumptions. Shareholder value is a market metric and a constraint; it is not part of the net social value.

## The decision gap

Ranked by how they look in the first six months (the price reaction and the early tone of the wire), the instruments are Mandatory third party evaluation, Strict liability, Liability with a safe harbour. Ranked by expected net social value over 5 years they are Liability with a safe harbour, Mandatory third party evaluation, Strict liability. Kendall tau b between the two is -0.33; the decision gap ((1 - tau) / 2) is 0.67, and the two orders invert in 100% of resamples.

## How sure we are

**Monte Carlo error.** Every expected value above carries the 95% bootstrap confidence interval of its mean over 500 resamples of the paths, paired across alternatives. The run followed its sampling plan: 120 paths, stopping when the preferred alternative was resolved against every other feasible one to within $5.0bn and the catastrophe probabilities to within 3%, or at the ceiling. The intervals are not adjusted for those sequential looks.

Convergence of the running estimate (the first paths of the run are exactly what a smaller run on this seed reports):

| Paths | Decision | Expected net social value of Mandatory third party evaluation, $bn | Standard error | P(catastrophe), status quo |
|---|---|---|---|---|
| 15 | Liability with a safe harbour | 41.0 | 17.52 | 14.3% |
| 30 | Liability with a safe harbour | 30.5 | 10.20 | 13.8% |
| 60 | Mandatory third party evaluation | 30.7 | 9.43 | 14.1% |
| 120 | Mandatory third party evaluation | 23.2 | 5.56 | 14.7% |

The decision is the same over the last doubling of the paths, and the final estimate lies inside every earlier interval.

Split into 4 independent batches of 30 paths, the run gives the same decision in 3 of them (Liability with a safe harbour, Mandatory third party evaluation, Mandatory third party evaluation, Mandatory third party evaluation).

**Parameters, one at a time.** Each of the 68 declared assumptions was moved to the low and the high end of its plausible range, the decision re made under each (feasibility re assessed, the status quo an alternative). Mandatory third party evaluation is worth $23.2bn at the run's values. The 15 largest swings:

| Assumption | Run's value | Low | Value at low, $bn | Decision at low | High | Value at high, $bn | Decision at high |
|---|---|---|---|---|---|---|---|
| Relocation cost | 0.0800 | 0.0400 | -85.8 | none | 0.16 | 23.2 | Mandatory third party evaluation |
| Monthly catastrophe probability | 0.0020 | 0.0005 | 14.7 | Liability with a safe harbour | 0.0050 | 106.2 | none |
| Audit rate | 0.50 | 0.30 | 11.5 | none | 0.80 | -63.5 | Mandatory third party evaluation |
| Weight of safety culture | 0.60 | 0.30 | 52.8 | none | 1.20 | -18.0 | the status quo |
| Trust sensitivity to harm | 0.0400 | 0.0200 | -6.8 | Mandatory third party evaluation | 0.0800 | 62.3 | Mandatory third party evaluation |
| Safety decay | 0.0200 | 0.0100 | -24.6 | the status quo | 0.0400 | 37.6 | none |
| Capability growth | 0.0230 | 0.0150 | -46.4 | the status quo | 0.0350 | -92.9 | none |
| Safety spend that displaces capability R&D | 0.60 | 0.30 | -2.9 | the status quo | 1.00 | 42.5 | Mandatory third party evaluation |
| Trust elasticity of adoption benefits | 0.50 | 0.20 | 5.0 | Mandatory third party evaluation | 1.00 | 48.4 | Mandatory third party evaluation |
| Reach ceiling saturation | 1.50 | 1.00 | -9.8 | Mandatory third party evaluation | 2.20 | 26.0 | Mandatory third party evaluation |
| Safety elasticity of incidents | 1.80 | 1.40 | 17.3 | none | 3.00 | -18.0 | the status quo |
| Output uplift base | 400.00 | 200.00 | 12.2 | Mandatory third party evaluation | 800.00 | 45.0 | Mandatory third party evaluation |
| Revenue lost offshore | 0.12 | 0.0600 | -8.3 | Mandatory third party evaluation | 0.24 | 23.2 | Mandatory third party evaluation |
| Median harm of a catastrophe | 400.00 | 150.00 | 16.0 | Liability with a safe harbour | 1,200.00 | 46.0 | Mandatory third party evaluation |
| Safety learning rate | 0.0800 | 0.0500 | 17.4 | none | 0.12 | -9.0 | the status quo |

The decision changes at an end of the range of 18 of the 68 assumptions; the 12 with the largest swings are Relocation cost, Monthly catastrophe probability, Audit rate, Weight of safety culture, Safety decay, Capability growth, Safety spend that displaces capability R&D, Safety elasticity of incidents, Median harm of a catastrophe, Safety learning rate, Revenue response to capability, Critical capability (the screen in the artefacts lists all 18). The sign of the focus option's value is not robust across the screen. For 11 of them the cause is feasibility: Mandatory third party evaluation stops satisfying a constraint under the alternative (on the central estimate: probability of a catastrophe 12.6% within the 14% ceiling (satisfied in 100% of resamples)); for 15 another alternative within the constraints overtakes it. Each re simulated assumption ran on the first 4 paths, paired with the main run: 35 of the 68 swings exceed twice their Monte Carlo standard error, and a change of decision inside that error is a warning to look, not a finding.

**Parameters, all together.** 64 joint draws of every assumption over its plausible range (correlated where they plausibly move together). Under that parameter uncertainty:

| Alternative | Mean net social value, $bn | 5th to 95th percentile over the draws | Share of draws it is the decision | Share of draws within constraints | Share within constraints and above the status quo | Expected regret where within constraints, $bn |
|---|---|---|---|---|---|---|
| The status quo | 0.0 | [0.0, 0.0] | 28% | 44% | 44% | 22.8 |
| Mandatory third party evaluation | -16.7 | [-175.9, 144.7] | 19% | 38% | 19% | 26.3 |
| Liability with a safe harbour | 88.0 | [-6.4, 284.0] | 8% | 8% | 8% | 0.0 |
| Strict liability | 21.0 | [-41.8, 117.5] | 0% | 0% | 0% | n/a |

Regret is how far an alternative falls short of the best alternative within the constraints in the same draw, averaged over the draws in which it is itself within them; it is read beside the share of draws in which it is, because choosing an alternative where it breaks a constraint is not a cost in $bn.

The ranges are declared judgements, a prior over the assumptions and not a posterior estimated from data. The margin of Mandatory third party evaluation over the best alternative moves with Relocation cost (rank correlation +0.48), Reach adjustment speed (rank correlation -0.38), Capability growth (rank correlation -0.37): of the 68 assumptions, 3 pass a 10% false discovery rate on that correlation.

**Which assumptions carry the variance.** A Sobol decomposition over the 5 assumptions with the largest swings (448 evaluations), for the value of Mandatory third party evaluation and for its margin over the best alternative. Shares with interactions (total order), with the 90% interval the size of the design allows:

| Assumption | Share of the value's variance, with interactions | 90% interval | Share of the margin's variance, with interactions | 90% interval | Alone (first order), margin |
|---|---|---|---|---|---|
| Relocation cost | 46% | 34% to 67% | 46% | 32% to 65% | 40% |
| Audit rate | 34% | 24% to 51% | 34% | 25% to 50% | 29% |
| Weight of safety culture | 30% | 11% to 54% | 30% | 11% to 57% | 0% |
| Trust sensitivity to harm | 6% | 4% to 9% | 6% | 4% to 10% | 8% |
| Monthly catastrophe probability | 2% | 1% to 3% | 2% | 1% to 3% | 2% |

The intervals are wide (half width 11% on average for the margin): the output is heavy tailed in these assumptions, which compound, so a design of this size ranks groups of assumptions and does not order neighbours. Shares with interactions add to more than one when the assumptions interact, as these do: first order shares sum to 79% of the margin's variance.

**Model structure.** Under 8 alternative model structures Mandatory third party evaluation remains the decision in 3 and stays within the constraints and above the status quo in 2:

| Variant | What changes | Decision | Focus option's rank among instruments | Its value, $bn | Within constraints |
|---|---|---|---|---|---|
| Myopic firms | firms plan six months ahead instead of twelve | Liability with a safe harbour | 3 | -10.2 | no |
| Forward looking firms | firms plan two years ahead | Mandatory third party evaluation | 3 | -87.4 | yes |
| Weak regulator | the regulator has half the stated capacity | none | 3 | -14.9 | no |
| Strong safety effect | safety practice cuts incidents faster | the status quo | 3 | -20.4 | yes |
| Weak safety effect | safety practice cuts incidents more slowly | none | 2 | 34.7 | no |
| Lax offshore | offshore activity is twice as hazardous as at home | Mandatory third party evaluation | 2 | 23.2 | yes |
| Heavy tail | the catastrophic tail is two and a half times more likely | none | 2 | 45.6 | no |
| Systemic catastrophes | catastrophic failures are strongly correlated across firms | Mandatory third party evaluation | 2 | 16.0 | yes |

**Gaming.** Firms game each instrument four ways; the instrument under its worst strategy, and whether it is then still within the constraints and above the status quo:

| Instrument | Honest value, $bn | Worst strategy | Value when gamed, $bn | Harm avoided when gamed, $bn | Loss to gaming, $bn | Acceptable under every strategy |
|---|---|---|---|---|---|---|
| Strict liability | -4.7 | Threshold splitting | -4.7 | 4.2 | 0.0 | no |
| Liability with a safe harbour | 39.0 | Compliance theatre | -7.3 | -5.7 | 46.3 | no |
| Mandatory third party evaluation | 23.2 | Maximal relocation | -138.1 | -3.4 | 161.3 | no |

When every instrument is gamed at its worst, the best choice is the status quo. Strategies: Compliance theatre: mandated safety spend is reported but not spent; evaluations are gamed; Maximal relocation: firms are more mobile and moving is cheaper than assumed; Threshold splitting: models are split so the regulator sees capability 20% below the real level; Use case relabelling: deployments are relabelled into lower tiers, avoiding 60% of tier costs.

**Robustly acceptable.** No instrument is within the constraints and above the status quo on the central estimate, in at least 90% of the joint draws, in every structural variant and under every gaming strategy. The preferred option is not among them: it is the best on the central estimate and not robust to the alternatives above.

**Validation against published evidence.** The model was confronted with 11 published benchmarks that bear on 10 of its 15 mechanisms. 3 of those mechanisms have a benchmark measured on AI itself; the others rest on analogues from other regulation and other technologies, each compared with an allowance for that distance. At the central assumptions the model is not contradicted by 9, is in tension with 1 (Share of the insurance loading used up by underwriting and administration) and is contradicted by 1 (Equity return when a horizontal regime becomes enforceable). Even the closest tenth of the draws of the assumptions miss Equity return when a horizontal regime becomes enforceable by more than 2 standard deviations: that is a failure of the model's form and not of a parameter value, so it is reported and left out of the weighting below. No benchmark bears on 5 mechanisms: severity, catastrophic tail, safety practice, evaluation, news.

| Benchmark | Kind | Observed (allowance, one sd) | Model at the central assumptions | z | Verdict | Model across the declared ranges, 5th to 95th | Predicted with it held out |
|---|---|---|---|---|---|---|---|
| Annual growth of recorded AI incidents | direct | 56% (sd 26%) | 42% | -0.5 | not contradicted | 31% to 67% | 44% (z -0.4) |
| Annual change in public trust in AI and AI companies | direct | -5.1% (sd 2.3%) | -6.2% | -0.5 | not contradicted | -16.5% to -2.2% | -9.7% (z -0.7) |
| Share of a fall in trust recovered about nine months after a salient incident | analogue | 20% (sd 35%) | 37% | +0.5 | not contradicted | 30% to 56% | 44% (z +0.7) |
| Compliance cost of a high risk regime as a share of development spending in scope | official | 10.8% (sd 6.9%) | 12.1% | +0.2 | not contradicted | 9.0% to 13.4% | 11.7% (z +0.1) |
| Effect of a horizontal compliance regime on the profits of firms in scope | analogue | -3.3% (sd 3.9%) | -7.4% | -1.1 | not contradicted | -9.7% to -5.9% | -7.9% (z -1.2) |
| Equity return when a horizontal regime becomes enforceable | analogue | -0.9% (sd 1.0%) | -4.9% | -3.9 | contradicted; a failure of form, left out of the weights | -5.6% to -3.3% | left out of the weights |
| Equity return of a firm when a regulatory fine is announced | analogue | -0.7% (sd 1.0%) | -0.2% | +0.5 | not contradicted | -0.8% to +0.8% | +0.1% (z +0.4) |
| Equity return of a firm when a serious incident becomes public | analogue | -1.1% (sd 1.1%) | -1.2% | -0.1 | not contradicted | -1.0% to +3.9% | +2.0% (z +1.4) |
| Share of regulated activity displaced abroad by a unilateral regime | analogue | 14.0% (sd 8.6%) | 24.8% | +1.3 | not contradicted | 0.3% to 25.2% | 16.7% (z +0.2) |
| Premium above expected claims in liability insurance | analogue | 31% (sd 15%) | 25% | -0.4 | not contradicted | 16% to 42% | 28% (z -0.2) |
| Share of the insurance loading used up by underwriting and administration | analogue | 107% (sd 25%) | 50% | -2.3 | in tension | 33% to 66% | 49% (z -2.1) |

The allowance is the benchmark's own standard error combined with a declared allowance for the distance between the setting it was measured in and the model's; z is the gap between model and observation in those units, with the Monte Carlo error of the model's value added. Not contradicted: within two; in tension: two to three; contradicted: beyond three. A benchmark is predicted with it held out from the draws weighted by all the others.

Weighting the 64 joint draws of the assumptions by how well each reproduces the 10 benchmarks it can be compared with leaves an effective 13 draws. In the weighted draws the decision is no alternative in 45% (unweighted 45%); the status quo in 23% (unweighted 28%); Mandatory third party evaluation in 20% (unweighted 19%); Liability with a safe harbour in 12% (unweighted 8%). 80% of the draws are ruled out by no benchmark at 3 standard deviations. Mandatory third party evaluation is within the constraints and above the status quo in 27% of the weighted draws (19% unweighted). Fewer than 20 effective draws: the weighted shares are indicative only on this budget. The benchmarks bear on 13 of the 68 assumptions drawn; they move most Resource share of the insurance loading (+0.7 sd), Capability elasticity of incidents (-0.3 sd), Weight firms put on growth (-0.2 sd), Revenue lost offshore (-0.2 sd), Relocation cost (-0.2 sd).

| Assumption the benchmarks bear on | Value on this run | Mean of the draws | Weighted mean | Shift, in sd of the draws | Spread kept | Through |
|---|---|---|---|---|---|---|
| Resource share of the insurance loading | 0.5 | 0.4997 | 0.5723 | +0.71 | 92% | insurance resource share |
| Capability elasticity of incidents | 1.3 | 1.332 | 1.276 | -0.30 | 74% | incident growth, compliance cost share |
| Weight firms put on growth | 3 | 3.168 | 2.999 | -0.23 | 81% | compliance cost share, leakage share, profit effect |
| Revenue lost offshore | 0.12 | 0.1398 | 0.1312 | -0.23 | 113% | leakage share |
| Relocation cost | 0.08 | 0.09324 | 0.08791 | -0.21 | 103% | leakage share |
| Capability growth | 0.023 | 0.02433 | 0.02514 | +0.20 | 97% | incident growth, trust trend, profit effect |
| Audit rate | 0.5 | 0.5336 | 0.5186 | -0.14 | 122% | compliance cost share |
| Share of incidents an evaluation could catch | 0.35 | 0.35 | 0.3428 | -0.12 | 92% | trust trend |
| Trust recovery | 0.05 | 0.06001 | 0.06135 | +0.09 | 81% | trust recovery |
| Trust sensitivity to harm | 0.04 | 0.04664 | 0.0458 | -0.07 | 102% | trust trend |

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

Indicators to watch, with the model's expectation under Mandatory third party evaluation: reportable incidents a year (6.6 to 9.6 across outcomes); the share of activity offshore (0% at the horizon); the news pressure index (peak 0.34, a hearing in 3% of paths); the industry's value against the status quo (+0.0% at the horizon). Revisit the decision if incidents run above that range for two quarters, if relocation exceeds the forecast, or if any of Relocation cost, Monthly catastrophe probability, Audit rate, Weight of safety culture, Safety decay, Capability growth, Safety spend that displaces capability R&D, Safety elasticity of incidents can be estimated from data.

## Gates, provenance and reproduction

**Gate 1 (battery)**: approved at 2026-11-16T06:04:09 in a public demonstration, without a sign off identity; inside an authority a named approver on the register takes this gate.
**Gate 2 (release)**: approved at 2026-11-16T06:04:25 in a public demonstration, without a sign off identity; inside an authority a named approver on the register takes this gate.
**Critic**: 57 of 57 checks passed before release.
Battery hash `67a124b8cccfcfac532e98aef3817f39fb3e0064bad36b7fbd5c196ef98267a7`; code fingerprint `28b530f37f3d12c48a159a7cb59c0eae091feb07e3b7c4b70029b020889c5c84`; PSL 1.2.0, numpy 2.5.3, scipy 1.18.1; profile demo; 11.4 seconds. Reproduce with `python -m psl.orchestrator --battery battery.json`.
