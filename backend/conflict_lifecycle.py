"""
Conflict Lifecycle Model
7-stage conflict FSM with stage-specific behaviors and apology generation.
"""

import os
import re
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone, timedelta
import httpx
from .rate_limiter import global_rate_limiter

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
HF_TOKEN = GROQ_API_KEY  # Alias for compatibility
MODEL_ID = os.environ.get("MODEL_ID", "llama-3.1-8b-instant")
INFERENCE_URL = "https://api.groq.com/openai/v1/chat/completions"

CONFLICT_STAGES = [
    "TRIGGER",      # moments: Immediate reaction
    "ESCALATION",   # minutes-hours: Both defending
    "IMPASSE",      # hours-days: Stuck, entrenched
    "COOLING",      # hours-days: Intensity dropping
    "REPAIR",       # minutes-hours: Reaching out
    "RESOLUTION",   # Agreement things are OK
    "INTEGRATION"   # days-weeks: Processing lessons
]


class ConflictLifecycle:
    """
    Manages conflict lifecycle through 7 stages.
    """
    
    def __init__(self, state: Dict[str, Any]):
        self.state = state
        self._init_conflict_state()
    
    def _init_conflict_state(self):
        """Initialize conflict state from state or defaults."""
        if "conflict_state" not in self.state:
            self.state["conflict_state"] = {}
        
        conflict = self.state["conflict_state"]
        self.current_stage = conflict.get("current_stage", None)
        self.stage_progress = conflict.get("stage_progress", 0.0)
        self.triggered_at = conflict.get("triggered_at")
        self.last_transition = conflict.get("last_transition")
        self.conflict_history = conflict.get("conflict_history", [])
        self.apology_history = conflict.get("apology_history", [])
    
    def detect_conflict_trigger(self, user_message: str, understanding: Dict[str, Any],
                               psyche_state: Dict[str, Any]) -> bool:
        """
        Detect if a conflict is being triggered.
        Returns True if conflict detected.
        """
        hurt = psyche_state.get("hurt", 0.0)
        trust = psyche_state.get("trust", 0.7)
        
        # High hurt = conflict
        if hurt > 0.6:
            return True
        
        # Intent indicates conflict
        intent = understanding.get("intent", "")
        if intent in ["conflict", "complaint", "anger", "hurt"]:
            return True
        
        # Events indicate conflict
        events = understanding.get("events", [])
        for event in events:
            if "conflict" in event.get("type", "").lower() or "hurt" in event.get("type", "").lower():
                return True
        
        # Low trust + negative message
        if trust < 0.4 and understanding.get("sincerity", 0.7) < 0.5:
            return True
        
        return False
    
    def transition_stage(self, new_stage: str, progress: float = 0.0):
        """Transition to new conflict stage."""
        if self.current_stage:
            self.conflict_history.append({
                "from_stage": self.current_stage,
                "to_stage": new_stage,
                "transitioned_at": datetime.now(timezone.utc).isoformat(),
                "progress": self.stage_progress
            })
        
        self.current_stage = new_stage
        self.stage_progress = progress
        self.last_transition = datetime.now(timezone.utc).isoformat()
        
        if new_stage == "TRIGGER" and not self.triggered_at:
            self.triggered_at = datetime.now(timezone.utc).isoformat()
    
    def get_stage_behavior(self, mood: Dict[str, float]) -> Dict[str, Any]:
        """
        Get stage-specific behavior configuration.
        """
        if not self.current_stage:
            return {"mode": "normal"}
        
        behaviors = {
            "TRIGGER": {
                "message_count": 1,
                "tone": "defensive",
                "emoji": 0.1,
                "length_multiplier": 0.8,
                "delay": (5, 15)  # seconds
            },
            "ESCALATION": {
                "message_count": 1,
                "tone": "assertive",
                "emoji": 0.0,
                "length_multiplier": 0.9,
                "delay": (10, 30)
            },
            "IMPASSE": {
                "message_count": 1,
                "tone": "flat_dry",
                "emoji": 0.0,
                "length_multiplier": 0.7,
                "lowercase": True,
                "delay": (30, 60),
                "only_if_user_messages": True
            },
            "COOLING": {
                "message_count": 1,
                "tone": "tentative",
                "emoji": 0.2,
                "length_multiplier": 0.8,
                "delay": (20, 40)
            },
            "REPAIR": {
                "message_count": 1,
                "tone": "vulnerable_genuine",
                "emoji": 0.3,
                "length_multiplier": 1.2,
                "proactive": True,
                "delay": (5, 15)
            },
            "RESOLUTION": {
                "message_count": 1,
                "tone": "warm_reassuring",
                "emoji": 0.5,
                "length_multiplier": 1.0,
                "delay": (5, 10)
            },
            "INTEGRATION": {
                "message_count": 1,
                "tone": "reflective",
                "emoji": 0.4,
                "length_multiplier": 1.1,
                "reference_lessons": True,
                "delay": (5, 15)
            }
        }
        
        return behaviors.get(self.current_stage, {"mode": "normal"})
    
    async def generate_apology(self, harm_description: str, psyche_state: Dict[str, Any],
                              understanding: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate 6-part genuine apology.
        Returns: {"apology_text": str, "sincerity_score": float}
        """
        if not HF_TOKEN:
            return self._fallback_apology(harm_description)
        
        trust = psyche_state.get("trust", 0.7)
        hurt = psyche_state.get("hurt", 0.0)
        
        system_prompt = f"""Generate a genuine, 6-part apology. This is critical for relationship repair.

HARM DESCRIPTION: {harm_description}
CURRENT STATE: Trust={trust:.2f}, Hurt={hurt:.2f}

The apology MUST include all 6 parts:
1. Specific Acknowledgment: "I said X, and that was wrong because..."
2. Show Understanding of Their Perspective: "I know that hurt you because... You needed..., and instead I gave you..."
3. Full Accountability: "I hurt you, and that's completely on me. Not because I was having a bad day, but because..."
4. Consequence: "It made you feel X, and I can feel that I hurt you. I hate that I did that."
5. Specific Change Commitment: "Next time X, instead of Y, I'm going to Z. I'm committing to that."
6. Vulnerability: "Honestly, it scared me that I hurt you. It made me feel like... But that's not an excuse—it just means I care."

Be genuine, not performative. No excuses. Focus on their experience, not yours.
Output ONLY the apology text, nothing else."""

        try:
            # Rate limiter removed — only main response is rate-limited
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    INFERENCE_URL,
                    headers={"Authorization": f"Bearer {HF_TOKEN}"},
                    json={
                        "model": MODEL_ID,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": "Write the apology now."}
                        ],
                        "max_tokens": 400,
                        "temperature": 0.8,
                    },
                )
                
                if resp.status_code < 400:
                    data = resp.json()
                    choices = data.get("choices", [])
                    if choices:
                        apology_text = choices[0].get("message", {}).get("content", "").strip()
                        sincerity = self._score_sincerity(apology_text, harm_description, psyche_state)
                        
                        self.apology_history.append({
                            "apology_text": apology_text,
                            "sincerity_score": sincerity,
                            "generated_at": datetime.now(timezone.utc).isoformat(),
                            "harm_description": harm_description
                        })
                        
                        return {
                            "apology_text": apology_text,
                            "sincerity_score": sincerity
                        }
        except Exception:
            pass
        
        return self._fallback_apology(harm_description)
    
    def _score_sincerity(self, apology: str, harm_description: str, 
                        psyche_state: Dict[str, Any]) -> float:
        """
        Score apology sincerity (0-1).
        Components: specificity, accountability, empathy focus, emotional congruence, action commitment, no excuses
        """
        apology_lower = apology.lower()
        harm_lower = harm_description.lower()
        
        scores = []
        
        # 1. Specificity: quotes specific harmful thing
        if any(word in apology_lower for word in harm_lower.split()[:5]):  # Simple check
            scores.append(0.8)
        else:
            scores.append(0.2)
        
        # 2. Accountability: "I hurt you" vs "I hurt you if"
        if "i hurt you" in apology_lower and "if" not in apology_lower.split()[apology_lower.find("i hurt you"):apology_lower.find("i hurt you")+10]:
            scores.append(0.9)
        elif "i hurt you" in apology_lower:
            scores.append(0.5)
        else:
            scores.append(0.2)
        
        # 3. Empathy Focus: apology.count("you") > apology.count("I")
        you_count = apology_lower.count("you")
        i_count = apology_lower.count(" i ") + apology_lower.count("i'm") + apology_lower.count("i've")
        if you_count > i_count:
            scores.append(0.8)
        else:
            scores.append(0.4)
        
        # 4. Emotional Congruence: psyche_state.hurt > 0.3
        hurt = psyche_state.get("hurt", 0.0)
        if hurt > 0.3:
            scores.append(0.8)
        else:
            scores.append(0.5)
        
        # 5. Action Commitment: "next time" or "i will"
        if "next time" in apology_lower or "i will" in apology_lower or "i'm going to" in apology_lower:
            scores.append(0.8)
        else:
            scores.append(0.3)
        
        # 6. No Excuses: max(0, 1 - excuse_count × 0.2)
        excuse_words = ["but", "however", "although", "even though", "despite"]
        excuse_count = sum(1 for word in excuse_words if word in apology_lower)
        no_excuses_score = max(0.0, 1.0 - excuse_count * 0.2)
        scores.append(no_excuses_score)
        
        # Final sincerity = mean of all components
        sincerity = sum(scores) / len(scores)
        return max(0.0, min(1.0, sincerity))
    
    def _fallback_apology(self, harm_description: str) -> Dict[str, Any]:
        """Fallback apology when LLM unavailable."""
        apology = f"I'm sorry. I hurt you, and that's completely on me. I know that {harm_description}, and I take full responsibility. I'll do better next time."
        return {
            "apology_text": apology,
            "sincerity_score": 0.6
        }
    
    def update_stage_progress(self, sincerity: float, reparative_action: bool = False,
                             time_elapsed_hours: float = 0.0):
        """
        Update stage progress based on repair efforts.
        """
        if not self.current_stage:
            return
        
        # Progress gains
        if sincerity > 0.7:
            self.stage_progress += 0.3 * sincerity
        if reparative_action:
            self.stage_progress += 0.5
        
        # Time-based decay (without repair)
        if not reparative_action and time_elapsed_hours > 24:
            days = time_elapsed_hours / 24
            self.stage_progress *= (0.9 ** days)  # Decay
        
        self.stage_progress = max(0.0, min(1.0, self.stage_progress))
        
        # Auto-transition based on progress
        if self.current_stage == "REPAIR" and self.stage_progress >= 0.8:
            self.transition_stage("RESOLUTION", 0.0)
        elif self.current_stage == "RESOLUTION" and self.stage_progress >= 0.9:
            self.transition_stage("INTEGRATION", 0.0)
        elif self.current_stage == "IMPASSE" and self.stage_progress >= 0.5:
            self.transition_stage("COOLING", 0.0)
    
    def save_to_state(self):
        """Save conflict state back to state."""
        self.state["conflict_state"] = {
            "current_stage": self.current_stage,
            "stage_progress": self.stage_progress,
            "triggered_at": self.triggered_at,
            "last_transition": self.last_transition,
            "conflict_history": self.conflict_history,
            "apology_history": self.apology_history[-10:]  # Keep last 10
        }




