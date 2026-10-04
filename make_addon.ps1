# Deployment script for GitHub Home Assistant Add-on
Write-Host "Deploying AntiGravity Workout Tracker to GitHub..."
git add .
git commit -m "Update Add-on $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
git push origin master
Write-Host "Deployment complete! Go to Home Assistant Add-on Store and click 'Check for Updates'."
