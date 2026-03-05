# Implementation Plan: AI Companion System Revamp

## Current State Analysis

**What we have:**
- ✅ FastAPI backend infrastructure
- ✅ PostgreSQL database
- ✅ Emotion detection (face/voice features → ML model)
- ✅ Basic LLM integration (Llama-3.2-3B via HuggingFace)
- ✅ Simple chat history
- ✅ Frontend with real-time emotion tracking

**What we need:**
- ❌ Persistent state machine (28K JSON/user)
- ❌ Memory hierarchy (STM, ACT, Episodic, Identity)
- ❌ Psyche engine (mood, trust, hurt, neurochemicals)
- ❌ Temporal awareness system
- ❌ Personality layers
- ❌ Initiative engine
- ❌ Two-stage LLM prompting
- ❌ QMAS (7-agent debate)
- ❌ Conflict lifecycle
- ❌ All other blueprint features

---

## Phase 1: Foundation (Week 1-2)
**Goal:** Build the core infrastructure that everything else depends on.

### 1.1 Persistent State Machine
- [ ] Design SQLite/Redis schema for 28K JSON/user state
- [ ] Implement state orchestrator with atomic updates
- [ ] State structure: core_personality, current_psyche, habits_cpbm, memory_hierarchy, neurochem_vector, relationship_ledger
- [ ] Fast read/write operations (0.5ms P99 read, 2.5ms P99 write)

### 1.2 Memory System (Core)
- [ ] Short-Term Memory (STM): Circular buffer, 30-min half-life
- [ ] Active Conversational Threads (ACT): Topic embeddings, salience decay (τ=3h)
- [ ] Episodic Memory: Emotionally salient events with forgetting curves
- [ ] Identity Memory: Promoted facts about user (confidence ≥0.75)
- [ ] Memory matching logic (similarity thresholds, NER overlap)

### 1.3 Basic Psyche Engine
- [ ] Mood system (14-dimensional vector) with decay (τ=6h)
- [ ] Trust & Hurt ledgers (basic accumulation/decay)
- [ ] Simple forgiveness FSM (4 states)
- [ ] Emotion contagion (basic implementation)

### 1.4 Perception Layer (Enhanced)
- [ ] Upgrade existing emotion detection to Perception Layer
- [ ] Intent detection
- [ ] Sincerity scoring
- [ ] Temporal tagging

**Deliverable:** System can store/retrieve state, maintain basic memory, track mood/trust/hurt.

---

## Phase 2: Temporal Awareness & Personality (Week 3-4)
**Goal:** Add time-awareness and personality layers.

### 2.1 Temporal Awareness System (TAS)
- [ ] Absolute time tracking (timestamp, timezone, circadian phases)
- [ ] Relative time deltas (hours/days since events)
- [ ] Circadian modulation (morning/evening/late-night behaviors)
- [ ] Integration with memory decay, mood dynamics, forgiveness

### 2.2 Five-Layer Personality Model
- [ ] Core layer (Big Five, slow drift ~0.002/day)
- [ ] Relationship layer (per-user, ~0.005-0.02/day)
- [ ] Situational layer (context-dependent, decay ≈0.3h)
- [ ] Mood layer (14 dimensions, τ=3-12h)
- [ ] Micro layer (per-message quirks)
- [ ] Personality synthesis formula with task-specific weights
- [ ] Anti-cloning orthogonalization

### 2.3 Conversational Pattern & Behavior Model (CPBM)
- [ ] Stable style traits tracking
- [ ] Style modes (mood-driven)
- [ ] Micro-habits (signature words, emoji patterns)
- [ ] CPBM learning (engagement-based, not cloning)

**Deliverable:** AI has personality that varies by time, relationship, and context.

---

## Phase 3: Reasoning & Response Generation (Week 5-7)
**Goal:** Implement the decision-making and response generation pipeline.

### 3.1 Two-Stage LLM Prompt Architecture
- [ ] Stage 1: Inner Reasoning Prompt (private, never shown)
- [ ] Stage 2: Response Synthesis Prompt (brief, natural output)
- [ ] Decision tree: when to enter full reasoning mode vs casual mode
- [ ] Upgrade existing LLM integration to two-stage

### 3.2 Quantum Multi-Agent System (QMAS)
- [ ] 7 internal agents (Emotional, Rational, Protective, Authentic, Growth, Creative, Memory)
- [ ] Multi-agent debate (100 Monte Carlo paths)
- [ ] Meta-synthesis (LLM ranks paths)
- [ ] Path selection with trust delta prediction

### 3.3 Cognitive Router
- [ ] 12-parameter decision tree
- [ ] Route to QMAS when needed
- [ ] Route to simple modes for casual interactions

### 3.4 Message Sequence Planner
- [ ] Burst patterns (mood-driven)
- [ ] Typing simulation (WPM calculation)
- [ ] Inter-message delays
- [ ] Micro-behaviors (typos, signature phrases)

### 3.5 Verifier & Authenticity Control
- [ ] JSON validation
- [ ] Memory ID matching (≥0.80 similarity)
- [ ] Temporal sanity checks
- [ ] Clone risk detection
- [ ] Content safety
- [ ] Fail-closed strategy

### 3.6 Conflict Lifecycle Model
- [ ] 7-stage conflict FSM (TRIGGER → ESCALATION → IMPASSE → COOLING → REPAIR → RESOLUTION → INTEGRATION)
- [ ] Stage-specific behaviors
- [ ] Apology generation with sincerity scoring

**Deliverable:** AI can reason through complex situations and generate authentic responses.

---

## Phase 4: Advanced Features (Week 8-10)
**Goal:** Add sophisticated features for human-like behavior.

### 4.1 Neurochemical Cascade Modeling
- [ ] Neurotransmitter vector (DA, CORT, OXY, SER, NE)
- [ ] Circadian & ultradian cycles
- [ ] Event-driven cascades (conflict, reconciliation, novelty)

### 4.2 Embodiment State & Energy Budgeting
- [ ] Energy budget E_daily (circadian × sleep debt × mood)
- [ ] Body state mapping (energized/normal/fatigued/exhausted)
- [ ] Fatigue typo injection
- [ ] Capacity accumulation (interaction fatigue)

### 4.3 Theory of Mind & Empathy Engine
- [ ] ToM state (user emotional state, receptivity, availability)
- [ ] Empathy utility scoring
- [ ] Candidate action generation
- [ ] Circadian-adjusted receptivity

### 4.4 Initiative Engine
- [ ] Initiative scoring (I_base + routine + unresolved + attachment)
- [ ] Routine resurfacing
- [ ] DND handling (hard/soft, ACS, override logic)
- [ ] Scheduling with delays

### 4.5 Reciprocity Ledger
- [ ] Entry types (vulnerability, support, effort, repair, forgiveness, celebration, initiation)
- [ ] Balance computation (30-day lookback)
- [ ] Imbalance response (AI overextended → distance increase)

### 4.6 Offline Learning
- [ ] Nightly consolidation worker
- [ ] Pattern confidence recomputation
- [ ] Identity promotion/demotion
- [ ] Memory decay
- [ ] Counterfactual replayer (for major episodes)

**Deliverable:** Complete system with all advanced features.

---

## Phase 5: Integration & Testing (Week 11-12)
**Goal:** Integrate everything, test, and optimize.

### 5.1 API Integration
- [ ] Update FastAPI endpoints to use new architecture
- [ ] Maintain backward compatibility where possible
- [ ] Add new endpoints for state inspection/debugging

### 5.2 Frontend Updates
- [ ] Integrate with new agent response format
- [ ] Add typing indicators (from Message Sequence Planner)
- [ ] Show initiative messages (autonomous messaging)
- [ ] Memory review UI (optional)

### 5.3 Testing & Validation
- [ ] Unit tests for state machine, memory, psyche
- [ ] Integration tests for full pipeline
- [ ] Synthetic user simulations
- [ ] Performance benchmarks

### 5.4 Observability
- [ ] Structured logging
- [ ] Audit trails
- [ ] Dashboards (KPIs: initiative ratio, complaint rate, etc.)

### 5.5 Safety & Ethics
- [ ] Age verification
- [ ] Anti-manipulation safeguards
- [ ] Exit strategy
- [ ] Refusal rules
- [ ] Privacy compliance (GDPR/CCPA)

**Deliverable:** Production-ready system.

---

## Implementation Strategy

### Efficiency Principles:
1. **Build incrementally** - Each phase delivers working functionality
2. **Test as you go** - Don't wait until the end
3. **Reuse existing code** - Emotion detection, LLM integration, DB setup
4. **Start simple, add complexity** - Basic versions first, enhance later
5. **Focus on core first** - State + Memory + Psyche before advanced features

### Risk Mitigation:
- **Complexity risk:** Start with MVP of each component, iterate
- **Latency risk:** Optimize QMAS (maybe reduce paths initially), cache state reads
- **Cost risk:** Use smaller models for QMAS initially, optimize prompt sizes
- **Testing risk:** Build synthetic test users, create simulation framework

### Success Metrics:
- State read: <1ms P99
- State write: <5ms P99
- Full pipeline latency: <10s (acceptable for complex reasoning)
- Memory accuracy: >90% identity promotion accuracy
- User satisfaction: Track via feedback

---

## Next Steps

**Immediate (Today):**
1. Create state machine schema and orchestrator
2. Implement basic memory system (STM + ACT)
3. Build basic psyche engine (mood + trust/hurt)

**This Week:**
- Complete Phase 1 foundation
- Test with simple conversations
- Integrate with existing emotion detection

**Next Week:**
- Start Phase 2 (Temporal + Personality)
- Begin two-stage LLM integration










