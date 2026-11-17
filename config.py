"""Server configuration for the Policy Scenario Lab, read once from the environment.

Every setting has a safe default: the server binds to localhost, every
ledger is signed (with an ephemeral secret and a loud warning if none is
configured), approvals are open to any named person in open mode and
restricted to identities from a trusted proxy header in header mode.

  PSL_HOST          bind address (default 127.0.0.1; use 0.0.0.0 only behind a proxy)
  PSL_PORT          port (default 8070)
  PSL_RUNS_DIR      directory for run folders (default ./runs)
  PSL_SECRET        HMAC key for ledger signatures (set this in production)
  PSL_AUTH_MODE     open | header  (header: identity comes from a trusted proxy header)
  PSL_USER_HEADER   header carrying the SSO identity (default X-Remote-User)
  PSL_ROLE_HEADER   header carrying the caller's role in header auth mode (default X-PSL-Role)
  PSL_APPROVERS     comma separated identities allowed to approve gates (empty = any)
  PSL_FOUR_EYES     1/0: approver must differ from preparer (default 1)
  PSL_REGISTER      path to the register of regulated or authorised persons approvers are checked against
  PSL_REGISTER_REQUIRED  on: an approver not on the register cannot approve (default: on when a register is set)
  PSL_DEV_MODE      on: Developer1 and Developer2 are accepted as preparer and approver (and as their
                    functions) without a register entry; every gate records dev mode; never for production
  PSL_GATES         named | open (default named): named takes a preparer and an approver with their functions,
                    checked against the register with four eyes; open makes the two gates single clicks with no
                    identities, for a public demonstration; every gate record and the posture page say which
  PSL_PROFILE       full | light | demo: the sampling plan (starting paths, ceiling, precision targets) and the
                    assurance budgets (default full; demo runs in about half a minute with the heavy stages reduced, which
                    the provenance declares)
  PSL_PATHS         Monte Carlo paths per policy the battery starts on (overrides the profile)
  PSL_MAX_PATHS     ceiling the adaptive sampling may grow the battery to (overrides the profile; set it equal to
                    PSL_PATHS for a fixed number of paths)
  PSL_WORKERS       threads for independent simulations (default: the machine's cores, at most four)
  PSL_SEED          seed of the random streams when the question names none (default 7); "seed 11" in a question
                    repeats the run on another family of streams, an independent replication
  PSL_HORIZON       months simulated (overrides the profile; default 60)
  PSL_TICK_PACE     seconds per simulated month on the wire (default 0.05)
  PSL_BENCHMARKS    JSON file of empirical benchmarks for the validation layer, replacing or extending the built in
                    evidence base (psl/benchmarks.py gives the fields); the set in force is hashed into the battery
  PSL_IDLE_SECONDS  seconds without a key, click, scroll or pointer movement after which an open page stops polling the
                    server unless a run is in progress (default 90; a host that stops the process as soon as the
                    page is quiet wants a longer window, a host with its own idle window a short one)
  PSL_REUSE         on: a battery identical to a completed run (same hash, code, libraries and uploaded series) is not
                    simulated again; its figures are copied, its stream replayed and the critic recomputes them
                    (default off; the public demonstration switches it on)
  PSL_ASK_RATE      ASK questions per identity per minute (default 20)
  PSL_UPLOAD_MAX_MB size limit for uploaded datasets (default 25)
  PSL_LLM_PROVIDER  off | anthropic | openai | azure | gemini | custom | local (default: anthropic if
                    ANTHROPIC_API_KEY is set, else off); a model only phrases, it never computes a number
  PSL_LLM           auto | off
  ANTHROPIC_API_KEY, PSL_MODEL, PSL_LLM_BASE, PSL_LLM_MODEL, PSL_LLM_KEY, PSL_LLM_PATH,
  PSL_LLM_API_VERSION, PSL_LLM_TEMPLATE, PSL_LLM_HEADERS, PSL_LLM_RESPONSE_PATH  as in the model layer
  PSL_EGRESS_ALLOWLIST  comma separated hosts a model call may reach (empty = only loopback endpoints)
  PSL_FRAME_ANCESTORS   origins allowed to embed the terminal in a frame (default: none but itself; app.py sets
                        "https://connect.posit.cloud" so that Posit Connect Cloud's own page can show it, and a
                        Hugging Face Space sets "https://huggingface.co https://*.hf.space")
"""

import math
import os
import secrets
import warnings


def _bool(v, default):
    if v is None or v == "":
        return default
    return str(v).strip().lower() in ("1", "true", "yes", "on")


def available_cores(cgroup="/sys/fs/cgroup"):
    """Processor cores this process may use: the machine's, fewer where the process is pinned, and fewer again
    where a container sets a quota (a host that sells one processor still shows the whole machine to os.cpu_count)."""
    n = os.cpu_count() or 1
    try:
        n = min(n, len(os.sched_getaffinity(0)))
    except (AttributeError, OSError):
        pass
    quota = None
    try:
        with open(os.path.join(cgroup, "cpu.max")) as f:                      # cgroup v2: "<quota> <period>" or "max <period>"
            q, period = f.read().split()[:2]
        if q != "max":
            quota = int(q) / int(period)
    except (OSError, ValueError, ZeroDivisionError):
        try:
            with open(os.path.join(cgroup, "cpu", "cpu.cfs_quota_us")) as f:  # cgroup v1: a quota of -1 is none
                q = int(f.read())
            with open(os.path.join(cgroup, "cpu", "cpu.cfs_period_us")) as f:
                period = int(f.read())
            if q > 0 and period > 0:
                quota = q / period
        except (OSError, ValueError):
            pass
    if quota is not None and quota > 0:
        n = min(n, max(1, math.ceil(quota)))
    return max(1, n)


PROFILES = {
    # The sampling plan and the assurance budget of a run.
    #   paths, max_paths     the battery starts on `paths` paths per policy and doubles, on the same random streams, until
    #                        the precision targets are met or `max_paths` is reached
    #   precision            nsv_gap_bn: the preferred alternative is resolved against another feasible one when the 95%
    #                        interval of their paired difference excludes zero or its half width is at most this ($bn);
    #                        p_catastrophe_halfwidth: the half width of the interval of a catastrophe probability
    #   boot                 bootstrap resamples of the paths
    #   screen_paths         paths each assumption's re simulation runs on in the screen (paired with the main run)
    #   joint_draws, joint_paths   joint draws of all the assumptions, and the paths each runs on
    #   sobol_k, sobol_base, sobol_paths   assumptions in the variance decomposition, its base sample, paths per evaluation
    #   variant_paths, redteam_paths       paths for the structural variants and for the red team
    #   batches              independent batches the run's paths are split into for the replication check
    "full": {"paths": 480, "max_paths": 3840, "horizon": 60, "boot": 1000,
             "precision": {"nsv_gap_bn": 2.5, "p_catastrophe_halfwidth": 0.01},
             "screen_paths": 32, "joint_draws": 256, "joint_paths": 8, "sobol_k": 8, "sobol_base": 256, "sobol_paths": 4,
             "variant_paths": 240, "redteam_paths": 240, "batches": 8, "tornado": True},
    "light": {"paths": 240, "max_paths": 960, "horizon": 60, "boot": 1000,
              "precision": {"nsv_gap_bn": 5.0, "p_catastrophe_halfwidth": 0.02},
              "screen_paths": 12, "joint_draws": 128, "joint_paths": 6, "sobol_k": 6, "sobol_base": 128, "sobol_paths": 3,
              "variant_paths": 96, "redteam_paths": 120, "batches": 4, "tornado": True},
    "demo": {"paths": 120, "max_paths": 480, "horizon": 36, "boot": 500,
             "precision": {"nsv_gap_bn": 5.0, "p_catastrophe_halfwidth": 0.03},
             "screen_paths": 4, "joint_draws": 64, "joint_paths": 4, "sobol_k": 5, "sobol_base": 64, "sobol_paths": 2,
             "variant_paths": 40, "redteam_paths": 60, "batches": 4, "tornado": True},
}


class Config:
    def __init__(self, env=None):
        env = os.environ if env is None else env
        self.host = env.get("PSL_HOST", "127.0.0.1")
        self.port = int(env.get("PSL_PORT", "8070"))
        self.runs_dir = env.get("PSL_RUNS_DIR", "runs")
        self.secret = env.get("PSL_SECRET") or None
        self.ephemeral_secret = self.secret is None
        if self.ephemeral_secret:
            self.secret = secrets.token_hex(32)
            warnings.warn("PSL_SECRET is not set: ledgers are signed with an ephemeral key "
                          "that will not survive a restart. Set PSL_SECRET in production.")
        self.auth_mode = env.get("PSL_AUTH_MODE", "open").strip().lower()
        if self.auth_mode not in ("open", "header"):
            raise ValueError("PSL_AUTH_MODE must be 'open' or 'header'")
        self.user_header = env.get("PSL_USER_HEADER", "X-Remote-User")
        self.role_header = env.get("PSL_ROLE_HEADER", "X-PSL-Role")
        self.approvers = {x.strip().lower() for x in env.get("PSL_APPROVERS", "").split(",") if x.strip()}
        self.four_eyes = _bool(env.get("PSL_FOUR_EYES"), True)
        self.register_path = env.get("PSL_REGISTER", "").strip()
        self.register_required = _bool(env.get("PSL_REGISTER_REQUIRED"), bool(self.register_path))
        self.dev_mode = _bool(env.get("PSL_DEV_MODE"), False)
        self.gates = (env.get("PSL_GATES", "named").strip().lower() or "named")
        if self.gates not in ("named", "open"):
            raise ValueError("PSL_GATES must be named or open")
        self.profile = env.get("PSL_PROFILE", "full").strip().lower()
        if self.profile not in PROFILES:
            raise ValueError("PSL_PROFILE must be full, light or demo")
        prof = dict(PROFILES[self.profile])
        if env.get("PSL_PATHS"):
            prof["paths"] = max(8, int(env["PSL_PATHS"]))
            prof["max_paths"] = max(prof["paths"], int(prof.get("max_paths", prof["paths"])))
            prof["redteam_paths"] = min(prof["paths"], int(prof.get("redteam_paths", prof["paths"])))
            prof["variant_paths"] = min(prof["paths"], int(prof.get("variant_paths", prof["paths"])))
        if env.get("PSL_MAX_PATHS"):
            prof["max_paths"] = max(prof["paths"], int(env["PSL_MAX_PATHS"]))
        if env.get("PSL_HORIZON"):
            prof["horizon"] = max(12, min(120, int(env["PSL_HORIZON"])))
        self.budget = prof
        self.seed = int(env.get("PSL_SEED", "7"))
        self.tick_pace = float(env.get("PSL_TICK_PACE", "0.05"))
        self.reuse = _bool(env.get("PSL_REUSE"), False)
        self.idle_seconds = max(10.0, float(env.get("PSL_IDLE_SECONDS", "90")))
        self.benchmarks_path = env.get("PSL_BENCHMARKS", "").strip()
        self.ask_rate = int(env.get("PSL_ASK_RATE", "20"))
        self.upload_max_mb = int(env.get("PSL_UPLOAD_MAX_MB", "25"))
        self.llm_mode = env.get("PSL_LLM", "auto").strip().lower()
        self.api_key = env.get("ANTHROPIC_API_KEY", "").strip()
        self.model = env.get("PSL_MODEL", "claude-sonnet-4-6")
        self.llm_provider = env.get("PSL_LLM_PROVIDER", "").strip().lower() or ("anthropic" if self.api_key else "off")
        if self.llm_provider not in ("off", "anthropic", "openai", "azure", "gemini", "custom", "local"):
            raise ValueError("PSL_LLM_PROVIDER must be off, anthropic, openai, azure, gemini, custom or local")
        self.llm_base = env.get("PSL_LLM_BASE", "").strip()
        self.llm_model = env.get("PSL_LLM_MODEL", "").strip()
        self.llm_path = env.get("PSL_LLM_PATH", "").strip()
        self.egress_allowlist = [h.strip() for h in env.get("PSL_EGRESS_ALLOWLIST", "").split(",") if h.strip()]
        self.frame_ancestors = [h.strip() for h in env.get("PSL_FRAME_ANCESTORS", "").split() if h.strip()]
        self.connectors = False          # the sandbox is air gapped: data arrives by upload only

    @property
    def llm_enabled(self):
        if self.llm_mode in ("off", "0", "false", "no"):
            return False
        if self.llm_provider == "anthropic":
            return bool(self.api_key)
        if self.llm_provider == "openai":
            return bool(self.llm_base and self.llm_model)
        if self.llm_provider == "azure":
            return bool(self.llm_base and self.llm_model and os.environ.get("PSL_LLM_KEY"))
        if self.llm_provider == "gemini":
            return bool(self.llm_model and os.environ.get("PSL_LLM_KEY"))
        if self.llm_provider == "custom":
            return bool(self.llm_base and os.environ.get("PSL_LLM_TEMPLATE") and os.environ.get("PSL_LLM_RESPONSE_PATH"))
        if self.llm_provider == "local":
            return bool(self.llm_path)
        return False

    def public(self):
        """Non secret view for /version and the front page."""
        return {"host": self.host, "port": self.port, "runs_dir": self.runs_dir,
                "auth_mode": self.auth_mode, "user_header": self.user_header,
                "approvers_restricted": bool(self.approvers), "four_eyes": self.four_eyes,
                "register": bool(self.register_path), "dev_mode": self.dev_mode, "gates": self.gates,
                "llm_enabled": self.llm_enabled, "llm_provider": self.llm_provider if self.llm_enabled else "off",
                "profile": self.profile, "budget": self.budget, "seed": self.seed, "frame_ancestors": self.frame_ancestors,
                "ledger_secret": "configured" if not self.ephemeral_secret else "ephemeral"}
