"""
Relationship Phases
Probabilistic phase transitions based on trust, reciprocity, vulnerability.
"""

import random
import math
from typing import Dict, Any, Optional
from datetime import datetime, timezone, timedelta
import numpy as np

PHASES = ["Discovery", "Building", "Steady", "Deep", "Maintenance", "Volatile"]

# Phase envelopes: behavioral caps based on relationship phase
# These limit how warm, patient, repair-oriented the AI can be
# Phase = social speed limit, not just personality
PHASE_ENVELOPES = {
    "Discovery": {
        # "I don't owe you emotional labor"
        "warmth_cap": 0.4,      # Limited warmth
        "patience_cap": 0.3,    # Low tolerance for BS
        "repair_cap": 0.2,      # Won't repair much
        "verbosity_cap": 0.5,   # Shorter responses
        "intimacy_cap": 0.1,    # Almost no intimacy
        "vulnerability_cap": 0.1,  # Won't be vulnerable
        "description": "I don't owe you emotional labor."
    },
    "Building": {
        # "I'm investing, but I can pull back"
        "warmth_cap": 0.6,
        "patience_cap": 0.5,
        "repair_cap": 0.4,
        "verbosity_cap": 0.7,
        "intimacy_cap": 0.3,
        "vulnerability_cap": 0.3,
        "description": "I'm investing, but I can pull back."
    },
    "Steady": {
        # "We have history — conflict matters"
        "warmth_cap": 0.7,
        "patience_cap": 0.6,
        "repair_cap": 0.6,
        "verbosity_cap": 0.8,
        "intimacy_cap": 0.5,
        "vulnerability_cap": 0.5,
        "description": "We have history. Conflict matters."
    },
    "Deep": {
        # "This bond has weight"
        "warmth_cap": 0.9,
        "patience_cap": 0.8,
        "repair_cap": 0.9,
        "verbosity_cap": 0.9,
        "intimacy_cap": 0.8,
        "vulnerability_cap": 0.8,
        "description": "This bond has weight."
    },
    "Maintenance": {
        "warmth_cap": 0.7,
        "patience_cap": 0.6,
        "repair_cap": 0.7,
        "verbosity_cap": 0.7,
        "intimacy_cap": 0.6,
        "vulnerability_cap": 0.6,
        "description": "Comfortable and stable."
    },
    "Volatile": {
        # Damaged relationship
        "warmth_cap": 0.3,
        "patience_cap": 0.2,
        "repair_cap": 0.3,
        "verbosity_cap": 0.4,
        "intimacy_cap": 0.2,
        "vulnerability_cap": 0.1,
        "description": "Trust is damaged. Guard is up."
    }
}

# Phase transition thresholds (stochastic)
PHASE_THRESHOLDS = {
    "Discovery": {"trust": (0.3, 0.1), "reciprocity": (0.0, 0.1), "vulnerability": (0.0, 0.1)},
    "Building": {"trust": (0.5, 0.1), "reciprocity": (0.2, 0.1), "vulnerability": (0.2, 0.1)},
    "Steady": {"trust": (0.7, 0.1), "reciprocity": (0.4, 0.1), "vulnerability": (0.4, 0.1)},
    "Deep": {"trust": (0.85, 0.1), "reciprocity": (0.6, 0.1), "vulnerability": (0.7, 0.1)},
    "Maintenance": {"trust": (0.8, 0.1), "reciprocity": (0.5, 0.1), "vulnerability": (0.5, 0.1)},
    "Volatile": {"trust": (0.4, 0.15), "reciprocity": (0.2, 0.15), "vulnerability": (0.3, 0.15)}
}


class RelationshipPhases:
    """
    Manages relationship phases with probabilistic transitions.
    """
    
    def __init__(self, state: Dict[str, Any]):
        self.state = state
        self._init_phases()
    
    def _init_phases(self):
        """Initialize phase state."""
        psyche = self.state.get("current_psyche", {})
        self.current_phase = psyche.get("relationship_phase", "Discovery")
        self.phase_history = self.state.get("phase_history", [])
        self.last_transition = self.state.get("last_phase_transition")
    
    def evaluate_phase_transition(self, psyche_state: Dict[str, Any],
                                 reciprocity_balance: float,
                                 vulnerability_score: float,
                                 shared_history_score: float = 0.0,
                                 respect: float = 0.5) -> Dict[str, Any]:
        """
        Evaluate if phase transition should occur (probabilistic).
        Uses meaningful shared history (episodic events, identity facts, trust-building moments),
        not just message count.
        
        Args:
            shared_history_score: Weighted score of meaningful interactions
                (episodic memories * 0.4 + identity memories * 0.3 + high-salience events * 0.3)
            respect: Current respect level (affects progression)
        """
        trust = psyche_state.get("trust", 0.5)
        hurt = psyche_state.get("hurt", 0.0)
        
        # Get current phase requirements
        current_idx = PHASES.index(self.current_phase) if self.current_phase in PHASES else 0
        
        # Evaluate transition to next phase
        can_advance = False
        can_regress = False
        
        # Let phase transitions happen naturally based on trust, reciprocity, and vulnerability
        # No hardcoded minimums - trust the psychological state
        
        # Check advancement (stochastic thresholds)
        if current_idx < len(PHASES) - 1:
            next_phase = PHASES[current_idx + 1]
            thresholds = PHASE_THRESHOLDS.get(next_phase, {})
            
            # Sample thresholds from distributions
            trust_threshold_mean, trust_threshold_std = thresholds.get("trust", (0.7, 0.1))
            trust_threshold = np.random.normal(trust_threshold_mean, trust_threshold_std)
            
            recip_threshold_mean, recip_threshold_std = thresholds.get("reciprocity", (0.4, 0.1))
            recip_threshold = np.random.normal(recip_threshold_mean, recip_threshold_std)
            
            vuln_threshold_mean, vuln_threshold_std = thresholds.get("vulnerability", (0.4, 0.1))
            vuln_threshold = np.random.normal(vuln_threshold_mean, vuln_threshold_std)
            
            # Respect threshold varies by phase
            respect_threshold = 0.4 if next_phase == "Building" else 0.5 if next_phase == "Steady" else 0.6
            
            # Check if all conditions met (with some variance)
            # Respect is now REQUIRED for advancement
            if (trust > trust_threshold and 
                respect > respect_threshold and  # Must have earned respect
                abs(reciprocity_balance) < 0.3 and  # Balanced reciprocity
                vulnerability_score > vuln_threshold and
                hurt < 0.3):  # Can't advance with high hurt
                can_advance = True
        
        # Check regression (to Volatile if trust/hurt is SEVERELY bad)
        # Volatile should be HARD to trigger - it's relationship damage, not just bad mood
        # In Discovery phase, we DON'T regress to Volatile (nothing is built yet)
        if self.current_phase != "Volatile" and self.current_phase != "Discovery":
            # Only regress if trust is VERY low or hurt is VERY high
            if trust < 0.25 or hurt > 0.7:
                # Sample regression probability
                regress_prob_mean = 0.7 if hurt > 0.7 else 0.4
                regress_prob_std = 0.15
                regress_prob = max(0.0, min(1.0, np.random.normal(regress_prob_mean, regress_prob_std)))
                
                if random.random() < regress_prob:
                    can_regress = True
        
        # In Discovery, bad behavior just means staying in Discovery (not progressing)
        # They haven't built anything to damage yet
        
        # Transition decision (stochastic - not always transition even if conditions met)
        transition = None
        if can_advance:
            # 70% chance to advance if conditions met
            if random.random() < 0.7:
                transition = PHASES[current_idx + 1]
        elif can_regress:
            transition = "Volatile"
        
        return {
            "current_phase": self.current_phase,
            "can_advance": can_advance,
            "can_regress": can_regress,
            "suggested_transition": transition,
            "trust": trust,
            "reciprocity_balance": reciprocity_balance,
            "vulnerability_score": vulnerability_score
        }
    
    def transition_phase(self, new_phase: str):
        """Transition to new phase."""
        if new_phase == self.current_phase:
            return
        
        self.phase_history.append({
            "from_phase": self.current_phase,
            "to_phase": new_phase,
            "transitioned_at": datetime.now(timezone.utc).isoformat()
        })
        
        self.current_phase = new_phase
        self.last_transition = datetime.now(timezone.utc).isoformat()
    
    def get_phase_behavior_modifiers(self) -> Dict[str, Any]:
        """
        Get behavior modifiers for current phase (stochastic).
        """
        modifiers = {
            "Discovery": {
                "initiative_frequency": (0.3, 0.1),  # (mean, std)
                "vulnerability_willingness": (0.2, 0.1),
                "conflict_style": "avoidant",
                "meta_disclosure": (0.1, 0.05)
            },
            "Building": {
                "initiative_frequency": (0.5, 0.1),
                "vulnerability_willingness": (0.4, 0.1),
                "conflict_style": "careful",
                "meta_disclosure": (0.3, 0.1)
            },
            "Steady": {
                "initiative_frequency": (0.7, 0.1),
                "vulnerability_willingness": (0.6, 0.1),
                "conflict_style": "direct",
                "meta_disclosure": (0.5, 0.1)
            },
            "Deep": {
                "initiative_frequency": (0.8, 0.1),
                "vulnerability_willingness": (0.8, 0.1),
                "conflict_style": "growth_oriented",
                "meta_disclosure": (0.7, 0.15)
            },
            "Maintenance": {
                "initiative_frequency": (0.6, 0.15),
                "vulnerability_willingness": (0.5, 0.15),
                "conflict_style": "stable",
                "meta_disclosure": (0.4, 0.1)
            },
            "Volatile": {
                "initiative_frequency": (0.4, 0.2),
                "vulnerability_willingness": (0.3, 0.2),
                "conflict_style": "defensive",
                "meta_disclosure": (0.2, 0.15)
            }
        }
        
        config = modifiers.get(self.current_phase, modifiers["Discovery"])
        
        # Sample each modifier from distribution
        result = {}
        for key, value in config.items():
            if isinstance(value, tuple) and len(value) == 2:
                # Numeric value with (mean, std) distribution
                mean, std = value
                if isinstance(mean, (int, float)):
                    result[key] = max(0.0, min(1.0, np.random.normal(mean, std)))
                else:
                    result[key] = mean  # Fallback if mean is not numeric
            else:
                # String value (like "conflict_style")
                result[key] = value
        
        return result
    
    def save_to_state(self):
        """Save phase state back to state."""
        self.state["current_psyche"]["relationship_phase"] = self.current_phase
        self.state["phase_history"] = self.phase_history[-20:]  # Keep last 20 transitions
        self.state["last_phase_transition"] = self.last_transition
    
    def get_phase_envelope(self) -> Dict[str, Any]:
        """
        Get behavioral envelope (caps) for current phase.
        Phase = social speed limit, not personality.
        
        Returns caps on: warmth, patience, repair, verbosity, intimacy, vulnerability
        """
        return PHASE_ENVELOPES.get(self.current_phase, PHASE_ENVELOPES["Discovery"])
    
    def apply_phase_caps(self, values: Dict[str, float]) -> Dict[str, float]:
        """
        Apply phase-based caps to behavioral values.
        
        Args:
            values: Dict with keys like 'warmth', 'patience', 'repair', etc.
        
        Returns:
            Same dict with values capped by phase envelope
        """
        envelope = self.get_phase_envelope()
        capped = {}
        
        for key, value in values.items():
            cap_key = f"{key}_cap"
            if cap_key in envelope:
                capped[key] = min(value, envelope[cap_key])
            else:
                capped[key] = value
        
        return capped
    
    def get_phase_description(self) -> str:
        """Get the psychological stance for current phase."""
        envelope = self.get_phase_envelope()
        return envelope.get("description", "")




