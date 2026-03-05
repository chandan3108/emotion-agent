# Discord Bot Setup - Step by Step Guide

## 🎯 You're on the Information Page - Here's What to Do Next

### **Step 1: Enable Bot (If Not Done)**

1. **Look at the left sidebar** - you should see:
   - Information
   - OAuth2
   - **Bot** ← Click this!
   - etc.

2. **Click "Bot"** (left sidebar)

3. **Click "Add Bot"** (if you see this button)
   - Click "Yes, do it!"

4. **Scroll down** to find **"Privileged Gateway Intents"**

5. **Enable these:**
   - ✅ **MESSAGE CONTENT INTENT** (REQUIRED!)
   - ✅ SERVER MEMBERS INTENT (optional)

6. **Click "Save Changes"** (if you made changes)

---

### **Step 2: Get Your Bot Token**

1. **Still on the "Bot" page**
2. **Look for "Token"** section
3. **Click "Reset Token"** or **"Copy"**
4. **Copy the token** (looks like: `MTQ1NjY1MjAwNjg2MDEzMjQyMw.GZCtbi...`)
5. **Save it somewhere safe**

**Note:** You already gave me this token, so you can skip this if you want.

---

### **Step 3: Invite Bot to Server (URL Generator)**

1. **Click "OAuth2"** in the left sidebar
2. **Click "URL Generator"** (NOT "General" - that's different!)
3. **In "Scopes" section**, check:
   - ✅ `bot`
   - ✅ `applications.commands` (optional)
4. **Scroll down** to "Bot Permissions"
5. **Check these permissions:**
   - ✅ Send Messages
   - ✅ Read Message History
   - ✅ Read Messages/View Channels
6. **Scroll to bottom** - you'll see a **"Generated URL"**
7. **Copy that URL**
8. **Open the URL in your browser**
9. **Select your Discord server**
10. **Click "Authorize"**

**Done!** Your bot is now in your server! ✅

---

## 📍 Where You Are Now

**You're on:** `https://discord.com/developers/applications/1456652006860132423/information`

**This is the "Information" page** - it's just general info about your app.

**What to do:**
1. Click **"Bot"** (left sidebar) → Enable MESSAGE CONTENT INTENT
2. Click **"OAuth2"** → **"URL Generator"** → Generate invite URL

---

## 🎯 Quick Navigation

**From Information page:**

1. **Left sidebar** → Click **"Bot"**
   - Enable MESSAGE CONTENT INTENT
   - Copy token (if needed)

2. **Left sidebar** → Click **"OAuth2"**
   - Click **"URL Generator"** tab
   - Select `bot` scope
   - Select permissions
   - Copy generated URL
   - Open URL → Authorize

---

## ✅ Checklist

- [ ] Go to **"Bot"** page
- [ ] Enable **MESSAGE CONTENT INTENT**
- [ ] Go to **"OAuth2"** → **"URL Generator"**
- [ ] Select `bot` scope
- [ ] Select bot permissions
- [ ] Copy generated URL
- [ ] Open URL → Authorize bot to server
- [ ] Bot appears in your server!

---

## 🐛 Common Confusion

### **"OAuth2" has two tabs:**
- **"General"** - For web apps (asks for redirect URL) ❌ Don't use this
- **"URL Generator"** - For bot invitations ✅ Use this!

**Use "URL Generator" - it doesn't ask for redirect URL!**

---

## 💡 Visual Guide

**Left Sidebar Navigation:**
```
📁 Your Application
  ├── 📄 Information (you're here)
  ├── 🔐 OAuth2
  │     ├── General (skip this)
  │     └── URL Generator ← USE THIS!
  ├── 🤖 Bot ← GO HERE FIRST!
  ├── ...
```

**Steps:**
1. Click **🤖 Bot** → Enable intents
2. Click **🔐 OAuth2** → **URL Generator**
3. Generate invite URL
4. Authorize bot

---

## 🚀 After Bot is Invited

Once bot is in your server:

1. **Run the bot:**
   ```bash
   cd backend
   python discord_bot.py
   ```

2. **Test it:**
   - Send DM to bot: `Hello!`
   - Or mention: `@BotName hello`

3. **Use commands:**
   - `!state` - See cognitive state
   - `!memory` - See memories
   - `!help` - Show commands

---

**Follow these steps and you'll have your bot running!** 🎉

