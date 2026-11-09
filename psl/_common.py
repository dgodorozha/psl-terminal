"""Helpers shared by the sentinel modules."""

import numpy as np


def _rolling_vol(returns, w=25):
    T = len(returns)
    out = np.zeros(T)
    for t in range(T):
        seg = returns[max(0, t - w):t + 1]
        out[t] = seg.std() if len(seg) > 2 else 0.0
    return out


def _online_matrix(T, n, events):
    """events: list of (t, members). Row t of the result holds the members
    of the latest event at or before t."""
    M = np.zeros((T, n), dtype=bool)
    if not events:
        return M
    events = sorted(events, key=lambda e: e[0])
    for k, (t, members) in enumerate(events):
        t_next = events[k + 1][0] if k + 1 < len(events) else T
        if members is not None and t_next > t:
            M[t:t_next, members] = True
    return M


import re as _re

_ACRONYMS = {"rl": "RL", "llm": "LLM", "luld": "LULD", "es": "ES", "hhi": "HHI", "smf": "SMF", "ai": "AI",
             "us": "US", "eu": "EU", "uk": "UK", "f1": "F1", "id": "ID", "csv": "CSV", "json": "JSON",
             "sqrt": "square root", "dd": "drawdown", "mm": "market maker"}
_IDENT = _re.compile(r"^[A-Za-z][A-Za-z0-9]*(?:_[A-Za-z0-9]+)+$")


def nice_name(s):
    """Regulator facing form of an identifier: underscores to spaces,
    sentence case, known acronyms upper case. Hashes, numbers and text
    that is not an identifier are returned unchanged."""
    if not isinstance(s, str) or not _IDENT.match(s):
        return s
    words = s.split("_")
    out = []
    for i, w in enumerate(words):
        lw = w.lower()
        if lw in _ACRONYMS:
            out.append(_ACRONYMS[lw])
        elif w.isupper() and len(w) == 1:          # vendor_A -> Vendor A
            out.append(w)
        elif i == 0:
            out.append(w[:1].upper() + w[1:])
        else:
            out.append(w)
    return " ".join(out)
