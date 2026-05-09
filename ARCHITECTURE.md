# Architecture

A precise description of what this project actually does and how the code is organised.

---

## What it is

A small Flask web app that displays five things on one page:

1. **Host metrics** — CPU, memory, and disk usage of the machine it runs on, read via `psutil`.
2. **Docker containers** — a list of running and stopped containers on the local Docker daemon, read via the Docker socket.
3. **AWS account inventory** — when AWS credentials are present, the account ID, region, EC2 instance counts (grouped by state), and S3 bucket count, read via `boto3`.
4. **GCP project inventory** — when GCP credentials are present, the project ID, Compute Engine instance counts (grouped by status), and GCS bucket count, read via `google-cloud` SDKs.
5. **Kubernetes cluster summary** — when a kubeconfig or in-cluster ServiceAccount is reachable, the API-server version, node readiness, pod counts by phase, and namespace count, read via the official `kubernetes` client.

That is the entire feature set. There is no scheduling, no alerting, no auto-scaling, no auth.

If a data source isn't reachable (no Docker socket, no AWS / GCP credentials, no Kubernetes config), the dashboard says so explicitly. There is no simulated data.

---

## Module map

All Python source lives in `src/`. Each module has one responsibility and a narrow interface.

| Module | Responsibility | Public API | Imports |
|---|---|---|---|
| `cache.py` | TTL memoisation decorator | `ttl_cache(seconds)` | stdlib |
| `host_metrics.py` | Read host CPU/mem/disk | `read() -> dict` | `psutil`, `cache` |
| `containers.py` | List local Docker containers | `read() -> dict` | `docker`, `cache` |
| `cloud_aws.py` | Probe AWS account inventory | `read() -> dict` | `boto3`, `cache` |
| `cloud_gcp.py` | Probe GCP project inventory | `read() -> dict` | `google-cloud-*`, `cache` |
| `k8s.py` | Probe Kubernetes cluster | `read() -> dict` | `kubernetes`, `cache` |
| `dashboard.py` | Render dicts → HTML string | `page(host, containers, aws, gcp, k8s) -> str` | stdlib |
| `app.py` | Flask routes | (entrypoint) | `flask` + the above |

**Coupling**: data modules don't import each other. `dashboard.py` depends only on the *shape* of the returned dicts (documented in each module's docstring), not on the modules themselves. Only `app.py` wires them together.

**Cohesion**: each data module owns one external dependency (`psutil`, `docker`, `boto3`, `google-cloud-*`, `kubernetes`). Removing a feature means removing one module and its route.

---

## Data flow

```
  Browser ── GET / ──▶ app.index()
                          │
                          ├─▶ host_metrics.read()  ──▶ psutil
                          ├─▶ containers.read()    ──▶ /var/run/docker.sock
                          ├─▶ cloud_aws.read()     ──▶ AWS APIs (STS, EC2, S3)
                          ├─▶ cloud_gcp.read()     ──▶ GCP APIs (Compute, Storage)
                          └─▶ k8s.read()           ──▶ kube-apiserver
                                  │
                                  ▼
                          dashboard.page(host, containers, aws, gcp, k8s)
                                  │
                                  ▼
                          HTML response
```

Each `read()` is wrapped in `@ttl_cache` so repeated calls within the TTL hit memory, not the underlying source:

| Source | TTL | Why |
|---|---|---|
| `host_metrics.read` | 2s | `psutil.cpu_percent(interval=0.2)` is a 200ms blocking call |
| `containers.read` | 5s | Docker socket round-trip is fast but unnecessary on every render |
| `cloud_aws.read` | 30s | AWS API calls are slow and have rate / cost implications |
| `cloud_gcp.read` | 30s | Same as AWS |
| `k8s.read` | 5s | API-server calls are local-network fast |

The browser auto-refreshes every 10s.

---

## HTTP routes

| Path | Returns | Source |
|---|---|---|
| `GET /` | HTML dashboard | composes all five modules |
| `GET /api/host` | JSON | `host_metrics.read()` |
| `GET /api/containers` | JSON | `containers.read()` |
| `GET /api/aws` | JSON | `cloud_aws.read()` |
| `GET /api/gcp` | JSON | `cloud_gcp.read()` |
| `GET /api/kubernetes` | JSON | `k8s.read()` |
| `GET /health` | `{"status": "ok"}` | none |

There is no `POST` anywhere; the app is read-only.

---

## Credentials

The app **never accepts credentials over HTTP.** Each cloud probe reads from its provider's standard credential chain, in this order:

### AWS (`boto3`)

1. `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` env vars
2. `~/.aws/credentials` (set up by `aws configure`)
3. IAM role (when running on EC2 / ECS / Lambda)

### GCP (`google.auth.default`)

1. `GOOGLE_APPLICATION_CREDENTIALS` env var pointing to a service-account key file
2. `gcloud auth application-default login` (writes to `~/.config/gcloud/`)
3. Workload identity (when running in GKE)
4. Project ID resolved from `GOOGLE_CLOUD_PROJECT`, ADC project, or `gcloud config set project`

### Kubernetes (`kubernetes.config`)

1. In-cluster ServiceAccount tokens (when running inside a pod)
2. `~/.kube/config` (typical local setup)

If none are present, the corresponding `read()` returns `{"connected": false, "error": ...}` and the dashboard renders a "not connected" panel. No simulated data is shown.

---

## Running it

### Locally with Python

```bash
cd src
pip install -r requirements.txt
python app.py
```

Then open <http://localhost:8080>. Override the port with `PORT=9000 python app.py`.

### In Docker

```bash
docker build -t zeus-monitor .

docker run -p 8080:8080 \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v ~/.aws:/root/.aws:ro \
  -v ~/.config/gcloud:/root/.config/gcloud:ro \
  -v ~/.kube:/root/.kube:ro \
  -e AWS_REGION=us-east-1 \
  zeus-monitor
```

Each volume mount enables one panel:

- `/var/run/docker.sock` → Docker container listing
- `~/.aws` → AWS panel
- `~/.config/gcloud` → GCP panel
- `~/.kube` → Kubernetes panel (note: kubeconfig referencing `localhost` won't reach the host's kube-apiserver from inside a container)

Remove a mount and the corresponding source will say "not connected".

### On Kubernetes

See `deploy/kubernetes/README.md`. There's also a `deploy/terraform/` module that provisions a GKE Autopilot cluster and deploys the app to it in one `terraform apply`.

---

## Adding a data source

To add (say) Azure subscription inventory:

1. Create `src/cloud_azure.py` with a `read() -> dict` function decorated with `@ttl_cache(seconds=...)`.
2. Add the SDK to `src/requirements.txt`.
3. Add a `_render_azure(azure: dict) -> str` to `dashboard.py` and call it from `page()`.
4. Add `import cloud_azure` and a `/api/azure` route to `app.py`.

You don't have to touch any other module.

---

## Repository layout

```
src/                       Python source (one module per data source)
deploy/
  kubernetes/              Manifests for `kubectl apply -f`
  terraform/               GKE Autopilot + app deployment in one apply
scripts/
  health_check.sh          Ad-hoc shell script for inspecting a host
Dockerfile                 Image build for the app
ARCHITECTURE.md            This file
README.md                  Top-level pointer
LICENSE
```

---

## What is **not** in this project

- **No tests.**
- **No auth, no HTTPS, no rate limiting.** This is a read-only dashboard meant to live on a private network or behind a separate ingress that handles auth.
- **No alerting, no scheduling, no auto-scaling logic.** The dashboard reports state; it doesn't act on it.
- **No multi-account / multi-project support.** Each cloud probe reports one account / one project (whatever the credentials resolve to).
- **The Terraform module has not been deployed from this dev environment.** It should plan cleanly against any GCP project with billing enabled, but you'll want to review the plan before applying to your own account.
