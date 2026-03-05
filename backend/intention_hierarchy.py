"""
Intention Hierarchy (Stage 8)
Micro/macro/strategic intentions ranked by alignment.
"""

from typing import Dict, Any, List, Optional
from enum import Enum
import numpy as np


class IntentionLevel(Enum):
    MICRO = "micro"  # Immediate response intent (e.g., "acknowledge", "question", "comfort")
    MACRO = "macro"  # Conversation-level intent (e.g., "build trust", "resolve conflict", "deepen connection")
    STRATEGIC = "strategic"  # Long-term relationship intent (e.g., "maintain stability", "grow intimacy", "repair damage")


class IntentionHierarchy:
    """
    Manages intention hierarchy: micro, macro, and strategic intentions.
    Ranks intentions by alignment with current state and goals.
    """
    
    def __init__(self):
        pass
    
    def generate_intentions(self, context: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Generate intentions at all three levels and rank by alignment.
        
        Args:
            context: Current psychological state, relationship phase, message context
        
        Returns:
            {
                "micro": [{"intent": str, "alignment": float, "priority": float}, ...],
                "macro": [{"intent": str, "alignment": float, "priority": float}, ...],
                "strategic": [{"intent": str, "alignment": float, "priority": float}, ...]
            }
        """
        trust = context.get("trust", 0.5)
        hurt = context.get("hurt", 0.0)
        relationship_phase = context.get("relationship_phase", "Discovery")
        conflict_stage = context.get("conflict_stage")
        message_emotion = context.get("emotion", "neutral")
        reciprocity = context.get("reciprocity_balance", 0.0)
        
        # Generate micro intentions (immediate response)
        micro_intentions = []
        
        if conflict_stage:
            micro_intentions.append({
                "intent": "de-escalate",
                "alignment": 0.9 if conflict_stage in ["ESCALATION", "IMPASSE"] else 0.5,
                "priority": 0.9
            })
        
        if message_emotion in ["sad", "angry", "frustrated"]:
            micro_intentions.append({
                "intent": "comfort",
                "alignment": 0.8,
                "priority": 0.8
            })
        
        if relationship_phase == "Discovery":
            micro_intentions.append({
                "intent": "establish_rapport",
                "alignment": 0.7,
                "priority": 0.6
            })
        
        # Default micro intention
        micro_intentions.append({
            "intent": "respond_naturally",
            "alignment": 0.5,
            "priority": 0.3
        })
        
        # Generate macro intentions (conversation-level)
        macro_intentions = []
        
        if conflict_stage:
            macro_intentions.append({
                "intent": "resolve_conflict",
                "alignment": 0.9,
                "priority": 0.9
            })
        
        if trust < 0.4:
            macro_intentions.append({
                "intent": "build_trust",
                "alignment": 0.8,
                "priority": 0.7
            })
        
        if relationship_phase == "Building":
            macro_intentions.append({
                "intent": "deepen_connection",
                "alignment": 0.7,
                "priority": 0.6
            })
        
        if reciprocity < -0.3:  # AI overextended
            macro_intentions.append({
                "intent": "establish_boundaries",
                "alignment": 0.8,
                "priority": 0.7
            })
        
        # Default macro intention
        macro_intentions.append({
            "intent": "maintain_relationship",
            "alignment": 0.5,
            "priority": 0.4
        })
        
        # Generate strategic intentions (long-term)
        strategic_intentions = []
        
        if relationship_phase == "Discovery":
            strategic_intentions.append({
                "intent": "establish_foundation",
                "alignment": 0.8,
                "priority": 0.7
            })
        elif relationship_phase == "Building":
            strategic_intentions.append({
                "intent": "grow_intimacy",
                "alignment": 0.7,
                "priority": 0.6
            })
        elif relationship_phase == "Deep":
            strategic_intentions.append({
                "intent": "maintain_depth",
                "alignment": 0.8,
                "priority": 0.7
            })
        elif relationship_phase == "Volatile":
            strategic_intentions.append({
                "intent": "stabilize_relationship",
                "alignment": 0.9,
                "priority": 0.9
            })
        
        # Default strategic intention
        strategic_intentions.append({
            "intent": "sustain_health",
            "alignment": 0.5,
            "priority": 0.5
        })
        
        # Rank all intentions by alignment * priority
        for intention_list in [micro_intentions, macro_intentions, strategic_intentions]:
            intention_list.sort(key=lambda x: x["alignment"] * x["priority"], reverse=True)
        
        return {
            "micro": micro_intentions,
            "macro": macro_intentions,
            "strategic": strategic_intentions
        }
    
    def get_primary_intentions(self, intentions: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Dict[str, Any]]:
        """
        Get the top intention from each level.
        
        Returns:
            {
                "micro": top micro intention,
                "macro": top macro intention,
                "strategic": top strategic intention
            }
        """
        return {
            "micro": intentions["micro"][0] if intentions["micro"] else None,
            "macro": intentions["macro"][0] if intentions["macro"] else None,
            "strategic": intentions["strategic"][0] if intentions["strategic"] else None
        }

