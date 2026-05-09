"""Host CPU / memory / disk via psutil. No external services."""
import os
from datetime import datetime

import psutil

from cache import ttl_cache


@ttl_cache(seconds=2.0)
def read() -> dict:
    return {
        "cpu_percent": psutil.cpu_percent(interval=0.2),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_percent": psutil.disk_usage("/").percent,
        "hostname": os.uname().nodename,
        "timestamp": datetime.now().strftime("%H:%M:%S"),
    }
