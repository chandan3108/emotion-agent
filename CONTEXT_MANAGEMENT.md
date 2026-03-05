# Context Window Management Strategy

## The Problem

When context reaches 100%, the LLM can't process new messages. We need smart management.

## Our Solution

### 1. **Proactive Management (85% threshold)**
- Start managing context when we hit 85% usage
- Don't wait until 100% (too late)

### 2. **Smart Prioritization**
- **Memories:** Keep only top 5 by salience + recency + type
- **Messages:** Keep last 10 verbatim, summarize older ones
- **State:** Compress to essential info only

### 3. **Summarization Strategy**
- Old messages → Single summary message
- Recent messages → Kept verbatim
- Memories → Prioritized by importance

### 4. **Aggressive Compression (if needed)**
- If still >95% after optimization
- Further reduce memory count
- Truncate less critical info
- Last resort to prevent overflow

## How It Works

```python
context_manager = get_context_manager(max_tokens=8000)

# Automatically optimizes context
optimized_context, metadata = context_manager.build_optimized_context(
    agent_state=agent_state,
    selected_memories=memories,
    message_history=history,
    system_prompt=system_msg
)

# metadata tells you:
# - usage_percentage
# - needs_management
# - memories_included
# - messages_included
```

## Memory Prioritization

**Priority Order:**
1. **Identity memories** (highest - facts about user)
2. **Episodic memories** (emotional events)
3. **ACT threads** (active topics)
4. **STM** (short-term, lowest priority)

**Scoring:**
- Salience: 50%
- Recency: 20%
- Type: 30% (identity > episodic > act > stm)
- Confidence: 10% (for identity)

## Message Summarization

**Strategy:**
- Last 10 messages: Kept verbatim
- Older messages: Summarized into one system message
- Format: `[Previous conversation summary: topic1 | topic2 | ...]`

**Future Enhancement:**
- Use LLM to generate better summaries
- Extract key themes, not just first sentences

## State Compression

**What We Keep:**
- Essential psyche (trust, hurt, forgiveness)
- Top 5 mood dimensions
- Core personality (Big Five, attachment)

**What We Remove:**
- Full memory hierarchy (selected separately)
- Detailed neurochemicals (not critical for response)
- Verbose metadata

## Monitoring

Check context usage:
```python
metadata = context_manager.build_optimized_context(...)
print(f"Context usage: {metadata['usage_percentage']:.1f}%")
```

## Adjusting for Your Model

**Different Models = Different Limits:**
- Llama-3.2-3B: ~8K tokens
- Llama-3.1-8B: ~128K tokens
- GPT-4: ~128K tokens

**To Adjust:**
```python
context_manager = get_context_manager(max_tokens=YOUR_MODEL_LIMIT)
```

## Best Practices

1. **Monitor Early:** Check usage at 85%, not 100%
2. **Prioritize Quality:** Keep most important memories
3. **Summarize Smartly:** Don't lose critical context
4. **Log Everything:** Track what gets compressed/removed
5. **Test Limits:** Know your model's actual limits

## Future Improvements

1. **LLM-Based Summarization:** Use LLM to create better summaries
2. **Semantic Compression:** Keep meaning, reduce tokens
3. **Dynamic Limits:** Adjust based on model performance
4. **Context Regeneration:** Rebuild context from state when needed
5. **Memory Chunking:** Split large memories into smaller pieces





