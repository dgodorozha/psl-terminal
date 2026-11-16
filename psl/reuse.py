"""Reuse of an identical battery.

A battery is deterministic: the same approved battery (the same hash: question, constraints, instruments, firms,
assumptions, horizon, sampling plan, seed, evidence base), run by the same code on the same numerical libraries with
the same uploaded series, gives the same figures. A public demonstration is asked the same question again and again,
so when reuse is switched on (PSL_REUSE=on) a battery whose key matches a completed run in the registry is not
simulated again: the stored figures are copied into the new run, the recorded stream is replayed to the panels, and
the critic then recomputes every figure of the new run from the copied paths exactly as it does for a computed one.

Nothing is hidden: the ledger records `battery_reused` with the source run, the artefacts carry `run.reused_from`,
and the briefing and the transparency record say which run computed the figures and when. Reuse is off by default,
which is what an authority deployment runs with.

The key is a SHA-256 over the battery hash, the code fingerprint (every module of this package), the versions of
Python, numpy and scipy, the start date of the wire and the uploaded series. A change to any of them is a miss.
"""

import hashlib
import json
import os
import shutil
import time

from . import code_fingerprint, provenance

MARK = "reuse.json"
COPIED = ("paths.npz", "paths.json", "results.json", "news_sample.json", "prices_sample.json", "assurance.json", "assumptions.json")
NEEDED = COPIED + ("artefacts.json", "battery.json")


def key(bat, datasets=None, start_year=2027, start_month=1):
    prov = provenance()
    doc = {"battery_hash": bat["hash"], "code": code_fingerprint(), "python": ".".join(prov["python"].split(".")[:2]),
           "numpy": prov["numpy"], "scipy": prov["scipy"], "start": [int(start_year), int(start_month)],
           "datasets": hashlib.sha256(json.dumps(datasets or [], sort_keys=True, default=str).encode()).hexdigest()}
    return hashlib.sha256(json.dumps(doc, sort_keys=True).encode()).hexdigest()


def record(outdir, k, bat, source=None):
    """Mark a completed run as reusable. `source` names the run that computed the figures when this one reused them."""
    doc = {"key": k, "battery_hash": bat["hash"], "written": time.time(), "source": source or os.path.basename(os.path.abspath(outdir))}
    tmp = os.path.join(outdir, MARK + ".tmp")
    with open(tmp, "w") as f:
        json.dump(doc, f)
    os.replace(tmp, os.path.join(outdir, MARK))


def find(root, k, exclude=None):
    """The most recent completed run under `root` with this key, or None."""
    best = None
    try:
        names = os.listdir(root)
    except OSError:
        return None
    for name in names:
        d = os.path.join(root, name)
        if exclude and os.path.abspath(d) == os.path.abspath(exclude):
            continue
        try:
            with open(os.path.join(d, MARK)) as f:
                doc = json.load(f)
        except (OSError, ValueError):
            continue
        if doc.get("key") != k or not all(os.path.exists(os.path.join(d, n)) for n in NEEDED):
            continue
        if best is None or doc.get("written", 0) > best[1].get("written", 0):
            best = (d, doc)
    return best


def copy(src, outdir):
    for n in COPIED:
        shutil.copyfile(os.path.join(src, n), os.path.join(outdir, n))
