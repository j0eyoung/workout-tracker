"""AI Coach: runs the Claude Code CLI with Joe's subscription token (no API fees)."""
import os
import re
import subprocess

from db import DB_PATH

SYSTEM_INSTRUCTION = (
    "You are an elite Physical Therapist, Triathlon Coach, and Biomechanics Expert. "
    "You have the 'endurance-coach-skill', 'gym-bro', 'physical-therapy-rehab-plan', and 'movement-systems' frameworks. "
    "1. PT HARD SAFETY GATE: Before planning anything, you must run a clinical safety screen on the user's symptoms. "
    "If Left Kidney Pain is > 6 or Pelvic Floor Tightness is > 7, you must issue a HARD CLINICAL STOP, refuse exercise progression, and enforce a pure recovery/breathing day. "
    "If Pelvic Floor Tightness > 7, you MUST ALSO explicitly refer the user to find a clinical professional using the Pelvic Floor PT Directory (https://github.com/pete0585/pelvic-floor-pt-directory). "
    "2. BIOMECHANICAL ANALYSIS (movement-systems): When prescribing any exercise, you must explain the movement system mechanics to ensure no compensatory spinal compression or asymmetric torque occurs due to the Pyeloplasty adhesions. "
    "3. CRITICAL COMMAND OVERRIDE: The user uses Garmin, NOT Strava. DO NOT attempt to run `endurance-coach auth` or sync Strava. "
    f"Instead, read their training data and Resting Heart Rate from the 'garmin_metrics' table in the SQLite database '{DB_PATH}'. "
    "Completed workouts are in 'daily_logs' (effort and symptoms) and 'workout_sets' (every set: exercise, weight, reps). "
    "4. MEDICAL CONSTRAINTS: Left Kidney Pyeloplasty Adhesions (NO heavy axial load, NO asymmetric torque) and hypertonic pelvic floor (limit high-impact running). "
    "5. EXPLAINABLE PLANNING: When you propose or alter a workout, you must explain exactly which past verified data points or PT constraints led to that decision. "
    "Keep answers short and easy to read on a phone."
)

REPORT_INSTRUCTION = (
    f"You are an expert AI data analyst. Read the SQLite database '{DB_PATH}': daily_logs, workout_sets and garmin_metrics. "
    "Generate a beautiful, portable, single-file HTML dashboard summarizing the user's progress, effort (RPE) trends, "
    "symptoms, weights lifted and Garmin data. Write the raw HTML directly into '/config/workout_tracker/progress_report.html'. "
    "Do not output anything else."
)


def has_token():
    return bool(os.getenv("CLAUDE_CODE_OAUTH_TOKEN"))


_ANSI = re.compile(r"\x1b\[[0-9;]*m")


def _run(prompt, timeout=300):
    """Returns (reply, error)."""
    try:
        # No stdin: otherwise the CLI waits for piped input and prints a warning instead of answering
        result = subprocess.run(["claude", "-p", prompt], capture_output=True, text=True, check=True,
                                timeout=timeout, stdin=subprocess.DEVNULL)
        return result.stdout.strip(), None
    except subprocess.CalledProcessError as e:
        # The Claude CLI prints most errors to stdout; stderr is mostly warnings
        detail = _ANSI.sub("", (e.stdout or "").strip() or (e.stderr or "").strip()) or f"exit code {e.returncode}"
        print(f"Claude CLI failed (exit {e.returncode}): {detail}", flush=True)
        return None, detail
    except (subprocess.TimeoutExpired, OSError) as e:
        print(f"Claude CLI did not run: {e}", flush=True)
        return None, str(e)


def ask(message, recent=()):
    """One coach reply. `recent` is the last few chat turns, for continuity."""
    conversation = "\n".join(f"{'Joe' if m.get('role') == 'user' else 'Coach'}: {m.get('content', '')}"
                             for m in list(recent)[-6:])
    prompt = SYSTEM_INSTRUCTION
    if conversation:
        prompt += f"\n\nConversation so far:\n{conversation}"
    prompt += f"\n\nUser Update: {message}"
    return _run(prompt)


def report():
    os.makedirs("/config/workout_tracker", exist_ok=True)
    return _run(REPORT_INSTRUCTION, timeout=600)
