"""A register of regulated persons for the gates.

In the UK, accountability attaches to named individuals: senior managers
approved by the FCA or PRA hold a controlled function, and certified staff
are attested fit and proper by their firm. An authority running the Lab keeps
a register of who may approve at its gates, drawn from its own HR or
governance system, or from the FCA Financial Services Register and the
Directory of certified persons. This module ties the approver to that
register: at each gate the approver's name (or individual reference
number) is looked up, the record must be active and hold an approving
function, and the match (reference number, function, firm, source, time of
the check) is written onto the gate entry, into the approvals file, the
briefing signatures and the transparency record. When a register is
configured and required, an approver not on it cannot approve.

Register file (`PSL_REGISTER`, CSV or JSON): one row per person with
  name, irn, firm, function, status, valid_from, valid_to, source
where status is active or inactive, function is an SMF or certified
function such as SMF24 or CF, and source names where the record came from
(for example "FCA Financial Services Register, checked 2026-09-01").

Optional live lookup: the FCA Register API (register.fca.org.uk) can
refresh a record by IRN when `PSL_CONNECTORS=on`, the host is on the
egress allowlist, and `PSL_FCA_REGISTER_EMAIL` and `PSL_KEY_FCA_REGISTER`
are set. The lookup is a refresh of the authority's own register, never a
substitute for it.
"""

import csv
import datetime
import io
import json
import os
import urllib.parse
import urllib.request

APPROVING_FUNCTIONS_DEFAULT = ("SMF", "CF", "SIF", "PRA SMF", "certified")
DEV_IDENTITIES = ("developer1", "developer2")


def dev_mode_on():
    return os.environ.get("PSL_DEV_MODE", "").strip().lower() in ("on", "1", "true", "yes")


def is_dev_identity(name):
    return _norm(name).replace(" ", "") in DEV_IDENTITIES
FCA_API = "https://register.fca.org.uk/services/V0.1"


def _now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


def _norm(s):
    return " ".join(str(s or "").strip().lower().replace(".", " ").split())


def load_register(path):
    """Rows from a CSV or JSON register file; [] when absent."""
    if not path or not os.path.isfile(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    rows = []
    if path.lower().endswith(".json"):
        data = json.loads(text)
        rows = data if isinstance(data, list) else data.get("persons", [])
    else:
        for r in csv.DictReader(io.StringIO(text)):
            rows.append(r)
    out = []
    for r in rows:
        out.append({"name": str(r.get("name", "")).strip(), "irn": str(r.get("irn", "")).strip(),
                    "firm": str(r.get("firm", "")).strip(), "function": str(r.get("function", "")).strip(),
                    "status": str(r.get("status", "active")).strip().lower() or "active",
                    "valid_from": str(r.get("valid_from", "")).strip(), "valid_to": str(r.get("valid_to", "")).strip(),
                    "source": str(r.get("source", "")).strip()})
    return out


class PersonRegister:
    def __init__(self, path=None, required=None, approving=APPROVING_FUNCTIONS_DEFAULT):
        self.path = path or os.environ.get("PSL_REGISTER", "")
        self.rows = load_register(self.path)
        flag = os.environ.get("PSL_REGISTER_REQUIRED", "").strip().lower()
        self.required = (flag in ("on", "1", "true", "yes")) if flag else (required if required is not None else bool(self.rows))
        self.approving = tuple(approving)

    @property
    def configured(self):
        return bool(self.rows)

    def lookup(self, name_or_irn):
        key = _norm(name_or_irn)
        if not key:
            return None
        for r in self.rows:
            if key == _norm(r["irn"]) and r["irn"]:
                return r
        # name match: exact normalised, or initial plus surname ("R. Ahmed" against "Rajib Ahmed")
        for r in self.rows:
            if key == _norm(r["name"]):
                return r
        parts = key.split()
        if len(parts) >= 2 and len(parts[0]) == 1:
            for r in self.rows:
                rp = _norm(r["name"]).split()
                if len(rp) >= 2 and rp[0][0] == parts[0] and rp[-1] == parts[-1]:
                    return r
        return None

    def _in_date(self, r):
        today = datetime.date.today().isoformat()
        if r.get("valid_from") and r["valid_from"] > today:
            return False
        if r.get("valid_to") and r["valid_to"] < today:
            return False
        return True

    def check(self, actor, role=None):
        """Verdict for an approver. Returns {ok, reason, match} where match
        carries what is recorded on the gate entry."""
        if dev_mode_on() and is_dev_identity(actor):
            # development identities: accepted without a register entry, and
            # every gate entry says so; never a regulated person
            return {"ok": True, "reason": "", "match": {"name": str(actor).strip(), "irn": "DEV", "firm": "development",
                                                        "function": (role or str(actor)).strip()[:80] or str(actor).strip(),
                                                        "source": "dev mode (PSL_DEV_MODE=on); not a regulated person",
                                                        "checked_at": _now(), "note": "dev mode", "dev_mode": True}}
        if not self.configured:
            return {"ok": not self.required, "reason": "no register configured" if not self.required
                    else "a register of regulated persons is required and none is configured", "match": None}
        r = self.lookup(actor)
        if r is None:
            return {"ok": False, "reason": f"{actor} is not on the register of regulated persons", "match": None}
        if r["status"] != "active":
            return {"ok": False, "reason": f"{r['name']} is on the register but not active", "match": None}
        if not self._in_date(r):
            return {"ok": False, "reason": f"{r['name']}'s function is outside its validity dates", "match": None}
        fn = r["function"].upper()
        if not any(fn.startswith(a.upper()) for a in self.approving):
            return {"ok": False, "reason": f"{r['name']} holds {r['function']}, not an approving function", "match": None}
        if role and _norm(role) and _norm(role) not in _norm(r["function"]) and _norm(r["function"]) not in _norm(role):
            note = f"declared function {role} differs from the register's {r['function']}; the register's is recorded"
        else:
            note = ""
        match = {"name": r["name"], "irn": r["irn"], "firm": r["firm"], "function": r["function"],
                 "source": r["source"], "checked_at": _now(), "note": note}
        return {"ok": True, "reason": "", "match": match}


def fca_lookup(irn, email=None, key=None, allowlist=None, timeout=20):
    """Refresh one record from the FCA Register API by individual reference
    number. Requires the connector switch, the host on the allowlist and the
    API credentials; returns a register row or raises."""
    from .llm import _check_endpoint
    email = email or os.environ.get("PSL_FCA_REGISTER_EMAIL", "")
    key = key or os.environ.get("PSL_KEY_FCA_REGISTER", "")
    if os.environ.get("PSL_CONNECTORS", "off").lower() not in ("on", "1", "true", "yes"):
        raise RuntimeError("connectors are off; the register refresh is an outbound call")
    if not (email and key):
        raise RuntimeError("PSL_FCA_REGISTER_EMAIL and PSL_KEY_FCA_REGISTER are required")
    url = f"{FCA_API}/Individuals/{urllib.parse.quote(irn)}"
    _check_endpoint(url, allowlist or [h.strip() for h in os.environ.get("PSL_EGRESS_ALLOWLIST", "").split(",") if h.strip()])
    req = urllib.request.Request(url, headers={"X-Auth-Email": email, "X-Auth-Key": key, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:   # noqa: S310 - https and allowlist checked
        data = json.loads(r.read(2 * 1024 * 1024))
    items = data.get("Data") or []
    if not items:
        raise RuntimeError(f"no individual with reference {irn}")
    d = items[0].get("Details") or items[0]
    return {"name": d.get("Full Name") or d.get("Name") or "", "irn": irn,
            "firm": d.get("Current roles & activities") or "", "function": d.get("Function") or "",
            "status": "active" if str(d.get("Status", "")).lower().startswith("active") else "inactive",
            "valid_from": "", "valid_to": "", "source": f"FCA Financial Services Register, checked {_now()[:10]}"}


def main(argv=None):
    """python -m psl.register check <name or IRN> [--register path]
       python -m psl.register refresh <IRN>   (FCA Register API, connectors on)"""
    import argparse
    import sys
    ap = argparse.ArgumentParser(prog="python -m psl.register")
    ap.add_argument("command", choices=["check", "refresh"])
    ap.add_argument("who")
    ap.add_argument("--register", default=os.environ.get("PSL_REGISTER") or None)
    ap.add_argument("--role", default=None)
    args = ap.parse_args(argv)
    if args.command == "check":
        print(json.dumps(PersonRegister(args.register).check(args.who, args.role), indent=1))
        return 0
    try:
        print(json.dumps(fca_lookup(args.who), indent=1))
        return 0
    except Exception as e:  # noqa: BLE001
        print(json.dumps({"ok": False, "error": str(e)}, indent=1))
        sys.exit(1)


if __name__ == "__main__":
    main()
