# PSL TERMINAL: the Policy Scenario Lab

An agent based laboratory for AI regulation, at terminal density, built to be run by a public
authority. A policy question becomes a battery of candidate regulatory instruments; every instrument
runs against the same synthetic AI economy on the same random numbers; each is scored on the harm it
prevents against the economic and social cost it imposes, with the technology industry's net gain or
loss, the news environment it generates and the market reaction reported beside it. Two named human
gates, a signed ledger, an independent critic, an evidence pack and a transparency record carry the
result from a question to a briefing a regulator can sign.

From the team behind the Herding Scenario Lab (team No Human Intelligence), on the same governance
infrastructure.

## What it does

| Panel | What you get |
|---|---|
| **NWS** News wire | The headlines four media agents write from the simulation, live as it runs, and the forecast news environment by quarter for every instrument (negative headlines, pressure, P(hearing)) |
| **MKT** Technology equities | Every firm's stock under the instrument being simulated, streaming; after evaluation, the value weighted index against the status quo on the same path, with its band |
| **SAF** Safety forecast | Incidents a year, P(major), P(catastrophe), expected harm, harm avoided with intervals, safety practice, capability, trust |
| **PNL** Industry gain or loss | Each firm's value change against the status quo, paired path by path, with P(gain); sector totals; the industry's net gain or loss |
| **WLF** Social ledger | Harm avoided, consumer surplus, output, producer surplus, compliance, enforcement, leakage, relocation, labour, as a waterfall to the net social value; who gains and who pays |
| **GAP** Decision gap | The instruments ranked by how they look in the first six months against how they score over the horizon; P(inversion); P(best) |
| **RSK** Assurance | Tornado over every value judgement, structural variants, red team gaming strategies, analogue event study, intervals |
| **RUN / LDG / REG / ASK** | Gates with refusal and reasons, the signed hash chain, the run registry, and a grounded oracle over the artefacts |
| **POL / AGT / DAT / SEC** | Define instruments and firm archetypes as bounded documents, bring price series through quarantine, check the deployment's security posture |

The method is written out equation by equation in [docs/METHOD.md](docs/METHOD.md); the operator's
manual is [docs/MANUAL.md](docs/MANUAL.md); deployment in [DEPLOY.md](DEPLOY.md). Two public addresses: Modal
runs the live terminal (`modal deploy modal_app.py`, scaled to zero between visitors), and GitHub Pages serves
`site/`, a replay of recorded runs rendered entirely in the browser
(`python tools/build_static.py --out site --live-url <the Modal address>` rebuilds it).

## Run it

    pip install -r requirements.txt
    PSL_SECRET=$(python -c "import secrets;print(secrets.token_hex(32))") \
    PSL_REGISTER=sample_data/register.csv python dash_app.py

Open <http://127.0.0.1:8070>. The approver at the gates must be on the register in an approving
function (the sample register has `Rajib Ahmed`, SMF24) and must differ from the preparer.

### Dev mode (no register entry needed)

    PSL_DEV_MODE=on PSL_PROFILE=demo PSL_REGISTER=sample_data/register.csv PSL_PORT=8070 python dash_app.py

Type `Developer1` as the preparer and as the preparer's function, `Developer2` as the approver and as
the approver's function. Every gate record says dev mode was used. Never for production.

### Walkthrough

1. Press Enter on the front page; the grid opens. Press `8` for RUN.
2. Type a question, for example *Which AI regulatory instrument best reduces expected harm from frontier
   AI over the next five years, keeping the technology sector's net loss below $400bn and the gross
   social cost under $150bn?* Name the preparer and the approver with their functions. **Plan.**
3. **Gate 1: approve battery.** Watch NWS and MKT stream each instrument; the rail walks SIMULATE,
   MARKETS, WELFARE, ASSURANCE, CRITIC.
4. Read SAF, PNL, WLF, GAP and RSK (`3 4 5 6 K`); ask the oracle (`9`).
5. **Gate 2: release briefing.** The briefing, the transparency record and the evidence pack are built;
   REG (`R`) lists the run.

### Command line

    PSL_SECRET=... PSL_DEV_MODE=on python -m psl.orchestrator --profile demo \
        --approve-battery --approve-briefing --preparer Developer1 --approver Developer2 --outdir runs/cli_demo

### Tests

    pip install -r requirements-dev.txt
    python -m pytest tests -q                 # 25 tests: library, economy, welfare, pipeline, critic, server, security
    python test_terminal.py http://127.0.0.1:8070   # browser walkthrough against a running terminal (Playwright)

## Configuration

Every setting is an environment variable with a safe default; see `config.py`. The ones that matter:

| Variable | Purpose | Default |
|---|---|---|
| `PSL_SECRET` | HMAC key for the ledger; set it or every ledger is signed with an ephemeral key | ephemeral, with a warning |
| `PSL_PROFILE` | `full` (240 paths), `light` (120), `demo` (60, about half a minute a run) | `full` |
| `PSL_REGISTER` | register of regulated persons approvers are checked against | none |
| `PSL_DEV_MODE` | `on` accepts Developer1 and Developer2 at the gates | off |
| `PSL_AUTH_MODE` | `open` (names typed) or `header` (identity and role from an authenticating proxy) | `open` |
| `PSL_FOUR_EYES` | approver must differ from preparer | on |
| `PSL_PORT`, `PSL_HOST` | bind | 8070, 127.0.0.1 |
| `PSL_LLM_PROVIDER` | `off`, `anthropic`, `openai`, `azure`, `gemini`, `custom`, `local`: a model only phrases text; every number it writes is vetted against the artefacts | off unless `ANTHROPIC_API_KEY` is set |

## Layout

    dash_app.py          the terminal (Dash + Flask); python dash_app.py
    config.py            environment configuration and the profiles
    runstore.py          run directories, metadata, served files, evidence packs
    psl/                 the library
      policies.py        instrument library, validation, bounds, the policy store
      firms.py           firm archetypes and the firm store
      assumptions.py     every value judgement with bounds and meaning; the tornado set
      economy.py         the agent based economy on common random numbers
      welfare.py         the social ledger, safety, news and market metrics
      evaluate.py        decision metrics, bootstrap, decision gap
      news.py            the four media agents and the wire
      assurance.py       tornado, structural variants, red team, analogue event study
      question.py        the question parser
      pipeline.py        plan and run a battery
      critic.py          the independent critic
      briefing.py        the supervisory briefing
      atrs.py            the transparency record
      ask.py             the grounded oracle
      ledger.py          hash chained, signed ledger
      register.py        register of regulated persons and dev mode
      security.py        posture, roles, quarantine primitives, asset manifest
      ingest.py          the data desk quarantine
      evidence.py        the evidence pack
      llm.py             optional model layer (phrasing only, vetted)
      orchestrator.py    command line runner
    assets/              terminal.js, psl.css, vendored fonts and charts, MANIFEST.sha256
    sample_data/         register.csv, analogue_event_study.csv, refused_pii_example.csv
    sample_outputs/      a released briefing, transparency record and critic report from a demo run
    tests/               pytest suite; test_terminal.py is the browser walkthrough
    docs/                METHOD.md, MANUAL.md
    tools/build_static.py, tools/replay.js, tools/test_static.py   the static replay site builder and its browser check
    site/                the built replay site (recorded runs, no server): serve it with GitHub Pages
    modal_app.py         the live terminal on Modal; modal deploy modal_app.py
    Dockerfile, render.yaml, .github/workflows/ (pages.yml, deploy-modal.yml), deploy/   deployment (Modal, GitHub Pages, Docker hosts, in house)

## Honesty

The economy is synthetic and the firms are archetypes; nothing here forecasts a named company or
event. Every output is an expected value with an interval on a declared set of assumptions, and the
tornado names the assumptions that would change the answer. The Lab informs a policy choice; a named
human makes it, at a gate, with reasons recorded.
