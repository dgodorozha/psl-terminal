"""Build the static replay site: recorded runs of the terminal rendered in the browser, no server.

    python tools/build_static.py --out site --profile demo --live-url https://your-workspace--psl.modal.run

For every question in the list (the default battery question and two more, or --questions file.json with a
list of strings) the builder plans the battery, approves Gate 1 (open gates by default, as the public site has; --gates named
records Developer1 and Developer2 in dev mode), runs it with the stream
recorded, lets the critic check it, releases the briefing at Gate 2 and builds the evidence pack, exactly as
the terminal does, using the terminal's own code. It then renders every panel the terminal would show at
every stage into HTML fragments, converts the terminal's layout to a static page, and writes a replay script
that plays the recorded stream back and swaps the fragments in as the stages pass. The result is a folder
GitHub Pages serves as it is. The page says it is a replay; the live terminal is one link away.
"""

import argparse
import datetime
import hashlib
import json
import os
import re
import shutil
import sys
import html as htmllib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

DEFAULT_QUESTIONS = [
    None,   # the terminal's default question
    "Compare strict liability with liability under a safe harbour and mandatory third party evaluations over the next "
    "five years; the technology sector's net loss must stay below $300bn and the probability of a catastrophic incident "
    "must fall by at least a quarter.",
    "Would a six month moratorium above the compute threshold or coordinated frontier licensing reduce expected harm more "
    "over three years, keeping the gross social cost under $100bn?",
]

VOID = {"input", "br", "hr", "img", "meta", "link"}
ATTR = {"className": "class", "htmlFor": "for", "autoComplete": "autocomplete", "maxLength": "maxlength",
        "spellCheck": "spellcheck", "readOnly": "readonly", "accessKey": "accesskey", "tabIndex": "tabindex",
        "colSpan": "colspan", "rowSpan": "rowspan"}
SKIP = {"n_clicks", "n_clicks_timestamp", "debounce", "inline", "options", "inputClassName", "labelClassName",
        "persistence", "persistence_type", "persisted_props", "loading_state", "max_size", "multiple", "interval",
        "n_intervals", "data", "setProps", "key", "disable_n_clicks", "contentEditable", "draggable", "hidden"}


def _css(style):
    out = []
    for k, v in (style or {}).items():
        k2 = re.sub(r"([A-Z])", lambda m: "-" + m.group(1).lower(), k)
        out.append(f"{k2}:{v}")
    return ";".join(out)


def _attrs(props, extra=None):
    bits = []
    for k, v in dict(props, **(extra or {})).items():
        if k in ("children", "value_text") or k in SKIP or v is None:
            continue
        if k == "style":
            if v:
                bits.append(f'style="{htmllib.escape(_css(v), quote=True)}"')
            continue
        name = ATTR.get(k, k)
        if isinstance(v, bool):
            if v:
                bits.append(name if name not in ("spellcheck",) else f'{name}="true"')
            elif name == "spellcheck":
                bits.append('spellcheck="false"')
            continue
        bits.append(f'{name}="{htmllib.escape(str(v), quote=True)}"')
    return (" " + " ".join(bits)) if bits else ""


def _children(ch, md):
    if ch is None:
        return ""
    if isinstance(ch, (list, tuple)):
        return "".join(_children(c, md) for c in ch)
    if isinstance(ch, (str, int, float)):
        return htmllib.escape(str(ch))
    return to_html(ch, md)


def to_html(comp, md=None):
    """Render a Dash component tree as static HTML."""
    if comp is None:
        return ""
    if isinstance(comp, (str, int, float)):
        return htmllib.escape(str(comp))
    if isinstance(comp, (list, tuple)):
        return "".join(to_html(c, md) for c in comp)
    j = comp.to_plotly_json()
    t, ns, p = j["type"], j["namespace"], dict(j["props"])
    if ns == "dash_core_components":
        if t in ("Interval", "Store", "Location", "Download"):
            return ""
        if t == "Markdown":
            body = md(p.get("children") or "") if md else htmllib.escape(str(p.get("children") or ""))
            return f'<div{_attrs({k: v for k, v in p.items() if k in ("id", "className", "style")})}>{body}</div>'
        if t == "Textarea":
            val = p.pop("value", "") or ""
            return f'<textarea{_attrs(p)}>{htmllib.escape(str(val))}</textarea>'
        if t == "Input":
            return f'<input{_attrs(p)}>'
        if t == "RadioItems":
            opts = p.get("options") or []
            cur = p.get("value")
            name = p.get("id", "radio")
            labs = []
            for o in opts:
                if not isinstance(o, dict):
                    o = {"label": o, "value": o}
                checked = " checked" if o.get("value") == cur else ""
                labs.append(f'<label class="{p.get("labelClassName", "")}"><input type="radio" class="{p.get("inputClassName", "")}" '
                            f'name="{htmllib.escape(str(name), quote=True)}" value="{htmllib.escape(str(o.get("value")), quote=True)}"{checked}>'
                            f'{htmllib.escape(str(o.get("label")))}</label>')
            return f'<div{_attrs({"id": p.get("id"), "className": p.get("className"), "style": p.get("style")})}>{"".join(labs)}</div>'
        if t == "Upload":
            return (f'<div{_attrs({"id": p.get("id"), "className": p.get("className")})} data-replay="disabled" '
                    f'title="Uploads are not available in the replay; use the live terminal">{_children(p.get("children"), md)}</div>')
        return _children(p.get("children"), md)
    tag = t.lower()
    inner = _children(p.get("children"), md)
    if tag in VOID:
        return f"<{tag}{_attrs(p)}>"
    return f"<{tag}{_attrs(p)}>{inner}</{tag}>"


def md_to_html(md_text):
    from psl.briefing import to_html as brief_html
    page = brief_html(md_text)
    m = re.search(r"<body>(.*)</body>", page, re.S)
    return m.group(1) if m else htmllib.escape(md_text)


def relink(frag, rid):
    return frag.replace(f'href="/run/{rid}/', f'href="data/{rid}/')


def main():
    ap = argparse.ArgumentParser(description="Build the static replay site")
    ap.add_argument("--out", default="site")
    ap.add_argument("--profile", default="demo", choices=("full", "light", "demo"))
    ap.add_argument("--questions", help="JSON file with a list of policy questions")
    ap.add_argument("--live-url", default="", help="address of the live terminal, linked from the page")
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--gates", default="open", choices=("open", "named"), help="open: single click gates without identities (default); named: Developer1 and Developer2 in dev mode")
    args = ap.parse_args()

    out = os.path.abspath(args.out)
    if os.path.isdir(out):
        shutil.rmtree(out)
    os.makedirs(os.path.join(out, "data"))
    os.environ.update({"PSL_RUNS_DIR": os.path.join(out, "data"), "PSL_DEV_MODE": "on" if args.gates == "named" else "off",
                       "PSL_GATES": args.gates, "PSL_PROFILE": args.profile,
                       "PSL_SECRET": os.environ.get("PSL_SECRET") or hashlib.sha256(b"psl static build").hexdigest(),
                       "PSL_TICK_PACE": "0", "PSL_HOST": "127.0.0.1", "PSL_LLM": "off",
                       "PSL_REGISTER": os.path.join(ROOT, "sample_data", "register.csv")})
    import dash_app as D  # noqa: E402
    OPEN = args.gates == "open"
    PREP, PREP_ROLE = (D.OPEN_ACTOR, "public demonstration") if OPEN else ("Developer1", "Developer1")
    APPR, APPR_ROLE = (D.OPEN_ACTOR, D.OPEN_ROLE) if OPEN else ("Developer2", "Developer2")
    from psl import ask as ASK  # noqa: E402
    from psl.atrs import atrs_record, render_markdown  # noqa: E402
    from psl.briefing import draft_briefing, to_html as brief_html  # noqa: E402
    from psl.critic import critic_check  # noqa: E402
    from psl.ledger import verify as ledger_verify  # noqa: E402
    from psl.question import DEFAULT_QUESTION  # noqa: E402
    from runstore import utc_now  # noqa: E402

    questions = DEFAULT_QUESTIONS
    if args.questions:
        with open(args.questions) as f:
            questions = json.load(f)
    questions = [q or DEFAULT_QUESTION for q in questions]

    # record phases with their position in the event sequence
    phases = []
    orig_progress = D._progress

    def rec_progress(step, phase, **kw):
        orig_progress(step, phase, **kw)
        with D.LOCK:
            phases.append({"seq": D.S["seq"], "step": step, "phase": phase, "policy": kw.get("policy")})
    D._progress = rec_progress

    runs = []
    for qi, question in enumerate(questions):
        print(f"[{qi + 1}/{len(questions)}] {question[:80]}", flush=True)
        phases.clear()
        with D.LOCK:
            D.S.update(D._fresh_state())
            D.S["preparer_role"] = PREP_ROLE
        D._worker_plan(question, PREP)
        if D.S["stage"] != "planned":
            raise SystemExit(f"planning failed: {D.S['err']}")
        rid = D.S["run_id"]
        frags, marks, verify = {}, {}, {}

        def snap(name):
            frags[f"run_{name}"] = relink(to_html(D._run_status(), md_to_html), rid)
            verify[name] = D._ldg_verify()
            marks[name] = D.S["seq"]

        frags["await_saf"] = to_html(D._saf_body()); frags["await_pnl"] = to_html(D._pnl_body())
        frags["await_wlf"] = to_html(D._wlf_body()); frags["await_gap"] = to_html(D._gap_body())
        frags["await_nws_fc"] = to_html(D._nws_forecast()); frags["await_rsk"] = to_html(D._rsk_body())
        snap("planned")
        # gate 1
        D._record_gate("gate1", "battery_signoff", APPR, "approved",
                       extra={"battery_hash": D.S["battery_hash"], "n_policies": len(D.S["battery"]["policies"])}, role=APPR_ROLE)
        D.STORE.update_meta(rid, stage="running", approver=APPR)
        D._bump(stage="running", step="simulate", phase="Gate 1 approved, battery running")
        D._alert("ok", (f"Gate 1 approved, battery {D.S['battery_hash'][:12]} running" if OPEN else
                        f"Gate 1 approved by {APPR}, battery {D.S['battery_hash'][:12]} running"))
        snap("running")
        D._worker_run()
        if D.S["stage"] != "evaluated":
            raise SystemExit(f"run failed: {D.S['err']}")
        arte = D.S["artefacts"]; ev = arte["results"]
        snap("evaluated")
        frags["saf"] = to_html(D._saf_body()); frags["gap"] = to_html(D._gap_body())
        frags["rsk"] = to_html(D._sectioned(D._rsk_body()))
        cands = [r["policy"] for r in ev["policies"] if r["policy"] != "baseline"]
        for pol in cands:
            with D.LOCK:
                D.S["pick"] = {"pnl": pol, "wlf": pol, "nws": pol}
            frags[f"pnl_{pol}"] = to_html(D._pnl_body()); frags[f"wlf_{pol}"] = to_html(D._wlf_body())
            frags[f"nws_fc_{pol}"] = to_html(D._nws_forecast())
        pref = ev["preferred"] or ev["best_unconstrained"]
        with D.LOCK:
            D.S["pick"] = {"pnl": pref, "wlf": pref, "nws": pref}
        evaluated = {"preferred": pref,
                     "index": {r["policy"]: {"mean": r["market"]["index_mean"], "lo": r["market"]["index_lo"], "hi": r["market"]["index_hi"],
                                             "base": r["market"]["index_base_mean"], "label": r["label"],
                                             "rel_mean": r["market"].get("rel_mean"), "rel_lo": r["market"].get("rel_lo"),
                                             "rel_hi": r["market"].get("rel_hi"), "early": r["market"]["early_reaction"]["mean"],
                                             "end": r["market"]["end_reaction"]["mean"]} for r in ev["policies"] if r["policy"] != "baseline"}}
        # gate 2 (the terminal's release path)
        critic = D.S["critic"]
        if not critic["ok"]:
            raise SystemExit("critic failed; the replay needs a clean run")
        approvals = dict(D.S["approvals"], preparer=PREP, preparer_role=PREP_ROLE,
                         gate2={"actor": APPR, "role": APPR_ROLE, "ts": utc_now(), "decision": "approved",
                                "register": None if OPEN else (D.REGISTER.check(APPR, APPR_ROLE) or {}).get("match"),
                                **({"open_gate": True} if OPEN else {})})
        text = draft_briefing(arte, approvals, rid)
        critic2 = critic_check(D.S["run_dir"], secret=D.CFG.secret, briefing_text=text)
        if not critic2["ok"]:
            raise SystemExit("critic rejected the briefing")
        D._record_gate("gate2", "briefing_release", APPR, "approved", extra={"critic_checks": critic2["n_checks"], "llm_drafted": False},
                       role=APPR_ROLE)
        approvals = dict(D.S["approvals"], preparer=PREP, preparer_role=PREP_ROLE)
        text = draft_briefing(arte, approvals, rid, critic=critic2)
        D.STORE.write_text(rid, "briefing.md", text); D.STORE.write_text(rid, "briefing.html", brief_html(text))
        D.STORE.write_json(rid, "critic.json", critic2)
        record = atrs_record(arte, approvals, rid)
        D.STORE.write_json(rid, "atrs_record.json", record); D.STORE.write_text(rid, "atrs_record.md", render_markdown(record))
        D.S["log"]("briefing_released", actor=APPR, approver=APPR, sha256=hashlib.sha256(text.encode()).hexdigest(), llm_drafted=False)
        D.STORE.update_meta(rid, stage="released", approver=APPR)
        pack, manifest = D.STORE.pack(rid)
        D.S["log"]("evidence_pack_built", files=list(manifest["files"]))
        rep = ledger_verify(D.S["log"].path, D.CFG.secret)
        D._bump(stage="released", step="released", briefing=text, critic=critic2, ledger_report=rep, phase="Briefing released, evidence pack built")
        D._alert("ok", "Briefing released, evidence pack built" if OPEN else f"Briefing released, approved by {APPR}, evidence pack built")
        snap("released")

        # the event timeline, merged by sequence number
        with D.LOCK:
            events = []
            for q, t in D.S["ticks"]:
                events.append({"seq": q, "kind": "tick", **{k: v for k, v in t.items() if k != "headlines"}})
            for q, h in D.S["heads"]:
                events.append({"seq": q, "kind": "head", **h})
            for q, a in D.S["alerts"]:
                events.append({"seq": q, "kind": "alert", **a})
            for q, r in D.S["ledger_rows"]:
                events.append({"seq": q, "kind": "ledger", "row": r})
            for ph in phases:
                events.append(dict(ph, kind="phase"))
            labels = list(D.S["labels"])
            pol_labels = {p["name"]: p["label"] for p in D.S["battery"]["policies"]}
            snapshot = D._snapshot()
        events.sort(key=lambda e: (e["seq"], 0 if e["kind"] == "phase" else 1))

        # the oracle's material, so ASK answers in the browser
        chunks = ASK.chunks(snapshot)
        firms = []
        for f in arte["firms"]:
            rows = []
            for r in ev["policies"]:
                if r["policy"] == "baseline":
                    continue
                fr = next(x for x in r["market"]["firms"] if x["firm"] == f["label"])
                rows.append(f"{r['label']}: {ASK._bn(fr['value_change']['mean'])} (P(gain) {ASK._pct(fr['value_change']['p_positive'])}, "
                            f"earnings {ASK._bn(fr['earnings_change_npv'])}, offshore at end {ASK._pct(fr['offshore_end'])})")
            firms.append({"name": f["name"], "label": f["label"],
                          "text": f"{f['label']} ({D._nice(f['sector'])}) under each instrument, value change against the baseline: " + "; ".join(rows) + "."})
        assumptions = []
        torn = (arte.get("assurance") or {}).get("tornado")
        for r in arte["assumption_table"]:
            words = [w for w in r["assumption"].split("_") if len(w) > 2 and w not in ("bn", "share", "base", "rate", "monthly")]
            t = f"{D._nice(r['assumption'])}: {r['value']} {r['unit']}; {r['meaning']}; bounds {r['low']} to {r['high']}."
            if torn:
                for row in torn["rows"]:
                    if row["assumption"] == r["assumption"]:
                        t += (f" In the tornado the preferred option's value is {ASK._bn(row['low']['nsv'])} at {row['low']['value']} and "
                              f"{ASK._bn(row['high']['nsv'])} at {row['high']['value']}" + ("; the best option changes." if row["best_changes"] else "."))
            assumptions.append({"key": r["assumption"], "nice": D._nice(r["assumption"]).lower(), "words": words, "text": t})
        ask = {"chunks": chunks, "intents": [[n, list(k)] for n, k in ASK.INTENTS], "weak": ASK.WEAK, "preferred": pref,
               "policies": [{"name": r["policy"], "label": r["label"]} for r in ev["policies"] if r["policy"] != "baseline"],
               "firms": firms, "assumptions": assumptions}

        replay = {"run_id": rid, "question": question, "labels": labels, "pol_labels": pol_labels, "events": events, "marks": marks,
                  "evaluated": evaluated, "fragments": frags, "verify": verify, "candidates": cands, "preferred": pref,
                  "n_checks": critic2["n_checks"], "profile": args.profile, "paths": arte["paths"], "horizon": arte["horizon"]}
        with open(os.path.join(out, "data", rid, "replay.json"), "w") as f:
            json.dump(replay, f)
        with open(os.path.join(out, "data", rid, "ask.json"), "w") as f:
            json.dump(ask, f)
        for big in ("paths.npz",):
            p = os.path.join(out, "data", rid, big)
            if os.path.isfile(p):
                os.remove(p)
        runs.append({"run_id": rid, "question": question, "preferred": pref, "preferred_label": pol_labels[pref],
                     "n_policies": len(cands) + 1, "paths": arte["paths"], "horizon": arte["horizon"]})
        import time
        time.sleep(1.1)   # run ids carry the second

    # shared fragments: registry, posture, library lists, the idle run control
    with D.LOCK:
        D.S.update(D._fresh_state())
    shared = {"reg": relink_all(to_html(D._reg_body()), runs), "sec": to_html(D._sec_body()),
              "pol_list": to_html(D._pol_list()), "agt_list": to_html(D._agt_list()), "dat_list": to_html(D._dat_list()),
              "run_idle": to_html(D._run_status())}
    with open(os.path.join(out, "data", "index.json"), "w") as f:
        json.dump({"runs": runs, "built": utc_now(), "live_url": args.live_url, "profile": args.profile, "shared": shared,
                   "version": D.__version__}, f)

    # the page: the terminal's own layout, converted
    with D.LOCK:
        D.S.update(D._fresh_state())
    page = to_html(D.app.layout, md_to_html)
    page = page.replace('<div class="tape-wrap"><div id="ticker-text">',
                        '<div class="tape-wrap"><div id="ticker-text">Replay of recorded runs. ')
    live = (f' Live terminal: <a href="{htmllib.escape(args.live_url, quote=True)}" target="_blank" rel="noopener">{htmllib.escape(args.live_url)}</a>.'
            if args.live_url else "")
    note = (f'<p class="duck build">Replay built {datetime.date.today().isoformat()} from {len(runs)} recorded run{"s" if len(runs) != 1 else ""} '
            f'on the {args.profile} profile. Everything on this page was computed by the terminal and recorded; nothing runs on a server, '
            f'so the question cannot be changed here.{live}</p>')
    page = page.replace('<p class="duck build">', note + '<p class="duck build">', 1)
    css_vendor = ""
    html_doc = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><title>PSL TERMINAL (replay)</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="Policy Scenario Lab: a replay of recorded runs of the PSL terminal">
<link rel="stylesheet" href="assets/psl.css">{css_vendor}
</head><body>
{page}
<script src="assets/vendor/lightweight-charts.standalone.production.js"></script>
<script src="assets/terminal.js"></script>
<script src="replay.js"></script>
</body></html>"""
    with open(os.path.join(out, "index.html"), "w") as f:
        f.write(html_doc)
    with open(os.path.join(out, ".nojekyll"), "w") as f:
        f.write("")
    shutil.copytree(os.path.join(ROOT, "assets"), os.path.join(out, "assets"), ignore=shutil.ignore_patterns("MANIFEST.sha256"))
    shutil.copy(os.path.join(ROOT, "tools", "replay.js"), os.path.join(out, "replay.js"))
    total = sum(os.path.getsize(os.path.join(dp, fn)) for dp, _, fns in os.walk(out) for fn in fns)
    print(f"site written to {out}: {len(runs)} runs, {total / 1e6:.1f} MB", flush=True)


def relink_all(frag, runs):
    for r in runs:
        frag = relink(frag, r["run_id"])
    return frag


if __name__ == "__main__":
    main()
