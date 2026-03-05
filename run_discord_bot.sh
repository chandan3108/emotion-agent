#!/bin/bash
# Simple script to run Discord bot

cd "$(dirname "$0")/backend"
source venv/bin/activate
python -m backend.discord_bot

