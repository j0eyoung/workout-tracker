import json

class WorkoutEngine:
    def __init__(self, db_path="workout_tracker.db"):
        self.db_path = db_path

    def generate_next_workout(self, last_log):
        """
        Dynamically builds the next workout based on active goals 
        (Triathlon, Snowboard) and current medical symptoms.
        """
        # In a real app, these are fetched from the SQLite DB
        active_goals = ["snowboarding", "triathlon"]
        pf_tightness = last_log.get("pelvic_floor_tightness", 1)
        kidney_pain = last_log.get("kidney_flank_pain", 1)
        
        workout_plan = {
            "warmup": ["Gut-Motility Primer", "360-Degree Rib Breathing", "TVA Adductor Hack"],
            "strength": [],
            "cardio": ""
        }

        # --- MEDICAL AUTO-REGULATION ---
        if kidney_pain > 5:
            # Flank is acting up: Force a recovery day, no twisting, lots of breathing
            workout_plan["strength"].append("Supported Butterfly Pose (3 mins)")
            workout_plan["strength"].append("Child's Pose (Focus on left rib expansion)")
            workout_plan["cardio"] = "Light walking or Zero-gravity Swimming (No running/biking)"
            return workout_plan

        # --- STRENGTH PROGRAMMING ---
        # Base core stability is always included
        workout_plan["strength"].extend(["Supine Heel Slides", "Wall-Push Deadbugs"])

        if "snowboarding" in active_goals or "skiing" in active_goals:
            # Inject lateral edge control and quad endurance (Zero spinal load)
            workout_plan["strength"].extend(["Wall Sits (45s)", "Banded Lateral Walks", "Wall Tibialis Raises"])

        # --- CARDIO & TRIATHLON PROGRAMMING ---
        if "triathlon" in active_goals:
            # Decide between Swim, Bike, or Run based on Pelvic Floor
            if pf_tightness >= 7:
                # High impact (running) or seated pressure (biking) will flare the pelvic floor.
                # Force Swimming: Zero gravity, massive cardio, relieves pelvic pressure.
                workout_plan["cardio"] = "Triathlon Prep: Swimming (Focus on symmetrical breathing, avoid aggressive torso rotation)"
            elif pf_tightness >= 4:
                # Moderate tightness: Biking is okay if saddle pressure is managed, or backwards walking.
                workout_plan["cardio"] = "Triathlon Prep: Cycling (Low resistance, high cadence) OR Backwards Incline Walk"
            else:
                # Pelvic floor is relaxed: Safe to train running impact
                workout_plan["cardio"] = "Triathlon Prep: Running (Zone 2, high cadence to minimize ground reaction force)"
        else:
            workout_plan["cardio"] = "Treadmill: 20m incline walk"

        return workout_plan

# Example execution
if __name__ == "__main__":
    engine = WorkoutEngine()
    
    # Simulate user logging a tight pelvic floor after a hard week
    recent_log = {
        "pelvic_floor_tightness": 8, 
        "kidney_flank_pain": 2
    }
    
    todays_workout = engine.generate_next_workout(recent_log)
    print("DYNAMIC WORKOUT GENERATED:")
    print(json.dumps(todays_workout, indent=2))
