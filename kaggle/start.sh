#!/usr/bin/env bash
# Kaggle Startup Script for AI Movie Studio
set -e

# Build frontend if missing
if [ ! -d "frontend/dist" ]; then
    echo "Building frontend..."
    cd frontend && npm install && npm run build && cd ..
fi

# Run the unified Python runner (handles unbuffered logging, tunnel watchdog & server)
exec python kaggle/run.py
