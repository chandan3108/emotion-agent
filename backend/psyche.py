"""
Psyche Engine - Emotion & Relationship Dynamics
Manages mood, trust, hurt, forgiveness, and emotion contagion.
"""

import math
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional
from enum import Enum


class ForgivenessState(Enum):
    UNFORGIVEN = "UNFORGIVEN"
    SOFTENING = "SOFTENING"
    TENTATIVE = "TENTATIVE"
    FORGIVEN = "FORGIVEN"


class PsycheEngine:
    """Manages psychological state: mood, trust, hurt, forgiveness, stance, respect, engagement."""
    
    def __init__(self, state: Dict[str, Any]):
        self.state = state
        self.psyche = state.get("current_psyche", {})
        self.mood = state.get("mood", {})
        self.neurochem = state.get("neurochem_vector", {})
        
        # === NEW 6-LAYER STATE MODEL ===
        # Stance: interpersonal attitude toward THIS user (volatile, can flip in one message)
        # Options: open, wary, guarded, irritated, bored, intrigued, defensive, affectionate, dismissive
        self.stance = self.psyche.get("stance", "open")
        
        # Respect: social valuation - how much effort the user deserves (0.0-1.0)
        self.respect = self.psyche.get("respect", 0.7)
        
        # Engagement: motivation to continue (0.0-1.0)
        # High = elaborates, asks follow-ups. Low = minimal replies, no repair
        self.engagement = self.psyche.get("engagement", 0.7)
        
        # Entitlement debt: patience depletion meter (0.0-1.0)
        # Increases when user assumes access, rushes intimacy, demands attention
        self.entitlement_debt = self.psyche.get("entitlement_debt", 0.0)
        
        # Anger/Frustration: intensity of negative reaction (0.0-1.0)
        # Increases with repeated disrespect, boundary violations, persistence after pushback
        # When high: blunt, short, may snap, no sugarcoating
        self.anger = self.psyche.get("anger", 0.0)
        
        # Disgust: complete loss of respect/attraction (0.0-1.0)
        # Increases with creepy behavior, entitlement, manipulation attempts
        # When high: cold, withdrawn, may end conversation
        self.disgust = self.psyche.get("disgust", 0.0)
        
        # Posture overlay: text block from reflection describing current behavioral tendencies
        self.posture = self.psyche.get("posture", "")
    
    # ========== Mood System (14-dimensional) ==========
    
    def update_mood(self, emotion_impact: Dict[str, float], delta_hours: float):
        """
        Update mood vector with decay and new impact.
        
        CRITICAL: Mood is influenced by neurochemicals, not just events.
        This is how real emotions work - hormones drive feelings.
        
        Args:
            emotion_impact: Dict of emotion -> impact value (0-1)
            delta_hours: Hours since last update
        """
        TAU_MOOD = 6.0  # 6-hour half-life
        
        # Get neurochemical influence on mood (THIS IS KEY)
        neuro_influence = self.get_neurochemical_influence_on_mood()
        
        # Decay existing mood
        for emotion in self.mood:
            if emotion in self.mood:
                self.mood[emotion] = self.mood[emotion] * math.exp(-delta_hours / TAU_MOOD)
        
        # Apply new impact (70% decayed, 30% new)
        for emotion, impact in emotion_impact.items():
            if emotion in self.mood:
                self.mood[emotion] = 0.7 * self.mood[emotion] + 0.3 * impact
            else:
                self.mood[emotion] = 0.3 * impact
        
        # Apply neurochemical influence (THIS IS WHAT MAKES IT REAL)
        # Neurochemicals modulate mood - this is how biology works
        for emotion, neuro_value in neuro_influence.items():
            if emotion in self.mood:
                # Blend: 60% current mood, 40% neurochemical influence
                self.mood[emotion] = 0.6 * self.mood[emotion] + 0.4 * neuro_value
        
        # Clamp to [0, 1]
        for emotion in self.mood:
            self.mood[emotion] = max(0.0, min(1.0, self.mood[emotion]))
    
    def get_mood_vector(self) -> Dict[str, float]:
        """Get current 14-dimensional mood vector."""
        return self.mood.copy()
    
    # ========== Trust & Hurt Ledgers ==========
    
    def update_trust(self, positive_event_score: float, alpha_pos: float = 0.1):
        """
        Update trust based on positive event.
        
        Formula: trust += α × positive_event_score × (1 - trust)
        """
        current_trust = self.psyche.get("trust", 0.7)
        new_trust = current_trust + alpha_pos * positive_event_score * (1 - current_trust)
        self.psyche["trust"] = max(0.0, min(1.0, new_trust))
    
    def update_hurt(self, hurt_event_score: float, alpha_neg: float = 0.15):
        """
        Update hurt based on negative event.
        
        Formula: hurt += α × hurt_event_score × (1 - hurt)
        """
        current_hurt = self.psyche.get("hurt", 0.0)
        new_hurt = current_hurt + alpha_neg * hurt_event_score * (1 - current_hurt)
        self.psyche["hurt"] = max(0.0, min(1.0, new_hurt))
    
    def decay_hurt(self, delta_hours: float):
        """
        Decay hurt over time.
        
        Formula: hurt(t) = hurt_0 × e^(-t/48h)
        """
        TAU_HURT = 48.0  # 48-hour half-life
        current_hurt = self.psyche.get("hurt", 0.0)
        self.psyche["hurt"] = current_hurt * math.exp(-delta_hours / TAU_HURT)
    
    # ========== Forgiveness Finite-State Machine ==========
    
    def update_forgiveness(self, sincerity_score: float, reparative_action: bool = False,
                          consistency_score: float = 0.0):
        """
        Update forgiveness FSM based on repair attempts.
        
        States: UNFORGIVEN → SOFTENING → TENTATIVE → FORGIVEN
        """
        current_state_str = self.psyche.get("forgiveness_state", "FORGIVEN")
        current_state = ForgivenessState(current_state_str)
        progress = self.psyche.get("forgiveness_progress", 1.0)
        
        # Progress gains
        if sincerity_score > 0:
            progress += 0.3 * sincerity_score
        
        if reparative_action:
            progress += 0.5 * consistency_score
        
        # State transitions
        if current_state == ForgivenessState.UNFORGIVEN:
            if progress >= 0.3:
                current_state = ForgivenessState.SOFTENING
                progress = 0.3
        elif current_state == ForgivenessState.SOFTENING:
            if progress >= 0.6:
                current_state = ForgivenessState.TENTATIVE
                progress = 0.6
        elif current_state == ForgivenessState.TENTATIVE:
            if progress >= 0.9:
                current_state = ForgivenessState.FORGIVEN
                progress = 1.0
        
        # Clamp progress
        progress = max(0.0, min(1.0, progress))
        
        self.psyche["forgiveness_state"] = current_state.value
        self.psyche["forgiveness_progress"] = progress
    
    def get_trust_restoration_multiplier(self) -> float:
        """Get trust restoration multiplier based on forgiveness state."""
        state_str = self.psyche.get("forgiveness_state", "FORGIVEN")
        state = ForgivenessState(state_str)
        
        multipliers = {
            ForgivenessState.UNFORGIVEN: 0.2,
            ForgivenessState.SOFTENING: 0.5,
            ForgivenessState.TENTATIVE: 0.85,
            ForgivenessState.FORGIVEN: 1.2
        }
        
        return multipliers.get(state, 1.0)
    
    # ========== Emotion Contagion ==========
    
    def apply_emotion_contagion(self, user_emotion_vector: Dict[str, float],
                                relationship_closeness: float, empathy_depth: float):
        """
        Apply emotion contagion - user's emotions "pull" AI's mood.
        
        Formula: contagion_factor = 0.3 × closeness + 0.2 × empathy
        """
        contagion_factor = 0.3 * relationship_closeness + 0.2 * empathy_depth
        damping = 0.6  # Prevent runaway escalations
        
        for emotion, user_value in user_emotion_vector.items():
            if emotion in self.mood:
                # Pull AI mood toward user emotion
                delta = (user_value - self.mood[emotion]) * contagion_factor * damping
                self.mood[emotion] = max(0.0, min(1.0, self.mood[emotion] + delta))
    
    # ========== Neurochemical Cascade (Context-Sensitive) ==========
    
    def _jitter(self, base: float, variance: float = 0.15) -> float:
        """Add random variance to a coefficient so identical events never feel the same."""
        import random
        return base * (1.0 + random.uniform(-variance, variance))
    
    def update_neurochemicals(self, event_type: str, intensity: float = 1.0, 
                             delta_hours: float = 0.0,
                             trust: float = 0.5, relationship_phase: str = "Discovery"):
        """
        Update neurotransmitter levels based on event type with context-sensitive cascades.
        
        Key improvement: Impact scales with trust and relationship phase.
        - Conflict with a trusted person hurts MORE (higher cort, bigger oxy drop)
        - Affection from a stranger has LESS bonding effect
        - Each coefficient gets ±15% random jitter so reactions are never identical
        
        Args:
            event_type: Type of event
            intensity: How intense the event was (0-1)
            delta_hours: Hours since last update (for natural decay)
            trust: Current trust level (0-1), modulates emotional impact
            relationship_phase: Current phase, affects which emotions activate
        """
        # Natural decay over time (neurotransmitters don't stay elevated forever)
        half_lives = {
            "da": 2.0,   # Dopamine: short half-life, quick spikes/decays
            "cort": 1.5,  # Cortisol: stress hormone, decays relatively quickly
            "oxy": 3.0,   # Oxytocin: bonding hormone, longer lasting
            "ser": 4.0,   # Serotonin: mood stabilizer, longest lasting
            "ne": 1.0     # Norepinephrine: alertness, very short half-life
        }
        
        for neuro, half_life in half_lives.items():
            if neuro in self.neurochem:
                baseline = 0.5
                decay_factor = math.exp(-delta_hours / half_life)
                self.neurochem[neuro] = baseline + (self.neurochem[neuro] - baseline) * decay_factor
        
        # Context multipliers: closer relationships = stronger emotional reactions
        # Discovery (strangers) → muted reactions; Deep → amplified
        closeness = trust  # 0-1, directly scales interpersonal impact
        phase_weight = {"Discovery": 0.5, "Building": 0.7, "Steady": 0.9,
                        "Deep": 1.2, "Maintenance": 1.0, "Volatile": 1.3}
        phase_mult = phase_weight.get(relationship_phase, 0.8)
        
        # Combined context factor (stranger conflict ≈ 0.25x, deep betrayal ≈ 1.4x)
        ctx = closeness * phase_mult
        
        # Neurochemical response profiles — each coefficient gets jitter
        # Format: (neurotransmitter, base_delta, context_sensitive)
        # context_sensitive=True means the delta scales with trust/phase
        PROFILES = {
            "conflict": [
                ("cort", +0.5, True),   # stress spike — worse from trusted people
                ("oxy",  -0.4, True),   # bonding breaks — more if bond was strong
                ("da",   -0.3, False),  # reward drops regardless
                ("ser",  -0.2, True),   # mood crash — scaled by closeness
                ("ne",   +0.4, False),  # alertness spike regardless
            ],
            "reconciliation": [
                ("oxy",  +0.5, True),   # bonding surge — stronger with history
                ("ser",  +0.4, True),   # mood lift — more relief if more was at stake
                ("cort", -0.4, True),   # stress relief — bigger if more stressed
                ("da",   +0.2, False),  # slight reward
            ],
            "novel_interaction": [
                ("da",   +0.4, False),  # novelty reward
                ("ne",   +0.3, False),  # alertness
            ],
            "rejection": [
                ("ser",  -0.4, True),   # mood crash — worse from someone you value
                ("oxy",  -0.3, True),   # bonding breaks
                ("cort", +0.3, True),   # stress
            ],
            "affection": [
                ("oxy",  +0.3, True),   # bonding — stronger in established relationships
                ("da",   +0.2, False),  # reward
                ("ser",  +0.2, False),  # mood up
            ],
            "vulnerability": [
                ("oxy",  +0.4, True),   # deep bonding — stronger with trust
                ("cort", -0.2, True),   # feels safe — more relief with trust
            ],
            "achievement": [
                ("da",   +0.5, False),  # reward spike
                ("ser",  +0.3, False),  # confidence
            ],
            "boredom": [
                ("da",   -0.3, False),  # low reward
                ("ne",   -0.2, False),  # low alertness
            ],
            "stress": [
                ("cort", +0.4, False),  # stress spike
                ("ne",   +0.3, False),  # hypervigilance
                ("ser",  -0.2, False),  # mood dip
            ],
            "excitement": [
                ("da",   +0.5, False),  # reward spike
                ("ne",   +0.4, False),  # energy
                ("ser",  +0.2, False),  # mood up
            ],
        }
        
        profile = PROFILES.get(event_type)
        if profile:
            for neuro_key, base_delta, context_sensitive in profile:
                # Apply context scaling for interpersonal events
                effective_delta = self._jitter(base_delta) * intensity
                if context_sensitive:
                    effective_delta *= ctx
                
                current = self.neurochem.get(neuro_key, 0.5)
                self.neurochem[neuro_key] = current + effective_delta
        
        # Clamp all values to [0, 1]
        for neuro in self.neurochem:
            self.neurochem[neuro] = max(0.0, min(1.0, self.neurochem[neuro]))
    
    def get_neurochemical_influence_on_mood(self) -> Dict[str, float]:
        """
        Calculate how neurochemicals influence mood dimensions.
        
        This is the key connection: neurochemicals → mood → behavior
        Not just mood vectors in isolation - they're driven by underlying biology.
        """
        da = self.neurochem.get("da", 0.5)
        cort = self.neurochem.get("cort", 0.3)
        oxy = self.neurochem.get("oxy", 0.5)
        ser = self.neurochem.get("ser", 0.5)
        ne = self.neurochem.get("ne", 0.5)
        
        # Neurochemical influence on mood (realistic mappings)
        influences = {
            "happiness": 0.4 * ser + 0.3 * da + 0.2 * oxy - 0.1 * cort,  # Serotonin + dopamine + oxytocin - cortisol
            "stress": 0.6 * cort + 0.3 * ne - 0.1 * ser,  # Cortisol + norepinephrine - serotonin
            "affection": 0.5 * oxy + 0.3 * da + 0.2 * ser,  # Oxytocin + dopamine + serotonin
            "energy": 0.4 * ne + 0.3 * da + 0.2 * ser - 0.1 * cort,  # Norepinephrine + dopamine - cortisol
            "anxiety": 0.5 * cort + 0.3 * ne - 0.2 * ser,  # Cortisol + norepinephrine - serotonin
            "contentment": 0.5 * ser + 0.3 * oxy - 0.2 * cort,  # Serotonin + oxytocin - cortisol
            "excitement": 0.5 * da + 0.3 * ne,  # Dopamine + norepinephrine
            "sadness": 0.4 * (1 - ser) + 0.3 * (1 - da) + 0.2 * cort,  # Low serotonin + low dopamine + cortisol
            "boredom": 0.6 * (1 - da) + 0.2 * (1 - ne),  # Low dopamine + low norepinephrine
            "playfulness": 0.4 * da + 0.3 * oxy + 0.2 * ser - 0.1 * cort,  # Dopamine + oxytocin - cortisol
        }
        
        # Clamp to [0, 1]
        for key in influences:
            influences[key] = max(0.0, min(1.0, influences[key]))
        
        return influences
    
    def get_neurochem_vector(self) -> Dict[str, float]:
        """Get current neurochemical vector."""
        return self.neurochem.copy()
    
    # ========== State Updates ==========
    
    def update_state(self, state: Dict[str, Any]):
        """Update state with current psyche values."""
        # Ensure new values are in psyche dict
        self.psyche["stance"] = self.stance
        self.psyche["respect"] = self.respect
        self.psyche["engagement"] = self.engagement
        self.psyche["entitlement_debt"] = self.entitlement_debt
        self.psyche["anger"] = self.anger
        self.psyche["disgust"] = self.disgust
        self.psyche["posture"] = self.posture
        
        state["current_psyche"] = self.psyche
        state["mood"] = self.mood
        state["neurochem_vector"] = self.neurochem
    
    def get_psyche_summary(self) -> Dict[str, Any]:
        """Get summary of current psyche state."""
        return {
            "trust": self.psyche.get("trust", 0.7),
            "hurt": self.psyche.get("hurt", 0.0),
            "forgiveness_state": self.psyche.get("forgiveness_state", "FORGIVEN"),
            "forgiveness_progress": self.psyche.get("forgiveness_progress", 1.0),
            "mood": self.mood.copy(),
            "neurochem": self.neurochem.copy(),
            # New 6-layer state
            "stance": self.stance,
            "respect": self.respect,
            "engagement": self.engagement,
            "entitlement_debt": self.entitlement_debt,
            "anger": self.anger,
            "disgust": self.disgust,
            "posture": self.posture
        }
    
    # ========== Stance, Respect, Engagement (NEW) ==========
    
    def update_stance(self, new_stance: str):
        """Update interpersonal stance. Called by reflection."""
        valid_stances = ["open", "wary", "guarded", "irritated", "bored", 
                        "intrigued", "defensive", "affectionate", "dismissive",
                        "curious", "amused", "withdrawn", "cold", "disgusted", "angry"]
        if new_stance.lower() in valid_stances:
            self.stance = new_stance.lower()
            self.psyche["stance"] = self.stance
    
    def update_respect(self, delta: float):
        """
        Update respect level with ASYMMETRY.
        EASY TO LOSE: Negative deltas are amplified 2x.
        HARD TO GAIN: Positive deltas are dampened 0.5x.
        This simulates how real respect works - you can lose someone's respect quickly,
        but earning it back takes time and consistency.
        """
        if delta < 0:
            # Losing respect is FAST - amplify negative changes
            actual_delta = delta * 2.0
        else:
            # Gaining respect is SLOW - dampen positive changes
            actual_delta = delta * 0.5
        
        self.respect = max(0.0, min(1.0, self.respect + actual_delta))
        self.psyche["respect"] = self.respect
    
    def update_engagement(self, delta: float):
        """Update engagement level. Positive = more motivated, negative = less."""
        self.engagement = max(0.0, min(1.0, self.engagement + delta))
        self.psyche["engagement"] = self.engagement
    
    def update_entitlement_debt(self, delta: float):
        """
        Update entitlement debt (patience depletion).
        Increases when user assumes access, rushes intimacy, demands attention.
        """
        self.entitlement_debt = max(0.0, min(1.0, self.entitlement_debt + delta))
        self.psyche["entitlement_debt"] = self.entitlement_debt
    
    def decay_entitlement_debt(self, delta_hours: float):
        """Decay entitlement debt over time (patience recovery)."""
        TAU_ENTITLEMENT = 24.0  # 24-hour half-life
        self.entitlement_debt = self.entitlement_debt * math.exp(-delta_hours / TAU_ENTITLEMENT)
        self.psyche["entitlement_debt"] = self.entitlement_debt
    
    def update_anger(self, delta: float):
        """
        Update anger/frustration level.
        Increases with: repeated disrespect, boundary violations, persistence after pushback.
        When high: blunt, short, may snap, no sugarcoating.
        """
        self.anger = max(0.0, min(1.0, self.anger + delta))
        self.psyche["anger"] = self.anger
    
    def decay_anger(self, delta_hours: float):
        """Decay anger over time."""
        TAU_ANGER = 4.0  # 4-hour half-life (anger fades faster than entitlement)
        self.anger = self.anger * math.exp(-delta_hours / TAU_ANGER)
        self.psyche["anger"] = self.anger
    
    def update_disgust(self, delta: float):
        """
        Update disgust level (complete loss of respect/attraction).
        Increases with: creepy behavior, manipulation, persistent entitlement.
        When high: cold, withdrawn, may refuse to engage.
        """
        self.disgust = max(0.0, min(1.0, self.disgust + delta))
        self.psyche["disgust"] = self.disgust
    
    def decay_disgust(self, delta_hours: float):
        """Decay disgust over time (slower than anger - disgust lingers)."""
        TAU_DISGUST = 48.0  # 48-hour half-life (disgust lingers)
        self.disgust = self.disgust * math.exp(-delta_hours / TAU_DISGUST)
        self.psyche["disgust"] = self.disgust
    
    def update_posture(self, posture_text: str):
        """Update posture overlay (from reflection). This is behavioral tendency text."""
        self.posture = posture_text
        self.psyche["posture"] = self.posture
    
    def apply_reflection_updates(self, updates: Dict[str, Any]):
        """
        Apply updates from Light or Deep reflection.
        All deltas are clamped to their documented ranges to prevent wild LLM swings.
        
        Expected keys:
        - stance: str
        - respect_delta: float (±0.15)
        - engagement_delta: float (±0.15)
        - entitlement_delta: float (-0.1 to +0.2)
        - anger_delta: float (-0.1 to +0.2)
        - disgust_delta: float (-0.1 to +0.2)
        - trust_delta: float (±0.3, let the LLM decide magnitude based on what happened)
        - hurt_delta: float (±0.3, real interactions can cause big shifts)
        - posture: str (behavioral tendencies)
        """
        if "stance" in updates and updates["stance"]:
            self.update_stance(updates["stance"])
        
        if "respect_delta" in updates:
            delta = max(-0.15, min(0.15, float(updates["respect_delta"] or 0)))
            self.update_respect(delta)
        
        if "engagement_delta" in updates:
            delta = max(-0.15, min(0.15, float(updates["engagement_delta"] or 0)))
            self.update_engagement(delta)
        
        if "entitlement_delta" in updates:
            delta = max(-0.1, min(0.2, float(updates["entitlement_delta"] or 0)))
            self.update_entitlement_debt(delta)
        
        if "anger_delta" in updates:
            delta = max(-0.1, min(0.2, float(updates["anger_delta"] or 0)))
            self.update_anger(delta)
        
        if "disgust_delta" in updates:
            delta = max(-0.1, min(0.2, float(updates["disgust_delta"] or 0)))
            self.update_disgust(delta)
        
        if "posture" in updates and updates["posture"]:
            self.update_posture(updates["posture"])
        
        # Trust: magnitude decided by LLM reasoning, not hardcoded dampeners
        if "trust_delta" in updates:
            current_trust = self.psyche.get("trust", 0.5)
            delta = max(-0.3, min(0.3, float(updates["trust_delta"] or 0)))
            self.psyche["trust"] = max(0.0, min(1.0, current_trust + delta))
            print(f"[TRUST] Delta: {delta:+.2f} → New: {self.psyche['trust']:.2f}")
        
        # Hurt: magnitude decided by LLM reasoning
        if "hurt_delta" in updates:
            current_hurt = self.psyche.get("hurt", 0.0)
            delta = max(-0.3, min(0.3, float(updates["hurt_delta"] or 0)))
            self.psyche["hurt"] = max(0.0, min(1.0, current_hurt + delta))
            print(f"[HURT] Delta: {delta:+.2f} → New: {self.psyche['hurt']:.2f}")
    
    def get_named_mood_state(self) -> Dict[str, Any]:
        """
        Derive a named mood state from the 14-dim mood vector + neurochemicals.
        Returns: {"state": "calm", "description": "...", "intensity": 0.7}
        
        No fabrication — purely derived from existing data.
        """
        h = self.mood.get("happiness", 0.5)
        s = self.mood.get("stress", 0.3)
        a = self.mood.get("affection", 0.5)
        ang = self.mood.get("anger", 0.1)
        cur = self.mood.get("curiosity", 0.5)
        sad = self.mood.get("sadness", 0.2)
        energy = self.mood.get("energy", 0.5)
        boredom = self.mood.get("boredom", 0.3)
        playfulness = self.mood.get("playfulness", 0.4)
        excitement = self.mood.get("excitement", 0.3)
        
        da = self.neurochem.get("da", 0.5)
        cort = self.neurochem.get("cort", 0.3)
        oxy = self.neurochem.get("oxy", 0.5)
        ser = self.neurochem.get("ser", 0.5)
        
        # Score each named state by how well it fits the current readings
        states = {
            "calm": (
                0.3 * ser + 0.2 * (1 - s) + 0.2 * (1 - ang) + 0.15 * (1 - cort) + 0.15 * h,
                "Settled. Not much is pulling at her emotionally."
            ),
            "focused": (
                0.3 * energy + 0.25 * cur + 0.2 * (1 - boredom) + 0.15 * da + 0.1 * (1 - s),
                "Locked in. Engaged with what's happening, mentally sharp."
            ),
            "playful": (
                0.3 * playfulness + 0.25 * da + 0.2 * h + 0.15 * (1 - s) + 0.1 * excitement,
                "Light mood. Teasing, jokes, doesn't take things too seriously."
            ),
            "affectionate": (
                0.35 * a + 0.25 * oxy + 0.2 * h + 0.1 * ser + 0.1 * (1 - ang),
                "Warm. Genuinely caring about the person she's talking to."
            ),
            "melancholic": (
                0.3 * sad + 0.2 * (1 - h) + 0.2 * (1 - da) + 0.15 * cort + 0.15 * (1 - energy),
                "Quiet sadness. Not dramatic — just a heaviness underneath."
            ),
            "agitated": (
                0.3 * s + 0.25 * cort + 0.2 * ang + 0.15 * (1 - ser) + 0.1 * self.entitlement_debt,
                "On edge. Responses are sharper, patience is thin."
            ),
            "withdrawn": (
                0.3 * boredom + 0.25 * (1 - energy) + 0.2 * (1 - a) + 0.15 * (1 - da) + 0.1 * self.disgust,
                "Checked out. Low effort, minimal engagement, not emotionally present."
            ),
            "energized": (
                0.3 * excitement + 0.25 * da + 0.2 * energy + 0.15 * (1 - sad) + 0.1 * cur,
                "Buzzing. High energy, talkative, enthusiastic."
            ),
        }
        
        # Find the best-fitting state
        best_state = "calm"
        best_score = 0.0
        for state_name, (score, _) in states.items():
            if score > best_score:
                best_score = score
                best_state = state_name
        
        _, description = states[best_state]
        
        return {
            "state": best_state,
            "description": description,
            "intensity": round(min(1.0, best_score), 2)
        }

