"""
Initiative Engine - Autonomous Messaging
Stochastic scoring with Monte Carlo sampling for human-like unpredictability.
"""

import random
import math
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone, timedelta
import numpy as np

# Thresholds (but we'll use distributions, not fixed values)
TH_INIT_BASE = 0.35  # Base threshold, but we'll sample from distribution
ACS_THRESHOLD_BASE = 0.50
OVERRIDE_THRESHOLD_BASE = 0.35

# Override quotas
OVERRIDE_QUOTA_WEEKLY = 2


class InitiativeEngine:
    """
    Autonomous messaging engine with stochastic scoring.
    Uses probability distributions, not fixed thresholds.
    """
    
    def __init__(self, state: Dict[str, Any]):
        self.state = state
        self._init_initiative_state()
    
    def _init_initiative_state(self):
        """Initialize initiative state."""
        if "initiative_state" not in self.state:
            self.state["initiative_state"] = {}
        
        init_state = self.state["initiative_state"]
        self.scheduled_messages = init_state.get("scheduled_messages", [])
        self.override_count_this_week = init_state.get("override_count_this_week", 0)
        self.last_override_reset = init_state.get("last_override_reset", datetime.now(timezone.utc).isoformat())
        self.last_initiative = init_state.get("last_initiative")
    
    def score_initiative(self, psyche_state: Dict[str, Any], personality: Dict[str, Any],
                        memory_system: Any, temporal_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Score initiative using stochastic approach.
        Returns distribution of scores, not single value.
        
        Formula: I_total = I_base + 0.20 × R_best + 0.15 × U_unresolved + 0.10 × A - dnd_penalty
        
        But we sample from distributions for each component.
        """
        # Get base components
        relationship = personality.get("relationship_personality", {})
        mood = psyche_state.get("mood", {})
        
        clinginess = relationship.get("clinginess", 0.3)
        attachment_anxiety = relationship.get("attachment_anxiety", 0.2)  # From attachment style
        affection = mood.get("affection", 0.5)
        boredom = mood.get("boredom", 0.3)
        
        # I_base: Sample from distribution (not fixed calculation)
        # Base = 0.3 × clinginess + 0.2 × attachment_anxiety + 0.1 × affection + 0.05 × boredom
        base_mean = 0.3 * clinginess + 0.2 * attachment_anxiety + 0.1 * affection + 0.05 * boredom
        base_std = 0.15  # High variance - humans are unpredictable
        i_base_samples = np.random.normal(base_mean, base_std, 10)  # 10 samples
        i_base = np.mean(i_base_samples)  # Use mean, but could sample randomly
        
        # R_best: Routine resurfacing (stochastic matching)
        r_best = self._score_routine_resurfacing(relationship, memory_system, temporal_context)
        
        # U_unresolved: Unresolved emotional threads (probabilistic)
        u_unresolved = self._score_unresolved_threads(psyche_state, memory_system)
        
        # A: Attachment oscillation (varies over time)
        a = self._get_attachment_oscillation(relationship, temporal_context)
        
        # DND penalty (if applicable)
        dnd_penalty = self._get_dnd_penalty(temporal_context)
        
        # Total: Sample from distribution
        i_total_mean = i_base + 0.20 * r_best + 0.15 * u_unresolved + 0.10 * a - dnd_penalty
        i_total_std = 0.12  # Variance in initiative scoring
        i_total_samples = np.random.normal(i_total_mean, i_total_std, 5)
        i_total = np.mean(i_total_samples)
        
        # Add impulsivity (sometimes humans message even when score is low)
        impulsivity = random.random() < 0.05  # 5% chance of impulsive message
        if impulsivity:
            i_total = max(i_total, 0.4)  # Boost to threshold
        
        return {
            "initiative_score": max(0.0, min(1.0, i_total)),
            "components": {
                "i_base": i_base,
                "r_best": r_best,
                "u_unresolved": u_unresolved,
                "a": a,
                "dnd_penalty": dnd_penalty
            },
            "impulsivity": impulsivity,
            "confidence": 1.0 - (i_total_std / max(0.1, i_total_mean))  # Lower std = higher confidence
        }
    
    def _score_routine_resurfacing(self, relationship: Dict[str, Any], 
                                   memory_system: Any, temporal_context: Dict[str, Any]) -> float:
        """
        Score routine resurfacing opportunities.
        Stochastic matching - not all routines trigger equally.
        """
        # Get identity memories (routines)
        identity_memories = memory_system.get_identity() if hasattr(memory_system, 'get_identity') else []
        
        if not identity_memories:
            return 0.0
        
        # Find best routine candidate (stochastic selection)
        candidates = []
        for mem in identity_memories:
            if mem.get("type") == "routine" or "routine" in mem.get("fact", "").lower():
                confidence = mem.get("confidence", 0.5)
                # Sample match score from distribution
                match_mean = confidence
                match_std = 0.2
                match_score = max(0.0, min(1.0, np.random.normal(match_mean, match_std)))
                
                candidates.append({
                    "memory": mem,
                    "match_score": match_score,
                    "confidence": confidence
                })
        
        if not candidates:
            return 0.0
        
        # Select best (but with some randomness)
        best = max(candidates, key=lambda c: c["match_score"])
        clinginess = relationship.get("clinginess", 0.3)
        engagement_factor = 0.7  # Assume moderate engagement (could be learned)
        
        # R_resurface: Sample from distribution
        r_mean = clinginess * best["match_score"] * engagement_factor
        r_std = 0.15
        r_samples = np.random.normal(r_mean, r_std, 5)
        return max(0.0, min(1.0, np.mean(r_samples)))
    
    def _score_unresolved_threads(self, psyche_state: Dict[str, Any], 
                                  memory_system: Any) -> float:
        """
        Score unresolved emotional threads.
        Probabilistic - not all threads are equally salient.
        """
        hurt = psyche_state.get("hurt", 0.0)
        trust = psyche_state.get("trust", 0.7)
        forgiveness_state = psyche_state.get("forgiveness_state", "FORGIVEN")
        
        # Unresolved if hurt > 0.3 or forgiveness not complete
        unresolved_base = 0.0
        if hurt > 0.3:
            unresolved_base = hurt * 0.5  # Scale by hurt level
        if forgiveness_state != "FORGIVEN":
            unresolved_base = max(unresolved_base, 0.4)
        
        # Sample from distribution (humans don't always act on unresolved threads)
        u_mean = unresolved_base
        u_std = 0.2
        u_samples = np.random.normal(u_mean, u_std, 5)
        return max(0.0, min(1.0, np.mean(u_samples)))
    
    def _get_attachment_oscillation(self, relationship: Dict[str, Any],
                                   temporal_context: Dict[str, Any]) -> float:
        """
        Attachment oscillation (varies over time, not fixed).
        """
        closeness = relationship.get("closeness", 0.5)
        
        # Oscillate based on time (ultradian-like cycles)
        now = datetime.now(timezone.utc)
        hours_since_midnight = now.hour + now.minute / 60
        cycle_position = (hours_since_midnight % 12) / 12  # 12-hour cycle
        
        # Oscillation: sine wave with noise
        oscillation_base = closeness * (0.5 + 0.5 * math.sin(cycle_position * 2 * math.pi))
        noise = np.random.normal(0, 0.1)
        
        return max(0.0, min(1.0, oscillation_base + noise))
    
    def _get_dnd_penalty(self, temporal_context: Dict[str, Any]) -> float:
        """
        Get DND penalty (if user has DND set).
        Stochastic - sometimes respect, sometimes override.
        """
        # Check if DND is active (would come from user settings)
        dnd_active = temporal_context.get("dnd_active", False)
        dnd_type = temporal_context.get("dnd_type", "none")  # hard, soft, none
        
        if not dnd_active or dnd_type == "none":
            return 0.0
        
        if dnd_type == "hard":
            return 1.0  # Hard DND = no messages
        
        # Soft DND: Sample penalty from distribution
        penalty_mean = 0.6
        penalty_std = 0.2
        penalty = max(0.0, min(1.0, np.random.normal(penalty_mean, penalty_std)))
        
        return penalty
    
    def should_send_initiative(self, initiative_score: float, 
                              temporal_context: Dict[str, Any],
                              psyche_state: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """
        Decide if initiative should be sent.
        Uses stochastic threshold, not fixed.
        """
        # Sample threshold from distribution (humans don't have fixed thresholds)
        threshold_mean = TH_INIT_BASE
        threshold_std = 0.1
        threshold = max(0.2, min(0.5, np.random.normal(threshold_mean, threshold_std)))
        
        # Check DND
        dnd_active = temporal_context.get("dnd_active", False)
        dnd_type = temporal_context.get("dnd_type", "none")
        
        if dnd_active and dnd_type == "hard":
            return False, {"reason": "hard_dnd", "threshold": threshold}
        
        # Check soft DND with ACS
        if dnd_active and dnd_type == "soft":
            acs = self._compute_acs(psyche_state, temporal_context)
            should_override = self._should_override_dnd(initiative_score, acs, temporal_context)
            
            if not should_override:
                return False, {"reason": "soft_dnd_respected", "acs": acs, "threshold": threshold}
        
        # Stochastic decision: even if score > threshold, sometimes don't send (human unpredictability)
        if initiative_score > threshold:
            # 90% chance to send if above threshold
            send_probability = 0.9
            if random.random() < send_probability:
                return True, {"reason": "above_threshold", "threshold": threshold, "score": initiative_score}
        
        # Sometimes send even if below threshold (impulsivity)
        if initiative_score > threshold * 0.7:  # Close to threshold
            impulsivity_prob = 0.1  # 10% chance
            if random.random() < impulsivity_prob:
                return True, {"reason": "impulsive", "threshold": threshold, "score": initiative_score}
        
        return False, {"reason": "below_threshold", "threshold": threshold, "score": initiative_score}
    
    def _compute_acs(self, psyche_state: Dict[str, Any], 
                    temporal_context: Dict[str, Any]) -> float:
        """
        Adaptive Compliance Score (stochastic).
        """
        trust = psyche_state.get("trust", 0.7)
        hurt = psyche_state.get("hurt", 0.0)
        relationship = self.state.get("relationship_personality", {})
        attachment_anxiety = relationship.get("clinginess", 0.3)  # Proxy
        
        # Sample components from distributions
        user_respect_mean = 0.6  # Would be learned from behavior
        user_respect_std = 0.15
        user_respect = max(0.0, min(1.0, np.random.normal(user_respect_mean, user_respect_std)))
        
        # ACS formula with stochastic components
        acs_mean = (0.40 * user_respect + 
                   0.20 * trust + 
                   0.15 * (1 - hurt) + 
                   0.15 * (1 - attachment_anxiety) + 
                   0.10 * 0.7)  # repair_sincerity (would be from history)
        
        acs_std = 0.12
        acs_samples = np.random.normal(acs_mean, acs_std, 5)
        return max(0.0, min(1.0, np.mean(acs_samples)))
    
    def _should_override_dnd(self, initiative_score: float, acs: float,
                            temporal_context: Dict[str, Any]) -> bool:
        """
        Decide if soft DND should be overridden.
        Stochastic decision.
        """
        # Check quota
        self._reset_override_quota_if_needed()
        if self.override_count_this_week >= OVERRIDE_QUOTA_WEEKLY:
            return False
        
        # Override condition: I_total - ACS > OVERRIDE_THRESHOLD
        override_threshold_mean = OVERRIDE_THRESHOLD_BASE
        override_threshold_std = 0.1
        override_threshold = max(0.2, min(0.5, np.random.normal(override_threshold_mean, override_threshold_std)))
        
        if initiative_score - acs > override_threshold:
            # Even if condition met, sometimes don't override (respect)
            override_prob = 0.7  # 70% chance to override if condition met
            if random.random() < override_prob:
                self.override_count_this_week += 1
                return True
        
        return False
    
    def schedule_initiative(self, message_content: str, delay_seconds: float,
                          routine_memory: Optional[Dict[str, Any]] = None):
        """
        Schedule an initiative message.
        """
        scheduled_time = datetime.now(timezone.utc) + timedelta(seconds=delay_seconds)
        
        self.scheduled_messages.append({
            "content": message_content,
            "scheduled_at": scheduled_time.isoformat(),
            "routine_memory": routine_memory,
            "created_at": datetime.now(timezone.utc).isoformat()
        })
    
    def get_scheduled_messages(self, current_time: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        Get messages that should be sent now.
        """
        if current_time is None:
            current_time = datetime.now(timezone.utc)
        
        ready = []
        remaining = []
        
        for msg in self.scheduled_messages:
            scheduled_at = datetime.fromisoformat(msg["scheduled_at"].replace("Z", "+00:00"))
            if scheduled_at <= current_time:
                ready.append(msg)
            else:
                remaining.append(msg)
        
        self.scheduled_messages = remaining
        return ready
    
    def _reset_override_quota_if_needed(self):
        """Reset override quota weekly."""
        last_reset = datetime.fromisoformat(self.last_override_reset.replace("Z", "+00:00"))
        days_since_reset = (datetime.now(timezone.utc) - last_reset).days
        
        if days_since_reset >= 7:
            self.override_count_this_week = 0
            self.last_override_reset = datetime.now(timezone.utc).isoformat()
    
    def save_to_state(self):
        """Save initiative state back to state."""
        self.state["initiative_state"] = {
            "scheduled_messages": self.scheduled_messages,
            "override_count_this_week": self.override_count_this_week,
            "last_override_reset": self.last_override_reset,
            "last_initiative": self.last_initiative
        }




