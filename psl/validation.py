"""The validation layer: what evidence can and cannot say about the model.

Three things are confronted with data here.

1. Published benchmarks (benchmarks.py). Each is one observable quantity with a published value: the growth of
   recorded AI incidents, the trend of public trust, what a compliance regime did to profits and to share prices, how
   much regulated activity moved abroad. For each the model's own value of the same quantity (a moment of the
   simulation, or a declared assumption) is computed and compared:

     at the central assumptions   z = (model - observed) / sqrt(se_obs^2 + transport^2 + se_model^2), where se_obs is
                                  the benchmark's standard error, transport the allowance for the distance between
                                  the measured setting and the model's (declared per benchmark, with its reason) and
                                  se_model the Monte Carlo error of the moment (a jackknife over paths). |z| <= 2 is
                                  reported as not contradicted, 2 to 3 as in tension, above 3 as contradicted.
     under the declared ranges    the same moment in every draw of the joint draw gives the model's prior predictive
                                  distribution; where the observation falls in it is reported.
     calibration                  each draw is weighted by how well it reproduces the benchmarks (a Gaussian
                                  likelihood with the variance above): importance sampling from the prior. The
                                  weighted draws are a posterior over the assumptions given the benchmarks and the
                                  allowances, and the share of them in which each alternative is the decision is
                                  reported beside the unweighted share. The effective number of draws says how far
                                  that can be trusted. History matching is reported with it: the share of draws no
                                  benchmark rules out at three standard deviations.
     held out checks              each calibration benchmark is predicted from the draws weighted by all the others
                                  (leave one out), so a benchmark is never judged only against a fit that used it.

   This cannot validate the model. It can show where the model is a poor description, which assumptions the
   evidence bears on, and which it leaves untouched; a benchmark from another sector with a wide allowance is weak
   evidence and is treated as such. Mechanisms with no benchmark are listed as unconfronted.

2. The market's early reaction to a regulatory announcement, through an event study on a price series the analyst
   uploads and maps to a firm archetype and to the instrument the historical event is an analogue of.

3. The mechanism register (mechanisms.py) records, for each mechanism, what evidence would test it; a run adds to
   each mechanism the benchmarks that bore on it and what they showed.

Event time convention (one convention, used for the estimate and stated in the output):
  the series is monthly closes p_0, ..., p_T; the return of month k is r_k = ln(p_k / p_{k-1});
  the event month E is the month the announcement falls in, so r_E is the first return that can contain it;
  estimation window: the EST_WINDOW = 24 returns r_{E-24}, ..., r_{E-1}; all 24 are required, a shorter history is
      refused rather than silently shortened;
  event window: the EVENT_WINDOW = 6 returns r_E, ..., r_{E+5} (months 0 to 5 after the event);
  abnormal return: r_k minus the market model alpha + beta m_k fitted on the estimation window (minus the
      estimation window mean when there is no market column);
  CAR_j: the sum of the abnormal returns of months 0 to j; the early reaction is the mean over j = 0..5 of
      exp(CAR_j) - 1, the average level of the price against its counterfactual over the six months, which is
      what the model's early reaction measures (the index against the status quo over months 1 to 6 after the
      announcement, month 1 being the first month end after it).

Calibration of a firm's volatility and beta is held out: when an event month is given they are estimated on the
returns before it, so the event window never informs the parameters it is compared with.

A single event cannot establish calibration. With several mapped events the Lab reports how many fall inside the
model's 10th to 90th percentile band and the exact binomial test of that count against the band's nominal 80%.
"""

import numpy as np

from .stats import benjamini_hochberg, binomial_coverage, spearman_test

EST_WINDOW = 24
EVENT_WINDOW = 6
MIN_EVENTS_FOR_COVERAGE = 8


def event_study(prices, event_index, market=None, est=EST_WINDOW, window=EVENT_WINDOW):
    """Event study on monthly closes around the event month. Returns a dict, or {'refused': reason}."""
    p = np.asarray(prices, dtype=float)
    E = int(event_index)
    if not np.all(np.isfinite(p)) or np.any(p <= 0):
        return {"refused": "prices must be positive and finite"}
    if E - est - 1 < 0:
        return {"refused": f"the estimation window needs {est} monthly returns before the event month; the series has {max(E - 1, 0)}"}
    if len(p) < E + window:
        return {"refused": f"the event window needs {window} months from the event month; the series has {len(p) - E}"}
    r = np.diff(np.log(p))                      # r[k] is the return of month k + 1
    est_ix = slice(E - est - 1, E - 1)          # months E - est, ..., E - 1
    ev_ix = slice(E - 1, E - 1 + window)        # months E, ..., E + window - 1
    T = est
    if market is not None:
        mk = np.asarray(market, dtype=float)
        if len(mk) != len(p) or not np.all(np.isfinite(mk)) or np.any(mk <= 0):
            return {"refused": "the market column must be positive, finite and as long as the price column"}
        m = np.diff(np.log(mk))
        X = np.vstack([np.ones(T), m[est_ix]]).T
        coef = np.linalg.lstsq(X, r[est_ix], rcond=None)[0]
        alpha, beta = float(coef[0]), float(coef[1])
        resid = r[est_ix] - X @ coef
        s2 = float(resid @ resid / (T - 2))
        ar = r[ev_ix] - (alpha + beta * m[ev_ix])
        mbar = float(m[est_ix].mean()); sxx = float(((m[est_ix] - mbar) ** 2).sum())
        # variance of the cumulative abnormal return with the estimation error of alpha and beta
        var_car = s2 * (window + window ** 2 / T + (float((m[ev_ix] - mbar).sum()) ** 2 / sxx if sxx > 0 else 0.0))
        model = "market model"
    else:
        alpha, beta = float(r[est_ix].mean()), None
        resid = r[est_ix] - alpha
        s2 = float(resid @ resid / (T - 1))
        ar = r[ev_ix] - alpha
        var_car = s2 * (window + window ** 2 / T)
        model = "mean adjusted"
    car_j = np.cumsum(ar)
    car = float(car_j[-1])
    early = float(np.mean(np.exp(car_j) - 1.0))
    w = (window - np.arange(window)) / window           # weight of each month's abnormal return in the mean level
    se_car = float(np.sqrt(max(var_car, 0.0)))
    return {"car": car, "se_car": se_car, "t_car": float(car / se_car) if se_car > 0 else None,
            "early_reaction": early, "se_early": float(np.sqrt(s2 * float((w ** 2).sum()))),
            "alpha": alpha, "beta": beta, "resid_sd": float(np.sqrt(s2)), "n_est": int(T), "model": model,
            "window_months": [0, window - 1], "event_index": E, "n": int(len(p)),
            "convention": f"estimation on the {T} monthly returns before the event month; abnormal returns over months 0 to {window - 1}, "
                          f"month 0 being the event month"}


def _firm_index(firms, key):
    for f, x in enumerate(firms):
        if key and (x.get("name") == key or x.get("label") == key):
            return f
    return None


def compare(datasets, ev, reds, firms):
    """Each uploaded event study against the model's predictive distribution of the early reaction. Returns a list
    of per dataset records and a coverage summary (None when no event is mapped to an instrument)."""
    out, inside, mapped = [], 0, 0
    B = reds["baseline"]
    names = [r["policy"] for r in ev["policies"]]
    for ds in datasets or []:
        es = ds.get("event_study")
        if not es:
            continue
        f = _firm_index(firms, ds.get("maps_to"))
        rows = []
        for r in ev["policies"]:
            if r["policy"] == "baseline":
                continue
            x = _early_paths(reds[r["policy"]], B, f)
            rows.append({"policy": r["policy"], "model_early_reaction": float(x.mean()), "lo": float(np.percentile(x, 10)),
                         "hi": float(np.percentile(x, 90))})
        rec = {"dataset": ds.get("name"), "classification": ds.get("classification"), "event_study": es, "rows": rows,
               "maps_to": ds.get("maps_to") or None, "level": "firm" if f is not None else "index",
               "analogue_of": ds.get("analogue_of") or None, "note": ds.get("note", "")}
        target = ds.get("analogue_of")
        if target in names and target != "baseline":
            x = _early_paths(reds[target], B, f)
            obs = es["early_reaction"]
            lo, hi = float(np.percentile(x, 10)), float(np.percentile(x, 90))
            sd = float(x.std(ddof=1))
            rec["comparison"] = {"policy": target, "observed": obs, "observed_se": es["se_early"], "model_mean": float(x.mean()),
                                 "model_lo": lo, "model_hi": hi, "pit": float((x <= obs).mean()),
                                 "z": float((obs - x.mean()) / np.sqrt(sd ** 2 + es["se_early"] ** 2)) if sd > 0 or es["se_early"] > 0 else None,
                                 "within_band": bool(lo <= obs <= hi)}
            mapped += 1; inside += int(lo <= obs <= hi)
        else:
            rec["comparison"] = None
        out.append(rec)
    cov = None
    if mapped:
        cov = {"events": mapped, "inside": inside, "nominal": 0.8, "share": inside / mapped,
               "p_value": binomial_coverage(inside, mapped, 0.8) if mapped >= MIN_EVENTS_FOR_COVERAGE else None,
               "assessable": mapped >= MIN_EVENTS_FOR_COVERAGE,
               "statement": (f"{inside} of {mapped} mapped events fall inside the model's 10th to 90th percentile band"
                             + ("" if mapped >= MIN_EVENTS_FOR_COVERAGE else
                                f"; at least {MIN_EVENTS_FOR_COVERAGE} events are needed before the coverage of the band can be tested, so this is an "
                                f"illustration and not evidence of calibration"))}
    return out, cov


def _early_paths(R, B, f):
    """Per path early reaction against the status quo over months 1 to 6: of firm f, or of the index."""
    if f is not None and "price_early_f" in R:
        return (R["price_early_f"][:, 1:7, f] / B["price_early_f"][:, 1:7, f] - 1.0).mean(axis=1)
    return (R["idx_early"] / B["idx_early"] - 1.0).mean(axis=1)


# ------------------------------------------------------------- benchmarks --
CONSISTENT, TENSION, CONTRADICTED = "not contradicted", "in tension", "contradicted"
MIN_DEFINED = 0.8        # a benchmark enters the calibration when its moment is defined in at least this share of the draws
MIN_ESS = 20.0           # fewer effective draws than this and the weighted shares are reported as unreliable
RULE_OUT = 3.0           # history matching: a draw is ruled out when a benchmark is this many standard deviations away
FORM_Z = 2.0             # a benchmark that even the closest tenth of the draws miss by more than this many standard
                         # deviations is a failure of the model's form, not of a parameter value: it is reported as one and
                         # left out of the weights, which it would otherwise decide (the draws that miss it least would
                         # carry all the weight for no reason to do with the mechanisms the other benchmarks test)
FDR = 0.10               # false discovery rate at which an assumption is said to be informed by a benchmark


def verdict(z):
    if z is None or not np.isfinite(z):
        return None
    return CONSISTENT if abs(z) <= 2.0 else (TENSION if abs(z) <= 3.0 else CONTRADICTED)


def _ratio(m):
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.where(m[..., 1] != 0, m[..., 0] / np.where(m[..., 1] != 0, m[..., 1], 1.0), np.nan)


def _growth(m):
    """Average annual growth of yearly counts m[..., y]: the least squares slope of their logs, as a rate."""
    Y = m.shape[-1]
    x = np.arange(Y) - (Y - 1) / 2.0
    with np.errstate(divide="ignore", invalid="ignore"):
        lg = np.log(m)
    return np.exp((lg * x).sum(axis=-1) / (x ** 2).sum()) - 1.0


def _ingredients(name, P, B, pol, H):
    """Per path ingredients X (N, m) of a moment and the function g that turns their path means into the moment.
    P: the reduced instrument (with the moment keys), B: the reduced status quo on the same paths."""
    ph = int(min(max(pol.get("phase_in", 0), 0), H - 1)) if pol else 0
    if name == "incident_growth":
        Y = H // 12
        if Y < 2:
            return None, None
        return P["m_inc_exp"][:, :Y * 12].reshape(-1, Y, 12).sum(axis=2), _growth
    if name == "trust_trend":
        return P["trust"][:, -1:], (lambda m: m[..., 0] ** (12.0 / H) - 1.0)
    if name == "compliance_cost_share":
        return np.stack([P["compliance"][:, ph:].sum(axis=1), P["m_rd_scope"][:, ph:].sum(axis=1)], axis=1), _ratio
    if name == "profit_effect":
        return (np.stack([P["earnings_exp"][:, ph:].sum(axis=1), B["earnings_exp"][:, ph:].sum(axis=1)], axis=1),
                lambda m: _ratio(m) - 1.0)
    if name == "enforcement_return":
        d = np.log(P["m_idx"][:, ph + 1] / P["m_idx"][:, ph]) - np.log(B["m_idx"][:, ph + 1] / B["m_idx"][:, ph])
        return d[:, None], (lambda m: m[..., 0])
    if name == "fine_return":
        return np.stack([P["m_fine_ar"], P["m_fine_n"]], axis=1), _ratio
    if name == "incident_return":
        return np.stack([P["m_major_ar"], P["m_major_n"]], axis=1), _ratio
    if name == "leakage_share":
        return np.stack([P["offshore_revenue"][:, -12:].sum(axis=1), P["m_rev_scope"][:, -12:].sum(axis=1)], axis=1), _ratio
    raise KeyError(name)


MOMENTS = ("incident_growth", "trust_trend", "compliance_cost_share", "profit_effect", "enforcement_return", "fine_return",
           "incident_return", "leakage_share")
_EVENT_COUNT = {"fine_return": 1, "incident_return": 1}       # column of the ingredient that counts the events


def moment(name, P, B, pol, H, blocks=1):
    """The moment in each of `blocks` equal blocks of paths: (values (blocks,), jackknife variances (blocks,)).
    A block where the moment is undefined (no event to average over) is NaN."""
    X, g = _ingredients(name, P, B, pol, H)
    if X is None:
        return np.full(blocks, np.nan), np.full(blocks, np.nan)
    n = X.shape[0] // blocks
    Xb = np.asarray(X, dtype=float).reshape(blocks, n, -1)
    tot = Xb.sum(axis=1)
    with np.errstate(divide="ignore", invalid="ignore"):
        val = g(tot / n)
        if n > 1:
            vj = g((tot[:, None, :] - Xb) / (n - 1))                               # leave one path out, (blocks, n)
            var = (n - 1) / n * ((vj - vj.mean(axis=1, keepdims=True)) ** 2).sum(axis=1)
        else:
            var = np.zeros(blocks)
    if name in _EVENT_COUNT:                                                       # fewer than two events: nothing to average
        few = tot[:, _EVENT_COUNT[name]] < 2
        val = np.where(few, np.nan, val); var = np.where(few, np.nan, var)
    var = np.where(np.isfinite(val) & ~np.isfinite(var), np.inf, var)
    return np.asarray(val, dtype=float), np.asarray(var, dtype=float)


def transform(spec, x):
    """A declared assumption mapped onto a benchmark's scale."""
    x = np.asarray(x, dtype=float)
    if not spec:
        return x
    if spec.get("name") == "recovered_fraction":
        return 1.0 - (1.0 - np.clip(x, 0.0, 1.0)) ** float(spec.get("months", 9))
    raise ValueError(f"unknown transform {spec}")


def instruments_needed(benchmarks):
    """The library instruments the benchmarks' moments are computed under (the status quo aside)."""
    return sorted({b["instrument"] for b in benchmarks if b["moment"] != "assumption" and b.get("instrument") not in (None, "baseline")})


def central(benchmarks, reds, a, policies, H):
    """Each benchmark against the model at its central assumptions. reds: reduced policies with the moment keys
    (the main run, with any instrument the battery lacks simulated beside it on its first paths)."""
    rows = []
    B = reds.get("baseline")
    for b in benchmarks:
        row = {"id": b["id"], "title": b["title"], "mechanisms": list(b["mechanisms"]), "kind": b["kind"], "unit": b["unit"],
               "observed": b["value"], "se": b["se"], "transport": float(b["transport"]), "sd_total": b["sd_total"],
               "moment": b["moment"], "instrument": b.get("instrument"), "assumption": b.get("assumption"),
               "n_observations": b["n_observations"], "model": None, "model_se": None, "z": None, "verdict": None, "why_not": None}
        if b["moment"] == "assumption":
            row["model"] = float(transform(b.get("transform"), a[b["assumption"]])); row["model_se"] = 0.0
        else:
            P = reds.get(b["instrument"])
            if P is None or B is None or "m_idx" not in P:
                row["why_not"] = "the instrument the benchmark is defined under was not simulated"
            else:
                n = int(min(P["n_paths"], B["n_paths"]))
                v, var = moment(b["moment"], _first(P, n), _first(B, n), policies.get(b["instrument"]), H)
                if np.isfinite(v[0]):
                    row["model"] = float(v[0]); row["model_se"] = float(np.sqrt(var[0])) if np.isfinite(var[0]) else None
                    row["paths"] = n
                else:
                    row["why_not"] = ("the horizon is too short for the moment" if b["moment"] == "incident_growth"
                                      else "the event the moment averages over did not occur on these paths")
        if row["model"] is not None:
            den = np.sqrt(b["sd_total"] ** 2 + (row["model_se"] or 0.0) ** 2)
            row["z"] = float((row["model"] - b["value"]) / den) if den > 0 else None
            row["verdict"] = verdict(row["z"])
        rows.append(row)
    return rows


def _first(R, n):
    if R["n_paths"] == n:
        return R
    out = dict(R)
    for k, v in R.items():
        if isinstance(v, np.ndarray) and v.shape[:1] == (R["n_paths"],):
            out[k] = v[:n]
    out["n_paths"] = n
    return out


def draw_moments(benchmarks, dreds, S, policies, H, draws):
    """Every benchmark's moment in every joint draw: {id: (values (draws,), variances (draws,))}. dreds: the reduced
    design (draws x n paths per policy, with the moment keys); S: the drawn assumptions {key: (draws,)}."""
    out = {}
    B = dreds.get("baseline")
    for b in benchmarks:
        if b["moment"] == "assumption":
            if b["assumption"] in S:
                out[b["id"]] = (transform(b.get("transform"), S[b["assumption"]]), np.zeros(draws))
            continue
        P = dreds.get(b["instrument"])
        if P is None or B is None or "m_idx" not in P:
            continue
        out[b["id"]] = moment(b["moment"], P, B, policies.get(b["instrument"]), H, blocks=draws)
    return out


def _wq(x, w, q):
    """Weighted quantile of x."""
    o = np.argsort(x)
    cw = np.cumsum(w[o]); cw = cw / cw[-1]
    return float(x[o][min(int(np.searchsorted(cw, q)), len(x) - 1)])


def calibrate(benchmarks, rows, per_draw, names, focus, a, ranges=None, accounting_only=()):
    """Weight the joint draws by the benchmarks. rows: central() output (the prior predictive columns are added to
    it in place). per_draw: {"S", "best", "ok", "nsv", "moments"} from the joint draw. Returns the calibration report."""
    S, best, mom = per_draw["S"], list(per_draw["best"]), per_draw["moments"]
    D = len(best)
    by = {b["id"]: b for b in benchmarks}
    Z, used = {}, []
    for r in rows:
        if r["id"] not in mom:
            continue
        v, var = mom[r["id"]]
        b = by[r["id"]]
        ok = np.isfinite(v)
        r["defined_share"] = float(ok.mean())
        if ok.sum() < 5:
            continue
        pooled = float(np.median(var[ok & np.isfinite(var)])) if (ok & np.isfinite(var)).any() else 0.0     # the draws' Monte Carlo variance, pooled
        sd = np.sqrt(b["sd_total"] ** 2 + pooled)
        z = np.where(ok, (v - b["value"]) / sd, 0.0)
        Z[r["id"]] = (z, ok, sd, v)
        x = v[ok]
        r["prior"] = {"lo": float(np.percentile(x, 5)), "median": float(np.median(x)), "hi": float(np.percentile(x, 95)),
                      "pit": float((x <= b["value"]).mean()), "mc_sd": float(np.sqrt(pooled)),
                      "inside": bool(np.percentile(x, 5) - 1.645 * b["sd_total"] <= b["value"] <= np.percentile(x, 95) + 1.645 * b["sd_total"])}
        r["reach"] = float((np.abs(z[ok]) <= RULE_OUT).mean())          # share of the draws that reproduce the benchmark
        r["closest"] = float(np.percentile(np.abs(z[ok]), 10))           # how far the closest tenth of the draws are from it
        r["structural"] = bool(r["closest"] > FORM_Z)
        if ok.mean() >= MIN_DEFINED and not r["structural"]:
            used.append(r["id"])
    if not used:
        return {"draws": D, "used": [], "reliable": False, "note": "no benchmark has a moment defined in enough draws to weight them"}

    def weights(ids):
        lw = -0.5 * sum(Z[i][0] ** 2 for i in ids) if ids else np.zeros(D)
        w = np.exp(lw - lw.max())
        return w / w.sum()

    w = weights(used)
    ess = float(1.0 / (w ** 2).sum())
    keep = np.ones(D, dtype=bool)
    ruled = {}
    for i in used:
        out_i = np.abs(Z[i][0]) > RULE_OUT
        ruled[i] = float(out_i.mean())
        keep &= ~out_i
    for r in rows:
        if r["id"] in Z:
            z, ok, sd, v = Z[r["id"]]
            ww = w[ok] / w[ok].sum()
            r["posterior"] = {"mean": float((ww * v[ok]).sum()), "lo": _wq(v[ok], ww, 0.05), "hi": _wq(v[ok], ww, 0.95)}
            if r["id"] in used:                      # held out: predicted from the draws weighted by every other benchmark
                wo = weights([i for i in used if i != r["id"]])
                wo = wo[ok] / wo[ok].sum()
                mu = float((wo * v[ok]).sum())
                sp = float(np.sqrt((wo * (v[ok] - mu) ** 2).sum()))
                r["held_out"] = {"mean": mu, "sd": sp, "z": float((mu - by[r["id"]]["value"]) / np.sqrt(sp ** 2 + sd ** 2)),
                                 "ess": float(1.0 / (wo ** 2).sum())}
                r["held_out"]["verdict"] = verdict(r["held_out"]["z"])
                r["ruled_out_share"] = ruled[r["id"]]
            r["used"] = r["id"] in used
    alts = list(names) + [None]

    def shares(weight):
        tot = float(weight.sum())
        return {("none" if nm is None else nm): (float(sum(weight[j] for j, bb in enumerate(best) if bb == nm)) / tot if tot > 0 else None) for nm in alts}

    fi = names.index(focus) if focus in names else None
    ok_f = np.asarray(per_draw["ok"])[fi] if fi is not None else None
    nsv_f = np.asarray(per_draw["nsv"])[fi] if fi is not None else None
    acc = (ok_f & (nsv_f > 0)) if fi is not None else None
    # which assumptions the benchmarks bear on: an assumption is informed by a benchmark when the benchmark's moment
    # moves with it across the draws (rank correlation, at a 10% false discovery rate over every assumption and
    # benchmark pair). That is a property of the model, not of the weights, so it does not ride on their noise.
    keys = [k for k, x in S.items() if np.std(np.asarray(x, dtype=float)) > 0]
    simulated = [k for k in keys if k not in accounting_only]        # an accounting assumption cannot move a simulated moment
    pairs, pvals = [], []
    for i in used:
        z, ok, sd, v = Z[i]
        direct = by[i].get("assumption") if by[i]["moment"] == "assumption" else None
        if direct is not None:
            pairs.append((direct, i, 1.0)); pvals.append(0.0)
            continue
        for k in simulated:
            rho, pv = spearman_test(np.asarray(S[k], dtype=float)[ok], v[ok])
            pairs.append((k, i, rho)); pvals.append(pv)
    flags = benjamini_hochberg(pvals, FDR) if pvals else []
    links = {}
    for (k, i, rho), fl in zip(pairs, flags):
        if fl:
            links.setdefault(k, []).append({"benchmark": i, "rho": float(rho)})
    moved = []
    for k in keys:
        x = np.asarray(S[k], dtype=float)
        m0, s0 = float(x.mean()), float(x.std(ddof=1))
        m1 = float((w * x).sum()); s1 = float(np.sqrt((w * (x - m1) ** 2).sum()))
        moved.append({"assumption": k, "default": float(a[k]), "prior_mean": m0, "posterior_mean": m1, "shift": (m1 - m0) / s0, "shrink": s1 / s0,
                      "posterior_lo": _wq(x, w, 0.05), "posterior_hi": _wq(x, w, 0.95),
                      "range": list(ranges[k]) if ranges and k in ranges else None,
                      "informed_by": sorted(links.get(k, []), key=lambda e: -abs(e["rho"])), "informed": k in links})
    noise = 2.0 / np.sqrt(max(ess, 1.0))
    moved.sort(key=lambda r: (not r["informed"], -abs(r["shift"])))
    rep = {"draws": D, "used": used, "ess": ess, "ess_share": ess / D, "reliable": bool(ess >= MIN_ESS), "min_ess": MIN_ESS,
           "not_ruled_out": int(keep.sum()), "not_ruled_out_share": float(keep.mean()), "rule_out_at": RULE_OUT,
           "decision_prior": shares(np.ones(D)), "decision_posterior": shares(w),
           "decision_not_ruled_out": shares(keep.astype(float)) if keep.any() else None,
           "focus": focus,
           "focus_acceptable_prior": float(acc.mean()) if acc is not None else None,
           "focus_acceptable_posterior": float((w * acc).sum()) if acc is not None else None,
           "focus_feasible_prior": float(ok_f.mean()) if ok_f is not None else None,
           "focus_feasible_posterior": float((w * ok_f).sum()) if ok_f is not None else None,
           "assumptions": [m for m in moved if m["informed"]][:16], "n_informed": int(sum(m["informed"] for m in moved)),
           "n_assumptions": len(moved), "shift_noise": float(noise), "fdr": FDR,
           "structural": [r["id"] for r in rows if r.get("structural")],
           "per_draw": {"decision": ["none" if b is None else b for b in best], "weight": [float(x) for x in w],
                        "not_ruled_out": [bool(x) for x in keep]},
           "note": "importance weights on the joint draws from a Gaussian likelihood of the benchmarks, with each benchmark's standard error, "
                   "its transport allowance and the draws' Monte Carlo error in the variance; a posterior given those allowances, "
                   "not a measurement"}
    return rep


def by_mechanism(rows, mechanism_ids):
    """For each mechanism of the register, the benchmarks that bore on it and what they showed."""
    out = []
    for mid in mechanism_ids:
        mine = [r for r in rows if mid in r["mechanisms"]]
        scored = [r for r in mine if r["verdict"]]
        worst = None
        for v in (CONTRADICTED, TENSION, CONSISTENT):
            if any(r["verdict"] == v for r in scored):
                worst = v; break
        out.append({"mechanism": mid, "benchmarks": [{"id": r["id"], "verdict": r["verdict"], "kind": r["kind"]} for r in mine],
                    "confronted": bool(scored), "direct": any(r["kind"] == "direct" for r in scored), "worst": worst})
    return out


def summarise(rows, mech):
    scored = [r for r in rows if r["verdict"]]
    return {"benchmarks": len(rows), "scored": len(scored),
            "not_contradicted": sum(r["verdict"] == CONSISTENT for r in scored),
            "in_tension": [r["id"] for r in scored if r["verdict"] == TENSION],
            "contradicted": [r["id"] for r in scored if r["verdict"] == CONTRADICTED],
            "not_scored": [r["id"] for r in rows if not r["verdict"]],
            "structural": [r["id"] for r in rows if r.get("structural")],
            "mechanisms": len(mech), "mechanisms_confronted": [m["mechanism"] for m in mech if m["confronted"]],
            "mechanisms_unconfronted": [m["mechanism"] for m in mech if not m["confronted"]],
            "mechanisms_direct": [m["mechanism"] for m in mech if m["direct"]]}


# ---------------------------------------------------------------- wording --
def _fmt(x, unit, digits=1, signed=None):
    """A benchmark quantity for print: all of them are rates, shares or returns, shown as percentages."""
    if x is None or not np.isfinite(x):
        return "n/a"
    signed = (unit in ("return", "relative", "a year, relative")) if signed is None else signed
    v = round(x * 100, digits) + 0.0                      # no negative zero
    return f"{v:+.{digits}f}%" if (signed and v != 0) else f"{v:.{digits}f}%"


def scorecard(vb):
    """The benchmarks as rows of text for a table: what was observed, what the model gives, and the verdict."""
    out = []
    for r in vb["rows"]:
        u = r["unit"]
        d = 1 if r["sd_total"] < 0.1 else 0               # one precision for the whole row
        pr, ho = r.get("prior"), r.get("held_out")
        out.append({"id": r["id"], "benchmark": r["title"], "kind": r["kind"],
                    "observed": f"{_fmt(r['observed'], u, d)} (sd {_fmt(r['sd_total'], u, d, signed=False)})",
                    "model": _fmt(r["model"], u, d) if r["model"] is not None else "not computed",
                    "z": f"{round(r['z'], 1) + 0.0:+.1f}" if r["z"] is not None else "",
                    "verdict": (r["verdict"] or ("not scored: " + (r["why_not"] or ""))) + ("; a failure of form, left out of the weights" if r.get("structural") else ""),
                    "ranges": f"{_fmt(pr['lo'], u, d)} to {_fmt(pr['hi'], u, d)}" if pr else "",
                    "held_out": (f"{_fmt(ho['mean'], u, d)} (z {round(ho['z'], 1) + 0.0:+.1f})" if ho else ("left out of the weights" if pr else "")),
                    "mechanisms": ", ".join(m.replace("_", " ") for m in r["mechanisms"])})
    return out


def narrative(vb, labels=None, titles=None):
    """The validation result in sentences: (summary, calibration, limits). labels: policy name -> label; titles:
    assumption key -> short title."""
    labels, titles = labels or {}, titles or {}
    sm, cb = vb["summary"], vb.get("calibration") or {}
    name = {r["id"]: r["title"] for r in vb["rows"]}
    lab = lambda k: "no alternative" if k == "none" else (labels.get(k, k) if k != "baseline" else "the status quo")
    n_dir = len(sm["mechanisms_direct"])
    a = (f"The model was confronted with {sm['scored']} published benchmarks that bear on {len(sm['mechanisms_confronted'])} of its "
         f"{sm['mechanisms']} mechanisms. {n_dir} of those mechanisms {'has' if n_dir == 1 else 'have'} a benchmark measured on AI itself; the "
         f"others rest on analogues from other regulation and other technologies, each compared with an allowance for that distance. "
         f"At the central assumptions the model is not contradicted by {sm['not_contradicted']}")
    if sm["in_tension"]:
        a += f", is in tension with {len(sm['in_tension'])} ({'; '.join(name[i] for i in sm['in_tension'])})"
    if sm["contradicted"]:
        a += f" and is contradicted by {len(sm['contradicted'])} ({'; '.join(name[i] for i in sm['contradicted'])})"
    a += "."
    if sm.get("structural"):
        a += (f" Even the closest tenth of the draws of the assumptions miss {'; '.join(name[i] for i in sm['structural'])} by more than "
              f"{FORM_Z:.0f} standard deviations: that is a failure of the model's form and not of a parameter value, so it is reported "
              f"and left out of the weighting below.")
    if sm["not_scored"]:
        a += f" Not scored on this run: {'; '.join(name[i] for i in sm['not_scored'])}."
    if sm["mechanisms_unconfronted"]:
        a += f" No benchmark bears on {len(sm['mechanisms_unconfronted'])} mechanisms: {', '.join(m.replace('_', ' ') for m in sm['mechanisms_unconfronted'])}."
    b = ""
    if cb.get("used"):
        post, prior = cb["decision_posterior"], cb["decision_prior"]
        order = sorted((k for k in post if (post[k] or 0) > 0.005 or (prior.get(k) or 0) > 0.005), key=lambda k: -(post[k] or 0))
        b = (f"Weighting the {cb['draws']} joint draws of the assumptions by how well each reproduces the {len(cb['used'])} benchmarks it can "
             f"be compared with leaves an effective {cb['ess']:.0f} draws. In the weighted draws the decision is "
             + "; ".join(f"{lab(k)} in {100 * (post[k] or 0):.0f}% (unweighted {100 * (prior.get(k) or 0):.0f}%)" for k in order[:4]) + ". "
             f"{100 * cb['not_ruled_out_share']:.0f}% of the draws are ruled out by no benchmark at {cb['rule_out_at']:.0f} standard deviations.")
        if cb.get("focus") and cb.get("focus_acceptable_posterior") is not None:
            b += (f" {lab(cb['focus'])} is within the constraints and above the status quo in {100 * cb['focus_acceptable_posterior']:.0f}% "
                  f"of the weighted draws ({100 * cb['focus_acceptable_prior']:.0f}% unweighted).")
        if not cb.get("reliable"):
            b += f" Fewer than {cb['min_ess']:.0f} effective draws: the weighted shares are indicative only on this budget."
        inf = cb.get("assumptions") or []
        if inf:
            top = sorted(inf, key=lambda m: -abs(m["shift"]))[:5]
            b += (f" The benchmarks bear on {cb['n_informed']} of the {cb['n_assumptions']} assumptions drawn; they move most "
                  + ", ".join(f"{titles.get(m['assumption'], m['assumption'])} ({m['shift']:+.1f} sd)" for m in top) + ".")
    c = ("Weighting by benchmarks is a posterior given the allowances declared for each benchmark, not a measurement: most of the evidence "
         "is an analogue, and a wide allowance makes a benchmark easy to pass and uninformative. What the benchmarks do not reach is listed "
         "with the reasons; in particular nothing here identifies the elasticity of realised adoption to trust.")
    return a, b, c
