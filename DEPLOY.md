# Deploying the Policy Scenario Lab

Two public addresses, both free: a Hugging Face Space runs the live terminal, and GitHub Pages serves the
replay site (recorded runs rendered in the browser, no server). Each links to the other.

## 1. GitHub (source of truth)

Create an empty repository on GitHub and push the contents of the zip to its `main` branch (drag and drop
in the browser works; the repository root must hold `dash_app.py`, `psl/`, `assets/`, `Dockerfile` and
`README.md`).

## 2. Hugging Face Space (the live terminal, free)

1. Sign in at huggingface.co and choose New Space. Name it (for example `psl-terminal`), pick the Docker
   SDK with the blank template, CPU basic (free), and public or private as you prefer.
2. In the Space's Settings, under Variables and secrets, add a secret `PSL_SECRET` with a 64 character hex
   value (`python -c "import secrets;print(secrets.token_hex(32))"`). Without it the ledger is signed with
   a key that changes on every restart, which the posture page reports.
3. Connect GitHub to the Space so every push redeploys. In the GitHub repository, Settings → Secrets and
   variables → Actions, add `HF_TOKEN` (a write token from huggingface.co/settings/tokens) and `HF_SPACE`
   (the Space id, `your-name/psl-terminal`). The workflow in `.github/workflows/sync-to-hf.yml` mirrors
   `main` to the Space on every push. Alternatively push directly:
   `git remote add space https://huggingface.co/spaces/your-name/psl-terminal && git push space main`.
4. The first build takes a few minutes. The terminal is then at
   `https://your-name-psl-terminal.hf.space` (and embedded on the Space page). Dev mode is on in the
   Dockerfile, so `Developer1` and `Developer2` work at the gates; the profile is `demo` (about half a
   minute a run). Change either in the Dockerfile `ENV` line or in the Space's variables.

What to expect: one long lived process with 2 vCPUs and 16 GB of memory, which the demo and light profiles
need. The Space sleeps after 48 hours without visitors and wakes on the next visit in about a minute. The run
registry lives on the container's disk and is lost when the Space restarts (persistent storage is a paid
add on). A free Space cannot sit behind your own domain.

The Dockerfile pins BLAS to one thread (`OPENBLAS_NUM_THREADS=1`), which is what resolved stalled runs on a
shared host before, and allows the terminal to be framed by huggingface.co so the Space page can display it
(`PSL_FRAME_ANCESTORS`); unset that variable on any other host.

## 3. GitHub Pages (the replay site, free, always on)

`python tools/build_static.py --out site --live-url https://your-name-psl-terminal.hf.space` runs the
recorded batteries and writes a self contained `site/` folder. Commit it to the repository (or to a
separate one), then in Settings → Pages choose Deploy from a branch, branch `main`, folder `/site` (or copy
it to `/docs` and choose that). The site is live at `https://your-name.github.io/<repository>/` within a
minute or two. Rebuild and recommit when the model changes.

## 4. Other hosts

The same Dockerfile runs on Render (`render.yaml` is a one click blueprint), Railway and Fly, all of which
charge for an always on service of this size. Vercel and other serverless platforms are not suitable: a run
is a background computation that must survive between requests, which serverless does not promise, and
keeping functions alive for it is what made it expensive.

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
| `PSL_PROFILE` | `demo` (half a minute), `light`, or `full` |
| `PSL_DEV_MODE` | `on` accepts Developer1 and Developer2 at the gates; never in production |
| `PSL_REGISTER` | register of regulated persons the approver is checked against |
| `PSL_AUTH_MODE` | `open` (names typed) or `header` (identities from an authenticating proxy) |
| `PSL_FRAME_ANCESTORS` | origins allowed to embed the terminal (the Space sets huggingface.co) |
| `PSL_RUNS_DIR` | where runs are written |

Check the posture page (`S`) after deploying: a warning is recorded in every run's artefacts and a failing
control blocks release.
