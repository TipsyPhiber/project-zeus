"""Flask entrypoint. Wires routes to the data-source modules.

Each `/api/*` route returns the raw dict from one module; `/` composes
them into the dashboard HTML via dashboard.page().
"""
import os
from concurrent.futures import ThreadPoolExecutor

from flask import Flask, jsonify

import cloud_aws
import cloud_gcp
import containers
import dashboard
import host_metrics
import k8s

app = Flask(__name__)

# One pool reused across requests so we don't pay thread-creation cost per poll.
_pool = ThreadPoolExecutor(max_workers=5, thread_name_prefix="probe")


def _read_all() -> dict:
    """Run all five data probes concurrently. Total time = the slowest probe."""
    futures = {
        "host": _pool.submit(host_metrics.read),
        "containers": _pool.submit(containers.read),
        "aws": _pool.submit(cloud_aws.read),
        "gcp": _pool.submit(cloud_gcp.read),
        "k8s": _pool.submit(k8s.read),
    }
    return {k: f.result() for k, f in futures.items()}


@app.route("/")
def index():
    return dashboard.page(**_read_all())


@app.route("/partial")
def partial():
    return dashboard.body(**_read_all())


@app.route("/api/host")
def api_host():
    return jsonify(host_metrics.read())


@app.route("/api/containers")
def api_containers():
    return jsonify(containers.read())


@app.route("/api/aws")
def api_aws():
    return jsonify(cloud_aws.read())


@app.route("/api/gcp")
def api_gcp():
    return jsonify(cloud_gcp.read())


@app.route("/api/kubernetes")
def api_kubernetes():
    return jsonify(k8s.read())


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
