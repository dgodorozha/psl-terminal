# PSL TERMINAL: operator's manual

The Policy Scenario Lab is a terminal: one screen, numbered panels, function codes, a command line, a
workflow rail and two human gates. This manual walks through a run and every page. `docs/METHOD.md`
states what is computed; this document says where to find it and how to read it.

## Starting the terminal

    pip install -r requirements.txt
    PSL_SECRET=<64 hex chars> PSL_REGISTER=sample_data/register.csv python dash_app.py

Open <http://127.0.0.1:8070>. For a demonstration without sign off identities, open the gates:

    PSL_GATES=open PSL_PROFILE=demo python dash_app.py

or keep named gates and accept the two development identities:

    PSL_DEV_MODE=on PSL_PROFILE=demo PSL_REGISTER=sample_data/register.csv python dash_app.py

**Profiles.** A profile is a sampling plan and an assurance budget. The battery starts on a number of
paths and doubles, on the same random streams, until its precision targets are met or its ceiling is
reached:

| Profile | Paths | A run of the default question takes about (two cores) |
|---|---|---|
| `demo` | 120, growing to at most 480 | half a minute |
| `light` | 240, growing to at most 960 | a minute |
| `full` (default) | 480, growing to at most 3,840 | under two minutes when it stops at 960 paths, as the default question does; longer the further it has to grow |

`PSL_PATHS` and `PSL_MAX_PATHS` override the plan (set them equal for a fixed number of paths);
`PSL_WORKERS` sets the threads; `PSL_SEED` the default seed. A question that names a horizon ("over
the next five years") overrides the profile's horizon.

## Navigation

- **Function codes.** Type a code in the command line and press GO (Enter): `NWS`, `MKT`, `SAF`, `PNL`,
  `WLF`, `GAP`, `LDG`, `RUN`, `ASK`, `POL`, `RSK`, `DAT`, `AGT`, `SEC`, `REG`. Aliases work too (`NEWS`,
  `STOCKS`, `SAFETY`, `WELFARE`, `GATES`, `TORNADO`, `LIBRARY`, `FIRMS`, `RUNS`).
- **Keys.** Digits `1` to `9` and `0`, letters `K D A S R P`, from any page, including the hidden pages
  and ASK. `Esc` restores the grid. `H` or `FRONT` reopens the front page. `LAYOUT` resets the panel sizes.
- **Footer keys.** The buttons along the bottom open every page from anywhere.
- **Maximise.** A code maximises its panel; double clicking a panel's header does the same; `Esc` returns.
- **Resize.** Drag the lines between boxes to widen or heighten any box; double click a line to restore
  that split. Every box scrolls in both directions when its content exceeds it.

## A run, step by step

1. **RUN (8).** Type the policy question. With named gates (the default), name the preparer and the
   preparer's function, the approver and the approver's function (an SMF or certified function); the
   approver must differ from the preparer (four eyes). With open gates (`PSL_GATES=open`) there are no
   identity fields: the gates are single clicks, and every record says so.
2. **Plan.** The question is read into a battery: the instruments it names (or the default battery),
   always with the status quo; the constraints it states (industry loss at most, gross social cost at
   most, the probability of a major or a catastrophic incident at most, harm reduction at least,
   consumer surplus loss at most); the horizon; and the seed if it names one ("seed 11"). A condition
   the Lab cannot test is shown as **not read as a constraint, so not applied**, here and in an alert:
   reword it or refuse the battery. The battery, its sampling plan, its hash and the reading appear in
   RUN; the rail moves to GATE 1. Nothing has simulated.
3. **Gate 1: approve battery** (or **Refuse** with a reason). The battery runs: the news wire and the
   equity panel stream the representative path of each alternative in turn; the ticker and the rail
   follow the stages (SIMULATE, MARKETS, WELFARE, ASSURANCE, CRITIC). If an estimate is short of its
   precision target the phase line says which, and the battery grows.
4. **Evaluated.** SAF, PNL, WLF, GAP, the NWS forecast, the MKT "vs status quo" view and RSK fill. The
   phase line names the decision (an instrument, or the status quo), the number of paths and whether the
   critic passed. If the critic failed, Gate 2 is sealed and the failing checks are listed in RUN.
5. **Gate 2: release briefing** (or **Refuse** with a reason). The briefing is drafted from the
   artefacts (a configured model may phrase it; every number is vetted against the artefacts), the critic
   checks it again, the transparency record and the evidence pack are built, and the briefing renders in
   RUN with links to every file.
6. **New run** clears the terminal for the next question (datasets, stored instruments, firm templates
   and assumption overrides are kept). **Stop** halts a run at the next check and seals the partial
   ledger.

To replicate a run on other random numbers, plan the same question with another seed: "... seed 11".

## The panels

**1 NWS News wire.** *Wire*: the headlines the four media agents (WIRE, TECH, CIVIC, CAPITOL) compose
from the simulation's events on the representative path, newest first, with the alternative they belong
to; filter with the selector. The header shows the headline count, the current news pressure and public
trust. *Forecast* (after evaluation): expected negative headlines a quarter with the 90th percentile and
the status quo behind them, the pressure index, and the headline counts a year by type for every
alternative, with the probability of a hearing.

**2 MKT Technology equities.** *Prices*: every firm's price under the alternative being simulated, one
line per firm, indexed to 100 before any instrument is announced (the same valuation for the whole
battery); the selector replays any alternative already run. *vs status quo* (after evaluation): the
value weighted index against the status quo on the same path, in percent, with its 10th to 90th band.

**3 SAF Safety forecast.** Expected harm at the status quo; expected harm avoided by each instrument
with the confidence interval of the estimate; for every alternative, incidents a year, major incidents
a year, P(major), P(catastrophe) with its 95% interval and the raw count of paths on which a
catastrophe was drawn, expected harm, the safety level and safety share firms end with, frontier
capability, trust and the offshore share. A tail note appears when the expected value sits above the
90th percentile of the outcomes.

**4 PNL Industry gain or loss.** For the chosen instrument: the industry's expected value change with
its 95% interval, the spread of outcomes and the probability it gains; the index reaction; each firm's
value change (earnings over the horizon plus the discounted market value change at its end, paired with
the status quo) with both intervals, P(gain), earnings, end price against the status quo, offshore
share and safety share; the sector totals.

**5 WLF Social ledger.** For the chosen instrument: the expected net social value with its 95%
interval, the spread of outcomes, the share of paths above zero, gross social cost and gross benefit,
gross cost per dollar of harm avoided, and whether it is within the constraints with the share of
resamples in which it is; the waterfall of the ten components to the net; the component table with
both intervals; who gains and who pays; the transfers excluded from the net.

**6 GAP Decision gap.** The decision in words (the preferred alternative, the conservative rule when it
differs, what is short of its precision target); the decision gap, Kendall's tau b and P(inversion);
the ladder from "looks best early" to "best over the horizon"; every alternative, the status quo
included, with its expected value, both intervals, feasibility, the share of resamples within the
constraints, ranking stability and ranks; the preferred alternative against each other feasible one,
paired, with the pairwise and the simultaneous interval and whether the paths tell them apart.

**7 LDG Rationale ledger.** The signed hash chain, entry by entry, with the replay verdict. Every
extension of the battery by the sampling plan is an entry.

**8 RUN.** Run control, the gates, the status, the battery with its sampling plan, the approvals, the
critic's verdict, the links and the released briefing.

**9 ASK.** The run oracle: grounded answers computed on the server from the run's artefacts (which
alternative and why, how sure, what it costs and who pays, how safe, a firm's stock, the news to
expect, an assumption and whether it changes the decision, the joint draw, the variance decomposition,
robustness, validation, the mechanisms, the red team, the ledger). Sources are listed on the right. A
configured model only phrases the answer; its text is vetted number by number.

**0 POL Policy library.** The built in instruments; define your own as a bounded JSON document
(validate and store; enable, disable or remove); assumption overrides for the next plan; the assumption
table with values, plausible ranges, bounds and meanings.

**K RSK Assurance.** Nine sections, selected by the buttons at the top:

- *Monte Carlo*: the sampling plan and whether its targets were met; the convergence of the running
  estimate; the decision in independent batches of the paths; every instrument with its expected value,
  both intervals, the share of resamples within the constraints and ranking stability.
- *Screen*: every assumption at the low and the high end of its plausible range, with the decision at
  each end, the standard error of the swing, and whether a change of decision is by feasibility or by
  value; the tornado of the fifteen largest swings.
- *Joint draw*: all the assumptions drawn together; for every alternative the share of draws in which
  it is the decision, within the constraints and acceptable, and its expected regret; the assumptions
  the decision margin moves with (those that pass a false discovery rate are in amber); Monte Carlo
  filtering.
- *Variance*: the Sobol decomposition over the most influential assumptions, with intervals.
- *Structural variants*: the decision and the focus option's rank, value and feasibility under each
  alternative model structure.
- *Red team*: each instrument honest and under its worst gaming strategy, and whether it stays
  acceptable under every strategy; the best choice when every instrument is gamed.
- *Robustness*: one row per instrument across all of the above, and which are robustly acceptable.
- *Benchmarks*: validation against published evidence. Every benchmark of the evidence base with what was observed, the
  model's value at the central assumptions, the verdict, the model's range across the joint draws and the
  value predicted with the benchmark held out; the decision shares of the joint draws unweighted, weighted
  by the benchmarks and among the draws no benchmark rules out; the assumptions the benchmarks bear on; the
  sources; the evidence that was examined and set aside, with the reason.
- *Events and mechanisms*: an uploaded event against the model's early
  reaction; the mechanism register, with the benchmarks of the run that bore on each mechanism.

**D DAT Data desk.** Upload a monthly (or finer) price series through quarantine: classification, an
optional event month, an optional firm archetype it maps to, an optional instrument the event is an
analogue of. The series calibrates the mapped firm's volatility and beta in the next plan (on the
returns before the event month) and, with an event month, feeds the validation section. Zero or
negative prices, dates that are not ISO dates, gaps in the months and personal data are refused, with
the reason.

**A AGT Firm workshop.** The default archetypes; define your own firm templates (at least two enabled
templates replace the default economy in the next plan).

**S SEC Security posture.** The deployment checked against the controls (ledger key, binding address,
authentication mode, the gates, four eyes, register, model egress, upload limits, asset manifest,
dataset classifications), each naming the chapter of *Security Engineering* whose argument it applies.

**R REG Run registry.** Every run with its stage, preparer, approver, decision, decision gap, ranking
stability, paths and files.

## Reading the numbers

- Every "$bn" figure is a present value over the horizon at the social discount rate; every figure
  "against the status quo" is a paired difference on the same random numbers.
- **Three intervals, never the same thing.** A *95% confidence interval* (square brackets after an
  expected value) is how well the paths estimate that expectation; more paths narrow it. *Outcomes,
  10th to 90th* is how different one simulated path can be from another; more paths do not narrow it.
  The *range under other assumptions* (the screen, the joint draw, the variants) is how the answer moves
  when the model moves; no number of paths touches it.
- **Ranking stability** is the share of bootstrap resamples of the paths in which an alternative is the
  best feasible one. It is conditional on the model. It is not the probability that the alternative is
  best in the world.
- **Within constraints, x% of resamples.** A constraint is tested on an estimate. Where the limit sits
  inside the estimate's interval, inclusion or exclusion is not settled, the share says how unsettled,
  and the conservative rule (within the constraints in at least 90% of resamples) may prefer a
  different alternative.
- **The status quo is an alternative.** If no instrument beats it within the constraints, the decision
  is the status quo and the best instrument is shown beside it.
- An expected value above the 90th percentile of the outcomes is carried by the few paths on which a
  catastrophe is averted; the panels say so and give the median and the tail share.
- **Robustly acceptable** is a different claim from preferred: within the constraints and above the
  status quo on the central estimate, in at least 90% of the joint draws, in every structural variant
  and under every gaming strategy.
- **Benchmark verdicts.** *Not contradicted* means the model's value is within two standard deviations of the
  published one, where the standard deviation combines the benchmark's own error with a declared allowance
  for the distance between where it was measured and the model. It is the strongest verdict there is, and a
  weak one when the allowance is wide. *In tension* is two to three, *contradicted* beyond three. A
  *failure of form* is a benchmark no value of the assumptions inside their ranges comes near.
- **Weighted by the benchmarks.** The joint draws weighted by how well each reproduces the benchmarks: a
  posterior given the allowances, read beside the unweighted share. The effective number of draws says how
  much is left to read; below twenty the weighted shares are marked indicative only.
- The decision gap is the distance between how the instruments look in the first six months and how
  they score over the horizon; near zero the early signals are informative, near one they invert the
  ranking.

## Files

`runs/<run id>/` holds `battery.json` (with the sampling plan and the seed), `assumptions.json`,
`plan.json`, `artefacts.json`, `results.json`, `assurance.json`, `news_sample.json`,
`prices_sample.json`, `paths.json`, `paths.npz` (the stored path arrays the critic and the second
implementation recompute from), `critic.json`, `approvals.json`, `ledger.jsonl`, `briefing.md` and
`.html`, `atrs_record.md` and `.json`, `meta.json` and `evidence_pack.zip` with its `manifest.json` and
`VERIFY.md`. The terminal serves the files listed in `runstore.SERVABLE` under `/run/<id>/<name>`.
`reuse.json` marks a completed run with the key under which an identical battery may reuse its figures
(`PSL_REUSE=on`); a run that did so says which run computed them in its ledger, artefacts and briefing.

## Command line

    PSL_SECRET=... PSL_DEV_MODE=on python -m psl.orchestrator --profile demo \
        --approve-battery --approve-briefing --preparer Developer1 --preparer-role Developer1 \
        --approver Developer2 --approver-role Developer2 --outdir runs/cli

`--paths` fixes the number of paths (add `--max-paths` for a ceiling), `--seed` the seed, `--horizon`
the months, `--assumptions file.json` overrides assumptions, `--battery runs/<id>/battery.json` replays
an approved battery exactly.
`--benchmarks file.json` replaces or extends the evidence base of the validation layer (a list replaces;
`{"benchmarks": [...]}` adds to the built in set or overrides it by `id`; the fields are documented in
`psl/benchmarks.py`), and `--reuse` copies the figures of a completed run of the identical battery in the
same directory of runs instead of simulating again.

    python tools/recompute.py runs/cli                    # a second implementation checks the accounting
    python tools/cost.py --profile demo                   # seconds, processor seconds and memory by stage, and the cost on a metered host
    python tools/replicate.py --seeds 20 --paths 480      # the same question on independent seeds
    python tools/sync_docs.py --check                     # the method document's tables match the code
    python -m pytest tests -q                             # the test suite
