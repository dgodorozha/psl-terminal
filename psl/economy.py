"""The synthetic AI economy: firms, a regulator, the public, the press and
the market, stepped month by month under one policy.

Every policy in a battery runs on the same pre drawn random numbers
(common random numbers), so the difference between two policies on a path
is the policy's doing and not the dice. The engine is vectorised over
Monte Carlo paths and firms; a full battery of nine policies with 240
paths over 60 months runs in a few seconds.

Agents
  firms       each month choose a safety share of R&D, an offshore share and
              whether to comply, by maximising a one year expected payoff
              under their own (optimistic) view of the incident rate and the
              policy's costs and penalties; culture adds an intrinsic weight
              on safety. Heterogeneous archetypes (firms.py).
  regulator   enforcement intensity follows public pressure within capacity;
              audits firms in scope and fines the non compliant; licensing
              delays releases; a moratorium freezes them.
  public      a trust index that falls with harm and recovers slowly; it sets
              the ceiling on deployment reach and the realised adoption
              benefits.
  press       event salience and tone become a news pressure index (every
              path) and, on the representative path, a wire of headlines
              composed by four media agents (news.py).
  market      prices are a fundamental value (an earnings multiple on the
              forward earnings the state implies) times a sentiment component
              driven by the market factor, policy uncertainty, news pressure
              and incident jumps.

State per month, every array (paths, firms): revenue run rate R ($bn a
year), capability C and released capability C_eff, safety level S, reach D,
offshore share O, compliance flag X, earnings, compliance cost, fines,
liability or premiums, incidents by category with monetised harm, a
catastrophe flag, enforcement e, pressure P, trust T and the service index
Q. See docs/METHOD.md for the equations.

Beside every realised incident the engine records what was expected of
that month given the state the path had reached: the expected harm
(probability times mean severity, by category and for the catastrophic
tail) and the probability of at least one catastrophe. Those conditional
expectations are what the expected value estimators use (welfare.py): they
have the same expectation as the realised draws and far less variance,
which is what makes a rare, very large loss estimable on a few hundred
paths.

Assumptions are scalars in an ordinary run. A sensitivity design passes one
value per path instead (arrays of shape (paths,)), so that hundreds of
alternative parameter values run in one vectorised pass on the same random
numbers; the two are the same computation.
"""

import numpy as np

from .policies import in_scope
from .stats import any_event_probability, conditional_event_probability, hermite

CATEGORIES = ("misuse", "accident", "systemic")
MODEL_SECTORS = ("frontier_lab", "open_weights", "consumer_ai", "autonomy", "startups")
SIGMA_GRID = np.array([0.02, 0.05, 0.10, 0.15, 0.20, 0.30])
OFFSHORE_GRID = np.array([0.0, 0.3, 0.6, 0.9])
COMPLY_GRID = np.array([0.0, 1.0])
SIGMA_REF = 0.1               # the safety share the baseline growth rates already assume
MILESTONE = 0.25
SALIENCE = {"minor": 0.12, "major": 0.45, "catastrophe": 1.2, "enforcement": 0.2, "relocation": 0.15, "milestone": 0.08}
_GH = hermite(24)
# the action grid on its own three axes, against arrays laid out (paths, firms, safety share, offshore share, comply)
SIG5 = SIGMA_GRID[None, None, :, None, None]
OM5 = OFFSHORE_GRID[None, None, None, :, None]
CHI5 = COMPLY_GRID[None, None, None, None, :]


class RandomBundle:
    """Common random numbers for one battery: the same draws for every policy.

    Every path has its own stream seeded by (seed, path index), so a bundle of
    fewer paths is exactly the first paths of a larger one with the same seed:
    an assurance re simulation on a smaller budget can be paired path by path
    with the main run, and its effect reported as a shift of the headline figure."""

    NAMES = ("z_market", "z_policy", "z_idio", "u_inc", "z_sev", "u_cat", "z_cat", "u_audit", "z_news", "z_common")

    def __init__(self, n_paths, horizon, n_firms, seed, start=0):
        """Paths start, ..., start + n_paths - 1 of the stream family `seed`."""
        N, H, F, C = n_paths, horizon, n_firms, len(CATEGORIES)
        self.seed = seed
        self.index = np.arange(int(start), int(start) + N)
        parts = {k: [] for k in self.NAMES}
        for i in self.index:
            rng = np.random.default_rng([int(seed), int(i)])
            parts["z_market"].append(rng.standard_normal(H))
            parts["z_policy"].append(rng.standard_normal(H))
            parts["z_idio"].append(rng.standard_normal((H, F)))
            parts["u_inc"].append(rng.random((H, F, C)))
            parts["z_sev"].append(rng.standard_normal((H, F, C)))
            parts["u_cat"].append(rng.random((H, F)))
            parts["z_cat"].append(rng.standard_normal((H, F)))
            parts["u_audit"].append(rng.random((H, F)))
            parts["z_news"].append(rng.standard_normal(H))
            parts["z_common"].append(rng.standard_normal(H))      # the factor catastrophes share; drawn last
        for k in self.NAMES:
            setattr(self, k, np.stack(parts[k], axis=0))

    def take(self, rows):
        """A bundle whose row j is this bundle's row rows[j]: a sensitivity design repeats the same paths once
        per alternative parameter value."""
        rows = np.asarray(rows, dtype=int)
        out = object.__new__(RandomBundle)
        out.seed = self.seed
        out.index = self.index[rows]
        for k in self.NAMES:
            setattr(out, k, getattr(self, k)[rows])
        return out


class PolicyResult:
    """Arrays of one policy's run; see the module docstring for the names."""

    def __init__(self, **kw):
        self.__dict__.update(kw)


def _actions():
    """The firm's action grid as three flat arrays (A,)."""
    s, o, c = np.meshgrid(SIGMA_GRID, OFFSHORE_GRID, COMPLY_GRID, indexing="ij")
    return s.ravel(), o.ravel(), c.ravel()


def _views(a, n):
    """Each assumption shaped to broadcast against per path (N,), per firm (N, F) and per action (N, F, A)
    arrays: the scalar itself, or, when a design gives one value per path, x, x[:, None] and x[:, None, None]."""
    p, f, fa = {}, {}, {}
    for k, v in a.items():
        if np.ndim(v) == 0:
            x = float(v)
            p[k] = f[k] = fa[k] = x
        else:
            x = np.asarray(v, dtype=float)
            if x.shape != (n,):
                raise ValueError(f"assumption {k}: one value per path expected, shape {(n,)}, got {x.shape}")
            p[k] = x; f[k] = x[:, None]; fa[k] = x[:, None, None]
    return p, f, fa


def _ex(x, extra):
    """A per path quantity (scalar or (N,)) with `extra` trailing axes."""
    return x if np.ndim(x) == 0 else np.asarray(x).reshape(np.shape(x) + (1,) * extra)


def _stack(vals):
    """K per path quantities stacked on a last axis: (K,) for scalars, (N, K) when any is per path."""
    return np.stack(np.broadcast_arrays(*[np.asarray(v, dtype=float) for v in vals]), axis=-1)


def _join(at_zero, at_one):
    """A quantity on the comply axis from its value when the firm does not comply (at_zero) and when it does
    (at_one), each with a comply axis of length one: the two broadcast against each other and stacked."""
    shape = np.broadcast_shapes(at_zero.shape, at_one.shape)
    out = np.empty(shape[:-1] + (2,))
    out[..., 0] = np.broadcast_to(at_zero, shape)[..., 0]
    out[..., 1] = np.broadcast_to(at_one, shape)[..., 0]
    return out


class Economy:
    def __init__(self, firms, assumptions, horizon=60, n_paths=240, seed=7, bundle=None, hooks=None, reference=False):
        self.firms = firms
        self.reference = bool(reference)      # True: the firms' decision written out on the full action grid (the tested definition)
        self.a = dict(assumptions)
        self.H = int(horizon)
        self.N = int(n_paths)
        self.F = len(firms)
        self.seed = seed
        self.rb = bundle or RandomBundle(self.N, self.H, self.F, seed)
        self.hooks = hooks or {}
        f = firms
        self.sector = [x["sector"] for x in f]
        self.labels = [x["label"] for x in f]
        self.R0 = np.array([x["revenue"] for x in f])
        self.margin = np.array([x["margin"] for x in f])
        self.g0 = np.array([x["growth"] for x in f])
        self.rd = np.array([x["rd_share"] for x in f])
        self.C0 = np.array([x["capability"] for x in f])
        self.S0 = np.array([x["safety"] for x in f])
        self.D0 = np.array([x["reach"] for x in f])
        self.scope_share = np.array([x["scope_share"] for x in f])
        self.mobility = np.array([x["mobility"] for x in f])
        self.culture = np.array([x["culture"] for x in f])
        self.beta = np.array([x["beta"] for x in f])
        self.ivol = np.array([x["idio_vol"] for x in f])
        self.pe = np.array([x["pe"] for x in f])
        self.ps = np.array([x["ps"] for x in f])
        self.compute_dep = np.array([x["compute_dependence"] for x in f])
        self.open_w = np.array([bool(x.get("open_weights")) for x in f])
        self.small = np.array([bool(x.get("small")) for x in f])
        self.is_model = np.array([s in MODEL_SECTORS for s in self.sector])
        self.is_chip = np.array([s == "chips" for s in self.sector])
        self.is_cloud = np.array([s == "hyperscaler" for s in self.sector])
        self.sig_a, self.om_a, self.chi_a = _actions()

    # ------------------------------------------------------------------ run --
    def run(self, policy, variant=None, gaming=None, stream=None):
        """Simulate one policy. `variant` overrides assumptions and behaviour for the
        structural robustness check; `gaming` is a red team strategy; `stream(t, payload)`
        receives the representative path month by month."""
        a = dict(self.a)
        variant = variant or {}
        gaming = gaming or {}
        a.update(variant.get("assumptions", {}))
        plan_months = float(variant.get("plan_months", 12.0))
        N, H, F = self.N, self.H, self.F
        rb = self.rb
        pol = policy
        K = len(CATEGORIES)
        ap, af, aa = _views(a, N)             # each assumption against (N,), (N, F) and (N, F, A) arrays
        base_haz = _stack([ap["hazard_base_misuse"], ap["hazard_base_accident"], ap["hazard_base_systemic"]])   # (K,) or (N, K)
        sev_med = _stack([ap["severity_misuse_median_bn"], ap["severity_accident_median_bn"], ap["severity_systemic_median_bn"]])
        sev_mean = sev_med * _ex(np.exp(0.5 * np.asarray(ap["severity_sigma"]) ** 2), 1)     # lognormal mean, (K,) or (N, K)
        bh_sum = base_haz.sum(axis=-1)                                       # scalar or (N,)
        sev_avg = (base_haz / _ex(bh_sum, 1) * sev_mean).sum(axis=-1)        # mean severity of an incident, scalar or (N,)
        bh3 = base_haz if base_haz.ndim == 1 else base_haz[:, None, :]       # against (N, F, K)
        sm3 = sev_med if sev_med.ndim == 1 else sev_med[:, None, :]
        smean3 = sev_mean if sev_mean.ndim == 1 else sev_mean[:, None, :]
        cat_mean = ap["catastrophe_harm_bn"] * np.exp(0.5 * np.asarray(ap["catastrophe_severity_sigma"]) ** 2)   # mean catastrophic harm
        rho = ap["catastrophe_correlation"]

        # policy scope per firm (sector test); the capability test is per path and month
        sector_in = np.array([in_scope(pol, s) for s in self.sector])
        cap_test = float(pol["capability_threshold"])
        split = float(gaming.get("threshold_split", 1.0))          # scope capability shown to the regulator
        theatre = bool(gaming.get("compliance_theatre", False))
        mobility = np.minimum(1.0, self.mobility * float(gaming.get("mobility_boost", 1.0)))
        reloc_cost = ap["relocation_cost"] * float(gaming.get("relocation_discount", 1.0))        # scalar or (N,)
        relabel = float(gaming.get("relabel", 0.0))                # share of tier friction and variable cost avoided
        capacity = float(pol["enforcement_capacity"]) * float(variant.get("capacity_mult", 1.0))
        coordinated = pol["scope"] == "coordinated"

        # state
        R = np.tile(self.R0, (N, 1)).astype(float)
        C = np.tile(self.C0, (N, 1)).astype(float)
        S = np.tile(self.S0, (N, 1)).astype(float)
        D = np.tile(self.D0, (N, 1)).astype(float)
        O = np.zeros((N, F))
        Chist = np.zeros((H + 1, N, F)); Chist[0] = C
        Ceff = C.copy()
        frozen = np.full((N, F), np.inf)        # moratorium ceiling on released capability
        xi = np.zeros((N, F))                   # sentiment component of the price
        e = np.full(N, 0.3 * capacity + 0.02)   # enforcement intensity
        Dref = D.copy()                         # reach on a path with full trust and no friction
        P = np.zeros(N)                         # news pressure
        T = np.ones(N)                          # public trust
        Rcore = R.copy()                        # revenue before the reach effect
        R12 = [R.copy()]                        # revenue history for the growth estimate

        # outputs
        out = {k: np.zeros((N, H, F)) for k in ("revenue", "earnings", "op_earnings", "compliance", "fines", "liability",
                                                 "liability_exp", "claims", "premium", "safety", "capability", "cap_eff", "reach", "offshore",
                                                 "comply", "sigma", "harm", "cat_harm", "harm_exp", "cat_harm_exp", "relocation")}
        out["incidents"] = np.zeros((N, H, F, K), dtype=bool)
        out["harm_cat"] = np.zeros((N, H, F, K))
        out["catastrophe"] = np.zeros((N, H, F), dtype=bool)
        out["audited"] = np.zeros((N, H, F), dtype=bool)
        out["fined"] = np.zeros((N, H, F), dtype=bool)
        prices = np.zeros((N, H + 1, F)); prices[:, 0, :] = 100.0
        series = {k: np.zeros((N, H)) for k in ("enforcement", "pressure", "trust", "service", "tone", "salience", "p_cat_any", "inc_exp")}
        out["major"] = np.zeros((N, H, F), dtype=bool)        # a major incident at the firm this month (for the validation moments)
        news_counts = np.zeros((N, H, 6))       # incident minor, incident major, catastrophe, enforcement, relocation, milestone
        events0 = []                            # representative path, for the wire
        first = {"delay": np.zeros(F, bool), "trust": False, "hearing": False, "safety": np.zeros(F, bool),
                 "milestone": np.floor(self.C0 / MILESTONE), "labour": 1.0, "reloc": np.zeros(F)}

        w0 = self.R0 / self.R0.sum()
        Q0 = float((w0 * self.C0 * self.D0).sum())

        def value(R_, run_rate_, g_):
            """Fundamental value: a revenue multiple plus an earnings multiple on forward earnings, with a smooth floor."""
            FE = 12.0 * run_rate_ * (1 + g_)
            k_ = 0.05 * R_
            return self.ps[None, :] * R_ + self.pe[None, :] * k_ * np.log1p(np.exp(np.clip(FE / k_, -30, 30)))

        # the valuation every index is measured from: the firms as they stand before any instrument is announced,
        # the same for every policy of the battery, so that an instrument's immediate effect on fundamentals shows
        # in the first month's price instead of disappearing into the base
        V_pre = value(self.R0[None, :], (self.R0 / 12.0 * self.margin)[None, :], self.g0[None, :])[0]
        cap0 = V_pre.copy()
        active_prev = False

        # what the monthly decision needs and does not change from month to month
        fixed = pol["fixed_cost"] * (~(self.small & pol["sandbox_small_firms"]))[None, :, None]
        var_c = pol["variable_cost"] * (1 - relabel)
        shield_f = af["safe_harbour_shield"] if pol["safe_harbour"] else 0.0
        dc = self._decision_constants(pol, a, aa, plan_months, mobility, coordinated, relabel, theatre, reloc_cost, bh_sum, sev_avg,
                                      fixed, var_c)
        # contagion runs between firms of one sector; a sector of one firm adds exactly nothing, so only the others are visited
        sector_masks = [mk for mk in (np.array([x == s for x in self.sector]) for s in sorted(set(self.sector))) if mk.sum() > 1]

        for t in range(H):
            active = (t >= pol["phase_in"]) and (pol["sunset"] == 0 or t < pol["phase_in"] + pol["sunset"])
            mora = active and pol["moratorium_months"] > 0 and t < pol["phase_in"] + pol["moratorium_months"]
            in_scope_pf = sector_in[None, :] & (Ceff * split >= cap_test) & active
            bind = np.where(in_scope_pf, 1.0 if coordinated else (1.0 - O), 0.0)      # share of activity bound

            # -------------------------------------------------- firm decisions --
            decide = self._decide_reference if self.reference else self._decide
            sigma_reported, sigma_c, om_c, chi_c, liab_c = decide(dc, in_scope_pf, mora, S, R, Ceff, D, O, e)
            bind_c = np.where(in_scope_pf, 1.0 if coordinated else (1.0 - om_c), 0.0)

            # ------------------------------------------------ monthly dynamics --
            O_new = O + np.clip(om_c - O, -0.1, 0.1)
            moved = np.maximum(0.0, O_new - O)
            reloc_cost_m = _ex(reloc_cost, 1) * moved * R
            O = O_new
            comp_m = chi_c * bind_c * (fixed[0, :, 0][None, :] + var_c * R * self.scope_share[None, :]) / 12.0
            S = np.clip(S + af["safety_learning"] * sigma_c / (sigma_c + 0.1) * (1 - S) - af["safety_decay"] * S, 0.02, 0.98)
            compute_now = 1.0 - pol["export_controls"] * O * self.compute_dep[None, :]
            diffusion = 0.0
            if self.open_w.any():
                C_open = (C * self.open_w[None, :]).max(axis=1, keepdims=True)
                restricted = pol["open_weights_restriction"] and active
                if not restricted:
                    diffusion = (af["open_weights_diffusion"] * 0.1 * np.maximum(0.0, C_open - C)
                                 * (self.is_model & ~self.open_w)[None, :])
            gC = af["capability_growth"] * (1 - af["safety_substitution"] * sigma_c) * compute_now + diffusion
            if mora:
                gC = np.where(in_scope_pf, gC * (1 - af["moratorium_research_slowdown"]), gC)
            C = C * np.exp(gC)
            Chist[t + 1] = C
            delay = np.rint(pol["release_delay"] * chi_c * bind_c).astype(int)
            src = np.clip(t + 1 - delay, 0, t + 1)
            Ceff_new = np.take_along_axis(Chist, src[None, :, :], axis=0)[0]
            if mora:
                frozen = np.where(in_scope_pf & np.isinf(frozen), Ceff, frozen)
            else:
                frozen[:] = np.inf
            Ceff_new = np.minimum(Ceff_new, frozen)
            dlogC = np.log(np.maximum(Ceff_new, 1e-6) / np.maximum(Ceff, 1e-6))
            Ceff = Ceff_new
            trust_f = np.sqrt(np.clip(T, 0.3, 1.0))[:, None]
            Dceil = (1 - np.exp(-af["reach_ceiling_k"] * Ceff))
            friction = pol["tier_friction"] * (1 - relabel) * np.where(sector_in[None, :] & active, 1.0, 0.0)
            D_new = D + af["reach_speed"] * (1 - friction) * (Dceil * trust_f - D)
            Dref = Dref + af["reach_speed"] * (Dceil - Dref)
            dD = D_new - D; D = D_new
            g_ref = af["capability_growth"] * (1 - af["safety_substitution"] * SIGMA_REF)             # scalar or (N, 1)
            dev_growth = ((dlogC - g_ref) * self.is_model[None, :] * R).sum(axis=1) / np.maximum((self.is_model[None, :] * R).sum(axis=1), 1e-9)
            g_fade = (af["long_run_growth"] + (self.g0[None, :] - af["long_run_growth"]) * np.exp(-t / af["growth_fade_months"])) / 12.0
            g_month = g_fade + af["revenue_capability_beta"] * (dlogC - g_ref) - af["offshore_revenue_haircut"] * O / 12.0
            g_month = g_month + af["chip_demand_coupling"] * dev_growth[:, None] * (self.is_chip * 1.0 + self.is_cloud * 0.5)[None, :]
            if pol["export_controls"] > 0:
                g_month = g_month - af["export_control_chip_loss"] * pol["export_controls"] / 12.0 * self.is_chip[None, :]
            if pol["open_weights_restriction"] and active:
                g_month = g_month - af["open_weights_restriction_growth_loss"] / 12.0 * self.open_w[None, :]
            Rcore = Rcore * (1 + np.clip(g_month, -0.2, 0.3))
            R = Rcore * (D / np.maximum(Dref, 1e-6)) ** af["revenue_reach_beta"]
            R12.append(R.copy())

            # ------------------------------------------------------- hazard --
            eval_eff = pol["eval_catch"] * chi_c * in_scope_pf * (0.5 if theatre else 1.0)
            common = ((Ceff) ** af["hazard_capability_elasticity"] * np.exp(-af["hazard_safety_elasticity"] * S)
                      * D ** af["hazard_reach_elasticity"] * (1 + O * af["offshore_laxity"]) * (1 - eval_eff * af["unsafe_release_share"]))
            lam = bh3 * common[:, :, None]
            transp = pol["transparency"] if active else 0.0
            restricted = bool(pol["open_weights_restriction"] and active)
            lam[:, :, 0] *= (1 - transp) * np.where(self.open_w[None, :] & (not restricted), af["open_weights_misuse_multiplier"], 1.0)
            lam[:, :, 2] *= (1 - 0.5 * transp)
            p_inc = 1 - np.exp(-lam)
            inc = rb.u_inc[:, t] < p_inc
            sev = sm3 * np.exp(_ex(ap["severity_sigma"], 2) * rb.z_sev[:, t])        # each incident's own harm, drawn or not
            harm_k = inc * sev
            harm_exp_k = p_inc * smean3                                             # E[harm_k | the state reached]
            p_cat = np.clip(af["catastrophe_prior_monthly"] * (Ceff > af["catastrophe_capability"]) * np.exp(-af["hazard_safety_elasticity"] * S)
                            * (1 + O * af["offshore_laxity"]) * (1 - 0.5 * eval_eff), 0.0, 1.0)      # each firm's marginal probability
            if p_cat.any():
                # firms' catastrophes share a common factor (shared models, components, vulnerabilities): a one factor
                # Gaussian copula with correlation rho leaves every firm's own probability at p_cat and makes joint
                # failures more likely than independence would
                cat = rb.u_cat[:, t] < conditional_event_probability(p_cat, rho, rb.z_common[:, t])
                p_any = any_event_probability(p_cat, rho, _GH)                      # P(at least one this month | state)
            else:
                cat = np.zeros((N, F), dtype=bool); p_any = np.zeros(N)
            cat_harm = cat * af["catastrophe_harm_bn"] * np.exp(af["catastrophe_severity_sigma"] * rb.z_cat[:, t])
            cat_harm_exp = p_cat * _ex(cat_mean, 1)
            harm_f = harm_k.sum(axis=2) + cat_harm
            harm_exp_f = harm_exp_k.sum(axis=2) + cat_harm_exp
            liab_share = pol["liability_multiplier"] * in_scope_pf * (1 - shield_f * chi_c)
            liab_due = liab_share * harm_f
            premium = np.zeros((N, F))
            liab_paid = np.zeros((N, F))
            liab_exp = np.zeros((N, F))                                            # E[liability the firm pays | state]
            if pol["liability_multiplier"] > 0 and pol["insurance_mandate"]:
                premium = (liab_c * (1 + af["insurance_loading"])) / 12.0       # the insurer pays the claims
            else:
                liab_paid = liab_due
                liab_exp = liab_share * harm_exp_f

            # --------------------------------------------------- enforcement --
            audited = (rb.u_audit[:, t] < af["audit_rate"] * e[:, None]) & in_scope_pf
            fined = audited & (chi_c < 0.5)
            fine = fined * pol["fine_rate"] * R * self.scope_share[None, :] * bind_c

            op_earn = R / 12.0 * self.margin[None, :]
            earnings = op_earn - comp_m - fine - liab_paid - premium - reloc_cost_m

            # ---------------------------------------------------------- news --
            # every incident is classified on its own harm: a firm month with two minor incidents is two minor
            # incidents, never one major one; a catastrophe is its own class
            major_k = inc & (sev >= _ex(ap["major_incident_bn"], 2))
            n_minor = (inc & ~major_k).sum(axis=(1, 2))
            n_major = major_k.sum(axis=(1, 2))
            n_cat = cat.sum(axis=1)
            n_enf = fined.sum(axis=1)
            n_rel = (moved > 0.05).sum(axis=1)
            n_mile = (np.floor(Ceff / MILESTONE) > np.floor((Ceff * np.exp(-dlogC)) / MILESTONE)).sum(axis=1)
            boost = 1 + (ap["news_reporting_boost"] if pol["incident_reporting"] and active else 0.0)
            neg = ((SALIENCE["minor"] * n_minor + SALIENCE["major"] * n_major + SALIENCE["catastrophe"] * n_cat) * boost
                   + SALIENCE["enforcement"] * n_enf + SALIENCE["relocation"] * n_rel)
            pos = SALIENCE["milestone"] * n_mile
            x = neg + 0.03 * np.abs(rb.z_news[:, t])
            P = ap["news_memory"] * P + (1 - ap["news_memory"]) * (1 - np.exp(-x))
            tone = (pos - neg) / np.maximum(pos + neg, 1e-9) * (pos + neg > 0)
            T = np.clip(T + ap["trust_recovery"] * (1 - T) - ap["trust_harm_sensitivity"] * np.log1p(harm_f.sum(axis=1)), 0.3, 1.0)
            e = np.clip(e + ap["enforcement_response"] * (capacity * (0.4 + 0.6 * P) - e), 0.0, 1.0)

            # -------------------------------------------------------- market --
            t12 = max(0, len(R12) - 13)
            g_est = np.clip(R / np.maximum(R12[t12], 1e-9) - 1.0, -0.3, 1.0) if t >= 11 else np.tile(self.g0, (N, 1))
            run_rate = op_earn - comp_m - premium - liab_c / 12.0           # one offs (fines, realised liability, moves) excluded
            V = value(R, run_rate, g_est)
            exposure = self.scope_share[None, :] * sector_in[None, :]
            ann = 0.0
            if t == 0 and not active:
                # an instrument announced now and in force later: the market anticipates costs that fundamentals do
                # not carry yet. One in force from the first month is already in V, so nothing is added to it.
                exp_cost = (pol["fixed_cost"] + pol["variable_cost"] * R * self.scope_share[None, :]) * sector_in[None, :]
                exp_liab = pol["liability_multiplier"] * 0.3 * sector_in[None, :]
                ann = -af["announcement_impact"] * (exp_cost + exp_liab) / np.maximum(12.0 * earnings, 0.05 * R) * 0.5
                ann = np.clip(ann, -0.25, 0.0)
            own_jump = -af["incident_jump"] * 0.05 * np.log1p((harm_f + liab_paid + fine + reloc_cost_m) / np.maximum(R / 12.0, 1e-6))
            sector_jump = np.zeros((N, F))
            for m in sector_masks:
                sj = (own_jump * m[None, :]).sum(axis=1, keepdims=True) - own_jump * m[None, :]
                sector_jump += af["contagion"] * sj * m[None, :] / max(1, m.sum() - 1)
            xi = (af["sentiment_persistence"] * xi + self.beta[None, :] * af["market_vol"] * rb.z_market[:, t][:, None]
                  + 0.01 * exposure * rb.z_policy[:, t][:, None] - af["news_price_impact"] * P[:, None] * (0.3 + exposure)
                  + own_jump + sector_jump + ann + self.ivol[None, :] * rb.z_idio[:, t])
            px = 100.0 * V / V_pre[None, :] * np.exp(xi)
            prices[:, t + 1, :] = px

            # ------------------------------------------------------- record --
            out["revenue"][:, t] = R; out["earnings"][:, t] = earnings; out["op_earnings"][:, t] = op_earn
            out["compliance"][:, t] = comp_m
            out["fines"][:, t] = fine; out["liability"][:, t] = liab_paid; out["premium"][:, t] = premium
            out["claims"][:, t] = liab_due; out["harm_exp"][:, t] = harm_exp_f; out["cat_harm_exp"][:, t] = cat_harm_exp
            out["liability_exp"][:, t] = liab_exp
            series["p_cat_any"][:, t] = p_any
            series["inc_exp"][:, t] = p_inc.sum(axis=(1, 2))        # expected number of incidents this month | state
            out["safety"][:, t] = S; out["capability"][:, t] = C; out["cap_eff"][:, t] = Ceff; out["reach"][:, t] = D
            out["offshore"][:, t] = O; out["comply"][:, t] = chi_c; out["sigma"][:, t] = sigma_reported
            out["harm"][:, t] = harm_f; out["cat_harm"][:, t] = cat_harm; out["relocation"][:, t] = reloc_cost_m
            out["incidents"][:, t] = inc; out["harm_cat"][:, t] = harm_k; out["catastrophe"][:, t] = cat
            out["audited"][:, t] = audited; out["fined"][:, t] = fined; out["major"][:, t] = major_k.any(axis=2)
            Q = (w0[None, :] * Ceff * D).sum(axis=1) / Q0
            series["enforcement"][:, t] = e; series["pressure"][:, t] = P; series["trust"][:, t] = T
            series["service"][:, t] = Q; series["tone"][:, t] = tone; series["salience"][:, t] = neg + pos
            news_counts[:, t] = np.stack([n_minor, n_major, n_cat, n_enf, n_rel, n_mile], axis=1)

            # events on the representative path
            ev = self._events(t, pol, active, active_prev, mora, inc[0], harm_k[0], major_k[0], cat[0], cat_harm[0], fined[0], fine[0],
                              O[0], Ceff[0], dlogC[0], S[0], T[0], P[0], Q[0], px[0], prices[0, t], delay[0],
                              in_scope_pf[0], chi_c[0], first)
            events0.append(ev)
            active_prev = active
            if stream is not None:
                stream(t, {"prices": px[0].tolist(), "events": ev, "pressure": float(P[0]), "trust": float(T[0]),
                           "enforcement": float(e[0]), "service": float(Q[0])})

        cap_end = cap0[None, :] * prices[:, -1, :] / 100.0
        return PolicyResult(policy=pol, prices=prices, cap0=cap0, cap_end=cap_end, series=series, news_counts=news_counts,
                            events0=events0, labels=self.labels, sectors=self.sector, horizon=H, n_paths=N,
                            path_index=rb.index.copy(), sector_in=sector_in, rd_share=self.rd, scope_share=self.scope_share, **out)


    # ------------------------------------------------------------- decisions --
    def _decision_constants(self, pol, a, aa, plan_months, mobility, coordinated, relabel, theatre, reloc_cost, bh_sum, sev_avg,
                            fixed, var_c):
        """Everything the firms' monthly choice uses that does not change during a run, laid out against the five
        axes (paths, firms, safety share, offshore share, comply)."""
        N = self.N
        a5 = {}
        for k, v in a.items():
            a5[k] = float(v) if np.ndim(v) == 0 else np.asarray(v, dtype=float)[:, None, None, None, None]
        c = PolicyResult(pol=pol, aa=aa, a5=a5, plan_months=plan_months, mobility=mobility, coordinated=coordinated, relabel=relabel,
                         theatre=theatre, reloc_cost=reloc_cost, bh_sum=bh_sum, sev_avg=sev_avg, fixed=fixed, var_c=var_c)
        c.om5 = np.minimum(OM5, mobility[None, :, None, None, None])                       # (1, F, 1, 4, 1)
        c.one_minus_om5 = 1.0 - c.om5
        c.mss = pol["min_safety_share"]
        c.liable = pol["liability_multiplier"] != 0
        c.export = pol["export_controls"] != 0
        c.delay = pol["release_delay"] != 0
        c.costly = (pol["fixed_cost"] != 0) or (var_c != 0)
        c.fines = pol["fine_rate"] != 0
        c.fixed5 = fixed[:, :, :, None, None]
        c.scope5 = self.scope_share[None, :, None, None, None]
        c.margin5 = np.maximum(self.margin, 0.1)[None, :, None, None, None]
        c.compute_f5 = 1.0 - pol["export_controls"] * c.om5 * self.compute_dep[None, :, None, None, None]
        c.pm_cg = plan_months * a5["capability_growth"]
        c.learn_g = a5["safety_learning"] * SIG5 / (SIG5 + 0.1)                             # at the six grid shares
        c.G_g = (1 - a5["safety_substitution"] * SIG5)
        c.orh_om = a5["offshore_revenue_haircut"] * c.om5
        c.lax5 = (1 + c.om5 * a5["offshore_laxity"])
        c.culture_cw = self.culture[None, :, None, None, None] * a5["culture_weight"]
        c.reloc5 = _ex(reloc_cost, 4)
        c.bh5 = _ex(bh_sum, 4)
        c.sev5 = _ex(sev_avg, 4)
        c.nI = np.arange(N)[:, None]
        c.fI = np.arange(self.F)[None, :]
        return c

    def _decide(self, c, in_scope_pf, mora, S, R, Ceff, D, O, e):
        """The firms' choice for the coming year: the action (safety share, offshore share, comply) with the highest
        expected payoff. Returns the safety share reported, the one practised, the offshore share, the compliance
        flag and the expected liability of the chosen action, each (paths, firms).

        The payoff is the one written out in _decide_reference, term for term and in the same order of operations, so
        the two give the same bits. This routine computes each term only on the action axes it depends on (a safety
        term on six values, an offshore term on four, their combinations only where the payoff is assembled), leaves
        out a term the policy sets to zero, and evaluates the exponential of the hazard once per distinct safety
        share; that is where the engine spends most of its time."""
        pol, a5, pm = c.pol, c.a5, c.plan_months
        N, F = self.N, self.F
        S5 = S[:, :, None, None, None]
        R5 = R[:, :, None, None, None]
        insc5 = in_scope_pf[:, :, None, None, None]
        bind_a = np.where(insc5, 1.0 if c.coordinated else c.one_minus_om5, 0.0)            # (N, F, 1, J, 1)
        liable = c.liable
        if liable:
            ceff_p = ((Ceff[:, :, None]) ** c.aa["hazard_capability_elasticity"])[:, :, :, None, None]
            d_p = (D[:, :, None] ** c.aa["hazard_reach_elasticity"])[:, :, :, None, None]
            cat_live = (Ceff[:, :, None, None, None] > a5["catastrophe_capability"]).astype(float)

        def parts(learn, G):
            """The terms of the payoff that depend on the safety share practised, for one set of shares: the growth
            value before any release delay, the culture term and the expected liability before any shield."""
            S12 = np.clip(S5 + pm * (learn * (1 - S5) - a5["safety_decay"] * S5), 0.02, 0.98)
            dC = c.pm_cg * G
            if c.export:
                dC = dC * c.compute_f5
            if mora:
                dC = np.where(insc5, dC * (1 - a5["moratorium_research_slowdown"]), dC)
            gv = a5["growth_value_weight"] * R5 * a5["revenue_capability_beta"] * dC
            cult = c.culture_cw * R5 * (S12 - S5)
            liab = None
            if liable:
                E12 = np.exp(-a5["hazard_safety_elasticity"] * S12)
                haz = (c.bh5 * ceff_p * E12 * d_p * c.lax5)
                lam_year = pm * haz * a5["firm_optimism"]
                exp_harm = lam_year * c.sev5
                exp_harm = exp_harm + pm * a5["catastrophe_prior_monthly"] * cat_live * E12 * a5["catastrophe_harm_bn"] * a5["firm_optimism"]
                liab = pol["liability_multiplier"] * exp_harm * insc5
            return gv, cult, liab

        U, cult, liab = parts(c.learn_g, c.G_g)                 # at the six grid shares
        m = None
        if c.mss != 0:
            # a complying firm in scope practises at least the floor m: its safety share is the grid value where that
            # is at least m and m otherwise. The terms are computed at the grid values and at m, then placed.
            m = c.mss * bind_a
            ge = SIG5 >= m
            gv_m, cult_m, liab_m = parts(a5["safety_learning"] * m / (m + 0.1), (1 - a5["safety_substitution"] * m))
            U = _join(U, np.where(ge, U, gv_m))
            cult = _join(cult, np.where(ge, cult, cult_m))
            if liable:
                liab = _join(liab, np.where(ge, liab, liab_m))
        if c.delay:
            delay_a = pol["release_delay"] * CHI5 * bind_a
            U = U * np.maximum(0.0, 1 - delay_a / pm)
        if c.costly:
            comp_cost = CHI5 * bind_a * (c.fixed5 + c.var_c * R5 * c.scope5)
            U = U - comp_cost * (pm / 12)
        if c.fines:
            audit_p = a5["audit_rate"] * e[:, None, None, None, None]
            U = U - (1 - CHI5) * bind_a * pm * audit_p * pol["fine_rate"] * R5 * c.scope5 * 1.5
        U = U - c.reloc5 * np.maximum(0.0, c.om5 - O[:, :, None, None, None]) * R5
        U = U - c.orh_om * R5 * c.margin5 * (pm / 12)
        if liable:
            if pol["safe_harbour"]:
                liab = liab * (1 - a5["safe_harbour_shield"] * CHI5)
            if pol["insurance_mandate"]:
                U = U - liab * (1 + a5["insurance_loading"])
            else:
                U = U - liab
                U = U - a5["firm_risk_aversion"] * 0.5 * liab
        U = U + cult

        # the first maximum in the order (safety share, offshore share, comply); an axis the payoff does not vary
        # along has length one here and the reference picks its first value, which is index zero
        best = np.argmax(U.reshape(N, F, -1), axis=2)
        I, J, K = np.unravel_index(best, U.shape[2:])
        nI, fI = c.nI, c.fI

        def pick(x):
            sh = x.shape
            return np.array(np.broadcast_to(x[nI if sh[0] > 1 else 0, fI if sh[1] > 1 else 0, I if sh[2] > 1 else 0,
                                              J if sh[3] > 1 else 0, K if sh[4] > 1 else 0], (N, F)))
        sigma_reported = SIGMA_GRID[I]
        if m is not None:                                # the floor binds where the firm complies
            sigma_reported = np.where(K == 1, np.maximum(sigma_reported, pick(m)), sigma_reported)
        sigma_c = sigma_reported if not c.theatre else SIGMA_GRID[I]          # theatre: the floor is reported, not practised
        om_c = pick(c.om5)
        chi_c = COMPLY_GRID[K]
        liab_c = pick(liab) if liab is not None else np.zeros((N, F))
        return sigma_reported, sigma_c, om_c, chi_c, liab_c

    def _decide_reference(self, c, in_scope_pf, mora, S, R, Ceff, D, O, e):
        """The same choice written out on the full grid of 48 actions, every term on every action: the definition
        _decide is tested against (tests/test_core.py)."""
        pol, aa = c.pol, c.aa
        N, F = self.N, self.F
        plan_months, mobility, coordinated, relabel, theatre = c.plan_months, c.mobility, c.coordinated, c.relabel, c.theatre
        reloc_cost, bh_sum, sev_avg = c.reloc_cost, c.bh_sum, c.sev_avg
        # expected incident rate per year under each safety share, from the firm's own view
        A = len(self.sig_a)
        sig = self.sig_a[None, None, :]
        om = np.minimum(self.om_a[None, None, :], mobility[None, :, None])
        chi = self.chi_a[None, None, :]
        bind_a = np.where(in_scope_pf[:, :, None], 1.0 if coordinated else (1.0 - om), 0.0)
        min_s = pol["min_safety_share"] * chi * bind_a
        sig_eff = np.maximum(sig, min_s)
        learn = aa["safety_learning"] * sig_eff / (sig_eff + 0.1)
        S12 = np.clip(S[:, :, None] + plan_months * (learn * (1 - S[:, :, None]) - aa["safety_decay"] * S[:, :, None]), 0.02, 0.98)
        compute_f = 1.0 - pol["export_controls"] * om * self.compute_dep[None, :, None]
        dC = plan_months * aa["capability_growth"] * (1 - aa["safety_substitution"] * sig_eff) * compute_f
        if mora:
            dC = np.where(in_scope_pf[:, :, None], dC * (1 - aa["moratorium_research_slowdown"]), dC)
        delay_a = pol["release_delay"] * chi * bind_a
        growth_value = aa["growth_value_weight"] * R[:, :, None] * aa["revenue_capability_beta"] * dC * np.maximum(0.0, 1 - delay_a / plan_months)
        haz = (_ex(bh_sum, 2) * (Ceff[:, :, None]) ** aa["hazard_capability_elasticity"] * np.exp(-aa["hazard_safety_elasticity"] * S12)
               * D[:, :, None] ** aa["hazard_reach_elasticity"] * (1 + om * aa["offshore_laxity"]))
        lam_year = plan_months * haz * aa["firm_optimism"]
        exp_harm = lam_year * _ex(sev_avg, 2)
        cat_live = (Ceff[:, :, None] > aa["catastrophe_capability"]).astype(float)
        exp_harm = exp_harm + plan_months * aa["catastrophe_prior_monthly"] * cat_live * np.exp(-aa["hazard_safety_elasticity"] * S12) * aa["catastrophe_harm_bn"] * aa["firm_optimism"]
        shield_a = aa["safe_harbour_shield"] if pol["safe_harbour"] else 0.0
        liab = pol["liability_multiplier"] * exp_harm * in_scope_pf[:, :, None] * (1 - shield_a * chi)
        if pol["insurance_mandate"]:
            liab_cost = liab * (1 + aa["insurance_loading"]); risk = 0.0 * liab
        else:
            liab_cost = liab; risk = aa["firm_risk_aversion"] * 0.5 * liab
        fixed = pol["fixed_cost"] * (~(self.small & pol["sandbox_small_firms"]))[None, :, None]
        var_c = pol["variable_cost"] * (1 - relabel)
        comp_cost = chi * bind_a * (fixed + var_c * R[:, :, None] * self.scope_share[None, :, None])
        audit_p = aa["audit_rate"] * e[:, None, None]
        penalty = (1 - chi) * bind_a * plan_months * audit_p * pol["fine_rate"] * R[:, :, None] * self.scope_share[None, :, None] * 1.5
        reloc = _ex(reloc_cost, 2) * np.maximum(0.0, om - O[:, :, None]) * R[:, :, None]
        haircut = aa["offshore_revenue_haircut"] * om * R[:, :, None] * np.maximum(self.margin, 0.1)[None, :, None] * (plan_months / 12)
        culture_term = self.culture[None, :, None] * aa["culture_weight"] * R[:, :, None] * (S12 - S[:, :, None])
        U = growth_value - comp_cost * (plan_months / 12) - penalty - reloc - haircut - liab_cost - risk + culture_term
        best = np.argmax(U, axis=2)                                   # (N, F)
        idx = (np.arange(N)[:, None], np.arange(F)[None, :], best)
        sig_full = np.broadcast_to(sig, (N, F, A)); om_full = np.broadcast_to(om, (N, F, A))
        chi_full = np.broadcast_to(chi, (N, F, A))
        sigma_reported = sig_eff[idx]
        sigma_c = sigma_reported if not theatre else sig_full[idx]
        om_c = om_full[idx]; chi_c = chi_full[idx]
        return sigma_reported, sigma_c, om_c, chi_c, liab[idx]

    # --------------------------------------------------------------- events --
    def _events(self, t, pol, active, active_prev, mora, inc, harm_k, major_k, cat, cat_harm, fined, fine, O_now, Ceff, dlogC, S, T, P, Q,
                px, px_prev, delay, in_scope_pf, chi, first):
        ev = []
        F = self.F
        if active and not active_prev:
            ev.append({"type": "policy_start", "pol": pol["label"], "mora": mora})
        if mora and t == pol["phase_in"] + pol["moratorium_months"] - 1:
            ev.append({"type": "moratorium_end", "pol": pol["label"]})
        if pol["sunset"] and t == pol["phase_in"] + pol["sunset"]:
            ev.append({"type": "policy_sunset", "pol": pol["label"]})
        for f in range(F):
            if cat[f]:
                ev.append({"type": "catastrophe", "firm": f, "harm": float(cat_harm[f])})
            for k in range(len(CATEGORIES)):
                if inc[f, k]:
                    ev.append({"type": "incident", "firm": f, "cat": CATEGORIES[k], "harm": float(harm_k[f, k]),
                               "major": bool(major_k[f, k])})
            if fined[f]:
                ev.append({"type": "enforcement", "firm": f, "fine": float(fine[f])})
            if np.floor(O_now[f] / 0.25 + 1e-9) > first["reloc"][f]:
                first["reloc"][f] = np.floor(O_now[f] / 0.25 + 1e-9)
                ev.append({"type": "relocation", "firm": f, "share": float(O_now[f])})
            m = np.floor(Ceff[f] / MILESTONE)
            if m > first["milestone"][f]:
                first["milestone"][f] = m
                ev.append({"type": "release", "firm": f, "capability": float(Ceff[f])})
            if delay[f] > 0 and not first["delay"][f] and in_scope_pf[f] and chi[f] > 0:
                first["delay"][f] = True
                ev.append({"type": "licence_delay", "firm": f, "months": int(delay[f])})
            if S[f] > 0.75 and not first["safety"][f]:
                first["safety"][f] = True
                ev.append({"type": "safety_milestone", "firm": f, "safety": float(S[f])})
            ret = px[f] / max(px_prev[f], 1e-9) - 1
            if abs(ret) >= 0.20:
                ev.append({"type": "market_move", "firm": f, "ret": float(ret)})
        if T < 0.7 and not first["trust"]:
            first["trust"] = True
            ev.append({"type": "trust_fall", "trust": float(T)})
        if P > 0.45 and not first["hearing"]:
            first["hearing"] = True
            ev.append({"type": "hearing", "pressure": float(P)})
        if P < 0.2:
            first["hearing"] = False
        if Q > first["labour"] * 1.25:
            first["labour"] = Q
            ev.append({"type": "labour", "service": float(Q)})
        return ev


# ------------------------------------------------------------------ helpers --
def battery_hash(battery):
    """SHA-256 of the planned battery: policies, firms, assumptions, horizon, paths, seed."""
    import hashlib
    import json
    return hashlib.sha256(json.dumps(battery, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()
