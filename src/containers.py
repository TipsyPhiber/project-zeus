"""Docker container inventory via the local Docker socket.

Returns `{"available": bool, "containers": [{name, image, status}, ...]}`.
If the socket isn't reachable (Docker not running, or container lacks the
`/var/run/docker.sock` mount) `available` is False.
"""
import docker
from docker.errors import DockerException

from cache import ttl_cache


@ttl_cache(seconds=5.0)
def read() -> dict:
    try:
        client = docker.from_env()
        client.ping()
    except DockerException as e:
        return {"available": False, "containers": [], "error": str(e)}

    try:
        out = []
        for c in client.containers.list(all=True):
            image = c.image.tags[0] if c.image.tags else c.image.short_id
            out.append({"name": c.name, "image": image, "status": c.status})
        return {"available": True, "containers": out}
    except DockerException as e:
        return {"available": True, "containers": [], "error": str(e)}
