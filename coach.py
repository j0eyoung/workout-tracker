"""AI Coach: runs the Claude Code CLI with Joe's subscription token (no API fees)."""
import json
import os
import re
import shutil
import subprocess
import threading
import time

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


# Sign-in happens inside the app (same flow as the Trading Terminal): `claude auth login --claudeai`
# prints a link, Joe approves it in a browser and pastes the code back. The login lives in
# CLAUDE_CONFIG_DIR (/data/claude in the add-on) so it survives updates.
CONFIG_DIR = os.getenv("CLAUDE_CONFIG_DIR", "")
_status_cache = (0.0, {})
_login = None


def binary():
    return shutil.which("claude")


def _env():
    env = dict(os.environ, DISABLE_AUTOUPDATER="1", BROWSER="none", NO_COLOR="1")
    env.pop("ANTHROPIC_API_KEY", None)  # an API key would override the subscription login
    if CONFIG_DIR:
        env["CLAUDE_CONFIG_DIR"] = CONFIG_DIR
    # A saved (possibly expired) Configuration-tab token beats the in-app login, so drop it once signed in
    if signed_in():
        env.pop("CLAUDE_CODE_OAUTH_TOKEN", None)
    return env


def status(max_age=600):
    """`claude auth status` as a dict ({} if the CLI is missing or fails); cached because it starts a program."""
    global _status_cache
    if time.time() - _status_cache[0] < max_age:
        return _status_cache[1]
    result = {}
    if binary():
        try:
            env = dict(os.environ, NO_COLOR="1")
            env.pop("CLAUDE_CODE_OAUTH_TOKEN", None)
            if CONFIG_DIR:
                env["CLAUDE_CONFIG_DIR"] = CONFIG_DIR
            out = subprocess.run([binary(), "auth", "status"], capture_output=True, text=True, timeout=20,
                                 env=env, stdin=subprocess.DEVNULL).stdout
            result = json.loads(out[out.find("{"):]) if "{" in out else {}
        except Exception:
            result = {}
    _status_cache = (time.time(), result)
    return result


def forget_status():
    global _status_cache
    _status_cache = (0.0, {})


def signed_in():
    s = status()
    return bool(s.get("loggedIn")) and s.get("authMethod") in ("claude.ai", "oauth_token", "claude_ai")


def has_token():
    """True when the coach has some way to sign in: the in-app login or a Configuration-tab token."""
    return signed_in() or bool(os.getenv("CLAUDE_CODE_OAUTH_TOKEN"))


def logout():
    if binary():
        subprocess.run([binary(), "auth", "logout"], capture_output=True, text=True, timeout=20, env=_env(),
                       stdin=subprocess.DEVNULL)
    forget_status()


class Login:
    """One run of `claude auth login --claudeai`, driven from the web page."""

    def __init__(self):
        self.output = ""
        self.started = time.time()
        self.proc = subprocess.Popen([binary(), "auth", "login", "--claudeai"], stdin=subprocess.PIPE,
                                     stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1,
                                     env=_env())
        threading.Thread(target=self._read, daemon=True).start()

    def _read(self):
        for line in self.proc.stdout:
            self.output += _ANSI.sub("", line)

    @property
    def url(self):
        m = re.search(r"https://\S+", self.output)
        return m.group(0) if m else None

    @property
    def done(self):
        return self.proc.poll() is not None

    @property
    def result(self):
        lines = [ln.strip() for ln in self.output.splitlines() if ln.strip() and "http" not in ln]
        return lines[-1] if lines else ""

    def send_code(self, code):
        if not self.done:
            self.proc.stdin.write("".join(code.split()) + "\n")
            self.proc.stdin.flush()

    def cancel(self):
        if not self.done:
            self.proc.kill()


def login_state():
    """What the page needs to draw the connect card."""
    global _login
    if _login and not _login.done and time.time() - _login.started > 600:
        _login.cancel()
    if _login and _login.done:
        forget_status()
    return {"signed_in": signed_in(), "cli": binary() is not None,
            "login": None if not _login else {"url": _login.url, "done": _login.done, "result": _login.result}}


def start_login():
    global _login
    if _login:
        _login.cancel()
    _login = Login() if binary() else None
    return login_state()


def send_code(code):
    if _login:
        _login.send_code(code)
        time.sleep(3)  # give the CLI a moment to finish before the page asks again
    return login_state()


def cancel_login():
    global _login
    if _login:
        _login.cancel()
    _login = None
    return login_state()


_ANSI = re.compile(r"\x1b\[[0-9;]*m")
_AUTH_WORDS = ("authenticate", "oauth", "log in", "login", "not logged", "unauthorized", "401")


def _run(prompt, timeout=300):
    """Returns (reply, error)."""
    try:
        # No stdin: otherwise the CLI waits for piped input and prints a warning instead of answering
        result = subprocess.run(["claude", "-p", prompt], capture_output=True, text=True, check=True,
                                timeout=timeout, stdin=subprocess.DEVNULL, env=_env())
        return result.stdout.strip(), None
    except subprocess.CalledProcessError as e:
        # The Claude CLI prints most errors to stdout; stderr is mostly warnings
        detail = _ANSI.sub("", (e.stdout or "").strip() or (e.stderr or "").strip()) or f"exit code {e.returncode}"
        print(f"Claude CLI failed (exit {e.returncode}): {detail}", flush=True)
        if any(w in detail.lower() for w in _AUTH_WORDS):
            global _status_cache  # `claude auth status` can still say logged in after the login expires
            _status_cache = (time.time() + 3600, {"loggedIn": False})
            return None, "Claude sign-in expired or invalid. Reconnect in the Coach tab."
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
