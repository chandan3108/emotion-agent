"""
Enhanced Semantic Extraction
Distribution-based interpretation with ambiguity resolution.
"""

import os
import re
from typing import Dict, Any, List, Optional
import httpx
import json
import numpy as np

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
HF_TOKEN = GROQ_API_KEY  # Alias for compatibility
MODEL_ID = os.environ.get("MODEL_ID", "llama-3.1-8b-instant")
INFERENCE_URL = "https://api.groq.com/openai/v1/chat/completions"


class EnhancedSemanticExtractor:
    """
    Enhanced semantic understanding with probabilistic interpretation.
    """
    
    def __init__(self):
        self.has_llm = bool(HF_TOKEN)
    
    async def extract_enhanced_understanding(self, message: str, context: Dict[str, Any],
                                           historical_patterns: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Extract enhanced semantic understanding with distribution-based interpretation.
        """
        # 1. Linguistic Surface Analysis
        linguistic = self._analyze_linguistic_surface(message)
        
        # 2. Contradiction Detection (probabilistic)
        contradiction = self._detect_contradiction(message, context)
        
        # 3. Context-Aware Interpretation (stochastic)
        context_interpretation = self._context_aware_interpretation(message, context, historical_patterns)
        
        # 4. Sarcasm Detection (probabilistic)
        sarcasm = self._detect_sarcasm(message, context, historical_patterns)
        
        # 5. Emotional Truthfulness (distribution-based)
        emotional_truth = self._reconcile_emotional_truth(message, context)
        
        # 6. Power Dynamics (stochastic inference)
        power_dynamics = self._infer_power_dynamics(message, context)
        
        # 7. Long-term Pattern Matching (probabilistic)
        pattern_match = self._match_long_term_patterns(message, historical_patterns)
        
        # 8. Ambiguity Resolution (weighted scoring)
        ambiguity_resolution = self._resolve_ambiguity(message, context, historical_patterns)
        
        return {
            "linguistic_analysis": linguistic,
            "contradiction": contradiction,
            "context_interpretation": context_interpretation,
            "sarcasm": sarcasm,
            "emotional_truth": emotional_truth,
            "power_dynamics": power_dynamics,
            "pattern_match": pattern_match,
            "ambiguity_resolution": ambiguity_resolution,
            "confidence": self._compute_confidence(linguistic, contradiction, sarcasm, ambiguity_resolution)
        }
    
    def _analyze_linguistic_surface(self, message: str) -> Dict[str, Any]:
        """Analyze linguistic surface features."""
        # Detect negations
        negations = len(re.findall(r'\b(not|no|never|nothing|nobody|nowhere)\b', message, re.IGNORECASE))
        
        # Detect intensifiers
        intensifiers = len(re.findall(r'\b(very|really|so|extremely|incredibly|absolutely)\b', message, re.IGNORECASE))
        
        # Detect qualifiers
        qualifiers = len(re.findall(r'\b(maybe|perhaps|probably|possibly|sort of|kind of)\b', message, re.IGNORECASE))
        
        return {
            "negation_count": negations,
            "intensifier_count": intensifiers,
            "qualifier_count": qualifiers,
            "has_negation": negations > 0,
            "has_intensifier": intensifiers > 0,
            "has_qualifier": qualifiers > 0
        }
    
    def _detect_contradiction(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Detect contradiction between text and emotion (probabilistic).
        """
        stated_emotion = context.get("emotion", "neutral")
        emotion_vector = context.get("emotion_vector", {})
        
        # Sample contradiction probability from distribution
        contradiction_prob_mean = 0.0
        
        # Check for common contradictions
        message_lower = message.lower()
        if "fine" in message_lower and stated_emotion in ["sad", "angry", "stressed"]:
            contradiction_prob_mean = 0.7  # "I'm fine" when not fine
        elif "okay" in message_lower and stated_emotion in ["sad", "angry"]:
            contradiction_prob_mean = 0.6
        
        contradiction_prob_std = 0.15
        contradiction_prob = max(0.0, min(1.0,
            np.random.normal(contradiction_prob_mean, contradiction_prob_std)))
        
        return {
            "has_contradiction": contradiction_prob > 0.5,
            "contradiction_probability": contradiction_prob,
            "contradiction_type": "emotional_masking" if contradiction_prob > 0.5 else None
        }
    
    def _context_aware_interpretation(self, message: str, context: Dict[str, Any],
                                     historical_patterns: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Context-aware interpretation (stochastic).
        """
        # Check if user historically reverses intent
        reverse_prob = 0.0
        if historical_patterns:
            # Count reversals in history
            reversals = sum(1 for p in historical_patterns if p.get("reversed_intent", False))
            if reversals > 0:
                reverse_prob = min(0.5, reversals / len(historical_patterns))
        
        # Sample interpretation confidence
        confidence_mean = 0.7
        confidence_std = 0.15
        confidence = max(0.0, min(1.0, np.random.normal(confidence_mean, confidence_std)))
        
        return {
            "interpretation_confidence": confidence,
            "reverse_intent_probability": reverse_prob,
            "context_relevant": len(historical_patterns) > 0
        }
    
    def _detect_sarcasm(self, message: str, context: Dict[str, Any],
                       historical_patterns: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Detect sarcasm (probabilistic).
        """
        message_lower = message.lower()
        
        # Linguistic markers
        sarcasm_markers = ["sure", "yeah right", "obviously", "of course"]
        has_marker = any(marker in message_lower for marker in sarcasm_markers)
        
        # Polarity contradiction
        positive_words = ["great", "wonderful", "amazing", "perfect"]
        negative_words = ["terrible", "awful", "horrible", "bad"]
        has_positive = any(word in message_lower for word in positive_words)
        has_negative = any(word in message_lower for word in negative_words)
        polarity_contradiction = has_positive and context.get("emotion", "neutral") in ["sad", "angry"]
        
        # Historical baseline
        historical_sarcasm_rate = 0.0
        if historical_patterns:
            sarcasm_count = sum(1 for p in historical_patterns if p.get("sarcasm", False))
            historical_sarcasm_rate = sarcasm_count / len(historical_patterns)
        
        # Combine signals (stochastic)
        sarcasm_prob_mean = 0.0
        if has_marker:
            sarcasm_prob_mean += 0.3
        if polarity_contradiction:
            sarcasm_prob_mean += 0.4
        sarcasm_prob_mean += historical_sarcasm_rate * 0.3
        
        sarcasm_prob_std = 0.2
        sarcasm_prob = max(0.0, min(1.0, np.random.normal(sarcasm_prob_mean, sarcasm_prob_std)))
        
        return {
            "is_sarcastic": sarcasm_prob > 0.5,
            "sarcasm_probability": sarcasm_prob,
            "markers_detected": has_marker,
            "polarity_contradiction": polarity_contradiction
        }
    
    def _reconcile_emotional_truth(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Reconcile emotional truth (distribution-based).
        """
        stated_emotion = context.get("emotion", "neutral")
        emotion_vector = context.get("emotion_vector", {})
        
        # Sample actual emotion from distribution
        if emotion_vector:
            # Use emotion vector to sample
            emotions = list(emotion_vector.keys())
            probs = list(emotion_vector.values())
            if probs:
                # Normalize
                total = sum(probs)
                if total > 0:
                    probs = [p / total for p in probs]
                    # Sample
                    actual_emotion = np.random.choice(emotions, p=probs)
                else:
                    actual_emotion = stated_emotion
            else:
                actual_emotion = stated_emotion
        else:
            actual_emotion = stated_emotion
        
        # Check if masked
        is_masked = actual_emotion != stated_emotion
        
        # Sample intensity
        intensity_mean = emotion_vector.get(actual_emotion, 0.5) if emotion_vector else 0.5
        intensity_std = 0.15
        intensity = max(0.0, min(1.0, np.random.normal(intensity_mean, intensity_std)))
        
        return {
            "actual_emotion": actual_emotion,
            "stated_emotion": stated_emotion,
            "is_masked": is_masked,
            "intensity": intensity
        }
    
    def _infer_power_dynamics(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Infer power dynamics (stochastic).
        """
        message_lower = message.lower()
        
        # Vulnerability indicators
        vulnerability_words = ["sorry", "apologize", "my fault", "i was wrong"]
        has_vulnerability = any(word in message_lower for word in vulnerability_words)
        
        # Authority indicators
        authority_words = ["you should", "you need to", "you must", "i expect"]
        has_authority = any(word in message_lower for word in authority_words)
        
        # Sample power dynamic
        if has_vulnerability:
            dynamic = "user_vulnerable"
            power_balance = np.random.normal(0.3, 0.1)  # User lower power
        elif has_authority:
            dynamic = "user_authoritative"
            power_balance = np.random.normal(0.7, 0.1)  # User higher power
        else:
            dynamic = "balanced"
            power_balance = np.random.normal(0.5, 0.1)
        
        return {
            "power_dynamic": dynamic,
            "power_balance": max(0.0, min(1.0, power_balance)),
            "user_vulnerable": has_vulnerability,
            "user_authoritative": has_authority
        }
    
    def _match_long_term_patterns(self, message: str, historical_patterns: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Match long-term patterns (probabilistic).
        """
        if not historical_patterns:
            return {"matched_patterns": [], "match_confidence": 0.0}
        
        matched = []
        message_lower = message.lower()
        
        for pattern in historical_patterns[-20:]:  # Last 20 patterns
            pattern_text = pattern.get("text", "").lower()
            if pattern_text:
                # Simple similarity
                similarity = len(set(message_lower.split()) & set(pattern_text.split())) / max(1, len(set(message_lower.split()) | set(pattern_text.split())))
                
                # Sample match confidence
                if similarity > 0.3:
                    confidence_mean = similarity
                    confidence_std = 0.15
                    confidence = max(0.0, min(1.0, np.random.normal(confidence_mean, confidence_std)))
                    
                    if confidence > 0.4:
                        matched.append({
                            "pattern_id": pattern.get("pattern_id"),
                            "similarity": similarity,
                            "confidence": confidence
                        })
        
        return {
            "matched_patterns": matched,
            "match_confidence": np.mean([m["confidence"] for m in matched]) if matched else 0.0
        }
    
    def _resolve_ambiguity(self, message: str, context: Dict[str, Any],
                          historical_patterns: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Resolve ambiguity with weighted scoring (stochastic).
        """
        # Example: "maybe we should take a break"
        message_lower = message.lower()
        
        ambiguous_phrases = {
            "take a break": {
                "interpretations": ["temporary_cooling", "breakup_signal"],
                "weights": [0.5, 0.5]  # Base weights
            }
        }
        
        resolution = {
            "is_ambiguous": False,
            "interpretations": [],
            "selected_interpretation": None,
            "confidence": 1.0
        }
        
        for phrase, config in ambiguous_phrases.items():
            if phrase in message_lower:
                resolution["is_ambiguous"] = True
                
                # Adjust weights based on context (stochastic)
                trust = context.get("trust", 0.7)
                has_recent_fight = context.get("has_recent_fight", False)
                
                weights = config["weights"].copy()
                
                if trust > 0.7 and not has_recent_fight:
                    # More likely temporary cooling
                    weights[0] = 0.8
                    weights[1] = 0.2
                elif trust < 0.4 and has_recent_fight:
                    # More likely breakup signal
                    weights[0] = 0.2
                    weights[1] = 0.8
                
                # Add noise
                weights = [max(0.0, min(1.0, w + np.random.normal(0, 0.1))) for w in weights]
                # Renormalize
                total = sum(weights)
                if total > 0:
                    weights = [w / total for w in weights]
                
                # Sample interpretation
                selected = np.random.choice(config["interpretations"], p=weights)
                
                resolution["interpretations"] = [
                    {"interpretation": interp, "weight": w} 
                    for interp, w in zip(config["interpretations"], weights)
                ]
                resolution["selected_interpretation"] = selected
                resolution["confidence"] = max(weights)
        
        return resolution
    
    def _compute_confidence(self, linguistic: Dict[str, Any], contradiction: Dict[str, Any],
                           sarcasm: Dict[str, Any], ambiguity: Dict[str, Any]) -> float:
        """
        Compute overall confidence (stochastic).
        """
        confidence_factors = []
        
        # Linguistic clarity
        if linguistic.get("has_qualifier"):
            confidence_factors.append(0.8)  # Qualifiers reduce confidence
        else:
            confidence_factors.append(1.0)
        
        # Contradiction reduces confidence
        if contradiction.get("has_contradiction"):
            confidence_factors.append(0.6)
        else:
            confidence_factors.append(1.0)
        
        # Sarcasm reduces confidence
        if sarcasm.get("is_sarcastic"):
            confidence_factors.append(0.7)
        else:
            confidence_factors.append(1.0)
        
        # Ambiguity reduces confidence
        if ambiguity.get("is_ambiguous"):
            confidence_factors.append(ambiguity.get("confidence", 0.5))
        else:
            confidence_factors.append(1.0)
        
        # Sample final confidence
        base_confidence = np.mean(confidence_factors)
        confidence_std = 0.1
        return max(0.0, min(1.0, np.random.normal(base_confidence, confidence_std)))




