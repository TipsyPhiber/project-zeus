"""Kubernetes cluster summary via the official `kubernetes` client.

Auth: tries in-cluster config first (when running inside a pod with a
ServiceAccount), falls back to ~/.kube/config. Returns cluster version,
node readiness counts, pod counts by phase, and namespace count.

Returns `{"connected": bool, ...}`. When connected, also returns
`version`, `nodes`, `pods`, `namespaces`.
"""
from cache import ttl_cache


def _load_config() -> str:
    """Load kube auth from in-cluster or local ~/.kube/config.

    Returns "in-cluster", "kubeconfig", or "" on failure.
    """
    try:
        from kubernetes import config
    except ImportError:
        return ""
    try:
        config.load_incluster_config()
        return "in-cluster"
    except config.ConfigException:
        pass
    try:
        config.load_kube_config()
        return "kubeconfig"
    except (config.ConfigException, FileNotFoundError):
        return ""


@ttl_cache(seconds=5.0)
def read() -> dict:
    try:
        from kubernetes import client
        from kubernetes.client.rest import ApiException
    except ImportError:
        return {"connected": False, "error": "kubernetes client not installed"}

    auth_mode = _load_config()
    if not auth_mode:
        return {
            "connected": False,
            "error": (
                "No Kubernetes config found. Either run inside a cluster (with a "
                "ServiceAccount) or have ~/.kube/config pointing at a reachable cluster."
            ),
        }

    result: dict = {"connected": True, "auth": auth_mode}

    try:
        version = client.VersionApi().get_code()
        result["version"] = f"{version.major}.{version.minor} ({version.git_version})"
    except ApiException as e:
        result["version"] = f"error: {e.reason}"
    except Exception as e:
        return {"connected": False, "error": f"could not reach API server: {e}"}

    core = client.CoreV1Api()

    try:
        nodes = core.list_node().items
        ready = 0
        for n in nodes:
            for cond in (n.status.conditions or []):
                if cond.type == "Ready" and cond.status == "True":
                    ready += 1
                    break
        result["nodes"] = {"total": len(nodes), "ready": ready}
    except ApiException as e:
        result["nodes"] = {"error": f"{e.status} {e.reason}"}

    try:
        pods = core.list_pod_for_all_namespaces().items
        phases: dict = {}
        for p in pods:
            phase = p.status.phase or "Unknown"
            phases[phase] = phases.get(phase, 0) + 1
        result["pods"] = {"total": len(pods), "by_phase": phases}
    except ApiException as e:
        result["pods"] = {"error": f"{e.status} {e.reason}"}

    try:
        ns = core.list_namespace().items
        result["namespaces"] = len(ns)
    except ApiException as e:
        result["namespaces"] = {"error": f"{e.status} {e.reason}"}

    return result
