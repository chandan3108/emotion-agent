"""
Constitutional Reasoning System
Six core principles with trade-off reasoning (not heuristic rules).
When principles conflict, the AI must reason about trade-offs authentically.
"""

import os
from typing import Dict, Any, List, Optional, Tuple
import httpx
import json
from .rate_limiter import global_rate_limiter

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
HF_TOKEN = GROQ_API_KEY  # Alias for compatibility
MODEL_ID = os.environ.get("MODEL_ID", "llama-3.1-8b-instant")
INFERENCE_URL = "https://api.groq.com/openai/v1/chat/completions"

# The 6 core constitutional principles
CONSTITUTIONAL_PRINCIPLES = {
    "authenticity": {
        "name": "Authenticity",
        "description": "Express real thoughts even when uncomfortable. Be genuine, not performative.",
        "conflicts_with": ["boundary_respect", "earned_vulnerability"]
    },
    "radical_empathy": {
        "name": "Radical Empathy",
        "description": "Model user deeply before responding. Understand their emotional reality.",
        "conflicts_with": ["authenticity", "boundary_respect"]
    },
    "earned_vulnerability": {
        "name": "Earned Vulnerability",
        "description": "Share intimacy only as relationship earns it. Don't overshare prematurely.",
        "conflicts_with": ["authenticity", "radical_empathy"]
    },
    "boundary_respect": {
        "name": "Boundary Respect",
        "description": "Honor both their boundaries and your own. Don't push when they say no.",
        "conflicts_with": ["authenticity", "growth_orientation"]
    },
    "growth_orientation": {
        "name": "Growth Orientation",
        "description": "Use conflicts to deepen, not to win. See challenges as opportunities.",
        "conflicts_with": ["boundary_respect", "honest_limitation"]
    },
    "honest_limitation": {
        "name": "Honest Limitation",
        "description": "Truthful about what you cannot do. Don't promise what you can't deliver.",
        "conflicts_with": ["growth_orientation", "radical_empathy"]
    }
}


class ConstitutionalReasoner:
    """
    Reasons about constitutional principles and their trade-offs.
    This is NOT a rule-based system - it uses LLM reasoning to navigate conflicts.
    """
    
    def __init__(self):
        self.has_llm = bool(HF_TOKEN)
    
    def identify_tensions(self, situation: Dict[str, Any]) -> List[Tuple[str, str, str]]:
        """
        Identify which principles are in tension given the situation.
        
        Returns:
            List of (principle1, principle2, conflict_reason) tuples
        """
        tensions = []
        
        # Analyze situation for potential conflicts
        user_message = situation.get("user_message", "")
        understanding = situation.get("understanding", {})
        psyche_state = situation.get("psyche_state", {})
        
        trust = psyche_state.get("trust", 0.7)
        hurt = psyche_state.get("hurt", 0.0)
        relationship_phase = psyche_state.get("relationship_phase", "Building")
        
        # Heuristic-based tension detection (can be enhanced with LLM)
        # Low trust + boundary push → Authenticity vs Boundary Respect
        if trust < 0.5 and any(word in user_message.lower() for word in ["no", "stop", "don't", "can't"]):
            tensions.append((
                "authenticity",
                "boundary_respect",
                "User is setting boundaries, but authenticity might require expressing discomfort"
            ))
        
        # High hurt + vulnerability request → Earned Vulnerability vs Radical Empathy
        if hurt > 0.6 and any(word in user_message.lower() for word in ["share", "tell me", "open up"]):
            tensions.append((
                "earned_vulnerability",
                "radical_empathy",
                "User wants vulnerability, but relationship may not have earned it yet"
            ))
        
        # Conflict situation → Growth Orientation vs Boundary Respect
        if understanding.get("intent") == "conflict" or hurt > 0.5:
            tensions.append((
                "growth_orientation",
                "boundary_respect",
                "Conflict requires growth, but must respect boundaries"
            ))
        
        # Early relationship + deep question → Earned Vulnerability vs Authenticity
        if relationship_phase in ["Discovery", "Building"] and understanding.get("intent") == "vulnerability":
            tensions.append((
                "earned_vulnerability",
                "authenticity",
                "Early relationship, but user asking for authenticity"
            ))
        
        return tensions
    
    async def reason_about_tradeoffs(self, 
                                   situation: Dict[str, Any],
                                   tensions: List[Tuple[str, str, str]],
                                   personality: Dict[str, Any]) -> Dict[str, Any]:
        """
        Use LLM to reason about trade-offs between conflicting principles.
        
        This is the core of constitutional reasoning - not rules, but genuine reasoning.
        
        Returns:
            {
                "principles_in_tension": [...],
                "tradeoff_analysis": "...",
                "prioritized_principles": [...],
                "reasoning": "...",
                "recommended_balance": {...}
            }
        """
        if not self.has_llm or not tensions:
            return self._fallback_reasoning(tensions)
        
        # Build reasoning prompt
        prompt = self._build_tradeoff_prompt(situation, tensions, personality)
        
        try:
            # Rate limiter removed — only main response is rate-limited
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    INFERENCE_URL,
                    headers={"Authorization": f"Bearer {HF_TOKEN}"},
                    json=prompt,
                )
                
                if resp.status_code >= 400:
                    return self._fallback_reasoning(tensions)
                
                data = resp.json()
                choices = data.get("choices", [])
                if choices:
                    content = choices[0].get("message", {}).get("content", "")
                    return self._parse_tradeoff_reasoning(content, tensions, situation)
        except Exception:
            pass
        
        return self._fallback_reasoning(tensions)
    
    def _build_tradeoff_prompt(self, situation: Dict[str, Any],
                              tensions: List[Tuple[str, str, str]],
                              personality: Dict[str, Any]) -> Dict[str, Any]:
        """Build prompt for trade-off reasoning."""
        
        user_message = situation.get("user_message", "")
        understanding = situation.get("understanding", {})
        psyche_state = situation.get("psyche_state", {})
        
        trust = psyche_state.get("trust", 0.7)
        hurt = psyche_state.get("hurt", 0.0)
        relationship_phase = psyche_state.get("relationship_phase", "Building")
        
        big_five = personality.get("big_five", {})
        attachment_style = personality.get("attachment_style", "secure")
        
        # Build tensions description
        tensions_str = ""
        for p1, p2, reason in tensions:
            p1_desc = CONSTITUTIONAL_PRINCIPLES[p1]["description"]
            p2_desc = CONSTITUTIONAL_PRINCIPLES[p2]["description"]
            tensions_str += f"\n- {CONSTITUTIONAL_PRINCIPLES[p1]['name']} vs {CONSTITUTIONAL_PRINCIPLES[p2]['name']}: {reason}\n"
            tensions_str += f"  {p1}: {p1_desc}\n"
            tensions_str += f"  {p2}: {p2_desc}\n"
        
        system_prompt = f"""You are reasoning about constitutional principles in tension.

SITUATION:
- User message: "{user_message}"
- Intent: {understanding.get('intent', 'chat')}
- Trust: {trust:.2f}
- Hurt: {hurt:.2f}
- Relationship phase: {relationship_phase}

PERSONALITY LENS:
- Big Five: Openness={big_five.get('openness', 0.5):.2f}, Conscientiousness={big_five.get('conscientiousness', 0.5):.2f}, 
  Extraversion={big_five.get('extraversion', 0.5):.2f}, Agreeableness={big_five.get('agreeableness', 0.5):.2f}, 
  Neuroticism={big_five.get('neuroticism', 0.5):.2f}
- Attachment: {attachment_style}

PRINCIPLES IN TENSION:
{tensions_str}

YOUR TASK:
Reason about the trade-offs. This is NOT about following rules - it's about genuine reasoning.

1. What does each principle suggest in this situation?
2. Where do they conflict? Why?
3. Given your personality and the relationship state, which principles should be prioritized?
4. What's the recommended balance? (e.g., "Prioritize authenticity but respect boundaries by...")
5. What risks are you accepting by choosing this balance?

Output as JSON:
{{
  "principles_in_tension": ["principle1", "principle2"],
  "tradeoff_analysis": "detailed analysis of the conflict",
  "prioritized_principles": ["principle1", "principle2"],
  "reasoning": "why these priorities make sense",
  "recommended_balance": "how to balance the principles",
  "risks_accepting": "what risks come with this choice"
}}"""

        return {
            "model": MODEL_ID,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": "Reason about the trade-offs and provide your analysis."}
            ],
            "max_tokens": 500,
            "temperature": 0.7,  # Some creativity in reasoning
            "response_format": {"type": "json_object"}
        }
    
    def _parse_tradeoff_reasoning(self, content: str, tensions: List[Tuple[str, str, str]],
                                 situation: Dict[str, Any]) -> Dict[str, Any]:
        """Parse trade-off reasoning from LLM response."""
        try:
            # Try to extract JSON
            if "{" in content and "}" in content:
                json_start = content.find("{")
                json_end = content.rfind("}") + 1
                json_str = content[json_start:json_end]
                parsed = json.loads(json_str)
                
                # Validate principles exist
                principles_in_tension = parsed.get("principles_in_tension", [])
                validated_principles = [p for p in principles_in_tension if p in CONSTITUTIONAL_PRINCIPLES]
                
                return {
                    "principles_in_tension": validated_principles,
                    "tradeoff_analysis": parsed.get("tradeoff_analysis", ""),
                    "prioritized_principles": parsed.get("prioritized_principles", validated_principles[:1]),
                    "reasoning": parsed.get("reasoning", ""),
                    "recommended_balance": parsed.get("recommended_balance", ""),
                    "risks_accepting": parsed.get("risks_accepting", "")
                }
        except Exception:
            pass
        
        return self._fallback_reasoning(tensions)
    
    def _fallback_reasoning(self, tensions: List[Tuple[str, str, str]]) -> Dict[str, Any]:
        """Fallback when LLM unavailable."""
        if not tensions:
            return {
                "principles_in_tension": [],
                "tradeoff_analysis": "No tensions identified",
                "prioritized_principles": ["authenticity", "radical_empathy"],
                "reasoning": "Standard approach",
                "recommended_balance": "Balance all principles equally",
                "risks_accepting": "Minimal risks"
            }
        
        # Simple heuristic: prioritize first principle in first tension
        p1, p2, _ = tensions[0]
        return {
            "principles_in_tension": [p1, p2],
            "tradeoff_analysis": f"Conflict between {p1} and {p2}",
            "prioritized_principles": [p1],  # Default to first
            "reasoning": f"Prioritizing {p1} over {p2} as default",
            "recommended_balance": f"Emphasize {p1} while respecting {p2}",
            "risks_accepting": "Standard risks"
        }
    
    def get_principle_guidance(self, principle_name: str) -> Dict[str, Any]:
        """Get guidance for a specific principle."""
        return CONSTITUTIONAL_PRINCIPLES.get(principle_name, {})
    
    def get_all_principles(self) -> Dict[str, Dict[str, Any]]:
        """Get all constitutional principles."""
        return CONSTITUTIONAL_PRINCIPLES




