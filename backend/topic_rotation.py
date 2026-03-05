"""
Topic Rotation & Fatigue (Stage 9)
Topic fatigue scoring, natural rotation, repair probability.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
import numpy as np
import math


class TopicRotation:
    """
    Manages topic fatigue and natural rotation.
    Prevents repetitive conversations and encourages diverse topics.
    """
    
    def __init__(self, state: Dict[str, Any]):
        self.state = state
        self.topic_history = state.get("topic_history", [])
        self.topic_fatigue = state.get("topic_fatigue", {})  # topic -> fatigue_score
    
    def calculate_topic_fatigue(self, topic: str, recent_messages: List[Dict[str, Any]]) -> float:
        """
        Calculate fatigue score for a topic (0-1).
        Higher = more fatigued, should rotate away.
        
        Args:
            topic: Topic identifier or keyword
            recent_messages: Recent conversation messages
        
        Returns:
            Fatigue score (0-1)
        """
        # Count recent mentions of topic
        topic_lower = topic.lower()
        recent_mentions = sum(1 for msg in recent_messages[-20:] 
                             if topic_lower in msg.get("content", "").lower())
        
        # Time-based decay: older mentions contribute less
        now = datetime.now(timezone.utc)
        time_weighted_mentions = 0.0
        
        for msg in recent_messages[-20:]:
            if topic_lower in msg.get("content", "").lower():
                msg_time = datetime.fromisoformat(msg.get("timestamp", now.isoformat()).replace("Z", "+00:00"))
                hours_ago = (now - msg_time).total_seconds() / 3600
                # Exponential decay: mentions older than 24h contribute less
                weight = math.exp(-hours_ago / 24.0)
                time_weighted_mentions += weight
        
        # Fatigue increases with recent mentions
        # Base fatigue from topic history
        base_fatigue = self.topic_fatigue.get(topic, 0.0)
        
        # Add fatigue from recent mentions
        recent_fatigue = min(1.0, time_weighted_mentions / 5.0)  # 5 mentions = max fatigue
        
        # Combined fatigue (weighted)
        total_fatigue = 0.6 * recent_fatigue + 0.4 * base_fatigue
        
        return min(1.0, total_fatigue)
    
    def should_rotate_topic(self, current_topic: str, recent_messages: List[Dict[str, Any]]) -> bool:
        """
        Determine if topic should be rotated away from.
        
        Returns:
            True if should rotate, False otherwise
        """
        fatigue = self.calculate_topic_fatigue(current_topic, recent_messages)
        
        # Rotate if fatigue > 0.6 (stochastic threshold)
        threshold = 0.6 + np.random.normal(0, 0.1)  # Add variance
        return fatigue > threshold
    
    def suggest_new_topic(self, recent_messages: List[Dict[str, Any]], 
                         relationship_phase: str, mood: Dict[str, float]) -> Optional[str]:
        """
        Suggest a new topic based on relationship phase and mood.
        
        Returns:
            Topic suggestion or None
        """
        # Topic suggestions by relationship phase
        phase_topics = {
            "Discovery": ["interests", "hobbies", "background", "goals"],
            "Building": ["values", "experiences", "dreams", "fears"],
            "Steady": ["daily_life", "plans", "reflections", "memories"],
            "Deep": ["vulnerabilities", "growth", "meaning", "connection"],
            "Maintenance": ["updates", "appreciation", "future", "gratitude"],
            "Volatile": ["repair", "understanding", "boundaries", "needs"]
        }
        
        # Get topics for current phase
        available_topics = phase_topics.get(relationship_phase, ["general"])
        
        # Filter out fatigued topics
        non_fatigued = [t for t in available_topics 
                       if self.calculate_topic_fatigue(t, recent_messages) < 0.5]
        
        if non_fatigued:
            # Select randomly from non-fatigued topics
            return np.random.choice(non_fatigued)
        
        # If all topics fatigued, suggest repair/rotation
        if relationship_phase == "Volatile":
            return "repair"
        
        return None
    
    def update_topic_fatigue(self, topic: str, recent_messages: List[Dict[str, Any]]):
        """
        Update fatigue score for a topic.
        """
        fatigue = self.calculate_topic_fatigue(topic, recent_messages)
        self.topic_fatigue[topic] = fatigue
    
    def decay_fatigue(self, delta_hours: float):
        """
        Decay topic fatigue over time.
        """
        decay_rate = 0.1  # 10% decay per hour
        # Create a copy of items to avoid "dictionary changed size during iteration" error
        # Use items() to get both key and value, then convert to list for safety
        topics_to_remove = []
        fatigue_copy = dict(self.topic_fatigue)  # Create a copy of the entire dictionary
        for topic, fatigue_value in fatigue_copy.items():
            new_fatigue = fatigue_value * math.exp(-decay_rate * delta_hours)
            self.topic_fatigue[topic] = new_fatigue
            if new_fatigue < 0.1:
                # Mark for removal
                topics_to_remove.append(topic)
        
        # Remove low fatigue topics
        for topic in topics_to_remove:
            if topic in self.topic_fatigue:  # Safety check
                del self.topic_fatigue[topic]
    
    def save_to_state(self):
        """Save topic rotation state."""
        self.state["topic_history"] = self.topic_history[-100:]  # Keep last 100
        self.state["topic_fatigue"] = self.topic_fatigue

