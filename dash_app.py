"""PSL TERMINAL: the Policy Scenario Lab at terminal density, built to be run
by a public authority.

Run with:  python dash_app.py   (then open http://127.0.0.1:8070)

A policy question is read into a battery of candidate regulatory
instruments. A named approver on the register signs the battery off at
Gate 1; every instrument then runs on the same synthetic AI economy and
the same random numbers, the news wire and the equity panel streaming the
representative path as it goes. The social ledger, the safety forecast,
the industry's gain or loss and the decision gap render as the scoring
completes; the assurance stages attack the answer; an independent critic
recomputes every figure before Gate 2 can release the briefing with its
evidence pack and transparency record.

Function codes
  1 NWS  news wire and forecast    6 GAP  decision gap           0 POL  policy library
  2 MKT  technology equities       7 LDG  rationale ledger       K RSK  assurance
  3 SAF  safety forecast           8 RUN  run control and gates  D DAT  data desk
  4 PNL  industry gain or loss     9 ASK  run oracle             A AGT  firm workshop
  5 WLF  social ledger                                           S SEC  security posture    R REG  run registry
"""

import datetime
import hashlib
import json
import logging
import os
import re
import threading
import time
from collections import defaultdict, deque

logging.getLogger("werkzeug").setLevel(logging.ERROR)

import flask  # noqa: E402
from dash import Dash, Input, Output, State, dcc, html, no_update, ctx  # noqa: E402
from dash import ClientsideFunction  # noqa: E402
from dash.exceptions import PreventUpdate  # noqa: E402
from flask import request as freq, send_from_directory, jsonify, abort  # noqa: E402

from config import Config  # noqa: E402
from runstore import RunStore, SERVABLE, utc_now  # noqa: E402
from psl import __version__, provenance  # noqa: E402
from psl import assumptions as AS  # noqa: E402
from psl import welfare as W  # noqa: E402
from psl import benchmarks as BM  # noqa: E402
from psl import validation as VAL  # noqa: E402
from psl.ask import answer as ask_answer  # noqa: E402
from psl.atrs import atrs_record, render_markdown  # noqa: E402
from psl.briefing import draft_briefing, to_html, COMP_LABELS  # noqa: E402
from psl.critic import critic_check  # noqa: E402
from psl.firms import FirmStore, template as firm_template, BOUNDS as FIRM_BOUNDS, MAX_FIRMS, validate_firm, default_firms  # noqa: E402
from psl.ingest import quarantine, dataset_summary, apply_calibration, persist_datasets, keep_recent  # noqa: E402
from psl.ledger import Ledger, verify as ledger_verify  # noqa: E402
from psl.llm import make_client, ask_llm, draft_briefing_llm, plan_llm  # noqa: E402
from psl.orchestrator import new_run_id  # noqa: E402
from psl.pipeline import make_battery, run_battery, SimulationStopped  # noqa: E402
from psl.policies import (PolicyStore, template as policy_template, BOUNDS as POLICY_BOUNDS, LIBRARY, SECTORS,  # noqa: E402
                          MAX_POLICIES, all_library, describe as describe_policy)
from psl.question import parse as parse_question, describe as describe_plan, DEFAULT_QUESTION  # noqa: E402
from psl.register import PersonRegister  # noqa: E402
from psl.security import posture, authorize, CLASSIFICATIONS  # noqa: E402
from psl._common import nice_name as _nice  # noqa: E402

CFG = Config()
BUILD = f"{__version__} {datetime.date.today().isoformat()}"
STORE = RunStore(CFG.runs_dir)
POLICIES = PolicyStore(CFG.runs_dir)
FIRMS = FirmStore(CFG.runs_dir)
REGISTER = PersonRegister(CFG.register_path or None, required=CFG.register_required if CFG.register_path else None)
CLIENT = make_client(CFG)
LOCK = threading.RLock()
STOP = threading.Event()
START_YEAR, START_MONTH = datetime.date.today().year + 1, 1


def _fresh_state():
    return {
        "run_id": None, "run_dir": None, "log": None, "started": None,
        "stage": "idle",      # idle|planning|planned|rejected|running|halted|evaluated|refused|released|error
        "phase": "Awaiting run control", "busy": False, "err": None,
        "seq": 0, "ticks": [], "heads": [], "alerts": [], "ledger_rows": [], "done": [],
        "rev": 0, "question": DEFAULT_QUESTION, "preparer": None, "preparer_role": "", "stop_actor": None,
        "battery": None, "battery_hash": None, "plan_text": "", "policy_current": None, "labels": [],
        "artefacts": None, "critic": None, "briefing": None, "approvals": {}, "ledger_report": None,
        "llm_used": False, "datasets": [], "posture": None, "assumption_overrides": {},
        "step": "plan",       # plan|gate1|simulate|markets|welfare|assurance|critic|gate2|released
        "pick": {"pnl": None, "wlf": None, "nws": None},
    }


S = _fresh_state()


def _mut(**kw):
    with LOCK:
        S.update(kw)


def _bump(**kw):
    with LOCK:
        S.update(kw)
        S["rev"] += 1


def _alert(lvl, msg):
    with LOCK:
        S["seq"] += 1
        S["alerts"].append((S["seq"], {"t": time.strftime("%H:%M:%S"), "lvl": lvl, "msg": msg}))


class StreamLedger(Ledger):
    """Ledger that also streams each entry into the LDG panel."""

    def __call__(self, event, actor=None, **payload):
        rec = super().__call__(event, actor=actor, **payload)
        with LOCK:
            S["seq"] += 1
            S["ledger_rows"].append((S["seq"], {"seq": rec["seq"], "ts": rec["ts"][11:19], "event": event,
                                               "actor": rec["actor"], "hash": rec["hash"][:16],
                                               "keys": ",".join(list(payload)[:5])}))
        return rec


# ---------------------------------------------------------------- identity --
def _role():
    if CFG.auth_mode == "header":
        try:
            return (flask.request.headers.get(CFG.role_header) or "viewer").strip().lower()
        except Exception:  # noqa: BLE001
            return "viewer"
    return "admin"


def _may(action):
    return authorize(_role(), action)


OPEN_GATES = CFG.gates == "open"
OPEN_ACTOR = "visitor"
OPEN_ROLE = "public demonstration, no sign off"


def _actor(field_value):
    """The acting identity, or the demonstration's stand in when the gates are open."""
    return identity(field_value) or (OPEN_ACTOR if OPEN_GATES else None)


def identity(field_value):
    if CFG.auth_mode == "header":
        try:
            u = (freq.headers.get(CFG.user_header) or "").strip()
        except RuntimeError:
            u = ""
        return u or None
    return (field_value or "").strip()[:80] or None


def authorised_approver(actor, role=None):
    if OPEN_GATES:
        return True, ""
    if not actor:
        return False, "a named approver is required"
    if CFG.auth_mode == "open" and not (role or "").strip():
        return False, "the approver's function is required (an SMF or certified function" + \
            (", or Developer2 in dev mode)" if CFG.dev_mode else ")")
    if CFG.approvers and actor.lower() not in CFG.approvers:
        return False, f"{actor} is not on the approver list"
    if CFG.four_eyes and S["preparer"] and actor.strip().lower() == S["preparer"].strip().lower():
        return False, "four eyes: the approver must differ from the preparer"
    verdict = REGISTER.check(actor, role)
    if not verdict["ok"]:
        return False, verdict["reason"]
    return True, ""


# ----------------------------------------------------------------- workers --
def _stream(kind, payload):
    with LOCK:
        S["seq"] += 1
        if kind == "tick":
            S["ticks"].append((S["seq"], payload))
            for h in payload.get("headlines", []):
                S["seq"] += 1
                S["heads"].append((S["seq"], dict(h, policy=payload["policy"])))
        elif kind == "policy_done":
            S["done"].append(payload)
            S["seq"] += 1
            S["alerts"].append((S["seq"], {"t": time.strftime("%H:%M:%S"), "lvl": "info",
                                            "msg": f"{payload['label']}: {payload['headlines']} headlines, "
                                                   f"{payload['share_negative']:.0%} negative"}))
    if kind == "tick" and CFG.tick_pace:
        time.sleep(CFG.tick_pace)


def _progress(step, phase, **kw):
    _bump(step=step, phase=phase, policy_current=kw.get("policy", S["policy_current"]))
    if step == "simulate" and kw.get("policy"):
        _alert("info", phase)
    elif step in ("markets", "welfare", "critic") or (step == "assurance" and ":" not in phase):
        _alert("info", phase)


def _worker_plan(question, preparer):
    run_id = None
    try:
        run_id = new_run_id()
        d = STORE.create(run_id)
        log = StreamLedger(os.path.join(d, "ledger.jsonl"), run_id, secret=CFG.secret, actor="orchestrator")
        with LOCK:
            keep_rev = S["rev"]
            dsets = list(S["datasets"]); overrides = dict(S["assumption_overrides"]); prole = S["preparer_role"]
            S.update(_fresh_state())
            S.update(run_id=run_id, run_dir=d, log=log, stage="planning", busy=True, question=question, preparer=preparer,
                     preparer_role=prole, started=utc_now(), step="plan", datasets=dsets, assumption_overrides=overrides,
                     phase="Reading the question and planning the battery", rev=keep_rev + 1)
        STOP.clear()
        log("run_started", actor=preparer, question=question, preparer=preparer, preparer_role=prole,
            provenance=provenance(), auth_mode=CFG.auth_mode, four_eyes=CFG.four_eyes, llm_enabled=CFG.llm_enabled,
            register_configured=REGISTER.configured, dev_mode=CFG.dev_mode, gates=CFG.gates, profile=CFG.profile)
        STORE.update_meta(run_id, question=question, preparer=preparer, stage="planning", created=utc_now())
        plan = parse_question(question)
        if CFG.llm_enabled:
            extra = plan_llm(question, CLIENT, log)
            if extra:
                for n in extra.get("policies", []):
                    if n not in plan["policies"]:
                        plan["policies"].append(n); plan["notes"].append("model reading")
                for k, v in extra.get("constraints", {}).items():
                    plan["constraints"].setdefault(k, v)
                if extra.get("horizon_months") and not plan.get("horizon_months"):
                    plan["horizon_months"] = extra["horizon_months"]
        firms, origin = FIRMS.economy()
        firms, cal_notes = apply_calibration(firms, dsets)
        seed = plan["seed"] if plan.get("seed") is not None else CFG.seed
        bat = make_battery(plan, firms=firms, assumptions=overrides, budget=dict(CFG.budget), custom_policies=POLICIES.enabled(),
                           profile=CFG.profile, seed=seed, benchmarks=BM.load(CFG.benchmarks_path) if CFG.benchmarks_path else None)
        bat["firms_origin"] = origin
        bat["calibration_notes"] = cal_notes
        bat["datasets"] = [{"name": x["name"], "sha256": x["sha256"], "classification": x["classification"],
                            "maps_to": x.get("maps_to"), "analogue_of": x.get("analogue_of"), "event_study": x.get("event_study")} for x in dsets]
        STORE.write_json(run_id, "battery.json", bat)
        if dsets:
            persist_datasets(dsets, d)
        log("battery_planned", n_policies=len(bat["policies"]), battery_hash=bat["hash"], assumptions_hash=bat["assumptions_hash"],
            policies=[p["name"] for p in bat["policies"]], constraints=bat["constraints"], reading=plan["notes"],
            horizon=bat["horizon"], paths=bat["paths"], firms_origin=origin, calibration=cal_notes,
            assumption_notes=bat["assumption_notes"])
        text = describe_plan(plan)
        _bump(stage="planned", battery=bat, battery_hash=bat["hash"], plan_text=text, step="gate1",
              labels=[f["label"] for f in bat["firms"]],
              phase=f"Battery planned, {len(bat['policies'])} instruments, hash {bat['hash'][:12]}, awaiting Gate 1")
        STORE.update_meta(run_id, stage="planned", battery_hash=bat["hash"], n_policies=len(bat["policies"]))
        _alert("ok", f"Battery planned: {text}")
        if plan.get("unread"):
            _alert("alert", "A condition in the question was not read as a constraint and will not be applied: "
                   + "; ".join(f'"{x}"' for x in plan["unread"]) + ". Reword it or refuse the battery at Gate 1.")
    except Exception as e:  # noqa: BLE001
        _bump(stage="error", err=repr(e)[:300], phase="Planning failed")
        _alert("alert", f"Planning failed {e!r}"[:200])
        if run_id:
            STORE.update_meta(run_id, stage="error")
    finally:
        _mut(busy=False)


def _worker_run():
    run_id = S["run_id"]
    try:
        with LOCK:
            bat, log, d = S["battery"], S["log"], S["run_dir"]
            dsets = list(S["datasets"])
        t0 = time.time()
        arte, _ = run_battery(bat, d, log=log, progress=_progress, stream=_stream, stop=STOP.is_set,
                              start_year=START_YEAR, start_month=START_MONTH, datasets=dsets or None, reuse=CFG.reuse)
        post = posture(CFG, datasets=[{"name": x["name"], "classification": x["classification"]} for x in dsets])
        log("security_posture", status=post["status"], n_fail=post["n_fail"], n_warn=post["n_warn"])
        arte["security"] = post
        STORE.write_json(run_id, "artefacts.json", arte)
        _bump(step="critic", phase="Critic: recomputing every figure from the stored paths")
        md = draft_briefing(arte, dict(S["approvals"], preparer=S["preparer"]), run_id)
        critic = critic_check(d, secret=CFG.secret, briefing_text=md)
        STORE.write_json(run_id, "critic.json", critic)
        log("critic_report", ok=critic["ok"], n_checks=critic["n_checks"], n_failed=critic["n_failed"],
            failed=[c["check"] for c in critic["checks"] if not c["ok"]])
        rep = ledger_verify(log.path, CFG.secret)
        ev = arte["results"]
        pref = _focus(arte)
        _bump(stage="evaluated", artefacts=arte, critic=critic, ledger_report=rep, posture=post,
              step="gate2" if critic["ok"] else "critic", pick={"pnl": pref, "wlf": pref, "nws": pref},
              phase=f"Critic {'passed' if critic['ok'] else 'failed'}, {'Gate 2 armed' if critic['ok'] else 'Gate 2 sealed'}, "
                    f"preferred {_alt(arte, ev['preferred'])}, {arte['paths']} paths, run {time.time() - t0:.0f} s")
        STORE.update_meta(run_id, stage="evaluated", critic_ok=critic["ok"], preferred=ev["preferred"] or "none",
                          decision_gap=ev["decision_gap"]["decision_gap"], winner_stability=ev["winner_stability"], paths=arte["paths"])
        if not (ev.get("precision") or {}).get("met", True):
            _alert("alert", "Short of the precision target at the ceiling on paths: "
                   + "; ".join(x["text"] for x in ev["precision"]["unresolved"])[:260])
        _alert("ok" if critic["ok"] else "alert",
               f"Critic verification {'passed' if critic['ok'] else 'FAILED'} ({critic['n_checks']} checks, {critic['n_failed']} failed)")
    except SimulationStopped as e:
        log = S["log"]
        log("emergency_stop", actor=S["stop_actor"] or "unknown", where=str(e))
        _bump(stage="halted", phase="Emergency stop, run halted, partial ledger sealed")
        STORE.update_meta(run_id, stage="halted", stopped_by=S["stop_actor"])
        STORE.pack(run_id)
        _alert("alert", f"Emergency stop by {S['stop_actor']}: {e}")
    except Exception as e:  # noqa: BLE001
        import traceback
        traceback.print_exc()
        _bump(stage="error", err=repr(e)[:300], phase="Run failed")
        _alert("alert", f"Run failed {e!r}"[:200])
        STORE.update_meta(run_id, stage="error")
    finally:
        _mut(busy=False)


def _label(arte, name):
    p = (arte or {}).get("policies", {}).get(name)
    return p["label"] if p else _nice(name or "")


# --------------------------------------------------------------------- app --
app = Dash(__name__, title="PSL TERMINAL", suppress_callback_exceptions=True)
server = app.server
server.config["MAX_CONTENT_LENGTH"] = int(CFG.upload_max_mb * 1024 * 1024 * 4 / 3) + 512 * 1024
_ASK_BUCKET = defaultdict(deque)


@server.before_request
def _guard():
    if CFG.auth_mode == "header" and freq.method == "POST" and freq.path in ("/_dash-update-component", "/ask"):
        if not (freq.headers.get(CFG.user_header) or "").strip():
            abort(401)


_ANCESTORS = " ".join(["'self'"] + CFG.frame_ancestors)


@server.after_request
def _headers(resp):
    resp.headers["X-Content-Type-Options"] = "nosniff"
    if not CFG.frame_ancestors:
        resp.headers["X-Frame-Options"] = "SAMEORIGIN"
    resp.headers["Referrer-Policy"] = "no-referrer"
    resp.headers["Content-Security-Policy"] = (
        "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; "
        f"img-src 'self' data: blob:; font-src 'self' data:; connect-src 'self'; frame-src 'self'; frame-ancestors {_ANCESTORS}; "
        "object-src 'none'; base-uri 'self'")
    if freq.path.startswith(("/run/", "/runs.json", "/ask", "/healthz", "/version")):
        resp.headers["Cache-Control"] = "no-store"
    return resp


@server.route("/healthz")
def _healthz():
    with LOCK:
        return jsonify({"ok": True, "stage": S["stage"], "busy": S["busy"], "run_id": S["run_id"]})


@server.route("/version")
def _version():
    return jsonify({"version": __version__, "build": BUILD, "config": CFG.public(), "provenance": provenance()})


@server.route("/runs.json")
def _runs():
    return jsonify(STORE.index())


@server.route("/run/<run_id>/<name>")
def _run_file(run_id, name):
    if not re.match(r"^[0-9]{8}-[0-9]{6}-[0-9a-f]{4}$", run_id) or name not in SERVABLE:
        abort(404)
    d = STORE.path(run_id)
    if not os.path.isfile(os.path.join(d, name)):
        abort(404)
    return send_from_directory(d, name, as_attachment=name.endswith(".zip"))


def _snapshot():
    with LOCK:
        lr = S["ledger_report"]
        if S["log"] is not None and (lr is None or S["stage"] in ("running", "planning")):
            lr = {"entries": S["log"].seq, "head": S["log"].head, "signed": S["log"].seq, "ok": None}
        news = {}
        if S["run_id"] and S["artefacts"]:
            ns = STORE.read_json(S["run_id"], "news_sample.json", {}) or {}
            news = {k: v.get("wire", []) for k, v in ns.items()}
        return {"stage": S["stage"], "question": S["question"], "run_id": S["run_id"], "approvals": dict(S["approvals"]),
                "critic": S["critic"], "ledger": lr, "artefacts": S["artefacts"], "news": news}


@server.route("/ask", methods=["POST"])
def _ask():
    body = freq.get_json(force=True, silent=True) or {}
    q = str(body.get("q", ""))[:600].strip()
    if not q:
        return jsonify({"error": "empty question"}), 400
    who = (identity(None) if CFG.auth_mode == "header" else None) or freq.remote_addr or "anon"
    now = time.time()
    if len(_ASK_BUCKET) > 5000:
        for k in [k for k, v in _ASK_BUCKET.items() if not v or now - v[-1] > 60]:
            _ASK_BUCKET.pop(k, None)
    bucket = _ASK_BUCKET[who]
    while bucket and now - bucket[0] > 60:
        bucket.popleft()
    if len(bucket) >= CFG.ask_rate:
        return jsonify({"error": "rate limit"}), 429
    bucket.append(now)
    snap = _snapshot()
    log = S["log"]
    res = ask_answer(snap, q, client=CLIENT if CFG.llm_enabled else None, log=log)
    brain = f"{CLIENT.provider} {CLIENT.model}, grounded on vetted context" if res.get("llm") else "deterministic, from the artefacts"
    if log is not None:
        log("ask", actor=who, question=q[:200], intent=res["intent"], sources=[c["id"] for c in res["sources"]], brain=brain)
    return jsonify({"text": res["answer"], "sources": res["sources"], "brain": brain, "intent": res["intent"]})


# ----------------------------------------------------------------- helpers --
def _fmt(x, nd=2):
    if x is None:
        return "n/a"
    if isinstance(x, (int, float)) and not isinstance(x, bool):
        if abs(x) < 0.5 * 10 ** (-nd):
            x = 0.0
        return f"{x:,.{nd}f}"
    return str(x)


def _cap(s):
    s = _nice(s)
    return s[:1].upper() + s[1:]


def _tail(summary, what):
    """A line explaining an expected value that sits above the 90th percentile of the outcomes: it is carried by the tail."""
    if not summary or summary["mean"] <= summary["hi"] or summary.get("tail_share", 0) < 0.3:
        return None
    return html.Div(f"Tail driven: the expected {what} ({_fmt(summary['mean'], 1)}) sits above the 90th percentile of the simulated outcomes "
                    f"({_fmt(summary['hi'], 1)}) because {_pct(summary['tail_share'])} of the outcomes' average comes from the tenth of paths with "
                    f"the largest values, typically paths where a catastrophic incident is averted; the median outcome is "
                    f"{_fmt(summary.get('median'), 1)}.", className="gap-note strong")


def _pct(x, nd=0):
    return "n/a" if x is None else f"{x * 100:.{nd}f}%"


def _bn(x, nd=1):
    if x is None:
        return "n/a"
    if abs(x) < 0.5 * 10 ** (-nd):
        x = 0.0
    sign = "-" if x < 0 else ""
    v = abs(x)
    return f"{sign}${v / 1000:,.2f}tn" if v >= 1000 else f"{sign}${v:,.{nd}f}bn"


def _ci(s, nd=1):
    """The 95% confidence interval of an expected value (Monte Carlo error)."""
    return f"[{_fmt(s['ci_lo'], nd)}, {_fmt(s['ci_hi'], nd)}]"


def _spread(s, nd=1):
    """The 10th to 90th percentile range of the simulated outcomes."""
    return f"[{_fmt(s['lo'], nd)}, {_fmt(s['hi'], nd)}]"


def _alt(arte, name):
    """An alternative's name for a sentence: the instrument's label, or 'the status quo'."""
    if name == "baseline":
        return "the status quo"
    return _label(arte, name) if name else "none"


def _focus(arte):
    """The instrument the single instrument panels open on: the preferred one, or the best instrument when the
    status quo is preferred or nothing satisfies the constraints."""
    ev = arte["results"]
    return ev["preferred"] if ev["preferred"] not in (None, "baseline") else ev["focus"]


_NUMERIC = re.compile(r"^[-+$]?(\d|n/a|\[)")


def _table(rows, cols, cls="data", heads=None):
    heads = heads or cols
    numeric = []
    for k, c in enumerate(cols):
        vals = [str(r.get(c, "")) for r in rows]
        numeric.append(k > 0 and vals and all(_NUMERIC.match(v.strip()) for v in vals if v.strip()))

    def cell(v):
        return _nice(v) if isinstance(v, str) else v

    def cls_for(k, v):
        if numeric[k]:
            return "num"
        return "wrap" if isinstance(v, str) and len(v) > 48 else ""
    return html.Table([
        html.Thead(html.Tr([html.Th(_nice(h) if isinstance(h, str) else h, className="num" if numeric[k] else "")
                            for k, h in enumerate(heads)])),
        html.Tbody([html.Tr([html.Td(cell(r.get(c, "")), className=cls_for(k, r.get(c, ""))) for k, c in enumerate(cols)])
                    for r in rows])], className=cls)


def _kv(k, v, cls="v"):
    return html.Div([html.Span(k, className="k"), html.Span(v, className=cls)], className="kv")


def _chart(kind, spec, height=180):
    """A chart drawn client side from its specification (terminal.js renders it as SVG)."""
    return html.Div(className="jchart", style={"height": f"{height}px"}, **{"data-spec": json.dumps(dict(spec, kind=kind))})


def _howto(intro, steps, note=None):
    return html.Div([html.Div(intro, className="howto-intro"), html.Ol([html.Li(s) for s in steps], className="howto-steps")]
                    + ([html.Div(note, className="howto-note")] if note else []), className="howto")


def _sectioned(children):
    """Split a flat body into selectable sections at each gap-name header."""
    secs, cur = [], None
    for ch in children if isinstance(children, list) else [children]:
        cls = getattr(ch, "className", "") or ""
        if cls.startswith("gap-name"):
            cur = [ch.children if isinstance(ch.children, str) else "Section", [ch]]
            secs.append(cur)
        else:
            if cur is None:
                cur = ["Overview", []]
                secs.append(cur)
            cur[1].append(ch)
    if len(secs) < 2:
        return children
    btns = [html.Button(lab.split(":")[0][:26], className="sec-btn" + (" on" if i == 0 else ""), **{"data-sec": str(i)})
            for i, (lab, _) in enumerate(secs)]
    return [html.Div(btns, className="sec-row")] + \
        [html.Div(kids, className="sec" + (" on" if i == 0 else ""), **{"data-sec": str(i)}) for i, (_, kids) in enumerate(secs)]


def _pols(arte):
    return {r["policy"]: r for r in arte["results"]["policies"]}


def _pick(key, arte):
    with LOCK:
        p = (S["pick"] or {}).get(key)
    pols = _pols(arte)
    if p in pols and p != "baseline":
        return p
    return _focus(arte)


def _picker(pid, arte, current):
    opts = [{"label": r["label"], "value": r["policy"]} for r in arte["results"]["policies"] if r["policy"] != "baseline"]
    return dcc.RadioItems(id=pid, options=opts, value=current, inline=True, className="seg", inputClassName="seg-in",
                          labelClassName="seg-lab")


# ------------------------------------------------------------ panel bodies --
def _await(text):
    return html.Div(text, className="await")


def _decision_note(arte):
    """The decision in one block, the same words on every panel that shows it."""
    ev = arte["results"]; d = ev["decision"]; pr = ev.get("precision") or {}
    kids = [html.Div(d["text"], className="gap-note strong")]
    if pr and not pr.get("met", True):
        kids.append(html.Div(f"Short of the precision target at the ceiling of {pr['max_paths']} paths: "
                             + "; ".join(x["text"] for x in pr["unresolved"]) + ".", className="gap-note strong"))
    return kids


def _saf_body():
    arte = S["artefacts"]
    if not arte:
        return [_await("Awaiting the battery: incident rates, the probability of a major and of a catastrophic incident, "
                       "expected harm, safety practice, capability and trust under every alternative render here.")]
    ev = arte["results"]; pref = _focus(arte)
    rows, bars = [], []
    for r in ev["policies"]:
        s = r["safety"]; pc = s["p_catastrophe_detail"]
        rows.append({"i": r["label"] + (" *" if r["policy"] == ev["preferred"] else ""), "inc": _fmt(s["incidents_per_year"]["mean"], 1),
                     "maj": _fmt(s["major_per_year"]["mean"], 2), "pm": _pct(s["p_major"]), "pc": _pct(s["p_catastrophe"], 1),
                     "pci": f"{_pct(pc['ci_lo'], 1)} to {_pct(pc['ci_hi'], 1)}", "kn": f"{pc['k']} of {pc['n']}",
                     "harm": _fmt(s["expected_harm_npv"]["mean"], 1), "S": _fmt(s["safety_level_end"], 2),
                     "sig": _pct(s["safety_share_end"]), "C": _fmt(s["frontier_capability_end"], 2), "T": _fmt(s["trust_end"], 2),
                     "off": _pct(s["offshore_share_end"])})
        if r["policy"] != "baseline":
            c = r["components"]["harm_avoided"]
            bars.append({"label": r["label"], "value": c["mean"], "lo": c["ci_lo"], "hi": c["ci_hi"],
                         "color": "#f6b52a" if r["policy"] == ev["preferred"] else "#6cb5ff"})
    base = ev["policies"][0]["safety"]
    return [html.Div(f"Expected harm at the status quo {_bn(base['expected_harm_npv']['mean'])} over {arte['horizon'] // 12} years, "
                     f"of which catastrophic {_bn(base['expected_catastrophe_harm_npv'])}; * preferred", className="feed-cap"),
            _chart("hbars", {"rows": bars, "unit": "$bn expected harm avoided, with the 95% confidence interval of the estimate", "zero": True},
                   height=max(120, 22 * len(bars) + 30)),
            *[x for x in [_tail(_pols(arte)[pref]["components"]["harm_avoided"], f"harm avoided by {_label(arte, pref)}")] if x is not None],
            _table(rows, ["i", "inc", "maj", "pm", "pc", "pci", "kn", "harm", "S", "sig", "C", "T", "off"],
                   heads=["alternative", "incidents/yr", "major/yr", "P(major)", "P(catastrophe)", "95% interval", "paths drawn", "harm $bn", "safety",
                          "safety share", "frontier cap.", "trust", "offshore"]),
            html.Div("Expected harm and the probability of a catastrophe are estimated from what each path's state makes likely, month by month "
                     "(the hazard it accumulates and the mean severity), not from the incidents that happened to be drawn: the same expectation, "
                     "far less noise. 'Paths drawn' is the raw count of paths on which a catastrophe was drawn. A major incident is a single "
                     "incident at or above the threshold; catastrophes are counted apart.", className="gap-note")]


def _pnl_body():
    arte = S["artefacts"]
    if not arte:
        return [_await("Awaiting the battery: each firm's value change against the status quo, the probability it gains, "
                       "earnings, and the sector totals under the chosen instrument render here.")]
    cur = _pick("pnl", arte)
    r = _pols(arte)[cur]; m = r["market"]; iv = r["industry_value_change"]
    bars = [{"label": f["firm"], "value": f["value_change"]["mean"], "lo": f["value_change"]["ci_lo"], "hi": f["value_change"]["ci_hi"],
             "color": "#47d6a3" if f["value_change"]["mean"] >= 0 else "#ff5f5f"} for f in m["firms"]]
    rows = [{"f": f["firm"], "s": _cap(f["sector"]), "v": _fmt(f["value_change"]["mean"], 1), "ci": _ci(f["value_change"]), "sp": _spread(f["value_change"]),
             "pg": _pct(f["value_change"]["p_positive"]), "e": _fmt(f["earnings_change_npv"], 1), "px": f"{f['price_end']:.0f} vs {f['price_end_base']:.0f}",
             "off": _pct(f["offshore_end"]), "sig": _pct(f["safety_share_end"])} for f in m["firms"]]
    sec = [{"s": _cap(x["sector"]), "v": _fmt(x["value_change"]["mean"], 1), "ci": _ci(x["value_change"]), "sp": _spread(x["value_change"]),
            "c0": _fmt(x["cap0"], 0)} for x in m["sectors"]]
    return [_picker("pnl-pick", arte, cur),
            html.Div([_kv("Industry value change", f"{_bn(iv['mean'], 0)} {_ci(iv, 0)}", "v bad" if iv["mean"] < 0 else "v ok"),
                      _kv("Outcomes, 10th to 90th", _spread(iv, 0)),
                      _kv("P(industry gains)", _pct(iv["p_positive"])),
                      _kv("Index, first six months", f"{m['early_reaction']['mean'] * 100:+.1f}%"),
                      _kv("Index, horizon", f"{m['end_reaction']['mean'] * 100:+.1f}%"),
                      _kv("Starting value", _bn(m["industry_cap0"], 0))], className="kv-row"),
            _chart("hbars", {"rows": bars, "unit": "$bn expected value change against the status quo, with its 95% confidence interval", "zero": True},
                   height=22 * len(bars) + 30),
            _table(rows, ["f", "s", "v", "ci", "sp", "pg", "e", "px", "off", "sig"],
                   heads=["firm", "sector", "value $bn", "95% interval", "outcomes 10th to 90th", "P(gain)", "earnings $bn", "price end", "offshore", "safety share"]),
            html.Div("By sector", className="feed-cap"),
            _table(sec, ["s", "v", "ci", "sp", "c0"], heads=["sector", "value $bn", "95% interval", "outcomes 10th to 90th", "starting value $bn"]),
            html.Div("Value change: the earnings change over the horizon plus the discounted change in market value at its end, "
                     "paired path by path with the status quo. Every index is measured from one valuation, the firms as they stand before any "
                     "instrument is announced, so an instrument in force from the first month shows its effect on fundamentals at once. "
                     "Shareholder value is a market metric and a constraint, not part of the net social value. Synthetic archetypes, not companies.",
                     className="gap-note")]


def _wlf_body():
    arte = S["artefacts"]
    if not arte:
        return [_await("Awaiting the battery: the social ledger of the chosen instrument renders here as a waterfall of "
                       "harm avoided, consumer surplus, output, producer surplus, compliance, enforcement, leakage and "
                       "labour, with who gains and who pays.")]
    cur = _pick("wlf", arte)
    r = _pols(arte)[cur]; c = r["components"]
    items = [{"label": COMP_LABELS[k], "value": c[k]["mean"]} for k in W.BENEFITS] + \
            [{"label": COMP_LABELS[k], "value": -c[k]["mean"]} for k in W.COSTS]
    rows = [{"c": COMP_LABELS[k], "v": _fmt(c[k]["mean"] if k in W.BENEFITS else -c[k]["mean"], 1),
             "ci": _ci(c[k]) if k in W.BENEFITS else f"[{_fmt(-c[k]['ci_hi'], 1)}, {_fmt(-c[k]['ci_lo'], 1)}]",
             "sp": _spread(c[k]) if k in W.BENEFITS else f"[{_fmt(-c[k]['hi'], 1)}, {_fmt(-c[k]['lo'], 1)}]"} for k in W.COMPONENTS]
    dist = [{"p": _cap(k), "v": _fmt(v, 1)} for k, v in r["distribution"].items()] + [{"p": "Total", "v": _fmt(r["incidence_total"], 1)}]
    nsv = r["net_social_value"]
    cpe = r.get("cost_per_harm_avoided")
    return [_picker("wlf-pick", arte, cur),
            html.Div([_kv("Expected net social value", f"{_bn(nsv['mean'])} {_ci(nsv)}", "v ok" if nsv["mean"] >= 0 else "v bad"),
                      _kv("Outcomes, 10th to 90th", _spread(nsv)), _kv("Paths above zero", _pct(nsv["p_positive"])),
                      _kv("Gross social cost", _bn(r["gross_cost"]["mean"])), _kv("Gross benefit", _bn(r["gross_benefit"]["mean"])),
                      _kv("Gross cost per $ of harm avoided", _fmt(cpe, 2) if cpe else "n/a"),
                      _kv("Within constraints", f"{'yes' if r['feasible'] else 'no'} ({_pct(r['p_feasible'])} of resamples)")], className="kv-row"),
            _chart("waterfall", {"items": items, "total_label": "Net social value", "unit": "$bn present value, expected"}, height=200),
            *[x for x in (_tail(nsv, "net social value"), _tail(c["harm_avoided"], "harm avoided")) if x is not None],
            _table(rows, ["c", "v", "ci", "sp"], heads=["component", "expected $bn", "95% interval", "outcomes 10th to 90th"]),
            html.Div("The 95% interval is the confidence interval of the expected value (how well the paths estimate it). The outcomes column "
                     "is the spread of simulated outcomes (how different one path can be from another). Gross cost is the sum of the expected "
                     "component changes that are costs, never netted against savings; gross benefit less gross cost is the net social value.",
                     className="gap-note"),
            html.Div("Who gains and who pays", className="feed-cap"),
            _table(dist, ["p", "v"], heads=["party", "$bn"]),
            html.Div(f"The incidence table follows the money as well as the real effects, so it sums to the net social value plus "
                     f"{_bn(r['nonresident_payments'])} that non resident owners finance of the firms' payments, a memorandum item the net "
                     f"does not count. Standing is residents; transfers are excluded whoever pays: fines {_bn(r['transfers']['fines'])}, liability paid by "
                     f"firms {_bn(r['transfers']['liability'])}, premiums {_bn(r['transfers']['premiums'])}, claims paid to victims "
                     f"{_bn(r['transfers']['claims'])}.", className="gap-note")]


def _gap_body():
    arte = S["artefacts"]
    if not arte:
        return [_await("Awaiting the battery: the decision among the alternatives, the status quo included, and the instruments ranked "
                       "by how they look in the first six months against how they score over the horizon.")]
    ev = arte["results"]; g = ev["decision_gap"]; pols = _pols(arte)
    pref = ev["preferred"]; hl = _focus(arte)
    cand = [r for r in ev["policies"] if r["policy"] != "baseline"]
    rows = [{"i": r["label"] + (" *" if r["policy"] == pref else ""),
             "nsv": _fmt(r["net_social_value"]["mean"], 1), "ci": _ci(r["net_social_value"]), "sp": _spread(r["net_social_value"]),
             "feas": "yes" if r["feasible"] else "no", "pf": _pct(r["p_feasible"]), "pb": _pct(r["p_best"]),
             "h": r.get("rank_headline", ""), "s": r.get("rank_social", ""), "hs": f"{r['headline_score']:+.3f}"}
            for r in sorted(ev["policies"], key=lambda r: -r["net_social_value"]["mean"])]
    ladder = {"left": [pols[n]["label"] for n in g["headline_order"]], "right": [pols[n]["label"] for n in g["social_order"]],
              "left_title": "looks best early", "right_title": "best over the horizon", "highlight": pols[hl]["label"],
              "unit": "amber: " + ("the preferred option under the question's constraints" if pref not in (None, "baseline") else
                                   "the best instrument; the status quo is preferred to it")}
    pb = [{"label": r["label"], "value": r["p_best"], "color": "#f6b52a"} for r in sorted(ev["policies"], key=lambda r: -r["p_best"])]
    diffs = [r for r in ev["policies"] if r.get("vs_preferred") and r["feasible"]]
    kids = [html.Div([_kv("Preferred", _cap(_alt(arte, pref)), "v big"), _kv("Decision gap", _fmt(g["decision_gap"], 2)),
                      _kv("Kendall tau b", f"{g['kendall_tau']:+.2f}"), _kv("P(inversion)", _pct(g["p_inversion"])),
                      _kv("Ranking stability", _pct(ev["winner_stability"])), _kv("Paths", str(ev["n_paths"]))], className="kv-row"),
            *_decision_note(arte),
            _chart("ladder", ladder, height=max(120, 20 * len(cand) + 40)),
            _table(rows, ["i", "nsv", "ci", "sp", "feas", "pf", "pb", "h", "s", "hs"],
                   heads=["alternative", "expected value $bn", "95% interval", "outcomes 10th to 90th", "within constraints", "resamples within",
                          "ranking stability", "headline rank", "social rank", "headline score"])]
    if diffs:
        kids += [html.Div(f"{_cap(_alt(arte, pref))} against each other feasible alternative, paired on the same paths", className="feed-cap"),
                 _table([{"i": r["label"], "d": _fmt(r["vs_preferred"]["difference"], 1),
                          "ci": f"[{_fmt(r['vs_preferred']['ci_lo'], 1)}, {_fmt(r['vs_preferred']['ci_hi'], 1)}]",
                          "sim": f"[{_fmt(r['vs_preferred']['simultaneous_lo'], 1)}, {_fmt(r['vs_preferred']['simultaneous_hi'], 1)}]",
                          "t": "yes" if r["vs_preferred"]["distinguishable"] else "no"} for r in diffs],
                        ["i", "d", "ci", "sim", "t"], heads=["against", "difference $bn", "95% interval", "simultaneous 95%", "told apart"])]
    kids += [html.Div("Ranking stability: the share of bootstrap resamples of the paths in which the alternative is the best feasible one", className="feed-cap"),
             _chart("hbars", {"rows": pb, "unit": "share of resamples; conditional on the model and its assumptions, not the probability of being best in the world",
                              "zero": False, "max": 1.0}, height=22 * len(pb) + 30),
             html.Div(g["note"] + ". The status quo scores zero by construction and is a decision alternative: an instrument is preferred only "
                      "if its expected net social value is above it. Feasibility is re assessed in every resample.", className="gap-note")]
    return kids


def _nws_forecast():
    arte = S["artefacts"]
    if not arte:
        return [_await("The forecast renders once the battery is scored: expected negative headlines per quarter with the 90th "
                       "percentile, the pressure index, and the headline counts a year by type for every instrument.")]
    cur = _pick("nws", arte)
    ev = arte["results"]; pols = _pols(arte); r = pols[cur]; b = pols["baseline"]
    n = r["news"]; nb = b["news"]
    q = {"bars": n["quarterly_negative"], "hi": n["quarterly_negative_hi"], "line": n["quarterly_pressure"],
         "base_bars": nb["quarterly_negative"], "labels": [f"Q{i + 1}" for i in range(len(n["quarterly_negative"]))],
         "unit": "negative headlines a quarter (bars; grey: status quo) and pressure (line)"}
    rows = []
    for x in ev["policies"]:
        h = x["news"]["headlines_per_year"]
        rows.append({"i": x["label"], "mi": _fmt(h["minor incidents"]["mean"], 1), "ma": _fmt(h["major incidents"]["mean"], 2),
                     "ca": _fmt(h["catastrophes"]["mean"], 3), "en": _fmt(h["enforcement actions"]["mean"], 2), "re": _fmt(h["relocations"]["mean"], 2),
                     "mil": _fmt(h["capability milestones"]["mean"], 1), "pp": _fmt(x["news"]["peak_pressure"]["mean"], 2),
                     "ph": _pct(x["news"]["p_hearing"]), "tone": f"{x['news']['early_tone']:+.2f}"})
    ws = arte["news"][cur]
    return [_picker("nws-pick", arte, cur),
            html.Div([_kv("Peak pressure", _fmt(n["peak_pressure"]["mean"], 2)), _kv("P(hearing)", _pct(n["p_hearing"])),
                      _kv("Months under high pressure", _pct(n["share_months_high_pressure"])), _kv("Early tone", f"{n['early_tone']:+.2f}"),
                      _kv("Representative wire", f"{ws.get('headlines', 0)} headlines, {_pct(ws.get('share_negative', 0))} negative")], className="kv-row"),
            _chart("quarters", q, height=170),
            _table(rows, ["i", "mi", "ma", "ca", "en", "re", "mil", "pp", "ph", "tone"],
                   heads=["instrument", "minor incidents/yr", "major/yr", "catastrophes/yr", "enforcement/yr", "relocations/yr", "milestones/yr",
                          "peak pressure", "P(hearing)", "early tone"]),
            html.Div("Counts are means over the paths; the wire on the left is one path. Headlines are composed by four media agents "
                     "from the simulation's events with templates; every figure in them is the event's own.", className="gap-note")]


def _rsk_body():
    arte = S["artefacts"]
    if not arte:
        return [_await("Awaiting the battery: the screen of every assumption, the joint draw, the variance decomposition, the structural "
                       "variants, the red team, the replication check and the validation render here as the assurance stages complete.")]
    asr = arte.get("assurance") or {}; ev = arte["results"]; pols = _pols(arte)
    pr = ev.get("precision") or {}

    def lab(n):
        return _cap(_alt(arte, n))
    kids = [html.Div("Monte Carlo: how well the paths estimate", className="gap-name")]
    kids += _decision_note(arte)
    if pr:
        kids.append(html.Div([_kv("Paths", str(pr["paths"])), _kv("Sampling plan", " then ".join(str(x) for x in pr["schedule"])),
                              _kv("Ceiling", str(pr["max_paths"])), _kv("Targets", f"{_bn(pr['targets']['nsv_gap_bn'])}, {_pct(pr['targets']['p_catastrophe_halfwidth'])}"),
                              _kv("Met", "yes" if pr["met"] else "no", "v ok" if pr["met"] else "v bad"),
                              _kv("Bootstrap", str(ev["bootstrap"]))], className="kv-row"))
    cv = asr.get("convergence")
    if cv and len(cv["rows"]) > 1:
        kids.append(_table([{"n": f"{r['paths']:,}", "d": lab(r["preferred"]), "v": _fmt(r.get("focus_nsv"), 1), "se": _fmt(r.get("focus_se"), 2),
                             "ci": f"[{_fmt(r.get('focus_lo'), 1)}, {_fmt(r.get('focus_hi'), 1)}]", "pc": _pct(r["p_catastrophe_status_quo"], 1)}
                            for r in cv["rows"]], ["n", "d", "v", "se", "ci", "pc"],
                           heads=["first paths", "decision", f"value of {lab(cv['focus'])} $bn", "standard error", "95% interval", "P(catastrophe), status quo"]))
        kids.append(html.Div("Convergence: the running estimate on the first paths of the run, which are exactly what a smaller run on this seed "
                             "reports. " + ("The decision is the same over the last doubling of the paths."
                                            if cv["decision_stable_over_last_doubling"] else
                                            "The decision changes over the last doubling of the paths: a reason to run more."), className="gap-note"))
    bt = asr.get("batches")
    if bt:
        kids.append(_table([{"b": r["batch"], "n": r["paths"], "d": lab(r["preferred"]), "bi": lab(r["best_intervention"])} for r in bt["rows"]],
                           ["b", "n", "d", "bi"], heads=["batch", "paths", "decision", "best instrument"]))
        kids.append(html.Div(f"The decision is the same in {bt['agree']} of {bt['k']} independent batches of the run's paths.", className="gap-note"))
    kids.append(_table([{"i": r["label"], "nsv": _fmt(r["net_social_value"]["mean"], 1), "ci": _ci(r["net_social_value"]), "sp": _spread(r["net_social_value"]),
                         "pp": _pct(r["net_social_value"]["p_positive"]),
                         "ha": _fmt(r["components"]["harm_avoided"]["mean"], 1), "hci": _ci(r["components"]["harm_avoided"]),
                         "iv": _fmt(r["industry_value_change"]["mean"], 0), "ici": _ci(r["industry_value_change"], 0), "pf": _pct(r["p_feasible"]), "pb": _pct(r["p_best"])}
                        for r in ev["policies"] if r["policy"] != "baseline"],
                       ["i", "nsv", "ci", "sp", "pp", "ha", "hci", "iv", "ici", "pf", "pb"],
                       heads=["instrument", "expected value $bn", "95% interval", "outcomes 10th to 90th", "paths above zero", "harm avoided", "95% interval",
                              "industry $bn", "95% interval", "resamples within", "ranking stability"]))
    t = asr.get("tornado"); scr = asr.get("screen")
    if t:
        kids.append(html.Div(f"Screen: {scr['n_assumptions']} assumptions, one at a time", className="gap-name"))
        rows = [{"label": _nice(r["assumption"]), "lo": r["low"]["nsv"], "hi": r["high"]["nsv"], "lo_v": r["low"]["value"], "hi_v": r["high"]["value"]}
                for r in t["rows"]]
        kids.append(html.Div(f"{lab(t['preferred'])} is worth {_bn(t['reference_nsv'])} at the run's values. Every assumption is moved to the low and "
                             f"the high end of its plausible range and the decision re made under each: feasibility re assessed, the status quo an "
                             f"alternative. The {t['shown']} largest swings:", className="feed-cap"))
        kids.append(_chart("tornado", {"rows": rows, "ref": t["reference_nsv"], "unit": "expected net social value of the focus option, $bn; blue: the assumption at the low end of its range, amber: at the high end; dashed: the run's value"}, height=22 * len(rows) + 30))
        kids.append(_table([{"a": _nice(r["assumption"]), "d": _fmt(r["default"], 4 if r["default"] < 0.1 else 2), "lv": _fmt(r["low"]["value"], 4 if r["low"]["value"] < 0.1 else 2),
                             "ln": _fmt(r["low"]["nsv"], 1), "lb": lab(r["low"]["best"]),
                             "hv": _fmt(r["high"]["value"], 4 if r["high"]["value"] < 0.1 else 2), "hn": _fmt(r["high"]["nsv"], 1),
                             "hb": lab(r["high"]["best"]),
                             "se": _fmt(r.get("swing_se"), 1) if r["resimulated"] else "exact",
                             "why": ", ".join(sorted({x for x in (r["low"].get("flip"), r["high"].get("flip")) if x})) or "",
                             "re": "re simulated" if r["resimulated"] else "recomputed"} for r in scr["rows"]],
                           ["a", "d", "lv", "ln", "lb", "hv", "hn", "hb", "se", "why", "re"],
                           heads=["assumption", "run's value", "low", "value at low", "decision at low", "high", "value at high", "decision at high",
                                  "standard error of the swing", "decision changes by", "how"]))
        kids.append(html.Div((f"The decision changes at an end of the range of {len(t['flips'])} of the {scr['n_assumptions']} assumptions: "
                              + ", ".join(_nice(k) for k in t["flips"][:14]) + (f" and {len(t['flips']) - 14} more" if len(t["flips"]) > 14 else "") + ". "
                              + (f"For {len(scr['flips_by_feasibility'])} the cause is feasibility ({lab(scr['reference_best'])} stops satisfying a "
                                 f"constraint under the alternative); for {len(scr['flips_by_value'])} another alternative within the constraints "
                                 f"overtakes it. " if scr.get("flips_by_feasibility") is not None else "")
                              + f"Re simulated on the first {scr['resimulated_paths']} paths, paired with the main run: "
                                f"{scr.get('n_swing_resolved', 0)} of {scr['n_assumptions']} swings exceed twice their Monte Carlo standard error.")
                             if t["flips"] else "No single assumption at an end of its range changes the decision.",
                             className="gap-note strong"))
    jd = asr.get("joint")
    if jd:
        kids.append(html.Div(f"Joint draw: {jd['draws']} draws of all the assumptions", className="gap-name"))
        kids.append(_table([{"i": lab(x["policy"]), "m": _fmt(x["nsv_mean"], 1), "r": f"[{_fmt(x['nsv_lo'], 1)}, {_fmt(x['nsv_hi'], 1)}]", "pb": _pct(x["p_best"]),
                             "pa": _pct(x["p_acceptable"]), "pf": _pct(x["p_feasible"]), "er": _fmt(x["expected_regret"], 1)}
                            for x in sorted(jd["alternatives"], key=lambda x: -x["p_best"])],
                           ["i", "m", "r", "pb", "pa", "pf", "er"],
                           heads=["alternative", "mean value $bn", "5th to 95th over draws", "share of draws it is the decision",
                                  "within constraints and above the status quo", "within constraints", "expected regret where within $bn"]))
        sens = [x for x in jd["sensitivity"]][:12]
        kids.append(html.Div("Rank correlation of each assumption with the focus option's margin over the best alternative", className="feed-cap"))
        kids.append(_chart("hbars", {"rows": [{"label": _nice(x["assumption"]), "value": x["rho_margin"],
                                               "color": "#f6b52a" if x.get("margin_driver") else "#5b6677"} for x in sens],
                                     "unit": f"Spearman rank correlation over {jd['draws']} draws; amber: passes a {_pct(jd.get('fdr', 0.1))} false discovery rate "
                                             f"over all {len(jd['sensitivity'])} assumptions; grey: does not",
                                     "zero": True}, height=22 * len(sens) + 30))
        srow = {x["assumption"]: x for x in jd["sensitivity"]}
        dd = [srow[k] for k in jd.get("decision_drivers", [])][:8]
        split = jd.get("filter_split") or [0, 0]
        kids.append(html.Div((f"Monte Carlo filtering: {lab(jd['focus'])} is the decision in {split[0]} draws and is not in {split[1]}. The two groups of draws "
                              "differ most in " + ", ".join(f"{_nice(x['assumption'])} (Kolmogorov Smirnov distance {x['ks_decision']:.2f})" for x in dd) + ".")
                             if dd else
                             (f"Monte Carlo filtering: {lab(jd['focus'])} is the decision in {split[0]} draws and is not in {split[1]}; no assumption separates "
                              f"the two groups at a {_pct(jd.get('fdr', 0.1))} false discovery rate."), className="gap-note strong"))
        kids.append(html.Div(jd["note"] + ". Expected regret: how far the alternative falls short of the best alternative within the constraints in the "
                             "same draw, averaged over the draws in which it is itself within them; read it beside the share of draws in which it is."
                             + (f" Lowest among the alternatives within the constraints in at least 90% of the draws: {lab(jd['least_regret'])}."
                                if jd.get("least_regret") else ""), className="gap-note"))
    var = asr.get("variance")
    if var:
        kids.append(html.Div("Variance: which assumptions carry it", className="gap-name"))
        iv = lambda r, k: f"{_pct(r[k + '_lo'])} to {_pct(r[k + '_hi'])}" if (k + "_lo") in r else ""
        kids.append(_table([{"a": _nice(r["assumption"]), "st": _pct(r["total_value"]), "sti": iv(r, "total_value"), "s1": _pct(r["first_order_value"]),
                             "mt": _pct(r["total_margin"]), "mti": iv(r, "total_margin"), "m1": _pct(r["first_order_margin"])} for r in var["rows"]],
                           ["a", "st", "sti", "s1", "mt", "mti", "m1"],
                           heads=["assumption", "value: with interactions", "90% interval", "value: alone", "margin: with interactions", "90% interval",
                                  "margin: alone"]))
        kids.append(html.Div(f"Sobol indices for {lab(var['focus'])} over the {len(var['keys'])} assumptions with the largest swings, "
                             f"{var['evaluations']} evaluations on a base sample of {var['base']}: shares of the variance these assumptions produce, alone "
                             f"(first order) and with their interactions (total order), with bootstrap intervals over the base sample. The intervals "
                             f"are wide (half width {_pct(var.get('mean_halfwidth_total_margin', 0))} on average for the margin) because the output is heavy "
                             f"tailed in these assumptions: the design ranks groups of assumptions and does not order neighbours. Shares with "
                             f"interactions add to more than one when assumptions interact. " + var["note"] + ".", className="gap-note"))
    st = asr.get("structural")
    if st:
        kids.append(html.Div(f"Structural variants: decision unchanged in {st['wins']} of {st['n']}", className="gap-name"))
        kids.append(_table([{"v": _nice(v["variant"]), "n": v["note"], "b": lab(v["best"]),
                             "r": v["preferred_rank"], "nsv": _fmt(v["preferred_nsv"], 1), "f": "yes" if v["preferred_feasible"] else "no",
                             "o": ", ".join(pols[n]["label"] if n in pols else n for n in v["order"][:3])} for v in st["variants"]],
                           ["v", "n", "b", "r", "nsv", "f", "o"],
                           heads=["variant", "what changes", "decision", "focus rank", "focus value $bn", "focus within constraints", "top three instruments"]))
        kids.append(html.Div(f"{lab(st['preferred'])} stays within the constraints and above the status quo in {st['acceptable']} of {st['n']} variants. "
                             f"Feasibility is re assessed under each variant.", className="gap-note"))
    rt = asr.get("red_team")
    if rt:
        kids.append(html.Div(f"Red team: best when every instrument is gamed, {lab(rt['maximin'])}", className="gap-name"))
        bars = []
        for r in rt["rows"]:
            bars.append({"label": r["label"] + " honest", "value": r["honest"]["nsv"], "color": "#6cb5ff"})
            bars.append({"label": r["label"] + " gamed", "value": r["worst_nsv"], "color": "#ff5f5f"})
        kids.append(_chart("hbars", {"rows": bars, "unit": "expected net social value $bn, honest and under the worst gaming strategy", "zero": True}, height=22 * len(bars) + 30))
        kids.append(_table([dict({"i": r["label"], "h": _fmt(r["honest"]["nsv"], 1), "w": _nice(r["worst_strategy"]), "g": _fmt(r["worst_nsv"], 1),
                                  "ha": _fmt(r["strategies"][r["worst_strategy"]]["harm_avoided"], 1), "l": _fmt(r["gaming_loss"], 1),
                                  "acc": "yes" if r["acceptable_under_all"] else "no"},
                                 **{k[:6]: _fmt(v["nsv"], 1) for k, v in r["strategies"].items()}) for r in rt["rows"]],
                           ["i", "h", "w", "g", "ha", "l", "acc"] + [k[:6] for k in rt["strategies"]],
                           heads=["instrument", "honest $bn", "worst strategy", "gamed $bn", "harm avoided gamed", "loss to gaming",
                                  "acceptable under every strategy"] + [_nice(k) for k in rt["strategies"]]))
        kids.append(html.Div("Acceptable: still within the question's constraints and above the status quo under the strategy. "
                             + "; ".join(f"{_nice(k)}: {v}" for k, v in rt["strategies"].items()), className="gap-note"))
    rb = asr.get("robustness")
    if rb:
        ra = rb["robustly_acceptable"]
        kids.append(html.Div("Robustness: " + (", ".join(pols[n]["label"] for n in ra) if ra else "no instrument") + " robustly acceptable", className="gap-name"))
        kids.append(_table([{"i": r["label"], "c": "yes" if r["central_acceptable"] else "no", "pf": _pct(r["p_feasible"]),
                             "ja": _pct(r["joint_p_acceptable"]), "jb": _pct(r["joint_p_best"]), "er": _fmt(r["expected_regret"], 1),
                             "sa": f"{r['structural_acceptable']} of {r['structural_n']}", "sb": r["structural_best"],
                             "ga": "yes" if r["gaming_acceptable"] else "no", "gw": _fmt(r["gaming_worst_nsv"], 1),
                             "ro": "yes" if r["robustly_acceptable"] else "no"} for r in rb["rows"]],
                           ["i", "c", "pf", "ja", "jb", "er", "sa", "sb", "ga", "gw", "ro"],
                           heads=["instrument", "central", "resamples within", "joint draws acceptable", "joint draws decision", "expected regret where within $bn",
                                  "structural acceptable", "structural decision", "gaming acceptable", "worst gamed $bn", "robustly acceptable"]))
        kids.append(html.Div("Acceptable: within the constraints and above the status quo. Robustly acceptable: " + rb["rule"] + ".", className="gap-note"))
    val = asr.get("validation") or {}
    evs = val.get("events") or []
    vb = val.get("benchmarks")
    if vb:
        s1, s2, s3 = VAL.narrative(vb, {n: p["label"] for n, p in pols.items()}, {k: AS.title(k) for k in arte["assumptions"]})
        sm = vb["summary"]
        kids.append(html.Div(f"Benchmarks: validation against published evidence, {sm['not_contradicted']} of {sm['scored']} not contradicted, "
                             f"{len(sm['mechanisms_confronted'])} of {sm['mechanisms']} mechanisms confronted", className="gap-name"))
        kids.append(html.Div(s1, className="gap-note strong"))
        kids.append(_table([{"b": r["benchmark"], "k": r["kind"], "o": r["observed"], "m": r["model"], "z": r["z"], "v": r["verdict"],
                             "r": r["ranges"], "h": r["held_out"]} for r in VAL.scorecard(vb)],
                           ["b", "k", "o", "m", "z", "v", "r", "h"],
                           heads=["benchmark", "kind", "observed (allowance, one sd)", "model, central assumptions", "z", "verdict",
                                  "model across the declared ranges", "predicted with it held out"], cls="data specs"))
        kids.append(html.Div("The allowance combines the benchmark's standard error with a declared allowance for the distance between the setting "
                             "it was measured in and the model's. z is the gap in those units: within two, not contradicted; two to three, in "
                             "tension; beyond three, contradicted. Held out: predicted from the joint draws weighted by all the other benchmarks.",
                             className="gap-note"))
        cb = vb.get("calibration") or {}
        if cb.get("used"):
            kids.append(html.Div("The joint draws weighted by the benchmarks", className="feed-cap"))
            kids.append(html.Div(s2, className="gap-note strong"))
            order = sorted(cb["decision_posterior"], key=lambda k: -(cb["decision_posterior"][k] or 0))
            kids.append(_table([{"a": ("No alternative within the constraints" if k == "none" else lab(k)),
                                 "u": f"{100 * (cb['decision_prior'].get(k) or 0):.0f}%", "w": f"{100 * (cb['decision_posterior'][k] or 0):.0f}%",
                                 "n": f"{100 * ((cb.get('decision_not_ruled_out') or {}).get(k) or 0):.0f}%"}
                                for k in order if (cb["decision_posterior"][k] or 0) > 0.004 or (cb["decision_prior"].get(k) or 0) > 0.004],
                               ["a", "u", "w", "n"], heads=["the decision is", "share of the draws", "share weighted by the benchmarks",
                                                             "share of the draws no benchmark rules out"]))
            if cb.get("assumptions"):
                kids.append(_table([{"a": AS.title(m["assumption"]), "d": f"{m['default']:.4g}", "p": f"{m['prior_mean']:.4g}", "q": f"{m['posterior_mean']:.4g}",
                                     "s": f"{m['shift']:+.2f}", "k": f"{100 * m['shrink']:.0f}%",
                                     "t": ", ".join(e["benchmark"].replace("_", " ") for e in m["informed_by"][:3])} for m in cb["assumptions"][:12]],
                                   ["a", "d", "p", "q", "s", "k", "t"],
                                   heads=["assumption the benchmarks bear on", "value on this run", "mean of the draws", "weighted mean",
                                          "shift, sd of the draws", "spread kept", "through"]))
        kids.append(html.Div(s3, className="gap-note"))
        kids.append(html.Div("The evidence base", className="feed-cap"))
        kids.append(_table([{"b": r["title"], "q": vb["sources"][r["id"]]["mapping"], "s": "; ".join(x["cite"] for x in vb["sources"][r["id"]]["sources"]),
                             "c": vb["sources"][r["id"]]["caveat"]} for r in vb["rows"]],
                           ["b", "q", "s", "c"], heads=["benchmark", "the model quantity it is compared with", "source", "caveat"], cls="data specs"))
        if vb.get("not_used"):
            kids.append(_table([{"e": x["evidence"], "m": x["bears_on"].replace("_", " "), "w": x["why_not"]} for x in vb["not_used"]],
                               ["e", "m", "w"], heads=["examined and set aside", "bears on", "why it is not used"], cls="data specs"))
    kids.append(html.Div("Events and mechanisms: validation against an observed event, and the mechanism register", className="gap-name"))
    if evs:
        for x in evs:
            es = x["event_study"]; cm = x.get("comparison")
            kids.append(html.Div(f"{x['dataset']} ({x['classification']}): abnormal return {es['car'] * 100:+.1f}% (standard error {es['se_car'] * 100:.1f}%) over "
                                 f"months 0 to 5 from {es.get('event_month', 'the event month')}, a level effect of {es['early_reaction'] * 100:+.1f}%; "
                                 f"{es['model']}, estimated on the {es['n_est']} monthly returns before the event month. "
                                 + (f"Mapped to {lab(cm['policy'])} at the {x['level']} level: the model's early reaction is {cm['model_mean'] * 100:+.1f}% "
                                    f"({cm['model_lo'] * 100:+.1f}% to {cm['model_hi'] * 100:+.1f}%), and the observation is "
                                    f"{'inside' if cm['within_band'] else 'outside'} that band." if cm else
                                    "Not mapped to an instrument, so it is reported and not compared."), className="feed-cap"))
            kids.append(_table([{"i": pols[r["policy"]]["label"], "m": f"{r['model_early_reaction'] * 100:+.1f}%",
                                 "ci": f"[{r['lo'] * 100:+.1f}%, {r['hi'] * 100:+.1f}%]"} for r in x["rows"]],
                               ["i", "m", "ci"], heads=["instrument", f"model early reaction ({x['level']})", "outcomes 10th to 90th"]))
        if val.get("coverage"):
            kids.append(html.Div(_cap(val["coverage"]["statement"]) + ".", className="gap-note strong"))
    else:
        kids.append(html.Div("No price series was uploaded on this run. In DAT, upload a monthly price series with an event month and the "
                             "instrument it is an analogue of: the abnormal return is compared with the model's predictive distribution of the "
                             "early market reaction.", className="await"))
    mech = arte.get("mechanisms") or []
    if mech:
        n_conf = sum(1 for m in mech if m.get("confronted"))
        kids.append(html.Div(f"The Lab is synthetic. No mechanism is estimated from data; {n_conf} of its {len(mech)} causal mechanisms were confronted "
                             f"with a published benchmark on this run, and the figures stay conditional on the model and its declared assumptions. "
                             f"Common random numbers make the comparison between alternatives precise inside the model; they do not make the model true.",
                             className="gap-note strong"))
        kids.append(_table([{"m": x["mechanism"], "st": x["status"], "ev": (x.get("evidence") or "no benchmark"),
                             "id": x["identifying_assumption"], "src": x["source"], "t": x["validation_test"]} for x in mech],
                           ["m", "st", "ev", "id", "src", "t"],
                           heads=["mechanism", "status", "benchmarks on this run", "identifying assumption", "what it rests on", "what would test it"],
                           cls="data specs"))
    return kids


def _pol_static():
    lib = all_library()
    rows = [{"n": p["label"], "s": "coordinated" if p["scope"] == "coordinated" else "domestic", "d": describe_policy(p), "note": p["note"]} for p in lib]
    return [
        _howto("The instrument library, and your own instruments.",
               ["Every built in instrument is a bounded JSON document; the table shows what each does. Name instruments in the "
                "policy question to compare them, or leave it to the default battery.",
                "To define your own, edit the document on the left: scope, phase in, threshold, costs, mandated safety share, "
                "evaluation catch rate, delays, liability, transparency, enforcement, controls. Every value is clamped to the "
                "bounds on the right and clamping is reported.",
                "Click Validate and store. The instrument joins every later plan while it is enabled, with its author and hash "
                "in the battery hash and the ledger.",
                "Assumption overrides (bottom) apply to the next plan: any value judgement in the assumptions table, within bounds."],
               "Nothing simulates until the battery is approved at Gate 1." if OPEN_GATES else
               "Nothing simulates until a named approver signs the battery off at Gate 1."),
        html.Div("Built in instruments", className="feed-cap"),
        _table(rows, ["n", "s", "d", "note"], heads=["instrument", "scope", "what it does", "note"]),
        html.Div([
            html.Div([html.Label("Instrument document (JSON)", htmlFor="pol-json"),
                      dcc.Textarea(id="pol-json", value=json.dumps(policy_template(), indent=1), rows=16, spellCheck=False, maxLength=8000)],
                     style={"flex": "2"}),
            html.Div([html.Label("Bounds"),
                      html.Div([html.Div(f"{k}: {v[0]} to {v[1]}", className="mono") for k, v in POLICY_BOUNDS.items()], className="gap-note", style={"columns": "2"}),
                      html.Div("scope: home or coordinated; applies_to: all or a list of " + ", ".join(SECTORS) + "; flags: safe_harbour, "
                               "insurance_mandate, incident_reporting, open_weights_restriction, sandbox_small_firms. "
                               f"At most {MAX_POLICIES} stored instruments.", className="gap-note")], style={"flex": "1", "paddingLeft": "12px"})],
                 style={"display": "flex", "gap": "8px"}),
        html.Div([html.Button("Validate and store", id="pol-add", className="act gate"),
                  html.Button("Reset to template", id="pol-template", className="act")], className="btn-row"),
        html.Div(id="pol-result"),
        html.Div([html.Label("Stored instrument", htmlFor="pol-pick"),
                  dcc.RadioItems(id="pol-pick", options=[], inline=True, className="seg", inputClassName="seg-in", labelClassName="seg-lab"),
                  html.Div([html.Button("Enable", id="pol-on", className="act"), html.Button("Disable", id="pol-off", className="act"),
                            html.Button("Remove", id="pol-remove", className="act refuse")], className="btn-row")]),
        html.Div(id="pol-list"),
        html.Div("Assumption overrides for the next plan (JSON object of assumption: value)", className="feed-cap"),
        html.Div([dcc.Textarea(id="asm-json", value="{}", rows=4, spellCheck=False, maxLength=6000, style={"flex": "2"}),
                  html.Div([html.Button("Apply overrides", id="asm-apply", className="act"), html.Div(id="asm-result")], style={"flex": "1", "paddingLeft": "12px"})],
                 style={"display": "flex", "gap": "8px"}),
        html.Div(_table([{"a": _nice(k), "v": v[0], "lo": v[1], "hi": v[2], "u": v[3], "m": v[4]} for k, v in AS.SPEC.items()],
                        ["a", "v", "lo", "hi", "u", "m"], heads=["assumption", "default", "low", "high", "unit", "meaning"]), className="scroll-table"),
    ]


def _pol_list():
    items = POLICIES.list()
    if not items:
        return html.Div("No stored instruments. The plan uses the library.", className="await")
    rows = [{"n": x["policy"]["label"], "e": "enabled" if x.get("enabled", True) else "disabled", "d": describe_policy(x["policy"]),
             "a": x["author"], "w": x["added"][:16], "h": x["sha256"][:12]} for x in items]
    return [html.Div(f"{len(items)} stored instrument{'s' if len(items) != 1 else ''}", className="feed-cap"),
            _table(rows, ["n", "e", "d", "a", "w", "h"], heads=["instrument", "state", "what it does", "author", "added", "sha256"])]


def _agt_static():
    return [
        _howto("The firm archetypes, and your own.",
               ["The default economy is eight archetypes of the AI value chain (below). None is a real company.",
                "To replace it, define at least two firms: revenue, margin, growth, R&D share, capability, safety practice, reach, the share "
                "of revenue in the regulated scope, mobility offshore, safety culture, beta, volatility and multiples. Every value is bounded.",
                "A firm can be calibrated from a price series uploaded in DAT: map the dataset to the firm's name and its volatility and "
                "beta replace the template's in the next plan.",
                "Click Validate and store; enabled templates replace the default economy in the next plan when there are at least two."],
               "The engine is agnostic to names: a mapping onto real companies is the authority's, and the briefing says so."),
        html.Div("Default economy", className="feed-cap"),
        _table([{"f": f["label"], "s": _cap(f["sector"]), "r": _fmt(f["revenue"], 0), "m": _pct(f["margin"]), "g": _pct(f["growth"]), "c": _fmt(f["capability"], 2),
                 "sa": _fmt(f["safety"], 2), "re": _fmt(f["reach"], 2), "sc": _pct(f["scope_share"]), "mo": _fmt(f["mobility"], 1), "cu": _fmt(f["culture"], 2),
                 "b": _fmt(f["beta"], 1), "v": _pct(f["idio_vol"]), "pe": _fmt(f["pe"], 0)} for f in default_firms()],
               ["f", "s", "r", "m", "g", "c", "sa", "re", "sc", "mo", "cu", "b", "v", "pe"],
               heads=["firm", "sector", "revenue $bn", "margin", "growth", "capability", "safety", "reach", "in scope", "mobility", "culture", "beta", "vol", "PE"]),
        html.Div([
            html.Div([html.Label("Firm template (JSON)", htmlFor="agt-json"),
                      dcc.Textarea(id="agt-json", value=json.dumps(firm_template(), indent=1), rows=14, spellCheck=False, maxLength=6000)], style={"flex": "2"}),
            html.Div([html.Label("Bounds"),
                      html.Div([html.Div(f"{k}: {v[0]} to {v[1]}", className="mono") for k, v in FIRM_BOUNDS.items()], className="gap-note", style={"columns": "2"}),
                      html.Div("sector: " + ", ".join(SECTORS) + f"; flags open_weights, small. At most {MAX_FIRMS} stored templates.", className="gap-note")],
                     style={"flex": "1", "paddingLeft": "12px"})], style={"display": "flex", "gap": "8px"}),
        html.Div([html.Button("Validate and store", id="agt-add", className="act gate"),
                  html.Button("Reset to template", id="agt-template", className="act")], className="btn-row"),
        html.Div(id="agt-result"),
        html.Div([html.Label("Stored template", htmlFor="agt-pick"),
                  dcc.RadioItems(id="agt-pick", options=[], inline=True, className="seg", inputClassName="seg-in", labelClassName="seg-lab"),
                  html.Div([html.Button("Enable", id="agt-on", className="act"), html.Button("Disable", id="agt-off", className="act"),
                            html.Button("Remove", id="agt-remove", className="act refuse")], className="btn-row")]),
        html.Div(id="agt-list"),
    ]


def _agt_list():
    items = FIRMS.list()
    if not items:
        return html.Div("No stored firm templates. The next plan uses the default economy.", className="await")
    en = sum(1 for x in items if x.get("enabled", True))
    rows = [{"f": x["firm"]["label"], "e": "enabled" if x.get("enabled", True) else "disabled", "s": _cap(x["firm"]["sector"]),
             "r": _fmt(x["firm"]["revenue"], 0), "c": _fmt(x["firm"]["capability"], 2), "a": x["author"], "w": x["added"][:16], "h": x["sha256"][:12]} for x in items]
    return [html.Div(f"{len(items)} stored template{'s' if len(items) != 1 else ''}, {en} enabled; "
                     + ("they replace the default economy in the next plan" if en >= 2 else "at least two enabled templates replace the default economy"),
                     className="feed-cap"),
            _table(rows, ["f", "e", "s", "r", "c", "a", "w", "h"], heads=["firm", "state", "sector", "revenue $bn", "capability", "author", "added", "sha256"])]


def _dat_static():
    return [
        _howto("Bring a price series into the Lab, through quarantine.",
               ["Choose the classification: public, synthetic, licensed or pseudonymised. It decides what may leave the run directory.",
                "Drop a CSV or JSON file with a date column and a price column (optionally a market column for a beta). Daily or monthly; "
                "the Lab keeps the last observation of each month.",
                "Optionally give an event month (YYYY-MM, a past regulatory announcement): the abnormal return over the six months from "
                "it is estimated on the 24 monthly returns before it (a shorter history is refused, not shortened).",
                "Optionally name the instrument the event is an analogue of: assurance then compares the observation with the model's "
                "predictive distribution of the early reaction for that instrument. Without it the event is reported and not compared.",
                "Optionally map the series to a firm archetype by name: its volatility and beta calibrate that firm in the next plan, "
                "estimated on the returns before the event month so that the event is held out.",
                "Every file passes one quarantine: size and type limits, a schema check, ISO dates, positive finite prices, a monthly "
                "series without gaps, a formula injection check, a personal identifier scan that refuses rather than redacts, and a hash "
                "for the ledger. Rows never enter the briefing or the evidence pack."],
               "sample_data/analogue_event_study.csv is a synthetic example with an event in 2024-06. One event illustrates the comparison; "
               "eight or more mapped events are needed before the coverage of the model's band can be tested."),
        html.Div([
            html.Div([html.Label("Classification", htmlFor="dat-class"),
                      dcc.RadioItems(id="dat-class", value="public", inline=True, className="seg", inputClassName="seg-in", labelClassName="seg-lab",
                                     options=[{"label": f"{k}: {v['note']}", "value": k} for k, v in CLASSIFICATIONS.items() if v["allowed"]])], className="dat-col"),
        ], className="dat-row"),
        html.Div([
            html.Div([html.Label("Event month (optional)", htmlFor="dat-event"),
                      dcc.Input(id="dat-event", type="text", placeholder="YYYY-MM", maxLength=7)], className="dat-col dat-narrow"),
            html.Div([html.Label("Maps to firm (optional)", htmlFor="dat-maps"),
                      dcc.Input(id="dat-maps", type="text", placeholder="for example frontier_lab_closed", maxLength=60)], className="dat-col"),
            html.Div([html.Label("Analogue of instrument (optional)", htmlFor="dat-analogue"),
                      dcc.Input(id="dat-analogue", type="text", placeholder="for example frontier_licensing", maxLength=60)], className="dat-col"),
            html.Div([html.Label("Upload CSV or JSON"),
                      dcc.Upload(id="dat-upload", multiple=False, max_size=CFG.upload_max_mb * 1024 * 1024,
                                 children=html.Div(["drop a file here or ", html.B("browse")]), className="dat-upload")], className="dat-col")], className="dat-row"),
        html.Div(id="dat-result"),
        html.Div(id="dat-list"),
    ]


def _dat_list():
    with LOCK:
        dsets = list(S["datasets"])
    if not dsets:
        return html.Div("No datasets waiting. The next plan runs on the synthetic economy alone.", className="await")
    rows = [{"n": d["name"], "c": d["classification"], "m": d["stats"]["n_months"], "v": _pct(d["stats"].get("annual_vol")),
             "b": _fmt(d["stats"].get("beta"), 2) if d["stats"].get("beta") is not None else "n/a", "map": d.get("maps_to") or "",
             "ev": (f"{d['event_study']['event_month']}: {d['event_study']['car'] * 100:+.1f}% (s.e. {d['event_study']['se_car'] * 100:.1f}%)"
                    if d.get("event_study") else d.get("event_note", "")),
             "an": d.get("analogue_of") or "",
             "p": "yes" if d.get("packable") else "no", "h": d["sha256"][:12]} for d in dsets]
    return [html.Div(f"{len(dsets)} dataset{'s' if len(dsets) != 1 else ''} waiting for the next plan", className="feed-cap"),
            _table(rows, ["n", "c", "m", "v", "b", "map", "ev", "an", "p", "h"],
                   heads=["dataset", "classification", "months", "annual vol", "beta", "maps to", "abnormal return, months 0 to 5", "analogue of",
                          "in pack", "sha256"])]


def _sec_body():
    with LOCK:
        p = S["posture"]; dsets = list(S["datasets"])
    if p is None:
        p = posture(CFG, datasets=[{"name": x["name"], "classification": x["classification"]} for x in dsets])
        with LOCK:
            S["posture"] = p
    chips = [html.Span(f"{p['n_pass']} pass", className="chip ok"), html.Span(f"{p['n_warn']} warn", className="chip warn" if p["n_warn"] else "chip"),
             html.Span(f"{p['n_fail']} fail", className="chip bad" if p["n_fail"] else "chip")]
    _cls = {"pass": "ok", "warn": "warn", "fail": "bad"}
    rows = [{"s": html.Span(i["status"], className="chip " + _cls.get(i["status"], "")), "c": i["control"], "d": i["detail"], "ch": "ch. " + i["sev3"]} for i in p["items"]]
    return [html.Div(chips + [html.Button("Re-check", id="sec-recheck", className="act sec-btn")], className="chip-row"),
            html.Div("Each control names the chapter of Security Engineering (Anderson, 3rd edition) whose argument it applies. "
                     "A failing control blocks release; a warning is recorded in the artefacts.", className="gap-note"),
            _table(rows, ["s", "c", "d", "ch"], heads=["status", "control", "detail", "chapter"])]


def _run_status():
    st = S["stage"]
    kids = []
    if S["err"]:
        kids.append(html.Div(f"Error: {S['err']}", className="seal"))
    if S["run_id"]:
        kids.append(html.Div(f"Run {S['run_id']}, prepared by {S['preparer']}" + (f" ({S['preparer_role']})" if S["preparer_role"] else "")
                             + f", started {S['started']}", className="feed-cap"))
    if st == "idle":
        kids.append(html.Div("A policy question is read into a battery of candidate instruments. Gate 1 runs the battery and Gate 2 "
                             "releases the briefing; either can be refused with a reason. This public demonstration takes no sign off "
                             "identities; inside an authority a named preparer and a named approver on the register take the gates, with "
                             "four eyes. Every step is chained into a signed ledger." if OPEN_GATES else
                             "A policy question is read into a battery of candidate instruments. A named approver on the register signs "
                             "the battery off at Gate 1 before anything simulates, and the briefing at Gate 2 before it leaves. Either gate "
                             "can be refused with reasons. Every step is chained into a signed ledger.", className="await"))
    if st == "planning":
        kids.append(html.Div("Reading the question and planning the battery.", className="seal arming"))
    bat = S["battery"]
    if bat and st != "planning":
        kids.append(html.Div(f"Battery: {len(bat['policies'])} alternatives, {bat['paths']} paths growing to at most {bat.get('max_paths', bat['paths'])} "
                             f"until the precision targets are met, {bat['horizon']} months, hash {bat['hash'][:16]}; "
                             f"{S['plan_text']}" + (f"; firms: {bat.get('firms_origin')}" if bat.get("firms_origin") else "")
                             + (("; " + "; ".join(bat["calibration_notes"])) if bat.get("calibration_notes") else ""), className="feed-cap"))
        kids.append(_table([{"i": p["label"], "s": "coordinated" if p["scope"] == "coordinated" else "domestic", "ph": p["phase_in"], "d": describe_policy(p)}
                            for p in bat["policies"]], ["i", "s", "ph", "d"], heads=["instrument", "scope", "phase in", "what it does"], cls="data specs"))
    for gname, key in (("Gate 1", "gate1"), ("Gate 2", "gate2")):
        a = S["approvals"].get(key)
        if a:
            cls = "seal approved" if a["decision"] == "approved" else "seal refused"
            reg = a.get("register") or {}
            if a.get("open_gate"):
                line = f"{gname} {a['decision']} at {a['ts']} (public demonstration, no sign off identity)"
            else:
                line = (f"{gname} {a['decision']} by {a['actor']}{(' (' + a['role'] + ')') if a.get('role') else ''} at {a['ts']}"
                        + (f"; {reg.get('source')}" if reg.get("dev_mode") else
                           (f"; on the register as {reg.get('function')} at {reg.get('firm')}, reference {reg.get('irn')}" if reg.get("irn") else "")))
            kids.append(html.Div(line + (f". Reason: {a['reason']}" if a.get("reason") else ""), className=cls))
    if st == "halted":
        kids.append(html.Div(f"Emergency stop by {S['stop_actor']}, partial ledger sealed, evidence pack exportable", className="seal"))
    if S["critic"] is not None:
        ok = S["critic"]["ok"]
        failed = [c["check"] for c in S["critic"]["checks"] if not c["ok"]]
        kids.append(html.Div(f"Critic {'passed' if ok else 'failed'}: {S['critic']['n_checks']} checks against the stored paths and the ledger"
                             + (f". Failed: {failed}" if failed else ""), className="verdict " + ("pass" if ok else "fail")))
        if ok and st == "evaluated":
            arte = S["artefacts"]; ev = arte["results"]; fo = _pols(arte)[_focus(arte)]
            kids.append(html.Div(f"{ev['decision']['text']} {fo['label']}: expected net social value {_bn(fo['net_social_value']['mean'])} "
                                 f"(95% confidence interval {_bn(fo['net_social_value']['ci_lo'])} to {_bn(fo['net_social_value']['ci_hi'])}) on "
                                 f"{arte['paths']} paths. The briefing exists as artefacts only; Gate 2 releases it, or refuses it with a recorded reason.",
                                 className="await"))
            pr = ev.get("precision") or {}
            if pr and not pr.get("met", True):
                kids.append(html.Div(f"Short of the precision target at the ceiling of {pr['max_paths']} paths: "
                                     + "; ".join(x["text"] for x in pr["unresolved"]) + ".", className="seal arming"))
    if S["run_id"] and st in ("evaluated", "released", "halted", "rejected", "refused"):
        rid = S["run_id"]
        kids.append(html.Div([
            html.A("artefacts.json", href=f"/run/{rid}/artefacts.json", target="_blank"), "  ",
            html.A("results.json", href=f"/run/{rid}/results.json", target="_blank"), "  ",
            html.A("assurance.json", href=f"/run/{rid}/assurance.json", target="_blank"), "  ",
            html.A("ledger.jsonl", href=f"/run/{rid}/ledger.jsonl", target="_blank"), "  ",
            html.A("evidence pack (zip)", href=f"/run/{rid}/evidence_pack.zip"),
            *(["  ", html.A("printable briefing", href=f"/run/{rid}/briefing.html", target="_blank"),
               "  ", html.A("transparency record (ATRS)", href=f"/run/{rid}/atrs_record.md", target="_blank")] if st == "released" else [])], className="links"))
    if st == "released" and S["briefing"]:
        kids.append(html.Div(dcc.Markdown(S["briefing"]), className="paper"))
    return kids


def _reg_body():
    runs = STORE.index()
    if not runs:
        return html.Div(f"No runs yet. Every planned run gets a directory under {STORE.root} with its own signed ledger.", className="await")
    rows = []
    for m in runs:
        rid = m.get("run_id", "")
        links = html.Span([html.A("artefacts", href=f"/run/{rid}/artefacts.json", target="_blank"), "  ",
                           html.A("ledger", href=f"/run/{rid}/ledger.jsonl", target="_blank"), "  ",
                           html.A("pack", href=f"/run/{rid}/evidence_pack.zip"),
                           *(["  ", html.A("briefing", href=f"/run/{rid}/briefing.html", target="_blank")] if m.get("stage") == "released" else [])])
        rows.append({"run": rid, "created": str(m.get("created", ""))[:19], "stage": m.get("stage"), "preparer": m.get("preparer"),
                     "approver": m.get("approver") or "", "pref": "status quo" if m.get("preferred") == "baseline" else _nice(m.get("preferred") or ""),
                     "gap": _fmt(m.get("decision_gap")),
                     "ws": _pct(m.get("winner_stability")) if m.get("winner_stability") is not None else "", "question": str(m.get("question", ""))[:70], "links": links})
    return [html.Div(f"{len(rows)} runs in {STORE.root}", className="feed-cap"),
            _table(rows, ["run", "created", "stage", "preparer", "approver", "pref", "gap", "ws", "question", "links"],
                   heads=["run", "created (UTC)", "stage", "preparer", "approver", "preferred", "gap", "stability", "question", "files"])]


def _ldg_verify():
    rep = S["ledger_report"]; log = S["log"]
    if log is None:
        return "No run open"
    if rep is None:
        return f"Chain {log.seq} entries, signed, head {log.head[:12]}, replay at evaluation"
    return (f"Chain {rep['entries']} entries, {rep['signed']} signed, head {str(rep['head'])[:12]}, "
            f"{'VERIFIED' if rep['ok'] else 'BROKEN: ' + '; '.join(rep['errors'][:2])}")


# ----------------------------------------------------------------- layout --
def _panel(idx, code, title, body, header_extra=None):
    right = header_extra if header_extra is not None else html.Span("", className="ph-live", id=f"ph-live-{code}")
    return html.Section([
        html.Header([html.Span(str(idx), className="ph-num"), html.Span(code, className="ph-code"), html.Span(title, className="ph-title"), right],
                    className="p-head"),
        html.Div(body, className="p-body", id=f"body-{code}"),
    ], className="panel", id=f"panel-{code}", **{"data-code": code})


def _nws_body():
    return [html.Div([html.Button("Wire", id="nws-wire-btn", className="mode on"),
                      html.Button("Forecast", id="nws-fc-btn", className="mode"),
                      html.Select([html.Option("Live", value="__live__")], id="nws-sel", className="sel"),
                      html.Span(id="nws-read", className="mkt-read")], className="mkt-modes"),
            html.Div(id="nws-feed", className="wire"),
            html.Div(id="nws-forecast", style={"display": "none"})]


def _mkt_body():
    return [html.Div([html.Button("Prices", id="mkt-px-btn", className="mode on"),
                      html.Button("vs status quo", id="mkt-vs-btn", className="mode", disabled=True, title="Index against the status quo, with its band (after the run)"),
                      html.Select([html.Option("Live", value="__live__")], id="mkt-sel", className="sel"),
                      html.Span(id="mkt-read", className="mkt-read")], className="mkt-modes"),
            html.Div(id="mkt-legend", className="legend"),
            html.Div(id="mkt-chart"),
            html.Div(id="mkt-vs", style={"display": "none"})]


def _run_static():
    header_mode = CFG.auth_mode == "header"
    if OPEN_GATES and not header_mode:
        ident = [html.Div("Gates: single clicks, no sign off identities (public demonstration). Inside an authority a named preparer and a "
                          "named approver on the register take them, with four eyes.", className="gap-note")]
    elif header_mode:
        ident = [html.Label("Acting identity"), html.Div(id="ident-chip", className="ident")]
    else:
        ident = [
        html.Label("Prepared by", htmlFor="who"),
        dcc.Input(id="who", type="text", placeholder="analyst preparing the battery", autoComplete="off", maxLength=80),
        html.Label("Preparer's function (required)", htmlFor="who-role"),
        dcc.Input(id="who-role", type="text", placeholder=("for example certified function, or Developer1 in dev mode" if CFG.dev_mode else "for example certified function or team"),
                  autoComplete="off", maxLength=80),
        html.Label("Approver at the gates", htmlFor="approver"),
        dcc.Input(id="approver", type="text", placeholder="named approver (must differ from preparer)" if CFG.four_eyes else "named approver", autoComplete="off", maxLength=80),
        html.Label("Approver's function (SMF or certified role; required)", htmlFor="approver-role"),
        dcc.Input(id="approver-role", type="text", placeholder=("for example SMF24, or Developer2 in dev mode" if CFG.dev_mode else "for example SMF24 or certified function"),
                  autoComplete="off", maxLength=80)]
    hidden = [] if not (header_mode or OPEN_GATES) else [
        dcc.Input(id="who", type="hidden", value=""), dcc.Input(id="approver", type="hidden", value=""),
        dcc.Input(id="approver-role", type="hidden", value=""), dcc.Input(id="who-role", type="hidden", value="")]
    return [
        html.Label("Policy question", htmlFor="q"),
        dcc.Textarea(id="q", value=DEFAULT_QUESTION, rows=3, spellCheck=False, maxLength=600,
                     title='Name instruments, a horizon and constraints. Add "seed 11" to repeat a run on other random numbers: an independent replication.'),
        *ident, *hidden,
        html.Label("Reason (required to refuse a gate; recorded in the ledger)", htmlFor="reason"),
        dcc.Textarea(id="reason", rows=2, spellCheck=False, maxLength=400, placeholder="why the battery or the briefing is refused"),
        html.Div([html.Button("Plan", id="plan", className="act", title="Read the question and plan the battery"),
                  html.Button("Stop", id="stop", className="act stopbtn", disabled=True, title="Emergency stop: halts the run now"),
                  html.Button("New run", id="newrun", className="act", title="Clear the terminal for a fresh run; datasets, instruments and firms are kept")],
                 className="btn-row"),
        html.Div([html.Button("Gate 1: approve battery", id="g1a", className="act gate", disabled=True), html.Button("Refuse", id="g1r", className="act refuse", disabled=True)], className="btn-row"),
        html.Div([html.Button("Gate 2: release briefing", id="g2a", className="act gate", disabled=True), html.Button("Refuse", id="g2r", className="act refuse", disabled=True)], className="btn-row"),
        html.Div(id="run-status"),
    ]


RAIL = [("plan", "Plan"), ("gate1", "Gate 1"), ("simulate", "Simulate"), ("markets", "Markets"), ("welfare", "Welfare"),
        ("assurance", "Assurance"), ("critic", "Critic"), ("gate2", "Gate 2"), ("released", "Released")]
FKEYS = [("1", "NWS", "News wire"), ("2", "MKT", "Technology equities"), ("3", "SAF", "Safety forecast"), ("4", "PNL", "Industry gain or loss"),
         ("5", "WLF", "Social ledger"), ("6", "GAP", "Decision gap"), ("7", "LDG", "Rationale ledger"), ("8", "RUN", "Run control"),
         ("9", "ASK", "Run oracle"), ("0", "POL", "Policy library"), ("K", "RSK", "Assurance"), ("D", "DAT", "Data desk"),
         ("A", "AGT", "Firm workshop"), ("S", "SEC", "Security posture"), ("R", "REG", "Run registry")]


def _rail():
    with LOCK:
        stage, step, critic = S["stage"], S["step"], S["critic"]
    order = [k for k, _ in RAIL]
    cur = order.index(step) if step in order else 0
    out = []
    for i, (key, label) in enumerate(RAIL):
        cls = "rail-step"
        if stage == "idle":
            pass
        elif stage == "released":
            cls += " ok" if key == "released" else " done"
        elif i < cur:
            cls += " done"
        elif i == cur:
            if stage in ("error", "halted", "rejected", "refused"):
                cls += " fail"
            elif stage == "evaluated" and key == "critic" and critic and not critic["ok"]:
                cls += " fail"
            else:
                cls += " active"
        out.append(html.Span(label, className=cls, **{"data-step": key}))
    return out


FRONT_INDEX = [
    ("NWS", "news wire: the headlines four media agents write from the simulation, live, and the forecast by quarter"),
    ("MKT", "technology equities: every firm's price under the instrument being simulated, and the index against the status quo"),
    ("SAF", "safety forecast: incidents, the probability of a major and of a catastrophic one, harm, safety practice, trust"),
    ("PNL", "industry gain or loss: each firm's value change against the status quo, with its probability of gaining"),
    ("WLF", "social ledger: what the instrument buys and costs, as a waterfall, and who gains and who pays"),
    ("GAP", "decision gap: the instruments ranked by how they look early against how they score over the horizon"),
    ("LDG", "rationale ledger: the signed hash chain, entry by entry, with replay"),
    ("RUN", "run control: the question, identities, gates with refusal, emergency stop, the briefing"),
    ("ASK", "run oracle: grounded answers computed from the artefacts"),
    ("POL", "policy library: the instruments, your own, and the assumption overrides"),
    ("RSK", "assurance: Monte Carlo error, the screen of every assumption, the joint draw, variants, red team, validation"),
    ("DAT", "data desk: price series through quarantine, for calibration and event studies"),
    ("AGT", "firm workshop: the archetypes and your own templates"),
    ("SEC", "security posture: the deployment checked against the controls"),
    ("REG", "run registry: every past run, its status and its evidence pack"),
]

app.layout = html.Div([
    dcc.Interval(id="iv-fast", interval=500),
    dcc.Interval(id="iv-slow", interval=1000),
    dcc.Store(id="cursor", data={"seq": 0}),
    dcc.Store(id="rev-store", data=-1),
    dcc.Store(id="stream"), dcc.Store(id="sink"), dcc.Store(id="sink2"), dcc.Store(id="sink3"), dcc.Store(id="sink4"), dcc.Store(id="sink5"),

    html.Div([
        html.Div([html.Span(className="brand-glyph"), html.Span("PSL", className="brand-code"), html.Span("Policy Scenario Lab", className="brand-name")], className="brand"),
        html.Div([html.Span("›", className="cmd-prompt"),
                  dcc.Input(id="cmd", type="text", placeholder="function code", autoComplete="off", debounce=False),
                  html.Span("GO", className="go-key", title="Enter"), html.Span(id="cmd-msg")], className="cmdline"),
        html.Span(id="phase-line", children="Awaiting run control"),
        html.Span([html.Span(id="run-chip", className="run-chip"), html.Span("IDLE", id="live-stage", className="st-idle"),
                   html.Span("--:--:--", id="clock")], className="top-right"),
    ], className="top-bar"),
    html.Div(_rail(), id="rail", className="rail"),

    html.Main([
        html.Div([
            _panel(1, "NWS", "News wire", _nws_body(), header_extra=html.Span(id="nws-live", className="ph-live")),
            html.Div(className="gutter gutter-v", id="gut-v-1", **{"data-kind": "v"}),
            _panel(2, "MKT", "Technology equities", _mkt_body(), header_extra=html.Span(id="mkt-live", className="ph-live")),
        ], className="trow", id="trow-1"),
        html.Div(className="gutter gutter-h", id="gut-h-1", **{"data-kind": "h"}),
        html.Div([
            _panel(3, "SAF", "Safety forecast", html.Div(id="saf-body")),
            html.Div(className="gutter gutter-v", id="gut-v-2", **{"data-kind": "v"}),
            _panel(4, "PNL", "Industry gain or loss", html.Div(id="pnl-body")),
            html.Div(className="gutter gutter-v", id="gut-v-3", **{"data-kind": "v"}),
            _panel(5, "WLF", "Social ledger", html.Div(id="wlf-body")),
            html.Div(className="gutter gutter-v", id="gut-v-4", **{"data-kind": "v"}),
            _panel(6, "GAP", "Decision gap", html.Div(id="gap-body")),
        ], className="trow", id="trow-2"),
        html.Div(className="gutter gutter-h", id="gut-h-2", **{"data-kind": "h"}),
        html.Div([
            _panel(7, "LDG", "Rationale ledger", [html.Div(id="ldg-verify", className="feed-cap"), html.Div(id="ldg-feed", className="feed")]),
            html.Div(className="gutter gutter-v", id="gut-v-5", **{"data-kind": "v"}),
            _panel(8, "RUN", "Run control, gates and briefing", _run_static()),
        ], className="trow", id="trow-3"),
        _panel(0, "POL", "Policy library: instruments, your own, assumptions", _pol_static()),
        _panel("K", "RSK", "Assurance: precision, screen, joint draw, variants, red team, validation", html.Div(id="rsk-body")),
        _panel("D", "DAT", "Data desk: price series through quarantine", _dat_static()),
        _panel("A", "AGT", "Firm workshop: archetypes and templates", _agt_static()),
        _panel("S", "SEC", "Security posture", html.Div(id="sec-body")),
        _panel("R", "REG", "Run registry", html.Div(id="reg-body")),
    ], className="term-grid", id="grid"),

    html.Footer([
        html.Div([html.Button([html.I(k), c], className="fkey", title=t, **{"data-code": c}) for k, c, t in FKEYS], className="fkeys"),
        html.Div(html.Div(id="ticker-text", children=(
            ("PSL terminal ready. Type a policy question and plan the battery. " if OPEN_GATES else
             "PSL terminal ready. Type a policy question, name a preparer and an approver, and plan the battery. ")
            + "Nothing simulates before Gate 1 and nothing is released before Gate 2. Every step is chained into a signed ledger.")),
                 className="tape-wrap")], className="ticker"),

    html.Div([
        html.Div([html.Span("9", className="ph-num"), html.Span("ASK", className="ph-code"), html.Span("Run oracle", className="ph-title"),
                  html.Span("answers are computed from this run's artefacts on the server; a model, when configured, only phrases them", className="ch-meta"),
                  html.Span(id="ch-brain", className="ch-meta ch-brain"), html.Button("Grid (Esc)", id="ch-back")], id="ch-head"),
        html.Div([
            html.Div([html.Div(id="ch-log"),
                      html.Div([dcc.Input(id="ch-in", type="text", autoComplete="off", maxLength=600,
                                          placeholder="ask which alternative to choose and how sure, what it costs, who pays, a firm's stock, "
                                                      "an assumption, the joint draw, robustness, validation, the red team"),
                                html.Button("Send ⏎", id="ch-send")], id="ch-inrow")], id="ch-left"),
            html.Div([html.H4("Sources used"), html.Div(id="ch-src")], id="ch-right")], id="ch-body")], id="chatpage"),

    html.Div(html.Div([
        html.Pre(["PSL", html.Span("▌", className="blink"), html.Span("Policy Scenario Lab", className="fp-name")]),
        html.P("An agent based laboratory for AI regulation: candidate instruments and the status quo run against the same synthetic AI "
               "economy, and are scored on the harm they prevent against the economic and social cost they impose, with the industry's gain or "
               "loss, the news to expect and the market reaction beside them.", className="sub"),
        html.P("Scenario evaluations conditional on a declared model and declared assumptions, with their uncertainty shown; not forecasts "
               "validated against data. From the team behind the Herding Scenario Lab. For policy, supervision and impact assessment teams.",
               className="sub2"),
        html.Div([html.Div([html.Span(c, className="tag"), html.Span(t, className="desc"),
                            html.Span({"ASK": "9", "POL": "0", "RSK": "K", "REG": "R", "DAT": "D", "SEC": "S", "AGT": "A"}.get(c, str(i + 1)), className="st")],
                           className="slot", **{"data-code": c}) for i, (c, t) in enumerate(FRONT_INDEX)], id="front-index"),
        html.Div([html.Button("Enter ⏎", id="fenter"), html.Button("Start a run", id="frun")], className="row"),
        html.P(["Type a code and press ", html.Code("GO"), " to open a page, or a digit ", html.Code("0 to 9"), " or ", html.Code("K D A S R"), ". ",
                html.Code("Esc"), " restores the grid and ", html.Code("FRONT"), " reopens this page."], className="duck"),
        html.P(f"Build {BUILD}   profile {CFG.profile}   auth {CFG.auth_mode}   gates {CFG.gates}   four eyes {'on' if CFG.four_eyes else 'off'}   "
               f"register {'on' if CFG.register_path else 'off'}   dev mode {'on' if CFG.dev_mode else 'off'}   model {'on' if CFG.llm_enabled else 'off'}   "
               f"ledger key {'configured' if not CFG.ephemeral_secret else 'ephemeral (set PSL_SECRET)'}", className="duck build")],
        className="inner"), id="front"),
], id="root")


# -------------------------------------------------------------- callbacks --
@app.callback(Output("stream", "data"), Output("cursor", "data"), Input("iv-fast", "n_intervals"), State("cursor", "data"), prevent_initial_call=True)
def _poll(_, cur):
    cur = cur or {"seq": 0}
    since = cur.get("seq", 0)
    with LOCK:
        payload = {"seq": S["seq"], "stage": S["stage"], "phase": S["phase"], "run_id": S["run_id"], "labels": S["labels"],
                   "policy": S["policy_current"],
                   "pol_labels": {p["name"]: p["label"] for p in S["battery"]["policies"]} if S["battery"] else {},
                   "ticks": [t for q, t in S["ticks"] if q > since],
                   "heads": [h for q, h in S["heads"] if q > since],
                   "alerts": [a for q, a in S["alerts"] if q > since],
                   "ledger": [r for q, r in S["ledger_rows"] if q > since],
                   "done": S["done"]}
        if S["artefacts"] and not cur.get("evaluated_for") == S["run_id"]:
            ev = S["artefacts"]["results"]
            payload["evaluated"] = {"preferred": _focus(S["artefacts"]),
                                    "index": {r["policy"]: {"mean": r["market"]["index_mean"], "lo": r["market"]["index_lo"], "hi": r["market"]["index_hi"],
                                                            "base": r["market"]["index_base_mean"], "label": r["label"],
                                                            "rel_mean": r["market"].get("rel_mean"), "rel_lo": r["market"].get("rel_lo"),
                                                            "rel_hi": r["market"].get("rel_hi"),
                                                            "early": r["market"]["early_reaction"]["mean"], "end": r["market"]["end_reaction"]["mean"]}
                                              for r in ev["policies"] if r["policy"] != "baseline"}}
            cur = dict(cur, evaluated_for=S["run_id"])
        if S["run_id"] is None:
            cur = dict(cur, evaluated_for=None)
    return payload, dict(cur, seq=payload["seq"])


app.clientside_callback(ClientsideFunction(namespace="psl", function_name="onStream"), Output("sink", "data"), Input("stream", "data"), prevent_initial_call=True)

_LAST_RENDER = {"t": 0.0}


@app.callback(Output("run-status", "children"), Output("plan", "disabled"), Output("stop", "disabled"),
              Output("g1a", "disabled"), Output("g1r", "disabled"), Output("g2a", "disabled"), Output("g2r", "disabled"),
              Output("saf-body", "children"), Output("pnl-body", "children"), Output("wlf-body", "children"), Output("gap-body", "children"),
              Output("nws-forecast", "children"), Output("rsk-body", "children"), Output("dat-list", "children"), Output("sec-body", "children"),
              Output("reg-body", "children"), Output("ldg-verify", "children"), Output("mkt-vs-btn", "disabled"), Output("run-chip", "children"),
              Output("rail", "children"), Output("rev-store", "data"),
              Input("iv-slow", "n_intervals"), State("rev-store", "data"))
def _render(_, last_rev):
    with LOCK:
        rev, st, busy, critic, rid, arte = S["rev"], S["stage"], S["busy"], S["critic"], S["run_id"], S["artefacts"]
    if rev == last_rev:
        raise PreventUpdate
    now = time.time()
    if busy and now - _LAST_RENDER["t"] < 3.0:
        raise PreventUpdate
    _LAST_RENDER["t"] = now
    plan_off = st in ("planning", "running") or busy
    stop_off = st not in ("planning", "running")
    g1_off = st != "planned"
    g2_off = not (st == "evaluated" and critic and critic["ok"])
    g2r_off = st != "evaluated"
    chip = f"run {rid}" if rid else ""
    return (_run_status(), plan_off, stop_off, g1_off, g1_off, g2_off, g2r_off,
            _saf_body(), _pnl_body(), _wlf_body(), _gap_body(), _nws_forecast(), _sectioned(_rsk_body()), _dat_list(), _sec_body(),
            _reg_body(), _ldg_verify(), arte is None, chip, _rail(), rev)


@app.callback(Output("sink5", "data"), Input("pnl-pick", "value"), Input("wlf-pick", "value"), Input("nws-pick", "value"), prevent_initial_call=True)
def _picks(pnl, wlf, nws):
    trig = ctx.triggered_id
    val = {"pnl-pick": pnl, "wlf-pick": wlf, "nws-pick": nws}.get(trig)
    key = {"pnl-pick": "pnl", "wlf-pick": "wlf", "nws-pick": "nws"}.get(trig)
    if not key or not val:
        raise PreventUpdate
    with LOCK:
        if (S["pick"] or {}).get(key) == val:
            raise PreventUpdate
        S["pick"] = dict(S["pick"] or {}, **{key: val})
        S["rev"] += 1
    return no_update


@app.callback(Output("sink2", "data"), Input("plan", "n_clicks"), State("q", "value"), State("who", "value"), State("who-role", "value"), prevent_initial_call=True)
def _plan(n, q, who, who_role):
    if not n:
        raise PreventUpdate
    if not _may("plan"):
        _alert("alert", f"Role {_role()} may not plan; refused"); _bump(); return no_update
    preparer = _actor(who)
    if not preparer:
        _alert("alert", "A named preparer is required before planning" if CFG.auth_mode == "open" else "No identity header: sign in through the proxy")
        _bump(); return no_update
    if OPEN_GATES:
        who_role = "public demonstration"
    if CFG.auth_mode == "open" and not (who_role or "").strip():
        _alert("alert", "The preparer's function is required before planning (for example certified function" + (", or Developer1 in dev mode)" if CFG.dev_mode else ")"))
        _bump(); return no_update
    with LOCK:
        if S["busy"] or S["stage"] in ("planning", "running"):
            raise PreventUpdate
        S["busy"] = True
        S["preparer_role"] = (who_role or "").strip()[:80]
    _bump()
    q = (q or DEFAULT_QUESTION).strip()[:600]
    threading.Thread(target=_worker_plan, args=(q, preparer), daemon=True).start()
    return no_update


def _record_gate(key, gate_name, actor, decision, reason=None, extra=None, role=None):
    ts = utc_now()
    rec = {"actor": actor, "ts": ts, "decision": decision, "role": (role or "").strip()[:80]}
    if reason:
        rec["reason"] = reason
    if OPEN_GATES:
        rec["open_gate"] = True
        extra = dict(extra or {}, open_gate=True)
    verdict = None if OPEN_GATES else REGISTER.check(actor, role)
    if verdict and verdict.get("match"):
        rec["register"] = verdict["match"]
        if not rec["role"]:
            rec["role"] = verdict["match"]["function"][:80]
        extra = dict(extra or {}, register=verdict["match"])
    with LOCK:
        S["approvals"][key] = rec
        rid = S["run_id"]
    S["log"]("gate", actor=actor, gate=gate_name, decision=decision, approver=actor, approver_role=(role or "").strip(), reason=reason, **(extra or {}))
    STORE.write_json(rid, "approvals.json", dict(S["approvals"], preparer=S["preparer"], preparer_role=S.get("preparer_role", "")))
    return rec


@app.callback(Output("sink4", "data"), Input("newrun", "n_clicks"), prevent_initial_call=True)
def _newrun(n):
    if not n:
        raise PreventUpdate

    def work():
        with LOCK:
            running = S["busy"] or S["stage"] in ("planning", "running")
        if running:
            STOP.set()
            for _ in range(120):
                time.sleep(0.25)
                with LOCK:
                    if not (S["busy"] or S["stage"] in ("planning", "running")):
                        break
        with LOCK:
            keep = {"datasets": list(S.get("datasets", [])), "assumption_overrides": dict(S.get("assumption_overrides", {})), "rev": S["rev"] + 1}
            S.update(_fresh_state())
            S.update(keep)
        STOP.clear()
        _alert("info", "New run: the terminal is clear. Type a question and plan the battery." if OPEN_GATES else
               "New run: the terminal is clear. Type a question, name a preparer and an approver and plan the battery.")
        _bump()
    threading.Thread(target=work, daemon=True).start()
    return no_update


@app.callback(Output("sink3", "data"), Input("g1a", "n_clicks"), Input("g1r", "n_clicks"), Input("g2a", "n_clicks"), Input("g2r", "n_clicks"), Input("stop", "n_clicks"),
              State("approver", "value"), State("reason", "value"), State("approver-role", "value"), State("who-role", "value"), prevent_initial_call=True)
def _gates(n1, n2, n3, n4, n5, approver_field, reason, approver_role, who_role):
    trig = ctx.triggered_id
    needed = {"stop": "stop", "g1a": "gate", "g1r": "gate", "g2a": "gate", "g2r": "gate"}.get(trig)
    if needed and not _may(needed):
        _alert("alert", f"Role {_role()} may not {needed}; refused"); return no_update
    with LOCK:
        S["preparer_role"] = (who_role or "").strip()[:80] or S["preparer_role"]
    actor = _actor(approver_field)
    if OPEN_GATES:
        approver_role = OPEN_ROLE
    reason = (reason or "").strip()[:400]
    rid = S["run_id"]
    if trig == "stop":
        with LOCK:
            if S["stage"] not in ("planning", "running"):
                raise PreventUpdate
            S["stop_actor"] = actor or "unnamed"
        STOP.set()
        S["log"]("emergency_stop_requested", actor=actor or "unnamed")
        _alert("alert", f"Emergency stop requested by {actor or 'unnamed'}, halting at the next check")
        _bump(phase="Emergency stop requested, halting")
        return no_update
    ok, why = authorised_approver(actor, approver_role)
    if trig in ("g1a", "g2a") and not ok:
        _alert("alert", f"Gate refused: {why}")
        if S["log"] is not None:
            S["log"]("gate_refused", actor=actor or "unnamed", gate="battery_signoff" if trig == "g1a" else "briefing_release", reason=why)
        _bump(); return no_update
    if trig in ("g1r", "g2r") and (not actor or not reason):
        _alert("alert", "Refusing a gate needs a reason" if OPEN_GATES else "Refusing a gate needs a named approver and a reason"); _bump(); return no_update

    if trig == "g1a":
        with LOCK:
            if S["stage"] != "planned" or S["busy"]:
                raise PreventUpdate
            S["busy"] = True
        _record_gate("gate1", "battery_signoff", actor, "approved", extra={"battery_hash": S["battery_hash"], "n_policies": len(S["battery"]["policies"])}, role=approver_role)
        STORE.update_meta(rid, stage="running", approver=actor)
        _bump(stage="running", step="simulate", phase="Gate 1 approved, battery running")
        _alert("ok", f"Gate 1 approved, battery {S['battery_hash'][:12]} running" if OPEN_GATES else
               f"Gate 1 approved by {actor}, battery {S['battery_hash'][:12]} running")
        threading.Thread(target=_worker_run, daemon=True).start()
    elif trig == "g1r":
        with LOCK:
            if S["stage"] != "planned":
                raise PreventUpdate
        _record_gate("gate1", "battery_signoff", actor, "refused", reason, extra={"battery_hash": S["battery_hash"]}, role=approver_role)
        _bump(stage="rejected", step="gate1", phase="Gate 1 refused, battery not run, plan again")
        STORE.update_meta(rid, stage="rejected", approver=actor, reason=reason)
        STORE.pack(rid)
        _alert("alert", f"Gate 1 refused: {reason}" if OPEN_GATES else f"Gate 1 refused by {actor}: {reason}")
    elif trig == "g2a":
        with LOCK:
            good = S["stage"] == "evaluated" and S["critic"] and S["critic"]["ok"]
            arte = S["artefacts"]; d = S["run_dir"]
        if not good:
            raise PreventUpdate
        approvals = dict(S["approvals"], preparer=S["preparer"], preparer_role=S.get("preparer_role", ""),
                         gate2={"actor": actor, "role": (approver_role or "").strip(), "ts": utc_now(), "decision": "approved",
                                "register": None if OPEN_GATES else (REGISTER.check(actor, approver_role) or {}).get("match"),
                                **({"open_gate": True} if OPEN_GATES else {})})
        text = draft_briefing(arte, approvals, rid)
        used_llm = False
        if CFG.llm_enabled:
            text, used_llm = draft_briefing_llm(arte, CLIENT, text, S["log"])
        critic = critic_check(d, secret=CFG.secret, briefing_text=text)
        if not critic["ok"]:
            _bump(critic=critic, step="critic", phase="Critic rejected the briefing, release refused")
            _alert("alert", "Critic rejected the briefing text; release refused")
            STORE.write_json(rid, "critic.json", critic)
            return no_update
        _record_gate("gate2", "briefing_release", actor, "approved", extra={"critic_checks": critic["n_checks"], "llm_drafted": used_llm}, role=approver_role)
        approvals = dict(S["approvals"], preparer=S["preparer"], preparer_role=S.get("preparer_role", ""))
        text = draft_briefing(arte, approvals, rid, critic=critic)
        if CFG.llm_enabled:
            text, used_llm = draft_briefing_llm(arte, CLIENT, text, S["log"])
        STORE.write_text(rid, "briefing.md", text)
        STORE.write_text(rid, "briefing.html", to_html(text))
        STORE.write_json(rid, "critic.json", critic)
        record = atrs_record(arte, approvals, rid)
        STORE.write_json(rid, "atrs_record.json", record)
        STORE.write_text(rid, "atrs_record.md", render_markdown(record))
        S["log"]("briefing_released", actor=actor, approver=actor, sha256=hashlib.sha256(text.encode()).hexdigest(), llm_drafted=used_llm)
        STORE.update_meta(rid, stage="released", approver=actor)
        pack, manifest = STORE.pack(rid)
        S["log"]("evidence_pack_built", files=list(manifest["files"]))
        rep = ledger_verify(S["log"].path, CFG.secret)
        _bump(stage="released", step="released", briefing=text, critic=critic, ledger_report=rep, llm_used=used_llm, phase="Briefing released, evidence pack built")
        _alert("ok", "Briefing released, evidence pack built" if OPEN_GATES else f"Briefing released, approved by {actor}, evidence pack built")
    elif trig == "g2r":
        with LOCK:
            if S["stage"] != "evaluated":
                raise PreventUpdate
        _record_gate("gate2", "briefing_release", actor, "refused", reason, role=approver_role)
        STORE.update_meta(rid, stage="refused", approver=actor, reason=reason)
        STORE.pack(rid)
        rep = ledger_verify(S["log"].path, CFG.secret)
        _bump(stage="refused", step="gate2", ledger_report=rep, phase="Gate 2 refused, briefing withheld, reasons recorded")
        _alert("alert", f"Gate 2 refused: {reason}" if OPEN_GATES else f"Gate 2 refused by {actor}: {reason}")
    return no_update


@app.callback(Output("dat-result", "children"), Input("dat-upload", "contents"), State("dat-upload", "filename"), State("dat-class", "value"),
              State("dat-event", "value"), State("dat-maps", "value"), State("who", "value"), State("dat-analogue", "value"), prevent_initial_call=True)
def _dat_intake(contents, filename, cls, event, maps, who, analogue=None):
    if not contents:
        raise PreventUpdate
    if not _may("upload"):
        return html.Div(f"Role {_role()} may not upload", className="seal refused")
    import base64
    try:
        header, b64 = contents.split(",", 1)
        raw = base64.b64decode(b64)
    except Exception:  # noqa: BLE001
        return html.Div("Upload could not be decoded", className="seal refused")
    who = _actor(who) or "unnamed"
    ds = quarantine(filename or "upload.csv", raw, uploader=who, classification=cls or "public", max_bytes=CFG.upload_max_mb * 1024 * 1024,
                    event_date=(event or "").strip() or None, maps_to=(maps or "").strip() or None,
                    analogue_of=(analogue or "").strip().lower().replace(" ", "_") or None)
    log = S["log"]
    if not ds["ok"]:
        if log is not None:
            log("dataset_refused", actor=who, name=ds["name"], reason=ds["reason"])
        _alert("alert", f"Dataset {ds['name']} refused: {ds['reason']}")
        return html.Div(f"Refused: {ds['reason']}", className="seal refused")
    with LOCK:
        S["datasets"] = keep_recent([x for x in S["datasets"] if x["name"] != ds["name"]] + [ds])
        S["posture"] = None
        S["rev"] += 1
    if log is not None:
        log("dataset_accepted", actor=who, name=ds["name"], sha256=ds["sha256"], classification=ds["classification"], stats=ds["stats"],
            event_study=ds.get("event_study"), maps_to=ds.get("maps_to"), analogue_of=ds.get("analogue_of"))
    _alert("ok", f"Dataset accepted: {dataset_summary(ds)}")
    return html.Div(f"Accepted: {dataset_summary(ds)}" + (f". {ds['event_note']}" if ds.get("event_note") else ""), className="seal approved")


@app.callback(Output("sec-body", "children", allow_duplicate=True), Input("sec-recheck", "n_clicks"), prevent_initial_call=True)
def _sec_recheck(n):
    with LOCK:
        S["posture"] = None
    return _sec_body()


@app.callback(Output("pol-json", "value"), Input("pol-template", "n_clicks"), prevent_initial_call=True)
def _pol_reset(n):
    return json.dumps(policy_template(), indent=1)


@app.callback(Output("pol-result", "children"), Output("pol-list", "children"), Output("pol-pick", "options"),
              Input("pol-add", "n_clicks"), Input("pol-on", "n_clicks"), Input("pol-off", "n_clicks"), Input("pol-remove", "n_clicks"), Input("rev-store", "data"),
              State("pol-json", "value"), State("pol-pick", "value"), State("who", "value"))
def _pol_actions(n_add, n_on, n_off, n_rm, rev, text, pick, who):
    trig = ctx.triggered_id
    msg = no_update
    author = _actor(who) or "unnamed"
    log = S["log"]
    if trig == "pol-add" and n_add:
        if not _may("plan"):
            msg = html.Div(f"Role {_role()} may not define instruments", className="seal refused")
        else:
            try:
                doc = json.loads(text or "{}")
            except json.JSONDecodeError as e:
                doc = None; msg = html.Div(f"Not valid JSON: {e}", className="seal refused")
            if doc is not None:
                res = POLICIES.add(doc, author=author)
                if res["ok"]:
                    msg = html.Div(f"Stored {res['record']['policy']['label']} (sha256 {res['record']['sha256'][:12]})"
                                   + (f"; clamped: {'; '.join(res['notes'])}" if res["notes"] else ""), className="seal approved")
                    if log is not None:
                        log("policy_stored", actor=author, name=res["record"]["policy"]["name"], sha256=res["record"]["sha256"], notes=res["notes"])
                else:
                    msg = html.Div("Refused: " + "; ".join(res["errors"]), className="seal refused")
    elif trig in ("pol-on", "pol-off") and pick:
        POLICIES.set_enabled(pick, trig == "pol-on")
        msg = html.Div(f"{_nice(pick)} {'enabled' if trig == 'pol-on' else 'disabled'} for the next plan", className="seal approved")
    elif trig == "pol-remove" and n_rm and pick:
        ok = POLICIES.remove(pick)
        msg = html.Div(f"Removed {_nice(pick)}" if ok else "Nothing removed", className="seal")
        if ok and log is not None:
            log("policy_removed", actor=author, name=pick)
    opts = [{"label": x["policy"]["label"], "value": x["policy"]["name"]} for x in POLICIES.list()]
    return msg, _pol_list(), opts


@app.callback(Output("asm-result", "children"), Input("asm-apply", "n_clicks"), State("asm-json", "value"), prevent_initial_call=True)
def _asm_apply(n, text):
    if not n:
        raise PreventUpdate
    try:
        doc = json.loads(text or "{}")
    except json.JSONDecodeError as e:
        return html.Div(f"Not valid JSON: {e}", className="seal refused")
    a, notes = AS.validate(doc)
    over = {k: v for k, v in doc.items() if k in AS.SPEC}
    with LOCK:
        S["assumption_overrides"] = {k: a[k] for k in over}
    return html.Div(f"{len(over)} override{'s' if len(over) != 1 else ''} applied to the next plan" + (f"; {'; '.join(notes)}" if notes else ""), className="seal approved")


@app.callback(Output("agt-json", "value"), Input("agt-template", "n_clicks"), prevent_initial_call=True)
def _agt_reset(n):
    return json.dumps(firm_template(), indent=1)


@app.callback(Output("agt-result", "children"), Output("agt-list", "children"), Output("agt-pick", "options"),
              Input("agt-add", "n_clicks"), Input("agt-on", "n_clicks"), Input("agt-off", "n_clicks"), Input("agt-remove", "n_clicks"), Input("rev-store", "data"),
              State("agt-json", "value"), State("agt-pick", "value"), State("who", "value"))
def _agt_actions(n_add, n_on, n_off, n_rm, rev, text, pick, who):
    trig = ctx.triggered_id
    msg = no_update
    author = _actor(who) or "unnamed"
    log = S["log"]
    if trig == "agt-add" and n_add:
        try:
            doc = json.loads(text or "{}")
        except json.JSONDecodeError as e:
            doc = None; msg = html.Div(f"Not valid JSON: {e}", className="seal refused")
        if doc is not None:
            res = FIRMS.add(doc, author=author)
            if res["ok"]:
                msg = html.Div(f"Stored {res['record']['firm']['label']} (sha256 {res['record']['sha256'][:12]})" + (f"; clamped: {'; '.join(res['notes'])}" if res["notes"] else ""),
                               className="seal approved")
                if log is not None:
                    log("firm_stored", actor=author, name=res["record"]["firm"]["name"], sha256=res["record"]["sha256"], notes=res["notes"])
            else:
                msg = html.Div("Refused: " + "; ".join(res["errors"]), className="seal refused")
    elif trig in ("agt-on", "agt-off") and pick:
        FIRMS.set_enabled(pick, trig == "agt-on")
        msg = html.Div(f"{_nice(pick)} {'enabled' if trig == 'agt-on' else 'disabled'}", className="seal approved")
    elif trig == "agt-remove" and n_rm and pick:
        ok = FIRMS.remove(pick)
        msg = html.Div(f"Removed {_nice(pick)}" if ok else "Nothing removed", className="seal")
    opts = [{"label": x["firm"]["label"], "value": x["firm"]["name"]} for x in FIRMS.list()]
    return msg, _agt_list(), opts


if __name__ == "__main__":
    print(f"PSL TERMINAL {BUILD} · http://{CFG.host}:{CFG.port} · profile {CFG.profile} · auth {CFG.auth_mode} · runs in {STORE.root}"
          + (" · WARNING: ephemeral ledger key" if CFG.ephemeral_secret else ""), flush=True)
    app.run(debug=False, host=CFG.host, port=CFG.port, threaded=True)
