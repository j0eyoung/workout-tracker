import streamlit as st
import json
import os
import sqlite3
from engine import WorkoutEngine
from db import DB_PATH, get_last_log
from exercises import GUIDES, CARDIO_IMAGES

st.set_page_config(page_title="AI Rehab & Training", layout="centered")

# Demo photos: stack the start and end photo and flip between them like a GIF
st.markdown("""
<style>
.ex-flip { display: grid; max-width: 320px; margin-bottom: 0.5rem; }
.ex-flip img { grid-area: 1 / 1; width: 100%; border-radius: 8px; }
.ex-flip img:last-child { animation: ex-flip 1.6s steps(1, end) infinite; }
@keyframes ex-flip { 50% { opacity: 0; } }
</style>
""", unsafe_allow_html=True)

engine = WorkoutEngine()

def show_images(urls):
    # Start photo last so it is on top when the animation begins
    imgs = "".join(f'<img src="{u}" alt="">' for u in reversed(urls))
    st.markdown(f'<div class="ex-flip">{imgs}</div>', unsafe_allow_html=True)

def show_guide(name):
    guide = GUIDES.get(name)
    if not guide:
        return
    if guide.get("images"):
        show_images(guide["images"])
        if guide.get("image_note"):
            st.caption(guide["image_note"])
    st.markdown(f"**{guide['dose']}**")
    st.markdown("\n".join(f"1. {cue}" for cue in guide["cues"]))

def label(name):
    guide = GUIDES.get(name)
    return f"{name} · {guide['dose']}" if guide else name

def save_log(rpe, pf, kidney, notes, workout_json):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT INTO daily_logs (date, completed, rpe, pelvic_floor_tightness, kidney_flank_pain, notes, executed_workout)
        VALUES (date('now'), 1, ?, ?, ?, ?, ?)
    """, (rpe, pf, kidney, notes, workout_json))
    conn.commit()
    conn.close()
    st.success("Workout Logged! The Dynamic Engine will adjust tomorrow's plan.")

st.title("🏂🏊‍♂️ AI Training Hub")
st.caption("Auto-regulated for Pyeloplasty Rehab & Pelvic Floor Health")

last_log = get_last_log()
todays_workout = engine.generate_next_workout(last_log)

tab1, tab2, tab3 = st.tabs(["📋 Today's Plan", "🧠 AI Coach", "📊 Progress Reports"])

with tab1:
    st.header("Today's Dynamic Plan")

    st.subheader("1. Daily Non-Negotiables")
    for item in todays_workout["warmup"]:
        st.checkbox(label(item))
        with st.expander("How to"):
            show_guide(item)

    st.subheader("2. Strength & Stability")
    for item in todays_workout["strength"]:
        with st.expander(label(item)):
            show_guide(item)

    st.subheader("📋 Live Set Tracker")
    st.write("Log your exact weights and reps here. You can add or delete rows as you go.")
    
    import pandas as pd
    if "tracker_data" not in st.session_state:
        rows = []
        for item in todays_workout["strength"]:
            # One row per prescribed set (3 if the exercise has no guide)
            for s in range(1, GUIDES.get(item, {}).get("sets", 3) + 1):
                rows.append({"Done": False, "Exercise": item[:30], "Set": s, "Weight (lbs)": 0, "Reps": 0})
        if not rows:
            rows = [{"Done": False, "Exercise": "Custom", "Set": 1, "Weight (lbs)": 0, "Reps": 0}]
        st.session_state.tracker_data = pd.DataFrame(rows)

    edited_df = st.data_editor(st.session_state.tracker_data, num_rows="dynamic", use_container_width=True)
    st.session_state.tracker_data = edited_df

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
            # Combine text notes with the structured table data
            final_notes = f"{notes}\n\nLogged Tracker Data:\n{st.session_state.tracker_data.to_string()}"
            save_log(rpe, pf_tightness, kidney_pain, final_notes, json.dumps(todays_workout))
            st.success("Workout logged successfully! See you tomorrow.")

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
