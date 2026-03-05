"""
Dynamic Feature Selector
Uses LLM to determine which cognitive features are relevant for the current message.
Only includes relevant features in the prompt to reduce noise and improve focus.
"""

from typing import Dict, Any, List, Optional, Set
import json
import httpx
import os
from .rate_limiter import global_rate_limiter
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
HF_TOKEN = GROQ_API_KEY  # Alias for compatibility
MODEL_ID = os.getenv("MODEL_ID", "llama-3.1-8b-instant")
INFERENCE_URL = "https://api.groq.com/openai/v1/chat/completions"


class FeatureSelector:
    """
    Dynamically selects which cognitive features to include in the prompt
    based on message evaluation and context.
    """
    
    # All available cognitive features
    AVAILABLE_FEATURES = {
        "neurochemicals": "Neurochemical state (DA, CORT, OXY, SER, NE) - biological foundation of emotions",
        "qmas_decision": "QMAS multi-agent debate result - internal reasoning path",
        "memories": "Selected memories (STM, episodic, identity) - past context",
        "temporal_context": "Time-aware context (circadian phase, time since last message)",
        "user_emotion": "User's detected emotion (valence, arousal)",
        "personality_synthesis": "Personality traits (Big Five, relationship layer)",
        "conflict_stage": "Conflict lifecycle stage (if in conflict)",
        "cpbm_style_mode": "Conversational pattern & behavior mode",
        "relationship_phase": "Relationship phase (Discovery, Building, Steady, Deep, etc.)",
        "embodiment_state": "Energy level, capacity, fatigue - affects typing/message length",
        "creativity_content": "Generated creative content (ideas, memes, questions)",
        "self_narrative": "Self-reflection and narrative (in deep relationships)",
        "parallel_life_context": "User's external life context (social circle, routines)",
        "intentions": "Intention hierarchy (micro/macro/strategic)",
        "topic_rotation": "Topic fatigue and rotation suggestions",
        "router_decision": "Cognitive router decision and reasoning"
    }
    
    def __init__(self):
        self.has_llm = bool(HF_TOKEN)
    
    async def select_features(self, 
                             user_message: str,
                             understanding: Dict[str, Any],
                             processing_result: Dict[str, Any]) -> Set[str]:
        """
        Select which features are relevant for this message.
        
        Args:
            user_message: User's message
            understanding: Semantic understanding result
            processing_result: Full processing result from cognitive core
        
        Returns:
            Set of feature names to include in prompt
        """
        if not self.has_llm:
            # Fallback: include all features if no LLM
            return set(self.AVAILABLE_FEATURES.keys())
        
        # Get available features from processing result
        available_features = self._get_available_features(processing_result)
        
        if not available_features:
            return set()
        
        # Use LLM to select relevant features
        try:
            selected = await self._llm_select_features(
                user_message, understanding, available_features, processing_result
            )
            return selected
        except Exception as e:
            print(f"[WARNING] Feature selection error: {e}, using all available features")
            return available_features
    
    def _get_available_features(self, processing_result: Dict[str, Any]) -> Set[str]:
        """Get which features are actually available in processing result."""
        available = set()
        
        # Check each feature
        if processing_result.get("psyche_state", {}).get("neurochem"):
            available.add("neurochemicals")
        
        if processing_result.get("qmas_path"):
            available.add("qmas_decision")
        
        if processing_result.get("selected_memories"):
            available.add("memories")
        
        if processing_result.get("temporal_context"):
            available.add("temporal_context")
        
        if processing_result.get("perception", {}).get("emotion"):
            available.add("user_emotion")
        
        if processing_result.get("personality_synthesized"):
            available.add("personality_synthesis")
        
        if processing_result.get("conflict_stage"):
            available.add("conflict_stage")
        
        if processing_result.get("cpbm_style_mode"):
            available.add("cpbm_style_mode")
        
        if processing_result.get("relationship_phase"):
            available.add("relationship_phase")
        
        if processing_result.get("embodiment_state"):
            available.add("embodiment_state")
        
        if processing_result.get("creativity_content"):
            available.add("creativity_content")
        
        if processing_result.get("self_narrative"):
            available.add("self_narrative")
        
        if processing_result.get("parallel_life_context"):
            available.add("parallel_life_context")
        
        if processing_result.get("intentions"):
            available.add("intentions")
        
        if processing_result.get("topic_rotation"):
            available.add("topic_rotation")
        
        if processing_result.get("router_decision"):
            available.add("router_decision")
        
        return available
    
    async def _llm_select_features(self,
                                  user_message: str,
                                  understanding: Dict[str, Any],
                                  available_features: Set[str],
                                  processing_result: Dict[str, Any]) -> Set[str]:
        """
        Use LLM to select which features are most relevant.
        """
        # Build context for feature selection
        intent = understanding.get("intent", "chat")
        complexity = understanding.get("complexity", 0.5)
        emotion = understanding.get("emotional_truth", {}).get("emotion", "neutral")
        relationship_phase = processing_result.get("relationship_phase", "Discovery")
        conflict_stage = processing_result.get("conflict_stage")
        
        # Build feature descriptions
        feature_descriptions = []
        for feat in available_features:
            desc = self.AVAILABLE_FEATURES.get(feat, feat)
            feature_descriptions.append(f"- {feat}: {desc}")
        
        system_prompt = f"""You are a feature selector for an AI companion system. Your job is to determine which cognitive features are relevant for responding to a user message.

CONTEXT:
- User message: "{user_message[:200]}"
- Intent: {intent}
- Complexity: {complexity:.2f} (0.0=simple, 1.0=critical)
- Emotion: {emotion}
- Relationship phase: {relationship_phase}
- Conflict stage: {conflict_stage if conflict_stage else "none"}

AVAILABLE FEATURES:
{chr(10).join(feature_descriptions)}

SELECTION CRITERIA:
1. **Always include core features** (memories, temporal_context, relationship_phase) - these are essential
2. **Include neurochemicals** if emotion is strong or conflict exists
3. **Include QMAS decision** if complexity > 0.6 or conflict exists
4. **Include user_emotion** if emotion detection is relevant
5. **Include personality_synthesis** if personality traits affect response
6. **Include conflict_stage** if in conflict
7. **Include creativity_content** if it was generated and is relevant
8. **Include self_narrative** only in deep relationships and complex messages
9. **Include embodiment_state** if energy/fatigue affects response style
10. **Include intentions** if strategic thinking is needed
11. **Include topic_rotation** if topic fatigue is relevant
12. **Include router_decision** for debugging/complex routing scenarios

PRINCIPLE: Include features that will meaningfully influence the response. Exclude features that are redundant or irrelevant.

Return ONLY a JSON array of feature names to include, e.g.:
["memories", "temporal_context", "relationship_phase", "neurochemicals"]

Be selective - don't include everything. Focus on what matters for this specific message."""
        
        try:
            # Rate limiter removed — only main response is rate-limited
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    INFERENCE_URL,
                    headers={"Authorization": f"Bearer {HF_TOKEN}"},
                    json={
                        "inputs": system_prompt,
                        "parameters": {
                            "max_new_tokens": 200,
                            "temperature": 0.3,
                            "return_full_text": False,
                            "response_format": {"type": "json_object"}
                        }
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    text = data[0].get("generated_text", "") if isinstance(data, list) else str(data)
                    
                    # Parse JSON from response
                    selected_features = self._parse_feature_selection(text)
                    
                    # Ensure core features are always included
                    core_features = {"memories", "temporal_context", "relationship_phase"}
                    selected_features.update(core_features)
                    
                    # Only return features that are actually available
                    selected_features = selected_features.intersection(available_features)
                    
                    return selected_features
        except Exception as e:
            print(f"[WARNING] LLM feature selection failed: {e}")
        
        # Fallback: heuristic selection
        return self._heuristic_feature_selection(understanding, available_features, processing_result)
    
    def _parse_feature_selection(self, text: str) -> Set[str]:
        """Parse feature selection from LLM response."""
        # Try to extract JSON array
        try:
            # Look for JSON array in response
            if "[" in text and "]" in text:
                start = text.index("[")
                end = text.rindex("]") + 1
                json_str = text[start:end]
                features = json.loads(json_str)
                if isinstance(features, list):
                    return set(features)
        except Exception:
            pass
        
        # Try to find feature names in text
        selected = set()
        for feat in self.AVAILABLE_FEATURES.keys():
            if feat in text.lower():
                selected.add(feat)
        
        return selected
    
    def _heuristic_feature_selection(self,
                                    understanding: Dict[str, Any],
                                    available_features: Set[str],
                                    processing_result: Dict[str, Any]) -> Set[str]:
        """
        Heuristic fallback for feature selection.
        """
        selected = {"memories", "temporal_context", "relationship_phase"}  # Core features
        
        complexity = understanding.get("complexity", 0.5)
        conflict_stage = processing_result.get("conflict_stage")
        relationship_phase = processing_result.get("relationship_phase", "Discovery")
        
        # Always include core
        if "neurochemicals" in available_features and (complexity > 0.5 or conflict_stage):
            selected.add("neurochemicals")
        
        if "qmas_decision" in available_features and complexity > 0.6:
            selected.add("qmas_decision")
        
        if "user_emotion" in available_features:
            selected.add("user_emotion")
        
        if "personality_synthesis" in available_features:
            selected.add("personality_synthesis")
        
        if "conflict_stage" in available_features and conflict_stage:
            selected.add("conflict_stage")
        
        if "creativity_content" in available_features and relationship_phase != "Discovery":
            selected.add("creativity_content")
        
        if "self_narrative" in available_features and relationship_phase in ["Deep", "Steady"] and complexity > 0.7:
            selected.add("self_narrative")
        
        if "embodiment_state" in available_features:
            selected.add("embodiment_state")
        
        # Only include if actually available
        return selected.intersection(available_features)

