# COMPREHENSIVE BLUEPRINT REVIEW - TODO LIST

## CRITICAL GAPS FOUND

### 1. TEMPORAL AWARENESS SYSTEM ❌
**Issue:** Uses UTC, not device time
**Blueprint:** Should use user's actual timezone and current time
**Fix:** Get timezone from user or system, use local time

### 2. RELATIONSHIP PHASE EVALUATION ❌
**Issue:** Uses `interaction_count` (STM + episodic + identity), not "shared history"
**Blueprint:** Should evaluate meaningful interactions (episodic events, identity facts, trust-building moments)
**Fix:** Calculate "shared history" as meaningful relationship milestones, not just message count

### 3. PERSONALITY SYSTEM - SHALLOW ❌
**Issues:**
- Drift is applied but not called regularly
- Anti-cloning exists but is simplified (not true orthogonalization)
- No long-term persona development (weeks/months)
- Personality doesn't develop own quirks over time
**Blueprint:** 
- Core: ~0.0005-0.002/day drift
- Relationship: ~0.005-0.02/day drift
- Anti-cloning: True orthogonalization (project user style away from core)
- Own persona: Develops unique quirks, phrases, behaviors over weeks/months
**Fix:** 
- Call `apply_drift()` on every message with time delta
- Implement true orthogonalization
- Add long-term quirk development system

### 4. MISSING PIPELINE STAGES ❌
**Missing:**
- Stage 6: Cognitive Router (12-parameter decision tree) - NOT IMPLEMENTED
- Stage 8: Intention Hierarchy - NOT IMPLEMENTED
- Stage 9: Topic Rotation & Fatigue - NOT IMPLEMENTED
- Stage 16: Offline Consolidation Worker - NOT IMPLEMENTED
- Stage 17: Counterfactual Replayer - NOT IMPLEMENTED

### 5. LLM DECIDES FEATURES IN PROMPT ❌
**Issue:** Prompt builder includes everything, not dynamically selected
**Blueprint:** LLM should evaluate message and decide which cognitive features to include
**Fix:** Add LLM-based feature selection before prompt building

### 6. TWO-STAGE LLM REASONING ❌
**Issue:** Only used when `reasoning_mode` is True (hardcoded triggers)
**Blueprint:** Should be used for complex messages based on LLM complexity assessment
**Fix:** Use complexity score to determine when to use two-stage reasoning

### 7. MESSAGE DELIVERY (Stage 15) ❌
**Issue:** Typing simulation, delays, burst sequencing not implemented in Discord bot
**Blueprint:** Should simulate typing, delays between messages, burst patterns
**Fix:** Implement typing indicators and delays in Discord bot

### 8. VERIFIER (Stage 14) ❌
**Issue:** Verifier exists but not called in pipeline
**Blueprint:** Should verify every response before sending
**Fix:** Add verifier call before message delivery

### 9. PROMPT BUILDER (Stage 12) ❌
**Issue:** Includes everything, not contextually selected
**Blueprint:** Should assemble based on what's relevant for this message
**Fix:** Make prompt builder dynamic based on LLM evaluation

### 10. PERSONALITY QUIRKS DEVELOPMENT ❌
**Issue:** No long-term quirk development (signature phrases, unique behaviors)
**Blueprint:** Should develop own quirks over weeks/months, not mimic user
**Fix:** Add quirk development system that evolves independently

## TODO LIST

### HIGH PRIORITY (Core Functionality)
1. ✅ Fix temporal awareness - use device/system timezone
2. ✅ Fix relationship phase evaluation - use meaningful shared history
3. ✅ Deepen personality system - long-term drift, true anti-cloning, own quirk development
4. ✅ Make LLM decide which features to include in prompt (dynamic feature selection)
5. ✅ Ensure two-stage LLM reasoning works for complex messages
6. ✅ Implement message delivery (typing simulation, delays, bursts) in Discord bot
7. ✅ Add verifier to pipeline (verify responses before sending)
8. ✅ Make prompt builder contextually selective (not include everything)

### MEDIUM PRIORITY (Missing Pipeline Stages)
9. ⏳ Implement Cognitive Router (Stage 6) - 12-parameter decision tree
10. ⏳ Implement Intention Hierarchy (Stage 8) - Micro/macro/strategic intentions
11. ⏳ Implement Topic Rotation & Fatigue (Stage 9) - Topic fatigue scoring
12. ⏳ Implement Offline Consolidation Worker (Stage 16) - Nightly tasks
13. ⏳ Implement Counterfactual Replayer (Stage 17) - Alternative simulations

### LOW PRIORITY (Enhancements)
14. ⏳ Add personality quirk development system (weeks/months timescale)
15. ⏳ Enhance anti-cloning with true orthogonalization
16. ⏳ Add constitutional reasoning conflicts (6 principles in tension)

