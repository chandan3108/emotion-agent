# Name Memory: How "My Name is Chandan" is Stored

## Quick Answer

**NO, the name is NOT remembered immediately as identity memory.**

**Current behavior:**
1. ✅ Goes to **STM (Short-Term Memory)** immediately
2. ❌ Does NOT go to identity memory immediately
3. ❌ Would NOT be promoted even if mentioned repeatedly (current limitation)

---

## Detailed Explanation

### What Happens When You Say "My name is Chandan"

#### Step 1: STM (Short-Term Memory) - ✅ IMMEDIATE

**Location:** `backend/memory.py:77-94`

Every user message goes to STM automatically:
- ✅ Stored immediately
- ✅ Available during current conversation
- ⚠️ Decays after 30 minutes
- ⚠️ Expires after 2 hours

**Storage:**
```python
# Every message goes to STM (automatic)
self.memory.add_stm(user_message, emotion_vector, perception_output)
```

**Your name "Chandan" is in STM:**
```json
{
  "content": "My name is Chandan",
  "timestamp": "2024-01-15T10:30:00Z",
  "emotion_vector": {"valence": 0.0, "arousal": 0.0},
  "perception_output": {...}
}
```

**The LLM can see STM in the prompt**, so during the current conversation, the AI knows your name from STM.

#### Step 2: Pattern Detection - ❌ NOT DETECTED

**Location:** `backend/pattern_detector.py:36-100`

The pattern detector only looks for **routine patterns**:
```python
routine_keywords = [
    "class", "gym", "work", "study", "meeting", "practice", "training",
    "every", "usually", "always", "typically", "routine", "schedule"
]

has_routine_indicator = any(keyword in message_lower for keyword in routine_keywords)

if not has_routine_indicator:
    return None  # No pattern detected
```

**"My name is Chandan" contains none of these keywords**, so:
- ❌ Pattern detection returns `None`
- ❌ No pattern candidate is created
- ❌ Name is NOT tracked for promotion

#### Step 3: Identity Memory Promotion - ❌ NOT POSSIBLE

**Location:** `backend/cognitive_core.py:695-719`, `backend/memory.py:247-273`

Identity memory promotion requires:
1. Pattern candidate exists (from pattern detection)
2. Pattern Confidence (PC) ≥ 0.75
3. 14+ distinct days
4. 8+ occurrences
5. < 3 contradictions

**Since no pattern candidate was created, promotion is impossible.**

---

## Current Limitation

**The system does NOT have special handling for identity facts like names.**

- ✅ STM: Works (name is in STM during conversation)
- ❌ Identity Memory: Does NOT work (name is not promoted)
- ❌ Episodic Memory: Only for emotionally salient events (name introduction is not emotional enough)

**Result:**
- Name is remembered **during the current conversation** (from STM)
- Name is **forgotten after 2 hours** (STM expires)
- Name is **NOT stored long-term** (no identity memory)

---

## Where Your Name Actually Lives

### During Conversation (0-2 hours):

**STM (Short-Term Memory):**
```python
# Stored in: state["memory_hierarchy"]["stm"]
[
  {
    "content": "My name is Chandan",
    "timestamp": "2024-01-15T10:30:00Z",
    ...
  }
]
```

**Accessible in prompt:**
```
RELEVANT MEMORIES:
- Recent: My name is Chandan...
```

### After 2 Hours:

**Gone** - STM expires, name is forgotten.

---

## How to Make Names Work (Current System)

**Option 1: Mention Name Repeatedly (BUT IT WON'T WORK)**

Even if you mention your name 8+ times over 14+ days, it still won't be promoted because:
- Pattern detector only looks for routine keywords
- Name doesn't match routine patterns
- No pattern candidate = no promotion

**Option 2: Use Name in Routine Context (MIGHT WORK)**

If you say things like:
- "Chandan goes to class at 10am"
- "I, Chandan, always study in the evening"

The pattern detector might pick up "goes to class" or "always study", but the name itself wouldn't be extracted.

**Option 3: Wait for Enhanced Implementation**

The code comments say:
```python
# In production, use LLM to extract structured routine information
# In production, use LLM to extract: "goes to gym Tues/Thurs" or "has class at 10am"
```

**A proper implementation would:**
1. Use LLM to extract identity facts (names, jobs, preferences, etc.)
2. Store them as pattern candidates immediately
3. Promote them to identity after meeting criteria (or immediately for high-confidence facts like names)

---

## What the Blueprint Says

The blueprint (`hello.txt`) doesn't explicitly mention name handling, but identity memory is supposed to store "facts about user (confidence ≥0.75)".

**Names should probably be:**
- Detected immediately (high confidence, explicit statement)
- Stored as identity memory (not requiring 14+ days, 8+ occurrences)
- But the current implementation doesn't do this

---

## Summary

| Question | Answer |
|----------|--------|
| **Is name remembered immediately?** | ❌ No (only in STM, not identity memory) |
| **Where is it stored?** | STM (Short-Term Memory) only |
| **Is it stored long-term?** | ❌ No (STM expires after 2 hours) |
| **Can it be promoted to identity?** | ❌ No (current pattern detector doesn't handle names) |
| **Does the AI know my name during conversation?** | ✅ Yes (from STM, visible in prompt) |
| **Does the AI remember my name later?** | ❌ No (STM expires, no identity memory) |

**This is a limitation that should be fixed** - names and basic identity facts should be stored immediately in identity memory with high confidence, not require the routine pattern promotion process.

