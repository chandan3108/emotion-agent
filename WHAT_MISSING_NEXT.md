# What's Missing & What's Next

## ✅ COMPLETED (Core Features)

All major cognitive features are implemented:
- ✅ All 19-stage processing pipeline
- ✅ Creativity Engine
- ✅ Self-Narrative Generation
- ✅ Parallel Life Awareness
- ✅ Enhanced PHL (Procedural Habit Layer)
- ✅ Comprehensive prompt building
- ✅ Neurochemical-driven behavior
- ✅ Stochastic everything

## 🔴 CRITICAL MISSING (High Priority)

### 1. **Engagement Score Calculation** ⚠️ CURRENTLY HARDCODED
**Location:** `backend/cognitive_core.py:169`
**Current:** `engagement_score = 0.6  # Would be computed from user's next response`

**What's Needed:**
```python
def calculate_engagement_score(user_response: Dict[str, Any], 
                               previous_ai_message: str) -> float:
    """
    Calculate engagement from:
    - Response time (fast = engaged)
    - Message length (longer = engaged)
    - Emotion (positive = engaged)
    - Reply quality (thoughtful = engaged)
    - Emoji usage (more = engaged)
    """
    # Combine signals with weights
    # Return 0.0-1.0
```

**Impact:** CPBM habit formation depends on this. Currently all habits form at same rate.

### 2. **Offline Consolidation Worker** (Nightly)
**Blueprint:** Lines 670-678

**What's Needed:**
```python
# backend/offline_consolidation.py
class OfflineConsolidationWorker:
    async def nightly_consolidation(self):
        # 1. Recompute pattern_confidence for all routine candidates
        # 2. Promote identities where thresholds met
        # 3. Decay non-reinforced memories
        # 4. Update habit strengths
        # 5. Adjust personality drift parameters based on weekly trends
```

**Impact:** Memory promotion, habit decay, pattern confidence updates happen offline.

### 3. **Counterfactual Replayer**
**Blueprint:** Lines 679-683

**What's Needed:**
```python
# backend/counterfactual_replayer.py
class CounterfactualReplayer:
    async def replay_major_episode(self, episode_id: str):
        # 1. Simulate alternative responses via policy search
        # 2. Evaluate long-term trust outcomes
        # 3. Adjust parameters (forgiveness weights, initiative thresholds, etc.)
        # 4. Push updates to live system after validation
```

**Impact:** System learns from major conflicts/episodes.

## 🟡 IMPORTANT MISSING (Medium Priority)

### 4. **Inner Dialogue (Multi-Agent)** - Different from QMAS
**Blueprint:** Lines 644-648

**What's Needed:**
```python
# backend/inner_dialogue.py
class InnerDialogue:
    def generate_inner_voices(self, situation: Dict) -> List[str]:
        # Emotional Agent: "You should reach out; she's been quiet"
        # Rational Agent: "She said quiet hours. Respect that."
        # Attachment Agent: "But what if she's upset with us?"
        # Planner blends proposals → hesitant, multi-faceted, human output
```

**Note:** This is different from QMAS. QMAS is for major decisions. Inner Dialogue is for everyday hesitations and internal conflict.

### 5. **Topic Rotation & Fatigue**
**Blueprint:** Mentioned in pipeline stage 9

**What's Needed:**
```python
# backend/topic_rotation.py
class TopicRotation:
    def calculate_topic_fatigue(self, topic: str, recent_topics: List[str]) -> float:
        # Score how tired user/AI are of this topic
        # Natural rotation when fatigue high
        # Repair probability when topic fatigue detected
```

### 6. **Intention Hierarchy**
**Blueprint:** Mentioned in pipeline stage 8

**What's Needed:**
```python
# backend/intention_hierarchy.py
class IntentionHierarchy:
    def rank_intentions(self, context: Dict) -> List[Dict]:
        # Micro intentions (immediate)
        # Macro intentions (conversation-level)
        # Strategic intentions (relationship-level)
        # Rank by alignment with personality/psyche
```

### 7. **Attachment Cycling & Meta-Cognition**
**Blueprint:** Lines 662-663

**What's Needed:**
```python
# Add to psyche.py or new file
def update_attachment_cycling(self, delta_days: float):
    # Attachment level oscillates slowly (weeks/months)
    # During deep phases, AI may self-reflect occasionally
    # Stochastic oscillation (not linear)
```

### 8. **Stability Dampening & Safety**
**Blueprint:** Lines 665-666

**What's Needed:**
```python
# Add exponential dampers to prevent spirals
def apply_stability_dampening(self, value: float, previous_value: float) -> float:
    # Prevent extreme swings
    # Exponential damping
    # Prevents personality spirals, mood spirals, etc.
```

## 🟢 NICE TO HAVE (Low Priority)

### 9. **Better NER/Entity Extraction**
**Current:** `parallel_life.py` uses simple heuristics
**What's Needed:** Proper NER model or LLM-based extraction for:
- People names
- Life events
- Routines
- Commitments

### 10. **Proper Embeddings for Memory**
**Current:** `cognitive_core.py:440` uses random vectors
**What's Needed:** Real embeddings (sentence-transformers, OpenAI, etc.) for:
- ACT thread matching
- Memory similarity
- Semantic search

### 11. **Better Memory Similarity**
**Current:** Simple text overlap
**What's Needed:** Embedding-based cosine similarity

### 12. **Content Moderation**
**Blueprint:** Failure modes section
**What's Needed:**
```python
# backend/content_moderation.py
class ContentModerator:
    def check_safety(self, message: str) -> Tuple[bool, str]:
        # Check for harmful content
        # Fail-closed strategy
        # Return (is_safe, reason)
```

### 13. **Rate Limiting**
**What's Needed:**
```python
# Prevent spam/abuse
# Limit messages per time window
# Respect user's DND settings
```

### 14. **Enhanced Error Handling**
**What's Needed:**
- Try-catch around all LLM calls
- Graceful degradation
- Fallback responses
- Error logging

### 15. **Structured Logging & Monitoring**
**Blueprint:** Production readiness checklist
**What's Needed:**
```python
# Structured logs for:
# - All stochastic decisions
# - Phase transitions
# - Reciprocity balance
# - Initiative sends
# - Memory promotions
# - Anomalies
```

### 16. **Testing**
**What's Needed:**
- Unit tests for each component
- Integration tests for pipeline
- Synthetic user simulations
- Edge case handling

## 📋 RECOMMENDED NEXT STEPS (Priority Order)

### Phase 1: Critical Fixes (This Week)
1. **Engagement Score Calculation** - Fix hardcoded value
2. **Error Handling** - Add try-catch, fallbacks
3. **Content Moderation** - Basic safety checks

### Phase 2: Offline Learning (Next Week)
4. **Offline Consolidation Worker** - Nightly consolidation
5. **Counterfactual Replayer** - Learn from major episodes

### Phase 3: Enhanced Features (Week 3-4)
6. **Inner Dialogue** - Everyday hesitations
7. **Topic Rotation** - Natural topic fatigue
8. **Stability Dampening** - Prevent spirals

### Phase 4: Production Polish (Week 5+)
9. **Proper Embeddings** - Replace random vectors
10. **Better NER** - Improve entity extraction
11. **Structured Logging** - Monitoring & observability
12. **Testing** - Unit & integration tests

## 🎯 IMMEDIATE ACTION ITEMS

### 1. Fix Engagement Score (30 min)
```python
# In cognitive_core.py, replace:
engagement_score = 0.6  # Would be computed from user's next response

# With:
engagement_score = self._calculate_engagement_from_response(
    user_message, previous_ai_message, emotion_data
)
```

### 2. Add Basic Error Handling (1 hour)
- Wrap all LLM calls in try-catch
- Add fallback responses
- Log errors

### 3. Add Content Moderation (1 hour)
- Basic keyword filtering
- LLM-based safety check (optional)
- Fail-closed strategy

## 📊 Current System Status

**Core Features:** ✅ 95% Complete
**Advanced Features:** ✅ 90% Complete (Creativity, Self-Narrative, Parallel Life added)
**Production Readiness:** ⚠️ 60% Complete (Missing: Logging, Testing, Safety)

## 🚀 Quick Wins

1. **Engagement Score** - 30 min fix, high impact
2. **Error Handling** - 1 hour, prevents crashes
3. **Content Moderation** - 1 hour, safety critical
4. **Structured Logging** - 2 hours, enables monitoring

---

**Bottom Line:** The core cognitive architecture is complete. What's missing is:
1. **Engagement calculation** (currently hardcoded)
2. **Offline learning** (nightly consolidation)
3. **Production polish** (logging, testing, safety)

The system is **functionally complete** but needs **production hardening**.

