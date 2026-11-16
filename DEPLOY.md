# Deploying the Policy Scenario Lab

Two public addresses, neither costing anything at demo usage: Modal runs the live terminal, and GitHub Pages
serves the replay site (recorded runs rendered in the browser, no server). Each links to the other. Everything
below is done from the terminal.

## 1. GitHub (source of truth)

    gh auth login
    git init -b main && git add -A && git commit -m "PSL terminal"
    gh repo create psl-terminal --public --source=. --remote=origin --push

The repository root must hold `dash_app.py`, `psl/`, `assets/`, `modal_app.py`, `Dockerfile` and `README.md`.

## 2. Modal (the live terminal)

Modal (modal.com) runs a container only while someone is using it and scales to zero afterwards; the Starter
plan carries a monthly free credit of which a demo terminal uses a small fraction. Hugging Face Spaces, the
earlier plan, now require a PRO subscription for Docker Spaces (static Spaces remain free, but the terminal
needs a server).

    python3 -m pip install --upgrade modal
    modal setup                                   # opens the browser; sign in with GitHub
    modal secret create psl-secret PSL_SECRET=$(python3 -c "import secrets;print(secrets.token_hex(32))")
    modal deploy modal_app.py                     # prints the address, https://<workspace>--psl.modal.run

`modal_app.py` holds the whole deployment: the image (Python 3.12 and `requirements.txt`), the environment
(`demo` profile, open gates, BLAS on one thread, four simulation threads, reuse of identical batteries), one core
and 1 GiB requested with room to burst, a persistent volume `psl-runs` for the run registry, one container at a
time (`max_containers=1`, so the terminal's state and gates live in one process), up to a hundred concurrent
requests from the browsers using it, and a ten minute window after the last request before the container stops.
The first visitor after a quiet spell waits a few seconds while it starts, and finds an empty terminal: the run
registry (REG) keeps every past run with its briefing and evidence pack.

**What it costs.** Modal bills, by the second, the larger of what a container requests and what it uses, for as
long as the container is up (list prices in November 2026: $0.0000131 a core second, $0.00000222 a GiB second;
the Starter plan includes $30 a month). The run itself is the small part; the time the container stays up
afterwards is the large one. Measured with `python tools/cost.py --profile demo` on two cores:

| | Seconds | Cost |
|---|---:|---:|
| A demo run, computed (35 processor seconds, 0.53 GiB at its peak) | 26 | $0.0005 |
| The same battery asked again, reused from the registry | under 1 | under $0.0001 |
| Idle until the container stops (ten minutes, plus the ninety seconds before an untouched page stops polling) | 690 | $0.0106 |
| A visit with one computed run | | about $0.011: some 2,700 visits on the monthly credit |

Three settings carry this, and each is one line to change:

- **The request** (`cpu=1.0, memory=(1024, 4096)` in `modal_app.py`). A request is paid for while the terminal
  sits idle. One core is guaranteed and a run bursts above it when the worker has room; `cpu=0.5` halves the idle
  cost and leaves a run slower when the worker is busy. Version 1.1.0 requested four cores and 4 GiB: $0.055 for
  the same idle time, and $0.22 an hour.
- **The window** (`scaledown_window=600`). Shorter is cheaper and resets an idle visitor's terminal sooner.
- **Polling.** The page asks the server for news three times a second. It now stops ninety seconds after the last
  key, click, scroll or pointer movement unless a run is in progress, and starts again on the next one
  (`assets/terminal.js`), so an open tab no longer keeps the container up. In 1.1.0 a tab left open overnight
  kept four cores billed until it was closed.

`PSL_REUSE=on` makes an identical battery (the same hash, code, libraries and uploaded series) replay the stored
run instead of simulating it again; the critic still recomputes every figure, and the ledger and the briefing say
which run computed them. It is off by default and on for the public demonstration.

To redeploy on every push, give GitHub the Modal token: the values are in `~/.modal.toml` after `modal setup`.

    python3 - <<'EOF'
    import tomllib, pathlib, subprocess
    cfg = tomllib.loads((pathlib.Path.home() / ".modal.toml").read_text())
    prof = next((v for v in cfg.values() if isinstance(v, dict) and v.get("active")), next(iter(cfg.values())))
    for k in ("token_id", "token_secret"):
        subprocess.run(["gh", "secret", "set", f"MODAL_{k.upper()}", "--body", prof[k]], check=True)
    EOF

`.github/workflows/deploy-modal.yml` then runs `modal deploy` on every push to `main` that touches the
application (pushes that only change `site/` or the documents are skipped). Without the secrets the job runs
and skips, so the repository stays green.

The gates are open (`PSL_GATES=open`: single clicks, no preparer or approver) and the profile is `demo`: a battery
starts on 120 paths and grows to at most 480 where its precision targets ask for it, about half a minute a run. Change either in the `.env({...})` block of `modal_app.py` and redeploy. Leave `PSL_FRAME_ANCESTORS` unset: nothing embeds the terminal on Modal.

## 3. GitHub Pages (the replay site, always on)

`python tools/build_static.py --out site --live-url https://<workspace>--psl.modal.run` runs the recorded
batteries and writes a self contained `site/` folder (a built copy ships in the repository). The workflow
`.github/workflows/pages.yml` publishes that folder to GitHub Pages on every push that changes it. Turn Pages
on once, before the first push of the workflow:

    gh api --method POST repos/OWNER/REPO/pages -f build_type=workflow

The site is then at `https://OWNER.github.io/REPO/`. (GitHub's "deploy from a branch" option only serves the
root or `/docs`, which is why the workflow is used.) Rebuild and recommit `site/` when the model changes. The
builder records four runs, each on its own seed: the default question, the same question again on the next seed
(an independent replication a reader can compare with the first), and two more questions.

## 4. Other hosts

The `Dockerfile` runs the terminal on any Docker host: a Hugging Face Docker Space (PRO; put the front matter
`sdk: docker` and `app_port: 7860` at the top of `README.md`, set `PSL_SECRET` as a Space secret and keep
`PSL_FRAME_ANCESTORS` as the Dockerfile sets it so the Space page can embed the terminal), Render
(`render.yaml` is a one click blueprint), Railway, Fly or Google Cloud Run. The Dockerfile sets open gates and the
`demo` profile for a public demonstration; an authority deployment overrides them (section 5). Vercel and other serverless
platforms are not suitable: a run is a background computation that must survive between requests, which
serverless does not promise, and keeping functions alive for it is what made it expensive.

## 5. Inside an authority

`deploy/docker-compose.yml` runs the terminal in header authentication mode behind an nginx proxy
(`deploy/nginx.conf`) that sets `X-Remote-User` from the authority's single sign on and `X-PSL-Role`
(`viewer`, `preparer`, `approver`, `admin`) from its directory, and strips any client supplied copy of those
headers. Typed names are ignored in this mode; the approver list (`PSL_APPROVERS`), the register
(`PSL_REGISTER`) and four eyes apply. Runs persist on the `psl-runs` volume. Set `PSL_SECRET` from the secret
store, turn dev mode off, and leave `PSL_FRAME_ANCESTORS` unset.

## Environment

| Variable | Purpose |
|---|---|
| `PSL_SECRET` | ledger signing key; required for a persistent, verifiable ledger |
| `PSL_PROFILE` | the sampling plan and assurance budget: `demo` (120 paths growing to at most 480, about half a minute), `light` (240 to 960) or `full` (480 to 3,840) |
| `PSL_PATHS`, `PSL_MAX_PATHS`, `PSL_SEED`, `PSL_WORKERS` | override the plan's starting paths and ceiling, the default seed, and the simulation threads |
| `PSL_GATES` | `named` (default: preparer and approver with functions, register, four eyes) or `open` (single click gates without identities, for the public demonstration; never in production) |
| `PSL_DEV_MODE` | `on` accepts Developer1 and Developer2 at named gates; never in production |
| `PSL_REGISTER` | register of regulated persons the approver is checked against |
| `PSL_AUTH_MODE` | `open` (names typed) or `header` (identities from an authenticating proxy) |
| `PSL_FRAME_ANCESTORS` | origins allowed to embed the terminal (only a Hugging Face Space needs it) |
| `PSL_RUNS_DIR` | where runs are written |

Check the posture page (`S`) after deploying: a warning is recorded in every run's artefacts and a failing
control blocks release.
