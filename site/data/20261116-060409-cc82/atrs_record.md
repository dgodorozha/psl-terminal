# Algorithmic transparency record: Policy Scenario Lab (PSL)

## Tier 1

**Description.** An agent based policy laboratory that compares candidate AI regulatory instruments on a synthetic AI economy: firms choosing capability, safety, compliance and location; a regulator; the public; the press; the market. Each instrument is scored on expected harm avoided against its economic and social cost, with the industry's net gain or loss, the forecast news environment and the market reaction reported beside it.

**How it is used.** To inform, not to make, a policy choice: the briefing is drafted from the run's artefacts, checked by an independent critic and released by a named human at a second gate. Outputs are scenario evaluations conditional on a synthetic model and a declared set of assumptions: expected values with the confidence interval of the estimate, the spread of simulated outcomes and the sensitivity to the assumptions kept apart. They are not forecasts of named companies or events and are not validated against data, except where an uploaded event study is compared with the model's market reaction.

Run 20261116-060409-cc82, released 2026-11-16T06:04:25+00:00, version 1.2.0.

## Tier 2

### Owner and responsibility

**Senior responsible owner.** none recorded: public demonstration, gates taken without sign off identities
**External supplier.** none; the tool runs on the authority's own infrastructure

### Description and rationale

**Detailed description.** Monthly agent based simulation over 60 months on 120 Monte Carlo paths per alternative, on common random numbers; a welfare accounting for residents of harm avoided, consumer surplus, output uplift, resident producer surplus, compliance resource cost, enforcement budget, offshore leakage, relocation cost, labour adjustment and insurance administration, with transfers excluded; a decision rule (the highest expected net social value among the alternatives that satisfy the question's constraints, the status quo included); expected values estimated by conditional Monte Carlo with bootstrap confidence intervals; adaptive sampling to declared precision targets; a screen of every assumption, a joint draw of all of them, a variance decomposition, structural variants, a red team and a replication check.
**Scope.** Candidate AI regulatory instruments: Status quo (voluntary commitments), Liability with a safe harbour, Mandatory third party evaluation, Strict liability
**Benefit.** A reproducible, assumption explicit comparison of instruments that no single study provides, with its uncertainty shown.
**Previous process.** Narrative impact assessments and expert elicitation without a common counterfactual.
**Alternatives considered.** Static cost benefit spreadsheets; econometric event studies alone; expert panels.

### Decision making process

**Process integration.** The policy question enters at the RUN page; the battery is approved at Gate 1; the briefing is released at Gate 2.
**Provided information.** Preferred option Mandatory third party evaluation: expected net social value 23.2 $bn (95% confidence interval 12.9 to 35.0; simulated outcomes -37.2 to 78.3 at the 10th and 90th percentiles); harm avoided 14.2 $bn; industry value change -41 $bn; within the constraints in 100% of resamples; ranking stability 100%. Mandatory third party evaluation is preferred: the highest expected net social value among the alternatives that satisfy the constraints, and above the status quo.
**Frequency and scale.** On demand per question; every run is kept in the registry.
**Human decisions and review.** Two named human gates with refusal and recorded reasons; an independent critic before Gate 2; the briefing cites every assumption.
**Required training.** Familiarity with cost benefit analysis and with the assumptions file.
**Appeals and review.** Any figure can be recomputed from the evidence pack by a second authority; the ledger is replayable.

### Tool specification

**System architecture.** Python; numpy and scipy; a Dash terminal; a hash chained HMAC signed ledger; a register of approvers.
**Phase.** prototype
**Maintenance.** versioned; the code fingerprint of each run is recorded
**Models.** No learned model in the decision path; an optional language model may phrase text and its output is vetted number by number.

### Data

**Source data.** Synthetic economy by default; optional uploaded price series for calibration and event studies, through a quarantine that refuses personal data.
**Data sharing.** The evidence pack carries only public or synthetic rows.
**Assumptions hash.** c6c928eedba23618356e89d5a97435ef127d1f3cdffa587947b837c966b1e125
**Battery hash.** 67a124b8cccfcfac532e98aef3817f39fb3e0064bad36b7fbd5c196ef98267a7

### Risks mitigations and impact assessments

**Impact assessment.** The screen of every assumption, the joint draw, the variance decomposition, the structural variants, the red team and the replication check in assurance.json; the decision gap between early appearance and long run value.
**Risks.**
- The model is synthetic and no mechanism is estimated from data: the mechanism register lists each with the evidence that would test it, and the validation layer reports which published benchmarks the model is in tension with or contradicted by (on this run 11 benchmarks, 10 of 15 mechanisms confronted; failing: Share of the insurance loading used up by underwriting and administration; Equity return when a horizontal regime becomes enforceable).
- The harm side rests on declared hazard and tail assumptions; the screen and the joint draw show which change the answer.
- The firms are archetypes; mapping onto real companies requires calibration and is labelled as such.
- A domestic instrument can be escaped by relocation; the leakage term depends on the mobility assumed.
- Ranking stability is conditional on the model; it is not the probability that an option is best in the world.
- A constraint is tested on an estimate; an option near a limit may be included or excluded by sampling error, which the share of resamples within the constraints reports.
**Mitigations.** Every assumption is declared with bounds and a plausible range; common random numbers; conditional estimators for rare events; precision targets; an independent critic; two gates; a replayable ledger; the preferred option is reported with the assumptions, structures and gaming strategies that would change it.
