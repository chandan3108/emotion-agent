"""
Cognitive Router (Stage 6)
12-parameter decision tree + 7-agent quantum debate routing.
Determines which cognitive engines to activate based on message complexity and context.
"""

from typing import Dict, Any, Optional, List
import numpy as np
import random


class CognitiveRouter:
    """
    12-parameter decision tree for routing messages to appropriate cognitive engines.
    Works in conjunction with QMAS (Quantum Multi-Agent System).
    """
    
    def __init__(self):
        # 12 parameters for decision tree
        self.parameters = {
            "message_complexity": 0.0,  # 0-1, from semantic understanding
            "emotional_depth": 0.0,  # 0-1, from perception
            "relationship_phase": "Discovery",  # Discovery, Building, Steady, Deep, etc.
            "trust_level": 0.5,  # 0-1
            "hurt_level": 0.0,  # 0-1
            "conflict_stage": None,  # TRIGGER, ESCALATION, IMPASSE, etc.
            "time_since_last_message": 0.0,  # hours
            "circadian_phase": "afternoon",  # morning, afternoon, evening, late_night
            "energy_level": 0.5,  # 0-1
            "unresolved_threads": 0,  # count
            "reciprocity_balance": 0.0,  # -1 to +1
            "vulnerability_willingness": 0.5  # 0-1
        }
    
    def route(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Route message through 12-parameter decision tree.
        
        Returns:
            {
                "use_qmas": bool,
                "use_deep_reasoning": bool,
                "use_enhanced_semantic": bool,
                "use_creativity": bool,
                "use_self_narrative": bool,
                "reasoning_depth": float,  # 0-1
                "qmas_paths": int,  # number of paths to sample
                "reasoning": str  # explanation of routing decision
            }
        """
        # Update parameters from context
        self.parameters.update({
            "message_complexity": context.get("complexity", 0.5),
            "emotional_depth": context.get("emotional_depth", 0.5),
            "relationship_phase": context.get("relationship_phase", "Discovery"),
            "trust_level": context.get("trust", 0.5),
            "hurt_level": context.get("hurt", 0.0),
            "conflict_stage": context.get("conflict_stage"),
            "time_since_last_message": context.get("hours_since_last_message", 0.0),
            "circadian_phase": context.get("circadian_phase", "afternoon"),
            "energy_level": context.get("energy", 0.5),
            "unresolved_threads": context.get("unresolved_threads", 0),
            "reciprocity_balance": context.get("reciprocity_balance", 0.0),
            "vulnerability_willingness": context.get("vulnerability_willingness", 0.5)
        })
        
        p = self.parameters
        
        # Decision tree logic
        routing = {
            "use_qmas": False,
            "use_deep_reasoning": False,
            "use_enhanced_semantic": False,
            "use_creativity": False,
            "use_self_narrative": False,
            "reasoning_depth": 0.5,
            "qmas_paths": 10,
            "reasoning": ""
        }
        
        reasoning_parts = []
        
        # 1. Enhanced Semantic (always for complex messages)
        if p["message_complexity"] >= 0.3:
            routing["use_enhanced_semantic"] = True
            reasoning_parts.append("complexity >= 0.3")
        
        # 2. QMAS (for high complexity, conflict, or deep emotional situations)
        qmas_score = (
            p["message_complexity"] * 0.4 +
            p["emotional_depth"] * 0.3 +
            (1.0 if p["conflict_stage"] else 0.0) * 0.2 +
            p["hurt_level"] * 0.1
        )
        
        if qmas_score >= 0.6:
            routing["use_qmas"] = True
            routing["qmas_paths"] = 20 if qmas_score >= 0.8 else 10
            reasoning_parts.append(f"QMAS needed (score={qmas_score:.2f})")
        
        # 3. Deep Reasoning (for conflicts, high hurt, or deep relationship phases)
        if (p["conflict_stage"] or 
            p["hurt_level"] > 0.6 or 
            (p["relationship_phase"] in ["Deep", "Maintenance"] and p["message_complexity"] > 0.5)):
            routing["use_deep_reasoning"] = True
            routing["reasoning_depth"] = max(0.7, p["message_complexity"])
            reasoning_parts.append("deep reasoning needed")
        
        # 4. Creativity (for boredom, high energy, positive mood)
        if (p["energy_level"] > 0.6 and 
            p["hurt_level"] < 0.3 and 
            not p["conflict_stage"] and
            p["relationship_phase"] in ["Building", "Steady", "Deep"]):
            creativity_score = (
                (1.0 - p.get("boredom", 0.5)) * 0.5 +
                p["energy_level"] * 0.3 +
                p["vulnerability_willingness"] * 0.2
            )
            if creativity_score > 0.5:
                routing["use_creativity"] = True
                reasoning_parts.append("creativity appropriate")
        
        # 5. Self-Narrative (for deep relationships, high trust, vulnerability)
        if (p["relationship_phase"] in ["Deep", "Maintenance"] and
            p["trust_level"] > 0.7 and
            p["vulnerability_willingness"] > 0.6 and
            not p["conflict_stage"]):
            routing["use_self_narrative"] = True
            reasoning_parts.append("self-narrative appropriate")
        
        routing["reasoning"] = "; ".join(reasoning_parts) if reasoning_parts else "standard routing"
        
        return routing

