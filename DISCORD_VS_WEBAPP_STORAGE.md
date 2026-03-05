# Discord Bot vs Web App: Testing & Storage

## 💾 Where Everything Is Stored

### **Current Storage: SQLite Database**

**Location:** `backend/state.py` → `state.db` (SQLite file)

**What's Stored:**
```python
# Each user gets a complete 28K JSON state stored in SQLite:
{
    "core_personality": {...},           # Big Five, attachment style, etc.
    "current_psyche": {...},             # Trust, hurt, forgiveness state
    "mood": {...},                       # 14-dimensional mood vector
    "memory_hierarchy": {
        "stm": [...],                    # Short-term memory
        "act_threads": [...],            # Active conversational threads
        "episodic": [...],               # Emotionally salient events
        "identity": [...],                # Promoted facts about user
        "milestones": [...],              # Relationship pivots
        "promises": [...],                # Tracked promises
        "morals": [...]                   # Injury flags
    },
    "neurochem_vector": {...},           # DA, CORT, OXY, SER, NE
    "relationship_ledger": {...},        # Reciprocity entries
    "theory_of_mind": {...},             # User state predictions
    "temporal_context": {...},           # Time deltas, circadian phase
    "habits_cpbm": {...},                # Learned conversational patterns
    "embodiment": {...},                 # Energy, capacity, sleep debt
    "qmas_state": {...},                 # Last QMAS path
    "metadata": {...}                    # Created/updated timestamps
}
```

**Storage Details:**
- **Database:** SQLite (`state.db` file)
- **Format:** JSON stored as TEXT in SQLite
- **Location:** Defaults to `backend/state.db` (can be configured)
- **Thread-safe:** Uses `threading.RLock()` for concurrent access
- **Atomic updates:** All state changes are atomic
- **Per-user:** Each user_id gets their own state row

**File Structure:**
```
backend/
  ├── state.db                    # SQLite database (created automatically)
  │   └── user_state table
  │       ├── user_id (PRIMARY KEY)
  │       ├── state_json (TEXT - 28K JSON)
  │       └── updated_at (TIMESTAMP)
  └── state.py                    # State orchestrator
```

**Note:** There's also a `db.py` with PostgreSQL setup, but that's for the old system. The new cognitive architecture uses SQLite.

---

## 🤖 Discord Bot vs Web App: Testing Comparison

### **Discord Bot: PROS ✅**

1. **Easier to Test**
   - Natural conversation flow (like texting)
   - Multiple users can test simultaneously
   - Real-time interaction
   - No UI to build/maintain

2. **Better for Long-Term Testing**
   - Users can chat over days/weeks
   - Natural growth trajectory
   - Easy to observe memory/relationship evolution
   - Can test initiative engine (autonomous messaging)

3. **Lower Barrier to Entry**
   - Users just join Discord server
   - No app installation
   - Works on all platforms
   - Familiar interface

4. **Easier to Debug**
   - Can see all messages in Discord
   - Easy to log/debug
   - Can create test channels
   - Can reset user state easily

5. **Better for Observing Growth**
   - Can watch relationship develop over time
   - Multiple users = multiple growth trajectories
   - Easy to compare different personalities
   - Can test conflict resolution naturally

6. **Cost Effective**
   - No hosting needed (runs on your machine/server)
   - Discord handles infrastructure
   - Free for testing

### **Discord Bot: CONS ❌**

1. **No Emotion Detection**
   - Can't use face/voice emotion detection
   - Only text-based
   - Missing perception layer features

2. **Limited UI**
   - Can't show typing indicators naturally
   - Can't show burst patterns well
   - Limited formatting options

3. **Discord-Specific**
   - Tied to Discord platform
   - Can't easily port to other platforms
   - Discord rate limits

4. **Privacy Concerns**
   - Messages visible in Discord
   - Less private than 1-on-1 web app
   - State stored locally (but can be shared)

### **Web App: PROS ✅**

1. **Full Feature Set**
   - Can use face/voice emotion detection
   - Can show typing indicators
   - Can show burst patterns
   - Full UI control

2. **Better UX**
   - Custom interface
   - Can show memory/state visually
   - Can show neurochemicals (for debugging)
   - Better for demos

3. **More Professional**
   - Looks more polished
   - Better for presentations
   - Can add features like memory review

4. **Privacy**
   - 1-on-1 conversations
   - More private
   - Better for sensitive topics

### **Web App: CONS ❌**

1. **More Complex**
   - Need to build/maintain UI
   - Frontend + backend coordination
   - More moving parts

2. **Harder to Test**
   - Need to deploy
   - Users need to sign up
   - More setup required

3. **Less Natural**
   - Web interface feels less like texting
   - Harder to test long-term growth
   - More artificial

4. **Cost**
   - Need hosting
   - More infrastructure
   - More expensive

---

## 🎯 Recommendation: **Start with Discord Bot**

### **Why Discord Bot First:**

1. **Faster to Build**
   - Discord.py library is simple
   - Can have working bot in hours
   - No frontend needed

2. **Better for Testing**
   - Natural conversation flow
   - Easy to test long-term growth
   - Multiple users simultaneously
   - Easy to observe memory/relationship evolution

3. **Easier to Debug**
   - All messages visible
   - Easy to log/debug
   - Can reset state easily
   - Can create test channels

4. **Better for Observing Growth**
   - Can watch relationship develop over days/weeks
   - Multiple users = multiple growth trajectories
   - Easy to test conflict resolution
   - Can test initiative engine naturally

5. **Lower Cost**
   - No hosting needed
   - Discord handles infrastructure
   - Free for testing

### **Then Build Web App Later**

Once the cognitive architecture is tested and working:
- Build web app with full features
- Add emotion detection
- Add visual state debugging
- Better UX for production

---

## 🚀 Discord Bot Implementation

### **Quick Start:**

```python
# backend/discord_bot.py
import discord
from discord.ext import commands
from .cognitive_core import CognitiveCore
import asyncio

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'{bot.user} has logged in!')

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    
    # Get user_id (Discord user ID)
    user_id = str(message.author.id)
    
    # Initialize cognitive core
    core = CognitiveCore(user_id=user_id)
    
    # Process message
    processing_result = await core.process_message(
        message.content,
        emotion_data=None  # Discord doesn't have emotion detection
    )
    
    # Generate response
    # (Use agent.py logic to generate response)
    
    # Send response
    await message.channel.send(response_text)

bot.run('YOUR_DISCORD_TOKEN')
```

### **Features to Add:**

1. **Private DMs**
   - Each user gets their own AI companion
   - State stored per user_id
   - Private conversations

2. **Initiative Engine**
   - Bot can message users autonomously
   - Respects DND settings
   - Natural timing

3. **State Inspection**
   - `!state` command to see current state
   - `!memory` to see memories
   - `!reset` to reset state (for testing)

4. **Test Channels**
   - Create test channels for different scenarios
   - Easy to reset/test

---

## 📊 Storage Architecture

### **Current: SQLite (Perfect for Testing)**

```
backend/state.db (SQLite)
├── user_state table
│   ├── user_id: "discord_123456789"
│   ├── state_json: "{...28K JSON...}"
│   └── updated_at: "2024-01-15T10:30:00Z"
```

**Pros:**
- ✅ Simple (single file)
- ✅ Fast (0.5ms P99 read, 2.5ms P99 write)
- ✅ Thread-safe
- ✅ Atomic updates
- ✅ Perfect for testing
- ✅ Easy to backup (just copy file)
- ✅ No setup needed

**Cons:**
- ❌ Not scalable (single file)
- ❌ Not distributed (can't share across servers)
- ❌ Limited concurrent writes

### **Future: PostgreSQL/Redis (For Production)**

**PostgreSQL:**
- Better for production
- Scalable
- Can handle concurrent users
- Better for analytics

**Redis:**
- Faster reads
- Better for caching
- Can use as cache + PostgreSQL as persistent

**Migration Path:**
```python
# Can easily swap storage backends
class StateOrchestrator:
    def __init__(self, backend="sqlite"):  # or "postgresql" or "redis"
        if backend == "sqlite":
            self.storage = SQLiteStorage()
        elif backend == "postgresql":
            self.storage = PostgreSQLStorage()
        elif backend == "redis":
            self.storage = RedisStorage()
```

---

## 🎯 Action Plan

### **Phase 1: Discord Bot (This Week)**
1. Install discord.py
2. Create basic bot
3. Integrate cognitive_core
4. Test with multiple users
5. Observe growth over days/weeks

### **Phase 2: Enhance Discord Bot (Next Week)**
1. Add initiative engine (autonomous messaging)
2. Add state inspection commands
3. Add test channels
4. Add logging/monitoring

### **Phase 3: Web App (Later)**
1. Once cognitive architecture is tested
2. Build web app with full features
3. Add emotion detection
4. Add visual debugging
5. Better UX for production

---

## 💡 Bottom Line

**For Testing:** **Discord Bot is Better**
- Faster to build
- Easier to test
- Better for observing growth
- Natural conversation flow
- Multiple users simultaneously

**For Production:** **Web App is Better**
- Full feature set
- Better UX
- More professional
- Privacy

**Storage:** **SQLite is Perfect for Testing**
- Simple, fast, thread-safe
- Easy to backup
- Can migrate to PostgreSQL later

**Recommendation:** Start with Discord bot, test thoroughly, then build web app once architecture is proven.

