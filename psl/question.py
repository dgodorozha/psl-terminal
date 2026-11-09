"""Reading the policy question.

The question a policymaker types is read deterministically into a plan:
which instruments to compare (named ones, or the default battery), the
horizon, and the constraints that define the decision (an industry loss
the economy can bear, a social cost budget, a ceiling on the probability
of a major incident or a catastrophe, a minimum harm reduction, a
consumer surplus floor). A model, when configured, may propose the same
structure, and its proposal is validated by the same bounds; the parser
is the path that always runs.
"""

import re

from .policies import KEYWORDS, DEFAULT_BATTERY, LIBRARY

DEFAULT_QUESTION = ("Which AI regulatory instrument best reduces expected harm from frontier AI over the next five years, "
                    "keeping the technology sector's net loss below $400bn and the gross social cost under $150bn?")

_MONEY = r"\$?\s*([0-9]+(?:\.[0-9]+)?)\s*(bn|billion|tn|trillion|m|million)?"


def _bn(val, unit):
    v = float(val)
    unit = (unit or "bn").lower()
    if unit in ("tn", "trillion"):
        return v * 1000
    if unit in ("m", "million"):
        return v / 1000
    return v


def parse(question):
    q = (question or "").strip()
    ql = q.lower()
    out = {"question": q, "policies": [], "constraints": {}, "horizon_months": None, "notes": []}
    # instruments named in the question
    named = []
    for name, keys in KEYWORDS.items():
        if any(re.search(r"\b" + re.escape(k), ql) for k in keys):
            named.append(name)
    # a package keyword also names its parts; keep the order of the library
    if "all polic" in ql or "every instrument" in ql or "all instruments" in ql or "whole library" in ql:
        named = [n for n in LIBRARY if n != "baseline"]
        out["notes"].append("every instrument in the library")
    if "licensing plus liability" in ql or "licensing and liability" in ql:
        named = [n for n in named if n not in ("frontier_licensing", "strict_liability")]
    pols = ["baseline"] + [n for n in LIBRARY if n in named and n != "baseline"]
    if len(pols) < 3:
        pols = list(DEFAULT_BATTERY)
        for n in named:
            if n not in pols:
                pols.append(n)
        out["notes"].append("default battery" + (" plus the instruments named" if named else ""))
    elif not out["notes"]:
        out["notes"].append("instruments named in the question")
    out["policies"] = pols
    # horizon
    m = re.search(r"(\d+|one|two|three|four|five|six|seven|eight|nine|ten)\s*(?:-| )?\s*year", ql)
    words = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10}
    if m:
        y = words.get(m.group(1)) or int(m.group(1))
        out["horizon_months"] = int(max(12, min(120, y * 12)))
    c = out["constraints"]
    m = re.search(r"(?:industry|sector|tech(?:nology)?(?: sector)?|firms?|companies)[^.;]*?(?:loss|cost|hit)[^.;]*?(?:below|under|less than|no more than|at most|within)\s*" + _MONEY, ql)
    if m:
        c["max_industry_loss_bn"] = _bn(m.group(1), m.group(2))
    m = re.search(r"(?:social|economic|welfare|total)[^.;]*?(?:cost|budget)[^.;]*?(?:below|under|less than|no more than|at most|within)\s*" + _MONEY, ql)
    if m:
        c["max_social_cost_bn"] = _bn(m.group(1), m.group(2))
    m = re.search(r"budget of\s*" + _MONEY, ql)
    if m and "max_social_cost_bn" not in c:
        c["max_social_cost_bn"] = _bn(m.group(1), m.group(2))
    m = re.search(r"(?:major incident|serious incident)[^.;]*?(?:below|under|less than|at most)\s*([0-9]+(?:\.[0-9]+)?)\s*(%|percent|per cent)", ql)
    if m:
        c["max_p_major"] = float(m.group(1)) / 100
    m = re.search(r"catastroph[^.;]*?(?:below|under|less than|at most)\s*([0-9]+(?:\.[0-9]+)?)\s*(%|percent|per cent)", ql)
    if m:
        c["max_p_catastrophe"] = float(m.group(1)) / 100
    m = re.search(r"(?:cut|reduce|lower)[^.;]*?harm[^.;]*?(?:by at least|by)\s*([0-9]+(?:\.[0-9]+)?)\s*(%|percent|per cent)", ql)
    if m:
        c["min_harm_reduction_pct"] = float(m.group(1))
    m = re.search(r"consumer surplus[^.;]*?(?:by more than|more than|above|over)\s*([0-9]+(?:\.[0-9]+)?)\s*(%|percent|per cent)", ql)
    if m:
        c["max_cs_loss_pct"] = float(m.group(1))
    return out


def describe(plan):
    """One sentence on how the question was read."""
    c = plan["constraints"]
    bits = [f"{len(plan['policies']) - 1} instruments against the baseline ({', '.join(plan['notes'])})"]
    if plan.get("horizon_months"):
        bits.append(f"horizon {plan['horizon_months'] // 12} years")
    for k, v in c.items():
        if k == "max_industry_loss_bn":
            bits.append(f"industry loss at most ${v:,.0f}bn")
        elif k == "max_social_cost_bn":
            bits.append(f"gross social cost at most ${v:,.0f}bn")
        elif k == "max_p_major":
            bits.append(f"probability of a major incident at most {v:.0%}")
        elif k == "max_p_catastrophe":
            bits.append(f"probability of a catastrophe at most {v:.0%}")
        elif k == "min_harm_reduction_pct":
            bits.append(f"harm cut by at least {v:.0f}%")
        elif k == "max_cs_loss_pct":
            bits.append(f"consumer surplus loss at most {v:.0f}%")
    return "; ".join(bits)
