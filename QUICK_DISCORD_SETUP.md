# Quick Discord Setup - Simple Steps

## 🎯 Right Now: You're on the Information Page

**Do this:**

### **1. Click "Bot" (Left Sidebar)**

- Enable **MESSAGE CONTENT INTENT** ✅
- Save changes

### **2. Click "OAuth2" → "URL Generator"**

- Check `bot` scope
- Check permissions (Send Messages, Read Messages)
- Copy the generated URL
- Open URL → Authorize

**That's it!** ✅

---

## 📝 Detailed Steps

### **Step 1: Bot Page**

1. **Left sidebar** → Click **"Bot"**
2. Scroll to **"Privileged Gateway Intents"**
3. Enable: **MESSAGE CONTENT INTENT** ✅
4. Click **"Save Changes"**

### **Step 2: Invite Bot**

1. **Left sidebar** → Click **"OAuth2"**
2. Click **"URL Generator"** tab (top of page)
3. **Scopes:** Check `bot`
4. **Bot Permissions:** Check:
   - Send Messages
   - Read Message History
   - Read Messages/View Channels
5. **Scroll down** → See "Generated URL"
6. **Copy URL**
7. **Open in browser** → Select server → **Authorize**

---

## ✅ Done!

Bot is now in your server. Run:

```bash
cd backend
python discord_bot.py
```

**Need more help?** See `DISCORD_SETUP_STEP_BY_STEP.md`

