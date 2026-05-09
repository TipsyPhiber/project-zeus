"""Docker container inventory via the local Docker socket.

Returns `{"available": bool, "containers": [{name, image, status}, ...]}`.

The socket location varies by setup: standard Docker daemon uses
/var/run/docker.sock, Docker Desktop uses ~/.docker/run/docker.sock,
and rootless Docker uses $XDG_RUNTIME_DIR/docker.sock. We try the
DOCKER_HOST env var first, then probe known unix-socket paths.
"""
import os

import docker
from docker.errors import DockerException

from cache import ttl_cache


def _candidate_sockets():
    """Yield (label, base_url) pairs for sockets to try, in priority order."""
    dh = os.environ.get("DOCKER_HOST")
    if dh:
        yield "DOCKER_HOST", dh

    home = os.path.expanduser("~")
    uid = os.getuid()
    for path in [
        "/var/run/docker.sock",
        f"{home}/.docker/run/docker.sock",
        f"{home}/.docker/desktop/docker.sock",
        f"/run/user/{uid}/docker.sock",
    ]:
        if os.path.exists(path):
            yield path, f"unix://{path}"


@ttl_cache(seconds=5.0)
def read() -> dict:
    tried = []
    for label, url in _candidate_sockets():
        try:
            client = docker.DockerClient(base_url=url)
            client.ping()
        except DockerException as e:
            tried.append(f"{label}: {e}")
            continue

        try:
            out = []
            for c in client.containers.list(all=True):
                # Read from cached attrs dict (populated by list()) rather than
                # c.image, which does an extra GET /images/<sha>/json that 404s
                # if the image was replaced or pruned after the container started.
                image = (c.attrs.get("Config", {}).get("Image")
                         or c.attrs.get("Image", "")[:19]
                         or "<unknown>")
                out.append({"name": c.name, "image": image, "status": c.status})
            return {"available": True, "source": label, "containers": out}
        except DockerException as e:
            return {"available": True, "source": label,
                    "containers": [], "error": str(e)}

    if not tried:
        return {"available": False, "containers": [],
                "error": ("No Docker socket found. Set DOCKER_HOST or check that "
                          "Docker is running.")}
    return {"available": False, "containers": [],
            "error": " | ".join(tried)}
