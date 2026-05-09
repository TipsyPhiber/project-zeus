# Project Zeus

A Flask dashboard that reports real host metrics, real Docker container state, and real AWS account inventory. No simulated data.

See [ARCHITECTURE.md](./ARCHITECTURE.md) for a full description of how the code is organised and what's intentionally not in scope.

## What it does

- Shows host CPU / memory / disk via `psutil`
- Lists local Docker containers via the Docker socket
- Shows AWS account / EC2 / S3 inventory via `boto3` when credentials are present
- Exposes JSON at `/api/host`, `/api/containers`, `/api/aws`, and `/health`

If a data source isn't reachable (no Docker, no AWS creds) the dashboard says so.

## Running it

### With Python

```bash
cd src
pip install -r requirements.txt
python app.py
```

Open <http://localhost:8080>.

### With Docker

```bash
docker build -t zeus-monitor .

docker run -p 8080:8080 \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v ~/.aws:/root/.aws:ro \
  -e AWS_REGION=us-east-1 \
  zeus-monitor
```

The Docker-socket mount enables container listing. The `~/.aws` mount enables AWS lookups. Either can be omitted; the dashboard will report that source as unavailable.

## Repository layout

```
src/
  app.py            Flask routes
  dashboard.py      HTML rendering
  host_metrics.py   psutil host metrics
  containers.py     Docker container inventory
  cloud_aws.py      boto3 AWS probe
  cache.py          TTL cache decorator
  requirements.txt
Dockerfile
scripts/health_check.sh   ad-hoc shell script for inspecting a host
ARCHITECTURE.md
LICENSE
```

## License

MIT — see `LICENSE`.
