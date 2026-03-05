"""
Conversational Pattern & Behavior Model (CPBM)
Learns user's style organically (not cloning) through engagement-based reinforcement.
"""

import math
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
import random

HABIT_FORMATION_THRESHOLD = 0.6

# Style mode multipliers
STYLE_MODE_MULTIPLIERS = {
    "excited": {"message_count": 1.8, "emoji": 2.0, "length": 1.3},
    "hurt": {"message_count": 0.5, "emoji": 0.1, "length": 0.8, "tone": "flat_dry"},
    "flirty": {"emoji": 1.5, "teasing": 1.8, "typos": "playful"},
    "bored": {"randomness": 2.0, "topic_jumps": 2.0, "meme_frequency": 1.5},
    "jealous": {"follow_ups": "pointed", "emoji": "???"},
    "playful": {"burst": True, "inter_delay": (1, 6)},
    "normal": {"message_count": 1.0, "emoji": 1.0, "length": 1.0}
}


class CPBM:
    """
    Conversational Pattern & Behavior Model.
    Learns from user interactions without cloning their style.
    """
    
    def __init__(self, state: Dict[str, Any]):
        self.state = state
        self._init_cpbm()
    
    def _init_cpbm(self):
        """Initialize CPBM from state or defaults."""
        habits = self.state.get("habits_cpbm", {})
        
        # Stable style traits (slow-drifting)
        self.stable_traits = {
            "long_message_preference": habits.get("long_message_preference", 0.5),
            "emoji_baseline": habits.get("emoji_baseline", 0.5),
            "teasing_style": habits.get("teasing_style", "light_playful"),  # light_playful, mean, absent
            "humor_frequency": habits.get("humor_frequency", 0.5),
            "punctuation_style": habits.get("punctuation_style", "expressive"),  # expressive, minimal, formal
            "formality_baseline": habits.get("formality_baseline", 0.3),
            "typo_intentionality": habits.get("typo_intentionality", 0.2),
            "last_updated": habits.get("last_updated", datetime.now(timezone.utc).isoformat())
        }
        
        # Style mode (mood-driven, changes frequently)
        self.style_mode = habits.get("style_mode", "normal")
        
        # Micro-habits (quick-forming, high-volatility)
        self.micro_habits = {
            "signature_words": habits.get("signature_words", {}),  # word -> context -> strength
            "emoji_patterns": habits.get("emoji_patterns", {}),  # emoji -> context -> strength
            "typo_playfulness": habits.get("typo_playfulness", 0.2),
            "double_text_habit": habits.get("double_text_habit", 0.2),
            "greeting_patterns": habits.get("greeting_patterns", []),
            "habit_scores": habits.get("habit_scores", {})  # pattern_id -> habit_score
        }
        
        # Observed patterns (candidates for promotion to habits)
        self.observed_patterns = habits.get("observed_patterns", [])
    
    def observe_user_style(self, user_message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Observe user's message style and extract latent tendencies.
        Returns environment description (not direct cloning).
        """
        message_length = len(user_message)
        emoji_count = sum(1 for c in user_message if ord(c) > 0x1F600 and ord(c) < 0x1F64F)  # Simple emoji detection
        emoji_density = emoji_count / max(1, message_length)
        
        # Extract patterns
        patterns = {
            "message_length": message_length,
            "emoji_density": emoji_density,
            "punctuation_density": sum(1 for c in user_message if c in "!?.") / max(1, message_length),
            "has_question": "?" in user_message,
            "has_exclamation": "!" in user_message,
            "uppercase_ratio": sum(1 for c in user_message if c.isupper()) / max(1, len(user_message)),
            "burst_frequency": context.get("burst_frequency", 0.0),  # From message history
            "time_of_day": context.get("circadian_phase", "afternoon")
        }
        
        # Extract signature phrases (common phrases user uses)
        words = user_message.lower().split()
        if len(words) >= 2:
            # Look for 2-word phrases
            for i in range(len(words) - 1):
                phrase = f"{words[i]} {words[i+1]}"
                if phrase not in self.micro_habits["signature_words"]:
                    self.micro_habits["signature_words"][phrase] = {
                        "strength": 0.1,
                        "context": context.get("emotion", "neutral"),
                        "first_seen": datetime.now(timezone.utc).isoformat()
                    }
        
        return patterns
    
    def update_from_engagement(self, observed_patterns: Dict[str, Any], 
                              engagement_score: float, user_response: Optional[Dict[str, Any]] = None):
        """
        Update CPBM based on engagement (not direct cloning).
        Engagement > 0.7 → reinforce patterns
        Engagement < 0.3 → reduce patterns
        """
        # Update stable traits (slow drift)
        if engagement_score > 0.7:
            # Positive engagement → reinforce successful patterns
            if observed_patterns.get("emoji_density", 0) > 0.1:
                # User uses emojis → increase emoji baseline slightly
                self.stable_traits["emoji_baseline"] = min(1.0, 
                    self.stable_traits["emoji_baseline"] + 0.01)
            
            if observed_patterns.get("message_length", 0) > 100:
                # User sends long messages → increase long message preference
                self.stable_traits["long_message_preference"] = min(1.0,
                    self.stable_traits["long_message_preference"] + 0.01)
        
        elif engagement_score < 0.3:
            # Poor engagement → reduce patterns
            self.stable_traits["emoji_baseline"] = max(0.0,
                self.stable_traits["emoji_baseline"] - 0.01)
        
        # Update habit scores for observed patterns
        pattern_id = self._get_pattern_id(observed_patterns)
        if pattern_id not in self.micro_habits["habit_scores"]:
            self.micro_habits["habit_scores"][pattern_id] = 0.0
        
        # Procedural Habit Layer (PHL) - Enhanced habit formation
        # From blueprint: if engagement_signal > 0.7: pattern.habit_score += 0.05
        # Uses stochastic engagement signal (not deterministic)
        engagement_signal = engagement_score
        # Add variance (engagement detection isn't perfect)
        engagement_signal = max(0.0, min(1.0, engagement_signal + random.gauss(0, 0.1)))
        
        if engagement_signal > 0.7:
            # Positive engagement → reinforce pattern
            habit_increment = 0.05
            # Add stochastic variance (habits form at different rates)
            habit_increment = max(0.03, min(0.07, habit_increment + random.gauss(0, 0.01)))
            self.micro_habits["habit_scores"][pattern_id] += habit_increment
            self.micro_habits["habit_scores"][pattern_id] = min(1.0, 
                self.micro_habits["habit_scores"][pattern_id])
        elif engagement_signal < 0.3:
            # Poor engagement → reduce habit score (pattern not working)
            self.micro_habits["habit_scores"][pattern_id] = max(0.0,
                self.micro_habits["habit_scores"][pattern_id] - 0.02)
        
        # Promote to habit if threshold reached (stochastic threshold)
        # Threshold varies slightly (humans don't have fixed thresholds)
        threshold = HABIT_FORMATION_THRESHOLD + random.gauss(0, 0.05)
        threshold = max(0.55, min(0.65, threshold))  # Keep in reasonable range
        
        if self.micro_habits["habit_scores"][pattern_id] >= threshold:
            self._promote_to_habit(pattern_id, observed_patterns)
        
        # Decay habits over time
        self._decay_habits()
        
        self.stable_traits["last_updated"] = datetime.now(timezone.utc).isoformat()
    
    def _get_pattern_id(self, patterns: Dict[str, Any]) -> str:
        """Generate unique ID for a pattern."""
        key_features = [
            f"len_{patterns.get('message_length', 0) // 50}",  # Bucket by 50 chars
            f"emoji_{patterns.get('emoji_density', 0) > 0.1}",
            f"punct_{patterns.get('punctuation_density', 0) > 0.05}",
            f"time_{patterns.get('time_of_day', 'unknown')}"
        ]
        return "_".join(key_features)
    
    def _promote_to_habit(self, pattern_id: str, patterns: Dict[str, Any]):
        """Promote pattern to habit."""
        if pattern_id not in self.observed_patterns:
            self.observed_patterns.append({
                "pattern_id": pattern_id,
                "patterns": patterns,
                "promoted_at": datetime.now(timezone.utc).isoformat(),
                "strength": 1.0,
                "last_used": datetime.now(timezone.utc).isoformat()
            })
    
    def _decay_habits(self):
        """Decay habit strengths over time."""
        now = datetime.now(timezone.utc)
        for habit in self.observed_patterns:
            last_used_str = habit.get("last_used")
            if last_used_str:
                last_used = datetime.fromisoformat(last_used_str.replace("Z", "+00:00"))
                days_since_use = (now - last_used).total_seconds() / 86400
                # Decay: strength *= exp(-days / 30)
                habit["strength"] *= math.exp(-days_since_use / 30.0)
                habit["strength"] = max(0.0, habit["strength"])
    
    def get_style_mode(self, mood: Dict[str, float]) -> str:
        """
        Determine style mode from mood.
        Returns: excited, hurt, flirty, bored, jealous, playful, normal
        """
        excitement = mood.get("excitement", 0.0)
        hurt = mood.get("sadness", 0.0)  # Proxy for hurt
        affection = mood.get("affection", 0.0)
        boredom = mood.get("boredom", 0.0)
        playfulness = mood.get("playfulness", 0.0)
        
        if excitement > 0.7:
            return "excited"
        elif hurt > 0.6:
            return "hurt"
        elif affection > 0.7 and playfulness > 0.6:
            return "flirty"
        elif boredom > 0.7:
            return "bored"
        elif playfulness > 0.6:
            return "playful"
        else:
            return "normal"
    
    def apply_style_mode(self, base_message_config: Dict[str, Any], 
                        style_mode: str) -> Dict[str, Any]:
        """
        Apply style mode multipliers to message configuration.
        """
        multipliers = STYLE_MODE_MULTIPLIERS.get(style_mode, STYLE_MODE_MULTIPLIERS["normal"])
        
        config = base_message_config.copy()
        
        if "message_count" in multipliers:
            config["message_count"] = int(config.get("message_count", 1) * multipliers["message_count"])
        
        if "emoji" in multipliers:
            if isinstance(multipliers["emoji"], (int, float)):
                config["emoji_multiplier"] = multipliers["emoji"]
            else:
                config["emoji_override"] = multipliers["emoji"]  # e.g., "???" for jealous
        
        if "length" in multipliers:
            config["length_multiplier"] = multipliers["length"]
        
        if "tone" in multipliers:
            config["tone"] = multipliers["tone"]
        
        if "teasing" in multipliers:
            config["teasing_multiplier"] = multipliers["teasing"]
        
        if "inter_delay" in multipliers:
            config["inter_message_delay_range"] = multipliers["inter_delay"]
        
        if "burst" in multipliers and multipliers["burst"]:
            config["burst_mode"] = True
        
        return config
    
    def get_micro_habits_for_message(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get micro-habits to apply to current message.
        Returns: signature phrases, emoji patterns, typo probability, etc.
        """
        habits = {
            "signature_phrases": [],
            "emoji_patterns": [],
            "typo_probability": self.micro_habits["typo_playfulness"],
            "double_text_probability": self.micro_habits["double_text_habit"]
        }
        
        # Get signature phrases for current context
        emotion = context.get("emotion", "neutral")
        for phrase, data in self.micro_habits["signature_words"].items():
            if data.get("context") == emotion and data.get("strength", 0) > 0.3:
                habits["signature_phrases"].append(phrase)
        
        # Get emoji patterns for current context
        for emoji, data in self.micro_habits["emoji_patterns"].items():
            if data.get("strength", 0) > 0.3:
                habits["emoji_patterns"].append(emoji)
        
        return habits
    
    def save_to_state(self):
        """Save CPBM back to state."""
        if "habits_cpbm" not in self.state:
            self.state["habits_cpbm"] = {}
        
        self.state["habits_cpbm"].update({
            "long_message_preference": self.stable_traits["long_message_preference"],
            "emoji_baseline": self.stable_traits["emoji_baseline"],
            "teasing_style": self.stable_traits["teasing_style"],
            "humor_frequency": self.stable_traits["humor_frequency"],
            "punctuation_style": self.stable_traits["punctuation_style"],
            "formality_baseline": self.stable_traits["formality_baseline"],
            "typo_intentionality": self.stable_traits["typo_intentionality"],
            "style_mode": self.style_mode,
            "signature_words": self.micro_habits["signature_words"],
            "emoji_patterns": self.micro_habits["emoji_patterns"],
            "typo_playfulness": self.micro_habits["typo_playfulness"],
            "double_text_habit": self.micro_habits["double_text_habit"],
            "greeting_patterns": self.micro_habits["greeting_patterns"],
            "habit_scores": self.micro_habits["habit_scores"],
            "observed_patterns": self.observed_patterns,
            "last_updated": self.stable_traits["last_updated"]
        })

