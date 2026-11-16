"""What a run costs: wall time, processor seconds and peak memory by stage, and what that is in money on a host
that bills by the second.

    python tools/cost.py --profile demo
    python tools/cost.py --profile full --cpu-price 0.0000131 --mem-price 0.00000222 --request-cpu 1 --request-mem 1

The run is the default question (or --question) through the whole pipeline, without the gates. It is then repeated
with reuse on, which is what a second visitor asking the same question costs. Prices default to Modal's list prices
in November 2026 (per physical core per second and per GiB per second); Modal bills the larger of what a container
requests and what it uses for as long as the container is up, so the table separates the run from the idle time
before the container scales to zero.
"""

import argparse
import os
import resource
import sys
import tempfile
import time
import warnings

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.environ.setdefault("PSL_SECRET", "cost")
warnings.simplefilter("ignore")

from config import PROFILES  # noqa: E402
from psl import __version__  # noqa: E402
from psl.pipeline import make_battery, run_battery  # noqa: E402
from psl.question import DEFAULT_QUESTION, parse  # noqa: E402


def measure(bat, outdir, reuse=False):
    marks = []
    t0, c0 = time.time(), time.process_time()
    arte, _ = run_battery(bat, outdir, progress=lambda step, phase, **k: marks.append((time.time(), step, phase)), reuse=reuse)
    t1, c1 = time.time(), time.process_time()
    stages, order = {}, []
    for i, (t, step, phase) in enumerate(marks):
        end = marks[i + 1][0] if i + 1 < len(marks) else t1
        key = step if step != "assurance" else "assurance: " + phase.split(":")[0].lower()
        key = {"assurance: structural variant": "assurance: structural variants", "assurance: variance decomposition over the "
               + phase.split("over the ")[-1]: "assurance: variance"}.get(key, key)
        if key.startswith("assurance: variance"):
            key = "assurance: variance"
        if key not in stages:
            stages[key] = 0.0; order.append(key)
        stages[key] += end - t
    return {"wall": t1 - t0, "cpu": c1 - c0, "stages": [(k, stages[k]) for k in order], "paths": arte["paths"],
            "reused": bool(arte["run"].get("reused_from")), "preferred": arte["results"]["preferred"]}


def money(wall, cpu_s, peak_gib, a):
    """Billed on the larger of request and use: processor seconds and GiB seconds over the wall time of the run."""
    return max(cpu_s, a.request_cpu * wall) * a.cpu_price + max(peak_gib, a.request_mem) * wall * a.mem_price


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--profile", default="demo", choices=sorted(PROFILES))
    ap.add_argument("--question", default=DEFAULT_QUESTION)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--cpu-price", type=float, default=0.0000131, help="$ per core per second")
    ap.add_argument("--mem-price", type=float, default=0.00000222, help="$ per GiB per second")
    ap.add_argument("--request-cpu", type=float, default=1.0, help="cores the container requests")
    ap.add_argument("--request-mem", type=float, default=1.0, help="GiB the container requests")
    ap.add_argument("--idle-seconds", type=float, default=600 + 90, help="seconds a container stays up after the last action: the scale "
                    "down window plus the time before an untouched page stops polling")
    ap.add_argument("--credit", type=float, default=30.0, help="monthly credit, $")
    a = ap.parse_args(argv)
    bat = make_battery(parse(a.question), budget=dict(PROFILES[a.profile]), profile=a.profile, seed=a.seed)
    with tempfile.TemporaryDirectory() as d:
        first = measure(bat, os.path.join(d, "first"))
        peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / (1024.0 * 1024.0)
        again = measure(bat, os.path.join(d, "second"), reuse=True)
    print(f"PSL {__version__}, profile {a.profile}, {first['paths']} paths, {os.cpu_count()} cores")
    print(f"\n{'stage':<34s}{'seconds':>9s}{'share':>8s}")
    for k, v in first["stages"]:
        print(f"{k:<34s}{v:9.1f}{100 * v / first['wall']:7.0f}%")
    print(f"{'run, computed':<34s}{first['wall']:9.1f}   processor {first['cpu']:.0f} s, peak memory {peak:.2f} GiB")
    print(f"{'run, identical battery reused':<34s}{again['wall']:9.1f}   processor {again['cpu']:.1f} s" + ("" if again["reused"] else "   (NOT reused)"))
    run_c = money(first["wall"], first["cpu"], peak, a)
    reuse_c = money(again["wall"], again["cpu"], peak, a)
    idle_c = a.idle_seconds * (a.request_cpu * a.cpu_price + a.request_mem * a.mem_price)
    print(f"\nat ${a.cpu_price:.7f} a core second and ${a.mem_price:.8f} a GiB second, requesting {a.request_cpu:g} core and {a.request_mem:g} GiB:")
    print(f"  a computed run                 ${run_c:.5f}")
    print(f"  a reused run                   ${reuse_c:.5f}")
    print(f"  idle until scale down ({a.idle_seconds:.0f} s)  ${idle_c:.5f}")
    print(f"  a visit with one computed run  ${run_c + idle_c:.5f}   ({a.credit / (run_c + idle_c):,.0f} visits on a ${a.credit:g} credit)")
    print(f"  an hour awake and idle         ${3600 * (a.request_cpu * a.cpu_price + a.request_mem * a.mem_price):.4f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
