"""Model layer: three providers behind one interface, every path boxed by a
fixed server side prompt and verified by the critic afterwards.

Providers (PSL_LLM_PROVIDER):
  anthropic  the Anthropic Messages API, or a gateway that proxies it
             (PSL_API_BASE); key from ANTHROPIC_API_KEY.
  azure      Azure OpenAI Service, the platform behind Microsoft Copilot for
             enterprises: PSL_LLM_BASE is the resource endpoint, PSL_LLM_MODEL
             the deployment name, PSL_LLM_KEY the key.
  gemini     the Google Gemini API: PSL_LLM_MODEL and PSL_LLM_KEY.
  custom     any JSON API the authority runs, described without code by a
             request template, headers and a response path.
  openai     any OpenAI compatible chat completions endpoint: an
             institutional gateway, Azure style deployments behind such a
             gateway, or a local server (vLLM, llama.cpp, Ollama, LM Studio)
             on the loopback interface. PSL_LLM_BASE is the base URL ending
             in /v1, PSL_LLM_MODEL the model name, PSL_LLM_KEY the bearer
             token (optional for local servers).
  local      a model the authority has installed itself, loaded from a
             directory with the transformers library (PSL_LLM_PATH). The Lab
             never downloads a model; the authority obtains it through its
             own channel, places it on disk and installs `transformers` and
             `torch` in the environment. Generation runs in process.
  off        no model; every path is deterministic (the default).

Network rules for the API providers: https is required unless the host is
the loopback interface; when an egress allowlist is configured the model's
host must be on it; responses are capped at 4 MB and calls time out.
Keys come from the environment only and are never written anywhere. If no
provider is configured, or a call fails, every entry point falls back to
the deterministic path, so the pipeline always completes and no generated
text can alter a computed number.
"""

import json
import os
import re
import urllib.parse
import urllib.request

DEFAULT_BASE = "https://api.anthropic.com"
MODEL = os.environ.get("PSL_MODEL", "claude-sonnet-4-6")
MAX_QUESTION_CHARS = 600
RESPONSE_CAP = 4 * 1024 * 1024
LOOPBACK = ("127.0.0.1", "localhost", "::1")


def _host(url):
    return (urllib.parse.urlparse(url).hostname or "").lower()


def _check_endpoint(url, allowlist=None):
    """https unless loopback; host on the allowlist when one is configured."""
    host = _host(url)
    if not host:
        raise RuntimeError("model endpoint has no host")
    if host not in LOOPBACK and not url.startswith("https://"):
        raise RuntimeError("the model endpoint must be https unless it is on the loopback interface")
    allow = [a.lower() for a in (allowlist or []) if a]
    if allow and host not in LOOPBACK and host not in allow:
        raise RuntimeError(f"model host {host} is not on the egress allowlist")


def _post_json(url, body, headers, timeout, allowlist=None):
    _check_endpoint(url, allowlist)
    req = urllib.request.Request(url, data=json.dumps(body).encode(),
                                 headers=dict({"Content-Type": "application/json"}, **headers))
    with urllib.request.urlopen(req, timeout=timeout) as r:   # noqa: S310 - scheme and host checked above
        raw = r.read(RESPONSE_CAP + 1)
    if len(raw) > RESPONSE_CAP:
        raise RuntimeError("model response exceeds the size cap")
    return json.loads(raw)


class ModelClient:
    provider = "off"
    model = None
    available = False

    def complete(self, prompt, system=None, max_tokens=1200, timeout=45):
        raise RuntimeError("no model configured")

    def describe(self):
        d = {"provider": self.provider, "model": self.model, "available": bool(self.available)}
        if getattr(self, "_error", None):
            d["note"] = self._error
        return d


class AnthropicClient(ModelClient):
    provider = "anthropic"

    def __init__(self, api_key=None, base=None, model=None, enabled=None, allowlist=None):
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "").strip()
        self.base = (base or os.environ.get("PSL_API_BASE") or DEFAULT_BASE).rstrip("/")
        self.model = model or MODEL
        mode = (os.environ.get("PSL_LLM", "auto") if enabled is None else enabled).lower()
        self.enabled = mode not in ("off", "0", "false", "no")
        self.allowlist = allowlist

    @property
    def available(self):
        return bool(self.api_key) and self.enabled

    def complete(self, prompt, system=None, max_tokens=1200, timeout=45):
        body = {"model": self.model, "max_tokens": max_tokens,
                "messages": [{"role": "user", "content": prompt}]}
        if system:
            body["system"] = system
        data = _post_json(f"{self.base}/v1/messages", body,
                          {"anthropic-version": "2023-06-01", "x-api-key": self.api_key or ""},
                          timeout, self.allowlist)
        return "".join(b.get("text", "") for b in data.get("content", []) if b.get("type") == "text")


ClaudeClient = AnthropicClient      # name kept for existing call sites


class OpenAICompatibleClient(ModelClient):
    """Chat completions against any OpenAI compatible endpoint: institutional
    gateways and local servers alike."""
    provider = "openai"

    def __init__(self, base=None, model=None, api_key=None, enabled=True, allowlist=None):
        self.base = (base or os.environ.get("PSL_LLM_BASE", "")).rstrip("/")
        self.model = model or os.environ.get("PSL_LLM_MODEL", "")
        self.api_key = api_key if api_key is not None else os.environ.get("PSL_LLM_KEY", "").strip()
        self.enabled = enabled
        self.allowlist = allowlist

    @property
    def available(self):
        return bool(self.base and self.model) and self.enabled

    def complete(self, prompt, system=None, max_tokens=1200, timeout=60):
        msgs = ([{"role": "system", "content": system}] if system else []) + [{"role": "user", "content": prompt}]
        body = {"model": self.model, "messages": msgs, "max_tokens": max_tokens, "temperature": 0}
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        data = _post_json(f"{self.base}/chat/completions", body, headers, timeout, self.allowlist)
        choices = data.get("choices") or []
        if not choices:
            raise RuntimeError("model returned no choices")
        msg = choices[0].get("message") or {}
        content = msg.get("content")
        if isinstance(content, list):
            content = "".join(p.get("text", "") for p in content if isinstance(p, dict))
        return content or ""


class LocalTransformersClient(ModelClient):
    """A model the authority installed itself, loaded from disk with the
    transformers library. Nothing is downloaded: the path must already hold
    the model files. Loaded lazily on first use and kept in process."""
    provider = "local"

    def __init__(self, path=None, max_input_tokens=4096, enabled=True):
        self.path = path or os.environ.get("PSL_LLM_PATH", "")
        self.model = os.path.basename(self.path.rstrip("/")) if self.path else None
        self.enabled = enabled
        self.max_input_tokens = max_input_tokens
        self._pipe = None
        self._error = None

    @property
    def available(self):
        if not (self.enabled and self.path and os.path.isdir(self.path)):
            return False
        try:
            import transformers  # noqa: F401
            return True
        except ImportError:
            self._error = "transformers is not installed; pip install transformers torch"
            return False

    def _load(self):
        if self._pipe is None:
            from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
            tok = AutoTokenizer.from_pretrained(self.path, local_files_only=True)
            mdl = AutoModelForCausalLM.from_pretrained(self.path, local_files_only=True)
            self._pipe = pipeline("text-generation", model=mdl, tokenizer=tok)
        return self._pipe

    def complete(self, prompt, system=None, max_tokens=1200, timeout=None):
        pipe = self._load()
        tok = pipe.tokenizer
        text = prompt
        if getattr(tok, "chat_template", None):
            msgs = ([{"role": "system", "content": system}] if system else []) + [{"role": "user", "content": prompt}]
            text = tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
        elif system:
            text = system + "\n\n" + prompt
        out = pipe(text, max_new_tokens=max_tokens, do_sample=False, return_full_text=False,
                   truncation=True, max_length=self.max_input_tokens)
        return (out[0].get("generated_text") or "") if out else ""


class AzureOpenAIClient(ModelClient):
    """Azure OpenAI Service, the platform behind Microsoft Copilot for
    enterprises: a deployment on the authority's own Azure resource.
    PSL_LLM_BASE is the resource endpoint (https://<resource>.openai.azure.com),
    PSL_LLM_MODEL the deployment name, PSL_LLM_KEY the key (or a bearer
    token with PSL_LLM_AUTH=bearer), PSL_LLM_API_VERSION the API version."""
    provider = "azure"

    def __init__(self, base=None, model=None, api_key=None, api_version=None, auth=None, enabled=True,
                 allowlist=None):
        self.base = (base or os.environ.get("PSL_LLM_BASE", "")).rstrip("/")
        self.model = model or os.environ.get("PSL_LLM_MODEL", "")
        self.api_key = api_key if api_key is not None else os.environ.get("PSL_LLM_KEY", "").strip()
        self.api_version = api_version or os.environ.get("PSL_LLM_API_VERSION", "2024-10-21")
        self.auth = (auth or os.environ.get("PSL_LLM_AUTH", "key")).lower()
        self.enabled = enabled
        self.allowlist = allowlist

    @property
    def available(self):
        return bool(self.base and self.model and self.api_key) and self.enabled

    def complete(self, prompt, system=None, max_tokens=1200, timeout=60):
        msgs = ([{"role": "system", "content": system}] if system else []) + [{"role": "user", "content": prompt}]
        body = {"messages": msgs, "max_tokens": max_tokens, "temperature": 0}
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.auth == "bearer" else {"api-key": self.api_key}
        url = f"{self.base}/openai/deployments/{urllib.parse.quote(self.model)}/chat/completions?api-version={self.api_version}"
        data = _post_json(url, body, headers, timeout, self.allowlist)
        choices = data.get("choices") or []
        if not choices:
            raise RuntimeError("model returned no choices")
        content = (choices[0].get("message") or {}).get("content")
        if isinstance(content, list):
            content = "".join(p.get("text", "") for p in content if isinstance(p, dict))
        return content or ""


class GeminiClient(ModelClient):
    """Google Gemini API (generateContent). PSL_LLM_MODEL is the model name,
    PSL_LLM_KEY the API key; PSL_LLM_BASE may point at a gateway."""
    provider = "gemini"
    DEFAULT = "https://generativelanguage.googleapis.com"

    def __init__(self, base=None, model=None, api_key=None, enabled=True, allowlist=None):
        self.base = (base or os.environ.get("PSL_LLM_BASE") or self.DEFAULT).rstrip("/")
        self.model = model or os.environ.get("PSL_LLM_MODEL", "")
        self.api_key = api_key if api_key is not None else os.environ.get("PSL_LLM_KEY", "").strip()
        self.enabled = enabled
        self.allowlist = allowlist

    @property
    def available(self):
        return bool(self.model and self.api_key) and self.enabled

    def complete(self, prompt, system=None, max_tokens=1200, timeout=60):
        body = {"contents": [{"role": "user", "parts": [{"text": prompt}]}],
                "generationConfig": {"maxOutputTokens": max_tokens, "temperature": 0}}
        if system:
            body["systemInstruction"] = {"parts": [{"text": system}]}
        url = f"{self.base}/v1beta/models/{urllib.parse.quote(self.model)}:generateContent"
        data = _post_json(url, body, {"x-goog-api-key": self.api_key}, timeout, self.allowlist)
        cands = data.get("candidates") or []
        if not cands:
            raise RuntimeError("model returned no candidates")
        parts = ((cands[0].get("content") or {}).get("parts")) or []
        return "".join(p.get("text", "") for p in parts if isinstance(p, dict))


def _dig(data, path):
    """Walk a dotted path with integer indices: choices.0.message.content."""
    cur = data
    for key in path.split("."):
        if isinstance(cur, list):
            cur = cur[int(key)]
        else:
            cur = cur[key]
    return cur


class CustomTemplateClient(ModelClient):
    """Any JSON API the authority runs, described without code: a request
    body template with {prompt}, {system}, {model} and {max_tokens}
    placeholders (PSL_LLM_TEMPLATE), a JSON object of headers where
    ${PSL_LLM_KEY} is substituted (PSL_LLM_HEADERS), the full endpoint URL
    (PSL_LLM_BASE) and the dotted path of the reply text in the response
    (PSL_LLM_RESPONSE_PATH, for example choices.0.message.content)."""
    provider = "custom"

    def __init__(self, base=None, model=None, template=None, headers=None, response_path=None, api_key=None,
                 enabled=True, allowlist=None):
        self.base = (base or os.environ.get("PSL_LLM_BASE", "")).strip()
        self.model = model or os.environ.get("PSL_LLM_MODEL", "custom")
        self.template = template or os.environ.get("PSL_LLM_TEMPLATE", "")
        self.headers_json = headers or os.environ.get("PSL_LLM_HEADERS", "{}")
        self.response_path = response_path or os.environ.get("PSL_LLM_RESPONSE_PATH", "")
        self.api_key = api_key if api_key is not None else os.environ.get("PSL_LLM_KEY", "").strip()
        self.enabled = enabled
        self.allowlist = allowlist

    @property
    def available(self):
        return bool(self.base and self.template and self.response_path) and self.enabled

    def complete(self, prompt, system=None, max_tokens=1200, timeout=60):
        def esc(s):
            return json.dumps(str(s))[1:-1]
        text = (self.template.replace("{prompt}", esc(prompt)).replace("{system}", esc(system or ""))
                .replace("{model}", esc(self.model)).replace("{max_tokens}", str(int(max_tokens))))
        body = json.loads(text)
        headers = {k: str(v).replace("${PSL_LLM_KEY}", self.api_key) for k, v in json.loads(self.headers_json).items()}
        data = _post_json(self.base, body, headers, timeout, self.allowlist)
        out = _dig(data, self.response_path)
        return out if isinstance(out, str) else json.dumps(out)


PROVIDERS = {
    "off": "no model; every path deterministic",
    "anthropic": "Anthropic Messages API or a gateway that proxies it",
    "openai": "any OpenAI compatible chat completions endpoint: institutional gateways, Mistral, Groq, Together, "
              "Bedrock's OpenAI compatible endpoint, Azure AI Foundry inference, vLLM, llama.cpp, Ollama, LM Studio",
    "azure": "Azure OpenAI Service, the platform behind Microsoft Copilot for enterprises",
    "gemini": "Google Gemini API",
    "custom": "any JSON API described by a request template and a response path",
    "local": "a model installed by the authority, loaded from disk with transformers",
}


def make_client(cfg=None):
    """The configured client. `cfg` is the Config (or None to read the
    environment); provider off returns a client that is never available."""
    env = os.environ
    provider = (getattr(cfg, "llm_provider", None) or env.get("PSL_LLM_PROVIDER") or "").strip().lower()
    allow = getattr(cfg, "egress_allowlist", None) or None
    if not provider:
        # backwards compatible default: anthropic when a key is present, else off
        provider = "anthropic" if env.get("ANTHROPIC_API_KEY", "").strip() else "off"
    if provider == "anthropic":
        return AnthropicClient(api_key=getattr(cfg, "api_key", None), model=getattr(cfg, "model", None),
                               enabled=getattr(cfg, "llm_mode", None), allowlist=allow)
    if provider == "openai":
        return OpenAICompatibleClient(base=getattr(cfg, "llm_base", None), model=getattr(cfg, "llm_model", None),
                                      allowlist=allow)
    if provider == "azure":
        return AzureOpenAIClient(base=getattr(cfg, "llm_base", None), model=getattr(cfg, "llm_model", None),
                                 allowlist=allow)
    if provider == "gemini":
        return GeminiClient(base=getattr(cfg, "llm_base", None) or None, model=getattr(cfg, "llm_model", None),
                            allowlist=allow)
    if provider == "custom":
        return CustomTemplateClient(base=getattr(cfg, "llm_base", None), model=getattr(cfg, "llm_model", None),
                                    allowlist=allow)
    if provider == "local":
        return LocalTransformersClient(path=getattr(cfg, "llm_path", None))
    return ModelClient()


# ---------- model assisted reading of the question ----------

PLAN_SYSTEM = ("You translate an AI regulation policy question into the structured plan of a policy simulation. "
               "Respond ONLY with JSON, no preamble and no markdown fences.")

PLAN_PROMPT = """Policy question: {q}

Instruments available: {names}

Respond with ONE JSON object:
{{"policies": [instrument names from the list, 2 to 10, never "baseline"],
  "horizon_years": 1 to 10 or null,
  "constraints": {{"max_industry_loss_bn": number or null, "max_social_cost_bn": number or null,
                   "max_p_major": 0 to 1 or null, "max_p_catastrophe": 0 to 1 or null,
                   "min_harm_reduction_pct": number or null, "max_cs_loss_pct": number or null}},
  "rationale": one sentence}}
Name only instruments the question asks about or plainly implies; if it names none, return the empty list."""


def plan_llm(question, client, log):
    """Ask the configured model to read the question; the result is merged into the deterministic reading and
    every value is validated by the caller. Returns a dict or None."""
    from .policies import LIBRARY
    if not client.available:
        return None
    try:
        raw = client.complete(PLAN_PROMPT.format(q=question[:MAX_QUESTION_CHARS], names=", ".join(n for n in LIBRARY if n != "baseline")),
                              system=PLAN_SYSTEM, max_tokens=600)
        m = re.search(r"\{.*\}", raw, re.S)
        data = json.loads(m.group(0) if m else raw)
        pols = [p for p in data.get("policies", []) if p in LIBRARY and p != "baseline"]
        cons = {}
        for k, (lo, hi) in (("max_industry_loss_bn", (0, 1e5)), ("max_social_cost_bn", (0, 1e5)), ("max_p_major", (0, 1)),
                            ("max_p_catastrophe", (0, 1)), ("min_harm_reduction_pct", (0, 100)), ("max_cs_loss_pct", (0, 100))):
            v = (data.get("constraints") or {}).get(k)
            if isinstance(v, (int, float)) and lo <= v <= hi:
                cons[k] = float(v)
        hy = data.get("horizon_years")
        out = {"policies": pols, "constraints": cons,
               "horizon_months": int(hy) * 12 if isinstance(hy, (int, float)) and 1 <= hy <= 10 else None,
               "rationale": str(data.get("rationale", ""))[:200]}
        log("llm_plan", provider=client.provider, model=client.model, accepted=out)
        return out
    except Exception as e:  # noqa: BLE001
        log("llm_plan_failed", error=str(e)[:200])
        return None


def draft_briefing_llm(artefacts, client, deterministic_text, log):
    """Rewrite the prose of the deterministic briefing with the configured model, keeping every table; the
    result is accepted only if every number in it appears in the artefacts (the critic's vetting).
    Returns (text, used_llm). Any failure returns the deterministic text."""
    from .critic import _vet_numbers
    if not client.available:
        log("llm_draft_skipped", reason="no model configured; deterministic briefing")
        return deterministic_text, False
    try:
        prompt = ("Below is a regulatory impact briefing drafted deterministically from a simulation's artefacts. Rewrite the "
                  "prose paragraphs so that they read as a senior policy adviser would write them, in British English, direct "
                  "and plain. Keep every heading and every table exactly as they are. Do not add, change or round any number; "
                  "do not add claims that are not in the text.\n\n" + deterministic_text[:80000])
        text = client.complete(prompt, system="You are an experienced regulatory economist writing for a decision maker. "
                               "Never invent or alter a figure.", max_tokens=6000, timeout=120)
        bad = _vet_numbers(text, artefacts)
        if bad:
            log("llm_draft_rejected", reason="numbers not in the artefacts", examples=bad[:8])
            return deterministic_text, False
        if text.count("|") < deterministic_text.count("|") * 0.9:
            log("llm_draft_rejected", reason="tables altered")
            return deterministic_text, False
        log("llm_draft_accepted", provider=client.provider, model=client.model, n_chars=len(text))
        return text, True
    except Exception as e:  # noqa: BLE001
        log("llm_draft_failed", error=str(e)[:200])
        return deterministic_text, False


ASK_SYSTEM = ("You phrase answers about a policy simulation run for a senior official. Use only the context and the "
              "deterministic answer; keep every number exactly as given; cite sources as [S1], [S2]; British English; "
              "at most 160 words; never speculate beyond the artefacts.")


def ask_llm(question, sources, deterministic_text, client, log):
    """Phrase an answer from the retrieved sources and the deterministic
    answer. The client only ever supplied the question."""
    if not client.available:
        return None
    q = question[:MAX_QUESTION_CHARS]
    ctx = "\n".join(f"[S{i + 1}] {c['title']}: {c['text']}" for i, c in enumerate(sources))
    prompt = (f"CONTEXT:\n{ctx}\n\nDETERMINISTIC ANSWER (computed from the artefacts):\n"
              f"{deterministic_text}\n\nQUESTION: {q}")
    try:
        text = client.complete(prompt, system=ASK_SYSTEM, max_tokens=700)
        log("ask_llm", model=client.model, sources=[c["id"] for c in sources],
            n_chars=len(text))
        return text
    except Exception as e:  # noqa: BLE001
        log("ask_llm_failed", error=str(e)[:200])
        return None
