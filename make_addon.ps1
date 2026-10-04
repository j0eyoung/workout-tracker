$SourceDir = "C:\AntiGravity\WorkoutTracker"
$TargetDir = "\\HA_GREEN_IP\addons\workout_tracker" # Update this to your HA Green's network share path

Write-Host "Copying Workout Tracker to Home Assistant Add-ons folder..."

# Check if target exists
if (!(Test-Path $TargetDir)) {
    New-Item -ItemType Directory -Force -Path $TargetDir
}

# Copy files
Copy-Item "$SourceDir\*" -Destination $TargetDir -Recurse -Force

Write-Host "Done! Go to Home Assistant -> Settings -> Add-ons -> Add-on Store -> Check for updates, then install/update AntiGravity Workout Tracker."
