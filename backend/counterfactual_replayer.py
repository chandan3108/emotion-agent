"""
Counterfactual Replayer (Stage 17)
Simulates alternatives for major episodes, tunes parameters.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import numpy as np


class CounterfactualReplayer:
    """
    Simulates alternative responses for major episodes.
    Evaluates long-term trust outcomes and adjusts parameters.
    """
    
    def __init__(self, state: Dict[str, Any]):
        self.state = state
        self.major_episodes = state.get("major_episodes", [])
    
    def identify_major_episode(self, context: Dict[str, Any]) -> bool:
        """
        Identify if current situation is a major episode worth replaying.
        
        Major episodes:
        - Conflicts (hurt > 0.6)
        - Trust violations (trust_delta < -0.2)
        - Deep disclosures (vulnerability > 0.7)
        - Relationship phase transitions
        
        Returns:
            True if major episode, False otherwise
        """
        hurt = context.get("hurt", 0.0)
        trust_delta = context.get("trust_delta", 0.0)
        vulnerability = context.get("vulnerability", 0.0)
        phase_transition = context.get("phase_transition", False)
        
        return (
            hurt > 0.6 or
            trust_delta < -0.2 or
            vulnerability > 0.7 or
            phase_transition
        )
    
    def simulate_alternatives(self, episode: Dict[str, Any], 
                             num_alternatives: int = 3) -> List[Dict[str, Any]]:
        """
        Simulate alternative responses for an episode.
        
        Args:
            episode: The major episode to replay
            num_alternatives: Number of alternative responses to simulate
        
        Returns:
            List of alternative response scenarios with predicted outcomes
        """
        alternatives = []
        
        # Original response
        original_response = episode.get("response", "")
        original_outcome = episode.get("outcome", {})
        
        # Generate alternative responses (simplified - in production would use LLM)
        alternative_strategies = [
            "more_vulnerable",
            "more_protective",
            "more_authentic",
            "more_empathetic",
            "more_direct"
        ]
        
        for strategy in alternative_strategies[:num_alternatives]:
            # Simulate outcome for this strategy
            predicted_outcome = self._predict_outcome(episode, strategy)
            
            alternatives.append({
                "strategy": strategy,
                "response": self._generate_alternative_response(episode, strategy),
                "predicted_outcome": predicted_outcome,
                "trust_delta": predicted_outcome.get("trust_delta", 0.0),
                "hurt_delta": predicted_outcome.get("hurt_delta", 0.0),
                "relationship_health": predicted_outcome.get("relationship_health", 0.5)
            })
        
        return alternatives
    
    def _predict_outcome(self, episode: Dict[str, Any], strategy: str) -> Dict[str, Any]:
        """
        Predict outcome for an alternative strategy.
        Simplified prediction model.
        """
        base_trust = episode.get("trust_before", 0.5)
        base_hurt = episode.get("hurt_before", 0.0)
        
        # Strategy-specific adjustments (simplified)
        adjustments = {
            "more_vulnerable": {"trust_delta": 0.1, "hurt_delta": -0.05},
            "more_protective": {"trust_delta": -0.05, "hurt_delta": 0.0},
            "more_authentic": {"trust_delta": 0.15, "hurt_delta": -0.1},
            "more_empathetic": {"trust_delta": 0.1, "hurt_delta": -0.15},
            "more_direct": {"trust_delta": 0.05, "hurt_delta": -0.05}
        }
        
        adj = adjustments.get(strategy, {"trust_delta": 0.0, "hurt_delta": 0.0})
        
        return {
            "trust_delta": adj["trust_delta"],
            "hurt_delta": adj["hurt_delta"],
            "relationship_health": base_trust + adj["trust_delta"] - (base_hurt + adj["hurt_delta"])
        }
    
    def _generate_alternative_response(self, episode: Dict[str, Any], strategy: str) -> str:
        """
        Generate alternative response for a strategy.
        Simplified - in production would use LLM.
        """
        # This would use LLM to generate alternative response
        # For now, return placeholder
        return f"[Alternative response using {strategy} strategy]"
    
    def tune_parameters(self, episode: Dict[str, Any], alternatives: List[Dict[str, Any]]):
        """
        Tune system parameters based on counterfactual analysis.
        
        If an alternative would have led to better outcomes, adjust parameters.
        """
        original_outcome = episode.get("outcome", {})
        original_health = original_outcome.get("relationship_health", 0.5)
        
        # Find best alternative
        best_alternative = max(alternatives, 
                             key=lambda x: x["predicted_outcome"].get("relationship_health", 0.0))
        best_health = best_alternative["predicted_outcome"].get("relationship_health", 0.5)
        
        # If alternative is significantly better, adjust parameters
        if best_health > original_health + 0.1:
            # Adjust parameters based on best strategy
            strategy = best_alternative["strategy"]
            
            # Update parameter tuning (stored in state)
            if "parameter_tuning" not in self.state:
                self.state["parameter_tuning"] = {}
            
            tuning = self.state["parameter_tuning"]
            
            # Adjust based on strategy
            if strategy == "more_vulnerable":
                tuning["vulnerability_weight"] = tuning.get("vulnerability_weight", 0.5) + 0.01
            elif strategy == "more_authentic":
                tuning["authenticity_weight"] = tuning.get("authenticity_weight", 0.5) + 0.01
            elif strategy == "more_empathetic":
                tuning["empathy_weight"] = tuning.get("empathy_weight", 0.5) + 0.01
            
            self.state["parameter_tuning"] = tuning
    
    def save_episode(self, episode: Dict[str, Any]):
        """
        Save a major episode for later replay.
        """
        if "major_episodes" not in self.state:
            self.state["major_episodes"] = []
        
        episode["timestamp"] = datetime.now(timezone.utc).isoformat()
        self.state["major_episodes"].append(episode)
        
        # Keep only last 50 episodes
        self.state["major_episodes"] = self.state["major_episodes"][-50:]
    
    def save_to_state(self):
        """Save counterfactual replayer state."""
        self.state["major_episodes"] = self.major_episodes

