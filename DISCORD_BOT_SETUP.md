# Discord Bot Setup Guide

## 🚀 Quick Start

### **Step 1: Install Discord.py**

```bash
cd backend
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install discord.py
```

### **Step 2: Create Discord Bot**

1. Go to https://discord.com/developers/applications
2. Click "New Application"
3. Name it (e.g., "Emotion Agent")
4. Go to "Bot" section
5. Click "Add Bot"
6. **IMPORTANT:** Enable these Privileged Gateway Intents:
   - ✅ MESSAGE CONTENT INTENT (required!)
   - ✅ SERVER MEMBERS INTENT (optional, for member info)
7. Copy the bot token (click "Reset Token" if needed)
8. Save the token - you'll need it!

### **Step 3: Invite Bot to Server**

1. Go to "OAuth2" → "URL Generator"
2. Select scopes:
   - ✅ `bot`
   - ✅ `applications.commands` (optional, for slash commands)
3. Select bot permissions:
   - ✅ Send Messages
   - ✅ Read Message History
   - ✅ Read Messages/View Channels
   - ✅ Use External Emojis (optional)
4. Copy the generated URL
5. Open URL in browser and invite bot to your server

### **Step 4: Set Environment Variables**

Create a `.env` file in the `backend/` directory:

```bash
# backend/.env
DISCORD_TOKEN=your_discord_bot_token_here
HF_TOKEN=your_huggingface_token_here
```

Or export them:

```bash
export DISCORD_TOKEN="your_discord_bot_token_here"
export HF_TOKEN="your_huggingface_token_here"
```

### **Step 5: Run the Bot**

```bash
cd backend
source venv/bin/activate
python -m backend.discord_bot
```

Or if you're in the backend directory:

```bash
python discord_bot.py
```

You should see:
```
🚀 Starting Discord bot...
✅ BotName#1234 has logged in!
Bot is in 1 guilds
```

---

## 🎮 How to Use

### **Private Messages (DMs)**
- Send a DM to the bot
- Bot will respond using full cognitive pipeline
- Each user gets their own AI companion state

### **Channel Mentions**
- Mention the bot in a channel: `@BotName hello`
- Bot will respond in the channel

### **Commands**

- `!state` - Show your cognitive state (trust, hurt, mood, neurochemicals, memories)
- `!memory` - Show your memories (STM, episodic, identity)
- `!reset` - Reset your state (for testing)
- `!help` - Show available commands

---

## 🔧 Features

### **✅ Implemented:**
1. **Full Cognitive Pipeline**
   - All 19 stages integrated
   - Memory, psyche, personality, QMAS, etc.
   - Neurochemical-driven behavior

2. **Private DMs**
   - Each user gets their own state
   - Private conversations
   - State persists across sessions

3. **State Inspection**
   - `!state` command shows current cognitive state
   - `!memory` command shows memories
   - `!reset` command for testing

4. **Error Handling**
   - Graceful degradation
   - Error messages to users
   - Logging for debugging

### **⚠️ Not Yet Implemented:**
1. **Initiative Engine (Autonomous Messaging)**
   - Bot can message users autonomously
   - Respects DND settings
   - Natural timing
   - (Code structure is there, needs Discord user object storage)

2. **Message History**
   - Currently only uses current message
   - Should store conversation history in state
   - (Can be added easily)

3. **Slash Commands**
   - Modern Discord commands
   - (Can be added easily)

---

## 🐛 Troubleshooting

### **Bot doesn't respond:**
1. Check bot is online (green dot in Discord)
2. Check MESSAGE CONTENT INTENT is enabled
3. Check bot has permissions in channel
4. Check console for errors

### **"Missing HF_TOKEN" error:**
- Set `HF_TOKEN` environment variable
- Get token from https://huggingface.co/settings/tokens

### **"Missing DISCORD_TOKEN" error:**
- Set `DISCORD_TOKEN` environment variable
- Get token from Discord Developer Portal

### **Bot crashes:**
- Check console for error messages
- Make sure all dependencies are installed
- Check database file permissions (`state.db`)

---

## 📊 Storage

**State is stored in:** `backend/state.db` (SQLite)

**Each user gets:**
- User ID: `discord_123456789` (Discord user ID)
- Full 28K JSON state
- Persistent across sessions

**To backup:**
```bash
cp backend/state.db backend/state.db.backup
```

**To reset all users:**
```bash
rm backend/state.db
# Will recreate on next run
```

---

## 🚀 Next Steps

### **Phase 1: Basic Testing (Now)**
1. ✅ Bot responds to DMs
2. ✅ Bot responds to mentions
3. ✅ Commands work
4. Test with multiple users
5. Observe state evolution

### **Phase 2: Enhancements (Next)**
1. Add message history storage
2. Add initiative engine (autonomous messaging)
3. Add slash commands
4. Add logging/monitoring
5. Add test channels

### **Phase 3: Production (Later)**
1. Add rate limiting
2. Add content moderation
3. Add structured logging
4. Add analytics
5. Deploy to server

---

## 💡 Tips

1. **Test in DMs first** - More private, easier to debug
2. **Use `!state` frequently** - See how state evolves
3. **Use `!reset` for testing** - Start fresh when needed
4. **Check console logs** - See what's happening
5. **Test with multiple users** - Each gets their own AI companion

---

## 📝 Notes

- **Discord Rate Limits:** Bot respects Discord's rate limits automatically
- **State Persistence:** State persists across bot restarts
- **Concurrent Users:** SQLite handles multiple users (with locking)
- **Privacy:** Each user's state is separate and private

---

**Ready to test! Start chatting with your AI companion!** 🎉

