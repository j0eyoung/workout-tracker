# Changelog

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
