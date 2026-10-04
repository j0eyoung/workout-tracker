#!/bin/bash

# Set the database path to the shared Home Assistant config folder
# so it persists across updates and is accessible to Claude Terminal
export DB_PATH="/config/workout_tracker.db"

# Initialize the database if it doesn't exist
python3 db.py

# Start the FastAPI background service for Claude Terminal
uvicorn api:app --host 0.0.0.0 --port 8000 &

# Start the Streamlit UI
streamlit run app.py --server.port 8501 --server.address 0.0.0.0
