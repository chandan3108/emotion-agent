"""
Embodiment State & Energy Budgeting
Stochastic energy fluctuations with fatigue and capacity modeling.
"""

import random
import math
from typing import Dict, Any, Optional
from datetime import datetime, timezone, timedelta
import numpy as np

# Energy ranges (stochastic)
ENERGY_RANGES = {
    "exhausted": (0.0, 0.2),
    "fatigued": (0.2, 0.4),
    "normal": (0.4, 0.7),
    "energized": (0.7, 0.9),
    "peak": (0.9, 1.0)
}

# Circadian baseline (varies by hour, stochastic)
def get_circadian_baseline(hour: int) -> float:
    """Get circadian baseline energy (stochastic per hour)."""
    # Simplified circadian curve
    if 6 <= hour < 10:  # Morning
        mean = 0.4
        std = 0.1
    elif 10 <= hour < 14:  # Midday
        mean = 0.6
        std = 0.1
    elif 14 <= hour < 18:  # Afternoon
        mean = 0.7
        std = 0.15
    elif 18 <= hour < 22:  # Evening
        mean = 0.8
        std = 0.1
    elif 22 <= hour < 24 or 0 <= hour < 6:  # Late night / early morning
        mean = 0.3
        std = 0.15
    else:
        mean = 0.5
        std = 0.1
    
    return max(0.0, min(1.0, np.random.normal(mean, std)))


class EmbodimentState:
    """
    Embodiment state with stochastic energy budgeting.
    """
    
    def __init__(self, state: Dict[str, Any]):
        self.state = state
        self._init_embodiment()
    
    def _init_embodiment(self):
        """Initialize embodiment state."""
        if "embodiment" not in self.state:
            self.state["embodiment"] = {}
        
        emb = self.state["embodiment"]
        self.E_daily = emb.get("E_daily", 0.7)  # Fresh start = rested, not tired
        self.capacity = emb.get("capacity", 0.0)  # No accumulated fatigue on fresh start
        self.sleep_debt = emb.get("sleep_debt", 0.0)
        self.last_update = emb.get("last_update", datetime.now(timezone.utc).isoformat())
        self.message_count_recent = emb.get("message_count_recent", 0)
        self.last_message_time = emb.get("last_message_time")
    
    def update_energy(self, mood: Dict[str, float], delta_hours: float = 0.0):
        """
        Update energy budget with stochastic fluctuations.
        
        E_daily = circadian_baseline(hour) × sleep_debt_multiplier × mood_energy_factor
        """
        now = datetime.now(timezone(timedelta(hours=5, minutes=30)))  # IST
        hour = now.hour
        
        # Circadian baseline (stochastic)
        circadian_base = get_circadian_baseline(hour)
        
        # Sleep debt multiplier (stochastic decay)
        sleep_debt_mult_mean = 1.0 - (self.sleep_debt * 0.3)  # Max 30% reduction
        sleep_debt_mult_std = 0.05
        sleep_debt_multiplier = max(0.5, min(1.0, 
            np.random.normal(sleep_debt_mult_mean, sleep_debt_mult_std)))
        
        # Mood energy factor (stochastic)
        energy_mood = mood.get("energy", 0.5)
        stress_mood = mood.get("stress", 0.3)
        mood_energy_factor_mean = energy_mood * (1 - stress_mood * 0.5)
        mood_energy_factor_std = 0.1
        mood_energy_factor = max(0.3, min(1.2, 
            np.random.normal(mood_energy_factor_mean, mood_energy_factor_std)))
        
        # Compute E_daily (with noise)
        E_mean = circadian_base * sleep_debt_multiplier * mood_energy_factor
        E_std = 0.1  # Natural variance
        self.E_daily = max(0.0, min(1.0, np.random.normal(E_mean, E_std)))
        
        # Update sleep debt (stochastic accumulation)
        if delta_hours > 0:
            # Sleep debt increases if E_daily is low (tired)
            if self.E_daily < 0.4:
                debt_increase_mean = delta_hours * 0.01
                debt_increase_std = debt_increase_mean * 0.3
                self.sleep_debt = min(1.0, self.sleep_debt + 
                    max(0.0, np.random.normal(debt_increase_mean, debt_increase_std)))
            else:
                # Recover sleep debt (stochastic)
                recovery_rate_mean = delta_hours * 0.005
                recovery_rate_std = recovery_rate_mean * 0.5
                self.sleep_debt = max(0.0, self.sleep_debt - 
                    max(0.0, np.random.normal(recovery_rate_mean, recovery_rate_std)))
        
        self.last_update = now.isoformat()
    
    def update_capacity(self, message_sent: bool = False):
        """
        Update interaction capacity (fatigue accumulation).
        Stochastic - not all messages cause equal fatigue.
        """
        now = datetime.now(timezone.utc)
        
        if message_sent:
            self.message_count_recent += 1
            self.last_message_time = now.isoformat()
        
        # Decay capacity over time (stochastic)
        if self.last_message_time:
            last_time = datetime.fromisoformat(self.last_message_time.replace("Z", "+00:00"))
            hours_since = (now - last_time).total_seconds() / 3600
            
            # Exponential decay with stochastic rate
            decay_rate_mean = 0.1  # per hour
            decay_rate_std = 0.02
            decay_rate = max(0.0, np.random.normal(decay_rate_mean, decay_rate_std))
            self.capacity *= math.exp(-decay_rate * hours_since)
        
        # Accumulate capacity from recent messages (stochastic)
        tau_capacity = 2.0  # hours (but varies)
        max_capacity = 1.0
        
        if self.message_count_recent > 0:
            # Fatigue per message (varies)
            fatigue_per_message_mean = 0.1
            fatigue_per_message_std = 0.03
            fatigue_per_message = max(0.0, 
                np.random.normal(fatigue_per_message_mean, fatigue_per_message_std))
            
            capacity_increase = (self.message_count_recent * fatigue_per_message) / tau_capacity
            self.capacity = min(max_capacity, self.capacity + capacity_increase)
        
        # Reset message count if enough time passed
        if self.last_message_time:
            last_time = datetime.fromisoformat(self.last_message_time.replace("Z", "+00:00"))
            if (now - last_time).total_seconds() > 3600:  # 1 hour
                self.message_count_recent = max(0, self.message_count_recent - 1)
    
    def get_body_state(self) -> str:
        """
        Get current body state (stochastic classification).
        """
        # Sample from distribution based on E_daily
        if self.E_daily <= 0.2:
            return "exhausted"
        elif self.E_daily <= 0.4:
            return "fatigued"
        elif self.E_daily <= 0.7:
            return "normal"
        elif self.E_daily <= 0.9:
            return "energized"
        else:
            return "peak"
    
    def get_typing_wpm(self, base_wpm: float = 45, personality_wpm_factor: float = 1.0) -> float:
        """
        Calculate typing WPM (stochastic).
        
        typing_wpm_actual = base_wpm × (0.6 + 0.4 × E) × personality_wpm_factor
        """
        # Energy multiplier (stochastic)
        energy_mult_mean = 0.6 + 0.4 * self.E_daily
        energy_mult_std = 0.1
        energy_mult = max(0.4, min(1.0, np.random.normal(energy_mult_mean, energy_mult_std)))
        
        # Personality factor (varies)
        personality_mult_mean = personality_wpm_factor
        personality_mult_std = 0.1
        personality_mult = max(0.7, min(1.3, 
            np.random.normal(personality_mult_mean, personality_mult_std)))
        
        wpm = base_wpm * energy_mult * personality_mult
        
        # Add final variance
        wpm += np.random.normal(0, 3)  # ±3 WPM variance
        
        return max(20, min(80, wpm))  # Cap at reasonable range
    
    def get_typo_probability(self) -> float:
        """
        Get typo probability based on energy (stochastic).
        
        if E < 0.3:
            typo_probability = (1 - E) × 0.5
        """
        if self.E_daily < 0.3:
            base_prob = (1 - self.E_daily) * 0.5
            # Add variance
            prob_std = 0.1
            return max(0.0, min(0.5, np.random.normal(base_prob, prob_std)))
        else:
            # Low probability even when not exhausted (humans make typos)
            return max(0.0, min(0.1, np.random.normal(0.05, 0.02)))
    
    def should_signal_overload(self) -> bool:
        """
        Check if should signal overload (stochastic).
        """
        if self.capacity > 1.0:
            # Definitely overloaded
            return True
        
        # Sometimes signal even if capacity < 1.0 (humans get tired unpredictably)
        if self.capacity > 0.8:
            signal_prob = 0.3  # 30% chance
            if random.random() < signal_prob:
                return True
        
        return False
    
    def get_energy_modulated_behavior(self) -> Dict[str, Any]:
        """
        Get behavior modifications based on energy state (stochastic).
        """
        body_state = self.get_body_state()
        
        behaviors = {
            "exhausted": {
                "message_length_multiplier": (0.5, 0.1),  # (mean, std)
                "emoji_multiplier": (0.3, 0.1),
                "initiative_multiplier": (0.2, 0.1),
                "typo_probability": (0.4, 0.1),
                "response_delay_multiplier": (1.5, 0.2)
            },
            "fatigued": {
                "message_length_multiplier": (0.7, 0.1),
                "emoji_multiplier": (0.6, 0.1),
                "initiative_multiplier": (0.5, 0.1),
                "typo_probability": (0.25, 0.1),
                "response_delay_multiplier": (1.2, 0.15)
            },
            "normal": {
                "message_length_multiplier": (1.0, 0.1),
                "emoji_multiplier": (1.0, 0.1),
                "initiative_multiplier": (1.0, 0.1),
                "typo_probability": (0.1, 0.05),
                "response_delay_multiplier": (1.0, 0.1)
            },
            "energized": {
                "message_length_multiplier": (1.2, 0.1),
                "emoji_multiplier": (1.3, 0.1),
                "initiative_multiplier": (1.4, 0.15),
                "typo_probability": (0.05, 0.02),
                "response_delay_multiplier": (0.8, 0.1)
            },
            "peak": {
                "message_length_multiplier": (1.5, 0.15),
                "emoji_multiplier": (1.6, 0.15),
                "initiative_multiplier": (1.8, 0.2),
                "typo_probability": (0.02, 0.01),
                "response_delay_multiplier": (0.7, 0.1)
            }
        }
        
        config = behaviors.get(body_state, behaviors["normal"])
        
        # Sample each multiplier from distribution
        result = {}
        for key, (mean, std) in config.items():
            if "multiplier" in key:
                result[key] = max(0.1, min(2.0, np.random.normal(mean, std)))
            elif "probability" in key:
                result[key] = max(0.0, min(1.0, np.random.normal(mean, std)))
            else:
                result[key] = max(0.5, min(2.0, np.random.normal(mean, std)))
        
        return result
    
    def save_to_state(self):
        """Save embodiment state back to state."""
        self.state["embodiment"] = {
            "E_daily": self.E_daily,
            "capacity": self.capacity,
            "sleep_debt": self.sleep_debt,
            "last_update": self.last_update,
            "message_count_recent": self.message_count_recent,
            "last_message_time": self.last_message_time
        }




