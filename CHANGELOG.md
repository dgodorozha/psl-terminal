# Changelog

## 1.2.0

A validation layer, and a cheaper pipeline. Every figure a 1.1.0 run reports is unchanged: the same battery
gives the same results, paths and assurance stages, number for number (checked on the demo and full profiles
and on 112 engine cases by hash); the validation results are new.

Validation layer
- An evidence base (`psl/benchmarks.py`): eleven published benchmarks, each with its source, standard error, the
  model quantity it is compared with and a declared allowance for its distance from the model; and the evidence
  that was examined and set aside, with the reason. Replaced or extended with `PSL_BENCHMARKS` or `--benchmarks`;
  the set in force is hashed into the battery approved at Gate 1.
- Every benchmark against the model at its central assumptions (not contradicted, in tension, contradicted) and
  across the joint draws; the joint draws weighted by the benchmarks, with the decision shares before and after,
  the effective number of draws and the share no benchmark rules out; each benchmark predicted with it held out;
  the assumptions the benchmarks bear on. A benchmark no draw comes near is reported as a failure of the model's
  form and left out of the weights.
- The mechanism register of a run carries the benchmarks that bore on each mechanism. The briefing, the
  assurance panel, the oracle and the transparency record report the layer; the critic checks it (six checks).

Running cost
- The engine's monthly decision computes each term only on the action axes it depends on, skips terms an
  instrument sets to zero and evaluates the hazard's exponential once per distinct safety share; the original
  is kept as `_decide_reference` and a test asserts the two return the same bits. The catastrophe integral
  evaluates the normal distribution only for firms with a live tail. On two cores a demo run takes 26 seconds
  where it took 42, a light one 52 where it took 98, a full one 99 where it took 232.
- `PSL_REUSE=on`: a battery identical to a completed run replays its stored figures and stream instead of
  simulating again; the critic recomputes them, and the ledger and the briefing say which run computed them.
- The page stops polling ninety seconds after the last input unless a run is in progress, so an open tab no
  longer keeps a metered host awake.
- Modal: one core and 1 GiB requested (four and 4 GiB before), bursting when the worker has room, a ten minute
  window, reuse on. Idle time after a visit costs about a fifth of what it did; an idle open tab costs nothing.
- `tools/cost.py` measures a run by stage and prices it.

## 1.1.0

Statistical and methodological revision, in answer to an independent review (`docs/REVIEW_RESPONSE.md`).
Results are not comparable with 1.0.x: the estimators, the timing convention, the valuation base and
one welfare component changed.

Decision rule
- The status quo is a decision alternative. An instrument is preferred only if its expected net social
  value is above zero; otherwise the answer is that no tested instrument improves on the status quo,
  and the best instrument is reported separately. A tie goes to the status quo.
- Feasibility is re assessed in every bootstrap resample: each alternative carries the share of
  resamples in which it satisfies each constraint, and the preferred option under a conservative rule
  (within the constraints in at least 90% of resamples) is reported beside the point estimate's.
- Equal scores share a rank; the decision gap uses Kendall's tau b.
- A condition in the question that the Lab cannot test is reported before Gate 1 as not applied.

Uncertainty
- Three intervals, kept apart everywhere: the 95% bootstrap confidence interval of every expected
  value, the 10th to 90th percentile spread of simulated outcomes, and the range under other
  assumptions and structures. Paired differences against the preferred alternative carry pairwise and
  simultaneous intervals. "P(best)" is renamed ranking stability and described as conditional on the model.
- Conditional Monte Carlo for expected harm, expected liability and the probability of a catastrophe
  (unbiased, a small fraction of the variance). Raw counts keep Wilson intervals.
- Adaptive sampling: a battery declares the paths it starts on, a ceiling and precision targets, all
  hashed at Gate 1; it doubles on the same random streams until the targets are met or the ceiling is
  reached, and says what is unresolved. Profiles: 480 to 3,840 (full), 240 to 960 (light), 120 to 480 (demo).
- Convergence table, independent batches, and `tools/replicate.py` for replication across seeds; a
  question can name its seed.

Model and accounting
- One pre intervention valuation for the whole battery; an instrument in force at once shows in the
  first month's price.
- Incidents are classified one by one; catastrophes are correlated across firms through a one factor
  Gaussian copula (`catastrophe_correlation`).
- One timing convention: flows discounted at the end of their month, values at the horizon by the
  horizon's factor.
- Gross cost and gross benefit are defined on the expected component changes, never negative, and
  differ by the net social value. A welfare accounting map assigns every simulated flow to one line.
  Standing is residents; a new component, the resource share of the insurance loading; a declared
  overlap share for the output uplift; an incidence table with an identity the critic checks.
- 68 declared assumptions, each with a plausible range and a title: five were constants in the code
  and three are new (the correlation of catastrophes, the resource share of the insurance loading, the
  overlap share).

Assurance
- A screen of every assumption with the decision re made at each end, the Monte Carlo error of each
  swing and the cause of each change of decision (feasibility or value); a joint draw of all assumptions
  (Latin hypercube, correlated groups) with the share of draws in which each alternative is the decision,
  feasible and acceptable, expected regret, drivers at a 10% false discovery rate and Monte Carlo
  filtering; a Sobol decomposition with intervals; eight structural variants and four gaming strategies
  with feasibility and acceptability re assessed; a robustness table.
- Validation: one event time convention with the full 24 return estimation window or a refusal,
  standard errors, held out calibration, comparison with the model only for a named analogue, a
  coverage test once eight events are mapped. A mechanism register: for each of fifteen mechanisms its
  source, identifying assumption, calibration, test and status.
- The data desk refuses zero, negative and non finite prices, dates that are not ISO dates and gaps in
  the months; the personal identifier scan no longer reads a long decimal price as a card number.

Verification
- The critic: 51 checks on a run that meets its precision targets and 52 on one that does not (the
  extra check is that the briefing says what is unresolved), including that the artefacts the briefing
  is drafted from are the documents it recomputed.
- `tools/recompute.py`: a second implementation of the accounting and the decision rule, numpy only.
- `tools/sync_docs.py`: the tables of `docs/METHOD.md` are generated from the code and tested.
- Tests rewritten around the estimators and the decision rule, including the regression tests the
  review asked for.
- scipy is now a dependency.

## 1.0.1

- Open gates (`PSL_GATES=open`) for the public demonstration: the two gates are single clicks with no
  preparer or approver identities, register or four eyes; every gate record carries `open_gate`, and
  the run status, briefing, transparency record and posture page say so. Named gates stay the default.
  The replay site is recorded with open gates; the Dockerfile and `modal_app.py` set them.
- Live terminal hosted on Modal (`modal_app.py`: one container, scaled to zero between visitors, run
  registry on a persistent volume) with `.github/workflows/deploy-modal.yml` redeploying on push. The
  Hugging Face Space route is kept as a Docker host option only: Docker Spaces now require a PRO
  subscription. `sync-to-hf.yml` removed; README front matter removed.

## 1.0.0

First release of the Policy Scenario Lab terminal.

- Agent based synthetic AI economy (eight firm archetypes, regulator, public trust, four media
  agents, market) stepped monthly on common random numbers with per path streams, so smaller
  re simulations pair with the main run.
- Library of fifteen regulatory instruments as bounded JSON documents; custom instruments, firm
  templates and assumption overrides from the terminal.
- Welfare accounting (harm avoided, consumer surplus, output, resident producer surplus, compliance,
  enforcement, leakage, relocation, labour) with transfers excluded; industry value change per firm
  and sector; safety forecast; numeric news forecast and a composed wire; decision metrics with a
  bootstrap (P(best), winner stability, decision gap, P(inversion)); constraints read from the question.
- Assurance: tornado over every declared value judgement (reweighted or re simulated and paired),
  structural variants, red team gaming strategies whose honest values equal the headline figures,
  analogue event study on uploaded series.
- Governance carried from the Herding Scenario Lab: hash chained HMAC signed ledger, register of
  regulated persons with mandatory functions and four eyes, dev mode (Developer1, Developer2), two
  gates with refusal and reasons, emergency stop, an independent critic that recomputes every figure
  and vets every number in the briefing (unit suffixes included), evidence pack, ATRS record,
  security posture, quarantine for uploads that refuses personal data.
- Terminal: fifteen function codes, keyboard and footer navigation from any page, resizable and
  scrollable panels, live news wire and equity panel, charts drawn client side from specifications,
  grounded oracle, run registry, New run.
