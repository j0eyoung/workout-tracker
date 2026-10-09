"""The week view: what each day of the week is for (strength, cardio, recovery or rest), built from your sports and
your recent symptoms. Today's real workout still adapts to how you feel; the week is the intent it follows.

Pattern (Mon-Sun): strength, cardio, strength (lighter), cardio, strength, long easy cardio, rest. The coach can move
things around; changes are saved per date in settings.json."""
import datetime

import library

FOCUS = ("strength", "cardio", "recovery", "rest")
LABELS = {"strength": "Strength", "cardio": "Cardio", "recovery": "Recovery", "rest": "Rest"}
DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
KEEP_DAYS = 28

# weekday -> (focus, cardio slot). Slots: a = main cardio, b = second cardio, long = long easy day
PATTERN = {0: ("strength", None), 1: ("strength", None), 2: ("cardio", "a"), 3: ("strength", None),
           4: ("strength", None), 5: ("strength", None), 6: ("rest", None)}
MAX_STRENGTH_DAYS = 5
STRENGTH_WEEKDAYS = [0, 1, 3, 4, 5]


def monday(date):
    return date - datetime.timedelta(days=date.weekday())


def _cardio_type(slot, goals):
    if "triathlon" in goals:
        return {"a": "swim", "b": "run", "long": "bike"}[slot]
    return {"a": "walk", "b": "bike", "long": "walk"}[slot]


# Each strength day works a different group, and the groups shift every week so no weekday is always the same.
THEMES = ["legs", "back", "core", "hips", "full"]
THEME_LABELS = {"legs": "Legs: quads and glutes", "back": "Back and posture", "hips": "Hips and balance",
                "core": "Core activation day", "full": "Full body and core",
                "core_add": "plus core", "mobility": "plus hip and spine mobility"}
PHASES = ["Base", "Build", "Build+", "Easy week"]  # 4-week cycle; the easy week trims the extras


def week_number(date):
    return date.isocalendar()[1]


def phase(date):
    return PHASES[week_number(date) % 4]


def theme_for(date, focus):
    if focus == "strength":
        # position among the week's strength days, shifted each week so a weekday is not always the same group
        pos = STRENGTH_WEEKDAYS.index(date.weekday()) if date.weekday() in STRENGTH_WEEKDAYS else date.weekday() % 5
        return THEMES[(pos + week_number(date)) % len(THEMES)]
    if focus == "cardio":
        return "core_add" if (date.weekday() // 2 + week_number(date)) % 2 == 0 else "mobility"
    return None


def _base(date, goals):
    focus, slot = PATTERN[date.weekday()]
    day = {"focus": focus, "cardio_type": None, "cardio_minutes": None}
    if slot:
        # Only the type is planned; today's engine works out the minutes from how your last sessions went
        day["cardio_type"] = _cardio_type(slot, goals)
        day["long"] = slot == "long"
    return day


def overrides():
    return library.load_settings().get("week_overrides") or {}


def day_plan(date, goals):
    """Plan for one date: the pattern plus any change the coach made (and you approved)."""
    day = _base(date, goals)
    ov = overrides().get(date.isoformat())
    if ov:
        day.update({k: v for k, v in ov.items() if k in ("focus", "cardio_type", "cardio_minutes", "note")})
        day["changed"] = True
        if day["focus"] in ("rest", "recovery"):
            day["cardio_type"], day["cardio_minutes"] = None, None
        elif day["focus"] == "cardio" and not day["cardio_type"]:
            base = _base(date, goals)
            day["cardio_type"] = base["cardio_type"] or _cardio_type("a", goals)
    day["theme"] = theme_for(date, day["focus"])
    day["theme_label"] = THEME_LABELS.get(day["theme"]) if day["theme"] else None
    day["phase"] = phase(date)
    return day


def mind_suggestion(focus):
    return {"strength": "8-minute yoga cool-down after your sets",
            "cardio": "Baduanjin qigong or breathing practice afterwards",
            "recovery": "Gentle yoga and a guided meditation",
            "rest": "Optional: a short yoga flow, qigong or a meditation"}[focus]


def week(start, today, goals, done_dates):
    """Seven days from `start` (a Monday), each with a status: done, today, missed or upcoming."""
    days = []
    for i in range(7):
        d = start + datetime.timedelta(days=i)
        plan = day_plan(d, goals)
        if d.isoformat() in done_dates:
            status = "done"
        elif d == today:
            status = "today"
        elif d < today:
            status = "missed" if plan["focus"] not in ("rest",) else "past"
        else:
            status = "upcoming"
        days.append({"date": d.isoformat(), "weekday": DAY_NAMES[d.weekday()], "label": LABELS[plan["focus"]],
                     "mind": mind_suggestion(plan["focus"]), "status": status, **plan})
    return days


# --- Saving the coach's changes -------------------------------------------------------------------------------

def save_changes(changes):
    all_ov = overrides()
    for c in changes:
        entry = {"focus": c["focus"], "note": c.get("why", "")}
        if c["focus"] == "cardio":
            entry.update(cardio_type=c.get("type"), cardio_minutes=c.get("minutes"))
        all_ov[c["date"]] = entry
    for old in sorted(all_ov)[:-KEEP_DAYS]:
        all_ov.pop(old, None)
    library.save_settings({"week_overrides": all_ov})


def clear_week(start):
    all_ov = overrides()
    for i in range(14):
        all_ov.pop((start + datetime.timedelta(days=i)).isoformat(), None)
    library.save_settings({"week_overrides": all_ov})
