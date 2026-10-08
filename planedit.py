"""Lets the coach change today's plan, safely.

The coach (a headless Claude CLI that cannot run tools) may end a reply with a fenced `plan-changes` block. The app
never trusts it: every change is checked here against the exercise library and the safety rules, shown to Joe as
Apply / No thanks, and only then saved for that day. Recovery days (kidney flank above 5) stay recovery days."""
import difflib
import json
import re

import library
from engine import CARDIO_MAX_MINUTES, CARDIO_TEXT

BLOCK = re.compile(r"```\s*plan-changes\s*(\{.*?\})\s*```", re.S)
MAX_CHANGES = 6
KEEP_DAYS = 14

INSTRUCTIONS = (
    "CHANGING TODAY'S PLAN: you may propose changes, and Joe will be asked to approve them. To do so, end your reply with "
    'one fenced block exactly like this (use only the operations you need):\n'
    '```plan-changes\n{"changes": [{"op": "add", "name": "Exercise name", "why": "short reason"}, '
    '{"op": "remove", "name": "Exercise name in today\'s plan"}, '
    '{"op": "cardio", "type": "bike", "minutes": 25, "why": "short reason"}]}\n```\n'
    "Rules: at most 6 changes; exercise names must come from today's plan or the SAFE EXERCISES list below, spelled exactly; "
    "cardio type is one of recovery, swim, bike, run, walk; on a recovery day change nothing except adding gentle mobility; "
    "never raise cardio by more than 10 minutes. Explain the reason in your reply too. If you do not want to change the plan, "
    "do not include the block."
)


def extract(reply):
    """(reply without the block, parsed block or None)."""
    if not reply:
        return reply, None
    m = BLOCK.search(reply)
    if not m:
        return reply, None
    clean = (reply[:m.start()] + reply[m.end():]).strip()
    try:
        return clean, json.loads(m.group(1))
    except ValueError:
        return clean, None


def _resolve(name, by_name):
    """Library entry for a name the coach wrote (exact, case-insensitive, then a close match)."""
    if not name:
        return None
    lower = {n.lower(): n for n in by_name}
    key = lower.get(str(name).strip().lower())
    if key is None:
        close = difflib.get_close_matches(str(name).strip().lower(), list(lower), n=1, cutoff=0.88)
        key = lower[close[0]] if close else None
    return by_name[key] if key else None


def validate(data, plan, by_name, equipment):
    """(changes that are allowed, reasons for the ones that are not)."""
    allowed, rejected = [], []
    recovery = plan.get("cardio_type") == "recovery"
    in_plan = {n.lower(): n for n in plan.get("strength", [])}
    equipment = set(equipment or []) | {"bodyweight"}
    for op in ((data or {}).get("changes") or [])[:MAX_CHANGES]:
        kind = op.get("op")
        why = str(op.get("why") or "")[:160]
        if kind == "add":
            e = _resolve(op.get("name"), by_name)
            if not e:
                rejected.append(f"'{op.get('name')}' isn't in the exercise library.")
            elif not e["safe"]:
                rejected.append(f"{e['name']} is filtered out for your kidney or pelvic floor.")
            elif e["equipment"] not in equipment:
                rejected.append(f"{e['name']} needs {e['equipment']}, which isn't in your equipment list.")
            elif recovery and "mobility" not in e["goal_tags"]:
                rejected.append(f"{e['name']} isn't gentle mobility, and today is a recovery day.")
            elif e["name"].lower() in in_plan:
                continue  # already in the plan
            else:
                allowed.append({"op": "add", "name": e["name"], "why": why})
                in_plan[e["name"].lower()] = e["name"]
        elif kind == "remove":
            name = in_plan.get(str(op.get("name") or "").strip().lower())
            if name:
                allowed.append({"op": "remove", "name": name, "why": why})
                in_plan.pop(name.lower(), None)
            else:
                rejected.append(f"'{op.get('name')}' isn't in today's plan.")
        elif kind == "cardio":
            ctype, current = op.get("type"), plan.get("cardio_minutes") or 0
            try:
                minutes = int(op.get("minutes"))
            except (TypeError, ValueError):
                rejected.append("The cardio change didn't have a number of minutes.")
                continue
            if ctype not in CARDIO_TEXT:
                rejected.append(f"'{ctype}' isn't a cardio type the app uses.")
            elif recovery and ctype != "recovery":
                rejected.append("Today is a recovery day, so cardio stays easy recovery.")
            elif not 5 <= minutes <= CARDIO_MAX_MINUTES:
                rejected.append(f"{minutes} minutes is outside the safe range (5-{CARDIO_MAX_MINUTES}).")
            elif ctype == plan.get("cardio_type") and minutes > current + 10:
                rejected.append(f"Cardio can go up by at most 10 minutes at once (now {current}).")
            else:
                allowed.append({"op": "cardio", "type": ctype, "minutes": minutes, "why": why})
        else:
            rejected.append("An unknown change was skipped.")
    return allowed, rejected


def label(c):
    if c["op"] == "add":
        return f"Add {c['name']}"
    if c["op"] == "remove":
        return f"Remove {c['name']}"
    return f"Cardio: {c['minutes']} min {c['type']}"


# --- Saved per day, in settings.json so they survive updates --------------------------------------------------

def overrides_for(date):
    return (library.load_settings().get("plan_overrides") or {}).get(date, {}).get("changes", [])


def save(date, changes):
    all_ov = library.load_settings().get("plan_overrides") or {}
    existing = all_ov.get(date, {}).get("changes", [])
    all_ov[date] = {"changes": existing + changes}
    for old in sorted(all_ov)[:-KEEP_DAYS]:
        all_ov.pop(old, None)
    library.save_settings({"plan_overrides": all_ov})


def clear(date):
    all_ov = library.load_settings().get("plan_overrides") or {}
    if all_ov.pop(date, None) is not None:
        library.save_settings({"plan_overrides": all_ov})


def apply(workout, changes):
    """Today's workout with the approved changes folded in."""
    for c in changes:
        if c["op"] == "add" and c["name"] not in workout["strength"]:
            workout["strength"].append(c["name"])
            workout.setdefault("accessories", []).append(
                {"name": c["name"], "why": "Added by your coach" + (f": {c['why']}" if c.get("why") else "")})
        elif c["op"] == "remove" and c["name"] in workout["strength"]:
            workout["strength"].remove(c["name"])
            workout["accessories"] = [a for a in workout.get("accessories", []) if a["name"] != c["name"]]
        elif c["op"] == "cardio":
            workout["cardio_type"], workout["cardio_minutes"] = c["type"], c["minutes"]
            workout["cardio"] = (f"{c['minutes']} min: {CARDIO_TEXT[c['type']]}. "
                                 "Easy pace (you can talk in full sentences); the first 5 min are your warm-up.")
            workout["cardio_note"] = "Changed by your coach" + (f": {c['why']}" if c.get("why") else ".")
    return workout


# --- What the coach is told -----------------------------------------------------------------------------------

def context(plan, entries, equipment, goals, per_tag=10):
    """Today's plan and a short list of safe exercises the coach may propose (names must match exactly)."""
    equipment = set(equipment or []) | {"bodyweight"}
    safe = [e for e in entries if e["safe"] and e["equipment"] in equipment and e["images"]]
    lines = ["TODAY'S PLAN (what Joe will do):",
             "Strength and extras: " + "; ".join(plan.get("strength", [])),
             f"Cardio: {plan.get('cardio_minutes')} min, type {plan.get('cardio_type')}",
             "Recovery day: " + ("YES (change nothing except gentle mobility)" if plan.get("cardio_type") == "recovery" else "no"),
             "Active sports and goals: " + (", ".join(goals) or "general fitness"),
             "", "SAFE EXERCISES you may add (already screened for his kidney and pelvic floor):"]
    snow = {"skiing", "snowboarding"} & set(goals)
    tags = (["legs", "balance", "core", "mobility", "upper back"] if snow else ["legs", "core", "mobility", "upper back"])
    for tag in tags:
        names = sorted(e["name"] for e in safe if tag in e["goal_tags"])[:400]
        step = max(1, len(names) // per_tag)
        lines.append(f"{tag}: " + "; ".join(names[::step][:per_tag]))
    return "\n".join(lines)
