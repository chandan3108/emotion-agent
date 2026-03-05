"""
Message Sequence Planner - Behavioral Choreography
Stochastic burst patterns, typing simulation, and micro-behaviors.
"""

import random
import math
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone
import numpy as np

# Base typing speeds (WPM) - will vary stochastically
BASE_WPM_MIN = 35
BASE_WPM_MAX = 65
BASE_WPM_MEAN = 45

# Burst pattern configurations (mood-driven, but stochastic)
BURST_PATTERNS = {
    "excited": {
        "message_count": (2, 4),  # Range, not fixed
        "inter_delay": (1, 6),  # seconds, sampled
        "typing_speed_multiplier": (1.1, 1.3)  # Faster when excited
    },
    "hurt": {
        "message_count": (1, 1),  # Single message
        "inter_delay": (30, 60),  # Longer delay
        "typing_speed_multiplier": (0.8, 1.0),  # Slower
        "typing_time_multiplier": 1.5  # Show typing longer
    },
    "playful": {
        "message_count": (2, 3),
        "inter_delay": (3, 10),
        "typing_speed_multiplier": (1.0, 1.2)
    },
    "jealous": {
        "message_count": (1, 3),  # Variable
        "inter_delay": (120, 300),  # 2-5 minutes
        "follow_up_pattern": "pointed"
    },
    "bored": {
        "message_count": (1, 2),
        "inter_delay": (10, 30),
        "randomness": 2.0
    },
    "normal": {
        "message_count": (1, 2),
        "inter_delay": (5, 15),
        "typing_speed_multiplier": (0.9, 1.1)
    }
}


class MessageSequencePlanner:
    """
    Plans message sequences with stochastic timing and burst patterns.
    """
    
    def __init__(self, state: Dict[str, Any]):
        self.state = state
    
    def plan_sequence(self, mood: Dict[str, float], style_mode: str,
                     personality: Dict[str, Any], energy: float = 0.5) -> Dict[str, Any]:
        """
        Plan message sequence based on mood and style.
        Returns stochastic plan (not fixed).
        """
        # Get burst pattern for style mode
        pattern_config = BURST_PATTERNS.get(style_mode, BURST_PATTERNS["normal"])
        
        # Sample message count from distribution
        msg_count_range = pattern_config.get("message_count", (1, 2))
        if isinstance(msg_count_range, tuple):
            # Sample from range (not uniform, but weighted)
            msg_count_mean = (msg_count_range[0] + msg_count_range[1]) / 2
            msg_count_std = (msg_count_range[1] - msg_count_range[0]) / 4
            msg_count = max(msg_count_range[0], min(msg_count_range[1], 
                int(np.random.normal(msg_count_mean, msg_count_std))))
        else:
            msg_count = msg_count_range
        
        # Sample inter-message delays
        inter_delays = []
        delay_range = pattern_config.get("inter_delay", (5, 15))
        for i in range(msg_count - 1):
            # Sample delay from distribution (not uniform)
            delay_mean = (delay_range[0] + delay_range[1]) / 2
            delay_std = (delay_range[1] - delay_range[0]) / 3
            delay = max(delay_range[0], min(delay_range[1], 
                np.random.normal(delay_mean, delay_std)))
            inter_delays.append(float(delay))
        
        # Calculate typing speeds (stochastic per message)
        typing_speeds = []
        speed_mult_range = pattern_config.get("typing_speed_multiplier", (0.9, 1.1))
        if isinstance(speed_mult_range, tuple):
            speed_mult_mean = (speed_mult_range[0] + speed_mult_range[1]) / 2
            speed_mult_std = (speed_mult_range[1] - speed_mult_range[0]) / 4
        else:
            speed_mult_mean = speed_mult_range
            speed_mult_std = 0.1
        
        for i in range(msg_count):
            # Base WPM varies per message (humans don't type at constant speed)
            base_wpm = np.random.normal(BASE_WPM_MEAN, 5)  # ±5 WPM variance
            base_wpm = max(BASE_WPM_MIN, min(BASE_WPM_MAX, base_wpm))
            
            # Apply mood/energy multiplier (stochastic)
            speed_mult = max(0.5, min(1.5, np.random.normal(speed_mult_mean, speed_mult_std)))
            energy_mult = 0.6 + 0.4 * energy  # Energy affects typing speed
            
            final_wpm = base_wpm * speed_mult * energy_mult
            typing_speeds.append(max(20, min(80, final_wpm)))  # Cap at reasonable range
        
        return {
            "message_count": msg_count,
            "inter_message_delays": inter_delays,
            "typing_speeds_wpm": typing_speeds,
            "style_mode": style_mode,
            "pattern_config": pattern_config,
            "energy": energy
        }
    
    def calculate_typing_time(self, message_text: str, wpm: float, 
                             energy: float = 0.5) -> float:
        """
        Calculate typing time for a message.
        Includes stochastic variance.
        """
        char_count = len(message_text)
        words = len(message_text.split())
        
        # Base time from WPM
        base_time_seconds = (words / wpm) * 60
        
        # Add variance (humans don't type at constant speed)
        time_variance = base_time_seconds * 0.15  # 15% variance
        actual_time = max(0.5, base_time_seconds + np.random.normal(0, time_variance))
        
        # Energy affects typing (tired = slower, more pauses)
        if energy < 0.3:
            # Exhausted: slower, more pauses
            pause_time = np.random.exponential(0.5)  # Random pauses
            actual_time += pause_time
        
        # Add small random jitter (avoid robotic consistency)
        jitter = np.random.normal(0, 0.3)
        actual_time += jitter
        
        return max(0.5, actual_time)
    
    def inject_micro_behaviors(self, message_text: str, energy: float,
                              cpbm_habits: Dict[str, Any]) -> str:
        """
        Inject micro-behaviors stochastically.
        NOTE: Typo injection disabled as it hurts readability more than it helps realism.
        """
        # Return message as-is - typos and signature phrases were causing more harm than good
        return message_text
    
    def _inject_typo(self, text: str) -> str:
        """
        Inject a realistic typo (stochastic selection).
        """
        if len(text) < 5:
            return text
        
        # Common typo patterns
        typo_types = [
            "char_swap",  # "teh" instead of "the"
            "char_drop",  # "th" instead of "the"
            "char_add",   # "thee" instead of "the"
            "case_error"  # "The" instead of "the" (mid-sentence)
        ]
        
        typo_type = random.choice(typo_types)
        words = text.split()
        
        if not words:
            return text
        
        # Pick random word (but not first or last usually)
        word_idx = random.randint(max(0, len(words) - 3), min(len(words) - 1, len(words) - 1))
        word = words[word_idx]
        
        if typo_type == "char_swap" and len(word) > 2:
            # Swap two adjacent characters
            idx = random.randint(0, len(word) - 2)
            word = word[:idx] + word[idx+1] + word[idx] + word[idx+2:]
        elif typo_type == "char_drop" and len(word) > 2:
            # Drop a character
            idx = random.randint(1, len(word) - 1)
            word = word[:idx] + word[idx+1:]
        elif typo_type == "char_add" and len(word) > 1:
            # Add a character
            idx = random.randint(1, len(word))
            char = random.choice("abcdefghijklmnopqrstuvwxyz")
            word = word[:idx] + char + word[idx:]
        elif typo_type == "case_error" and word[0].isupper():
            # Wrong case
            word = word[0].lower() + word[1:]
        
        words[word_idx] = word
        return " ".join(words)
    
    def plan_burst_sequence(self, messages: List[str], sequence_plan: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Plan full burst sequence with timing.
        Returns list of message delivery instructions.
        """
        delivery_plan = []
        cumulative_delay = 0.0
        
        for i, message in enumerate(messages):
            wpm = sequence_plan["typing_speeds_wpm"][i] if i < len(sequence_plan["typing_speeds_wpm"]) else BASE_WPM_MEAN
            energy = sequence_plan.get("energy", 0.5)
            
            typing_time = self.calculate_typing_time(message, wpm, energy)
            
            delivery_plan.append({
                "message": message,
                "typing_time_seconds": typing_time,
                "send_after_delay": cumulative_delay,
                "wpm": wpm
            })
            
            # Add inter-message delay (if not last message)
            if i < len(messages) - 1:
                inter_delay = sequence_plan["inter_message_delays"][i] if i < len(sequence_plan["inter_message_delays"]) else 5.0
                cumulative_delay += typing_time + inter_delay
        
        return delivery_plan




