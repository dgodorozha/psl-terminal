"""Run registry: one directory per run, never overwritten.

runs/<run_id>/
  ledger.jsonl     signed hash chain (append only)
  battery.json     the approved battery with its hash
  rows.json        per scenario evaluation rows (rewritten as scenarios complete)
  net.json         correlation network frames for the NET panel
  tapes.json       per scenario price paths and markers
  three.json       three worlds paths
  artefacts.json   every computed metric (single source of truth for the briefing)
  aut.json         autonomy gate detail
  critic.json      the critic's report
  approvals.json   who approved or refused what, when, and why
  briefing.md/html the released briefing
  meta.json        registry entry
  evidence_pack.zip
"""

import datetime
import json
import os

from psl.evidence import build_pack
from psl.ledger import NumpyEncoder

SERVABLE = {"artefacts.json", "results.json", "assurance.json", "battery.json", "plan.json", "assumptions.json",
            "news_sample.json", "prices_sample.json", "paths.json", "critic.json", "approvals.json", "meta.json",
            "briefing.md", "briefing.html", "ledger.jsonl", "evidence_pack.zip",
            "atrs_record.md", "atrs_record.json"}


def utc_now(spec="seconds"):
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec=spec)


class RunStore:
    def __init__(self, root):
        self.root = os.path.abspath(root)
        os.makedirs(self.root, exist_ok=True)

    def path(self, run_id, name=None):
        d = os.path.join(self.root, run_id)
        return os.path.join(d, name) if name else d

    def create(self, run_id):
        os.makedirs(self.path(run_id), exist_ok=True)
        return self.path(run_id)

    def write_json(self, run_id, name, obj):
        tmp = self.path(run_id, name + ".tmp")
        with open(tmp, "w") as f:
            json.dump(obj, f, indent=1, cls=NumpyEncoder)
        os.replace(tmp, self.path(run_id, name))

    def write_text(self, run_id, name, text):
        tmp = self.path(run_id, name + ".tmp")
        with open(tmp, "w") as f:
            f.write(text)
        os.replace(tmp, self.path(run_id, name))

    def read_json(self, run_id, name, default=None):
        p = self.path(run_id, name)
        if not os.path.isfile(p):
            return default
        with open(p) as f:
            return json.load(f)

    def update_meta(self, run_id, **kw):
        meta = self.read_json(run_id, "meta.json", {}) or {}
        meta.update(kw)
        meta.setdefault("run_id", run_id)
        meta["updated"] = utc_now()
        self.write_json(run_id, "meta.json", meta)
        return meta

    def pack(self, run_id):
        return build_pack(self.path(run_id))

    def index(self, limit=200):
        out = []
        if not os.path.isdir(self.root):
            return out
        for name in sorted(os.listdir(self.root), reverse=True):
            meta = self.read_json(name, "meta.json")
            if meta:
                out.append(meta)
            if len(out) >= limit:
                break
        return out

    def exists(self, run_id):
        return os.path.isdir(self.path(run_id))
