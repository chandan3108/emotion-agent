# How to Run Discord Bot - Fixed!

## ✅ Import Error Fixed!

The bot now handles imports correctly. Here's how to run it:

---

## 🚀 Method 1: Run as Module (Recommended)

**From the `emotion-agent` folder (parent directory):**

```bash
cd /Users/chandu/Downloads/emotion-agent
cd backend
source venv/bin/activate
python -m backend.discord_bot
```

**Or from backend folder:**

```bash
cd backend
source venv/bin/activate
python -m backend.discord_bot
```

---

## 🚀 Method 2: Use Run Script

I created a simple script for you:

```bash
cd /Users/chandu/Downloads/emotion-agent
./run_discord_bot.sh
```

---

## 🚀 Method 3: Direct Run (Should Work Now)

The imports are fixed, so this should work:

```bash
cd backend
source venv/bin/activate
python discord_bot.py
```

---

## ✅ What You Should See

```
🚀 Starting Discord bot...
Make sure you have:
  - DISCORD_TOKEN set in environment
  - HF_TOKEN set in environment
  - Bot has MESSAGE CONTENT INTENT enabled in Discord Developer Portal
✅ REM#1234 has logged in!
Bot is in 1 guilds
```

**If you see this, it's working!** ✅

---

## 🐛 If You Still Get Errors

### **"Module not found":**
```bash
pip install -r requirements.txt
```

### **"DISCORD_TOKEN not found":**
- Check `.env` file exists in `backend/` folder
- Check tokens are correct

### **Other errors:**
- Check console output for specific error
- Make sure virtual environment is activated

---

## 🎯 Quick Command

**Just run this:**

```bash
cd /Users/chandu/Downloads/emotion-agent/backend
source venv/bin/activate
python -m backend.discord_bot
```

**That's it!** 🎉

