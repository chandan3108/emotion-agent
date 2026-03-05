"""
Parallel Life Simulation / User Social Circle and Life Awareness
Tracks user's life events, social context, and parallel existence.
AI is aware that user has a life outside the conversation.
"""

import os
import random
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone, timedelta
import httpx
import math

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
HF_TOKEN = GROQ_API_KEY  # Alias for compatibility
MODEL_ID = os.environ.get("MODEL_ID", "llama-3.1-8b-instant")
INFERENCE_URL = "https://api.groq.com/openai/v1/chat/completions"


class ParallelLifeAwareness:
    """
    Tracks and reasons about user's life outside the conversation.
    
    From blueprint:
    - User has a social circle, work, routines, events
    - AI should be aware of this parallel existence
    - Can reference user's life contextually
    - Understands user has other relationships, commitments
    - Respects boundaries and doesn't assume constant availability
    """
    
    def __init__(self, state: Dict[str, Any]):
        self.state = state
        self.life_context = state.get("parallel_life_context", {
            "social_circle": [],  # People user mentions
            "routines": [],  # Daily/weekly routines
            "life_events": [],  # Major events (work, school, travel, etc.)
            "commitments": [],  # Ongoing commitments
            "availability_patterns": {},  # When user is typically available
            "social_dynamics": {}  # Relationship dynamics with others
        })
    
    def update_from_message(self, user_message: str, understanding: Dict[str, Any],
                           memory_system) -> None:
        """
        Extract life context from user message.
        
        Looks for:
        - Mentions of people (friends, family, coworkers)
        - Life events (work, school, travel, activities)
        - Routines (gym, class, meetings)
        - Social dynamics (conflicts, celebrations, etc.)
        """
        events = understanding.get("events", [])
        
        # Extract people mentioned
        # In production, use NER or LLM extraction
        # For now, simple heuristic + LLM if available
        people_mentioned = self._extract_people(user_message, understanding)
        for person in people_mentioned:
            if person not in [p.get("name") for p in self.life_context["social_circle"]]:
                self.life_context["social_circle"].append({
                    "name": person,
                    "first_mentioned": datetime.now(timezone.utc).isoformat(),
                    "mention_count": 1,
                    "relationship_type": "unknown"  # Would be inferred
                })
            else:
                # Update mention count
                for p in self.life_context["social_circle"]:
                    if p.get("name") == person:
                        p["mention_count"] = p.get("mention_count", 0) + 1
                        p["last_mentioned"] = datetime.now(timezone.utc).isoformat()
        
        # Extract life events
        for event in events:
            event_type = event.get("type", "")
            if event_type in ["work", "school", "travel", "activity", "commitment"]:
                self.life_context["life_events"].append({
                    "type": event_type,
                    "description": event.get("content", ""),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "recurring": event.get("recurring", False)
                })
        
        # Extract routines (from memory system identity promotions)
        # Routines are already tracked in memory, but we can reference them here
        if memory_system:
            identity_memories = memory_system.get_identity()
            for identity in identity_memories:
                fact = identity.get("fact", "")
                if "goes to" in fact.lower() or "has class" in fact.lower() or "works" in fact.lower():
                    # This is a routine
                    routine = {
                        "description": fact,
                        "confidence": identity.get("confidence", 0.5),
                        "source": "identity_memory"
                    }
                    # Avoid duplicates
                    if routine not in self.life_context["routines"]:
                        self.life_context["routines"].append(routine)
    
    def _extract_people(self, message: str, understanding: Dict[str, Any]) -> List[str]:
        """
        Extract people mentioned in message.
        In production, use proper NER or LLM extraction.
        """
        # Simple heuristic: look for capitalized words that might be names
        # This is a placeholder - should use proper NER
        words = message.split()
        people = []
        
        # Look for patterns like "my friend X", "X said", etc.
        for i, word in enumerate(words):
            if word.lower() in ["friend", "mom", "dad", "brother", "sister", "coworker", "boss"]:
                # Next word might be a name
                if i + 1 < len(words):
                    next_word = words[i + 1]
                    if next_word[0].isupper() and len(next_word) > 2:
                        people.append(next_word)
        
        # Also check understanding for extracted entities
        entities = understanding.get("entities", [])
        for entity in entities:
            if entity.get("type") == "PERSON":
                people.append(entity.get("text", ""))
        
        return list(set(people))  # Remove duplicates
    
    def get_life_context_for_prompt(self) -> Dict[str, Any]:
        """
        Get life context to include in prompts.
        Helps AI understand user has a parallel existence.
        """
        # Get recent routines (high confidence)
        routines = [r for r in self.life_context["routines"] 
                   if r.get("confidence", 0) > 0.7][:3]
        
        # Get frequently mentioned people
        social_circle = sorted(
            self.life_context["social_circle"],
            key=lambda x: x.get("mention_count", 0),
            reverse=True
        )[:5]
        
        # Get recent life events
        recent_events = sorted(
            self.life_context["life_events"],
            key=lambda x: x.get("timestamp", ""),
            reverse=True
        )[:3]
        
        return {
            "routines": [r.get("description", "") for r in routines],
            "social_circle": [p.get("name", "") for p in social_circle],
            "recent_events": [e.get("description", "")[:50] for e in recent_events],
            "has_parallel_life": len(routines) > 0 or len(social_circle) > 0
        }
    
    def should_reference_life_context(self, temporal_context: Dict[str, Any],
                                     initiative_score: float) -> bool:
        """
        Determine if AI should reference user's life context.
        
        Examples:
        - "How was class today?" (routine reference)
        - "Did you end up talking to [friend]?" (social circle reference)
        - "Hope work wasn't too stressful" (life event reference)
        """
        # Only reference if:
        # 1. High initiative score (AI is initiating)
        # 2. Appropriate time (not too early/late)
        # 3. Has context to reference (routines, people, events)
        # 4. Stochastic: 60% chance even if conditions met
        
        if initiative_score < 0.4:
            return False
        
        has_context = (len(self.life_context["routines"]) > 0 or 
                      len(self.life_context["social_circle"]) > 0)
        
        if not has_context:
            return False
        
        # Time check (don't reference routines at weird times)
        hour = temporal_context.get("hour", 12)
        if hour < 6 or hour > 23:
            return False  # Too early/late
        
        # Stochastic: 60% chance
        return random.random() < 0.6
    
    async def generate_life_reference(self, context: Dict[str, Any]) -> Optional[str]:
        """
        Generate natural reference to user's life context.
        
        Examples:
        - "How was class today?"
        - "Did you end up talking to Sarah?"
        - "Hope your meeting went well"
        """
        life_context = self.get_life_context_for_prompt()
        
        if not life_context.get("has_parallel_life"):
            return None
        
        routines = life_context.get("routines", [])
        social_circle = life_context.get("social_circle", [])
        recent_events = life_context.get("recent_events", [])
        
        # Choose what to reference (stochastic)
        reference_type = random.choice(["routine", "person", "event"])
        
        if reference_type == "routine" and routines:
            routine = random.choice(routines)
            # In production, would use LLM to generate natural reference
            return f"how was {routine.lower()} today?"
        
        elif reference_type == "person" and social_circle:
            person = random.choice(social_circle)
            return f"did you end up talking to {person}?"
        
        elif reference_type == "event" and recent_events:
            event = recent_events[0]  # Most recent
            return f"hope {event.lower()} went well"
        
        return None
    
    def get_availability_inference(self, temporal_context: Dict[str, Any],
                                  memory_system) -> Dict[str, Any]:
        """
        Infer user's likely availability based on:
        - Historical reply patterns
        - Routines (e.g., class at 2pm = unavailable)
        - Time of day
        - Day of week
        """
        hour = temporal_context.get("hour", 12)
        day_of_week = temporal_context.get("day_of_week", "Monday")
        
        # Base availability by time of day
        if 6 <= hour < 9:
            base_availability = 0.3  # Morning, might be busy
        elif 9 <= hour < 17:
            base_availability = 0.5  # Daytime, variable
        elif 17 <= hour < 22:
            base_availability = 0.8  # Evening, more available
        else:
            base_availability = 0.6  # Late night, variable
        
        # Adjust for routines
        routines = self.life_context.get("routines", [])
        for routine in routines:
            # In production, would parse routine times
            # For now, assume routines reduce availability during their time
            pass
        
        return {
            "likely_available": base_availability > 0.6,
            "availability_score": base_availability,
            "reasoning": f"Based on time ({hour}:00) and routines"
        }
    
    def save_to_state(self):
        """Save life context to state."""
        self.state["parallel_life_context"] = self.life_context

