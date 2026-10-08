"""Add-on web server: the phone-first UI in static/ and the JSON API behind it, plus the
/workout endpoints Claude Terminal uses.

The UI is served through Home Assistant ingress under a per-install path prefix, so the
page only ever uses relative URLs (e.g. fetch("api/plan")).
"""
import datetime
import os
import sqlite3
import threading
import time

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import coach
import history
import library
import media
import meditation
import mindbody
import ninjas_sync
from db import DB_PATH, get_last_log
from engine import WorkoutEngine
from exercises import CARDIO_IMAGES, GUIDES

HERE = os.path.dirname(os.path.abspath(__file__))
VERSION = "0.3.4"

app = FastAPI(title="AI Workout Tracker")
app.mount("/static", StaticFiles(directory=os.path.join(HERE, "static")), name="static")
engine = WorkoutEngine()

# --- Exercise library (kept in memory; refreshed so background API Ninjas additions show up) ----

_library = {"loaded_at": 0.0, "entries": [], "by_name": {}}
_library_lock = threading.Lock()


def get_library():
    with _library_lock:
        if time.time() - _library["loaded_at"] > 600:
            entries = library.get_library(DB_PATH)
            _library.update(loaded_at=time.time(), entries=entries, by_name={e["name"]: e for e in entries})
    return _library


def library_card(e, why=None):
    similar = (e["image_match"] or "").startswith("similar")
    dose, sets = library.dose_for(e)
    return {
        "name": e["name"], "dose": dose, "sets": sets, "why": why,
        "images": e["images"], "image_note": f"Picture shows a similar movement ({e['image_match'][9:]})." if similar else None,
        "steps": e["instructions"], "tips": e["tips"], "safe": e["safe"],
        "warning": None if e["safe"] else
        "Filtered out of your plans: " + "; ".join(library.FLAG_REASONS.get(f, f) for f in e["constraint_tags"]) + ".",
        "muscles": e["muscles"], "equipment": e["equipment"], "level": e["level"],
        "sources": [library.SOURCE_NAMES.get(s, s) for s in e["sources"]],
    }


def how_to(name, why=None):
    """Dose, pictures and steps for an exercise in today's plan."""
    guide = GUIDES.get(name)
    if guide:
        return {"name": name, "dose": guide["dose"], "sets": guide.get("sets", 3), "why": why,
                "images": guide.get("images", []), "image_note": guide.get("image_note"),
                "steps": guide["cues"], "tips": [], "safe": True, "warning": None}
    entry = get_library()["by_name"].get(name)
    if entry:
        return library_card(entry, why)
    return {"name": name, "dose": None, "sets": 3, "why": why, "images": [], "image_note": None,
            "steps": [], "tips": [], "safe": True, "warning": None}


def todays_workout():
    return engine.generate_next_workout(
        get_last_log(), today=datetime.date.fromisoformat(history.local_today()),
        library=get_library()["entries"], equipment=library.selected_equipment())


# --- Draft rows: the page uses {exercise, set, weight, reps, done}; 0.2.x drafts used table headers ---

def _page_row(r):
    if "exercise" in r:
        return r
    return {"exercise": r.get("Exercise"), "set": r.get("Set"), "weight": r.get("Weight (lbs)"),
            "reps": r.get("Reps"), "done": bool(r.get("Done"))}


def _history_row(r):
    return {"Exercise": r.get("exercise"), "Set": r.get("set"), "Weight (lbs)": r.get("weight"),
            "Reps": r.get("reps"), "Done": bool(r.get("done"))}


# --- Pages and API ---------------------------------------------------------------------------------

@app.get("/")
def index():
    return FileResponse(os.path.join(HERE, "static", "index.html"), headers={"Cache-Control": "no-cache"})


@app.get("/api/plan")
def plan():
    today = history.local_today()
    w = todays_workout()
    why = {a["name"]: a["why"] for a in w.get("accessories", [])}
    draft = history.load_draft(DB_PATH, today) or {}
    last = get_last_log()
    kidney, pf = last.get("kidney_flank_pain"), last.get("pelvic_floor_tightness")
    return {
        "cooldown": {"note": mindbody.cooldown_note(kidney, pf), "cards": mindbody.cooldown(kidney, pf)},
        "date": today,
        "warmup": [how_to(n) for n in w["warmup"]],
        "strength": [how_to(n, why.get(n)) for n in w["strength"]],
        "cardio": {"text": w["cardio"], "minutes": w.get("cardio_minutes"), "note": w.get("cardio_note"),
                   "type": w.get("cardio_type"), "images": CARDIO_IMAGES.get(w.get("cardio_type"), [])},
        "draft": {"tracker": [_page_row(r) for r in draft.get("tracker", [])], "checks": draft.get("checks", {})},
    }


class Draft(BaseModel):
    date: str
    tracker: list[dict] = []
    checks: dict[str, bool] = {}


@app.put("/api/draft")
def save_draft(d: Draft):
    if d.date != history.local_today():
        raise HTTPException(409, "A new day has started; reload the plan.")
    history.save_draft(DB_PATH, d.tracker, d.checks, d.date)
    return {"ok": True}


class Completion(BaseModel):
    rpe: int
    pelvic_floor: int
    kidney: int
    notes: str = ""
    tracker: list[dict] = []


@app.post("/api/complete")
def complete(c: Completion):
    log_id = history.complete_workout(DB_PATH, c.rpe, c.pelvic_floor, c.kidney, c.notes, todays_workout(),
                                      [_history_row(r) for r in c.tracker])
    return {"ok": True, "log_id": log_id}


@app.get("/api/history")
def workout_history(limit: int = 60):
    return {"workouts": history.get_history(DB_PATH, limit), "exercises": history.logged_exercises(DB_PATH)}


@app.get("/api/progress")
def progress(exercise: str):
    return {"exercise": exercise, "days": history.exercise_progress(DB_PATH, exercise)}


@app.get("/api/library")
def search_library(q: str = "", focus: str = "", muscle: str = "", equipment: str = "",
                   pictures: bool = True, filtered: bool = False, offset: int = 0, limit: int = 25):
    entries = get_library()["entries"]
    words = q.lower().split()
    results = [
        e for e in entries
        if (filtered or e["safe"]) and (not pictures or e["images"])
        and all(w in e["name"].lower() for w in words)
        and (not focus or focus in e["goal_tags"])
        and (not muscle or muscle in e["muscles"])
        and (not equipment or e["equipment"] == equipment)
    ]
    return {
        "total": len(results), "all": len(entries), "safe": sum(e["safe"] for e in entries),
        "results": [library_card(e) for e in results[offset:offset + limit]],
        "muscles": sorted({m for e in entries for m in e["muscles"]}),
        "equipment": sorted({e["equipment"] for e in entries}),
    }


@app.get("/api/status")
def status():
    return {"version": VERSION, "claude_token": coach.has_token(), "ninjas": ninjas_sync.status(),
            "credits": library.CREDITS}


class CoachMessage(BaseModel):
    message: str
    recent: list[dict] = []


@app.post("/api/coach")
def ask_coach(m: CoachMessage):
    reply, error = coach.ask(m.message, m.recent)
    return {"reply": reply, "error": error}


@app.get("/api/media/yoga/{name}")
def yoga_picture(name: str):
    """A yoga picture from the private B2 bucket (cached on first use)."""
    try:
        path = media.get(name)
    except FileNotFoundError:
        raise HTTPException(404, "No such picture")
    except Exception as e:
        raise HTTPException(502, f"Couldn't load the picture: {e}")
    return FileResponse(path, media_type="image/jpeg", headers={"Cache-Control": "public, max-age=2592000"})


@app.get("/api/mindbody")
def mind_body():
    return mindbody.cards()


@app.get("/api/meditation")
def meditation_library():
    items, error = meditation.practices()
    return {"practices": items, "error": error, "credit": meditation.CREDIT,
            "categories": [{"id": c, "label": meditation.LABELS.get(c, c.title())}
                           for c in sorted({p["category"] for p in items})]}


class ScriptRequest(BaseModel):
    minutes: int = 5
    focus: str = ""


@app.post("/api/meditation/script")
def meditation_script(r: ScriptRequest):
    script, error = coach.meditation_script(max(2, min(r.minutes, 15)), r.focus)
    return {"script": script, "error": error}


@app.get("/api/settings")
def get_settings():
    return {"equipment": library.selected_equipment(), "equipment_options": library.EQUIPMENT_OPTIONS,
            "media_base_url": library.load_settings().get("media_base_url", ""), "media_private": media.configured(),
            "gear_notes": library.load_settings().get("gear_notes", library.DEFAULT_GEAR_NOTES)}


class Settings(BaseModel):
    equipment: list[str] | None = None
    gear_notes: str | None = None
    media_base_url: str | None = None


@app.put("/api/settings")
def put_settings(s: Settings):
    patch = {}
    if s.equipment is not None:
        # "bodyweight" is always available; unknown names are dropped
        patch["equipment"] = sorted({e for e in s.equipment if e in library.EQUIPMENT_OPTIONS} | {"bodyweight"})
    if s.gear_notes is not None:
        patch["gear_notes"] = s.gear_notes.strip()[:2000]
    if s.media_base_url is not None:
        url = s.media_base_url.strip().rstrip("/")
        if url and not url.startswith("https://"):
            raise HTTPException(400, "The media address must start with https://")
        patch["media_base_url"] = url
    if patch:
        library.save_settings(patch)
    return get_settings()


@app.get("/api/claude")
def claude_state():
    return coach.login_state()


@app.post("/api/claude/login")
def claude_login():
    return coach.start_login()


class LoginCode(BaseModel):
    code: str


@app.post("/api/claude/code")
def claude_code(c: LoginCode):
    return coach.send_code(c.code)


@app.post("/api/claude/cancel")
def claude_cancel():
    return coach.cancel_login()


@app.post("/api/claude/logout")
def claude_logout():
    coach.logout()
    return coach.login_state()


@app.post("/api/report")
def make_report():
    _, error = coach.report()
    return {"ok": error is None, "error": error, "path": "/config/workout_tracker/progress_report.html"}


# --- Claude Terminal endpoints (unchanged from 0.1.x) ----------------------------------------------

class SymptomLog(BaseModel):
    rpe: int
    pelvic_floor_tightness: int
    kidney_flank_pain: int
    notes: str = ""


@app.get("/workout/today")
def get_todays_workout():
    """Claude Terminal can call this to see what Joe is supposed to do today."""
    return todays_workout()


@app.post("/workout/log")
def log_symptoms(log: SymptomLog):
    """Claude Terminal can call this to log Joe's symptoms and force the engine to adapt."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        INSERT INTO daily_logs (date, completed, rpe, pelvic_floor_tightness, kidney_flank_pain, notes, executed_workout)
        VALUES (?, 1, ?, ?, ?, ?, ?)
    """, (history.local_today(), log.rpe, log.pelvic_floor_tightness, log.kidney_flank_pain, log.notes, "{}"))
    conn.commit()
    conn.close()
    return {"status": "success", "message": "Symptoms logged. Tomorrow's workout has been auto-regulated."}
