# 🚀 START HERE - Get Your Discord Bot Running

## Step-by-Step Guide (15 minutes)

### **Step 1: Install Discord.py** (2 minutes)

```bash
cd backend
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install discord.py
```

---

### **Step 2: Create Discord Bot** (5 minutes)

1. **Go to:** https://discord.com/developers/applications
2. **Click:** "New Application"
3. **Name it:** "Emotion Agent" (or whatever you want)
4. **Click:** "Create"
5. **Go to:** "Bot" section (left sidebar)
6. **Click:** "Add Bot" → "Yes, do it!"
7. **Scroll down** to "Privileged Gateway Intents"
8. **Enable these:**
   - ✅ **MESSAGE CONTENT INTENT** (REQUIRED!)
   - ✅ SERVER MEMBERS INTENT (optional)
9. **Click:** "Reset Token" → Copy the token
10. **SAVE THE TOKEN!** You'll need it in Step 4

---

### **Step 3: Invite Bot to Your Server** (3 minutes)

1. **In Discord Developer Portal**, go to **"OAuth2"** → **"URL Generator"**
2. **Select Scopes:**
   - ✅ `bot`
   - ✅ `applications.commands` (optional)
3. **Select Bot Permissions:**
   - ✅ Send Messages
   - ✅ Read Message History
   - ✅ Read Messages/View Channels
4. **Copy the generated URL** (at the bottom)
5. **Open URL in browser**
6. **Select your Discord server**
7. **Click:** "Authorize"

---

### **Step 4: Set Environment Variables** (2 minutes)

**Option A: Create `.env` file (Recommended)**

Create file: `backend/.env`

```bash
DISCORD_TOKEN=your_discord_bot_token_here
HF_TOKEN=your_huggingface_token_here
```

**Option B: Export in terminal**

```bash
export DISCORD_TOKEN="your_discord_bot_token_here"
export HF_TOKEN="your_huggingface_token_here"
```

**Where to get tokens:**
- **DISCORD_TOKEN:** From Step 2 (Discord Developer Portal → Bot → Token)
- **HF_TOKEN:** From https://huggingface.co/settings/tokens

---

### **Step 5: Run the Bot** (1 minute)

```bash
cd backend
source venv/bin/activate  # If not already activated
python discord_bot.py
```

**You should see:**
```
🚀 Starting Discord bot...
✅ BotName#1234 has logged in!
Bot is in 1 guilds
```

**If you see errors:**
- Check tokens are set correctly
- Check MESSAGE CONTENT INTENT is enabled
- Check all dependencies installed: `pip install -r requirements.txt`

---

## ✅ Test It!

### **Test in DMs:**
1. Open Discord
2. Find your bot in server member list
3. Right-click bot → **"Message"**
4. Send: `Hello!`
5. Bot should respond!

### **Test in Channel:**
1. Go to any channel
2. Type: `@BotName hello`
3. Bot should respond!

### **Test Commands:**
- `!state` - See cognitive state
- `!memory` - See memories
- `!reset` - Reset state
- `!help` - Show commands

---

## 🐛 Troubleshooting

### **"Missing DISCORD_TOKEN" error:**
- Set `DISCORD_TOKEN` environment variable
- Or create `backend/.env` file with token

### **"Missing HF_TOKEN" error:**
- Set `HF_TOKEN` environment variable
- Get token from: https://huggingface.co/settings/tokens

### **Bot doesn't respond:**
- ✅ Check bot is online (green dot in Discord)
- ✅ Check MESSAGE CONTENT INTENT is enabled
- ✅ Check bot has permissions in channel
- ✅ Check console for errors

### **Bot crashes:**
- Check console for error messages
- Install dependencies: `pip install -r requirements.txt`
- Check `state.db` file permissions

---

## 🎯 What Happens Next

1. **Bot responds** using full cognitive pipeline
2. **State evolves** - trust, hurt, mood, neurochemicals update
3. **Memory forms** - bot remembers you, patterns, relationship
4. **Relationship grows** - over time, bot learns and adapts

---

## 💡 Quick Tips

- **Start with DMs** - More private, easier to test
- **Use `!state`** - See cognitive state evolve
- **Test over days** - See relationship grow
- **Watch console** - See what's happening

---

## 📝 Files You Need

- ✅ `backend/discord_bot.py` - Bot code (already created)
- ✅ `backend/.env` - Your tokens (you create this)
- ✅ `backend/state.db` - State database (created automatically)

---

**That's it! Follow these 5 steps and you'll be chatting with your AI companion!** 🎉

**Need help?** Check `DISCORD_BOT_SETUP.md` for detailed troubleshooting.

