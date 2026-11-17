# PSL TERMINAL: the Policy Scenario Lab

An agent based laboratory for AI regulation, at terminal density, built to be run by a public
authority. A policy question becomes a battery of alternatives: every candidate regulatory instrument
and the status quo. Every alternative runs against the same synthetic AI economy on the same random
numbers and is scored on the harm it prevents against the economic and social cost it imposes, with
the technology industry's net gain or loss, the news environment it generates and the market reaction
reported beside it. Two human gates, a signed ledger, an independent critic, an evidence pack and a
transparency record carry the result from a question to a briefing a regulator can sign.

The Lab is synthetic. Its figures are scenario evaluations conditional on a declared model and declared
assumptions, not forecasts validated against data, and its preferred option is the model's answer to a
question, to be examined, not an established recommendation.

From the team behind the Herding Scenario Lab (team No Human Intelligence), on the same governance
infrastructure.

## What it does

| Panel | What you get |
|---|---|
| **NWS** News wire | The headlines four media agents write from the simulation, live as it runs, and the forecast news environment by quarter for every alternative (negative headlines, pressure, P(hearing)) |
| **MKT** Technology equities | Every firm's stock under the alternative being simulated, streaming, indexed to one valuation taken before any instrument is announced; after evaluation, the value weighted index against the status quo on the same path, with its band |
| **SAF** Safety forecast | Incidents a year, P(major), P(catastrophe) with its confidence interval, expected harm and harm avoided, safety practice, capability, trust |
| **PNL** Industry gain or loss | Each firm's value change against the status quo, paired path by path, with its confidence interval, the spread of outcomes and P(gain); sector totals |
| **WLF** Social ledger | Ten welfare components as a waterfall to the net social value; gross cost and gross benefit; who gains and who pays; the transfers excluded |
| **GAP** Decision gap | The decision, the status quo included; every alternative with both intervals, the share of resamples in which it satisfies the constraints and its ranking stability; paired differences; early appearance against value over the horizon |
| **RSK** Assurance | The sampling plan and convergence; a screen of every assumption; a joint draw of all of them with expected regret; a variance decomposition; structural variants; red team gaming strategies; a robustness table; validation against published benchmarks, with the joint draws weighted by them; validation against an uploaded event; the mechanism register |
| **RUN, LDG, REG, ASK** | Gates with refusal and reasons, the signed hash chain, the run registry, and a grounded oracle over the artefacts |
| **POL, AGT, DAT, SEC** | Define instruments and firm archetypes as bounded documents, bring price series through quarantine, check the deployment's security posture |

The method is written out equation by equation in [docs/METHOD.md](docs/METHOD.md), with its tables
generated from the code; the operator's manual is [docs/MANUAL.md](docs/MANUAL.md); deployment in
[DEPLOY.md](DEPLOY.md). [docs/REVIEW_RESPONSE.md](docs/REVIEW_RESPONSE.md) answers an independent
statistical and methodological review point by point, and [docs/replication.md](docs/replication.md)
reports the default question repeated on twenty independent seeds.

Two public addresses: GitHub Pages serves `site/`, a replay of recorded runs rendered entirely in the browser
(`python tools/build_static.py --out site --live-url <the live address>` rebuilds it), and the live terminal
runs on any of three hosts that are free at demonstration use: Modal (`modal deploy modal_app.py`, scaled to
zero between visitors), Posit Connect Cloud (published from this repository, starting `app.py`) or a GitHub
codespace (`.devcontainer/`, on demand). [DEPLOY.md](DEPLOY.md) has the steps and what each allows.

## How an answer is put together

1. **The decision rule.** The alternatives are every instrument and the status quo, which scores zero.
   The preferred alternative has the highest expected net social value among those that satisfy the
   question's constraints. If no instrument beats the status quo, the answer says so.
2. **Three kinds of interval, kept apart.** The 95% confidence interval of an expected value (Monte
   Carlo error); the 10th to 90th percentile spread of simulated outcomes; and the range under other
   assumptions and model structures.
3. **Feasibility is an estimate too.** Every alternative carries the share of bootstrap resamples in
   which it satisfies each constraint, and the preferred option under a conservative rule is reported
   beside the preferred option on the point estimate.
4. **Rare events.** Expected harm and the probability of a catastrophe are estimated from the hazard
   each path accumulates, not from the incidents that happened to be drawn; the battery grows, on the
   same random streams, until declared precision targets are met or its ceiling is reached, and what is
   still unresolved is said.
5. **Every assumption is attacked.** All 68 are moved to the ends of a plausible range one at a time,
   drawn jointly, and the most influential decomposed by variance; the battery is re run under eight
   alternative model structures and four gaming strategies; feasibility is re assessed every time.
6. **Preferred is not robust.** The briefing distinguishes the preferred option from the robustly
   acceptable ones and says when the first is not among the second.
7. **The model is confronted with evidence.** Eleven published benchmarks (the growth of recorded AI
   incidents, the trend of public trust, what a compliance regime did to profits and share prices, how
   much regulated activity moved abroad), each with its source and an allowance for its distance from
   the model, are compared with the model's own value of the same quantity. The joint draws are then
   weighted by how well each reproduces them, and the decision is reported before and after. What the
   model fails, and what no evidence reaches, is said.

## Run it

    pip install -r requirements.txt
    PSL_SECRET=$(python -c "import secrets;print(secrets.token_hex(32))") \
    PSL_REGISTER=sample_data/register.csv python dash_app.py

Open <http://127.0.0.1:8070>. The approver at the gates must be on the register in an approving
function (the sample register has `Rajib Ahmed`, SMF24) and must differ from the preparer.

### Open gates (public demonstration)

    python app.py

`app.py` is the public demonstration: `dash_app.py` with open gates, the `demo` profile, reuse of identical
batteries, a five minute idle window and the settings a small container wants (its first lines list them; an
environment variable overrides each). It is the file Posit Connect Cloud and a GitHub codespace start.

The two gates become single clicks with no preparer or approver identities; this is how the public
site runs. Every gate record, the briefing, the transparency record and the posture page say the gates
were open. Inside an authority the default (`PSL_GATES=named`) applies: named preparer and approver with
their functions, the register and four eyes.

### Dev mode (named gates without a register entry)

    PSL_DEV_MODE=on PSL_PROFILE=demo PSL_REGISTER=sample_data/register.csv PSL_PORT=8070 python dash_app.py

Type `Developer1` as the preparer and as the preparer's function, `Developer2` as the approver and as
the approver's function. Every gate record says dev mode was used. Never for production.

### Walkthrough

1. Press Enter on the front page; the grid opens. Press `8` for RUN.
2. Type a question, for example *Which AI regulatory instrument best reduces expected harm from frontier
   AI over the next five years, keeping the technology sector's net loss below $400bn and the gross
   social cost under $150bn?* With named gates, name the preparer and the approver with their functions.
   **Plan.** The reading of the question appears; a condition the Lab cannot test is flagged as not applied.
3. **Gate 1: approve battery.** Watch NWS and MKT stream each alternative; the rail walks SIMULATE,
   MARKETS, WELFARE, ASSURANCE, CRITIC.
4. Read SAF, PNL, WLF, GAP and RSK (`3 4 5 6 K`); ask the oracle (`9`).
5. **Gate 2: release briefing.** The briefing, the transparency record and the evidence pack are built;
   REG (`R`) lists the run.
6. Plan the same question with "seed 11" added to replicate it on other random numbers.

### Command line

    PSL_SECRET=... PSL_DEV_MODE=on python -m psl.orchestrator --profile demo \
        --approve-battery --approve-briefing --preparer Developer1 --preparer-role Developer1 \
        --approver Developer2 --approver-role Developer2 --outdir runs/cli_demo

### Checks

    pip install -r requirements-dev.txt
    python -m pytest tests -q                       # the test suite: decision rule, estimators, intervals, accounting, validation, pipeline, critic, server, security
    python tools/recompute.py runs/cli_demo         # a second implementation, numpy only, recomputes the accounting and the decision
    python tools/replicate.py --seeds 20 --paths 480    # the same question on independent seeds: decision frequency, standard errors, interval coverage
    python tools/sync_docs.py --check               # the method document's tables match the code
    python tools/cost.py --profile demo             # seconds, processor seconds and memory by stage; the cost on a host that bills by the second
    python test_terminal.py http://127.0.0.1:8070   # browser walkthrough against a running terminal (Playwright)

## Configuration

Every setting is an environment variable with a safe default; see `config.py`. The ones that matter:

| Variable | Purpose | Default |
|---|---|---|
| `PSL_SECRET` | HMAC key for the ledger; set it or every ledger is signed with an ephemeral key | ephemeral, with a warning |
| `PSL_PROFILE` | the sampling plan and assurance budget: `full` (480 paths growing to at most 3,840), `light` (240 to 960), `demo` (120 to 480, about half a minute a run) | `full` |
| `PSL_PATHS`, `PSL_MAX_PATHS` | the paths a battery starts on and the ceiling it may grow to (equal for a fixed number) | from the profile |
| `PSL_SEED` | seed of the random streams when the question names none | 7 |
| `PSL_WORKERS` | threads for independent simulations | the machine's cores, at most four |
| `PSL_BENCHMARKS` | JSON file of empirical benchmarks that replaces or extends the built in evidence base of the validation layer | the built in set |
| `PSL_REUSE` | `on`: a battery identical to a completed run (same hash, code, libraries, uploaded series) replays its stored figures instead of simulating again; the critic recomputes them and the ledger says so | off |
| `PSL_IDLE_SECONDS` | seconds without a key, click, scroll or pointer movement after which an open page stops polling the server, unless a run is in progress | 90 (`app.py`: 300) |
| `PSL_REGISTER` | register of regulated persons approvers are checked against | none |
| `PSL_GATES` | `named` (preparer and approver with functions, register, four eyes) or `open` (single click gates, no identities; the public demonstration) | `named` |
| `PSL_DEV_MODE` | `on` accepts Developer1 and Developer2 at named gates | off |
| `PSL_AUTH_MODE` | `open` (names typed) or `header` (identity and role from an authenticating proxy) | `open` |
| `PSL_FOUR_EYES` | approver must differ from preparer | on |
| `PSL_PORT`, `PSL_HOST` | bind | 8070, 127.0.0.1 |
| `PSL_LLM_PROVIDER` | `off`, `anthropic`, `openai`, `azure`, `gemini`, `custom`, `local`: a model only phrases text; every number it writes is vetted against the artefacts | off unless `ANTHROPIC_API_KEY` is set |

## Layout

    dash_app.py          the terminal (Dash + Flask); python dash_app.py
    app.py               the public demonstration (open gates, demo profile): what Posit Connect Cloud and a codespace start; python app.py
    config.py            environment configuration and the profiles
    runstore.py          run directories, metadata, served files, evidence packs
    psl/                 the library
      policies.py        instrument library, validation, bounds, the policy store
      firms.py           firm archetypes and the firm store
      assumptions.py     every assumption with bounds, a plausible range and a meaning; correlated groups; constants
      mechanisms.py      the mechanism register: source, identifying assumption, calibration, test, status
      economy.py         the agent based economy on common random numbers
      reduce.py          from simulated paths to what the accounting needs; batteries in chunks; sensitivity designs
      welfare.py         the estimand, the accounting map, the components, safety, news and market metrics
      stats.py           bootstrap, intervals, rank statistics, the copula, sampling designs, Sobol indices
      evaluate.py        the decision rule, feasibility, paired differences, the decision gap, precision
      assurance.py       screen, joint draw, variance decomposition, structural variants, red team, convergence, robustness
      benchmarks.py      the evidence base: published benchmarks with their sources, and the evidence set aside
      validation.py      the validation layer: moments, verdicts, the joint draws weighted by the benchmarks; the event study
      reuse.py           an identical battery replays a completed run instead of simulating again
      news.py            the four media agents and the wire
      question.py        the question parser
      pipeline.py        plan and run a battery, with adaptive sampling
      critic.py          the independent critic
      briefing.py        the supervisory briefing
      atrs.py            the transparency record
      ask.py             the grounded oracle
      ledger.py          hash chained, signed ledger
      register.py        register of regulated persons and dev mode
      security.py        posture, roles, quarantine primitives, asset manifest
      ingest.py          the data desk quarantine
      evidence.py        the evidence pack
      parallel.py        independent simulations side by side
      llm.py             optional model layer (phrasing only, vetted)
      orchestrator.py    command line runner
    assets/              terminal.js, psl.css, vendored fonts and charts, MANIFEST.sha256
    sample_data/         register.csv, analogue_event_study.csv, refused_pii_example.csv
    sample_outputs/      a released briefing, transparency record and critic report: the default question on the full profile
    tests/               pytest suite; test_terminal.py is the browser walkthrough
    docs/                METHOD.md, MANUAL.md, REVIEW_RESPONSE.md, replication.md and .json
    tools/               replicate.py, recompute.py, sync_docs.py, cost.py; build_static.py, replay.js, test_static.py (the replay site)
    site/                the built replay site (recorded runs, no server): serve it with GitHub Pages
    modal_app.py         the live terminal on Modal; modal deploy modal_app.py
    .devcontainer/       the live terminal in a GitHub codespace
    Dockerfile, render.yaml, .github/workflows/ (pages.yml, deploy-modal.yml), deploy/   deployment (Modal, GitHub Pages, Docker hosts, in house)

## What it is not

The economy is synthetic and the firms are archetypes; nothing here forecasts a named company or
event. No mechanism of the model is estimated from data. Ten of the fifteen are confronted with a
published benchmark, most of them analogues from other regulation and other technologies; five have
none, and nothing identifies how far adoption follows trust. The mechanism register lists each with
the evidence that would test it. The plausible ranges of the assumptions are declared judgements. A run's preferred option is a hypothesis conditional on
all of that. The Lab informs a policy choice; a human makes it, at a gate, with reasons recorded.
