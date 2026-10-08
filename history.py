"""Workout history: completed workouts with every set as its own row, plus an auto-saved draft of
today's workout so ticks and set entries survive closing the page.

Dates use the Home Assistant time zone (Supervisor passes it to the add-on as TZ), so an evening
workout is logged on the right day.
"""
import datetime
import json
import os
import sqlite3
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

SCHEMA = [
    """CREATE TABLE IF NOT EXISTS workout_sets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        log_id INTEGER,          -- daily_logs.id of the completed workout
        date TEXT,
        exercise TEXT,
        set_number INTEGER,
        weight_lbs REAL,
        reps INTEGER,
        done INTEGER
    )""",
    """CREATE TABLE IF NOT EXISTS workout_drafts (
        date TEXT PRIMARY KEY,   -- local date of the workout in progress
        data JSON,               -- {"tracker": [rows], "checks": {item: bool}}
        updated_at TEXT
    )""",
]


def local_now():
    try:
        tz = ZoneInfo(os.getenv("TZ") or "UTC")
    except ZoneInfoNotFoundError:
        tz = ZoneInfo("UTC")
    return datetime.datetime.now(tz)


def local_today():
    return local_now().date().isoformat()


def ensure_schema(db_path):
    conn = sqlite3.connect(db_path)
    for statement in SCHEMA:
        conn.execute(statement)
    conn.commit()
    conn.close()


# --- Draft of today's workout ---------------------------------------------------------------------

def load_draft(db_path, date=None):
    conn = sqlite3.connect(db_path)
    row = conn.execute("SELECT data FROM workout_drafts WHERE date = ?", (date or local_today(),)).fetchone()
    conn.close()
    return json.loads(row[0]) if row else None


def save_draft(db_path, tracker_rows, checks, date=None):
    conn = sqlite3.connect(db_path)
    conn.execute(
        "INSERT OR REPLACE INTO workout_drafts (date, data, updated_at) VALUES (?, ?, ?)",
        (date or local_today(), json.dumps({"tracker": tracker_rows, "checks": checks}), local_now().isoformat()))
    conn.commit()
    conn.close()


# --- Completed workouts ---------------------------------------------------------------------------

def _number(value, cast):
    try:
        return cast(value) if value not in (None, "") else None
    except (TypeError, ValueError):
        return None


def complete_workout(db_path, rpe, pelvic_floor, kidney, notes, workout, tracker_rows, date=None):
    """Saves the workout and its sets, clears today's draft and returns the new daily_logs id."""
    date = date or local_today()
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute(
        """INSERT INTO daily_logs (date, completed, rpe, pelvic_floor_tightness, kidney_flank_pain, notes, executed_workout)
           VALUES (?, 1, ?, ?, ?, ?, ?)""",
        (date, rpe, pelvic_floor, kidney, notes, json.dumps(workout)))
    log_id = c.lastrowid
    sets = []
    for row in tracker_rows:
        weight, reps, done = _number(row.get("Weight (lbs)"), float), _number(row.get("Reps"), int), bool(row.get("Done"))
        if done or weight or reps:   # skip untouched rows
            sets.append((log_id, date, str(row.get("Exercise") or "").strip(), _number(row.get("Set"), int), weight, reps, int(done)))
    c.executemany(
        "INSERT INTO workout_sets (log_id, date, exercise, set_number, weight_lbs, reps, done) VALUES (?, ?, ?, ?, ?, ?, ?)",
        sets)
    c.execute("DELETE FROM workout_drafts WHERE date = ?", (date,))
    conn.commit()
    conn.close()
    return log_id


def get_history(db_path, limit=60):
    """Completed workouts, newest first, each with its sets."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    logs = [dict(r) for r in conn.execute(
        """SELECT id, date, rpe, pelvic_floor_tightness, kidney_flank_pain, notes, executed_workout
           FROM daily_logs ORDER BY date DESC, id DESC LIMIT ?""", (limit,))]
    sets = {}
    if logs:
        ids = [log["id"] for log in logs]
        for r in conn.execute(
                f"SELECT * FROM workout_sets WHERE log_id IN ({','.join('?' * len(ids))}) ORDER BY id", ids):
            sets.setdefault(r["log_id"], []).append(dict(r))
    conn.close()
    for log in logs:
        try:
            log["workout"] = json.loads(log.pop("executed_workout") or "{}")
        except ValueError:
            log["workout"] = {}
        log["sets"] = sets.get(log["id"], [])
    return logs


def exercise_progress(db_path, exercise):
    """Per workout day for one exercise: heaviest weight, total reps and sets done."""
    conn = sqlite3.connect(db_path)
    rows = conn.execute(
        """SELECT date, MAX(weight_lbs), SUM(reps), SUM(done)
           FROM workout_sets WHERE exercise = ? GROUP BY date ORDER BY date""", (exercise,)).fetchall()
    conn.close()
    return [{"date": d, "top_weight_lbs": w or 0, "total_reps": r or 0, "sets_done": s or 0} for d, w, r, s in rows]


def logged_exercises(db_path):
    conn = sqlite3.connect(db_path)
    names = [r[0] for r in conn.execute(
        "SELECT exercise FROM workout_sets WHERE exercise != '' GROUP BY exercise ORDER BY COUNT(*) DESC")]
    conn.close()
    return names
