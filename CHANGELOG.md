# Changelog

## 0.3.1 - Settings Tab and In-App Claude Sign-In

### 🌟 Features
* **Settings tab:** pick the equipment you have by tapping chips. Today's plan rebuilds as soon as you change it. More settings (sports, training goals) will go here later.
* **Connect Claude inside the app:** Settings > Connect Claude gives you a sign-in link, you paste the code back, and the coach uses your Claude subscription. No more `claude setup-token`. The login is kept across updates.

### 🔧 Changes
* An old, expired token in the Configuration tab no longer breaks the coach once you have signed in (that was the "401 Invalid bearer token" error).
* When the sign-in expires, the coach tells you to reconnect instead of showing a raw error.

## 0.3.0 - Fast Phone-First App

### 🌟 Features
* **New, much faster app.** Streamlit is gone: the screens are a lightweight web page served by the add-on's own server. Taps (ticking warm-ups, marking sets done, adding sets) respond instantly on your phone; the server is only called to load and save.
* **Built for the phone:** bottom tab bar (Today, History, Coach, Library), big tap targets, a number keypad for weight and reps, and light or dark to match your phone.
* **Set logging per exercise:** each exercise card has its own sets with a done button, lbs and reps. "+ Add set" copies your last set, and "+ Add another exercise" logs something extra.
* **Auto-save** shows "Saved ✓" at the top. It saves right away when you lock the phone, and the finish sliders and notes are remembered on that phone until you complete the workout.
* **History:** tap a workout to see its exercises, cardio and every set, with a progress chart per exercise (heaviest lbs and total reps).
* **Coach** remembers the last few messages of the conversation, so follow-up questions work.
* **Library:** instant search with focus chips (legs, upper back, core, mobility, balance), muscle and equipment filters, and "Show more".

### 🔧 Changes
* One server on port 8501 for the app and Claude Terminal (`/workout/today`, `/workout/log`); port 8000 is no longer used.
* Smaller image and faster startup: Streamlit, pandas and pyarrow are no longer installed.
* The daily plan and cardio progression use your Home Assistant time zone's date.

## 0.2.1 - Workout History, API Ninjas & Your Home Gym

### 🌟 Features
* **History tab:** every completed workout with its date, effort, symptoms, exercises, cardio and each set (weight, reps, done), plus a progress chart per exercise (heaviest weight and total reps by day).
* **Sets saved as real rows** (new `workout_sets` table) instead of a block of text in the notes, so progress can be charted.
* **Auto-save:** warm-up ticks and the set tracker save as you go. Closing or reloading the page no longer loses them, and a page left open overnight starts fresh the next day.
* **API Ninjas exercises (optional):** add your free API Ninjas key in Configuration and the add-on collects their ~3,000 exercises (with steps and safety notes) in the background, staying under 90 calls an hour and your monthly budget (default 2,500 of the free 3,000). Progress shows on the Exercise Library tab.
* **Weight plates** are now equipment (your 25, 2 x 10 and 2.5 lb plates). Plate-loaded moves get the same spine-loading checks as dumbbells.

### 🔧 Fixes
* **Workout dates use your Home Assistant time zone** instead of UTC, so evening workouts land on the right day.
* **Equipment defaults to your home gym:** bodyweight, bands, dumbbells, 15 lb kettlebell, plates, foam roller, adjustable bench, pull-up bar, Centr 1 cable machine, EZ-curl bar, barbell and cardio machines. Daily extras no longer pick stability ball, medicine ball, gym-machine, suspension, slider or unknown-equipment exercises. Barbell lifts stay filtered out for your kidney. If you already saved Configuration, click **Reset to defaults** there (or tick the new items) to pick this up.

## 0.2.0 - Exercise Library (about 5,000 exercises)

### 🌟 Features
* **Exercise Library:** merges four databases into one list of about 5,000 exercises, stored in the `exercise_library` table of `/config/workout_tracker.db`:
  * Free Exercise DB (876, public domain, photos and steps)
  * RepDB (609, illustrations, steps and tips). Exercise data by RepDB (repdb.co)
  * Strength to Overcome functional fitness database (3,242, detailed movement tags)
  * Boostcamp programs (830 exercise names with typical sets and reps)
* **Safety filter for your kidney, pelvic floor and core:** every exercise is checked for torso twisting, weight loading the spine, one-sided weight, crunch/sit-up/plank pressure, jumping, explosive swings, heavy barbell lifting, lower-back loading, upside-down positions and advanced level. About 1,850 pass; the rest stay browsable with the reason they're left out.
* **Pictures across sources:** exercises without their own picture borrow the picture of a closely similar movement, labeled as such.
* **New 📚 Exercise Library tab:** search and filter by focus (legs, upper back, core, mobility, balance), muscle and equipment.
* **Daily plan adds 4 rotating extras** from the safe list: snowboard legs, posture/swim pulling, beginner core and mobility (2 gentle stretches on recovery days). New picks each day, each with a "why it's in today's plan" line.
* **Equipment setting:** choose the equipment you have in the add-on Configuration tab; daily extras only use that equipment.
* **Better pictures for your own moves:** Wall Sit, Dead Bug, Banded Lateral Walk, Butterfly and Child's Pose now use RepDB illustrations.

## 0.1.9 - Cardio Minutes, Exercise Guides & Coach Errors

### 🌟 Features
* **Cardio now says how long:** every cardio session shows its minutes (recovery 15, swim 20, run 20, incline walk 20, bike 30), at an easy Zone 2 pace.
* **Cardio auto-adjusts from your logs:** adds 5 min (max once a week, up to 45) when your last session felt easy (effort 6 or less) and flank pain stayed at 3 or below. Cuts back by about a quarter when your last effort was 8+. A "Why this length" line explains each change.
* **Exercise guides:** every exercise shows its dose (sets, reps or time) and step-by-step form cues from your routine. Tap an exercise to open it.
* **Demo photos:** Dead Bug, Lateral Band Walk, Butterfly, Child's Pose, bike, treadmill run and walk show start/finish photos that flip like a GIF (public-domain Free Exercise DB).
* **Set tracker** creates one row per prescribed set instead of always 3.

### 🔧 Fixes
* **AI Coach errors now show the real message** (Claude's CLI prints errors to stdout, which the app used to drop). Errors also appear in the add-on's Log tab.
* **Claude token:** spaces and line breaks picked up when copying the token from a terminal are removed automatically.

## 0.1.8 - Open Web UI & Sidebar

### 🌟 Features
* **Open from Home Assistant:** the add-on page now has **Open Web UI**, and you can turn on **Show in sidebar** to get a "Workouts" panel. Works in the HA phone app, behind your Home Assistant login.
* Direct access on port 8501 still works.

## 0.1.7 - Prebuilt Image, Claude Token & Garmin Fix

(0.1.6 was never released: its build hung and was replaced by this version.)

### 🌟 Features
* **Claude token setting:** new "Claude token" field in the add-on Configuration tab. Run `claude setup-token` in Claude Terminal and paste the token there so the AI Coach uses your Max subscription. The token stays on your Home Assistant, never on GitHub.

### 🔧 Fixes
* **Installs no longer build on the HA Green:** GitHub now builds the add-on image and Home Assistant just downloads it. Installs and updates take a minute or two instead of 40+ minutes.
* **Fixed the 0.1.5 install failure:** 0.1.5 ran on Python 3.13 and tried to compile `pydantic-core` and `numpy` from source. The image now uses Python 3.12, where every package installs from a prebuilt wheel.
* **Fixed the endless dependency loop:** `garminconnect` 0.2.14 pulled in `withings-sync`, whose newer versions require a newer `garminconnect`, so pip searched old versions forever. Now on `garminconnect` 0.3.17, the same version that created your Garmin token.
* **Garmin sync reads your token again:** sync now loads `/config/garmin_tokens.json` in the 0.3.x token format and saves refreshed tokens back to it.
* **Fixed the app crashing on open:** the web UI and API now use the database in `/config/workout_tracker.db` (the one created at startup) instead of an empty file inside the container.
* Removed the unused `endurance-coach` CLI, which forced a slow C++ compile of `better-sqlite3`.

## 0.1.0 - Initial Release (The Megazord AI Coach)

Welcome to the AI Workout Tracker! This initial release combines five massive AI frameworks into a single, locally-hosted Home Assistant Add-on powered by Claude.

### 🌟 Features
* **Garmin Connect Integration:** Natively connects to Garmin to pull Resting Heart Rate, HRV, and recent activity logs securely into a local SQLite database, avoiding enterprise API costs.
* **Endurance Coach Engine:** Integrates Triathlon periodization, TSS (Training Stress Score) tracking, and Heart Rate Zone targeting.
* **Gym-Bro Explainable Planning:** AI will dynamically build workouts based on your symptoms and explain *why* it made each decision. Includes a button to generate portable HTML progress reports.
* **Physical Therapy Hard Gate:** Automatically halts workouts and prescribes recovery breathing if Left Kidney or Pelvic Floor pain metrics exceed safety thresholds.
* **Automated PT Referrals:** Dynamically links to the Pelvic Floor PT Directory if symptoms require a professional consultation.
* **Movement-Systems Biomechanics:** Support for video/image form uploads. Claude will use Shirley Sahrmann's frameworks to analyze spinal and pelvic alignment to protect Pyeloplasty adhesions.
* **Local Claude CLI Runner:** Uses your existing Claude session token to run inference entirely in the background terminal—zero API fees!

### 🔧 Security
* Strict `.gitignore` implementation ensuring OAuth tokens and databases remain strictly on your local Home Assistant instance.
* Dedicated `setup_garmin.py` for headless MFA resolution.
