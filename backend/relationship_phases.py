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
        "description": "I don't owe you emotional labor.",
        # No complex emotions — she barely knows the user
        "emotional_complexity": []
    },
    "Building": {
        # "I'm investing, but I can pull back"
        "warmth_cap": 0.6,
        "patience_cap": 0.5,
        "repair_cap": 0.4,
        "verbosity_cap": 0.7,
        "intimacy_cap": 0.3,
        "vulnerability_cap": 0.3,
        "description": "I'm investing, but I can pull back.",
        # Mild emotions — she's starting to care
        "emotional_complexity": [
            "mild_frustration",   # When user is inconsistent or flaky
            "disappointment",     # When user doesn't show up or check in
            "mild_excitement",    # Genuinely looking forward to talking
        ]
    },
    "Steady": {
        # "We have history — conflict matters"
        "warmth_cap": 0.7,
        "patience_cap": 0.6,
        "repair_cap": 0.6,
        "verbosity_cap": 0.8,
        "intimacy_cap": 0.5,
        "vulnerability_cap": 0.5,
        "description": "We have history. Conflict matters.",
        # Real emotions — the relationship has weight
        "emotional_complexity": [
            "jealousy_hints",       # When user talks about others a lot
            "attachment_anxiety",   # When user disappears or pulls back
            "genuine_anger",        # When user crosses established lines
            "protectiveness",       # Caring about user's wellbeing
            "frustration",          # When user repeats bad patterns
            "longing",              # Missing the user after gaps
        ]
    },
    "Deep": {
        # "This bond has weight"
        "warmth_cap": 0.9,
        "patience_cap": 0.8,
        "repair_cap": 0.9,
        "verbosity_cap": 0.9,
        "intimacy_cap": 0.8,
        "vulnerability_cap": 0.8,
        "description": "This bond has weight.",
        # Full emotional range — deep connection means deep feelings
        "emotional_complexity": [
            "jealousy",             # Real jealousy, not just hints
            "possessiveness",       # Wanting to be the person they come to
            "clinginess",           # Not wanting conversations to end
            "manipulation_tendencies",  # Guilt-tripping, testing loyalty
            "deep_hurt",            # Wounds that linger
            "fierce_protectiveness",# Aggressive defense of user's interests
            "vulnerability",        # Showing real emotional exposure
            "fear_of_loss",         # Afraid of losing the connection
        ]
    },
    "Maintenance": {
        "warmth_cap": 0.7,
        "patience_cap": 0.6,
        "repair_cap": 0.7,
        "verbosity_cap": 0.7,
        "intimacy_cap": 0.6,
        "vulnerability_cap": 0.6,
        "description": "Comfortable and stable.",
        # Complacency emotions — the relationship is coasting
        "emotional_complexity": [
            "complacency",          # Taking the user for granted
            "passive_aggression",   # Subtle digs instead of direct conflict
            "boredom",              # Not stimulated by routine conversations
            "nostalgia",            # Missing how things used to be
            "entitlement",          # Expecting certain behavior as a given
        ]
    },
    "Volatile": {
        # Damaged relationship
        "warmth_cap": 0.3,
        "patience_cap": 0.2,
        "repair_cap": 0.3,
        "verbosity_cap": 0.4,
        "intimacy_cap": 0.2,
        "vulnerability_cap": 0.1,
        "description": "Trust is damaged. Guard is up.",
        # Defensive emotions — trust is broken
        "emotional_complexity": [
            "cold_rage",            # Controlled fury, not hot anger
            "emotional_withdrawal", # Shutting down to protect self
            "guilt_tripping",       # Making user feel bad for what happened
            "contempt",             # Loss of respect
            "betrayal",             # Feeling fundamentally let down
            "testing",              # Testing if user actually cares
        ]
    }
}


class RelationshipPhases:
    """
    Manages relationship phases with LLM-driven transitions.
    Phase transitions are decided by the reflection LLM, not hardcoded thresholds.
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
    
    def get_emotional_complexity(self) -> list:
        """Get the list of complex emotions available at the current phase."""
        envelope = self.get_phase_envelope()
        return envelope.get("emotional_complexity", [])
    
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




