"""
Memory System with Temporal Integration
Implements STM, ACT, Episodic, Identity memory tiers per blueprint.
"""

import json
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
from dataclasses import dataclass, asdict
import math
from .rate_limiter import global_rate_limiter


@dataclass
class STMEntry:
    """Short-Term Memory entry (30-minute half-life)."""
    content: str
    emotion_vector: Dict[str, float]
    timestamp: str
    perception_output: Dict[str, Any]
    topic: str = ""  # Current topic for this memory
    emotional_weight: float = 0.0  # Emotional significance (0-1)


@dataclass
class ACTThread:
    """Active Conversational Thread (2-6 hours, extensible)."""
    thread_id: str
    topic_embedding: List[float]  # Semantic embedding vector
    anchor_texts: List[str]
    creation_time: str
    salience: float  # 0-1, decays over time
    last_reinforced: str
    tau_thread: float = 3.0  # Decay constant in hours (default 3 hours)


@dataclass
class EpisodicMemory:
    """Episodic memory for emotionally salient events."""
    memory_id: str
    event_type: str  # fight, confession, apology, promise, achievement
    content: str
    emotional_valence: float
    relational_impact: float  # 0-1, affects retention
    timestamp: str
    salience: float
    half_life_hours: float  # Computed from relational_impact
    evidence_event_ids: List[str]  # Links to other memories
    topic: str = ""  # Topic of this episodic memory
    emotional_weight: float = 0.0  # Emotional significance (0-1)


@dataclass
class IdentityMemory:
    """Promoted facts about user (confidence ≥0.75)."""
    identity_id: str
    fact: str
    confidence: float  # 0-1
    promoted_at: str
    evidence_count: int
    contradictions: int
    last_accessed: str = ""  # For knowledge decay tracking


class MemorySystem:
    """Manages all memory tiers with temporal decay."""
    
    def __init__(self, state: Dict[str, Any], user_id: str = ""):
        self.state = state
        self.user_id = user_id
        self.memory = state.get("memory_hierarchy", {
            "stm": [],
            "act_threads": [],
            "episodic": [],
            "identity": [],
            "milestones": [],
            "promises": [],
            "morals": []
        })
    
    # ========== Short-Term Memory ==========
    
    def add_stm(self, content: str, emotion_vector: Dict[str, float], 
                perception_output: Dict[str, Any], topic: str = None):
        """Add entry to STM (circular buffer, max 20 entries)."""
        # Calculate emotional weight from emotion vector
        emotional_weight = max(emotion_vector.values()) if emotion_vector else 0.0
        
        entry = STMEntry(
            content=content,
            emotion_vector=emotion_vector,
            timestamp=datetime.now(timezone.utc).isoformat(),
            perception_output=perception_output,
            topic=topic or perception_output.get("topic", "general"),
            emotional_weight=emotional_weight
        )
        
        stm = self.memory.get("stm", [])
        stm.append(asdict(entry))
        
        # Keep only last 20 entries (circular buffer)
        if len(stm) > 20:
            stm = stm[-20:]
        
        self.memory["stm"] = stm
    
    def get_stm(self, decay: bool = True) -> List[Dict[str, Any]]:
        """Get STM entries, optionally applying decay."""
        stm = self.memory.get("stm", [])
        
        if not decay:
            return stm
        
        # Apply decay (30-minute half-life)
        now = datetime.now(timezone.utc)
        tau_stm = 0.5  # 30 minutes in hours
        
        decayed_stm = []
        for entry in stm:
            entry_time = datetime.fromisoformat(entry["timestamp"].replace("Z", "+00:00"))
            delta_hours = (now - entry_time).total_seconds() / 3600
            
            # Exponential decay
            if delta_hours < 8.0:  # Keep entries < 8 hours old (covers a full conversation day)
                decayed_stm.append(entry)
        
        self.memory["stm"] = decayed_stm
        return decayed_stm
    
    # ========== Active Conversational Threads ==========
    
    def find_or_create_act_thread(self, topic_embedding: List[float], 
                                  anchor_text: str, 
                                  similarity_threshold: float = 0.82) -> Tuple[str, bool]:
        """
        Find existing ACT thread or create new one.
        
        Returns:
            (thread_id, is_new)
        """
        threads = self.memory.get("act_threads", [])
        now = datetime.now(timezone.utc)
        
        # Decay and filter active threads
        active_threads = []
        for thread_dict in threads:
            thread = ACTThread(**thread_dict)
            thread_time = datetime.fromisoformat(thread.creation_time.replace("Z", "+00:00"))
            delta_hours = (now - thread_time).total_seconds() / 3600
            
            # Decay salience
            thread.salience = thread.salience * math.exp(-delta_hours / thread.tau_thread)
            
            # Keep if salience > 0.1 or recently reinforced
            if thread.salience > 0.1 or delta_hours < 6.0:
                active_threads.append(thread)
        
        # Find best matching thread
        best_match = None
        best_similarity = 0.0
        
        for thread in active_threads:
            # Cosine similarity (simplified - in production use proper embedding comparison)
            similarity = self._cosine_similarity(topic_embedding, thread.topic_embedding)
            
            if similarity > best_similarity:
                best_similarity = similarity
                best_match = thread
        
        # Create new thread if no good match
        if best_similarity < similarity_threshold or best_match is None:
            new_thread = ACTThread(
                thread_id=f"t{int(now.timestamp() * 1000)}",
                topic_embedding=topic_embedding,
                anchor_texts=[anchor_text],
                creation_time=now.isoformat(),
                salience=1.0,
                last_reinforced=now.isoformat()
            )
            active_threads.append(new_thread)
            self.memory["act_threads"] = [asdict(t) for t in active_threads]
            return new_thread.thread_id, True
        
        # Reinforce existing thread
        best_match.anchor_texts.append(anchor_text)
        best_match.salience = min(1.0, best_match.salience + 0.2)
        best_match.last_reinforced = now.isoformat()
        self.memory["act_threads"] = [asdict(t) for t in active_threads]
        return best_match.thread_id, False
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Compute cosine similarity between two vectors."""
        if len(vec1) != len(vec2) or len(vec1) == 0:
            return 0.0
        
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = math.sqrt(sum(a * a for a in vec1))
        norm2 = math.sqrt(sum(a * a for a in vec2))
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def get_act_threads(self) -> List[Dict[str, Any]]:
        """Get all ACT threads (as dicts for compatibility)."""
        threads = self.memory.get("act_threads", [])
        now = datetime.now(timezone.utc)
        
        # Decay and return active threads
        active_threads = []
        for thread_dict in threads:
            thread = ACTThread(**thread_dict)
            thread_time = datetime.fromisoformat(thread.creation_time.replace("Z", "+00:00"))
            delta_hours = (now - thread_time).total_seconds() / 3600
            
            # Decay salience
            thread.salience = thread.salience * math.exp(-delta_hours / thread.tau_thread)
            
            # Keep if salience > 0.1 or recently reinforced
            if thread.salience > 0.1 or delta_hours < 6.0:
                active_threads.append(asdict(thread))
        
        return active_threads
    
    # ========== Episodic Memory ==========
    
    def add_episodic(self, event_type: str, content: str, 
                     emotional_valence: float, relational_impact: float,
                     evidence_event_ids: List[str] = None) -> str:
        """Add episodic memory with forgetting curve."""
        memory_id = f"m{int(datetime.now(timezone.utc).timestamp() * 1000)}"
        
        # Compute half-life from relational impact
        base_half_life = 48.0  # hours
        half_life = base_half_life * (1 + relational_impact)
        
        entry = EpisodicMemory(
            memory_id=memory_id,
            event_type=event_type,
            content=content,
            emotional_valence=emotional_valence,
            relational_impact=relational_impact,
            timestamp=datetime.now(timezone.utc).isoformat(),
            salience=1.0,
            half_life_hours=half_life,
            evidence_event_ids=evidence_event_ids,
            topic="general",
            emotional_weight=abs(emotional_valence)  # Use valence as emotional weight
        )
        
        episodic = self.memory.get("episodic", [])
        episodic.append(asdict(entry))
        self.memory["episodic"] = episodic
        
        # Generate semantic embedding (non-blocking, fails silently)
        if self.user_id:
            try:
                from .semantic_search import get_semantic_search
                sem = get_semantic_search()
                emo_weight = "normal"
                flagged = False
                if relational_impact > 0.6 or abs(emotional_valence) > 0.6:
                    emo_weight = "high"
                    flagged = True
                elif relational_impact > 0.4:
                    emo_weight = "medium"
                if event_type == "relationship_milestone":
                    emo_weight = "high"
                    flagged = True
                sem.store_embedding(self.user_id, "episodic", memory_id, content,
                                   emo_weight, flagged)
            except Exception:
                pass  # Never break memory storage
        
        return memory_id
    
    def get_episodic(self, event_type: Optional[str] = None, 
                     min_salience: float = 0.1) -> List[Dict[str, Any]]:
        """Get episodic memories, applying forgetting curve."""
        episodic = self.memory.get("episodic", [])
        now = datetime.now(timezone.utc)
        
        result = []
        for entry_dict in episodic:
            entry = EpisodicMemory(**entry_dict)
            
            # Apply forgetting curve
            entry_time = datetime.fromisoformat(entry.timestamp.replace("Z", "+00:00"))
            delta_hours = (now - entry_time).total_seconds() / 3600
            entry.salience = entry.salience * math.exp(-delta_hours / entry.half_life_hours)
            
            # Filter by type and salience
            if (event_type is None or entry.event_type == event_type) and entry.salience >= min_salience:
                result.append(asdict(entry))
        
        return result
    
    # ========== Identity Memory ==========
    
    def promote_to_identity(self, fact: str, confidence: float, 
                           evidence_count: int) -> Optional[str]:
        """
        Promote fact to identity memory if confidence ≥ 0.75.
        
        Returns:
            identity_id if promoted, None otherwise
        """
        if confidence < 0.75:
            return None
        
        now = datetime.now(timezone.utc).isoformat()
        identity_id = f"i{int(datetime.now(timezone.utc).timestamp() * 1000)}"
        
        entry = IdentityMemory(
            identity_id=identity_id,
            fact=fact,
            confidence=confidence,
            promoted_at=now,
            evidence_count=evidence_count,
            contradictions=0,
            last_accessed=now
        )
        
        identity = self.memory.get("identity", [])
        identity.append(asdict(entry))
        self.memory["identity"] = identity
        
        # Generate semantic embedding (non-blocking)
        if self.user_id:
            try:
                from .semantic_search import get_semantic_search
                sem = get_semantic_search()
                sem.store_embedding(self.user_id, "identity", identity_id, fact)
            except Exception:
                pass
        
        return identity_id
    
    def get_identity(self, min_confidence: float = 0.75) -> List[Dict[str, Any]]:
        """Get identity memories above confidence threshold.
        Excludes [knowledge] prefixed facts (those are legacy)."""
        identity = self.memory.get("identity", [])
        now = datetime.now(timezone.utc).isoformat()
        result = []
        for entry in identity:
            if entry.get("confidence", 0) >= min_confidence:
                # Skip legacy [knowledge] facts — they belong in learned_facts
                if entry.get("fact", "").startswith("[knowledge]"):
                    continue
                result.append(entry)
        return result
    
    # ========== Learned Facts (World Knowledge) ==========
    
    def store_learned_fact(self, fact: str, source: str, query: str = "") -> bool:
        """Store a learned fact from web search. Separate from identity memory.
        Returns True if stored, False if duplicate."""
        learned = self.memory.get("learned_facts", [])
        
        # Check for duplicates (fuzzy match)
        for existing in learned:
            if fact.lower()[:50] in existing.get("fact", "").lower() or existing.get("fact", "").lower()[:50] in fact.lower():
                # Refresh the existing fact's timestamp
                existing["last_accessed"] = datetime.now(timezone.utc).isoformat()
                return False
        
        now = datetime.now(timezone.utc).isoformat()
        entry = {
            "fact": fact,
            "source": source,
            "query": query,
            "stored_at": now,
            "last_accessed": now,
            "access_count": 0
        }
        learned.append(entry)
        
        # Cap at 50 facts — remove oldest unused
        if len(learned) > 50:
            learned.sort(key=lambda f: f.get("last_accessed", ""))
            learned = learned[-50:]
        
        self.memory["learned_facts"] = learned
        return True
    
    def get_learned_facts(self, query: str = "", apply_decay: bool = True, user_id: str = "") -> List[Dict[str, Any]]:
        """Get learned facts, optionally filtered by relevance to query.
        Uses FTS5 full-text search when available, falls back to keyword matching.
        Applies 72-hour half-life decay — old unused facts get pruned."""
        learned = self.memory.get("learned_facts", [])
        
        if apply_decay:
            now = datetime.now(timezone.utc)
            active_facts = []
            for fact in learned:
                accessed = fact.get("last_accessed", fact.get("stored_at", ""))
                try:
                    fact_time = datetime.fromisoformat(accessed.replace("Z", "+00:00"))
                    hours_since = (now - fact_time).total_seconds() / 3600
                    # 72-hour half-life — prune facts not accessed in 2 weeks
                    if hours_since < 336:  # 14 days max
                        active_facts.append(fact)
                except:
                    active_facts.append(fact)
            self.memory["learned_facts"] = active_facts
            learned = active_facts
        
        # If query given, try FTS5 first, then fall back to keyword matching
        if query:
            # Try FTS5 search
            try:
                from .memory_search import get_memory_search
                search_index = get_memory_search()
                fts_results = search_index.search(user_id or "", query, memory_type="learned_facts", limit=5)
                if fts_results:
                    # Match FTS5 results back to actual fact entries
                    matched = []
                    for result in fts_results:
                        for fact in learned:
                            if fact.get("fact", "")[:50] == result["content"][:50]:
                                fact["last_accessed"] = datetime.now(timezone.utc).isoformat()
                                fact["access_count"] = fact.get("access_count", 0) + 1
                                matched.append(fact)
                                break
                    if matched:
                        return matched
            except Exception as e:
                pass  # Fall through to keyword matching
            
            # Keyword fallback
            query_words = set(query.lower().split()) - {"the", "a", "is", "in", "of", "and", "to", "for", "it", "do", "you", "know", "about", "what"}
            relevant = []
            for fact in learned:
                fact_text = fact.get("fact", "").lower()
                fact_query = fact.get("query", "").lower()
                overlap = sum(1 for w in query_words if w in fact_text or w in fact_query)
                if overlap >= 1:
                    fact["last_accessed"] = datetime.now(timezone.utc).isoformat()
                    fact["access_count"] = fact.get("access_count", 0) + 1
                    relevant.append(fact)
            return relevant
        
        return learned
    
    # ========== Enhanced Memory Methods ==========
    
    def get_relevant_memories(self, current_topic: str, recent_messages: List[Dict] = None, user_id: str = "") -> List[Dict[str, Any]]:
        """Return memories relevant to current conversation.
        Uses SEMANTIC search first (meaning-based), with FTS5 keyword fallback."""
        relevant_memories = []
        uid = user_id or self.user_id
        
        # 1. Try semantic search first (meaning-based)
        try:
            from .semantic_search import get_semantic_search
            sem = get_semantic_search()
            sem_results = sem.search(uid, current_topic, limit=8)
            if sem_results:
                for result in sem_results:
                    relevant_memories.append({
                        "content": result["content"],
                        "type": result["memory_type"],
                        "metadata": {
                            "similarity": result["similarity"],
                            "emotional_weight": result.get("emotional_weight", "normal"),
                            "flagged_for_recall": result.get("flagged_for_recall", False)
                        },
                        "source": "semantic"
                    })
                if len(relevant_memories) >= 4:
                    return relevant_memories  # Enough semantic results
        except Exception:
            pass  # Fall through to FTS5
        
        # 2. Augment with FTS5 keyword search (catches exact names/terms)
        try:
            from .memory_search import get_memory_search
            search_index = get_memory_search()
            fts_results = search_index.search(uid, current_topic, limit=8)
            if fts_results:
                seen_content = {m["content"][:50] for m in relevant_memories}
                for result in fts_results:
                    if result["content"][:50] not in seen_content:
                        relevant_memories.append({
                            "content": result["content"],
                            "type": result["memory_type"],
                            "metadata": result["metadata"],
                            "source": "fts5"
                        })
                        seen_content.add(result["content"][:50])
                if relevant_memories:
                    return relevant_memories[:10]
        except Exception:
            pass
        
        # 3. Fallback: basic topic matching
        stm = self.get_stm(decay=False)
        episodic = self.get_episodic(min_salience=0.1)
        identity = self.get_identity(min_confidence=0.5)
        
        for memory in stm + episodic + identity:
            memory_topic = memory.get("topic", "").lower()
            if current_topic.lower() in memory_topic or memory_topic in current_topic.lower():
                relevant_memories.append(memory)
        
        return relevant_memories
    
    def get_recent_context(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Only recent memories for casual topics."""
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(hours=hours)
        
        recent_memories = []
        for memory_type in ["stm", "episodic"]:
            memories = self.memory.get(memory_type, [])
            for memory in memories:
                memory_time = datetime.fromisoformat(memory["timestamp"].replace("Z", "+00:00"))
                if memory_time > cutoff:
                    recent_memories.append(memory)
        
        return recent_memories
    
    def prioritize_emotional(self, memories: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Always include emotional memories."""
        # Sort by emotional weight (descending)
        return sorted(memories, key=lambda m: m.get("emotional_weight", 0), reverse=True)
    
    def calculate_relevance(self, memory: Dict[str, Any], current_context: Dict[str, Any]) -> float:
        """Score memory relevance instead of keyword matching."""
        score = 0.0
        
        # Topic overlap (40%)
        current_topic = current_context.get("topic", "").lower()
        memory_topic = memory.get("topic", "").lower()
        if current_topic and memory_topic and (current_topic in memory_topic or memory_topic in current_topic):
            score += 0.4
        
        # Recency (30%)
        memory_time = datetime.fromisoformat(memory["timestamp"].replace("Z", "+00:00"))
        hours_old = (datetime.now(timezone.utc) - memory_time).total_seconds() / 3600
        if hours_old < 24:
            score += 0.3
        
        # Emotional weight (20%)
        emotional_weight = memory.get("emotional_weight", 0)
        score += emotional_weight * 0.2
        
        # Salience for episodic memories (10%)
        if memory.get("salience", 0) > 0.5:
            score += 0.1
        
        return score
    
    async def reason_about_memories(self, current_context: Dict[str, Any], 
                                   recent_messages: List[Dict] = None) -> Dict[str, Any]:
        """Use LLM to reason about memory relevance instead of hardcoded logic."""
        from .agent import INFERENCE_URL, MODEL_ID
        import httpx
        import os
        
        # Get candidate memories
        all_memories = self.get_stm(decay=False) + self.get_episodic(min_salience=0.1) + self.get_identity(min_confidence=0.5)
        
        if not all_memories:
            return {"relevant_memories": [], "reasoning": "No memories available"}
        
        # Build LLM prompt for memory reasoning
        prompt = f"""You are a memory reasoning system. Your job is to determine which memories are relevant to the current conversation.

CURRENT CONTEXT:
- Topic: {current_context.get('topic', 'general')}
- Relationship Phase: {current_context.get('phase', 'Discovery')}
- Recent messages: {[m.get('content', '')[:50] + '...' for m in (recent_messages or [])[-3:]]}

CANDIDATE MEMORIES:
{self._format_memories_for_llm(all_memories[:10])}

TASK:
1. Analyze each memory for relevance to CURRENT CONTEXT
2. Consider: topic overlap, emotional significance, recency, relationship phase
3. Return ONLY relevant memories with reasoning

RESPONSE FORMAT:
{{
  "relevant_memories": [
    {{
      "memory_index": 0,
      "relevance_score": 0.8,
      "reasoning": "This memory is relevant because...",
      "emotional_weight": 0.6,
      "topic_match": "high/medium/low"
    }}
  ],
  "overall_reasoning": "Brief summary of why these memories were selected"
}}

Be selective. Only include memories that genuinely add value to the current conversation."""

        try:
            # Rate limiter removed — only main response is rate-limited
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    INFERENCE_URL,
                    headers={"Authorization": f"Bearer {os.environ.get('GROQ_API_KEY')}"},
                    json={
                        "model": MODEL_ID,
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": 500,
                        "temperature": 0.3
                    }
                )
                
                if resp.status_code == 200:
                    result = resp.json()["choices"][0]["message"]["content"]
                    import json
                    llm_response = json.loads(result)
                    
                    # Map LLM responses back to actual memories
                    relevant_memories = []
                    for item in llm_response.get("relevant_memories", []):
                        idx = item.get("memory_index", 0)
                        if idx < len(all_memories):
                            memory = all_memories[idx].copy()
                            memory["relevance_score"] = item.get("relevance_score", 0.5)
                            memory["llm_reasoning"] = item.get("reasoning", "")
                            memory["emotional_weight"] = item.get("emotional_weight", 0.5)
                            relevant_memories.append(memory)
                    
                    return {
                        "relevant_memories": relevant_memories,
                        "reasoning": llm_response.get("overall_reasoning", "")
                    }
        except Exception as e:
            print(f"[ERROR] LLM memory reasoning failed: {e}")
        
        # Fallback to basic logic
        return {"relevant_memories": all_memories[:5], "reasoning": "LLM failed, using fallback"}
    
    def _format_memories_for_llm(self, memories: List[Dict]) -> str:
        """Format memories for LLM consumption."""
        formatted = []
        for i, memory in enumerate(memories):
            content = memory.get("content", "")[:100]
            topic = memory.get("topic", "unknown")
            mem_type = "Identity" if "confidence" in memory else "Episodic" if "salience" in memory else "STM"
            formatted.append(f"[{i}] {mem_type}: {content} (Topic: {topic})")
        return "\n".join(formatted)
    
    def get_memory_hierarchy(self) -> Dict[str, Any]:
        """Get current memory hierarchy state."""
        return self.memory
    
    def update_state_memory(self, state: Dict[str, Any]):
        """Update state with current memory hierarchy."""
        state["memory_hierarchy"] = self.memory

