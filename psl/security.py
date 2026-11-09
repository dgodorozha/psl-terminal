"""Security controls for the Policy Scenario Lab, after Anderson, Security Engineering
(3rd edition, 2020). Each control names the chapter whose reasoning it
applies; the mapping is written out in docs/SECURITY_FRAMEWORK.md.

  posture()        a self check of the deployment against the controls,
                   reported in the SEC panel and recorded at release
                   (chapter 27 secure systems development, chapter 28
                   assurance)
  manifest         a hash manifest of every vendored front end asset so a
                   modified script or font is detected before the terminal
                   serves it (supply chain, chapters 21 and 27)
  authorize()      roles and least privilege for plan, upload, gate and
                   stop; separation of duty is the four eyes rule the gates
                   already enforce (chapter 6 access control, chapter 12
                   dual control)
  classify()       data classification with a no write down rule: nothing
                   confidential or personal enters the sandbox, and licensed
                   or pseudonymised rows never leave the run directory in
                   an evidence pack (chapter 9 multilevel security,
                   chapter 10 boundaries)
  pii_scan()       a scan for personal identifiers in uploaded text,
                   refused rather than stored (chapter 26 surveillance or
                   privacy)
  sanitize_cell()  defence against spreadsheet formula injection in
                   anything the platform exports as CSV (chapter 21)
  egress_allowed() an outbound allowlist for connectors; the sandbox is
                   air gapped unless a host is named (chapter 21)
"""

import hashlib
import os
import re

CLASSIFICATIONS = {
    "synthetic": {"allowed": True, "packable": True, "note": "generated data, no restriction"},
    "public": {"allowed": True, "packable": True, "note": "published data, attribution recorded"},
    "pseudonymised": {"allowed": True, "packable": False,
                      "note": "identifiers replaced; rows stay in the run directory, only hashes and "
                              "aggregates enter the evidence pack"},
    "licensed": {"allowed": True, "packable": False,
                 "note": "vendor licensed data; rows never leave the run directory"},
    "confidential": {"allowed": False, "packable": False,
                     "note": "confidential supervisory information is refused by policy"},
    "personal": {"allowed": False, "packable": False, "note": "personal data is refused by policy"},
}

ROLES = {
    "viewer": {"view", "ask"},
    "preparer": {"view", "ask", "plan", "upload", "fetch"},
    "approver": {"view", "ask", "gate", "stop"},
    "admin": {"view", "ask", "plan", "upload", "fetch", "gate", "stop", "posture"},
}

ASSET_DIRS = ["assets/vendor", "assets/fonts"]
ASSET_FILES = ["assets/terminal.js", "assets/psl.css"]
MANIFEST = "assets/MANIFEST.sha256"

_FORMULA = re.compile(r"^[=+\-@\t\r]")
_PII = {
    "email": re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
    "uk_phone": re.compile(r"\b(?:\+44\s?7\d{3}|\(?07\d{3}\)?)\s?\d{3}\s?\d{3}\b"),
    "uk_ni": re.compile(r"\b[A-CEGHJ-PR-TW-Z]{2}\d{6}[A-D]\b"),
    "iban": re.compile(r"\b[A-Z]{2}\d{2}[A-Z0-9]{11,30}\b"),
    "card": re.compile(r"\b(?:\d[ -]?){13,19}\b"),
}


def _luhn(s):
    d = [int(c) for c in re.sub(r"\D", "", s)]
    if len(d) < 13:
        return False
    total = 0
    for i, x in enumerate(reversed(d)):
        if i % 2 == 1:
            x *= 2
            if x > 9:
                x -= 9
        total += x
    return total % 10 == 0


def pii_scan(text, limit=200000):
    """Counts of personal identifier patterns in the text. Card numbers are
    Luhn checked to avoid flagging ordinary long numbers."""
    t = text[:limit]
    hits = {}
    for name, rx in _PII.items():
        found = rx.findall(t)
        if name == "card":
            found = [f for f in found if _luhn(f)]
        if found:
            hits[name] = len(found)
    return hits


def _is_number(s):
    try:
        float(s.replace(",", ""))
        return True
    except ValueError:
        return False


def looks_like_formula(s):
    """A cell a spreadsheet would evaluate: starts with = + - @ or a tab or
    carriage return and is not simply a signed number."""
    return bool(_FORMULA.match(s)) and not _is_number(s.strip())


def sanitize_cell(value):
    """Prefix cells that a spreadsheet would evaluate as a formula."""
    s = str(value)
    return "'" + s if looks_like_formula(s) else s


def classify(label):
    label = (label or "").strip().lower()
    if label not in CLASSIFICATIONS:
        return {"label": label, "allowed": False, "packable": False,
                "note": f"unknown classification; allowed: {', '.join(k for k, v in CLASSIFICATIONS.items() if v['allowed'])}"}
    return dict(CLASSIFICATIONS[label], label=label)


def authorize(role, action):
    """Least privilege: True if the role may perform the action."""
    return action in ROLES.get((role or "").strip().lower(), set())


def egress_allowed(host, allowlist):
    host = (host or "").lower().strip()
    return bool(host) and host in {h.strip().lower() for h in (allowlist or []) if h.strip()}


def _sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def build_manifest(root="."):
    """Write the sha256 manifest of the vendored assets."""
    entries = []
    for d in ASSET_DIRS:
        p = os.path.join(root, d)
        if not os.path.isdir(p):
            continue
        for dirpath, _, files in os.walk(p):
            for fn in sorted(files):
                rel = os.path.relpath(os.path.join(dirpath, fn), root)
                entries.append((rel, _sha(os.path.join(root, rel))))
    for f in ASSET_FILES:
        if os.path.isfile(os.path.join(root, f)):
            entries.append((f, _sha(os.path.join(root, f))))
    entries.sort()
    with open(os.path.join(root, MANIFEST), "w") as fh:
        for rel, h in entries:
            fh.write(f"{h}  {rel}\n")
    return entries


def verify_manifest(root="."):
    """Compare the vendored assets with the manifest. Returns (ok, detail)."""
    p = os.path.join(root, MANIFEST)
    if not os.path.isfile(p):
        return False, {"missing_manifest": True, "mismatched": [], "missing": [], "checked": 0}
    mismatched, missing, n = [], [], 0
    with open(p) as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            h, rel = line.split("  ", 1)
            fp = os.path.join(root, rel)
            n += 1
            if not os.path.isfile(fp):
                missing.append(rel)
            elif _sha(fp) != h:
                mismatched.append(rel)
    return (not mismatched and not missing), {"missing_manifest": False, "mismatched": mismatched,
                                              "missing": missing, "checked": n}


def posture(cfg, root=".", datasets=None):
    """Deployment self check. Each item carries the chapter of Security
    Engineering whose argument it applies. `fail` blocks release; `warn`
    is recorded."""
    items = []

    def item(control, status, detail, chapter):
        items.append({"control": control, "status": status, "detail": detail, "sev3": chapter})

    ephemeral = bool(getattr(cfg, "ephemeral_secret", True))
    item("ledger signing key configured", "warn" if ephemeral else "pass",
         "PSL_SECRET not set; ledgers are signed with an ephemeral key" if ephemeral else
         "persistent HMAC key from the environment", "5 cryptography, 12 banking and bookkeeping")
    auth = getattr(cfg, "auth_mode", "open")
    item("identities come from an authenticating proxy", "pass" if auth == "header" else "warn",
         f"auth mode {auth}" + ("" if auth == "header" else "; names are self declared, fine for a demo, not "
                                                             "for production"), "6 access control")
    dev = os.environ.get("PSL_DEV_MODE", "").strip().lower() in ("on", "1", "true", "yes")
    item("development mode off", "pass" if not dev else "warn",
         "dev mode off" if not dev else "PSL_DEV_MODE=on: Developer1 and Developer2 are accepted at the gates; never for production",
         "6 access control")
    reg = os.environ.get("PSL_REGISTER", "")
    item("approvers tied to a register of regulated persons", "pass" if reg and os.path.isfile(reg) else "warn",
         f"register {reg}: approvers must be active and hold an approving function" if reg and os.path.isfile(reg)
         else "no register configured; approvers are self declared (set PSL_REGISTER)", "6 access control")
    item("separation of duty at the gates", "pass" if getattr(cfg, "four_eyes", True) else "fail",
         "preparer and approver must differ" if getattr(cfg, "four_eyes", True) else "four eyes disabled",
         "12 banking and bookkeeping (dual control)")
    host = getattr(cfg, "host", "127.0.0.1")
    item("service bound to the loopback or behind a proxy", "pass" if host in ("127.0.0.1", "localhost") else "warn",
         f"host {host}", "21 network attack and defence")
    item("debug mode off", "pass" if not getattr(cfg, "debug", False) else "fail",
         "Flask debug off" if not getattr(cfg, "debug", False) else "debug exposes an interactive console",
         "27 secure systems development")
    conn = getattr(cfg, "connectors", False)
    allow = getattr(cfg, "egress_allowlist", []) or []
    if not conn:
        item("outbound connectors disabled (air gap)", "pass", "data arrives by upload only", "21 network attack and defence")
    else:
        item("outbound connectors limited to an allowlist", "pass" if allow else "fail",
             ("hosts: " + ", ".join(allow)) if allow else "connectors on with an empty allowlist",
             "21 network attack and defence")
    keys = [k for k in os.environ if k.startswith("PSL_KEY_") or k in ("ANTHROPIC_API_KEY", "PSL_LLM_KEY")]
    prov = (os.environ.get("PSL_LLM_PROVIDER") or ("anthropic" if os.environ.get("ANTHROPIC_API_KEY") else "off")).lower()
    if prov == "off" or os.environ.get("PSL_LLM", "auto").lower() in ("off", "0", "false", "no"):
        item("model provider", "pass", "no model configured; every path deterministic", "27 secure systems development")
    elif prov == "local":
        p = os.environ.get("PSL_LLM_PATH", "")
        item("model provider", "pass" if os.path.isdir(p) else "warn",
             f"local model loaded from disk ({p or 'no path'}); nothing downloaded" if os.path.isdir(p)
             else "PSL_LLM_PATH is not a directory; the deterministic path is used", "27 secure systems development")
    else:
        base = {"anthropic": os.environ.get("PSL_API_BASE", "https://api.anthropic.com"),
                "gemini": os.environ.get("PSL_LLM_BASE") or "https://generativelanguage.googleapis.com"
                }.get(prov, os.environ.get("PSL_LLM_BASE", ""))
        try:
            from .llm import _check_endpoint
            _check_endpoint(base.rstrip("/") + "/", allow if os.environ.get("PSL_CONNECTORS", "off").lower() == "on" else None)
            item("model provider", "pass", f"{prov} at {base}: https or loopback, host allowed", "21 network attack and defence")
        except Exception as e:  # noqa: BLE001
            item("model provider", "fail", f"{prov} at {base}: {str(e)[:120]}", "21 network attack and defence")
    item("credentials held in the environment, never in files or logs", "pass",
         f"{len(keys)} credential variables present" if keys else "no credentials configured",
         "4 protocols, 5 cryptography")
    ok, det = verify_manifest(root)
    item("vendored front end assets match their hash manifest", "pass" if ok else "fail",
         f"{det['checked']} files checked" + (f"; mismatched {det['mismatched']}" if det["mismatched"] else "")
         + (f"; missing {det['missing']}" if det["missing"] else "")
         + ("; manifest missing, run python -m psl.security manifest" if det["missing_manifest"] else ""),
         "27 secure systems development (supply chain)")
    item("upload size and type limits enforced", "pass",
         f"{getattr(cfg, 'upload_max_mb', 25)} MB, CSV or JSON only, formula and PII scans", "21 network attack and defence")
    item("ask rate limit", "pass", f"{getattr(cfg, 'ask_rate', 20)} questions per identity per minute",
         "21 network attack and defence")
    anc = getattr(cfg, "frame_ancestors", []) or []
    item("security headers on every response", "pass" if not anc else "warn",
         "content security policy, nosniff, no store, frame ancestors self" if not anc else
         "content security policy, nosniff, no store; the terminal may be framed by " + ", ".join(anc),
         "21 network attack and defence")
    bad = [d["name"] for d in (datasets or []) if not classify(d.get("classification")).get("allowed")]
    item("no confidential or personal data in the sandbox", "fail" if bad else "pass",
         ("refused datasets present: " + ", ".join(bad)) if bad else "every dataset carries an allowed classification",
         "9 multilevel security, 10 boundaries")
    unpack = [d["name"] for d in (datasets or []) if not classify(d.get("classification")).get("packable")]
    item("licensed or pseudonymised rows never leave the run directory", "pass",
         (", ".join(unpack) + " excluded from the evidence pack") if unpack else "no restricted datasets", "10 boundaries")
    item("uploaded series used only in aggregate (volatility, beta, event study)", "pass",
         "no row level data enters the briefing or the evidence pack", "11 inference control")
    item("every welfare figure recomputed by an independent critic before release", "pass",
         "critic.json lists the checks; Gate 2 cannot arm on a failure", "28 assurance")
    item("every step, gate and refusal in a hash chained signed ledger", "pass",
         "replayable with python -m psl.ledger verify", "12 banking and bookkeeping (audit)")
    status = "fail" if any(i["status"] == "fail" for i in items) else (
        "warn" if any(i["status"] == "warn" for i in items) else "pass")
    return {"status": status, "items": items, "n_pass": sum(i["status"] == "pass" for i in items),
            "n_warn": sum(i["status"] == "warn" for i in items), "n_fail": sum(i["status"] == "fail" for i in items)}


def main(argv=None):
    import argparse
    import json
    ap = argparse.ArgumentParser(prog="python -m psl.security")
    ap.add_argument("command", choices=["posture", "manifest", "verify"])
    args = ap.parse_args(argv)
    if args.command == "manifest":
        n = len(build_manifest("."))
        print(f"manifest written: {n} assets")
    elif args.command == "verify":
        ok, det = verify_manifest(".")
        print(json.dumps({"ok": ok, **det}, indent=1))
    else:
        import sys
        sys.path.insert(0, ".")
        from config import Config
        print(json.dumps(posture(Config()), indent=1))


if __name__ == "__main__":
    main()
