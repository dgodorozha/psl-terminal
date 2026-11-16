"""Keep the tables in the documents identical to the code they describe.

docs/METHOD.md states the method equation by equation; its tables of firms, instruments, assumptions,
constants, variants, strategies, mechanisms, the accounting map and the profiles are generated from the code,
between markers of the form

    <!-- generated:assumptions -->
    ...
    <!-- /generated:assumptions -->

so a definition in the document cannot drift from its implementation. The test suite runs the check.

    python tools/sync_docs.py            # rewrite the generated blocks
    python tools/sync_docs.py --check    # exit code 1 if a document is out of date
"""

import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from config import PROFILES  # noqa: E402
from psl import assumptions as AS  # noqa: E402
from psl import assurance as ASR  # noqa: E402
from psl import welfare as W  # noqa: E402
from psl.firms import default_firms  # noqa: E402
from psl.mechanisms import MECHANISMS  # noqa: E402
from psl.policies import BOUNDS, DEFAULT_BATTERY, LIBRARY, describe, library_policy  # noqa: E402

DOCS = ("docs/METHOD.md",)


def _num(x):
    if isinstance(x, bool):
        return "yes" if x else "no"
    if isinstance(x, int) or float(x).is_integer():
        return f"{float(x):,.0f}"
    return f"{x:.4g}"


def firms():
    L = ["| Firm | Sector | Revenue $bn | Margin | Growth | Capability | Safety | Reach | In scope | Mobility | Culture | Beta | Idio vol | PE |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for f in default_firms():
        L.append(f"| {f['label']} | `{f['sector']}` | {f['revenue']:g} | {f['margin']:.0%} | {f['growth']:.0%} | {f['capability']:g} | "
                 f"{f['safety']:g} | {f['reach']:g} | {f['scope_share']:.0%} | {f['mobility']:g} | {f['culture']:g} | {f['beta']:g} | "
                 f"{f['idio_vol']:.0%} | {f['pe']:g} |")
    return "\n".join(L)


def instruments():
    L = ["| Name | Label | In force from month | What it does |", "|---|---|---|---|"]
    for name in LIBRARY:
        p = library_policy(name)
        L.append(f"| `{name}` | {p['label']} | {p['phase_in']} | {describe(p)} |")
    L += ["", "The default battery is " + ", ".join(f"`{n}`" for n in DEFAULT_BATTERY) + ". An instrument is a bounded JSON document; bounds: "
          + ", ".join(f"`{k}` {lo:g} to {hi:g}" for k, (lo, hi) in BOUNDS.items())
          + ". Custom instruments are validated, clamped to the bounds (clamping is reported), hashed and carried in the battery hash and the ledger."]
    return "\n".join(L)


def assumptions():
    L = ["| Assumption | Key | Value | Plausible range | Accepted bounds | Unit | Meaning | Enters |", "|---|---|---|---|---|---|---|---|"]
    for k, (default, lo, hi, unit, meaning) in AS.SPEC.items():
        r0, r1 = AS.RANGE[k]
        L.append(f"| {AS.TITLE[k]} | `{k}` | {_num(default)} | {_num(r0)} to {_num(r1)} | {_num(lo)} to {_num(hi)} | {unit} | {meaning} | "
                 f"{'the accounting only' if k in AS.WELFARE_ONLY else 'the simulation'} |")
    L += ["", f"{len(AS.SPEC)} assumptions; {len(AS.WELFARE_ONLY)} enter only the welfare accounting and are recomputed exactly from the stored "
          f"paths when they change, the other {len(AS.SPEC) - len(AS.WELFARE_ONLY)} change the simulated economy and are re simulated."]
    return "\n".join(L)


def correlated():
    return "\n".join(f"- {', '.join(f'`{k}`' for k in group)}: rank correlation about {rho:g} ({why})." for group, rho, why in AS.CORRELATED)


def constants():
    return "\n".join(f"- **{k}**: {v}." for k, v in AS.CONSTANTS.items())


def structural():
    L = ["| Variant | What changes |", "|---|---|"]
    L += [f"| `{k}` | {v['note']} |" for k, v in ASR.STRUCTURAL.items()]
    return "\n".join(L)


def gaming():
    L = ["| Strategy | What changes |", "|---|---|"]
    L += [f"| `{k}` | {v['note']} |" for k, v in ASR.GAMING.items()]
    return "\n".join(L)


def account_map():
    L = ["| Simulated flow | Enters | Kind | Whose | Note |", "|---|---|---|---|---|"]
    L += [f"| `{m['flow']}` | {m['enters']} | {m['kind']} | {m['who']} | {m['note']} |" for m in W.ACCOUNT_MAP]
    return "\n".join(L)


def mechanisms():
    out = []
    for i, m in enumerate(MECHANISMS, 1):
        out += [f"**{i}. {m['mechanism']}.**", "",
                f"- Form: `{m['equation']}`",
                f"- Assumptions: {', '.join(f'`{k}`' for k in m['assumptions'])}",
                f"- Rests on: {m['source']}",
                f"- Identifying assumption: {m['identifying_assumption']}",
                f"- Calibration: {m['calibration']}",
                f"- What would test it: {m['validation_test']}",
                f"- Status: {m['status']}" + ("; tested in the Lab when an event is uploaded" if m["tested_here"] else ""), ""]
    return "\n".join(out).rstrip()


def profiles():
    L = ["| Profile | Paths (start to ceiling) | Horizon | Resolve the decision to within | Catastrophe probability to within | Bootstrap | "
         "Screen paths | Joint draws x paths | Variance: inputs, base, paths | Variant paths | Red team paths | Batches |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for name, p in PROFILES.items():
        L.append(f"| `{name}` | {p['paths']} to {p['max_paths']:,} | {p['horizon']} months | ${p['precision']['nsv_gap_bn']:g}bn | "
                 f"{p['precision']['p_catastrophe_halfwidth']:.0%} | {p['boot']:,} | {p['screen_paths']} | {p['joint_draws']} x {p['joint_paths']} | "
                 f"{p['sobol_k']}, {p['sobol_base']}, {p['sobol_paths']} | {p['variant_paths']} | {p['redteam_paths']} | {p['batches']} |")
    return "\n".join(L)


def components():
    L = ["| Component | Sign in the net | Definition (per path, present value, $bn) |", "|---|---|---|"]
    D = {
        "harm_avoided": "`harm_valuation_multiplier x sum_t d_t (h_SQ,t - h_P,t)`, with `h` the harm expected in the month given the state the path has reached (section 8)",
        "cs_change": "`(consumer_surplus_base_bn / 12) x sum_t d_t (Q_P,t^e - Q_SQ,t^e)`, `e = cs_elasticity`, `Q` the AI service index (released capability times reach, revenue weighted, 1 at the start)",
        "productivity_change": "`(1 - benefit_overlap_share) x (productivity_base_bn / 12) x sum_t d_t (Q_P,t^e' T_P,t^tau - Q_SQ,t^e' T_SQ,t^tau)`, `e' = productivity_elasticity`, `tau = trust_elasticity`, `T` public trust",
        "producer_surplus_change": "`domestic_ownership_share x sum_t d_t (operating profit_P,t - operating profit_SQ,t)`, operating profit before compliance, fines, liability, premiums and relocation",
        "compliance_cost": "`compliance_deadweight_share x sum_t d_t (compliance_P,t - compliance_SQ,t)`",
        "enforcement_cost": "`(enforcement_cost_bn / 12) x sum_t d_t (e_P,t - e_SQ,t)`, `e` the enforcement intensity",
        "leakage": "`leakage_value_share x sum_t d_t (offshore revenue_P,t - offshore revenue_SQ,t)`",
        "relocation_cost": "`sum_t d_t (relocation_P,t - relocation_SQ,t)`",
        "labour_change": "`labour_adjustment_bn x sum_t d_t (max(Q_P,t - Q_P,t-1, 0) - max(Q_SQ,t - Q_SQ,t-1, 0))`, `Q_0 = 1`",
        "insurance_admin_cost": "`insurance_admin_share x loading / (1 + loading) x sum_t d_t (premium_P,t - premium_SQ,t)`, `loading = insurance_loading`",
    }
    for k in W.COMPONENTS:
        L.append(f"| `{k}` | {'+' if k in W.BENEFITS else '-'} | {D[k]} |")
    return "\n".join(L)


def benchmarks():
    from psl import benchmarks as BM
    from psl.validation import _fmt
    L = ["| Benchmark | Kind | Observed | Standard error | Allowance for distance | Model quantity | Mechanisms | Source |", "|---|---|---|---|---|---|---|---|"]
    for b in BM.table():
        d = 1 if b["sd_total"] < 0.1 else 0
        src = "; ".join(f"[{x['cite']}]({x['url']})" if x.get("url") else x["cite"] for x in b["sources"])
        L.append(f"| {b['title']} (`{b['id']}`) | {b['kind']} | {_fmt(b['value'], b['unit'], d)} | {_fmt(b['se'], b['unit'], d, signed=False)}: {b['se_basis']} | "
                 f"{_fmt(b['transport'], b['unit'], d, signed=False)}: {b['transport_basis']} | {b['mapping']} | "
                 f"{', '.join(m.replace('_', ' ') for m in b['mechanisms'])} | {src} |")
    return "\n".join(L)


def benchmarks_not_used():
    from psl import benchmarks as BM
    L = ["| Evidence examined | Bears on | Why it is not a benchmark |", "|---|---|---|"]
    for x in BM.NOT_USED:
        cite = f"[{x['source']['cite']}]({x['source']['url']})" if x["source"].get("url") else x["source"]["cite"]
        L.append(f"| {x['evidence']} ({cite}) | {x['bears_on'].replace('_', ' ')} | {x['why_not']} |")
    return "\n".join(L)


GENERATORS = {"benchmarks": benchmarks, "benchmarks_not_used": benchmarks_not_used, "firms": firms, "instruments": instruments, "assumptions": assumptions, "correlated": correlated, "constants": constants,
              "structural": structural, "gaming": gaming, "account_map": account_map, "mechanisms": mechanisms, "profiles": profiles,
              "components": components}
_BLOCK = re.compile(r"(<!-- generated:(\w+) -->\n)(.*?)(<!-- /generated:\2 -->)", re.S)


def render(text):
    def sub(m):
        name = m.group(2)
        if name not in GENERATORS:
            raise SystemExit(f"unknown generated block: {name}")
        return m.group(1) + GENERATORS[name]() + "\n" + m.group(4)
    return _BLOCK.sub(sub, text)


def blocks(text):
    return [m.group(2) for m in _BLOCK.finditer(text)]


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    check = "--check" in argv
    stale = []
    for rel in DOCS:
        path = os.path.join(ROOT, rel)
        with open(path) as f:
            old = f.read()
        new = render(old)
        if new != old:
            stale.append(rel)
            if not check:
                with open(path, "w") as f:
                    f.write(new)
    if check and stale:
        print("out of date: " + ", ".join(stale) + "; run python tools/sync_docs.py")
        return 1
    print(("up to date" if not stale else "rewritten: " + ", ".join(stale)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
