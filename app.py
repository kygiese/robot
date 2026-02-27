"""
Flask Control Server for Robot

This server:
- Serves the HTML/JavaScript control interface
- Accepts control commands from the webpage
- Forwards validated commands to the robot control layer
- Handles safety features (heartbeat, command validation)

Run with: python app.py
Access at: http://<robot-ip>:5000/
"""

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import robot_control
import time
import subprocess
import threading
import os
import dialog_engine as de

app = Flask(__name__)
CORS(app)  # Enable CORS for local network access

# Initialize robot control (will use mock mode if hardware not available)
robot = None

# Dialog engine singleton
_dialog_engine = None

# Default script path (relative to this file)
DEFAULT_SCRIPT = os.path.join(os.path.dirname(__file__), "sample_script.txt")

# Rate limiting for command flooding prevention
last_command_times = {}
MIN_COMMAND_INTERVAL = 0.05  # 50ms minimum between commands per endpoint


def get_robot():
    """Get or initialize the robot control instance"""
    global robot
    if robot is None:
        robot = robot_control.get_robot()
    return robot


def rate_limit_check(endpoint):
    """
    Check if request should be rate limited.
    Returns True if request should proceed, False if rate limited.
    """
    current_time = time.time()
    if endpoint in last_command_times:
        elapsed = current_time - last_command_times[endpoint]
        if elapsed < MIN_COMMAND_INTERVAL:
            return False
    last_command_times[endpoint] = current_time
    return True


def validate_number(value, default=0, min_val=-100, max_val=100):
    """Validate and parse a numeric value"""
    try:
        num = float(value)
        return max(min_val, min(max_val, num))
    except (ValueError, TypeError):
        return default


# ============== Page Routes ==============

@app.route("/")
def index():
    """Serve the main control interface"""
    return render_template("index.html")


# ============== Robot Control API ==============

@app.route("/api/drive", methods=["POST"])
def api_drive():
    """
    Drive control endpoint.
    
    Data Flow:
    1. Browser sends JSON: {left_speed, right_speed} or {x, y} for joystick
    2. Server validates values are numbers in range -100 to 100
    3. Invalid values are rejected or clamped
    4. Valid commands forwarded to robot control layer
    
    Request body (joystick mode):
        {"x": -100 to 100, "y": -100 to 100}
    
    Request body (direct mode):
        {"left_speed": -100 to 100, "right_speed": -100 to 100}
    """
    if not rate_limit_check("drive"):
        return jsonify({"status": "rate_limited"}), 429
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "No data provided"}), 400
        
        r = get_robot()
        
        # Joystick mode (x, y coordinates)
        if "x" in data and "y" in data:
            x = validate_number(data.get("x", 0))
            y = validate_number(data.get("y", 0))
            result = r.drive_joystick(x, y)
        # Direct mode (left/right speeds)
        elif "left_speed" in data or "right_speed" in data:
            left = validate_number(data.get("left_speed", 0))
            right = validate_number(data.get("right_speed", 0))
            result = r.drive(left, right)
        else:
            return jsonify({"status": "error", "message": "Invalid parameters"}), 400
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/head/pan", methods=["POST"])
def api_head_pan():
    """
    Head pan control endpoint.
    
    Request body:
        {"position": -100 to 100}
    """
    if not rate_limit_check("head_pan"):
        return jsonify({"status": "rate_limited"}), 429
    
    try:
        data = request.get_json()
        if not data or "position" not in data:
            return jsonify({"status": "error", "message": "Position required"}), 400
        
        position = validate_number(data.get("position", 0))
        result = get_robot().head_pan(position)
        return jsonify(result)
    
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/head/tilt", methods=["POST"])
def api_head_tilt():
    """
    Head tilt control endpoint.
    
    Request body:
        {"position": -100 to 100}
    """
    if not rate_limit_check("head_tilt"):
        return jsonify({"status": "rate_limited"}), 429
    
    try:
        data = request.get_json()
        if not data or "position" not in data:
            return jsonify({"status": "error", "message": "Position required"}), 400
        
        position = validate_number(data.get("position", 0))
        result = get_robot().head_tilt(position)
        return jsonify(result)
    
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/waist", methods=["POST"])
def api_waist():
    """
    Waist rotation control endpoint.
    
    Request body:
        {"position": -100 to 100}
    """
    if not rate_limit_check("waist"):
        return jsonify({"status": "rate_limited"}), 429
    
    try:
        data = request.get_json()
        if not data or "position" not in data:
            return jsonify({"status": "error", "message": "Position required"}), 400
        
        position = validate_number(data.get("position", 0))
        result = get_robot().waist(position)
        return jsonify(result)
    
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/stop", methods=["POST"])
def api_stop():
    """
    Emergency stop endpoint.
    Sets all motors to neutral/stopped state.
    """
    try:
        result = get_robot().stop()
        return jsonify(result)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/heartbeat", methods=["POST"])
def api_heartbeat():
    """
    Heartbeat endpoint.
    Browser should call this regularly to indicate connection is alive.
    If heartbeat stops, robot will automatically stop for safety.
    """
    try:
        get_robot().heartbeat()
        return jsonify({"status": "ok", "timestamp": time.time()})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/state", methods=["GET"])
def api_state():
    """Get current robot state"""
    try:
        state = get_robot().get_state()
        return jsonify(state)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/speak", methods=["POST"])
def api_speak():
    """
    Voice output endpoint.
    Uses espeak or similar text-to-speech.
    
    Request body:
        {"phrase_index": 0-3} or {"text": "custom text"}
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "No data provided"}), 400
        
        phrases = robot_control.get_phrases()
        
        # Get phrase by index or custom text
        if "phrase_index" in data:
            idx = int(data["phrase_index"])
            if 0 <= idx < len(phrases):
                text = phrases[idx]
            else:
                return jsonify({"status": "error", "message": "Invalid phrase index"}), 400
        elif "text" in data:
            text = str(data["text"])[:200]  # Limit length for safety
        else:
            return jsonify({"status": "error", "message": "phrase_index or text required"}), 400
        
        # Try to speak using espeak (common on Raspberry Pi)
        def speak_async(text):
            try:
                subprocess.run(["espeak", text, " -s", "100"], timeout=10, capture_output=True)
            except FileNotFoundError:
                # espeak not installed, try alternative
                try:
                    subprocess.run(["say", text], timeout=10, capture_output=True)
                except FileNotFoundError:
                    print(f"Speech output (no TTS available): {text}")
            except Exception as e:
                print(f"Speech error: {e}")
        
        # Run speech in background thread to not block
        thread = threading.Thread(target=speak_async, args=(text,))
        thread.start()
        
        return jsonify({"status": "ok", "text": text})
    
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/phrases", methods=["GET"])
def api_phrases():
    """Get list of available phrases"""
    return jsonify({"phrases": robot_control.get_phrases()})


# ============== Dialog Engine API ==============

def get_dialog_engine():
    """Get or create the dialog engine singleton."""
    global _dialog_engine
    if _dialog_engine is None:
        _dialog_engine = de.DialogEngine(robot_control=get_robot())
        if os.path.isfile(DEFAULT_SCRIPT):
            _dialog_engine.load(DEFAULT_SCRIPT)
    return _dialog_engine


@app.route("/api/dialog/input", methods=["POST"])
def api_dialog_input():
    """
    Send user text input to the dialog engine.

    Request body:
        {"text": "user input string"}  (max 500 characters; longer inputs are truncated)

    Response:
        {"response": "robot reply", "action_tags": [...], "matched": bool, "state": "..."}
    """
    try:
        data = request.get_json()
        if not data or "text" not in data:
            return jsonify({"status": "error", "message": "text field required"}), 400

        user_text = str(data["text"])[:500]  # cap length for safety
        engine = get_dialog_engine()
        result = engine.process_input(user_text)

        # Speak the response text asynchronously
        response_text = result.get("response", "")
        if response_text:
            def speak_async(text):
                try:
                    subprocess.run(
                        ["espeak", text, "-s", "130"],
                        timeout=15, capture_output=True
                    )
                except FileNotFoundError:
                    try:
                        subprocess.run(["say", text], timeout=15, capture_output=True)
                    except FileNotFoundError:
                        print(f"Dialog TTS (no TTS): {text}")
                except Exception as e:
                    print(f"Dialog TTS error: {e}")

            threading.Thread(target=speak_async, args=(response_text,), daemon=True).start()

        result["status"] = "ok"
        return jsonify(result)

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/dialog/status", methods=["GET"])
def api_dialog_status():
    """Get current dialog engine status."""
    try:
        engine = get_dialog_engine()
        return jsonify({"status": "ok", **engine.get_status()})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/dialog/load", methods=["POST"])
def api_dialog_load():
    """
    Load a TangoChat script file into the dialog engine.

    Request body:
        {"filename": "path/to/script.txt"}
    """
    try:
        data = request.get_json()
        if not data or "filename" not in data:
            return jsonify({"status": "error", "message": "filename required"}), 400

        filename = str(data["filename"])
        # Restrict to files under the app directory for safety
        app_dir = os.path.dirname(os.path.abspath(__file__))
        abs_path = os.path.abspath(os.path.join(app_dir, filename))
        if not abs_path.startswith(app_dir):
            return jsonify({"status": "error", "message": "Access denied"}), 403

        engine = get_dialog_engine()
        success = engine.load(abs_path)

        errors = [str(e) for e in engine.parse_errors]
        if success:
            return jsonify({
                "status": "ok",
                "loaded": True,
                "rule_count": len(engine.top_rules),
                "errors": errors
            })
        else:
            return jsonify({
                "status": "error",
                "loaded": False,
                "errors": errors
            }), 400

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/dialog/reset", methods=["POST"])
def api_dialog_reset():
    """Reset dialog engine conversation state (variables, scope)."""
    try:
        engine = get_dialog_engine()
        engine.reset()
        return jsonify({"status": "ok", "state": engine.state.value})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# ============== Error Handlers ==============

@app.errorhandler(404)
def not_found(e):
    return jsonify({"status": "error", "message": "Not found"}), 404


@app.errorhandler(500)
def server_error(e):
    # Ensure robot stops on server error
    try:
        get_robot().stop()
    except:
        pass
    return jsonify({"status": "error", "message": "Server error"}), 500


# ============== Startup ==============

if __name__ == "__main__":
    print("=" * 50)
    print("Robot Control Server")
    print("=" * 50)
    print("\nStarting server...")
    print("Access the control interface at:")
    print("  http://localhost:5000/")
    print("  http://<robot-ip>:5000/")
    print("\nPress Ctrl+C to stop the server")
    print("=" * 50)
    
    # Initialize robot before starting server
    get_robot()
    
    # Initialize dialog engine with default script
    get_dialog_engine()
    
    # Run Flask server
    # host='0.0.0.0' allows access from other devices on the network
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)