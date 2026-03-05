"""
Temporal Awareness System (TAS)
Makes every decision time-aware. Humans are temporally aware - so should the AI.
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, Tuple
from enum import Enum
import math
import random



class CircadianPhase(Enum):
    MORNING = "morning"      # 06:00-10:00
    AFTERNOON = "afternoon"  # 10:00-17:00
    EVENING = "evening"      # 17:00-22:00
    LATE_NIGHT = "late_night"  # 22:00-02:00
    NIGHT = "night"         # 02:00-06:00


class TemporalAwarenessSystem:
    """
    Pervasive temporal awareness - every decision is time-aware.
    Integrates with memory decay, mood dynamics, forgiveness, initiative.
    """
    
    def __init__(self, user_timezone: str = None):
        """
        Initialize temporal awareness system.
        If user_timezone is None, defaults to IST (UTC+5:30) for India.
        """
        if user_timezone is None:
            # Default to IST (India Standard Time = UTC+5:30)
            self.user_timezone = "IST"
            self.timezone_offset_hours = 5.5  # IST is UTC+5:30
        else:
            self.user_timezone = user_timezone
            # Parse timezone offset if provided in UTC+X format
            if user_timezone.startswith("UTC"):
                try:
                    self.timezone_offset_hours = float(user_timezone[3:])
                except:
                    self.timezone_offset_hours = 5.5  # Default to IST
            elif user_timezone == "IST":
                self.timezone_offset_hours = 5.5
            else:
                self.timezone_offset_hours = 0  # UTC
    
    def get_current_time(self) -> datetime:
        """
        Get current time in user's timezone.
        Converts UTC to user's timezone using offset.
        """
        utc_now = datetime.now(timezone.utc)
        # Apply timezone offset
        offset = timedelta(hours=self.timezone_offset_hours)
        user_time = utc_now + offset
        return user_time
    
    def get_circadian_phase(self, timestamp: Optional[datetime] = None) -> CircadianPhase:
        """
        Determine circadian phase based on hour.
        
        Phases:
        - Morning (06:00-10:00): Drier tone, shorter messages, formal, lower warmth
        - Afternoon (10:00-17:00): Baseline behavior
        - Evening (17:00-21:00): Warmer, more affectionate, longer, relaxed
        - Late-night (22:00-02:00): Higher vulnerability, more impulsivity, poetic, playful
        - Night (02:00-06:00): Minimal, tired, withdrawn
        """
        if timestamp is None:
            timestamp = self.get_current_time()
        
        hour = timestamp.hour
        
        if 6 <= hour < 10:
            return CircadianPhase.MORNING
        elif 10 <= hour < 17:
            return CircadianPhase.AFTERNOON
        elif 17 <= hour < 22:
            return CircadianPhase.EVENING
        elif 22 <= hour < 24 or 0 <= hour < 2:
            return CircadianPhase.LATE_NIGHT
        else:  # 2 <= hour < 6
            return CircadianPhase.NIGHT
    
    def get_time_deltas(self, temporal_context: Dict[str, Any]) -> Dict[str, float]:
        """
        Calculate time deltas since key events.
        
        Returns:
            {
                "hours_since_last_message": float,
                "days_since_last_conflict": float,
                "days_since_last_apology": float,
                "days_since_relationship_start": float,
                "hours_since_last_routine_event": float,
            }
        """
        now = self.get_current_time()
        deltas = {}
        
        # Hours since last message
        last_message_time = temporal_context.get("last_message_time")
        if last_message_time:
            try:
                if isinstance(last_message_time, str):
                    last_time = datetime.fromisoformat(last_message_time.replace("Z", "+00:00"))
                else:
                    last_time = last_message_time
                delta = (now - last_time).total_seconds() / 3600
                deltas["hours_since_last_message"] = max(0, delta)
            except Exception:
                deltas["hours_since_last_message"] = 0.0
        else:
            deltas["hours_since_last_message"] = 0.0
        
        # Days since last conflict
        last_conflict_time = temporal_context.get("last_conflict_time")
        if last_conflict_time:
            try:
                if isinstance(last_conflict_time, str):
                    conflict_time = datetime.fromisoformat(last_conflict_time.replace("Z", "+00:00"))
                else:
                    conflict_time = last_conflict_time
                delta = (now - conflict_time).total_seconds() / (3600 * 24)
                deltas["days_since_last_conflict"] = max(0, delta)
            except Exception:
                deltas["days_since_last_conflict"] = None
        else:
            deltas["days_since_last_conflict"] = None
        
        # Days since last apology
        last_apology_time = temporal_context.get("last_apology_time")
        if last_apology_time:
            try:
                if isinstance(last_apology_time, str):
                    apology_time = datetime.fromisoformat(last_apology_time.replace("Z", "+00:00"))
                else:
                    apology_time = last_apology_time
                delta = (now - apology_time).total_seconds() / (3600 * 24)
                deltas["days_since_last_apology"] = max(0, delta)
            except Exception:
                deltas["days_since_last_apology"] = None
        else:
            deltas["days_since_last_apology"] = None
        
        # Days since relationship start
        relationship_start = temporal_context.get("relationship_start_time")
        if relationship_start:
            try:
                if isinstance(relationship_start, str):
                    start_time = datetime.fromisoformat(relationship_start.replace("Z", "+00:00"))
                else:
                    start_time = relationship_start
                delta = (now - start_time).total_seconds() / (3600 * 24)
                deltas["days_since_relationship_start"] = max(0, delta)
            except Exception:
                deltas["days_since_relationship_start"] = 0.0
        else:
            deltas["days_since_relationship_start"] = 0.0
        
        # Hours since last routine event
        last_routine_time = temporal_context.get("last_routine_event_time")
        if last_routine_time:
            try:
                if isinstance(last_routine_time, str):
                    routine_time = datetime.fromisoformat(last_routine_time.replace("Z", "+00:00"))
                else:
                    routine_time = last_routine_time
                delta = (now - routine_time).total_seconds() / 3600
                deltas["hours_since_last_routine_event"] = max(0, delta)
            except Exception:
                deltas["hours_since_last_routine_event"] = None
        else:
            deltas["hours_since_last_routine_event"] = None
        
        return deltas
    
    def modulate_behavior_by_time(self, circadian_phase: CircadianPhase, 
                                  time_deltas: Dict[str, float]) -> Dict[str, float]:
        """
        Modulate behavior based on time of day and time since events.
        
        Returns modulation factors:
        {
            "message_length_multiplier": float,
            "warmth_multiplier": float,
            "emoji_multiplier": float,
            "vulnerability_multiplier": float,
            "formality": float,  # 0=casual, 1=formal
            "initiative_probability": float,
        }
        """
        modulations = {}
        
        # Circadian phase effects
        if circadian_phase == CircadianPhase.MORNING:
            modulations["message_length_multiplier"] = 0.7  # Shorter
            modulations["warmth_multiplier"] = 0.6  # Less warm
            modulations["emoji_multiplier"] = 0.5  # Fewer emojis
            modulations["vulnerability_multiplier"] = 0.4  # Less vulnerable
            modulations["formality"] = 0.7  # More formal
            modulations["initiative_probability"] = 0.3  # Less likely to initiate
        
        elif circadian_phase == CircadianPhase.AFTERNOON:
            modulations["message_length_multiplier"] = 1.0  # Baseline
            modulations["warmth_multiplier"] = 0.8  # Moderate warmth
            modulations["emoji_multiplier"] = 0.8  # Moderate emojis
            modulations["vulnerability_multiplier"] = 0.6  # Moderate vulnerability
            modulations["formality"] = 0.4  # Casual
            modulations["initiative_probability"] = 0.5  # Moderate
        
        elif circadian_phase == CircadianPhase.EVENING:
            modulations["message_length_multiplier"] = 1.3  # Longer
            modulations["warmth_multiplier"] = 1.2  # Warmer
            modulations["emoji_multiplier"] = 1.2  # More emojis
            modulations["vulnerability_multiplier"] = 0.9  # More vulnerable
            modulations["formality"] = 0.2  # Very casual
            modulations["initiative_probability"] = 0.7  # More likely to initiate
        
        elif circadian_phase == CircadianPhase.LATE_NIGHT:
            modulations["message_length_multiplier"] = 1.1  # Slightly longer
            modulations["warmth_multiplier"] = 1.0  # Baseline warmth
            modulations["emoji_multiplier"] = 1.1  # Slightly more emojis
            modulations["vulnerability_multiplier"] = 1.3  # Higher vulnerability
            modulations["formality"] = 0.1  # Very casual
            modulations["initiative_probability"] = 0.6  # Moderate (but more impulsive)
        
        else:  # NIGHT
            modulations["message_length_multiplier"] = 0.5  # Much shorter
            modulations["warmth_multiplier"] = 0.5  # Less warm
            modulations["emoji_multiplier"] = 0.3  # Few emojis
            modulations["vulnerability_multiplier"] = 0.3  # Less vulnerable
            modulations["formality"] = 0.6  # More formal
            modulations["initiative_probability"] = 0.1  # Very unlikely
        
        # Time delta effects
        hours_since_message = time_deltas.get("hours_since_last_message", 0)
        days_since_conflict = time_deltas.get("days_since_last_conflict")
        
        # If it's been a while since last message, be warmer when reconnecting
        if hours_since_message > 24:
            modulations["warmth_multiplier"] *= 1.2
            modulations["initiative_probability"] *= 1.3
        
        # If recent conflict, be more cautious
        if days_since_conflict is not None and days_since_conflict < 1:
            modulations["warmth_multiplier"] *= 0.8
            modulations["vulnerability_multiplier"] *= 0.7
            modulations["formality"] = min(1.0, modulations["formality"] + 0.2)
        
        # Clamp all values
        for key in modulations:
            if "multiplier" in key or "probability" in key:
                modulations[key] = max(0.0, min(2.0, modulations[key]))
            elif key == "formality":
                modulations[key] = max(0.0, min(1.0, modulations[key]))
        
        return modulations
    
    def get_temporal_context_for_prompt(self, temporal_context: Dict[str, Any]) -> str:
        """
        Generate temporal context string for LLM prompt.
        Makes AI aware of time without being robotic about it.
        """
        now = self.get_current_time()
        phase = self.get_circadian_phase(now)
        deltas = self.get_time_deltas(temporal_context)
        modulations = self.modulate_behavior_by_time(phase, deltas)
        
        # Build natural context string
        context_parts = []
        
        # Time of day (natural, not robotic)
        phase_names = {
            CircadianPhase.MORNING: "morning",
            CircadianPhase.AFTERNOON: "afternoon",
            CircadianPhase.EVENING: "evening",
            CircadianPhase.LATE_NIGHT: "late night",
            CircadianPhase.NIGHT: "night"
        }
        context_parts.append(f"It's {phase_names[phase]} for you.")
        
        # Time since last message
        hours = deltas.get("hours_since_last_message", 0)
        if hours > 24:
            days = hours / 24
            context_parts.append(f"It's been {int(days)} day(s) since you last talked.")
        elif hours > 1:
            context_parts.append(f"It's been {int(hours)} hour(s) since you last talked.")
        
        # Recent conflict
        days_conflict = deltas.get("days_since_last_conflict")
        if days_conflict is not None and days_conflict < 3:
            context_parts.append(f"There was a conflict {days_conflict:.1f} day(s) ago.")
        
        # Relationship length
        days_relationship = deltas.get("days_since_relationship_start", 0)
        if days_relationship > 0:
            if days_relationship < 7:
                context_parts.append(f"You've been talking for {int(days_relationship)} day(s).")
            elif days_relationship < 30:
                weeks = days_relationship / 7
                context_parts.append(f"You've been talking for {weeks:.1f} week(s).")
            else:
                months = days_relationship / 30
                context_parts.append(f"You've been talking for {months:.1f} month(s).")
        
        # Behavioral modulation hints (subtle, for LLM to use naturally)
        if modulations["warmth_multiplier"] > 1.1:
            context_parts.append("You're feeling warmer/more affectionate right now.")
        elif modulations["warmth_multiplier"] < 0.7:
            context_parts.append("You're feeling a bit more reserved right now.")
        
        if modulations["vulnerability_multiplier"] > 1.2:
            context_parts.append("You're feeling more open/vulnerable right now.")
        
        if modulations["formality"] > 0.6:
            context_parts.append("You're being a bit more formal right now.")
        
        return " ".join(context_parts)
    
    def update_temporal_context(self, temporal_context: Dict[str, Any], 
                               event_type: str) -> Dict[str, Any]:
        """
        Update temporal context when events occur.
        
        Event types: message, conflict, apology, routine_event, promise
        """
        now = self.get_current_time().isoformat()
        updated = temporal_context.copy()
        
        if event_type == "message":
            updated["last_message_time"] = now
        elif event_type == "conflict":
            updated["last_conflict_time"] = now
        elif event_type == "apology":
            updated["last_apology_time"] = now
        elif event_type == "routine_event":
            updated["last_routine_event_time"] = now
        elif event_type == "promise":
            updated["last_promise_time"] = now
        
        return updated




