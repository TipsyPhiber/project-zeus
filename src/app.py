from flask import Flask, jsonify
import os
import random
import time
from datetime import datetime

app = Flask(__name__)

# --- BACKEND LOGIC ---
def get_system_metrics():
    # Simulating changing data so the dashboard looks "alive"
    cpu = random.randint(12, 45)
    memory = random.randint(30, 60)
    active_nodes = 3
    if cpu > 40:
        active_nodes = 4 # Simulate auto-scaling
    
    return {
        "cpu": cpu,
        "memory": memory,
        "nodes": active_nodes,
        "timestamp": datetime.now().strftime("%H:%M:%S")
    }

@app.route('/api/status')
def status():
    return jsonify(get_system_metrics())

# --- THE FRONTEND GUI ---
@app.route('/')
def dashboard():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Zeus Infrastructure Monitor</title>
        <meta http-equiv="refresh" content="5"> <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
        <style>
            body { 
                font-family: 'JetBrains Mono', monospace; 
                background-color: #0d1117; 
                color: #c9d1d9; 
                text-align: center; 
                padding: 20px;
            }
            h1 { color: #58a6ff; text-transform: uppercase; letter-spacing: 2px; }
            
            .grid { 
                display: flex; 
                justify-content: center; 
                gap: 20px; 
                margin-top: 30px; 
            }
            
            .card { 
                background: #161b22; 
                border: 1px solid #30363d; 
                border-radius: 6px; 
                width: 250px; 
                padding: 20px; 
                box-shadow: 0 3px 6px rgba(0,0,0,0.4);
            }
            
            .metric { font-size: 3em; font-weight: bold; margin: 10px 0; color: #fff; }
            .label { font-size: 0.8em; color: #8b949e; text-transform: uppercase; }
            
            /* Status Light Animation */
            .status-box {
                border: 1px solid #2ea043;
                background: rgba(46, 160, 67, 0.1);
            }
            .status-text { 
                color: #3fb950; 
                font-weight: bold; 
                font-size: 1.5em;
                animation: pulse 2s infinite;
            }
            
            @keyframes pulse {
                0% { opacity: 1; }
                50% { opacity: 0.5; }
                100% { opacity: 1; }
            }

            /* Fake Terminal */
            .terminal {
                margin: 40px auto;
                width: 80%;
                max-width: 800px;
                background: #000;
                border: 1px solid #30363d;
                border-radius: 6px;
                text-align: left;
                padding: 15px;
                font-size: 0.9em;
                color: #3fb950;
                height: 150px;
                overflow: hidden;
                box-shadow: 0 0 10px rgba(0, 255, 0, 0.1);
            }
            .log-line { margin: 5px 0; border-bottom: 1px solid #111; }
            .timestamp { color: #8b949e; margin-right: 10px; }
        </style>
    </head>
    <body>
        <h1>⚡ Project Zeus Dashboard</h1>
        <p>AWS EKS Cluster • us-east-1 • Production</p>
        
        <div class="grid">
            <div class="card status-box">
                <div class="label">System Status</div>
                <div class="status-text">● OPERATIONAL</div>
            </div>

            <div class="card">
                <div class="label">Active Pods</div>
                <div class="metric">""" + str(get_system_metrics()['nodes']) + """</div>
            </div>

            <div class="card">
                <div class="label">CPU Usage</div>
                <div class="metric">""" + str(get_system_metrics()['cpu']) + """%</div>
            </div>
        </div>

        <div class="terminal">
            <div class="log-line"><span class="timestamp">[10:00:01]</span> Zeus Monitor initialized...</div>
            <div class="log-line"><span class="timestamp">[10:00:02]</span> Connection established to AWS CloudWatch</div>
            <div class="log-line"><span class="timestamp">[10:00:03]</span> Scanned 14 EC2 instances. No idle resources found.</div>
            <div class="log-line"><span class="timestamp">[10:00:04]</span> EKS Cluster health check: PASSED</div>
            <div class="log-line"><span class="timestamp">[10:00:05]</span> Waiting for next telemetry packet...</div>
        </div>
        
        <p style="margin-top: 20px; color: #484f58; font-size: 0.8em;">Auto-refreshing every 5s</p>
    </body>
    </html>
    """

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80)
