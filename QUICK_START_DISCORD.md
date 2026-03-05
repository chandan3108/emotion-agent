# Quick Start: Discord Bot 🚀

## What You Need to Do

### **1. Install Discord.py** (2 minutes)

```bash
cd backend
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install discord.py
```

### **2. Create Discord Bot** (5 minutes)

1. Go to: https://discord.com/developers/applications
2. Click **"New Application"**
3. Name it: "Emotion Agent" (or whatever you want)
4. Go to **"Bot"** section (left sidebar)
5. Click **"Add Bot"**
6. **CRITICAL:** Scroll down to **"Privileged Gateway Intents"**
   - ✅ Enable **"MESSAGE CONTENT INTENT"** (required!)
   - ✅ Enable **"SERVER MEMBERS INTENT"** (optional)
7. Click **"Reset Token"** → Copy the token
8. **Save the token!** You'll need it.

### **3. Invite Bot to Your Server** (2 minutes)

1. In Discord Developer Portal, go to **"OAuth2"** → **"URL Generator"**
2. Select **Scopes:**
   - ✅ `bot`
   - ✅ `applications.commands` (optional)
3. Select **Bot Permissions:**
   - ✅ Send Messages
   - ✅ Read Message History
   - ✅ Read Messages/View Channels
4. Copy the generated URL
5. Open URL in browser → Select your server → **Authorize**

### **4. Set Environment Variables** (1 minute)

Create `.env` file in `backend/` directory:

```bash
# backend/.env
DISCORD_TOKEN=your_discord_bot_token_here
HF_TOKEN=your_huggingface_token_here
```

**OR** export them:

```bash
export DISCORD_TOKEN="your_token_here"
export HF_TOKEN="your_hf_token_here"
```

### **5. Run the Bot** (1 minute)

```bash
cd backend
source venv/bin/activate
python discord_bot.py
```

You should see:
```
🚀 Starting Discord bot...
✅ BotName#1234 has logged in!
Bot is in 1 guilds
```

---

## ✅ Done! Now Test It

### **Test in DMs:**
1. Open Discord
2. Find your bot in the server member list
3. Right-click → **"Message"**
4. Send: `Hello!`
5. Bot should respond!

### **Test in Channel:**
1. Go to any channel
2. Type: `@BotName hello`
3. Bot should respond!

### **Test Commands:**
- `!state` - See your cognitive state
- `!memory` - See your memories
- `!reset` - Reset your state (for testing)
- `!help` - Show commands

---

## 🎯 What Happens

1. **You send a message** → Bot processes it through full cognitive pipeline
2. **Bot responds** → Using memory, psyche, personality, QMAS, etc.
3. **State evolves** → Trust, hurt, mood, neurochemicals all update
4. **Memory forms** → Bot remembers you, your patterns, your relationship
5. **Relationship grows** → Over time, bot learns and adapts to you

---

## 🐛 Troubleshooting

### **Bot doesn't respond:**
- ✅ Check bot is online (green dot)
- ✅ Check MESSAGE CONTENT INTENT is enabled
- ✅ Check bot has permissions
- ✅ Check console for errors

### **"Missing DISCORD_TOKEN":**
- Set `DISCORD_TOKEN` environment variable
- Get token from Discord Developer Portal

### **"Missing HF_TOKEN":**
- Set `HF_TOKEN` environment variable
- Get from: https://huggingface.co/settings/tokens

### **Bot crashes:**
- Check console for error messages
- Make sure all dependencies installed: `pip install -r requirements.txt`
- Check `state.db` file permissions

---

## 📊 What's Stored

**State:** `backend/state.db` (SQLite)

**Each user gets:**
- Their own AI companion state
- Persistent memory
- Evolving relationship
- All cognitive features

**To backup:**
```bash
cp backend/state.db backend/state.db.backup
```

---

## 🚀 Next Steps

1. **Chat with the bot** - See how it responds
2. **Use `!state`** - Watch state evolve
3. **Test over days** - See relationship grow
4. **Test conflicts** - See how bot handles hurt/forgiveness
5. **Test memory** - See what bot remembers

---

## 💡 Tips

- **Start with DMs** - More private, easier to test
- **Use `!state` frequently** - See cognitive state
- **Test with multiple users** - Each gets their own AI
- **Watch console logs** - See what's happening
- **Be patient** - Bot needs time to learn and grow

---

**That's it! You're ready to test your AI companion!** 🎉

See `DISCORD_BOT_SETUP.md` for more detailed documentation.

