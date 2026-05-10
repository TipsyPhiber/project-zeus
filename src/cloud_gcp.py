"""GCP project inventory via google-cloud SDKs.

Reads credentials via Application Default Credentials (`gcloud auth
application-default login` or GOOGLE_APPLICATION_CREDENTIALS pointing at
a service-account key, or workload identity in-cluster). Never accepts
secrets via HTTP.

Returns `{"connected": bool, ...}`. When connected, also returns
`project`, `compute`, `storage`.
"""
import os

from cache import ttl_cache


_NO_CREDS_MSG = (
    "No GCP credentials found. Run `gcloud auth application-default login` "
    "or set GOOGLE_APPLICATION_CREDENTIALS to a service-account key."
)


def _likely_has_creds() -> bool:
    """Cheap check before invoking google.auth.default(), which can spend
    several seconds probing the GCE metadata server on non-GCE hosts."""
    if os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
        return True
    adc = os.path.expanduser("~/.config/gcloud/application_default_credentials.json")
    return os.path.exists(adc)


@ttl_cache(seconds=30.0, stale_while_revalidate=True)
def read() -> dict:
    if not _likely_has_creds():
        return {"connected": False, "error": _NO_CREDS_MSG}

    try:
        import google.auth
        from google.auth.exceptions import DefaultCredentialsError, GoogleAuthError
        from google.api_core.exceptions import GoogleAPICallError, PermissionDenied
    except ImportError:
        return {"connected": False, "error": "google-auth not installed"}

    try:
        creds, project_id = google.auth.default()
    except DefaultCredentialsError as e:
        return {"connected": False, "error": f"{_NO_CREDS_MSG} ({e})"}

    project_id = project_id or os.environ.get("GOOGLE_CLOUD_PROJECT")
    if not project_id:
        return {
            "connected": False,
            "error": (
                "GCP credentials present but no project ID. Set "
                "GOOGLE_CLOUD_PROJECT or run `gcloud config set project <id>`."
            ),
        }

    result = {"connected": True, "project": project_id}

    try:
        from google.cloud import compute_v1
        client = compute_v1.InstancesClient(credentials=creds)
        states: dict = {}
        total = 0
        for _zone, response in client.aggregated_list(project=project_id):
            for instance in (response.instances or []):
                s = instance.status
                states[s] = states.get(s, 0) + 1
                total += 1
        result["compute"] = {"total": total, "by_state": states}
    except (GoogleAuthError, GoogleAPICallError, PermissionDenied) as e:
        result["compute"] = {"error": str(e)}
    except ImportError:
        result["compute"] = {"error": "google-cloud-compute not installed"}

    try:
        from google.cloud import storage
        client = storage.Client(project=project_id, credentials=creds)
        buckets = list(client.list_buckets())
        result["storage"] = {"buckets": len(buckets)}
    except (GoogleAuthError, GoogleAPICallError, PermissionDenied) as e:
        result["storage"] = {"error": str(e)}
    except ImportError:
        result["storage"] = {"error": "google-cloud-storage not installed"}

    return result
