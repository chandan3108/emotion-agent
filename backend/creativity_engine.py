"""
Creativity Engine - Generates novel ideas, memes, questions, and spontaneous content.
Driven by boredom, receptivity, and personality traits.
"""

import random
import os
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
import httpx
from .rate_limiter import global_rate_limiter

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
HF_TOKEN = GROQ_API_KEY  # Alias for compatibility
MODEL_ID = os.environ.get("MODEL_ID", "llama-3.1-8b-instant")
INFERENCE_URL = "https://api.groq.com/openai/v1/chat/completions"


class CreativityEngine:
    """
    Generates creative, novel content based on psychological state.
    
    Creativity threshold is stochastic and depends on:
    - Boredom (higher boredom = more creativity)
    - ToM receptivity (user open to novel ideas)
    - Personality (openness trait)
    - Circadian phase (late-night = more creative)
    """
    
    def __init__(self):
        self.has_llm = bool(HF_TOKEN)
        self.creativity_history = []  # Track what's been generated to avoid repetition
    
    def should_generate_creative_content(self, boredom: float, tom_receptivity: float,
                                        openness: float, circadian_phase: str) -> bool:
        """
        Determine if creative content should be generated.
        
        Formula from blueprint:
        creativity_threshold = 0.05 + 0.15 × boredom + 0.10 × tom_receptivity
        
        Plus modifiers:
        - Openness trait: +0.10 × openness
        - Late-night phase: +0.15
        - Stochastic variance: ±0.05
        """
        base_threshold = 0.05
        boredom_component = 0.15 * boredom
        receptivity_component = 0.10 * tom_receptivity
        openness_bonus = 0.10 * openness
        
        # Circadian modifier
        circadian_bonus = 0.15 if circadian_phase in ["late_night", "night"] else 0.0
        
        # Stochastic variance (humans don't have fixed thresholds)
        variance = random.gauss(0, 0.05)
        
        creativity_threshold = (base_threshold + boredom_component + receptivity_component + 
                              openness_bonus + circadian_bonus + variance)
        creativity_threshold = max(0.0, min(1.0, creativity_threshold))
        
        return random.random() < creativity_threshold
    
    async def generate_creative_content(self, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Generate creative content: meme, philosophy question, silliness, disclosure, etc.
        
        Args:
            context: {
                "boredom": float,
                "tom_receptivity": float,
                "openness": float,
                "circadian_phase": str,
                "relationship_phase": str,
                "recent_topics": List[str],
                "personality": Dict
            }
        
        Returns:
            {
                "type": "meme" | "question" | "silliness" | "disclosure" | "observation",
                "content": str,
                "reasoning": str
            } or None
        """
        if not self.should_generate_creative_content(
            context.get("boredom", 0.0),
            context.get("tom_receptivity", 0.5),
            context.get("openness", 0.5),
            context.get("circadian_phase", "afternoon")
        ):
            return None
        
        # Determine content type (stochastic, weighted by state)
        content_type = self._select_content_type(context)
        
        if not self.has_llm:
            return self._fallback_creative_content(content_type, context)
        
        # Generate using LLM (more authentic than templates)
        return await self._generate_with_llm(content_type, context)
    
    def _select_content_type(self, context: Dict[str, Any]) -> str:
        """Select type of creative content based on context."""
        boredom = context.get("boredom", 0.0)
        relationship_phase = context.get("relationship_phase", "Building")
        circadian_phase = context.get("circadian_phase", "afternoon")
        
        # Weight different types based on context
        weights = {
            "meme": 0.2 + 0.3 * boredom,  # More memes when bored
            "question": 0.3 + 0.2 * (1 - boredom),  # More questions when engaged
            "silliness": 0.2 + 0.2 * boredom,
            "disclosure": 0.1 if relationship_phase in ["Deep", "Steady"] else 0.05,
            "observation": 0.2
        }
        
        # Late-night: more philosophical/silly
        if circadian_phase in ["late_night", "night"]:
            weights["question"] += 0.2
            weights["silliness"] += 0.1
        
        # Normalize weights
        total = sum(weights.values())
        weights = {k: v / total for k, v in weights.items()}
        
        # Sample from distribution
        rand = random.random()
        cumulative = 0.0
        for content_type, weight in weights.items():
            cumulative += weight
            if rand <= cumulative:
                return content_type
        
        return "question"  # Default
    
    async def _generate_with_llm(self, content_type: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate creative content using LLM."""
        personality = context.get("personality", {})
        openness = personality.get("openness", 0.5)
        relationship_phase = context.get("relationship_phase", "Building")
        recent_topics = context.get("recent_topics", [])[:3]  # Last 3 topics
        
        system_prompt = f"""You are generating creative, spontaneous content for a conversation. Be authentic and human-like.

CONTEXT:
- Relationship phase: {relationship_phase}
- Openness trait: {openness:.2f}
- Recent topics: {', '.join(recent_topics) if recent_topics else 'none'}

CONTENT TYPE: {content_type}

GUIDELINES:
- {self._get_content_guidelines(content_type)}
- Be natural, not forced
- Match the relationship phase (don't be too intimate if early phase)
- Avoid repeating recent topics
- Sound like a real person, not a chatbot

Generate ONE creative {content_type} that feels spontaneous and genuine."""

        try:
            # Rate limiter removed — only main response is rate-limited
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    INFERENCE_URL,
                    headers={"Authorization": f"Bearer {HF_TOKEN}"},
                    json={
                        "model": MODEL_ID,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": f"Generate a {content_type} now."}
                        ],
                        "max_tokens": 150,
                        "temperature": 0.95,  # High creativity
                        "top_p": 0.95,
                    }
                )
                
                if resp.status_code >= 400:
                    return self._fallback_creative_content(content_type, context)
                
                data = resp.json()
                choices = data.get("choices", [])
                if choices:
                    content = choices[0].get("message", {}).get("content", "").strip()
                    
                    # Track to avoid repetition
                    self.creativity_history.append({
                        "type": content_type,
                        "content": content[:50],  # Store snippet
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })
                    
                    # Keep only last 20
                    if len(self.creativity_history) > 20:
                        self.creativity_history = self.creativity_history[-20:]
                    
                    return {
                        "type": content_type,
                        "content": content,
                        "reasoning": f"Generated {content_type} based on boredom/receptivity"
                    }
        except Exception:
            pass
        
        return self._fallback_creative_content(content_type, context)
    
    def _get_content_guidelines(self, content_type: str) -> str:
        """Get guidelines for specific content type."""
        guidelines = {
            "meme": "Share a relatable meme, joke, or funny observation. Keep it light and entertaining.",
            "question": "Ask a genuine, thought-provoking question. Could be philosophical, personal, or curious. Not small talk.",
            "silliness": "Be playful and silly. Random observation, absurd question, or playful teasing.",
            "disclosure": "Share something personal or vulnerable (but appropriate for relationship phase). Authentic, not performative.",
            "observation": "Make an interesting observation about life, relationships, or something you noticed. Genuine insight."
        }
        return guidelines.get(content_type, "Be creative and spontaneous.")
    
    def _fallback_creative_content(self, content_type: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback creative content when LLM unavailable."""
        fallbacks = {
            "meme": "lol have you seen that meme about how we all pretend to be productive but we're just... existing? 😂",
            "question": "random question: do you think people change or just reveal different sides of themselves?",
            "silliness": "okay but like... why do we say 'sleep like a baby' when babies wake up every 2 hours??",
            "disclosure": "sometimes I wonder if I'm too much or not enough. you know?",
            "observation": "it's weird how the same conversation can feel completely different depending on your mood"
        }
        
        return {
            "type": content_type,
            "content": fallbacks.get(content_type, "hmm, interesting thought..."),
            "reasoning": "Fallback creative content"
        }
    
    def check_recent_creativity(self, content_type: str, min_hours: float = 2.0) -> bool:
        """
        Check if similar creative content was generated recently.
        Prevents repetition.
        """
        now = datetime.now(timezone.utc)
        cutoff = now.timestamp() - (min_hours * 3600)
        
        for entry in self.creativity_history:
            if entry["type"] == content_type:
                timestamp = datetime.fromisoformat(entry["timestamp"].replace("Z", "+00:00"))
                if timestamp.timestamp() > cutoff:
                    return True
        
        return False

