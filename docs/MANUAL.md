# PSL TERMINAL: operator's manual

The Policy Scenario Lab is a terminal: one screen, numbered panels, function codes, a command line, a
workflow rail and two human gates. This manual walks through a run and every page.

## Starting the terminal

    pip install -r requirements.txt
    PSL_SECRET=<64 hex chars> PSL_REGISTER=sample_data/register.csv python dash_app.py

Open <http://127.0.0.1:8070>. For a demonstration without a register entry, turn dev mode on:

    PSL_DEV_MODE=on PSL_PROFILE=demo PSL_REGISTER=sample_data/register.csv PSL_PORT=8070 python dash_app.py

Profiles: `demo` (60 paths, about half a minute a run), `light` (120 paths), `full` (240 paths, the
default; a few minutes). A question that names a horizon ("over the next five years") overrides the
profile's horizon.

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

1. **RUN (8).** Type the policy question. Name the preparer and the preparer's function (mandatory),
   the approver and the approver's function (an SMF or certified function; mandatory). In dev mode
   `Developer1` and `Developer2` are accepted as names and as functions. The approver must differ from
   the preparer (four eyes).
2. **Plan.** The question is read into a battery: the instruments it names (or the default battery), the
   constraints it states (industry loss at most, gross social cost at most, harm reduction at least,
   catastrophe probability at most), and the horizon. The battery, its hash and the reading appear in RUN;
   the rail moves to GATE 1. Nothing has simulated.
3. **Gate 1: approve battery** (or **Refuse** with a reason). The approver is checked against the
   register (or dev mode) and recorded in the ledger with the register entry. The battery runs: the news
   wire and the equity panel stream the representative path of each instrument in turn; the ticker and
   the rail follow the stages (SIMULATE, MARKETS, WELFARE, ASSURANCE, CRITIC).
4. **Evaluated.** SAF, PNL, WLF, GAP, the NWS forecast, the MKT "vs baseline" view and RSK fill. The
   phase line names the preferred option and whether the critic passed. If the critic failed, Gate 2 is
   sealed and the failing checks are listed in RUN.
5. **Gate 2: release briefing** (or **Refuse** with a reason). The briefing is drafted from the
   artefacts (a configured model may phrase it; every number is vetted against the artefacts), the critic
   checks it again, the transparency record and the evidence pack are built, and the briefing renders in
   RUN with links to every file.
6. **New run** clears the terminal for the next question (datasets, stored instruments, firm templates
   and assumption overrides are kept). **Stop** halts a run at the next check and seals the partial
   ledger.

## The panels

**1 NWS News wire.** *Wire*: the headlines the four media agents (WIRE, TECH, CIVIC, CAPITOL) compose
from the simulation's events on the representative path, newest first, with the instrument they belong
to; filter by instrument with the selector. The header shows the headline count, the current news
pressure and public trust. *Forecast* (after evaluation): expected negative headlines a quarter with the
90th percentile and the status quo behind them, the pressure index, and the headline counts a year by
type for every instrument, with the probability of a hearing.

**2 MKT Technology equities.** *Prices*: every firm's price under the instrument being simulated, one
line per firm, indexed to 100 at the announcement; the selector replays any instrument already run.
*vs baseline* (after evaluation): the value weighted index against the status quo on the same path, in
percent, with its 10th to 90th band; the header line gives the first six months' and the horizon's
reaction.

**3 SAF Safety forecast.** Expected harm at the status quo; harm avoided by each instrument with its
interval; incidents a year, major incidents a year, P(major), P(catastrophe), expected harm, the safety
level and safety share firms end with, frontier capability, trust and the offshore share. A tail note
appears when the mean sits above the 90th percentile.

**4 PNL Industry gain or loss.** For the chosen instrument: the industry's value change with its
interval and the probability it gains; the index reaction; each firm's value change (earnings over the
horizon plus the discounted market value change at its end, paired with the baseline), P(gain), earnings,
end price against the baseline, offshore share and safety share; the sector totals.

**5 WLF Social ledger.** For the chosen instrument: the net social value with its interval, P(positive),
the median, the gross social cost, the cost per dollar of harm avoided and P(best); the waterfall from
harm avoided through consumer surplus, output, producer surplus, compliance, enforcement, leakage,
relocation and labour to the net; the component table; who gains and who pays; the transfers excluded
from the net.

**6 GAP Decision gap.** The decision gap, Kendall's tau, P(inversion) and the winner's stability; the
ladder from "looks best early" to "best over the horizon"; every instrument's ranks (headline, social,
harm, industry), headline score, net value, P(best) and feasibility.

**7 LDG Rationale ledger.** The signed hash chain, entry by entry, with the replay verdict.

**8 RUN.** Run control, the gates, the status, the battery, the approvals, the critic's verdict, the
links and the released briefing.

**9 ASK.** The run oracle: grounded answers computed on the server from the run's artefacts (which
instrument and why, what it costs and who pays, how safe, a firm's stock, the news to expect, an
assumption and whether it changes the answer, the red team, the ledger). Sources are listed on the right.
A configured model only phrases the answer; its text is vetted number by number.

**0 POL Policy library.** The built in instruments; define your own as a bounded JSON document
(validate and store; enable, disable or remove); assumption overrides for the next plan; the assumption
table with bounds and meanings.

**K RSK Assurance.** Tornado (every value judgement at the edges of its range, with the option that
would then be best), structural variants, the red team (honest against the worst gaming strategy), the
analogue event study, and the intervals for every instrument.

**D DAT Data desk.** Upload a monthly price series through quarantine (classification, event month,
mapping to a firm). The dataset calibrates the mapped firm's volatility and beta in the next plan and,
with an event month, feeds the analogue event study. Personal data is refused, not redacted.

**A AGT Firm workshop.** The default archetypes; define your own firm templates (at least two enabled
templates replace the default economy in the next plan).

**S SEC Security posture.** The deployment checked against the controls (ledger key, binding address,
authentication mode, four eyes, register, model egress, upload limits, asset manifest, dataset
classifications), each naming the chapter of *Security Engineering* whose argument it applies.

**R REG Run registry.** Every run with its stage, preparer, approver, preferred option, decision gap,
winner stability and files.

## Reading the numbers

- Every "$bn" figure is a present value over the horizon at the social discount rate; every "against the
  baseline" figure is a paired difference on the same random numbers.
- Intervals are the 10th to 90th percentiles across paths. A mean above the 90th percentile means the
  expected value is carried by the few paths in which a catastrophe is averted; the panels say so and
  give the median and the tail share.
- P(best) is a bootstrap over paths; a winner with P(best) below a half is a close call and the briefing
  says so.
- The decision gap is the distance between how the instruments look in the first six months and how
  they score over the horizon; a gap near zero means the early signals are informative, a gap near one
  means they invert the ranking.

## Files

`runs/<run id>/` holds `battery.json`, `assumptions.json`, `plan.json`, `artefacts.json`, `results.json`,
`assurance.json`, `news_sample.json`, `prices_sample.json`, `paths.npz` (the stored path arrays the
critic recomputes from), `critic.json`, `approvals.json`, `ledger.jsonl`, `briefing.md` and `.html`,
`atrs_record.md` and `.json`, `meta.json` and `evidence_pack.zip` with its `manifest.json` and
`VERIFY.md`. The terminal serves the files listed in `runstore.SERVABLE` under `/run/<id>/<name>`.

## Command line

    PSL_SECRET=... PSL_DEV_MODE=on python -m psl.orchestrator --profile demo \
        --approve-battery --approve-briefing --preparer Developer1 --approver Developer2 --outdir runs/cli

runs the same chain without the terminal; `--battery runs/<id>/battery.json` replays a battery;
`--register`, `--preparer-role` and `--approver-role` apply the same gate rules.
