"""The live PSL terminal on Modal (modal.com): one long lived container serving the Dash app, scaled to zero when
nobody is using it and woken by the next visitor, with the run registry on a persistent volume. The Starter plan
carries a monthly free credit that a demo terminal does not come close to using.

    python3 -m pip install modal && modal setup
    modal secret create psl-secret PSL_SECRET=$(python3 -c "import secrets;print(secrets.token_hex(32))")
    modal deploy modal_app.py            # prints the address: https://<workspace>--psl.modal.run

Only this file is Modal specific; the Dockerfile is for Docker hosts and `python dash_app.py` for a laptop.
"""

import threading
import time

import modal

APP_DIR = "/app"
RUNS_DIR = "/runs"
COMMIT_EVERY = 60          # seconds between volume commits while the container is alive

image = (
    modal.Image.debian_slim(python_version="3.12")
    .pip_install_from_requirements("requirements.txt")
    .env({
        "OPENBLAS_NUM_THREADS": "1", "OMP_NUM_THREADS": "1", "MKL_NUM_THREADS": "1",
        "PSL_HOST": "0.0.0.0", "PSL_RUNS_DIR": RUNS_DIR, "PSL_AUTH_MODE": "open", "PSL_LLM": "off",
        "PSL_PROFILE": "demo", "PSL_DEV_MODE": "on", "PSL_REGISTER": "sample_data/register.csv",
        "PSL_TICK_PACE": "0.02",
    })
    # the repository itself, mounted at start (so a redeploy is seconds, not a rebuild); what is not needed stays out
    .add_local_dir(".", remote_path=APP_DIR, ignore=[
        ".git", ".github", "runs", "site", "shots", "shots_static", ".venv", "deploy",
        "**/__pycache__", "**/.pytest_cache", "**/*.zip", "**/*.mp4", "**/.DS_Store",
    ])
)

runs = modal.Volume.from_name("psl-runs", create_if_missing=True)
app = modal.App("psl-terminal")


def _serve(app_dir=APP_DIR, runs_dir=RUNS_DIR, volume=None):
    """Import the terminal with the repository as the working directory and return its WSGI application."""
    import os
    import sys
    os.chdir(app_dir)
    if app_dir not in sys.path:
        sys.path.insert(0, app_dir)
    os.makedirs(runs_dir, exist_ok=True)
    from dash_app import server
    if volume is not None:
        def _commit():                      # persist the registry while the container lives; Modal also commits on exit
            while True:
                time.sleep(COMMIT_EVERY)
                try:
                    volume.commit()
                except Exception:           # a failed commit is retried next time; it must never take the terminal down
                    pass
        threading.Thread(target=_commit, daemon=True, name="psl-volume-commit").start()
    return server


@app.function(
    image=image,
    secrets=[modal.Secret.from_name("psl-secret")],      # PSL_SECRET, the ledger signing key
    volumes={RUNS_DIR: runs},
    cpu=2.0,
    memory=2048,
    max_containers=1,          # one process: the terminal's state and its gates live in memory
    scaledown_window=900,      # stay up fifteen minutes after the last request, then scale to zero
)
@modal.concurrent(max_inputs=100)    # the poll, the gates and the uploads all arrive at once from one browser
@modal.wsgi_app(label="psl")
def terminal():
    return _serve(volume=runs)
