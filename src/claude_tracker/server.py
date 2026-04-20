from flask import Flask, jsonify, render_template, request

from claude_tracker import db

app = Flask(__name__)


def _days() -> int:
    try:
        v = int(request.args.get("days", 30))
        return v if v > 0 else 0  # 0 means all time
    except (TypeError, ValueError):
        return 30


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/summary")
def api_summary():
    return jsonify(db.query_summary(_days()))


@app.get("/api/daily")
def api_daily():
    return jsonify(db.query_daily(_days()))


@app.get("/api/hourly")
def api_hourly():
    date = request.args.get("date")
    if date:
        return jsonify(db.query_hourly_for_date(date))
    return jsonify(db.query_hourly(_days()))


@app.get("/api/git-activity")
def api_git_activity():
    date = request.args.get("date")
    if not date:
        return jsonify({"error": "date parameter required"}), 400
    try:
        hour = int(request.args.get("hour")) if request.args.get("hour") is not None else None
    except (TypeError, ValueError):
        hour = None

    paths = db.query_projects_for_date(date)
    from claude_tracker.git_activity import get_git_activity
    return jsonify(get_git_activity(paths, date, hour))


@app.get("/api/projects")
def api_projects():
    return jsonify(db.query_projects(_days()))


@app.get("/api/models")
def api_models():
    return jsonify(db.query_models(_days()))


@app.post("/api/sync")
def api_sync():
    from claude_tracker.collector import collect
    n = collect()
    return jsonify({"files_processed": n})


def run(host: str = "127.0.0.1", port: int = 5555, debug: bool = False):
    app.run(host=host, port=port, debug=debug)
