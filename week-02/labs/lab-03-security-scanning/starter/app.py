"""
Vulnerable Flask Application
This app is intentionally built with outdated dependencies for security scanning practice.
"""

from flask import Flask, jsonify
import requests

app = Flask(__name__)

@app.route("/")
def home():
    return """
    <h1>Security Scanning Lab</h1>
    <p>This application is intentionally vulnerable for educational purposes.</p>
    <ul>
        <li><a href="/health">Health Check</a></li>
        <li><a href="/version">Version Info</a></li>
        <li><a href="/external">External API Test</a></li>
    </ul>
    """

@app.route("/health")
def health():
    return jsonify({
        "status": "healthy",
        "service": "vulnerable-app"
    })

@app.route("/version")
def version():
    return jsonify({
        "app": "vulnerable-app",
        "version": "1.0.0",
        "python": "3.9",
        "flask": "2.0.1",
        "requests": "2.25.1"
    })

@app.route("/external")
def external():
    """Make a request to an external API to demonstrate requests usage"""
    try:
        response = requests.get("https://api.github.com/", timeout=5)
        return jsonify({
            "status": "success",
            "external_api": "github",
            "response_code": response.status_code
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

if __name__ == "__main__":
    # Running on all interfaces (0.0.0.0) for container accessibility
    app.run(host="0.0.0.0", port=5000, debug=False)
