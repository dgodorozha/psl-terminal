# Response to the statistical and methodological review

Policy Scenario Lab, version 1.1.0. This document answers the review point by point: what was
reproduced, what changed, where the change sits in the code, which test holds it in place, and what
remains open. Every figure below can be regenerated with the commands in the last section.

## Summary

1. **Every finding in sections 1 and 2 of the review was reproduced on version 1.0.1 with the review's
   own numbers, and is corrected.** None was disputed.
2. **Sections 3 to 5 are implemented**: an explicit estimand and a welfare accounting map; a screen of
   every assumption, a joint draw of all of them and a variance decomposition; four kinds of uncertainty
   reported apart; a mechanism register; feasibility and acceptability re assessed under every
   alternative model and gaming strategy; a stricter validation step; decision focused robustness
   metrics; regression tests; replication across seeds.
3. **The review's reading of the bundled run was right, and for the reason it gave.** Version 1.0.1
   excluded liability with a safe harbour because its industry loss was estimated at $426.1bn on 60
   paths against a $400bn limit. Run on 480 paths, version 1.0.1's own code puts that loss at $401bn,
   $392bn and $379bn on seeds 7, 8 and 9. The exclusion was sampling error, and the option the run then
   recommended was not the one its own model prefers.
4. **The answer to the default question is now reported with the evidence of how far it can be
   trusted.** On the central assumptions liability with a safe harbour is preferred, and that is
   settled as far as Monte Carlo error goes (20 of 20 seeds). It is not robust to the model: it is the
   decision in a quarter of the joint draws of the assumptions, in two of eight alternative model
   structures, and it fails under one gaming strategy. Transparency and disclosure is worth less on the
   central estimate and is robustly acceptable. The briefing now says both.
5. **The Lab's status has not changed.** The review's closing sentence stands: a preferred option is a
   model conditional hypothesis, not a statistically established recommendation. What has changed is
   that the Lab says so itself, in the first paragraphs of every briefing, and shows how conditional.
   No mechanism is calibrated, and one of fifteen can be confronted with data. That is the main thing
   still open, and it cannot be closed by code.

## 0. Reproduction on version 1.0.1

Seed 7, 60 paths, 60 months, the bundled setup.

| Finding | The review's figure | Reproduced on 1.0.1 | On 1.1.0 |
|---|---|---|---|
| 1.1 A policy worse than doing nothing is recommended | risk tiering selected at -$77.39bn; moratorium -$98.82bn; status quo $0bn | -77.39, -98.82, risk tiering selected | the status quo is the decision; the best instrument is reported separately |
| 1.2 Intervals are outcome percentiles | mandatory evaluations +24.5, bootstrap interval of the mean -4.4 to +65.0; the top two $2.58bn apart | 24.54; about -4 to 67; 2.58 apart, paired interval about -45 to 50 | every expected value carries a 95% confidence interval; outcome percentiles are reported beside it under their own name |
| 1.3 Rare events on too few paths | 12 of 60 against 11 of 60 | 12 of 60 and 11 of 60 | 15.0% (14.7% to 15.2%) against 12.7% (12.5% to 12.9%) on 960 paths |
| 1.4 Feasibility treated as certain | safe harbour loss $426.1bn, interval $380bn to $469bn, limit $400bn | 426.1; 380 to 469 | loss $390bn (378 to 401); within the limit in 95% of resamples; 387 pooled over 20 seeds |
| 2 Gross cost not gross | $19.65bn reported, $19.79bn recomputed | 19.65 and 19.79 | one definition, never negative, gross benefit less gross cost equals the net |
| 2 Valuation base after the policy's first update | about -$245bn hidden for risk tiering in force at once | -245.4 | one valuation before any instrument, common to the battery |
| 2 Zero price accepted | NaN volatility | NaN | refused, with the reason |

## 1. High priority findings

### 1.1 The system can recommend a policy that is worse than doing nothing

Accepted in full. The status quo is now a decision alternative that scores zero. The preferred
alternative is the feasible one with the highest expected net social value; a tie goes to the status
quo, wherever it is listed. If no instrument beats it, the decision text is "No tested instrument
improves on the status quo", and the best instrument is reported separately (`best_intervention`),
as the review recommended. If nothing satisfies the constraints, the status quo included, there is no
preferred alternative and the briefing says which constraint each alternative fails.

- Code: `psl/evaluate.py` (`decide`, `best_index`, `_decision_text`).
- Tests: `test_stats.py::test_a_policy_worse_than_the_status_quo_is_never_recommended` (the review's own
  battery of risk tiering and a moratorium, and the tie cases);
  `test_pipeline.py::test_a_battery_of_instruments_worse_than_doing_nothing_ends_with_the_status_quo`
  (the same battery through the pipeline, the briefing and the critic).
- The critic refuses to arm Gate 2 if an instrument with a non positive expected value is preferred to
  a feasible status quo, and the second implementation checks the same from the stored paths.

### 1.2 Intervals do not communicate uncertainty in expected outcomes

Accepted in full. Three measures are now reported separately, under different names, in every panel,
in the briefing and in the oracle's answers:

| What is reported | Name on screen | What it measures |
|---|---|---|
| 95% bootstrap confidence interval, with a standard error | "95% interval" in square brackets after an expected value | how well the paths estimate the expectation |
| 10th and 90th percentiles of simulated outcomes | "outcomes, 10th to 90th" | how different one path can be from another |
| range under other assumptions and structures | the screen, the joint draw, the variants | how the answer moves when the model moves |

The bootstrap resamples paths, which keeps the pairing across alternatives, and one set of resamples
is used for every quantity of a run. The difference between the preferred alternative and each other
one carries a paired standard error, a pairwise interval and a simultaneous interval over all the
comparisons; the alternatives the paths cannot tell apart from the preferred one are listed as its
confidence set.

On the full profile's run of the default question (seed 7, 960 paths):

| Alternative | Expected net social value, $bn | 95% interval | Outcomes, 10th to 90th | Industry value change, $bn | 95% interval | Within constraints, share of resamples | Ranking stability |
|---|---:|---|---|---:|---|---:|---:|
| Liability with a safe harbour | 36.4 | 33.5 to 39.5 | -25.9 to 82.0 | -390 | -401 to -378 | 95% | 95% |
| Transparency and disclosure | 27.5 | 25.8 to 29.0 | 2.2 to 64.8 | 45 | 39 to 51 | 100% | 5% |
| Mandatory third party evaluation | 22.1 | 19.0 to 25.2 | -33.5 to 65.4 | -58 | -67 to -49 | 100% | 0% |
| Compute threshold reporting | 11.0 | 9.8 to 12.6 | -2.1 to 27.9 | 167 | 162 to 173 | 100% | 0% |
| Status quo | 0.0 | | | 0 | | 100% | 0% |
| Strict liability | -4.6 | -6.0 to -3.0 | -25.7 to 18.2 | -1,250 | -1,263 to -1,237 | 0% | 0% |
| Risk tiering (EU style) | -69.6 | -71.5 to -67.9 | -102.9 to -31.9 | -399 | -406 to -391 | 65% | 0% |
| Frontier licensing | -104.8 | -106.8 to -102.8 | -136.9 to -81.3 | -494 | -503 to -484 | 0% | 0% |
| Six month moratorium | -116.1 | -118.0 to -114.2 | -148.7 to -83.1 | -10 | -17 to -3 | 100% | 0% |

The confidence interval of the safe harbour's value is about $6bn wide; its outcome spread is about
$108bn wide. Version 1.0.1 printed only the second and called it an interval.

- Code: `psl/stats.py` (`Boot`), `psl/welfare.py` (`summarise`), `psl/evaluate.py`.
- Tests: `test_stats.py::test_wilson_and_bootstrap_intervals_on_known_cases`;
  `test_stats.py::test_an_interval_covers_independent_seeds_about_as_often_as_it_says`.

**Are the intervals right?** Measured rather than asserted (`docs/replication.md`): across 20
independent seeds at 480 paths, the spread of each estimate across seeds matches the standard error a
single run reports (ratios from 0.78 to 1.32 for the net social value, most within 0.1 of one), and
145 of 160 intervals for the net social value (91%), 148 of 160 for the industry value (92%) and 175 of
180 for the catastrophe probability (97%) contain the mean of the other seeds, where a perfectly
calibrated interval would manage about 94%. The intervals for the two money quantities are, if
anything, slightly narrow. They get worse on fewer paths and shorter horizons, where the benefit
arrives on very few paths: in an exploratory check at 48 paths over 24 months, 106 of 120 intervals
(88%) contained a 6,000 path reference. A studentised bootstrap and a BCa interval were tried and did
not do materially better, so the percentile interval was kept and its measured coverage is reported.

### 1.3 Rare event probabilities estimated on too few paths

Accepted, with a different method from the one the review suggests first.

**Conditional Monte Carlo.** The engine knows, in every month of every path, the probability of each
incident and of a catastrophe given the state the path has reached. Expected harm is now estimated from
those conditional expectations instead of from the incidents drawn, and the probability of a
catastrophe over the horizon from the hazard each path accumulates up to its first catastrophe
(`docs/METHOD.md`, section 8). Both estimators have the expectation of the frequencies they replace, by
the law of iterated expectations, and a small fraction of their variance. On the default question the
catastrophe probability under the status quo is 15.0% with a 95% interval of 14.7% to 15.2% on 960
paths; the raw count is 161 of 960 (a Wilson interval of 14.5% to 19.3%), and a frequency would need
more than 90,000 paths for the same precision. The one path difference the review pointed to (12 of 60
against 11 of 60) is now 15.2% against 12.9% pooled over 20 seeds, with a standard deviation across
seeds of about 0.1 points each.

Importance sampling was considered and not used. A change of measure over a five year path with eight
firms and four kinds of draw needs likelihood ratio weights whose variance grows with the horizon, and
its validation is delicate; the conditional expectation is exact given the state and needs none. The
raw count is still reported beside every probability, with a Wilson interval.

**Adaptive sampling.** A battery now declares the paths it starts on, a ceiling and precision targets,
all part of the hash approved at Gate 1. It doubles, on the same random streams, until the preferred
alternative is resolved against every other feasible one, the catastrophe probabilities are within
their target, and no decision relevant feasibility is split, or until the ceiling is reached; anything
still unresolved is listed in the briefing, the ledger and the panels. The profiles are 480 paths
growing to at most 3,840 (full), 240 to 960 (light) and 120 to 480 (demo), in place of 240, 120 and 60.
The default question stops at 960 paths in the full profile, with every target met.

**What is still estimated from the draws.** The consequences of the incidents that were drawn (lost
trust, slower adoption, market reactions) feed back into the path and are not integrated out. For
several instruments the largest benefit is not the harm avoided directly but the adoption that higher
trust allows, and that component carries the variance of the rare events drawn. It is what the
confidence intervals above are made of and what the sampling plan works on. It is also a modelling
matter: see 3.1 and "What remains open".

- Code: `psl/economy.py` (the conditional expectations), `psl/reduce.py` (`conditional_catastrophe`),
  `psl/pipeline.py` (the sampling plan), `psl/evaluate.py` (`precision`), `config.py` (the profiles).
- Tests: `test_stats.py::test_conditional_estimators_are_unbiased_and_far_tighter` (2,400 paths: paired
  z scores against the frequencies below 3.5, variance below 2% of theirs);
  `test_pipeline.py::test_adaptive_sampling_grows_the_battery_on_the_same_streams` (a battery grown from
  8 to 32 paths is path for path the battery run on 32).

### 1.4 Feasibility treated as certain

Accepted in full. Feasibility is re assessed inside every bootstrap resample. Each alternative carries,
for each constraint and for all of them together, the share of resamples in which it is within the
limits, with the interval of the constrained metric and its margin to the limit. The ranking stability
uses the same resamples, so an alternative that is sometimes infeasible is sometimes not the best. A
conservative rule is reported beside the expected value rule: the preferred alternative among those
within the constraints in at least 90% of resamples. With one binding constraint that is the same as
requiring a one sided 90% upper confidence bound of the constrained metric to be within its limit;
with several it is stricter. When the two rules disagree the briefing says so in its first paragraph.

The safe harbour is the case the review picked, and it shows the whole mechanism. On seed 7 its share
of resamples within the $400bn limit is 37% at 120 paths, 60% at 240, 83% at 480 and 95% at 960; the
sampling plan keeps adding paths because of it. Across 20 seeds at 480 paths it is preferred under the
expected value rule in all 20, and under the conservative rule in 13, with transparency and disclosure
taking the other 7. Pooled over those seeds its industry loss is $387bn with a standard error of about
$1.3bn: within the limit, by 3%.

- Code: `psl/evaluate.py` (`feasible_mask`, `constraint_values`, the `p_feasible` and `p_ok` fields,
  `ASSURED_P`).
- Test: `test_stats.py::test_feasibility_at_a_boundary_is_reported_as_uncertain`.

## 2. Calculation and implementation issues

| Finding | Verdict | What changed | Test |
|---|---|---|---|
| Gross social cost is not consistently gross | Reproduced (19.65 against 19.79) | Gross cost is the sum of the expected component changes that are costs: positive cost components and negative benefit components. Gross benefit is the mirror image. Both are non negative and differ by the net social value; net economic cost is reported separately. The definition is applied to expected values, so it is the same in the point estimate, in every resample and under every alternative assumption. | `test_stats.py::test_gross_cost_is_never_negative_and_reconciles_with_the_net_value`; `test_core.py::test_welfare_identities_and_baseline_scores_zero` |
| Major incidents counted on firm month totals | Reproduced | Every incident is classified on its own harm. Two minor incidents at one firm in one month are two minor incidents; catastrophes are counted apart. | `test_core.py::test_incidents_are_classified_one_by_one` (asserts on a sample that contains firm months whose total passes the threshold with no single incident above it) |
| Market valuations start after each policy's first update | Reproduced (-$245.4bn) | One valuation of the firms as they stand before any instrument is announced, the same for the whole battery. An instrument in force from the first month shows in the first month's price. The anticipation term now applies only to an instrument announced before it takes effect. | `test_core.py::test_every_index_starts_from_one_pre_intervention_valuation` |
| Rankings mishandle ties | Reproduced | Equal scores share a rank (1, 1, 3). The decision gap uses Kendall's tau b. Identical instruments under different names get identical ranks in either order, a difference of exactly zero and a place in the confidence set. | `test_stats.py::test_identical_policies_share_a_rank_and_ties_do_not_move_tau` |
| Input validation accepts invalid prices | Reproduced (NaN) | The data desk refuses zero, negative and non finite prices, dates that are not ISO dates, and gaps in the monthly series, each with the reason. While testing this a second defect turned up: the personal identifier scan read the digits after a decimal point as a possible card number, so a price such as 153.72999572753906 could be refused as personal data. Fixed. | `test_stats.py::test_the_data_desk_refuses_what_would_corrupt_an_estimate`; `test_security.py::test_quarantine_refusals` |
| Event study inconsistent with its documentation | Reproduced (23 returns; short windows accepted) | One event time convention, stated in the code, the method document and the output: the 24 returns before the event month, all 24 required or the study is refused; the 6 returns from the event month. The cumulative abnormal return carries a standard error that includes the estimation error of the market model. | `test_stats.py::test_event_study_uses_one_convention_and_the_full_window`; `test_stats.py::test_event_study_test_has_the_right_size` (no event: the test rejects between 4% and 9% of the time) |
| Discount timing misaligned | Reproduced | One convention: a monthly flow is discounted at the end of its month, `(1 + r)^(-t/12)` for t = 1 to H; a value at the horizon by `(1 + r)^(-H/12)`, the same date as the last flow. | `test_core.py::test_welfare_identities_and_baseline_scores_zero` |

The review notes that a stated definition and its implementation differed. Two measures now guard
against that class of error. `tools/recompute.py` is a second implementation of the accounting and
the decision rule, written from the method document with numpy alone and importing nothing from the
Lab; on the run above all 237 figures it recomputes agree with the Lab's to within the single
precision the paths are stored in, and it catches a gross cost changed by $0.14bn, the size of the
discrepancy the review found. And the tables of `docs/METHOD.md` are generated from the code, with a
test that fails when they drift.

## 3. Methodological cohesion

### 3.1 A consistent welfare estimand

Accepted. The estimand is stated at the top of `psl/welfare.py` and in section 2 of the method
document as the review writes it, `dW(P) = E[W(P) - W(SQ)]`, with its standing (residents), its unit
($bn of present value), its timing convention and its counterfactual (the status quo path on the same
random numbers).

**The accounting map.** `welfare.ACCOUNT_MAP` connects every monetary flow the simulation records to
exactly one line: a welfare component, a transfer, or a market metric. It is printed in the method
document, shipped in every run's artefacts, and tested for completeness.

**Double counting.** The three benefit components are separated by definition. Consumer surplus is
households' non market surplus from AI services. The output uplift is value added in the sectors that
adopt AI net of what they pay AI providers, so it excludes the AI sector's own profit. Producer surplus
is the AI sector's operating profit before compliance, fines, liability, premiums and relocation, each
of which is counted once elsewhere or is a transfer. This is the weakest part of the answer to the
review, and it should be read as such: the separation is a declaration. The two benefit bases are
declared annual values, and nothing in the simulation derives one from the other, so the code cannot
show that they do not overlap. What it can do is make the judgement explicit and movable. A new
assumption, `benefit_overlap_share`, removes from the output uplift whatever share an analyst judges to
be already in the other two components. It is zero by default and the screen moves it to one half: the
safe harbour's value falls from $36.4bn to $20.4bn and the decision does not change.

**The four items the review names.**

| Item | Treatment |
|---|---|
| Offshore leakage | Residents' rents (wage premia, tax base) on activity that moved. The firms' own profit loss from moving is in operating profit and is not counted again. |
| Compliance expenditure | A resource cost for its deadweight share; the rest is rent to compliance providers, a transfer, and appears in the incidence table. |
| Insurance loading | Previously a pure transfer. Now a resource cost (underwriting, administration) for a declared share of it, a new component; the insurer's margin and expected claims remain transfers. |
| Relocation | A one off resource cost; counted in full. |

Transfers (fines, liability, premiums, claims) are excluded whoever pays. Because standing is
residents and part of the firms is owned abroad, what non resident owners finance of the firms'
payments is reported as a memorandum item. The incidence table follows the money and sums to the net
social value plus that item, an identity the critic checks on every run.

- Tests: `test_core.py::test_welfare_identities_and_baseline_scores_zero`;
  `test_core.py::test_welfare_only_assumptions_never_reach_the_simulation`.

### 3.2 Comprehensive sensitivity analysis

Accepted. There are now 68 declared assumptions: the 60 the review counted, five that were constants
buried in the engine, and three new ones. Each has a plausible range, distinct from the bounds the Lab
will accept from a user, and a short title.

| Stage | What it does | On the default question (full profile) |
|---|---|---|
| Screen | All 68, one at a time, to both ends of the plausible range, with the decision re made at each end, the Monte Carlo standard error of each swing, and the cause of each change of decision | the decision changes at an end of the range of 36 assumptions: for 32 because the safe harbour's industry loss crosses the limit, for 8 because another alternative overtakes it; 41 of 68 swings exceed twice their standard error |
| Joint draw | All 68 together: a Latin hypercube, triangular distributions on the ranges, a Gaussian copula for five groups that plausibly move together; 256 draws | transparency and disclosure is the decision in 70% of draws, the safe harbour in 25%, mandatory evaluation in 4%; the safe harbour is within the constraints in 41% |
| Variance decomposition | Sobol indices over the 8 assumptions with the largest swings, with bootstrap intervals; 2,560 evaluations | with interactions, capability growth carries 52% of the variance of the decision margin (38% to 63%), the capability elasticity of incidents 48% (35% to 64%), the share of safety spend that displaces capability research 29%, trust sensitivity to harm 23%; first order shares sum to 46%, so about half the variance comes from interactions |

The tornado survives as a view of the screen's fifteen largest swings. The assumptions the review named
as omitted (capability growth, safety learning, severity dispersion, the base hazards, enforcement) are
all in the screen, and the first of them is the largest swing in the model.

The joint draw also reports which assumptions the answer moves with, in two ways: the rank correlation
of each with the decision margin, and Monte Carlo filtering (the Kolmogorov Smirnov distance between an
assumption's values in the draws where the focus option is the decision and where it is not). With 68
assumptions tested against one output some would pass by chance, so an assumption is called a driver
only if it survives a 10% false discovery rate.

Two cautions belong here. The screen re simulates on a subset of the paths (32 in the full profile, 4
in the demo), which is why every swing now carries its standard error and the briefing counts how many
are resolved. And the Sobol shares converge slowly, because the output is heavy tailed where capability
growth and its elasticity compound: the intervals are wide, and the decomposition ranks groups of
assumptions without ordering neighbours. Both are stated where the numbers appear.

- Code: `psl/assurance.py` (`screen`, `joint_draw`, `variance_decomposition`), `psl/assumptions.py`
  (`RANGE`, `CORRELATED`, `sample`), `psl/stats.py`. Every sensitivity design runs in one vectorised
  pass: an assumption may take one value per path, which is tested to be the same computation as a
  scalar.
- Tests: `test_pipeline.py::test_assurance_is_paired_with_the_main_run`;
  `test_pipeline.py::test_an_alternative_that_changes_nothing_reproduces_the_headline`;
  `test_stats.py::test_sobol_indices_recover_known_functions` (an additive function and the Ishigami
  function); `test_stats.py::test_latin_hypercube_copula_and_triangular_margins`;
  `test_stats.py::test_false_discovery_control_and_filtering`.

### 3.3 Separate the kinds of uncertainty

Accepted. The four kinds in the review's table are reported under separate headings in the briefing
and in the assurance panel: the outcome spread beside every expected value; Monte Carlo error
(intervals, convergence, batches, replication); parameter uncertainty (screen, joint draw, variance);
and structural uncertainty (variants, red team).

P(best) is renamed **ranking stability** everywhere. Its definition is printed with it: the share of
bootstrap resamples of the paths in which an alternative is the best feasible one, conditional on the
model and its assumptions, and not the probability that it is best in the world. The share of joint
draws in which an alternative is the decision is reported separately and is not given that name
either: it is conditional on the model structure and on a prior over the assumptions.

The two numbers disagree on the default question, which is the point of keeping them apart. Ranking
stability says 95% for the safe harbour. The joint draw says 25%.

### 3.4 The causal interpretation

Accepted. `psl/mechanisms.py` is a register of the model's fifteen causal mechanisms. For each it
records the functional form, the assumptions it uses, what it rests on, its identifying assumption, how
it would be calibrated, what observation would test it, and its status. It is printed in the method
document, shipped in every run's artefacts, shown in the assurance panel, and the critic checks that
every assumption belongs to a mechanism in it. Its summary is not flattering and is printed in every
briefing: of fifteen mechanisms, one can be confronted with data in the Lab and none is calibrated.
The sources it cites bracket magnitudes or motivate a form; no parameter is estimated from them.

The distinction the review draws, between what a policy does inside the model and what it would do in
the industry, is now stated in the opening paragraphs of every briefing and on the terminal's front page.

**Correlated catastrophes.** Catastrophes are no longer independent across firms given the state. A
common factor drawn each month joins them through a one factor Gaussian copula with a declared
correlation (0.3 by default, 0 to 0.6 in the screen, 0.8 as a structural variant). Each firm's own
probability is unchanged; joint failures become more likely, and the probability that at least one
firm fails in a month is computed by quadrature. Under the systemic variant the decision on the
default question changes to transparency and disclosure.

One limit of this should be stated. The copula changes how catastrophes cluster. It does not make a
joint failure worse than the sum of its parts: harm is still added across firms. A model in which
simultaneous failures amplify one another would give correlation a larger role than it has here.

- Tests: `test_stats.py::test_correlated_catastrophes_integrate_to_the_brute_force_probability` (the
  quadrature against 1.5 million brute force draws);
  `test_stats.py::test_catastrophe_correlation_changes_clustering_not_the_marginal_rate`.

### 3.5 Risk constraints and robustness

Accepted. Every assurance stage now re makes the decision: feasibility is re assessed against the
question's constraints under each alternative assumption, structure and gaming strategy, and the status
quo is an alternative in each. The earlier code carried the central feasible set forward, as the review
says.

- **Structural variants** report the decision, and the focus option's rank, value and feasibility,
  under each of eight structures.
- **The red team** asks the question the review asks: is the instrument still acceptable (within the
  constraints and above the status quo) when gamed? It reports that for each of four strategies, and the
  maximin choice among the instruments that stay within the constraints under all of them.
- **Robustly acceptable** is defined and reported: acceptable on the central estimate, in at least 90%
  of the joint draws, in every structural variant and under every gaming strategy.

On the default question the distinction the review asks for is sharp. The safe harbour is the high
performing option. It remains the decision in 2 of 8 structural variants and acceptable in 3; under
compliance theatre its value falls from $36.4bn to -$2.2bn and it leaves the constraints. Transparency
and disclosure and compute threshold reporting are the robustly acceptable options, and transparency is
the maximin choice. The briefing ends its robustness section with the sentence "The preferred option is
not among them: it is the best on the central estimate and not robust to the alternatives above."

### 3.6 External validation

Accepted as far as code can take it, which is not far. This is the main open item.

What changed: the event study has one convention and a standard error; a series that calibrates a
firm's volatility and beta is cut at the event month, so the event window is held out from the
parameters it is compared with; an observation is compared with the model only when the analyst names
the instrument the event is an analogue of, against the model's predictive distribution for that
instrument and firm (mean, band, probability integral transform, z score); and the output says in
terms that one event cannot establish calibration. With eight or more mapped events the Lab reports the
coverage of the model's 80% band with an exact binomial test.

What did not change: the Lab has no observed incident, compliance, relocation or adoption data, so the
mechanisms the welfare result depends on remain untested. The register documents, mechanism by
mechanism, what evidence would test each and that it is unavailable here, as the review asks. On the
bundled sample event (synthetic) the observation falls outside the model's band, and the output reports
that as it is.

## 4. The suggested sequence

| Step in the review | Status | Where |
|---|---|---|
| 1. Decision logic and accounting definitions | done | 1.1, section 2 |
| 2. Statistically appropriate uncertainty reporting | done: confidence intervals for expected values and differences, standard errors, convergence tables, batches, feasibility probabilities; outcome percentiles kept separate | 1.2, 1.4 |
| 3. Rebuild the sensitivity framework | done: all 68 assumptions screened, interactions through the joint draw and total order indices, constraints evaluated under every variant, parameter uncertainty propagated | 3.2, 3.5 |
| 4. Make the welfare framework auditable | done as accounting: estimand, map, identities, a second implementation. The separation of the benefit components remains a declaration | 3.1 |
| 5. Empirical validation and falsification tests | partly: inputs validated, the event study made credible, the mechanisms documented as uncalibrated. No test against observed behaviour | 3.6 |
| 6. Decision focused robustness metrics | done: the share of resamples and of joint draws in which the value is above zero, the share in which each constraint holds, expected regret, the robustness table | below |

**The metrics of step 6, and where they are.** The probability of positive net social value is
reported three ways, because it has three meanings: the share of simulated paths above zero (outcome
spread), the share of resamples in which the expected value is above zero (Monte Carlo), and the share
of joint draws above zero (parameter uncertainty). The probability of satisfying each constraint is
`p_ok` per constraint and `p_feasible` overall, over resamples, and again over joint draws. Expected
regret is measured against the best alternative within the constraints in the same joint draw, over the
draws in which the alternative is itself within them, and is read beside the share of draws in which
it is: regret measured without the constraints would make an option that breaks them look safe.

## 5. Tests and replication

The suite has 56 tests, from 26: 17 on the library, the engine and the accounting, 15 on the
estimators, intervals, designs and the event study, 11 on the pipeline, the critic and the tools, 5 on
security and 8 on the server. The three regression tests the review asks for are there under plain
names. The server tests are skipped with a message, not errors, where Flask or Dash is not installed.
A workflow (`.github/workflows/tests.yml`) runs the suite and the document check on every push.

**Seeds.** The review is right that three runs on seed 7 are not replications. Three things changed.
`tools/replicate.py` repeats a question on independent seeds and reports the decision frequency, the
spread of each estimate against its reported standard error, and interval coverage;
`docs/replication.md` is its output for the default question on 20 seeds. A question can name its seed
("seed 11"), so a replication can be run from the terminal. And the bundled replay now records four
runs on four seeds, the second being the default question again on the next seed.

## What changed in the answer to the default question

| | Version 1.0.1, bundled run | Version 1.1.0 |
|---|---|---|
| Paths | 60 | 480, grown to 960 by the sampling plan |
| Preferred | Mandatory third party evaluation, $24.5bn | Liability with a safe harbour, $36.4bn (33.5 to 39.5) |
| Liability with a safe harbour | excluded: loss $426.1bn against a $400bn limit | within the limit: loss $390bn (378 to 401), in 95% of resamples |
| Replication | none | preferred in 20 of 20 seeds at 480 paths; in 13 of 20 under the conservative rule |
| Robustness | not assessed against the constraints | the decision in 25% of joint draws and 2 of 8 structures; fails under compliance theatre |
| Robustly acceptable | not defined | Transparency and disclosure; compute threshold reporting |

The change of preferred option owes more to the number of paths than to the corrections. Version
1.0.1's own code, run on 480 paths, already ranks the safe harbour first (expected net social value
$33bn, $42bn and $38bn on seeds 7, 8 and 9, against $21bn, $22bn and $16bn for mandatory evaluation)
with an industry loss either side of the limit. The corrections moved the figures by less than the
sampling error of the original run.

What a reader should take from the new answer is the pair, not the first name. The safe harbour has
the highest expected value on the central assumptions, by about $9bn over transparency and disclosure,
and sits about 3% inside a hard limit. About two thirds of its gross benefit ($31.9bn of $49.4bn)
comes through one channel, the adoption that higher public trust allows, which rests on three
assumptions with no causal estimate behind them; at the low end of the plausible range of the first of
them its value is $5bn. The harm it avoids directly is $17.6bn. Transparency and disclosure is worth
less and survives everything the assurance stage does to it. Which of the two a policymaker should
prefer is a judgement about how much weight to put on the central assumptions, and the Lab now presents
it as one.

## Where the response departs from the recommendation

- **Rare events**: conditional Monte Carlo, not importance sampling (1.3).
- **Conservative rule**: a share of resamples within the constraints, at 90%, in place of an upper
  confidence bound per metric. The two coincide for one binding constraint. The 90% is a choice.
- **Structural uncertainty**: alternative structures reported as scenarios. The review's table also
  mentions model comparison; with no data to weigh one structure against another there is nothing to
  compare them on, so none is attempted.
- **Bootstrap**: percentile intervals, with measured coverage, in place of a more elaborate interval
  that did not perform better here.
- **Sequential looks**: the intervals are not adjusted for the looks of the sampling plan (at most
  four). This is stated wherever the plan is described. A group sequential correction is not
  implemented.

## What remains open

1. **Validation.** No mechanism is calibrated. Incident hazards, the catastrophic tail, the firms'
   compliance and relocation responses and the trust channel are declared assumptions with ranges that
   are judgements. Until some of them are confronted with data, every result is conditional on them,
   and the joint draw is a prior, not a posterior.
2. **The trust channel.** The largest benefit of the preferred option is indirect, and the mechanism
   behind it has no causal estimate in the literature reviewed. It is the first thing an empirical
   programme should address, and the screen shows the decision changes at the low end of its range.
3. **Overlap between benefit components.** Separated by definition, adjustable by a declared share,
   not measured.
4. **The plausible ranges.** Sixty eight judgements. The ranges of the fifteen value judgements were
   already in version 1.0.1; the other fifty three were set for this revision and deserve review by
   people who know each mechanism.
5. **Correlation between assumptions.** Five groups are drawn together. Other dependencies are ignored.
6. **Simultaneous failures.** Correlated, not amplified (3.4).
7. **Interval coverage.** Slightly below nominal for the money quantities at the default size, and
   lower on few paths and short horizons (1.2).
8. **Precision of the sensitivity stages.** The screen and the variance decomposition run on subsets of
   the paths and report their own error; in the demo profile that error is large.

## Addendum, version 1.2.0: a validation layer

Section 3.6 above ends on what code could not do: confront the mechanisms with evidence. Version 1.2.0
adds the part of that which the published literature allows, and reports its limits with it. The
method is in `docs/METHOD.md`, section 13; nothing in sections 1 to 5 of this response changes, and
every figure of a 1.1.0 run is reproduced number for number.

**What it does.** An evidence base (`psl/benchmarks.py`) holds eleven published benchmarks, each with
its source, its standard error, the model quantity it is compared with and a declared allowance for
the distance between the setting it was measured in and the model's. Two are measured on AI itself (the
growth of recorded incidents, the trend of public trust in AI and AI companies), one is the
Commission's ex ante cost estimate for the AI Act, and eight are analogues: what the GDPR did to
profits and share prices, carbon leakage, the market's reaction to cyber incidents and to fines, the
recovery of trust in autonomous vehicles after the 2018 crashes, and the loading and expenses of
property and casualty insurance. On every run each benchmark is compared with the model's own value
of the same quantity, at the central assumptions and in every draw of the joint draw; the draws are
then weighted by how well each reproduces the benchmarks, and the decision is reported before and
after. The set in force is hashed into the battery approved at Gate 1, and an authority replaces or
extends it with its own data.

**What it shows on the default question** (full profile, seed 7, 960 paths, 256 joint draws):

| Benchmark | Kind | Observed (allowance, one sd) | Model, central assumptions | Verdict |
|---|---|---|---|---|
| Annual growth of recorded AI incidents | direct | 56% (26%) | 42% | not contradicted |
| Annual change in public trust in AI and AI companies | direct | -5.1% (2.3%) | -6.3% | not contradicted |
| Share of a fall in trust recovered about nine months after a salient incident | analogue | 20% (35%) | 37% | not contradicted |
| Compliance cost of a high risk regime as a share of development spending in scope | official | 10.8% (6.9%) | 12.1% | not contradicted |
| Effect of a horizontal compliance regime on the profits of firms in scope | analogue | -3.3% (3.9%) | -7.4% | not contradicted |
| Equity return when a horizontal regime becomes enforceable | analogue | -0.9% (1.0%) | -4.8% | contradicted: a failure of form |
| Equity return of a firm when a regulatory fine is announced | analogue | -0.7% (1.0%) | 0.0% | not contradicted |
| Equity return of a firm when a serious incident becomes public | analogue | -1.1% (1.1%) | -1.1% | not contradicted |
| Share of regulated activity displaced abroad by a unilateral regime | analogue | 14.0% (8.6%) | 24.8% | not contradicted |
| Premium above expected claims in liability insurance | analogue | 31% (15%) | 25% | not contradicted |
| Share of the insurance loading used up by underwriting and administration | analogue | 107% (25%) | 50% | in tension |

Three things follow.

1. **One mechanism fails, and it is a failure of form.** The model prices the cost of an instrument
   in the month it takes effect: under risk tiering its index falls 4.8% that month against the status
   quo. When the GDPR became enforceable, share prices of exposed firms fell by 0.6% to 1.1%, the cost
   having been capitalised earlier. No draw of the assumptions comes near the observation, so this is
   not a parameter to tune: the market module anticipates too little. It affects the early reaction
   and the decision gap, which rest on the timing of prices. It does not affect the industry value at
   the horizon, which the constraint is tested on.
2. **The declared range of one assumption sits below the evidence.** The model treats between a
   quarter and three quarters of the insurance loading as a real resource cost. In the US property and
   casualty aggregate for 2022 and 2023, expenses used up all of it. At a share of one the safe
   harbour's insurance administration cost roughly doubles, from $1.6bn; the decision does not change.
3. **The evidence does not move the answer.** Weighted by the ten benchmarks that enter the weights
   (an effective 76 of the 256 draws), the safe harbour is the decision in 22% of the draws against 25%
   unweighted, and transparency and disclosure in 73% against 70%; 79% of the draws are ruled out by
   no benchmark. The answer of section "What changed in the answer" stands as it was, including its
   fragility.

**What it does not do.** No mechanism is estimated from data. Five of the fifteen have no benchmark
at all: severity, the catastrophic tail, safety practice, evaluation and the news. "Not contradicted"
is a weak verdict where the allowance is wide, and for the analogues it is. The allowances are
judgements, stated with their reasons. Most to the point of the previous section: nothing here
identifies the elasticity of realised adoption to trust. The one large body of evidence found (a meta
analysis of 128 samples) gives a correlation of 0.50 between trust and the intention to use a
technology, which supports the sign of the channel and cannot be turned into an elasticity; and the
benchmark that does bear on the trust channel, the fall in trust over five years, constrains how fast
trust falls under the status quo, not what a fall costs. The evidence examined and set aside is
listed in the method document with the reason for each.

**What remains open, revised.** Items 1 and 2 of the list above now read: the model has been
confronted with what the literature offers and survives most of it, at wide allowances; its market
module is contradicted on the timing of prices; and the largest benefit of the preferred option still
runs through a channel whose strength no evidence found constrains.

## How to check this response

    pip install -r requirements.txt pytest
    python -m pytest tests -q                              # 64 tests
    python tools/sync_docs.py --check                      # the method document's tables match the code

    # the default question, full profile: about two minutes on two cores (four in 1.1.0)
    PSL_DEV_MODE=on PSL_SECRET=k python -m psl.orchestrator --profile full --approve-battery --approve-briefing \
        --preparer Developer1 --preparer-role Developer1 --approver Developer2 --approver-role Developer2 --outdir runs/full
    python tools/recompute.py runs/full                    # a second implementation recomputes 237 figures

    # the review's battery: every instrument worse than doing nothing
    PSL_DEV_MODE=on PSL_SECRET=k python -m psl.orchestrator --profile demo --question "Compare risk tiering and a moratorium over five years" \
        --approve-battery --approve-briefing --preparer Developer1 --preparer-role Developer1 \
        --approver Developer2 --approver-role Developer2 --outdir runs/status_quo

    python tools/replicate.py --seeds 20 --paths 480 --out docs/replication.json     # about a minute

    # the validation layer: the benchmarks are in the briefing and in runs/full/assurance.json under validation
    python tools/cost.py --profile demo                    # what a run costs, by stage
