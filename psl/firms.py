"""Firm archetypes: the synthetic technology companies the policies act on.

The default economy holds eight archetypes that between them cover the AI
value chain. None is a real company; the figures are round numbers chosen
to be the right order of magnitude for the sector, and the briefing says
so. An authority can replace them in the AGT page with its own templates
(for example a mapping onto the companies it supervises, calibrated from
price data uploaded through the data desk); every value is bounded and
clamping is reported.

    {"name": "frontier_lab_closed", "label": "Frontier Lab (closed weights)", "sector": "frontier_lab",
     "revenue": 15.0,        # $bn a year
     "margin": 0.15,         # operating margin before compliance, penalties and liability
     "growth": 0.45,         # organic revenue growth a year at the baseline
     "rd_share": 0.35,       # R&D as a share of revenue, split between capability and safety
     "capability": 1.2,      # capability index, 1.0 = the frontier at the start
     "safety": 0.5,          # safety practice level, 0 to 1
     "reach": 0.7,           # deployment reach, 0 to 1
     "scope_share": 0.9,     # share of revenue inside the regulated scope
     "mobility": 0.4,        # how easily activity moves offshore, 0 to 1
     "culture": 0.55,        # intrinsic weight on safety in the firm's own choices, 0 to 1
     "beta": 1.4,            # market beta
     "idio_vol": 0.12,       # monthly idiosyncratic volatility of the price
     "pe": 45,               # earnings multiple when profitable
     "ps": 8,                # revenue multiple floor
     "compute_dependence": 0.9,   # share of revenue growth tied to compute access
     "open_weights": false,
     "small": false}         # qualifies for a sandbox
"""

import datetime
import hashlib
import json
import os
import re

from .policies import SECTORS

BOUNDS = {
    "revenue": (0.5, 500.0), "margin": (-0.5, 0.6), "growth": (-0.2, 1.0), "rd_share": (0.02, 0.6),
    "capability": (0.1, 3.0), "safety": (0.05, 0.95), "reach": (0.05, 1.0), "scope_share": (0.0, 1.0),
    "mobility": (0.0, 1.0), "culture": (0.0, 1.0), "beta": (0.2, 2.5), "idio_vol": (0.02, 0.3),
    "pe": (5.0, 120.0), "ps": (1.0, 30.0), "compute_dependence": (0.0, 1.0),
}
FLAGS = ("open_weights", "small")
_NAME = re.compile(r"^[a-z][a-z0-9_]{2,39}$")
MAX_FIRMS = 16

DEFAULT_FIRMS = [
    dict(name="frontier_lab_closed", label="Frontier Lab (closed weights)", sector="frontier_lab", revenue=15.0,
         margin=0.15, growth=0.45, rd_share=0.35, capability=1.2, safety=0.5, reach=0.7, scope_share=0.9,
         mobility=0.4, culture=0.55, beta=1.4, idio_vol=0.10, pe=45, ps=8, compute_dependence=0.9),
    dict(name="frontier_lab_open", label="Frontier Lab (open weights)", sector="open_weights", revenue=4.0,
         margin=0.05, growth=0.5, rd_share=0.4, capability=1.05, safety=0.4, reach=0.6, scope_share=0.9,
         mobility=0.6, culture=0.45, beta=1.5, idio_vol=0.12, pe=60, ps=10, compute_dependence=0.9, open_weights=True),
    dict(name="hyperscaler", label="Hyperscaler cloud", sector="hyperscaler", revenue=120.0, margin=0.30, growth=0.18,
         rd_share=0.15, capability=1.1, safety=0.6, reach=0.9, scope_share=0.4, mobility=0.2, culture=0.6,
         beta=1.1, idio_vol=0.07, pe=28, ps=6, compute_dependence=1.0),
    dict(name="chip_designer", label="Chip designer", sector="chips", revenue=90.0, margin=0.45, growth=0.25,
         rd_share=0.2, capability=0.6, safety=0.7, reach=0.95, scope_share=0.15, mobility=0.3, culture=0.6,
         beta=1.6, idio_vol=0.08, pe=35, ps=8, compute_dependence=0.3),
    dict(name="enterprise_software", label="Enterprise software", sector="enterprise_software", revenue=60.0,
         margin=0.28, growth=0.14, rd_share=0.18, capability=0.8, safety=0.6, reach=0.85, scope_share=0.5,
         mobility=0.1, culture=0.6, beta=1.0, idio_vol=0.07, pe=30, ps=6, compute_dependence=0.5),
    dict(name="consumer_ai", label="Consumer AI platform", sector="consumer_ai", revenue=30.0, margin=0.20,
         growth=0.30, rd_share=0.22, capability=0.95, safety=0.45, reach=0.8, scope_share=0.7, mobility=0.3,
         culture=0.4, beta=1.3, idio_vol=0.09, pe=38, ps=7, compute_dependence=0.7),
    dict(name="autonomy_robotics", label="Autonomy and robotics", sector="autonomy", revenue=8.0, margin=0.08,
         growth=0.40, rd_share=0.3, capability=0.85, safety=0.5, reach=0.4, scope_share=0.8, mobility=0.3,
         culture=0.5, beta=1.5, idio_vol=0.11, pe=50, ps=9, compute_dependence=0.6),
    dict(name="startup_cohort", label="AI start up cohort", sector="startups", revenue=6.0, margin=-0.10,
         growth=0.60, rd_share=0.5, capability=0.7, safety=0.35, reach=0.3, scope_share=0.6, mobility=0.7,
         culture=0.35, beta=1.7, idio_vol=0.10, pe=60, ps=15, compute_dependence=0.8, small=True),
]

DEFAULTS = {"label": "", "sector": "frontier_lab", "revenue": 5.0, "margin": 0.1, "growth": 0.3, "rd_share": 0.3,
            "capability": 1.0, "safety": 0.5, "reach": 0.5, "scope_share": 0.8, "mobility": 0.4, "culture": 0.5,
            "beta": 1.3, "idio_vol": 0.12, "pe": 40.0, "ps": 8.0, "compute_dependence": 0.8,
            "open_weights": False, "small": False}


def _clamp(name, value, lo, hi, notes):
    try:
        v = float(value)
    except (TypeError, ValueError):
        notes.append(f"{name}: not a number, default used")
        return None
    c = min(hi, max(lo, v))
    if c != v:
        notes.append(f"{name}: {v} clamped to {c}")
    return c


def validate_firm(doc):
    errors, notes = [], []
    if not isinstance(doc, dict):
        return False, None, ["a firm is a JSON object"], notes
    name = str(doc.get("name", "")).strip().lower()
    if not _NAME.match(name):
        errors.append("name must be 3 to 40 lower case letters, digits or underscores, starting with a letter")
    firm = dict(DEFAULTS)
    firm["name"] = name
    firm["label"] = str(doc.get("label", "") or name.replace("_", " ").capitalize())[:60]
    sector = str(doc.get("sector", "frontier_lab")).strip().lower()
    if sector not in SECTORS:
        errors.append(f"sector must be one of {list(SECTORS)}")
    firm["sector"] = sector
    for key, (lo, hi) in BOUNDS.items():
        if key in doc:
            v = _clamp(key, doc[key], lo, hi, notes)
            if v is not None:
                firm[key] = v
    for key in FLAGS:
        if key in doc:
            firm[key] = bool(doc[key])
    if firm["sector"] == "open_weights":
        firm["open_weights"] = True
    return (not errors), (firm if not errors else None), errors, notes


def default_firms():
    out = []
    for d in DEFAULT_FIRMS:
        ok, f, errors, _ = validate_firm(d)
        assert ok, errors
        out.append(f)
    return out


def firm_hash(firm):
    return hashlib.sha256(json.dumps(firm, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def template():
    return dict(DEFAULTS, name="my_firm", label="My firm", sector="consumer_ai", revenue=12.0, margin=0.18,
                growth=0.3, capability=0.9, safety=0.5, reach=0.6)


class FirmStore:
    """Firm templates the authority has defined (`<runs_dir>/firms.json`). When any are
    enabled they replace the default economy in the next plan."""

    def __init__(self, root):
        self.root = root
        self.path = os.path.join(root, "firms.json")

    def _load(self):
        if not os.path.isfile(self.path):
            return []
        with open(self.path) as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []

    def _save(self, items):
        os.makedirs(self.root, exist_ok=True)
        tmp = self.path + ".tmp"
        with open(tmp, "w") as f:
            json.dump(items, f, indent=1)
        os.replace(tmp, self.path)

    def list(self):
        return self._load()

    def add(self, doc, author=""):
        ok, firm, errors, notes = validate_firm(doc)
        if not ok:
            return {"ok": False, "errors": errors, "notes": notes}
        items = [x for x in self._load() if x["firm"]["name"] != firm["name"]]
        if len(items) >= MAX_FIRMS:
            return {"ok": False, "errors": [f"at most {MAX_FIRMS} firms; remove one first"], "notes": notes}
        rec = {"firm": firm, "sha256": firm_hash(firm), "author": (author or "")[:80],
               "added": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"), "enabled": True}
        items.append(rec)
        self._save(items)
        return {"ok": True, "record": rec, "notes": notes, "errors": []}

    def remove(self, name):
        items = self._load()
        keep = [x for x in items if x["firm"]["name"] != name]
        self._save(keep)
        return len(keep) < len(items)

    def set_enabled(self, name, enabled):
        items = self._load()
        for x in items:
            if x["firm"]["name"] == name:
                x["enabled"] = bool(enabled)
        self._save(items)

    def enabled(self):
        return [x["firm"] for x in self._load() if x.get("enabled", True)]

    def economy(self):
        """The firms of the next plan: the enabled templates if there are at least two, else the defaults."""
        en = self.enabled()
        return (en, "custom") if len(en) >= 2 else (default_firms(), "default")
