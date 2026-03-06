"""
Semantic Memory Search — Vector embedding-based memory retrieval.
Uses sentence-transformers (all-MiniLM-L6-v2) for local embeddings.

This provides MEANING-based search on top of existing FTS5 keyword search.
"remember when I was stressed about exams" → matches "User was anxious about upcoming tests"

Zero API calls — embeddings run locally on CPU, ~5ms per embedding.
"""

import sqlite3
import json
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timezone

# Lazy-load model to avoid slow startup
_model = None
_model_loading = False

def _get_model():
    """Lazy-load the embedding model (80MB, fast on CPU)."""
    global _model, _model_loading
    if _model is not None:
        return _model
    if _model_loading:
        return None  # Prevent recursive loading
    
    _model_loading = True
    try:
        from sentence_transformers import SentenceTransformer
        print("[SEMANTIC] Loading embedding model (first time only)...")
        _model = SentenceTransformer('all-MiniLM-L6-v2')
        print("[SEMANTIC] Model loaded successfully")
        return _model
    except Exception as e:
        print(f"[SEMANTIC] Failed to load model: {e}")
        _model_loading = False
        return None


class SemanticMemoryIndex:
    """
    Vector embedding index for memory entries.
    Stores embeddings in SQLite, computes cosine similarity for retrieval.
    
    Designed as a non-breaking enhancement — if anything fails,
    the calling code falls back to FTS5 keyword search.
    """
    
    def __init__(self, db_path: str = "semantic_memory.db"):
        self.db_path = Path(db_path)
        self._init_db()
    
    def _init_db(self):
        """Create embedding storage table."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS memory_embeddings (
                        user_id TEXT NOT NULL,
                        memory_type TEXT NOT NULL,
                        memory_id TEXT NOT NULL,
                        content TEXT NOT NULL,
                        embedding BLOB NOT NULL,
                        emotional_weight TEXT DEFAULT 'normal',
                        flagged_for_recall INTEGER DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        PRIMARY KEY (user_id, memory_type, memory_id)
                    )
                """)
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_user_type 
                    ON memory_embeddings(user_id, memory_type)
                """)
                conn.commit()
        except Exception as e:
            print(f"[SEMANTIC] DB init error: {e}")
    
    def embed_text(self, text: str) -> Optional[np.ndarray]:
        """Generate embedding for a text string. Returns None if model unavailable."""
        model = _get_model()
        if model is None:
            return None
        try:
            # Truncate long texts to avoid slow encoding
            text = text[:500]
            embedding = model.encode(text, normalize_embeddings=True)
            return embedding
        except Exception as e:
            print(f"[SEMANTIC] Embedding error: {e}")
            return None
    
    def store_embedding(self, user_id: str, memory_type: str, memory_id: str, 
                        content: str, emotional_weight: str = "normal",
                        flagged_for_recall: bool = False) -> bool:
        """
        Generate and store embedding for a memory entry.
        Returns True if successful, False otherwise.
        Non-blocking — failures don't affect the calling code.
        """
        embedding = self.embed_text(content)
        if embedding is None:
            return False
        
        try:
            embedding_bytes = embedding.tobytes()
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO memory_embeddings 
                    (user_id, memory_type, memory_id, content, embedding, emotional_weight, flagged_for_recall)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (user_id, memory_type, memory_id, content[:500], 
                      embedding_bytes, emotional_weight, int(flagged_for_recall)))
                conn.commit()
            return True
        except Exception as e:
            print(f"[SEMANTIC] Store error: {e}")
            return False
    
    def search(self, user_id: str, query: str, memory_type: str = None, 
               limit: int = 8, min_similarity: float = 0.25) -> List[Dict[str, Any]]:
        """
        Semantic search — find memories by meaning, not keywords.
        
        Args:
            user_id: User to search for
            query: Natural language query
            memory_type: Optional filter (episodic, identity, stm_summary, etc.)
            limit: Max results
            min_similarity: Minimum cosine similarity threshold
            
        Returns:
            List of dicts with content, memory_type, similarity score, etc.
        """
        query_embedding = self.embed_text(query)
        if query_embedding is None:
            return []
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                if memory_type:
                    cursor = conn.execute("""
                        SELECT memory_type, memory_id, content, embedding, 
                               emotional_weight, flagged_for_recall
                        FROM memory_embeddings 
                        WHERE user_id = ? AND memory_type = ?
                    """, (user_id, memory_type))
                else:
                    cursor = conn.execute("""
                        SELECT memory_type, memory_id, content, embedding,
                               emotional_weight, flagged_for_recall
                        FROM memory_embeddings 
                        WHERE user_id = ?
                    """, (user_id,))
                
                results = []
                for row in cursor.fetchall():
                    mem_type, mem_id, content, emb_bytes, emo_weight, flagged = row
                    
                    # Reconstruct embedding from bytes
                    stored_embedding = np.frombuffer(emb_bytes, dtype=np.float32)
                    
                    # Cosine similarity (embeddings are already normalized)
                    similarity = float(np.dot(query_embedding, stored_embedding))
                    
                    if similarity >= min_similarity:
                        # Boost flagged-for-recall memories
                        boosted_score = similarity + (0.1 if flagged else 0)
                        
                        results.append({
                            "memory_type": mem_type,
                            "memory_id": mem_id,
                            "content": content,
                            "similarity": round(similarity, 3),
                            "boosted_score": round(boosted_score, 3),
                            "emotional_weight": emo_weight,
                            "flagged_for_recall": bool(flagged),
                            "source": "semantic"
                        })
                
                # Sort by boosted score (flagged memories rank higher)
                results.sort(key=lambda x: x["boosted_score"], reverse=True)
                return results[:limit]
                
        except Exception as e:
            print(f"[SEMANTIC] Search error: {e}")
            return []
    
    def reindex_user(self, user_id: str, memories: Dict[str, List[Dict]]):
        """
        Rebuild semantic index for a user from their memory hierarchy.
        Call on startup or after major memory changes.
        
        Args:
            memories: Dict with keys like 'episodic', 'identity', 'stm_summaries'
        """
        model = _get_model()
        if model is None:
            print("[SEMANTIC] Cannot reindex — model not available")
            return
        
        count = 0
        
        # Index episodic memories
        for mem in memories.get("episodic", []):
            content = mem.get("content", "")
            mem_id = mem.get("memory_id", str(hash(content)))
            event_type = mem.get("event_type", "event")
            
            # Determine emotional weight and recall flag
            emotional_weight = "normal"
            flagged = False
            salience = mem.get("salience", 0.5)
            relational_impact = mem.get("relational_impact", 0.5)
            
            if salience > 0.7 or relational_impact > 0.7:
                emotional_weight = "high"
                flagged = True
            elif salience > 0.5:
                emotional_weight = "medium"
            
            # Relationship milestones are always high weight
            if event_type == "relationship_milestone":
                emotional_weight = "high"
                flagged = True
            
            if content and len(content) > 3:
                if self.store_embedding(user_id, "episodic", mem_id, content,
                                       emotional_weight, flagged):
                    count += 1
        
        # Index identity memories
        for mem in memories.get("identity", []):
            fact = mem.get("fact", "")
            mem_id = mem.get("identity_id", str(hash(fact)))
            if fact and len(fact) > 3:
                if self.store_embedding(user_id, "identity", mem_id, fact):
                    count += 1
        
        # Index STM summaries
        for mem in memories.get("stm_summaries", []):
            content = mem.get("content", "")
            if content and content.startswith("[Summary of"):
                mem_id = str(hash(content))
                if self.store_embedding(user_id, "stm_summary", mem_id, content):
                    count += 1
        
        # Index learned facts
        for mem in memories.get("learned_facts", []):
            fact = mem.get("fact", "")
            mem_id = str(hash(fact))
            if fact and len(fact) > 3:
                if self.store_embedding(user_id, "learned_fact", mem_id, fact):
                    count += 1
        
        if count > 0:
            print(f"[SEMANTIC] Reindexed {count} memories for user {user_id[:8]}...")
    
    def get_stats(self, user_id: str) -> Dict[str, int]:
        """Get count of indexed memories by type."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT memory_type, COUNT(*) 
                    FROM memory_embeddings 
                    WHERE user_id = ?
                    GROUP BY memory_type
                """, (user_id,))
                return {row[0]: row[1] for row in cursor.fetchall()}
        except:
            return {}
    
    def remove_user(self, user_id: str):
        """Remove all embeddings for a user."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("DELETE FROM memory_embeddings WHERE user_id = ?", (user_id,))
                conn.commit()
        except Exception as e:
            print(f"[SEMANTIC] Remove error: {e}")


# Global instance
_semantic_index: Optional[SemanticMemoryIndex] = None

def get_semantic_search(db_path: str = "semantic_memory.db") -> SemanticMemoryIndex:
    """Get or create global semantic search index."""
    global _semantic_index
    if _semantic_index is None:
        _semantic_index = SemanticMemoryIndex(db_path)
    return _semantic_index
