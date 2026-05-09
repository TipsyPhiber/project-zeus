"""Flask entrypoint. Wires routes to the data-source modules.

Each `/api/*` route returns the raw dict from one module; `/` composes
them into the dashboard HTML via dashboard.page().
"""
import os

from flask import Flask, jsonify

import cloud_aws
import containers
import dashboard
import host_metrics

app = Flask(__name__)


@app.route("/")
def index():
    return dashboard.page(
        host=host_metrics.read(),
        containers=containers.read(),
        aws=cloud_aws.read(),
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


@app.route("/health")
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
