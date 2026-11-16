# Policy Scenario Lab briefing

**Run** 20261116-060333-5970. **Question.** Replication on seed 8: which AI regulatory instrument best reduces expected harm from frontier AI over the next five years, keeping the technology sector's net loss below $400bn and the gross social cost under $150bn?

**How it was read.** 8 instruments and the status quo (default battery); horizon 5 years; 240 Monte Carlo paths per alternative (the run started on 120 and doubled on the same random streams, ceiling 480), every alternative on the same random numbers, seed 8; constraints: industry loss at most $400bn; gross social cost at most $150bn.

**What this is.** A comparison of alternatives inside a synthetic model of the AI economy under declared assumptions. The figures are conditional on that model: they are scenario evaluations, not forecasts validated against data, and the preferred option is the model's answer to the question, to be examined, not an established recommendation. Confronted with 11 published benchmarks, mostly analogues from other regulation, the model is not contradicted by 9 and fails or strains on equity return when a horizontal regime becomes enforceable; share of the insurance loading used up by underwriting and administration. 5 of its 15 mechanisms have no benchmark at all, and no mechanism is estimated from data.

## The answer

**Preferred option: Liability with a safe harbour.** Expected net social value $37.4bn (95% confidence interval $32.0bn to $43.5bn) over 5 years, the highest among the alternatives that satisfy the constraints and above the status quo, which scores zero. It avoids $17.6bn of expected harm (19% of the status quo's), and the industry's expected value change is -$386bn (95% confidence interval -$407bn to -$364bn).

Across the simulated outcomes the net social value of Liability with a safe harbour runs from -$23.7bn (10th percentile) to $90.1bn (90th percentile) and is positive on 60% of paths; that range is how different one path can be from another, not the uncertainty of the expected value, which the confidence interval gives. The confidence interval excludes zero.

**How firm the decision is on these paths.** Liability with a safe harbour is the best feasible alternative in 92% of bootstrap resamples of the paths, with feasibility re assessed in each. That share is ranking stability under the model and its assumptions; it is not the probability that the option is best in the world. It satisfies the constraints in 92% of resamples. 

**Feasibility that the paths do not settle.** Risk tiering (EU style) is within the constraints in 85% of resamples (expected net social value -$68.5bn). A constraint is tested on an estimate; where the limit sits inside the estimate's interval, inclusion or exclusion is not settled.

Every precision target was met at 240 paths.

## The options compared

| Alternative | Expected net social value, $bn | 95% confidence interval | Outcomes, 10th to 90th percentile | Harm avoided, $bn | Gross social cost, $bn | Industry value change, $bn | P(catastrophe) | Headline score | Within constraints | Share of resamples within | Ranking stability |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Liability with a safe harbour (preferred) | 37.4 | [32.0, 43.5] | [-23.7, 90.1] | 17.6 | 12.9 | -386 | 12.3% | -0.002 | yes | 92% | 92% |
| Transparency and disclosure | 26.9 | [23.8, 30.0] | [3.1, 67.0] | 1.6 | 1.9 | 51 | 15.2% | +0.014 | yes | 100% | 8% |
| Mandatory third party evaluation | 18.9 | [13.8, 24.9] | [-34.1, 64.4] | 14.2 | 13.6 | -55 | 13.0% | +0.010 | yes | 100% | 0% |
| Compute threshold reporting | 12.3 | [9.2, 15.9] | [-2.1, 29.5] | 3.1 | 2.1 | 172 | 14.8% | +0.014 | yes | 100% | 0% |
| Status quo (voluntary commitments) | 0.0 | [0.0, 0.0] | [0.0, 0.0] | 0.0 | 0.0 | 0 | 15.2% | +0.000 | yes | 100% | 0% |
| Strict liability | -4.2 | [-7.1, -0.6] | [-25.5, 17.5] | 4.2 | 10.8 | -1,245 | 14.6% | +0.002 | no | 0% | 0% |
| Risk tiering (EU style) | -68.5 | [-72.4, -64.6] | [-101.8, -26.5] | 4.4 | 73.0 | -392 | 14.7% | -0.003 | yes | 85% | 0% |
| Frontier licensing | -103.4 | [-107.4, -98.5] | [-135.4, -79.2] | 3.6 | 107.1 | -494 | 14.7% | +0.010 | no | 0% | 0% |
| Six month moratorium above the threshold | -114.2 | [-118.3, -109.8] | [-149.0, -77.0] | 6.5 | 120.9 | -6 | 14.3% | -0.012 | yes | 100% | 0% |

The status quo carries an expected harm of $93.1bn over the horizon, 9.2 reportable incidents a year, a 100% probability of at least one major incident and a 15.2% probability of a catastrophic one (95% confidence interval 14.8% to 15.6%; a catastrophe was drawn on 32 of 240 paths). The probability is estimated from the hazard each path accumulates, not from the count of paths on which the event happened to be drawn, which is why it is far more precise than that count.

**Liability with a safe harbour against each other feasible alternative** (paired on the same paths):

| Against | Difference in expected net social value, $bn | 95% confidence interval | Simultaneous 95% interval | Told apart |
|---|---|---|---|---|
| Status quo (voluntary commitments) | 37.4 | [32.0, 43.5] | [29.9, 45.0] | yes |
| Transparency and disclosure | 10.6 | [6.2, 15.9] | [4.2, 16.9] | yes |
| Compute threshold reporting | 25.2 | [20.7, 30.2] | [18.9, 31.5] | yes |
| Mandatory third party evaluation | 18.5 | [13.5, 23.9] | [11.6, 25.4] | yes |
| Risk tiering (EU style) | 105.9 | [101.5, 111.2] | [99.9, 112.0] | yes |
| Six month moratorium above the threshold | 151.6 | [147.3, 156.3] | [145.7, 157.5] | yes |

## What Liability with a safe harbour buys and costs

| Component | Expected value, $bn present value | 95% confidence interval | Outcomes, 10th to 90th percentile |
|---|---|---|---|
| Harm avoided | 17.6 | [17.6, 17.6] | [1.0, 8.4] |
| Consumer surplus | -1.1 | [-1.8, -0.3] | [-7.0, 7.0] |
| Output uplift (adoption) | 32.7 | [28.2, 37.8] | [-4.5, 79.9] |
| Resident producer surplus | -0.4 | [-0.6, -0.1] | [-2.1, 2.0] |
| Compliance (resource cost) | -9.6 | [-9.6, -9.6] | [-9.7, -9.4] |
| Enforcement budget (cost) | -0.3 | [-0.3, -0.3] | [-0.3, -0.2] |
| Activity lost offshore (cost) | 0.0 | [0.0, 0.0] | [0.0, 0.0] |
| Relocation cost | 0.0 | [0.0, 0.0] | [0.0, 0.0] |
| Labour adjustment (cost) | 0.0 | [0.0, 0.0] | [-0.1, 0.1] |
| Insurance administration (resource cost) | -1.6 | [-1.6, -1.6] | [-1.6, -1.6] |
| **Net social value** | **37.4** | [32.0, 43.5] | [-23.7, 90.1] |

Expected harm avoided is estimated from the harm expected in each month given the state the path has reached (probability times mean severity), which has the same expectation as the harm drawn and far less variance. The outcomes column uses the harm as drawn: its median is $3.1bn and the average of the draws is $14.2bn; 80% of that average comes from the tenth of paths with the largest values, the paths on which a catastrophic incident is averted.

Gross social cost $12.9bn (the expected component changes that are costs, never netted against savings), gross benefit $50.3bn; their difference is the net social value. Gross cost per dollar of expected harm avoided: 0.73.
Transfers, excluded from the net: fines $0.0bn, liability paid by firms $0.0bn, insurance premiums $16.1bn, claims paid to victims $17.0bn.

## Who gains and who pays

| Party | Change, $bn present value |
|---|---|
| Compliance providers (rents) | 4.1 |
| Consumers | -1.1 |
| Domestic workers and tax base (activity moved offshore) | 0.0 |
| Insurers | -2.4 |
| Public at risk (harm not suffered, compensation received) | 34.6 |
| Resident owners of AI firms | -18.2 |
| Sectors that adopt AI (output) | 32.7 |
| Taxpayers (fines less enforcement) | -0.3 |
| Workers (adjustment) | 0.0 |
| **Total** | **49.4** |

The table follows the money as well as the real effects, so it sums to the net social value ($37.4bn) plus what non resident owners finance of the firms' payments ($11.9bn), a memorandum item the net social value does not count. Standing is residents: real resources used in the jurisdiction count in full, income counts for residents, and transfers are excluded whoever pays.

## Safety forecast

| Alternative | Incidents a year | Major a year | P(major) | P(catastrophe) | 95% confidence interval | Expected harm, $bn | Safety level at end | Frontier capability at end | Trust at end |
|---|---|---|---|---|---|---|---|---|---|
| Status quo (voluntary commitments) | 9.2 | 1.25 | 100% | 15.2% | 14.8% to 15.6% | 93.1 | 0.66 | 4.36 | 0.73 |
| Transparency and disclosure | 8.4 | 1.18 | 100% | 15.2% | 14.8% to 15.6% | 91.5 | 0.66 | 4.36 | 0.74 |
| Compute threshold reporting | 9.0 | 1.22 | 100% | 14.8% | 14.3% to 15.1% | 90.1 | 0.66 | 4.36 | 0.74 |
| Mandatory third party evaluation | 8.1 | 1.08 | 100% | 13.0% | 12.7% to 13.3% | 78.9 | 0.66 | 4.11 | 0.76 |
| Risk tiering (EU style) | 8.4 | 1.15 | 100% | 14.7% | 14.3% to 15.1% | 88.8 | 0.67 | 4.25 | 0.75 |
| Frontier licensing | 9.0 | 1.22 | 100% | 14.7% | 14.2% to 15.0% | 89.5 | 0.67 | 4.04 | 0.74 |
| Strict liability | 8.8 | 1.18 | 100% | 14.6% | 14.2% to 15.0% | 88.9 | 0.68 | 4.21 | 0.75 |
| Liability with a safe harbour | 7.9 | 1.05 | 100% | 12.3% | 12.0% to 12.6% | 75.5 | 0.68 | 4.30 | 0.77 |
| Six month moratorium above the threshold | 8.6 | 1.17 | 100% | 14.3% | 14.0% to 14.7% | 86.6 | 0.66 | 4.09 | 0.75 |

Under Liability with a safe harbour the economy runs 7.9 reportable incidents a year (misuse 4.2, accidents 2.6, systemic 1.0), against 9.2 at the status quo; the expected catastrophic harm is $55.0bn against $69.1bn. Firms end with 12% of R&D on safety, 0% of activity offshore and 100% compliance. A major incident is a single incident at or above the threshold; catastrophes are counted apart.

## The news environment to expect

| Alternative | Minor incident headlines a year | Major incident headlines a year | Enforcement headlines a year | Relocation headlines a year | Peak pressure | P(hearing) | Early tone |
|---|---|---|---|---|---|---|---|
| Status quo (voluntary commitments) | 8.0 | 1.25 | 2.35 | 0.00 | 0.32 | 1% | -0.08 |
| Transparency and disclosure | 7.3 | 1.18 | 0.00 | 0.00 | 0.33 | 2% | +0.07 |
| Compute threshold reporting | 7.8 | 1.22 | 0.00 | 0.00 | 0.35 | 4% | +0.07 |
| Mandatory third party evaluation | 7.0 | 1.08 | 1.30 | 0.00 | 0.34 | 5% | +0.07 |
| Risk tiering (EU style) | 7.2 | 1.15 | 1.46 | 0.00 | 0.36 | 8% | +0.07 |
| Frontier licensing | 7.8 | 1.22 | 1.66 | 2.40 | 0.37 | 5% | +0.07 |
| Strict liability | 7.6 | 1.18 | 6.88 | 0.00 | 0.43 | 28% | +0.07 |
| Liability with a safe harbour | 6.8 | 1.05 | 0.00 | 0.00 | 0.32 | 0% | +0.07 |
| Six month moratorium above the threshold | 7.5 | 1.17 | 0.00 | 0.00 | 0.34 | 3% | -0.08 |

On the representative path the wire under Liability with a safe harbour ran 160 headlines over the horizon, 25% of them negative. The three worst: "Credential harvesting attack tied to Frontier Lab (open weights) causes $8.0bn in losses" (WIRE, 2029-07); "Regulators open inquiry into AI start up cohort after $1.1bn sector wide hallucination event" (WIRE, 2029-09); "AI start up cohort slides 30% as investors weigh regulatory costs" (WIRE, 2027-01).

## The market

Industry net value change under Liability with a safe harbour: -$386bn (95% confidence interval -$407bn to -$364bn) on a starting value of $6.38tn; across outcomes -$574bn to -$195bn, and the industry gains on 2% of paths. The value weighted index reacts -1.6% against the status quo over the first six months and -3.8% by the end of the horizon. Every index is measured from the same valuation, the firms as they stand before any instrument is announced, so an instrument's immediate effect on fundamentals shows in the first month.

| Firm | Sector | Expected value change, $bn | 95% confidence interval | Outcomes, 10th to 90th | P(gain) | Earnings change, $bn | Offshore at end | Safety share at end |
|---|---|---|---|---|---|---|---|---|
| Frontier Lab (closed weights) | Frontier lab | -78.9 | [-81.4, -76.3] | [-101.7, -55.2] | 0% | -4.5 | 0% | 12% |
| Frontier Lab (open weights) | Open weights | -40.9 | [-42.2, -39.8] | [-52.4, -29.3] | 0% | -3.1 | 0% | 12% |
| Hyperscaler cloud | hyperscaler | -50.1 | [-55.3, -44.7] | [-98.5, -0.9] | 10% | -6.3 | 0% | 12% |
| Chip designer | chips | -52.3 | [-61.3, -43.1] | [-117.0, 17.0] | 13% | -3.1 | 0% | 12% |
| Enterprise software | Enterprise software | -39.1 | [-41.6, -36.5] | [-60.0, -16.6] | 2% | -3.7 | 0% | 12% |
| Consumer AI platform | Consumer AI | -64.0 | [-66.6, -61.5] | [-86.9, -42.5] | 1% | -4.2 | 0% | 12% |
| Autonomy and robotics | autonomy | -56.8 | [-58.4, -55.0] | [-74.9, -40.9] | 0% | -2.9 | 0% | 12% |
| AI start up cohort | startups | -3.7 | [-4.4, -3.0] | [-10.3, 2.4] | 18% | -2.5 | 0% | 12% |

| Sector | Expected value change, $bn | Starting value, $bn |
|---|---|---|
| Frontier lab | -78.9 | 267 |
| Open weights | -40.9 | 60 |
| hyperscaler | -50.1 | 1,910 |
| chips | -52.3 | 2,492 |
| Enterprise software | -39.1 | 935 |
| Consumer AI | -64.0 | 507 |
| autonomy | -56.8 | 119 |
| startups | -3.7 | 91 |

The firms are synthetic archetypes of the AI value chain, not companies; the figures are the model's and carry its assumptions. Shareholder value is a market metric and a constraint; it is not part of the net social value.

## The decision gap

Ranked by how they look in the first six months (the price reaction and the early tone of the wire), the instruments are Compute threshold reporting, Transparency and disclosure, Frontier licensing, Mandatory third party evaluation, Strict liability, Liability with a safe harbour, Risk tiering (EU style), Six month moratorium above the threshold. Ranked by expected net social value over 5 years they are Liability with a safe harbour, Transparency and disclosure, Mandatory third party evaluation, Compute threshold reporting, Strict liability, Risk tiering (EU style), Frontier licensing, Six month moratorium above the threshold. Kendall tau b between the two is +0.29; the decision gap ((1 - tau) / 2) is 0.36, and the two orders invert in 0% of resamples.

## How sure we are

**Monte Carlo error.** Every expected value above carries the 95% bootstrap confidence interval of its mean over 500 resamples of the paths, paired across alternatives. The run followed its sampling plan: 120 then 240 paths, stopping when the preferred alternative was resolved against every other feasible one to within $5.0bn and the catastrophe probabilities to within 3%, or at the ceiling. The intervals are not adjusted for those sequential looks.

Convergence of the running estimate (the first paths of the run are exactly what a smaller run on this seed reports):

| Paths | Decision | Expected net social value of Liability with a safe harbour, $bn | Standard error | P(catastrophe), status quo |
|---|---|---|---|---|
| 30 | Liability with a safe harbour | 39.1 | 7.09 | 14.7% |
| 60 | Liability with a safe harbour | 33.9 | 4.93 | 14.5% |
| 120 | Liability with a safe harbour | 38.7 | 4.50 | 15.1% |
| 240 | Liability with a safe harbour | 37.4 | 3.08 | 15.2% |

The decision is the same over the last doubling of the paths, and the final estimate lies inside every earlier interval.

Split into 4 independent batches of 60 paths, the run gives the same decision in 4 of them (Liability with a safe harbour, Liability with a safe harbour, Liability with a safe harbour, Liability with a safe harbour).

**Parameters, one at a time.** Each of the 68 declared assumptions was moved to the low and the high end of its plausible range, the decision re made under each (feasibility re assessed, the status quo an alternative). Liability with a safe harbour is worth $37.4bn at the run's values. The 15 largest swings:

| Assumption | Run's value | Low | Value at low, $bn | Decision at low | High | Value at high, $bn | Decision at high |
|---|---|---|---|---|---|---|---|
| Monthly catastrophe probability | 0.0020 | 0.0005 | 28.5 | Liability with a safe harbour | 0.0050 | 167.5 | Liability with a safe harbour |
| Capability growth | 0.0230 | 0.0150 | 24.2 | Liability with a safe harbour | 0.0350 | 160.0 | Liability with a safe harbour |
| Safety elasticity of incidents | 1.80 | 1.40 | 126.6 | Mandatory third party evaluation | 3.00 | 14.8 | Transparency and disclosure |
| Trust sensitivity to harm | 0.0400 | 0.0200 | 13.7 | Transparency and disclosure | 0.0800 | 116.4 | Liability with a safe harbour |
| Median harm of a catastrophe | 400.00 | 150.00 | 30.1 | Liability with a safe harbour | 1,200.00 | 85.6 | Mandatory third party evaluation |
| Output uplift base | 400.00 | 200.00 | 21.1 | Liability with a safe harbour | 800.00 | 70.2 | Liability with a safe harbour |
| Trust elasticity of adoption benefits | 0.50 | 0.20 | 17.2 | Transparency and disclosure | 1.00 | 65.7 | Liability with a safe harbour |
| Safety spend that displaces capability R&D | 0.60 | 0.30 | 63.5 | Liability with a safe harbour | 1.00 | 19.0 | Transparency and disclosure |
| Capability elasticity of incidents | 1.30 | 0.90 | 17.3 | Transparency and disclosure | 1.80 | 60.1 | Mandatory third party evaluation |
| Share of incidents an evaluation could catch | 0.35 | 0.20 | 28.3 | Transparency and disclosure | 0.50 | 69.4 | Liability with a safe harbour |
| Median harm of a misuse incident | 0.15 | 0.0800 | 33.2 | Liability with a safe harbour | 0.30 | 72.6 | Liability with a safe harbour |
| Safety decay | 0.0200 | 0.0100 | 47.7 | Transparency and disclosure | 0.0400 | 77.2 | Mandatory third party evaluation |
| Harm valuation multiplier | 1.00 | 0.50 | 28.6 | Liability with a safe harbour | 2.00 | 55.0 | Liability with a safe harbour |
| Trust recovery | 0.0500 | 0.0300 | 45.8 | Liability with a safe harbour | 0.10 | 23.2 | Transparency and disclosure |
| Systemic incident rate | 0.0200 | 0.0100 | 21.5 | Transparency and disclosure | 0.0400 | 42.5 | Liability with a safe harbour |

The decision changes at an end of the range of 35 of the 68 assumptions; the 12 with the largest swings are Safety elasticity of incidents, Trust sensitivity to harm, Median harm of a catastrophe, Trust elasticity of adoption benefits, Safety spend that displaces capability R&D, Capability elasticity of incidents, Share of incidents an evaluation could catch, Safety decay, Trust recovery, Systemic incident rate, Weight firms put on growth, Median harm of an accident (the screen in the artefacts lists all 35). The sign of the focus option's value is robust across the screen. For 34 of them the cause is feasibility: Liability with a safe harbour stops satisfying a constraint under the alternative (on the central estimate: industry loss $386bn within the $400bn limit (satisfied in 92% of resamples)); for 3 another alternative within the constraints overtakes it. Each re simulated assumption ran on the first 4 paths, paired with the main run: 36 of the 68 swings exceed twice their Monte Carlo standard error, and a change of decision inside that error is a warning to look, not a finding.

**Parameters, all together.** 64 joint draws of every assumption over its plausible range (correlated where they plausibly move together). Under that parameter uncertainty:

| Alternative | Mean net social value, $bn | 5th to 95th percentile over the draws | Share of draws it is the decision | Share of draws within constraints | Share within constraints and above the status quo | Expected regret where within constraints, $bn |
|---|---|---|---|---|---|---|
| Liability with a safe harbour | 105.5 | [25.7, 252.7] | 39% | 42% | 42% | 1.1 |
| Transparency and disclosure | 43.8 | [17.8, 93.0] | 36% | 100% | 100% | 30.1 |
| Mandatory third party evaluation | -9.0 | [-149.9, 150.1] | 22% | 80% | 48% | 55.3 |
| Compute threshold reporting | 19.9 | [4.5, 47.1] | 2% | 100% | 100% | 54.0 |
| Risk tiering (EU style) | -60.4 | [-165.9, 49.1] | 2% | 34% | 12% | 114.6 |
| The status quo | 0.0 | [0.0, 0.0] | 0% | 100% | 100% | 73.9 |
| Frontier licensing | -129.4 | [-377.8, -3.0] | 0% | 28% | 3% | 141.7 |
| Strict liability | 11.0 | [-46.1, 92.9] | 0% | 0% | 0% | n/a |
| Six month moratorium above the threshold | -108.8 | [-264.8, -22.3] | 0% | 75% | 0% | 148.2 |

Regret is how far an alternative falls short of the best alternative within the constraints in the same draw, averaged over the draws in which it is itself within them; it is read beside the share of draws in which it is, because choosing an alternative where it breaks a constraint is not a cost in $bn. Among the alternatives within the constraints in at least 90% of the draws, Transparency and disclosure has the lowest expected regret.

The ranges are declared judgements, a prior over the assumptions and not a posterior estimated from data. The margin of Liability with a safe harbour over the best alternative moves with Monthly catastrophe probability (rank correlation +0.49), Median harm of a catastrophe (rank correlation +0.36), Correlation of catastrophes across firms (rank correlation +0.35), Safe harbour shield (rank correlation +0.35): of the 68 assumptions, 4 pass a 10% false discovery rate on that correlation. The draws in which it is the decision differ from the draws in which it is not most in Monthly catastrophe probability (Kolmogorov Smirnov distance 0.51).

**Which assumptions carry the variance.** A Sobol decomposition over the 5 assumptions with the largest swings (448 evaluations), for the value of Liability with a safe harbour and for its margin over the best alternative. Shares with interactions (total order), with the 90% interval the size of the design allows:

| Assumption | Share of the value's variance, with interactions | 90% interval | Share of the margin's variance, with interactions | 90% interval | Alone (first order), margin |
|---|---|---|---|---|---|
| Safety elasticity of incidents | 54% | 39% to 76% | 60% | 43% to 82% | 19% |
| Capability growth | 45% | 27% to 83% | 39% | 25% to 66% | 18% |
| Monthly catastrophe probability | 29% | 7% to 51% | 32% | 7% to 56% | 2% |
| Trust sensitivity to harm | 19% | 12% to 31% | 15% | 9% to 24% | 10% |
| Median harm of a catastrophe | 5% | 3% to 7% | 5% | 3% to 8% | 2% |

The intervals are wide (half width 15% on average for the margin): the output is heavy tailed in these assumptions, which compound, so a design of this size ranks groups of assumptions and does not order neighbours. Shares with interactions add to more than one when the assumptions interact, as these do: first order shares sum to 50% of the margin's variance.

**Model structure.** Under 8 alternative model structures Liability with a safe harbour remains the decision in 3 and stays within the constraints and above the status quo in 4:

| Variant | What changes | Decision | Focus option's rank among instruments | Its value, $bn | Within constraints |
|---|---|---|---|---|---|
| Myopic firms | firms plan six months ahead instead of twelve | Liability with a safe harbour | 1 | 38.7 | yes |
| Forward looking firms | firms plan two years ahead | Transparency and disclosure | 1 | 38.7 | no |
| Weak regulator | the regulator has half the stated capacity | Transparency and disclosure | 1 | 37.6 | no |
| Strong safety effect | safety practice cuts incidents faster | Compute threshold reporting | 2 | 20.7 | yes |
| Weak safety effect | safety practice cuts incidents more slowly | Mandatory third party evaluation | 1 | 66.7 | no |
| Lax offshore | offshore activity is twice as hazardous as at home | Liability with a safe harbour | 1 | 37.4 | yes |
| Heavy tail | the catastrophic tail is two and a half times more likely | Mandatory third party evaluation | 1 | 90.0 | no |
| Systemic catastrophes | catastrophic failures are strongly correlated across firms | Liability with a safe harbour | 1 | 38.3 | yes |

**Gaming.** Firms game each instrument four ways; the instrument under its worst strategy, and whether it is then still within the constraints and above the status quo:

| Instrument | Honest value, $bn | Worst strategy | Value when gamed, $bn | Harm avoided when gamed, $bn | Loss to gaming, $bn | Acceptable under every strategy |
|---|---|---|---|---|---|---|
| Transparency and disclosure | 26.9 | Threshold splitting | 26.9 | 1.6 | 0.0 | yes |
| Compute threshold reporting | 12.3 | Compliance theatre | 5.7 | 1.5 | 6.6 | yes |
| Liability with a safe harbour | 37.4 | Compliance theatre | 2.3 | -5.7 | 35.1 | no |
| Strict liability | -4.2 | Threshold splitting | -4.2 | 4.2 | 0.0 | no |
| Six month moratorium above the threshold | -114.2 | Compliance theatre | -118.9 | 5.1 | 4.7 | no |
| Mandatory third party evaluation | 18.9 | Maximal relocation | -129.4 | -3.5 | 148.4 | no |
| Risk tiering (EU style) | -68.5 | Maximal relocation | -169.9 | -12.4 | 101.4 | no |
| Frontier licensing | -103.4 | Maximal relocation | -171.7 | -1.9 | 68.3 | no |

When every instrument is gamed at its worst, the best choice is Transparency and disclosure. Strategies: Compliance theatre: mandated safety spend is reported but not spent; evaluations are gamed; Maximal relocation: firms are more mobile and moving is cheaper than assumed; Threshold splitting: models are split so the regulator sees capability 20% below the real level; Use case relabelling: deployments are relabelled into lower tiers, avoiding 60% of tier costs.

**Robustly acceptable.** Transparency and disclosure, Compute threshold reporting are within the constraints and above the status quo on the central estimate, in at least 90% of the joint draws, in every structural variant and under every gaming strategy. The preferred option is not among them: it is the best on the central estimate and not robust to the alternatives above.

**Validation against published evidence.** The model was confronted with 11 published benchmarks that bear on 10 of its 15 mechanisms. 3 of those mechanisms have a benchmark measured on AI itself; the others rest on analogues from other regulation and other technologies, each compared with an allowance for that distance. At the central assumptions the model is not contradicted by 9, is in tension with 1 (Share of the insurance loading used up by underwriting and administration) and is contradicted by 1 (Equity return when a horizontal regime becomes enforceable). Even the closest tenth of the draws of the assumptions miss Equity return when a horizontal regime becomes enforceable by more than 2 standard deviations: that is a failure of the model's form and not of a parameter value, so it is reported and left out of the weighting below. No benchmark bears on 5 mechanisms: severity, catastrophic tail, safety practice, evaluation, news.

| Benchmark | Kind | Observed (allowance, one sd) | Model at the central assumptions | z | Verdict | Model across the declared ranges, 5th to 95th | Predicted with it held out |
|---|---|---|---|---|---|---|---|
| Annual growth of recorded AI incidents | direct | 56% (sd 26%) | 42% | -0.5 | not contradicted | 28% to 66% | 45% (z -0.4) |
| Annual change in public trust in AI and AI companies | direct | -5.1% (sd 2.3%) | -6.1% | -0.4 | not contradicted | -17.0% to -2.1% | -7.4% (z -0.5) |
| Share of a fall in trust recovered about nine months after a salient incident | analogue | 20% (sd 35%) | 37% | +0.5 | not contradicted | 30% to 55% | 43% (z +0.6) |
| Compliance cost of a high risk regime as a share of development spending in scope | official | 10.8% (sd 6.9%) | 12.1% | +0.2 | not contradicted | 9.1% to 13.3% | 12.1% (z +0.2) |
| Effect of a horizontal compliance regime on the profits of firms in scope | analogue | -3.3% (sd 3.9%) | -7.4% | -1.1 | not contradicted | -9.9% to -6.0% | -8.0% (z -1.1) |
| Equity return when a horizontal regime becomes enforceable | analogue | -0.9% (sd 1.0%) | -4.8% | -3.9 | contradicted; a failure of form, left out of the weights | -5.8% to -3.6% | left out of the weights |
| Equity return of a firm when a regulatory fine is announced | analogue | -0.7% (sd 1.0%) | -0.2% | +0.5 | not contradicted | -2.2% to -0.7% | -1.1% (z -0.3) |
| Equity return of a firm when a serious incident becomes public | analogue | -1.1% (sd 1.1%) | -1.4% | -0.3 | not contradicted | -4.1% to 0.0% | -2.2% (z -0.5) |
| Share of regulated activity displaced abroad by a unilateral regime | analogue | 14.0% (sd 8.6%) | 24.8% | +1.3 | not contradicted | 0.3% to 25.2% | 17.6% (z +0.3) |
| Premium above expected claims in liability insurance | analogue | 31% (sd 15%) | 25% | -0.4 | not contradicted | 15% to 42% | 27% (z -0.3) |
| Share of the insurance loading used up by underwriting and administration | analogue | 107% (sd 25%) | 50% | -2.3 | in tension | 33% to 67% | 51% (z -2.1) |

The allowance is the benchmark's own standard error combined with a declared allowance for the distance between the setting it was measured in and the model's; z is the gap between model and observation in those units, with the Monte Carlo error of the model's value added. Not contradicted: within two; in tension: two to three; contradicted: beyond three. A benchmark is predicted with it held out from the draws weighted by all the others.

Weighting the 64 joint draws of the assumptions by how well each reproduces the 10 benchmarks it can be compared with leaves an effective 27 draws. In the weighted draws the decision is Transparency and disclosure in 39% (unweighted 36%); Mandatory third party evaluation in 32% (unweighted 22%); Liability with a safe harbour in 29% (unweighted 39%); Compute threshold reporting in 0% (unweighted 2%). 92% of the draws are ruled out by no benchmark at 3 standard deviations. Liability with a safe harbour is within the constraints and above the status quo in 36% of the weighted draws (42% unweighted). The benchmarks bear on 13 of the 68 assumptions drawn; they move most Resource share of the insurance loading (+0.7 sd), Price jump on an own incident (-0.3 sd), Capability growth (-0.2 sd), Audit rate (+0.1 sd), Revenue response to capability (-0.1 sd).

| Assumption the benchmarks bear on | Value on this run | Mean of the draws | Weighted mean | Shift, in sd of the draws | Spread kept | Through |
|---|---|---|---|---|---|---|
| Resource share of the insurance loading | 0.5 | 0.5003 | 0.5701 | +0.68 | 77% | insurance resource share |
| Price jump on an own incident | 0.5 | 0.5828 | 0.53 | -0.34 | 95% | incident return |
| Capability growth | 0.023 | 0.02431 | 0.02361 | -0.17 | 81% | incident growth, trust trend, profit effect |
| Audit rate | 0.5 | 0.5333 | 0.5478 | +0.14 | 107% | fine return, compliance cost share |
| Revenue response to capability | 0.5 | 0.5338 | 0.5193 | -0.14 | 105% | profit effect, compliance cost share |
| Insurance loading | 0.25 | 0.2836 | 0.2721 | -0.14 | 73% | insurance loading |
| Trust sensitivity to harm | 0.04 | 0.04666 | 0.04497 | -0.13 | 94% | trust trend |
| Revenue lost offshore | 0.12 | 0.1399 | 0.1436 | +0.10 | 99% | leakage share |
| Capability elasticity of incidents | 1.3 | 1.334 | 1.35 | +0.09 | 85% | incident growth |
| Safety elasticity of incidents | 1.8 | 2.067 | 2.091 | +0.07 | 102% | trust trend |

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

Indicators to watch, with the model's expectation under Liability with a safe harbour: reportable incidents a year (6.4 to 9.4 across outcomes); the share of activity offshore (0% at the horizon); the news pressure index (peak 0.32, a hearing in 0% of paths); the industry's value against the status quo (-3.8% at the horizon). Revisit the decision if incidents run above that range for two quarters, if relocation exceeds the forecast, or if any of Safety elasticity of incidents, Trust sensitivity to harm, Median harm of a catastrophe, Trust elasticity of adoption benefits, Safety spend that displaces capability R&D, Capability elasticity of incidents, Share of incidents an evaluation could catch, Safety decay can be estimated from data.

## Gates, provenance and reproduction

**Gate 1 (battery)**: approved at 2026-11-16T06:03:33 in a public demonstration, without a sign off identity; inside an authority a named approver on the register takes this gate.
**Gate 2 (release)**: approved at 2026-11-16T06:04:08 in a public demonstration, without a sign off identity; inside an authority a named approver on the register takes this gate.
**Critic**: 57 of 57 checks passed before release.
Battery hash `549dc96651fd63830949937c6ae19b5fc2454f3398af8f5bec9e926479c9fb68`; code fingerprint `28b530f37f3d12c48a159a7cb59c0eae091feb07e3b7c4b70029b020889c5c84`; PSL 1.2.0, numpy 2.5.3, scipy 1.18.1; profile demo; 25.6 seconds. Reproduce with `python -m psl.orchestrator --battery battery.json`.
