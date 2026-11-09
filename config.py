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
  PSL_PROFILE       full | light | demo: Monte Carlo paths and assurance budgets (default full; demo runs in
                    about twenty seconds with the heavy stages reduced and declared in the provenance)
  PSL_PATHS         Monte Carlo paths per policy (overrides the profile)
  PSL_HORIZON       months simulated (overrides the profile; default 60)
  PSL_TICK_PACE     seconds per simulated month on the wire (default 0.05)
  PSL_ASK_RATE      ASK questions per identity per minute (default 20)
  PSL_UPLOAD_MAX_MB size limit for uploaded datasets (default 25)
  PSL_LLM_PROVIDER  off | anthropic | openai | azure | gemini | custom | local (default: anthropic if
                    ANTHROPIC_API_KEY is set, else off); a model only phrases, it never computes a number
  PSL_LLM           auto | off
  ANTHROPIC_API_KEY, PSL_MODEL, PSL_LLM_BASE, PSL_LLM_MODEL, PSL_LLM_KEY, PSL_LLM_PATH,
  PSL_LLM_API_VERSION, PSL_LLM_TEMPLATE, PSL_LLM_HEADERS, PSL_LLM_RESPONSE_PATH  as in the model layer
  PSL_EGRESS_ALLOWLIST  comma separated hosts a model call may reach (empty = only loopback endpoints)
  PSL_FRAME_ANCESTORS   origins allowed to embed the terminal in a frame (default: none but itself; a Hugging Face
                        Space sets "https://huggingface.co https://*.hf.space" so the Space page can show it)
"""

import os
import secrets
import warnings


def _bool(v, default):
    if v is None or v == "":
        return default
    return str(v).strip().lower() in ("1", "true", "yes", "on")


PROFILES = {
    # paths per policy, months, bootstrap resamples, paths for the structural variants and the tornado's re simulations,
    # paths for the red team (the same as the main run, so its honest values match the headline figures)
    "full": {"paths": 240, "horizon": 60, "boot": 400, "variant_paths": 120, "redteam_paths": 240, "tornado": True},
    "light": {"paths": 120, "horizon": 60, "boot": 200, "variant_paths": 80, "redteam_paths": 120, "tornado": True},
    "demo": {"paths": 60, "horizon": 36, "boot": 100, "variant_paths": 30, "redteam_paths": 60, "tornado": True},
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
        self.profile = env.get("PSL_PROFILE", "full").strip().lower()
        if self.profile not in PROFILES:
            raise ValueError("PSL_PROFILE must be full, light or demo")
        prof = dict(PROFILES[self.profile])
        if env.get("PSL_PATHS"):
            prof["paths"] = max(8, int(env["PSL_PATHS"]))
            prof["redteam_paths"] = prof["paths"]
        if env.get("PSL_HORIZON"):
            prof["horizon"] = max(12, min(120, int(env["PSL_HORIZON"])))
        self.budget = prof
        self.tick_pace = float(env.get("PSL_TICK_PACE", "0.05"))
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
                "register": bool(self.register_path), "dev_mode": self.dev_mode,
                "llm_enabled": self.llm_enabled, "llm_provider": self.llm_provider if self.llm_enabled else "off",
                "profile": self.profile, "budget": self.budget, "frame_ancestors": self.frame_ancestors,
                "ledger_secret": "configured" if not self.ephemeral_secret else "ephemeral"}
