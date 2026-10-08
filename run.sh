#!/bin/bash

# Set the database path to the shared Home Assistant config folder
# so it persists across updates and is accessible to Claude Terminal
export DB_PATH="/config/workout_tracker.db"

# Claude token from the add-on Configuration tab (made with `claude setup-token`)
token="$(python3 -c 'import json; print(json.load(open("/data/options.json")).get("claude_code_oauth_token") or "")' 2>/dev/null)"
if [ -n "$token" ]; then
    export CLAUDE_CODE_OAUTH_TOKEN="$token"
else
    echo "No Claude token set: the AI Coach tab will not work until you add one in the Configuration tab."
fi

# Initialize the database if it doesn't exist
python3 db.py

# Start the FastAPI background service for Claude Terminal
uvicorn api:app --host 0.0.0.0 --port 8000 &

# Start the Streamlit UI
# CORS/XSRF off: Home Assistant ingress proxies the page from its own origin
streamlit run app.py --server.port 8501 --server.address 0.0.0.0 \
    --server.headless true --server.enableCORS false --server.enableXsrfProtection false \
    --browser.gatherUsageStats false
