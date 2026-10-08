import streamlit as st
import json
import os
import sqlite3
from engine import WorkoutEngine
from db import DB_PATH, get_last_log
from exercises import GUIDES, CARDIO_IMAGES
import history
import library
import ninjas_sync
import pandas as pd

st.set_page_config(page_title="AI Rehab & Training", layout="centered")

# Demo pictures: stack the start and finish picture and flip between them like a GIF
st.markdown("""
<style>
.ex-flip { display: grid; max-width: 320px; margin-bottom: 0.5rem; }
.ex-flip img { grid-area: 1 / 1; width: 100%; border-radius: 8px; }
.ex-flip.two img:last-child { animation: ex-flip 1.6s steps(1, end) infinite; }
@keyframes ex-flip { 50% { opacity: 0; } }
</style>
""", unsafe_allow_html=True)

engine = WorkoutEngine()

@st.cache_data(ttl=3600)
def load_library():
    return library.get_library(DB_PATH)

LIBRARY = load_library()
LIBRARY_BY_NAME = {e["name"]: e for e in LIBRARY}

def show_images(urls):
    # Start picture last so it is on top when the animation begins
    imgs = "".join(f'<img src="{u}" alt="">' for u in reversed(urls))
    flip = " two" if len(urls) > 1 else ""
    st.markdown(f'<div class="ex-flip{flip}">{imgs}</div>', unsafe_allow_html=True)

def show_library_entry(e, why=None):
    if not e["safe"]:
        reasons = "; ".join(library.FLAG_REASONS.get(f, f) for f in e["constraint_tags"])
        st.warning(f"Filtered out of your plans: {reasons}.")
    if why:
        st.caption(f"Why it's in today's plan: {why}")
    if e["images"]:
        show_images(e["images"])
        if (e["image_match"] or "").startswith("similar"):
            st.caption(f"Picture shows a similar movement ({e['image_match'][9:]}).")
    st.markdown(f"**{library.dose_for(e)[0]}**")
    if e["instructions"]:
        st.markdown("\n".join(f"1. {step}" for step in e["instructions"]))
    if e["tips"]:
        st.markdown("Tips: " + " ".join(e["tips"]))
    facts = [f"Muscles: {', '.join(e['muscles'])}" if e["muscles"] else "",
             f"Equipment: {e['equipment']}", f"Level: {e['level']}" if e["level"] else "",
             "Sources: " + ", ".join(library.SOURCE_NAMES[s] for s in e["sources"])]
    st.caption(" · ".join(f for f in facts if f))

def show_guide(name, why=None):
    guide = GUIDES.get(name)
    if not guide:
        if name in LIBRARY_BY_NAME:
            show_library_entry(LIBRARY_BY_NAME[name], why)
        return
    if guide.get("images"):
        show_images(guide["images"])
        if guide.get("image_note"):
            st.caption(guide["image_note"])
    st.markdown(f"**{guide['dose']}**")
    st.markdown("\n".join(f"1. {cue}" for cue in guide["cues"]))

def dose(name):
    if name in GUIDES:
        return GUIDES[name]["dose"], GUIDES[name].get("sets", 3)
    if name in LIBRARY_BY_NAME:
        return library.dose_for(LIBRARY_BY_NAME[name])
    return None, 3

def label(name):
    text = dose(name)[0]
    return f"{name} · {text.split('.')[0]}" if text else name

def tracker_rows(df):
    # Through JSON so numpy numbers become plain ones
    return json.loads(df.to_json(orient="records"))

def reset_workout_state():
    for key in [k for k in st.session_state if k.startswith("check_")] + ["tracker_data", "saved_draft"]:
        st.session_state.pop(key, None)

st.title("🏂🏊‍♂️ AI Training Hub")
st.caption("Auto-regulated for Pyeloplasty Rehab & Pelvic Floor Health")

last_log = get_last_log()
todays_workout = engine.generate_next_workout(last_log, library=LIBRARY, equipment=library.selected_equipment())
accessory_why = {a["name"]: a["why"] for a in todays_workout.get("accessories", [])}

tab1, tab_history, tab2, tab3, tab4 = st.tabs(
    ["📋 Today's Plan", "🗓️ History", "🧠 AI Coach", "📊 Progress Reports", "📚 Exercise Library"])

# Ticks and sets are auto-saved as a draft for today, so closing the page loses nothing.
# A page left open overnight starts fresh on the new day.
today = history.local_today()
if st.session_state.get("workout_date") != today:
    reset_workout_state()
    st.session_state.workout_date = today
draft = history.load_draft(DB_PATH, today) or {}

with tab1:
    st.header("Today's Dynamic Plan")

    st.subheader("1. Daily Non-Negotiables")
    for item in todays_workout["warmup"]:
        if f"check_{item}" not in st.session_state:
            st.session_state[f"check_{item}"] = draft.get("checks", {}).get(item, False)
        st.checkbox(label(item), key=f"check_{item}")
        with st.expander("How to"):
            show_guide(item)

    st.subheader("2. Strength & Stability")
    for item in todays_workout["strength"]:
        with st.expander(label(item)):
            show_guide(item, accessory_why.get(item))

    st.subheader("📋 Live Set Tracker")
    st.write("Log your exact weights and reps here. You can add or delete rows as you go. Everything saves automatically.")

    if "tracker_data" not in st.session_state:
        rows = draft.get("tracker") or []
        if not rows:
            for item in todays_workout["strength"]:
                # One row per prescribed set (3 if the exercise has no dose)
                for s in range(1, dose(item)[1] + 1):
                    rows.append({"Done": False, "Exercise": item, "Set": s, "Weight (lbs)": 0, "Reps": 0})
        if not rows:
            rows = [{"Done": False, "Exercise": "Custom", "Set": 1, "Weight (lbs)": 0, "Reps": 0}]
        st.session_state.tracker_data = pd.DataFrame(rows)

    # Short labels and narrow columns so all five fit on a phone screen
    edited_df = st.data_editor(
        st.session_state.tracker_data, num_rows="dynamic", use_container_width=True, hide_index=True,
        column_order=["Done", "Exercise", "Set", "Weight (lbs)", "Reps"],
        column_config={
            "Done": st.column_config.CheckboxColumn("✓", width="small"),
            "Exercise": st.column_config.TextColumn("Exercise", width="medium"),
            "Set": st.column_config.NumberColumn("Set", width="small", min_value=1, step=1),
            "Weight (lbs)": st.column_config.NumberColumn("lbs", width="small", min_value=0, step=2.5),
            "Reps": st.column_config.NumberColumn("Reps", width="small", min_value=0, step=1),
        })
    st.session_state.tracker_data = edited_df

    # Auto-save today's ticks and sets whenever they change
    current_draft = {"tracker": tracker_rows(edited_df),
                     "checks": {item: st.session_state[f"check_{item}"] for item in todays_workout["warmup"]}}
    if st.session_state.get("saved_draft") != current_draft:
        history.save_draft(DB_PATH, current_draft["tracker"], current_draft["checks"], today)
        st.session_state.saved_draft = current_draft

    st.subheader("3. Cardio Protocol")
    st.info(todays_workout["cardio"])
    if todays_workout.get("cardio_note"):
        st.caption(f"Why this length: {todays_workout['cardio_note']}")
    if todays_workout.get("cardio_type") in CARDIO_IMAGES:
        show_images(CARDIO_IMAGES[todays_workout["cardio_type"]])

    st.divider()

    st.header("Post-Workout Log")
    st.write("Your symptoms here dictate tomorrow's workout.")

    with st.form("log_form"):
        rpe = st.slider("Overall Effort (RPE)", 1, 10, 5)
        pf_tightness = st.slider("Pelvic Floor Tightness", 1, 10, 1, help="Higher numbers will automatically reduce impact cardio (running).")
        kidney_pain = st.slider("Left Kidney / Flank Tightness", 1, 10, 1, help="Higher numbers will force recovery/breathing protocols.")
        notes = st.text_area("Notes for the AI Coach")
        
        submitted = st.form_submit_button("Complete Workout")
        if submitted:
            history.complete_workout(DB_PATH, rpe, pf_tightness, kidney_pain, notes, todays_workout,
                                     tracker_rows(st.session_state.tracker_data), today)
            reset_workout_state()
            st.success("Workout saved to your History. The plan above has already adjusted for next time.")

with tab_history:
    st.header("Workout History")
    logs = history.get_history(DB_PATH)
    if not logs:
        st.info("No completed workouts yet. Press **Complete Workout** at the end of Today's Plan to save one here.")
    else:
        exercises_logged = history.logged_exercises(DB_PATH)
        if exercises_logged:
            st.subheader("Progress by exercise")
            chosen = st.selectbox("Exercise", exercises_logged)
            progress = pd.DataFrame(history.exercise_progress(DB_PATH, chosen)).set_index("date")
            st.line_chart(progress[["top_weight_lbs", "total_reps"]])
            st.caption("Heaviest weight (lbs) and total reps on each workout day.")

        st.subheader(f"Completed workouts ({len(logs)})")
        for log in logs:
            title = (f"{log['date']} · effort {log['rpe']}/10 · flank {log['kidney_flank_pain']}/10 · "
                     f"pelvic floor {log['pelvic_floor_tightness']}/10")
            with st.expander(title):
                workout = log["workout"]
                if workout.get("strength"):
                    st.markdown("**Exercises:** " + ", ".join(workout["strength"]))
                if workout.get("cardio"):
                    st.markdown(f"**Cardio:** {workout['cardio']}")
                if log["sets"]:
                    sets = pd.DataFrame(log["sets"])[["exercise", "set_number", "weight_lbs", "reps", "done"]]
                    sets.columns = ["Exercise", "Set", "Weight (lbs)", "Reps", "Done"]
                    sets["Done"] = sets["Done"].astype(bool)
                    st.dataframe(sets, hide_index=True, use_container_width=True)
                if log["notes"]:
                    st.text(log["notes"])

with tab2:
    st.header("Chat with your AI Coach")
    st.write("Tell the coach how you're feeling, upload a video of your form, and the AI will analyze it and update your plan.")

    if not os.getenv("CLAUDE_CODE_OAUTH_TOKEN"):
        st.warning("No Claude token set. Run `claude setup-token` in Claude Terminal, paste the token into this add-on's Configuration tab, then restart the add-on.")

    if "messages" not in st.session_state:
        st.session_state.messages = [{"role": "assistant", "content": "Hey Joe, how did the left flank feel during those wall sits today?"}]

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # File uploader feature temporarily removed to save build time on ARM hardware.
    file_prompt_injection = ""

    if prompt := st.chat_input("E.g., 'My kidney is tight...' or 'Check my squat form.'"):
        
        # Combine text prompt with file injection if present
        combined_prompt = prompt
        if file_prompt_injection:
            combined_prompt = f"{file_prompt_injection}\n\nAdditional user notes: {prompt}"
            
        st.session_state.messages.append({"role": "user", "content": combined_prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        with st.chat_message("assistant"):
            with st.spinner("AI Coach is analyzing your form and updating your database..."):
                import subprocess
                
                # Combine all frameworks: endurance, gym-bro, pt rehab, and movement-systems biomechanics
                system_instruction = (
                    "You are an elite Physical Therapist, Triathlon Coach, and Biomechanics Expert. "
                    "You have the 'endurance-coach-skill', 'gym-bro', 'physical-therapy-rehab-plan', and 'movement-systems' frameworks. "
                    "1. PT HARD SAFETY GATE: Before planning anything, you must run a clinical safety screen on the user's symptoms. "
                    "If Left Kidney Pain is > 6 or Pelvic Floor Tightness is > 7, you must issue a HARD CLINICAL STOP, refuse exercise progression, and enforce a pure recovery/breathing day. "
                    "If Pelvic Floor Tightness > 7, you MUST ALSO explicitly refer the user to find a clinical professional using the Pelvic Floor PT Directory (https://github.com/pete0585/pelvic-floor-pt-directory). "
                    "2. BIOMECHANICAL ANALYSIS (movement-systems): When prescribing any exercise, or when asked to analyze uploaded images/frames of the user's form, you must explain the movement system mechanics to ensure no compensatory spinal compression or asymmetric torque occurs due to the Pyeloplasty adhesions. You have tools to read image files from the local directory if the user provides filenames. "
                    "3. CRITICAL COMMAND OVERRIDE: The user uses Garmin, NOT Strava. DO NOT attempt to run `endurance-coach auth` or sync Strava. "
                    "Instead, you must read their training data and Resting Heart Rate directly from the 'garmin_metrics' table in the SQLite database 'workout_tracker.db'. "
                    "4. MEDICAL CONSTRAINTS: Left Kidney Pyeloplasty Adhesions (NO heavy axial load, NO asymmetric torque) and hypertonic pelvic floor (limit high-impact running). "
                    "5. EXPLAINABLE PLANNING: When you propose or alter a workout, you must explain exactly which past verified data points or PT constraints led to that decision. "
                    "Use your tools to query their recent logs, and UPDATE the database to auto-regulate tomorrow's workout via SQL. "
                    "Do not ask for permission, just use SQL to modify the routine."
                )
                
                full_prompt = f"{system_instruction}\n\nUser Update: {combined_prompt}"
                
                try:
                    result = subprocess.run(
                        ["claude", "-p", full_prompt],
                        capture_output=True,
                        text=True,
                        check=True,
                        timeout=300
                    )

                    response_text = result.stdout
                    st.markdown(response_text)
                    st.session_state.messages.append({"role": "assistant", "content": response_text})

                except subprocess.CalledProcessError as e:
                    # The Claude CLI prints most errors to stdout, not stderr
                    detail = (e.stderr or "").strip() or (e.stdout or "").strip() or f"exit code {e.returncode}"
                    print(f"Claude CLI failed (exit {e.returncode}): {detail}", flush=True)
                    error_msg = f"Coach encountered an error: {detail}"
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})
                except (subprocess.TimeoutExpired, OSError) as e:
                    print(f"Claude CLI did not run: {e}", flush=True)
                    error_msg = f"Coach encountered an error: {e}"
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})

with tab3:
    st.header("Portable HTML Progress Reports")
    st.write("Generate a standalone HTML file of your verified training history, similar to the gym-bro NavAIgate reports.")
    if st.button("Generate Portable HTML Report"):
        with st.spinner("Compiling database history into a standalone HTML file..."):
            import subprocess
            report_instruction = (
                "You are an expert AI data analyst. Read the 'workout_tracker.db' SQLite database, including the garmin_metrics table. "
                "Generate a beautiful, portable, single-file HTML dashboard summarizing the user's progress, RPE trends, and Garmin data. "
                "Write the raw HTML code directly into a file called 'progress_report.html' in this directory. Do not output anything else."
            )
            subprocess.run(["claude", "-p", report_instruction], capture_output=True, text=True)
            st.success("Report generated! Check your Home Assistant /config/workout_tracker folder for 'progress_report.html'.")

with tab4:
    st.header("Exercise Library")
    safe_count = sum(e["safe"] for e in LIBRARY)
    st.caption(f"{len(LIBRARY)} exercises from {len(library.SOURCE_NAMES)} databases · "
               f"{safe_count} safe for you · {len(LIBRARY) - safe_count} filtered out for your kidney, pelvic floor or core")
    ninjas = ninjas_sync.status()
    if ninjas:
        state_text = "all collected" if ninjas["complete"] else "still collecting in the background"
        st.caption(f"API Ninjas: {ninjas['exercises']} exercises so far ({state_text}; "
                   f"{ninjas['calls_this_month']} calls used this month). New ones appear here within an hour.")

    c1, c2 = st.columns(2)
    query = c1.text_input("Search", placeholder="e.g. glute bridge")
    focus = c2.selectbox("Focus", ["All", "legs", "upper back", "core", "mobility", "balance"])
    c3, c4 = st.columns(2)
    muscle = c3.selectbox("Muscle", ["All"] + sorted({m for e in LIBRARY for m in e["muscles"]}))
    equipment_filter = c4.selectbox("Equipment", ["All"] + sorted({e["equipment"] for e in LIBRARY}))
    c5, c6 = st.columns(2)
    pictures_only = c5.toggle("Only with pictures", value=True)
    show_filtered = c6.toggle("Show filtered-out exercises")

    words = query.lower().split()
    results = [
        e for e in LIBRARY
        if (show_filtered or e["safe"])
        and (not pictures_only or e["images"])
        and all(w in e["name"].lower() for w in words)
        and (focus == "All" or focus in e["goal_tags"])
        and (muscle == "All" or muscle in e["muscles"])
        and (equipment_filter == "All" or e["equipment"] == equipment_filter)
    ]
    st.write(f"**{len(results)} matches**")
    for e in results[:30]:
        with st.expander(f"{e['name']} · {e['equipment']}" + ("" if e["safe"] else " · ⚠️ filtered out")):
            show_library_entry(e)
    if len(results) > 30:
        st.caption("Showing the first 30. Narrow the search to see the rest.")

st.divider()
st.caption(library.CREDITS)
