"""Running independent simulations side by side.

A policy run is a long sequence of numpy operations on large arrays, during which the interpreter lock is
released, so two runs on two cores take a little over half the time of two in sequence. Each run owns its state
and only reads the shared random numbers, and no random number generator is shared, so the results are identical
whatever the scheduling. PSL_WORKERS sets the number of threads (default: the machine's cores, at most four).
"""

import os
from concurrent.futures import ThreadPoolExecutor


def workers():
    try:
        w = int(os.environ.get("PSL_WORKERS", "0"))
    except ValueError:
        w = 0
    return w if w > 0 else max(1, min(4, os.cpu_count() or 1))


def pmap(fn, items):
    """[fn(x) for x in items], in input order, on up to workers() threads."""
    items = list(items)
    w = min(workers(), len(items))
    if w <= 1:
        return [fn(x) for x in items]
    with ThreadPoolExecutor(w) as ex:
        return list(ex.map(fn, items))
