"""
Persistent State Machine - Central Orchestrator
Maintains 28K JSON per user with atomic updates.
Never forgets context, never needs reminders.
"""

import json
import sqlite3
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from pathlib import Path
import threading

# State structure matches blueprint specification
STATE_SCHEMA = {
    "core_personality": {
        "constitutional_principles": ["authenticity", "radical_empathy", "earned_vulnerability", 
                                     "boundary_respect", "growth_orientation", "honest_limitation"],
        "big_five": {"openness": 0.5, "conscientiousness": 0.5, "extraversion": 0.5, 
                     "agreeableness": 0.5, "neuroticism": 0.5},
        "humor_style": "light_playful",
        "sensitivity": 0.5,
        "attachment_style": "secure"  # secure, anxious, avoidant
    },
    "current_psyche": {
        "trust": 0.3,  # Start low - trust must be earned over time
        "hurt": 0.0,
        "anger": 0.0,
        "forgiveness_state": "FORGIVEN",  # UNFORGIVEN, SOFTENING, TENTATIVE, FORGIVEN
        "forgiveness_progress": 1.0,
        "phase_confidence": 0.3,  # Low confidence in early phase
        "relationship_phase": "Discovery"  # Discovery, Building, Steady, Deep, Maintenance, Volatile
    },
    "mood": {
        "happiness": 0.4,  # Neutral, not overly happy
        "stress": 0.2,
        "anger": 0.0,
        "affection": 0.2,  # Low affection - must build over time
        "energy": 0.5,
        "boredom": 0.3,
        "anxiety": 0.3,  # Slight anxiety meeting someone new
        "excitement": 0.1,  # Low excitement initially
        "sadness": 0.1,
        "contentment": 0.3,  # Neutral contentment
        "frustration": 0.1,
        "curiosity": 0.5,  # Moderate curiosity about new person
        "playfulness": 0.2,  # Low playfulness initially
        "vulnerability": 0.1  # Very low vulnerability - must be earned
    },
    "habits_cpbm": {
        "long_message_preference": 0.5,
        "emoji_baseline": 0.5,
        "teasing_style": "light_playful",
        "humor_frequency": 0.5,
        "punctuation_style": "expressive",
        "formality_baseline": 0.3,
        "typo_intentionality": 0.2,
        "ellipsis_habit": 0.3,
        "double_text_habit": 0.2,
        "wpm_baseline": 45,
        "latency_preference": 0.5
    },
    "memory_hierarchy": {
        "stm": [],  # Short-term memory (circular buffer)
        "act_threads": [],  # Active conversational threads
        "episodic": [],  # Emotionally salient events
        "identity": [],  # Promoted facts about user
        "milestones": [],  # Relationship pivots (never decay)
        "promises": [],  # Tracked promises
        "morals": []  # Injury flags
    },
    "pattern_candidates": {},  # Routine pattern candidates (before promotion to identity)
    "neurochem_vector": {
        "da": 0.5,  # Dopamine
        "cort": 0.3,  # Cortisol
        "oxy": 0.5,  # Oxytocin
        "ser": 0.5,  # Serotonin
        "ne": 0.5  # Norepinephrine
    },
    "relationship_ledger": {
        "entries": [],  # Reciprocity entries
        "balance": 0.0  # -1 (AI overextended) to +1 (user overextended)
    },
    "theory_of_mind": {
        "user_emotional_state_dist": {},
        "likelihood_of_reply_5min": 0.5,
        "likelihood_of_reply_30min": 0.7,
        "likely_availability": "unknown",
        "openness_to_initiative": 0.5,
        "likelihood_of_repair_after_conflict": 0.6,
        "vulnerability_receptiveness": 0.5,
        "humor_receptiveness": 0.6,
        "expected_message_length": 50,
        "predicted_circadian_state": "afternoon",
        "fatigue_level": 0.3,
        "stress_level": 0.3,
        "emotional_stability": 0.7
    },
    "temporal_context": {
        "last_message_time": None,
        "last_ai_message_time": None,  # Track AI message time for engagement calculation
        "last_conflict_time": None,
        "last_apology_time": None,
        "last_routine_event_time": None,
        "last_promise_time": None,
        "relationship_start_time": None
    },
    "cpbm_style_mode": "normal",  # excited, hurt, flirty, bored, jealous, playful, normal
    "embodiment": {
        "E_daily": 0.5,  # Energy budget [0, 1]
        "capacity": 0.3,  # Interaction fatigue [0, 1]
        "sleep_debt": 0.0
    },
    "qmas_state": {
        "last_path": None,
        "dominant_agent": None
    },
    "metadata": {
        "created_at": None,
        "updated_at": None,
        "version": "1.0"
    }
}


class StateOrchestrator:
    """Central state machine that maintains persistent state per user."""
    
    def __init__(self, db_path: str = "state.db"):
        self.db_path = Path(db_path)
        self.lock = threading.RLock()
        self._init_db()
    
    def _init_db(self):
        """Initialize SQLite database with state table."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS user_state (
                    user_id TEXT PRIMARY KEY,
                    state_json TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_updated_at ON user_state(updated_at)
            """)
            conn.commit()
    
    def get_state(self, user_id: str) -> Dict[str, Any]:
        """Get current state for user. Returns default state if user doesn't exist."""
        with self.lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT state_json FROM user_state WHERE user_id = ?",
                    (user_id,)
                )
                row = cursor.fetchone()
                
                if row:
                    state = json.loads(row[0])
                else:
                    # Initialize new user with default state
                    state = self._create_default_state(user_id)
                    self._save_state(user_id, state, conn)
                
                return state
    
    def _create_default_state(self, user_id: str) -> Dict[str, Any]:
        """Create default state for new user."""
        state = json.loads(json.dumps(STATE_SCHEMA))  # Deep copy
        now = datetime.now(timezone.utc).isoformat()
        state["metadata"]["created_at"] = now
        state["metadata"]["updated_at"] = now
        state["temporal_context"]["relationship_start_time"] = now
        return state
    
    def update_state(self, user_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Atomically update state. Updates are merged deeply.
        
        Args:
            user_id: User identifier
            updates: Partial state updates (will be merged)
        
        Returns:
            Updated full state
        """
        with self.lock:
            with sqlite3.connect(self.db_path) as conn:
                # Get current state
                state = self.get_state(user_id)
                
                # Deep merge updates
                state = self._deep_merge(state, updates)
                
                # Update metadata
                state["metadata"]["updated_at"] = datetime.now(timezone.utc).isoformat()
                
                # Save
                self._save_state(user_id, state, conn)
                
                return state
    
    def _deep_merge(self, base: Dict, updates: Dict) -> Dict:
        """Deep merge updates into base dictionary."""
        result = base.copy()
        
        for key, value in updates.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def _save_state(self, user_id: str, state: Dict[str, Any], conn: sqlite3.Connection):
        """Save state to database."""
        state_json = json.dumps(state)
        conn.execute(
            "INSERT OR REPLACE INTO user_state (user_id, state_json, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP)",
            (user_id, state_json)
        )
        conn.commit()
    
    def delete_state(self, user_id: str) -> bool:
        """Delete user state (for GDPR compliance)."""
        with self.lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "DELETE FROM user_state WHERE user_id = ?",
                    (user_id,)
                )
                conn.commit()
                return cursor.rowcount > 0
    
    def list_user_ids(self) -> List[str]:
        """List all user IDs in the database."""
        with self.lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT user_id FROM user_state")
                return [row[0] for row in cursor.fetchall()]


# Global instance
_state_orchestrator: Optional[StateOrchestrator] = None


def get_state_orchestrator(db_path: str = "state.db") -> StateOrchestrator:
    """Get or create global state orchestrator instance."""
    global _state_orchestrator
    if _state_orchestrator is None:
        _state_orchestrator = StateOrchestrator(db_path)
    return _state_orchestrator

