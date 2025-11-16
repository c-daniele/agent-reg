#!/bin/bash
# Start the Agent Registry backend server

# Activate virtual environment
source .venv/bin/activate

# Set PYTHONPATH to include src directory for module imports
export PYTHONPATH="${PYTHONPATH}:src"

# Start uvicorn server
python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
