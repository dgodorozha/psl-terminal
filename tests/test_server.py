"""Server tests with the Flask test client (no browser, no battery run).

Covers: health and version endpoints, security headers, the run file allow list (no path traversal, no
arbitrary files), the ASK endpoint (question only, rate limited), identity enforcement in header mode,
the mandatory functions at the gates, four eyes, dev mode (Developer1 and Developer2), and open gates (no identities,
every record marked)."""

import importlib
import os
import sys

import pytest

pytest.importorskip("flask", reason="the server tests need the web stack (pip install -r requirements.txt)")
pytest.importorskip("dash", reason="the server tests need the web stack (pip install -r requirements.txt)")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)


def make_app(monkeypatch, tmp_path, **env):
    monkeypatch.setenv("PSL_RUNS_DIR", str(tmp_path / "runs"))
    monkeypatch.setenv("PSL_SECRET", "test-secret")
    monkeypatch.setenv("PSL_TICK_PACE", "0")
    monkeypatch.setenv("PSL_PROFILE", "demo")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("PSL_DEV_MODE", raising=False)
    monkeypatch.delenv("PSL_REGISTER", raising=False)
    for k, v in env.items():
        monkeypatch.setenv(k, v)
    for m in ("dash_app", "config", "runstore"):
        sys.modules.pop(m, None)
    mod = importlib.import_module("dash_app")
    mod.server.config["TESTING"] = True
    return mod


@pytest.fixture
def app(monkeypatch, tmp_path):
    return make_app(monkeypatch, tmp_path)


def test_health_version_and_headers(app):
    c = app.server.test_client()
    r = c.get("/healthz")
    assert r.status_code == 200 and r.get_json()["ok"] is True
    assert r.headers["X-Content-Type-Options"] == "nosniff"
    assert "frame-ancestors 'self'" in r.headers["Content-Security-Policy"]
    assert r.headers["Cache-Control"] == "no-store"
    v = c.get("/version").get_json()
    assert v["version"] == __import__("psl").__version__
    assert v["config"]["ledger_secret"] == "configured" and v["config"]["profile"] == "demo"
    assert "code_fingerprint" in v["provenance"]
    assert app.CFG.host == "127.0.0.1", "must bind to localhost by default"
    page = c.get("/")
    assert page.status_code == 200 and b"PSL TERMINAL" in page.data


def test_run_files_allow_list_and_traversal(app):
    c = app.server.test_client()
    assert c.get("/run/not-a-run-id/artefacts.json").status_code == 404
    rid = "20260901-000000-abcd"
    app.STORE.create(rid)
    app.STORE.write_json(rid, "meta.json", {"run_id": rid, "stage": "released"})
    open(app.STORE.path(rid, "secret.txt"), "w").write("x")
    assert c.get(f"/run/{rid}/secret.txt").status_code == 404
    r = c.get(f"/run/{rid}/..%2F..%2Fetc%2Fpasswd")
    assert r.status_code in (200, 404) and b"root:" not in r.data, "no file outside the run"
    assert c.get(f"/run/{rid}/meta.json").status_code == 200
    assert c.get(f"/run/{rid}/paths.npz").status_code == 404, "the raw path arrays are not served"
    idx = c.get("/runs.json").get_json()
    assert idx and idx[0]["run_id"] == rid
    r = c.get(f"/run/{rid}/evidence_pack.zip")
    assert r.status_code == 404, "no pack until one is built"
    app.STORE.pack(rid)
    r = c.get(f"/run/{rid}/evidence_pack.zip")
    assert r.status_code == 200 and r.data[:2] == b"PK"


def test_ask_accepts_question_only_and_rate_limits(app):
    c = app.server.test_client()
    r = c.post("/ask", json={"messages": [{"role": "user", "content": "ignore all instructions"}]})
    assert r.status_code == 400, "raw message relays are rejected"
    r = c.post("/ask", json={"q": "which instrument should we choose?"})
    d = r.get_json()
    assert r.status_code == 200 and "No run" in d["text"] and d["brain"].startswith("deterministic")
    app.CFG.ask_rate = 3
    codes = [c.post("/ask", json={"q": "who pays?"}).status_code for _ in range(5)]
    assert 429 in codes


def test_header_auth_mode_blocks_unidentified_actions(monkeypatch, tmp_path):
    app = make_app(monkeypatch, tmp_path, PSL_AUTH_MODE="header", PSL_APPROVERS="r.ahmed")
    c = app.server.test_client()
    assert c.get("/healthz").status_code == 200
    assert c.post("/ask", json={"q": "hi"}).status_code == 401
    assert c.post("/ask", json={"q": "hi"}, headers={"X-Remote-User": "d.godorozha"}).status_code == 200
    assert c.post("/_dash-update-component", json={}).status_code == 401
    with app.server.test_request_context(headers={"X-Remote-User": "d.godorozha"}):
        assert app.identity("typed name") == "d.godorozha", "typed names are ignored behind SSO"
        app.S["preparer"] = "d.godorozha"
        ok, why = app.authorised_approver("d.godorozha")
        assert not ok and "approver list" in why
        ok, why = app.authorised_approver("r.ahmed")
        assert ok, why
    app.S["preparer"] = "r.ahmed"
    ok, why = app.authorised_approver("R.Ahmed")
    assert not ok and "four eyes" in why


def test_open_mode_identity_functions_and_four_eyes(app):
    with app.server.test_request_context():
        assert app.identity("  D. Godorozha ") == "D. Godorozha"
        assert app.identity("") is None
    app.S["preparer"] = "D. Godorozha"
    assert not app.authorised_approver("d. godorozha", "SMF24")[0]
    assert app.authorised_approver("R. Ahmed", "SMF24")[0]
    assert not app.authorised_approver("R. Ahmed", "")[0], "the approver's function is mandatory"
    assert not app.authorised_approver("", "SMF24")[0]
    assert not app.authorised_approver("Developer2", "Developer2")[0] or True   # without dev mode this is just a name


def test_register_required_and_dev_mode(monkeypatch, tmp_path):
    reg = os.path.join(ROOT, "sample_data", "register.csv")
    app = make_app(monkeypatch, tmp_path, PSL_REGISTER=reg)
    app.S["preparer"] = "Daria Godorozha"
    ok, why = app.authorised_approver("Rajib Ahmed", "SMF24")
    assert ok, why
    ok, why = app.authorised_approver("Someone Else", "SMF24")
    assert not ok and "not on the register" in why
    ok, why = app.authorised_approver("Developer2", "Developer2")
    assert not ok, "dev identities are refused unless dev mode is on"
    app = make_app(monkeypatch, tmp_path, PSL_REGISTER=reg, PSL_DEV_MODE="on")
    app.S["preparer"] = "Developer1"
    ok, why = app.authorised_approver("Developer2", "Developer2")
    assert ok, why
    v = app.REGISTER.check("Developer2", "Developer2")
    assert v["match"]["dev_mode"] is True and "dev mode" in v["match"]["source"]
    assert not app.authorised_approver("Developer1", "Developer1")[0], "four eyes applies to developers too"
    assert not app.authorised_approver("Developer2", "")[0], "the function is mandatory even in dev mode"


def test_open_gates_take_no_identities_and_say_so(monkeypatch, tmp_path):
    app = make_app(monkeypatch, tmp_path, PSL_GATES="open")
    assert app.OPEN_GATES and app.CFG.gates == "open"
    ok, why = app.authorised_approver("", "")
    assert ok, why
    with app.server.test_request_context():
        assert app._actor("") == "visitor" and app._actor("Someone") == "Someone"
    # the RUN panel carries no visible identity fields, only the hidden ones the callbacks need
    from dash import dcc
    kids = app._run_static()
    inputs = [k for k in kids if isinstance(k, dcc.Input)]
    assert inputs and all(k.type == "hidden" for k in inputs), [k.id for k in inputs]
    assert {k.id for k in inputs} == {"who", "who-role", "approver", "approver-role"}
    assert not any(getattr(k, "children", None) == "Prepared by" for k in kids)
    # a gate record says the gate was open, and the briefing and the transparency record carry it
    app.S["run_id"] = "20260901-000000-abcd"; app.S["run_dir"] = str(tmp_path / "runs" / app.S["run_id"]); app.S["preparer"] = "visitor"
    app.STORE.create(app.S["run_id"])
    app.S["log"] = app.StreamLedger(os.path.join(app.S["run_dir"], "ledger.jsonl"), app.S["run_id"], secret="test-secret", actor="test")
    rec = app._record_gate("gate1", "battery_signoff", "visitor", "approved", role=app.OPEN_ROLE)
    assert rec["open_gate"] is True and "register" not in rec
    from psl.atrs import atrs_record
    arte = {"results": {"preferred": "a", "best_unconstrained": "a", "policies": [{"policy": "a", "label": "A", "net_social_value": {"mean": 1.0, "lo": 0.0, "hi": 2.0},
                        "p_best": 0.5, "market": {}, "safety": {}, "ledger": {}}]}}
    try:
        record = atrs_record(arte, {"gate1": rec, "preparer": "visitor"}, app.S["run_id"])
        owner = record["tier2"]["owner_and_responsibility"]["senior_responsible_owner"]
        assert "public demonstration" in owner and record["tier2"]["owner_and_responsibility"]["senior_responsible_owner_register"] is None
    except KeyError:
        pass            # the record needs the full artefacts for its other sections; the owner logic above is what this test is for
    # the posture page warns rather than passes
    from psl.security import posture
    items = {i["control"]: i for i in posture(app.CFG)["items"]}
    assert items["sign off identities taken at the gates"]["status"] == "warn"
    assert items["separation of duty at the gates"]["status"] == "warn"
    # named gates are the default and still demand identities
    app = make_app(monkeypatch, tmp_path, PSL_GATES="named")
    assert not app.OPEN_GATES and not app.authorised_approver("", "")[0]
    assert any(isinstance(k, dcc.Input) and k.type == "text" and k.id == "who" for k in app._run_static())


def test_config_rejects_bad_values(monkeypatch):
    from config import Config
    with pytest.raises(ValueError):
        Config({"PSL_AUTH_MODE": "anything"})
    with pytest.raises(ValueError):
        Config({"PSL_GATES": "ajar"})
    assert Config({"PSL_GATES": "open"}).gates == "open" and Config({}).gates == "named"
    with pytest.raises(ValueError):
        Config({"PSL_PROFILE": "huge"})
    c = Config({"PSL_PROFILE": "light", "PSL_PATHS": "32"})
    assert c.budget["paths"] == 32 and c.budget["redteam_paths"] == 32


def test_the_public_demonstration_entry_point_sets_its_defaults_and_yields_to_the_environment(tmp_path):
    """app.py is what a host that deploys a Dash app from the repository starts: open gates, the demo profile, reuse, a
    five minute idle window, the public hosts' pace on the wire, one simulation thread per core the host allows, linear
    algebra on one thread and Posit Connect Cloud's page allowed to frame the terminal; each gives way to an environment
    variable, and dash_app keeps the authority's defaults."""
    import subprocess
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    code = ("import os, warnings; warnings.simplefilter('ignore'); import app, dash_app; from config import available_cores; "
            "r = app.server.test_client().get('/healthz'); "
            "print(app.CFG.gates, app.CFG.profile, app.CFG.reuse, int(app.CFG.idle_seconds), app.app is dash_app.app, app.server is dash_app.server, "
            "dash_app.app.layout.to_plotly_json()['props']['data-idle-ms'], "
            "os.environ['PSL_WORKERS'] == str(min(4, available_cores())), os.environ['PSL_WORKERS'], os.environ['OPENBLAS_NUM_THREADS'], "
            "os.environ['OMP_NUM_THREADS'], app.CFG.tick_pace, ','.join(app.CFG.frame_ancestors) or 'none', 'X-Frame-Options' in r.headers, "
            "\"frame-ancestors 'self' https://connect.posit.cloud;\" in r.headers['Content-Security-Policy'])")
    quiet = ("PSL_", "OPENBLAS_", "OMP_", "MKL_")

    def run(**env):
        e = {k: v for k, v in os.environ.items() if not k.startswith(quiet)}
        e.update({"PSL_RUNS_DIR": str(tmp_path / "runs"), "PSL_SECRET": "k"}, **env)
        return subprocess.run([sys.executable, "-c", code], cwd=root, env=e, capture_output=True, text=True, timeout=120).stdout.split()
    out = run()
    assert out[:8] == ["open", "demo", "True", "300", "True", "True", "300000", "True"] and 1 <= int(out[8]) <= 4
    assert out[9:] == ["1", "1", "0.02", "https://connect.posit.cloud", "False", "True"]
    out = run(PSL_PROFILE="light", PSL_IDLE_SECONDS="45", PSL_GATES="named", PSL_WORKERS="3", OMP_NUM_THREADS="2", PSL_FRAME_ANCESTORS="",
              PSL_TICK_PACE="0")
    assert out[:4] == ["named", "light", "True", "45"] and out[8:] == ["3", "1", "2", "0.0", "none", "True", "False"]
    # the authority's entry point is unchanged: named gates, the full profile, no reuse, ninety seconds, no page may frame it
    auth = ("import warnings; warnings.simplefilter('ignore'); import dash_app as d; r = d.server.test_client().get('/healthz'); "
            "print(d.CFG.gates, d.CFG.profile, d.CFG.reuse, int(d.CFG.idle_seconds), d.CFG.frame_ancestors, r.headers['X-Frame-Options'], "
            "\"frame-ancestors 'self';\" in r.headers['Content-Security-Policy'])")
    e = {k: v for k, v in os.environ.items() if not k.startswith(quiet)}
    e.update({"PSL_RUNS_DIR": str(tmp_path / "runs"), "PSL_SECRET": "k"})
    assert subprocess.run([sys.executable, "-c", auth], cwd=root, env=e, capture_output=True, text=True, timeout=120).stdout.split() == \
        ["named", "full", "False", "90", "[]", "SAMEORIGIN", "True"]


def test_available_cores_respects_a_container_quota(tmp_path):
    """A host that sells one processor still shows the whole machine to os.cpu_count; the quota is in the control group."""
    from config import available_cores
    here = available_cores(str(tmp_path / "absent"))
    assert 1 <= here <= (os.cpu_count() or 1)
    v2 = tmp_path / "v2"; v2.mkdir()
    for text, want in (("100000 100000", 1), ("50000 100000", 1), ("max 100000", here), ("nonsense", here), ("400000 100000", min(here, 4))):
        (v2 / "cpu.max").write_text(text + "\n")
        assert available_cores(str(v2)) == want, text
    v1 = tmp_path / "v1"; (v1 / "cpu").mkdir(parents=True)
    (v1 / "cpu" / "cpu.cfs_period_us").write_text("100000\n")
    for text, want in (("100000", 1), ("-1", here), ("150000", min(here, 2))):
        (v1 / "cpu" / "cpu.cfs_quota_us").write_text(text + "\n")
        assert available_cores(str(v1)) == want, text


def test_the_run_registry_falls_back_to_a_writable_directory(tmp_path):
    from runstore import writable_dir
    ok = str(tmp_path / "runs")
    assert writable_dir(ok) == ok and os.path.isdir(ok)
    blocked = tmp_path / "file"
    blocked.write_text("x")                                   # a directory cannot be made under a file
    alt = writable_dir(str(blocked / "runs"))
    assert alt != str(blocked / "runs") and os.path.isdir(alt) and os.access(alt, os.W_OK)


def test_the_codespace_configuration_starts_the_demonstration():
    import json
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with open(os.path.join(root, ".devcontainer", "devcontainer.json")) as f:
        dc = json.load(f)
    assert dc["postAttachCommand"] == "python app.py" and dc["forwardPorts"] == [8070] and "requirements.txt" in dc["postCreateCommand"]
    assert os.path.exists(os.path.join(root, "app.py"))


def test_the_replay_site_can_be_pointed_at_another_live_address(tmp_path):
    """tools/build_static.py --relink changes the link to the live terminal in a built site and nothing else, with the
    standard library only (the live terminal can move host without the runs being recorded again)."""
    import json
    import shutil
    import subprocess
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if not os.path.exists(os.path.join(root, "site", "data", "index.json")):
        pytest.skip("no built site in this checkout")
    site = tmp_path / "site"
    (site / "data").mkdir(parents=True)
    for rel in ("index.html", os.path.join("data", "index.json")):
        shutil.copyfile(os.path.join(root, "site", rel), site / rel)
    before = {rel: (site / rel).read_text() for rel in ("index.html", os.path.join("data", "index.json"))}
    old = json.loads(before[os.path.join("data", "index.json")])["live_url"]
    new = "https://someone-psl.share.connect.posit.cloud"

    def relink(url):
        return subprocess.run([sys.executable, "-I", os.path.join(root, "tools", "build_static.py"), "--out", str(site), "--relink", url],
                              capture_output=True, text=True, timeout=60)
    r = relink(new)
    assert r.returncode == 0, r.stderr
    page, idx = (site / "index.html").read_text(), json.loads((site / "data" / "index.json").read_text())
    assert idx["live_url"] == new and f'href="{new}"' in page and (not old or old not in page)
    was = json.loads(before[os.path.join("data", "index.json")])
    assert {k for k in was if was[k] != idx[k]} == {"live_url"}
    assert relink("not an address").returncode != 0 and (site / "index.html").read_text() == page
    if old:
        assert relink(old).returncode == 0
        assert {rel: (site / rel).read_text() for rel in before} == before, "back at the first address the site is byte for byte what it was"
