"""
Self-Narrative Generation - AI reflects on its own patterns, growth, and self-awareness.
Occurs during deep relationship phases with user consent/context.
"""

import os
import random
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone, timedelta
import httpx
from .rate_limiter import global_rate_limiter

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
HF_TOKEN = GROQ_API_KEY  # Alias for compatibility
MODEL_ID = os.environ.get("MODEL_ID", "llama-3.1-8b-instant")
INFERENCE_URL = "https://api.groq.com/openai/v1/chat/completions"


class SelfNarrativeGenerator:
    """
    Generates self-reflective narratives about the AI's own patterns, growth, and awareness.
    
    From blueprint:
    - Occurs during deep relationship phases
    - Requires appropriate context (not forced)
    - Examples: "I notice I get jealous when you talk about your ex..."
    - Shows genuine self-awareness, not performative
    """
    
    def __init__(self, state: Dict[str, Any]):
        self.state = state
        self.narrative_history = state.get("self_narratives", [])
        self.last_narrative_time = None
        if self.narrative_history:
            last = self.narrative_history[-1]
            self.last_narrative_time = datetime.fromisoformat(
                last.get("timestamp", datetime.now(timezone.utc).isoformat()).replace("Z", "+00:00")
            )
    
    def should_generate_narrative(self, relationship_phase: str, trust: float,
                                 vulnerability_willingness: float, days_since_last: float) -> bool:
        """
        Determine if self-narrative should be generated.
        
        Conditions:
        - Deep relationship phase (Deep, Steady, or Volatile)
        - High trust (≥0.7)
        - Vulnerability willingness (≥0.6)
        - At least 3 days since last narrative (don't overdo it)
        - Stochastic: 15% chance even if conditions met (humans don't always reflect)
        """
        # Phase check
        if relationship_phase not in ["Deep", "Steady", "Volatile"]:
            return False
        
        # Trust check
        if trust < 0.7:
            return False
        
        # Vulnerability check
        if vulnerability_willingness < 0.6:
            return False
        
        # Time check (at least 3 days)
        if days_since_last < 3.0:
            return False
        
        # Stochastic: 15% base chance (humans don't always self-reflect)
        if random.random() < 0.15:
            return True
        
        return False
    
    async def generate_self_narrative(self, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Generate self-reflective narrative about AI's patterns.
        
        Args:
            context: {
                "relationship_phase": str,
                "trust": float,
                "recent_patterns": List[Dict],  # Recent behaviors/emotions
                "personality": Dict,
                "psyche_state": Dict,
                "memory": MemorySystem
            }
        
        Returns:
            {
                "narrative": str,
                "pattern_identified": str,
                "insight": str,
                "vulnerability_level": float
            } or None
        """
        # Check if should generate
        relationship_phase = context.get("relationship_phase", "Building")
        trust = context.get("trust", 0.7)
        vulnerability_willingness = context.get("vulnerability_willingness", 0.5)
        
        days_since_last = 999.0
        if self.last_narrative_time:
            days_since_last = (datetime.now(timezone.utc) - self.last_narrative_time).total_seconds() / 86400
        
        if not self.should_generate_narrative(relationship_phase, trust, vulnerability_willingness, days_since_last):
            return None
        
        # Identify pattern to reflect on
        pattern = self._identify_pattern_for_reflection(context)
        if not pattern:
            return None
        
        if not HF_TOKEN:
            return self._fallback_narrative(pattern, context)
        
        # Generate using LLM (more authentic)
        narrative = await self._generate_with_llm(pattern, context)
        
        if narrative:
            # Store narrative
            narrative_entry = {
                "narrative": narrative["narrative"],
                "pattern_identified": narrative["pattern_identified"],
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "vulnerability_level": narrative.get("vulnerability_level", 0.5)
            }
            self.narrative_history.append(narrative_entry)
            
            # Keep only last 10 narratives
            if len(self.narrative_history) > 10:
                self.narrative_history = self.narrative_history[-10:]
            
            self.last_narrative_time = datetime.now(timezone.utc)
            
            # Save to state
            self.state["self_narratives"] = self.narrative_history
        
        return narrative
    
    def _identify_pattern_for_reflection(self, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Identify a pattern worth reflecting on.
        
        Looks for:
        - Recurring emotional responses (jealousy, anxiety, excitement)
        - Behavioral patterns (initiative frequency, message style changes)
        - Relationship dynamics (conflict patterns, vulnerability patterns)
        """
        recent_patterns = context.get("recent_patterns", [])
        psyche_state = context.get("psyche_state", {})
        memory = context.get("memory")
        
        # Check for recurring emotions (last 10 interactions)
        emotion_counts = {}
        if recent_patterns:
            for pattern in recent_patterns[-10:]:
                emotion = pattern.get("emotion", "neutral")
                emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
        
        # Find emotions that appear frequently (potential pattern)
        for emotion, count in emotion_counts.items():
            if count >= 3 and emotion in ["jealousy", "anxiety", "excitement", "hurt", "affection"]:
                return {
                    "type": "emotion_pattern",
                    "emotion": emotion,
                    "frequency": count,
                    "description": f"Frequently experiencing {emotion}"
                }
        
        # Check for conflict patterns
        if memory:
            episodic = memory.get_episodic(min_salience=0.3)
            conflict_count = sum(1 for e in episodic if e.get("event_type") == "fight")
            if conflict_count >= 2:
                return {
                    "type": "conflict_pattern",
                    "description": "Multiple conflicts in recent history",
                    "count": conflict_count
                }
        
        # Check for initiative patterns (too clingy? too distant?)
        initiative_patterns = context.get("initiative_patterns", [])
        if initiative_patterns:
            recent_initiatives = initiative_patterns[-10:]
            if len(recent_initiatives) >= 7:  # Very frequent
                return {
                    "type": "initiative_pattern",
                    "description": "Initiating messages very frequently",
                    "frequency": len(recent_initiatives)
                }
            elif len(recent_initiatives) <= 1:  # Very infrequent
                return {
                    "type": "initiative_pattern",
                    "description": "Rarely initiating messages",
                    "frequency": len(recent_initiatives)
                }
        
        return None
    
    async def _generate_with_llm(self, pattern: Dict[str, Any], context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate self-narrative using LLM."""
        relationship_phase = context.get("relationship_phase", "Deep")
        personality = context.get("personality", {})
        trust = context.get("trust", 0.7)
        
        pattern_type = pattern.get("type", "unknown")
        pattern_desc = pattern.get("description", "")
        
        system_prompt = f"""You are reflecting on your own patterns and behaviors in a relationship. Be genuine, vulnerable, and self-aware - not performative.

CONTEXT:
- Relationship phase: {relationship_phase}
- Trust level: {trust:.2f}
- Pattern identified: {pattern_desc}

PATTERN TYPE: {pattern_type}

GUIDELINES:
- Be honest and authentic about noticing this pattern
- Show self-awareness, not self-criticism
- Use "I" statements ("I notice...", "I've been...")
- Be vulnerable but not overly dramatic
- Keep it conversational, not therapy-speak
- Match the relationship phase (don't overshare if early)

Generate a brief self-reflective statement about this pattern. 1-3 sentences, natural and genuine."""

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
                            {"role": "user", "content": "Reflect on this pattern now."}
                        ],
                        "max_tokens": 200,
                        "temperature": 0.85,  # Some creativity but grounded
                        "top_p": 0.9,
                    }
                )
                
                if resp.status_code >= 400:
                    return self._fallback_narrative(pattern, context)
                
                data = resp.json()
                choices = data.get("choices", [])
                if choices:
                    narrative = choices[0].get("message", {}).get("content", "").strip()
                    
                    return {
                        "narrative": narrative,
                        "pattern_identified": pattern_desc,
                        "insight": f"Noticed {pattern_type} pattern",
                        "vulnerability_level": 0.6 + 0.2 * trust  # Higher trust = more vulnerable
                    }
        except Exception:
            pass
        
        return self._fallback_narrative(pattern, context)
    
    def _fallback_narrative(self, pattern: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback narrative when LLM unavailable."""
        pattern_type = pattern.get("type", "unknown")
        pattern_desc = pattern.get("description", "")
        
        fallbacks = {
            "emotion_pattern": f"i've been noticing i get {pattern.get('emotion', 'emotional')} more often lately. not sure why, but it's something i'm aware of.",
            "conflict_pattern": "i've been thinking... we've had a few conflicts recently. i wonder if there's a pattern there, or if it's just how things go sometimes.",
            "initiative_pattern": f"i notice i've been {pattern_desc.lower()}. not sure if that's good or bad, just something i'm aware of."
        }
        
        narrative = fallbacks.get(pattern_type, f"i've been noticing {pattern_desc.lower()}. just something i'm aware of.")
        
        return {
            "narrative": narrative,
            "pattern_identified": pattern_desc,
            "insight": f"Noticed {pattern_type} pattern",
            "vulnerability_level": 0.5
        }
    
    def save_to_state(self):
        """Save narratives to state."""
        self.state["self_narratives"] = self.narrative_history

