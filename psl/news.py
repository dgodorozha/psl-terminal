"""The press: four media agents that turn the simulation's events into a
news wire, and the aggregate news forecast.

The engine records every event on the representative path (incidents,
catastrophes, enforcement actions, relocations, releases, licence delays,
policy milestones, market moves, a fall in trust, a hearing, a labour
milestone). Each month four outlets with different beats and tones choose
the stories they will run from those events by newsworthiness, and write a
headline from a template bank with the event's own numbers filled in.
Nothing in a headline is free text from a model: the figures are the
simulation's and the words are the template's, so the wire can be audited
line by line against the event log.

The forecast across all paths is numeric (expected headlines by type per
quarter, the pressure index, the probability of a hearing) and comes from
the engine's per path counts; the wire is one draw of what that forecast
looks like in print.

Outlets
  WIRE     financial newswire: markets, earnings, licences, fines
  TECH     technology desk: releases, capability, research, open weights
  CIVIC    public interest desk: incidents, harm, trust, enforcement
  CAPITOL  political desk: policy milestones, hearings, relocation, controls
"""

import numpy as np

OUTLETS = {
    "WIRE": {"beat": {"market_move": 0.6, "enforcement": 0.9, "licence_delay": 0.8, "incident": 0.6, "catastrophe": 1.0,
                      "relocation": 0.7, "release": 0.5, "policy_start": 0.7, "policy_sunset": 0.6, "moratorium_end": 0.7},
             "tone": 0.0, "budget": 2},
    "TECH": {"beat": {"release": 1.0, "safety_milestone": 0.9, "licence_delay": 0.8, "moratorium_end": 0.9, "incident": 0.5,
                      "catastrophe": 0.9, "relocation": 0.6, "policy_start": 0.6, "labour": 0.5},
             "tone": 0.15, "budget": 2},
    "CIVIC": {"beat": {"incident": 1.0, "catastrophe": 1.0, "trust_fall": 1.0, "enforcement": 0.8, "hearing": 0.7,
                       "labour": 0.8, "safety_milestone": 0.4, "policy_start": 0.5},
              "tone": -0.2, "budget": 2},
    "CAPITOL": {"beat": {"policy_start": 1.0, "policy_sunset": 1.0, "hearing": 1.0, "relocation": 1.0, "enforcement": 0.7,
                         "catastrophe": 0.9, "incident": 0.4, "moratorium_end": 0.8, "trust_fall": 0.6},
                "tone": -0.05, "budget": 1},
}

CAT_WORDS = {
    "misuse": ["fraud campaign", "synthetic identity ring", "automated phishing wave", "disinformation operation",
               "voice cloning scam", "credential harvesting attack", "market manipulation scheme"],
    "accident": ["autonomous system failure", "mis specified trading agent", "medical triage error", "grid control fault",
                 "runaway recommendation loop", "logistics routing collapse", "flawed credit decisions"],
    "systemic": ["correlated model outage", "liquidity cascade", "information ecosystem shock", "shared model failure across venues",
                 "payment system disruption", "sector wide hallucination event"],
}

TEMPLATES = {
    "incident": {
        "minor": ["{firm} model linked to {what}; losses put at ${harm}", "{what} traced to {firm} system, regulator told; ${harm} in losses",
                  "{firm} confirms {what}, estimates ${harm} in damages", "Users report {what} on {firm} services; ${harm} at stake"],
        "major": ["{what} tied to {firm} causes ${harm} in losses", "MAJOR: {firm} system behind {what}; damages reach ${harm}",
                  "{firm} faces ${harm} fallout after {what}", "Regulators open inquiry into {firm} after ${harm} {what}"],
    },
    "catastrophe": ["CATASTROPHIC FAILURE: {firm} system triggers ${harm} crisis", "Markets reel as {firm} model failure spreads; ${harm} lost",
                    "{firm} at centre of ${harm} systemic event; emergency measures invoked"],
    "enforcement": ["{firm} fined ${fine} for breaching {pol} obligations", "Regulator sanctions {firm}: ${fine} penalty under {pol}",
                    "{firm} found non compliant; ${fine} fine imposed"],
    "relocation": ["{firm} moves {share} of development offshore, citing {pol}", "{firm} shifts {share} of AI work abroad as {pol} bites",
                   "Jurisdiction loses {share} of {firm} activity to lighter regimes"],
    "release": ["{firm} releases model at capability {cap}", "{firm} crosses capability {cap} with new release",
                "New {firm} system reaches capability {cap}; rivals under pressure"],
    "licence_delay": ["{firm} release held {months} months pending approval under {pol}", "{pol}: {firm} waits {months} months for clearance",
                      "{firm} delays launch by {months} months to satisfy {pol}"],
    "safety_milestone": ["{firm} safety practice rated strong after sustained investment", "{firm} safety programme reaches top tier",
                         "Analysts: {firm} now leads sector on safety practice"],
    "policy_start": ["{pol} takes effect; obligations begin today", "{pol} comes into force across the sector",
                     "Day one of {pol}: firms report compliance programmes under way"],
    "policy_start_mora": ["{pol}: releases above the threshold frozen from today", "Moratorium begins under {pol}; frontier releases paused"],
    "moratorium_end": ["Moratorium lifts: frontier releases resume under {pol}", "Pause over: regulator clears releases to resume"],
    "policy_sunset": ["{pol} lapses as sunset clause takes effect", "{pol} expires; sector returns to prior regime"],
    "market_move": {"up": ["{firm} shares jump {ret} on the month", "{firm} rallies {ret} as investors re rate growth"],
                    "down": ["{firm} shares fall {ret} on the month", "{firm} slides {ret} as investors weigh regulatory costs"]},
    "trust_fall": ["Public trust in AI services falls to {trust}; adoption slows", "Survey: trust in AI at {trust} after string of incidents"],
    "hearing": ["Lawmakers call emergency hearing on AI safety as pressure mounts", "Committee summons AI executives after month of incidents",
                "Government signals tougher line after public outcry"],
    "labour": ["AI service index up {pct} since start; unions seek adjustment support", "Automation milestone: AI services index at {q}x; retraining demand rises"],
}


def _money(x):
    if x >= 1000:
        return f"{x / 1000:.1f}tn"
    if x >= 10:
        return f"{x:.0f}bn"
    if x >= 1:
        return f"{x:.1f}bn"
    return f"{x * 1000:.0f}m"


def _newsworthiness(ev):
    t = ev["type"]
    if t == "catastrophe":
        return 3.0
    if t == "incident":
        return 0.4 + 0.6 * np.log10(1 + ev["harm"] / 0.05) + (0.6 if ev["major"] else 0.0)
    if t == "enforcement":
        return 0.7 + 0.3 * np.log10(1 + ev["fine"] / 0.05)
    if t == "relocation":
        return 0.8 + ev["share"]
    if t == "market_move":
        return 0.5 + 3 * abs(ev["ret"])
    return {"release": 0.6, "licence_delay": 0.7, "safety_milestone": 0.5, "policy_start": 1.2, "policy_sunset": 1.0,
            "moratorium_end": 1.0, "trust_fall": 1.1, "hearing": 1.4, "labour": 0.7}.get(t, 0.5)


def _tone(ev):
    t = ev["type"]
    return {"catastrophe": -1.0, "incident": -0.7 if ev.get("major") else -0.45, "enforcement": -0.35, "relocation": -0.4,
            "release": 0.5, "licence_delay": -0.2, "safety_milestone": 0.6, "policy_start": -0.05, "policy_sunset": 0.05,
            "moratorium_end": 0.3, "market_move": 0.5 if ev.get("ret", 0) > 0 else -0.5, "trust_fall": -0.6,
            "hearing": -0.5, "labour": -0.2}.get(t, 0.0)


def _fill(template, ev, labels, pol_label, rng):
    f = labels[ev["firm"]] if "firm" in ev else ""
    d = {"firm": f, "pol": pol_label,
         "harm": _money(ev.get("harm", 0.0)), "fine": _money(ev.get("fine", 0.0)),
         "share": f"{ev.get('share', 0) * 100:.0f}%", "cap": f"{ev.get('capability', 0):.2f}",
         "months": str(ev.get("months", 0)), "ret": f"{abs(ev.get('ret', 0)) * 100:.0f}%",
         "trust": f"{ev.get('trust', 0) * 100:.0f}%", "q": f"{ev.get('service', 1):.1f}",
         "pct": f"{(ev.get('service', 1) - 1) * 100:.0f}%",
         "what": rng.choice(CAT_WORDS.get(ev.get("cat", "misuse"), ["incident"])) if "cat" in ev else "incident"}
    out = template.format(**d)
    return out[:1].upper() + out[1:]


def _template_for(ev, rng):
    t = ev["type"]
    if t == "incident":
        return rng.choice(TEMPLATES["incident"]["major" if ev["major"] else "minor"])
    if t == "market_move":
        return rng.choice(TEMPLATES["market_move"]["up" if ev["ret"] > 0 else "down"])
    if t == "policy_start" and ev.get("mora"):
        return rng.choice(TEMPLATES["policy_start_mora"])
    return rng.choice(TEMPLATES.get(t, ["{firm} in the news"]))


class WireComposer:
    """Composes the wire month by month, keeping the outlets' memory of what they have already run."""

    def __init__(self, labels, pol_label, start_year=2027, start_month=1, seed=3):
        self.labels, self.pol_label = labels, pol_label
        self.start_year, self.start_month = start_year, start_month
        self.rng = np.random.default_rng(seed)
        self.seen = {}

    def date(self, t):
        y, m = divmod(self.start_month - 1 + t, 12)
        return f"{self.start_year + y}-{m + 1:02d}"

    def month(self, t, events):
        out, used = [], set()
        date = self.date(t)
        for outlet, spec in OUTLETS.items():
            scored = []
            for i, ev in enumerate(events):
                w = spec["beat"].get(ev["type"], 0.0)
                if w <= 0 or i in used:
                    continue
                key = (ev["type"], ev.get("firm"))
                novelty = 1.0 / (1.0 + 0.5 * self.seen.get(key, 0))
                scored.append((w * _newsworthiness(ev) * novelty, i))
            scored.sort(reverse=True)
            for score, i in scored[:spec["budget"]]:
                ev = events[i]
                used.add(i)
                key = (ev["type"], ev.get("firm"))
                self.seen[key] = self.seen.get(key, 0) + 1
                head = _fill(_template_for(ev, self.rng), ev, self.labels, self.pol_label, self.rng)
                tone = float(np.clip(_tone(ev) + spec["tone"] * 0.3, -1, 1))
                out.append({"t": t, "date": date, "outlet": outlet, "headline": head, "tone": tone,
                            "salience": float(min(1.0, score / 3.0)), "type": ev["type"],
                            "firm": self.labels[ev["firm"]] if "firm" in ev else None})
        return out


def compose_wire(events_by_month, labels, pol_label, start_year=2027, start_month=1, seed=3):
    """The whole wire for a representative path: list of headline dicts."""
    wc = WireComposer(labels, pol_label, start_year, start_month, seed)
    wire = []
    for t, events in enumerate(events_by_month):
        wire.extend(wc.month(t, events))
    return wire


def wire_summary(wire):
    n = len(wire)
    if not n:
        return {"headlines": 0}
    tones = np.array([w["tone"] for w in wire])
    by_type = {}
    for w in wire:
        by_type[w["type"]] = by_type.get(w["type"], 0) + 1
    by_outlet = {}
    for w in wire:
        by_outlet[w["outlet"]] = by_outlet.get(w["outlet"], 0) + 1
    return {"headlines": n, "share_negative": float((tones < -0.2).mean()), "mean_tone": float(tones.mean()),
            "by_type": by_type, "by_outlet": by_outlet,
            "worst": sorted(wire, key=lambda w: w["tone"])[:3]}
