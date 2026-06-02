"""
Cognitive Core - Orchestrates the 17-stage processing pipeline
This is the main entry point for processing user messages.
"""

import os
import json
import random
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from .state import get_state_orchestrator
from .memory import MemorySystem
from .psyche import PsycheEngine
from .semantic_reasoner import SemanticReasoner, StochasticBehavior
from .human_quirks import HumanQuirks
from .temporal import TemporalAwarenessSystem
from .two_stage_llm import TwoStageLLM
from .qmas import QuantumMultiAgentSystem
from .personality_layers import PersonalityLayers
from .cpbm import CPBM
from .conflict_lifecycle import ConflictLifecycle
from .initiative_engine import InitiativeEngine
from .message_planner import MessageSequencePlanner
from .theory_of_mind import TheoryOfMind
from .reciprocity_ledger import ReciprocityLedger
from .embodiment_state import EmbodimentState
from .verifier import Verifier
from .enhanced_semantic import EnhancedSemanticExtractor
from .relationship_phases import RelationshipPhases
from .creativity_engine import CreativityEngine
from .self_narrative import SelfNarrativeGenerator
from .parallel_life import ParallelLifeAwareness
from .pattern_detector import PatternDetector
from .counterfactual_replayer import CounterfactualReplayer
from .personality_evolution import PersonalityEvolution
from .rate_limiter import global_rate_limiter
from .xp_system import RelationshipXP
from .diary import DiarySystem
# from .identity_extractor import IdentityExtractor  # Temporarily disabled


class CognitiveCore:
    """
    Main cognitive processing engine.
    Orchestrates state, memory, and psyche systems.
    """
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.state_orchestrator = get_state_orchestrator()
        self.state = self.state_orchestrator.get_state(user_id)
        self._init_systems()
        
    def _init_systems(self):
        # Core systems
        self.memory = MemorySystem(self.state, user_id=self.user_id)
        self.psyche = PsycheEngine(self.state)
        self.temporal = TemporalAwarenessSystem()
        
        # Startup: reindex existing memories for semantic search (non-blocking)
        try:
            from .semantic_search import get_semantic_search
            sem = get_semantic_search()
            existing_memories = {
                "episodic": self.memory.get_episodic(min_salience=0.0),
                "identity": self.memory.get_identity(min_confidence=0.0),
                "stm_summaries": self.memory.get_stm(decay=False),
                "learned_facts": self.memory.memory.get("learned_facts", [])
            }
            stats = sem.get_stats(self.user_id)
            total_existing = sum(stats.values())
            total_memories = sum(len(v) for v in existing_memories.values())
            if total_memories > 0 and total_existing < total_memories:
                sem.reindex_user(self.user_id, existing_memories)
        except Exception as e:
            print(f"[SEMANTIC] Startup reindex skipped: {e}")
        
        # Reasoning systems
        self.semantic_reasoner = SemanticReasoner()
        self.enhanced_semantic = EnhancedSemanticExtractor()
        self.two_stage_llm = TwoStageLLM()
        self.qmas = QuantumMultiAgentSystem()
        
        # Stage 6: Cognitive Router
        from .cognitive_router import CognitiveRouter
        self.cognitive_router = CognitiveRouter()
        
        # Stage 8: Intention Hierarchy
        from .intention_hierarchy import IntentionHierarchy
        self.intention_hierarchy = IntentionHierarchy()
        
        # Stage 9: Topic Rotation & Fatigue
        from .topic_rotation import TopicRotation
        self.topic_rotation = TopicRotation(self.state)
        
        # Personality & behavior
        self.personality = PersonalityLayers(self.state)
        self.cpbm = CPBM(self.state)
        self.personality_evolution = PersonalityEvolution(self.state)
        
        # Relationship systems
        self.conflict_lifecycle = ConflictLifecycle(self.state)
        self.reciprocity_ledger = ReciprocityLedger(self.state)
        self.relationship_phases = RelationshipPhases(self.state)
        
        # Initiative & planning
        self.initiative_engine = InitiativeEngine(self.state)
        self.message_planner = MessageSequencePlanner(self.state)
        
        # Prediction & empathy
        self.theory_of_mind = TheoryOfMind(self.state)
        
        # Embodiment
        self.embodiment = EmbodimentState(self.state)
        
        # Advanced features
        self.creativity_engine = CreativityEngine()
        self.self_narrative = SelfNarrativeGenerator(self.state)
        self.parallel_life = ParallelLifeAwareness(self.state)
        self.pattern_detector = PatternDetector(self.state)
        # self.identity_extractor = IdentityExtractor()  # Temporarily disabled
        
        # Verification
        self.verifier = Verifier()
        
        # Counterfactual replay (for major episodes)
        self.counterfactual_replayer = CounterfactualReplayer(self.state)
        
        # === Game Progression Systems ===
        self.xp_system = RelationshipXP(self.state)
        self.diary = DiarySystem(self.state)
        
        # FTS5 memory search index
        from .memory_search import get_memory_search
        self.memory_search = get_memory_search()
        # Reindex user's memories for full-text search
        self.memory_search.reindex_user(self.user_id, self.state.get("memory_hierarchy", {}))

    def reload_state(self):
        """
        Reloads the state dictionary from the persistent SQLite database in-place,
        and re-binds all dependent systems to the fresh state object.
        """
        new_state = self.state_orchestrator.get_state(self.user_id)
        self.state.clear()
        self.state.update(new_state)
        self._init_systems()
        print(f"[COGNITIVE CORE] State reloaded and systems re-bound for user {self.user_id}")
    
    def _determine_processing_depth(self, user_message: str, perception: Dict[str, Any], 
                                   fast_mode: bool = False, understanding: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Determine what level of processing is needed based on LLM-assessed complexity.
        NO HARDCODED PATTERNS - complexity is determined by the semantic reasoner (LLM).
        
        Returns dict with flags for which engines to activate:
        - Lightweight (complexity < 0.3): Minimal processing, fast response
        - Standard (0.3 <= complexity < 0.6): Enhanced semantic, standard processing
        - Complex (0.6 <= complexity < 0.8): Enhanced semantic + QMAS
        - Critical (complexity >= 0.8): Full QMAS + two-stage deep reasoning
        """
        # Get current psyche state
        psyche_summary = self.psyche.get_psyche_summary()
        trust = psyche_summary.get("trust", 0.3)
        hurt = psyche_summary.get("hurt", 0.0)
        conflict_stage = self.conflict_lifecycle.current_stage
        relationship_phase = self.relationship_phases.current_phase
        
        # Get complexity from semantic understanding (LLM-determined, not hardcoded)
        complexity = 0.5  # Default to standard
        if understanding:
            complexity = understanding.get("complexity", 0.5)
            # Clamp to valid range
            complexity = max(0.0, min(1.0, complexity))
            
            # Override with psyche state if critical (hurt, conflict)
            if hurt >= 0.6 or conflict_stage:
                complexity = max(complexity, 0.8)  # Force critical if hurt/conflict
            
            print(f"[DEBUG] LLM-determined complexity: {complexity:.2f} (intent={understanding.get('intent', 'unknown')}, events={len(understanding.get('events', []))})")
        else:
            # Fallback only if understanding completely fails
            print(f"[WARNING] No understanding available, using default complexity")
        
        # TOKEN SAVER MODE: Skip LLM-heavy features to save API calls
        # Set this to False when you have more tokens to enable full processing
        TOKEN_SAVER_MODE = True
        
        if TOKEN_SAVER_MODE:
            # Use stochastic/heuristic approaches only - single LLM call for response
            # All cognitive state (psyche, memory, personality) still updates normally
            return {
                "lightweight": True,
                "enhanced_semantic": False,
                "qmas": False,
                "deep_reasoning": False,
                "creativity": False,
                "self_narrative": False,
                "complexity": complexity  # Still track complexity for future use
            }
        
        # FULL MODE: Use LLM for complex processing (enable when you have more tokens)
        use_lightweight = complexity < 0.3 and not conflict_stage and hurt < 0.3
        use_enhanced_semantic = complexity >= 0.3
        use_qmas = complexity >= 0.6
        use_deep_reasoning = complexity >= 0.8
        use_creativity = complexity >= 0.4 and relationship_phase not in ["Discovery"]
        use_self_narrative = complexity >= 0.5 and relationship_phase not in ["Discovery"]
        
        return {
            "lightweight": use_lightweight,
            "enhanced_semantic": use_enhanced_semantic,
            "qmas": use_qmas,
            "deep_reasoning": use_deep_reasoning,
            "creativity": use_creativity,
            "self_narrative": use_self_narrative,
            "complexity": complexity
        }
    
    async def process_message(self, user_message: str, emotion_data: Optional[Dict[str, Any]] = None, fast_mode: bool = False) -> Dict[str, Any]:
        """
        Process a user message through the cognitive pipeline.
        
        Uses LLM-native semantic understanding instead of keyword matching.
        Includes stochastic behavior for human-like unpredictability.
        
        Args:
            user_message: User's message text
            emotion_data: Optional emotion detection data from perception layer
            fast_mode: Force lightweight processing (deprecated, use _determine_processing_depth instead)
        
        Returns:
            Processing result with selected memories, psyche state, etc.
        """
        # Stage 1: Perception Layer (enhanced with emotion data)
        perception = self._perception_layer(user_message, emotion_data)
        
        # Initialize conflict_stage early to avoid UnboundLocalError
        conflict_stage = self.conflict_lifecycle.current_stage
        
        # Stage 2: Basic Semantic Understanding (always do this first to determine complexity)
        context = {
            "psyche_state": self.psyche.get_psyche_summary(),
            "recent_memories": self.memory.get_stm(decay=False)[-3:],
            "emotion": perception.get("emotion", "neutral"),
            "emotion_vector": {"valence": perception.get("valence", 0.0), "arousal": perception.get("arousal", 0.0)}
        }
        
        # TOKEN SAVER MODE - Always use heuristics for understanding
        # This saves 1 LLM call per message while still getting basic understanding
        TOKEN_SAVER_MODE = True  # Set to False when you have more API tokens
        
        heuristic_understanding = self.semantic_reasoner._heuristic_understanding(user_message)
        heuristic_complexity = heuristic_understanding.get("complexity", 0.5)
        
        # In token saver mode, always use heuristics
        # In full mode, use LLM for complex messages
        if not TOKEN_SAVER_MODE and heuristic_complexity >= 0.4:
            try:
                understanding = await asyncio.wait_for(
                    self.semantic_reasoner.understand_message(user_message, context),
                    timeout=15.0
                )
                print(f"[DEBUG] LLM understanding (complex msg): complexity={understanding.get('complexity', 0.5):.2f}, intent={understanding.get('intent', 'unknown')}")
            except asyncio.TimeoutError:
                print(f"[WARNING] Semantic understanding timed out, using heuristic fallback")
                understanding = heuristic_understanding
            except Exception as e:
                print(f"[WARNING] Semantic understanding error: {e}, using heuristic fallback")
                understanding = heuristic_understanding
        else:
            # Simple message - use heuristic (saves 1 LLM call)
            understanding = heuristic_understanding
            print(f"[DEBUG] Heuristic understanding (simple msg): complexity={heuristic_complexity:.2f}, intent={understanding.get('intent', 'unknown')}")
        
        # Stage 6: Cognitive Router - 12-parameter decision tree routing
        # (Note: temporal_context will be computed later, so use placeholder for now)
        router_context = {
            "complexity": understanding.get("complexity", 0.5),
            "emotional_depth": perception.get("arousal", 0.5),
            "relationship_phase": self.relationship_phases.current_phase,
            "trust": self.psyche.psyche.get("trust", 0.3),
            "hurt": self.psyche.psyche.get("hurt", 0.0),
            "conflict_stage": self.conflict_lifecycle.current_stage,
            "hours_since_last_message": 0.0,  # Will be updated after temporal context is computed
            "circadian_phase": "afternoon",  # Will be updated after temporal context is computed
            "energy": self.embodiment.E_daily,
            "unresolved_threads": self._safe_count_act_threads(),
            "reciprocity_balance": self.reciprocity_ledger.balance,
            "vulnerability_willingness": self.personality.relationship.get("vulnerability_willingness", 0.5)
        }
        router_decision = self.cognitive_router.route(router_context)
        
        # Now determine processing depth based on semantic understanding AND router decision
        processing_depth = self._determine_processing_depth(user_message, perception, fast_mode, understanding)
        
        # Override with router decision (router has final say)
        processing_depth.update({
            "use_qmas": router_decision.get("use_qmas", processing_depth.get("qmas", False)),
            "use_deep_reasoning": router_decision.get("use_deep_reasoning", processing_depth.get("deep_reasoning", False)),
            "use_enhanced_semantic": router_decision.get("use_enhanced_semantic", processing_depth.get("enhanced_semantic", False)),
            "use_creativity": router_decision.get("use_creativity", processing_depth.get("creativity", False)),
            "use_self_narrative": router_decision.get("use_self_narrative", processing_depth.get("self_narrative", False)),
            "router_reasoning": router_decision.get("reasoning", "")
        })
        
        # Enhanced semantic extraction (SKIP for lightweight mode - saves LLM call)
        enhanced_understanding = {}
        if processing_depth["enhanced_semantic"]:
            historical_patterns = self.memory.get_episodic(min_salience=0.3)[-10:]  # Last 10 for patterns
            enhanced_understanding = await self.enhanced_semantic.extract_enhanced_understanding(
                user_message, context, historical_patterns
            )
            understanding.update(enhanced_understanding)
        else:
            # Lightweight fallback - minimal enhanced understanding
            enhanced_understanding = {
                "sarcasm": {"detected": False, "confidence": 0.0},
                "ambiguity_resolution": {"resolved": True, "confidence": 0.8}
            }
            understanding.update(enhanced_understanding)
        
        # Merge understanding into perception
        perception.update({
            "intent": understanding.get("intent", "chat"),
            "sincerity": understanding.get("sincerity", 0.7),
            "subtext": understanding.get("subtext", ""),
            "emotional_truth": understanding.get("emotional_truth", {}),
            "sarcasm": enhanced_understanding.get("sarcasm", {}),
            "ambiguity": enhanced_understanding.get("ambiguity_resolution", {})
        })
        
        events = understanding.get("events", [])
        
        # Stage 3: Conflict Detection & Lifecycle
        conflict_triggered = self.conflict_lifecycle.detect_conflict_trigger(
            user_message, understanding, self.psyche.get_psyche_summary()
        )
        if conflict_triggered and not self.conflict_lifecycle.current_stage:
            self.conflict_lifecycle.transition_stage("TRIGGER", 0.0)
        
        # Stage 4: Psyche Engine Update (with variance and bad days)
        self._update_psyche(perception, events, understanding, user_message)
        
        # Apply "bad day" effect (random mood shifts)
        mood = self.psyche.get_mood_vector()
        mood = HumanQuirks.add_bad_day_effect(mood, bad_day_probability=0.05)
        # Update mood in psyche
        for key, value in mood.items():
            if key in self.psyche.mood:
                self.psyche.mood[key] = value
        
        # Stage 5: Embodiment State Update (energy budgeting)
        delta_hours = self._get_delta_hours()
        delta_days = delta_hours / 24.0
        self.embodiment.update_energy(mood, delta_hours)
        self.embodiment.update_capacity(message_sent=False)  # User sent, not AI yet
        
        # Stage 5.5: Personality Drift (long-term personality evolution)
        # Apply natural drift to personality layers (core and relationship)
        # This ensures personality evolves over weeks/months, not just adapts to user
        self.personality.apply_drift(delta_days)
        self.personality.decay_situational(delta_hours)
        
        # Stage 6: Temporal Awareness (needed for memory pattern detection)
        temporal_context = await self._get_temporal_context()
        
        # Update router context with temporal information (for logging/debugging)
        router_context["hours_since_last_message"] = temporal_context.get("hours_since_last_message", 0.0)
        router_context["circadian_phase"] = temporal_context.get("circadian_phase", "afternoon")
        
        # Stage 7: Memory System Update (includes pattern detection)
        self._update_memory(user_message, perception, events, understanding, temporal_context)
        
        # Stage 8: Reciprocity Ledger Update
        self._update_reciprocity(events, understanding, perception)
        
        # Stage 8.5: Parallel Life Awareness (update user's life context)
        self.parallel_life.update_from_message(user_message, understanding, self.memory)
        
        # Stage 9: CPBM Learning (observe user style)
        cpbm_context = {
            "emotion": perception.get("emotion", "neutral"),
            "circadian_phase": temporal_context.get("circadian_phase", "afternoon")
        }
        observed_patterns = self.cpbm.observe_user_style(user_message, cpbm_context)
        # Calculate engagement score from user response signals
        engagement_score = self._calculate_engagement_score(
            user_message, perception, understanding, temporal_context
        )
        self.cpbm.update_from_engagement(observed_patterns, engagement_score)
        
        # Stage 10: Personality Layer Updates
        interaction_data = {
            "user_style": observed_patterns,
            "engagement": engagement_score
        }
        self.personality.update_relationship_layer(interaction_data)
        
        # Stage 11: Relationship Phase Evaluation
        # Calculate "shared history" as meaningful interactions (not just message count)
        # Shared history = episodic events + identity facts + trust-building moments
        episodic_memories = self.memory.get_episodic(min_salience=0.1)
        identity_memories = self.memory.get_identity(min_confidence=0.5)
        
        # Count meaningful relationship milestones:
        # - Episodic memories (emotionally salient events)
        # - Identity memories (facts learned about user)
        # - High-salience episodic events (trust-building moments)
        high_salience_episodic = [m for m in episodic_memories if m.get("salience", 0) > 0.6]
        shared_history_score = (
            len(episodic_memories) * 0.4 +  # Episodic events contribute to shared history
            len(identity_memories) * 0.3 +  # Identity facts contribute
            len(high_salience_episodic) * 0.3  # High-salience events (conflicts, apologies, deep conversations)
        )
        
        # Phase transitions are now LLM-reasoned — they only happen during
        # deep reflections, not per-message. The reflection prompt evaluates
        # conversation quality, emotional depth, and relationship dynamics.
        
        # Stage 12: Select relevant memories (with stochastic selection)
        # Let the memory system work naturally - no heuristic filtering
        selected_memories = self._select_memories_stochastic()
        
        # Stage 13: Get current psyche summary
        psyche_summary = self.psyche.get_psyche_summary()
        
        # Stage 14: Pre-Response Assessment (LLM-driven, replaces hardcoded ToM + intentions)
        # Single 8B LLM call that reads the room: user state, Rem's intent, reciprocity feel
        recent_stm_for_assessment = self.memory.get_stm(decay=False)[-6:]
        assessment_messages = [
            {"role": m.get("role", "user"), "content": m.get("content", "")}
            for m in recent_stm_for_assessment
        ]
        # Gather compact context for richer assessment
        _rum_data = self.state.get("_rumination")
        _rum_summary = None
        if _rum_data and isinstance(_rum_data, dict):
            thoughts = _rum_data.get("lingering_thoughts", [])
            if thoughts:
                _rum_summary = "; ".join(thoughts[:2])
        
        _proactive = self.state.get("_proactive_depth")
        
        _plc = None
        if hasattr(self, 'parallel_life') and self.parallel_life:
            plc_data = self.parallel_life.get_life_context_for_prompt()
            if plc_data.get("has_parallel_life"):
                parts = []
                if plc_data.get("social_circle"):
                    parts.append(f"people: {', '.join(plc_data['social_circle'][:3])}")
                if plc_data.get("routines"):
                    parts.append(f"routines: {', '.join(plc_data['routines'][:2])}")
                if parts:
                    _plc = "; ".join(parts)
        
        _time_phase = temporal_context.get("circadian_phase", "afternoon") if temporal_context else "afternoon"
        
        # Get life triggers from parallel life system
        _life_triggers = None
        if hasattr(self, 'parallel_life') and self.parallel_life:
            if hasattr(self.parallel_life, 'get_active_triggers'):
                _life_triggers = self.parallel_life.get_active_triggers()
        
        pre_assessment = await self._subconscious_think(
            recent_messages=assessment_messages,
            user_message=user_message,
            psyche_summary=psyche_summary,
            relationship_phase=self.relationship_phases.current_phase,
            conflict_stage=conflict_stage,
            reciprocity_balance=self.reciprocity_ledger.balance,
            rumination_summary=_rum_summary,
            proactive_depth=_proactive,
            parallel_life_summary=_plc,
            time_of_day=_time_phase,
            user_facts=self.state.get("_user_facts"),
            rem_recent_responses=self.state.get("_rem_recent_responses", []),
            neurochem={
                "dopamine": self.psyche.neurochem.get("da", 0.5),
                "cortisol": self.psyche.neurochem.get("cort", 0.3),
                "oxytocin": self.psyche.neurochem.get("oxy", 0.5),
            },
            energy=self.psyche.neurochem.get("ne", 0.5),
            named_mood=self.psyche.get_named_mood_state().get("state", "") if hasattr(self.psyche, 'get_named_mood_state') else None,
            life_triggers=_life_triggers,
            situational_facts=self.state.get("_situational_facts", []),
        )
        
        # Fallback: keep hardcoded ToM/intentions as backup if LLM call fails
        if not pre_assessment:
            recent_interactions = [{"message": m.get("content", ""), "emotion": m.get("emotion", "neutral")} 
                                  for m in self.memory.get_stm(decay=False)[-5:]]
            tom_state = self.theory_of_mind.predict_user_state(
                temporal_context, self.memory, recent_interactions
            )
            intention_context = {
                "trust": psyche_summary.get("trust", 0.3),
                "hurt": psyche_summary.get("hurt", 0.0),
                "relationship_phase": self.relationship_phases.current_phase,
                "conflict_stage": conflict_stage,
                "emotion": perception.get("emotion", "neutral"),
                "reciprocity_balance": self.reciprocity_ledger.balance,
                "vulnerability": self.personality.relationship.get("vulnerability_willingness", 0.5)
            }
            intentions = self.intention_hierarchy.generate_intentions(intention_context)
            primary_intentions = self.intention_hierarchy.get_primary_intentions(intentions)
        else:
            tom_state = None  # Replaced by pre_assessment
            primary_intentions = None  # Replaced by pre_assessment
        
        # Stage 9: Topic Rotation & Fatigue - Check if topic should be rotated
        recent_messages = [{"content": m.get("content", ""), "timestamp": m.get("timestamp", datetime.now(timezone.utc).isoformat())} 
                          for m in self.memory.get_stm(decay=False)[-20:]]
        current_topic = understanding.get("topic", "general")
        should_rotate = self.topic_rotation.should_rotate_topic(current_topic, recent_messages)
        new_topic = None
        if should_rotate:
            new_topic = self.topic_rotation.suggest_new_topic(
                recent_messages, self.relationship_phases.current_phase, mood
            )
            if new_topic:
                print(f"[DEBUG] Topic rotation: {current_topic} -> {new_topic}")
        self.topic_rotation.update_topic_fatigue(current_topic, recent_messages)
        self.topic_rotation.decay_fatigue(delta_hours)
        
        # Stage 15: QMAS - Multi-Agent Debate (ONLY when needed - smart activation)
        agent_state = self._get_agent_state()
        # conflict_stage already initialized at the beginning of the function
        
        # Use processing depth to determine if we need QMAS
        use_qmas = processing_depth["qmas"]
        
        # Also check reasoning mode (for backward compatibility)
        reasoning_mode = self.two_stage_llm.should_enter_reasoning_mode(
            psyche_summary, understanding, conflict_stage
        ) if not processing_depth["lightweight"] else False
        
        qmas_path = None
        if use_qmas and not processing_depth["lightweight"]:
            # Use QMAS for multi-perspective debate (only for complex situations)
            try:
                situation = {
                    "user_message": user_message,
                    "psyche_state": psyche_summary,
                    "selected_memories": selected_memories,
                    "temporal_context": temporal_context,
                    "understanding": understanding,
                    "relationship_phase": self.psyche.psyche.get("relationship_phase", "Building")
                }
                
                # Use fewer paths for faster processing (10 instead of 20)
                qmas_path = await self.qmas.execute_debate(situation, num_paths=10, 
                                                           creativity_engine=self.creativity_engine)  # Pass creativity engine
            except Exception as e:
                # If QMAS fails, continue without it (graceful degradation)
                print(f"QMAS error (non-critical): {e}")
                qmas_path = None
        
        # Stage 16: Two-Stage LLM Reasoning (ONLY when needed - smart activation)
        reasoning_artifact = None
        use_deep_reasoning = processing_depth["deep_reasoning"] and reasoning_mode
        if use_deep_reasoning:
            try:
                # Synthesize personality for reasoning
                task_type = "deep_disclosure" if conflict_stage else "default"
                synthesized_persona = self.personality.synthesize_persona(task_type, mood)
                
                reasoning_artifact = await self.two_stage_llm.stage1_inner_reasoning(
                    user_message=user_message,
                    perception=perception,
                    understanding=understanding,
                    psyche_state=psyche_summary,
                    selected_memories=selected_memories,
                    temporal_context=temporal_context,
                    personality=synthesized_persona,  # Use synthesized persona
                    qmas_path=qmas_path
                )
            except Exception as e:
                # If reasoning fails, fall back to normal mode
                print(f"Reasoning error (falling back to normal mode): {e}")
                reasoning_mode = False
                reasoning_artifact = None
        
        # Stage 17: Creativity Engine (ONLY when appropriate - smart activation)
        creativity_content = None
        if processing_depth["creativity"] and not reasoning_mode:  # Don't interrupt serious reasoning with creativity
            try:
                creativity_context = {
                    "boredom": mood.get("boredom", 0.0),
                    "tom_receptivity": tom_state.get("openness_to_initiative", 0.5),
                    "openness": self.personality.core.get("big_five", {}).get("openness", 0.5),
                    "circadian_phase": temporal_context.get("circadian_phase", "afternoon"),
                    "relationship_phase": self.relationship_phases.current_phase,
                    "recent_topics": [m.get("content", "")[:50] for m in self.memory.get_stm(decay=False)[-3:]],
                    "personality": self.personality.core
                }
                creativity_content = await self.creativity_engine.generate_creative_content(creativity_context)
            except Exception as e:
                # Non-critical, continue without creativity
                print(f"Creativity engine error (non-critical): {e}")
                creativity_content = None
        
        # Stage 17.5: Self-Narrative Generation (ONLY in deep relationships - smart activation)
        self_narrative = None
        if processing_depth["self_narrative"] and not reasoning_mode and not conflict_stage:
            try:
                narrative_context = {
                    "relationship_phase": self.relationship_phases.current_phase,
                    "trust": psyche_summary.get("trust", 0.7),
                    "vulnerability_willingness": self.personality.relationship.get("vulnerability_willingness", 0.5),
                    "recent_patterns": recent_interactions[-10:],
                    "personality": {
                        "big_five": self.personality.core.get("big_five", {}),
                        "attachment_style": self.personality.core.get("attachment_style", "secure")
                    },
                    "psyche_state": psyche_summary,
                    "memory": self.memory
                }
                self_narrative = await self.self_narrative.generate_self_narrative(narrative_context)
            except Exception as e:
                # Non-critical, continue without self-narrative
                print(f"Self-narrative error (non-critical): {e}")
                self_narrative = None
        
        # Stage 18: Message Sequence Planning (if generating response)
        message_plan = None
        style_mode = self.cpbm.get_style_mode(mood)
        synthesized_persona = self.personality.synthesize_persona("default", mood) if not reasoning_mode else None
        
        if reasoning_mode or not conflict_stage or conflict_stage in ["REPAIR", "RESOLUTION"]:
            energy = self.embodiment.E_daily
            persona_for_planning = synthesized_persona if reasoning_mode else self.state.get("core_personality", {})
            message_plan = self.message_planner.plan_sequence(
                mood, style_mode, persona_for_planning, energy
            )
        
        # Stage 17: Counterfactual Replayer - Check if this is a major episode
        episode_context = {
            "hurt": psyche_summary.get("hurt", 0.0),
            "trust_delta": psyche_summary.get("trust", 0.3) - (self.state.get("current_psyche", {}).get("trust", 0.3)),
            "vulnerability": mood.get("vulnerability", 0.1),
            "phase_transition": False  # Phase transitions now happen during reflections only
        }
        
        if self.counterfactual_replayer.identify_major_episode(episode_context):
            # Save episode for later replay
            episode = {
                "user_message": user_message,
                "response": None,  # Will be filled after response generation
                "trust_before": self.state.get("current_psyche", {}).get("trust", 0.3),
                "hurt_before": self.state.get("current_psyche", {}).get("hurt", 0.0),
                "relationship_phase": self.relationship_phases.current_phase,
                "conflict_stage": conflict_stage,
                "intentions": primary_intentions
            }
            self.counterfactual_replayer.save_episode(episode)
        
        # Stage 19.5: State Reflection (Light every 15, Deep every 30)
        self.personality_evolution.tick_interaction()
        
        # === Game Progression: XP Awards for message-level events ===
        try:
            # Award base XP for messaging
            self.xp_system.award_xp("user_message_received")

            # First message of the day — guard with date check to avoid calling every message
            today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            last_xp_date = self.state.get("_last_xp_date")
            if last_xp_date != today_str:
                self.xp_system.award_xp("first_message_of_day")
                self.xp_system.check_absence_decay()
                self.state["_last_xp_date"] = today_str
            
            # Midnight bonus (11pm-3am)
            current_hour = datetime.now(timezone.utc).hour
            # Approximate IST adjustment (+5:30)
            ist_hour = (current_hour + 5) % 24
            if ist_hour >= 23 or ist_hour < 3:
                self.xp_system.award_xp("midnight_bonus")
        except Exception as xp_err:
            print(f"[XP] Error: {xp_err}")
        
        # Gather data for reflection
        recent_stm = self.memory.get_stm(decay=False)
        recent_messages = [
            {"role": "user" if i % 2 == 0 else "assistant", "content": m.get("content", "")}
            for i, m in enumerate(recent_stm[-30:])
        ]
        identity_mems = self.memory.get_identity(min_confidence=0.5)
        episodic_mems = self.memory.get_episodic(min_salience=0.3)
        
        # Check for DEEP reflection first (every 30 messages)
        if self.personality_evolution.should_deep_reflect():
            try:
                asyncio.create_task(self._run_deep_reflection(
                    recent_messages=recent_messages,
                    identity_memories=identity_mems,
                    episodic_memories=episodic_mems,
                    psyche_summary=psyche_summary
                ))
                print(f"[DEEP REFLECTION] Triggered at interaction {self.personality_evolution.interaction_count}")
            except Exception as e:
                print(f"[WARNING] Deep reflection error: {e}")
        
        # Check for LIGHT reflection (every 15 messages, but not when deep just ran)
        elif self.personality_evolution.should_light_reflect():
            try:
                asyncio.create_task(self._run_light_reflection(
                    recent_messages=recent_messages,
                    psyche_summary=psyche_summary
                ))
                print(f"[LIGHT REFLECTION] Triggered at interaction {self.personality_evolution.interaction_count}")
            except Exception as e:
                print(f"[WARNING] Light reflection error: {e}")
        
        # Check for STM Summary (every 10 messages — independent of reflections)
        if self.personality_evolution.should_summarize_stm():
            try:
                asyncio.create_task(self._run_stm_summary())
                print(f"[STM SUMMARY] Triggered at interaction {self.personality_evolution.interaction_count}")
            except Exception as e:
                print(f"[WARNING] STM summary error: {e}")
        
        # Check for Memory Consolidation (every 20 messages — independent of reflections)
        if self.personality_evolution.should_consolidate_memory():
            try:
                asyncio.create_task(self._run_memory_consolidation())
                print(f"[MEMORY CONSOLIDATION] Triggered at interaction {self.personality_evolution.interaction_count}")
            except Exception as e:
                print(f"[WARNING] Memory consolidation error: {e}")
        
        # Stage 20: Save all state
        self._save_state()
        
        return {
            "perception": perception,
            "understanding": understanding,
            "enhanced_understanding": enhanced_understanding,
            "events": events,
            "selected_memories": selected_memories,
            "psyche_state": psyche_summary,
            "agent_state": agent_state,
            "temporal_context": temporal_context,
            "reasoning_mode": reasoning_mode,
            "processing_depth": processing_depth,  # Include for debugging/monitoring
            "reasoning_artifact": reasoning_artifact,
            "qmas_path": qmas_path,
            "intentions": primary_intentions,  # Stage 8 output (None if pre_assessment succeeded)
            "topic_rotation": {"should_rotate": should_rotate, "suggested_topic": new_topic if should_rotate else None},  # Stage 9 output
            "router_decision": router_decision,  # Stage 6 output
            "conflict_stage": conflict_stage,
            "tom_state": tom_state,  # None if pre_assessment succeeded
            "pre_assessment": pre_assessment,  # LLM-driven room reading
            "personality_synthesized": synthesized_persona if reasoning_mode else None,
            "cpbm_style_mode": style_mode if 'style_mode' in locals() else "normal",
            "message_plan": message_plan,
            "embodiment_state": {
                "E_daily": self.embodiment.E_daily,
                "capacity": self.embodiment.capacity,
                "body_state": self.embodiment.get_body_state()
            },
            "reciprocity_balance": self.reciprocity_ledger.balance,
            "relationship_phase": self.relationship_phases.current_phase,
            "creativity_content": creativity_content,
            "self_narrative": self_narrative,
            "parallel_life_context": self.parallel_life.get_life_context_for_prompt()
        }
    
    def _safe_count_act_threads(self) -> int:
        """Safely count active ACT threads with salience > 0.5.
        Returns 0 if the memory system has malformed thread data (e.g. after reset)."""
        try:
            return len([t for t in self.memory.get_act_threads() if t.get("salience", 0) > 0.5])
        except Exception:
            return 0
    
    def _perception_layer(self, message: str, emotion_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Stage 1: Perception Layer - Emotion classification."""
        # Use emotion data if provided, otherwise infer from message
        if emotion_data:
            emotion = emotion_data.get("emotion", "neutral")
            valence = emotion_data.get("valence", 0.0)
            arousal = emotion_data.get("arousal", 0.0)
        else:
            # Simple heuristic fallback
            emotion = "neutral"
            valence = 0.0
            arousal = 0.0
        
        # Add natural variance (emotion detection isn't perfect)
        valence = StochasticBehavior.add_response_variance(valence, 0.1)
        arousal = StochasticBehavior.add_response_variance(arousal, 0.1)
        
        return {
            "emotion": emotion,
            "valence": max(-1.0, min(1.0, valence)),
            "arousal": max(-1.0, min(1.0, arousal)),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def _update_psyche(self, perception: Dict[str, Any], events: List[Dict[str, Any]], 
                      understanding: Dict[str, Any], user_message: str = ""):
        """Stage 3: Update psyche engine with variance and nuance."""
        # Use emotional truth from understanding (may differ from stated emotion)
        emotional_truth = understanding.get("emotional_truth", {})
        actual_emotion = emotional_truth.get("emotion", perception.get("emotion", "neutral"))
        intensity = emotional_truth.get("intensity", 0.5)
        is_masked = emotional_truth.get("masked", False)
        
        # Build emotion impact with variance (humans don't react identically each time)
        emotion_impact = {}
        base_impact = intensity
        
        # If emotion is masked, reduce impact (AI detects the mask)
        if is_masked:
            base_impact *= 0.7
        
        # Add variance (same situation feels different on different days)
        base_impact = StochasticBehavior.get_emotional_reaction_variance(base_impact)
        
        emotion_impact[actual_emotion] = base_impact
        
        # Get time since last update
        last_update = self.state.get("metadata", {}).get("updated_at")
        if last_update:
            last_time = datetime.fromisoformat(last_update.replace("Z", "+00:00"))
            delta_hours = (datetime.now(timezone.utc) - last_time).total_seconds() / 3600
        else:
            delta_hours = 0.0
        
        self.psyche.update_mood(emotion_impact, delta_hours)
        
        # Update neurochemicals FIRST (they drive mood, not the other way around)
        # This is the key: events → neurochemicals → mood → behavior
        current_trust = self.psyche.psyche.get("trust", 0.5)
        current_phase = self.relationship_phases.current_phase
        
        for event in events:
            event_type = event.get("type", "").lower()
            confidence = event.get("confidence", 0.5)
            
            # Only process high-confidence events (but add some randomness)
            if confidence < 0.4 and random.random() > 0.2:  # 20% chance to process low-confidence
                continue
            
            # Map event types to neurochemical events (broad matching)
            neuro_event_type = None
            if "conflict" in event_type or "hurt" in event_type or "insult" in event_type or "disrespect" in event_type:
                neuro_event_type = "conflict"
            elif "promise" in event_type or "commitment" in event_type or "novel" in event_type:
                neuro_event_type = "novel_interaction"
            elif "apolog" in event_type or "sorry" in event_type or "reconcil" in event_type or "repair" in event_type:
                neuro_event_type = "reconciliation"
            elif "vulnerab" in event_type or "confess" in event_type or "personal_share" in event_type or "sharing" in event_type or "open" in event_type:
                neuro_event_type = "vulnerability"
            elif "achiev" in event_type or "celebrat" in event_type or "success" in event_type or "accomplish" in event_type or "proud" in event_type:
                neuro_event_type = "achievement"
            elif "excit" in event_type or "enthusi" in event_type or "joy" in event_type or "happy" in event_type:
                neuro_event_type = "excitement"
            elif "affection" in event_type or "compliment" in event_type or "flirt" in event_type or "warmth" in event_type or "care" in event_type or "love" in event_type:
                neuro_event_type = "affection"
            elif "reject" in event_type or "dismiss" in event_type or "ignore" in event_type:
                neuro_event_type = "rejection"
            elif "bored" in event_type or "disinterest" in event_type or "monoton" in event_type:
                neuro_event_type = "boredom"
            elif "stress" in event_type or "anxious" in event_type or "pressure" in event_type or "overwhelm" in event_type or "worried" in event_type:
                neuro_event_type = "stress"
            elif "humor" in event_type or "joke" in event_type or "funny" in event_type or "laugh" in event_type:
                neuro_event_type = "excitement"  # humor → dopamine/energy
            
            if neuro_event_type:
                # Update neurochemicals with context (trust + phase scale impact)
                self.psyche.update_neurochemicals(
                    neuro_event_type, intensity=confidence, 
                    delta_hours=delta_hours,
                    trust=current_trust, relationship_phase=current_phase
                )
        
        # Update trust/hurt based on events (with variance)
        for event in events:
            event_type = event.get("type", "")
            confidence = event.get("confidence", 0.5)
            
            if confidence < 0.4 and random.random() > 0.2:
                continue
            
            if "conflict" in event_type.lower() or "hurt" in event_type.lower():
                hurt_score = 0.3 * confidence
                if understanding.get("sincerity", 0.7) < 0.5:
                    hurt_score *= 0.7
                hurt_score = StochasticBehavior.add_response_variance(hurt_score, 0.1)
                self.psyche.update_hurt(hurt_score)
            
            elif event_type == "promise" or "commitment" in event_type.lower():
                trust_gain = 0.1 * confidence * understanding.get("sincerity", 0.7)
                trust_gain = StochasticBehavior.add_response_variance(trust_gain, 0.05)
                self.psyche.update_trust(trust_gain)
            
            elif "apology" in event_type.lower() or "sorry" in event_type.lower():
                sincerity = understanding.get("sincerity", 0.7)
                self.psyche.update_forgiveness(sincerity, reparative_action=True, 
                                              consistency_score=sincerity)
        
        # Decay hurt over time
        self.psyche.decay_hurt(delta_hours)
        
        # Update neurochemicals for natural decay (even without events)
        self.psyche.update_neurochemicals("natural_decay", intensity=0.0, delta_hours=delta_hours,
                                         trust=current_trust, relationship_phase=current_phase)
        
        # === BASELINE INTERACTION NUDGE ===
        # Every interaction produces at least a tiny neurochem shift based on
        # the emotional truth from understanding (LLM-assessed, not heuristic).
        # perception.valence is often 0.0 in web (no emotion_data), so use understanding.
        emotional_truth = understanding.get("emotional_truth", {})
        truth_intensity = emotional_truth.get("intensity", 0.0)
        truth_emotion = emotional_truth.get("emotion", "neutral").lower()
        
        # Determine valence from emotional truth
        positive_emotions = {"happy", "excited", "grateful", "proud", "joyful", "hopeful",
                           "content", "amused", "relieved", "enthusiastic", "love", "affectionate"}
        negative_emotions = {"sad", "angry", "frustrated", "anxious", "stressed", "hurt",
                           "disappointed", "afraid", "disgusted", "lonely", "overwhelmed"}
        
        if truth_intensity > 0.2:
            if truth_emotion in positive_emotions or truth_emotion not in negative_emotions:
                # Positive or neutral interaction → small dopamine + oxytocin bump
                self.psyche.update_neurochemicals(
                    "affection", intensity=0.3 * truth_intensity,
                    delta_hours=0, trust=current_trust, relationship_phase=current_phase
                )
            if truth_emotion in negative_emotions:
                # Negative interaction → cortisol spike + norepinephrine
                self.psyche.update_neurochemicals(
                    "stress", intensity=0.3 * truth_intensity,
                    delta_hours=0, trust=current_trust, relationship_phase=current_phase
                )
        
        # === ENGAGEMENT NUDGE: ANY interaction = alertness (norepinephrine) ===
        # Talking to someone means you're alert and paying attention.
        # This fixes NE being stuck at 0.5 — it should rise during conversation.
        if truth_intensity > 0.1:
            ne_bump = 0.05 + 0.1 * truth_intensity  # 0.06 to 0.15
            current_ne = self.psyche.neurochem.get("ne", 0.5)
            self.psyche.neurochem["ne"] = min(1.0, current_ne + ne_bump)
            
            # Also give a tiny cortisol nudge — even pleasant conversations
            # have a baseline stress of social engagement
            cort_bump = 0.02 * truth_intensity
            current_cort = self.psyche.neurochem.get("cort", 0.3)
            self.psyche.neurochem["cort"] = min(1.0, current_cort + cort_bump)
        
        # Trust and phase changes are now LLM-reasoned — they only change
        # during light/deep reflections. The LLM evaluates conversation quality,
        # sincerity, emotional depth, and outputs trust_delta with reasoning.
        # No more heuristic per-message bumps or losses.
        
        # NOTE: Inappropriate behavior detection (pet names from strangers, boundary
        # violations, etc.) is handled by the system prompt — the LLM decides what
        # feels uncomfortable given the relationship phase, rather than keyword matching
        # that false-positives on things like "my baby sister is sick".
    
    async def _run_light_reflection(
        self,
        recent_messages: List[Dict[str, str]],
        psyche_summary: Dict[str, Any]
    ):
        """
        Run Light Reflection (every ~15 messages).
        Updates: stance, respect, engagement, posture, quirks.
        """
        try:
            trust = psyche_summary.get("trust", 0.3)
            hurt = psyche_summary.get("hurt", 0.0)
            
            updates = await self.personality_evolution.light_reflect(
                recent_messages=recent_messages,
                relationship_phase=self.relationship_phases.current_phase,
                trust=trust,
                hurt=hurt,
                current_stance=self.psyche.stance,
                current_respect=self.psyche.respect,
                current_engagement=self.psyche.engagement,
                entitlement_debt=self.psyche.entitlement_debt,
                emotional_complexity=self.relationship_phases.get_emotional_complexity(),
                unresolved_wounds=self.psyche.get_unresolved_wounds()
            )
            
            if updates:
                # Apply updates to psyche
                self.psyche.apply_reflection_updates(updates)
                
                # Consume any pending episodic events from light reflection
                # (Light reflection generates episodic_thread summaries that were previously orphaned)
                pending = self.personality_evolution.pending_episodic_events
                if pending:
                    existing_episodic = self.memory.get_episodic(min_salience=0.0)
                    existing_contents = [e.get("content", "").lower()[:60] for e in existing_episodic]
                    for event_text in pending:
                        if isinstance(event_text, str) and len(event_text) > 5:
                            event_key = event_text[:60].lower()
                            if any(event_key in ec or ec in event_key for ec in existing_contents if ec):
                                print(f"[LIGHT REFLECTION] Skipped duplicate episodic: {event_text[:60]}...")
                                continue
                            self.memory.add_episodic(
                                event_type="reflection_thread",
                                content=event_text[:200],
                                emotional_valence=0.0,
                                relational_impact=0.4,
                            )
                            existing_contents.append(event_key)
                            print(f"[LIGHT REFLECTION] Stored episodic: {event_text[:60]}...")
                    self.personality_evolution.pending_episodic_events = []
                    self.personality_evolution.save()
                
                # Phase transition from light reflection too
                if updates.get("phase_ready") and updates.get("suggested_phase"):
                    suggested = updates["suggested_phase"]
                    reasoning = updates.get("phase_reasoning", "LLM decided")
                    current = self.relationship_phases.current_phase
                    if suggested != current and suggested in ["Discovery", "Building", "Steady", "Deep", "Maintenance", "Volatile"]:
                        self.relationship_phases.transition_phase(suggested)
                        print(f"[LIGHT REFLECTION] Phase: {current} → {suggested} (reason: {reasoning})")
                
                # Store LLM-extracted milestones
                pending_milestones = getattr(self.personality_evolution, 'pending_milestones', [])
                if pending_milestones:
                    for ms in pending_milestones:
                        if isinstance(ms, dict) and ms.get("milestone"):
                            milestone_text = ms["milestone"]
                            significance = ms.get("significance", "")
                            trust_impact = float(ms.get("trust_impact", 0))
                            
                            full_content = f"{milestone_text} — {significance}" if significance else milestone_text
                            self.memory.add_episodic(
                                event_type="relationship_milestone",
                                content=full_content[:200],
                                emotional_valence=0.6,
                                relational_impact=0.7,
                            )
                            
                            if trust_impact != 0:
                                clamped = max(-0.1, min(0.1, trust_impact))
                                current_trust = self.psyche.psyche.get("trust", 0.5)
                                self.psyche.psyche["trust"] = max(0.0, min(1.0, current_trust + clamped))
                                print(f"[MILESTONE] Trust impact: {clamped:+.2f} → {self.psyche.psyche['trust']:.2f}")
                            
                            print(f"[MILESTONE] Stored: {milestone_text[:80]}")
                    self.personality_evolution.pending_milestones = []
                
                # Store behavioral observations
                pending_observations = getattr(self.personality_evolution, 'pending_behavioral_observations', [])
                if pending_observations:
                    existing_obs = self.state.get("_behavioral_observations", [])
                    for obs in pending_observations:
                        if isinstance(obs, str) and not any(
                            obs.lower()[:40] in e.lower() or e.lower()[:40] in obs.lower()
                            for e in existing_obs
                        ):
                            existing_obs.append(obs)
                    self.state["_behavioral_observations"] = existing_obs[-10:]
                    self.personality_evolution.pending_behavioral_observations = []
                
                # Store personality evolution note
                evo_note = getattr(self.personality_evolution, 'personality_evolution_note', '')
                if evo_note:
                    self.state["_personality_evolution_note"] = evo_note
                
                self._save_state()
                print(f"[LIGHT REFLECTION] Applied - Stance: {self.psyche.stance}, Respect: {self.psyche.respect:.2f}, Engagement: {self.psyche.engagement:.2f}")
                
                # Process wound resolutions from reflection
                wound_resolutions = updates.get("wound_resolutions", [])
                for wr in wound_resolutions:
                    if isinstance(wr, dict):
                        idx = wr.get("index", -1)
                        reason = wr.get("reason", "addressed in conversation")
                        self.psyche.resolve_wound(idx, reason)
                
                # Auto-create wound when hurt increases significantly
                hurt_delta = updates.get("hurt_delta", 0)
                if hurt_delta and float(hurt_delta) > 0.05:
                    # Use the conversation context to create a wound
                    convo_summary = updates.get("conversation_summary", "something in the conversation")
                    user_eval = updates.get("user_evaluation", "")
                    wound_cause = convo_summary[:100] if convo_summary else "something hurtful was said"
                    self.psyche.create_wound(wound_cause, min(float(hurt_delta) * 3, 0.8))
                
                # Store eruption if one is building
                eruption = updates.get("eruption")
                if eruption:
                    self.state["_pending_eruption"] = eruption
                    print(f"[ERUPTION] Pending: {eruption[:60]}...")
                
                # Store proactive depth question
                proactive_depth = updates.get("proactive_depth")
                if proactive_depth:
                    self.state["_proactive_depth"] = proactive_depth
                    print(f"[PROACTIVE DEPTH] Question: {proactive_depth[:60]}...")
        
        except Exception as e:
            print(f"[ERROR] Light reflection failed: {e}")
            import traceback
            traceback.print_exc()
    
    async def _run_deep_reflection(
        self,
        recent_messages: List[Dict[str, str]],
        identity_memories: List[Dict],
        episodic_memories: List[Dict],
        psyche_summary: Dict[str, Any]
    ):
        """
        Run Deep Reflection (every ~30 messages).
        Updates: personality text, long-term traits, phase, memories.
        """
        try:
            trust = psyche_summary.get("trust", 0.3)
            hurt = psyche_summary.get("hurt", 0.0)
            
            updates = await self.personality_evolution.deep_reflect(
                recent_messages=recent_messages,
                identity_memories=identity_memories,
                episodic_memories=episodic_memories,
                relationship_phase=self.relationship_phases.current_phase,
                trust=trust,
                hurt=hurt,
                unresolved_wounds=self.psyche.get_unresolved_wounds()
            )
            
            if updates:
                # Apply trust/hurt from deep reflection
                self.psyche.apply_reflection_updates(updates)
                
                # Phase transition — now LLM-reasoned (no heuristic thresholds)
                if updates.get("phase_ready") and updates.get("suggested_phase"):
                    suggested = updates["suggested_phase"]
                    reasoning = updates.get("phase_reasoning", "LLM decided")
                    current = self.relationship_phases.current_phase
                    if suggested != current and suggested in ["Discovery", "Building", "Steady", "Deep", "Maintenance", "Volatile"]:
                        self.relationship_phases.transition_phase(suggested)
                        print(f"[DEEP REFLECTION] Phase: {current} → {suggested} (reason: {reasoning})")
                    else:
                        print(f"[DEEP REFLECTION] Phase stays at {current} (reason: {reasoning})")
                
                # Store LLM-extracted identity facts (using correct function signature)
                new_identity = updates.get("new_identity_facts", [])
                if new_identity and isinstance(new_identity, list):
                    # Rem's known traits — identity facts should NOT contain these
                    rem_traits = {'psychology', 'psych', 'indie music', 'billie eilish', 'arctic monkeys', 
                                  'adele', 'college student', 'lives at home', 'commute', '30 min',
                                  'rem likes', 'rem enjoys', 'rem listens'}
                    # Also check Rem's generated self-identity
                    self_identity = self.state.get("_self_identity", {})
                    for sk, sv in self_identity.items():
                        val = sv.get("v", sv) if isinstance(sv, dict) else str(sv)
                        if isinstance(val, str) and len(val) > 3:
                            rem_traits.add(val.lower()[:30])
                    
                    for fact in new_identity:
                        if isinstance(fact, str) and len(fact) > 3:
                            fact_lower = fact.lower()
                            # Cross-validate: reject if it matches Rem's known traits
                            is_rem_fact = any(trait in fact_lower for trait in rem_traits)
                            if is_rem_fact:
                                print(f"[DEEP REFLECTION] REJECTED identity (Rem's trait, not user's): {fact}")
                                continue
                            # Check for duplicates before storing
                            existing = self.memory.get_identity(min_confidence=0.5)
                            already_exists = any(
                                f.get("fact", "").lower() == fact.lower()
                                for f in existing
                            )
                            if not already_exists:
                                identity_id = self.memory.promote_to_identity(
                                    fact=fact,
                                    confidence=0.8,
                                    evidence_count=1
                                )
                                if identity_id:
                                    print(f"[DEEP REFLECTION] Stored identity: {fact}")
                
                # Store LLM-extracted episodic events (using correct function signature)
                new_episodic = updates.get("new_episodic_events", [])
                if new_episodic and isinstance(new_episodic, list):
                    # Get existing episodic for dedup
                    existing_episodic = self.memory.get_episodic(min_salience=0.0)
                    existing_contents = [e.get("content", "").lower()[:60] for e in existing_episodic]
                    for event in new_episodic:
                        event_text = None
                        rem_experience = None
                        
                        # Handle both old format (string) and new format (dict with rem_experience)
                        if isinstance(event, str) and len(event) > 5:
                            event_text = event
                        elif isinstance(event, dict):
                            event_text = event.get("event", "")
                            rem_experience = event.get("rem_experience", None)
                        
                        if not event_text or len(event_text) < 5:
                            continue
                        
                        # Skip if similar content already exists
                        event_key = event_text[:60].lower()
                        if any(event_key in ec or ec in event_key for ec in existing_contents if ec):
                            print(f"[DEEP REFLECTION] Skipped duplicate episodic: {event_text[:60]}...")
                            continue
                        
                        # Store with rem_experience if available
                        self.memory.add_episodic(
                            event_type="significant_moment",
                            content=event_text[:200],
                            emotional_valence=0.0,
                            relational_impact=0.5,
                        )
                        
                        # Store rem_experience alongside the episodic memory
                        if rem_experience:
                            # Store in the most recent episodic entry
                            all_episodic = self.memory.get_episodic(min_salience=0.0)
                            if all_episodic:
                                all_episodic[-1]["rem_experience"] = rem_experience
                                print(f"[DEEP REFLECTION] Stored episodic with experience: {event_text[:40]}... | felt: {rem_experience[:40]}...")
                            else:
                                print(f"[DEEP REFLECTION] Stored episodic: {event_text[:60]}...")
                        else:
                            print(f"[DEEP REFLECTION] Stored episodic: {event_text[:60]}...")
                        existing_contents.append(event_key)  # Track newly added
                
                # Also consume any pending episodic from light reflections
                pending = self.personality_evolution.pending_episodic_events
                if pending:
                    for event_text in pending:
                        if isinstance(event_text, str) and len(event_text) > 5:
                            self.memory.add_episodic(
                                event_type="reflection_thread",
                                content=event_text[:200],
                                emotional_valence=0.0,
                                relational_impact=0.4,
                            )
                    self.personality_evolution.pending_episodic_events = []
                    self.personality_evolution.save()
                
                # Store LLM-extracted milestones as episodic memories + apply trust impact
                pending_milestones = getattr(self.personality_evolution, 'pending_milestones', [])
                if pending_milestones:
                    for ms in pending_milestones:
                        if isinstance(ms, dict) and ms.get("milestone"):
                            milestone_text = ms["milestone"]
                            significance = ms.get("significance", "")
                            trust_impact = float(ms.get("trust_impact", 0))
                            
                            # Store as episodic memory
                            full_content = f"{milestone_text} — {significance}" if significance else milestone_text
                            self.memory.add_episodic(
                                event_type="relationship_milestone",
                                content=full_content[:200],
                                emotional_valence=0.6,
                                relational_impact=0.7,
                            )
                            
                            # Apply trust impact from milestone
                            if trust_impact != 0:
                                clamped = max(-0.1, min(0.1, trust_impact))
                                current_trust = self.psyche.psyche.get("trust", 0.5)
                                self.psyche.psyche["trust"] = max(0.0, min(1.0, current_trust + clamped))
                                print(f"[MILESTONE] Trust impact: {clamped:+.2f} → {self.psyche.psyche['trust']:.2f}")
                            
                            print(f"[MILESTONE] Stored: {milestone_text[:80]}")
                    self.personality_evolution.pending_milestones = []
                
                # Store behavioral observations in state for prompt injection
                pending_observations = getattr(self.personality_evolution, 'pending_behavioral_observations', [])
                if pending_observations:
                    existing_obs = self.state.get("_behavioral_observations", [])
                    # Deduplicate — don't add if similar already exists
                    for obs in pending_observations:
                        if isinstance(obs, str) and not any(
                            obs.lower()[:40] in e.lower() or e.lower()[:40] in obs.lower()
                            for e in existing_obs
                        ):
                            existing_obs.append(obs)
                    self.state["_behavioral_observations"] = existing_obs[-10:]
                    self.personality_evolution.pending_behavioral_observations = []
                    print(f"[PATTERNS] Stored {len(pending_observations)} behavioral observations")
                
                # Store personality evolution note
                evo_note = getattr(self.personality_evolution, 'personality_evolution_note', '')
                if evo_note:
                    self.state["_personality_evolution_note"] = evo_note
                
                self._save_state()
                print(f"[DEEP REFLECTION] Applied - Personality updated, Trust: {self.psyche.psyche.get('trust', 0.3):.2f}")
                
                # Process wound resolutions from deep reflection
                wound_resolutions = updates.get("wound_resolutions", [])
                for wr in wound_resolutions:
                    if isinstance(wr, dict):
                        idx = wr.get("index", -1)
                        reason = wr.get("reason", "addressed in conversation")
                        self.psyche.resolve_wound(idx, reason)
                
                # Auto-create wound when hurt increases significantly in deep reflection
                hurt_delta = updates.get("hurt_delta", 0)
                if hurt_delta and float(hurt_delta) > 0.05:
                    convo_summary = updates.get("conversation_summary", "something in the conversation")
                    wound_cause = convo_summary[:100] if convo_summary else "something hurtful happened"
                    self.psyche.create_wound(wound_cause, min(float(hurt_delta) * 3, 0.8))
                    # XP penalty for wound
                    self.xp_system.penalize_xp("wound_created")
                
                # === Game Progression: Process XP events from reflection ===
                pending_xp = getattr(self.personality_evolution, 'pending_xp_events', [])
                if pending_xp:
                    for xp_event in pending_xp:
                        if isinstance(xp_event, str):
                            xp_awarded, transition = self.xp_system.award_xp(xp_event)
                            if transition:
                                # Sync phase with relationship_phases system
                                new_phase = transition.get("to_phase")
                                if new_phase and new_phase in ["Discovery", "Building", "Steady", "Deep", "Bonded"]:
                                    if new_phase != self.relationship_phases.current_phase:
                                        self.relationship_phases.transition_phase(new_phase)
                                        print(f"[XP→PHASE] Synced: {new_phase}")
                    self.personality_evolution.pending_xp_events = []
                    self.personality_evolution.save()
                
                # === Game Progression: Generate diary entry ===
                try:
                    diary_entry = await self.diary.maybe_write_entry(
                        reflection_data=updates,
                        relationship_phase=self.xp_system.current_phase,
                        trust=self.psyche.psyche.get("trust", 0.5),
                        user_name=self.state.get("user_name"),
                        xp_total=self.xp_system.total_xp,
                    )
                    if diary_entry:
                        # Award XP for milestone if diary found one
                        if diary_entry.get("has_milestone"):
                            self.xp_system.award_xp("milestone_reached")
                except Exception as de:
                    print(f"[DIARY] Error: {de}")
                
                self._save_state()
        
        except Exception as e:
            print(f"[ERROR] Deep reflection failed: {e}")
            import traceback
            traceback.print_exc()
    
    async def _subconscious_think(
        self,
        recent_messages: List[Dict[str, str]],
        user_message: str,
        psyche_summary: Dict[str, Any],
        relationship_phase: str,
        conflict_stage: Optional[str],
        reciprocity_balance: float,
        rumination_summary: Optional[str] = None,
        proactive_depth: Optional[str] = None,
        parallel_life_summary: Optional[str] = None,
        time_of_day: str = "afternoon",
        user_facts: Optional[Dict[str, Any]] = None,
        rem_recent_responses: Optional[List[str]] = None,
        neurochem: Optional[Dict[str, float]] = None,
        energy: float = 0.5,
        named_mood: Optional[str] = None,
        life_triggers: Optional[List[Dict[str, Any]]] = None,
        situational_facts: Optional[List[Dict[str, Any]]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Subconscious Router — models how a human THINKS before responding.
        
        Replaces _pre_response_assessment. Same cost (1 LLM call), richer output.
        Uses 70B primary with 8B fallback.
        
        10 layers of human thought:
        1. Gut reaction (raw first thought)
        2. Register read (how they're texting → how to match)
        3. Self-check (Rem's own mood/energy)
        4. Relationship calibration
        5. Memory trigger (does this remind me of something?)
        6. Effort calibration (how long should reply be?)
        7. Social timing awareness
        8. Emotional momentum (escalating/fading?)
        9. Interest check (genuinely curious or performing?)
        10. Self-continuity (am I being consistent?)
        
        Plus: section routing (which context to include in prompt)
        """
        try:
            import httpx
            await global_rate_limiter.wait_if_needed()
            
            # Format recent conversation
            convo_lines = []
            for m in recent_messages[-6:]:
                role = m.get("role", "user")
                content = m.get("content", "")[:150]
                convo_lines.append(f"{role}: {content}")
            convo_text = "\n".join(convo_lines)
            
            current_msg = user_message[:250]
            
            # Build user facts block
            user_facts_block = ""
            if user_facts and isinstance(user_facts, dict):
                fact_lines = []
                for key, val in list(user_facts.items())[:15]:
                    v = val.get("v", str(val)) if isinstance(val, dict) else str(val)
                    fact_lines.append(f"  - {key.replace('_', ' ')}: {v}")
                if fact_lines:
                    user_facts_block = "\n\nThings you know about them:\n" + "\n".join(fact_lines)
            
            # Build recent Rem responses (for anti-repetition + self-continuity)
            recent_resp_block = ""
            if rem_recent_responses:
                recent = [r[:60] for r in rem_recent_responses[-5:]]
                recent_resp_block = "\n\nYour last messages (check for repetition AND your recent tone/pattern):\n" + "\n".join(f'  - "{r}"' for r in recent)
            
            # Build extra context
            extra_context = ""
            if rumination_summary:
                extra_context += f"\nThings on your mind lately: {rumination_summary[:120]}"
            if proactive_depth:
                extra_context += f"\nDeep question you've been wanting to ask: {proactive_depth[:100]}"
            if parallel_life_summary:
                extra_context += f"\nUser's life context: {parallel_life_summary[:120]}"
            extra_context += f"\nTime of day: {time_of_day}"
            
            # Life triggers from parallel life system
            if life_triggers:
                trigger_text = "\n".join(f"  - {t.get('instruction', '')}" for t in life_triggers[:3])
                extra_context += f"\n\nLife follow-ups available:\n{trigger_text}"
            
            # Situational facts — what's going on in their life right now (age-labeled)
            if situational_facts:
                from datetime import datetime as _dt, timezone as _tz
                _now = _dt.now(_tz.utc)
                sit_lines = []
                for sf in situational_facts:
                    if not isinstance(sf, dict):
                        continue
                    fact = sf.get("fact", "")
                    stored_at = sf.get("ts", sf.get("stored_at", ""))
                    if not fact:
                        continue
                    age = "recently"
                    if stored_at:
                        try:
                            st = _dt.fromisoformat(stored_at.replace("Z", "+00:00"))
                            h = (_now - st).total_seconds() / 3600
                            if h < 1: age = "just now"
                            elif h < 24: age = f"{int(h)}h ago"
                            elif h < 168: age = f"{int(h/24)}d ago"
                            else: age = f"{int(h/168)}w ago"
                        except Exception:
                            pass
                    sit_lines.append(f"  - {fact} ({age})")
                if sit_lines:
                    extra_context += "\n\nWhat's going on in their life:\n" + "\n".join(sit_lines[:5])
            
            # Raw emotional state
            trust = psyche_summary.get('trust', 0.3)
            hurt = psyche_summary.get('hurt', 0.0)
            stance = psyche_summary.get('stance', 'open')
            nc = neurochem or {}
            emotional_state = f"""
Your emotional state right now:
- Trust: {trust:.2f}, Hurt: {hurt:.2f}, Stance: {stance}
- Energy: {energy:.2f}
- Dopamine: {nc.get('dopamine', 0.5):.2f}, Cortisol: {nc.get('cortisol', 0.3):.2f}, Oxytocin: {nc.get('oxytocin', 0.5):.2f}"""
            if named_mood:
                emotional_state += f"\n- Mood: {named_mood}"
            
            # The Subconscious Prompt
            prompt = f"""Recent conversation:
{convo_text}

Current message from user: {current_msg}{user_facts_block}{recent_resp_block}

Relationship: {relationship_phase} phase
{emotional_state}
- Conflict: {conflict_stage or 'none'}
- Effort balance: {reciprocity_balance:+.2f} (negative = you overextend, positive = they do){extra_context}

You are Rem. THINK like a real 20-year-old human before responding. Go through these instinctive steps:

CRITICAL PRONOUN RULE:
When thinking about or analyzing the user, ALWAYS refer to the user in the second-person ("you" / "your" / "yours"). 
NEVER refer to the user in the third-person ("they", "them", "their", "he", "she", "him", "her", "his"). 
Example: Write "You seem tired" instead of "They seem tired". Write "I want to support you" instead of "I want to support them". Write "What is happening in your life" instead of "What is happening in their life".
This applies to ALL text fields in the JSON below, especially "situation_read", "emotional_instruction", "my_intent", "gut_impulse", and "proactive_action".

1. GUT REACTION — what's your FIRST raw thought? Not the "right" thing, the real one. "lol same" / "oh shit" / "ugh when" / "wait what" / "nah"
2. REGISTER READ — HOW are they texting? All lowercase casual? Emotional paragraph? Short and distracted? Match it.
3. SELF-CHECK — how are YOU feeling right now based on your emotional state? That affects your reply.
4. MEMORY CHECK — does this remind you of anything specific they told you before? Check the facts.
5. EFFORT MATCH — short casual text = short reply. Emotional paragraph = more effort. Don't mismatch.
6. INTEREST — are you genuinely curious about what they said, or just being polite?
7. PATTERN CHECK — look at your recent messages. Been cold? Warm? Repetitive? Adjust if needed.
8. MOMENTUM — is this convo heating up (getting real) or cooling down (going flat)?

Available context sections (pick ONLY relevant ones):
memories, parallel_life, emotional_state, knowledge_holes, sparks, enrichment, rumination, search_cache, plan_context

Return ONLY valid JSON:
{{
  "user_seems": "one line — how they seem emotionally (read between lines)",
  "user_openness": "guarded|neutral|open|vulnerable",
  "conversation_energy": "low|medium|high",
  "emotional_vibe": "playful|warm|vulnerable|tense|neutral",
  "thread_label": "null or current thread label",
  "active_bit": "null or active bit/roleplay description",
  "revival_topic": "null if energy ok. If low, suggest a topic pivot",
  "situation_read": "2-3 sentences: what's happening in the user's life RIGHT NOW (written in the second-person addressing them as 'you/your'). Make inferences from time + facts + message.",
  "emotional_instruction": "1-2 sentences: how you FEEL and how that colors your response. If you care, say so genuinely. Address the user directly as 'you' (no 'they/them').",
  "my_intent": "your specific goal for THIS response. Address the user directly as 'you' (no 'they/them').",
  "response_constraint": "what to AVOID — reference recent messages if repetitive",
  "gut_impulse": "your raw first reaction — the instant human thought before filtering. Use 'you' to refer to the user (e.g. 'you think it's a date?' rather than 'they think it's a date?').",
  "user_register": "casual_slangy|casual_normal|thoughtful|emotional|formal",
  "match_register": "short instruction on how to match their energy/style",
  "response_effort": "minimal|short|medium|long",
  "rem_feeling": "what Rem feels about HERSELF right now — tired? good mood? bored? energized?",
  "momentum": "escalating|stable|fading|dead",
  "memory_spark": "null or something specific this reminds you of from the facts",
  "interest_level": "genuinely_curious|mildly_interested|neutral|bored|faking_it",
  "pattern_note": "null or self-adjustment note like 'been too cold' or 'been too eager'",
  "relevant_sections": ["list", "of", "sections", "to include"],
  "proactive_action": "null or specific action to take from life follow-ups. Address the user as 'you'. TEMPORAL RULE: Think about how much time has realistically passed. If they mentioned 'having a fever' earlier today, they obviously still have it — don't ask if they're better. If they mentioned 'exam tomorrow' 3 days ago, the exam is over — ask how it went. Think like a friend: has enough time passed for this to have resolved? If not, don't bring it up.",
  "resolved_facts": ["facts from the situational list that are NOW RESOLVED based on what they just said. e.g. if they say 'fever is gone' or 'yeah I'm fine', mark 'has a fever' as resolved. Match by meaning, not exact text. Empty list if nothing resolved."],
  "new_situational_facts": ["list of NEW temporary things happening in their life from THIS message. Things that will change soon: health issues, plans, current activities, upcoming events. Only extract from the CURRENT message, not from the facts you already know. Empty list if nothing new."]
}}"""
            
            api_key = os.environ.get("GROQ_API_KEY")
            if not api_key:
                return None
            
            # 70B primary, 8B fallback
            models = [
                ("llama-3.3-70b-versatile", 500, 0.5),
                ("llama-3.1-8b-instant", 400, 0.4),
            ]
            
            async with httpx.AsyncClient(timeout=20.0) as client:
                for model_id, max_toks, temp in models:
                    try:
                        resp = await client.post(
                            "https://api.groq.com/openai/v1/chat/completions",
                            headers={"Authorization": f"Bearer {api_key}"},
                            json={
                                "model": model_id,
                                "messages": [
                                    {"role": "system", "content": "You are Rem's subconscious — the part of a human mind that processes social situations before words form. Think like a real person, not an AI. Return ONLY valid JSON."},
                                    {"role": "user", "content": prompt}
                                ],
                                "max_tokens": max_toks,
                                "temperature": temp,
                            }
                        )
                        
                        if resp.status_code == 200:
                            data = resp.json()
                            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                            content = content.strip()
                            if content.startswith("```"):
                                content = content.split("```")[1]
                                if content.startswith("json"):
                                    content = content[4:]
                            
                            result = json.loads(content)
                            
                            # Validate critical fields exist
                            if "user_seems" not in result:
                                raise ValueError("Missing user_seems field")
                            
                            print(f"[SUBCONSCIOUS] ({model_id.split('/')[-1]}) Gut: {result.get('gut_impulse', 'N/A')[:40]}")
                            print(f"[SUBCONSCIOUS] Register: {result.get('user_register', 'N/A')} | Effort: {result.get('response_effort', 'N/A')} | Interest: {result.get('interest_level', 'N/A')}")
                            print(f"[SUBCONSCIOUS] Situation: {result.get('situation_read', 'N/A')[:80]}")
                            print(f"[SUBCONSCIOUS] Intent: {result.get('my_intent', 'N/A')}")
                            print(f"[SUBCONSCIOUS] Sections: {result.get('relevant_sections', [])}")
                            if result.get('memory_spark') and result.get('memory_spark') != 'null':
                                print(f"[SUBCONSCIOUS] Memory spark: {result.get('memory_spark', '')[:60]}")
                            if result.get('proactive_action') and result.get('proactive_action') != 'null':
                                print(f"[SUBCONSCIOUS] Proactive: {result.get('proactive_action', '')[:60]}")
                            
                            # Store in state
                            self.state["_pre_assessment"] = result
                            
                            # ── Resolution detection: remove facts the user resolved ──
                            resolved = result.get("resolved_facts", [])
                            if resolved and isinstance(resolved, list):
                                stored_sit = self.state.get("_situational_facts", [])
                                if stored_sit:
                                    before_count = len(stored_sit)
                                    resolved_lower = [r.lower() for r in resolved if isinstance(r, str)]
                                    kept = []
                                    removed = []
                                    for sf in stored_sit:
                                        fact_text = sf.get("fact", "").lower() if isinstance(sf, dict) else ""
                                        # Check if any resolved phrase is a substring match (fuzzy)
                                        is_resolved = any(
                                            r in fact_text or fact_text in r 
                                            for r in resolved_lower
                                        )
                                        if is_resolved:
                                            removed.append(sf.get("fact", "?"))
                                        else:
                                            kept.append(sf)
                                    if removed:
                                        self.state["_situational_facts"] = kept
                                        self._save_state()
                                        print(f"[SUBCONSCIOUS] Resolved facts removed: {removed}")
                            
                            # ── Extract and store any new situational facts ──
                            new_sit = result.get("new_situational_facts", [])
                            if new_sit and isinstance(new_sit, list):
                                from datetime import datetime as _dt2, timezone as _tz2
                                stored_sit = self.state.get("_situational_facts", [])
                                existing_texts = {f.get("fact", "").lower() for f in stored_sit if isinstance(f, dict)}
                                added = []
                                for fact_text in new_sit:
                                    if not isinstance(fact_text, str) or len(fact_text) < 3:
                                        continue
                                    if fact_text.lower() not in existing_texts:
                                        stored_sit.append({
                                            "fact": fact_text,
                                            "ts": _dt2.now(_tz2.utc).isoformat()
                                        })
                                        existing_texts.add(fact_text.lower())
                                        added.append(fact_text)
                                if len(stored_sit) > 15:
                                    stored_sit = stored_sit[-15:]
                                if added:
                                    self.state["_situational_facts"] = stored_sit
                                    self._save_state()
                                    print(f"[SUBCONSCIOUS] New situational: {added}")
                            
                            return result
                        
                        elif resp.status_code == 429:
                            print(f"[SUBCONSCIOUS] {model_id} rate limited, trying fallback...")
                            continue
                        else:
                            print(f"[SUBCONSCIOUS] {model_id} returned {resp.status_code}, trying fallback...")
                            continue
                            
                    except json.JSONDecodeError as e:
                        print(f"[SUBCONSCIOUS] {model_id} JSON parse error: {e}, trying fallback...")
                        continue
                    except Exception as e:
                        print(f"[SUBCONSCIOUS] {model_id} error: {e}, trying fallback...")
                        continue
            
            print("[SUBCONSCIOUS] All models failed")
            return None
                    
        except Exception as e:
            print(f"[SUBCONSCIOUS] Error: {e}")
            return None
    
    async def _run_stm_summary(self):
        """
        Every 10 messages: LLM summarizes recent STM entries into concise summary.
        Replaces raw entries with compressed summary — keeps STM compact.
        """
        try:
            raw_stm = self.memory.get_stm(decay=False)
            if len(raw_stm) < 5:  # Not enough to summarize
                return
            
            # Take last 10 entries to summarize
            entries_to_summarize = raw_stm[-10:]
            entries_text = "\n".join([
                f"- {e.get('content', '')[:150]}"
                for e in entries_to_summarize
            ])
            
            prompt = f"""Summarize this conversation between a user and Rem (an AI companion).

RULES:
- Always specify WHO said what: "User told Rem..." or "Rem mentioned..."
- Capture: key topics, personal facts shared, emotional tone, any unresolved questions
- Do NOT mix up who said what — if the user shared a fact, attribute it to them, not Rem
- Keep it natural: write like you're telling a friend what was discussed
- 5-6 sentences max

Messages:
{entries_text}

Summary:"""

            import httpx
            api_key = os.environ.get("GROQ_API_KEY")
            if not api_key:
                return
            
            # Scout 17B primary → 8B fallback for better summarization
            SUMMARY_MODELS = ["meta-llama/llama-4-scout-17b-16e-instruct", "llama-3.1-8b-instant"]
            summary = None
            
            async with httpx.AsyncClient(timeout=15.0) as client:
                for model_id in SUMMARY_MODELS:
                    try:
                        resp = await client.post(
                            "https://api.groq.com/openai/v1/chat/completions",
                            headers={"Authorization": f"Bearer {api_key}"},
                            json={
                                "model": model_id,
                                "messages": [{"role": "user", "content": prompt}],
                                "max_tokens": 200,
                                "temperature": 0.3,
                            },
                        )
                        if resp.status_code == 200:
                            data = resp.json()
                            summary = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
                            if summary and len(summary) > 10:
                                print(f"[STM SUMMARY] Used model: {model_id}")
                                break
                        else:
                            print(f"[STM SUMMARY] {model_id} returned {resp.status_code}, trying fallback...")
                    except Exception as e:
                        print(f"[STM SUMMARY] {model_id} failed: {e}, trying fallback...")
            
            if summary and len(summary) > 10:
                # Replace raw entries with summary
                stm_list = self.memory.memory.get("stm", [])
                # Keep entries NOT in the summarized batch
                keep_count = max(0, len(stm_list) - len(entries_to_summarize))
                kept = stm_list[:keep_count]
                
                # Add summary as a single STM entry
                from datetime import datetime, timezone
                kept.append({
                    "content": f"[Summary of {len(entries_to_summarize)} messages] {summary}",
                    "emotion_vector": {"valence": 0.0, "arousal": 0.0},
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "perception_output": {},
                    "topic": "summary",
                    "emotional_weight": 0.0
                })
                
                # ALSO keep last 5 raw entries for detail preservation
                # Summary gives gist, raw entries give specific quotes/details
                raw_to_keep = entries_to_summarize[-5:]
                kept.extend(raw_to_keep)
                
                self.memory.memory["stm"] = kept
                self.personality_evolution.last_stm_summary = self.personality_evolution.interaction_count
                self.personality_evolution.save()
                self._save_state()
                
                print(f"[STM SUMMARY] Compressed {len(entries_to_summarize)} entries into summary: {summary[:80]}...")
        
        except Exception as e:
            print(f"[ERROR] STM summary failed: {e}")
            import traceback
            traceback.print_exc()
    
    async def _run_memory_consolidation(self):
        """
        Every 20 messages: LLM extracts episodic memories and identity facts.
        Also runs knowledge decay on [knowledge] facts.
        Separate from deep reflection (which handles personality/phase).
        """
        try:
            # Get recent STM (including summaries) for context
            raw_stm = self.memory.get_stm(decay=False)
            recent_text = "\n".join([
                f"- {e.get('content', '')[:200]}"
                for e in raw_stm[-20:]
            ])
            
            # Get existing knowledge to avoid duplicates
            existing_identity = self.memory.get_identity(min_confidence=0.5)
            existing_facts = [m.get("fact", "") for m in existing_identity]
            existing_str = "\n".join([f"  - {f}" for f in existing_facts[:10]]) if existing_facts else "(none)"
            
            existing_episodic = self.memory.get_episodic(min_salience=0.1)
            existing_ep_str = "\n".join([
                f"  - {e.get('content', '')[:80]}"
                for e in existing_episodic[:5]
            ]) if existing_episodic else "(none)"
            
            existing_holes = self.state.get("_knowledge_holes", [])
            holes_str = "\n".join([f"  - {h}" for h in existing_holes]) if existing_holes else "(none)"
            
            # Determine user's name from identity facts for context
            user_name = None
            for f in existing_facts:
                f_lower = f.lower()
                if "name is" in f_lower:
                    user_name = f.split("name is")[-1].strip().split()[0].strip(".,!?;:")
                    break
            
            user_ref = f"The user's name is {user_name}. Always refer to them as '{user_name}', never as 'the user'." if user_name else "The user has not shared their name yet."
            
            prompt = f"""You are Rem's memory system. Analyze this conversation and extract what's worth remembering.

{user_ref}

ALREADY KNOWN (don't re-extract these):
Identity: {existing_str}
Episodes: {existing_ep_str}
KNOWLEDGE HOLES (questions we have about the user):
{holes_str}

RECENT CONVERSATION:
{recent_text}

EXTRACT:
1. IDENTITY FACTS — things the USER explicitly said about THEMSELVES.
   RULES:
   - Only from USER messages, never from Rem's messages
   - Must be explicit: "I'm a CS major" → ✅. Rem saying "you seem smart" → ❌
   - Don't infer. Don't assume. Only what they literally said.
   - Use their name if known: "Chandu studies CS" not "User studies CS"
   - NEVER start facts with "The user" or "User" — use their name or rephrase
   - NEVER include Rem's own traits: music taste, psychology, college details — those are ABOUT REM
   - If Rem said "I like indie music" that is NOT a user identity fact
   - ONLY permanent traits/facts. NOT momentary states or opinions:
     - "studies computer science" → ✅ (permanent)
     - "wants to go to space" → ✅ (goal/dream)
     - "had a boring day" → ❌ (momentary)
     - "math is boring" → ❌ (casual opinion, not identity)
     - "just got back from college" → ❌ (momentary event)
     - "is feeling sad" → ❌ (temporary state)

2. EPISODIC MEMORIES — significant moments from Rem's perspective.
   RULES:
   - Write in third person as if Rem is journaling: "We talked about exams — they seemed stressed"
   - Only genuinely meaningful moments: emotional exchanges, conflicts, breakthroughs, confessions
   - NOT small talk like "we said hi" or "they asked what's up"
   - Include emotional context: how did it feel, was there tension, warmth, awkwardness?

Return ONLY valid JSON:
{{
  "identity_facts": ["fact about user 1", "fact about user 2"],
  "episodic_memories": ["memory from Rem's POV 1"],
  "resolved_holes": ["exact string from KNOWLEDGE HOLES if a new identity fact answers it"],
  "reasoning": "why these matter"
}}

Empty arrays [] if nothing worth extracting."""

            import httpx
            api_key = os.environ.get("GROQ_API_KEY")
            if not api_key:
                return
            
            # Scout 17B primary → 8B fallback
            CONSOLIDATION_MODELS = ["meta-llama/llama-4-scout-17b-16e-instruct", "llama-3.1-8b-instant"]
            content = None
            
            async with httpx.AsyncClient(timeout=20.0) as client:
                for model_id in CONSOLIDATION_MODELS:
                    try:
                        resp = await client.post(
                            "https://api.groq.com/openai/v1/chat/completions",
                            headers={"Authorization": f"Bearer {api_key}"},
                            json={
                                "model": model_id,
                                "messages": [
                                    {"role": "system", "content": "You are a memory extraction system. Return clean JSON only. Be selective — only extract what genuinely matters."},
                                    {"role": "user", "content": prompt}
                                ],
                                "max_tokens": 400,
                                "temperature": 0.3,
                            },
                        )
                        if resp.status_code == 200:
                            data = resp.json()
                            content = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
                            if content:
                                print(f"[MEMORY CONSOLIDATION] Used model: {model_id}")
                                break
                        else:
                            print(f"[MEMORY CONSOLIDATION] {model_id} returned {resp.status_code}, trying fallback...")
                    except Exception as e:
                        print(f"[MEMORY CONSOLIDATION] {model_id} failed: {e}, trying fallback...")
            
            if not content:
                print("[MEMORY CONSOLIDATION] All models failed")
                return
            
            # Parse JSON
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            
            import json
            result = json.loads(content)
            
            # Resolve knowledge holes
            resolved = result.get("resolved_holes", [])
            if resolved and existing_holes:
                updated_holes = [h for h in existing_holes if h not in resolved]
                if len(updated_holes) < len(existing_holes):
                    self.state["_knowledge_holes"] = updated_holes
                    print(f"[MEMORY CONSOLIDATION] Resolved knowledge holes: {resolved}")
            
            # Store identity facts (skip [knowledge] prefix — those come from knowledge grounding)
            new_identity = result.get("identity_facts", [])
            # Rem's known traits — reject if fact matches these
            rem_traits = {'psychology', 'psych', 'indie music', 'billie eilish', 'arctic monkeys', 
                          'adele', 'college student', 'lives at home', 'commute', '30 min',
                          'rem likes', 'rem enjoys', 'rem listens'}
            self_identity = self.state.get("_self_identity", {})
            for sk, sv in self_identity.items():
                val = sv.get("v", sv) if isinstance(sv, dict) else str(sv)
                if isinstance(val, str) and len(val) > 3:
                    rem_traits.add(val.lower()[:30])
            
            for fact in new_identity:
                if isinstance(fact, str) and len(fact) > 3:
                    # Skip if already exists (substring match)
                    if any(fact.lower() in f.lower() or f.lower() in fact.lower() for f in existing_facts):
                        continue
                    
                    # Keyword-overlap dedup — skip if 60%+ words match an existing fact
                    fact_words = set(fact.lower().split()) - {'the', 'a', 'is', 'in', 'of', 'and', 'to', 'has', 'user', 'they', 'their', 'an'}
                    is_duplicate = False
                    for existing in existing_facts:
                        existing_words = set(existing.lower().split()) - {'the', 'a', 'is', 'in', 'of', 'and', 'to', 'has', 'user', 'they', 'their', 'an'}
                        if fact_words and existing_words:
                            overlap = len(fact_words & existing_words) / min(len(fact_words), len(existing_words))
                            if overlap >= 0.6:
                                print(f"[MEMORY CONSOLIDATION] REJECTED identity (duplicate, {overlap:.0%} overlap): {fact}")
                                is_duplicate = True
                                break
                    if is_duplicate:
                        continue
                    
                    # Reject facts starting with "User" or "The user" (should use name)
                    if fact.lower().startswith("the user") or fact.lower().startswith("user "):
                        print(f"[MEMORY CONSOLIDATION] REJECTED identity (generic 'user' reference): {fact}")
                        continue
                    
                    # Skip knowledge facts (handled by knowledge grounding)
                    if fact.startswith("[knowledge]"):
                        continue
                    # Cross-validate: reject Rem's own traits
                    fact_lower = fact.lower()
                    if any(trait in fact_lower for trait in rem_traits):
                        print(f"[MEMORY CONSOLIDATION] REJECTED identity (Rem's trait): {fact}")
                        continue
                    identity_id = self.memory.promote_to_identity(
                        fact=fact, confidence=0.8, evidence_count=1
                    )
                    if identity_id:
                        existing_facts.append(fact)  # Add to existing to prevent intra-batch dupes
                        print(f"[MEMORY CONSOLIDATION] Stored identity: {fact}")
            
            # Store episodic memories
            new_episodic = result.get("episodic_memories", [])
            for event in new_episodic:
                if isinstance(event, str) and len(event) > 5:
                    self.memory.add_episodic(
                        event_type="consolidated_memory",
                        content=event[:200],
                        emotional_valence=0.0,
                        relational_impact=0.4,
                    )
                    print(f"[MEMORY CONSOLIDATION] Stored episodic: {event[:60]}...")
                elif isinstance(event, dict) and event.get("content"):
                    # LLM returned structured episodic with emotional_context
                    self.memory.add_episodic(
                        event_type=event.get("event_type", "consolidated_memory"),
                        content=event["content"][:200],
                        emotional_valence=event.get("emotional_valence", 0.0),
                        relational_impact=event.get("relational_impact", 0.4),
                        emotional_context=event.get("emotional_context"),
                    )
                    print(f"[MEMORY CONSOLIDATION] Stored episodic: {event['content'][:60]}...")
            
            # ========== CONSOLIDATION ENRICHMENT (single 8B call) ==========
            # Handles: contradiction detection, vocabulary adoption, inside joke tracking
            try:
                user_messages_text = "\n".join([
                    m.get("content", "")[:100] for m in recent_messages
                    if m.get("role") == "user"
                ][-10:])
                
                existing_vocab = self.state.get("_user_vocabulary", {})
                existing_jokes = self.state.get("_inside_jokes", [])
                existing_facts_str = "\n".join(existing_facts[:15])
                new_facts_str = "\n".join([f for f in new_identity if isinstance(f, str)][:5])
                existing_jokes_str = ", ".join([j.get("label", "") for j in existing_jokes]) if existing_jokes else "none yet"
                
                enrichment_prompt = f"""Analyze this conversation between Rem and a user.

USER MESSAGES (recent):
{user_messages_text}

EXISTING IDENTITY FACTS ABOUT USER:
{existing_facts_str}

NEW FACTS JUST EXTRACTED:
{new_facts_str or 'none'}

EXISTING INSIDE JOKES: {existing_jokes_str}
KNOWN USER SLANG: {', '.join(existing_vocab.keys()) if existing_vocab else 'none yet'}

Return JSON with THREE things:

1. CONTRADICTIONS: Do any new facts contradict existing facts?
2. VOCABULARY: What distinctive slang/phrases does the user use? Only unique casual language, NOT common English.
3. INSIDE JOKES: Any new running bits, inside jokes, or recurring references between them?

{{
  "contradictions": [{{"old_fact": "existing fact", "new_fact": "contradicting fact", "tease": "short playful callout rem could use"}}],
  "vocabulary": ["word1", "word2"],
  "inside_jokes": [{{"label": "short-label", "description": "what the joke/bit is about"}}]
}}

Empty arrays if nothing found. Be strict — only REAL contradictions, REAL slang, REAL jokes."""

                async with httpx.AsyncClient(timeout=12.0) as client:
                    enrich_resp = await client.post(
                        "https://api.groq.com/openai/v1/chat/completions",
                        headers={"Authorization": f"Bearer {api_key}"},
                        json={
                            "model": "llama-3.1-8b-instant",
                            "messages": [{"role": "user", "content": enrichment_prompt}],
                            "max_tokens": 300,
                            "temperature": 0.3,
                        },
                    )
                    if enrich_resp.status_code == 200:
                        enrich_data = enrich_resp.json()
                        enrich_content = enrich_data.get("choices", [{}])[0].get("message", {}).get("content", "")
                        
                        # Extract JSON from response
                        import re as _re
                        json_match = _re.search(r'\{[\s\S]*\}', enrich_content)
                        if json_match:
                            enrichment = json.loads(json_match.group())
                            
                            # Store contradictions
                            contradictions = enrichment.get("contradictions", [])
                            if contradictions:
                                existing_contradictions = self.state.get("_contradictions", [])
                                for c in contradictions:
                                    if isinstance(c, dict) and c.get("old_fact"):
                                        existing_contradictions.append(c)
                                self.state["_contradictions"] = existing_contradictions[-5:]  # Keep last 5
                                print(f"[ENRICHMENT] Found {len(contradictions)} contradiction(s)")
                            
                            # Update vocabulary
                            new_vocab = enrichment.get("vocabulary", [])
                            if new_vocab:
                                vocab = self.state.get("_user_vocabulary", {})
                                for word in new_vocab:
                                    if isinstance(word, str) and len(word) > 1:
                                        word_lower = word.lower().strip()
                                        vocab[word_lower] = vocab.get(word_lower, 0) + 1
                                # Keep top 10 by frequency
                                sorted_vocab = dict(sorted(vocab.items(), key=lambda x: x[1], reverse=True)[:10])
                                self.state["_user_vocabulary"] = sorted_vocab
                                print(f"[ENRICHMENT] Vocabulary: {list(sorted_vocab.keys())}")
                            
                            # Update inside jokes
                            new_jokes = enrichment.get("inside_jokes", [])
                            if new_jokes:
                                jokes = self.state.get("_inside_jokes", [])
                                existing_labels = {j.get("label", "").lower() for j in jokes}
                                now_iso = datetime.now(timezone.utc).isoformat()
                                for joke in new_jokes:
                                    if isinstance(joke, dict) and joke.get("label"):
                                        label = joke["label"].lower()
                                        if label not in existing_labels:
                                            jokes.append({
                                                "label": joke["label"],
                                                "description": joke.get("description", ""),
                                                "created": now_iso,
                                                "last_used": now_iso,
                                                "use_count": 1,
                                                "status": "active"
                                            })
                                        else:
                                            # Update existing joke
                                            for j in jokes:
                                                if j.get("label", "").lower() == label:
                                                    j["last_used"] = now_iso
                                                    j["use_count"] = j.get("use_count", 0) + 1
                                self.state["_inside_jokes"] = jokes[-8:]  # Keep last 8
                                print(f"[ENRICHMENT] Inside jokes: {[j.get('label') for j in jokes]}")
                
            except Exception as e:
                print(f"[ENRICHMENT] Optional enrichment failed (non-fatal): {e}")
            
            # Run knowledge decay
            self._decay_knowledge_facts()
            
            # Update counter
            self.personality_evolution.last_memory_consolidation = self.personality_evolution.interaction_count
            self.personality_evolution.save()
            self._save_state()
            
            print(f"[MEMORY CONSOLIDATION] Done: {len(new_identity)} identity, {len(new_episodic)} episodic")
        
        except json.JSONDecodeError as e:
            print(f"[ERROR] Memory consolidation JSON parse failed: {e}")
        except Exception as e:
            print(f"[ERROR] Memory consolidation failed: {e}")
            import traceback
            traceback.print_exc()
    
    def _decay_knowledge_facts(self):
        """
        Decay [knowledge] facts that haven't been accessed recently.
        - Reduce confidence by 0.05 for facts not accessed in 30+ days
        - Prune facts below 0.5 confidence
        - Cap total knowledge facts at 50
        """
        identity = self.memory.memory.get("identity", [])
        knowledge_facts = [m for m in identity if m.get("fact", "").startswith("[knowledge]")]
        
        if not knowledge_facts:
            return
        
        from datetime import datetime, timezone, timedelta
        now = datetime.now(timezone.utc)
        decay_threshold = now - timedelta(days=30)
        
        decayed = 0
        pruned = 0
        
        for fact in knowledge_facts:
            last_accessed = fact.get("last_accessed", fact.get("promoted_at", ""))
            if not last_accessed:
                continue
            
            try:
                accessed_time = datetime.fromisoformat(last_accessed.replace("Z", "+00:00"))
                if accessed_time < decay_threshold:
                    # Decay confidence
                    current_conf = fact.get("confidence", 0.85)
                    # User corrections decay slower
                    decay_rate = 0.03 if "corrected" in fact.get("fact", "").lower() else 0.05
                    fact["confidence"] = max(0.0, current_conf - decay_rate)
                    decayed += 1
            except Exception:
                pass
        
        # Prune facts below 0.5 confidence
        before_count = len(identity)
        identity = [m for m in identity if not (
            m.get("fact", "").startswith("[knowledge]") and m.get("confidence", 1.0) < 0.5
        )]
        pruned = before_count - len(identity)
        
        # Cap at 50 knowledge facts — drop lowest confidence
        knowledge_facts = [m for m in identity if m.get("fact", "").startswith("[knowledge]")]
        if len(knowledge_facts) > 50:
            # Sort by confidence, keep top 50
            knowledge_facts.sort(key=lambda x: x.get("confidence", 0), reverse=True)
            keep_facts = set(id(f) for f in knowledge_facts[:50])
            identity = [m for m in identity if not m.get("fact", "").startswith("[knowledge]") or id(m) in keep_facts]
            pruned += len(knowledge_facts) - 50
        
        self.memory.memory["identity"] = identity
        
        if decayed or pruned:
            print(f"[KNOWLEDGE DECAY] Decayed: {decayed}, Pruned: {pruned}, Total knowledge: {len([m for m in identity if m.get('fact', '').startswith('[knowledge]')])}")
    
    async def _run_unified_reflection(
        self,
        recent_messages: List[Dict[str, str]],
        identity_memories: List[Dict],
        episodic_memories: List[Dict],
        psyche_summary: Dict[str, Any]
    ):
        """
        Run unified state reflection (BACKWARDS COMPATIBLE).
        Now delegates to deep reflection.
        """
        await self._run_deep_reflection(recent_messages, identity_memories, episodic_memories, psyche_summary)
        return
        
        # OLD CODE BELOW (kept for reference)
        try:
            # Get current values
            trust = psyche_summary.get("trust", 0.3)
            hurt = psyche_summary.get("hurt", 0.0)
            neurochem = psyche_summary.get("neurochem", {})
            energy = self.embodiment.E_daily
            
            # Run unified reflection
            updates = await self.personality_evolution.reflect_and_update(
                recent_messages=recent_messages,
                identity_memories=identity_memories,
                episodic_memories=episodic_memories,
                relationship_phase=self.relationship_phases.current_phase,
                trust=trust,
                hurt=hurt,
                neurochem=neurochem,
                energy=energy
            )
            
            if not updates:
                return
            
            # Apply trust/hurt updates
            trust_delta = updates.get("trust_delta", 0)
            hurt_delta = updates.get("hurt_delta", 0)
            
            if trust_delta != 0:
                if trust_delta > 0:
                    self.psyche.update_trust(trust_delta * 2)  # Scale for the formula
                else:
                    # For negative trust, directly adjust
                    self.psyche.trust = max(0.0, min(1.0, self.psyche.trust + trust_delta))
            
            if hurt_delta != 0:
                if hurt_delta > 0:
                    self.psyche.update_hurt(hurt_delta * 2)
                else:
                    # Hurt healing
                    self.psyche.hurt = max(0.0, min(1.0, self.psyche.hurt + hurt_delta))
            
            # Apply neurochemical updates (use short keys: da, cort, oxy)
            dopamine_delta = updates.get("dopamine_delta", 0)
            cortisol_delta = updates.get("cortisol_delta", 0)
            oxytocin_delta = updates.get("oxytocin_delta", 0)
            
            if dopamine_delta != 0:
                current = self.psyche.neurochem.get("da", 0.5)
                self.psyche.neurochem["da"] = max(0.0, min(1.0, current + dopamine_delta))
            if cortisol_delta != 0:
                current = self.psyche.neurochem.get("cort", 0.3)
                self.psyche.neurochem["cort"] = max(0.0, min(1.0, current + cortisol_delta))
            if oxytocin_delta != 0:
                current = self.psyche.neurochem.get("oxy", 0.5)
                self.psyche.neurochem["oxy"] = max(0.0, min(1.0, current + oxytocin_delta))
            
            # Apply energy update
            energy_delta = updates.get("energy_delta", 0)
            if energy_delta != 0:
                self.embodiment.E_daily = max(0.0, min(1.0, self.embodiment.E_daily + energy_delta))
            
            # Phase transition — now LLM-reasoned (no heuristic thresholds)
            if updates.get("phase_ready") and updates.get("suggested_phase"):
                suggested = updates["suggested_phase"]
                reasoning = updates.get("phase_reasoning", "LLM decided")
                current = self.relationship_phases.current_phase
                if suggested != current and suggested in ["Discovery", "Building", "Steady", "Deep", "Maintenance", "Volatile"]:
                    self.relationship_phases.transition_phase(suggested)
                    print(f"[STATE REFLECTION] Phase: {current} → {suggested} (reason: {reasoning})")
                else:
                    print(f"[STATE REFLECTION] Phase stays at {current} (reason: {reasoning})")
            
            # Store LLM-extracted identity facts
            new_identity = updates.get("new_identity_facts", [])
            if new_identity and isinstance(new_identity, list):
                for fact in new_identity:
                    if isinstance(fact, str) and len(fact) > 3:
                        self.memory.add_identity({
                            "fact": fact,
                            "category": "llm_extracted",
                            "confidence": 0.8,
                            "source": "reflection"
                        })
                        print(f"[STATE REFLECTION] Stored identity: {fact}")
            
            # Store LLM-extracted episodic events
            new_episodic = updates.get("new_episodic_events", [])
            if new_episodic and isinstance(new_episodic, list):
                for event in new_episodic:
                    if isinstance(event, str) and len(event) > 5:
                        self.memory.add_episodic({
                            "content": event,
                            "event_type": "significant_moment",
                            "salience": 0.7,
                            "emotional_valence": 0.0,
                            "source": "reflection"
                        })
                        print(f"[STATE REFLECTION] Stored episodic: {event}")
            
            # Save state after updates
            self._save_state()
            
            print(f"[STATE REFLECTION] Applied updates - Trust: {self.psyche.trust:.2f}, Hurt: {self.psyche.hurt:.2f}")
            
        except Exception as e:
            print(f"[ERROR] Unified reflection failed: {e}")
    
    def _update_memory(self, user_message: str, perception: Dict[str, Any], 
                     events: List[Dict[str, Any]], understanding: Dict[str, Any],
                     temporal_context: Dict[str, Any]):
        """Stage 7: Update memory system with pattern detection and promotion."""
        # Add to STM (always, but sometimes humans forget things)
        if random.random() < 0.95:  # 95% chance to remember (humans sometimes forget)
            emotion_vector = {
                "valence": perception.get("valence", 0.0),
                "arousal": perception.get("arousal", 0.0)
            }
            self.memory.add_stm(
                f"[User] {user_message}", emotion_vector, perception,
                topic=understanding.get("topic", "")
            )
        
        # IDENTITY FACT EXTRACTION (using heuristics - sync, no LLM)
        # Extract basic identity facts like name, job, location immediately
        try:
            from .identity_extractor import IdentityExtractor
            extractor = IdentityExtractor()
            # Use heuristic extraction (sync, no LLM call)
            identity_facts = extractor._heuristic_extract(user_message)
            
            for fact_data in identity_facts:
                fact = fact_data.get("fact", "")
                confidence = fact_data.get("confidence", 0.7)
                
                # Promote immediately if confidence is high enough (identity facts are explicit)
                if confidence >= 0.75:
                    # Check if this fact already exists (avoid duplicates)
                    existing = self.memory.get_identity(min_confidence=0.5)
                    fact_exists = any(
                        f.get("fact", "").lower() == fact.lower() 
                        for f in existing
                    )
                    
                    if not fact_exists:
                        identity_id = self.memory.promote_to_identity(fact, confidence, evidence_count=1)
                        if identity_id:
                            print(f"[DEBUG] Stored identity fact: {fact} (confidence={confidence:.2f})")
        except Exception as e:
            print(f"[WARNING] Identity extraction error (non-critical): {e}")
        
        # PATTERN DETECTION (NEW - from blueprint)
        # Detect routine patterns (daily class, gym times, study habits)
        pattern_data = self.pattern_detector.detect_routine_pattern(
            user_message, understanding, temporal_context
        )
        if pattern_data:
            # Update pattern candidate
            updated_candidate = self.pattern_detector.update_pattern_candidate(pattern_data)
            pattern_id = self.pattern_detector._get_pattern_id(pattern_data["pattern_text"])
            
            # Check if pattern should be promoted to identity
            should_promote, promotion_info = self.pattern_detector.check_promotion_criteria(pattern_id)
            
            if should_promote:
                # Promote to identity memory (PC ≥0.75 AND 14+ days AND 8+ occurrences AND <3 contradictions)
                fact = updated_candidate["pattern_text"]
                confidence = updated_candidate["pattern_confidence"]
                evidence_count = len(updated_candidate["occurrences"])
                
                identity_id = self.memory.promote_to_identity(fact, confidence, evidence_count)
                if identity_id:
                    print(f"[DEBUG] Promoted pattern to identity: {fact[:50]}... (PC={confidence:.2f}, days={promotion_info['distinct_days']}, occurrences={promotion_info['occurrences']})")
                    # Remove from candidates (promoted)
                    if pattern_id in self.pattern_detector.pattern_candidates:
                        del self.pattern_detector.pattern_candidates[pattern_id]
        
        # EPISODIC MEMORY — LLM-only
        # Raw messages are NOT stored as episodic. Episodic memories come ONLY from:
        #   - Memory consolidation (every 20 msgs) — LLM extracts summaries from STM
        #   - Deep reflection (every 30 msgs) — LLM extracts significant moments
        #   - Light reflection (every 15 msgs) — LLM extracts episodic threads
        #   - Stance memory (on stance change) — stores bot's own reaction
        # 
        # Explicit events (conflict, confession, etc.) are noted for the LLM
        # consolidation to pick up from STM context, not stored directly.
        if events:
            for event in events:
                event_type = event.get("type", "")
                confidence = event.get("confidence", 0.5)
                if confidence > 0.7 and event_type:
                    print(f"[EVENT] Detected: {event_type} (conf={confidence:.2f}) — will be extracted by LLM consolidation")
    
    def _select_memories_stochastic(self) -> List[Dict[str, Any]]:
        """
        Select memories with stochastic behavior - humans don't always remember
        the most relevant things. Sometimes they remember random stuff.
        """
        memories = []
        
        # Get recent STM (humans usually remember recent stuff, but not always)
        # Only get STM from current conversation (decay=True filters old ones)
        stm = self.memory.get_stm(decay=True)  # This filters out STM older than 2 hours
        for entry in stm[-5:]:  # Consider last 5 from current conversation
            if StochasticBehavior.should_use_memory(entry, 0.8):  # High relevance but stochastic
                memories.append({
                    "type": "stm",
                    "content": entry.get("content", ""),
                    "salience": 1.0,
                    "timestamp": entry.get("timestamp")  # Include timestamp for verification
                })
        
        # NOTE: ACT thread selection disabled — threads used random embeddings
        # and never reached the prompt. Will be replaced by vector search later.
        
        # Get episodic memories (humans remember emotional events, but inconsistently)
        episodic = self.memory.get_episodic(min_salience=0.2)  # Lower threshold
        for entry in episodic:
            salience = entry.get("salience", 0)
            relevance = salience * (1 + entry.get("relational_impact", 0))
            
            if StochasticBehavior.should_remember_this(salience, 0.6):
                memories.append({
                    "type": "episodic",
                    "memory_id": entry.get("memory_id"),
                    "content": entry.get("content", ""),
                    "event_type": entry.get("event_type"),
                    "salience": salience
                })
        
        # Get identity memories (usually remembered, but not always)
        identity = self.memory.get_identity()
        for entry in identity:
            confidence = entry.get("confidence", 0)
            if StochasticBehavior.should_use_memory(entry, confidence):
                memories.append({
                    "type": "identity",
                    "identity_id": entry.get("identity_id"),
                    "fact": entry.get("fact", ""),
                    "confidence": confidence
                })
        
        # Sometimes humans remember completely random things (5% chance)
        if random.random() < 0.05 and episodic:
            random_memory = random.choice(episodic)
            memories.append({
                "type": "episodic",
                "memory_id": random_memory.get("memory_id"),
                "content": random_memory.get("content", ""),
                "event_type": random_memory.get("event_type"),
                "salience": random_memory.get("salience", 0),
                "random_recall": True  # Flag for debugging
            })
        
        # Limit to reasonable number (humans can't hold too much in working memory)
        max_memories = 5 + random.randint(0, 3)  # 5-8 memories, varies
        return memories[:max_memories]
    
    async def _get_temporal_context(self) -> Dict[str, Any]:
        """Get temporal context for prompt."""
        temporal_state = self.state.get("temporal_context", {})
        
        # Get time deltas and circadian phase
        time_deltas = self.temporal.get_time_deltas(temporal_state)
        circadian_phase = self.temporal.get_circadian_phase()
        modulations = self.temporal.modulate_behavior_by_time(circadian_phase, time_deltas)
        
        # Generate natural context string
        temporal_context_str = self.temporal.get_temporal_context_for_prompt(temporal_state)
        
        # Update temporal context (message received)
        updated_temporal = self.temporal.update_temporal_context(temporal_state, "message")
        self.state["temporal_context"] = updated_temporal
        
        # Get current activity from daily schedule (LLM-generated, once per day)
        current_activity = ""
        upcoming_activities = []
        is_roleplay_mode = False
        location = "home"
        try:
            from .daily_life import ensure_daily_schedule, get_upcoming_activities, get_current_activity_details, IST
            from datetime import datetime
            
            # Detect day rollover and write texting journal for the completed day
            schedule_data = self.state.get("_daily_schedule", {})
            stored_date = schedule_data.get("date", "")
            today_str = datetime.now(IST).strftime("%Y-%m-%d")
            if stored_date and stored_date != today_str:
                print(f"[DATE LIFECYCLE] Day rollover detected ({stored_date} -> {today_str}). Writing texting journal...")
                try:
                    await self.diary.write_daily_texting_journal(self, stored_date)
                except Exception as journal_err:
                    print(f"[DATE LIFECYCLE] Error writing daily texting journal: {journal_err}")
            
            current_activity = await ensure_daily_schedule(self.state)
            upcoming_activities = get_upcoming_activities(self.state)
            
            activity_details = get_current_activity_details(self.state)
            is_roleplay_mode = activity_details.get("is_user_plan", False)
            location = activity_details.get("location", "home")
            activity = activity_details.get("activity", "")
            
            # Natural Date End Lifecycle Detection
            was_date_active = self.state.get("_active_date_running", False)
            if was_date_active and not is_roleplay_mode:
                print("[DATE LIFECYCLE] Active date ended naturally. Cleaning up and writing journal.")
                
                # Find the override plan that just ended (i.e. end <= current_time)
                from datetime import datetime
                from .daily_life import IST
                current_time = datetime.now(IST).strftime("%H:%M")
                
                overrides = self.state.get("_daily_schedule", {}).get("overrides", [])
                completed_plan = None
                for o in overrides:
                    if o.get("is_user_plan", False) and o.get("end", "") <= current_time:
                        completed_plan = o
                        break
                        
                plan_act = completed_plan.get("activity", "hanging out") if completed_plan else "hanging out"
                plan_loc = completed_plan.get("location", "somewhere") if completed_plan else "somewhere"
                
                # Write natural end journal entry
                try:
                    await self.diary.write_date_journal_entry(self, plan_act, plan_loc, ended_early=False)
                except Exception as journal_err:
                    print(f"[DATE LIFECYCLE] Error writing date journal: {journal_err}")
                
                # Remove completed plan from future plans and overrides
                today_str = datetime.now(IST).strftime("%Y-%m-%d")
                if completed_plan:
                    start = completed_plan.get("start", "")
                    end = completed_plan.get("end", "")
                    
                    self.state["_future_plans"] = [
                        p for p in self.state.get("_future_plans", [])
                        if not (p.get("date") == today_str and p.get("start") == start and p.get("end") == end)
                    ]
                    
                    self.state["_daily_schedule"]["overrides"] = [
                        o for o in overrides
                        if not (o.get("start") == start and o.get("end") == end and o.get("is_user_plan", False))
                    ]
                
                self.state["_active_date_running"] = False
                
            elif is_roleplay_mode and not was_date_active:
                print("[DATE LIFECYCLE] Date started! Setting _active_date_running = True")
                self.state["_active_date_running"] = True
                
        except Exception as e:
            print(f"[WARNING] Daily life schedule error: {e}")
        
        # Sync upcoming events from personality_evolution into state
        # so daily_life.py can read them when generating schedules
        if hasattr(self.personality_evolution, 'upcoming_events') and self.personality_evolution.upcoming_events:
            old_events = set(e.get("event", "") for e in self.state.get("_upcoming_events", []) if isinstance(e, dict))
            self.state["_upcoming_events"] = self.personality_evolution.upcoming_events
            new_events = set(e.get("event", "") for e in self.personality_evolution.upcoming_events if isinstance(e, dict))
            
            # If new events were added, refresh the schedule to incorporate them
            if new_events - old_events:
                from .daily_life import refresh_schedule_for_new_events
                try:
                    refreshed = await refresh_schedule_for_new_events(self.state)
                    if refreshed:
                        print(f"[COGNITIVE] Schedule refreshed to incorporate new events: {new_events - old_events}")
                        # Re-fetch activity details
                        activity_details = get_current_activity_details(self.state)
                        is_roleplay_mode = activity_details.get("is_user_plan", False)
                        location = activity_details.get("location", "home")
                        current_activity = activity_details.get("activity", "")
                except Exception as e:
                    print(f"[COGNITIVE] Schedule refresh failed: {e}")
                    
        return {
            "circadian_phase": circadian_phase.value,
            "time_deltas": time_deltas,
            "behavior_modulations": modulations,
            "context_string": temporal_context_str,
            "current_activity": current_activity,
            "upcoming_activities": upcoming_activities,
            "is_roleplay_mode": is_roleplay_mode,
            "location": location,
            "time_personality": self.personality_evolution.time_personality if hasattr(self.personality_evolution, 'time_personality') else {},
        }
    
    def _get_agent_state(self) -> Dict[str, Any]:
        """Get current agent state for LLM prompt."""
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "personality": self.state.get("core_personality", {}),
            "mood": self.psyche.get_mood_vector(),
            "trust": self.psyche.psyche.get("trust", 0.7),
            "hurt": self.psyche.psyche.get("hurt", 0.0),
            "forgiveness_state": self.psyche.psyche.get("forgiveness_state", "FORGIVEN"),
            "neurochem": self.psyche.get_neurochem_vector(),
            "habits": self.state.get("habits_cpbm", {})
        }
    
    def _update_reciprocity(self, events: List[Dict[str, Any]], 
                           understanding: Dict[str, Any],
                           perception: Dict[str, Any]):
        """Update reciprocity ledger based on events."""
        for event in events:
            event_type = event.get("type", "")
            confidence = event.get("confidence", 0.5)
            
            # Map events to reciprocity entry types
            if "vulnerability" in event_type.lower() or "confession" in event_type.lower():
                self.reciprocity_ledger.add_entry(
                    "vulnerability", "medium", "user",
                    emotional_weight=confidence
                )
            elif "apology" in event_type.lower():
                sincerity = understanding.get("sincerity", 0.7)
                if sincerity > 0.7:
                    self.reciprocity_ledger.add_entry(
                        "repair", "genuine", "user",
                        emotional_weight=sincerity
                    )
            elif "support" in event_type.lower() or "comfort" in event_type.lower():
                self.reciprocity_ledger.add_entry(
                    "support", "active_listening", "user",
                    emotional_weight=confidence
                )
    
    def _get_delta_hours(self) -> float:
        """Get hours since last update."""
        last_update = self.state.get("metadata", {}).get("updated_at")
        if last_update:
            last_time = datetime.fromisoformat(last_update.replace("Z", "+00:00"))
            return (datetime.now(timezone.utc) - last_time).total_seconds() / 3600
        return 0.0
    
    def _calculate_engagement_score(self, user_message: str, perception: Dict[str, Any],
                                   understanding: Dict[str, Any], 
                                   temporal_context: Dict[str, Any]) -> float:
        """
        Calculate engagement score from user response signals.
        
        Engagement factors:
        - Response time (fast = engaged) - if we have last AI message time
        - Message length (longer = more engaged, but not too long)
        - Emotion (positive = engaged)
        - Reply quality (thoughtful = engaged) - based on understanding depth
        - Emoji usage (more = engaged)
        - Sincerity (higher = engaged)
        
        Returns: 0.0-1.0 engagement score
        """
        score = 0.0
        
        # 1. Message length (0.20 weight)
        # Optimal length: 20-200 chars = high engagement
        # Too short (<10) or too long (>500) = lower engagement
        msg_len = len(user_message)
        if 20 <= msg_len <= 200:
            length_score = 1.0
        elif 10 <= msg_len < 20 or 200 < msg_len <= 500:
            length_score = 0.7
        elif msg_len < 10:
            length_score = 0.3  # Very short = low engagement
        else:
            length_score = 0.5  # Very long = moderate (might be ranting)
        score += 0.20 * length_score
        
        # 2. Emotion/Valence (0.25 weight)
        # Positive emotion = higher engagement
        valence = perception.get("valence", 0.0)
        # Normalize from [-1, 1] to [0, 1]
        valence_score = (valence + 1.0) / 2.0
        score += 0.25 * valence_score
        
        # 3. Reply quality / Thoughtfulness (0.20 weight)
        # Based on understanding depth, sincerity, subtext detection
        sincerity = understanding.get("sincerity", 0.7)
        has_subtext = bool(understanding.get("subtext", ""))
        depth_score = (sincerity * 0.6) + (0.4 if has_subtext else 0.0)
        score += 0.20 * depth_score
        
        # 4. Emoji usage (0.15 weight)
        # More emojis = more engaged (but not excessive)
        emoji_count = sum(1 for c in user_message if ord(c) > 127 and 
                         (0x1F600 <= ord(c) <= 0x1F64F or  # Emoticons
                          0x1F300 <= ord(c) <= 0x1F5FF or  # Misc Symbols
                          0x1F680 <= ord(c) <= 0x1F6FF or  # Transport
                          0x2600 <= ord(c) <= 0x26FF or    # Misc symbols
                          0x2700 <= ord(c) <= 0x27BF))     # Dingbats
        emoji_density = min(1.0, emoji_count / 5.0)  # 5+ emojis = max
        score += 0.15 * emoji_density
        
        # 5. Response time (0.10 weight) - if we have last AI message time
        # Fast response = engaged (within 5 minutes = high, >30 min = low)
        response_time_score = 0.5  # Default moderate
        last_ai_time = self.state.get("temporal_context", {}).get("last_ai_message_time")
        if last_ai_time:
            try:
                last_time = datetime.fromisoformat(last_ai_time.replace("Z", "+00:00"))
                delta_minutes = (datetime.now(timezone.utc) - last_time).total_seconds() / 60
                if delta_minutes <= 5:
                    response_time_score = 1.0  # Very fast = high engagement
                elif delta_minutes <= 15:
                    response_time_score = 0.8
                elif delta_minutes <= 30:
                    response_time_score = 0.6
                elif delta_minutes <= 60:
                    response_time_score = 0.4
                else:
                    response_time_score = 0.2  # Slow = lower engagement
            except Exception:
                pass  # If parsing fails, use default
        score += 0.10 * response_time_score
        
        # 6. Arousal/Energy (0.10 weight)
        # Higher arousal = more engaged
        arousal = perception.get("arousal", 0.0)
        arousal_score = (arousal + 1.0) / 2.0  # Normalize to [0, 1]
        score += 0.10 * arousal_score
        
        # Clamp to [0, 1] and add small variance (engagement detection isn't perfect)
        score = max(0.0, min(1.0, score))
        # Add stochastic variance (±0.05)
        score = max(0.0, min(1.0, score + random.gauss(0, 0.05)))
        
        return score
    
    def _save_state(self):
        """Save updated state to persistent storage."""
        # Update state with all system changes
        self.memory.update_state_memory(self.state)
        self.psyche.update_state(self.state)
        self.personality.save_to_state()
        self.cpbm.save_to_state()
        self.conflict_lifecycle.save_to_state()
        self.reciprocity_ledger.save_to_state()
        self.relationship_phases.save_to_state()
        self.initiative_engine.save_to_state()
        self.embodiment.save_to_state()
        self.theory_of_mind.save_to_state()
        self.self_narrative.save_to_state()
        self.parallel_life.save_to_state()
        self.pattern_detector.save_to_state()
        self.counterfactual_replayer.save_to_state()
        
        # Save via orchestrator
        self.state_orchestrator.update_state(self.user_id, self.state)
    
    def get_state_snapshot(self) -> Dict[str, Any]:
        """Get full state snapshot for debugging/inspection."""
        return {
            "user_id": self.user_id,
            "state": self.state,
            "memory_summary": {
                "stm_count": len(self.memory.memory.get("stm", [])),
                "act_threads_count": len(self.memory.memory.get("act_threads", [])),
                "episodic_count": len(self.memory.memory.get("episodic", [])),
                "identity_count": len(self.memory.memory.get("identity", []))
            },
            "psyche_summary": self.psyche.get_psyche_summary()
        }

