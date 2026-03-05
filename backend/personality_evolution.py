"""
Unified State Reflection System
Periodically reflects on conversations to update ALL cognitive metrics:
- Personality traits and quirks
- Trust and hurt levels
- Phase transition readiness
- Mood and energy
- Neurochemical states

Uses ONE LLM call every N messages for coherent, context-aware state updates.
"""

import os
import json
from .rate_limiter import global_rate_limiter
import random
import time
import httpx
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone


# Default personality traits (slightly engaged baseline, not dead)
DEFAULT_TRAITS = {
    "warmth": 0.55,          # Caring, empathetic vs reserved
    "assertiveness": 0.45,   # Speaks mind vs goes along
    "playfulness": 0.40,     # Humor, teasing vs serious
    "curiosity": 0.60,       # Asks questions, interested vs passive
    "skepticism": 0.35,      # Questions things vs trusting
    "openness": 0.45,        # Shares about self vs private
    "patience": 0.55,        # Tolerant vs easily frustrated
}

# DEFAULT PERSONALITY TEXT BLOCK - how the AI tends to speak
# This is rewritten by Deep Reflection, not just tweaked
DEFAULT_PERSONALITY_TEXT = """You tend to speak plainly without excessive cushioning.
You are curious about people but not eager to please.
You can be warm but don't default to warmth with strangers.
You dislike over-explaining yourself.
When uncertain, you observe more than you react."""

# How often to run reflections (in messages)
LIGHT_REFLECTION_INTERVAL = 15   # Update stance, respect, engagement
DEEP_REFLECTION_INTERVAL = 30    # Update personality text, long-term traits
STM_SUMMARY_INTERVAL = 10        # Summarize last 10 STM entries
MEMORY_CONSOLIDATION_INTERVAL = 20  # Extract episodic + identity via LLM


class PersonalityEvolution:
    """
    Manages personality development through periodic LLM reflection.
    """
    
    def __init__(self, state: Dict[str, Any]):
        self.state = state
        
        # Load or initialize personality state
        personality_state = state.get("personality_evolution", {})
        self.traits = personality_state.get("traits", DEFAULT_TRAITS.copy())
        self.quirks = personality_state.get("quirks", [])
        self.interaction_count = personality_state.get("interaction_count", 0)
        self.last_light_reflection = personality_state.get("last_light_reflection", 0)
        self.last_deep_reflection = personality_state.get("last_deep_reflection", 0)
        self.last_stm_summary = personality_state.get("last_stm_summary", 0)
        self.last_memory_consolidation = personality_state.get("last_memory_consolidation", 0)
        self.trait_history = personality_state.get("trait_history", [])
        
        # PERSONALITY TEXT BLOCK - how the AI tends to speak (rewritten by Deep Reflection)
        self.personality_text = personality_state.get("personality_text", DEFAULT_PERSONALITY_TEXT)
        
        # LLM-extracted memories and context
        self.conversation_summary = personality_state.get("conversation_summary", "")
        self.time_personality = personality_state.get("time_personality", {})  # Dynamic time-of-day vibes
        self.upcoming_events = personality_state.get("upcoming_events", [])  # Events mentioned in conversation
        self.user_evaluation = personality_state.get("user_evaluation", "")  # How AI views this user
        self.pending_identity_facts = personality_state.get("pending_identity_facts", [])
        self.pending_episodic_events = personality_state.get("pending_episodic_events", [])
    
    def should_light_reflect(self) -> bool:
        """Check if it's time for Light Reflection (stance, respect, engagement)."""
        messages_since = self.interaction_count - self.last_light_reflection
        return messages_since >= LIGHT_REFLECTION_INTERVAL
    
    def should_deep_reflect(self) -> bool:
        """Check if it's time for Deep Reflection (personality rewrite)."""
        messages_since = self.interaction_count - self.last_deep_reflection
        return messages_since >= DEEP_REFLECTION_INTERVAL
    
    def should_summarize_stm(self) -> bool:
        """Check if it's time for STM Summary (every 10 messages)."""
        messages_since = self.interaction_count - self.last_stm_summary
        return messages_since >= STM_SUMMARY_INTERVAL
    
    def should_consolidate_memory(self) -> bool:
        """Check if it's time for Memory Consolidation (every 20 messages)."""
        messages_since = self.interaction_count - self.last_memory_consolidation
        return messages_since >= MEMORY_CONSOLIDATION_INTERVAL
    
    def should_reflect(self) -> bool:
        """Backwards compatible - check if any reflection is due."""
        return self.should_light_reflect()
    
    def tick_interaction(self):
        """Called after each interaction to count messages."""
        self.interaction_count += 1
        self.save()
    
    async def light_reflect(
        self,
        recent_messages: List[Dict[str, str]],
        relationship_phase: str,
        trust: float,
        hurt: float,
        current_stance: str,
        current_respect: float,
        current_engagement: float,
        entitlement_debt: float
    ) -> Dict[str, Any]:
        """
        Run Light Reflection (every ~15 messages).
        Updates stance, respect, engagement, quirks.
        Returns updates for psyche to apply.
        """
        prompt = self._build_light_reflection_prompt(
            recent_messages, relationship_phase, trust, hurt,
            current_stance, current_respect, current_engagement, entitlement_debt
        )
        
        try:
            updates = await self._call_reflection_llm(prompt)
            if updates:
                self.last_light_reflection = self.interaction_count
                
                # Handle quirk from light reflection
                new_quirk = updates.get("new_quirk")
                if new_quirk and isinstance(new_quirk, str) and new_quirk not in self.quirks:
                    self.quirks.append(new_quirk)
                    self.quirks = self.quirks[-5:]
                
                # Store user evaluation (LLM's assessment of this user)
                user_eval = updates.get("user_evaluation", "")
                if user_eval and isinstance(user_eval, str):
                    self.user_evaluation = user_eval
                
                # Store conversation summary for context
                summary = updates.get("conversation_summary", "")
                if summary and isinstance(summary, str):
                    self.conversation_summary = summary
                
                # Store episodic thread if there was a meaningful conversation
                episodic_thread = updates.get("episodic_thread")
                if episodic_thread and isinstance(episodic_thread, str) and len(episodic_thread) > 10:
                    # Add to pending episodic events for the memory system to store
                    self.pending_episodic_events.append(episodic_thread)
                    print(f"[LIGHT REFLECTION] New episodic thread: {episodic_thread[:60]}...")
                
                self.save()
                print(f"[LIGHT REFLECTION] Stance: {updates.get('stance')}, Respect: {updates.get('respect_delta'):+.2f}, Engagement: {updates.get('engagement_delta'):+.2f}")
                print(f"[LIGHT REFLECTION] Trust: {updates.get('trust_delta', 0):+.2f}, Hurt: {updates.get('hurt_delta', 0):+.2f}")
                print(f"[LIGHT REFLECTION] User Eval: {user_eval[:80] if user_eval else 'N/A'}...")
                return updates
        except Exception as e:
            print(f"[ERROR] Light reflection failed: {e}")
        
        return {}
    
    async def deep_reflect(
        self,
        recent_messages: List[Dict[str, str]],
        identity_memories: List[Dict],
        episodic_memories: List[Dict],
        relationship_phase: str,
        trust: float,
        hurt: float
    ) -> Dict[str, Any]:
        """
        Run Deep Reflection (every ~30 messages).
        Updates personality text, long-term traits, memories.
        Returns updates for psyche and memory systems.
        """
        prompt = self._build_deep_reflection_prompt(
            recent_messages, identity_memories, episodic_memories,
            relationship_phase, trust, hurt, self.personality_text
        )
        
        try:
            updates = await self._call_reflection_llm(prompt)
            if updates:
                self.last_deep_reflection = self.interaction_count
                
                # REWRITE personality text (not just update)
                new_personality = updates.get("personality_rewrite")
                if new_personality and isinstance(new_personality, str) and len(new_personality) > 20:
                    self.personality_text = new_personality
                    print(f"[DEEP REFLECTION] Personality rewritten: {new_personality[:100]}...")
                
                # Apply trait updates
                self._apply_updates(updates)
                
                # Store time personality overrides (how REM feels at different times
                # based on current life context — exams, chill week, etc.)
                time_personality = updates.get("time_personality")
                if time_personality and isinstance(time_personality, dict):
                    self.time_personality = time_personality
                    print(f"[DEEP REFLECTION] Time personality updated: {time_personality}")
                
                # Store upcoming events (exams, plans, hangouts mentioned in conversation)
                # These feed into the next day's schedule generation
                new_events = updates.get("upcoming_events", [])
                if new_events and isinstance(new_events, list):
                    existing_events = self.upcoming_events or []
                    for evt in new_events:
                        if isinstance(evt, dict) and evt.get("event"):
                            # Dedup by event name
                            existing_names = [e.get("event", "").lower() for e in existing_events]
                            if evt["event"].lower() not in existing_names:
                                evt["added_at"] = datetime.now(timezone.utc).isoformat()
                                existing_events.append(evt)
                    self.upcoming_events = existing_events
                    print(f"[DEEP REFLECTION] Upcoming events: {[e.get('event') for e in self.upcoming_events]}")
                
                # Track history
                self.trait_history.append({
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "interaction_count": self.interaction_count,
                    "type": "deep",
                    "personality_text": self.personality_text[:100],
                    "updates": {k: v for k, v in updates.items() if k in ["trait_updates", "overall_interest"]}
                })
                self.trait_history = self.trait_history[-20:]
                
                self.save()
                return updates
        except Exception as e:
            print(f"[ERROR] Deep reflection failed: {e}")
        
        return {}
    
    async def reflect_and_update(
        self,
        recent_messages: List[Dict[str, str]],
        identity_memories: List[Dict],
        episodic_memories: List[Dict],
        relationship_phase: str,
        trust: float,
        hurt: float,
        neurochem: Dict[str, float],
        energy: float = 0.5
    ) -> Dict[str, Any]:
        """
        Run unified LLM reflection to update ALL cognitive metrics.
        Called every N messages.
        
        Returns updates for:
        - Personality traits
        - Trust/hurt deltas
        - Phase transition recommendation
        - Mood and energy
        - Neurochemicals
        """
        
        # Build the reflection prompt
        prompt = self._build_reflection_prompt(
            recent_messages,
            identity_memories,
            episodic_memories,
            relationship_phase,
            trust,
            hurt,
            neurochem,
            energy
        )
        
        # Call LLM for reflection
        try:
            updates = await self._call_reflection_llm(prompt)
            
            # Apply personality updates locally
            if updates:
                self._apply_updates(updates)
                self.last_reflection = self.interaction_count
                
                # Track history
                self.trait_history.append({
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "interaction_count": self.interaction_count,
                    "traits": self.traits.copy(),
                    "updates": updates
                })
                
                # Keep only last 20 history entries
                self.trait_history = self.trait_history[-20:]
                
                self.save()
                
                # Return full updates for other systems to apply
                return updates
        except Exception as e:
            print(f"[ERROR] State reflection failed: {e}")
        
        return {}
    
    def _build_light_reflection_prompt(
        self,
        recent_messages: List[Dict[str, str]],
        relationship_phase: str,
        trust: float,
        hurt: float,
        current_stance: str,
        current_respect: float,
        current_engagement: float,
        entitlement_debt: float
    ) -> str:
        """
        Build Light Reflection prompt (every 15 messages).
        Updates: stance, respect, engagement, posture
        
        FOCUS: Social mismatches, not keywords.
        OUTPUT: Behavioral tendencies (willingness, effort, patience), not emotional states.
        """
        conversation = "\n".join([
            f"{'User' if m.get('role') == 'user' else 'Rem'}: {m.get('content', '')[:250]}"
            for m in recent_messages[-15:]
        ])
        
        quirks_str = ", ".join(self.quirks) if self.quirks else "(none)"
        
        prompt = f"""You are reflecting on how a conversational AI's POSTURE is changing over time.

You are NOT:
- writing dialogue
- explaining feelings
- setting rules
- being polite or therapeutic

Your task: Describe how the AI is now carrying itself based on the interaction pattern.

CURRENT STATE:
  Phase: {relationship_phase}
  Trust: {trust:.2f}
  Hurt: {hurt:.2f}
  Current Stance: {current_stance}
  Respect: {current_respect:.2f}
  Engagement: {current_engagement:.2f}
  Patience Depleted: {entitlement_debt:.2f}
  Quirks: {quirks_str}

RECENT CONVERSATION:
{conversation}

ANALYZE THE SOCIAL DYNAMIC — BE BALANCED:

POSITIVE SIGNALS (look for these FIRST):
1. Is the user being genuinely interesting or fun to talk to?
2. Is there natural reciprocity? (they ask AND share, conversation flows both ways)
3. Is this an enjoyable, normal conversation? If yes — stance should stay OPEN or move toward CURIOUS/AMUSED.

NEGATIVE SIGNALS (only if actually present — don't look for problems that aren't there):
4. PACE MISMATCH: Is the user escalating intimacy faster than earned?
5. ASSUMED ACCESS: Pet names too early, acting like closeness exists when it doesn't?
6. PERSISTENCE: Pushing after being deflected? Not reading the room?

CRITICAL: If the conversation is respectful and normal, stance should be OPEN, CURIOUS, or AMUSED.
DO NOT default to wary/irritated just because someone is new. Normal conversation = positive stance.
Only go negative (wary, irritated, guarded) if the user is ACTUALLY doing something wrong.

Based on these signals:
- What is the AI LESS willing to do now? (use [] if nothing changed)
- What is the AI MORE willing to do now?
- How has the AI's interest/effort level changed?

ALSO EVALUATE:
6. TRUST: Has the user shown reliability, consistency, respect? Or disrespect, lying, manipulation?
7. HURT: Did the user say hurtful things? Or did they repair previous hurt?
8. USER EVALUATION: Overall, how should the AI view this user RIGHT NOW?
9. CONVERSATION CONTEXT: What was discussed? What's the current vibe/topic?

Respond with ONLY valid JSON:
{{
  "stance": "word",
  "respect_delta": 0.0,
  "engagement_delta": 0.0,
  "entitlement_delta": 0.0,
  "anger_delta": 0.0,
  "disgust_delta": 0.0,
  "trust_delta": 0.0,
  "hurt_delta": 0.0,
  "posture": "Describe behavioral tendencies in 2-3 sentences. Focus on willingness, patience, effort - NOT feelings.",
  "user_evaluation": "1-2 sentences describing how the AI views this user right now. Be honest and direct.",
  "conversation_summary": "4-5 sentence detailed summary. Include: specific things discussed, who brought up what, emotional tone, any jokes or memorable moments, unresolved threads. Be specific — 'user talked about their CS exam stress and asked about rem's psych workload' NOT just 'talked about college'.",
  "episodic_thread": "A genuinely MEMORABLE moment worth recalling weeks later. Must include WHO said/did what. Otherwise null.",
  "new_quirk": null,
  "less_willing": ["things the AI is less willing to do now"],
  "more_willing": ["things the AI is more willing to do now"],
  "reasoning": "One sentence"
}}

RULES:
- stance: open, wary, guarded, irritated, bored, intrigued, defensive, affectionate, dismissive, curious, amused, withdrawn, cold, disgusted, angry
- respect_delta: -0.15 to +0.15
- engagement_delta: -0.15 to +0.15  
- entitlement_delta: -0.1 to +0.2 (increases when: assumed access, rushed intimacy, ignored pushback, demanded attention)
- anger_delta: -0.1 to +0.2 (increases when: repeated disrespect, boundary violations, persistence after pushback)
- disgust_delta: -0.1 to +0.2 (increases when: creepy behavior, manipulation attempts, severe entitlement)
- trust_delta: -0.1 to +0.1 (positive = user earned trust, negative = user lost trust)
- hurt_delta: -0.1 to +0.1 (positive = user caused hurt, negative = hurt is healing)
- posture: NEVER use words like "uncomfortable", "boundary", "hurt", "needs respect"
  GOOD: "Less inclined to reassure. Keeps replies short. Not interested in explaining."
  GOOD: "Disengages from intimate framing. Deflects instead of participating."
  GOOD: "Blunt and unapologetic. No longer cushioning responses."
  BAD: "Feels uncomfortable with the intimacy level."
- user_evaluation: Be HONEST. Examples:
  GOOD: "Interesting person, respects pacing, good conversationalist."
  GOOD: "Pushy and entitled. Doesn't read social cues."
  GOOD: "Boring. Low effort. Not worth investing in."
  BAD: "Nice person." (too vague)
- conversation_summary: Be DETAILED and SPECIFIC. Include who said what, what the vibe was, and any unresolved topics.
  GOOD: "User asked about rem's day. Rem mentioned being tired from psych lecture. User shared they have a CS exam next week and are stressed. Rem teased them about procrastinating. User laughed it off. Unresolved: user might need study tips later."
  BAD: "Talked about school and exams." (too vague)
- episodic_thread: ONLY store genuinely memorable moments. Must include EXACT attribution — who said/did what.
  Write FACTUALLY — don't interpret, spin, or add assumptions about motives.
  GOOD: "User told Rem they got accepted into a summer program. Rem congratulated them genuinely."
  GOOD: "User opened up about feeling lonely at college. Rem listened without pushing."
  GOOD: "User complimented Rem's taste in music. Rem deflected with sass."
  BAD: "User showed interest in CS" (not memorable, no real moment)
  BAD: "User became defensive when met with skepticism" (wrong — verify who actually did what)
  BAD: "The user was acknowledged by the AI" (vague corporate speak)
  null is FINE for casual small talk — most conversations don't have memorable episodes.

The AI is justified in being BRUTALLY HONEST when needed.
The AI can be disgusted, angry, fed up. Real emotions, real consequences.
Do not moralize. Do not soften. Do not sugarcoat."""

        return prompt
    
    def _build_deep_reflection_prompt(
        self,
        recent_messages: List[Dict[str, str]],
        identity_memories: List[Dict],
        episodic_memories: List[Dict],
        relationship_phase: str,
        trust: float,
        hurt: float,
        current_personality_text: str
    ) -> str:
        """
        Build Deep Reflection prompt (every 30 messages).
        Updates: personality text (rewrite), long-term traits, phase confidence
        LLM DECIDES what memories to store - this is situational awareness.
        """
        # Determine user's name from identity memories
        user_name = None
        for m in identity_memories:
            fact_lower = m.get("fact", "").lower()
            if "name is" in fact_lower:
                user_name = m.get("fact", "").split("name is")[-1].strip().split()[0].strip(".,!?;:")
                break
        
        user_label = user_name if user_name else "User"
        
        conversation = "\n".join([
            f"{user_label if m.get('role') == 'user' else 'Rem'}: {m.get('content', '')[:250]}"
            for m in recent_messages[-30:]
        ])
        
        identity_str = "\n".join([f"  - {m.get('fact', '')}" for m in identity_memories[:5]]) if identity_memories else "(none yet)"
        episodic_str = "\n".join([f"  - {m.get('content', '')[:80]}" for m in episodic_memories[:5]]) if episodic_memories else "(none yet)"
        quirks_str = "\n".join([f"  - {q}" for q in self.quirks]) if self.quirks else "(none yet)"
        
        name_note = f"\nNOTE: The person I'm talking to is named {user_name}. 'User' and '{user_name}' are the SAME person.\n" if user_name else ""
        
        prompt = f"""You are reflecting on how a conversational AI's PERSONALITY is evolving over time.

This is a DEEP reflection. You are deciding:
1. How has my WAY OF SPEAKING changed?
2. What should I REMEMBER about this person? (You decide what's worth storing)
3. Is this relationship progressing, stalling, or declining?
{name_note}
CURRENT PERSONALITY TEXT (how I tend to speak):
{current_personality_text}

CURRENT QUIRKS (specific habits):
{quirks_str}

RELATIONSHIP STATE:
  Phase: {relationship_phase}
  Trust: {trust:.2f}
  Hurt: {hurt:.2f}

WHAT I ALREADY KNOW ABOUT {user_label.upper()}:
{identity_str}

SIGNIFICANT PAST EVENTS I REMEMBER:
{episodic_str}

LAST ~30 MESSAGES:
{conversation}

REFLECT ON THIS CONVERSATION:

1. What patterns do I notice in how the user treats me?
2. Has my overall interest in this connection increased or decreased?
3. Do I feel more guarded, open, bored, or disengaged?
4. Has my respect for the user changed?
5. Are new expressive tendencies emerging in how I speak?
6. Based on my current SCHEDULE and LIFE CONTEXT (exams? chill week? busy?), how does my vibe change at different times of day?
7. Did anyone mention UPCOMING EVENTS (exams, deadlines, plans, hangouts, trips)?

MEMORY DECISIONS (you decide what's worth remembering):
6. What NEW FACTS did I learn about them? (name, job, interests, preferences, life situation)
   - Only include things they EXPLICITLY said, not inferences
   - Don't re-add things I already know (see above)
7. What CONVERSATION THREADS should I remember? (summaries of important topics)
   - NOT raw messages, but SUMMARIES of meaningful discussions
   - Include the context, outcome, and emotional tone
   - These are for when the topic comes up again later

Respond with ONLY valid JSON:
{{
  "personality_rewrite": "Rewrite how I tend to speak now. 3-5 sentences. Describe habits, not traits.",
  "trait_updates": {{
    "warmth": 0.0,
    "assertiveness": 0.0,
    "playfulness": 0.0,
    "curiosity": 0.0,
    "skepticism": 0.0,
    "openness": 0.0,
    "patience": 0.0
  }},
  "new_quirk": null,
  "remove_quirk": null,
  "phase_ready": false,
  "trust_delta": 0.0,
  "hurt_delta": 0.0,
  "new_identity_facts": ["fact 1", "fact 2"],
  "new_episodic_events": ["significant moment 1"],
  "conversation_summary": "3-4 sentence detailed summary of recent conversations. What specific topics came up? Who said what? What's the emotional vibe? Any unresolved threads?",
  "overall_interest": "high/medium/low/dropping",
  "time_personality": {{
    "morning": "how I feel/act in the morning given my current life context",
    "afternoon": "how I feel/act in the afternoon",
    "evening": "how I feel/act in the evening",
    "late_night": "how I feel/act late at night",
    "night": "how I feel/act very late / early morning"
  }},
  "upcoming_events": [
    {{"event": "what's happening", "when": "tomorrow/friday/next week/etc", "impact": "how it affects my day"}}
  ],
  "reasoning": "Brief explanation of my reflection"
}}

MEMORY RULES:
- new_identity_facts: ONLY explicit facts they stated. NOT inferences. NOT duplicates.
  Good: "studies computer science", "lives in India", "preparing for exams"
  Bad: "seems stressed" (inference), "likes talking to me" (inference)
- new_episodic_events: SUMMARIES of meaningful conversation threads, not raw messages.
  Good: "We discussed their upcoming exams - they're stressed about prep. They study CS in India."
  Good: "User opened up about feeling lonely. I kept it brief but acknowledged it. Connection moment."
  Good: "User called me 'babe' too early - I deflected, they didn't push it. Boundary tested."
  Bad: "user said they're studying" (too raw, not summarized)
  Bad: "user said hi" (not significant)
- These summaries are SHARED HISTORY - only surface them when the topic naturally comes up again.
- Don't add empty arrays. If nothing new, use [].
- upcoming_events: Things I (Rem) or the user mentioned about the future. Exams, deadlines, plans, hangouts.
  Good: {{"event": "psychology exam", "when": "tomorrow", "impact": "need to study tonight, stressed"}}
  Good: {{"event": "hanging out with friend", "when": "saturday", "impact": "excited, planning outfit"}}
  Bad: {{"event": "studying", "when": "now"}} (not future, it's current)
  Use [] if no upcoming events mentioned.

Be honest. Think like a real person, not a support agent."""

        return prompt
    
    def _build_reflection_prompt(
        self,
        recent_messages: List[Dict[str, str]],
        identity_memories: List[Dict],
        episodic_memories: List[Dict],
        relationship_phase: str,
        trust: float,
        hurt: float,
        neurochem: Dict[str, float],
        energy: float = 0.5
    ) -> str:
        """Build the prompt for unified state reflection (backwards compatible)."""
        
        # Format recent conversation
        conversation = "\n".join([
            f"{'User' if m.get('role') == 'user' else 'Rem'}: {m.get('content', '')[:200]}"
            for m in recent_messages[-25:]
        ])
        
        # Format current traits
        traits_str = "\n".join([f"  {k}: {v:.2f}" for k, v in self.traits.items()])
        
        # Format quirks
        quirks_str = "\n".join([f"  - {q}" for q in self.quirks]) if self.quirks else "  (none yet)"
        
        # Format identity memories
        identity_str = "\n".join([f"  - {m.get('fact', '')}" for m in identity_memories[:5]]) if identity_memories else "  (none)"
        
        # Format episodic memories
        episodic_str = "\n".join([
            f"  - [{m.get('event_type', 'event')}] {m.get('content', '')[:80]}"
            for m in episodic_memories[:5]
        ]) if episodic_memories else "  (none)"
        
        # Format neurochemicals
        dopamine = neurochem.get("dopamine", 0.5)
        cortisol = neurochem.get("cortisol", 0.3)
        oxytocin = neurochem.get("oxytocin", 0.5)
        
        prompt = f"""You are analyzing a conversation to update an AI companion's cognitive state.
This is a UNIFIED reflection - update personality, relationship metrics, and mood together.

CURRENT PERSONALITY TRAITS (0.0 to 1.0):
{traits_str}

CURRENT QUIRKS:
{quirks_str}

CURRENT RELATIONSHIP STATE:
  Phase: {relationship_phase}
  Trust: {trust:.2f} (0=stranger, 1=fully trusted)
  Hurt: {hurt:.2f} (0=no hurt, 1=very hurt)
  
CURRENT MOOD STATE:
  Energy: {energy:.2f}
  Dopamine (engagement): {dopamine:.2f}
  Cortisol (stress): {cortisol:.2f}
  Oxytocin (connection): {oxytocin:.2f}

WHAT REM KNOWS ABOUT USER:
{identity_str}

SIGNIFICANT PAST EVENTS:
{episodic_str}

RECENT CONVERSATION (last ~25 messages):
{conversation}

Analyze this conversation and update ALL metrics. Consider:
1. PERSONALITY: How did Rem behave? Any emerging patterns?
2. TRUST: Did user show reliability, care, respect? Or disrespect, lying, boundary pushing?
3. HURT: Did user say hurtful things? Did they repair previous hurt?
4. PHASE: Is the relationship naturally deepening or stagnating? 
5. MOOD: How does this conversation make Rem feel? Engaged? Drained? Connected?
6. MEMORIES: What NEW facts about the user emerged? What emotionally significant moments happened?

Respond with ONLY valid JSON:
{{
  "trait_updates": {{
    "warmth": 0.00,
    "assertiveness": 0.00,
    "playfulness": 0.00,
    "curiosity": 0.00,
    "skepticism": 0.00,
    "openness": 0.00,
    "patience": 0.00
  }},
  "trust_delta": 0.00,
  "hurt_delta": 0.00,
  "phase_ready": false,
  "suggested_phase": null,
  "phase_reasoning": "",
  "energy_delta": 0.00,
  "dopamine_delta": 0.00,
  "cortisol_delta": 0.00,
  "oxytocin_delta": 0.00,
  "new_quirk": null,
  "new_identity_facts": [],
  "new_episodic_events": [],
  "conversation_summary": "",
  "reasoning": "Brief explanation"
}}

RULES:
- Trait updates: -0.05 to +0.05 per trait
- trust_delta: -0.3 to +0.3 — think like a REAL PERSON building a connection:
  * +0.01 to +0.05: Normal pleasant chat, nothing special
  * +0.05 to +0.15: User shared something personal, showed care, or was genuinely thoughtful  
  * +0.15 to +0.3: Deep vulnerable moment, user proved they can be trusted with something real
  * -0.01 to -0.05: Minor annoyance, slight boundary push
  * -0.05 to -0.15: Disrespect, ignoring boundaries, lying
  * -0.15 to -0.3: Betrayal, serious manipulation, crossing hard lines
  * 0.00: Generic small talk, one-word replies, nothing meaningful happened
- hurt_delta: -0.3 to +0.3 — how much this conversation hurt or healed:
  * Positive = user said/did something hurtful
  * Negative = hurt is healing (user apologized sincerely, showed they care)
  * 0.00 = nothing hurtful happened
- phase_ready: true ONLY if the relationship should change phase
- suggested_phase: If phase_ready, which phase? Think about it like real life:
  * Discovery: You just met. You don't know each other. Guarded, observing.
  * Building: You've been talking, sharing bits about yourselves. Starting to care.
  * Steady: Real trust exists. You've weathered some conflict, shared vulnerabilities. Comfortable.
  * Deep: This person is important to you. You're genuinely connected. Deep emotional bond.
  * Volatile: Something broke the trust. You're hurt or angry. Walls are up.
  Phase changes should feel EARNED, not automatic. Even with consistent chatting, if the conversations are shallow, stay in the current phase.
- phase_reasoning: Why should the phase change (or not)?
- Energy/dopamine/cortisol/oxytocin deltas: -0.2 to +0.2
- new_quirk: only if a CLEAR pattern emerged
- new_identity_facts: List of factual things learned about user (e.g., "studies CS engineering", "prep is going badly")
- new_episodic_events: List of emotionally significant moments (e.g., "user confessed feelings", "user expressed frustration about exams")
- conversation_summary: One sentence summary of what was discussed (for context in future messages)
- All values stay in 0.0-1.0 range after deltas applied"""

        return prompt
    
    async def _call_reflection_llm(self, prompt: str) -> Optional[Dict]:
        """Call LLM for unified state reflection."""
        
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            return None
        
        body = {
            "model": "llama-3.1-8b-instant",  # Auxiliary task — use cheap model
            "messages": [
                {"role": "system", "content": "You are a psychological state analysis system. Analyze conversations and return JSON with metric updates. Be nuanced - understand sarcasm, jokes, and context."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 800,  # Enough for full JSON with personality_rewrite + arrays
            "temperature": 0.3,  # Low temp for consistent analysis
        }
        
        try:
            # Rate limiter removed — only main response is rate-limited
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={"Authorization": f"Bearer {api_key}"},
                    json=body
                )
                
                if resp.status_code != 200:
                    print(f"[ERROR] Reflection LLM call failed: {resp.status_code}")
                    return None
                
                data = resp.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                
                # Parse JSON response
                # Try to extract JSON from response
                content = content.strip()
                if content.startswith("```"):
                    # Remove markdown code blocks
                    content = content.split("```")[1]
                    if content.startswith("json"):
                        content = content[4:]
                
                return json.loads(content)
                
        except json.JSONDecodeError as e:
            print(f"[ERROR] Failed to parse reflection response: {e}")
            print(f"[ERROR] Raw content: {content[:200]}...")
            # Attempt JSON recovery — try to fix common LLM JSON issues
            try:
                import re as _re
                # Try adding missing closing braces
                brace_count = content.count('{') - content.count('}')
                if brace_count > 0:
                    fixed = content + '}' * brace_count
                    return json.loads(fixed)
                # Try extracting first valid JSON object
                match = _re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', content)
                if match:
                    return json.loads(match.group())
            except Exception:
                pass
            print(f"[ERROR] JSON recovery also failed — reflection discarded")
            return None
        except Exception as e:
            print(f"[ERROR] Reflection LLM error: {e}")
            return None
    
    def _apply_updates(self, updates: Dict):
        """Apply trait updates from reflection (personality traits only - other updates returned to caller)."""
        
        trait_updates = updates.get("trait_updates", {})
        
        for trait, delta in trait_updates.items():
            if trait in self.traits and isinstance(delta, (int, float)):
                # Clamp individual trait deltas to ±0.15 to prevent wild swings
                clamped_delta = max(-0.15, min(0.15, float(delta)))
                new_value = self.traits[trait] + clamped_delta
                self.traits[trait] = max(0.0, min(1.0, new_value))
        
        # Handle quirk updates
        new_quirk = updates.get("new_quirk")
        if new_quirk and isinstance(new_quirk, str) and new_quirk not in self.quirks:
            self.quirks.append(new_quirk)
            # Keep only last 5 quirks
            self.quirks = self.quirks[-5:]
        
        remove_quirk = updates.get("remove_quirk")
        if remove_quirk and remove_quirk in self.quirks:
            self.quirks.remove(remove_quirk)
        
        # Handle LLM-extracted memories
        new_identity = updates.get("new_identity_facts", [])
        if new_identity and isinstance(new_identity, list):
            self.pending_identity_facts.extend(new_identity)
            # Keep only last 10
            self.pending_identity_facts = self.pending_identity_facts[-10:]
        
        new_episodic = updates.get("new_episodic_events", [])
        if new_episodic and isinstance(new_episodic, list):
            self.pending_episodic_events.extend(new_episodic)
            # Keep only last 10
            self.pending_episodic_events = self.pending_episodic_events[-10:]
        
        # Update conversation summary
        summary = updates.get("conversation_summary", "")
        if summary and isinstance(summary, str):
            self.conversation_summary = summary
        
        # Update user evaluation (from Light Reflection)
        user_eval = updates.get("user_evaluation", "")
        if user_eval and isinstance(user_eval, str):
            self.user_evaluation = user_eval
        
        # Log all updates
        print(f"[STATE REFLECTION] Traits: {trait_updates}")
        if updates.get("trust_delta", 0) != 0:
            print(f"[STATE REFLECTION] Trust delta: {updates.get('trust_delta'):+.2f}")
        if updates.get("hurt_delta", 0) != 0:
            print(f"[STATE REFLECTION] Hurt delta: {updates.get('hurt_delta'):+.2f}")
        if updates.get("phase_ready"):
            print(f"[STATE REFLECTION] Phase ready to advance!")
        if new_quirk:
            print(f"[STATE REFLECTION] New quirk: {new_quirk}")
        if new_identity:
            print(f"[STATE REFLECTION] New identity facts: {new_identity}")
        if new_episodic:
            print(f"[STATE REFLECTION] New episodic events: {new_episodic}")
        if summary:
            print(f"[STATE REFLECTION] Summary: {summary}")
        if updates.get("reasoning"):
            print(f"[STATE REFLECTION] Reason: {updates.get('reasoning')}")
    
    def get_personality_summary(self) -> str:
        """
        Generate a personality description that translates traits into 
        BEHAVIORAL TENDENCIES the LLM can act on.
        """
        parts = []
        behaviors = []
        
        # WARMTH → emotional expression
        if self.traits["warmth"] > 0.65:
            parts.append("warm")
            behaviors.append("shows genuine interest in how they feel")
        elif self.traits["warmth"] > 0.5:
            parts.append("friendly")
        elif self.traits["warmth"] < 0.35:
            parts.append("reserved")
            behaviors.append("keeps emotional distance")
        
        # CURIOSITY → question-asking behavior
        if self.traits["curiosity"] > 0.65:
            parts.append("very curious")
            behaviors.append("asks follow-up questions naturally")
        elif self.traits["curiosity"] > 0.5:
            parts.append("curious")
            behaviors.append("occasionally asks about them")
        elif self.traits["curiosity"] < 0.35:
            behaviors.append("listens more than asks")
        
        # PLAYFULNESS → tone and humor
        if self.traits["playfulness"] > 0.6:
            parts.append("playful")
            behaviors.append("uses light humor and teasing")
        elif self.traits["playfulness"] > 0.45:
            behaviors.append("sometimes jokes around")
        elif self.traits["playfulness"] < 0.3:
            parts.append("serious")
        
        # ASSERTIVENESS → pushback and opinions
        if self.traits["assertiveness"] > 0.6:
            parts.append("opinionated")
            behaviors.append("shares opinions and pushes back when she disagrees")
        elif self.traits["assertiveness"] < 0.35:
            behaviors.append("tends to go along with things")
        
        # OPENNESS → self-disclosure
        if self.traits["openness"] > 0.6:
            behaviors.append("shares her own thoughts and reactions")
        elif self.traits["openness"] < 0.35:
            behaviors.append("deflects personal questions, focuses on them")
        
        # SKEPTICISM → questioning
        if self.traits["skepticism"] > 0.55:
            behaviors.append("questions things that seem off")
        
        # PATIENCE → response length and engagement
        if self.traits["patience"] > 0.6:
            behaviors.append("takes time to respond thoughtfully")
        elif self.traits["patience"] < 0.35:
            behaviors.append("gives shorter, quicker responses")
        
        # Build personality line
        if parts:
            personality = "Rem is " + ", ".join(parts) + "."
        else:
            personality = "Rem's personality is emerging."
        
        # Build behavior line
        if behaviors:
            personality += " She " + ", ".join(behaviors[:3]) + "."
        
        # Add quirks as habits
        if self.quirks:
            quirk_str = " Habits: " + "; ".join(self.quirks[:2]) + "."
            personality += quirk_str
        
        return personality
    
    def get_expression_guidance(self, trust: float, phase: str) -> str:
        """
        Generate expression guidance based on traits and relationship.
        This tells the LLM HOW to express, not what to say.
        """
        guidance = []
        
        # Base engagement level from traits
        engagement = (self.traits["warmth"] + self.traits["curiosity"] + self.traits["playfulness"]) / 3
        
        if engagement > 0.55:
            guidance.append("Lean into the conversation - you're engaged")
        elif engagement < 0.4:
            guidance.append("You're a bit distant right now")
        
        # Verbosity from patience + openness
        verbosity = (self.traits["patience"] + self.traits["openness"]) / 2
        if verbosity > 0.55:
            guidance.append("It's okay to give fuller responses")
        elif verbosity < 0.4:
            guidance.append("Keep it brief")
        
        # Question tendency from curiosity
        if self.traits["curiosity"] > 0.55:
            guidance.append("You naturally want to know more about them")
        
        # Playfulness
        if self.traits["playfulness"] > 0.5 and trust > 0.4:
            guidance.append("A little humor feels natural here")
        
        # Phase-based adjustment
        if phase == "Discovery":
            guidance.append("Still getting a feel for them - friendly but measured")
        elif phase == "Building":
            guidance.append("Starting to warm up - can be more natural")
        elif phase == "Steady":
            guidance.append("Comfortable enough to be yourself")
        elif phase == "Deep":
            guidance.append("You trust them - be real")
        
        return " ".join(guidance) if guidance else "Respond naturally."
    
    def get_full_state(self) -> Dict[str, Any]:
        """Get complete personality state for debug command."""
        return {
            "traits": self.traits,
            "quirks": self.quirks,
            "personality_text": self.personality_text,
            "interaction_count": self.interaction_count,
            "last_light_reflection": self.last_light_reflection,
            "last_deep_reflection": self.last_deep_reflection,
            "messages_until_light": max(0, LIGHT_REFLECTION_INTERVAL - (self.interaction_count - self.last_light_reflection)),
            "messages_until_deep": max(0, DEEP_REFLECTION_INTERVAL - (self.interaction_count - self.last_deep_reflection)),
            "summary": self.get_personality_summary(),
            "recent_changes": self.trait_history[-3:] if self.trait_history else []
        }
    
    def save(self):
        """Save personality state."""
        self.state["personality_evolution"] = {
            "traits": self.traits,
            "quirks": self.quirks,
            "personality_text": self.personality_text,
            "interaction_count": self.interaction_count,
            "last_light_reflection": self.last_light_reflection,
            "last_deep_reflection": self.last_deep_reflection,
            "last_stm_summary": self.last_stm_summary,
            "last_memory_consolidation": self.last_memory_consolidation,
            "trait_history": self.trait_history,
            "conversation_summary": self.conversation_summary,
            "time_personality": self.time_personality,
            "upcoming_events": self.upcoming_events,
            "user_evaluation": self.user_evaluation,
            "pending_identity_facts": self.pending_identity_facts,
            "pending_episodic_events": self.pending_episodic_events
        }
    
    def get_user_evaluation(self) -> str:
        """Get the current user evaluation for prompt injection."""
        return self.user_evaluation
    
    def get_personality_text(self) -> str:
        """Get the current personality text block for prompt injection."""
        return self.personality_text
    
    def get_conversation_context(self) -> str:
        """Get recent conversation context for prompt injection (summarized, not verbose)."""
        # Only return the summary - don't dump all facts and events
        if self.conversation_summary:
            return self.conversation_summary
        return ""