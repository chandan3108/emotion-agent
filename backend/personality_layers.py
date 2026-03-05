"""
Five-Layer Personality Model
Core, Relationship, Situational, Mood, Micro layers with synthesis formula.
Anti-cloning via orthogonalization.
"""

import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone, timedelta
import math

# Task-specific weights for personality synthesis
TASK_WEIGHTS = {
    "deep_disclosure": [0.50, 0.30, 0.10, 0.05, 0.05],  # Core-heavy
    "impulsive_reply": [0.10, 0.15, 0.10, 0.50, 0.15],  # Mood-heavy
    "routine": [0.20, 0.30, 0.20, 0.20, 0.10],  # Relationship-heavy
    "playful": [0.10, 0.20, 0.10, 0.15, 0.45],  # Micro-heavy
    "serious_apology": [0.40, 0.40, 0.05, 0.10, 0.05],  # Core + Relationship
    "default": [0.30, 0.25, 0.15, 0.20, 0.10]  # Balanced
}

# Drift rates per layer (per day)
DRIFT_RATES = {
    "core": 0.001,  # ~0.0005-0.002/day
    "relationship": 0.01,  # ~0.005-0.02/day
    "situational": 0.0,  # Decays by time, not drift
    "mood": 0.0,  # Decays by time, not drift
    "micro": 0.0  # High volatility, resets per message
}

# Situational decay constant (hours)
SITUATIONAL_DECAY_TAU = 0.3  # hours


class PersonalityLayers:
    """
    Five-layer personality model with synthesis and anti-cloning.
    """
    
    def __init__(self, state: Dict[str, Any]):
        self.state = state
        self._init_layers()
    
    def _init_layers(self):
        """Initialize personality layers from state or defaults."""
        # Core layer (from state.core_personality)
        core_personality = self.state.get("core_personality", {})
        self.core = {
            "big_five": core_personality.get("big_five", {
                "openness": 0.5,
                "conscientiousness": 0.5,
                "extraversion": 0.5,
                "agreeableness": 0.5,
                "neuroticism": 0.5
            }),
            "humor_style": core_personality.get("humor_style", "light_playful"),
            "sensitivity": core_personality.get("sensitivity", 0.5),
            "attachment_style": core_personality.get("attachment_style", "secure"),
            "last_updated": core_personality.get("last_updated", datetime.now(timezone.utc).isoformat())
        }
        
        # Relationship layer (per-user, from state or init)
        if "relationship_personality" not in self.state:
            self.state["relationship_personality"] = {}
        rel_personality = self.state["relationship_personality"]
        # Check if this is a new relationship (no history)
        is_new_relationship = not rel_personality.get("last_updated")
        self.relationship = {
            "closeness": rel_personality.get("closeness", 0.2 if is_new_relationship else 0.5),  # Start low
            "clinginess": rel_personality.get("clinginess", 0.1 if is_new_relationship else 0.3),  # Start very low
            "teasing": rel_personality.get("teasing", 0.2 if is_new_relationship else 0.5),  # Start low
            "boldness": rel_personality.get("boldness", 0.2 if is_new_relationship else 0.4),  # Start low
            "vulnerability_willingness": rel_personality.get("vulnerability_willingness", 0.2 if is_new_relationship else 0.5),  # Start very low
            "last_updated": rel_personality.get("last_updated", datetime.now(timezone.utc).isoformat())
        }
        
        # Situational layer (context-dependent, resets)
        self.situational = {
            "mode": "normal",  # fight, flirt, bored, normal
            "intensity": 0.0,
            "activated_at": None,
            "decay_tau": SITUATIONAL_DECAY_TAU
        }
        
        # Mood layer (from psyche.mood - already exists)
        # We'll reference it but not duplicate
        
        # Micro layer (per-message quirks)
        # Long-term quirk development: own signature phrases, behaviors over weeks/months
        micro_state = self.state.get("micro_personality", {})
        self.micro = {
            "emoji_patterns": micro_state.get("emoji_patterns", {}),
            "signature_phrases": micro_state.get("signature_phrases", []),  # Own phrases developed over time
            "typo_playfulness": micro_state.get("typo_playfulness", 0.2),
            "double_text_habit": micro_state.get("double_text_habit", 0.2),
            "greeting_pattern": micro_state.get("greeting_pattern", None),
            "quirk_development": micro_state.get("quirk_development", {
                "phrases": {},  # phrase -> {strength, first_used, last_used, usage_count}
                "behaviors": {},  # behavior -> {strength, first_used, last_used, usage_count}
                "last_updated": datetime.now(timezone.utc).isoformat()
            })
        }
    
    def synthesize_persona(self, task_type: str = "default", 
                         mood_vector: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
        """
        Synthesize final persona from all layers using weighted combination.
        
        Formula: Persona = normalize(wcore × Core + wrel × Relationship + 
                                     wsit × Situational + wmood × Mood + wmicro × Micro)
        
        Args:
            task_type: Type of task (determines weights)
            mood_vector: Current mood vector (14 dimensions)
        
        Returns:
            Synthesized persona dict for LLM prompt
        """
        weights = TASK_WEIGHTS.get(task_type, TASK_WEIGHTS["default"])
        w_core, w_rel, w_sit, w_mood, w_micro = weights
        
        # Get mood vector (from psyche if not provided)
        if mood_vector is None:
            mood_vector = self.state.get("mood", {})
        
        # Synthesize personality traits
        persona = {
            # Core traits (weighted heavily for deep tasks)
            "openness": self.core["big_five"]["openness"] * w_core,
            "conscientiousness": self.core["big_five"]["conscientiousness"] * w_core,
            "extraversion": self.core["big_five"]["extraversion"] * w_core,
            "agreeableness": self.core["big_five"]["agreeableness"] * w_core,
            "neuroticism": self.core["big_five"]["neuroticism"] * w_core,
            "humor_style": self.core["humor_style"],
            "sensitivity": self.core["sensitivity"] * w_core,
            "attachment_style": self.core["attachment_style"],
            
            # Relationship traits (weighted for routine/playful tasks)
            "closeness": self.relationship["closeness"] * w_rel,
            "clinginess": self.relationship["clinginess"] * w_rel,
            "teasing": self.relationship["teasing"] * w_rel,
            "boldness": self.relationship["boldness"] * w_rel,
            "vulnerability_willingness": self.relationship["vulnerability_willingness"] * w_rel,
            
            # Situational traits (context-dependent)
            "situational_mode": self.situational["mode"],
            "situational_intensity": self.situational["intensity"] * w_sit,
            
            # Mood traits (weighted heavily for impulsive replies)
            "mood_happiness": mood_vector.get("happiness", 0.5) * w_mood,
            "mood_stress": mood_vector.get("stress", 0.3) * w_mood,
            "mood_affection": mood_vector.get("affection", 0.5) * w_mood,
            "mood_energy": mood_vector.get("energy", 0.5) * w_mood,
            "mood_boredom": mood_vector.get("boredom", 0.3) * w_mood,
            "mood_playfulness": mood_vector.get("playfulness", 0.3) * w_mood,
            
            # Micro traits (weighted heavily for playful tasks)
            "emoji_baseline": self.micro.get("emoji_baseline", 0.5) * w_micro,
            "typo_playfulness": self.micro["typo_playfulness"] * w_micro,
            "double_text_habit": self.micro["double_text_habit"] * w_micro,
        }
        
        # Normalize key dimensions to [0, 1]
        for key in ["openness", "conscientiousness", "extraversion", "agreeableness", 
                   "neuroticism", "closeness", "clinginess", "teasing", "boldness"]:
            if key in persona:
                persona[key] = max(0.0, min(1.0, persona[key]))
        
        return persona
    
    def update_relationship_layer(self, interaction_data: Dict[str, Any]):
        """
        Update relationship layer based on interactions.
        Uses orthogonalization to prevent cloning user style.
        
        Args:
            interaction_data: Contains user style, engagement, etc.
        """
        # Get user style (if detected)
        user_style = interaction_data.get("user_style", {})
        engagement = interaction_data.get("engagement", 0.5)
        
        # Anti-cloning: Project user style away from core basis
        # Only use orthogonal component for updates
        if user_style:
            # Extract orthogonal component (simplified - in full implementation would use proper vector projection)
            # For now, we'll use a damped update that respects core identity
            core_basis = {
                "teasing": self.core["big_five"]["extraversion"],  # Core influences relationship style
                "boldness": self.core["big_five"]["openness"],
                "closeness": self.core["big_five"]["agreeableness"]
            }
            
            # Update relationship traits with damping (prevents cloning)
            damping = 0.3  # Only 30% of user style influences relationship layer
            learning_rate = 0.05 * engagement  # Engagement modulates learning rate
            
            if "teasing" in user_style:
                user_teasing = user_style["teasing"]
                core_teasing = core_basis["teasing"]
                # Orthogonal component: user_style - projection onto core
                orthogonal = user_teasing - core_teasing
                self.relationship["teasing"] += learning_rate * damping * orthogonal
                self.relationship["teasing"] = max(0.0, min(1.0, self.relationship["teasing"]))
            
            if "boldness" in user_style:
                user_boldness = user_style["boldness"]
                core_boldness = core_basis["boldness"]
                orthogonal = user_boldness - core_boldness
                self.relationship["boldness"] += learning_rate * damping * orthogonal
                self.relationship["boldness"] = max(0.0, min(1.0, self.relationship["boldness"]))
        
        # Update closeness based on engagement and time
        if engagement > 0.7:
            self.relationship["closeness"] = min(1.0, self.relationship["closeness"] + 0.02)
        elif engagement < 0.3:
            self.relationship["closeness"] = max(0.0, self.relationship["closeness"] - 0.01)
        
        self.relationship["last_updated"] = datetime.now(timezone.utc).isoformat()
    
    def set_situational_mode(self, mode: str, intensity: float = 0.7):
        """
        Set situational mode (fight, flirt, bored, normal).
        Decays over time (τ ≈ 0.3 hours).
        """
        self.situational["mode"] = mode
        self.situational["intensity"] = intensity
        self.situational["activated_at"] = datetime.now(timezone.utc).isoformat()
    
    def decay_situational(self, delta_hours: float):
        """
        Decay situational layer over time.
        """
        if self.situational["activated_at"]:
            # Exponential decay
            self.situational["intensity"] *= math.exp(-delta_hours / self.situational["decay_tau"])
            
            # Reset to normal if intensity drops below threshold
            if self.situational["intensity"] < 0.1:
                self.situational["mode"] = "normal"
                self.situational["intensity"] = 0.0
                self.situational["activated_at"] = None
    
    def apply_drift(self, delta_days: float):
        """
        Apply natural drift to personality layers.
        Core drifts slowly, relationship drifts faster.
        """
        # Core layer drift (very slow)
        drift_core = DRIFT_RATES["core"] * delta_days
        for trait in ["openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"]:
            # Random walk with small drift
            noise = np.random.normal(0, drift_core * 0.5)
            self.core["big_five"][trait] += noise
            self.core["big_five"][trait] = max(0.0, min(1.0, self.core["big_five"][trait]))
        
        # Relationship layer drift (faster)
        drift_rel = DRIFT_RATES["relationship"] * delta_days
        for trait in ["closeness", "clinginess", "teasing", "boldness"]:
            noise = np.random.normal(0, drift_rel * 0.5)
            self.relationship[trait] += noise
            self.relationship[trait] = max(0.0, min(1.0, self.relationship[trait]))
        
        self.core["last_updated"] = datetime.now(timezone.utc).isoformat()
        self.relationship["last_updated"] = datetime.now(timezone.utc).isoformat()
    
    def update_micro_layer(self, message_data: Dict[str, Any]):
        """
        Update micro layer with per-message quirks.
        High volatility, resets frequently.
        """
        # Extract micro patterns from message
        if "emoji_count" in message_data:
            emoji_density = message_data["emoji_count"] / max(1, message_data.get("message_length", 1))
            # Update emoji baseline (rolling average)
            current = self.micro.get("emoji_baseline", 0.5)
            self.micro["emoji_baseline"] = 0.7 * current + 0.3 * emoji_density
        
        if "signature_phrase" in message_data:
            phrase = message_data["signature_phrase"]
            if phrase not in self.micro["signature_phrases"]:
                self.micro["signature_phrases"].append(phrase)
                # Keep only last 10
                self.micro["signature_phrases"] = self.micro["signature_phrases"][-10:]
    
    def get_personality_summary(self) -> str:
        """Get human-readable personality summary for prompts."""
        core = self.core
        rel = self.relationship
        
        summary = f"""Personality Summary:
- Core: {core['attachment_style']} attachment, {core['humor_style']} humor, sensitivity={core['sensitivity']:.2f}
- Big Five: O={core['big_five']['openness']:.2f}, C={core['big_five']['conscientiousness']:.2f}, 
  E={core['big_five']['extraversion']:.2f}, A={core['big_five']['agreeableness']:.2f}, 
  N={core['big_five']['neuroticism']:.2f}
- Relationship: closeness={rel['closeness']:.2f}, teasing={rel['teasing']:.2f}, 
  boldness={rel['boldness']:.2f}, clinginess={rel['clinginess']:.2f}
- Situational: {self.situational['mode']} (intensity={self.situational['intensity']:.2f})"""
        
        return summary
    
    def save_to_state(self):
        """Save personality layers back to state."""
        # Update core personality
        self.state["core_personality"].update({
            "big_five": self.core["big_five"],
            "humor_style": self.core["humor_style"],
            "sensitivity": self.core["sensitivity"],
            "attachment_style": self.core["attachment_style"],
            "last_updated": self.core["last_updated"]
        })
        
        # Update relationship personality
        self.state["relationship_personality"] = self.relationship
        
        # Update situational (stored in state for persistence)
        if "situational_personality" not in self.state:
            self.state["situational_personality"] = {}
        self.state["situational_personality"] = self.situational
        
        # Update micro (stored in micro_personality for long-term quirk development)
        if "micro_personality" not in self.state:
            self.state["micro_personality"] = {}
        self.state["micro_personality"].update({
            "emoji_patterns": self.micro.get("emoji_patterns", {}),
            "signature_phrases": self.micro.get("signature_phrases", []),
            "typo_playfulness": self.micro.get("typo_playfulness", 0.2),
            "double_text_habit": self.micro.get("double_text_habit", 0.2),
            "greeting_pattern": self.micro.get("greeting_pattern", None),
            "quirk_development": self.micro.get("quirk_development", {})
        })
        
        # Also update habits_cpbm for backward compatibility
        if "habits_cpbm" not in self.state:
            self.state["habits_cpbm"] = {}
        self.state["habits_cpbm"].update({
            "emoji_baseline": self.micro.get("emoji_baseline", 0.5),
            "typo_intentionality": self.micro.get("typo_playfulness", 0.2),
            "double_text_habit": self.micro.get("double_text_habit", 0.2),
            "signature_phrases": self.micro.get("signature_phrases", [])
        })

