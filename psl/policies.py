"""The policy instrument library.

A policy is a small JSON document of bounded parameters, the same language
for the built in instruments, for packages that combine them and for an
instrument an authority writes itself in the POL page. Every value is
validated against hard bounds and any clamping is reported, so nothing is
changed silently; the document's hash enters the battery hash approved at
Gate 1 and the ledger.

    {"name": "frontier_licensing", "label": "Frontier licensing",
     "note": "a licence to train or deploy above the capability threshold",
     "scope": "home",                # home: obligations bind on domestic activity only;
                                     # coordinated: they follow the firm wherever it operates
     "phase_in": 6,                  # months before obligations bite
     "sunset": 0,                    # months after which the policy lapses (0 = never)
     "capability_threshold": 1.0,    # obligations apply above this capability index (0 = every model)
     "applies_to": ["frontier_lab", "open_weights", "hyperscaler"],   # sectors in scope ("all" = every firm)
     "fixed_cost": 0.15,             # $bn a year per firm in scope (conformity, audits, licence fees)
     "variable_cost": 0.02,          # share of in scope revenue spent on compliance
     "min_safety_share": 0.18,       # mandated minimum share of R&D spent on safety
     "eval_catch": 0.5,              # share of unsafe releases caught by pre deployment evaluation
     "release_delay": 4,             # months of approval delay between a capability gain and its deployment
     "moratorium_months": 0,         # months during which releases above the threshold are frozen
     "liability_multiplier": 0.0,    # share of the monetised harm an incident's firm must pay
     "safe_harbour": false,          # compliant firms are shielded from most liability
     "insurance_mandate": false,     # liability must be insured (adds a premium, smooths payouts)
     "incident_reporting": true,     # mandatory incident reports: the regulator learns faster, the press sees more
     "transparency": 0.0,            # model documentation and provenance: reduces the misuse environment (0 to 0.3)
     "enforcement_capacity": 0.7,    # the regulator's capacity to audit and fine (0 to 1)
     "fine_rate": 0.08,              # fine as a share of annual revenue for a firm found non compliant
     "open_weights_restriction": false,   # weights above the threshold may not be published
     "export_controls": 0.0,         # strength of compute export controls (0 to 1)
     "sandbox_small_firms": false,   # small firms get a lighter regime (fixed cost waived)
     "tier_friction": 0.0}           # risk tiering friction on deployment growth (0 to 0.3)

Only `name` is required; every other key has the baseline's default
(no obligation). Names are lower case letters, digits and underscores.
"""

import datetime
import hashlib
import json
import os
import re

SECTORS = ("frontier_lab", "open_weights", "hyperscaler", "chips", "enterprise_software",
           "consumer_ai", "autonomy", "startups")

BOUNDS = {
    "phase_in": (0, 36), "sunset": (0, 120), "capability_threshold": (0.0, 3.0),
    "fixed_cost": (0.0, 2.0), "variable_cost": (0.0, 0.10), "min_safety_share": (0.0, 0.5),
    "eval_catch": (0.0, 0.9), "release_delay": (0, 12), "moratorium_months": (0, 24),
    "liability_multiplier": (0.0, 1.5), "transparency": (0.0, 0.3), "enforcement_capacity": (0.0, 1.0),
    "fine_rate": (0.0, 0.2), "export_controls": (0.0, 1.0), "tier_friction": (0.0, 0.3),
}
FLAGS = ("safe_harbour", "insurance_mandate", "incident_reporting", "open_weights_restriction", "sandbox_small_firms")
SCOPES = ("home", "coordinated")
_NAME = re.compile(r"^[a-z][a-z0-9_]{2,39}$")
MAX_POLICIES = 24

DEFAULTS = {
    "label": "", "note": "", "scope": "home", "phase_in": 0, "sunset": 0, "capability_threshold": 0.0,
    "applies_to": "all", "fixed_cost": 0.0, "variable_cost": 0.0, "min_safety_share": 0.0, "eval_catch": 0.0,
    "release_delay": 0, "moratorium_months": 0, "liability_multiplier": 0.0, "safe_harbour": False,
    "insurance_mandate": False, "incident_reporting": False, "transparency": 0.0, "enforcement_capacity": 0.1,
    "fine_rate": 0.0, "open_weights_restriction": False, "export_controls": 0.0, "sandbox_small_firms": False,
    "tier_friction": 0.0,
}

# ----------------------------------------------------------------- library --
LIBRARY = {
    "baseline": dict(
        label="Status quo (voluntary commitments)",
        note="No new obligation. Existing consumer and product law only, with the regulator's present capacity. "
             "Every other policy is measured against this path, pair by pair.",
        enforcement_capacity=0.1),
    "transparency_disclosure": dict(
        label="Transparency and disclosure",
        note="Model documentation, provenance marking and public incident disclosure. Cheap, and it shrinks the "
             "misuse environment rather than the capability.",
        fixed_cost=0.01, variable_cost=0.002, transparency=0.15, incident_reporting=True, enforcement_capacity=0.3,
        fine_rate=0.01),
    "compute_threshold_reporting": dict(
        label="Compute threshold reporting",
        note="Developers above a training compute threshold report their models and their own evaluations. "
             "The regime an executive order can create.",
        capability_threshold=1.0, applies_to=["frontier_lab", "open_weights", "hyperscaler"],
        fixed_cost=0.03, variable_cost=0.005, eval_catch=0.15, incident_reporting=True, enforcement_capacity=0.4,
        fine_rate=0.02, phase_in=3),
    "mandatory_third_party_evals": dict(
        label="Mandatory third party evaluation",
        note="Independent pre deployment evaluation above a threshold, with a short approval delay. Catches a "
             "share of unsafe releases before they ship.",
        capability_threshold=0.8, applies_to=["frontier_lab", "open_weights", "hyperscaler", "consumer_ai", "autonomy"],
        fixed_cost=0.08, variable_cost=0.01, eval_catch=0.45, release_delay=2, min_safety_share=0.08,
        incident_reporting=True, enforcement_capacity=0.5, fine_rate=0.06, phase_in=6),
    "risk_tiering": dict(
        label="Risk tiering (EU style)",
        note="Obligations by use case tier for every deployer, conformity assessment before high risk deployment, "
             "a sandbox for small firms. Compliance cost scales with deployment, not with the frontier.",
        applies_to="all", fixed_cost=0.05, variable_cost=0.03, tier_friction=0.15, release_delay=1,
        min_safety_share=0.05, incident_reporting=True, transparency=0.1, sandbox_small_firms=True,
        enforcement_capacity=0.6, fine_rate=0.07, phase_in=12),
    "frontier_licensing": dict(
        label="Frontier licensing",
        note="A licence to train or deploy above the capability threshold: mandated safety spend, independent "
             "evaluation, an approval delay, audits with real fines. Domestic scope: a mobile lab can leave.",
        capability_threshold=1.0, applies_to=["frontier_lab", "open_weights", "hyperscaler"],
        fixed_cost=0.15, variable_cost=0.02, min_safety_share=0.25, eval_catch=0.6, release_delay=4,
        incident_reporting=True, enforcement_capacity=0.7, fine_rate=0.1, phase_in=6),
    "coordinated_licensing": dict(
        label="Coordinated frontier licensing",
        note="The licensing regime agreed across jurisdictions, so obligations follow the firm wherever it operates. "
             "Slower to arrive, harder to escape.",
        scope="coordinated", capability_threshold=1.0, applies_to=["frontier_lab", "open_weights", "hyperscaler"],
        fixed_cost=0.15, variable_cost=0.02, min_safety_share=0.25, eval_catch=0.6, release_delay=4,
        incident_reporting=True, enforcement_capacity=0.7, fine_rate=0.1, phase_in=12),
    "strict_liability": dict(
        label="Strict liability",
        note="Firms pay for the harm their systems cause, insured by mandate. No ex ante obligation: the price "
             "of an incident does the work, and the firms choose their own safety spend.",
        applies_to="all", liability_multiplier=0.8, insurance_mandate=True, fixed_cost=0.02, variable_cost=0.005,
        incident_reporting=True, enforcement_capacity=0.3, phase_in=6),
    "liability_with_safe_harbour": dict(
        label="Liability with a safe harbour",
        note="Strict liability, but a firm that meets the evaluation and safety spend standard is shielded from "
             "most of it. Compliance becomes the cheaper choice.",
        applies_to="all", liability_multiplier=0.8, safe_harbour=True, min_safety_share=0.12, eval_catch=0.35,
        fixed_cost=0.08, variable_cost=0.012, insurance_mandate=True, incident_reporting=True,
        enforcement_capacity=0.4, fine_rate=0.03, phase_in=6),
    "moratorium": dict(
        label="Six month moratorium above the threshold",
        note="Releases above the capability threshold are frozen for six months, then reporting applies. "
             "The sharpest brake and the one most easily left behind.",
        capability_threshold=1.1, applies_to=["frontier_lab", "open_weights", "hyperscaler"],
        moratorium_months=6, fixed_cost=0.03, eval_catch=0.15, incident_reporting=True,
        enforcement_capacity=0.5, fine_rate=0.05, phase_in=1),
    "export_controls": dict(
        label="Compute export controls",
        note="Controls on advanced compute leaving the jurisdiction: offshore development loses its compute, the "
             "chip sector loses a market. Paired with reporting at home.",
        export_controls=0.7, capability_threshold=1.0, applies_to=["frontier_lab", "open_weights", "hyperscaler", "chips"],
        fixed_cost=0.02, incident_reporting=True, enforcement_capacity=0.4, fine_rate=0.03),
    "open_weights_restriction": dict(
        label="Open weights restriction",
        note="Weights above the threshold may not be published. The open developer's model changes, the misuse "
             "environment shrinks, diffusion slows.",
        open_weights_restriction=True, capability_threshold=0.9, applies_to=["open_weights"],
        transparency=0.1, fixed_cost=0.02, incident_reporting=True, enforcement_capacity=0.4, fine_rate=0.04),
    "sandbox_light_touch": dict(
        label="Sandbox and light touch",
        note="A regulatory sandbox, voluntary standards, reporting and provenance marking. The pro innovation "
             "option.",
        applies_to="all", sandbox_small_firms=True, incident_reporting=True, transparency=0.1,
        variable_cost=0.004, enforcement_capacity=0.3, fine_rate=0.01),
    "eu_style_package": dict(
        label="EU style package",
        note="Risk tiering with mandatory third party evaluation above the threshold, incident reporting, "
             "provenance marking and a sandbox.",
        applies_to="all", fixed_cost=0.10, variable_cost=0.03, tier_friction=0.15, release_delay=2,
        capability_threshold=0.0, min_safety_share=0.10, eval_catch=0.45, incident_reporting=True,
        transparency=0.15, sandbox_small_firms=True, enforcement_capacity=0.65, fine_rate=0.07, phase_in=12),
    "licensing_plus_liability": dict(
        label="Licensing plus liability",
        note="Frontier licensing with strict liability and a safe harbour for licensed firms: ex ante control at "
             "the frontier and an ex post price everywhere else.",
        capability_threshold=1.0, applies_to="all", fixed_cost=0.15, variable_cost=0.02, min_safety_share=0.25,
        eval_catch=0.6, release_delay=4, liability_multiplier=0.8, safe_harbour=True, insurance_mandate=True,
        incident_reporting=True, enforcement_capacity=0.7, fine_rate=0.1, phase_in=6),
}

DEFAULT_BATTERY = ["baseline", "transparency_disclosure", "compute_threshold_reporting",
                   "mandatory_third_party_evals", "risk_tiering", "frontier_licensing",
                   "strict_liability", "liability_with_safe_harbour", "moratorium"]

KEYWORDS = {
    "transparency_disclosure": ("transparen", "disclos", "watermark", "provenance"),
    "compute_threshold_reporting": ("reporting", "compute threshold", "executive order", "threshold reporting"),
    "mandatory_third_party_evals": ("eval", "third party", "audit", "red team"),
    "risk_tiering": ("tier", "eu ai act", "risk based", "high risk"),
    "frontier_licensing": ("licen",),
    "coordinated_licensing": ("coordinat", "international", "treaty", "harmonis"),
    "strict_liability": ("liabil", "tort", "insurance"),
    "liability_with_safe_harbour": ("safe harbour", "safe harbor"),
    "moratorium": ("moratorium", "pause", "freeze"),
    "export_controls": ("export control", "chip control", "compute control"),
    "open_weights_restriction": ("open weight", "open source", "weights"),
    "sandbox_light_touch": ("sandbox", "light touch", "pro innovation", "voluntary"),
    "eu_style_package": ("eu style", "european package", "eu package"),
    "licensing_plus_liability": ("licensing plus liability", "licensing and liability"),
}


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


def validate_policy(doc):
    """Validate and normalise a policy document. Returns (ok, policy, errors, notes)."""
    errors, notes = [], []
    if not isinstance(doc, dict):
        return False, None, ["a policy is a JSON object"], notes
    name = str(doc.get("name", "")).strip().lower()
    if not _NAME.match(name):
        errors.append("name must be 3 to 40 lower case letters, digits or underscores, starting with a letter")
    pol = dict(DEFAULTS)
    pol["name"] = name
    pol["label"] = str(doc.get("label", "") or name.replace("_", " ").capitalize())[:80]
    pol["note"] = str(doc.get("note", ""))[:400]
    scope = str(doc.get("scope", "home")).strip().lower()
    if scope not in SCOPES:
        errors.append("scope must be home or coordinated")
    pol["scope"] = scope
    ap = doc.get("applies_to", "all")
    if isinstance(ap, str):
        ap = ap.strip().lower()
        if ap != "all":
            ap = [ap]
    if isinstance(ap, list):
        bad = [s for s in ap if s not in SECTORS]
        if bad:
            errors.append(f"applies_to has unknown sectors {bad}; sectors are {list(SECTORS)}")
        ap = sorted(set(ap))
    pol["applies_to"] = ap
    for key, (lo, hi) in BOUNDS.items():
        if key in doc:
            v = _clamp(key, doc[key], lo, hi, notes)
            if v is not None:
                pol[key] = int(round(v)) if key in ("phase_in", "sunset", "release_delay", "moratorium_months") else v
    for key in FLAGS:
        if key in doc:
            pol[key] = bool(doc[key])
    if pol["sunset"] and pol["sunset"] <= pol["phase_in"]:
        errors.append("sunset must come after phase_in")
    if pol["safe_harbour"] and pol["liability_multiplier"] == 0:
        notes.append("safe_harbour has no effect without liability")
    if pol["moratorium_months"] and pol["capability_threshold"] == 0:
        notes.append("a moratorium at threshold 0 freezes every release")
    return (not errors), (pol if not errors else None), errors, notes


def policy_hash(pol):
    return hashlib.sha256(json.dumps(pol, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def library_policy(name):
    """A validated built in policy, or None."""
    if name not in LIBRARY:
        return None
    ok, pol, errors, _ = validate_policy(dict(LIBRARY[name], name=name))
    assert ok, (name, errors)
    return pol


def all_library():
    return [library_policy(n) for n in LIBRARY]


def template():
    return dict(DEFAULTS, name="my_instrument", label="My instrument",
                note="describe the obligation, whom it binds and what it is meant to change",
                applies_to=["frontier_lab", "open_weights"], capability_threshold=1.0, fixed_cost=0.05,
                variable_cost=0.01, min_safety_share=0.1, eval_catch=0.3, incident_reporting=True,
                enforcement_capacity=0.5, fine_rate=0.04, phase_in=6)


def in_scope(pol, sector):
    ap = pol["applies_to"]
    return ap == "all" or sector in ap


class PolicyStore:
    """Instruments the authority has defined, kept in `<runs_dir>/policies.json`
    with provenance. `enabled` instruments join every later plan."""

    def __init__(self, root):
        self.root = root
        self.path = os.path.join(root, "policies.json")

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
        ok, pol, errors, notes = validate_policy(doc)
        if not ok:
            return {"ok": False, "errors": errors, "notes": notes}
        if pol["name"] in LIBRARY:
            return {"ok": False, "errors": [f"{pol['name']} is a built in instrument; choose another name"], "notes": notes}
        items = [x for x in self._load() if x["policy"]["name"] != pol["name"]]
        if len(items) >= MAX_POLICIES:
            return {"ok": False, "errors": [f"at most {MAX_POLICIES} instruments; remove one first"], "notes": notes}
        rec = {"policy": pol, "sha256": policy_hash(pol), "author": (author or "")[:80],
               "added": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"), "enabled": True}
        items.append(rec)
        self._save(items)
        return {"ok": True, "record": rec, "notes": notes, "errors": []}

    def remove(self, name):
        items = self._load()
        keep = [x for x in items if x["policy"]["name"] != name]
        self._save(keep)
        return len(keep) < len(items)

    def set_enabled(self, name, enabled):
        items = self._load()
        for x in items:
            if x["policy"]["name"] == name:
                x["enabled"] = bool(enabled)
        self._save(items)

    def enabled(self):
        return [x["policy"] for x in self._load() if x.get("enabled", True)]


def describe(pol):
    """One line of what the instrument does, for tables and the briefing."""
    bits = []
    if pol["capability_threshold"] > 0:
        bits.append(f"above capability {pol['capability_threshold']:.1f}")
    if pol["min_safety_share"] > 0:
        bits.append(f"safety spend at least {pol['min_safety_share']:.0%} of R&D")
    if pol["eval_catch"] > 0:
        bits.append(f"evaluations catch {pol['eval_catch']:.0%} of unsafe releases")
    if pol["release_delay"] > 0:
        bits.append(f"{pol['release_delay']} month approval delay")
    if pol["moratorium_months"] > 0:
        bits.append(f"{pol['moratorium_months']} month moratorium")
    if pol["liability_multiplier"] > 0:
        bits.append(f"liability for {pol['liability_multiplier']:.0%} of harm" + (" with a safe harbour" if pol["safe_harbour"] else ""))
    if pol["transparency"] > 0:
        bits.append("provenance and disclosure")
    if pol["export_controls"] > 0:
        bits.append("compute export controls")
    if pol["open_weights_restriction"]:
        bits.append("no open weights above the threshold")
    if pol["tier_friction"] > 0:
        bits.append("risk tier conformity for deployers")
    if pol["fixed_cost"] or pol["variable_cost"]:
        bits.append(f"compliance ${pol['fixed_cost']:.2f}bn fixed plus {pol['variable_cost']:.1%} of revenue")
    bits.append(f"enforcement capacity {pol['enforcement_capacity']:.1f}" + (f", fines {pol['fine_rate']:.0%} of revenue" if pol["fine_rate"] else ""))
    bits.append("coordinated across jurisdictions" if pol["scope"] == "coordinated" else "domestic scope")
    return "; ".join(bits)
