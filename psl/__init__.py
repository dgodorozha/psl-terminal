"""Policy Scenario Lab (PSL) core library.

An agent based policy laboratory for AI regulation. A battery of candidate
regulatory instruments is run against the same synthetic AI economy: firms
that choose how much to invest in capability, safety and compliance and
where to locate; a regulator whose enforcement follows public pressure;
media agents that turn what happens into a news wire; investors who price
the firms. Each policy is scored on the decision a policymaker faces, the
expected harm it prevents against the economic and social cost it imposes,
with the industry's net gain or loss, the forecast news environment and the
market reaction reported beside it. The status quo is one of the
alternatives. Every expected value carries the confidence interval of its
Monte Carlo estimate, kept apart from the spread of simulated outcomes and
from the range under other assumptions and model structures; every value
judgement is declared in an assumptions file that the critic checks and the
briefing cites. The figures are conditional on the declared model: scenario
evaluations, not validated forecasts.

The simulation is built on the Herding Scenario Lab's governance: a hash
chained signed ledger, two named human gates checked against a register,
an independent critic that recomputes every figure before release, an
evidence pack and a transparency record.
"""

import hashlib
import os
import platform
import sys

__version__ = "1.2.0"


def code_fingerprint() -> str:
    """SHA-256 over the source of every module in this package, in sorted
    order. Recorded in artefacts so a run can be tied to the exact code."""
    here = os.path.dirname(os.path.abspath(__file__))
    h = hashlib.sha256()
    for name in sorted(os.listdir(here)):
        if name.endswith(".py"):
            with open(os.path.join(here, name), "rb") as f:
                h.update(name.encode())
                h.update(f.read())
    return h.hexdigest()


def provenance() -> dict:
    import numpy
    import scipy
    return {
        "psl_version": __version__,
        "code_fingerprint": code_fingerprint(),
        "python": sys.version.split()[0],
        "numpy": numpy.__version__,
        "scipy": scipy.__version__,
        "platform": platform.platform(),
    }
