#!/usr/bin/env python3
"""
NansenAgent Server - HTTP API + static file server
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import sys

# Add current dir to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from agent import process_query

app = Flask(__name__, static_folder=".")
CORS(app)

# Example queries for the UI
EXAMPLE_QUERIES = [
    "What tokens are smart money buying on Solana right now?",
    "Show me smart money inflows on Base in the last 6 hours",
    "What are the top smart money trades on Ethereum this week?",
    "Analyze trending tokens on Arbitrum",
    "What is smart money doing on BNB chain this month?",
    "Show smart money transfers on Ethereum in the last hour",
]


# ✅ Serve frontend
@app.route("/")
def index():
    return send_from_directory(".", "index.html")


# ✅ MAIN API (FIXED — only one route)
@app.route("/api/query", methods=["POST"])
def query():
    print("\n➡️ Received request")

    try:
        data = request.get_json()
        question = data.get("question", "").strip()

        print(f"🧠 Question: {question}")

        if not question:
            return jsonify({
                "success": False,
                "error": "No question provided"
            }), 400

        result = process_query(question)

        print("✅ Sending response\n")
        return jsonify(result)

    except Exception as e:
        print(f"❌ Server error: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"Server error: {str(e)}"
        }), 500


# ✅ Example queries endpoint
@app.route("/api/examples", methods=["GET"])
def examples():
    return jsonify({"examples": EXAMPLE_QUERIES})


# ✅ Health check
@app.route("/api/health", methods=["GET"])
def health():
    import subprocess

    try:
        r = subprocess.run(
            ["nansen", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        nansen_version = r.stdout.strip() or "installed"
    except FileNotFoundError:
        nansen_version = None

    return jsonify({
        "status": "ok",
        "nansen_cli": nansen_version,
        "anthropic_key": bool(os.environ.get("ANTHROPIC_API_KEY")),
        "nansen_key": bool(os.environ.get("NANSEN_API_KEY"))
    })


# ✅ Start server
if __name__ == "__main__":
    from waitress import serve

    port = int(os.environ.get("PORT", 5000))

    print(f"\n🚀 NansenAgent → http://localhost:{port}")
    print(f"   ANTHROPIC_API_KEY: {'✅' if os.environ.get('ANTHROPIC_API_KEY') else '❌ missing'}")
    print(f"   NANSEN_API_KEY:    {'✅' if os.environ.get('NANSEN_API_KEY') else '❌ missing'}\n")

    serve(
        app,
        host="0.0.0.0",
        port=port,
        threads=8,
        channel_timeout=120
    )