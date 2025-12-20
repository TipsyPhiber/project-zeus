from flask import Flask, jsonify
import os

app = Flask(__name__)

# --- THE BACKEND API ---
@app.route('/api/status')
def status():
    return jsonify({
        "service": "Zeus Infrastructure Monitor",
        "status": "operational",
        "region": os.environ.get('AWS_REGION', 'us-east-1'),
        "container_id": os.environ.get('HOSTNAME', 'local')
    })

# --- THE WEB GUI ---
@app.route('/')
def dashboard():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Zeus Cloud Monitor</title>
        <style>
            body { font-family: sans-serif; background-color: #1a1a1a; color: #fff; text-align: center; padding-top: 50px; }
            .card { background: #333; padding: 20px; border-radius: 10px; display: inline-block; width: 300px; margin: 20px; box-shadow: 0 4px 8px rgba(0,0,0,0.3); }
            h1 { color: #00d2ff; }
            .status { color: #00ff88; font-weight: bold; font-size: 1.2em; }
            .metric { font-size: 2em; margin: 10px 0; }
            .label { font-size: 0.8em; color: #aaa; }
        </style>
    </head>
    <body>
        <h1>⚡ Project Zeus Dashboard</h1>
        <p>Real-time Infrastructure Monitoring</p>
        
        <div class="card">
            <div class="label">SYSTEM STATUS</div>
            <div class="status">OPERATIONAL</div>
        </div>

        <div class="card">
            <div class="label">ACTIVE NODES</div>
            <div class="metric">3</div>
        </div>

        <div class="card">
            <div class="label">CLOUD REGION</div>
            <div class="metric" style="font-size: 1.5em">us-east-1</div>
        </div>

        <p style="margin-top: 50px; color: #555;">Powered by AWS EKS & Python Flask</p>
    </body>
    </html>
    """

if __name__ == "__main__":
    # Start the web server on port 80
    app.run(host='0.0.0.0', port=80)
