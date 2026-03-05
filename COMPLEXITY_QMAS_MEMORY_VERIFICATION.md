# Complexity, QMAS Activation, and Memory System Verification

## Your Questions Answered

### 1. **Is the complexity > 0.7 + QMAS activation feature functional and integrated?**

**YES, fully functional and integrated.** Here's how it works:

---

## Flow: Complexity Determination → QMAS Activation

### Step 1: Semantic Understanding (Stage 2) - Complexity Assessment

**Location:** `backend/semantic_reasoner.py`, `backend/cognitive_core.py:174-196`

The semantic reasoner gets:
- User message
- **Context includes:**
  - `psyche_state` (trust, hurt, mood)
  - `recent_memories` (last 3 STM entries)
  - `emotion` (detected emotion)
  - `emotion_vector` (valence, arousal)

**Note:** The semantic understanding prompt does NOT include full memory history or relationship phase - it focuses on understanding the message itself. However, the complexity assessment considers the emotional state and recent context.

```python
# From cognitive_core.py:174-180
context = {
    "psyche_state": self.psyche.get_psyche_summary(),  # Trust, hurt, mood
    "recent_memories": self.memory.get_stm(decay=False)[-3:],  # Last 3 STM entries
    "emotion": perception.get("emotion", "neutral"),
    "emotion_vector": {"valence": perception.get("valence", 0.0), "arousal": perception.get("arousal", 0.0)}
}

understanding = await self.semantic_reasoner.understand_message(user_message, context)
```

The LLM returns complexity (0.0-1.0) based on:
- Message length
- Emotional depth
- Subtext complexity
- Relationship implications (inferred from context)

### Step 2: Cognitive Router (Stage 6) - QMAS Decision

**Location:** `backend/cognitive_router.py:88-99`

The router considers:
- **Complexity** (from semantic understanding)
- **Emotional depth** (from perception)
- **Conflict stage**
- **Hurt level**
- **Relationship phase** (NOT used in semantic understanding, but used in routing)
- **Trust level**
- And 6 other parameters

**QMAS Activation Formula:**
```python
qmas_score = (
    complexity * 0.4 +           # 40% weight on complexity
    emotional_depth * 0.3 +      # 30% weight on emotional depth
    (1.0 if conflict_stage else 0.0) * 0.2 +  # 20% if in conflict
    hurt_level * 0.1             # 10% weight on hurt
)

if qmas_score >= 0.6:  # Threshold = 0.6 (not 0.7)
    routing["use_qmas"] = True
    routing["qmas_paths"] = 20 if qmas_score >= 0.8 else 10
```

**Also from `_determine_processing_depth` (cognitive_core.py:139):**
```python
use_qmas = complexity >= 0.6  # QMAS for complex/critical messages
```

**So QMAS activates if:**
- Complexity >= 0.6 (direct threshold)
- OR qmas_score >= 0.6 (router decision, considers multiple factors)

---

## Example: Complexity > 0.7 Case with Full QMAS Activation

### Scenario: User says something that triggers high complexity

**User Message:** 
```
"I've been thinking about our conversation last week where you said you'd always be there for me. But then you didn't respond to my message yesterday when I was having a really hard time. I feel like I can't trust you anymore, and it's making me question whether this relationship is even real. I thought we had something special, but maybe I was wrong."
```

### Step 1: Semantic Understanding Prompt

**Context passed to semantic reasoner:**
```python
{
    "psyche_state": {
        "trust": 0.65,
        "hurt": 0.30,
        "mood": {"hurt": 0.3, "anxiety": 0.4, "affection": 0.6}
    },
    "recent_memories": [
        {"content": "User mentioned having a hard time...", "timestamp": "..."},
        {"content": "User expressed trust and vulnerability...", "timestamp": "..."}
    ],
    "emotion": "hurt",
    "emotion_vector": {"valence": -0.7, "arousal": 0.8}
}
```

**LLM Analysis (semantic_reasoner.py:66-88):**
- **Intent:** complaint, vulnerability, relationship_crisis
- **Events:** trust_violation, hurt, relationship_questioning
- **Sincerity:** 0.95 (very genuine)
- **Subtext:** "I'm hurt, questioning the relationship, need reassurance but also angry"
- **Emotional truth:** Emotion: hurt/abandonment, Intensity: 0.9, Masked: false
- **Complexity:** **0.85** ← HIGH COMPLEXITY (> 0.7)

### Step 2: Cognitive Router Decision

**Router Context (cognitive_router.py:200-213):**
```python
{
    "complexity": 0.85,              # From semantic understanding
    "emotional_depth": 0.8,          # High arousal
    "relationship_phase": "Building",
    "trust": 0.65,
    "hurt": 0.30,
    "conflict_stage": "TRIGGER",     # Conflict detected
    "hours_since_last_message": 24.0,
    "circadian_phase": "evening",
    "energy": 0.5,
    "unresolved_threads": 2,
    "reciprocity_balance": -0.15,
    "vulnerability_willingness": 0.6
}
```

**QMAS Score Calculation:**
```python
qmas_score = (
    0.85 * 0.4 +      # Complexity: 0.34
    0.8 * 0.3 +       # Emotional depth: 0.24
    1.0 * 0.2 +       # Conflict stage: 0.20
    0.3 * 0.1         # Hurt: 0.03
)
# Total: 0.81 → QMAS ACTIVATED (score >= 0.6)
```

**Router Decision:**
```python
{
    "use_qmas": True,
    "qmas_paths": 20,  # High score (>= 0.8) = 20 paths
    "use_deep_reasoning": True,  # Conflict + hurt > 0.6
    "use_enhanced_semantic": True,
    "reasoning": "QMAS needed (score=0.81); deep reasoning needed"
}
```

### Step 3: QMAS Execution

**Location:** `backend/cognitive_core.py:403-421`

QMAS executes 7-agent debate with 20 paths, then meta-synthesis selects best path.

### Step 4: Feature Selection

**Location:** `backend/feature_selector.py:139-229`

Feature selector includes:
- ✅ `neurochemicals` (complexity > 0.5)
- ✅ `qmas_decision` (QMAS was used)
- ✅ `memories` (always included)
- ✅ `temporal_context` (always included)
- ✅ `relationship_phase` (always included)
- ✅ `user_emotion` (high emotion detected)
- ✅ `conflict_stage` (in conflict)
- ✅ `personality_synthesis` (complex message)
- ✅ `embodiment_state` (usually included)
- ✅ `creativity_content` (if generated)
- ✅ `self_narrative` (if relationship phase is Deep/Steady)

**Total: ~10-12 features included**

### Step 5: Final Prompt with QMAS Decision

**Example prompt section (from agent.py:307-312):**
```
CURRENT PSYCHOLOGICAL STATE:
- Trust: 0.65
- Hurt: 0.30
- Forgiveness: FORGIVEN (1.00)
- Mood: hurt=0.30, anxiety=0.40, affection=0.60, stress=0.45, guilt=0.25

NEUROCHEMICAL STATE (BIOLOGICAL FOUNDATION):
DA (dopamine)=0.42: LOW - affects motivation, reward, excitement
CORT (cortisol)=0.58: NORMAL - affects stress, anxiety, alertness
OXY (oxytocin)=0.52: LOW - affects bonding, trust, warmth
SER (serotonin)=0.48: LOW - affects mood stability, confidence
NE (norepinephrine)=0.55: NORMAL - affects alertness, focus, energy
These hormones directly influence how you feel right now. Let that show authentically.

- Internal Debate: Growth agent recommends Acknowledge hurt fully, validate feelings, have honest conversation about availability expectations (trust delta: +0.12)
  (After multi-agent debate, this emerged as the best path)

RELEVANT MEMORIES:
- Identity: User values consistent communication (confidence: 0.85)
- Past event: User expressed vulnerability about feeling abandoned...
- Past event: Deep conversation about trust and reliability last week...

CONFLICT STAGE: TRIGGER
Behavior: careful tone, 1 message(s)

RELATIONSHIP PHASE: Building (moderate closeness, growing familiarity)
- Appropriate behaviors: Validate emotions, show care, set boundaries gently
- Avoid: Dismissing feelings, being defensive, over-apologizing
```

**✅ YES, this feature is fully functional and integrated!**

---

## 2. Simple Messages: Do They Still Get Identity Memory and Relationship Phase?

**YES, absolutely!** Simple messages still get:

### Always-Included Core Features (feature_selector.py:218-219):
```python
core_features = {"memories", "temporal_context", "relationship_phase"}
selected_features.update(core_features)  # Always added
```

### Example: Simple Message "hey, how's it going?"

**Feature Selection:**
- ✅ `memories` (ALWAYS) - Includes identity memories like "I'm a student"
- ✅ `temporal_context` (ALWAYS)
- ✅ `relationship_phase` (ALWAYS)
- ✅ `embodiment_state` (usually included)
- Maybe `user_emotion` (if detected)
- ❌ `neurochemicals` (not needed for simple messages)
- ❌ `qmas_decision` (not activated)
- ❌ `conflict_stage` (not in conflict)

**Prompt includes:**
```
RELEVANT MEMORIES:
- Identity: User is a student (confidence: 0.85)
- Identity: User loves talking about their cat (confidence: 0.90)
- Past event: User mentioned their exam last week...

TEMPORAL CONTEXT: Afternoon (2:30 PM). 4 hours since last message.

RELATIONSHIP PHASE: Building (moderate closeness, growing familiarity)
- Appropriate behaviors: Casual warmth, reference shared memories
```

**✅ YES, simple messages get identity memory and relationship phase!**

---

## 3. How Do I Know What's in What Memory? How Is Memory Storage Determined?

### Memory Types and Storage Logic

#### **STM (Short-Term Memory)**
- **What goes here:** Every user message (last 20 entries)
- **Storage:** Automatic, every message
- **Location:** `backend/memory.py:77-94`
- **Decay:** 30-minute half-life, expires after 2 hours

#### **Episodic Memory**
- **What goes here:** Emotionally salient events (conflicts, confessions, apologies, achievements)
- **Storage:** Automatic when events detected
- **Location:** `backend/cognitive_core.py:721-754`
- **Criteria:**
  - Event detected by semantic understanding (conflict, confession, apology, etc.)
  - Emotional salience: `abs(valence) + arousal > 0.5` OR `confidence > 0.6`
  - 80% chance to remember (stochastic)
- **Decay:** Exponential decay based on relational impact

**Example events that become episodic:**
- "I'm really hurt that you didn't respond" → conflict event → episodic memory
- "I have to tell you something... I've been struggling with anxiety" → confession → episodic memory
- "I'm so sorry for yesterday" → apology → episodic memory
- "I got accepted to grad school!" → achievement → episodic memory

#### **Identity Memory**
- **What goes here:** Facts about the user that are consistently true
- **Storage:** Promoted from pattern candidates (NOT direct)
- **Location:** `backend/pattern_detector.py`, `backend/cognitive_core.py:695-719`
- **Promotion Criteria (STRICT):**
  - Pattern Confidence (PC) ≥ 0.75
  - 14+ distinct days (observed over 2 weeks)
  - 8+ occurrences (mentioned 8+ times)
  - < 3 contradictions in 30-day window

**Current Implementation:**
- **Pattern Detection:** Uses keyword matching for routine patterns (gym, class, work, study, etc.)
- **Pattern Text Extraction:** Simplified - uses message content (in production, should use LLM to extract structured facts)
- **Location:** `backend/pattern_detector.py:36-100`

**Example: "I'm a student"**
1. User mentions "class", "study", "exam" multiple times
2. Pattern detector creates pattern candidate: "User mentions classes/studying"
3. After 14+ days and 8+ occurrences with PC ≥ 0.75 → promoted to identity
4. Identity memory: `{"fact": "User is a student", "confidence": 0.82, "evidence_count": 12}`

**⚠️ IMPORTANT: Current limitation**
- Pattern extraction is **simplified** (keyword-based, not LLM-based)
- Identity facts like "I'm a student" would need to be mentioned repeatedly in routine contexts (classes, studying, exams)
- **In production, this should use LLM to extract structured identity facts** from any message

**What CAN be promoted to identity:**
- Routines: "goes to gym Tues/Thurs", "has class at 10am"
- Habits: "usually studies in the evening"
- Facts: "works as a software engineer" (if mentioned consistently)
- Preferences: "loves cats" (if mentioned 8+ times over 14+ days)

**What CANNOT be promoted:**
- One-time statements: "I'm feeling sad today" → episodic (event), not identity
- Inconsistent mentions: Mentioned 3 times → stays as pattern candidate
- Contradicted patterns: "I never go to the gym" after promoting "goes to gym" → contradiction added

---

## 4. Can I Force Memory Storage? Or Is It LLM-Based?

### Current System: **Hybrid (Mostly Automatic, Some LLM-Based)**

#### **Automatic (No LLM, Deterministic):**
1. **STM:** Always stored, no choice
2. **Episodic:** Automatic when events detected (80% stochastic chance)
3. **Pattern Detection:** Keyword-based (NOT LLM-based currently)

#### **LLM-Based:**
1. **Semantic Understanding:** LLM determines intent, events, complexity
2. **Event Detection:** LLM identifies events (conflict, confession, etc.)
3. **Complexity Assessment:** LLM determines complexity (0.0-1.0)

#### **Stochastic (Random):**
1. **Memory Selection:** Stochastic selection of which memories to include (`_select_memories_stochastic`)
2. **Memory Storage:** 80% chance to store episodic memories (humans forget sometimes)

### Can You Force Memory Storage?

**Short Answer: NO, not directly. The system is automatic.**

**However:**
- **Identity Memory:** Mention facts repeatedly (8+ times over 14+ days) → automatic promotion
- **Episodic Memory:** Say things that trigger events (conflict, confession, apology) → automatic storage
- **STM:** Always stored automatically

**To check what's stored:**
```python
# In code, you can access:
core.memory.get_stm()              # Short-term memory
core.memory.get_episodic()         # Episodic memories
core.memory.get_identity()         # Identity memories
core.pattern_detector.get_all_candidates()  # Pattern candidates (not yet promoted)
```

**To see in logs:**
- Look for `[DEBUG] Promoted pattern to identity: ...` messages
- Look for `[DEBUG] Memory state: STM=X, Episodic=Y, Identity=Z` messages

---

## Summary: Verification Checklist

✅ **Complexity > 0.7 + QMAS Activation:** Functional and integrated
- Semantic understanding determines complexity
- Cognitive router activates QMAS (qmas_score >= 0.6 OR complexity >= 0.6)
- QMAS decision included in final prompt

✅ **Simple Messages Get Identity Memory:** Yes
- Core features (memories, temporal_context, relationship_phase) always included
- Identity memories like "I'm a student" are included in selected memories

✅ **Memory Storage:** Automatic, hybrid system
- STM: Always stored
- Episodic: Automatic when events detected
- Identity: Promoted from patterns (14+ days, 8+ occurrences, PC ≥ 0.75)

✅ **Context Considered:**
- **Semantic Understanding:** Gets psyche_state, recent_memories (last 3 STM)
- **Cognitive Router:** Gets full context (relationship_phase, trust, hurt, conflict_stage, etc.)
- **Feature Selection:** Gets full processing_result (all context available)
- **Final Prompt:** Gets selected features only (optimized for response time)

**The system is fully functional and integrated!** 🎉

