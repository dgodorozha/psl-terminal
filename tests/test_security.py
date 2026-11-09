"""Data desk and security: the quarantine refuses personal data and formula injection, enforces the schema
and the classification scheme, computes the event study and calibration; the posture self check and the
asset manifest behave; the ledger chain detects tampering."""

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from config import Config  # noqa: E402
from psl.ingest import quarantine, apply_calibration, persist_datasets  # noqa: E402
from psl.firms import default_firms  # noqa: E402
from psl.ledger import Ledger, verify  # noqa: E402
from psl.security import posture, classify, authorize, pii_scan, looks_like_formula, build_manifest, verify_manifest  # noqa: E402

SAMPLE = os.path.join(ROOT, "sample_data", "analogue_event_study.csv")


def test_sample_event_study_passes_and_calibrates(tmp_path):
    raw = open(SAMPLE, "rb").read()
    ds = quarantine("analogue_event_study.csv", raw, uploader="t", classification="synthetic", event_date="2024-06", maps_to="chip_designer")
    assert ds["ok"], ds.get("reason")
    assert ds["stats"]["n_months"] == 36 and ds["stats"]["beta"] is not None
    assert ds["event_study"]["event_month"] == "2024-06" and ds["event_study"]["car"] < -0.05, "the sample carries a negative abnormal return after the event"
    firms, notes = apply_calibration(default_firms(), [ds])
    chip = next(f for f in firms if f["name"] == "chip_designer")
    assert notes and 0.02 <= chip["idio_vol"] <= 0.3 and 0.2 <= chip["beta"] <= 2.5
    idx = persist_datasets([ds], str(tmp_path))
    assert idx[0]["packable"] and os.path.isfile(os.path.join(tmp_path, "data", idx[0]["file"]))
    ds2 = quarantine("x.csv", raw, classification="licensed")
    idx2 = persist_datasets([ds2], str(tmp_path / "b"))
    assert not idx2[0]["packable"] and not os.path.isfile(os.path.join(tmp_path, "b", "data", idx2[0]["file"])), "no write down"


def test_quarantine_refusals():
    pii = open(os.path.join(ROOT, "sample_data", "refused_pii_example.csv"), "rb").read()
    ds = quarantine("refused_pii_example.csv", pii)
    assert not ds["ok"] and "personal identifiers" in ds["reason"]
    assert pii_scan("call 4111 1111 1111 1111 now")
    assert looks_like_formula("=HYPERLINK(1)") and looks_like_formula("+cmd|' /C calc'!A0") and not looks_like_formula("12.5")
    bad = b"date,price\n2024-01,=1+1\n" + b"\n".join(f"2024-{m:02d},100".encode() for m in range(2, 13)) + b"\n2025-01,100\n2025-02,100\n"
    ds = quarantine("f.csv", bad)
    assert not ds["ok"] and "formula" in ds["reason"]
    ds = quarantine("f.txt", b"date,price\n2024-01,1\n")
    assert not ds["ok"] and "CSV or JSON" in ds["reason"]
    ds = quarantine("f.csv", b"foo,bar\n1,2\n")
    assert not ds["ok"] and "schema" in ds["reason"]
    ds = quarantine("f.csv", b"date,price\n2024-01,1\n2024-02,2\n")
    assert not ds["ok"] and "thirteen" in ds["reason"]
    ds = quarantine("f.csv", b"date,price\n2024-01,1\n", classification="secret")
    assert not ds["ok"] and "classification" in ds["reason"]
    assert classify("public")["packable"] and not classify("licensed")["packable"] and not classify("secret")["allowed"]


def test_roles():
    assert authorize("viewer", "ask") and not authorize("viewer", "plan")
    assert authorize("preparer", "plan") and not authorize("preparer", "gate")
    assert authorize("approver", "gate") and authorize("approver", "stop") and not authorize("approver", "plan")
    assert authorize("admin", "gate") and not authorize("nobody", "view")


def test_posture_and_manifest(tmp_path):
    cfg = Config({"PSL_SECRET": "k" * 64, "PSL_AUTH_MODE": "header", "PSL_FOUR_EYES": "1", "PSL_REGISTER": os.path.join(ROOT, "sample_data", "register.csv")})
    p = posture(cfg, root=ROOT)
    assert p["n_fail"] == 0, [i for i in p["items"] if i["status"] == "fail"]
    assert all(i["sev3"] for i in p["items"])
    weak = posture(Config({}), root=ROOT, datasets=[{"name": "x", "classification": "licensed"}])
    assert weak["n_warn"] >= 1
    ok, detail = verify_manifest(ROOT)
    assert ok, ("the shipped asset manifest must match the shipped assets", detail)


def test_ledger_detects_tampering(tmp_path):
    path = str(tmp_path / "ledger.jsonl")
    log = Ledger(path, "r1", secret="k")
    log("a", x=1); log("b", y=[1, 2]); log("c")
    rep = verify(path, "k")
    assert rep["ok"] and rep["entries"] == 3 and rep["signed"] == 3
    lines = open(path).read().splitlines()
    rec = json.loads(lines[1]); rec["payload"]["y"] = [9]
    lines[1] = json.dumps(rec)
    open(path, "w").write("\n".join(lines) + "\n")
    rep = verify(path, "k")
    assert not rep["ok"] and rep["errors"]
