"""The data desk: observed data into the Lab through one quarantine.

Two uses, both aggregate:
  calibration    a monthly (or finer) price series for a firm the authority maps onto an archetype: its
                 volatility and its beta against an optional market column replace the archetype's
                 idio_vol and beta in the next plan
  event study    the same series with an event date (a past regulatory announcement): the cumulative
                 abnormal return over the months after it, compared in assurance with the model's
                 implied early reaction

The quarantine: size and type limits, UTF 8 text only, a schema check, a
spreadsheet formula injection check, a personal identifier scan that
refuses rather than redacts, a classification with a no write down rule,
and a hash for the ledger. Raw rows never enter the briefing; the evidence pack
carries the monthly series only for public or synthetic data.
"""

import csv
import datetime
import hashlib
import io
import json
import os

import numpy as np

from .security import classify, pii_scan, looks_like_formula

ALLOWED_EXT = (".csv", ".json")
MAX_ROWS = 200000
MAX_DATASETS = 8


def quarantine(filename, content, uploader="", classification="public", max_bytes=25 * 1024 * 1024,
               event_date=None, maps_to=None, note=""):
    """Validate bytes into a dataset record or a refusal."""
    name = (filename or "").strip()
    ext = ("." + name.rsplit(".", 1)[-1].lower()) if "." in name else ""
    rec = {"name": name, "uploader": uploader, "classification": classification, "ok": False,
           "uploaded": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")}
    cls = classify(classification)
    if not cls["allowed"]:
        return dict(rec, reason=f"classification '{classification}' refused: {cls['note']}")
    if ext not in ALLOWED_EXT:
        return dict(rec, reason="only CSV or JSON files are accepted")
    if len(content) > max_bytes:
        return dict(rec, reason=f"file exceeds {max_bytes // (1024 * 1024)} MB")
    if b"\x00" in content[:4096]:
        return dict(rec, reason="binary content refused")
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        return dict(rec, reason="file is not UTF 8 text")
    hits = pii_scan(text)
    if hits:
        return dict(rec, reason="personal identifiers found (" + ", ".join(f"{k} {v}" for k, v in hits.items())
                    + "); personal data is refused, not redacted")
    try:
        if ext == ".json":
            data = json.loads(text)
            rows = data if isinstance(data, list) else data.get("rows") or data.get("data")
            if not isinstance(rows, list) or not rows or not all(isinstance(r, dict) for r in rows):
                return dict(rec, reason="JSON must be a list of row objects or {rows: [...]}")
        else:
            rows = [r for r in csv.DictReader(io.StringIO(text))]
    except Exception as e:  # noqa: BLE001
        return dict(rec, reason=f"could not parse: {str(e)[:120]}")
    if not rows:
        return dict(rec, reason="no rows")
    if len(rows) > MAX_ROWS:
        return dict(rec, reason=f"more than {MAX_ROWS} rows")
    rows = [{(k.strip().lower() if k else k): v for k, v in r.items()} for r in rows]
    cols = [c for c in rows[0].keys() if c]
    formula = sum(1 for r in rows[:5000] for v in r.values() if isinstance(v, str) and looks_like_formula(v))
    if formula:
        return dict(rec, reason=f"{formula} cells begin with a formula character; refused (spreadsheet injection)")
    tcol = next((c for c in ("date", "month", "timestamp", "time", "period") if c in cols), None)
    pcol = next((c for c in ("price", "close", "adj_close", "px_last", "last", "value", "index") if c in cols), None)
    mcol = next((c for c in ("market", "benchmark", "index_level", "spx", "nasdaq") if c in cols and c != pcol), None)
    if tcol is None or pcol is None:
        return dict(rec, reason="schema: need a date column and a price column (optional: a market column)")
    try:
        series = [(str(r[tcol])[:7], float(str(r[pcol]).replace(",", ""))) for r in rows if r.get(pcol) not in (None, "")]
        market = [float(str(r[mcol]).replace(",", "")) for r in rows if r.get(pcol) not in (None, "")] if mcol else None
    except ValueError:
        return dict(rec, reason="price or market column is not numeric")
    # monthly: take the last observation of each month, in order
    months, prices, mkt = [], [], []
    seen = {}
    for i, (m, p) in enumerate(series):
        seen[m] = i
    for m in sorted(seen):
        i = seen[m]
        months.append(m); prices.append(series[i][1])
        if market is not None:
            mkt.append(market[i])
    if len(prices) < 13:
        return dict(rec, reason="at least thirteen months of prices are needed")
    sha = hashlib.sha256(content).hexdigest()
    out = dict(rec, ok=True, n_rows=len(rows), months=months, sha256=sha, size=len(content), columns=cols,
               schema={"date": tcol, "price": pcol, "market": mcol}, packable=cls["packable"], maps_to=maps_to or "",
               note=note[:200], stats=stats(prices, mkt if market is not None else None),
               monthly={"price": [float(x) for x in prices], "market": ([float(x) for x in mkt] if market is not None else None)},
               provenance={"uploaded_by": uploader, "sha256": sha, "bytes": len(content), "classification": classification})
    if event_date:
        ed = str(event_date)[:7]
        if ed in months:
            from .assurance import analogue
            es = analogue(prices, months.index(ed), market=mkt if market is not None else None)
            if es:
                es["event_month"] = ed
                out["event_study"] = es
        else:
            out["event_note"] = f"event month {ed} not in the series ({months[0]} to {months[-1]})"
    return out


def stats(prices, market=None):
    p = np.asarray(prices, dtype=float)
    r = np.diff(np.log(p))
    out = {"n_months": int(len(p)), "monthly_vol": float(r.std(ddof=1)) if len(r) > 2 else None,
           "annual_vol": float(r.std(ddof=1) * np.sqrt(12)) if len(r) > 2 else None,
           "mean_monthly_return": float(r.mean()) if len(r) else None}
    if market is not None and len(market) == len(p):
        m = np.diff(np.log(np.asarray(market, dtype=float)))
        if m.std() > 0:
            beta = float(np.cov(r, m, ddof=1)[0, 1] / m.var(ddof=1))
            resid = r - beta * m
            out["beta"] = beta
            out["idio_monthly_vol"] = float(resid.std(ddof=1))
    return out


def dataset_summary(ds):
    s = ds.get("stats") or {}
    bits = [f"{ds['name']} ({ds['classification']}, {ds.get('n_rows', 0)} rows, {s.get('n_months', 0)} months)"]
    if s.get("annual_vol") is not None:
        bits.append(f"annual vol {s['annual_vol']:.0%}")
    if s.get("beta") is not None:
        bits.append(f"beta {s['beta']:.2f}")
    if ds.get("maps_to"):
        bits.append(f"maps to {ds['maps_to']}")
    if ds.get("event_study"):
        bits.append(f"event {ds['event_study']['event_month']}: CAR {ds['event_study']['car'] * 100:+.1f}%")
    return "; ".join(bits)


def apply_calibration(firms, datasets):
    """Firm templates with idio_vol and beta replaced by a mapped dataset's estimates; returns (firms, notes)."""
    notes = []
    out = [dict(f) for f in firms]
    for ds in datasets or []:
        if not ds.get("maps_to"):
            continue
        s = ds.get("stats") or {}
        for f in out:
            if f["name"] == ds["maps_to"] or f["label"] == ds["maps_to"]:
                if s.get("idio_monthly_vol") is not None:
                    f["idio_vol"] = float(min(0.3, max(0.02, s["idio_monthly_vol"])))
                    f["beta"] = float(min(2.5, max(0.2, s["beta"])))
                    notes.append(f"{f['label']}: idio vol {f['idio_vol']:.3f} and beta {f['beta']:.2f} from {ds['name']}")
                elif s.get("monthly_vol") is not None:
                    f["idio_vol"] = float(min(0.3, max(0.02, s["monthly_vol"] * 0.8)))
                    notes.append(f"{f['label']}: idio vol {f['idio_vol']:.3f} from {ds['name']} (no market column, 80% of total)")
    return out, notes


def persist_datasets(datasets, run_dir):
    """Write the dataset index into the run directory and, for public or synthetic datasets, the monthly
    series the Lab actually used (date, price, market), so a second authority can recompute the event
    study from the evidence pack. Licensed or pseudonymised series stay out (no write down)."""
    d = os.path.join(run_dir, "data")
    os.makedirs(d, exist_ok=True)
    index = []
    for ds in datasets:
        base = os.path.basename(ds["name"]).rsplit(".", 1)[0]
        fname = f"{base}.monthly.csv"
        if ds.get("packable") and ds.get("monthly"):
            with open(os.path.join(d, fname), "w", newline="") as f:
                w = csv.writer(f)
                w.writerow(["month", "price"] + (["market"] if ds["monthly"].get("market") else []))
                for i, m in enumerate(ds["months"]):
                    row = [m, f"{ds['monthly']['price'][i]:.6g}"]
                    if ds["monthly"].get("market"):
                        row.append(f"{ds['monthly']['market'][i]:.6g}")
                    w.writerow(row)
        index.append({"name": ds["name"], "classification": ds["classification"], "sha256": ds["sha256"], "n_rows": ds.get("n_rows"),
                      "stats": ds.get("stats"), "event_study": ds.get("event_study"), "maps_to": ds.get("maps_to"),
                      "packable": ds.get("packable", False), "file": fname, "uploaded": ds.get("uploaded")})
    with open(os.path.join(d, "index.json"), "w") as f:
        json.dump(index, f, indent=1)
    return index


def keep_recent(datasets, limit=MAX_DATASETS):
    return datasets[-limit:]
