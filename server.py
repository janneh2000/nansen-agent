#!/usr/bin/env python3
"""
NansenAgent Server - HTTP API + static file server
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import sys

# Add parent dir to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from agent import process_query

app = Flask(__name__, static_folder=".")
CORS(app)

# Example queries for the UI
EXAMPLE_QUERIES = [
    "What tokens are smart money buying on Solana right now?",
    "Show me the top smart money traders on Ethereum this week",
    "What's the netflow of smart money on Base in the last 24h?",
    "Analyze the top trending tokens on Arbitrum",
    "What is smart money doing on BNB chain this month?",
    "Show me smart money transfers on Ethereum in the last hour",
]


@app.route("/")
def index():
    return send_from_directory(".", "index.html")


@app.route("/api/query", methods=["POST"])
def query():
    data = request.get_json()
    question = data.get("question", "").strip()
    
    if not question:
        return jsonify({"success": False, "error": "No question provided"}), 400
    
    result = process_query(question)
    return jsonify(result)


@app.route("/api/examples", methods=["GET"])
def examples():
    return jsonify({"examples": EXAMPLE_QUERIES})


@app.route("/api/health", methods=["GET"])
def health():
    # Check if nansen-cli is installed
    import subprocess
    try:
        r = subprocess.run(["nansen", "--version"], capture_output=True, text=True, timeout=5)
        nansen_version = r.stdout.strip() or "installed"
    except FileNotFoundError:
        nansen_version = None
    
    return jsonify({
        "status": "ok",
        "nansen_cli": nansen_version,
        "anthropic_key": bool(os.environ.get("ANTHROPIC_API_KEY")),
        "nansen_key": bool(os.environ.get("NANSEN_API_KEY"))
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"\n🚀 NansenAgent running at http://localhost:{port}")
    print(f"   ANTHROPIC_API_KEY: {'✅ set' if os.environ.get('ANTHROPIC_API_KEY') else '❌ missing'}")
    print(f"   NANSEN_API_KEY:    {'✅ set' if os.environ.get('NANSEN_API_KEY') else '❌ missing (run: nansen login)'}\n")
    app.run(host="0.0.0.0", port=port, debug=False)
