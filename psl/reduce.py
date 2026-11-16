"""From a simulated policy to what the accounting needs.

A PolicyResult holds every array of a run, per path, month and firm: at a few thousand paths that is hundreds of
megabytes per policy. Everything downstream (the social ledger, the safety, market and news metrics, the bootstrap,
the critic) works on much less, so each chunk of paths is reduced as soon as it is simulated and the reduced
pieces are joined. Paths are independent and each has its own random stream, so a battery can grow by adding
chunks (the adaptive sampling in pipeline.py) and a sensitivity design can be run in bounded memory.

A reduced policy is a dict:
  per path and month (N, H)   the monetary flows summed over firms (harm as drawn and as expected given the state,
                              compliance, fines, liability paid, claims, premiums, relocation, offshore revenue,
                              operating profit, earnings), the service, trust, enforcement, pressure and tone
                              series, incident counts, and the probability of a catastrophe in the month
  per path (N,)               the market value at the horizon, the catastrophe indicator and its conditional
                              estimator, the major incident indicator
  with full=True              per firm values (present value of earnings, value at the horizon, early prices), the
                              index path, incident counts by category, end states, the news counts and the
                              representative path
"""

import numpy as np

from .economy import Economy, RandomBundle
from .parallel import pmap

MONTHLY = ("harm", "harm_exp", "cat_harm", "cat_harm_exp", "compliance", "fines", "liability", "claims", "premium",
           "relocation", "offshore_revenue", "op_earnings", "earnings", "earnings_exp", "service", "trust", "enforcement",
           "pressure", "tone", "n_incidents", "n_major", "n_cat", "p_cat_any")
PER_PATH = ("cap_end", "cat_any", "cat_cmc", "major_any", "tone_early")
FULL_PATH = ("idx", "idx_early", "earn_f", "earn_exp_f", "cap_end_f", "price_early_f", "price_end_f", "inc_cat", "safety_end", "sigma_end",
             "cap_eff_end", "frontier_end", "offshore_end", "comply_end", "offshore_end_f", "comply_end_f", "sigma_end_f",
             "news_counts")
STORED = MONTHLY + PER_PATH          # what paths.npz keeps for the critic
# what the validation layer's moments are computed from (validation.py); kept only when a run asks for them
MOMENT_KEYS = ("m_inc_exp", "m_idx", "m_rd_scope", "m_rev_scope", "m_fine_ar", "m_fine_n", "m_major_ar", "m_major_n")


def conditional_catastrophe(n_cat, p_any):
    """The conditional Monte Carlo estimator of P(at least one catastrophe over the horizon), per path:

        sum over months t of  1{no catastrophe before t} x P(a catastrophe in month t | the state reached).

    P(first catastrophe in month t) = E[1{none before t} P(one in t | state)], so the sum has expectation
    P(at least one); a path contributes its accumulated hazard up to its first catastrophe instead of a 0 or a 1,
    which removes most of the variance of a rare event's frequency."""
    hit = np.asarray(n_cat) > 0
    before = np.cumsum(hit, axis=1) - hit            # catastrophes in earlier months
    return ((before == 0) * np.asarray(p_any)).sum(axis=1)


def reduce(res, discount_f=None, full=True, moments=False):
    """res: a PolicyResult. discount_f: the monthly discount factors (H,) for the per firm present values
    (needed only with full=True). moments: also keep what the validation layer's moments are computed from."""
    R = {"n_paths": int(res.n_paths), "horizon": int(res.horizon)}
    R["harm"] = res.harm.sum(axis=2); R["harm_exp"] = res.harm_exp.sum(axis=2)
    R["cat_harm"] = res.cat_harm.sum(axis=2); R["cat_harm_exp"] = res.cat_harm_exp.sum(axis=2)
    for k in ("compliance", "fines", "liability", "claims", "premium", "relocation", "op_earnings", "earnings"):
        R[k] = getattr(res, k).sum(axis=2)
    # earnings with the liability a firm pays replaced by what it was expected to pay given the state: the same
    # expectation as earnings, without the draw of the incident (the expected value estimator of the industry's value)
    earn_exp = res.earnings + res.liability - res.liability_exp
    R["earnings_exp"] = earn_exp.sum(axis=2)
    R["offshore_revenue"] = (res.offshore * res.revenue / 12.0).sum(axis=2)
    for k in ("service", "trust", "enforcement", "pressure", "tone"):
        R[k] = res.series[k]
    R["p_cat_any"] = res.series["p_cat_any"]
    R["n_incidents"] = res.incidents.sum(axis=(2, 3)).astype(float)
    R["n_major"] = res.news_counts[:, :, 1].astype(float)          # individual incidents at or above the threshold
    R["n_cat"] = res.catastrophe.sum(axis=2).astype(float)
    R["cap_end"] = res.cap_end.sum(axis=1)
    R["cat_any"] = (R["n_cat"].sum(axis=1) > 0).astype(float)
    R["cat_cmc"] = conditional_catastrophe(R["n_cat"], R["p_cat_any"])
    R["major_any"] = (R["n_major"].sum(axis=1) > 0).astype(float)
    R["tone_early"] = res.series["tone"][:, :6].mean(axis=1)
    if moments:
        w = res.cap0 / res.cap0.sum()
        idx = (res.prices * w[None, None, :]).sum(axis=2)                          # the value weighted index, (N, H + 1)
        scope = res.sector_in.astype(float)                                        # firms in the instrument's sector scope
        monthly_rev = res.revenue / 12.0
        R["m_inc_exp"] = res.series["inc_exp"]
        R["m_idx"] = idx
        R["m_rd_scope"] = (monthly_rev * (res.rd_share * res.scope_share * scope)[None, None, :]).sum(axis=2)
        R["m_rev_scope"] = (monthly_rev * scope[None, None, :]).sum(axis=2)
        # a firm's log return in a month less the index's: summed over the firm months with a fine, and with a major incident
        ar = np.log(res.prices[:, 1:, :] / res.prices[:, :-1, :]) - np.log(idx[:, 1:] / idx[:, :-1])[:, :, None]
        R["m_fine_ar"] = (ar * res.fined).sum(axis=(1, 2)); R["m_fine_n"] = res.fined.sum(axis=(1, 2)).astype(float)
        R["m_major_ar"] = (ar * res.major).sum(axis=(1, 2)); R["m_major_n"] = res.major.sum(axis=(1, 2)).astype(float)
    if full:
        w = res.cap0 / res.cap0.sum()
        R["idx"] = (res.prices * w[None, None, :]).sum(axis=2)                     # (N, H + 1)
        R["idx_early"] = R["idx"][:, 1:7]
        d = np.ones(res.horizon) if discount_f is None else np.asarray(discount_f)
        R["earn_f"] = (res.earnings * d[None, :, None]).sum(axis=1)               # (N, F) present value of earnings, as drawn
        R["earn_exp_f"] = (earn_exp * d[None, :, None]).sum(axis=1)               # the same with expected liability
        R["cap_end_f"] = res.cap_end
        R["price_early_f"] = res.prices[:, :7, :]
        R["price_end_f"] = res.prices[:, -1, :]
        R["inc_cat"] = res.incidents.sum(axis=(1, 2)).astype(float)               # (N, K)
        R["safety_end"] = res.safety[:, -1, :].mean(axis=1); R["sigma_end"] = res.sigma[:, -1, :].mean(axis=1)
        R["cap_eff_end"] = res.cap_eff[:, -1, :].mean(axis=1); R["frontier_end"] = res.cap_eff[:, -1, :].max(axis=1)
        R["offshore_end"] = res.offshore[:, -1, :].mean(axis=1); R["comply_end"] = res.comply[:, -1, :].mean(axis=1)
        R["offshore_end_f"] = res.offshore[:, -1, :]; R["comply_end_f"] = res.comply[:, -1, :]
        R["sigma_end_f"] = res.sigma[:, -1, :]
        R["news_counts"] = res.news_counts
        R["price_sum"] = res.prices.sum(axis=0)                                   # (H + 1, F), for the mean price path
        R["rep"] = {"prices": res.prices[0].copy(), "events": res.events0,
                    "series": {k: res.series[k][0].copy() for k in ("pressure", "trust", "enforcement", "service")}}
        R["labels"] = list(res.labels); R["sectors"] = list(res.sectors); R["cap0"] = res.cap0.copy()
        R["label"] = res.policy["label"]; R["name"] = res.policy["name"]
    return R


def concat(parts):
    """Join reduced chunks of the same policy along the path axis; the representative path is the first chunk's."""
    if len(parts) == 1:
        return parts[0]
    out = dict(parts[0])
    out["n_paths"] = int(sum(p["n_paths"] for p in parts))
    for k in MONTHLY + PER_PATH + FULL_PATH + MOMENT_KEYS:
        if k in parts[0]:
            out[k] = np.concatenate([p[k] for p in parts], axis=0)
    if "price_sum" in parts[0]:
        out["price_sum"] = sum(p["price_sum"] for p in parts)
    return out


def head(R, n):
    """The first n paths of a reduced policy (common random numbers make these the paths a smaller run uses)."""
    out = dict(R)
    out["n_paths"] = int(n)
    for k in MONTHLY + PER_PATH + FULL_PATH + MOMENT_KEYS:
        if k in R:
            out[k] = R[k][:n]
    return out


def blocks(R, n_blocks):
    """Split a reduced design run of n_blocks x n paths into its blocks (list of reduced dicts of n paths)."""
    n = R["n_paths"] // n_blocks
    out = []
    for b in range(n_blocks):
        piece = {"n_paths": n, "horizon": R["horizon"]}
        for k in MONTHLY + PER_PATH + tuple(m for m in MOMENT_KEYS if m in R):
            piece[k] = R[k][b * n:(b + 1) * n]
        out.append(piece)
    return out


def simulate_battery(policies, firms, a, horizon, n_paths, seed, start=0, chunk=480, full=True, variant=None, gaming=None,
                     streams=None, before=None, after=None, discount_f=None, stop=None, moments=False):
    """Every policy of `policies` (name -> policy) on paths start, ..., start + n_paths - 1, chunk by chunk, each chunk's
    random numbers drawn once and shared by all the policies. Returns {name: reduced policy}.

    streams: {name: callback} for the representative path. When given (and start == 0) the first chunk runs policy by
    policy in order, calling before(name) and after(name, reduced, seconds) around each, so a live display can follow;
    otherwise the policies of a chunk run side by side."""
    names = list(policies)
    parts = {name: [] for name in names}
    F = len(firms)
    done = 0
    while done < n_paths:
        n = int(min(chunk, n_paths - done))
        eco = Economy(firms, a, horizon=horizon, n_paths=n, seed=seed, bundle=RandomBundle(n, horizon, F, seed, start=start + done))
        if streams is not None and done == 0 and start == 0:
            import time
            for name in names:
                if stop and stop():
                    break
                if before:
                    before(name)
                t0 = time.time()
                red = reduce(eco.run(policies[name], variant=variant, gaming=gaming, stream=streams.get(name)), discount_f=discount_f, full=full,
                             moments=moments)
                parts[name].append(red)
                if after:
                    after(name, red, time.time() - t0)
        else:
            def one(name, _eco=eco):
                return name, reduce(_eco.run(policies[name], variant=variant, gaming=gaming), discount_f=discount_f, full=full, moments=moments)
            for name, red in pmap(one, names):
                parts[name].append(red)
        done += n
        if stop and stop():
            break
    return {name: concat(p) for name, p in parts.items() if p}


def simulate(policy, firms, a, horizon, n_paths, seed, start=0, chunk=480, full=True, variant=None, gaming=None,
             stream=None, discount_f=None, stop=None):
    """One policy on paths start, ..., start + n_paths - 1 (see simulate_battery)."""
    name = policy.get("name", "policy")
    out = simulate_battery({name: policy}, firms, a, horizon, n_paths, seed, start=start, chunk=chunk, full=full, variant=variant,
                           gaming=gaming, streams=({name: stream} if stream is not None else None), discount_f=discount_f, stop=stop)
    return out[name]


def simulate_gamed(policy, strategies, firms, a, horizon, n, seed):
    """One policy under each gaming strategy (name -> spec) on the first n paths, the strategies side by side on the
    same random numbers. Returns {strategy: reduced policy}."""
    eco = Economy(firms, a, horizon=horizon, n_paths=n, seed=seed, bundle=RandomBundle(n, horizon, len(firms), seed))
    return dict(pmap(lambda item: (item[0], reduce(eco.run(policy, gaming=item[1]), full=False)), strategies.items()))


def simulate_design(policies, firms, a, rows, horizon, n, seed, chunk=960, variant=None, gaming=None, progress=None, moments=False):
    """A sensitivity design in one vectorised pass per policy.

    rows: a list of dicts, each the assumptions that differ from `a` in one design row (an alternative parameter
    value, a joint draw, ...). Every row runs on the same n paths (the first n of the stream family `seed`), so
    row b occupies paths b*n ... (b+1)*n - 1 of the result and differs from the central run on those paths only
    through its parameters. Returns ({policy name: reduced dict of len(rows) x n paths}, a_design) where a_design
    holds, for every assumption that varies, one value per path, and the scalar otherwise."""
    B = len(rows)
    F = len(firms)
    varying = sorted({k for r in rows for k in r})
    bundle = RandomBundle(n, horizon, F, seed)
    out = {name: [] for name in policies}
    a_parts = {k: [] for k in varying}
    per = max(1, int(chunk // n))                       # design rows per chunk
    for b0 in range(0, B, per):
        sub = rows[b0:b0 + per]
        nb = len(sub)
        a_c = dict(a)
        for k in varying:
            a_c[k] = np.repeat(np.array([float(r.get(k, a[k])) for r in sub]), n)
            a_parts[k].append(a_c[k])
        rb = bundle.take(np.tile(np.arange(n), nb))
        eco = Economy(firms, a_c, horizon=horizon, n_paths=nb * n, seed=seed, bundle=rb)

        def one(item, _eco=eco):
            return item[0], reduce(_eco.run(item[1], variant=variant, gaming=gaming), full=False, moments=moments)
        for name, red in pmap(one, policies.items()):
            out[name].append(red)
        if progress:
            progress(min(B, b0 + nb), B)
    reds = {name: concat(parts) for name, parts in out.items()}
    a_design = dict(a)
    for k in varying:
        a_design[k] = np.concatenate(a_parts[k])
    return reds, a_design
