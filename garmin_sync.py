from garminconnect import Garmin
import sqlite3
import datetime
import json
import os

def sync_garmin(email, password):
    """Connects to Garmin Connect and saves today's stats and last activity to our DB."""
    try:
        # Initialize Garmin client
        client = Garmin(email, password)
        client.login()

        today = datetime.date.today()
        
        # Fetch daily health stats (Resting Heart Rate, HRV, Stress)
        health_stats = client.get_stats(today.isoformat())
        rhr = health_stats.get('restingHeartRateInBeatsPerMinute', 0)
        
        # Fetch the latest workout activity
        activities = client.get_activities(0, 1) # get the 1 most recent activity
        latest_activity = activities[0] if activities else {}

        # Save to SQLite DB for Claude to analyze
        conn = sqlite3.connect(os.getenv("DB_PATH", "workout_tracker.db"))
        c = conn.cursor()
        
        # We'll save this into a new table specifically for Garmin data
        c.execute('''
            CREATE TABLE IF NOT EXISTS garmin_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                resting_hr INTEGER,
                latest_activity_type TEXT,
                duration_secs INTEGER,
                avg_hr INTEGER,
                max_hr INTEGER,
                raw_data JSON
            )
        ''')
        
        c.execute('''
            INSERT INTO garmin_metrics (date, resting_hr, latest_activity_type, duration_secs, avg_hr, max_hr, raw_data)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            today.isoformat(),
            rhr,
            latest_activity.get('activityType', {}).get('typeKey', 'unknown'),
            latest_activity.get('duration', 0),
            latest_activity.get('averageHR', 0),
            latest_activity.get('maxHR', 0),
            json.dumps(latest_activity)
        ))
        
        conn.commit()
        conn.close()
        return True, "Garmin data synced successfully!"

    except Exception as e:
        return False, f"Garmin sync failed: {str(e)}"

if __name__ == "__main__":
    print("Garmin sync module ready.")
