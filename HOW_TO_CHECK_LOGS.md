# How to Check Debug Logs

## Option 1: Run Bot in Foreground (See Logs Live)

Run this command in your terminal:

```bash
cd /Users/chandu/Downloads/emotion-agent
source backend/venv/bin/activate
python -m backend.discord_bot
```

Or use the helper script:

```bash
./run_discord_bot_with_logs.sh
```

This will show all debug logs in real-time. Press `Ctrl+C` to stop.

## Option 2: Run Bot in Background with Log File

```bash
cd /Users/chandu/Downloads/emotion-agent
source backend/venv/bin/activate
python -m backend.discord_bot > discord_bot.log 2>&1 &
```

Then check logs with:
```bash
tail -f discord_bot.log
```

## Option 3: Check Recent Logs (if already running)

If the bot is already running in background, you can check what it printed by looking at the process output. However, background processes don't always capture stdout.

**Best option:** Stop the bot and run it in foreground (Option 1) to see logs.

## What to Look For

When you send a message, you should see:
- `[DEBUG] Processing message: ...`
- `[DEBUG] Discovery check: phase=Discovery, episodic=0, identity=0, is_truly_new=True`
- `[DEBUG] Token limit: phase=Discovery, is_discovery=True, max_tokens=25`
- `[DEBUG] Calling LLM API... (max_tokens=25)`
- `[DEBUG] LLM API call complete, status: 200`

If `is_truly_new=False` or `max_tokens=256`, that's the problem!

