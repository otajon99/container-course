from flask import Flask
import os
import socket

app = Flask(__name__)

# Configurable via environment variable
GREETING = os.environ.get("GREETING", "Hello")
ENVIRONMENT = os.environ.get("ENVIRONMENT", "development")
# TODO: Replace "YOUR_NAME_HERE" with your actual name!
STUDENT_NAME = os.environ.get("STUDENT_NAME", "YOUR_NAME_HERE")
# TODO: Replace with your GitHub username
GITHUB_USERNAME = os.environ.get("GITHUB_USERNAME", "YOUR_GITHUB_USERNAME")
APP_VERSION = os.environ.get("APP_VERSION", "v4")

# Kubernetes Downward API fields (injected by the Deployment manifest)
POD_NAME = os.environ.get("POD_NAME", socket.gethostname())
POD_NAMESPACE = os.environ.get("POD_NAMESPACE", "unknown")
NODE_NAME = os.environ.get("NODE_NAME", "unknown")
POD_IP = os.environ.get("POD_IP", "unknown")

@app.route("/")
def home():
    return f"""
    <html>
    <head>
        <title>{STUDENT_NAME}'s App</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
            .container {{ background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); max-width: 600px; }}
            h1 {{ color: #326CE5; }}
            .info {{ background: #e8f0fe; padding: 15px; border-radius: 5px; margin-top: 20px; }}
            .info p {{ margin: 5px 0; }}
            code {{ background: #263238; color: #80cbc4; padding: 2px 6px; border-radius: 3px; }}
            .nav {{ margin-top: 20px; }}
            .nav a {{ display: inline-block; margin-right: 10px; padding: 8px 16px; background: #326CE5; color: white; text-decoration: none; border-radius: 5px; }}
            .nav a:hover {{ background: #1a4db0; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>{GREETING} from Kubernetes! ☸️</h1>
            <div class="info">
                <p><strong>Student:</strong> {STUDENT_NAME}</p>
                <p><strong>Version:</strong> <code>{APP_VERSION}</code></p>
                <p><strong>Environment:</strong> {ENVIRONMENT}</p>
                <p><strong>Pod:</strong> <code>{POD_NAME}</code></p>
            </div>
            <div class="nav">
                <a href="/info">/info</a>
                <a href="/health">/health</a>
                <a href="/student">/student</a>
            </div>
        </div>
    </body>
    </html>
    """

@app.route("/info")
def info():
    """Pod information endpoint — reveals Kubernetes metadata via Downward API"""
    return {
        "pod_name": POD_NAME,
        "pod_namespace": POD_NAMESPACE,
        "pod_ip": POD_IP,
        "node_name": NODE_NAME,
        "hostname": socket.gethostname(),
        "app_version": APP_VERSION,
        "student": STUDENT_NAME,
        "github_username": GITHUB_USERNAME,
    }

@app.route("/health")
def health():
    return {"status": "healthy", "version": APP_VERSION}

@app.route("/student")
def student():
    """Student information endpoint"""
    return {
        "name": STUDENT_NAME,
        "github_username": GITHUB_USERNAME,
        "app_version": APP_VERSION,
    }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"Starting {STUDENT_NAME}'s app on port {port} (version {APP_VERSION})...")
    app.run(host="0.0.0.0", port=port)
