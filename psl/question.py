"""Reading the policy question.

The question a policymaker types is read deterministically into a plan:
which instruments to compare (named ones, or the default battery), the
horizon, and the constraints that define the decision (an industry loss
the economy can bear, a social cost budget, a ceiling on the probability
of a major incident or a catastrophe, a minimum harm reduction, a
consumer surplus floor). A model, when configured, may propose the same
structure, and its proposal is validated by the same bounds; the parser
is the path that always runs.

A question may also name the seed of the random streams ("seed 11"): the
same question on another seed is an independent replication of the run.
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
    out = {"question": q, "policies": [], "constraints": {}, "horizon_months": None, "notes": [], "seed": None}
    # "seed 11" anywhere in the question repeats the run on another family of random streams (a replication)
    m = re.search(r"\bseed\s*(?:=|:|of)?\s*(\d{1,6})\b", ql)
    if m:
        out["seed"] = int(m.group(1))
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

    # A word that appears only inside another instrument's name, or only as a description, does not name an
    # instrument of its own: the alternatives are the ones the question asks about.
    def only_within(short_rx, long_rx):
        longs = [m.span() for m in re.finditer(long_rx, ql)]
        shorts = [m.span() for m in re.finditer(short_rx, ql)]
        return bool(shorts) and all(any(a <= s0 and s1 <= b for a, b in longs) for s0, s1 in shorts)
    drop = set()
    if {"strict_liability", "liability_with_safe_harbour"} <= set(named) and not re.search(r"strict liab|\btort|\binsurance", ql) \
            and only_within(r"liabil\w*", r"liabil\w*\s+(?:with|under)\s+(?:a\s+|the\s+)?safe harbou?r"):
        drop.add("strict_liability")                 # "liability with a safe harbour" alone
    if {"frontier_licensing", "coordinated_licensing"} <= set(named) \
            and only_within(r"licen\w*", r"coordinat\w*\s+(?:frontier\s+)?licen\w*"):
        drop.add("frontier_licensing")               # "coordinated frontier licensing" alone
    if "compute_threshold_reporting" in named and not re.search(r"reporting|executive order", ql):
        drop.add("compute_threshold_reporting")      # "above the compute threshold" describes a scope
    if "mandatory_third_party_evals" in named and not re.search(r"third party|\baudit|red team|\bevals?\b|\bevaluations?\b", ql):
        drop.add("mandatory_third_party_evals")      # "evaluate" the verb
    named = [n for n in named if n not in drop]
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
    spans = []                       # the parts of the question that were read as a horizon, a seed or a constraint
    m = re.search(r"(\d+|one|two|three|four|five|six|seven|eight|nine|ten)\s*(?:-| )?\s*year", ql)
    words = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10}
    if m:
        y = words.get(m.group(1)) or int(m.group(1))
        out["horizon_months"] = int(max(12, min(120, y * 12)))
        spans.append(m.span())
    m = re.search(r"\bseed\s*(?:=|:|of)?\s*\d{1,6}\b", ql)
    if m:
        spans.append(m.span())
    c = out["constraints"]
    m = re.search(r"(?:industry|sector|tech(?:nology)?(?: sector)?|firms?|companies)[^.;]*?(?:loss|cost|hit)[^.;]*?(?:below|under|less than|no more than|at most|within)\s*" + _MONEY, ql)
    if m:
        c["max_industry_loss_bn"] = _bn(m.group(1), m.group(2)); spans.append(m.span())
    m = re.search(r"(?:social|economic|welfare|total)[^.;]*?(?:cost|budget)[^.;]*?(?:below|under|less than|no more than|at most|within)\s*" + _MONEY, ql)
    if m:
        c["max_social_cost_bn"] = _bn(m.group(1), m.group(2)); spans.append(m.span())
    m = re.search(r"budget of\s*" + _MONEY, ql)
    if m and "max_social_cost_bn" not in c:
        c["max_social_cost_bn"] = _bn(m.group(1), m.group(2)); spans.append(m.span())
    m = re.search(r"(?:major incident|serious incident)[^.;]*?(?:below|under|less than|at most)\s*([0-9]+(?:\.[0-9]+)?)\s*(%|percent|per cent)", ql)
    if m:
        c["max_p_major"] = float(m.group(1)) / 100; spans.append(m.span())
    m = re.search(r"catastroph[^.;]*?(?:below|under|less than|at most)\s*([0-9]+(?:\.[0-9]+)?)\s*(%|percent|per cent)", ql)
    if m:
        c["max_p_catastrophe"] = float(m.group(1)) / 100; spans.append(m.span())
    m = re.search(r"(?:cut|reduce|lower)[^.;]*?harm[^.;]*?(?:by at least|by)\s*([0-9]+(?:\.[0-9]+)?)\s*(%|percent|per cent)", ql)
    if m:
        c["min_harm_reduction_pct"] = float(m.group(1)); spans.append(m.span())
    m = re.search(r"consumer surplus[^.;]*?(?:by more than|more than|above|over)\s*([0-9]+(?:\.[0-9]+)?)\s*(%|percent|per cent)", ql)
    if m:
        c["max_cs_loss_pct"] = float(m.group(1)); spans.append(m.span())
    out["unread"] = _unread(ql, spans)
    if out["unread"]:
        out["notes"].append("NOT read as a constraint, so not applied: " + "; ".join(f'"{x}"' for x in out["unread"]))
    return out


_LIMIT = re.compile(r"\b(?:below|under|less than|no more than|not more than|at most|at least|within|not exceed|must|keeping|keep|more than|by at least)\b")
_QUANTITY = re.compile(r"\d|%|\$|\b(?:quarter|half|third|fifth|tenth)\b")
_SEPARATOR = re.compile(r";|\.(?=\s|$)|,(?=\s)|\?|\band\b|\bbut\b|\bwhile\b")


def _unread(ql, spans):
    """Clauses of the question that look like a condition (a limit word and a quantity) and were not read as a
    constraint, a horizon or a seed. A condition the Lab does not apply must be visible before Gate 1, not silently
    dropped: the plan lists these, and the approver decides whether the battery still answers the question."""
    out, start = [], 0
    cuts = [m.span() for m in _SEPARATOR.finditer(ql)] + [(len(ql), len(ql))]
    for a, b in cuts:
        clause, lo, hi = ql[start:a], start, a
        start = b
        text = clause.strip()
        if not text or not _LIMIT.search(text) or not _QUANTITY.search(text):
            continue
        if any(s0 < hi and s1 > lo for s0, s1 in spans):
            continue
        out.append(text[:140])
    return out


def describe(plan):
    """One sentence on how the question was read."""
    c = plan["constraints"]
    plan = dict(plan, notes=[n for n in plan["notes"] if not n.startswith("NOT read")])
    bits = [f"{len(plan['policies']) - 1} instruments and the status quo ({', '.join(plan['notes'])})"]
    if plan.get("horizon_months"):
        bits.append(f"horizon {plan['horizon_months'] // 12} years")
    if plan.get("seed") is not None:
        bits.append(f"seed {plan['seed']}")
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
    if plan.get("unread"):
        bits.append("NOT read as a constraint, so not applied: " + "; ".join(f'"{x}"' for x in plan["unread"]))
    return "; ".join(bits)
