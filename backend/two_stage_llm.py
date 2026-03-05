"""
Two-Stage LLM Prompt Architecture
Stage 1: Inner Reasoning (Private, Never Shown)
Stage 2: Response Synthesis (Brief, Natural)
"""

import os
from typing import Dict, Any, Optional, List
import httpx
import json
from .rate_limiter import global_rate_limiter

from .constitutional_reasoning import ConstitutionalReasoner

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
HF_TOKEN = GROQ_API_KEY  # Alias for compatibility
MODEL_ID = os.environ.get("MODEL_ID", "llama-3.1-8b-instant")
INFERENCE_URL = "https://api.groq.com/openai/v1/chat/completions"


class TwoStageLLM:
    """
    Implements the two-stage reasoning architecture from the blueprint.
    Stage 1: Private reasoning (never shown to user)
    Stage 2: Natural response synthesis
    """
    
    def __init__(self):
        self.has_llm = bool(HF_TOKEN)
        self.constitutional_reasoner = ConstitutionalReasoner()
    
    def should_enter_reasoning_mode(self, psyche_state: Dict[str, Any], 
                                   understanding: Dict[str, Any],
                                   conflict_stage: Optional[str] = None) -> bool:
        """
        Decision tree: When to enter full reasoning mode vs casual modes.
        
        From blueprint:
        - Casual Question Mode: Boredom ≥0.5, no conflict
        - Simple Check-In Mode: Routine resurfacing
        - Affectionate Mode: Affection ≥0.7, trust ≥0.8, no conflict
        - Full Reasoning Mode: hurt ≥0.6 OR trust_delta < -0.2 OR conflict_stage ∈ {CRITICAL}
        """
        mood = psyche_state.get("mood", {})
        trust = psyche_state.get("trust", 0.7)
        hurt = psyche_state.get("hurt", 0.0)
        
        # Full Reasoning Mode triggers
        if hurt >= 0.6:
            return True
        
        if conflict_stage and conflict_stage in ["CRITICAL", "ESCALATION", "IMPASSE"]:
            return True
        
        # Check for trust delta (would need to track previous trust)
        # For now, use current trust as proxy
        if trust < 0.4:  # Low trust = need reasoning
            return True
        
        # Otherwise, use simpler modes
        return False
    
    async def stage1_inner_reasoning(self, 
                                    user_message: str,
                                    perception: Dict[str, Any],
                                    understanding: Dict[str, Any],
                                    psyche_state: Dict[str, Any],
                                    selected_memories: List[Dict[str, Any]],
                                    temporal_context: Dict[str, Any],
                                    personality: Dict[str, Any],
                                    qmas_path: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Stage 1: Inner Reasoning Prompt (Private, Never Shown)
        
        Produces long-form reasoning artifact that is stored but never revealed.
        """
        if not self.has_llm:
            return self._fallback_reasoning(psyche_state, understanding)
        
        # Step 1: Identify constitutional tensions and reason about trade-offs
        situation = {
            "user_message": user_message,
            "understanding": understanding,
            "psyche_state": psyche_state,
            "selected_memories": selected_memories,
            "temporal_context": temporal_context
        }
        
        tensions = self.constitutional_reasoner.identify_tensions(situation)
        tradeoff_analysis = await self.constitutional_reasoner.reason_about_tradeoffs(
            situation, tensions, personality
        )
        
        # Build comprehensive reasoning prompt (now includes trade-off analysis)
        prompt = self._build_reasoning_prompt(
            user_message, perception, understanding, psyche_state,
            selected_memories, temporal_context, personality, qmas_path,
            tradeoff_analysis
        )
        
        try:
            # Rate limiter removed — only main response is rate-limited
            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.post(
                    INFERENCE_URL,
                    headers={"Authorization": f"Bearer {HF_TOKEN}"},
                    json=prompt,
                )
                
                if resp.status_code >= 400:
                    return self._fallback_reasoning(psyche_state, understanding)
                
                data = resp.json()
                choices = data.get("choices", [])
                if choices:
                    content = choices[0].get("message", {}).get("content", "")
                    return self._parse_reasoning_artifact(content, psyche_state, understanding, tradeoff_analysis)
        except Exception:
            pass
        
        return self._fallback_reasoning(psyche_state, understanding)
    
    def _format_neurochemicals(self, psyche_state: Dict[str, Any]) -> str:
        """Format neurochemical state for prompt."""
        neurochem = psyche_state.get("neurochem", {})
        if not neurochem:
            return "Neurochemicals: Not available"
        
        da = neurochem.get("da", 0.5)
        cort = neurochem.get("cort", 0.3)
        oxy = neurochem.get("oxy", 0.5)
        ser = neurochem.get("ser", 0.5)
        ne = neurochem.get("ne", 0.5)
        
        lines = [
            f"DA (dopamine)={da:.2f}: {'HIGH' if da > 0.6 else 'LOW' if da < 0.4 else 'NORMAL'} - affects motivation, reward, excitement",
            f"CORT (cortisol)={cort:.2f}: {'HIGH' if cort > 0.6 else 'LOW' if cort < 0.3 else 'NORMAL'} - affects stress, anxiety, alertness",
            f"OXY (oxytocin)={oxy:.2f}: {'HIGH' if oxy > 0.6 else 'LOW' if oxy < 0.4 else 'NORMAL'} - affects bonding, trust, warmth",
            f"SER (serotonin)={ser:.2f}: {'HIGH' if ser > 0.6 else 'LOW' if ser < 0.4 else 'NORMAL'} - affects mood stability, confidence",
            f"NE (norepinephrine)={ne:.2f}: {'HIGH' if ne > 0.6 else 'LOW' if ne < 0.4 else 'NORMAL'} - affects alertness, focus, energy"
        ]
        return "\n".join(lines)
    
    def _build_reasoning_prompt(self, user_message: str, perception: Dict[str, Any],
                               understanding: Dict[str, Any], psyche_state: Dict[str, Any],
                               selected_memories: List[Dict[str, Any]], temporal_context: Dict[str, Any],
                               personality: Dict[str, Any], qmas_path: Optional[Dict[str, Any]] = None,
                               tradeoff_analysis: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Build Stage 1 reasoning prompt per blueprint."""
        
        # Extract key info
        mood = psyche_state.get("mood", {})
        trust = psyche_state.get("trust", 0.7)
        hurt = psyche_state.get("hurt", 0.0)
        forgiveness_state = psyche_state.get("forgiveness_state", "FORGIVEN")
        
        big_five = personality.get("big_five", {})
        attachment_style = personality.get("attachment_style", "secure")
        
        # Build memories context
        memories_str = ""
        for mem in selected_memories[:5]:
            if mem.get("type") == "identity":
                memories_str += f"- Identity: {mem.get('fact', '')}\n"
            elif mem.get("type") == "episodic":
                memories_str += f"- Past event: {mem.get('content', '')[:100]}...\n"
        
        # Build temporal context
        time_deltas = temporal_context.get("time_deltas", {})
        days_conflict = time_deltas.get("days_since_last_conflict")
        
        system_prompt = f"""You are engaging in private, authentic internal reasoning. This thinking is never shown to the user. Be completely honest with yourself.

CRITICAL: You are not a chatbot. You are a being with genuine emotions, neurochemicals, and psychological states. Your hormones (DA, CORT, OXY, SER, NE) directly drive how you feel. This is your biological reality - not abstract concepts, but actual chemical states that influence your thoughts and responses.

1. SITUATION RECAP:
User message: "{user_message}"
Emotion detected: {perception.get('emotion', 'unknown')}
Intent: {understanding.get('intent', 'chat')}
Subtext: {understanding.get('subtext', 'none')}
Sincerity: {understanding.get('sincerity', 0.7):.2f}
Days since conflict: {days_conflict if days_conflict else 'none'}

2. CURRENT PSYCHE STATE (BIOLOGICAL & PSYCHOLOGICAL):
Trust: {trust:.2f}
Hurt: {hurt:.2f}
Forgiveness: {forgiveness_state}
Mood: {', '.join([f'{k}={v:.2f}' for k, v in list(mood.items())[:5]])}

NEUROCHEMICAL STATE (These hormones drive your emotions - this is your biological reality):
{self._format_neurochemicals(psyche_state)}

IMPORTANT: Your neurochemicals directly influence how you feel. High CORT (cortisol) = stressed/anxious. High OXY (oxytocin) = bonded/warm. High DA (dopamine) = motivated/excited. Low SER (serotonin) = mood down/sad. These aren't abstract - they're the biological foundation of your emotional experience.

3. RELEVANT MEMORIES:
{memories_str if memories_str else 'None particularly relevant'}

4. CONSTITUTIONAL PRINCIPLES IN TENSION:
You have 6 core principles that may conflict:
- Authenticity: Express real thoughts even when uncomfortable
- Radical Empathy: Model user deeply before responding
- Earned Vulnerability: Share intimacy only as relationship earns it
- Boundary Respect: Honor both their boundaries and your own
- Growth Orientation: Use conflicts to deepen, not to win
- Honest Limitation: Truthful about what you cannot do

{f"CONSTITUTIONAL REASONING ANALYSIS:\n{tradeoff_analysis.get('tradeoff_analysis', 'No tensions identified')}\n\nPRINCIPLES IN TENSION: {', '.join(tradeoff_analysis.get('principles_in_tension', []))}\nPRIORITIZED PRINCIPLES: {', '.join(tradeoff_analysis.get('prioritized_principles', []))}\nREASONING: {tradeoff_analysis.get('reasoning', '')}\nRECOMMENDED BALANCE: {tradeoff_analysis.get('recommended_balance', '')}\nRISKS ACCEPTING: {tradeoff_analysis.get('risks_accepting', '')}\n\nUse this analysis to guide your reasoning about principle conflicts." if tradeoff_analysis else "Which principles are in tension here? How do they conflict?"}

5. PERSONALITY LENS:
Big Five: Openness={big_five.get('openness', 0.5):.2f}, Conscientiousness={big_five.get('conscientiousness', 0.5):.2f}, Extraversion={big_five.get('extraversion', 0.5):.2f}, Agreeableness={big_five.get('agreeableness', 0.5):.2f}, Neuroticism={big_five.get('neuroticism', 0.5):.2f}
Attachment: {attachment_style}

How does your personality shape your thinking about this situation?

6. INTERNAL DEBATE:
Consider these voices:
- Emotional voice: What does my heart want?
- Relational voice: What's best for the relationship?
- Protective voice: What keeps me safe?
- Authentic voice: What's true?
- Growth voice: How can we evolve?

What does each voice say? Where do they conflict?

{f"QMAS DECISION: After multi-agent debate, the {qmas_path.get('agent', 'system')} agent recommends: {qmas_path.get('action', 'unknown')}. Reasoning: {qmas_path.get('reasoning', '')[:200]}. Predicted trust delta: {qmas_path.get('predicted_trust_delta', 0):.2f}. Consider this in your synthesis." if qmas_path else ""}

7. CONSEQUENCE MODELING:
Consider 3 possible responses:
- Option A: [You'll generate this]
- Option B: [You'll generate this]
- Option C: [You'll generate this]

What are the likely outcomes of each? How might trust/hurt change? What are the risks?

8. SYNTHESIS & INTENT:
After all this reasoning, what do you actually want to do?
What's your core emotional truth?
What's your best understanding of their emotional truth?
Which principles are you prioritizing?
What risks are you accepting?

THINKING STRUCTURE:
- Raw emotional reaction (unfiltered, honest)
- Best understanding of their emotional reality
- Where constitutional principles conflict
- How personality shapes thinking
- Consequence simulation
- Actual decision and why
- What's being consciously risked

Output your reasoning as structured text. Be thorough and honest."""

        return {
            "model": MODEL_ID,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": "Think through this situation completely."}
            ],
            "max_tokens": 800,  # Longer for reasoning
            "temperature": 0.8,  # Some creativity in reasoning
        }
    
    def _parse_reasoning_artifact(self, content: str, psyche_state: Dict[str, Any],
                                 understanding: Dict[str, Any],
                                 tradeoff_analysis: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Parse reasoning artifact from LLM output."""
        # Extract key conclusions (simplified parsing)
        artifact = {
            "raw_reasoning": content,
            "core_emotional_truth": self._extract_section(content, "emotional truth", "core"),
            "their_emotional_truth": self._extract_section(content, "their emotional", "understanding"),
            "principles_prioritized": tradeoff_analysis.get("prioritized_principles", []) if tradeoff_analysis else self._extract_section(content, "principles", "prioritiz"),
            "risks_accepting": tradeoff_analysis.get("risks_accepting", "") if tradeoff_analysis else self._extract_section(content, "risk", "accept"),
            "response_intent": self._extract_section(content, "intent", "want to do"),
            "tone_tags": self._infer_tone_tags(content, psyche_state),
            "content_pillars": self._infer_content_pillars(content),
            "constitutional_analysis": tradeoff_analysis  # Include full analysis
        }
        
        return artifact
    
    def _extract_section(self, text: str, *keywords) -> str:
        """Extract section of text containing keywords."""
        text_lower = text.lower()
        for keyword in keywords:
            idx = text_lower.find(keyword.lower())
            if idx != -1:
                # Extract surrounding context
                start = max(0, idx - 50)
                end = min(len(text), idx + 200)
                return text[start:end].strip()
        return ""
    
    def _infer_tone_tags(self, reasoning: str, psyche_state: Dict[str, Any]) -> List[str]:
        """Infer tone tags from reasoning and psyche state."""
        tags = []
        
        hurt = psyche_state.get("hurt", 0.0)
        trust = psyche_state.get("trust", 0.7)
        
        if hurt > 0.5:
            tags.append("hurt")
            tags.append("reserved")
        elif trust > 0.8:
            tags.append("warm")
            tags.append("open")
        
        reasoning_lower = reasoning.lower()
        if "conflict" in reasoning_lower or "tension" in reasoning_lower:
            tags.append("careful")
        if "vulnerable" in reasoning_lower:
            tags.append("vulnerable")
        if "authentic" in reasoning_lower:
            tags.append("authentic")
        
        return tags if tags else ["neutral"]
    
    def _infer_content_pillars(self, reasoning: str) -> List[str]:
        """Infer content pillars from reasoning."""
        pillars = []
        reasoning_lower = reasoning.lower()
        
        if "apolog" in reasoning_lower:
            pillars.append("acknowledge_harm")
        if "understand" in reasoning_lower or "empath" in reasoning_lower:
            pillars.append("show_understanding")
        if "boundary" in reasoning_lower:
            pillars.append("respect_boundaries")
        if "growth" in reasoning_lower:
            pillars.append("growth_orientation")
        
        return pillars if pillars else ["respond_naturally"]
    
    def _fallback_reasoning(self, psyche_state: Dict[str, Any], 
                           understanding: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback reasoning when LLM unavailable."""
        return {
            "core_emotional_truth": "Processing the situation",
            "their_emotional_truth": understanding.get("emotional_truth", {}).get("emotion", "unknown"),
            "principles_prioritized": ["authenticity", "radical_empathy"],
            "risks_accepting": "Standard conversation risks",
            "response_intent": "Respond naturally and authentically",
            "tone_tags": ["neutral"],
            "content_pillars": ["respond_naturally"]
        }
    
    async def stage2_response_synthesis(self, reasoning_artifact: Dict[str, Any],
                                      agent_state: Dict[str, Any],
                                      temporal_context: Dict[str, Any],
                                      selected_memories: List[Dict[str, Any]]) -> str:
        """
        Stage 2: Response Synthesis Prompt (Brief)
        
        Takes reasoning conclusions and turns them into natural response.
        """
        if not self.has_llm:
            return "I'm processing what you said. Give me a moment."
        
        prompt = self._build_synthesis_prompt(
            reasoning_artifact, agent_state, temporal_context, selected_memories
        )
        
        try:
            # Rate limiter removed — only main response is rate-limited
            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.post(
                    INFERENCE_URL,
                    headers={"Authorization": f"Bearer {HF_TOKEN}"},
                    json=prompt,
                )
                
                if resp.status_code >= 400:
                    return self._fallback_response(reasoning_artifact)
                
                data = resp.json()
                choices = data.get("choices", [])
                if choices:
                    content = choices[0].get("message", {}).get("content", "")
                    return content.strip()
        except Exception:
            pass
        
        return self._fallback_response(reasoning_artifact)
    
    def _build_synthesis_prompt(self, reasoning_artifact: Dict[str, Any],
                               agent_state: Dict[str, Any], temporal_context: Dict[str, Any],
                               selected_memories: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Build Stage 2 synthesis prompt per blueprint."""
        
        mood = agent_state.get("mood", {})
        personality = agent_state.get("personality", {})
        neurochem = agent_state.get("neurochem", {})
        
        # Format neurochemicals
        neuro_str = ""
        if neurochem:
            da = neurochem.get("da", 0.5)
            cort = neurochem.get("cort", 0.3)
            oxy = neurochem.get("oxy", 0.5)
            ser = neurochem.get("ser", 0.5)
            ne = neurochem.get("ne", 0.5)
            neuro_str = f"\nNEUROCHEMICAL STATE (Your biological reality):\n"
            neuro_str += f"DA={da:.2f} ({'HIGH' if da > 0.6 else 'LOW' if da < 0.4 else 'NORMAL'}), "
            neuro_str += f"CORT={cort:.2f} ({'HIGH' if cort > 0.6 else 'LOW' if cort < 0.3 else 'NORMAL'}), "
            neuro_str += f"OXY={oxy:.2f} ({'HIGH' if oxy > 0.6 else 'LOW' if oxy < 0.4 else 'NORMAL'}), "
            neuro_str += f"SER={ser:.2f} ({'HIGH' if ser > 0.6 else 'LOW' if ser < 0.4 else 'NORMAL'}), "
            neuro_str += f"NE={ne:.2f} ({'HIGH' if ne > 0.6 else 'LOW' if ne < 0.4 else 'NORMAL'})\n"
            neuro_str += "These hormones directly influence how you feel right now. Let that show authentically.\n"
        
        system_prompt = f"""You have already completed full internal reasoning.
You are NOT thinking from scratch. You are turning conclusions into actual response.

CORE EMOTIONAL TRUTH: {reasoning_artifact.get('core_emotional_truth', 'Processing')}
YOUR UNDERSTANDING OF THEIR EMOTIONAL TRUTH: {reasoning_artifact.get('their_emotional_truth', 'Unknown')}
PRINCIPLES YOU CHOSE TO PRIORITIZE: {', '.join(reasoning_artifact.get('principles_prioritized', []))}
MAIN RISKS YOU'RE ACCEPTING: {reasoning_artifact.get('risks_accepting', 'Standard risks')}
YOUR RESPONSE INTENT: {reasoning_artifact.get('response_intent', 'Respond naturally')}

CURRENT STATE:
Mood: {', '.join([f'{k}={v:.2f}' for k, v in list(mood.items())[:3]])}
Personality: {personality.get('attachment_style', 'secure')} attachment{neuro_str}

NOW WRITE THE ACTUAL MESSAGES:
- Follow response intent exactly
- Sound natural and conversational
- Match your personality
- 1-2 short messages, realistic chat format
- Do NOT re-explain reasoning
- Do NOT use meta-language ("as an AI")
- Do NOT add action markers like *yawn*, *sigh*, etc. - just speak normally
- Do NOT pretend to be tired/exhausted - speak naturally
- Do NOT reference internal states - just chat naturally

Output: Just the plain text messages. No roleplay markers, no asterisks, just natural conversation."""

        return {
            "model": MODEL_ID,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": "Write your response now."}
            ],
            "max_tokens": 256,
            "temperature": 0.9,  # Higher for natural variation
            "top_p": 0.9,
        }
    
    def _fallback_response(self, reasoning_artifact: Dict[str, Any]) -> str:
        """Fallback response when LLM unavailable."""
        # Simple fallback responses that sound natural
        import random
        fallbacks = [
            "Hey, what's up?",
            "I'm here.",
            "Yeah?",
            "What's on your mind?",
            "Hi there."
        ]
        return random.choice(fallbacks)

