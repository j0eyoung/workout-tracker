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
import garmin_sync
import history
import library
import media
import meditation
import mindbody
import ninjas_sync
import planedit
import planner
import progression
import tts
from db import DB_PATH, get_last_log
from engine import WorkoutEngine
from exercises import CARDIO_IMAGES, GUIDES

HERE = os.path.dirname(os.path.abspath(__file__))
VERSION = "0.5.0"

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


SPORT_OPTIONS = [("skiing", "Skiing"), ("snowboarding", "Snowboarding"), ("triathlon", "Triathlon")]


def selected_sports():
    chosen = library.load_settings().get("sports")
    return chosen if chosen is not None else ["skiing", "snowboarding", "triathlon"]


def _generate(date_iso):
    """The engine's workout for a date, following that day's place in the weekly plan."""
    goals = selected_sports()
    d = datetime.date.fromisoformat(date_iso)
    day = planner.day_plan(d, goals)
    w = engine.generate_next_workout(
        get_last_log(), today=d, library=get_library()["entries"], equipment=library.selected_equipment(),
        goals=goals, focus=day["focus"], cardio_type=day["cardio_type"], theme=day["theme"])
    if day["phase"] == "Easy week" and day["focus"] == "strength" and w.get("accessories"):
        last = w["accessories"].pop()          # easy week: one fewer extra
        if last["name"] in w["strength"]:
            w["strength"].remove(last["name"])
    if day.get("cardio_minutes") and w.get("cardio_type") != "recovery":
        # minutes the coach put in the week: never more than 10 above what progression allows
        minutes = min(int(day["cardio_minutes"]), (w.get("cardio_minutes") or 0) + 10)
        w = planedit.apply(w, [{"op": "cardio", "type": w["cardio_type"], "minutes": minutes, "why": "weekly plan"}])
    return w


def todays_workout():
    today = history.local_today()
    return planedit.apply(_generate(today), planedit.overrides_for(today))


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


def with_progress(card, last, phase):
    """Adds last time's sets and a suggested weight and reps to an exercise card."""
    date, sets = history.last_session(DB_PATH, card["name"])
    card["progress"] = progression.suggest(date, sets, phase, last.get("rpe"), last.get("kidney_flank_pain"),
                                           last.get("pelvic_floor_tightness"))
    return card


@app.get("/api/plan")
def plan():
    today = history.local_today()
    w = todays_workout()
    why = {a["name"]: a["why"] for a in w.get("accessories", [])}
    draft = history.load_draft(DB_PATH, today) or {}
    last = get_last_log()
    kidney, pf = last.get("kidney_flank_pain"), last.get("pelvic_floor_tightness")
    phase = planner.phase(datetime.date.fromisoformat(today))
    return {
        "phase": phase,
        "coach_changes": len(planedit.overrides_for(today)),
        "cooldown": {"note": mindbody.cooldown_note(kidney, pf), "cards": mindbody.cooldown(kidney, pf)},
        "date": today,
        "warmup": [how_to(n) for n in w["warmup"]],
        "strength": [with_progress(how_to(n, why.get(n)), last, phase) for n in w["strength"]],
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
    plan = todays_workout()
    lib = get_library()
    today = datetime.date.fromisoformat(history.local_today())
    context = "\n\n".join([planedit.INSTRUCTIONS, planedit.context(plan, lib["entries"], library.selected_equipment(), selected_sports()),
                           planedit.week_context(today, selected_sports())])
    reply, error = coach.ask(m.message, m.recent, plan_context=context,
                             season=library.load_settings().get("season_start", ""), sports=selected_sports())
    reply, data = planedit.extract(reply)
    ops = (data or {}).get("changes") or []
    changes, rejected = planedit.validate({"changes": [c for c in ops if c.get("op") != "day"]}, plan, lib["by_name"],
                                          library.selected_equipment())
    days, days_bad = planedit.validate_days([c for c in ops if c.get("op") == "day"], today, selected_sports())
    return {"reply": reply, "error": error, "rejected": rejected + days_bad,
            "changes": [dict(c, label=planedit.label(c)) for c in changes + days]}


class PlanChanges(BaseModel):
    changes: list[dict]


@app.post("/api/plan/changes")
def apply_changes(p: PlanChanges):
    """Joe approved the coach's changes. Checked again here, so only valid ones are ever saved."""
    lib = get_library()
    today = history.local_today()
    plan = planedit.apply(_generate(today), planedit.overrides_for(today))
    day_ops = [c for c in p.changes if c.get("op") == "day"]
    allowed, rejected = planedit.validate({"changes": [c for c in p.changes if c.get("op") != "day"]}, plan,
                                          lib["by_name"], library.selected_equipment())
    days_ok, days_bad = planedit.validate_days(day_ops, datetime.date.fromisoformat(today), selected_sports())
    if allowed:
        planedit.save(today, allowed)
    if days_ok:
        planner.save_changes(days_ok)
    return {"ok": True, "applied": len(allowed) + len(days_ok), "rejected": rejected + days_bad}


@app.get("/api/week")
def get_week(offset: int = 0):
    """The week (Monday to Sunday). offset 0 = this week, 1 = next week."""
    today = datetime.date.fromisoformat(history.local_today())
    start = planner.monday(today) + datetime.timedelta(days=7 * max(-1, min(offset, 2)))
    goals = selected_sports()
    done = {w["date"] for w in history.get_history(DB_PATH, 60)}
    days = planner.week(start, today, goals, done)
    for day in days:
        if day["status"] in ("today", "upcoming") and day["focus"] in ("strength", "cardio"):
            w = _generate(day["date"])
            day["strength"] = [n for n in w["strength"]] if day["focus"] == "strength" else []
            day["cardio_text"] = f"{w['cardio_minutes']} min {w['cardio_type']}" if day["focus"] != "rest" else None
    season = library.load_settings().get("season_start") or ""
    weeks_left = None
    if season:
        try:
            weeks_left = max(0, (datetime.date.fromisoformat(season) - today).days // 7)
        except ValueError:
            pass
    return {"start": start.isoformat(), "offset": offset, "days": days, "sports": goals, "phase": planner.phase(start),
            "season_start": season, "weeks_to_season": weeks_left}


@app.post("/api/week/reset")
def reset_week():
    planner.clear_week(planner.monday(datetime.date.fromisoformat(history.local_today())))
    return {"ok": True}


@app.post("/api/plan/reset")
def reset_changes():
    planedit.clear(history.local_today())
    return {"ok": True}


@app.on_event("startup")
def _start_garmin_sync():
    garmin_sync.start_background(history.local_today)


@app.get("/api/garmin")
def garmin_state():
    return garmin_sync.status()


class GarminLogin(BaseModel):
    email: str
    password: str


@app.post("/api/garmin/connect")
def garmin_connect(g: GarminLogin):
    result = garmin_sync.connect(g.email, g.password)
    if result["ok"] and not result["needs_mfa"]:
        garmin_sync.sync(datetime.date.fromisoformat(history.local_today()))
    return {**result, **garmin_sync.status()}


class GarminCode(BaseModel):
    code: str


@app.post("/api/garmin/mfa")
def garmin_mfa(c: GarminCode):
    result = garmin_sync.submit_mfa(c.code)
    if result["ok"]:
        garmin_sync.sync(datetime.date.fromisoformat(history.local_today()))
    return {**result, **garmin_sync.status()}


@app.post("/api/garmin/sync")
def garmin_sync_now():
    ok, message = garmin_sync.sync(datetime.date.fromisoformat(history.local_today()))
    return {"ok": ok, "message": message, **garmin_sync.status()}


@app.post("/api/garmin/disconnect")
def garmin_disconnect():
    garmin_sync.disconnect()
    return garmin_sync.status()


@app.post("/api/media/test")
def media_test():
    return media.test()


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


@app.get("/api/voices")
def voices():
    return {"voices": tts.catalog(), "selected": library.load_settings().get("voice", tts.DEFAULT_VOICE)}


class TTSRequest(BaseModel):
    voice: str = tts.DEFAULT_VOICE
    text: str = ""
    preview: bool = False


@app.post("/api/tts")
def make_audio(r: TTSRequest):
    text = tts.PREVIEW_TEXT if r.preview else r.text.strip()[:12000]
    if not text:
        raise HTTPException(400, "Nothing to read")
    return tts.public(tts.start(r.voice, text))


@app.get("/api/tts/{key}")
def audio_status(key: str):
    job = tts.status(key)
    if not job:
        raise HTTPException(404, "Unknown audio")
    return tts.public(job)


@app.get("/api/tts/{key}/audio")
def audio_file(key: str):
    job = tts.status(key)
    if not job or job["status"] != "ready":
        raise HTTPException(404, "Audio isn't ready")
    return FileResponse(job["path"], media_type="audio/wav", headers={"Cache-Control": "private, max-age=86400"})


@app.get("/api/settings")
def get_settings():
    return {"equipment": library.selected_equipment(), "equipment_options": library.EQUIPMENT_OPTIONS,
            "media_base_url": library.load_settings().get("media_base_url", ""), "media_private": media.configured(),
            "sports": selected_sports(), "sport_options": [{"id": i, "label": l} for i, l in SPORT_OPTIONS],
            "season_start": library.load_settings().get("season_start", ""),
            "gear_notes": library.load_settings().get("gear_notes", library.DEFAULT_GEAR_NOTES)}


class Settings(BaseModel):
    equipment: list[str] | None = None
    gear_notes: str | None = None
    media_base_url: str | None = None
    voice: str | None = None
    sports: list[str] | None = None
    season_start: str | None = None


@app.put("/api/settings")
def put_settings(s: Settings):
    patch = {}
    if s.equipment is not None:
        # "bodyweight" is always available; unknown names are dropped
        patch["equipment"] = sorted({e for e in s.equipment if e in library.EQUIPMENT_OPTIONS} | {"bodyweight"})
    if s.gear_notes is not None:
        patch["gear_notes"] = s.gear_notes.strip()[:2000]
    if s.sports is not None:
        patch["sports"] = [x for x, _ in SPORT_OPTIONS if x in s.sports]
    if s.season_start is not None:
        try:
            patch["season_start"] = datetime.date.fromisoformat(s.season_start).isoformat() if s.season_start else ""
        except ValueError:
            raise HTTPException(400, "The season date must look like 2026-12-01")
    if s.voice is not None and s.voice in tts.VOICES:
        patch["voice"] = s.voice
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
