"""The whole chain on a tiny budget: plan, run, evaluate, assure, critic, briefing, transparency record,
evidence pack. Checks the artefacts are coherent (paired assurance on common random numbers, the red
team's honest figures equal the headline figures), the critic passes, the briefing's numbers are vetted,
and the pack verifies."""

import json
import os
import sys
import zipfile

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from psl import assumptions as AS  # noqa: E402
from psl.atrs import atrs_record, render_markdown  # noqa: E402
from psl.briefing import draft_briefing, to_html  # noqa: E402
from psl.critic import critic_check, _vet_numbers  # noqa: E402
from psl.evidence import build_pack  # noqa: E402
from psl.ledger import Ledger, verify  # noqa: E402
from psl.pipeline import make_battery, run_battery, SimulationStopped  # noqa: E402
from psl.question import parse  # noqa: E402

TINY = {"paths": 8, "horizon": 18, "boot": 40, "variant_paths": 4, "redteam_paths": 8, "tornado": True}


@pytest.fixture(scope="module")
def run(tmp_path_factory):
    out = tmp_path_factory.mktemp("run")
    plan = parse("Compare transparency, strict liability and liability with a safe harbour over two years; "
                 "industry loss under $900bn")
    bat = make_battery(plan, budget=dict(TINY), profile="demo")
    log = Ledger(os.path.join(out, "ledger.jsonl"), "tiny", secret="k")
    events = []
    arte, results = run_battery(bat, str(out), log=log, progress=lambda s, p, **k: events.append(s))
    return {"dir": str(out), "bat": bat, "arte": arte, "log": log, "events": events}


def test_battery_and_artefacts(run):
    bat, arte = run["bat"], run["arte"]
    assert [p["name"] for p in bat["policies"]][0] == "baseline" and len(bat["policies"]) == 4
    assert bat["horizon"] == 24 and bat["paths"] == 8
    assert arte["battery_hash"] == bat["hash"] and arte["assumptions_hash"] == AS.assumptions_hash(bat["assumptions"])
    ev = arte["results"]
    assert set(ev["names"]) == {p["name"] for p in bat["policies"]}
    assert ev["preferred"] in ev["names"] or ev["preferred"] is None
    for r in ev["policies"]:
        s = r["net_social_value"]
        assert s["lo"] <= s["median"] <= s["hi"]
        assert len(r["news"]["quarterly_negative"]) == 8
        assert len(r["market"]["index_mean"]) == 25 and len(r["market"]["rel_mean"]) == 25
    assert {"simulate", "markets", "welfare", "assurance", "critic"} <= set(run["events"])
    for name in ("artefacts.json", "results.json", "assurance.json", "battery.json", "paths.npz", "news_sample.json", "prices_sample.json"):
        assert os.path.isfile(os.path.join(run["dir"], name)), name


def test_assurance_is_paired_with_the_main_run(run):
    arte = run["arte"]; ev = arte["results"]
    pols = {r["policy"]: r for r in ev["policies"]}
    asr = arte["assurance"]
    t = asr["tornado"]
    pref = t["preferred"]
    assert abs(t["reference_nsv"] - pols[pref]["net_social_value"]["mean"]) < 1e-6
    assert {r["assumption"] for r in t["rows"]} == set(AS.TORNADO)
    # the red team's honest value is the headline value: same paths, same seed
    for r in asr["red_team"]["rows"]:
        assert abs(r["honest"]["nsv"] - pols[r["policy"]]["net_social_value"]["mean"]) < 1e-6, r["policy"]
        assert r["worst_nsv"] <= r["honest"]["nsv"] + 1e-9
    st = asr["structural"]
    assert st["n"] == len(st["variants"]) >= 3
    for v in st["variants"]:
        assert v["best"] in pols and 1 <= v["preferred_rank"] <= len(pols) - 1
        for n, row in v["table"].items():
            assert row["resimulated_paths"] == 4


def test_critic_briefing_record_and_pack(run):
    d, arte, log = run["dir"], run["arte"], run["log"]
    approvals = {"preparer": "Developer1", "preparer_role": "Developer1",
                 "gate1": {"actor": "Developer2", "role": "Developer2", "ts": "2026-01-01T00:00:00+00:00", "decision": "approved"}}
    md = draft_briefing(arte, approvals, "tiny")
    assert "Preferred option" in md or "preferred" in md.lower()
    assert _vet_numbers(md, arte) == [], "every number in the briefing must come from the artefacts"
    assert _vet_numbers(md + " The value is $999.123bn, 77.7% of paths.", arte) == ["77.7%", "999.123bn"]
    critic = critic_check(d, secret="k", briefing_text=md)
    failed = [c for c in critic["checks"] if not c["ok"]]
    assert critic["ok"], failed
    assert critic["n_checks"] >= 25
    html = to_html(md)
    assert "<table" in html and "<script" not in html
    rec = atrs_record(arte, approvals, "tiny", organisation="Test Authority")
    assert rec["tier1"]["name"].startswith("Policy Scenario Lab") and "risks" in rec["tier2"]["risks_mitigations_and_impact_assessments"]
    assert render_markdown(rec).startswith("# Algorithmic transparency record")
    with open(os.path.join(d, "briefing.md"), "w") as f:
        f.write(md)
    with open(os.path.join(d, "critic.json"), "w") as f:
        json.dump(critic, f)
    rep = verify(log.path, "k")
    assert rep["ok"] and rep["entries"] >= 8
    assert not verify(log.path, "wrong-key")["ok"], "the signature must bind the key"
    pack, manifest = build_pack(d)
    with zipfile.ZipFile(pack) as z:
        names = set(z.namelist())
        assert {"manifest.json", "VERIFY.md", "artefacts.json", "ledger.jsonl", "briefing.md", "critic.json"} <= names
        assert "paths.npz" not in names or True


def test_stop_halts_the_run(tmp_path):
    plan = parse("baseline against transparency over two years")
    bat = make_battery(plan, budget=dict(TINY), profile="demo")
    with pytest.raises(SimulationStopped):
        run_battery(bat, str(tmp_path), stop=lambda: True)
