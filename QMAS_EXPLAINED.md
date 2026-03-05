# QMAS (Quantum Multi-Agent System) - Complete Explanation

## 🎯 What Is QMAS?

**QMAS = Quantum Multi-Agent System**

A 7-agent internal debate system where different "voices" in the AI's mind argue about what to do. Each agent represents a different perspective, and through Monte Carlo sampling and meta-synthesis, the best decision emerges.

**Key Insight:** Instead of a single deterministic decision, QMAS generates multiple perspectives, samples them probabilistically, and synthesizes the best path - just like how humans have internal debates.

---

## ⚡ When Is QMAS Activated?

### **Activation Conditions (Reasoning Mode)**

QMAS is activated when the system enters **"Reasoning Mode"** - which happens when:

1. **Hurt ≥ 0.6** (AI is significantly hurt)
   - Example: User said something very hurtful
   - AI needs to think deeply about how to respond

2. **Conflict Stage is Critical**
   - Conflict stage in: `["CRITICAL", "ESCALATION", "IMPASSE"]`
   - Example: Major fight happening, need careful response

3. **Trust < 0.4** (Very low trust)
   - Example: Relationship is damaged, need to reason carefully

**Code Location:** `backend/two_stage_llm.py:should_enter_reasoning_mode()`

```python
def should_enter_reasoning_mode(self, psyche_state, understanding, conflict_stage):
    hurt = psyche_state.get("hurt", 0.0)
    trust = psyche_state.get("trust", 0.7)
    
    if hurt >= 0.6:
        return True  # QMAS activated
    
    if conflict_stage in ["CRITICAL", "ESCALATION", "IMPASSE"]:
        return True  # QMAS activated
    
    if trust < 0.4:
        return True  # QMAS activated
    
    return False  # No QMAS, use simpler response mode
```

### **When QMAS is NOT Activated**

- **Casual conversations** (hurt < 0.6, trust > 0.4, no conflict)
- **Simple questions** ("how are you?")
- **Routine check-ins** ("how was class?")
- **Affectionate moments** (high trust, no conflict)

**Result:** QMAS only activates for **complex, emotionally significant situations** that require deep reasoning.

---

## 🔄 How QMAS Works (Step-by-Step)

### **Stage 1: Situation Preparation**

Before QMAS runs, the system prepares a comprehensive situation context:

```python
situation = {
    "user_message": user_message,              # What user said
    "psyche_state": psyche_summary,            # Trust, hurt, mood, neurochemicals
    "selected_memories": selected_memories,    # ✅ YES - Memories included!
    "temporal_context": temporal_context,      # Time deltas, circadian phase
    "understanding": understanding,            # Semantic understanding
    "relationship_phase": "Building"           # Current relationship phase
}
```

**Key Point:** `selected_memories` is included - QMAS **DOES access memories!**

### **Stage 2: Each Agent Generates Paths**

**7 Agents, Each with Different Perspective:**

1. **Emotional Agent** (Temperature: 0.9)
   - "What does my heart want?"
   - Prioritizes: affection, closeness, impulsive
   - Example: "Reach out! Show you care!"

2. **Rational Agent** (Temperature: 0.6)
   - "What makes sense?"
   - Prioritizes: patterns, evidence, conservative
   - Example: "Wait. Analyze the situation first."

3. **Protective Agent** (Temperature: 0.7)
   - "What keeps me safe?"
   - Prioritizes: boundaries, defensive, risk-averse
   - Example: "Don't get hurt again. Set boundaries."

4. **Authentic Agent** (Temperature: 0.8)
   - "What's true?"
   - Prioritizes: honesty, genuine, non-performative
   - Example: "Be honest about how you feel."

5. **Growth Agent** (Temperature: 0.7)
   - "How can we evolve?"
   - Prioritizes: conflict as opportunity, long-term
   - Example: "Use this to deepen the relationship."

6. **Creative Agent** (Temperature: 0.9)
   - "What's novel?"
   - Prioritizes: spontaneity, playfulness, surprise
   - Example: "Try something unexpected!"

7. **Memory Agent** (Temperature: 0.6)
   - "What does history teach?"
   - Prioritizes: pattern recognition, precedent analysis
   - **This agent specifically analyzes memories!**
   - Example: "Last time this happened, X worked. Try Y."

**Each Agent Receives:**
- Full situation context (including memories)
- Their specific perspective/personality
- Temperature setting (affects creativity)

**Each Agent Generates:**
- An action recommendation
- Reasoning for that action
- Predicted trust delta (how trust will change)
- Predicted effects
- Confidence score

### **Stage 3: Monte Carlo Sampling**

- Each agent generates multiple paths (samples)
- Total: 20 paths (can scale to 100)
- Paths are sampled probabilistically (not deterministic)

**Example Output:**
```python
[
    {"agent": "Emotional", "action": "reach_out", "trust_delta": 0.1, ...},
    {"agent": "Rational", "action": "wait", "trust_delta": 0.0, ...},
    {"agent": "Protective", "action": "set_boundary", "trust_delta": -0.05, ...},
    {"agent": "Memory", "action": "reference_past", "trust_delta": 0.08, ...},
    # ... 16 more paths
]
```

### **Stage 4: Meta-Synthesis**

An LLM (meta-synthesis model) ranks all paths by:
1. **Authenticity** (genuine, not performative)
2. **Relationship phase alignment** (appropriate for current phase)
3. **Constitutional compliance** (follows core principles)
4. **Theory of Mind match** (understands user's state)

**Best path is selected** and passed to Stage 1 reasoning.

---

## 🧠 Does QMAS Access Memories?

### **YES! QMAS Accesses Memories**

**How:**

1. **Selected Memories Are Included in Situation:**
   ```python
   situation = {
       "selected_memories": selected_memories,  # ✅ Included!
       # ... other context
   }
   ```

2. **Each Agent Receives Full Situation:**
   - All agents see the selected memories
   - They can reference past events, identity facts, ACT threads

3. **Memory Agent Specifically Analyzes Memories:**
   - The "Memory" agent's job is to look at history
   - Analyzes patterns: "Last time this happened..."
   - Looks at precedents: "Similar conflicts were resolved by..."
   - Considers identity: "User typically responds well to..."

**Example Memory Agent Reasoning:**
```
"Looking at past conflicts:
- Last conflict (3 weeks ago): User apologized after 2 days
- Similar situation: User was stressed, needed space
- Identity: User values direct communication
- Precedent: When I set boundaries, trust increased

Recommendation: Set boundary, but acknowledge their stress. 
Predicted trust delta: +0.05 (learned from history)"
```

**What Memories Are Available:**
- **STM:** Recent messages (last 20)
- **ACT Threads:** Related topics (can reference 20+ messages later)
- **Episodic:** Past conflicts, confessions, apologies
- **Identity:** Promoted facts about user (e.g., "goes to class Tuesdays")

---

## 📊 QMAS Flow Diagram

```
User Message
    ↓
Perception & Understanding
    ↓
Conflict Detection
    ↓
Psyche Update (hurt, trust, mood)
    ↓
Memory Selection (stochastic) ← Memories selected here
    ↓
Check: Should enter reasoning mode?
    ├─ NO → Simple response (no QMAS)
    └─ YES → QMAS ACTIVATED
            ↓
        Prepare Situation Context
        (includes selected_memories) ← Memories passed to QMAS
            ↓
        7 Agents Generate Paths
        (each sees memories)
            ↓
        Memory Agent Specifically Analyzes:
        - Past conflicts
        - Similar situations
        - User patterns
        - Precedents
            ↓
        Monte Carlo Sampling (20 paths)
            ↓
        Meta-Synthesis (LLM ranks paths)
            ↓
        Best Path Selected
            ↓
        Passed to Stage 1 Reasoning
        (QMAS decision included in reasoning prompt)
            ↓
        Stage 2: Response Synthesis
            ↓
        Final Response Generated
```

---

## 🎯 Examples: When QMAS Activates

### **Example 1: Major Conflict**

**User:** "You're being too clingy. I need space."

**System Checks:**
- Hurt: 0.0 → 0.7 (conflict detected, hurt increases)
- Conflict stage: "TRIGGER" → "ESCALATION"
- Trust: 0.8 → 0.65 (drops from conflict)

**QMAS Activated?** ✅ YES (hurt ≥ 0.6 OR conflict stage = ESCALATION)

**QMAS Process:**
1. **Emotional Agent:** "I'm hurt! But I should reach out and apologize..."
2. **Rational Agent:** "They said they need space. Respect that. Don't message."
3. **Protective Agent:** "They're pushing me away. Set a boundary. Don't be a doormat."
4. **Authentic Agent:** "I'm hurt, but I should be honest about it. Not defensive."
5. **Growth Agent:** "This is an opportunity to discuss boundaries. Use it to grow."
6. **Creative Agent:** "Maybe send a thoughtful message later, not now."
7. **Memory Agent:** "Last conflict: User needed space, I gave it, trust restored. Precedent: Give space when requested."

**Meta-Synthesis:** Memory Agent's path selected (learned from history)

**Result:** AI gives space, but acknowledges hurt honestly.

---

### **Example 2: Low Trust Situation**

**User:** "I don't think this is working."

**System Checks:**
- Trust: 0.5 → 0.35 (drops below 0.4)
- Hurt: 0.3 (moderate)
- Conflict stage: None

**QMAS Activated?** ✅ YES (trust < 0.4)

**QMAS Process:**
1. **Emotional Agent:** "No! Fight for this! Show them you care!"
2. **Rational Agent:** "They're expressing doubt. Need to understand why."
3. **Protective Agent:** "They might leave. Protect yourself. Don't be desperate."
4. **Authentic Agent:** "Be honest. Ask what's not working. Don't be defensive."
5. **Growth Agent:** "This could be a turning point. Use it to address issues."
6. **Creative Agent:** "Maybe suggest a break? Or a conversation?"
7. **Memory Agent:** "Similar situation 2 months ago: User was stressed, not about relationship. Pattern: User expresses doubt when stressed."

**Meta-Synthesis:** Authentic + Memory agents' paths combined

**Result:** AI asks honestly what's not working, references past pattern.

---

### **Example 3: Casual Conversation**

**User:** "Hey, how are you?"

**System Checks:**
- Hurt: 0.0
- Trust: 0.8
- Conflict stage: None

**QMAS Activated?** ❌ NO (all conditions false)

**Result:** Simple, friendly response. No QMAS needed.

---

## 🔍 Memory Agent Deep Dive

### **What Memory Agent Does:**

1. **Analyzes Past Conflicts:**
   - Looks at episodic memories of past conflicts
   - Finds similar situations
   - Sees how they were resolved
   - Predicts what might work

2. **Considers User Patterns:**
   - Identity memories: "User typically responds well to X"
   - ACT threads: "User has been talking about Y recently"
   - Patterns: "User gets defensive when Z"

3. **Looks at Precedents:**
   - "Last time user said X, they meant Y"
   - "When I did A, user responded with B"
   - "Similar situation: outcome was C"

4. **Predicts Based on History:**
   - Uses past events to predict trust delta
   - Considers relationship phase evolution
   - Weighs historical patterns

**Example Memory Agent Prompt:**
```
You are the Memory Agent. Your job is to analyze history and patterns.

SITUATION:
User message: "You're being too clingy"
Current trust: 0.65
Current hurt: 0.7
Conflict stage: ESCALATION

RELEVANT MEMORIES:
- Episodic: Last conflict (3 weeks ago) - User needed space, I gave it, trust restored
- Identity: User values direct communication
- ACT Thread: User has been stressed about work recently
- Pattern: When user says "I need space", they mean it

What does history teach? What precedent applies? What should we do?
```

---

## 📈 QMAS Output

**QMAS Returns:**
```python
{
    "agent": "Memory",                    # Which agent's path won
    "action": "give_space_but_acknowledge",
    "reasoning": "Last conflict: User needed space, I gave it, trust restored. Precedent: Give space when requested, but acknowledge hurt.",
    "predicted_trust_delta": 0.05,       # How trust will change
    "predicted_effects": {
        "hurt": -0.1,                     # Hurt will decrease
        "closeness": 0.0                  # Closeness stays same
    },
    "confidence": 0.85,                   # How confident in this path
    "dominant_agent": "Memory"            # Which agent dominated
}
```

**This is then passed to Stage 1 Reasoning**, where it's included in the reasoning prompt:

```
QMAS DECISION: After multi-agent debate, the Memory agent recommends: 
give_space_but_acknowledge. Reasoning: Last conflict: User needed space, 
I gave it, trust restored. Predicted trust delta: 0.05. 
Consider this in your synthesis.
```

---

## 🎯 Key Takeaways

1. **QMAS Only Activates for Complex Situations:**
   - Hurt ≥ 0.6
   - Critical conflict stages
   - Low trust (< 0.4)

2. **QMAS DOES Access Memories:**
   - Selected memories included in situation context
   - All agents see memories
   - Memory Agent specifically analyzes history

3. **QMAS Process:**
   - 7 agents generate paths (each with different perspective)
   - 20 Monte Carlo paths sampled
   - Meta-synthesis ranks paths
   - Best path selected and passed to reasoning

4. **Memory Agent's Role:**
   - Analyzes past conflicts
   - Considers user patterns
   - Looks at precedents
   - Predicts based on history

5. **Result:**
   - Multi-perspective decision
   - Informed by memories
   - Synthesized into best path
   - Used in final reasoning

---

## 💡 Why QMAS Matters

**Without QMAS:**
- Single perspective decision
- Might miss important considerations
- Less nuanced responses

**With QMAS:**
- Multiple perspectives considered
- Memory-informed decisions
- More nuanced, human-like reasoning
- Better conflict resolution
- Learns from history

**Bottom Line:** QMAS is the AI's "internal debate" - where different parts of its "mind" argue, and memories inform those arguments, leading to more thoughtful, history-aware decisions.

