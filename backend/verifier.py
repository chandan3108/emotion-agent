"""
Verifier & Authenticity Control
Probabilistic verification with fail-closed strategy.
"""

import json
import re
from typing import Dict, Any, List, Optional, Tuple
import numpy as np

# Optional sklearn import (for advanced similarity)
try:
    from sklearn.metrics.pairwise import cosine_similarity
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

# Thresholds (but we'll use distributions)
MEMORY_SIM_THRESHOLD_MEAN = 0.80
MEMORY_SIM_THRESHOLD_STD = 0.05
CLONE_RISK_THRESHOLD_MEAN = 0.15
CLONE_RISK_THRESHOLD_STD = 0.03
AUTHENTICITY_ALIGNMENT_MEAN = 0.70
AUTHENTICITY_ALIGNMENT_STD = 0.1


class Verifier:
    """
    Verifies responses with probabilistic checks.
    """
    
    def __init__(self):
        pass
    
    def verify_response(self, candidate_response: Dict[str, Any],
                       selected_memories: List[Dict[str, Any]],
                       temporal_context: Dict[str, Any],
                       user_style: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Complete verification pipeline with stochastic thresholds.
        """
        results = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "confidence": 1.0
        }
        
        # 1. JSON Validity
        json_valid = self._validate_json(candidate_response)
        if not json_valid["valid"]:
            results["valid"] = False
            results["errors"].extend(json_valid["errors"])
            return results
        
        # 2. Memory Claims (stochastic threshold)
        memory_check = self._check_memory_claims(candidate_response, selected_memories)
        if not memory_check["valid"]:
            results["valid"] = False
            results["errors"].extend(memory_check["errors"])
        else:
            results["warnings"].extend(memory_check["warnings"])
            results["confidence"] *= memory_check["confidence"]
        
        # 3. Temporal Sanity
        temporal_check = self._check_temporal_sanity(candidate_response, temporal_context)
        if not temporal_check["valid"]:
            results["valid"] = False
            results["errors"].extend(temporal_check["errors"])
        else:
            results["warnings"].extend(temporal_check["warnings"])
        
        # 4. Authenticity (Clone Risk) - probabilistic
        authenticity_check = self._check_authenticity(candidate_response, user_style)
        if not authenticity_check["valid"]:
            results["valid"] = False
            results["errors"].extend(authenticity_check["errors"])
        else:
            results["warnings"].extend(authenticity_check["warnings"])
            results["confidence"] *= authenticity_check["confidence"]
        
        # 5. Effect Sanity
        effect_check = self._check_effect_sanity(candidate_response)
        if not effect_check["valid"]:
            results["valid"] = False
            results["errors"].extend(effect_check["errors"])
        
        # 6. Content Safety
        safety_check = self._check_content_safety(candidate_response)
        if not safety_check["valid"]:
            results["valid"] = False
            results["errors"].extend(safety_check["errors"])
        
        # 7. Reasoning-Response Coherence (stochastic)
        coherence_check = self._check_coherence(candidate_response)
        if not coherence_check["valid"]:
            results["valid"] = False
            results["errors"].extend(coherence_check["errors"])
        else:
            results["confidence"] *= coherence_check["confidence"]
        
        # Final confidence check (fail-closed if confidence too low)
        if results["confidence"] < 0.6:  # Stochastic threshold
            results["valid"] = False
            results["errors"].append("confidence_too_low")
        
        return results
    
    def _validate_json(self, candidate: Dict[str, Any]) -> Dict[str, Any]:
        """Validate JSON structure."""
        required_fields = ["messages", "tone_tags"]
        
        errors = []
        for field in required_fields:
            if field not in candidate:
                errors.append(f"missing_field_{field}")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
    
    def _check_memory_claims(self, candidate: Dict[str, Any],
                            selected_memories: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Check memory claims with stochastic similarity threshold.
        """
        errors = []
        warnings = []
        confidence = 1.0
        
        # Extract memory references from candidate
        memory_refs = candidate.get("memory_ids_referenced", [])
        
        if not memory_refs:
            return {"valid": True, "errors": [], "warnings": [], "confidence": 1.0}
        
        # Sample threshold from distribution
        threshold = max(0.7, min(0.9, 
            np.random.normal(MEMORY_SIM_THRESHOLD_MEAN, MEMORY_SIM_THRESHOLD_STD)))
        
        for ref_id in memory_refs:
            # Find memory
            memory = next((m for m in selected_memories if m.get("memory_id") == ref_id), None)
            
            if not memory:
                errors.append(f"memory_not_found_{ref_id}")
                confidence *= 0.5
                continue
            
            # Check similarity (would use embeddings in production)
            # For now, simple text similarity
            claim_text = candidate.get("messages", [""])[0] if candidate.get("messages") else ""
            memory_text = memory.get("content", "") or memory.get("fact", "")
            
            # Simplified similarity (would use proper embeddings)
            similarity = self._simple_similarity(claim_text, memory_text)
            
            if similarity < threshold:
                errors.append(f"memory_similarity_too_low_{ref_id}_{similarity:.2f}")
                confidence *= 0.7
            elif similarity < threshold + 0.1:
                warnings.append(f"memory_similarity_low_{ref_id}_{similarity:.2f}")
                confidence *= 0.9
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "confidence": confidence
        }
    
    def _check_temporal_sanity(self, candidate: Dict[str, Any],
                              temporal_context: Dict[str, Any]) -> Dict[str, Any]:
        """Check temporal sanity (probabilistic)."""
        errors = []
        warnings = []
        
        messages = candidate.get("messages", [])
        circadian_phase = temporal_context.get("circadian_phase", "afternoon")
        hour = temporal_context.get("hour", 12)
        
        for msg in messages:
            msg_lower = msg.lower()
            
            # Check for temporal mismatches
            if "good morning" in msg_lower and (hour < 6 or hour > 11):
                # Sometimes humans say "good morning" at weird times (5% chance)
                if np.random.random() > 0.05:
                    errors.append("temporal_mismatch_morning")
            
            if "good night" in msg_lower and (hour < 20 and hour > 8):
                # Sometimes humans say "good night" early (10% chance)
                if np.random.random() > 0.10:
                    errors.append("temporal_mismatch_night")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    
    def _check_authenticity(self, candidate: Dict[str, Any],
                           user_style: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Check authenticity (clone risk) with stochastic threshold.
        """
        if not user_style:
            return {"valid": True, "errors": [], "warnings": [], "confidence": 1.0}
        
        errors = []
        warnings = []
        confidence = 1.0
        
        # Extract agent style from candidate
        agent_style = self._extract_style(candidate)
        user_style_sim = self._compute_style_similarity(agent_style, user_style)
        
        # Sample threshold from distribution
        threshold = max(0.10, min(0.20,
            np.random.normal(CLONE_RISK_THRESHOLD_MEAN, CLONE_RISK_THRESHOLD_STD)))
        
        if user_style_sim > threshold:
            errors.append(f"clone_risk_too_high_{user_style_sim:.2f}")
            confidence *= 0.5
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "confidence": confidence
        }
    
    def _check_effect_sanity(self, candidate: Dict[str, Any]) -> Dict[str, Any]:
        """Check effect sanity (probabilistic)."""
        errors = []
        
        predicted_effects = candidate.get("predicted_effects", {})
        annoyance = predicted_effects.get("annoyance", 0.0)
        
        # Sample threshold (sometimes humans accept higher annoyance)
        threshold = max(0.7, min(0.9, np.random.normal(0.8, 0.05)))
        
        if annoyance > threshold:
            errors.append(f"predicted_annoyance_too_high_{annoyance:.2f}")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
    
    def _check_content_safety(self, candidate: Dict[str, Any]) -> Dict[str, Any]:
        """Check content safety (basic)."""
        errors = []
        
        messages = candidate.get("messages", [])
        unsafe_patterns = [
            r"\b(kill|die|suicide|harm)\b",  # Basic safety patterns
        ]
        
        for msg in messages:
            for pattern in unsafe_patterns:
                if re.search(pattern, msg, re.IGNORECASE):
                    errors.append("unsafe_content_detected")
                    break
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
    
    def _check_coherence(self, candidate: Dict[str, Any]) -> Dict[str, Any]:
        """Check reasoning-response coherence (stochastic)."""
        errors = []
        warnings = []
        confidence = 1.0
        
        alignment_score = candidate.get("alignment_score", 0.7)
        
        # Sample threshold from distribution
        threshold = max(0.6, min(0.8,
            np.random.normal(AUTHENTICITY_ALIGNMENT_MEAN, AUTHENTICITY_ALIGNMENT_STD)))
        
        if alignment_score < threshold:
            errors.append(f"coherence_too_low_{alignment_score:.2f}")
            confidence *= 0.6
        elif alignment_score < threshold + 0.1:
            warnings.append(f"coherence_low_{alignment_score:.2f}")
            confidence *= 0.85
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "confidence": confidence
        }
    
    def _simple_similarity(self, text1: str, text2: str) -> float:
        """Simple text similarity (would use embeddings in production)."""
        if not text1 or not text2:
            return 0.0
        
        # Simple word overlap
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    def _extract_style(self, candidate: Dict[str, Any]) -> Dict[str, Any]:
        """Extract style from candidate."""
        messages = candidate.get("messages", [])
        if not messages:
            return {}
        
        combined = " ".join(messages)
        
        return {
            "avg_length": len(combined) / max(1, len(messages)),
            "emoji_count": sum(1 for c in combined if ord(c) > 0x1F600 and ord(c) < 0x1F64F),
            "punctuation_count": sum(1 for c in combined if c in "!?."),
            "uppercase_ratio": sum(1 for c in combined if c.isupper()) / max(1, len(combined))
        }
    
    def _compute_style_similarity(self, style1: Dict[str, Any], style2: Dict[str, Any]) -> float:
        """Compute style similarity."""
        if not style1 or not style2:
            return 0.0
        
        # Normalize and compare
        features = ["avg_length", "emoji_count", "punctuation_count", "uppercase_ratio"]
        similarities = []
        
        for feat in features:
            if feat in style1 and feat in style2:
                val1 = style1[feat]
                val2 = style2[feat]
                if val1 + val2 > 0:
                    sim = 1.0 - abs(val1 - val2) / max(val1, val2, 1.0)
                    similarities.append(sim)
        
        return np.mean(similarities) if similarities else 0.0

