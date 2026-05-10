"""TTL cache for zero-arg data probes.

`@ttl_cache(seconds=N)` memoises the most recent return value of `fn`
for N seconds. Threadsafe. Per-function (does not key on arguments) —
intended for parameterless probes like `host_metrics.read()`.

`@ttl_cache(seconds=N, stale_while_revalidate=True)` returns the
previous value immediately when the TTL has expired, and kicks off a
background refresh. Use for slow probes (network calls) where users
prefer "instant + slightly stale" over "blocked + fresh". The very
first call is still synchronous (there's no stale value yet).
"""
import threading
import time
from functools import wraps
from typing import Callable


def ttl_cache(seconds: float, stale_while_revalidate: bool = False) -> Callable:
    def decorator(fn: Callable) -> Callable:
        state = {"data": None, "ts": 0.0, "valid": False, "refreshing": False}
        lock = threading.Lock()

        def _refresh():
            try:
                new_data = fn()
                with lock:
                    state["data"] = new_data
                    state["ts"] = time.monotonic()
            finally:
                with lock:
                    state["refreshing"] = False

        @wraps(fn)
        def wrapper(*args, **kwargs):
            with lock:
                now = time.monotonic()
                fresh = state["valid"] and (now - state["ts"]) < seconds

                if fresh:
                    return state["data"]

                if stale_while_revalidate and state["valid"]:
                    # Return stale immediately, refresh in background
                    # (only one refresh in flight at a time).
                    if not state["refreshing"]:
                        state["refreshing"] = True
                        threading.Thread(target=_refresh, daemon=True).start()
                    return state["data"]

                # Cold start, or non-SWR: refresh synchronously.
                state["data"] = fn(*args, **kwargs)
                state["ts"] = now
                state["valid"] = True
                return state["data"]

        return wrapper

    return decorator
