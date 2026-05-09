"""Flask entrypoint. Wires routes to the data-source modules.

Each `/api/*` route returns the raw dict from one module; `/` composes
them into the dashboard HTML via dashboard.page().
"""
import os

from flask import Flask, jsonify

import cloud_aws
import cloud_gcp
import containers
import dashboard
import host_metrics
import k8s

app = Flask(__name__)


@app.route("/")
def index():
    return dashboard.page(
        host=host_metrics.read(),
        containers=containers.read(),
        aws=cloud_aws.read(),
        gcp=cloud_gcp.read(),
        k8s=k8s.read(),
    )


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
