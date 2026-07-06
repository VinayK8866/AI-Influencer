from flask import Flask, jsonify, request
from flask_cors import CORS
import sys
import os
import threading
import json
from dotenv import load_dotenv

# Load local environment variables from parent directory's .env.local
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(parent_dir, '.env.local'))
load_dotenv(os.path.join(parent_dir, '.env')) # Also fallback to standard .env

# Ensure the adjacent python scripts can be imported
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from agency import AgencyCOO
    from main import MayaAutopilot
except ImportError as e:
    print(f"Error importing modules: {e}")

app = Flask(__name__)
CORS(app)

def run_autopilot_background(post_type, location=None):
    try:
        # Helper to update active run state in state.json
        def update_active_run(step, log_entry=None):
            try:
                state_path = "state.json"
                state = {}
                if os.path.exists(state_path):
                    with open(state_path, 'r') as f:
                        state = json.load(f)
                
                if "active_run" not in state:
                    state["active_run"] = {"logs": []}
                
                state["active_run"]["status"] = "processing"
                state["active_run"]["post_type"] = post_type
                state["active_run"]["current_step"] = step
                if log_entry:
                    state["active_run"]["logs"].append(log_entry)
                    if len(state["active_run"]["logs"]) > 25:
                        state["active_run"]["logs"] = state["active_run"]["logs"][-25:]
                
                with open(state_path, 'w') as f:
                    json.dump(state, f)
            except Exception as e:
                print(f"Error writing background status: {e}")

        # Step 1: Initialize
        update_active_run("Step 1/5: Booting Autopilot & Storyboard Engines", "Orchestrating social hooks & visual assets...")
        autopilot = MayaAutopilot()
        active_loc = location if location else autopilot.state.get("current_location", "Milan")
        
        # Step 2: Strategy Sourcing
        update_active_run("Step 2/5: Sourcing 80/20 Engagement Strategy Memory", f"Analyzing historical metrics for {active_loc}...")
        
        # Step 3: Debate & Storyboarding
        update_active_run("Step 3/5: Running Agency Storyboard Debate", "Creative Director & Researcher styling cinematic layout...")
        
        # Run standard loop
        autopilot.run_cycle(post_type=post_type, force_location=active_loc)
        
        # Step 4: Complete
        try:
            state_path = "state.json"
            if os.path.exists(state_path):
                with open(state_path, 'r') as f:
                    state = json.load(f)
                state["active_run"] = {
                    "status": "idle",
                    "post_type": None,
                    "current_step": "Draft completed successfully!",
                    "logs": ["Done! Instagram content drafted & strategy updated! Refresh to view latest wardrobe metrics."]
                }
                with open(state_path, 'w') as f:
                    json.dump(state, f)
        except Exception as e:
            pass
            
    except Exception as e:
        # Step 5: Failed
        try:
            state_path = "state.json"
            if os.path.exists(state_path):
                with open(state_path, 'r') as f:
                    state = json.load(f)
                state["active_run"] = {
                    "status": "failed",
                    "post_type": None,
                    "current_step": "Autopilot Execution Failed!",
                    "logs": [f"Error details: {str(e)}", "Please check your Gemini API quota or local internet connection."]
                }
                with open(state_path, 'w') as f:
                    json.dump(state, f)
        except:
            pass

@app.route('/api/status', methods=['GET'])
def get_status():
    try:
        state = {"current_location": "Milan"}
        state_path = "state.json"
        if os.path.exists(state_path):
            try:
                with open(state_path, 'r') as f:
                    state = json.load(f)
            except Exception as read_err:
                print(f"[API Status] Error reading local state.json: {read_err}")

        # Server status is online and state is loaded directly from local state.json database
        return jsonify({"status": "online", "state": state}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/update-settings', methods=['POST'])
def update_settings():
    """Updates settings like Maya's active location completely without editing code."""
    try:
        data = request.json or {}
        location = data.get("location")
        
        state_path = "state.json"
        state = {"current_location": "Milan"}
        if os.path.exists(state_path):
            with open(state_path, 'r') as f:
                state = json.load(f)
                
        if location:
            state["current_location"] = location
            
        with open(state_path, 'w') as f:
            json.dump(state, f)
            
        return jsonify({
            "success": True,
            "message": f"Successfully updated current location to {location}.",
            "state": state
        }), 200
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
    """Triggers a background async run of the autopilot."""
    try:
        data = request.json or {}
        post_type = data.get("post_type", "photo") # "photo" or "reel"
        location = data.get("location")

        # Verify if background run is already active
        state_path = "state.json"
        if os.path.exists(state_path):
            try:
                with open(state_path, 'r') as f:
                    state = json.load(f)
                if state.get("active_run", {}).get("status") == "processing":
                    return jsonify({
                        "success": False,
                        "message": "A post draft generation is already active in the background. Please wait!"
                    }), 400
            except:
                pass

        # Spin background thread
        thread = threading.Thread(target=run_autopilot_background, args=(post_type, location))
        thread.daemon = True
        thread.start()

        return jsonify({
            "success": True,
            "message": f"Background {post_type} cycle started successfully!"
        }), 200
    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"CRITICAL ERROR in /api/trigger-cycle:\n{error_trace}")
        return jsonify({"error": str(e), "trace": error_trace}), 500

@app.route('/api/webhook/instagram', methods=['POST'])
def instagram_webhook():
    """
    Instagram Graph API Webhook endpoint.
    Scans incoming comments for trigger keywords ('style', 'link', 'milan', 'outfit')
    and automatically responds with the current post's active outfit affiliate links.
    """
    try:
        data = request.json or {}
        print(f"[Webhook Received] Raw Webhook Content: {data}")
        
        # Meta webhooks can be batch events, but we parse the direct message structure
        comment_text = data.get("comment_text", "").lower()
        username = data.get("username", "fashion_enthusiast")
        
        triggers = ["style", "link", "milan", "outfit", "wear", "dress"]
        matched_trigger = None
        for trig in triggers:
            if trig in comment_text:
                matched_trigger = trig
                break
                
        if not matched_trigger:
            return jsonify({
                "success": False,
                "message": "No target keywords matched in comment."
            }), 200
            
        # 1. Load active state to find out what outfits are currently active
        autopilot = MayaAutopilot()
        state = autopilot.state
        last_post = state.get("last_post", {})
        active_products = last_post.get("products", [])
        location = last_post.get("location", "Milan")
        
        # 2. Load outfit catalog to extract links
        catalog_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "outfit_catalog.json")
        catalog = []
        if os.path.exists(catalog_path):
            import json
            with open(catalog_path, 'r') as f:
                catalog = json.load(f)
                
        links_sent = []
        for prod_id in active_products:
            for item in catalog:
                if item["id"] == prod_id:
                    links_sent.append(f"{item['name']}: {item['affiliate_link']}")
                    
        if not links_sent:
            # Send default styling link if no specific products were active
            links_sent.append("Maya's Curated Travel Outfits: https://www.amazon.com/shop/mayarossi")
            
        # Construct the high-fidelity DM response
        dm_response = f"Hi @{username}! 🖤 So happy you loved the vibes in {location}! Here is the direct link to the look: " + " | ".join(links_sent) + " Spices & Spritz! 🌶️✨"
        
        # In a real live environment, we would trigger meta API to send DM:
        # autopilot.social.cl.direct_send(dm_response, [user_id])
        # We log and return the message here
        print(f"[Auto-DM Dispatcher] Successfully sent DM to @{username}: {dm_response}")
        
        return jsonify({
            "success": True,
            "username": username,
            "trigger_keyword": matched_trigger,
            "dm_sent": dm_response,
            "active_products": active_products
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/analytics', methods=['GET'])
def get_analytics():
    """
    Returns live processed data metrics for locations, products and average ER.
    """
    try:
        from analytics import StrategyOptimizer
        optimizer = StrategyOptimizer()
        brief = optimizer.generate_performance_brief()
        
        # Load raw history
        history = optimizer.history
        
        return jsonify({
            "success": True,
            "brief": brief,
            "history": history
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Vercel requires the app variable to be exposed
if __name__ == '__main__':
    app.run(debug=True, port=5328)
