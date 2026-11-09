# Algorithmic transparency record: Policy Scenario Lab (PSL)

## Tier 1

**Description.** An agent based policy laboratory that compares candidate AI regulatory instruments on a synthetic AI economy: firms choosing capability, safety, compliance and location; a regulator; the public; the press; the market. Each instrument is scored on expected harm avoided against its economic and social cost, with the industry's net gain or loss, the forecast news environment and the market reaction reported beside it.

**How it is used.** To inform, not to make, a policy choice: the briefing is drafted from the run's artefacts, checked by an independent critic and released by a named human at a second gate. Outputs are expected values with intervals on a declared set of assumptions; they are not forecasts of named companies or events.

Run 20261109-075322-a7dc, released 2026-11-09T07:53:32+00:00, version 1.0.0.

## Tier 2

### Owner and responsibility

**Senior responsible owner.** Developer2
**Senior responsible owner function.** Developer2
**Senior responsible owner register.** source: dev mode (PSL_DEV_MODE=on); not a regulated person; function: Developer2; reference: DEV; checked_at: 2026-11-09T07:53:32+00:00
**External supplier.** none; the tool runs on the authority's own infrastructure

### Description and rationale

**Detailed description.** Monthly agent based simulation over 60 months on 60 Monte Carlo paths per instrument, on common random numbers; a welfare accounting of harm avoided, consumer surplus, output uplift, resident producer surplus, compliance resource cost, enforcement budget, offshore leakage, relocation cost and labour adjustment; a decision metric (expected net social value under the question's constraints) with a bootstrap for the probability that each instrument is best.
**Scope.** Candidate AI regulatory instruments: Status quo (voluntary commitments), Liability with a safe harbour, Mandatory third party evaluation, Strict liability
**Benefit.** A reproducible, assumption explicit comparison of instruments that no single study provides, with its uncertainty shown.
**Previous process.** Narrative impact assessments and expert elicitation without a common counterfactual.
**Alternatives considered.** Static cost benefit spreadsheets; econometric event studies alone; expert panels.

### Decision making process

**Process integration.** The policy question enters at the RUN page; the battery is approved at Gate 1; the briefing is released at Gate 2.
**Provided information.** Preferred option Mandatory third party evaluation: expected net social value 24.5 $bn [-43.5, 58.7]; harm avoided 17.7 $bn; industry value change -96 $bn; P(best) 41%.
**Frequency and scale.** On demand per question; every run is kept in the registry.
**Human decisions and review.** Two named human gates with refusal and recorded reasons; an independent critic before Gate 2; the briefing cites every assumption.
**Required training.** Familiarity with cost benefit analysis and with the assumptions file.
**Appeals and review.** Any figure can be recomputed from the evidence pack by a second authority; the ledger is replayable.

### Tool specification

**System architecture.** Python; numpy; a Dash terminal; a hash chained HMAC signed ledger; a register of approvers.
**Phase.** prototype
**Maintenance.** versioned; the code fingerprint of each run is recorded
**Models.** No learned model in the decision path; an optional language model may phrase text and its output is vetted number by number.

### Data

**Source data.** Synthetic economy by default; optional uploaded price series for calibration and event studies, through a quarantine that refuses personal data.
**Data sharing.** The evidence pack carries only public or synthetic rows.
**Assumptions hash.** b85a6faf3ec1a97fe657b8e7da96af2f3039a4d315258cb17a31e425cec538f1
**Battery hash.** a4217449df380aaf02a9bd0f1843ba3d9a6cfaecc779f487e3a218af021ce530

### Risks mitigations and impact assessments

**Impact assessment.** The tornado, structural variants and red team in assurance.json; the decision gap between early appearance and long run value.
**Risks.**
- The harm side rests on declared hazard and tail assumptions; the tornado shows which change the answer.
- The firms are archetypes; mapping onto real companies requires calibration and is labelled as such.
- A domestic instrument can be escaped by relocation; the leakage term depends on the mobility assumed.
- Expected values hide path dependence; the intervals and P(best) must be read with the means.
**Mitigations.** Every assumption is declared and bounded; common random numbers; an independent critic; two gates; a replayable ledger; the preferred option is reported with the assumptions that would change it.
