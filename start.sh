#!/bin/bash
# Emotion Agent — Backend Start Script
# Usage: ./start.sh

set -e

cd "$(dirname "$0")"

# Check required env vars
if [ -z "$GROQ_API_KEY" ]; then
    echo "❌ GROQ_API_KEY is not set. Export it or create a .env file."
    exit 1
fi

echo "🚀 Starting Emotion Agent backend..."
echo "   Model: ${MODEL_ID:-meta-llama/llama-4-scout-17b-16e-instruct}"

# Activate venv if present
if [ -d "backend/venv" ]; then
    source backend/venv/bin/activate
fi

# Start FastAPI
uvicorn backend.main:app --host 0.0.0.0 --port 8000
