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
import os
import threading

from services.text_to_speech import TextToSpeech, get_default_phrases
from services.DialogEngine import DialogEngine
from ActionRunner import ActionRunner

app = Flask(__name__)
CORS(app)  # Enable CORS for local network access

# Initialize robot control (will use mock mode if hardware not available)
robot = None

# Initialize text-to-speech service
tts = TextToSpeech()

# Dialog engine and action runner (initialized lazily)
_dialog_engine = None
_action_runner = None
_dialog_lock = threading.Lock()

#_lidar = None
#_lidar_lock = threading.Lock()

# Default script path (relative to app.py location)
_DEFAULT_SCRIPT = os.path.join(os.path.dirname(__file__), "testDialogFileForPractice.txt")

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


@app.route("/api/wallFollow", methods=["POST"])
def api_wallFollow():

    try:
        result = get_robot().wallFollow()
        return jsonify(result)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/wallFollowMode", methods=["POST"])
def api_wallFollowMode():

    try:
        data = request.get_json()
        if not data or "on" not in data:
            return jsonify({"status": "error", "message": "Position required"}), 400

        on = data.get("on", False)
        direction = data.get("mode", False)

        result = get_robot().wallFollowMode(on, direction)
        return jsonify(result)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/guide", methods=["POST"])
def api_guide():

    try:
        result = get_robot().guide()
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
    Uses the TextToSpeech service for espeak or similar text-to-speech.
    
    Request body:
        {"phrase_index": 0-3} or {"text": "custom text"}
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "No data provided"}), 400
        
        phrases = get_default_phrases()
        
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
        
        # Use the text-to-speech service
        result = tts.speak(text, async_mode=True)
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/phrases", methods=["GET"])
def api_phrases():
    """Get list of available phrases"""
    return jsonify({"phrases": get_default_phrases()})


def get_dialog_engine(script_path=None):
    """Get or initialize the dialog engine singleton."""
    global _dialog_engine, _action_runner
    with _dialog_lock:
        if _dialog_engine is None or script_path is not None:
            engine = DialogEngine()
            path = script_path or _DEFAULT_SCRIPT
            if engine.load_script(path):
                _dialog_engine = engine
                _action_runner = ActionRunner(get_robot())
            else:
                return None, None
        return _dialog_engine, _action_runner


# ============== Dialog API ==============

@app.route("/api/dialog", methods=["POST"])
def api_dialog():
    """
    Dialog endpoint — accepts typed user input, processes it through the
    dialog engine, speaks the response, and triggers robot actions.

    Request body:
        {"text": "user input string"}
        {"text": "...", "script": "/path/to/script.bot"}  # optional reload

    Response:
        {"status": "ok", "response": "robot reply", "actions": [...]}
        {"status": "no_match", "response": null}
    """
    try:
        data = request.get_json()
        if not data or "text" not in data:
            return jsonify({"status": "error", "message": "text field required"}), 400

        user_text = str(data["text"]).strip()
        if not user_text:
            return jsonify({"status": "error", "message": "text must not be empty"}), 400

        script_path = data.get("script")
        engine, runner = get_dialog_engine(script_path)
        if engine is None:
            return jsonify({"status": "error",
                            "message": "Dialog engine failed to load script"}), 500

        response, actions = engine.process_input(user_text)

        # Global interrupt — stop wheels and cancel any running actions
        if engine.was_interrupted():
            if runner:
                runner.cancel()

        if response is None:
            return jsonify({"status": "no_match", "response": None, "actions": []})

        # Speak the response asynchronously
        tts.speak(response, async_mode=True)

        # Run actions in a background thread so the HTTP response returns quickly
        if actions and runner:
            threading.Thread(target=runner.run_actions, args=(actions,),
                             daemon=True).start()

        return jsonify({
            "status": "ok",
            "response": response,
            "actions": actions,
        })

    except Exception as exc:
        return jsonify({"status": "error", "message": str(exc)}), 500


@app.route("/api/dialog/reset", methods=["POST"])
def api_dialog_reset():
    """Reset dialog engine conversational state (variables and scope)."""
    try:
        engine, _ = get_dialog_engine()
        if engine:
            engine.reset()
        return jsonify({"status": "ok"})
    except Exception as exc:
        return jsonify({"status": "error", "message": str(exc)}), 500


@app.route("/api/dialog/load", methods=["POST"])
def api_dialog_load():
    """
    (Re)load a dialog script.

    Request body:
        {"script": "/path/to/script.bot"}
    """
    try:
        data = request.get_json()
        if not data or "script" not in data:
            return jsonify({"status": "error", "message": "script field required"}), 400

        engine, _ = get_dialog_engine(str(data["script"]))
        if engine is None:
            return jsonify({"status": "error", "message": "Failed to load script"}), 500
        return jsonify({"status": "ok"})
    except Exception as exc:
        return jsonify({"status": "error", "message": str(exc)}), 500


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
    
    # Run Flask server
    # host='0.0.0.0' allows access from other devices on the network
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)