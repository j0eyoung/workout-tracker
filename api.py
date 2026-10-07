from fastapi import FastAPI
from pydantic import BaseModel
from engine import WorkoutEngine
from db import DB_PATH
import sqlite3

app = FastAPI(title="AI Workout API", description="API for Claude Terminal to control HA Workouts")
engine = WorkoutEngine()

class SymptomLog(BaseModel):
    rpe: int
    pelvic_floor_tightness: int
    kidney_flank_pain: int
    notes: str = ""

@app.get("/workout/today")
def get_todays_workout():
    """Claude Terminal can call this to see what Joe is supposed to do today."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT pelvic_floor_tightness, kidney_flank_pain FROM daily_logs ORDER BY id DESC LIMIT 1")
    row = c.fetchone()
    conn.close()
    
    last_log = {"pelvic_floor_tightness": row[0], "kidney_flank_pain": row[1]} if row else {}
    return engine.generate_next_workout(last_log)

@app.post("/workout/log")
def log_symptoms(log: SymptomLog):
    """Claude Terminal can call this to log Joe's symptoms and force the engine to adapt."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT INTO daily_logs (date, completed, rpe, pelvic_floor_tightness, kidney_flank_pain, notes, executed_workout)
        VALUES (date('now'), 1, ?, ?, ?, ?, ?)
    """, (log.rpe, log.pelvic_floor_tightness, log.kidney_flank_pain, log.notes, "{}"))
    conn.commit()
    conn.close()
    return {"status": "success", "message": "Symptoms logged. Tomorrow's workout has been auto-regulated."}
