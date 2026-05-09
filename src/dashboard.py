"""HTML rendering. Pure: takes data dicts, returns an HTML string.

No data sources, no Flask. Each `_render_*` function turns one section's
data into HTML; `page()` glues them together.
"""

_CSS = """
body { font-family:'JetBrains Mono',monospace; background:#0d1117; color:#c9d1d9;
       padding:20px; max-width:1100px; margin:0 auto; }
h1 { color:#58a6ff; text-transform:uppercase; letter-spacing:2px; text-align:center; }
h2 { color:#8b949e; font-size:0.9em; text-transform:uppercase; letter-spacing:1px;
     margin-top:40px; border-bottom:1px solid #30363d; padding-bottom:6px; }
.grid { display:flex; gap:20px; flex-wrap:wrap; }
.card { background:#161b22; border:1px solid #30363d; border-radius:6px;
        flex:1 1 200px; padding:20px; text-align:center; }
.metric { font-size:2.5em; font-weight:bold; margin:10px 0; color:#fff; }
.label { font-size:0.75em; color:#8b949e; text-transform:uppercase; }
.containers { width:100%; border-collapse:collapse; background:#161b22;
              border:1px solid #30363d; }
.containers th, .containers td { padding:10px; border-bottom:1px solid #30363d;
                                 text-align:left; }
.containers th { color:#8b949e; font-weight:normal; text-transform:uppercase;
                 font-size:0.7em; }
.s-running { color:#3fb950; }
.s-exited, .s-dead, .s-error { color:#f85149; }
.s-paused, .s-restarting, .s-created { color:#d29922; }
.muted { color:#8b949e; }
.small { font-size:0.8em; }
.provider { background:#161b22; border:1px solid #30363d; border-radius:6px;
            padding:16px; margin-bottom:10px; }
.provider-head { font-size:1.1em; margin-bottom:8px; }
.dot { display:inline-block; width:10px; height:10px; border-radius:50%;
       margin-right:8px; vertical-align:middle; }
.dot-green { background:#3fb950; box-shadow:0 0 6px #3fb950; }
.dot-red   { background:#f85149; }
.kv { display:flex; gap:10px; padding:4px 0; }
.k  { width:60px; color:#8b949e; font-size:0.85em; }
.v  { flex:1; }
.pill { background:#21262d; border:1px solid #30363d; border-radius:10px;
        padding:1px 8px; margin-right:4px; font-size:0.85em; }
footer { margin-top:30px; color:#484f58; font-size:0.75em; text-align:center; }
footer a { color:#484f58; }
"""


def _render_host(h: dict) -> str:
    return f"""
    <div class="grid">
        <div class="card"><div class="label">CPU</div>
            <div class="metric">{h['cpu_percent']:.1f}%</div></div>
        <div class="card"><div class="label">Memory</div>
            <div class="metric">{h['memory_percent']:.1f}%</div></div>
        <div class="card"><div class="label">Disk</div>
            <div class="metric">{h['disk_percent']:.1f}%</div></div>
    </div>
    """


def _render_containers(c: dict) -> str:
    if not c.get("available"):
        msg = c.get("error", "Docker socket not available.")
        return (f'<div class="muted">Docker not reachable: {msg}<br>'
                f'Mount /var/run/docker.sock or start Docker.</div>')
    items = c.get("containers") or []
    if not items:
        return '<div class="muted">No containers found.</div>'
    rows = "".join(
        f'<tr><td>{x["name"]}</td><td>{x["image"]}</td>'
        f'<td class="s-{x["status"]}">{x["status"]}</td></tr>'
        for x in items
    )
    return (f'<table class="containers">'
            f'<thead><tr><th>Name</th><th>Image</th><th>Status</th></tr></thead>'
            f'<tbody>{rows}</tbody></table>')


def _render_aws(aws: dict) -> str:
    if not aws.get("connected"):
        return (f'<div class="provider">'
                f'<div class="provider-head"><span class="dot dot-red"></span>'
                f'<strong>AWS</strong>'
                f'<span class="muted"> — not connected</span></div>'
                f'<div class="muted small">{aws.get("error", "Unknown error")}</div>'
                f'</div>')

    ec2 = aws.get("ec2") or {}
    s3 = aws.get("s3") or {}

    if "error" in ec2:
        ec2_html = f'<span class="muted small">error: {ec2["error"]}</span>'
    else:
        pills = " ".join(
            f'<span class="pill">{k}: {v}</span>'
            for k, v in (ec2.get("by_state") or {}).items()
        )
        ec2_html = f'{ec2.get("total", 0)} total {pills}'

    if "error" in s3:
        s3_html = f'<span class="muted small">error: {s3["error"]}</span>'
    else:
        s3_html = f'{s3.get("buckets", 0)} buckets'

    return (f'<div class="provider">'
            f'<div class="provider-head"><span class="dot dot-green"></span>'
            f'<strong>AWS</strong>'
            f'<span class="muted small"> — account {aws["account"]} • '
            f'{aws["region"]}</span></div>'
            f'<div class="kv"><span class="k">EC2</span>'
            f'<span class="v">{ec2_html}</span></div>'
            f'<div class="kv"><span class="k">S3</span>'
            f'<span class="v">{s3_html}</span></div>'
            f'<div class="muted small">{aws["arn"]}</div>'
            f'</div>')


def page(host: dict, containers: dict, aws: dict) -> str:
    running = sum(1 for x in containers.get("containers", [])
                  if x.get("status") == "running")
    total = len(containers.get("containers", []))
    return f"""<!DOCTYPE html>
<html>
<head>
    <title>Zeus Infrastructure Monitor</title>
    <meta http-equiv="refresh" content="10">
    <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
    <style>{_CSS}</style>
</head>
<body>
    <h1>⚡ Project Zeus</h1>
    <p style="text-align:center;" class="muted">
      Host: {host['hostname']} • {host['timestamp']}
    </p>

    <h2>Host Metrics</h2>
    {_render_host(host)}

    <h2>Cloud Providers</h2>
    {_render_aws(aws)}

    <h2>Docker Containers ({running}/{total} running)</h2>
    {_render_containers(containers)}

    <footer>
      Auto-refreshing every 10s •
      <a href="/api/host">/api/host</a> •
      <a href="/api/containers">/api/containers</a> •
      <a href="/api/aws">/api/aws</a> •
      <a href="/health">/health</a>
    </footer>
</body>
</html>"""
