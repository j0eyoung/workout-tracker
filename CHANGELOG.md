# Changelog

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
