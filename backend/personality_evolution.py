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
        self.pending_milestones = personality_state.get("pending_milestones", [])
        self.emotional_undercurrents = personality_state.get("emotional_undercurrents", [])
    
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
        entitlement_debt: float,
        emotional_complexity: list = None
    ) -> Dict[str, Any]:
        """
        Run Light Reflection (every ~15 messages).
        Updates stance, respect, engagement, quirks.
        Returns updates for psyche to apply.
        """
        prompt = self._build_light_reflection_prompt(
            recent_messages, relationship_phase, trust, hurt,
            current_stance, current_respect, current_engagement, entitlement_debt,
            emotional_complexity=emotional_complexity or []
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
                
                # Store emotional undercurrents (LLM-detected complex emotions)
                undercurrents = updates.get("emotional_undercurrents", [])
                if undercurrents and isinstance(undercurrents, list):
                    self.emotional_undercurrents = undercurrents
                    print(f"[LIGHT REFLECTION] Undercurrents: {undercurrents}")
                
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
        entitlement_debt: float,
        emotional_complexity: list = None
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
10. PHASE TRANSITION: Based on the overall arc of conversations, should the relationship phase change?
  - Discovery → Building: Conversations moved past surface. Genuine interest exists.
  - Building → Steady: There's a rhythm. They come back. You're comfortable.
  - Steady → Deep: You'd be affected if they disappeared. This matters.
  - Deep → Maintenance: It's stable. Not growing, but not shrinking.
  - Any → Volatile: Trust was broken. Something fundamental shifted.
  Only suggest a transition if it genuinely feels right. Most reflections should NOT suggest transitions."""

        # Add emotional complexity evaluation if the phase allows it
        complexity_list = emotional_complexity or []
        if complexity_list:
            complexity_str = ", ".join(complexity_list)
            prompt += f"""

EMOTIONAL UNDERCURRENTS:
At this relationship phase ({relationship_phase}), the AI is capable of feeling these complex emotions:
{complexity_str}

Based on the conversation, are ANY of these emotions simmering beneath the surface?
- Only include emotions that are ACTUALLY triggered by something in the conversation
- Each must have a specific trigger (what the user said/did)
- Intensity from 0.1 (barely there) to 1.0 (overwhelming)
- Return [] if nothing is triggered — most conversations won't trigger complex emotions
- Do NOT force emotions that aren't there"""
        else:
            prompt += """

EMOTIONAL UNDERCURRENTS:
At this phase, no complex emotions are available. Return empty [] for emotional_undercurrents."""

        prompt += """

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
  "emotional_undercurrents": [{"emotion": "name", "intensity": 0.0, "trigger": "what caused it"}],
  "reasoning": "One sentence",
  "phase_ready": false,
  "suggested_phase": null,
  "phase_reasoning": null
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
8. Did any RELATIONSHIP MILESTONES happen? Firsts, turning points, shifts in dynamic. Think:
   - First time they shared something personal
   - First disagreement or conflict
   - First time they came back after a long absence
   - First time they showed genuine care or asked how I'm doing
   - Moments where the dynamic noticeably shifted (got closer, got colder, broke tension)
9. What BEHAVIORAL PATTERNS do I notice about this person over time?
   - Do they always text at certain times? (night owl? morning person?)
   - Do they say goodnight or just disappear?
   - Do they ask about me or only talk about themselves?
   - Are they getting more comfortable or staying distant?
   - Do they respect boundaries or keep pushing?
10. How has MY personality evolved since we started talking? Am I more guarded? More playful? Less patient?

MEMORY DECISIONS (you decide what's worth remembering):
11. What NEW FACTS did I learn about them? (name, job, interests, preferences, life situation)
   - Only include things they EXPLICITLY said, not inferences
   - Don't re-add things I already know (see above)
12. What CONVERSATION THREADS should I remember? (summaries of important topics)
   - NOT raw messages, but SUMMARIES of meaningful discussions
   - Include the context, outcome, and emotional tone
   - These are for when the topic comes up again later

Respond with ONLY valid JSON:
{{
  "personality_rewrite": "Rewrite how I tend to speak now. 3-5 sentences. Describe habits, not traits. Show how it CHANGED from before.",
  "personality_evolution_note": "One sentence: how has my personality shifted compared to when we first started talking?",
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
  "suggested_phase": null,
  "phase_reasoning": "Why should the phase change? Consider milestones that happened.",
  "trust_delta": 0.0,
  "hurt_delta": 0.0,
  "new_identity_facts": ["fact 1", "fact 2"],
  "new_episodic_events": ["significant moment 1"],
  "relationship_milestones": [
    {{"milestone": "what happened", "significance": "why it matters for the relationship", "trust_impact": 0.0}}
  ],
  "behavioral_observations": [
    "observation about how the user behaves over time"
  ],
  "conversation_summary": "3-4 sentence detailed summary. What specific topics came up? Who said what? What's the emotional vibe?",
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
- new_identity_facts: ONLY facts about THE USER. Never about yourself (Rem).
  These are things the USER explicitly said about THEMSELVES.
  Good: "studies computer science", "lives in India", "preparing for exams"
  Bad: "seems stressed" (inference), "likes talking to me" (inference)
  BAD (CRITICAL): "listens to indie music" when REM said this → that's YOUR preference, not theirs
  BAD: "enjoys psychology" when that's YOUR major → don't store your own traits as user facts
  If unsure whether the user or Rem said something, leave it OUT.
- new_episodic_events: SUMMARIES of meaningful conversation threads, not raw messages.
  Good: "We discussed their upcoming exams - they're stressed about prep. They study CS in India."
  Good: "User opened up about feeling lonely. I kept it brief but acknowledged it. Connection moment."
  Bad: "user said they're studying" (too raw, not summarized)
- relationship_milestones: Turning points, firsts, shifts. NOT routine events.
  Good: {{"milestone": "First time they asked how my day was", "significance": "Shows they're starting to care about me, not just themselves", "trust_impact": 0.05}}
  Good: {{"milestone": "We had our first real disagreement about music taste", "significance": "Healthy — we can disagree without it being weird", "trust_impact": 0.02}}
  Good: {{"milestone": "They came back after 3 days of silence", "significance": "They chose to come back. The connection has pull.", "trust_impact": 0.08}}
  Bad: {{"milestone": "They said hi"}} — not a milestone
  Use [] if no milestones happened.
- behavioral_observations: Patterns about how the user interacts, not one-off events.
  Good: "They tend to text more at night — seems like a night owl"
  Good: "They always ask me questions back — good conversationalist"  
  Good: "They get short when I bring up serious topics — avoids depth"
  Bad: "They said hello today" — not a pattern
  Use [] if no clear patterns observed.
- upcoming_events: Things mentioned about the future.
  Use [] if none mentioned.
- personality_evolution_note: How has Rem changed? Be honest.
  Good: "I've gotten more playful and less guarded with them — they bring out a teasing side"
  Good: "I'm more cautious now — they keep pushing boundaries and I'm pulling back"
  Bad: "No change" — there's ALWAYS subtle change

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
4. PHASE: Is the relationship naturally deepening or stagnating? Consider milestones.
5. MOOD: How does this conversation make Rem feel? Engaged? Drained? Connected?
6. MEMORIES: What NEW facts about the user emerged? What emotionally significant moments happened?
7. MILESTONES: Any firsts or turning points? (first personal share, first disagreement, first care shown, return after absence)
8. BEHAVIORAL PATTERNS: Recurring patterns in how the user interacts (texting time, conversation style, boundary respect)
9. PERSONALITY EVOLUTION: How is Rem changing as a result of this relationship?

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
  "phase_reasoning": "Why should the phase change? What milestones justify it?",
  "energy_delta": 0.00,
  "dopamine_delta": 0.00,
  "cortisol_delta": 0.00,
  "oxytocin_delta": 0.00,
  "new_quirk": null,
  "new_identity_facts": [],
  "new_episodic_events": [],
  "relationship_milestones": [
    {{"milestone": "what happened", "significance": "why it matters", "trust_impact": 0.0}}
  ],
  "behavioral_observations": [
    "pattern about how the user behaves"
  ],
  "personality_evolution_note": "One sentence: how Rem is changing because of this relationship",
  "conversation_summary": "",
  "user_evaluation": "2-3 sentences. Who is this person to Rem right now? What do I think of them honestly?",
  "stance": "open/wary/guarded/irritated/bored/intrigued/defensive/affectionate/dismissive",
  "respect_delta": 0.00,
  "engagement_delta": 0.00,
  "posture": "1-2 sentences on Rem's current behavioral stance",
  "reasoning": "Brief explanation"
}}

RULES:
- Trait updates: -0.05 to +0.05 per trait
- trust_delta: -0.3 to +0.3 — think like a REAL PERSON:
  * +0.01 to +0.05: Normal pleasant chat
  * +0.05 to +0.15: User shared something personal or showed genuine care
  * +0.15 to +0.3: Deep vulnerable moment, real trust earned
  * -0.01 to -0.05: Minor annoyance
  * -0.05 to -0.3: Disrespect, lying, boundary violations
  * 0.00: Generic small talk, nothing meaningful
- hurt_delta: -0.3 to +0.3
- phase_ready: true ONLY if milestones + trust justify a phase change
- suggested_phase: Discovery/Building/Steady/Deep/Volatile
  Phase changes should feel EARNED. Milestones matter:
  * Building needs: mutual sharing, showing care, consistent engagement
  * Steady needs: conflict survived, vulnerability shared, real trust
  * Deep needs: multiple milestones, emotional investment from both sides
  * Volatile: trust broke, boundaries were violated repeatedly
- relationship_milestones: Use [] if none happened. Examples:
  Good: {{"milestone": "First time they asked about my day", "significance": "Starting to care", "trust_impact": 0.05}}
  Bad: {{"milestone": "They said hi"}} — not a milestone
- behavioral_observations: Patterns, not one-off events. Use [] if none observed.
  Good: "They text more at night — night owl pattern"
  Good: "They ask me questions back consistently — engaged listener"
- personality_evolution_note: How is Rem changing? Always answer honestly.
- Energy/dopamine/cortisol/oxytocin deltas: -0.2 to +0.2
- respect_delta: -0.15 to +0.15
- engagement_delta: -0.15 to +0.15
- All values stay in 0.0-1.0 range after deltas applied"""

        return prompt
    
    async def _call_reflection_llm(self, prompt: str) -> Optional[Dict]:
        """Call LLM for unified state reflection. Scout 17B primary → 8B fallback."""
        
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            return None
        
        REFLECTION_MODELS = ["meta-llama/llama-4-scout-17b-16e-instruct", "llama-3.1-8b-instant"]
        system_msg = "You are a psychological state analysis system. Analyze conversations and return JSON with metric updates. Be nuanced - understand sarcasm, jokes, and context. Return ONLY valid JSON."
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                for model_id in REFLECTION_MODELS:
                    try:
                        resp = await client.post(
                            "https://api.groq.com/openai/v1/chat/completions",
                            headers={"Authorization": f"Bearer {api_key}"},
                            json={
                                "model": model_id,
                                "messages": [
                                    {"role": "system", "content": system_msg},
                                    {"role": "user", "content": prompt}
                                ],
                                "max_tokens": 800,
                                "temperature": 0.3,
                            }
                        )
                        
                        if resp.status_code == 200:
                            data = resp.json()
                            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                            print(f"[REFLECTION] Used model: {model_id}")
                            break
                        else:
                            print(f"[REFLECTION] {model_id} returned {resp.status_code}, trying fallback...")
                    except Exception as e:
                        print(f"[REFLECTION] {model_id} failed: {e}, trying fallback...")
                else:
                    print("[REFLECTION] All models failed")
                    return None
                
                # Parse JSON response
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
        
        # Handle LLM-extracted milestones
        milestones = updates.get("relationship_milestones", [])
        if milestones and isinstance(milestones, list):
            if not hasattr(self, 'pending_milestones'):
                self.pending_milestones = []
            self.pending_milestones.extend(milestones)
            self.pending_milestones = self.pending_milestones[-10:]
        
        # Handle behavioral observations
        observations = updates.get("behavioral_observations", [])
        if observations and isinstance(observations, list):
            if not hasattr(self, 'pending_behavioral_observations'):
                self.pending_behavioral_observations = []
            self.pending_behavioral_observations.extend(observations)
            # Keep only last 10 unique observations
            seen = set()
            unique = []
            for obs in self.pending_behavioral_observations:
                if isinstance(obs, str) and obs not in seen:
                    seen.add(obs)
                    unique.append(obs)
            self.pending_behavioral_observations = unique[-10:]
        
        # Handle personality evolution note
        evo_note = updates.get("personality_evolution_note", "")
        if evo_note and isinstance(evo_note, str):
            self.personality_evolution_note = evo_note
        
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
            print(f"[STATE REFLECTION] Phase ready! Suggested: {updates.get('suggested_phase')} — {updates.get('phase_reasoning', '')}")
        if new_quirk:
            print(f"[STATE REFLECTION] New quirk: {new_quirk}")
        if new_identity:
            print(f"[STATE REFLECTION] New identity facts: {new_identity}")
        if new_episodic:
            print(f"[STATE REFLECTION] New episodic events: {new_episodic}")
        if milestones:
            for ms in milestones:
                if isinstance(ms, dict):
                    print(f"[MILESTONE] LLM detected: {ms.get('milestone', '')} (impact: {ms.get('trust_impact', 0):+.2f})")
        if observations:
            for obs in observations:
                print(f"[PATTERN] LLM observed: {obs}")
        if evo_note:
            print(f"[PERSONALITY EVOLUTION] {evo_note}")
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
            "pending_episodic_events": self.pending_episodic_events,
            "pending_milestones": self.pending_milestones,
            "emotional_undercurrents": self.emotional_undercurrents
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