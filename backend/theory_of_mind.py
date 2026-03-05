"""
Theory of Mind & Empathy Engine
Probabilistic user state predictions and empathy-based action selection.
"""

import random
import math
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone, timedelta
import numpy as np

# Empathy utility weights (but we'll sample from distributions)
WEIGHT_TRUST = 0.3
WEIGHT_ENGAGEMENT = 0.25
WEIGHT_LONG_TERM = 0.20
WEIGHT_COMFORT = 0.15
WEIGHT_ANNOYANCE = -0.15
WEIGHT_RISK = -0.10

# Circadian receptivity modifiers (stochastic)
CIRCADIAN_RECEPTIVITY = {
    "morning": (0.3, 0.1),  # (mean, std) - tired/rushed
    "afternoon": (0.6, 0.15),  # moderate
    "evening": (0.8, 0.1),  # relaxed
    "late_night": (0.7, 0.15)  # vulnerable/playful
}


class TheoryOfMind:
    """
    Theory of Mind engine with probabilistic user state predictions.
    """
    
    def __init__(self, state: Dict[str, Any]):
        self.state = state
        self._init_tom_state()
    
    def _init_tom_state(self):
        """Initialize ToM state."""
        if "theory_of_mind" not in self.state:
            self.state["theory_of_mind"] = {}
        
        tom = self.state["theory_of_mind"]
        self.user_emotional_state_dist = tom.get("user_emotional_state_dist", {})
        self.reply_patterns = tom.get("reply_patterns", {})  # Per circadian phase
        self.availability_patterns = tom.get("availability_patterns", {})
        self.receptivity_history = tom.get("receptivity_history", [])
    
    def predict_user_state(self, temporal_context: Dict[str, Any],
                          memory_system: Any, recent_interactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Predict user's current state using probabilistic distributions.
        """
        circadian_phase = temporal_context.get("circadian_phase", "afternoon")
        
        # Predict emotional state (distribution, not single value)
        emotional_state = self._predict_emotional_state(recent_interactions)
        
        # Predict reply likelihood (stochastic)
        reply_5min = self._predict_reply_likelihood(5, circadian_phase, recent_interactions)
        reply_30min = self._predict_reply_likelihood(30, circadian_phase, recent_interactions)
        
        # Predict availability (probabilistic)
        availability = self._predict_availability(circadian_phase, temporal_context)
        
        # Predict receptivity (distribution-based)
        receptivity = self._predict_receptivity(circadian_phase, temporal_context, recent_interactions)
        
        # Predict other states (stochastic)
        repair_likelihood = self._predict_repair_likelihood(memory_system)
        vulnerability_receptiveness = self._predict_vulnerability_receptiveness(recent_interactions)
        humor_receptiveness = self._predict_humor_receptiveness(recent_interactions)
        
        # Expected message length (distribution)
        expected_length = self._predict_message_length(recent_interactions)
        
        return {
            "user_emotional_state_dist": emotional_state,
            "likelihood_of_reply_5min": reply_5min,
            "likelihood_of_reply_30min": reply_30min,
            "likely_availability": availability,
            "openness_to_initiative": receptivity,
            "likelihood_of_repair_after_conflict": repair_likelihood,
            "vulnerability_receptiveness": vulnerability_receptiveness,
            "humor_receptiveness": humor_receptiveness,
            "expected_message_length": expected_length,
            "predicted_circadian_state": circadian_phase,
            "fatigue_level": self._predict_fatigue(circadian_phase),
            "stress_level": self._predict_stress(recent_interactions),
            "emotional_stability": self._predict_emotional_stability(recent_interactions)
        }
    
    def _predict_emotional_state(self, recent_interactions: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Predict emotional state distribution (not single emotion).
        """
        if not recent_interactions:
            # Default distribution
            return {
                "neutral": 0.5,
                "happy": 0.2,
                "stressed": 0.1,
                "sad": 0.1,
                "angry": 0.05,
                "excited": 0.05
            }
        
        # Aggregate from recent interactions (with decay)
        emotion_counts = {}
        total_weight = 0.0
        
        for i, interaction in enumerate(recent_interactions[-5:]):  # Last 5
            weight = math.exp(-i * 0.3)  # Exponential decay
            emotion = interaction.get("emotion", "neutral")
            emotion_counts[emotion] = emotion_counts.get(emotion, 0.0) + weight
            total_weight += weight
        
        # Normalize to distribution
        if total_weight > 0:
            distribution = {k: v / total_weight for k, v in emotion_counts.items()}
        else:
            distribution = {"neutral": 1.0}
        
        # Add noise (uncertainty in prediction)
        noise_std = 0.1
        for emotion in distribution:
            distribution[emotion] = max(0.0, min(1.0, 
                distribution[emotion] + np.random.normal(0, noise_std)))
        
        # Renormalize
        total = sum(distribution.values())
        if total > 0:
            distribution = {k: v / total for k, v in distribution.items()}
        
        return distribution
    
    def _predict_reply_likelihood(self, minutes: int, circadian_phase: str,
                                 recent_interactions: List[Dict[str, Any]]) -> float:
        """
        Predict reply likelihood (stochastic).
        """
        # Base likelihood from circadian phase
        phase_mean, phase_std = CIRCADIAN_RECEPTIVITY.get(circadian_phase, (0.5, 0.15))
        base_likelihood = np.random.normal(phase_mean, phase_std)
        
        # Adjust for time window
        if minutes == 5:
            # Short window: lower likelihood
            base_likelihood *= 0.6
        elif minutes == 30:
            # Longer window: higher likelihood
            base_likelihood *= 1.2
        
        # Adjust based on historical patterns (if available)
        if recent_interactions:
            avg_reply_time = self._get_avg_reply_time(recent_interactions)
            if avg_reply_time < 10:  # Fast replier
                base_likelihood *= 1.2
            elif avg_reply_time > 60:  # Slow replier
                base_likelihood *= 0.7
        
        return max(0.0, min(1.0, base_likelihood))
    
    def _predict_availability(self, circadian_phase: str,
                            temporal_context: Dict[str, Any]) -> str:
        """
        Predict availability (probabilistic classification).
        """
        # Sample from distribution
        if circadian_phase == "morning":
            # More likely busy
            probs = {"free": 0.3, "busy": 0.6, "sleeping": 0.1}
        elif circadian_phase == "late_night":
            # More likely free but maybe sleeping
            probs = {"free": 0.5, "busy": 0.2, "sleeping": 0.3}
        elif circadian_phase == "evening":
            # More likely free
            probs = {"free": 0.7, "busy": 0.2, "sleeping": 0.1}
        else:  # afternoon
            probs = {"free": 0.5, "busy": 0.4, "sleeping": 0.1}
        
        # Sample from distribution
        rand = random.random()
        cumsum = 0.0
        for state, prob in probs.items():
            cumsum += prob
            if rand <= cumsum:
                return state
        
        return "free"  # Default
    
    def _predict_receptivity(self, circadian_phase: str, temporal_context: Dict[str, Any],
                           recent_interactions: List[Dict[str, Any]]) -> float:
        """
        Predict receptivity to initiative (distribution-based).
        """
        # Base from circadian
        phase_mean, phase_std = CIRCADIAN_RECEPTIVITY.get(circadian_phase, (0.5, 0.15))
        receptivity = np.random.normal(phase_mean, phase_std)
        
        # Adjust based on recent engagement
        if recent_interactions:
            recent_engagement = np.mean([i.get("engagement", 0.5) for i in recent_interactions[-3:]])
            receptivity = 0.7 * receptivity + 0.3 * recent_engagement
        
        return max(0.0, min(1.0, receptivity))
    
    def _predict_repair_likelihood(self, memory_system: Any) -> float:
        """
        Predict likelihood of repair after conflict (stochastic).
        """
        # Would use conflict history from memory
        # For now, sample from distribution
        base_likelihood = 0.6
        std = 0.2
        return max(0.0, min(1.0, np.random.normal(base_likelihood, std)))
    
    def _predict_vulnerability_receptiveness(self, recent_interactions: List[Dict[str, Any]]) -> float:
        """Predict receptiveness to vulnerability (stochastic)."""
        base = 0.5
        std = 0.15
        # Adjust based on recent vulnerability exchanges
        if recent_interactions:
            has_vulnerability = any("vulnerability" in str(i).lower() for i in recent_interactions[-3:])
            if has_vulnerability:
                base = 0.7  # More receptive if recently shared
        
        return max(0.0, min(1.0, np.random.normal(base, std)))
    
    def _predict_humor_receptiveness(self, recent_interactions: List[Dict[str, Any]]) -> float:
        """Predict receptiveness to humor (stochastic)."""
        base = 0.6
        std = 0.15
        # Adjust based on recent humor
        if recent_interactions:
            has_humor = any("lol" in str(i).lower() or "haha" in str(i).lower() for i in recent_interactions[-3:])
            if has_humor:
                base = 0.8
        
        return max(0.0, min(1.0, np.random.normal(base, std)))
    
    def _predict_message_length(self, recent_interactions: List[Dict[str, Any]]) -> int:
        """Predict expected message length (distribution)."""
        if recent_interactions:
            lengths = [len(str(i.get("message", ""))) for i in recent_interactions[-5:]]
            if lengths:
                mean_length = np.mean(lengths)
                std_length = np.std(lengths) if len(lengths) > 1 else mean_length * 0.3
                predicted = max(10, int(np.random.normal(mean_length, std_length)))
                return predicted
        
        # Default distribution
        return int(np.random.normal(50, 20))  # Mean 50, std 20
    
    def _predict_fatigue(self, circadian_phase: str) -> float:
        """Predict user fatigue level (stochastic)."""
        if circadian_phase == "morning":
            base = 0.6  # Tired
        elif circadian_phase == "late_night":
            base = 0.5  # Moderate
        else:
            base = 0.3  # Less tired
        
        return max(0.0, min(1.0, np.random.normal(base, 0.15)))
    
    def _predict_stress(self, recent_interactions: List[Dict[str, Any]]) -> float:
        """Predict user stress level (stochastic)."""
        base = 0.3
        if recent_interactions:
            # Check for stress indicators
            stress_indicators = sum(1 for i in recent_interactions[-3:] 
                                  if "stress" in str(i).lower() or "busy" in str(i).lower())
            if stress_indicators > 0:
                base = 0.5
        
        return max(0.0, min(1.0, np.random.normal(base, 0.15)))
    
    def _predict_emotional_stability(self, recent_interactions: List[Dict[str, Any]]) -> float:
        """Predict emotional stability (stochastic)."""
        base = 0.7
        if recent_interactions:
            # Check for volatility
            emotions = [i.get("emotion", "neutral") for i in recent_interactions[-5:]]
            if len(set(emotions)) > 3:  # Many different emotions = volatile
                base = 0.5
        
        return max(0.0, min(1.0, np.random.normal(base, 0.15)))
    
    def _get_avg_reply_time(self, interactions: List[Dict[str, Any]]) -> float:
        """Get average reply time in minutes."""
        reply_times = []
        for i in range(1, len(interactions)):
            if "timestamp" in interactions[i] and "timestamp" in interactions[i-1]:
                # Would calculate time delta
                pass
        return 15.0  # Default
    
    def score_empathy_actions(self, candidate_actions: List[Dict[str, Any]],
                              tom_state: Dict[str, Any], psyche_state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Score candidate actions using empathy utility function.
        Uses stochastic scoring.
        
        U(action) = wtrust × E[Δtrust] + weng × E[engagement] + wlong × E[long_term_rel_health] 
                    + wcomfort × E[comfort] - wann × E[annoyance] - wrisk × E[rejection_risk]
        """
        scored_actions = []
        
        for action in candidate_actions:
            action_type = action.get("type", "unknown")
            
            # Predict effects (stochastic)
            trust_delta = self._predict_trust_delta(action_type, tom_state, psyche_state)
            engagement = self._predict_engagement(action_type, tom_state)
            long_term_health = self._predict_long_term_health(action_type, psyche_state)
            comfort = self._predict_comfort(action_type, tom_state)
            annoyance = self._predict_annoyance(action_type, tom_state)
            rejection_risk = self._predict_rejection_risk(action_type, tom_state, psyche_state)
            
            # Sample weights from distributions (not fixed)
            w_trust = np.random.normal(WEIGHT_TRUST, 0.05)
            w_eng = np.random.normal(WEIGHT_ENGAGEMENT, 0.05)
            w_long = np.random.normal(WEIGHT_LONG_TERM, 0.05)
            w_comfort = np.random.normal(WEIGHT_COMFORT, 0.05)
            w_ann = abs(np.random.normal(WEIGHT_ANNOYANCE, 0.05))
            w_risk = abs(np.random.normal(WEIGHT_RISK, 0.05))
            
            # Calculate utility (stochastic)
            utility = (w_trust * trust_delta + 
                      w_eng * engagement + 
                      w_long * long_term_health + 
                      w_comfort * comfort - 
                      w_ann * annoyance - 
                      w_risk * rejection_risk)
            
            scored_actions.append({
                **action,
                "utility_score": utility,
                "predicted_effects": {
                    "trust_delta": trust_delta,
                    "engagement": engagement,
                    "long_term_health": long_term_health,
                    "comfort": comfort,
                    "annoyance": annoyance,
                    "rejection_risk": rejection_risk
                }
            })
        
        # Sort by utility (but add some randomness - humans don't always choose optimal)
        scored_actions.sort(key=lambda x: x["utility_score"], reverse=True)
        
        # Add selection probability (not always pick top)
        for i, action in enumerate(scored_actions):
            # Top action: 60% probability, 2nd: 25%, 3rd: 10%, rest: 5%
            if i == 0:
                action["selection_probability"] = 0.6
            elif i == 1:
                action["selection_probability"] = 0.25
            elif i == 2:
                action["selection_probability"] = 0.10
            else:
                action["selection_probability"] = 0.05 / max(1, len(scored_actions) - 3)
        
        return scored_actions
    
    def _predict_trust_delta(self, action_type: str, tom_state: Dict[str, Any],
                           psyche_state: Dict[str, Any]) -> float:
        """Predict trust delta (stochastic)."""
        # Sample from distribution based on action type
        if action_type == "comfort":
            return np.random.normal(0.1, 0.05)
        elif action_type == "vulnerability":
            return np.random.normal(0.15, 0.08)
        elif action_type == "challenge":
            return np.random.normal(-0.05, 0.1)  # Can decrease trust
        else:
            return np.random.normal(0.0, 0.05)
    
    def _predict_engagement(self, action_type: str, tom_state: Dict[str, Any]) -> float:
        """Predict engagement (stochastic)."""
        base_engagement = tom_state.get("openness_to_initiative", 0.5)
        
        if action_type == "humor":
            return np.random.normal(base_engagement + 0.2, 0.1)
        elif action_type == "curiosity":
            return np.random.normal(base_engagement + 0.1, 0.1)
        else:
            return np.random.normal(base_engagement, 0.1)
    
    def _predict_long_term_health(self, action_type: str, psyche_state: Dict[str, Any]) -> float:
        """Predict long-term relationship health (stochastic)."""
        if action_type in ["comfort", "vulnerability", "repair"]:
            return np.random.normal(0.7, 0.15)
        else:
            return np.random.normal(0.5, 0.15)
    
    def _predict_comfort(self, action_type: str, tom_state: Dict[str, Any]) -> float:
        """Predict comfort provided (stochastic)."""
        if action_type == "comfort":
            return np.random.normal(0.8, 0.1)
        elif action_type == "vulnerability":
            return np.random.normal(0.6, 0.15)
        else:
            return np.random.normal(0.4, 0.15)
    
    def _predict_annoyance(self, action_type: str, tom_state: Dict[str, Any]) -> float:
        """Predict annoyance caused (stochastic)."""
        if action_type == "challenge":
            return np.random.normal(0.3, 0.15)
        elif action_type == "playful_pursuit":
            return np.random.normal(0.2, 0.1)
        else:
            return np.random.normal(0.1, 0.05)
    
    def _predict_rejection_risk(self, action_type: str, tom_state: Dict[str, Any],
                               psyche_state: Dict[str, Any]) -> float:
        """Predict rejection risk (stochastic)."""
        trust = psyche_state.get("trust", 0.7)
        
        if action_type == "vulnerability":
            # Higher risk if trust is low
            base_risk = 0.3 - (trust * 0.2)
            return max(0.0, min(1.0, np.random.normal(base_risk, 0.1)))
        else:
            return np.random.normal(0.1, 0.05)
    
    def save_to_state(self):
        """Save ToM state back to state."""
        self.state["theory_of_mind"] = {
            "user_emotional_state_dist": self.user_emotional_state_dist,
            "reply_patterns": self.reply_patterns,
            "availability_patterns": self.availability_patterns,
            "receptivity_history": self.receptivity_history[-50:]  # Keep last 50
        }




