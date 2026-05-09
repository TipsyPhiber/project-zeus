# Architecture

A precise description of what this project actually does and how the code is organised.

---

## What it is

A small Flask web app that displays three things on one page:

1. **Host metrics** — CPU, memory, and disk usage of the machine it runs on, read via `psutil`.
2. **Docker containers** — a list of running and stopped containers on the local Docker daemon, read via the Docker socket.
3. **AWS account inventory** — when AWS credentials are present, the account ID, region, EC2 instance counts (grouped by state), and S3 bucket count, read via `boto3`.

---

## Module map

All Python source lives in `src/`. Each module has one responsibility and a narrow interface.

| Module | Responsibility | Public API | Imports |
|---|---|---|---|
| `cache.py` | TTL memoisation decorator | `ttl_cache(seconds)` | stdlib |
| `host_metrics.py` | Read host CPU/mem/disk | `read() -> dict` | `psutil`, `cache` |
| `containers.py` | List local Docker containers | `read() -> dict` | `docker`, `cache` |
| `cloud_aws.py` | Probe AWS account inventory | `read() -> dict` | `boto3`, `cache` |
| `dashboard.py` | Render dicts → HTML string | `page(host, containers, aws) -> str` | stdlib |
| `app.py` | Flask routes | (entrypoint) | `flask` + the above |

**Coupling**: data modules don't import each other. `dashboard.py` depends only on the *shape* of the returned dicts (documented in each module's docstring), not on the modules themselves. Only `app.py` wires them together.

**Cohesion**: each data module owns one external dependency (`psutil`, `docker`, `boto3`). Removing a feature means removing one module and its route.

---

## Data flow

```
  Browser ── GET / ──▶ app.index()
                          │
                          ├─▶ host_metrics.read()  ──▶ psutil
                          ├─▶ containers.read()    ──▶ /var/run/docker.sock
                          └─▶ cloud_aws.read()     ──▶ AWS APIs (STS, EC2, S3)
                                  │
                                  ▼
                          dashboard.page(host, containers, aws)
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

The browser auto-refreshes every 10s.

---

## HTTP routes

| Path | Returns | Source |
|---|---|---|
| `GET /` | HTML dashboard | composes all three modules |
| `GET /api/host` | JSON | `host_metrics.read()` |
| `GET /api/containers` | JSON | `containers.read()` |
| `GET /api/aws` | JSON | `cloud_aws.read()` |
| `GET /health` | `{"status": "ok"}` | none |

There is no `POST` anywhere; the app is read-only.

---

## Credentials

The app **never accepts credentials over HTTP**. AWS credentials are read by `boto3` from the standard chain, in this order:

1. `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` env vars
2. `~/.aws/credentials` (set up by `aws configure`)
3. IAM role (when running on EC2 / ECS / Lambda)

If none of these are present, `cloud_aws.read()` returns `{"connected": false, "error": ...}` and the dashboard renders a "not connected" panel. No simulated data is shown.

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
  -e AWS_REGION=us-east-1 \
  zeus-monitor
```

The two volume mounts are what make the corresponding panels light up:

- `/var/run/docker.sock` → container can list other containers on the host.
- `~/.aws:/root/.aws:ro` → container can read your AWS credentials.

Remove either mount and the dashboard will say that source is unavailable.

---

## Adding a data source

To add (say) GCP project inventory:

1. Create `src/cloud_gcp.py` with a `read() -> dict` function decorated with `@ttl_cache(seconds=...)`.
2. Add the SDK to `src/requirements.txt`.
3. Add a `_render_gcp(gcp: dict) -> str` to `dashboard.py` and call it from `page()`.
4. Add `import cloud_gcp` and a `/api/gcp` route to `app.py`.

You don't have to touch any other module.

---
