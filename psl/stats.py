"""Statistical machinery, kept in one place so that every interval in the Lab is computed the same way.

Three kinds of uncertainty are reported and never merged (docs/METHOD.md, section 9):

  outcome spread      the 10th and 90th percentiles of the simulated outcomes: how different the world can be
                      from one path to the next under the declared model (aleatoric)
  Monte Carlo error   how precisely a finite number of paths estimates an expectation: a standard error and a
                      95% bootstrap confidence interval for every mean, paired path by path for every difference
  parameter and       how the answer moves when the declared assumptions and the model structure move
  structural          (assurance.py: the screen, the joint parameter draw, the variance decomposition, the variants)

The bootstrap resamples paths. Each path carries every policy on the same random numbers, so resampling paths
keeps the pairing, and one set of resamples (a count matrix) is reused for every quantity of a run: the bootstrap
draws of two quantities are then draws of the same resampled battery, which is what feasibility inside each draw,
paired differences and the ranking need.
"""

import numpy as np
from scipy import stats as _st
from scipy.special import ndtr, ndtri

LEVEL = 0.95


class Boot:
    """B bootstrap resamples of N paths as a (B, N) matrix of multiplicities.

    means(X) for X of shape (..., N) returns the resampled means, shape (..., B)."""

    def __init__(self, n, b=1000, seed=0):
        self.n, self.b = int(n), int(b)
        rng = np.random.default_rng([int(seed), 7919])
        idx = rng.integers(0, self.n, size=(self.b, self.n))
        counts = np.zeros((self.b, self.n), dtype=np.float64)
        np.add.at(counts, (np.arange(self.b)[:, None], idx), 1.0)
        self.w = counts / float(self.n)                      # rows sum to one

    def means(self, x):
        return np.asarray(x, dtype=float) @ self.w.T

    def ci(self, x, level=LEVEL):
        """(mean, standard error, lower, upper) of the mean of x over paths."""
        x = np.asarray(x, dtype=float)
        m = self.means(x)
        lo, hi = np.percentile(m, [50 * (1 - level), 100 - 50 * (1 - level)])
        return float(x.mean()), float(m.std(ddof=1)), float(lo), float(hi)


def interval(draws, level=LEVEL):
    lo, hi = np.percentile(np.asarray(draws, dtype=float), [50 * (1 - level), 100 - 50 * (1 - level)])
    return float(lo), float(hi)


def wilson(k, n, level=LEVEL):
    """Wilson score interval for a proportion k of n."""
    if n <= 0:
        return 0.0, 1.0
    z = float(ndtri(0.5 + level / 2))
    p = k / n
    den = 1 + z * z / n
    mid = (p + z * z / (2 * n)) / den
    half = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return float(max(0.0, mid - half)), float(min(1.0, mid + half))


def kendall_tau_b(a, b):
    """Kendall's tau b (tie aware) between two score vectors; 0 when either has no variation."""
    a = np.asarray(a, dtype=float); b = np.asarray(b, dtype=float)
    if len(a) < 2:
        return 1.0
    a = _tied(a); b = _tied(b)
    if np.all(a == a[0]) or np.all(b == b[0]):
        return 0.0
    t = _st.kendalltau(a, b, variant="b").statistic
    return 0.0 if not np.isfinite(t) else float(t)


def _tied(v, rel=1e-9):
    """Round to a relative tolerance so that values equal up to floating point noise are ties."""
    v = np.asarray(v, dtype=float)
    scale = max(1.0, float(np.max(np.abs(v)))) * rel
    return np.round(v / scale) * scale


def rank_desc(values):
    """Competition ranks, 1 = highest; equal values share a rank (1, 2, 2, 4), so the order two identical
    options appear in cannot give them different ranks."""
    v = _tied(values)
    return _st.rankdata(-v, method="min").astype(int)


def hermite(n=24):
    """Nodes and weights for E[g(Z)], Z standard normal (probabilists' Gauss Hermite)."""
    x, w = np.polynomial.hermite_e.hermegauss(n)
    return x, w / w.sum()


def any_event_probability(p, rho, nodes=None):
    """P(at least one of F events) when event f has marginal probability p[..., f] and the events are joined by a one
    factor Gaussian copula with correlation rho (scalar or one value per leading index): the survival probability
    is integrated over the common factor by Gauss Hermite quadrature. rho = 0 gives 1 - prod(1 - p)."""
    p = np.asarray(p, dtype=float)
    rho_a = np.asarray(rho, dtype=float)
    if rho_a.ndim == 0 and float(rho_a) <= 0.0:
        return 1.0 - np.prod(1.0 - p, axis=-1)
    x, w = nodes if nodes is not None else hermite()
    with np.errstate(divide="ignore"):
        thr = ndtri(p)                                                    # -inf where p == 0
    sr = np.sqrt(np.clip(rho_a, 0.0, 0.999999))
    s1 = np.sqrt(1.0 - np.clip(rho_a, 0.0, 0.999999))
    # an event of probability zero has conditional probability zero at every node: the normal distribution function
    # is evaluated only for the others (most firms in most months are below the capability at which the tail is live)
    cond = np.zeros(p.shape + (len(x),))                                  # (..., F, G)
    live = p > 0
    if live.any():
        if rho_a.ndim:
            lead = (slice(None),) * rho_a.ndim + (None,) * (p.ndim - rho_a.ndim)
            sr_l = np.broadcast_to(sr[lead], p.shape)[live][:, None]
            s1_l = np.broadcast_to(s1[lead], p.shape)[live][:, None]
        else:
            sr_l, s1_l = sr, s1
        cond[live] = ndtr((thr[live][:, None] - sr_l * x) / s1_l)
    surv = np.prod(1.0 - cond, axis=-2)                                   # (..., G)
    return 1.0 - surv @ w


def conditional_event_probability(p, rho, z):
    """Each event's probability given the common factor z (shape of the leading index of p)."""
    p = np.asarray(p, dtype=float)
    rho_a = np.asarray(rho, dtype=float)
    if rho_a.ndim == 0 and float(rho_a) <= 0.0:
        return p
    with np.errstate(divide="ignore"):
        thr = ndtri(p)
    r = np.clip(rho_a, 0.0, 0.999999)
    sr = np.sqrt(r); s1 = np.sqrt(1.0 - r)
    if rho_a.ndim:
        sr = sr[..., None]; s1 = s1[..., None]
    return ndtr((thr - sr * np.asarray(z)[..., None]) / s1)


# ------------------------------------------------------------ sampling designs --
def triangular_ppf(u, lo, mode, hi):
    """Inverse CDF of the triangular distribution on [lo, hi] with the given mode."""
    u = np.asarray(u, dtype=float)
    if hi <= lo:
        return np.full_like(u, mode)
    fc = (mode - lo) / (hi - lo)
    left = lo + np.sqrt(np.maximum(u * (hi - lo) * (mode - lo), 0.0))
    right = hi - np.sqrt(np.maximum((1 - u) * (hi - lo) * (hi - mode), 0.0))
    return np.where(u < fc, left, right)


def latin_hypercube(m, k, seed=0):
    """m points in [0, 1]^k, one in each of m strata per dimension."""
    rng = np.random.default_rng([int(seed), 104729])
    u = (np.argsort(rng.random((m, k)), axis=0) + rng.random((m, k))) / m
    return u


def gaussian_copula(u, corr):
    """Impose a correlation matrix on independent uniforms (m, k) through a Gaussian copula; the marginals stay
    uniform. corr is (k, k), positive definite."""
    z = ndtri(np.clip(u, 1e-12, 1 - 1e-12))
    L = np.linalg.cholesky(np.asarray(corr, dtype=float))
    return ndtr(z @ L.T)


def spearman(x, y):
    x = np.asarray(x, dtype=float); y = np.asarray(y, dtype=float)
    if np.all(x == x[0]) or np.all(y == y[0]):
        return 0.0
    r = _st.spearmanr(x, y).statistic
    return 0.0 if not np.isfinite(r) else float(r)


def saltelli(m, k, seed=0):
    """Saltelli's design for k inputs: base matrices A and B (m, k) in [0, 1] (scrambled Sobol points) and the k
    matrices AB_i (A with column i taken from B). Returns (A, B, [AB_0, ..., AB_{k-1}])."""
    eng = _st.qmc.Sobol(d=2 * k, scramble=True, seed=int(seed))
    pts = eng.random(m)
    A, B = pts[:, :k], pts[:, k:]
    ABs = []
    for i in range(k):
        ab = A.copy(); ab[:, i] = B[:, i]
        ABs.append(ab)
    return A, B, ABs


def sobol_indices(fA, fB, fAB):
    """First order (Saltelli 2010) and total order (Jansen 1999) indices from the outputs on A, B and each AB_i.
    Returns (S1, ST) as arrays of length k, clipped to [0, 1]; (zeros, zeros) when the output does not vary."""
    fA = np.asarray(fA, dtype=float); fB = np.asarray(fB, dtype=float)
    var = np.var(np.concatenate([fA, fB]), ddof=1)
    k = len(fAB)
    if not np.isfinite(var) or var <= 1e-18:
        return np.zeros(k), np.zeros(k)
    # f(AB_i) - f(A) has mean zero, so centring f(B) leaves the first order estimator's expectation unchanged and
    # removes the variance a large mean would add to it
    fBc = fB - np.mean(np.concatenate([fA, fB]))
    s1 = np.array([np.mean(fBc * (np.asarray(f) - fA)) / var for f in fAB])
    st = np.array([0.5 * np.mean((fA - np.asarray(f)) ** 2) / var for f in fAB])
    return np.clip(s1, 0.0, 1.0), np.clip(st, 0.0, 1.0)


def sobol_intervals(fA, fB, fAB, b=200, seed=0, level=0.90):
    """Bootstrap intervals for the Sobol indices: the base sample's rows are resampled (the same rows of A, B and
    every AB_i, which belong together) and the indices recomputed. Returns (S1_lo, S1_hi, ST_lo, ST_hi), arrays of
    length k. The intervals describe the error of a finite design, the only error the indices carry when every
    evaluation runs on the same paths."""
    fA = np.asarray(fA, dtype=float); fB = np.asarray(fB, dtype=float)
    F = np.stack([np.asarray(f, dtype=float) for f in fAB], axis=0)          # (k, m)
    m, k = fA.size, F.shape[0]
    rng = np.random.default_rng([int(seed), 15485863])
    s1 = np.zeros((b, k)); st = np.zeros((b, k))
    for j in range(b):
        ix = rng.integers(0, m, size=m)
        s1[j], st[j] = sobol_indices(fA[ix], fB[ix], F[:, ix])
    q = [50 * (1 - level), 100 - 50 * (1 - level)]
    lo1, hi1 = np.percentile(s1, q, axis=0)
    lot, hit = np.percentile(st, q, axis=0)
    return lo1, hi1, lot, hit


def benjamini_hochberg(pvalues, q=0.10):
    """Which of a family of tests are discoveries at false discovery rate q (Benjamini and Hochberg 1995): a boolean
    array in the order given. Controls the expected share of false positives among the flagged, which is what a
    screen of many assumptions against one output needs."""
    p = np.asarray(pvalues, dtype=float)
    m = p.size
    if m == 0:
        return np.zeros(0, dtype=bool)
    order = np.argsort(p)
    passed = p[order] <= q * (np.arange(1, m + 1) / m)
    k = int(np.max(np.nonzero(passed)[0])) + 1 if passed.any() else 0
    out = np.zeros(m, dtype=bool)
    out[order[:k]] = True
    return out


def spearman_test(x, y):
    """(rho, two sided p value) of Spearman's rank correlation; (0, 1) when either input does not vary."""
    x = np.asarray(x, dtype=float); y = np.asarray(y, dtype=float)
    if np.all(x == x[0]) or np.all(y == y[0]):
        return 0.0, 1.0
    r = _st.spearmanr(x, y)
    if not np.isfinite(r.statistic):
        return 0.0, 1.0
    return float(r.statistic), float(r.pvalue)


def ks_split(x, flag):
    """Monte Carlo filtering: the two sample Kolmogorov Smirnov statistic between the values of x in the draws where
    flag holds and where it does not, with its p value; (0, 1) when either group has fewer than five draws."""
    x = np.asarray(x, dtype=float); flag = np.asarray(flag, dtype=bool)
    if flag.sum() < 5 or (~flag).sum() < 5:
        return 0.0, 1.0
    r = _st.ks_2samp(x[flag], x[~flag])
    return float(r.statistic), float(r.pvalue)


def binomial_coverage(k, n, nominal):
    """Exact two sided binomial test that k of n observations fall inside an interval of nominal coverage."""
    if n <= 0:
        return None
    return float(_st.binomtest(int(k), int(n), float(nominal)).pvalue)
