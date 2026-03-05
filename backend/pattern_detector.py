"""
Routine Pattern Detection & Identity Promotion
Implements the blueprint's pattern confidence calculation and promotion criteria.
"""

import math
import random
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone, timedelta
from collections import defaultdict
import numpy as np


class PatternDetector:
    """
    Detects recurring patterns (routines, habits) and promotes them to identity memory.
    
    From blueprint:
    - Pattern Confidence: PC = 1 - e^(-3 × raw) where raw = 0.40×TA + 0.25×TI + 0.20×URP + 0.10×F + 0.05×noise
    - Promotion Criteria: PC ≥0.75 AND 14+ distinct days AND 8+ occurrences AND <3 contradictions in 30-day window
    """
    
    def __init__(self, state: Dict[str, Any]):
        self.state = state
        self.pattern_candidates = state.get("pattern_candidates", {})
        # Format: pattern_id -> {
        #   "pattern_text": str,
        #   "occurrences": [{"timestamp": iso, "context": dict}],
        #   "distinct_days": set of dates,
        #   "contradictions": [{"timestamp": iso, "evidence": str}],
        #   "raw_score": float,
        #   "pattern_confidence": float,
        #   "last_updated": iso
        # }
    
    def detect_routine_pattern(self, user_message: str, understanding: Dict[str, Any],
                              temporal_context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Detect if message contains a routine pattern.
        
        Returns:
            Pattern candidate dict if detected, None otherwise
        """
        # Extract potential routine indicators from message
        routine_keywords = [
            "class", "gym", "work", "study", "meeting", "practice", "training",
            "every", "usually", "always", "typically", "routine", "schedule"
        ]
        
        message_lower = user_message.lower()
        has_routine_indicator = any(keyword in message_lower for keyword in routine_keywords)
        
        if not has_routine_indicator:
            return None
        
        # Extract time/context information
        hour = temporal_context.get("hour", 12)
        day_of_week = temporal_context.get("day_of_week", "unknown")
        circadian_phase = temporal_context.get("circadian_phase", "afternoon")
        
        # Try to extract routine description (simplified - in production use LLM)
        # For now, use message as pattern text if it contains routine indicators
        pattern_text = self._extract_pattern_text(user_message, understanding)
        
        if not pattern_text:
            return None
        
        return {
            "pattern_text": pattern_text,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "hour": hour,
            "day_of_week": day_of_week,
            "circadian_phase": circadian_phase,
            "context": {
                "emotion": understanding.get("emotion", "neutral"),
                "intent": understanding.get("intent", "chat")
            }
        }
    
    def _extract_pattern_text(self, message: str, understanding: Dict[str, Any]) -> Optional[str]:
        """
        Extract pattern description from message.
        In production, use LLM to extract structured routine information.
        """
        # Simplified extraction - look for time + activity patterns
        message_lower = message.lower()
        
        # Try to extract: "I go to [place] [time]" or "I have [activity] [time]"
        time_patterns = ["at", "on", "every", "usually", "always"]
        activity_patterns = ["go to", "have", "do", "attend", "practice"]
        
        has_time = any(tp in message_lower for tp in time_patterns)
        has_activity = any(ap in message_lower for ap in activity_patterns)
        
        if has_time or has_activity:
            # Return a normalized pattern text
            # In production, use LLM to extract: "goes to gym Tues/Thurs" or "has class at 10am"
            return message[:100]  # Simplified - use full message as pattern for now
        
        return None
    
    def update_pattern_candidate(self, pattern_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update or create pattern candidate with new occurrence.
        
        Returns:
            Updated pattern candidate with new confidence score
        """
        pattern_text = pattern_data["pattern_text"]
        pattern_id = self._get_pattern_id(pattern_text)
        timestamp = datetime.fromisoformat(pattern_data["timestamp"])
        date = timestamp.date()
        
        # Get or create candidate
        if pattern_id not in self.pattern_candidates:
            self.pattern_candidates[pattern_id] = {
                "pattern_text": pattern_text,
                "occurrences": [],
                "distinct_days": set(),
                "contradictions": [],
                "raw_score": 0.0,
                "pattern_confidence": 0.0,
                "last_updated": timestamp.isoformat()
            }
        
        candidate = self.pattern_candidates[pattern_id]
        
        # Add occurrence
        candidate["occurrences"].append({
            "timestamp": pattern_data["timestamp"],
            "hour": pattern_data.get("hour"),
            "day_of_week": pattern_data.get("day_of_week"),
            "context": pattern_data.get("context", {})
        })
        
        # Add distinct day
        candidate["distinct_days"].add(date.isoformat())
        
        # Calculate pattern confidence
        self._calculate_pattern_confidence(candidate)
        
        candidate["last_updated"] = timestamp.isoformat()
        
        return candidate
    
    def _calculate_pattern_confidence(self, candidate: Dict[str, Any]):
        """
        Calculate pattern confidence: PC = 1 - e^(-3 × raw)
        where raw = 0.40×TA + 0.25×TI + 0.20×URP + 0.10×F + 0.05×noise
        """
        occurrences = candidate["occurrences"]
        distinct_days = len(candidate["distinct_days"])
        contradictions = len(candidate["contradictions"])
        
        if len(occurrences) == 0:
            candidate["pattern_confidence"] = 0.0
            candidate["raw_score"] = 0.0
            return
        
        # TA: Temporal Alignment (how consistent are the times?)
        ta = self._calculate_temporal_alignment(occurrences)
        
        # TI: Temporal Interval (how regular is the interval?)
        ti = self._calculate_temporal_interval(occurrences)
        
        # URP: User Reference Pattern (how consistently does user reference this?)
        urp = self._calculate_user_reference_pattern(occurrences)
        
        # F: Frequency (how often does it occur?)
        f = min(1.0, len(occurrences) / 20.0)  # Normalize to 20 occurrences = 1.0
        
        # Noise: Random variance
        noise = random.gauss(0, 0.05)
        
        # Calculate raw score
        raw = 0.40 * ta + 0.25 * ti + 0.20 * urp + 0.10 * f + 0.05 * noise
        raw = max(0.0, min(1.0, raw))  # Clamp to [0, 1]
        
        # Calculate pattern confidence
        pc = 1 - math.exp(-3 * raw)
        
        candidate["raw_score"] = raw
        candidate["pattern_confidence"] = pc
    
    def _calculate_temporal_alignment(self, occurrences: List[Dict[str, Any]]) -> float:
        """
        TA: Temporal Alignment - how consistent are the times?
        If occurrences happen at similar hours, TA is high.
        """
        if len(occurrences) < 2:
            return 0.5  # Neutral if not enough data
        
        hours = [occ.get("hour") for occ in occurrences if occ.get("hour") is not None]
        if not hours:
            return 0.5
        
        # Calculate variance in hours
        mean_hour = np.mean(hours)
        variance = np.var(hours)
        
        # Low variance = high alignment (happens at similar times)
        # Normalize: variance of 0 = 1.0, variance of 12 = 0.0
        ta = max(0.0, min(1.0, 1.0 - (variance / 144.0)))  # 12^2 = 144
        
        return ta
    
    def _calculate_temporal_interval(self, occurrences: List[Dict[str, Any]]) -> float:
        """
        TI: Temporal Interval - how regular is the interval?
        If occurrences happen at regular intervals (daily, weekly), TI is high.
        """
        if len(occurrences) < 3:
            return 0.5  # Need at least 3 to detect intervals
        
        # Sort by timestamp
        sorted_occ = sorted(occurrences, key=lambda x: x["timestamp"])
        
        # Calculate intervals between consecutive occurrences
        intervals = []
        for i in range(1, len(sorted_occ)):
            try:
                t1 = datetime.fromisoformat(sorted_occ[i-1]["timestamp"].replace("Z", "+00:00"))
                t2 = datetime.fromisoformat(sorted_occ[i]["timestamp"].replace("Z", "+00:00"))
                delta_hours = (t2 - t1).total_seconds() / 3600
                intervals.append(delta_hours)
            except Exception:
                continue
        
        if not intervals:
            return 0.5
        
        # Check if intervals are regular (low variance)
        mean_interval = np.mean(intervals)
        variance = np.var(intervals)
        
        # Low variance = high interval regularity
        # Normalize: variance of 0 = 1.0, variance of mean = 0.0
        if mean_interval > 0:
            cv = variance / mean_interval  # Coefficient of variation
            ti = max(0.0, min(1.0, 1.0 - cv))  # Low CV = high regularity
        else:
            ti = 0.5
        
        return ti
    
    def _calculate_user_reference_pattern(self, occurrences: List[Dict[str, Any]]) -> float:
        """
        URP: User Reference Pattern - how consistently does user reference this?
        If user mentions it frequently and consistently, URP is high.
        """
        if len(occurrences) < 2:
            return 0.5
        
        # Simple heuristic: more occurrences = higher URP
        # In production, analyze semantic consistency of references
        urp = min(1.0, len(occurrences) / 10.0)  # 10 occurrences = 1.0
        
        return urp
    
    def check_promotion_criteria(self, pattern_id: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Check if pattern meets promotion criteria:
        PC ≥0.75 AND 14+ distinct days AND 8+ occurrences AND <3 contradictions in 30-day window
        
        Returns:
            (should_promote, promotion_info)
        """
        if pattern_id not in self.pattern_candidates:
            return False, {}
        
        candidate = self.pattern_candidates[pattern_id]
        
        pc = candidate["pattern_confidence"]
        distinct_days = len(candidate["distinct_days"])
        occurrences = len(candidate["occurrences"])
        
        # Count contradictions in last 30 days
        now = datetime.now(timezone.utc)
        recent_contradictions = [
            c for c in candidate["contradictions"]
            if (now - datetime.fromisoformat(c["timestamp"].replace("Z", "+00:00"))).days < 30
        ]
        contradiction_count = len(recent_contradictions)
        
        # Check all criteria
        meets_pc = pc >= 0.75
        meets_days = distinct_days >= 14
        meets_occurrences = occurrences >= 8
        meets_contradictions = contradiction_count < 3
        
        should_promote = meets_pc and meets_days and meets_occurrences and meets_contradictions
        
        promotion_info = {
            "pattern_confidence": pc,
            "distinct_days": distinct_days,
            "occurrences": occurrences,
            "contradictions": contradiction_count,
            "meets_pc": meets_pc,
            "meets_days": meets_days,
            "meets_occurrences": meets_occurrences,
            "meets_contradictions": meets_contradictions
        }
        
        return should_promote, promotion_info
    
    def _get_pattern_id(self, pattern_text: str) -> str:
        """Generate unique ID for pattern."""
        # Use hash of normalized pattern text
        normalized = pattern_text.lower().strip()
        return f"pattern_{hash(normalized) % 1000000}"
    
    def add_contradiction(self, pattern_id: str, evidence: str):
        """Add contradiction to pattern candidate."""
        if pattern_id not in self.pattern_candidates:
            return
        
        self.pattern_candidates[pattern_id]["contradictions"].append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "evidence": evidence
        })
        
        # Recalculate confidence (contradictions reduce it)
        candidate = self.pattern_candidates[pattern_id]
        self._calculate_pattern_confidence(candidate)
    
    def save_to_state(self):
        """Save pattern candidates to state."""
        # Convert sets to lists for JSON serialization
        for pattern_id, candidate in self.pattern_candidates.items():
            if isinstance(candidate.get("distinct_days"), set):
                candidate["distinct_days"] = list(candidate["distinct_days"])
        
        self.state["pattern_candidates"] = self.pattern_candidates
    
    def get_all_candidates(self) -> Dict[str, Dict[str, Any]]:
        """Get all pattern candidates."""
        return self.pattern_candidates.copy()

