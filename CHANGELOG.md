# Changelog

## 0.5.2 - More Pictures

### 🌟 Features
* **All eight Baduanjin moves now have pictures** (photos by Alexander Callegari, CC BY-SA 3.0 de).
* **Pictures for five more yoga poses** from freely licensed Wikimedia Commons photos: legs up the wall, reclined bound angle, knees to chest, happy baby and mountain pose. Each shows its photographer and licence under the picture. They are bundled in the add-on.
## 0.5.1 - Qigong Pictures

### 🌟 Features
* **Pictures for the Baduanjin qigong moves** (7 of the 8 so far), from freely licensed photos by Alexander Callegari on Wikimedia Commons (CC BY-SA 3.0 de, resized). They are bundled in the add-on, so there is nothing to set up.
* Where your kidney-safe version differs from the traditional movement (looking back, the sway, the forward fold), the card says so under the picture.
## 0.5.0 - Garmin Connected From Inside the App

### 🌟 Features
* **Connect Garmin in Settings.** Enter your Garmin email and password once (and the verification code if Garmin asks for one). The password is used only for the sign-in and is never saved; only a login token is kept on your Home Assistant, and it refreshes itself.
* **Automatic sync every few hours** of resting heart rate, HRV, last night's sleep, body battery and your latest activity. "Sync now" does it on demand.
* **The coach uses it.** It now sees your Garmin numbers alongside your logged effort and symptoms. If Garmin isn't connected it says so instead of guessing.

### 🔧 Changes
* Fixed the old sync reading the wrong field for resting heart rate (it always stored 0).
## 0.4.7 - Picture Test Tries Several Files

### 🔧 Changes
* The picture test now tries three different pictures and passes if any of them loads, instead of failing because one specific file is missing.
* Added `tools/upload_yoga.py`, a script that uploads the yoga pictures to your bucket one at a time with retries (the Backblaze web uploader rate-limits large drags).
## 0.4.6 - Picture Test Shows What It Found

### 🔧 Changes
* When the picture test can sign in but can't find a picture, it now lists how many pictures it found in your folder, whether any are in a subfolder, and an example file name, so a missing upload or a wrong folder is easy to spot.
## 0.4.5 - Test Your Picture Connection

### 🌟 Features
* **Test connection button** in Settings > Yoga pictures. It fetches one picture from your private bucket and tells you plainly what is wrong if it can't: wrong bucket name, wrong key or secret, a key without read access, the wrong folder, or an endpoint it can't reach. It never shows your keys.

### 🔧 Changes
* Settings now says "Private bucket details saved" until the test passes, instead of "connected" (it only meant the fields were filled in).
## 0.4.4 - Suggested Weights and Reps

### 🌟 Features
* **Each exercise card shows what you did last time and what to try today,** and the set rows are pre-filled with it. Small steps only: a rep or two at a time, and weight goes up (2.5 lb under 20 lb, otherwise 5 lb) only once you reach 12 reps, then you start back at 8.
* **It holds back when your body says so:** no increase after a hard session (effort 8 or more), or when your last kidney score was above 3 or pelvic floor above 6. Bodyweight moves progress a little faster.
* **Build+ weeks add two reps, and the Easy week backs off** to last time's load with one set fewer.
* Exercises you have never logged show no suggestion, so the first time is your own call.
## 0.4.3 - Five Strength Days With Core Activation Every Day

### 🌟 Features
* **Five strength days a week** (Mon, Tue, Thu, Fri, Sat) with Wednesday as the cardio day and Sunday as rest. The coach can still move days around, now up to 5 strength days a week with at least one rest or recovery day.
* **Core activation on every strength day:** each one has two core slots (activation and stability), and a dedicated **core activation day** joins the rotation. Cardio days add a short core or mobility piece too.
* The five groups (legs, back and posture, core activation, hips and balance, full body and core) rotate across the week and shift every week, so a weekday is never the same twice in a row.
## 0.4.2 - A Different Muscle Group Every Day, A Different Week Every Week

### 🌟 Features
* **Each strength day works a different group:** legs (quads and glutes, with ski and snowboard leg work), back and posture, or hips and balance. The three groups rotate week to week, so Monday is not always the same.
* **Cardio days add one short piece of extra work** for a group that isn't trained that day (core, or hip and spine mobility), which also alternates from week to week.
* **A 4-week cycle:** Base, Build, Build+, then an Easy week that trims one extra from each strength day. The Week tab shows which week you are in and what each day is for.
* The coach sees the muscle group planned for each day when it suggests changes.
## 0.4.1 - Roomier Tab Bar and Sports-Aware Coach

### 🌟 Features
* **Five tabs instead of seven:** Today, Week, Coach, Mind & Body and **More**. More opens a short menu for History, Library and Settings. Swiping still moves through every screen.

### 🔧 Changes
* **Untick Triathlon in Settings > Sports and it really goes away:** the coach no longer introduces itself as a triathlon coach, and cardio descriptions no longer start with "Triathlon Prep". The coach is now told which sports you are training for and sticks to them.
## 0.4.0 - Weekly Plan and Swipe Navigation

### 🌟 Features
* **Week tab:** see the whole week at a glance, Monday to Sunday, with next week one tap away. Each day shows what it is for (strength, cardio, recovery or rest), the cardio type, the exercises, a mind-body suggestion, and whether you did it. The default week is strength, cardio, strength, cardio, strength, a long easy cardio day, and a rest day. With Triathlon on, cardio rotates swim, run and bike.
* **Today follows the week.** Rest and recovery days turn into gentle recovery days, cardio days keep the strength part short, and the planned cardio type is used when it is safe for your pelvic floor score. A high kidney score still forces a recovery day, whatever the week says.
* **The coach can plan your week.** Ask it to adjust the week (there is a button on the Week tab) and it suggests changes to specific days. You approve with **Apply**. Every week keeps at least one rest or recovery day and at most 4 strength days, and cardio stays between 5 and 45 minutes.
* **Swipe left and right** to move between tabs. It is ignored on sliders, text boxes, audio players and sideways-scrolling strips so it never gets in the way.
* Weeks to snow season show on the Week tab when you set the season date in Settings.

### 🔧 Changes
* The bottom tab "Mind & Body" is now "Mind" to make room for the Week tab.
## 0.3.6 - Sports and a Coach That Can Change Your Plan

### 🌟 Features
* **Sports in Settings:** tick Skiing, Snowboarding and Triathlon, and optionally set when the snow season starts. Daily extras lean toward ski and snowboard legs and add a balance slot (single-leg, ankle and hip control). Triathlon controls whether the swim, bike and run cardio is used.
* **The coach can change today's plan.** Ask it, for example, for more ski-useful work or a shorter cardio day. It suggests changes (add or remove an exercise, change cardio minutes), and nothing happens until you tap **Apply**. "Undo coach changes" on the Today tab brings the original plan back.
* **Safety still wins:** every suggestion is checked by the app. Exercises that are filtered out for your kidney or pelvic floor, that need equipment you don't have, or that aren't in the library are skipped, and the coach is told why. On a recovery day the plan stays a recovery day (only gentle mobility can be added), and cardio can't jump by more than 10 minutes.
## 0.3.5 - Natural Voices for Meditation

### 🌟 Features
* **Pick your meditation voice.** Eight natural-sounding female voices (American, Scottish, British and Irish-English) made right on your Home Assistant with Piper, so there is no robotic phone voice and nothing is sent to a cloud service. Choose one under Meditation and tap "Hear this voice" to try it.
* Sessions Claude writes for you now become a real audio file with the normal player (pause, scrub, replay). A session you already made opens instantly the next time.
* A voice is about 60 MB and downloads the first time you pick it, so only the voices you use take space. The phone's own voice stays as a fallback if the audio can't be made.
## 0.3.4 - Yoga Pictures From Your Private Bucket

### 🌟 Features
* **Yoga pictures from a private bucket,** set up the same way as the Trading Terminal: fill in the bucket endpoint, name, access key and secret key on this add-on's Configuration tab. The add-on fetches each picture with the key, keeps a copy on the Green (a few MB), and the key never reaches your phone.
* The bucket can stay private. Without the key set, Settings still accepts a public folder address instead.
## 0.3.3 - Meditation, More Yoga, Coach That Reads Your Data

### 🌟 Features
* **Meditation** in the Mind & Body tab: about 70 free guided practices (mindfulness, breathwork, yoga nidra, sleep, open awareness) from The Holistic Care's Stillness Library, played straight from their server. Nothing is stored on your Home Assistant.
* **A session written for you:** pick a length (3, 5 or 10 minutes) and an optional focus. Claude writes a calm script with slow breathing, long exhales and no straining, and your phone reads it aloud.
* **32 more yoga poses** (79 in total, including gentle floor work, supports like legs up the wall, mobility and four breathing practices with no breath holds). Every pose has steps and a safety note.

### 🔧 Changes
* **The coach no longer tries to run database commands.** It could not ask for approval from inside the app, so it stalled. The app now reads your recent workouts, symptoms, sets and Garmin data itself and gives them to the coach. The HTML progress report is written the same way.
* If there is no Garmin data stored yet, the coach says so instead of guessing.
## 0.3.2 - Mind & Body: Yoga, Qigong and Cool-Downs

### 🌟 Features
* **Mind & Body tab:** 47 yoga poses (steps, tips, safety notes, up to 5 pictures each) and the Baduanjin qigong routine, adjusted for the left kidney: head-only turns, hips square, folds only as far as is comfortable.
* **Cool-down on Today:** a short, gentle yoga wind-down after cardio, picked from your last symptom scores. High kidney or pelvic floor scores give rest and breathing only.
* **Safety:** deep twists, backbends, inversions, hard core work and extreme stretches are marked "not in auto picks" and never chosen automatically.
* **Settings:** gear details the coach reads (weights, plates, bands), vibration plate and inversion table added as equipment, and an address for the yoga pictures.

### 🔧 Changes
* Yoga pictures come from the Yoga Posture Dataset on Kaggle (CC0) and are hosted outside the add-on.
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
