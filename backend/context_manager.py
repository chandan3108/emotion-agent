"""
Context Window Management
Handles context overflow when approaching 100% token limit.
"""

from typing import Dict, Any, List, Tuple
from datetime import datetime, timezone
import json


class ContextManager:
    """
    Manages context window to prevent overflow.
    Implements smart summarization and memory prioritization.
    """
    
    def __init__(self, max_tokens: int = 8000, warning_threshold: float = 0.85):
        """
        Args:
            max_tokens: Maximum context window size
            warning_threshold: Start managing at this % (default 85%)
        """
        self.max_tokens = max_tokens
        self.warning_threshold = warning_threshold
        self.warning_tokens = int(max_tokens * warning_threshold)
    
    def estimate_tokens(self, text: str) -> int:
        """
        Rough token estimation (4 chars ≈ 1 token for English).
        For production, use tiktoken or similar.
        """
        return len(text) // 4
    
    def check_context_size(self, current_context: str) -> Tuple[bool, float]:
        """
        Check if context is approaching limit.
        
        Returns:
            (needs_management, usage_percentage)
        """
        current_tokens = self.estimate_tokens(current_context)
        usage = current_tokens / self.max_tokens
        
        needs_management = current_tokens >= self.warning_tokens
        
        return needs_management, usage
    
    def prioritize_memories(self, memories: List[Dict[str, Any]], 
                          max_memories: int = 5) -> List[Dict[str, Any]]:
        """
        Prioritize memories by salience, recency, and relevance.
        Keep only the most important ones.
        """
        if len(memories) <= max_memories:
            return memories
        
        # Score each memory
        scored = []
        for mem in memories:
            score = 0.0
            
            # Salience (most important)
            salience = mem.get("salience", 0.0)
            score += salience * 0.5
            
            # Recency (if has timestamp)
            if "timestamp" in mem or "created_at" in mem:
                score += 0.2  # Recent memories get boost
            
            # Type priority: identity > episodic > act > stm
            type_priority = {
                "identity": 0.3,
                "episodic": 0.25,
                "act": 0.15,
                "stm": 0.1
            }
            mem_type = mem.get("type", "stm")
            score += type_priority.get(mem_type, 0.1)
            
            # Confidence (for identity memories)
            confidence = mem.get("confidence", 0.0)
            score += confidence * 0.1
            
            scored.append((score, mem))
        
        # Sort by score, take top N
        scored.sort(key=lambda x: x[0], reverse=True)
        return [mem for _, mem in scored[:max_memories]]
    
    def summarize_old_messages(self, messages: List[Dict[str, str]], 
                            keep_recent: int = 10) -> List[Dict[str, str]]:
        """
        Summarize old messages, keep recent ones verbatim.
        
        Strategy:
        - Keep last N messages verbatim (default 10)
        - Summarize older messages into a single summary message
        """
        if len(messages) <= keep_recent:
            return messages
        
        # Split into recent and old
        recent = messages[-keep_recent:]
        old = messages[:-keep_recent]
        
        # Create summary of old messages
        if old:
            # Extract key topics/themes from old messages
            summary_content = self._create_summary(old)
            
            summary_message = {
                "role": "system",
                "content": f"[Previous conversation summary: {summary_content}]"
            }
            
            # Return: summary + recent messages
            return [summary_message] + recent
        
        return recent
    
    def _create_summary(self, messages: List[Dict[str, str]]) -> str:
        """
        Create a brief summary of old messages.
        In production, use LLM to generate better summaries.
        """
        # Simple extraction of key topics
        user_messages = [m["content"] for m in messages if m["role"] == "user"]
        
        # Extract first sentence of each user message (rough summary)
        summaries = []
        for msg in user_messages[:5]:  # Limit to first 5
            first_sentence = msg.split('.')[0]
            if len(first_sentence) > 10:
                summaries.append(first_sentence[:100])
        
        if summaries:
            return " | ".join(summaries)
        
        return "Previous conversation about various topics."
    
    def compress_state(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compress state representation to save tokens.
        Keep essential info, summarize or remove less critical parts.
        """
        compressed = {}
        
        # Keep essential psyche state (compact)
        psyche = state.get("current_psyche", {})
        compressed["psyche"] = {
            "trust": round(psyche.get("trust", 0.7), 2),
            "hurt": round(psyche.get("hurt", 0.0), 2),
            "forgiveness": psyche.get("forgiveness_state", "FORGIVEN")
        }
        
        # Keep mood (compact, only top 5 dimensions)
        mood = state.get("mood", {})
        top_moods = sorted(mood.items(), key=lambda x: x[1], reverse=True)[:5]
        compressed["mood"] = {k: round(v, 2) for k, v in top_moods}
        
        # Keep personality summary (compact)
        personality = state.get("core_personality", {})
        compressed["personality"] = {
            "big_five": personality.get("big_five", {}),
            "attachment": personality.get("attachment_style", "secure")
        }
        
        # Don't include full memory hierarchy (too large)
        # Memories are selected separately
        
        return compressed
    
    def build_optimized_context(self, 
                               agent_state: Dict[str, Any],
                               selected_memories: List[Dict[str, Any]],
                               message_history: List[Dict[str, str]],
                               system_prompt: str) -> Tuple[str, Dict[str, Any]]:
        """
        Build optimized context that fits within token limit.
        
        Returns:
            (optimized_context, metadata)
        """
        # Start with system prompt
        context_parts = [system_prompt]
        
        # Add compressed agent state
        compressed_state = self.compress_state(agent_state)
        state_str = json.dumps(compressed_state, indent=0)
        context_parts.append(f"\nAGENT STATE:\n{state_str}\n")
        
        # Add prioritized memories (limit to 5)
        prioritized_memories = self.prioritize_memories(selected_memories, max_memories=5)
        if prioritized_memories:
            context_parts.append("\nMEMORIES:\n")
            for mem in prioritized_memories:
                mem_str = self._format_memory(mem)
                context_parts.append(mem_str)
        
        # Add message history (summarize old, keep recent)
        optimized_history = self.summarize_old_messages(message_history, keep_recent=10)
        context_parts.append("\nCONVERSATION:\n")
        for msg in optimized_history:
            context_parts.append(f"{msg['role']}: {msg['content']}")
        
        # Combine
        full_context = "\n".join(context_parts)
        
        # Check size
        needs_management, usage = self.check_context_size(full_context)
        
        metadata = {
            "estimated_tokens": self.estimate_tokens(full_context),
            "usage_percentage": usage * 100,
            "needs_management": needs_management,
            "memories_included": len(prioritized_memories),
            "messages_included": len(optimized_history)
        }
        
        # If still too large, apply more aggressive compression
        if needs_management and usage > 0.95:
            full_context = self._aggressive_compression(full_context, metadata)
            metadata["aggressive_compression"] = True
        
        return full_context, metadata
    
    def _format_memory(self, memory: Dict[str, Any]) -> str:
        """Format memory for context (compact)."""
        mem_type = memory.get("type", "unknown")
        content = memory.get("content", memory.get("fact", ""))[:150]  # Truncate
        
        if mem_type == "identity":
            return f"- {content} (confidence: {memory.get('confidence', 0):.2f})"
        elif mem_type == "episodic":
            return f"- Past: {content}..."
        elif mem_type == "act":
            return f"- Topic: {content}..."
        else:
            return f"- {content}..."
    
    def _aggressive_compression(self, context: str, metadata: Dict[str, Any]) -> str:
        """
        Apply aggressive compression when context is still too large.
        Last resort - reduces quality but prevents overflow.
        """
        # Reduce memory count further
        # Truncate message history more
        # Remove less critical state info
        
        # For now, just truncate the context
        max_chars = int(self.max_tokens * 0.9 * 4)  # 90% of max, in chars
        if len(context) > max_chars:
            context = context[:max_chars] + "\n[Context truncated due to size limit]"
            metadata["truncated"] = True
        
        return context


# Global instance
_context_manager: ContextManager = None


def get_context_manager(max_tokens: int = 8000) -> ContextManager:
    """Get or create global context manager."""
    global _context_manager
    if _context_manager is None:
        _context_manager = ContextManager(max_tokens)
    return _context_manager










