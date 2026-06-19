import sys
import os
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent))

from backend.cognitive_core import CognitiveCore
from backend.state import get_state_orchestrator

def main():
    user_id = "test_perf_user"
    
    # 1. Clean previous state if any
    orch = get_state_orchestrator()
    orch.delete_state(user_id)
    
    # 2. Get state and add some fake memories
    state = orch.get_state(user_id)
    
    # Add fake episodic memories with all required fields
    state["memory_hierarchy"]["episodic"] = [
        {
            "memory_id": "ep_1",
            "event_type": "event",
            "content": "We had a great breakfast together yesterday morning.",
            "emotional_valence": 0.8,
            "relational_impact": 0.8,
            "timestamp": "2026-06-03T09:00:00Z",
            "half_life_hours": 48.0,
            "evidence_event_ids": [],
            "salience": 0.8
        },
        {
            "memory_id": "ep_2",
            "event_type": "event",
            "content": "User was worried about their integral calculus exam.",
            "emotional_valence": -0.5,
            "relational_impact": 0.7,
            "timestamp": "2026-06-03T09:10:00Z",
            "half_life_hours": 48.0,
            "evidence_event_ids": [],
            "salience": 0.7
        }
    ]
    # Add fake STM memory with valid ISO timestamp
    state["memory_hierarchy"]["stm"] = [
        {"content": "Just a normal chat message that should not be indexed", "timestamp": "2026-06-03T09:00:00Z"},
        {"content": "[Summary of previous conversation regarding school]", "timestamp": "2026-06-03T09:05:00Z"}
    ]
    
    # Save state back
    orch.update_state(user_id, state)
    
    # Also clean the SQLite databases to start fresh
    import sqlite3
    from backend.semantic_search import get_semantic_search
    from backend.memory_search import get_memory_search
    
    sem = get_semantic_search()
    fts = get_memory_search()
    
    # Clear index for this user
    with sqlite3.connect(sem.db_path) as conn:
        conn.execute("DELETE FROM memory_embeddings WHERE user_id = ?", (user_id,))
        conn.commit()
    with sqlite3.connect(fts.db_path) as conn:
        conn.execute("DELETE FROM memory_fts WHERE user_id = ?", (user_id,))
        conn.execute("DELETE FROM indexed_entries WHERE user_id = ?", (user_id,))
        conn.commit()
        
    print("\n--- FIRST INITIALIZATION (SHOULD INDEX BOTH) ---")
    core1 = CognitiveCore(user_id=user_id)
    
    print("\n--- SECOND INITIALIZATION (SHOULD SKIP BOTH) ---")
    core2 = CognitiveCore(user_id=user_id)
    
    print("\nVerification successful!")

if __name__ == "__main__":
    main()
