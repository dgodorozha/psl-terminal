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
"""

import numpy as np

from .policies import in_scope

CATEGORIES = ("misuse", "accident", "systemic")
MODEL_SECTORS = ("frontier_lab", "open_weights", "consumer_ai", "autonomy", "startups")
SIGMA_GRID = np.array([0.02, 0.05, 0.10, 0.15, 0.20, 0.30])
OFFSHORE_GRID = np.array([0.0, 0.3, 0.6, 0.9])
COMPLY_GRID = np.array([0.0, 1.0])
CULTURE_WEIGHT = 0.6          # $bn of valued safety per unit revenue per unit of safety gain, times culture
SIGMA_REF = 0.1               # the safety share the baseline growth rates already assume
REACH_K = 1.5                 # reach ceiling 1 - exp(-k C)
OPEN_WEIGHTS_MISUSE = 1.3     # misuse rate multiplier for a firm that publishes weights
OPEN_WEIGHTS_RESTRICTION_GROWTH = 0.10   # annual revenue growth lost by the open developer under a restriction
MILESTONE = 0.25


class RandomBundle:
    """Common random numbers for one battery: the same draws for every policy.

    Every path has its own stream seeded by (seed, path index), so a bundle of
    fewer paths is exactly the first paths of a larger one with the same seed:
    an assurance re simulation on a smaller budget can be paired path by path
    with the main run, and its effect reported as a shift of the headline figure."""

    def __init__(self, n_paths, horizon, n_firms, seed):
        N, H, F, C = n_paths, horizon, n_firms, len(CATEGORIES)
        self.seed = seed
        names = ("z_market", "z_policy", "z_idio", "u_inc", "z_sev", "u_cat", "z_cat", "u_audit", "z_news")
        parts = {k: [] for k in names}
        for i in range(N):
            rng = np.random.default_rng([int(seed), i])
            parts["z_market"].append(rng.standard_normal(H))
            parts["z_policy"].append(rng.standard_normal(H))
            parts["z_idio"].append(rng.standard_normal((H, F)))
            parts["u_inc"].append(rng.random((H, F, C)))
            parts["z_sev"].append(rng.standard_normal((H, F, C)))
            parts["u_cat"].append(rng.random((H, F)))
            parts["z_cat"].append(rng.standard_normal((H, F)))
            parts["u_audit"].append(rng.random((H, F)))
            parts["z_news"].append(rng.standard_normal(H))
        for k in names:
            setattr(self, k, np.stack(parts[k], axis=0))


class PolicyResult:
    """Arrays of one policy's run; see the module docstring for the names."""

    def __init__(self, **kw):
        self.__dict__.update(kw)


def _actions():
    """The firm's action grid as three flat arrays (A,)."""
    s, o, c = np.meshgrid(SIGMA_GRID, OFFSHORE_GRID, COMPLY_GRID, indexing="ij")
    return s.ravel(), o.ravel(), c.ravel()


class Economy:
    def __init__(self, firms, assumptions, horizon=60, n_paths=240, seed=7, bundle=None, hooks=None):
        self.firms = firms
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
        base_haz = np.array([a["hazard_base_misuse"], a["hazard_base_accident"], a["hazard_base_systemic"]])
        sev_med = np.array([a["severity_misuse_median_bn"], a["severity_accident_median_bn"], a["severity_systemic_median_bn"]])
        sev_mean = sev_med * np.exp(0.5 * a["severity_sigma"] ** 2)

        # policy scope per firm (sector test); the capability test is per path and month
        sector_in = np.array([in_scope(pol, s) for s in self.sector])
        cap_test = float(pol["capability_threshold"])
        split = float(gaming.get("threshold_split", 1.0))          # scope capability shown to the regulator
        theatre = bool(gaming.get("compliance_theatre", False))
        mobility = np.minimum(1.0, self.mobility * float(gaming.get("mobility_boost", 1.0)))
        reloc_cost = a["relocation_cost"] * float(gaming.get("relocation_discount", 1.0))
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
                                                 "premium", "safety", "capability", "cap_eff", "reach", "offshore", "comply",
                                                 "sigma", "harm", "cat_harm", "relocation")}
        out["incidents"] = np.zeros((N, H, F, K), dtype=bool)
        out["harm_cat"] = np.zeros((N, H, F, K))
        out["catastrophe"] = np.zeros((N, H, F), dtype=bool)
        out["audited"] = np.zeros((N, H, F), dtype=bool)
        out["fined"] = np.zeros((N, H, F), dtype=bool)
        prices = np.zeros((N, H + 1, F)); prices[:, 0, :] = 100.0
        series = {k: np.zeros((N, H)) for k in ("enforcement", "pressure", "trust", "service", "tone", "salience")}
        news_counts = np.zeros((N, H, 6))       # incident minor, incident major, catastrophe, enforcement, relocation, milestone
        events0 = []                            # representative path, for the wire
        first = {"delay": np.zeros(F, bool), "trust": False, "hearing": False, "safety": np.zeros(F, bool),
                 "milestone": np.floor(self.C0 / MILESTONE), "labour": 1.0, "reloc": np.zeros(F)}

        w0 = self.R0 / self.R0.sum()
        Q0 = float((w0 * self.C0 * self.D0).sum())
        E0 = None; V0 = None; cap0 = None
        active_prev = False

        for t in range(H):
            active = (t >= pol["phase_in"]) and (pol["sunset"] == 0 or t < pol["phase_in"] + pol["sunset"])
            mora = active and pol["moratorium_months"] > 0 and t < pol["phase_in"] + pol["moratorium_months"]
            in_scope_pf = sector_in[None, :] & (Ceff * split >= cap_test) & active
            bind = np.where(in_scope_pf, 1.0 if coordinated else (1.0 - O), 0.0)      # share of activity bound

            # -------------------------------------------------- firm decisions --
            # expected incident rate per year under each safety share, from the firm's own view
            A = len(self.sig_a)
            sig = self.sig_a[None, None, :]
            om = np.minimum(self.om_a[None, None, :], mobility[None, :, None])
            chi = self.chi_a[None, None, :]
            bind_a = np.where(in_scope_pf[:, :, None], 1.0 if coordinated else (1.0 - om), 0.0)
            min_s = pol["min_safety_share"] * chi * bind_a
            sig_eff = np.maximum(sig, min_s)
            learn = a["safety_learning"] * sig_eff / (sig_eff + 0.1)
            S12 = np.clip(S[:, :, None] + plan_months * (learn * (1 - S[:, :, None]) - a["safety_decay"] * S[:, :, None]), 0.02, 0.98)
            compute_f = 1.0 - pol["export_controls"] * om * self.compute_dep[None, :, None]
            dC = plan_months * a["capability_growth"] * (1 - a["safety_substitution"] * sig_eff) * compute_f
            if mora:
                dC = np.where(in_scope_pf[:, :, None], dC * (1 - a["moratorium_research_slowdown"]), dC)
            delay_a = pol["release_delay"] * chi * bind_a
            growth_value = a["growth_value_weight"] * R[:, :, None] * a["revenue_capability_beta"] * dC * np.maximum(0.0, 1 - delay_a / plan_months)
            haz = (base_haz.sum() * (Ceff[:, :, None]) ** a["hazard_capability_elasticity"] * np.exp(-a["hazard_safety_elasticity"] * S12)
                   * D[:, :, None] ** a["hazard_reach_elasticity"] * (1 + om * a["offshore_laxity"]))
            lam_year = plan_months * haz * a["firm_optimism"]
            exp_harm = lam_year * float((base_haz / base_haz.sum() * sev_mean).sum())
            cat_live = (Ceff[:, :, None] > a["catastrophe_capability"]).astype(float)
            exp_harm = exp_harm + plan_months * a["catastrophe_prior_monthly"] * cat_live * np.exp(-a["hazard_safety_elasticity"] * S12) * a["catastrophe_harm_bn"] * a["firm_optimism"]
            shield = a["safe_harbour_shield"] if pol["safe_harbour"] else 0.0
            liab = pol["liability_multiplier"] * exp_harm * in_scope_pf[:, :, None] * (1 - shield * chi)
            if pol["insurance_mandate"]:
                liab_cost = liab * (1 + a["insurance_loading"]); risk = 0.0 * liab
            else:
                liab_cost = liab; risk = a["firm_risk_aversion"] * 0.5 * liab
            fixed = pol["fixed_cost"] * (~(self.small & pol["sandbox_small_firms"]))[None, :, None]
            var_c = pol["variable_cost"] * (1 - relabel)
            comp_cost = chi * bind_a * (fixed + var_c * R[:, :, None] * self.scope_share[None, :, None])
            audit_p = a["audit_rate"] * e[:, None, None]
            penalty = (1 - chi) * bind_a * plan_months * audit_p * pol["fine_rate"] * R[:, :, None] * self.scope_share[None, :, None] * 1.5
            reloc = reloc_cost * np.maximum(0.0, om - O[:, :, None]) * R[:, :, None]
            haircut = a["offshore_revenue_haircut"] * om * R[:, :, None] * np.maximum(self.margin, 0.1)[None, :, None] * (plan_months / 12)
            culture_term = self.culture[None, :, None] * CULTURE_WEIGHT * R[:, :, None] * (S12 - S[:, :, None])
            U = growth_value - comp_cost * (plan_months / 12) - penalty - reloc - haircut - liab_cost - risk + culture_term
            best = np.argmax(U, axis=2)                                   # (N, F)
            idx = (np.arange(N)[:, None], np.arange(F)[None, :], best)
            sig_full = np.broadcast_to(sig, (N, F, A)); om_full = np.broadcast_to(om, (N, F, A))
            chi_full = np.broadcast_to(chi, (N, F, A))
            sigma_reported = sig_eff[idx]
            sigma_c = sigma_reported if not theatre else sig_full[idx]
            om_c = om_full[idx]; chi_c = chi_full[idx]
            bind_c = np.where(in_scope_pf, 1.0 if coordinated else (1.0 - om_c), 0.0)

            # ------------------------------------------------ monthly dynamics --
            O_new = O + np.clip(om_c - O, -0.1, 0.1)
            moved = np.maximum(0.0, O_new - O)
            reloc_cost_m = reloc_cost * moved * R
            O = O_new
            comp_m = chi_c * bind_c * (fixed[0, :, 0][None, :] + var_c * R * self.scope_share[None, :]) / 12.0
            S = np.clip(S + a["safety_learning"] * sigma_c / (sigma_c + 0.1) * (1 - S) - a["safety_decay"] * S, 0.02, 0.98)
            compute_now = 1.0 - pol["export_controls"] * O * self.compute_dep[None, :]
            diffusion = 0.0
            if self.open_w.any():
                C_open = (C * self.open_w[None, :]).max(axis=1, keepdims=True)
                restricted = pol["open_weights_restriction"] and active
                if not restricted:
                    diffusion = (a["open_weights_diffusion"] * 0.1 * np.maximum(0.0, C_open - C)
                                 * (self.is_model & ~self.open_w)[None, :])
            gC = a["capability_growth"] * (1 - a["safety_substitution"] * sigma_c) * compute_now + diffusion
            if mora:
                gC = np.where(in_scope_pf, gC * (1 - a["moratorium_research_slowdown"]), gC)
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
            Dceil = (1 - np.exp(-REACH_K * Ceff))
            friction = pol["tier_friction"] * (1 - relabel) * np.where(sector_in[None, :] & active, 1.0, 0.0)
            D_new = D + a["reach_speed"] * (1 - friction) * (Dceil * trust_f - D)
            Dref = Dref + a["reach_speed"] * (Dceil - Dref)
            dD = D_new - D; D = D_new
            g_ref = a["capability_growth"] * (1 - a["safety_substitution"] * SIGMA_REF)
            dev_growth = ((dlogC - g_ref) * self.is_model[None, :] * R).sum(axis=1) / np.maximum((self.is_model[None, :] * R).sum(axis=1), 1e-9)
            g_fade = (a["long_run_growth"] + (self.g0[None, :] - a["long_run_growth"]) * np.exp(-t / a["growth_fade_months"])) / 12.0
            g_month = g_fade + a["revenue_capability_beta"] * (dlogC - g_ref) - a["offshore_revenue_haircut"] * O / 12.0
            g_month = g_month + a["chip_demand_coupling"] * dev_growth[:, None] * (self.is_chip * 1.0 + self.is_cloud * 0.5)[None, :]
            if pol["export_controls"] > 0:
                g_month = g_month - a["export_control_chip_loss"] * pol["export_controls"] / 12.0 * self.is_chip[None, :]
            if pol["open_weights_restriction"] and active:
                g_month = g_month - OPEN_WEIGHTS_RESTRICTION_GROWTH / 12.0 * self.open_w[None, :]
            Rcore = Rcore * (1 + np.clip(g_month, -0.2, 0.3))
            R = Rcore * (D / np.maximum(Dref, 1e-6)) ** a["revenue_reach_beta"]
            R12.append(R.copy())

            # ------------------------------------------------------- hazard --
            eval_eff = pol["eval_catch"] * chi_c * in_scope_pf * (0.5 if theatre else 1.0)
            common = ((Ceff) ** a["hazard_capability_elasticity"] * np.exp(-a["hazard_safety_elasticity"] * S)
                      * D ** a["hazard_reach_elasticity"] * (1 + O * a["offshore_laxity"]) * (1 - eval_eff * a["unsafe_release_share"]))
            lam = base_haz[None, None, :] * common[:, :, None]
            transp = pol["transparency"] if active else 0.0
            restricted = bool(pol["open_weights_restriction"] and active)
            lam[:, :, 0] *= (1 - transp) * np.where(self.open_w[None, :] & (not restricted), OPEN_WEIGHTS_MISUSE, 1.0)
            lam[:, :, 2] *= (1 - 0.5 * transp)
            p_inc = 1 - np.exp(-lam)
            inc = rb.u_inc[:, t] < p_inc
            harm_k = inc * sev_med[None, None, :] * np.exp(a["severity_sigma"] * rb.z_sev[:, t])
            p_cat = (a["catastrophe_prior_monthly"] * (Ceff > a["catastrophe_capability"]) * np.exp(-a["hazard_safety_elasticity"] * S)
                     * (1 + O * a["offshore_laxity"]) * (1 - 0.5 * eval_eff))
            cat = rb.u_cat[:, t] < p_cat
            cat_harm = cat * a["catastrophe_harm_bn"] * np.exp(0.5 * rb.z_cat[:, t])
            harm_f = harm_k.sum(axis=2) + cat_harm
            liab_due = pol["liability_multiplier"] * harm_f * in_scope_pf * (1 - shield * chi_c)
            premium = np.zeros((N, F))
            liab_paid = np.zeros((N, F))
            if pol["liability_multiplier"] > 0 and pol["insurance_mandate"]:
                premium = (liab[idx] * (1 + a["insurance_loading"])) / 12.0
            else:
                liab_paid = liab_due

            # --------------------------------------------------- enforcement --
            audited = (rb.u_audit[:, t] < a["audit_rate"] * e[:, None]) & in_scope_pf
            fined = audited & (chi_c < 0.5)
            fine = fined * pol["fine_rate"] * R * self.scope_share[None, :] * bind_c

            op_earn = R / 12.0 * self.margin[None, :]
            earnings = op_earn - comp_m - fine - liab_paid - premium - reloc_cost_m

            # ---------------------------------------------------------- news --
            major = harm_f >= a["major_incident_bn"]
            n_minor = (inc.any(axis=2) & ~major & ~cat).sum(axis=1)
            n_major = (major & ~cat).sum(axis=1)
            n_cat = cat.sum(axis=1)
            n_enf = fined.sum(axis=1)
            n_rel = (moved > 0.05).sum(axis=1)
            n_mile = (np.floor(Ceff / MILESTONE) > np.floor((Ceff * np.exp(-dlogC)) / MILESTONE)).sum(axis=1)
            boost = 1 + (a["news_reporting_boost"] if pol["incident_reporting"] and active else 0.0)
            neg = (0.12 * n_minor + 0.45 * n_major + 1.2 * n_cat) * boost + 0.2 * n_enf + 0.15 * n_rel
            pos = 0.08 * n_mile
            x = neg + 0.03 * np.abs(rb.z_news[:, t])
            P = a["news_memory"] * P + (1 - a["news_memory"]) * (1 - np.exp(-x))
            tone = (pos - neg) / np.maximum(pos + neg, 1e-9) * (pos + neg > 0)
            T = np.clip(T + a["trust_recovery"] * (1 - T) - a["trust_harm_sensitivity"] * np.log1p(harm_f.sum(axis=1)), 0.3, 1.0)
            e = np.clip(e + a["enforcement_response"] * (capacity * (0.4 + 0.6 * P) - e), 0.0, 1.0)

            # -------------------------------------------------------- market --
            t12 = max(0, len(R12) - 13)
            g_est = np.clip(R / np.maximum(R12[t12], 1e-9) - 1.0, -0.3, 1.0) if t >= 11 else np.tile(self.g0, (N, 1))
            run_rate = op_earn - comp_m - premium - liab[idx] / 12.0           # one offs (fines, realised liability, moves) excluded
            FE = 12.0 * run_rate * (1 + g_est)
            k = 0.05 * R
            V = self.ps[None, :] * R + self.pe[None, :] * k * np.log1p(np.exp(np.clip(FE / k, -30, 30)))   # smooth floor at the revenue multiple
            if V0 is None:
                V0 = V.copy(); cap0 = V0[0].copy()
            exposure = self.scope_share[None, :] * sector_in[None, :]
            ann = 0.0
            if t == 0:
                exp_cost = (pol["fixed_cost"] + pol["variable_cost"] * R * self.scope_share[None, :]) * sector_in[None, :]
                exp_liab = pol["liability_multiplier"] * 0.3 * sector_in[None, :]
                ann = -a["announcement_impact"] * (exp_cost + exp_liab) / np.maximum(12.0 * earnings, 0.05 * R) * 0.5
                ann = np.clip(ann, -0.25, 0.0)
            own_jump = -a["incident_jump"] * 0.05 * np.log1p((harm_f + liab_paid + fine + reloc_cost_m) / np.maximum(R / 12.0, 1e-6))
            sector_jump = np.zeros((N, F))
            for s in set(self.sector):
                m = np.array([x == s for x in self.sector])
                sj = (own_jump * m[None, :]).sum(axis=1, keepdims=True) - own_jump * m[None, :]
                sector_jump += a["contagion"] * sj * m[None, :] / max(1, m.sum() - 1)
            xi = (a["sentiment_persistence"] * xi + self.beta[None, :] * a["market_vol"] * rb.z_market[:, t][:, None]
                  + 0.01 * exposure * rb.z_policy[:, t][:, None] - a["news_price_impact"] * P[:, None] * (0.3 + exposure)
                  + own_jump + sector_jump + ann + self.ivol[None, :] * rb.z_idio[:, t])
            px = 100.0 * V / V0 * np.exp(xi)
            prices[:, t + 1, :] = px

            # ------------------------------------------------------- record --
            out["revenue"][:, t] = R; out["earnings"][:, t] = earnings; out["op_earnings"][:, t] = op_earn
            out["compliance"][:, t] = comp_m
            out["fines"][:, t] = fine; out["liability"][:, t] = liab_paid; out["premium"][:, t] = premium
            out["safety"][:, t] = S; out["capability"][:, t] = C; out["cap_eff"][:, t] = Ceff; out["reach"][:, t] = D
            out["offshore"][:, t] = O; out["comply"][:, t] = chi_c; out["sigma"][:, t] = sigma_reported
            out["harm"][:, t] = harm_f; out["cat_harm"][:, t] = cat_harm; out["relocation"][:, t] = reloc_cost_m
            out["incidents"][:, t] = inc; out["harm_cat"][:, t] = harm_k; out["catastrophe"][:, t] = cat
            out["audited"][:, t] = audited; out["fined"][:, t] = fined
            Q = (w0[None, :] * Ceff * D).sum(axis=1) / Q0
            series["enforcement"][:, t] = e; series["pressure"][:, t] = P; series["trust"][:, t] = T
            series["service"][:, t] = Q; series["tone"][:, t] = tone; series["salience"][:, t] = neg + pos
            news_counts[:, t] = np.stack([n_minor, n_major, n_cat, n_enf, n_rel, n_mile], axis=1)

            # events on the representative path
            ev = self._events(t, pol, active, active_prev, mora, inc[0], harm_k[0], cat[0], cat_harm[0], fined[0], fine[0],
                              O[0], Ceff[0], dlogC[0], S[0], T[0], P[0], Q[0], px[0], prices[0, t], delay[0],
                              in_scope_pf[0], chi_c[0], first)
            events0.append(ev)
            active_prev = active
            if stream is not None:
                stream(t, {"prices": px[0].tolist(), "events": ev, "pressure": float(P[0]), "trust": float(T[0]),
                           "enforcement": float(e[0]), "service": float(Q[0])})

        cap_end = cap0[None, :] * prices[:, -1, :] / 100.0
        return PolicyResult(policy=pol, prices=prices, cap0=cap0, cap_end=cap_end, series=series, news_counts=news_counts,
                            events0=events0, labels=self.labels, sectors=self.sector, horizon=H, n_paths=N, **out)

    # --------------------------------------------------------------- events --
    def _events(self, t, pol, active, active_prev, mora, inc, harm_k, cat, cat_harm, fined, fine, O_now, Ceff, dlogC, S, T, P, Q,
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
                               "major": bool(harm_k[f, k] >= self.a["major_incident_bn"])})
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
