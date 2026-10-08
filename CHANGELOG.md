# Changelog

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
