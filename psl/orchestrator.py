"""Command line orchestration: the same workflow as the terminal, for a
batch run or a replay of an evidence pack.

    python -m psl.orchestrator --question "..." --approve-battery --approve-briefing \\
        --preparer "D. Godorozha" --preparer-role "certified function" \\
        --approver "R. Ahmed" --approver-role "SMF24" --register sample_data/register.csv --outdir runs/cli

    python -m psl.orchestrator --battery runs/<id>/battery.json --approve-battery --approve-briefing ... --outdir replay

Gates: nothing simulates before Gate 1 (battery approval) and nothing is
released before Gate 2 (briefing release). Both need a named approver who
differs from the preparer (four eyes) and, when a register is configured,
is on it in an approving function. Both functions are mandatory. In dev
mode (PSL_DEV_MODE=on) Developer1 and Developer2 are accepted and every
record says so.
"""

import argparse
import datetime
import json
import os
import sys

from . import __version__, provenance
from . import assumptions as AS
from .atrs import atrs_record, render_markdown
from .briefing import draft_briefing, to_html
from .critic import critic_check
from .evidence import build_pack
from .firms import default_firms
from .ledger import Ledger, plain
from .pipeline import make_battery, run_battery, SimulationStopped
from .question import parse, describe, DEFAULT_QUESTION
from .register import PersonRegister, dev_mode_on, is_dev_identity


def utc_now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


def new_run_id():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d-%H%M%S") + "-" + os.urandom(2).hex()


def gate(register, actor, role, preparer, four_eyes=True):
    """Verdict for an approval request. Returns (ok, reason, match)."""
    if not actor:
        return False, "a named approver is required", None
    if not role:
        return False, "the approver's function is required (an SMF or certified function" + (", or Developer2 in dev mode)" if dev_mode_on() else ")"), None
    if four_eyes and preparer and actor.strip().lower() == preparer.strip().lower():
        return False, "four eyes: the approver must differ from the preparer", None
    v = register.check(actor, role)
    return v["ok"], v["reason"], v["match"]


def run_pipeline(question, outdir, approve_battery=False, approve_briefing=False, preparer=None, preparer_role=None,
                 approver=None, approver_role=None, register_path=None, secret=None, budget=None, profile="full",
                 battery=None, assumptions=None, firms=None, four_eyes=True, quiet=False, organisation="", team=""):
    os.makedirs(outdir, exist_ok=True)
    run_id = os.path.basename(os.path.abspath(outdir))
    log = Ledger(os.path.join(outdir, "ledger.jsonl"), run_id, secret=secret, actor="orchestrator")
    say = (lambda *a: None) if quiet else (lambda *a: print(*a, flush=True))
    if preparer and is_dev_identity(preparer) and dev_mode_on() and not preparer_role:
        preparer_role = preparer.strip()
    if approver and is_dev_identity(approver) and dev_mode_on() and not approver_role:
        approver_role = approver.strip()
    if preparer and not preparer_role:
        raise SystemExit("[GATE] the preparer's function is required (--preparer-role), for example 'certified function'"
                         + (" or Developer1 in dev mode." if dev_mode_on() else "."))
    if approver and (approve_battery or approve_briefing) and not approver_role:
        raise SystemExit("[GATE] the approver's function is required (--approver-role), for example 'SMF24'"
                         + (" or Developer2 in dev mode." if dev_mode_on() else "."))
    register = PersonRegister(register_path or None)
    approvals = {"preparer": preparer or "", "preparer_role": preparer_role or ""}
    log("run_started", actor=preparer or "orchestrator", question=question, preparer=preparer, preparer_role=preparer_role,
        provenance=provenance(), register_configured=register.configured, dev_mode=dev_mode_on())

    # ---- plan
    if battery is None:
        plan = parse(question)
        bat = make_battery(plan, firms=firms, assumptions=assumptions, budget=budget, profile=profile)
        say(f"[PLAN] {describe(plan)}; {bat['paths']} paths, {bat['horizon']} months; battery {bat['hash'][:12]}")
    else:
        bat = battery
        say(f"[PLAN] replaying battery {bat['hash'][:12]}: {len(bat['policies'])} instruments, {bat['paths']} paths, {bat['horizon']} months")
    log("battery_planned", n_policies=len(bat["policies"]), battery_hash=bat["hash"], assumptions_hash=bat["assumptions_hash"],
        policies=[p["name"] for p in bat["policies"]], constraints=bat["constraints"], reading=bat.get("reading"))
    with open(os.path.join(outdir, "battery.json"), "w") as f:
        json.dump(plain(bat), f, indent=1)

    # ---- gate 1
    if not approve_battery:
        log("gate1_pending", battery_hash=bat["hash"])
        say("[GATE 1] battery planned and awaiting approval; rerun with --approve-battery")
        return None
    ok, why, match = gate(register, approver, approver_role, preparer, four_eyes)
    if not ok:
        log("gate1_refused", actor=approver or "unnamed", reason=why)
        raise SystemExit(f"[GATE 1] refused: {why}")
    approvals["gate1"] = {"decision": "approved", "actor": approver, "role": approver_role, "ts": utc_now(), "register": match,
                          "battery_hash": bat["hash"]}
    log("gate1_approved", actor=approver, role=approver_role, register=match, battery_hash=bat["hash"])
    say(f"[GATE 1] approved by {approver} ({approver_role})" + (f", on the register as {match['function']}" if match and not match.get("dev_mode") else
                                                               (" (dev mode)" if match and match.get("dev_mode") else "")))

    # ---- run
    def progress(step, phase, **kw):
        say(f"[{step.upper()}] {phase}")
    try:
        arte, _ = run_battery(bat, outdir, log=log, progress=progress)
    except SimulationStopped as e:
        log("run_stopped", reason=str(e))
        raise SystemExit(f"[STOP] {e}")
    ev = arte["results"]
    say(f"[RESULT] preferred {ev['preferred']} (best unconstrained {ev['best_unconstrained']}); decision gap {ev['decision_gap']['decision_gap']:.2f}; "
        f"winner stability {ev['winner_stability']:.0%}")

    # ---- critic and briefing
    md = draft_briefing(arte, approvals, run_id)
    critic = critic_check(outdir, secret=secret, briefing_text=md)
    with open(os.path.join(outdir, "critic.json"), "w") as f:
        json.dump(critic, f, indent=1)
    log("critic_report", ok=critic["ok"], n_checks=critic["n_checks"], n_failed=critic["n_failed"],
        failed=[c["check"] for c in critic["checks"] if not c["ok"]])
    say(f"[CRITIC] {critic['n_checks'] - critic['n_failed']} of {critic['n_checks']} checks passed" + ("" if critic["ok"] else
        ": " + "; ".join(c["check"] for c in critic["checks"] if not c["ok"])))
    with open(os.path.join(outdir, "approvals.json"), "w") as f:
        json.dump(approvals, f, indent=1)
    if not approve_briefing:
        log("gate2_pending")
        say("[GATE 2] briefing drafted and awaiting release; rerun with --approve-briefing")
        return arte
    if not critic["ok"]:
        log("gate2_blocked", reason="critic failed")
        raise SystemExit("[GATE 2] blocked: the critic failed; see critic.json")
    ok, why, match = gate(register, approver, approver_role, preparer, four_eyes)
    if not ok:
        log("gate2_refused", actor=approver or "unnamed", reason=why)
        raise SystemExit(f"[GATE 2] refused: {why}")
    approvals["gate2"] = {"decision": "approved", "actor": approver, "role": approver_role, "ts": utc_now(), "register": match}
    md = draft_briefing(arte, approvals, run_id, critic=critic)
    with open(os.path.join(outdir, "briefing.md"), "w") as f:
        f.write(md)
    with open(os.path.join(outdir, "briefing.html"), "w") as f:
        f.write(to_html(md))
    rec = atrs_record(arte, approvals, run_id, organisation=organisation, team=team)
    with open(os.path.join(outdir, "atrs_record.json"), "w") as f:
        json.dump(rec, f, indent=1)
    with open(os.path.join(outdir, "atrs_record.md"), "w") as f:
        f.write(render_markdown(rec))
    with open(os.path.join(outdir, "approvals.json"), "w") as f:
        json.dump(approvals, f, indent=1)
    log("gate2_approved", actor=approver, role=approver_role, register=match)
    log("briefing_released", actor=approver, sha256_md=_sha(os.path.join(outdir, "briefing.md")))
    meta = {"run_id": run_id, "question": question, "preparer": preparer, "approver": approver, "stage": "released",
            "created": utc_now(), "updated": utc_now(), "preferred": ev["preferred"], "battery_hash": bat["hash"]}
    with open(os.path.join(outdir, "meta.json"), "w") as f:
        json.dump(meta, f, indent=1)
    pack, manifest = build_pack(outdir)
    log("evidence_pack_built", files=list(manifest["files"]))
    say(f"[GATE 2] released by {approver}; briefing.md, atrs_record.md and evidence_pack.zip written to {outdir}")
    return arte


def _sha(path):
    import hashlib
    h = hashlib.sha256()
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()


def main(argv=None):
    ap = argparse.ArgumentParser(description="Policy Scenario Lab orchestrator")
    ap.add_argument("--question", default=DEFAULT_QUESTION)
    ap.add_argument("--battery", help="replay a battery.json")
    ap.add_argument("--outdir", default=os.path.join("runs", new_run_id()))
    ap.add_argument("--approve-battery", action="store_true")
    ap.add_argument("--approve-briefing", action="store_true")
    ap.add_argument("--preparer"); ap.add_argument("--preparer-role")
    ap.add_argument("--approver"); ap.add_argument("--approver-role")
    ap.add_argument("--register", default=os.environ.get("PSL_REGISTER", ""))
    ap.add_argument("--profile", default=os.environ.get("PSL_PROFILE", "full"), choices=("full", "light", "demo"))
    ap.add_argument("--paths", type=int); ap.add_argument("--horizon", type=int)
    ap.add_argument("--assumptions", help="JSON file of assumption overrides")
    ap.add_argument("--no-four-eyes", action="store_true")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args(argv)
    from config import PROFILES  # noqa: WPS433  (the server's profile table)
    budget = dict(PROFILES[args.profile])
    if args.paths:
        budget["paths"] = args.paths; budget["redteam_paths"] = args.paths
    if args.horizon:
        budget["horizon"] = args.horizon
    battery = None
    if args.battery:
        with open(args.battery) as f:
            battery = json.load(f)
    assumptions = None
    if args.assumptions:
        with open(args.assumptions) as f:
            assumptions = json.load(f)
    run_pipeline(args.question, args.outdir, approve_battery=args.approve_battery, approve_briefing=args.approve_briefing,
                 preparer=args.preparer, preparer_role=args.preparer_role, approver=args.approver, approver_role=args.approver_role,
                 register_path=args.register or None, secret=os.environ.get("PSL_SECRET"), budget=budget, profile=args.profile,
                 battery=battery, assumptions=assumptions, four_eyes=not args.no_four_eyes, quiet=args.quiet)


if __name__ == "__main__":
    sys.exit(main())
