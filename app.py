from flask import Flask, render_template, request, jsonify
import json
import datetime
import os

app = Flask(__name__)   # create the Flask app; __name__ tells Flask where to find templates

LOG_FILE = "pomodoro_log.json"

# Settings — same defaults as the CLI version
WORK_MINUTES        = 25
SHORT_BREAK_MINUTES = 5
LONG_BREAK_MINUTES  = 15
CYCLES_BEFORE_LONG  = 4


# --- Helper functions (same logic as pomodoro.py) ---

def load_log():
    try:
        with open(LOG_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def save_log(log):
    with open(LOG_FILE, "w") as f:
        json.dump(log, f, indent=2)


# --- Routes ---
# A "route" maps a URL to a Python function.
# When someone visits that URL, Flask calls the function and returns what it gives back.

@app.route("/")
def index():
    """Serve the main timer page. Pass settings to the template."""
    return render_template("index.html",
                           work=WORK_MINUTES,
                           short_break=SHORT_BREAK_MINUTES,
                           long_break=LONG_BREAK_MINUTES,
                           cycles_before_long=CYCLES_BEFORE_LONG)


@app.route("/log", methods=["POST"])
def log_session():
    """Receive a completed work session from the browser and save it."""
    data = request.get_json()   # read the JSON the browser sent

    log = load_log()
    entry = {
        "date":  data["date"],
        "cycle": data["cycle"],
        "start": data["start"],
        "end":   data["end"],
    }
    log.append(entry)
    save_log(log)

    return jsonify({"status": "ok", "total_today": sum(
        1 for e in log if e["date"] == data["date"]
    )})


@app.route("/summary")
def summary():
    """Return today's session summary as JSON."""
    log = load_log()
    today = datetime.date.today().strftime("%Y-%m-%d")
    todays = [e for e in log if e["date"] == today]
    total = len(todays)
    minutes = total * WORK_MINUTES

    return jsonify({
        "date":     today,
        "total":    total,
        "minutes":  minutes,
        "hours":    minutes // 60,
        "remainder": minutes % 60,
        "sessions": todays,
    })


# --- Start the server ---
if __name__ == "__main__":
    # host="0.0.0.0" makes the server reachable from your iPhone on the same WiFi
    # debug=True auto-reloads when you save changes
    print("Starting Pomodoro server...")
    print("Open on this Mac:   http://localhost:5000")
    print("Find your Mac's IP with: ipconfig getifaddr en0")
    app.run(host="0.0.0.0", port=5000, debug=True)
