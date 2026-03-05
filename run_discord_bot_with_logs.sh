#!/bin/bash
# Run Discord bot with logs visible in terminal

cd /Users/chandu/Downloads/emotion-agent
source backend/venv/bin/activate

echo "Starting Discord bot with visible logs..."
echo "Press Ctrl+C to stop"
echo ""

python -m backend.discord_bot

