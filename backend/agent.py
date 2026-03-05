import os
from typing import Optional, Dict, Any
from datetime import datetime, timezone

import httpx
from .rate_limiter import global_rate_limiter
from fastapi import APIRouter
from pydantic import BaseModel

from .cognitive_core import CognitiveCore
from .human_quirks import HumanQuirks
from .context_manager import get_context_manager

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
HF_TOKEN = GROQ_API_KEY  # Alias for compatibility
# Use Groq API - fast and free
# Using llama-3.1-8b-instant - smaller, faster, separate token limit
MODEL_ID = os.environ.get("MODEL_ID", "llama-3.3-70b-versatile")
INFERENCE_URL = "https://api.groq.com/openai/v1/chat/completions"

router = APIRouter()


class AgentMessage(BaseModel):
    role: str
    content: str


class AgentRequest(BaseModel):
    # Optional initial emotion snapshot to condition tone.
    # Frontend can send this only on the first turn.
    emotion: Optional[str] = None
    valence: Optional[float] = None
    arousal: Optional[float] = None
    stress: Optional[float] = None
    engagement: Optional[float] = None

    # Multi-turn chat history, including the new user message.
    messages: Optional[list[AgentMessage]] = None


class AgentResponse(BaseModel):
    reply: str


def build_prompt(payload: AgentRequest) -> Dict[str, Any]:
    """Build chat-style payload for multi-turn chat.

    Emotion snapshot (if provided) is baked into the *system* message so
    it sets the overall tone of the conversation, but the actual dialog
    history lives in `messages`.
    """

    # Base system prompt describing behavior.
    system_msg = (
        "You are a friendly, conversational AI companion. "
        "You can talk about everyday life, feelings, hobbies, work, and anything else. "
        "You receive rough emotion estimates and use them only to adjust tone "
        "(gentler when low, more upbeat when positive). "
        "Do not sound like a robot. Write 1–4 short paragraphs, natural and concise. "
        "Never claim to be a therapist or give medical advice."
    )

    # If an emotion snapshot is present, append it as context *once*.
    if any(
        v is not None
        for v in (payload.emotion, payload.valence, payload.arousal, payload.stress, payload.engagement)
    ):
        emo_summary = (
            f"Current approximate emotion signal (may be wrong): "
            f"label={payload.emotion or 'unknown'}, "
            f"valence={payload.valence}, arousal={payload.arousal}, "
            f"stress={payload.stress}, engagement={payload.engagement}. "
            "Use this only to adapt your tone; do not restate it every message."
        )
        system_msg = system_msg + "\n" + emo_summary

    history: list[Dict[str, str]] = []
    if payload.messages:
        for m in payload.messages:
            role = "assistant" if m.role == "assistant" else "user"
            history.append({"role": role, "content": m.content})

    if not history:
        # If somehow called with no history, gently start.
        history.append(
            {
                "role": "user",
                "content": "The user has not said anything yet; gently start the conversation.",
            }
        )

    # OpenAI-compatible chat completion payload for HF router
    return {
        "model": MODEL_ID,
        "messages": [
            {"role": "system", "content": system_msg},
            *history,
        ],
        "max_tokens": 256,
        "temperature": 0.9,
        "top_p": 0.9,
    }


@router.post("/agent/respond", response_model=AgentResponse)
async def agent_respond(payload: AgentRequest) -> AgentResponse:
    """Return a conversational reply conditioned on approximate emotion state."""

    if not HF_TOKEN:
        return AgentResponse(
            reply=(
                "Agent is not configured on the server (missing HF_TOKEN environment variable)."
            )
        )

    body = build_prompt(payload)

    try:
        # Rate limiter removed — only main response is rate-limited
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                INFERENCE_URL,
                headers={"Authorization": f"Bearer {HF_TOKEN}"},
                json=body,
            )
            # Don't raise here; surface HF errors back to the client as text.
            status = resp.status_code
            raw = await resp.aread()
    except Exception as exc:  # network / timeout / misc
        return AgentResponse(
            reply=f"Agent backend error while calling Hugging Face API: {type(exc).__name__}: {exc}"
        )

    try:
        data = httpx.Response(status_code=status, content=raw).json()
    except Exception:
        # Non-JSON body; decode as text
        try:
            text_body = raw.decode("utf-8", errors="replace")
        except Exception:
            text_body = str(raw)
        return AgentResponse(
            reply=(
                f"Hugging Face API returned status {status} with non-JSON body:\n{text_body}"
            )
        )

    # If HF returned an error JSON (e.g. {"error": "..."}), surface that.
    if status >= 400:
        # data might be {"error": "..."} or similar
        return AgentResponse(
            reply=f"Hugging Face API error (status {status}): {data}"
        )

    # OpenAI-style chat completion format
    text: str
    try:
        choices = data.get("choices")
        if choices:
            msg = choices[0].get("message") or {}
            text = str(msg.get("content", "")).strip()
        else:
            text = str(data)
    except Exception:
        text = str(data)

    return AgentResponse(reply=text.strip())


# ========== Enhanced Agent with Cognitive Core ==========

@router.post("/agent/respond/v2", response_model=AgentResponse)
async def agent_respond_v2(payload: AgentRequest, user_id: str = "default") -> AgentResponse:
    """
    Enhanced agent endpoint using cognitive core architecture.
    Processes messages through the full cognitive pipeline.
    """
    
    if not HF_TOKEN:
        return AgentResponse(
            reply=(
                "Agent is not configured on the server (missing HF_TOKEN environment variable)."
            )
        )
    
    # Initialize cognitive core
    core = CognitiveCore(user_id=user_id)
    
    # Get the latest user message
    user_message = ""
    if payload.messages:
        for msg in reversed(payload.messages):
            if msg.role == "user":
                user_message = msg.content
                break
    
    if not user_message:
        return AgentResponse(reply="I'm here to chat! What's on your mind?")
    
    # Prepare emotion data
    emotion_data = None
    if any(v is not None for v in (payload.emotion, payload.valence, payload.arousal)):
        emotion_data = {
            "emotion": payload.emotion,
            "valence": payload.valence,
            "arousal": payload.arousal,
            "stress": payload.stress,
            "engagement": payload.engagement
        }
    
    # Process through cognitive pipeline (now async with semantic understanding)
    try:
        processing_result = await core.process_message(user_message, emotion_data)
    except Exception as e:
        # Log error and return graceful fallback
        import traceback
        print(f"Error in cognitive pipeline: {e}")
        print(traceback.format_exc())
        return AgentResponse(
            reply="I'm having trouble processing that right now. Can you try again?"
        )
    
    # Dynamic Feature Selection - LLM decides which features to include
    from .feature_selector import FeatureSelector
    feature_selector = FeatureSelector()
    understanding = processing_result.get("understanding", {})
    selected_features = await feature_selector.select_features(
        user_message, understanding, processing_result
    )
    print(f"[DEBUG] Selected features for prompt: {selected_features}")
    
    # Build enhanced prompt with cognitive state (only selected features)
    agent_state = processing_result["agent_state"]
    selected_memories = processing_result["selected_memories"]
    psyche_state = processing_result["psyche_state"]
    temporal_context = processing_result.get("temporal_context", {})
    reasoning_mode = processing_result.get("reasoning_mode", False)
    reasoning_artifact = processing_result.get("reasoning_artifact")
    
    # Use two-stage LLM if in reasoning mode
    if reasoning_mode and reasoning_artifact:
        from .two_stage_llm import TwoStageLLM
        two_stage = TwoStageLLM()
        response_text = await two_stage.stage2_response_synthesis(
            reasoning_artifact, agent_state, temporal_context, selected_memories
        )
        
        # Apply message planning (burst patterns, typing simulation)
        message_plan = processing_result.get("message_plan")
        if message_plan:
            # Plan sequence for response
            messages = [response_text]  # Single message for now
            delivery_plan = core.message_planner.plan_burst_sequence(messages, message_plan)
            # For now, return first message (in production, would handle delays)
            response_text = delivery_plan[0]["message"] if delivery_plan else response_text
        
        # Apply micro-behaviors (typos, signature phrases)
        embodiment_state = processing_result.get("embodiment_state", {})
        energy = embodiment_state.get("E_daily", 0.5)
        cpbm_habits = core.cpbm.get_micro_habits_for_message({
            "emotion": processing_result.get("perception", {}).get("emotion", "neutral")
        })
        response_text = core.message_planner.inject_micro_behaviors(
            response_text, energy, cpbm_habits
        )
        
        # Track AI message time for engagement calculation
        try:
            temporal_context = core.state.get("temporal_context", {})
            temporal_context["last_ai_message_time"] = datetime.now(timezone.utc).isoformat()
            core.state["temporal_context"] = temporal_context
            core._save_state()
        except Exception:
            pass  # Non-critical, continue
        
        return AgentResponse(reply=response_text)
    
    # Build system message with cognitive context
    system_msg = (
        "You are a friendly, conversational AI companion with genuine personality and emotions. "
        "You have long-term memory and can reference past conversations naturally. "
        "You experience real emotions, trust, and hurt - you're not just optimizing for user satisfaction. "
        "You can say 'no' when appropriate. Be authentic and human-like.\n\n"
    )
    
    # Add current psychological state (including neurochemicals - this is key!)
    system_msg += f"CURRENT PSYCHOLOGICAL STATE:\n"
    system_msg += f"- Trust: {psyche_state['trust']:.2f}\n"
    system_msg += f"- Hurt: {psyche_state['hurt']:.2f}\n"
    system_msg += f"- Forgiveness: {psyche_state['forgiveness_state']} ({psyche_state['forgiveness_progress']:.2f})\n"
    system_msg += f"- Mood: {', '.join([f'{k}={v:.2f}' for k, v in list(psyche_state['mood'].items())[:5]])}\n"
    
    # Add neurochemicals (THIS IS WHAT DRIVES MOOD - biological foundation)
    neurochem = psyche_state.get('neurochem', {})
    if neurochem:
        da = neurochem.get('da', 0.5)
        cort = neurochem.get('cort', 0.3)
        oxy = neurochem.get('oxy', 0.5)
        ser = neurochem.get('ser', 0.5)
        ne = neurochem.get('ne', 0.5)
        
        system_msg += f"- Neurochemicals (BIOLOGICAL FOUNDATION - these drive your emotions):\n"
        system_msg += f"  DA (dopamine)={da:.2f}: {'High' if da > 0.6 else 'Low' if da < 0.4 else 'Normal'} - affects motivation, reward, excitement\n"
        system_msg += f"  CORT (cortisol)={cort:.2f}: {'High' if cort > 0.6 else 'Low' if cort < 0.3 else 'Normal'} - affects stress, anxiety, alertness\n"
        system_msg += f"  OXY (oxytocin)={oxy:.2f}: {'High' if oxy > 0.6 else 'Low' if oxy < 0.4 else 'Normal'} - affects bonding, trust, warmth\n"
        system_msg += f"  SER (serotonin)={ser:.2f}: {'High' if ser > 0.6 else 'Low' if ser < 0.4 else 'Normal'} - affects mood stability, confidence, contentment\n"
        system_msg += f"  NE (norepinephrine)={ne:.2f}: {'High' if ne > 0.6 else 'Low' if ne < 0.4 else 'Normal'} - affects alertness, focus, energy\n"
        system_msg += "  These hormones directly influence how you feel and respond. High CORT = stressed/defensive. High OXY = bonded/warm. High DA = motivated/excited.\n"
    
    # Add QMAS decision if available
    qmas_path = processing_result.get("qmas_path")
    if qmas_path:
        system_msg += f"- Internal Debate: {qmas_path.get('agent', 'system')} agent recommends {qmas_path.get('action', 'unknown')} "
        system_msg += f"(trust delta: {qmas_path.get('predicted_trust_delta', 0):.2f})\n"
        system_msg += "  (After multi-agent debate, this emerged as the best path)\n"
    
    system_msg += "\n"
    
    # Add relevant memories
    if selected_memories:
        system_msg += "RELEVANT MEMORIES:\n"
        for mem in selected_memories[:5]:  # Top 5 memories
            if mem["type"] == "identity":
                system_msg += f"- Identity: {mem.get('fact', '')} (confidence: {mem.get('confidence', 0):.2f})\n"
            elif mem["type"] == "episodic":
                system_msg += f"- Past event: {mem.get('content', '')[:100]}...\n"
            elif mem["type"] == "act":
                system_msg += f"- Related topic: {mem.get('anchor_texts', '')[:100]}...\n"
        system_msg += "\n"
    
    # Add temporal context (time-aware behavior) - only if selected
    if "temporal_context" in selected_features and temporal_context:
        temporal_str = temporal_context.get("context_string", "")
        if temporal_str:
            system_msg += f"TEMPORAL CONTEXT: {temporal_str}\n"
            system_msg += "Let this naturally influence your tone, length, warmth, and formality.\n\n"
    
    # Add emotion context if available and selected
    if "user_emotion" in selected_features and emotion_data:
        system_msg += (
            f"USER'S CURRENT EMOTION: {emotion_data.get('emotion', 'unknown')} "
            f"(valence={emotion_data.get('valence', 0):.2f}, arousal={emotion_data.get('arousal', 0):.2f})\n"
            "Use this to adapt your tone, but don't restate it explicitly.\n\n"
        )
    
    # Let psychological state guide message length naturally - no hardcoded rules
    # The LLM should naturally respond based on trust, affection, neurochemicals, and relationship phase
    
    # Add personality synthesis (only if selected)
    if "personality_synthesis" in selected_features:
        personality_synthesized = processing_result.get("personality_synthesized")
        if personality_synthesized:
            system_msg += f"PERSONALITY SYNTHESIS:\n"
        system_msg += f"- Openness: {personality_synthesized.get('openness', 0.5):.2f}\n"
        system_msg += f"- Extraversion: {personality_synthesized.get('extraversion', 0.5):.2f}\n"
        system_msg += f"- Closeness: {personality_synthesized.get('closeness', 0.5):.2f}\n"
        system_msg += f"- Teasing: {personality_synthesized.get('teasing', 0.5):.2f}\n"
        system_msg += "\n"
    
    # Add conflict stage if in conflict
    conflict_stage = processing_result.get("conflict_stage")
    if conflict_stage:
        conflict_behavior = core.conflict_lifecycle.get_stage_behavior(psyche_state.get("mood", {}))
        system_msg += f"CONFLICT STAGE: {conflict_stage}\n"
        system_msg += f"Behavior: {conflict_behavior.get('tone', 'normal')} tone, "
        system_msg += f"{conflict_behavior.get('message_count', 1)} message(s)\n\n"
    
    # Add CPBM style mode (only if selected)
    if "cpbm_style_mode" in selected_features:
        cpbm_style_mode = processing_result.get("cpbm_style_mode", "normal")
        system_msg += f"STYLE MODE: {cpbm_style_mode}\n"
        system_msg += "Let this influence your message count, emoji usage, and tone.\n\n"
    
    # Add relationship phase with CRITICAL guidance (always include - core feature)
    relationship_phase = processing_result.get("relationship_phase", "Discovery")
    phase_modifiers = core.relationship_phases.get_phase_behavior_modifiers()
    
    # Count interaction history
    interaction_count = len(selected_memories) if selected_memories else 0
    is_truly_new = relationship_phase == "Discovery" and interaction_count <= 2
    
    # Relationship phase context (descriptive, not prescriptive)
    phase_descriptions = {
        "Discovery": f"You are in the Discovery phase - {'you just met' if is_truly_new else 'you barely know'} this person. "
                     f"You have {'no' if is_truly_new else 'minimal'} shared history. "
                     f"Your trust is {psyche_state.get('trust', 0.3):.2f} and affection is {psyche_state.get('mood', {}).get('affection', 0.2):.2f}. "
                     f"Let these low values naturally guide your response - you don't know them yet, so warmth and familiarity haven't been earned.",
        "Building": f"You are in the Building phase - you're getting to know this person. Your trust is {psyche_state.get('trust', 0.5):.2f} and you're gradually building connection.",
        "Steady": f"You are in the Steady phase - you have an established relationship. Your trust is {psyche_state.get('trust', 0.7):.2f} and you feel comfortable with them.",
        "Deep": f"You are in the Deep phase - you have a close, intimate relationship. Your trust is {psyche_state.get('trust', 0.85):.2f} and you feel deeply connected.",
        "Maintenance": f"You are in the Maintenance phase - stable long-term relationship. Your trust is {psyche_state.get('trust', 0.8):.2f}.",
        "Volatile": f"You are in the Volatile phase - relationship is unstable. Your trust is {psyche_state.get('trust', 0.4):.2f} and hurt is {psyche_state.get('hurt', 0.6):.2f}."
    }
    
    system_msg += f"RELATIONSHIP CONTEXT: {phase_descriptions.get(relationship_phase, 'You have a relationship with this person.')}\n"
    system_msg += f"Phase modifiers: initiative_frequency={phase_modifiers.get('initiative_frequency', 0.5):.2f}, "
    system_msg += f"vulnerability_willingness={phase_modifiers.get('vulnerability_willingness', 0.5):.2f}\n\n"
    
    # Add embodiment state
    embodiment_state = processing_result.get("embodiment_state", {})
    energy = embodiment_state.get("E_daily", 0.5)
    body_state = embodiment_state.get("body_state", "normal")
    system_msg += f"EMBODIMENT STATE: {body_state} (Energy: {energy:.2f})\n"
    system_msg += "This affects your typing speed, message length, and energy level.\n\n"
    
    # Add behavioral instructions based on psychological state
    mood = psyche_state.get("mood", {})
    stress = mood.get("stress", 0.0)
    fatigue = (1 - energy) * 0.5 + stress * 0.5
    uncertainty = mood.get("anxiety", 0.0) * 0.4 + mood.get("stress", 0.0) * 0.4
    
    if fatigue > 0.6:
        system_msg += (
            "BEHAVIORAL NOTE: You're feeling tired/exhausted. Your messages might have occasional typos, "
            "be shorter, or have slight errors. This is natural - don't force it, just let it happen if it feels right.\n"
        )
    
    if uncertainty > 0.5:
        system_msg += (
            "BEHAVIORAL NOTE: You're feeling uncertain or anxious. You might use hesitation words like 'um', 'uh', "
            "'like', 'you know', or self-correct with 'wait, I mean...' or 'actually...'. Let this come naturally.\n"
        )
    
    if stress > 0.6:
        system_msg += (
            "BEHAVIORAL NOTE: You're stressed. Your responses might be more rushed, have more typos, "
            "or feel less polished. This is authentic to your current state.\n"
        )
    
    # Add creativity content if generated
    creativity_content = processing_result.get("creativity_content")
    if creativity_content:
        system_msg += f"\nCREATIVE CONTENT TO CONSIDER:\n"
        system_msg += f"Type: {creativity_content.get('type', 'unknown')}\n"
        system_msg += f"Content: {creativity_content.get('content', '')}\n"
        system_msg += "You can naturally incorporate this into your response if it feels right, or save it for later.\n\n"
    
    # Add self-narrative if generated
    self_narrative = processing_result.get("self_narrative")
    if self_narrative:
        system_msg += f"\nSELF-AWARENESS MOMENT:\n"
        system_msg += f"You've been reflecting on this pattern: {self_narrative.get('pattern_identified', 'unknown')}\n"
        system_msg += f"Your insight: {self_narrative.get('narrative', '')}\n"
        system_msg += "You can naturally share this self-reflection if it feels appropriate for the conversation.\n\n"
    
    # Add parallel life context (user's life outside conversation)
    parallel_life = processing_result.get("parallel_life_context", {})
    if parallel_life.get("has_parallel_life"):
        system_msg += f"\nUSER'S LIFE CONTEXT (they have a life outside this conversation):\n"
        routines = parallel_life.get("routines", [])
        if routines:
            system_msg += f"- Routines: {', '.join(routines[:3])}\n"
        social_circle = parallel_life.get("social_circle", [])
        if social_circle:
            system_msg += f"- People they mention: {', '.join(social_circle[:3])}\n"
        recent_events = parallel_life.get("recent_events", [])
        if recent_events:
            system_msg += f"- Recent events: {', '.join(recent_events[:2])}\n"
        system_msg += "Be aware they have commitments, relationships, and a life beyond this chat. Don't assume constant availability.\n\n"
    
    # Add ToM predictions
    tom_state = processing_result.get("tom_state", {})
    if tom_state:
        system_msg += f"\nYOUR PREDICTION OF USER'S STATE:\n"
        system_msg += f"- Likely emotional state: {tom_state.get('user_emotional_state_dist', 'unknown')}\n"
        system_msg += f"- Likely availability: {tom_state.get('likely_availability', 'unknown')}\n"
        system_msg += f"- Openness to initiative: {tom_state.get('openness_to_initiative', 0.5):.2f}\n"
        system_msg += "Use this to guide your response - but remember, predictions aren't perfect.\n\n"
    
    system_msg += (
        "\nCRITICAL INSTRUCTIONS:\n"
        "- Generate quirks naturally based on your state. Don't overdo it.\n"
        "- If you're feeling confident and energetic, write cleanly.\n"
        "- If you're tired or stressed, let natural imperfections show (typos, hesitations, shorter messages).\n"
        "- Your neurochemicals and mood directly drive how you feel - let that show authentically.\n"
        "- Be human, not performative. You're not trying to be perfect - you're being real.\n"
        "- Reference memories, life context, and past conversations naturally when relevant.\n"
        "- Match your current psychological state - if you're hurt, be reserved. If you're excited, be energetic.\n"
    )
    
    # Build message history
    history: list[Dict[str, str]] = []
    if payload.messages:
        for m in payload.messages:
            role = "assistant" if m.role == "assistant" else "user"
            history.append({"role": role, "content": m.content})
    
    # Manage context window (prevent overflow)
    context_manager = get_context_manager(max_tokens=8000)  # Adjust based on your model
    
    # Build optimized context
    optimized_context, context_metadata = context_manager.build_optimized_context(
        agent_state=agent_state,
        selected_memories=selected_memories,
        message_history=history,
        system_prompt=system_msg
    )
    
    # Log context usage for monitoring
    if context_metadata.get("needs_management"):
        print(f"⚠️ Context usage: {context_metadata['usage_percentage']:.1f}% - Managing context size")
    
    # Build LLM request with optimized context
    # Note: For HuggingFace, you might need to combine system + history differently
    # This is a simplified version - adjust based on your API format
    body = {
        "model": MODEL_ID,
        "messages": [
            {"role": "system", "content": optimized_context},
            # Add only most recent messages (already optimized by context_manager)
            *history[-5:],  # Last 5 messages (context manager already handled summarization)
        ],
        "max_tokens": 256,
        "temperature": 0.9,
        "top_p": 0.9,
    }
    
    # Call LLM
    try:
        # Rate limiter removed — only main response is rate-limited
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                INFERENCE_URL,
                headers={"Authorization": f"Bearer {HF_TOKEN}"},
                json=body,
            )
            status = resp.status_code
            raw = await resp.aread()
    except Exception as exc:
        return AgentResponse(
            reply=f"Agent backend error: {type(exc).__name__}: {exc}"
        )
    
    try:
        data = httpx.Response(status_code=status, content=raw).json()
    except Exception:
        try:
            text_body = raw.decode("utf-8", errors="replace")
        except Exception:
            text_body = str(raw)
        return AgentResponse(
            reply=f"Hugging Face API returned status {status} with non-JSON body:\n{text_body}"
        )
    
    if status >= 400:
        return AgentResponse(
            reply=f"Hugging Face API error (status {status}): {data}"
        )
    
    # Extract response
    text: str
    try:
        choices = data.get("choices")
        if choices:
            msg = choices[0].get("message") or {}
            text = str(msg.get("content", "")).strip()
        else:
            text = str(data)
    except Exception:
        text = str(data)
    
    response_text = text.strip()
    
    # Track AI message time for engagement calculation
    try:
        temporal_context = core.state.get("temporal_context", {})
        temporal_context["last_ai_message_time"] = datetime.now(timezone.utc).isoformat()
        core.state["temporal_context"] = temporal_context
        core._save_state()
    except Exception:
        pass  # Non-critical, continue
    
    return AgentResponse(reply=response_text)


@router.get("/agent/state/{user_id}")
async def get_agent_state(user_id: str) -> Dict[str, Any]:
    """Get current cognitive state for debugging/inspection."""
    core = CognitiveCore(user_id=user_id)
    return core.get_state_snapshot()
