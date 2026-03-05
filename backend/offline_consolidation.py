"""
Offline Consolidation Worker (Stage 16)
Nightly: recomputes pattern confidence, promotes/demotes identities, decays memories.
"""

from typing import Dict, Any, List
from datetime import datetime, timezone, timedelta
import asyncio
import math


class OfflineConsolidationWorker:
    """
    Runs nightly consolidation tasks:
    - Recompute pattern confidence
    - Promote/demote identities
    - Decay memories
    - Update habit strengths
    """
    
    def __init__(self, state_orchestrator):
        self.state_orchestrator = state_orchestrator
    
    async def run_consolidation(self, user_id: str):
        """
        Run nightly consolidation for a user.
        
        Args:
            user_id: User ID to consolidate
        """
        state = self.state_orchestrator.get_state(user_id)
        
        # 1. Recompute pattern confidence for all routine candidates
        from .pattern_detector import PatternDetector
        pattern_detector = PatternDetector(state)
        
        # Get all pattern candidates
        pattern_candidates = state.get("pattern_detector_state", {}).get("pattern_candidates", {})
        
        for pattern_id, pattern_data in pattern_candidates.items():
            if not pattern_data.get("promoted_to_identity", False):
                # Recalculate pattern confidence
                temporal_context = state.get("temporal_context", {})
                # This would call the pattern detector's confidence calculation
                # For now, we'll just update the last_updated timestamp
                pattern_data["last_updated"] = datetime.now(timezone.utc).isoformat()
        
        # 2. Promote identities where thresholds met
        from .memory import MemorySystem
        memory = MemorySystem(state)
        
        for pattern_id, pattern_data in pattern_candidates.items():
            if not pattern_data.get("promoted_to_identity", False):
                pc = pattern_data.get("last_pc", 0.0)
                occurrences = pattern_data.get("occurrences", [])
                
                # Check promotion criteria
                if pc >= 0.75 and len(occurrences) >= 8:
                    # Check distinct days
                    distinct_days = len(set(
                        datetime.fromisoformat(occ.replace("Z", "+00:00")).date()
                        for occ in occurrences
                    ))
                    
                    if distinct_days >= 14:
                        # Promote to identity
                        fact = f"User's routine: {pattern_data.get('content', '')}"
                        confidence = pc
                        evidence_count = len(occurrences)
                        
                        identity_id = memory.promote_to_identity(fact, confidence, evidence_count)
                        if identity_id:
                            pattern_data["promoted_to_identity"] = True
        
        # 3. Decay non-reinforced memories
        # Episodic memories decay based on forgetting curve
        episodic_memories = memory.get_episodic(min_salience=0.0)
        now = datetime.now(timezone.utc)
        
        for mem in episodic_memories:
            created_time = datetime.fromisoformat(mem.get("created_at", now.isoformat()).replace("Z", "+00:00"))
            days_old = (now - created_time).days
            
            # Exponential decay: salience decreases over time
            base_salience = mem.get("salience", 0.5)
            half_life = mem.get("half_life", 30)  # days
            
            decayed_salience = base_salience * math.exp(-days_old / half_life)
            mem["salience"] = max(0.0, decayed_salience)
            
            # Remove very low salience memories
            if mem["salience"] < 0.05:
                memory.remove_episodic(mem.get("id"))
        
        # 4. Update habit strengths (decay unused habits)
        habits_cpbm = state.get("habits_cpbm", {})
        habit_scores = habits_cpbm.get("habit_scores", {})
        
        for pattern_id, score in list(habit_scores.items()):
            # Decay habits that haven't been used recently
            # This would require tracking last_used timestamp
            # For now, just decay all habits slightly
            habit_scores[pattern_id] = max(0.0, score * 0.99)  # 1% decay per day
        
        habits_cpbm["habit_scores"] = habit_scores
        state["habits_cpbm"] = habits_cpbm
        
        # 5. Save updated state
        self.state_orchestrator.update_state(user_id, state)
    
    async def run_nightly_consolidation(self):
        """
        Run consolidation for all users (called nightly).
        """
        print(f"[CONSOLIDATION] Running nightly consolidation at {datetime.now(timezone.utc).isoformat()}")
        
        # Get all user IDs and consolidate each user
        try:
            user_ids = self.state_orchestrator.list_user_ids()
            print(f"[CONSOLIDATION] Found {len(user_ids)} users to consolidate")
            
            for user_id in user_ids:
                try:
                    await self.run_consolidation(user_id)
                except Exception as e:
                    print(f"[CONSOLIDATION] Error consolidating user {user_id}: {e}")
                    continue  # Continue with other users even if one fails
            
            print(f"[CONSOLIDATION] Nightly consolidation completed at {datetime.now(timezone.utc).isoformat()}")
        except Exception as e:
            print(f"[CONSOLIDATION] Error running nightly consolidation: {e}")

