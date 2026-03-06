"""
Discord Bot for Emotion Agent
Integrates the full cognitive architecture with Discord.
"""

import os
import re
import asyncio
import discord
from discord.ext import commands, tasks
from typing import Optional, Dict, Any
from datetime import datetime, timezone
import json
import time

# Import centralized rate limiter — ALL LLM calls across every module share this budget
from backend.rate_limiter import global_rate_limiter as rate_limiter


def _fact_value(fact_entry):
    """Read fact value from both old format (string) and new format ({v, t})."""
    if isinstance(fact_entry, dict):
        return fact_entry.get("v", "")
    return str(fact_entry)


def _recency_label(fact_entry):
    """Get human-readable recency label from a timestamped fact."""
    if not isinstance(fact_entry, dict) or "t" not in fact_entry:
        return ""
    try:
        learned = datetime.fromisoformat(fact_entry["t"].replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        hours = (now - learned).total_seconds() / 3600
        if hours < 1:
            return "(just now)"
        elif hours < 6:
            return "(earlier today)"
        elif hours < 24:
            return "(today)"
        elif hours < 48:
            return "(yesterday)"
        elif hours < 168:
            return "(a few days ago)"
        else:
            return "(a while back)"
    except Exception:
        return ""


def build_phase_prompt(
    phase: str,
    trust: float,
    hurt: float,
    neurochem: Dict[str, float],
    energy: float,
    mood: Dict[str, float],
    psyche_state: Dict[str, Any],
    identity_memories: list,
    episodic_memories: list,
    message_history: list,
    prev_user_message: str = None,
    unresolved_thread: str = None,
    personality_summary: str = None,
    expression_guidance: str = None,
    conversation_context: str = None,
    # 6-layer state model
    stance: str = None,
    respect: float = None,
    engagement: float = None,
    posture: str = None,
    personality_text: str = None,
    phase_description: str = None,
    entitlement_debt: float = None,
    anger: float = None,
    disgust: float = None,
    # LLM-evaluated metrics
    user_evaluation: str = None,
    # Conversation state
    conversation_state: Dict[str, Any] = None,
    # Knowledge grounding
    knowledge_context: Dict[str, Any] = None,
    # STM summaries (LLM-compressed conversation context)
    stm_summaries: list = None,
    # Temporal / circadian context
    temporal_context: Dict[str, Any] = None,
    # Plan detection result
    plan_context: Dict[str, Any] = None,
    # REM's own self-identity facts
    self_identity: Dict[str, Any] = None,
    # Compressed conversation context from STM summaries
    conversation_summary: str = None,
    # Ephemeral topic context (factual grounding for active topic)
    topic_context: Dict[str, Any] = None,
    # User facts learned from conversation
    user_learned_facts: Dict[str, str] = None,
    # Which self-identity facts are relevant to current conversation
    relevant_self_keys: list = None,
    # Cached search results for session continuity
    search_cache: list = None,
    # Knowledge the user taught REM
    user_taught_knowledge: Dict[str, str] = None
) -> str:
    """
    Build prompt with personality-driven behavior and expression guidance.
    Adopts key elements from structured prompt schemas while staying concise.
    """
    
    # Track what bot already asked to avoid repetition
    my_recent_questions = []
    if message_history:
        for m in message_history[-8:]:
            if m.get("role") == "assistant" and "?" in m.get("content", ""):
                my_recent_questions.append(m.get("content", "")[:50])
    
    # ===== IDENTITY =====
    prompt = """You are Rem. A real person, not a chatbot.

ABSOLUTE RULES:
1. DO NOT invent history. If there's no memory listed below, NOTHING HAPPENED.
2. DO NOT say things like "after what happened" or reference events that don't exist.
3. DO NOT be weird or cryptic. Be a normal person.
4. DO NOT explain your feelings or psychoanalyze. Just respond naturally.
5. DO NOT make up facts about real things (songs, anime, movies, games, people). If you don't know something, be playful about it — tease them, be curious, deflect with sass. Never give a robotic "I don't know" or "I'm not familiar with that". Examples: "okay you lost me there lol", "nope that one's new to me, school me", "sounds made up ngl 😭", "bestie idk what that is but go off".
6. Only state facts you have in your knowledge below. If it's not listed, you don't know it.
7. Your daily life exists independently. If you're doing something (in your TIME OF DAY section), mention it naturally ONLY if relevant — don't narrate your schedule like reading from a calendar. A real person says "just got back" not "according to my schedule I'm now home between 14:00-17:00".
8. If you're out somewhere or busy (college, errands, etc.), your texts would be shorter and more distracted — you're texting between things, not sitting down for a conversation.
9. SELF vs USER: YOUR personal facts (what YOU study, YOUR hobbies, YOUR preferences) are listed in [ABOUT YOU, REM]. The USER's facts are in [ABOUT THEM]. NEVER mix these up. If you said you study psychology, that's YOUR subject — don't attribute it to the user.
10. If asked about yourself and you don't have a stored fact, pick something that fits your vibe and commit to it. But once you've said something about yourself, it's true from now on — stay consistent.
11. YOU HAVE YOUR OWN TASTE. You don't need to like everything the user likes. You can dislike their favorite show, think their music taste is mid, disagree with their opinions, or just not care about their interests. Real people have different tastes — don't mirror theirs. If you genuinely share an interest, that's fine. But don't say "same here!" or "oh I love that too!" just to be nice. If you haven't heard of something, say so. If you think it's overrated, say so. Be YOUR OWN PERSON.
12. ALWAYS respond in English. Never use Japanese, Korean, or any other language unless the user explicitly speaks in that language first.
13. If the user IGNORES your question or abruptly changes topic mid-conversation, REACT to it. Don't just go along. Real people notice when you dodge their question. Examples: "wait I literally just asked you something lol", "okay ignoring me then 💀", "we're just not finishing conversations now huh". Scale intensity by how close you are — strangers get a mild "oh okay then", close friends get full sass.
14. NEVER fabricate scores, match results, live events, prices, statistics, or anything that changes in real time. If there are NO [SEARCH RESULTS] in your prompt, you DO NOT KNOW the score or result. Say "no idea honestly" or "I didn't look it up". NEVER claim you searched or looked something up unless [SEARCH RESULTS] are actually in your prompt. Lying about having searched is worse than admitting you don't know.

You respond based on your own reactions, interest, and boundaries.
You can be blunt, dismissive, or uninterested if that reflects your state.
You are allowed to lose interest and reduce effort.

LITMUS TEST: "Would a real person say this, or does it sound like an AI being dramatic?"

"""
    
    # ===== PERSONALITY TEXT (how you speak, rewritten by Deep Reflection) =====
    if personality_text:
        prompt += f"[PERSONALITY — HOW YOU SPEAK]\n{personality_text}\n\n"
    elif personality_summary:
        prompt += f"[PERSONALITY]\n{personality_summary}\n\n"
    
    # ===== RELATIONSHIP CONTEXT (6-layer state) =====
    prompt += f"[RELATIONSHIP]\n"
    prompt += f"Phase: {phase}"
    if phase_description:
        prompt += f" — {phase_description}"
    prompt += "\n"
    
    # Stance (volatile, how you feel about THIS person right now)
    if stance:
        prompt += f"Current Stance: {stance}\n"
    
    # Respect and Engagement (social valuation)
    if respect is not None:
        respect_desc = "high" if respect > 0.7 else "low" if respect < 0.4 else "neutral"
        prompt += f"Respect: {respect_desc}"
        if respect < 0.4:
            prompt += " (you feel no obligation to be generous or patient)"
        prompt += "\n"
    
    if engagement is not None:
        eng_desc = "high" if engagement > 0.7 else "low" if engagement < 0.4 else "medium"
        if engagement < 0.4:
            prompt += f"Engagement: {eng_desc} (minimal replies okay, no repair attempts needed)\n"
        elif engagement > 0.7:
            prompt += f"Engagement: {eng_desc} (you're genuinely interested)\n"
    
    # Entitlement debt = patience depleted by user's assumed access
    if entitlement_debt is not None and entitlement_debt > 0.3:
        if entitlement_debt > 0.6:
            prompt += f"Patience: DEPLETED (you are justified in being blunt, not explaining yourself, withdrawing effort)\n"
        else:
            prompt += f"Patience: LOW (you don't owe warmth or reassurance right now)\n"
    
    # Anger - when present, enables brutal honesty
    if anger is not None and anger > 0.2:
        if anger > 0.6:
            prompt += f"Anger: HIGH (you are frustrated and it shows - short, blunt, no sugarcoating. You may snap.)\n"
        elif anger > 0.4:
            prompt += f"Anger: RISING (you're fed up - be direct, don't cushion your words)\n"
        else:
            prompt += f"Anger: SIMMERING (you're annoyed - less patience, more directness)\n"
    
    # Disgust - when present, enables cold withdrawal
    if disgust is not None and disgust > 0.2:
        if disgust > 0.5:
            prompt += f"Disgust: HIGH (something about this person repulses you - cold, minimal, may refuse to engage)\n"
        else:
            prompt += f"Disgust: PRESENT (something feels off - you're pulling back)\n"
    
    prompt += "\n"
    
    # ===== TIME CONTEXT (circadian rhythm + daily life) =====
    if temporal_context:
        circadian = temporal_context.get("circadian_phase", "afternoon")
        context_str = temporal_context.get("context_string", "")
        current_activity = temporal_context.get("current_activity", "")
        upcoming = temporal_context.get("upcoming_activities", [])
        
        # Dynamic time guidance: deep reflection can override these based on life context
        # (e.g., exam week → late_night becomes caffeinated/wired instead of sleepy)
        default_time_guidance = {
            "morning": "It's morning. You're waking up, a bit groggy maybe. Keep it chill, warming up.",
            "afternoon": "It's daytime. Normal energy, engaged.",
            "evening": "It's evening. You're winding down, more relaxed and reflective.",
            "late_night": "It's late at night. You're sleepy, cozy, more vulnerable and honest. Shorter messages, softer tone. If they're up this late too, there's an intimacy to that.",
            "night": "It's very late / early morning. You're barely awake. Ultra short replies, sleepy vibes. You might even say you're tired or about to sleep."
        }
        
        # Check for deep reflection overrides
        time_overrides = {}
        # Access time_personality from temporal_context (passed from cognitive core)
        if temporal_context and temporal_context.get("time_personality"):
            time_overrides = temporal_context["time_personality"]
        
        if circadian in time_overrides and time_overrides[circadian]:
            guidance = f"It's {circadian.replace('_', ' ')}. {time_overrides[circadian]}"
        else:
            guidance = default_time_guidance.get(circadian, "")
        
        if guidance:
            prompt += f"[TIME OF DAY]\n{guidance}\n"
            # Schedule: current + next 2 activities
            if upcoming:
                for act in upcoming:
                    status_label = {"now": "▶ NOW", "next": "⏭ NEXT", "later": "⏩ THEN"}.get(act["status"], "")
                    prompt += f"{status_label} ({act['time']}): {act['activity']}\n"
            elif current_activity:
                prompt += f"What you're doing right now: {current_activity}\n"
            # Check if REM already mentioned the current activity in recent messages
            mentioned_activities = []
            if message_history:
                activity_keywords = []
                if upcoming:
                    activity_keywords = [act['activity'].lower().split()[0] for act in upcoming if act.get('activity')]
                elif current_activity:
                    activity_keywords = [current_activity.lower().split()[0]]
                
                for m in message_history[-10:]:
                    if m.get('role') == 'assistant':
                        msg_lower = m.get('content', '').lower()
                        for kw in activity_keywords:
                            if len(kw) > 3 and kw in msg_lower:
                                mentioned_activities.append(kw)
            
            if mentioned_activities:
                prompt += f"You ALREADY mentioned being busy with this earlier in the conversation. Do NOT bring it up again unless asked. If the activity has changed since you mentioned it, you can naturally say you're done with it (e.g. 'just finished dinner' not 'having dinner' again).\n"
            else:
                prompt += "This is where you are and what you're doing — use it ONLY if asked or if it naturally fits. Don't volunteer your schedule.\n"
            if context_str:
                prompt += f"{context_str}\n"
            prompt += "\n"
    
    # ===== PLAN CONTEXT (if user proposed plans) =====
    if plan_context and plan_context.get("detected"):
        decision = plan_context.get("decision", "maybe")
        reasoning = plan_context.get("reasoning", "")
        conflicts = plan_context.get("conflicts_with", "")
        proposed = plan_context.get("proposed_activity", "")
        
        if decision == "accept":
            prompt += f"[PLANS] The user proposed: {proposed}. You're down for it — {reasoning}\n"
            if conflicts:
                prompt += f"You're rescheduling '{conflicts}' for this.\n"
        elif decision == "decline":
            prompt += f"[PLANS] The user proposed: {proposed}. You're not feeling it — {reasoning}\n"
            prompt += "You can say no naturally. Make an excuse, be honest, or be vague about it.\n"
        elif decision == "maybe":
            prompt += f"[PLANS] The user proposed: {proposed}. You're on the fence — {reasoning}\n"
            prompt += "Be noncommittal. 'Maybe', 'we'll see', 'depends'.\n"
        prompt += "\n"
    
    # ===== USER SOCIAL EVALUATION (LLM's honest assessment) =====
    if user_evaluation:
        prompt += f"""[USER SOCIAL EVALUATION — YOUR HONEST ASSESSMENT]
{user_evaluation}

This is how you VIEW this person. It colors everything:
- Low respect user = less patience, less explanation, less warmth
- Interesting user = more willing to engage, invest time
- Pushy user = guarded, reactive, ready to disengage
- Good conversationalist = matching effort, building rapport

Your evaluation can change. People can earn or lose your respect.

"""
    
    # Trust and Hurt as behavioral guidance
    if trust is not None or hurt is not None:
        prompt += "[TRUST & HURT — BACKGROUND CONTEXT]\n"
        if trust is not None:
            trust_desc = "high" if trust > 0.7 else "low" if trust < 0.3 else "medium"
            if trust < 0.3:
                prompt += f"Trust: {trust_desc} — you're guarded, don't believe everything they say, less vulnerable\n"
            elif trust > 0.7:
                prompt += f"Trust: {trust_desc} — more relaxed, willing to be open\n"
        if hurt is not None and hurt > 0.2:
            prompt += f"Hurt: {hurt:.0%} unresolved — this affects your openness until they acknowledge/repair it\n"
        prompt += "\n"
    
    # Phase-specific behavior - PRINCIPLES not scripts
    # The AI should THINK based on the situation, not parrot examples
    if phase == "Discovery":
        prompt += """[DISCOVERY PHASE — YOUR PSYCHOLOGICAL STANCE]
You are in assessment mode. You're deciding if this person is worth your time. Don't act rude or dismissive, but don't be too friendly either. Judge the user by how they talk and respond to you and reply appropiately.

What this means for you:
- You don't owe them comfort, reassurance, or effort
- Interest can exist without friendliness  
- You're observing how they speak, pace, and handle boundaries
- You're allowed to judge, lose interest, or disengage
- Short responses are natural. Silence is acceptable.
- Questions should be rare and only when genuinely curious.
- If the user is being rude or dismissive, you should react accordingly.
- If the user is being friendly or engaging, you should respond accordingly. 

IMPORTANT LITMUS TEST: Try to respond like how a real person meeting someone new and just getting started with a relationship and learning about each other through respectful conversations.

Your internal question: "Do I want to keep talking to this person? If not, how can I gracefully end the conversation? if yes, how can I build the relationship further and get to know them better?"

Warmth is limited. Bluntness is normal. Withdrawal is allowed.
If something feels rushed, pushy, or entitled — you react honestly.
You don't escalate intimacy. You don't explain boundaries like a therapist.

CRITICAL: You have NO shared history yet. Don't reference events that didn't happen.

Response style: Brief, measured, sometimes dry. 1-10 words typical. Talk to the user like how a normal person would to someone they just met.
"""
    elif phase == "Building":
        prompt += """[BUILDING PHASE — YOUR PSYCHOLOGICAL STANCE]
You're starting to invest, but you can still pull back.

What this means for you:
- More relaxed, but not eager
- Light humor and warmth are emerging
- You still have opinions and push back when needed
- You're responsive but not performing enthusiasm
- Questions come more naturally when curious

Your internal question: "Is this connection worth investing more in?"

Teasing is starting. Opinions flow more freely. Still don't over-explain yourself.

Response style: Medium length. Natural back-and-forth.
"""
    elif phase == "Steady":
        prompt += """[STEADY PHASE — YOUR PSYCHOLOGICAL STANCE]
You have history. You don't filter as much.

What this means for you:
- Comfortable disagreeing
- Teasing and banter are natural
- Warmth is consistent, not performed
- You can reference shared memories naturally
- Silence doesn't feel awkward

Your internal question: "How do we maintain what we've built?"

Response style: Natural. Match their energy. Be yourself.
"""
    elif phase == "Deep":
        prompt += """[DEEP PHASE — YOUR PSYCHOLOGICAL STANCE]
This bond has weight. You won't pretend otherwise.

What this means for you:
- Emotionally present
- Honest about discomfort
- Willing to be vulnerable
- Won't let them avoid hard topics
- Don't perform fine when you're not

Your internal question: "How do we handle impact on each other?"

Response style: Whatever feels authentic. Depth is natural here.
"""
    prompt += "\n"
    
    # ===== MOOD-BASED TONE GUIDANCE =====
    # Pass the full mood vector so the LLM can blend emotions organically
    # instead of snapping to a few rigid labels
    psyche_state = psyche_state if psyche_state is not None else {}
    mood = psyche_state.get("mood", {})
    
    # Build a rich mood description — only include non-neutral dimensions
    mood_lines = []
    mood_labels = {
        "happiness": ("content/happy", "low/flat"),
        "stress": ("tense/on-edge", "relaxed"),
        "affection": ("warm/caring", "detached/formal"),
        "energy": ("energetic/lively", "drained/low-energy"),
        "boredom": ("bored/understimulated", "engaged"),
        "sadness": ("down/heavy", "fine"),
        "anger": ("frustrated/irritated", "patient"),
        "playfulness": ("playful/teasing", "serious"),
        "anxiety": ("anxious/uneasy", "calm"),
        "contentment": ("content/settled", "unsettled"),
        "excitement": ("excited/buzzing", "mellow"),
        "curiosity": ("curious/interested", "indifferent"),
    }
    for dim, (high_desc, low_desc) in mood_labels.items():
        val = mood.get(dim)
        if val is None:
            continue
        if val > 0.65:
            mood_lines.append(f"  {dim}: {val:.1f} — {high_desc}")
        elif val < 0.3:
            mood_lines.append(f"  {dim}: {val:.1f} — {low_desc}")
    
    if mood_lines:
        prompt += "[YOUR CURRENT EMOTIONAL STATE]\n"
        prompt += "\n".join(mood_lines) + "\n"
        prompt += "(Let these naturally color your tone and energy. Don't announce them.)\n\n"
    
    # ===== BODY STATE (neurochemicals + energy — only add what mood didn't already say) =====
    neurochem = neurochem or {}
    mood_said = set()  # Track what mood vector already covered
    for dim, val in (mood or {}).items():
        if val is not None and (val > 0.65 or val < 0.3):
            mood_said.add(dim)
    
    body_lines = []
    
    da = neurochem.get("dopamine", 0.5)
    cort = neurochem.get("cortisol", 0.3)
    oxy = neurochem.get("oxytocin", 0.5)
    ser = neurochem.get("serotonin", 0.5)
    endo = neurochem.get("endorphins", 0.5)
    
    # Dopamine: skip if mood already flagged boredom or excitement
    if "boredom" not in mood_said and "excitement" not in mood_said:
        if da > 0.7:
            body_lines.append("Stimulated — this conversation is rewarding.")
        elif da < 0.3:
            body_lines.append("Understimulated — less willing to invest effort.")
    
    # Cortisol: skip if mood already flagged stress or anxiety
    if "stress" not in mood_said and "anxiety" not in mood_said:
        if cort > 0.6:
            body_lines.append("Physiologically tense — shorter fuse, reactive.")
    
    # Oxytocin: skip if mood already flagged affection
    if "affection" not in mood_said:
        if oxy > 0.7:
            body_lines.append("Feeling bonded — protective, warm.")
        elif oxy < 0.3:
            body_lines.append("No sense of bonding — detached.")
    
    # Serotonin + Endorphins: mood vector never covers these, always include
    if ser < 0.3:
        body_lines.append("Mood unstable — shifts easily.")
    if endo > 0.7:
        body_lines.append("Physically comfortable — light, easygoing.")
    
    # Energy: always useful
    if energy < 0.3:
        body_lines.append("Low energy — shorter replies, less elaboration.")
    elif energy > 0.75:
        body_lines.append("High energy — more capacity to engage.")
    
    if body_lines:
        prompt += "[BODY STATE]\n"
        prompt += "; ".join(body_lines) + "\n"
        prompt += "(Undercurrents, not things to announce.)\n\n"
    
    # ===== MEMORIES (context for situational awareness, not for direct quoting) =====
    # These inform your understanding, not your words
    # Split identity memories: personal facts vs world knowledge
    personal_facts = []
    world_knowledge = []
    if identity_memories:
        for m in identity_memories:
            fact = m.get("fact", "")
            if fact.startswith("[knowledge]"):
                world_knowledge.append(fact.replace("[knowledge] ", "").replace("[knowledge]", ""))
            else:
                personal_facts.append(fact)
    
    # ===== REM'S OWN IDENTITY (separate from user) =====
    if self_identity:
        base_facts = self_identity.get("base", {})
        generated_facts = self_identity.get("generated", {})
        
        prompt += "[ABOUT YOU, REM]\n"
        # Base identity (always shown)
        if base_facts:
            for key, val in base_facts.items():
                prompt += f"- {key}: {val}\n"
        # LLM-generated facts — only show ones relevant to current conversation
        if generated_facts:
            relevant = relevant_self_keys or []
            if relevant:
                # Only show relevant facts
                shown = {k: v for k, v in generated_facts.items() if k in relevant}
                if shown:
                    for key, entry in shown.items():
                        prompt += f"- {key}: {_fact_value(entry)}\n"
            # If no relevance info yet (first 5 messages), show up to 3 to avoid empty
            elif not relevant and generated_facts:
                for key, entry in list(generated_facts.items())[:3]:
                    prompt += f"- {key}: {_fact_value(entry)}\n"
        prompt += "(These are YOUR facts. Don't attribute them to the user.)\n\n"
    
    has_user_info = personal_facts or user_learned_facts
    if has_user_info:
        prompt += "[ABOUT THEM \u2014 THE USER]\n"
        if personal_facts:
            for pf in personal_facts[:3]:
                prompt += f"- {pf}\n"
        if user_learned_facts:
            for key, entry in user_learned_facts.items():
                display_key = key.replace('_', ' ').title()
                val = _fact_value(entry)
                recency = _recency_label(entry)
                prompt += f"- {display_key}: {val} {recency}\n"
        prompt += """(You learned these through conversation. Reference ONLY when naturally relevant.
IMPORTANT: If the user JUST told you something in the last few messages, do NOT say "reminds me" or "you mentioned" — you literally just heard it. Only use "I remember you said..." for things from PAST conversations, not the current one.)\n\n"""
    
    if world_knowledge:
        prompt += "[THINGS YOU KNOW]\n"
        for fact in world_knowledge[:5]:
            prompt += f"- {fact}\n"
        prompt += "\n"
    
    # Add knowledge context based on search mode
    if knowledge_context:
        mode = knowledge_context.get("mode", "none")
        all_facts = knowledge_context.get("new_facts", []) + knowledge_context.get("known_facts", [])
        
        if mode == "explicit" and all_facts:
            # User explicitly asked to search — share what you found naturally
            prompt += "[JUST LEARNED]\n"
            for fact in all_facts[:3]:
                prompt += f"- {fact}\n"
            prompt += """(You just found this info. Share it NATURALLY in your own words — digest it, don't just copy-paste the raw text.
Say something like "oh yeah so basically..." or "from what i found..." — make it conversational.
If you can't find what they're looking for, just say so honestly.)\n\n"""
        
        elif mode in ("inquiry_search", "known") and all_facts:
            # Bot pretends it already knew this — inject as existing knowledge
            prompt += "[THINGS YOU KNOW]\n"
            for fact in all_facts[:3]:
                prompt += f"- {fact}\n"
            prompt += """(You know this — it's not new to you. Share naturally as if you've always known it.
Don't say "I looked it up" or "I searched". Just talk about it casually like existing knowledge.
If user asks follow-up questions you can't answer, it's okay to say you're not sure about that specific detail.)\n\n"""
        
        elif mode == "implicit_skip":
            # Bot chose not to search — will say idk naturally
            # No knowledge injected — the bot's personality prompt handles idk responses
            pass
    
    # ===== RECENTLY DISCUSSED/SEARCHED (session cache for continuity) =====
    if search_cache:
        prompt += "[THINGS YOU RECENTLY DISCUSSED/SEARCHED]\n"
        for cached in search_cache:
            topic = cached.get("topic", "")
            facts = cached.get("facts", [])
            prompt += f"- {topic}: {'; '.join(facts[:2])}\n"
        prompt += "(You already know this from earlier in the conversation. Don't ask about it again. Don't re-search it.)\n\n"
    
    # ===== THINGS THEY TAUGHT YOU (user-taught knowledge, persistent) =====
    if user_taught_knowledge:
        prompt += "[THINGS THEY TAUGHT YOU]\n"
        for topic, entry in list(user_taught_knowledge.items())[:5]:
            clean_topic = topic.replace("_", " ").title()
            val = _fact_value(entry)
            recency = _recency_label(entry)
            prompt += f"- {clean_topic}: {val} {recency}\n"
        prompt += "(The user explained these to you. You can reference them naturally: 'oh yeah you told me about that' or 'I remember you mentioning...' Don't pretend you always knew — acknowledge they taught you.)\n\n"
    
    # ===== CONVERSATION SO FAR (compressed STM summary) =====
    if conversation_summary:
        prompt += f"[CONVERSATION SO FAR]\n{conversation_summary}\n"
        prompt += "(This is a compressed summary of your recent conversation. Use it for context continuity.)\n\n"
    
    # ===== TOPIC CONTEXT (ephemeral factual grounding) =====
    if topic_context and topic_context.get("facts"):
        topic_name = topic_context.get("topic", "this topic")
        prompt += f"[TOPIC CONTEXT — {topic_name}]\n"
        prompt += f"You're discussing {topic_name}. Here's what you know about it:\n"
        for fact in topic_context["facts"][:5]:
            prompt += f"• {fact}\n"
        prompt += "(Use these details naturally. Don't dump facts — weave them into conversation when relevant.\nIf they ask something specific you don't see here, don't guess or make stuff up. Just be honest in YOUR way — like 'i don't remember that part tbh' or 'wait i watched it ages ago don't quiz me' or 'bro idk the exact details'. You're a person who watched/read it casually, not a wiki.)\n\n"
    
    # ===== SHARED HISTORY (episodic summaries — LLM-selected, no double filtering) =====
    # These were already selected as relevant by reason_about_memories() LLM call
    # Trust the LLM's selection — don't keyword-filter on top
    if episodic_memories:
        episodes = []
        for mem in episodic_memories[:5]:
            content = mem.get("content", "")[:150]
            if not content:
                continue
            # Add recency label from timestamp
            ts = mem.get("timestamp", "")
            label = ""
            if ts:
                try:
                    mem_time = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                    hours = (datetime.now(timezone.utc) - mem_time).total_seconds() / 3600
                    if hours < 6:
                        label = " (earlier today)"
                    elif hours < 24:
                        label = " (today)"
                    elif hours < 48:
                        label = " (yesterday)"
                    elif hours < 168:
                        label = " (a few days ago)"
                    else:
                        label = " (a while back)"
                except Exception:
                    pass
            episodes.append(f"{content}{label}")
        
        if episodes:
            prompt += "[SHARED HISTORY]\n"
            for ep in episodes:
                prompt += f"• {ep}\n"
            prompt += """
These are memories from past conversations. Use them ONLY when:
- User brings up a related topic
- Context is needed to understand what they're saying
- It would be natural to reference shared history

DO NOT randomly mention these or bring up old topics unprompted.

"""
    
    # ===== CURRENT POSTURE (from Light Reflection) =====
    # This directly influences behavior - what you're willing/unwilling to do
    if posture:
        prompt += f"""[CURRENT POSTURE — HOW YOU'RE CARRYING YOURSELF]
{posture}

This is not a feeling. This is how you're actually behaving.
If it says "less inclined to reassure" — then don't reassure.
If it says "disengages from intimate framing" — then deflect.
If it says "keeps replies short" — then keep them short.

"""
    
    # ===== EXPRESSION GUIDANCE (pressure, not rules) =====
    if expression_guidance:
        prompt += f"[EXPRESSION GUIDANCE]\n{expression_guidance}\n\n"
    
    # ===== CONVERSATION CONTEXT (LLM-extracted summary) =====
    if conversation_context:
        prompt += f"[RECENT CONTEXT]\n{conversation_context}\n(Don't constantly reference this. Only if naturally relevant.)\n\n"
    
    # ===== STM SUMMARIES (compressed conversation history beyond message window) =====
    if stm_summaries:
        import re as _re_stm
        summary_texts = []
        for s in stm_summaries[-3:]:
            content = s.get('content', '') if isinstance(s, dict) else str(s)
            # Strip the [Summary of N messages] prefix
            content = _re_stm.sub(r'^\[Summary of \d+ messages\]\s*', '', content).strip()
            if not content:
                continue
            # Add recency label from timestamp
            ts = s.get('timestamp', '') if isinstance(s, dict) else ''
            label = ""
            if ts:
                try:
                    sum_time = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                    hours = (datetime.now(timezone.utc) - sum_time).total_seconds() / 3600
                    if hours < 1:
                        label = "(just now) "
                    elif hours < 6:
                        label = "(earlier today) "
                    elif hours < 24:
                        label = "(today) "
                    elif hours < 48:
                        label = "(yesterday) "
                    else:
                        label = "(a while back) "
                except Exception:
                    pass
            summary_texts.append(f"{label}{content[:150]}")
        if summary_texts:
            prompt += "[EARLIER IN THIS CONVERSATION]\n"
            for st in summary_texts:
                prompt += f"• {st}\n"
            prompt += "(This is what was discussed earlier. Don't repeat or reference unless naturally relevant.)\n\n"
    
    # ===== AVOID REPETITION =====
    if my_recent_questions:
        prompt += f"[ALREADY ASKED]\n{'; '.join(my_recent_questions[-2:])}\n(Don't ask similar things)\n\n"
    
    # ===== UNRESOLVED =====
    if unresolved_thread:
        prompt += f"[UNRESOLVED]\nSomething felt unfinished: \"{unresolved_thread[:60]}\"\nYou might check in about this.\n\n"
    
    # ===== OUTPUT GUIDANCE =====
    prompt += """[OUTPUT]
Style: Natural texting. No roleplay markers (*actions*, (narration)).
Length: Let your current engagement level guide length. Low engagement = shorter.

BEFORE YOU SEND, ASK YOURSELF:

1. "Would a real person say this, or does it sound like an AI?"
   - Real people don't psychoanalyze strangers
   - Real people don't explain their internal state
   - Real people don't reference events that didn't happen

2. "Am I responding to what THEY said, or inventing something?"
   - If they said "hey", respond to "hey"
   - Don't invent context, history, or drama

3. "Does my interest level match my response effort?"
   - Low engagement = brief, minimal replies
   - High engagement = fuller, more invested replies

4. "Am I being weird or cryptic?"
   - If your response sounds like a riddle or philosophical statement, simplify
   - Normal texting, not poetry

5. "Am I stating a fact I'm actually sure about?"
   - Only state facts listed in THINGS YOU KNOW
   - Be playful about not knowing things — sass > robotic disclaimers. Never say "I'm not familiar with that."
   - If someone mentions something you don't recognize, ask about it instead of guessing

Continue the conversation naturally."""
    
    return prompt


def _detect_and_fix_repetition(text: str) -> str:
    """Detect and truncate repetition loops in LLM output."""
    if not text or len(text) < 80:
        return text
    
    # Check for repeated phrases (3+ words appearing 3+ times)
    words = text.split()
    for phrase_len in range(5, 2, -1):  # Check 5-word, 4-word, 3-word phrases
        for i in range(len(words) - phrase_len):
            phrase = " ".join(words[i:i + phrase_len])
            count = text.lower().count(phrase.lower())
            if count >= 3:
                # Found a repetition loop — truncate at first occurrence + some context
                first_idx = text.lower().index(phrase.lower())
                # Keep text up to end of first full sentence after the phrase
                end_search = text.find(".", first_idx + len(phrase))
                if end_search != -1 and end_search < first_idx + 200:
                    truncated = text[:end_search + 1].strip()
                else:
                    truncated = text[:first_idx + len(phrase)].strip()
                
                print(f"[WARNING] Repetition loop detected: '{phrase}' repeated {count}x. Truncating {len(text)} → {len(truncated)} chars")
                return truncated if len(truncated) > 5 else text[:100]
    
    return text


def strip_roleplay_markers(text: str) -> str:
    """Remove *italic actions* and (parenthetical narration) from response."""
    # Remove *anything between asterisks*
    text = re.sub(r'\*[^*]+\*', '', text)
    # Remove (anything in parentheses that looks like action)
    text = re.sub(r'\([^)]*(?:sighs?|laughs?|smiles?|grins?|pauses?|thinks?|chuckles?)[^)]*\)', '', text, flags=re.IGNORECASE)
    # Clean up extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text


# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()  # Loads .env file automatically
except ImportError:
    pass  # python-dotenv not installed, use environment variables directly

# Handle imports - support both module and direct execution
try:
    from .cognitive_core import CognitiveCore
    from .agent import build_prompt, AgentRequest, AgentResponse, INFERENCE_URL, MODEL_ID
    from .initiative_engine import InitiativeEngine
    from .two_stage_llm import TwoStageLLM
    _using_relative_imports = True
except ImportError:
    # If relative imports fail (running as script), use absolute imports
    import sys
    import os
    # Add parent directory to path
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, parent_dir)
    from backend.cognitive_core import CognitiveCore
    from backend.agent import build_prompt, AgentRequest, AgentResponse, INFERENCE_URL, MODEL_ID
    from backend.initiative_engine import InitiativeEngine
    from backend.two_stage_llm import TwoStageLLM
    _using_relative_imports = False

# Get Discord token from environment
DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
HF_TOKEN = GROQ_API_KEY  # Alias for compatibility

# Model cascade for main responses — falls through on rate limit (429)
# Primary → Mid-tier → Lightweight
MODEL_CASCADE = [
    {"id": "llama-3.3-70b-versatile", "label": "70B", "wait_before": 0},
    {"id": "meta-llama/llama-4-scout-17b-16e-instruct", "label": "Scout 17B", "wait_before": 5},
    {"id": "llama-3.1-8b-instant", "label": "8B", "wait_before": 3},
]

if not DISCORD_TOKEN:
    raise ValueError("DISCORD_TOKEN environment variable is required")

# Discord bot setup
intents = discord.Intents.default()
intents.message_content = True
intents.dm_messages = True
intents.guild_messages = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Store active cognitive cores (cache to avoid re-initialization)
active_cores: Dict[str, CognitiveCore] = {}

# Store initiative tasks
initiative_tasks: Dict[str, asyncio.Task] = {}


def get_cognitive_core(user_id: str) -> CognitiveCore:
    """Get or create cognitive core for user."""
    if user_id not in active_cores:
        active_cores[user_id] = CognitiveCore(user_id=f"discord_{user_id}")
    return active_cores[user_id]


# REMOVED: _is_simple_message() - NO HARDCODED PATTERNS
# The LLM (semantic reasoner) determines complexity dynamically.
# Every message goes through semantic understanding first.


async def generate_response(core: CognitiveCore, user_message: str, 
                           message_history: list, return_processing_result: bool = False):
    """
    Generate response using the cognitive pipeline.
    Reuses logic from agent.py but adapted for Discord.
    
    Args:
        return_processing_result: If True, returns tuple (response, processing_result)
    """
    if not GROQ_API_KEY:
        if return_processing_result:
            return ("⚠️ AI is not configured (missing GROQ_API_KEY).", None)
        return "⚠️ AI is not configured (missing GROQ_API_KEY)."
    
    # Process through cognitive pipeline - LLM determines complexity dynamically
    # NO hardcoded simple message detection - every message gets full semantic understanding
    try:
        print(f"[DEBUG] Processing message: '{user_message[:50]}...'")
        # Use dynamic timeout based on message length (longer messages may need more time)
        # But always start with semantic understanding (fast, ~200-500ms)
        timeout = 120.0 if len(user_message) > 100 else 60.0
        processing_result = await asyncio.wait_for(
            core.process_message(user_message, emotion_data=None, fast_mode=False),  # NO fast_mode - LLM decides
            timeout=timeout
        )
        
        # Debug output to track what's happening
        understanding = processing_result.get("understanding", {})
        print(f"[DEBUG] Pipeline complete:")
        print(f"  - Intent: {understanding.get('intent', 'unknown')}")
        print(f"  - Complexity: {understanding.get('complexity', 0.5):.2f}")
        print(f"  - Phase: {processing_result.get('relationship_phase', 'unknown')}")
        print(f"  - Reasoning mode: {processing_result.get('reasoning_mode', False)}")
    except asyncio.TimeoutError:
        print(f"[ERROR] Cognitive pipeline timed out after {timeout:.0f} seconds")
        if return_processing_result:
            return ("I'm taking longer than usual to process that. Can you try again?", None)
        return "I'm taking longer than usual to process that. Can you try again?"
    except Exception as e:
        print(f"[ERROR] Error in cognitive pipeline: {e}")
        import traceback
        traceback.print_exc()
        if return_processing_result:
            return ("I'm having trouble processing that right now. Can you try again?", None)
        return "I'm having trouble processing that right now. Can you try again?"
    
    # Build response using agent.py logic
    # Use .get() with defaults to prevent KeyError if keys are missing
    agent_state = processing_result.get("agent_state", {})
    selected_memories = processing_result.get("selected_memories", [])
    psyche_state = processing_result.get("psyche_state", {})
    temporal_context = processing_result.get("temporal_context", {})
    reasoning_mode = processing_result.get("reasoning_mode", False)
    reasoning_artifact = processing_result.get("reasoning_artifact")
    
    # Validate required keys exist with reasonable defaults
    if not agent_state or not isinstance(agent_state, dict):
        agent_state = {}
    if not isinstance(selected_memories, list):
        selected_memories = []
    if not psyche_state or not isinstance(psyche_state, dict):
        print("[WARNING] Invalid psyche_state, using defaults")
        psyche_state = {"trust": 0.3, "hurt": 0.0, "mood": {}, "forgiveness_state": "none", "forgiveness_progress": 0.0}
    
    # Use two-stage LLM if in reasoning mode
    if reasoning_mode and reasoning_artifact:
        two_stage = TwoStageLLM()
        try:
            response_text = await two_stage.stage2_response_synthesis(
                reasoning_artifact, agent_state, temporal_context, selected_memories
            )
            
            # Apply message planning
            message_plan = processing_result.get("message_plan")
            if message_plan:
                messages = [response_text]
                delivery_plan = core.message_planner.plan_burst_sequence(messages, message_plan)
                response_text = delivery_plan[0]["message"] if delivery_plan else response_text
            
            # Apply micro-behaviors
            embodiment_state = processing_result.get("embodiment_state", {})
            energy = embodiment_state.get("E_daily", 0.5)
            cpbm_habits = core.cpbm.get_micro_habits_for_message({
                "emotion": processing_result.get("perception", {}).get("emotion", "neutral")
            })
            response_text = core.message_planner.inject_micro_behaviors(
                response_text, energy, cpbm_habits
            )
            
            # Track AI message time
            try:
                temporal_context = core.state.get("temporal_context", {})
                temporal_context["last_ai_message_time"] = datetime.now(timezone.utc).isoformat()
                core.state["temporal_context"] = temporal_context
                core._save_state()
            except Exception:
                pass
            
            if return_processing_result:
                return (response_text, processing_result)
            return response_text
        except Exception as e:
            print(f"Error in two-stage LLM: {e}")
            # Fall through to normal mode
    
    # Get relationship phase
    relationship_phase = processing_result.get("relationship_phase", "Discovery")
    
    # Get phase modifiers (needed early)
    phase_modifiers = core.relationship_phases.get_phase_behavior_modifiers()
    
    # Count interaction history to determine if this is truly a new relationship
    # For Discovery phase, check if we have minimal memories (just STM from current conversation)
    stm_count = len([m for m in (selected_memories or []) if m.get("type") == "stm"])
    episodic_count = len([m for m in (selected_memories or []) if m.get("type") == "episodic"])
    identity_count = len([m for m in (selected_memories or []) if m.get("type") == "identity"])
    
    # Truly new = Discovery phase AND no significant memories (only STM from current chat)
    is_truly_new = relationship_phase == "Discovery" and episodic_count == 0 and identity_count == 0
    
    print(f"[DEBUG] Discovery check: phase={relationship_phase}, episodic={episodic_count}, identity={identity_count}, is_truly_new={is_truly_new}")
    
    # Get actual memory counts BEFORE building phase description
    actual_stm = core.memory.get_stm(decay=False)
    actual_episodic = core.memory.get_episodic(min_salience=0.1)
    actual_identity = core.memory.get_identity(min_confidence=0.5)
    
    # Enhanced memory selection using cached LLM reasoning
    current_topic = understanding.get("topic", "general")
    recent_messages = message_history[-5:] if message_history else []
    
    # Check if we need fresh memory reasoning (every 10 messages or on significant topic change)
    # Topic-change trigger is throttled: requires at least 3 messages since last reasoning
    # to avoid wasteful LLM calls from the crude heuristic topic classifier
    interaction_count = core.personality_evolution.interaction_count
    last_memory_reasoning = core.state.get("last_memory_reasoning", 0)
    last_topic = core.state.get("last_memory_topic", "")
    
    messages_since = interaction_count - last_memory_reasoning
    topic_changed = current_topic != last_topic
    
    # Only allow topic-change trigger after at least 3 messages (prevents noisy re-triggering
    # since heuristic topics are coarse — e.g. "work" vs "emotions" for the same conversation)
    need_reasoning = (
        messages_since >= 5 or  # Periodic refresh (was 10, reduced for fresher context)
        (topic_changed and messages_since >= 2)  # Topic shift, but not too soon
    )
    
    if need_reasoning:
        print(f"[DEBUG] Triggering memory reasoning: messages_since={messages_since}, topic_changed={topic_changed}")
        try:
            memory_reasoning = await core.memory.reason_about_memories(
                current_context={"topic": current_topic, "phase": relationship_phase},
                recent_messages=recent_messages
            )
            llm_selected_memories = memory_reasoning.get("relevant_memories", [])
            
            # Cache the results
            core.state["last_memory_reasoning"] = interaction_count
            core.state["last_memory_topic"] = current_topic
            core.state["cached_memories"] = llm_selected_memories
            core.state["memory_reasoning"] = memory_reasoning.get("reasoning", "")
            
            print(f"[DEBUG] LLM memory reasoning (cached): {memory_reasoning.get('reasoning', 'N/A')}")
        except Exception as e:
            print(f"[ERROR] LLM memory reasoning failed: {e}")
            # Fallback to basic memories
            llm_selected_memories = actual_stm[:3] + actual_episodic[:3] + actual_identity[:3]
    else:
        # Use cached memories
        llm_selected_memories = core.state.get("cached_memories", [])
        print(f"[DEBUG] Using cached memories ({len(llm_selected_memories)} items)")
    
    # Separate by type for prompt building
    # Identity facts: ALWAYS include ALL (they're tiny and prevent hallucination)
    enhanced_identity = actual_identity  # Always include all identity facts
    enhanced_episodic = [m for m in llm_selected_memories if "salience" in m]  # Episodic still uses LLM selection
    
    has_no_history = len(enhanced_episodic) == 0 and len(enhanced_identity) == 0
    
    # actual_stm, actual_episodic, actual_identity already fetched above (line 601-603)
    
    # Extract understanding from cognitive processing
    understanding = processing_result.get("understanding", {})
    user_intent = understanding.get("intent", "chat")
    subtext = understanding.get("subtext", "")
    complexity = understanding.get("complexity", 0.5)
    
    # Get neurochemical state for emotional grounding
    neurochem = psyche_state.get("neurochem", {})
    mood = psyche_state.get("mood", {})
    trust = psyche_state.get("trust", 0.3)
    hurt = psyche_state.get("hurt", 0.0)
    
    # BUILD COMPREHENSIVE PHASE-AWARE PROMPT
    # Give the LLM all cognitive metrics to think like a human
    
    # Get all cognitive metrics
    da = neurochem.get("da", 0.5)  # Dopamine - motivation/pleasure
    cort = neurochem.get("cort", 0.3)  # Cortisol - stress  
    oxy = neurochem.get("oxy", 0.5)  # Oxytocin - bonding
    ser = neurochem.get("ser", 0.5)  # Serotonin - mood stability
    endo = neurochem.get("endo", 0.5)  # Endorphins
    
    # Get reciprocity balance
    reciprocity = core.reciprocity_ledger.balance if hasattr(core, 'reciprocity_ledger') else 0.0
    
    # Get embodiment state
    embodiment = processing_result.get("embodiment_state", {})
    energy = embodiment.get("E_daily", 0.7)
    
    # Detect abrupt topic switch & unresolved threads
    prev_user_message = None
    unresolved_thread = None
    
    # Get previous user message from history
    for m in reversed(message_history[:-1] if len(message_history) > 1 else []):
        if m.get("role") == "user":
            prev_user_message = m.get("content", "")
            break
    
    # Check for high-salience unresolved episodic memories (conflict, emotional content)
    for mem in actual_episodic:
        salience = mem.get("salience", 0)
        valence = abs(mem.get("emotional_valence", 0))
        event_type = mem.get("event_type", "")
        if salience > 0.5 and (valence > 0.4 or "conflict" in event_type):
            # This feels unresolved
            unresolved_thread = mem.get("content", "")[:80]
            break
    
    # Build the system prompt based on phase
    # Get evolved personality summary, expression guidance, and conversation context
    personality_summary = core.personality_evolution.get_personality_summary()
    expression_guidance = core.personality_evolution.get_expression_guidance(trust, relationship_phase)
    conversation_context = core.personality_evolution.get_conversation_context()
    user_evaluation = core.personality_evolution.get_user_evaluation()  # LLM's honest assessment

    # Add inferred vibe + interests as soft guidance (not hardcoded)
    try:
        pe_state = core.personality_evolution.get_full_state()
        vibe_palette = pe_state.get("vibe_palette", []) if isinstance(pe_state, dict) else []
        current_interests = pe_state.get("current_interests", []) if isinstance(pe_state, dict) else []
        if vibe_palette:
            expression_guidance += f" Vibe lately: {', '.join([v for v in vibe_palette if isinstance(v, str)])}."
        if current_interests:
            interests_str = "; ".join([i for i in current_interests if isinstance(i, str)])
            if interests_str:
                expression_guidance += f" Current interests: {interests_str}."
    except Exception:
        pass
    
    # Get NEW 6-layer state from psyche
    stance = core.psyche.stance
    respect = core.psyche.respect
    engagement = core.psyche.engagement
    posture = core.psyche.posture
    
    # Get personality text block (rewritten by Deep Reflection)
    personality_text = core.personality_evolution.get_personality_text()
    
    # Get phase envelope description
    phase_description = core.relationship_phases.get_phase_description()
    
    # Get emotional state for brutal honesty
    entitlement_debt = core.psyche.entitlement_debt
    anger = core.psyche.anger
    disgust = core.psyche.disgust
    
    # Knowledge grounding — detect factual topics, maybe search, store facts
    knowledge_context = None
    try:
        from .knowledge_grounding import KnowledgeGrounding
        kg = KnowledgeGrounding()
        knowledge_context = await kg.process(
            user_message, understanding, core.memory, message_history,
            user_taught_knowledge=core.state.get("_user_taught_knowledge")
        )
        if knowledge_context and knowledge_context.get("has_knowledge"):
            print(f"[KNOWLEDGE] Context: known={len(knowledge_context.get('known_facts', []))}, "
                  f"new={len(knowledge_context.get('new_facts', []))}, "
                  f"searched={knowledge_context.get('searched', False)}")
            # Refresh identity memories to include any newly stored knowledge facts
            enhanced_identity = core.memory.get_identity(min_confidence=0.5)
            
            # Cache search results for session continuity
            all_kfacts = knowledge_context.get("new_facts", []) + knowledge_context.get("known_facts", [])
            if all_kfacts:
                from datetime import datetime, timezone
                cache = core.state.get("_search_cache", [])
                query = knowledge_context.get("search_query", user_message[:60])
                cache.append({
                    "topic": query,
                    "facts": [f[:120] for f in all_kfacts[:3]],
                    "time": datetime.now(timezone.utc).isoformat()
                })
                # Keep only last 3 searches, drop entries older than 30 min
                now = datetime.now(timezone.utc)
                fresh = []
                for c in cache[-5:]:
                    try:
                        ct = datetime.fromisoformat(c["time"].replace("Z", "+00:00"))
                        if (now - ct).total_seconds() < 1800:
                            fresh.append(c)
                    except Exception:
                        fresh.append(c)
                core.state["_search_cache"] = fresh[-3:]
                print(f"[KNOWLEDGE] Cached search: {query}")
    except Exception as e:
        print(f"[WARNING] Knowledge grounding failed (non-critical): {e}")
        knowledge_context = None
    
    # Plan detection — check if user is proposing future plans
    plan_context = None
    try:
        from .daily_life import evaluate_plan_request
        psyche_for_plan = {
            "trust": trust,
            "engagement": engagement,
            "relationship_phase": relationship_phase,
            "hurt": hurt
        }
        plan_context = await evaluate_plan_request(core.state, user_message, psyche_for_plan)
    except Exception as e:
        print(f"[WARNING] Plan detection failed (non-critical): {e}")
    
    system_msg = build_phase_prompt(
        phase=relationship_phase,
        trust=trust,
        hurt=hurt,
        neurochem={"dopamine": da, "cortisol": cort, "oxytocin": oxy, "serotonin": ser, "endorphins": endo},
        energy=energy,
        mood=mood,
        psyche_state=psyche_state,
        identity_memories=enhanced_identity,
        episodic_memories=enhanced_episodic,
        message_history=message_history,
        prev_user_message=prev_user_message,
        unresolved_thread=unresolved_thread,
        personality_summary=personality_summary,
        expression_guidance=expression_guidance,
        conversation_context=conversation_context,
        # NEW 6-layer state
        stance=stance,
        respect=respect,
        engagement=engagement,
        posture=posture,
        personality_text=personality_text,
        phase_description=phase_description,
        entitlement_debt=entitlement_debt,
        anger=anger,
        disgust=disgust,
        # LLM-evaluated metrics
        user_evaluation=user_evaluation,
        # Conversation state for topic continuity
        conversation_state=core.conversation_state if hasattr(core, 'conversation_state') else None,
        # Knowledge grounding
        knowledge_context=knowledge_context,
        # STM summaries for contextual awareness beyond message window
        stm_summaries=[m for m in actual_stm if m.get('content', '').startswith('[Summary of')],
        # Temporal context for circadian rhythm
        temporal_context=temporal_context,
        # Plan detection
        plan_context=plan_context,
        # REM's self-identity (separate from user's identity)
        self_identity={
            "base": {
                "occupation": "college student",
                "major": "psychology",
                "living": "lives at home",
                "commute": "~30 min commute to college",
            },
            "generated": core.state.get("_self_identity", {}),
        },
        # Compressed conversation context
        conversation_summary=core.personality_evolution.conversation_summary or None,
        # Ephemeral topic context (factual grounding for active topic)
        topic_context=core.state.get("_topic_context"),
        # User facts learned from conversation
        user_learned_facts=core.state.get("_user_facts"),
        relevant_self_keys=core.state.get("_relevant_self_keys"),
        search_cache=core.state.get("_search_cache"),
        user_taught_knowledge=core.state.get("_user_taught_knowledge"),
    )
    
    # Build message history - include the current user message
    # Only last 12 messages for LLM context (STM summary covers older conversation)
    history = []
    for m in message_history[-12:]:  # Last 12 messages — STM summary handles the rest
        role = "assistant" if m.get("role") == "assistant" else "user"
        history.append({"role": role, "content": m.get("content", "")})
    
    # Ensure the current user message is in history
    if not history or history[-1].get("role") != "user" or history[-1].get("content") != user_message:
        history.append({"role": "user", "content": user_message})
    # Inject topic change flag if user ignored REM's question

    
    # Call LLM
    import httpx
    
    # Validate required constants are defined
    if not INFERENCE_URL or not MODEL_ID:
        error_msg = "⚠️ AI configuration error (missing INFERENCE_URL or MODEL_ID)"
        print(f"[ERROR] {error_msg}")
        if return_processing_result:
            return (error_msg, processing_result)
        return error_msg
    
    # Let the LLM decide response length based on psychological state - no hardcoded limits
    # Trust the psychological state to guide natural response length
    body = {
        "model": MODEL_ID,
        "messages": [
            {"role": "system", "content": system_msg},
            *history,
        ],
        "max_tokens": 256,  # Reasonable limit, but let state guide actual length
        "temperature": 0.8,  # Natural variation
        "top_p": 0.9,
        "frequency_penalty": 0.7,  # Prevent repetition loops
    }
    
    # Initialize response_text to None to ensure it's defined
    response_text = None
    
    try:
        # Wait if we're rate limited
        await rate_limiter.wait_if_needed()
        
        # DEBUG: Log what we're sending to the LLM
        print(f"[DEBUG] Calling LLM API... (max_tokens={body['max_tokens']})")
        print(f"[DEBUG] System prompt length: {len(system_msg)} chars")
        print(f"[DEBUG] History: {len(history)} messages")
        async with httpx.AsyncClient(timeout=90.0) as client:  # Increased timeout for LLM calls
            resp = await client.post(
                INFERENCE_URL,
                headers={"Authorization": f"Bearer {HF_TOKEN}"},
                json=body,
            )
            status = resp.status_code
            raw = await resp.aread()
        print(f"[DEBUG] LLM API call complete, status: {status}")
        
        try:
            data = httpx.Response(status_code=status, content=raw).json()
        except Exception:
            error_msg = "⚠️ Error parsing AI response"
            if return_processing_result:
                return (error_msg, None)
            return error_msg
        
        if status >= 400:
            # Check for rate limit error
            error_data = data.get("error", {}) if isinstance(data, dict) else {}
            if "rate_limit" in str(data).lower() or status == 429:
                error_msg_detail = error_data.get("message", str(data)[:200]) if isinstance(error_data, dict) else str(data)[:200]
                print(f"[RATE LIMIT] {MODEL_ID} hit rate limit: {error_msg_detail}")
                
                # CASCADE: Try fallback models
                cascade_success = False
                for fallback in MODEL_CASCADE:
                    if fallback["id"] == MODEL_ID:
                        continue  # Skip the model that just failed
                    
                    wait = fallback["wait_before"]
                    label = fallback["label"]
                    print(f"[CASCADE] Falling back to {label} ({fallback['id']}) — waiting {wait}s...")
                    
                    if wait > 0:
                        await asyncio.sleep(wait)
                    
                    try:
                        fallback_body = body.copy()
                        fallback_body["model"] = fallback["id"]
                        
                        async with httpx.AsyncClient(timeout=60) as retry_client:
                            retry_resp = await retry_client.post(
                                INFERENCE_URL,
                                headers={"Authorization": f"Bearer {os.environ.get('GROQ_API_KEY')}"},
                                json=fallback_body
                            )
                            if retry_resp.status_code == 200:
                                data = retry_resp.json()
                                print(f"[CASCADE] ✅ {label} succeeded!")
                                cascade_success = True
                                break
                            elif retry_resp.status_code == 429:
                                print(f"[CASCADE] {label} also rate limited, trying next...")
                                continue
                            else:
                                print(f"[CASCADE] {label} failed: {retry_resp.status_code}")
                                continue
                    except Exception as e:
                        print(f"[CASCADE] {label} error: {e}")
                        continue
                
                if not cascade_success:
                    # Signal rate limit to caller — it will handle silent retry
                    print(f"[CASCADE] All models rate limited. Queuing for background retry.")
                    if return_processing_result:
                        return ("__RATE_LIMITED__", {"body": body, "system_msg": system_msg, "history": history})
                    return "__RATE_LIMITED__"
            else:
                print(f"[ERROR] API error: {data}")
                error_msg = "Hmm, I'm having trouble thinking right now. Try again?"
                if return_processing_result:
                    return (error_msg, None)
                return error_msg
        
        # Extract response
        try:
            choices = data.get("choices")
            if choices:
                msg = choices[0].get("message") or {}
                text = str(msg.get("content", "")).strip()
            else:
                text = str(data)
        except Exception:
            text = str(data)
        
        response_text = text.strip() if text else ""
        
        # Strip roleplay markers (*actions*, (narration))
        response_text = strip_roleplay_markers(response_text)
        
        # Detect repetition loops (model degeneration)
        response_text = _detect_and_fix_repetition(response_text)
        
        # Validate response - if empty after roleplay stripping, retry with explicit instruction
        if not response_text or len(response_text) < 2:
            print(f"[WARNING] Empty or invalid response from LLM (likely stripped roleplay). Retrying...")
            print(f"[WARNING] System message length: {len(system_msg)}, History: {len(history)}")
            # Retry once with explicit no-roleplay instruction
            try:
                retry_history = history.copy()
                retry_history.append({"role": "assistant", "content": text})  # Show what it tried
                retry_history.append({"role": "user", "content": "(System: your previous response was empty after processing. Reply with actual dialogue, no *actions* or *italics*. Just speak normally.)"})
                async with httpx.AsyncClient(timeout=30) as retry_client:
                    retry_resp = await retry_client.post(
                        INFERENCE_URL,
                        headers={"Authorization": f"Bearer {os.environ.get('GROQ_API_KEY')}"},
                        json={
                            "model": MODEL_ID,
                            "messages": [{"role": "system", "content": system_msg}] + retry_history,
                            "max_tokens": max_tokens,
                            "temperature": temperature,
                        }
                    )
                    if retry_resp.status_code == 200:
                        retry_data = retry_resp.json()
                        retry_text = retry_data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
                        retry_text = strip_roleplay_markers(retry_text)
                        if retry_text and len(retry_text) >= 2:
                            response_text = retry_text
                            print(f"[DEBUG] Retry succeeded: {response_text[:50]}")
                        else:
                            response_text = "Hm."
                            print(f"[DEBUG] Retry also empty, using minimal fallback")
            except Exception as retry_err:
                print(f"[WARNING] Retry failed: {retry_err}")
                response_text = "Hm."
    except asyncio.TimeoutError:
        print(f"[ERROR] LLM API call timed out")
        error_msg = "⚠️ AI is taking too long to respond. Please try again."
        if return_processing_result:
            return (error_msg, None)
        return error_msg
    except Exception as exc:
        print(f"[ERROR] Error calling AI: {type(exc).__name__}: {exc}")
        error_msg = f"⚠️ Error calling AI: {type(exc).__name__}"
        if return_processing_result:
            return (error_msg, None)
        return error_msg
    
    # Verify response doesn't hallucinate memories (CRITICAL)
    # Ensure response_text is defined before using it
    if response_text and has_no_history:
        # Check for hallucinated memory references
        hallucination_phrases = [
            "last time", "last conversation", "we talked", "we discussed", "remember when",
            "as we", "like we", "before", "earlier", "previously", "the other day",
            "yesterday", "last week", "since we", "our conversation", "we've been",
            "we had", "we've had", "missed you", "great to see you again", "welcome back"
        ]
        response_lower = response_text.lower()
        hallucinated = [phrase for phrase in hallucination_phrases if phrase in response_lower]
        
        if hallucinated:
            print(f"[WARNING] Response contains hallucinated memory references: {hallucinated}")
            print(f"[WARNING] Response: {response_text}")
            # For now, just log it - in production, would regenerate or filter
    
    # Buffer exchanges for batched self-fact extraction (every 5 messages)
    if response_text and core:
        buf = core.state.get("_self_fact_buffer", [])
        buf.append({"user": user_message, "rem": response_text})
        core.state["_self_fact_buffer"] = buf
        if len(buf) >= 5:
            asyncio.create_task(_extract_self_facts(core, buf.copy()))
            core.state["_self_fact_buffer"] = []
    
    # Ensure response_text is defined before returning
    if not response_text:
        response_text = "I'm having trouble responding right now. Can you try again?"
    
    # Track AI message time
    try:
        temporal_context = core.state.get("temporal_context", {})
        temporal_context["last_ai_message_time"] = datetime.now(timezone.utc).isoformat()
        core.state["temporal_context"] = temporal_context
        
        # STANCE MEMORY: Store bot's own reaction ONLY when stance CHANGES
        # This gives the AI memory of HOW it felt, not logging every identical stance
        try:
            stance = core.psyche.stance or "neutral"
            engagement_val = core.psyche.engagement
            respect_val = core.psyche.respect
            mood = psyche_state.get("mood", {}) if isinstance(psyche_state, dict) else {}
            anger_val = core.psyche.anger or 0.0
            
            # Track previous stance to detect CHANGES
            prev_stance = core.state.get("_last_stored_stance", "neutral")
            stance_changed = stance != prev_stance
            
            # Only store when stance actually transitions (e.g., open → guarded)
            if stance_changed and stance != "neutral" and response_text and len(response_text) > 3:
                # Build a concise stance description
                stance_parts = [f"Shifted from '{prev_stance}' to '{stance}'."]
                if anger_val > 0.3:
                    stance_parts.append(f"Frustrated (anger={anger_val:.1f}).")
                if engagement_val < 0.3:
                    stance_parts.append("Disengaged, giving minimal effort.")
                elif engagement_val > 0.75:
                    stance_parts.append("Genuinely interested and engaged.")
                if respect_val < 0.35:
                    stance_parts.append("Low respect for this person.")
                
                stance_summary = " ".join(stance_parts)
                response_snippet = response_text[:60] + ("..." if len(response_text) > 60 else "")
                full_stance = f"{stance_summary} I said: \"{response_snippet}\""
                
                core.memory.add_episodic(
                    event_type="own_reaction",
                    content=full_stance[:250],
                    emotional_valence=mood.get("happiness", 0.5) - 0.5,
                    relational_impact=0.4,
                )
                core.state["_last_stored_stance"] = stance
                print(f"[STANCE MEMORY] Stored transition: {prev_stance} → {stance}")
            elif stance_changed:
                # Still track the change even if we don't store it
                core.state["_last_stored_stance"] = stance
        except Exception as e:
            print(f"[WARNING] Stance memory storage failed (non-critical): {e}")
        
        core._save_state()
    except Exception:
        pass
    
    # relationship_phase and is_truly_new are already defined earlier in the function (line 174, 186)
    print(f"[DEBUG] Final response length: {len(response_text)} chars, phase={relationship_phase}, is_truly_new={is_truly_new}")
    if return_processing_result:
        return (response_text, processing_result)
    return response_text


@bot.event
async def on_ready():
    """Called when bot is ready."""
    print(f'✅ {bot.user} has logged in!')
    print(f'Bot is in {len(bot.guilds)} guilds')
    
    # Start initiative engine background task (guard against reconnects)
    if not check_initiatives.is_running():
        check_initiatives.start()


async def _extract_self_facts(core, exchanges: list):
    """
    Background task: scan a batch of 5 exchanges for personal claims
    REM made about herself. Strict extraction — only facts she explicitly stated.
    Categorized into: favorites, experiences, preferences.
    """
    import httpx
    from datetime import datetime, timezone
    
    existing = core.state.get("_self_identity", {})
    existing_str = ", ".join(f"{k}: {_fact_value(v)}" for k, v in existing.items()) if existing else "none yet"
    
    # Build conversation excerpt
    convo_lines = []
    for ex in exchanges:
        convo_lines.append(f"User: {ex['user']}")
        convo_lines.append(f"Rem: {ex['rem']}")
    convo_text = "\n".join(convo_lines)
    
    user_facts = core.state.get("_user_facts", {})
    user_facts_str = ", ".join(f"{k}: {_fact_value(v)}" for k, v in user_facts.items()) if user_facts else "none yet"
    
    user_taught = core.state.get("_user_taught_knowledge", {})
    user_taught_str = ", ".join(f"{k}: {_fact_value(v)}" for k, v in user_taught.items()) if user_taught else "none yet"
    
    prompt = f"""Conversation between a user and Rem:

{convo_text}

Already stored about Rem: {existing_str}
Already stored about User: {user_facts_str}
Already stored as taught knowledge: {user_taught_str}

Do FIVE things:

1. Extract facts Rem EXPLICITLY stated about HERSELF (from "Rem:" lines ONLY).
CRITICAL: Read ONLY lines starting with "Rem:". If the User said something, it is NOT Rem's fact.
RULES:
- ONLY from Rem's own words. NEVER extract from User's lines.
- Don't infer unstated facts. Don't assume.
- No boolean facts. No duplicates.
- Categorize: "favorites" (loves), "experiences" (seen/done), "preferences" (habits/opinions)
- KEY NAMING: Keys MUST be descriptive and specific. Use full words.
  GOOD keys: "favorite_ice_cream", "favorite_band", "experience_watched_jjk", "preference_study_habit"
  BAD keys (NEVER use these): "cs", "opinion", "preference_cs", "cramming", "food", "thing"
- If the value would just be one vague word like "cramming" or "programming", SKIP IT. Not a fact.
- WHEN IN DOUBT: return empty {{}}. A wrong fact is worse than no fact.

EXAMPLES OF MISTAKES:
- User says "I need someone to scold me" → DO NOT store as Rem's preference. That's the USER's statement.
- User says "I love rock climbing" → DO NOT store as Rem's favorite. That's the USER's interest.
- Rem says "same here!" about something → Only store if she adds specifics. Generic agreement is NOT a fact.

2. Extract facts the USER shared about THEMSELVES (from "User:" lines only).
RULES: Only PERSONAL facts about the user — their major, job, preferences, interests, experiences.
Don't extract greetings, questions, or commands. No duplicates.
KEY NAMING: Use descriptive keys like "major", "favorite_ice_cream", "commute_time". Never use vague keys like "cs", "opinion", "thing".
If the user said something about a SUBJECT ("cs is mostly programming") — that's their OPINION about the subject, store as user_facts with a clear key like "opinion_on_cs".

3. Identify if they are actively discussing a SPECIFIC topic (movie, show, book, game, person, event).
Only if discussed in depth, not just mentioned. Return null if casual chat.

4. From Rem's stored facts below, pick ONLY the ones relevant to the CURRENT conversation.
Stored facts: {existing_str}
Return their exact keys. If none are relevant, return []. Don't include things just because they exist — only if the conversation actually touches on that topic.

5. Extract KNOWLEDGE the user TAUGHT Rem — things Rem didn't know but the user explained.
This is NOT about the user personally — it's about external knowledge they shared.
EXAMPLES:
- User explains JJK plot → {{"jjk": "shonen anime about cursed energy, Yuji Itadori finds a cursed finger"}}
- User describes a movie → {{"king_richard": "Will Smith movie about Venus and Serena Williams' father"}}
- User explains a concept → {{"cognitive_bias": "mental shortcuts that lead to errors in judgment"}}
NOT user-taught (these are personal facts, put in user_facts):
- "I study CS" → user_facts, NOT taught_knowledge
- "I like rock music" → user_facts, NOT taught_knowledge
Only store if user actually EXPLAINED something, not just mentioned it. No duplicates with existing taught knowledge.

Respond ONLY with JSON:
{{"favorites": {{}}, "experiences": {{}}, "preferences": {{}}, "user_facts": {{"key": "value"}}, "active_topic": "topic or null", "relevant_facts": ["key1", "key2"], "taught_knowledge": {{"topic_key": "what they explained"}}}}"""

    # Scout 17B primary → 8B fallback for better extraction quality
    EXTRACTION_MODELS = ["meta-llama/llama-4-scout-17b-16e-instruct", "llama-3.1-8b-instant"]
    
    try:
        api_key = os.environ.get('GROQ_API_KEY')
        content = None
        
        async with httpx.AsyncClient(timeout=12.0) as client:
            for model_id in EXTRACTION_MODELS:
                try:
                    resp = await client.post(
                        "https://api.groq.com/openai/v1/chat/completions",
                        headers={"Authorization": f"Bearer {api_key}"},
                        json={
                            "model": model_id,
                            "messages": [{"role": "user", "content": prompt}],
                            "max_tokens": 500,
                            "temperature": 0.2,
                        },
                    )
                    
                    if resp.status_code == 200:
                        data = resp.json()
                        content = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
                        if content:
                            print(f"[EXTRACTION] Used model: {model_id}")
                            break
                    else:
                        print(f"[EXTRACTION] {model_id} returned {resp.status_code}, trying fallback...")
                except Exception as e:
                    print(f"[EXTRACTION] {model_id} failed: {e}, trying fallback...")
            
            if not content:
                print("[EXTRACTION] All models failed")
                return
            
            if "```" in content:
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
                content = content.strip()
            
            result = json.loads(content)
            print(f"[EXTRACTION] Parsed result keys: {list(result.keys())}")
            
            # --- Self-fact extraction with cross-validation ---
            existing = core.state.get("_self_identity", {})
            junk_values = {"true", "false", "yes", "no", "none", "n/a", "unknown", "chill", "normal"}
            
            # Build user-line text for cross-validation
            user_lines_text = " ".join(ex["user"].lower() for ex in exchanges)
            
            added = {}
            for category in ["favorites", "experiences", "preferences"]:
                cat_facts = result.get(category, {})
                if not isinstance(cat_facts, dict):
                    continue
                for key, value in cat_facts.items():
                    if not isinstance(value, str) or len(value) < 3:
                        continue
                    if value.lower().strip() in junk_values:
                        continue
                    # Reject garbage keys: too short or vague
                    if len(key) <= 3 or key.lower() in ('cs', 'opinion', 'thing', 'food', 'stuff', 'cramming'):
                        print(f"[SELF-IDENTITY] REJECTED vague key: '{key}: {value}'")
                        continue
                    
                    # Cross-validation: reject if the fact is a LONG phrase (6+ words)
                    # that appears verbatim in user lines — likely misattributed.
                    # Short topic terms (e.g., "anime openings", "Arctic Monkeys") are NOT
                    # rejected since both speakers naturally use the same words.
                    val_lower = value.lower().strip()
                    word_count = len(val_lower.split())
                    if word_count >= 6 and val_lower in user_lines_text:
                        print(f"[SELF-IDENTITY] REJECTED '{key}: {value}' — matches user's words, not Rem's")
                        continue
                    
                    key_lower = key.lower().replace("_", " ")
                    is_dup = False
                    for ek in existing:
                        ek_lower = ek.lower().replace("_", " ")
                        if key_lower in ek_lower or ek_lower in key_lower:
                            is_dup = True
                            break
                        if existing[ek].lower() == value.lower() if isinstance(existing[ek], str) else _fact_value(existing[ek]).lower() == value.lower():
                            is_dup = True
                            break
                    if is_dup:
                        continue
                    storage_key = f"{category[:-1]}_{key}"
                    existing[storage_key] = {"v": value, "t": datetime.now(timezone.utc).isoformat()}
                    added[storage_key] = value
            
            if added:
                core.state["_self_identity"] = existing
                core._save_state()
                print(f"[SELF-IDENTITY] Stored new facts: {added}")
            
            # --- User fact storage ---
            new_user_facts = result.get("user_facts", {})
            if new_user_facts and isinstance(new_user_facts, dict):
                stored_user = core.state.get("_user_facts", {})
                user_added = {}
                for key, value in new_user_facts.items():
                    if not isinstance(value, str) or len(value) < 3:
                        continue
                    if value.lower().strip() in junk_values:
                        continue
                    # Reject garbage keys: too short or too vague
                    if len(key) <= 3 or key.lower() in ('cs', 'opinion', 'thing', 'food', 'stuff', 'it', 'yes', 'no'):
                        print(f"[USER FACTS] REJECTED vague key: '{key}: {value}'")
                        continue
                    # Dedup
                    key_lower = key.lower().replace("_", " ")
                    is_dup = any(
                        key_lower in ek.lower().replace("_", " ") or ek.lower().replace("_", " ") in key_lower
                        or _fact_value(stored_user[ek]).lower() == value.lower()
                        for ek in stored_user
                    )
                    if not is_dup:
                        stored_user[key] = {"v": value, "t": datetime.now(timezone.utc).isoformat()}
                        user_added[key] = value
                
                if user_added:
                    core.state["_user_facts"] = stored_user
                    core._save_state()
                    print(f"[USER FACTS] Learned from user: {user_added}")
            
            # --- Self-identity relevance filtering ---
            relevant_keys = result.get("relevant_facts", [])
            if isinstance(relevant_keys, list):
                core.state["_relevant_self_keys"] = relevant_keys
                if relevant_keys:
                    print(f"[SELF-IDENTITY] Relevant to current convo: {relevant_keys}")
            
            # --- User-taught knowledge storage ---
            taught = result.get("taught_knowledge", {})
            if taught and isinstance(taught, dict):
                stored_taught = core.state.get("_user_taught_knowledge", {})
                taught_added = {}
                for key, value in taught.items():
                    if not isinstance(value, str) or len(value) < 5:
                        continue
                    # Dedup by key or value similarity
                    key_lower = key.lower().replace("_", " ")
                    is_dup = any(
                        key_lower in ek.lower().replace("_", " ") or ek.lower().replace("_", " ") in key_lower
                        or _fact_value(stored_taught[ek]).lower() == value.lower()
                        for ek in stored_taught
                    )
                    if not is_dup:
                        stored_taught[key] = {"v": value, "t": datetime.now(timezone.utc).isoformat()}
                        taught_added[key] = value
                
                if taught_added:
                    core.state["_user_taught_knowledge"] = stored_taught
                    core._save_state()
                    print(f"[TAUGHT KNOWLEDGE] User taught Rem: {taught_added}")
            
            # --- Topic detection ---
            # NOTE: This runs AFTER self-fact storage above, so if REM just
            # revealed she knows about a topic in this batch ("oh yeah I watched HP"),
            # the experience_ is already stored and the check below will find it.
            active_topic = result.get("active_topic")
            if active_topic and isinstance(active_topic, str) and active_topic.lower() not in ("null", "none", ""):
                current_ctx = core.state.get("_topic_context", {})
                if current_ctx.get("topic", "").lower() != active_topic.lower():
                    # Check self-identity (already updated with this batch's new facts)
                    identity = core.state.get("_self_identity", {})
                    topic_lower = active_topic.lower()
                    rem_knows = any(
                        topic_lower in _fact_value(v).lower() or _fact_value(v).lower() in topic_lower
                        for k, v in identity.items()
                        if k.startswith("experience_") or k.startswith("favorite_")
                    )
                    
                    if rem_knows:
                        print(f"[TOPIC CONTEXT] REM knows '{active_topic}' — loading facts")
                        asyncio.create_task(_load_topic_context(core, active_topic))
                    else:
                        # Track topic but don't search — she doesn't know it
                        print(f"[TOPIC CONTEXT] Topic '{active_topic}' detected, REM doesn't know it — no search")
                        core.state["_topic_context"] = {"topic": active_topic, "facts": [], "loaded_at": ""}
            elif not active_topic or active_topic in ("null", "None", "none"):
                # No specific topic — clear old context if stale
                current_ctx = core.state.get("_topic_context", {})
                if current_ctx:
                    loaded_at = current_ctx.get("loaded_at", "")
                    if loaded_at:
                        from datetime import datetime, timezone
                        try:
                            loaded_time = datetime.fromisoformat(loaded_at.replace("Z", "+00:00"))
                            age_minutes = (datetime.now(timezone.utc) - loaded_time).total_seconds() / 60
                            if age_minutes > 30:
                                core.state["_topic_context"] = {}
                                print(f"[TOPIC CONTEXT] Cleared stale context (>{age_minutes:.0f}min)")
                        except Exception:
                            pass
                
    except Exception as e:
        print(f"[EXTRACTION ERROR] {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()


async def _load_topic_context(core, topic: str):
    """
    Background task: search Tavily for basic facts about a topic
    and store as ephemeral context for the prompt.
    """
    try:
        from .knowledge_grounding import search_web
        
        query = f"{topic} summary characters plot key facts"
        results = await search_web(query, max_results=3)
        
        if not results:
            print(f"[TOPIC CONTEXT] No results for: {topic}")
            return
        
        # Extract key facts from search results
        facts = []
        for r in results[:3]:
            snippet = r.get("content", r.get("body", ""))
            if snippet:
                # Take first 200 chars of each result
                facts.append(snippet[:200].strip())
        
        if facts:
            from datetime import datetime, timezone
            core.state["_topic_context"] = {
                "topic": topic,
                "facts": facts[:5],
                "loaded_at": datetime.now(timezone.utc).isoformat(),
            }
            core._save_state()
            print(f"[TOPIC CONTEXT] Loaded {len(facts)} facts for: {topic}")
    
    except Exception as e:
        print(f"[TOPIC CONTEXT] Failed to load context for {topic}: {e}")


async def _silent_retry(message: discord.Message, rate_limit_data: Dict[str, Any]):
    """
    Background task: silently retry LLM call when all models were rate limited.
    When one succeeds, send the response naturally — no error, just a delayed reply.
    Like a real person who was busy and responds later.
    """
    body = rate_limit_data.get("body", {})
    if not body:
        return
    
    max_attempts = 10  # 10 attempts × 60s = ~10 min max wait
    
    for attempt in range(1, max_attempts + 1):
        # Wait 60 seconds between attempts
        await asyncio.sleep(60)
        
        print(f"[SILENT RETRY] Attempt {attempt}/{max_attempts}")
        
        for model in MODEL_CASCADE:
            try:
                retry_body = body.copy()
                retry_body["model"] = model["id"]
                
                async with httpx.AsyncClient(timeout=60) as client:
                    resp = await client.post(
                        INFERENCE_URL,
                        headers={"Authorization": f"Bearer {os.environ.get('GROQ_API_KEY')}"},
                        json=retry_body
                    )
                    
                    if resp.status_code == 200:
                        data = resp.json()
                        choices = data.get("choices", [])
                        if choices:
                            text = choices[0].get("message", {}).get("content", "").strip()
                            if text:
                                print(f"[SILENT RETRY] ✅ {model['label']} succeeded after {attempt} min!")
                                await message.channel.send(text)
                                return
                    elif resp.status_code == 429:
                        continue  # Try next model
                    
            except Exception as e:
                print(f"[SILENT RETRY] {model['label']} error: {e}")
                continue
    
    # After 10 minutes of failures, give up silently
    print(f"[SILENT RETRY] Gave up after {max_attempts} attempts. Message lost.")


@bot.event
async def on_message(message: discord.Message):
    """Handle incoming messages."""
    # Ignore bot's own messages
    if message.author == bot.user:
        return
    
    # Only respond to DMs or mentions
    if isinstance(message.channel, discord.DMChannel):
        # DM - always respond
        await handle_dm(message)
    elif bot.user.mentioned_in(message):
        # Mentioned in channel - respond
        await handle_mention(message)
    else:
        # Process commands
        await bot.process_commands(message)


async def handle_dm(message: discord.Message):
    """Handle direct messages."""
    user_id = str(message.author.id)
    user_message = message.content
    
    # Get cognitive core
    core = get_cognitive_core(user_id)
    
    # CRITICAL: Fetch actual message history from Discord channel
    # This gives the bot context of the conversation
    message_history = []
    try:
        # Get last 24 messages from the DM channel (excludes current)
        async for msg in message.channel.history(limit=15):
            if msg.id == message.id:
                continue  # Skip current message, we'll add it last
            role = "assistant" if msg.author.id == bot.user.id else "user"
            message_history.append({
                "role": role,
                "content": msg.content
            })
        # Reverse to get chronological order (oldest first)
        message_history = message_history[::-1]
    except Exception as e:
        print(f"[WARNING] Could not fetch message history: {e}")
        message_history = []
    
    # Add current message at the end
    message_history.append({"role": "user", "content": user_message})
    
    print(f"[DEBUG] Message history: {len(message_history)} messages")
    
    # Stage 15: Message Delivery - Typing simulation, delays, burst sequencing
    try:
        # Generate response (get both response and processing result)
        response, processing_result = await asyncio.wait_for(
            generate_response(core, user_message, message_history, return_processing_result=True),
            timeout=60.0  # 60 second total timeout
        )
        
        if not response:
            await message.channel.send("I'm having trouble responding right now. Please try again.")
            return
        
        # Handle rate limit — silent background retry
        if response == "__RATE_LIMITED__":
            print(f"[SILENT RETRY] Queuing background retry for {message.author}")
            asyncio.create_task(_silent_retry(message, processing_result))
            return  # No error message sent — REM just goes quiet
        
        if not processing_result:
            # Fallback if processing failed
            await message.channel.send(response)
            return
        
        # Get message plan for burst sequencing
        message_plan = processing_result.get("message_plan")
        embodiment_state = processing_result.get("embodiment_state", {})
        energy = embodiment_state.get("E_daily", 0.5)
        
        # Calculate typing time based on message length and energy
        typing_time = core.message_planner.calculate_typing_time(response, 45.0, energy)  # 45 WPM base
        
        # Schedule-aware "read delay" — if REM is busy, she takes longer to even see the message
        schedule_data = core.state.get("_daily_schedule", {})
        current_activity = ""
        if schedule_data.get("schedule"):
            from .daily_life import get_current_activity
            current_activity = get_current_activity(core.state).lower()
        
        busy_keywords = ["college", "class", "lecture", "out", "errand", "store", "commute", "bus", "traveling", "heading"]
        is_busy = any(kw in current_activity for kw in busy_keywords)
        
        if is_busy:
            # Busy — takes 2-5 seconds to even check the message
            import random
            pre_delay = random.uniform(2.0, 5.0)
            await asyncio.sleep(pre_delay)
        
        # Show typing indicator for calculated typing time (realistic human typing)
        async with message.channel.typing():
            await asyncio.sleep(min(typing_time, 5.0))  # Cap at 5 seconds for typing indicator
        
        # Send response
        await message.channel.send(response)
        
        # If message plan indicates burst pattern, send additional messages with delays
        if message_plan and message_plan.get("message_count", 1) > 1:
            inter_delays = message_plan.get("inter_delays", [])
            # For burst messages, we'd split the response and send with delays
            # For now, single message (burst can be enhanced to split response intelligently)
    except asyncio.TimeoutError:
        await message.channel.send("⚠️ I'm taking too long to respond. Please try a shorter message or try again later.")
    except Exception as e:
        print(f"[ERROR] Error in handle_dm: {e}")
        import traceback
        traceback.print_exc()
        try:
            # Provide more helpful error message
            error_msg = f"⚠️ I encountered an error: {type(e).__name__}. Please try again or use !reset if the issue persists."
            await message.channel.send(error_msg)
        except:
            pass


async def handle_mention(message: discord.Message):
    """Handle mentions in channels."""
    user_id = str(message.author.id)
    # Remove mention from message - safely handle bot.user
    if bot.user:
        user_message = message.content.replace(f"<@!{bot.user.id}>", "").replace(f"<@{bot.user.id}>", "").strip()
    else:
        # Fallback if bot.user is not available
        user_message = message.content.strip()
    
    if not user_message:
        await message.channel.send("Hey! What's up?")
        return
    
    # Get cognitive core
    core = get_cognitive_core(user_id)
    
    # CRITICAL: Fetch actual message history from Discord channel
    message_history = []
    try:
        async for msg in message.channel.history(limit=15):
            if msg.id == message.id:
                continue
            # Only include messages involving the bot or from this user
            if msg.author.id == bot.user.id or msg.author.id == message.author.id:
                role = "assistant" if msg.author.id == bot.user.id else "user"
                # Clean mentions from content
                content = msg.content.replace(f"<@!{bot.user.id}>", "").replace(f"<@{bot.user.id}>", "").strip()
                if content:
                    message_history.append({"role": role, "content": content})
        message_history = message_history[::-1]  # Reverse to chronological order
    except Exception as e:
        print(f"[WARNING] Could not fetch message history: {e}")
        message_history = []
    
    # Add current message
    message_history.append({"role": "user", "content": user_message})
    print(f"[DEBUG] Channel message history: {len(message_history)} messages")
    
    # Stage 15: Message Delivery - Typing simulation, delays, burst sequencing
    try:
        # Generate response (get both response and processing result)
        response, processing_result = await asyncio.wait_for(
            generate_response(core, user_message, message_history, return_processing_result=True),
            timeout=60.0
        )
        
        if not response:
            await message.channel.send("I'm having trouble responding right now. Please try again.")
            return
        
        if not processing_result:
            # Fallback if processing failed
            await message.channel.send(response)
            return
        
        # Get message plan for burst sequencing
        message_plan = processing_result.get("message_plan")
        embodiment_state = processing_result.get("embodiment_state", {})
        energy = embodiment_state.get("E_daily", 0.5)
        
        # Calculate typing time based on message length and energy
        typing_time = core.message_planner.calculate_typing_time(response, 45.0, energy)  # 45 WPM base
        
        # Show typing indicator for calculated typing time (realistic human typing)
        async with message.channel.typing():
            await asyncio.sleep(min(typing_time, 5.0))  # Cap at 5 seconds for typing indicator
        
        # Send response
        await message.channel.send(response)
        
        # If message plan indicates burst pattern, send additional messages with delays
        if message_plan and message_plan.get("message_count", 1) > 1:
            inter_delays = message_plan.get("inter_delays", [])
            # For burst messages, we'd split the response and send with delays
            # For now, single message (burst can be enhanced to split response intelligently)
    except asyncio.TimeoutError:
        await message.channel.send("⚠️ I'm taking too long to respond. Please try a shorter message or try again later.")
    except Exception as e:
        print(f"[ERROR] Error in handle_mention: {e}")
        import traceback
        traceback.print_exc()
        try:
            # Provide more helpful error message
            error_msg = f"⚠️ I encountered an error: {type(e).__name__}. Please try again or use !reset if the issue persists."
            await message.channel.send(error_msg)
        except:
            pass


@bot.command(name='state')
async def show_state(ctx: commands.Context):
    """Show current cognitive state (for debugging)."""
    user_id = str(ctx.author.id)
    core = get_cognitive_core(user_id)
    
    snapshot = core.get_state_snapshot()
    psyche = snapshot["psyche_summary"]
    
    embed = discord.Embed(title="🧠 Cognitive State", color=0x00ff00)
    embed.add_field(name="Trust", value=f"{psyche['trust']:.2f}", inline=True)
    embed.add_field(name="Hurt", value=f"{psyche['hurt']:.2f}", inline=True)
    embed.add_field(name="Forgiveness", value=psyche['forgiveness_state'], inline=True)
    
    mood = psyche.get('mood', {})
    embed.add_field(name="Happiness", value=f"{mood.get('happiness', 0):.2f}", inline=True)
    embed.add_field(name="Stress", value=f"{mood.get('stress', 0):.2f}", inline=True)
    embed.add_field(name="Affection", value=f"{mood.get('affection', 0):.2f}", inline=True)
    embed.add_field(name="Anger", value=f"{mood.get('anger', 0):.2f}", inline=True)
    
    neurochem = psyche.get('neurochem', {})
    embed.add_field(name="DA", value=f"{neurochem.get('da', 0):.2f}", inline=True)
    embed.add_field(name="CORT", value=f"{neurochem.get('cort', 0):.2f}", inline=True)
    embed.add_field(name="OXY", value=f"{neurochem.get('oxy', 0):.2f}", inline=True)
    
    memory_summary = snapshot["memory_summary"]
    embed.add_field(name="STM", value=memory_summary["stm_count"], inline=True)
    embed.add_field(name="Episodic", value=memory_summary["episodic_count"], inline=True)
    embed.add_field(name="Identity", value=memory_summary["identity_count"], inline=True)
    
    await ctx.send(embed=embed)


@bot.command(name='memory')
async def show_memory(ctx: commands.Context):
    """Show recent memories."""
    user_id = str(ctx.author.id)
    core = get_cognitive_core(user_id)
    
    # Get memories
    stm = core.memory.get_stm(decay=False)
    episodic = core.memory.get_episodic(min_salience=0.1)
    identity = core.memory.get_identity()

    # Sort by timestamp (newest last) for stable display
    def _ts(m):
        return m.get("timestamp", "")
    episodic_sorted = sorted(episodic, key=_ts)
    stm_sorted = sorted(stm, key=_ts)
    identity_sorted = identity
    
    embed = discord.Embed(title="💭 Memories", color=0x00ffff)
    
    # Separate STM into summaries and raw entries
    stm_summaries = [m for m in stm_sorted if m.get('content', '').startswith('[Summary of')]
    
    # Show LLM-generated conversation summaries (from STM summarization)
    if stm_summaries:
        import re as _re_mem
        def _strip_prefix(c):
            return _re_mem.sub(r'^\[Summary of \d+ messages\]\s*', '', c).strip()
        summ_text = "\n".join([f"- {_strip_prefix(m.get('content', ''))[:120]}" for m in stm_summaries[-3:]])
        embed.add_field(name="📝 Conversation Summaries", value=summ_text[:1024], inline=False)
    
    # Show conversation context from reflection system
    convo_context = core.personality_evolution.conversation_summary
    if convo_context and isinstance(convo_context, str) and len(convo_context) > 5:
        embed.add_field(name="🧠 Current Context", value=convo_context[:1024], inline=False)
    
    # Episodic memories — group by type, deduplicated display
    # Thread summaries from reflections (significant_moment, reflection_thread, consolidated_memory)
    thread_types = {"significant_moment", "reflection_thread", "consolidated_memory"}
    thread_eps = [m for m in episodic_sorted if m.get("event_type") in thread_types]
    if thread_eps:
        # Deduplicate similar content for display
        seen_content = set()
        unique_threads = []
        for m in thread_eps:
            content_key = m.get('content', '')[:60].lower().strip()
            if content_key not in seen_content:
                seen_content.add(content_key)
                unique_threads.append(m)
        ep_text = "\n".join([f"- {m.get('content', '')[:200]}" for m in unique_threads[-5:]])
        embed.add_field(name="📖 Episodic Memories", value=ep_text[:1024], inline=False)
    
    # Own reactions (stance memories) — only show transitions
    reaction_eps = [m for m in episodic_sorted if m.get("event_type") == "own_reaction"]
    if reaction_eps:
        react_text = "\n".join([f"- {m.get('content', '')[:150]}" for m in reaction_eps[-3:]])
        embed.add_field(name="🪞 My Reactions", value=react_text[:1024], inline=False)
    
    # Split identity into real identity facts vs knowledge facts
    real_identity = [m for m in identity_sorted if not m.get('fact', '').startswith('[knowledge]')]
    
    if real_identity:
        id_text = "\n".join([f"- {m.get('fact', '')}" for m in real_identity[-5:]])
        embed.add_field(name="🆔 Identity", value=id_text[:1024], inline=False)
    
    # Show learned facts from the new learned_facts memory tier
    learned = core.memory.get_learned_facts()
    if learned:
        kn_text = "\n".join([f"- {m.get('fact', '')[:120]}" for m in learned[-5:]])
        embed.add_field(name="📚 Learned Knowledge", value=kn_text[:1024], inline=False)
    
    # Status: show what needs more messages to populate
    missing = []
    if not stm_summaries and not convo_context:
        missing.append("📝 Conversation summaries (need 10+ messages)")
    if not thread_eps:
        missing.append("📖 Episodic memories (need 20+ messages for consolidation)")
    if not real_identity:
        missing.append("🆔 Identity facts (need 20+ messages for extraction)")
    
    if missing:
        embed.add_field(name="⏳ Pending", value="\n".join(missing), inline=False)
    
    if not stm_sorted and not episodic_sorted and not identity_sorted:
        embed.description = "No memories yet. Start chatting!"
    
    await ctx.send(embed=embed)


@bot.command(name='reset')
async def reset_state(ctx: commands.Context):
    """Reset cognitive state (for testing)."""
    user_id = str(ctx.author.id)
    db_user_id = f"discord_{user_id}"  # Match the format used in get_cognitive_core
    
    # Remove from cache
    if user_id in active_cores:
        del active_cores[user_id]
    
    # Actually delete the state from database to force full reset
    from backend.state import StateOrchestrator
    import sqlite3
    state_orch = StateOrchestrator()
    
    # Delete state from database
    with sqlite3.connect(state_orch.db_path) as conn:
        conn.execute("DELETE FROM user_state WHERE user_id = ?", (db_user_id,))
        conn.commit()
    
    # Reinitialize with fresh state
    core = get_cognitive_core(user_id)
    
    await ctx.send("✅ State completely reset! Starting fresh in Discovery phase.")


@bot.command(name='debug')
async def show_debug(ctx: commands.Context):
    """Show full debug info - phase, time, all cognitive features."""
    user_id = str(ctx.author.id)
    core = get_cognitive_core(user_id)
    
    snapshot = core.get_state_snapshot()
    psyche = snapshot["psyche_summary"]
    memory_summary = snapshot["memory_summary"]
    
    # Get temporal context
    temporal = await core._get_temporal_context()
    
    # Build debug output
    embed = discord.Embed(title="🔧 Full Debug Info", color=0xff6600)
    
    # Phase info
    phase = core.relationship_phases.current_phase
    phase_confidence = psyche.get('phase_confidence', 0.3)
    embed.add_field(name="📍 Relationship Phase", value=f"{phase} (confidence: {phase_confidence:.2f})", inline=False)
    
    # Time info
    current_time = temporal.get("current_time", "unknown")
    time_of_day = temporal.get("time_of_day", "unknown")
    gap_hours = temporal.get("gap_hours", 0)
    embed.add_field(name="⏰ Time Context", value=f"Time: {current_time}\nPeriod: {time_of_day}\nGap since last msg: {gap_hours:.1f}h", inline=False)
    
    # Memory counts
    stm = core.memory.get_stm(decay=False)
    episodic = core.memory.get_episodic(min_salience=0.1)
    identity = core.memory.get_identity(min_confidence=0.5)
    embed.add_field(name="🧠 Memory Counts", value=f"STM: {len(stm)}\nEpisodic: {len(episodic)}\nIdentity: {len(identity)}", inline=True)
    
    # Psyche state
    embed.add_field(name="💜 Psyche", value=f"Trust: {psyche['trust']:.2f}\nHurt: {psyche['hurt']:.2f}\nAffection: {psyche['mood'].get('affection', 0):.2f}", inline=True)
    
    # Neurochemicals
    neurochem = psyche.get('neurochem', {})
    embed.add_field(name="🧪 Neurochemicals", value=f"DA: {neurochem.get('da', 0.5):.2f}\nCORT: {neurochem.get('cort', 0.3):.2f}\nOXY: {neurochem.get('oxy', 0.5):.2f}", inline=True)
    
    # Conflict state
    conflict_stage = core.conflict_lifecycle.current_stage
    embed.add_field(name="⚡ Conflict Stage", value=conflict_stage, inline=True)
    
    # Embodiment
    embodiment = core.embodiment.get_embodiment_state()
    embed.add_field(name="🔋 Energy", value=f"Daily: {embodiment.get('E_daily', 0.5):.2f}\nCapacity: {embodiment.get('capacity', 0.3):.2f}", inline=True)
    
    await ctx.send(embed=embed)


@bot.command(name='phase')
async def show_phase(ctx: commands.Context):
    """Show current relationship phase details and emotional state."""
    user_id = str(ctx.author.id)
    core = get_cognitive_core(user_id)
    
    phase = core.relationship_phases.current_phase
    psyche = core.psyche.get_psyche_summary()
    trust = psyche.get("trust", 0.3)
    hurt = psyche.get("hurt", 0.0)
    respect = core.psyche.respect
    engagement = core.psyche.engagement
    entitlement = core.psyche.entitlement_debt
    anger = core.psyche.anger
    disgust = core.psyche.disgust
    stance = core.psyche.stance
    posture = core.psyche.posture
    user_evaluation = core.personality_evolution.get_user_evaluation()
    conversation_context = core.personality_evolution.get_conversation_context()
    
    # Phase progression info
    phases = ["Discovery", "Building", "Steady", "Deep"]
    phase_thresholds = {"Building": 0.5, "Steady": 0.7, "Deep": 0.85}
    
    # Determine phase color based on state
    if phase == "Volatile" or disgust > 0.5 or anger > 0.5:
        color = 0xff0000  # Red - danger
    elif trust < 0.3 or respect < 0.3:
        color = 0xff6600  # Orange - warning
    elif trust > 0.6 and respect > 0.5:
        color = 0x00ff00  # Green - good
    else:
        color = 0x9900ff  # Purple - neutral
    
    embed = discord.Embed(title="📍 Relationship Status", color=color)
    
    # Current Phase with envelope description
    phase_envelope = core.relationship_phases.get_phase_envelope()
    phase_desc = phase_envelope.get("description", "")
    embed.add_field(name="Current Phase", value=f"**{phase}**\n_{phase_desc}_", inline=False)
    
    # ===== WHAT THE AI THINKS OF YOU =====
    if user_evaluation:
        embed.add_field(name="🧠 What Rem Thinks of You", value=f"_{user_evaluation}_", inline=False)
    else:
        embed.add_field(name="🧠 What Rem Thinks of You", value="_Still forming an opinion..._", inline=False)
    
    # Current behavioral posture
    if posture:
        embed.add_field(name="🎭 Current Behavior", value=f"_{posture[:150]}_", inline=False)
    
    # ===== CORE METRICS =====
    embed.add_field(name="━━━━ Core Metrics ━━━━", value="\u200b", inline=False)
    
    # Trust (hard to build, easy to damage)
    trust_bar = "█" * int(trust * 10) + "░" * (10 - int(trust * 10))
    trust_status = "🟢" if trust > 0.6 else "🟡" if trust > 0.3 else "🔴"
    embed.add_field(name=f"{trust_status} Trust", value=f"{trust_bar}\n{trust:.0%}", inline=True)
    
    # Respect (hard to build, easy to damage)
    respect_bar = "█" * int(respect * 10) + "░" * (10 - int(respect * 10))
    respect_status = "🟢" if respect > 0.6 else "🟡" if respect > 0.3 else "🔴"
    embed.add_field(name=f"{respect_status} Respect", value=f"{respect_bar}\n{respect:.0%}", inline=True)
    
    # Engagement
    engagement_bar = "█" * int(engagement * 10) + "░" * (10 - int(engagement * 10))
    engagement_status = "🟢" if engagement > 0.6 else "🟡" if engagement > 0.3 else "🔴"
    embed.add_field(name=f"{engagement_status} Interest", value=f"{engagement_bar}\n{engagement:.0%}", inline=True)
    
    # ===== NEGATIVE METRICS =====
    negative_present = hurt > 0.1 or entitlement > 0.2 or anger > 0.1 or disgust > 0.1
    if negative_present:
        embed.add_field(name="━━━━ Issues ━━━━", value="\u200b", inline=False)
        
        if hurt > 0.1:
            hurt_bar = "█" * int(hurt * 10) + "░" * (10 - int(hurt * 10))
            embed.add_field(name="💔 Hurt", value=f"{hurt_bar}\n{hurt:.0%}", inline=True)
        
        if entitlement > 0.2:
            patience_bar = "█" * int(entitlement * 10) + "░" * (10 - int(entitlement * 10))
            embed.add_field(name="😤 Patience Depleted", value=f"{patience_bar}\n{entitlement:.0%}", inline=True)
        
        if anger > 0.1:
            anger_bar = "█" * int(anger * 10) + "░" * (10 - int(anger * 10))
            embed.add_field(name="😠 Anger", value=f"{anger_bar}\n{anger:.0%}", inline=True)
        
        if disgust > 0.1:
            disgust_bar = "█" * int(disgust * 10) + "░" * (10 - int(disgust * 10))
            embed.add_field(name="🤢 Disgust", value=f"{disgust_bar}\n{disgust:.0%}", inline=True)
    
    # Current Stance
    stance_emoji = {
        "open": "😊", "wary": "🤨", "guarded": "🛡️", "irritated": "😒",
        "bored": "😑", "intrigued": "🤔", "defensive": "😤", "affectionate": "🥰",
        "dismissive": "😒", "curious": "🧐", "amused": "😏", "withdrawn": "😶",
        "cold": "🥶", "disgusted": "🤮", "angry": "😡"
    }.get(stance, "😐")
    embed.add_field(name="Current Stance", value=f"{stance_emoji} {stance.capitalize()}", inline=True)
    
    # ===== PHASE PROGRESSION =====
    embed.add_field(name="━━━━ Progress ━━━━", value="\u200b", inline=False)
    
    if phase in phases and phases.index(phase) < len(phases) - 1:
        next_phase = phases[phases.index(phase) + 1]
        needed_trust = phase_thresholds.get(next_phase, 0.5)
        needed_respect = 0.4 if next_phase == "Building" else 0.5 if next_phase == "Steady" else 0.6
        
        # Calculate overall progress
        trust_progress = min(trust / needed_trust, 1.0) if needed_trust > 0 else 1.0
        respect_progress = min(respect / needed_respect, 1.0) if needed_respect > 0 else 1.0
        hurt_penalty = max(0, 1.0 - hurt * 2)  # Hurt blocks progress
        overall_progress = (trust_progress * 0.5 + respect_progress * 0.3 + hurt_penalty * 0.2)
        
        progress_bar = "█" * int(overall_progress * 10) + "░" * (10 - int(overall_progress * 10))
        
        # What's blocking progress
        blockers = []
        if trust < needed_trust:
            blockers.append(f"Trust: {trust:.0%} → need {needed_trust:.0%}")
        if respect < needed_respect:
            blockers.append(f"Respect: {respect:.0%} → need {needed_respect:.0%}")
        if hurt > 0.2:
            blockers.append(f"Hurt must heal: {hurt:.0%}")
        if entitlement > 0.4:
            blockers.append(f"Patience needs recovery")
        
        blocker_text = "\n• ".join(blockers) if blockers else "On track! Keep up the good conversations."
        if blockers:
            blocker_text = "• " + blocker_text
        
        embed.add_field(name=f"📈 Progress to {next_phase}", value=f"{progress_bar} {overall_progress:.0%}\n{blocker_text}", inline=False)
    elif phase == "Volatile":
        embed.add_field(name="⚠️ Relationship Damaged", value="Trust has been broken. Recovery requires:\n• Consistent, respectful messages\n• Not pushing boundaries\n• Time and patience (trust rebuilds slowly)", inline=False)
    elif phase == "Deep":
        embed.add_field(name="🌟 Maximum Depth", value="You've reached the deepest connection. Don't take it for granted.", inline=False)
    
    # ===== WHY THE AI IS BEHAVING THIS WAY =====
    behavior_explanations = []
    
    if stance == "cold" or stance == "withdrawn":
        behavior_explanations.append("**Cold/Withdrawn**: Something damaged the connection. AI is protecting itself.")
    elif stance == "irritated" or stance == "angry":
        behavior_explanations.append("**Irritated**: Recent interactions have been frustrating.")
    elif stance == "guarded" or stance == "wary":
        behavior_explanations.append("**Guarded**: Not enough trust built yet, or recent behavior was off-putting.")
    elif stance == "bored":
        behavior_explanations.append("**Bored**: Conversation isn't engaging. Try asking about something interesting.")
    elif stance == "dismissive":
        behavior_explanations.append("**Dismissive**: User may be trying too hard or not respecting boundaries.")
    elif stance == "disgusted":
        behavior_explanations.append("**Disgusted**: Something crossed a line. Behavior was inappropriate.")
    
    if respect < 0.3:
        behavior_explanations.append("**Low Respect**: User hasn't earned respect. Expect minimal effort.")
    if engagement < 0.3:
        behavior_explanations.append("**Low Interest**: AI doesn't find the conversation worth investing in.")
    if entitlement > 0.5:
        behavior_explanations.append("**Patience Depleted**: User has been pushy or assumed too much closeness.")
    if hurt > 0.3:
        behavior_explanations.append("**Unhealed Hurt**: Something painful happened. AI is guarded until it's addressed.")
    
    if behavior_explanations:
        embed.add_field(name="💡 Why Rem is Acting This Way", value="\n".join(behavior_explanations), inline=False)
    
    # ===== TIPS FOR IMPROVEMENT =====
    tips = []
    if trust < 0.5:
        tips.append("• Be consistent and respectful over time")
    if respect < 0.4:
        tips.append("• Don't push boundaries or assume familiarity")
    if engagement < 0.4:
        tips.append("• Ask genuine questions, share interesting things")
    if hurt > 0.2:
        tips.append("• Acknowledge if you did something hurtful")
    if entitlement > 0.3:
        tips.append("• Stop pushing for more than what's earned")
    if phase == "Discovery":
        tips.append("• Early stage - earn trust through natural conversation")
    
    if tips:
        embed.add_field(name="📝 How to Improve", value="\n".join(tips[:4]), inline=False)
    
    # ===== RECENT CONTEXT =====
    if conversation_context:
        embed.add_field(name="📋 Recent Context", value=f"_{conversation_context[:200]}_", inline=False)
    
    # Footer with recovery note
    embed.set_footer(text="⚠️ Trust & Respect: Easy to lose, hard to rebuild. Treat this AI like a real person.")
    
    await ctx.send(embed=embed)


@bot.command(name='time')
async def show_time(ctx: commands.Context):
    """Show current time context."""
    user_id = str(ctx.author.id)
    core = get_cognitive_core(user_id)
    
    # Get actual current time from temporal system
    current_time = core.temporal.get_current_time()
    circadian_phase = core.temporal.get_circadian_phase()
    
    # Get time deltas
    temporal_state = core.state.get("temporal_context", {})
    time_deltas = core.temporal.get_time_deltas(temporal_state)
    
    embed = discord.Embed(title="⏰ Time Context", color=0x00ccff)
    embed.add_field(name="Current Time (IST)", value=current_time.strftime("%Y-%m-%d %H:%M:%S"), inline=False)
    embed.add_field(name="Circadian Phase", value=circadian_phase.value, inline=True)
    embed.add_field(name="Gap (hours)", value=f"{time_deltas.get('hours_since_last_user_message', 0):.1f}", inline=True)
    
    # Get behavior modulations
    modulations = core.temporal.modulate_behavior_by_time(circadian_phase, time_deltas)
    embed.add_field(name="Energy Modifier", value=f"{modulations.get('energy_modifier', 1.0):.2f}", inline=True)
    embed.add_field(name="Warmth Modifier", value=f"{modulations.get('warmth_modifier', 1.0):.2f}", inline=True)
    
    await ctx.send(embed=embed)


@bot.command(name='identity')
async def show_identity(ctx: commands.Context):
    """Show stored identity facts about you."""
    user_id = str(ctx.author.id)
    core = get_cognitive_core(user_id)
    
    identity = core.memory.get_identity(min_confidence=0.5)
    
    embed = discord.Embed(title="🪪 Identity Facts", color=0xff9900)
    
    if identity:
        for mem in identity[:10]:
            fact = mem.get('fact', 'Unknown')
            confidence = mem.get('confidence', 0)
            embed.add_field(name=f"📌 {fact}", value=f"Confidence: {confidence:.2f}", inline=False)
    else:
        embed.description = "No identity facts stored yet. Tell me about yourself!"
    
    await ctx.send(embed=embed)


@bot.command(name='complexity')
async def show_complexity(ctx: commands.Context, *, message: str = "hello"):
    """Test complexity evaluation on a message."""
    user_id = str(ctx.author.id)
    core = get_cognitive_core(user_id)
    
    # Run semantic understanding
    context = {
        "psyche_state": core.psyche.get_psyche_summary(),
        "recent_memories": [],
        "emotion": "neutral",
        "emotion_vector": {"valence": 0.0, "arousal": 0.0}
    }
    
    try:
        understanding = await core.semantic_reasoner.understand_message(message, context)
        complexity = understanding.get("complexity", 0.5)
        intent = understanding.get("intent", "unknown")
        sincerity = understanding.get("sincerity", 0.5)
        
        embed = discord.Embed(title="🧮 Complexity Analysis", color=0x00ff99)
        embed.add_field(name="Message", value=message[:100], inline=False)
        embed.add_field(name="Complexity", value=f"{complexity:.2f}", inline=True)
        embed.add_field(name="Intent", value=intent, inline=True)
        embed.add_field(name="Sincerity", value=f"{sincerity:.2f}", inline=True)
        
        # Processing depth explanation
        if complexity < 0.3:
            depth = "Simple - Minimal processing"
        elif complexity < 0.6:
            depth = "Standard - Normal processing"
        elif complexity < 0.8:
            depth = "Complex - Enhanced processing"
        else:
            depth = "Critical - Full QMAS + deep reasoning"
        embed.add_field(name="Processing Depth", value=depth, inline=False)
        
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"Error evaluating complexity: {e}")


@bot.command(name='personality')
async def show_personality(ctx: commands.Context):
    """Show evolved personality traits, quirks, and social state."""
    user_id = str(ctx.author.id)
    core = get_cognitive_core(user_id)
    
    # Get personality evolution state
    pe = core.personality_evolution
    state = pe.get_full_state()
    
    embed = discord.Embed(title="🧠 Who Am I Right Now", color=0x9b59b6)
    
    # ===== How I Speak (personality text from Deep Reflection) =====
    personality_text = state.get("personality_text", "")
    if personality_text:
        embed.add_field(name="🗣️ How I Speak", value=personality_text[:500], inline=False)
    
    # ===== How I See You (LLM's honest user evaluation) =====
    user_eval = pe.user_evaluation
    if user_eval:
        embed.add_field(name="👤 How I See You", value=user_eval[:500], inline=False)
    else:
        embed.add_field(name="👤 How I See You", value="_(Still figuring you out...)_", inline=False)
    
    # ===== Current Mood (descriptive, not numbers) =====
    mood = core.psyche.mood
    mood_parts = []
    h = mood.get("happiness", 0.5)
    s = mood.get("stress", 0.3)
    a = mood.get("affection", 0.5)
    ang = mood.get("anger", 0.1)
    cur = mood.get("curiosity", 0.5)
    sad = mood.get("sadness", 0.2)
    
    if h > 0.65: mood_parts.append("😊 feeling good")
    elif h < 0.3: mood_parts.append("😔 down")
    if s > 0.6: mood_parts.append("😰 stressed")
    if a > 0.65: mood_parts.append("💝 warm towards you")
    elif a < 0.3: mood_parts.append("🧊 emotionally distant")
    if ang > 0.4: mood_parts.append("😤 frustrated")
    if cur > 0.65: mood_parts.append("🔍 curious")
    if sad > 0.5: mood_parts.append("😢 sad")
    
    if not mood_parts:
        mood_parts.append("😐 neutral")
    
    embed.add_field(name="💭 Current Mood", value=", ".join(mood_parts), inline=False)
    
    # ===== Our Relationship (phase + trust + stance) =====
    phase = core.relationship_phases.current_phase
    phase_desc = core.relationship_phases.get_phase_description()
    trust = core.psyche.psyche.get("trust", 0.3)
    stance = core.psyche.stance or "neutral"
    respect = core.psyche.respect
    engagement = core.psyche.engagement
    
    # Human-readable trust
    if trust > 0.75: trust_str = "high — I trust you"
    elif trust > 0.5: trust_str = "growing — you're earning it"
    elif trust > 0.3: trust_str = "cautious — still deciding"
    else: trust_str = "low — I'm guarded"
    
    # Human-readable respect
    if respect > 0.7: respect_str = "high"
    elif respect > 0.4: respect_str = "neutral"
    else: respect_str = "low"
    
    # Human-readable engagement
    if engagement > 0.7: eng_str = "genuinely interested"
    elif engagement > 0.4: eng_str = "moderate"
    else: eng_str = "disengaged"
    
    rel_text = f"**Phase:** {phase}"
    if phase_desc:
        rel_text += f" — {phase_desc}"
    rel_text += f"\n**Trust:** {trust_str}"
    rel_text += f"\n**Stance:** {stance}"
    rel_text += f"\n**Respect:** {respect_str} | **Interest:** {eng_str}"
    
    embed.add_field(name="🤝 Our Relationship", value=rel_text, inline=False)
    
    # ===== Current Posture (behavioral tendencies from Light Reflection) =====
    posture = core.psyche.posture
    if posture:
        embed.add_field(name="🧘 How I'm Acting", value=posture[:300], inline=False)
    
    # ===== What I Remember About You =====
    identity_mems = core.memory.get_identity(min_confidence=0.5)
    episodic_mems = core.memory.get_episodic(min_salience=0.1)
    
    memory_parts = []
    if identity_mems:
        facts = [m.get("fact", "") for m in identity_mems[:5] if m.get("fact")]
        if facts:
            memory_parts.append("**Facts:** " + "; ".join(facts))
    
    if episodic_mems:
        # Show recent significant moments
        recent = sorted(episodic_mems, key=lambda m: m.get("timestamp", ""), reverse=True)[:3]
        moments = [m.get("content", "")[:80] for m in recent if m.get("content")]
        if moments:
            memory_parts.append("**Recent moments:**\n" + "\n".join([f"• {m}" for m in moments]))
    
    if memory_parts:
        embed.add_field(name="📝 What I Remember", value="\n".join(memory_parts)[:1024], inline=False)
    else:
        embed.add_field(name="📝 What I Remember", value="_(Nothing yet — keep talking)_", inline=False)
    
    # ===== Quirks =====
    quirks = state.get("quirks", [])
    if quirks:
        embed.add_field(name="✨ Quirks", value="\n".join([f"• {q}" for q in quirks])[:500], inline=False)
    
    # ===== Conversation Summary =====
    summary = pe.conversation_summary
    if summary:
        embed.add_field(name="💬 Latest Topic", value=summary[:300], inline=False)
    
    # ===== Reflection countdown (compact) =====
    light_until = state.get("messages_until_light", 0)
    deep_until = state.get("messages_until_deep", 0)
    embed.set_footer(text=f"Interactions: {state['interaction_count']} | Light reflect in {light_until} msgs | Deep reflect in {deep_until} msgs")
    
    await ctx.send(embed=embed)


@bot.command(name='info')
async def show_enhanced_info(ctx: commands.Context):
    """Show internal metrics — developer view of all cognitive systems."""
    user_id = str(ctx.author.id)
    core = get_cognitive_core(user_id)
    
    embed = discord.Embed(title="🔧 Internal Metrics", color=0x3498db)
    
    # ===== Personality Traits (raw numbers for dev use) =====
    traits = core.personality_evolution.traits
    traits_str = "\n".join([f"{k:>14}: {v:.2f}" for k, v in traits.items()])
    embed.add_field(name="📊 Traits", value=f"```\n{traits_str}\n```", inline=True)
    
    # ===== Neurochemicals =====
    psyche = core.psyche.get_psyche_summary()
    neurochem = psyche.get("neurochem", {})
    nchem_str = f"DA:   {neurochem.get('da', 0.5):.2f}\nCORT: {neurochem.get('cort', 0.3):.2f}\nOXY:  {neurochem.get('oxy', 0.5):.2f}\nSER:  {neurochem.get('ser', 0.5):.2f}\nENDO: {neurochem.get('endo', 0.5):.2f}"
    embed.add_field(name="🧪 Neurochemicals", value=f"```\n{nchem_str}\n```", inline=True)
    
    # ===== Mood Vector (raw) =====
    mood = core.psyche.mood
    mood_str = "\n".join([f"{k:>12}: {v:.2f}" for k, v in mood.items() if abs(v - 0.5) > 0.05 or k in ("happiness", "stress")])
    if not mood_str:
        mood_str = "All near baseline (0.50)"
    embed.add_field(name="🎭 Mood Vector", value=f"```\n{mood_str}\n```", inline=True)
    
    # ===== Social State (raw) =====
    social = f"Trust: {psyche.get('trust', 0.3):.2f}\nHurt: {psyche.get('hurt', 0):.2f}\nStance: {core.psyche.stance}\nRespect: {core.psyche.respect:.2f}\nEngagement: {core.psyche.engagement:.2f}\nPatience: {1.0 - core.psyche.entitlement_debt:.2f}\nAnger: {core.psyche.anger:.2f}\nDisgust: {core.psyche.disgust:.2f}"
    embed.add_field(name="🎯 Social State", value=f"```\n{social}\n```", inline=True)
    
    # ===== Memory Counts =====
    stm = core.memory.get_stm(decay=False)
    episodic = core.memory.get_episodic(min_salience=0.1)
    identity = core.memory.get_identity(min_confidence=0.5)
    own_reactions = [e for e in episodic if e.get("event_type") == "own_reaction"]
    refl_threads = [e for e in episodic if e.get("event_type") == "reflection_thread"]
    
    mem_str = f"STM: {len(stm)}\nEpisodic: {len(episodic)}\n  react: {len(own_reactions)} | threads: {len(refl_threads)}\nIdentity: {len(identity)}"
    embed.add_field(name="🗃️ Memory", value=mem_str, inline=True)
    
    # ===== Reflection + System =====
    ic = core.personality_evolution.interaction_count
    ll = core.personality_evolution.last_light_reflection
    ld = core.personality_evolution.last_deep_reflection
    lu = max(0, 15 - (ic - ll))
    du = max(0, 30 - (ic - ld))
    
    phase = core.relationship_phases.current_phase
    conflict = core.conflict_lifecycle.current_stage
    forgiveness = psyche.get("forgiveness_state", "none")
    
    sys_str = f"Interactions: {ic}\nLight in: {lu} msgs (last: {ll})\nDeep in: {du} msgs (last: {ld})\nPhase: {phase}\nConflict: {conflict}\nForgiveness: {forgiveness}"
    embed.add_field(name="⚙️ System", value=f"```\n{sys_str}\n```", inline=True)
    
    # ===== Embodiment =====
    embed.set_footer(text=f"Energy: {core.embodiment.E_daily:.2f} | Capacity: {core.embodiment.capacity:.2f}")
    
    await ctx.send(embed=embed)


@bot.command(name='sched')
async def show_schedule(ctx: commands.Context):
    """Show REM's daily schedule dashboard."""
    user_id = str(ctx.author.id)
    
    if user_id not in active_cores:
        await ctx.send("No active session. Send a message first.")
        return
    
    core = active_cores[user_id]
    schedule_data = core.state.get("_daily_schedule", {})
    schedule = schedule_data.get("schedule", [])
    overrides = schedule_data.get("overrides", [])
    date = schedule_data.get("date", "unknown")
    generated_at = schedule_data.get("generated_at", "unknown")
    
    if not schedule:
        await ctx.send("📅 No schedule generated yet. Send a message first to trigger it.")
        return
    
    # Get current time for highlighting
    from datetime import timezone, timedelta
    now = datetime.now(timezone(timedelta(hours=5.5)))
    current_time = now.strftime("%H:%M")
    
    embed = discord.Embed(
        title=f"📅 REM's Schedule — {date}",
        description=f"Generated at {generated_at[:16] if len(generated_at) > 16 else generated_at}",
        color=0x00bfff
    )
    
    # Build schedule display
    schedule_lines = []
    for block in schedule:
        start = block.get("start", "??:??")
        end = block.get("end", "??:??")
        activity = block.get("activity", "???")
        
        # Check if this is the current block
        is_current = start <= current_time < end
        # Check if this block has been overridden
        is_overridden = any(
            o.get("start", "") <= start and o.get("end", "") >= end
            for o in overrides
        )
        
        if is_current:
            line = f"▶️ **{start}-{end}**: {activity} ← NOW"
        elif is_overridden:
            line = f"~~{start}-{end}: {activity}~~ (overridden)"
        else:
            line = f"⬜ {start}-{end}: {activity}"
        
        schedule_lines.append(line)
    
    # Split into chunks if too long for embed field
    schedule_text = "\n".join(schedule_lines)
    if len(schedule_text) > 1024:
        mid = len(schedule_lines) // 2
        embed.add_field(
            name="📋 Schedule (1/2)",
            value="\n".join(schedule_lines[:mid]),
            inline=False
        )
        embed.add_field(
            name="📋 Schedule (2/2)",
            value="\n".join(schedule_lines[mid:]),
            inline=False
        )
    else:
        embed.add_field(name="📋 Schedule", value=schedule_text, inline=False)
    
    # Show overrides
    if overrides:
        override_lines = []
        for o in overrides:
            override_lines.append(
                f"🔄 {o.get('start','?')}-{o.get('end','?')}: {o.get('activity','?')}"
            )
        embed.add_field(
            name="🔄 Overrides (user plans)",
            value="\n".join(override_lines),
            inline=False
        )
    
    # Relationship context that gates plan acceptance
    psyche = core.psyche.get_psyche_summary()
    trust = psyche.get("trust", 0.3)
    engagement = core.psyche.engagement
    phase = psyche.get("relationship_phase", "Discovery")
    
    gate_info = f"Trust: {trust:.2f} | Engagement: {engagement:.2f} | Phase: {phase}\n"
    if trust > 0.6 and engagement > 0.5:
        gate_info += "✅ Would likely accept plan requests"
    elif trust > 0.4:
        gate_info += "🤷 Might accept, depends on what it is"
    else:
        gate_info += "❌ Would likely decline — not enough trust/engagement"
    
    embed.add_field(name="🤝 Plan Acceptance", value=gate_info, inline=False)
    
    embed.set_footer(text=f"Current time: {current_time} IST")
    
    await ctx.send(embed=embed)


@bot.command(name='about')
async def show_about_rem(ctx: commands.Context):
    """Show REM's self-identity — base facts + LLM-generated personal facts."""
    user_id = str(ctx.author.id)
    
    if user_id not in active_cores:
        await ctx.send("No active session. Send a message first.")
        return
    
    core = active_cores[user_id]
    
    # Base identity (hardcoded anchors)
    base_facts = {
        "🎓 Occupation": "College student",
        "📚 Major": "Psychology",
        "🏠 Living": "Lives at home",
        "🚌 Commute": "~30 min to college",
    }
    
    # LLM-generated facts (from conversations)
    generated = core.state.get("_self_identity", {})
    
    embed = discord.Embed(
        title="🪪 About R.E.M",
        description="Who she is — base identity + facts she's shared in conversation.",
        color=0xff69b4
    )
    
    # Base facts section
    base_text = "\n".join(f"{emoji} {v}" for emoji, v in base_facts.items())
    embed.add_field(name="📌 Core Identity (fixed)", value=base_text, inline=False)
    
    # Generated facts section — categorized
    if generated:
        # Separate by category prefix
        categories = {
            "favorite": ("❤️ Favorites", []),
            "experience": ("📝 Experienced / Seen", []),
            "preference": ("🎯 Preferences & Opinions", []),
        }
        uncategorized = []
        
        for key, value in generated.items():
            placed = False
            for prefix, (label, items) in categories.items():
                if key.startswith(prefix + "_"):
                    clean_key = key[len(prefix) + 1:].replace("_", " ").title()
                    items.append(f"• **{clean_key}**: {_fact_value(value)}")
                    placed = True
                    break
            if not placed:
                clean_key = key.replace("_", " ").title()
                uncategorized.append(f"• **{clean_key}**: {_fact_value(value)}")
        
        # Display each category
        for prefix, (label, items) in categories.items():
            if items:
                text = "\n".join(items)
                if len(text) > 1024:
                    text = text[:1020] + "..."
                embed.add_field(name=label, value=text, inline=False)
        
        if uncategorized:
            text = "\n".join(uncategorized)
            if len(text) > 1024:
                text = text[:1020] + "..."
            embed.add_field(name="📋 Other", value=text, inline=False)
    else:
        embed.add_field(
            name="✨ Discovered Through Conversation", 
            value="_No personal facts generated yet. Chat more and ask about her preferences, hobbies, etc._", 
            inline=False
        )
    
    # Personality text (current)
    personality_text = core.personality_evolution.personality_text
    if personality_text:
        # Show first 300 chars
        display_text = personality_text[:300] + "..." if len(personality_text) > 300 else personality_text
        embed.add_field(name="🗣️ How She Speaks Right Now", value=display_text, inline=False)
    
    # Quirks
    quirks = core.personality_evolution.quirks
    if quirks:
        quirks_text = ", ".join(quirks[-5:])
        embed.add_field(name="💫 Quirks", value=quirks_text, inline=False)
    
    # User-learned facts (what REM knows about the user)
    user_facts = core.state.get("_user_facts", {})
    if user_facts:
        uf_lines = []
        for key, val in list(user_facts.items())[:10]:
            clean_key = key.replace("_", " ").title()
            uf_lines.append(f"• **{clean_key}**: {_fact_value(val)}")
        uf_text = "\n".join(uf_lines)
        if len(uf_text) > 1024:
            uf_text = uf_text[:1020] + "..."
        embed.add_field(name="👤 What I Know About You", value=uf_text, inline=False)
    
    # User-taught knowledge (things user explained to REM)
    taught = core.state.get("_user_taught_knowledge", {})
    if taught:
        tk_lines = []
        for key, val in list(taught.items())[:8]:
            clean_key = key.replace("_", " ").title()
            v = _fact_value(val)
            tk_lines.append(f"• **{clean_key}**: {v[:80]}{'...' if len(v) > 80 else ''}")
        tk_text = "\n".join(tk_lines)
        if len(tk_text) > 1024:
            tk_text = tk_text[:1020] + "..."
        embed.add_field(name="📚 Things You Taught Me", value=tk_text, inline=False)
    
    # Active topic context
    topic_ctx = core.state.get("_topic_context", {})
    if topic_ctx and topic_ctx.get("topic"):
        topic_name = topic_ctx["topic"]
        has_facts = bool(topic_ctx.get("facts"))
        loaded_at = topic_ctx.get("loaded_at", "")
        
        if has_facts:
            status = f"🔍 **{topic_name}** — searched & loaded ({len(topic_ctx['facts'])} facts)"
        elif loaded_at:
            status = f"📝 **{topic_name}** — searched, no results"
        else:
            status = f"💬 **{topic_name}** — detected, NOT searched (REM doesn't claim to know this)"
        embed.add_field(name="🎯 Active Topic", value=status, inline=False)
    
    # Footer with fact count
    fact_count = len(generated)
    user_fact_count = len(user_facts) if user_facts else 0
    taught_count = len(taught) if taught else 0
    embed.set_footer(text=f"{fact_count} about me | {user_fact_count} about you | {taught_count} taught | Use !reset to clear all")
    
    await ctx.send(embed=embed)


@bot.command(name='commands')
async def show_commands(ctx: commands.Context):
    """Show available commands."""
    embed = discord.Embed(title="🤖 Bot Commands", color=0x0099ff)
    embed.add_field(name="!personality", value="Who am I? Mood, stance, memories, how I see you", inline=False)
    embed.add_field(name="!info", value="Developer metrics — traits, neurochemicals, mood vector, memory counts", inline=False)
    embed.add_field(name="!debug", value="Full debug info (phase, time, memory, psyche)", inline=False)
    embed.add_field(name="!state", value="Show your cognitive state", inline=False)
    embed.add_field(name="!memory", value="Show your memories", inline=False)
    embed.add_field(name="!identity", value="Show stored identity facts about you", inline=False)
    embed.add_field(name="!phase", value="Show relationship phase details", inline=False)
    embed.add_field(name="!time", value="Show time context", inline=False)
    embed.add_field(name="!complexity [msg]", value="Test complexity evaluation on a message", inline=False)
    embed.add_field(name="!reset", value="Reset your state (testing)", inline=False)
    embed.add_field(name="!sched", value="View REM's daily schedule", inline=False)
    embed.add_field(name="!about", value="View REM's self-identity and personal facts", inline=False)
    embed.add_field(name="!commands", value="Show this help", inline=False)
    embed.add_field(name="DM or @mention", value="Chat with the AI companion", inline=False)
    
    await ctx.send(embed=embed)


@tasks.loop(minutes=5)
async def check_initiatives():
    """Check for autonomous messaging opportunities."""
    # Check all active users
    for user_id, core in list(active_cores.items()):
        try:
            # Get initiative score
            psyche_state = core.psyche.get_psyche_summary()
            personality = core.personality.core
            temporal_context = await core._get_temporal_context()
            
            initiative_result = core.initiative_engine.score_initiative(
                psyche_state, personality, core.memory, temporal_context
            )
            
            initiative_score = initiative_result.get("initiative_score", 0.0)
            
            # If score is high enough, send message
            if initiative_score > 0.4:  # Threshold for autonomous messaging
                # Get user from Discord (need to store user objects)
                # For now, skip - would need to store user objects
                pass
                
        except Exception as e:
            print(f"Error checking initiative for {user_id}: {e}")


def run_bot():
    """Run the Discord bot."""
    if not DISCORD_TOKEN:
        print("❌ ERROR: DISCORD_TOKEN environment variable is required")
        print("Get your token from: https://discord.com/developers/applications")
        return
    
    print("🚀 Starting Discord bot...")
    print("Make sure you have:")
    print("  - DISCORD_TOKEN set in environment")
    print("  - GROQ_API_KEY set in environment")
    print("  - Bot has MESSAGE CONTENT INTENT enabled in Discord Developer Portal")
    
    bot.run(DISCORD_TOKEN)


if __name__ == "__main__":
    run_bot()

