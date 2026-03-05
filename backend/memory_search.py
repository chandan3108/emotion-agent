"""
FTS5 Memory Index — Full-text search over memory entries.
Uses SQLite FTS5 (built-in, zero dependencies) for fast fuzzy matching.

This sits alongside the existing state.db and provides search capabilities
without changing the existing memory storage format.
"""

import sqlite3
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone


class MemorySearchIndex:
    """FTS5-backed search index for memory entries."""
    
    def __init__(self, db_path: str = "memory_search.db"):
        self.db_path = Path(db_path)
        self._init_db()
    
    def _init_db(self):
        """Create FTS5 virtual table if it doesn't exist."""
        with sqlite3.connect(self.db_path) as conn:
            # FTS5 table for full-text search
            conn.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS memory_fts USING fts5(
                    user_id,
                    memory_type,
                    memory_id,
                    content,
                    metadata,
                    tokenize='porter unicode61'
                )
            """)
            # Regular table to track what's indexed (for dedup)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS indexed_entries (
                    user_id TEXT,
                    memory_type TEXT,
                    memory_id TEXT,
                    indexed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (user_id, memory_type, memory_id)
                )
            """)
            conn.commit()
    
    def index_memory(self, user_id: str, memory_type: str, memory_id: str, 
                     content: str, metadata: Dict = None):
        """Index a single memory entry. Skips if already indexed."""
        with sqlite3.connect(self.db_path) as conn:
            # Check if already indexed
            cursor = conn.execute(
                "SELECT 1 FROM indexed_entries WHERE user_id=? AND memory_type=? AND memory_id=?",
                (user_id, memory_type, memory_id)
            )
            if cursor.fetchone():
                return  # Already indexed
            
            meta_json = json.dumps(metadata or {})
            conn.execute(
                "INSERT INTO memory_fts (user_id, memory_type, memory_id, content, metadata) VALUES (?, ?, ?, ?, ?)",
                (user_id, memory_type, memory_id, content, meta_json)
            )
            conn.execute(
                "INSERT INTO indexed_entries (user_id, memory_type, memory_id) VALUES (?, ?, ?)",
                (user_id, memory_type, memory_id)
            )
            conn.commit()
    
    def search(self, user_id: str, query: str, memory_type: str = None, 
               limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search memories using FTS5 full-text search.
        
        Supports:
        - Fuzzy matching via Porter stemming (e.g., "running" matches "run")
        - Phrase search: "jujutsu kaisen"
        - Boolean: anime OR manga
        - Prefix: anim* matches anime, animation, etc.
        """
        if not query or not query.strip():
            return []
        
        # Clean query for FTS5 — escape special chars, add prefix matching
        clean_words = []
        for word in query.strip().split():
            # Remove special chars that break FTS5
            word = ''.join(c for c in word if c.isalnum() or c == '_')
            if word and len(word) >= 2:
                clean_words.append(f'"{word}"*')  # Prefix match each word
        
        if not clean_words:
            return []
        
        fts_query = ' OR '.join(clean_words)
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                if memory_type:
                    cursor = conn.execute("""
                        SELECT memory_type, memory_id, content, metadata, 
                               rank
                        FROM memory_fts 
                        WHERE memory_fts MATCH ? AND user_id = ? AND memory_type = ?
                        ORDER BY rank
                        LIMIT ?
                    """, (fts_query, user_id, memory_type, limit))
                else:
                    cursor = conn.execute("""
                        SELECT memory_type, memory_id, content, metadata,
                               rank
                        FROM memory_fts 
                        WHERE memory_fts MATCH ? AND user_id = ?
                        ORDER BY rank
                        LIMIT ?
                    """, (fts_query, user_id, limit))
                
                results = []
                for row in cursor.fetchall():
                    results.append({
                        "memory_type": row[0],
                        "memory_id": row[1],
                        "content": row[2],
                        "metadata": json.loads(row[3]) if row[3] else {},
                        "relevance_rank": row[4]
                    })
                return results
        except Exception as e:
            print(f"[FTS5] Search error: {e}")
            return []
    
    def reindex_user(self, user_id: str, memories: Dict[str, List[Dict]]):
        """
        Rebuild the FTS5 index for a user from their memory hierarchy.
        Call this on startup or after major memory changes.
        
        Args:
            user_id: User ID
            memories: Dict with keys like 'episodic', 'identity', 'learned_facts'
        """
        with sqlite3.connect(self.db_path) as conn:
            # Clear existing entries for this user
            conn.execute("DELETE FROM memory_fts WHERE user_id = ?", (user_id,))
            conn.execute("DELETE FROM indexed_entries WHERE user_id = ?", (user_id,))
            
            count = 0
            
            # Index episodic memories
            for mem in memories.get("episodic", []):
                mem_id = mem.get("memory_id", f"ep_{count}")
                content = mem.get("content", "")
                if content:
                    conn.execute(
                        "INSERT INTO memory_fts (user_id, memory_type, memory_id, content, metadata) VALUES (?, ?, ?, ?, ?)",
                        (user_id, "episodic", mem_id, content, json.dumps({
                            "event_type": mem.get("event_type", ""),
                            "salience": mem.get("salience", 0.5),
                            "emotional_valence": mem.get("emotional_valence", 0.0)
                        }))
                    )
                    conn.execute(
                        "INSERT OR IGNORE INTO indexed_entries (user_id, memory_type, memory_id) VALUES (?, ?, ?)",
                        (user_id, "episodic", mem_id)
                    )
                    count += 1
            
            # Index identity memories
            for mem in memories.get("identity", []):
                mem_id = mem.get("identity_id", f"id_{count}")
                fact = mem.get("fact", "")
                if fact and not fact.startswith("[knowledge]"):
                    conn.execute(
                        "INSERT INTO memory_fts (user_id, memory_type, memory_id, content, metadata) VALUES (?, ?, ?, ?, ?)",
                        (user_id, "identity", mem_id, fact, json.dumps({
                            "confidence": mem.get("confidence", 0.75)
                        }))
                    )
                    conn.execute(
                        "INSERT OR IGNORE INTO indexed_entries (user_id, memory_type, memory_id) VALUES (?, ?, ?)",
                        (user_id, "identity", mem_id)
                    )
                    count += 1
            
            # Index learned facts
            for i, mem in enumerate(memories.get("learned_facts", [])):
                mem_id = f"lf_{i}"
                fact = mem.get("fact", "")
                if fact:
                    conn.execute(
                        "INSERT INTO memory_fts (user_id, memory_type, memory_id, content, metadata) VALUES (?, ?, ?, ?, ?)",
                        (user_id, "learned_facts", mem_id, fact, json.dumps({
                            "source": mem.get("source", ""),
                            "query": mem.get("query", "")
                        }))
                    )
                    conn.execute(
                        "INSERT OR IGNORE INTO indexed_entries (user_id, memory_type, memory_id) VALUES (?, ?, ?)",
                        (user_id, "learned_facts", mem_id)
                    )
                    count += 1
            
            # Index STM summaries (these are valuable compressed context)
            for i, mem in enumerate(memories.get("stm", [])):
                content = mem.get("content", "")
                if content and content.startswith("[Summary of"):
                    conn.execute(
                        "INSERT INTO memory_fts (user_id, memory_type, memory_id, content, metadata) VALUES (?, ?, ?, ?, ?)",
                        (user_id, "stm_summary", f"stm_{i}", content, "{}")
                    )
                    count += 1
            
            conn.commit()
            print(f"[FTS5] Reindexed {count} memories for user {user_id}")
    
    def remove_user(self, user_id: str):
        """Remove all indexed memories for a user."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM memory_fts WHERE user_id = ?", (user_id,))
            conn.execute("DELETE FROM indexed_entries WHERE user_id = ?", (user_id,))
            conn.commit()


# Global instance
_memory_search: Optional[MemorySearchIndex] = None


def get_memory_search(db_path: str = "memory_search.db") -> MemorySearchIndex:
    """Get or create global memory search index."""
    global _memory_search
    if _memory_search is None:
        _memory_search = MemorySearchIndex(db_path)
    return _memory_search
