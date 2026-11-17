"""The public demonstration: the terminal with open gates on the demo profile.

Hosts that deploy a Dash app straight from a repository start here: this is the primary file for Posit Connect Cloud,
and `python app.py` is what a GitHub codespace runs. It sets the demonstration's defaults and hands over to dash_app,
which remains the entry point for an authority (named gates, the register, four eyes, the full profile).

Every default below gives way to an environment variable of the same name:

  PSL_GATES=open         single click gates without identities
  PSL_PROFILE=demo       120 paths growing to at most 480, about half a minute a run
  PSL_REUSE=on           an identical battery replays its stored run instead of simulating again
  PSL_IDLE_SECONDS=300   an untouched page keeps polling for five minutes, then stops; on a host that stops the
                         process as soon as nobody is connected that is how long a result stays on screen unattended
  PSL_TICK_PACE=0.02     seconds a simulated month stays on the wire, as on the other public hosts (0.05 otherwise)
  PSL_WORKERS            the processor cores the host allows this process, at most four (a container sold as one
                         processor runs the simulations one at a time, which also keeps memory at its lowest)
  PSL_FRAME_ANCESTORS=https://connect.posit.cloud
                         so that Posit Connect Cloud's own page can show the terminal in a frame; no other site may,
                         and the posture page (S) reports the allowance
  OPENBLAS_NUM_THREADS, OMP_NUM_THREADS, MKL_NUM_THREADS = 1
                         linear algebra on one thread: the simulations are already run side by side

Set PSL_SECRET as a secret variable on the host so the ledger is signed with a key that outlives the process.
"""

import os
import socket
import threading
import time

from config import available_cores

for _name, _value in {"PSL_GATES": "open", "PSL_PROFILE": "demo", "PSL_REUSE": "on", "PSL_IDLE_SECONDS": "300", "PSL_TICK_PACE": "0.02",
                      "PSL_WORKERS": str(min(4, available_cores())), "PSL_FRAME_ANCESTORS": "https://connect.posit.cloud",
                      "OPENBLAS_NUM_THREADS": "1", "OMP_NUM_THREADS": "1", "MKL_NUM_THREADS": "1"}.items():
    os.environ.setdefault(_name, _value)

from dash_app import BUILD, CFG, STORE, app, server  # noqa: E402,F401


def address(env=None):
    """Where a browser finds the terminal: the forwarded address in a GitHub codespace, the local one elsewhere."""
    env = os.environ if env is None else env
    name, domain = env.get("CODESPACE_NAME", "").strip(), env.get("GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN", "").strip()
    if env.get("CODESPACES", "").lower() == "true" and name and domain:
        return f"https://{name}-{CFG.port}.{domain}"
    return f"http://{CFG.host}:{CFG.port}"


def already_running(host=None, port=None):
    """A codespace runs this file every time a browser attaches to it; the second start finds the first one's port."""
    host = (host or CFG.host).replace("0.0.0.0", "127.0.0.1")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.settimeout(1.0)
        return probe.connect_ex((host, int(port or CFG.port))) == 0


def heartbeat(seen, every=60.0, out=print):
    """One line a minute while somebody is using the terminal. A codespace stops thirty minutes after the last
    activity in it, and a line in its terminal is activity, so the codespace stays up while the demonstration is in use
    and no longer: an untouched page stops asking after PSL_IDLE_SECONDS, and the lines stop with it."""
    while True:
        time.sleep(every)
        if time.time() - seen["at"] < every:
            out(time.strftime("%H:%M") + " in use", flush=True)


if __name__ == "__main__":
    in_codespace = os.environ.get("CODESPACES", "").lower() == "true"
    if already_running():
        print(f"PSL TERMINAL is already running on port {CFG.port}: {address()}", flush=True)
        raise SystemExit(0)
    print(f"PSL TERMINAL {BUILD} (public demonstration) · {address()} · profile {CFG.profile} · gates {CFG.gates} · "
          f"runs in {STORE.root}" + (" · WARNING: ephemeral ledger key" if CFG.ephemeral_secret else ""), flush=True)
    if in_codespace:
        print("The address is private to you until the port is made public: Ports tab, right click the port, Port Visibility, "
              "Public.", flush=True)
        seen = {"at": 0.0}

        @server.before_request
        def _seen():
            seen["at"] = time.time()

        threading.Thread(target=heartbeat, args=(seen,), daemon=True).start()
    app.run(debug=False, host=CFG.host, port=CFG.port, threaded=True)
