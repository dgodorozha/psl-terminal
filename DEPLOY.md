# Deploying the Policy Scenario Lab

Two public addresses. GitHub Pages serves the replay site (recorded runs rendered in the browser, no server): it
is always on and costs nothing. The live terminal needs a server, and there are three hosts for it, each free at
demonstration use and each stopping at its allowance:

| | Modal (section 2) | Posit Connect Cloud (section 3) | GitHub Codespaces (section 4) |
|---|---|---|---|
| Started from | a laptop, `modal deploy modal_app.py` | the GitHub repository, in the browser | the GitHub repository, in the browser |
| Entry point | `modal_app.py` | `app.py` | `.devcontainer/`, which runs `app.py` |
| Address | `https://<workspace>--psl.modal.run` | `https://<name>.share.connect.posit.cloud` | `https://<codespace>-8070.app.github.dev` |
| There for a visitor | at any time: the container starts on the visit | at any time: the process starts on the visit | while the codespace is running |
| Allowance | a monthly credit in dollars | monthly usage credits | 120 core hours a month |
| At the allowance | deploys and containers stop until the billing cycle resets or the spend limit is raised | applications do not run until the next usage period | use is blocked until the next month |
| Run registry | kept on a volume | starts empty with each process | kept while the codespace exists |

The replay site links to whichever is in use (section 5). Sections 1, 2 and 5 are done from the terminal, sections 3
and 4 in the browser.

## 1. GitHub (source of truth)

    gh auth login
    git init -b main && git add -A && git commit -m "PSL terminal"
    gh repo create psl-terminal --public --source=. --remote=origin --push

The repository root must hold `dash_app.py`, `app.py`, `psl/`, `assets/`, `requirements.txt`, `modal_app.py`,
`Dockerfile` and `README.md`.

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
  (`assets/terminal.js`; `PSL_IDLE_SECONDS` sets the window), so an open tab no longer keeps the container up. In
  1.1.0 a tab left open overnight kept four cores billed until it was closed.

`PSL_REUSE=on` makes an identical battery (the same hash, code, libraries and uploaded series) replay the stored
run instead of simulating it again; the critic still recomputes every figure, and the ledger and the briefing say
which run computed them. It is off by default and on for the public demonstration.

**When a deploy stops with "reaching billing cycle spend limit".** The workspace has used its allowance for the
billing cycle; nothing is wrong with the application. `modal app stop psl-terminal` stops whatever is still
running, the usage and the limit are at modal.com/settings/usage, and `modal deploy modal_app.py` works again
once the cycle resets or the limit is raised. Sections 3 and 4 are hosts for the meantime.

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
and skips, so the repository stays green. With them, the job fails for as long as the workspace is at its spend
limit; `gh workflow disable deploy-modal.yml` switches it off until then.

The gates are open (`PSL_GATES=open`: single clicks, no preparer or approver) and the profile is `demo`: a battery
starts on 120 paths and grows to at most 480 where its precision targets ask for it, about half a minute a run. Change either in the `.env({...})` block of `modal_app.py` and redeploy. Leave `PSL_FRAME_ANCESTORS` unset: nothing embeds the terminal on Modal.

## 3. Posit Connect Cloud (the live terminal, published from the repository)

Posit Connect Cloud (connect.posit.cloud) publishes a Dash application from a public GitHub repository, in the
browser. In November 2026 its Free plan allowed five applications on one processor with up to 4 GB of memory.
The Free plan is capped, not billed: use is counted in usage credits, and when a month's credits are spent the
applications do not run until the next usage period (enforced from the first usage period beginning on or after
1 November 2026). The number of credits a plan includes is on connect.posit.cloud/plans.

It starts `app.py`, the public demonstration's entry point: open gates, the `demo` profile, reuse of identical
batteries, one simulation thread for each processor the host allows and linear algebra on one thread (the file's
first lines list every default, and an environment variable overrides each). It installs `requirements.txt`.

1. Sign in at <https://connect.posit.cloud> with the GitHub account that owns the repository.
2. Open the publishing form already filled in (put the owner and the repository in the address):

       https://connect.posit.cloud/publish?contentType=dash&sourceRepositoryURL=https%3A%2F%2Fgithub.com%2FOWNER%2FREPO&sourceRef=main&sourceRefType=branch&primaryFile=app.py&pythonVersion=3.12

   or click **Publish** on the Home page and choose Dash, the repository, the branch `main` and the primary file
   `app.py`. The first time, Connect Cloud asks to install its GitHub App: give it access to the repository.
3. Open **Advanced settings**. The Python version must be 3.12 or later: the pinned scipy does not install on
   3.11, the form's default, and the build then stops at `scipy==1.18.1`. Add a secret variable `PSL_SECRET` whose
   value is the output of `python3 -c "import secrets;print(secrets.token_hex(32))"`, so the ledger is signed with a
   key that outlives the process.
4. **Publish**. The log shows the packages being installed; the terminal is then at an address of the form
   `https://<content-id>.share.connect.posit.cloud`.
5. In the content's settings (the Edit Settings icon): compute at 1 CPU and 2 GB; **Max Worker Processes 1**,
   because the terminal keeps the state of its run in one process and a second process would be a second, empty
   terminal; Idle Timeout 60 seconds; and a custom name, which makes the address
   `https://<account>-<name>.share.connect.posit.cloud`.

With "Automatically publish on push" left on, every push to `main` republishes.

**How it behaves there.** Connect Cloud starts a process when a visitor arrives and stops it once no connection
has been open for the Idle Timeout. An open page asks the server for news three times a second while it is in use
or a run is in progress, which keeps the process up; a page nobody has touched for five minutes stops asking
(`PSL_IDLE_SECONDS=300` in `app.py`), the process stops, and the credits stop with it. The next visitor waits a few
seconds for a new process and finds an empty terminal: Connect Cloud documents no disk that outlives a process, so
the run registry and the reuse of identical batteries last as long as the process does. So that Connect Cloud's
own page can show the terminal in a frame, `app.py` lets `https://connect.posit.cloud`, and no other site, frame it
(`PSL_FRAME_ANCESTORS`); the posture page (`S`) reports the allowance. If that page stays blank, open the address
itself.

**What it costs.** Credits accrue for each hour a process runs: 0.75 for each processor plus 0.25 for each GB of
memory in the compute setting. That is 1.25 an hour at 1 CPU and 2 GB, and 1.0 at 1 GB, which is enough for the
`demo` profile (measured on one processor: a run peaks at 0.43 GiB and is on screen in about 45 seconds, 17 when
an identical battery is reused; `light` and `full` want 2 GB). A ten minute visit and the five idle minutes after
it come to about 0.3 credits. The content's Usage page shows what has been used.

## 4. GitHub Codespaces (the live terminal on demand)

A codespace is a small virtual machine that GitHub starts from the repository. A personal account has 120 core
hours and 15 GB of storage a month without charge (60 hours on the two core machine), and without a payment method
on file use is blocked at the quota. It is not a permanent address: the terminal is there while the codespace is
running, which suits a demonstration or a meeting.

`.devcontainer/devcontainer.json` holds the set up: Python 3.12, `requirements.txt` installed when the codespace is
created, and `python app.py` run each time it is opened.

1. On the repository's page: **Code**, **Codespaces**, **Create codespace on main**. The first start installs the
   packages, which takes a few minutes.
2. The panel at the bottom prints the address, `https://<codespace>-8070.app.github.dev`, and a notice offers
   **Open in Browser**. The address is private to the owner, signed in to GitHub. If the panel has been closed,
   `python app.py` in a new terminal starts the demonstration again.
3. To let others in: the **Ports** tab, right click port 8070, **Port Visibility**, **Public**. A visitor passes a
   notice from GitHub once and then sees the terminal. Check the visibility again after the codespace has been
   restarted.
4. Stop it when the demonstration is over, at <https://github.com/codespaces> (the menu beside the codespace,
   **Stop codespace**); the same page starts it again, at the same address.

Left alone, a codespace stops thirty minutes after the last activity in it. Requests to a forwarded port are not
activity, but a line in the codespace's terminal is, so `app.py` prints one line a minute while somebody is using
the terminal: the codespace stays up through a demonstration and stops half an hour after the last visitor's page
goes idle. A codespace also stops after twelve hours whatever happens. `PSL_SECRET` is optional here: set it under
the account's Settings, Codespaces, Secrets for a ledger key that outlives a restart.

The same file runs the demonstration on any machine with the requirements installed: `python app.py`.

## 5. GitHub Pages (the replay site, always on)

`python tools/build_static.py --out site --live-url https://<workspace>--psl.modal.run` runs the recorded
batteries and writes a self contained `site/` folder (a built copy ships in the repository). The workflow
`.github/workflows/pages.yml` publishes that folder to GitHub Pages on every push that changes it. Turn Pages
on once, before the first push of the workflow:

    gh api --method POST repos/OWNER/REPO/pages -f build_type=workflow

The site is then at `https://OWNER.github.io/REPO/`. (GitHub's "deploy from a branch" option only serves the
root or `/docs`, which is why the workflow is used.) Rebuild and recommit `site/` when the model changes. The
builder records four runs, each on its own seed: the default question, the same question again on the next seed
(an independent replication a reader can compare with the first), and two more questions.

When the live terminal moves to another host, the link on the replay site is changed without recording the runs
again (two files change, and nothing but Python is needed):

    python3 tools/build_static.py --out site --relink https://<the new address>
    git add site && git commit -m "Replay site: new address of the live terminal" && git push

## 6. Other hosts

The `Dockerfile` runs the terminal on any Docker host: a Hugging Face Docker Space (PRO; put the front matter
`sdk: docker` and `app_port: 7860` at the top of `README.md`, set `PSL_SECRET` as a Space secret and keep
`PSL_FRAME_ANCESTORS` as the Dockerfile sets it so the Space page can embed the terminal), Render
(`render.yaml` is a one click blueprint), Railway, Fly or Google Cloud Run. The Dockerfile sets open gates and the
`demo` profile for a public demonstration; an authority deployment overrides them (section 7).

What a host must offer: one long lived process (a run is a background computation that must survive between
requests, and the terminal keeps its state in that process), about 25 processor seconds and 0.5 GiB for a `demo`
run, and Python 3.12 or later. That rules out the free instances of Render and Koyeb (a tenth of a processor and
512 MB), and serverless platforms such as Vercel, where keeping functions alive for a run is what made it
expensive. Google Cloud Run has a monthly free tier but asks for a card, and needs instance based billing (the
processor allocated outside requests) for a run to progress.

## 7. Inside an authority

`deploy/docker-compose.yml` runs the terminal in header authentication mode behind an nginx proxy
(`deploy/nginx.conf`) that sets `X-Remote-User` from the authority's single sign on and `X-PSL-Role`
(`viewer`, `preparer`, `approver`, `admin`) from its directory, and strips any client supplied copy of those
headers. Typed names are ignored in this mode; the approver list (`PSL_APPROVERS`), the register
(`PSL_REGISTER`) and four eyes apply. Runs persist on the `psl-runs` volume. Set `PSL_SECRET` from the secret
store, turn dev mode off, and leave `PSL_FRAME_ANCESTORS` unset. The entry point is `dash_app.py`; `app.py` is
the public demonstration and is not for an authority.

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
| `PSL_REUSE` | `on`: an identical battery replays its stored run instead of simulating again (the public demonstration) |
| `PSL_IDLE_SECONDS` | seconds without input after which an open page stops polling the server unless a run is in progress (90; `app.py` sets 300) |
| `PSL_FRAME_ANCESTORS` | origins allowed to embed the terminal (`app.py` allows Posit Connect Cloud's page, the Dockerfile a Hugging Face Space; otherwise none) |
| `PSL_RUNS_DIR` | where runs are written (a directory that cannot be written falls back to the system's temporary directory) |

Check the posture page (`S`) after deploying: a warning is recorded in every run's artefacts and a failing
control blocks release.
