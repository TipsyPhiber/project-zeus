"""TTL cache for zero-arg data probes.

`@ttl_cache(seconds=N)` memoises the most recent return value of `fn`
for N seconds. Threadsafe. Per-function (does not key on arguments) —
intended for parameterless probes like `host_metrics.read()`.
"""
import threading
import time
from functools import wraps
from typing import Callable


def ttl_cache(seconds: float) -> Callable:
    def decorator(fn: Callable) -> Callable:
        state = {"data": None, "ts": 0.0, "valid": False}
        lock = threading.Lock()

        @wraps(fn)
        def wrapper(*args, **kwargs):
            with lock:
                now = time.monotonic()
                if state["valid"] and (now - state["ts"]) < seconds:
                    return state["data"]
                state["data"] = fn(*args, **kwargs)
                state["ts"] = now
                state["valid"] = True
                return state["data"]

        return wrapper

    return decorator
