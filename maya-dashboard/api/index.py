from flask import Flask, jsonify, request
from flask_cors import CORS
import sys
import os

# Ensure the adjacent python scripts can be imported
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from agency import AgencyCOO
    from main import MayaAutopilot
except ImportError as e:
    print(f"Error importing modules: {e}")

app = Flask(__name__)
CORS(app)

@app.route('/api/status', methods=['GET'])
def get_status():
    try:
        autopilot = MayaAutopilot()
        state = autopilot.state
        return jsonify({"status": "online", "state": state}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/generate-reel-storyboard', methods=['POST'])
def generate_reel_storyboard():
    try:
        data = request.json or {}
        location = data.get("location", "Milan")
        concept = f"Luxury Travel & Fashion fusion concept set in {location}."

        coo = AgencyCOO()
        agency_output = coo.run_reel_workflow(concept)

        return jsonify({
            "success": True,
            "storyboard": agency_output.get("storyboard"),
            "metadata": agency_output.get("metadata")
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

import traceback

@app.route('/api/trigger-cycle', methods=['POST'])
def trigger_cycle():
    """Triggers a full run of the autopilot."""
    try:
        data = request.json or {}
        post_type = data.get("post_type", "photo") # "photo" or "reel"

        # On Vercel Hobby tier, synchronous operations are limited to 10s.
        # A true production deployment handling Muapi video polling would require
        # Vercel Pro (300s timeout) or an external background job queue (e.g., Inngest).
        # We execute synchronously here.
        autopilot = MayaAutopilot()
        autopilot.run_cycle(post_type=post_type)

        return jsonify({
            "success": True,
            "message": f"Successfully completed {post_type} cycle."
        }), 200
    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"CRITICAL ERROR in /api/trigger-cycle:\n{error_trace}")
        return jsonify({"error": str(e), "trace": error_trace}), 500

# Vercel requires the app variable to be exposed
if __name__ == '__main__':
    app.run(debug=True, port=5328)
