from flask import Flask, render_template, request, jsonify
import json
import datetime
import os

app = Flask(__name__)

LOG_FILE   = "pomodoro_log.json"
TASKS_FILE = "tasks.json"

# Settings
WORK_MINUTES         = 25
SHORT_BREAK_MINUTES  = 5
LONG_BREAK_MINUTES   = 15
LUNCH_BREAK_MINUTES  = 60
POMODOROS_PER_TASK   = 4


# --- Session log helpers ---

def load_log():
    try:
        with open(LOG_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def save_log(log):
    with open(LOG_FILE, "w") as f:
        json.dump(log, f, indent=2)


# --- Task list helpers ---

def load_tasks():
    try:
        with open(TASKS_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"date": None, "tasks": [], "carryover": []}

def save_tasks(data):
    with open(TASKS_FILE, "w") as f:
        json.dump(data, f, indent=2)


# --- Routes ---

@app.route("/")
def index():
    return render_template("index.html",
                           work=WORK_MINUTES,
                           short_break=SHORT_BREAK_MINUTES,
                           long_break=LONG_BREAK_MINUTES,
                           lunch_break=LUNCH_BREAK_MINUTES,
                           pomodoros_per_task=POMODOROS_PER_TASK)


@app.route("/tasks", methods=["GET"])
def get_tasks():
    """Return any carryover tasks from yesterday to pre-fill the morning form."""
    data = load_tasks()
    return jsonify({"carryover": data.get("carryover", [])})


@app.route("/tasks", methods=["POST"])
def set_tasks():
    """Save today's task list when the user clicks Start Day."""
    data_in = request.get_json()
    today   = datetime.date.today().strftime("%Y-%m-%d")

    tasks_data = {
        "date":     today,
        "tasks":    [{"name": n, "completed": None, "extra_minutes": None}
                     for n in data_in["tasks"]],
        "carryover": []   # rebuilt during the day as tasks finish
    }
    save_tasks(tasks_data)
    return jsonify({"status": "ok"})


@app.route("/task-complete", methods=["POST"])
def task_complete():
    """Record whether a task was finished and save carryover if not."""
    data_in      = request.get_json()
    idx          = data_in["task_index"]
    completed    = data_in["completed"]
    extra_minutes = data_in.get("extra_minutes", 0)

    tasks_data = load_tasks()

    if 0 <= idx < len(tasks_data["tasks"]):
        tasks_data["tasks"][idx]["completed"]     = completed
        tasks_data["tasks"][idx]["extra_minutes"] = extra_minutes

        if not completed:
            # Add to carryover queue for tomorrow
            tasks_data["carryover"].append({
                "name":          tasks_data["tasks"][idx]["name"],
                "extra_minutes": extra_minutes
            })

    save_tasks(tasks_data)
    return jsonify({"status": "ok"})


@app.route("/log", methods=["POST"])
def log_session():
    data = request.get_json()
    log  = load_log()
    log.append({
        "date":  data["date"],
        "cycle": data["cycle"],
        "start": data["start"],
        "end":   data["end"],
    })
    save_log(log)
    return jsonify({"status": "ok", "total_today": sum(
        1 for e in log if e["date"] == data["date"]
    )})


@app.route("/summary")
def summary():
    log   = load_log()
    today = datetime.date.today().strftime("%Y-%m-%d")
    todays  = [e for e in log if e["date"] == today]
    total   = len(todays)
    minutes = total * WORK_MINUTES
    return jsonify({
        "date":      today,
        "total":     total,
        "minutes":   minutes,
        "hours":     minutes // 60,
        "remainder": minutes % 60,
        "sessions":  todays,
    })


if __name__ == "__main__":
    print("Starting Pomodoro server...")
    print("Open on this Mac:   http://localhost:5001")
    print("Find your Mac's IP: ipconfig getifaddr en0")
    app.run(host="0.0.0.0", port=5001, debug=True)
