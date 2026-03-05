# QMAS Model Configuration Guide

## Overview

The Quantum Multi-Agent System (QMAS) now supports **specialized models per agent** for better performance. Each agent can use a different model optimized for its specific role.

## Default Configuration

By default, QMAS uses:
- **Most agents**: `meta-llama/Llama-3.2-3B-Instruct` (fast, efficient)
- **Rational & Memory agents**: `meta-llama/Llama-3.1-8B-Instruct` (better reasoning)
- **Meta-synthesis**: `meta-llama/Llama-3.1-8B-Instruct` (better ranking/synthesis)

## Customizing Models via Environment Variables

Set these environment variables to override default models:

```bash
# Individual agent models
export QMAS_MODEL_EMOTIONAL="meta-llama/Llama-3.2-3B-Instruct"
export QMAS_MODEL_RATIONAL="meta-llama/Llama-3.1-8B-Instruct"
export QMAS_MODEL_PROTECTIVE="meta-llama/Llama-3.2-3B-Instruct"
export QMAS_MODEL_AUTHENTIC="meta-llama/Llama-3.2-3B-Instruct"
export QMAS_MODEL_GROWTH="meta-llama/Llama-3.2-3B-Instruct"
export QMAS_MODEL_CREATIVE="meta-llama/Llama-3.2-3B-Instruct"
export QMAS_MODEL_MEMORY="meta-llama/Llama-3.1-8B-Instruct"

# Meta-synthesis model (for ranking/synthesizing paths)
export QMAS_META_SYNTHESIS_MODEL="meta-llama/Llama-3.1-8B-Instruct"
```

## Recommended Model Assignments

### For Better Reasoning (Rational, Memory agents):
- `meta-llama/Llama-3.1-8B-Instruct` - Better reasoning, pattern recognition
- `mistralai/Mistral-7B-Instruct-v0.2` - Strong reasoning capabilities
- `meta-llama/Llama-3.1-70B-Instruct` - Best reasoning (if you have access)

### For Creative/Emotional Agents:
- `meta-llama/Llama-3.2-3B-Instruct` - Fast, good for creative tasks
- `mistralai/Mixtral-8x7B-Instruct-v0.1` - Creative and nuanced
- `meta-llama/Llama-3.1-8B-Instruct` - Balanced

### For Meta-Synthesis (Ranking):
- `meta-llama/Llama-3.1-8B-Instruct` - Good balance
- `meta-llama/Llama-3.1-70B-Instruct` - Best quality (if available)
- `mistralai/Mistral-7B-Instruct-v0.2` - Strong synthesis

## Setting Your HuggingFace Token

**Important**: You need to set your HuggingFace token as an environment variable:

```bash
export HF_TOKEN="your_huggingface_token_here"
```

Or in your `.env` file:
```
HF_TOKEN=your_huggingface_token_here
```

## Example: High-Performance Configuration

For best quality (if you have access to larger models):

```bash
export HF_TOKEN="your_token"
export QMAS_MODEL_RATIONAL="meta-llama/Llama-3.1-70B-Instruct"
export QMAS_MODEL_MEMORY="meta-llama/Llama-3.1-70B-Instruct"
export QMAS_META_SYNTHESIS_MODEL="meta-llama/Llama-3.1-70B-Instruct"
```

## Example: Cost-Optimized Configuration

For lower costs (all 3B models):

```bash
export HF_TOKEN="your_token"
export QMAS_MODEL_RATIONAL="meta-llama/Llama-3.2-3B-Instruct"
export QMAS_MODEL_MEMORY="meta-llama/Llama-3.2-3B-Instruct"
export QMAS_META_SYNTHESIS_MODEL="meta-llama/Llama-3.2-3B-Instruct"
```

## Programmatic Configuration

You can also configure models programmatically:

```python
from backend.qmas import QuantumMultiAgentSystem

# Custom model configuration
custom_models = {
    "Rational": "meta-llama/Llama-3.1-8B-Instruct",
    "Memory": "meta-llama/Llama-3.1-8B-Instruct",
    # ... other agents use defaults
}

qmas = QuantumMultiAgentSystem(agent_models=custom_models)
```

## Model Availability

Make sure the models you specify are:
1. Available on HuggingFace Inference API
2. Compatible with the `/v1/chat/completions` endpoint
3. Accessible with your HuggingFace token

Check model availability at: https://huggingface.co/models

## Notes

- Models are loaded lazily (only when needed)
- If a model fails, the agent falls back to default behavior
- Larger models = better quality but slower + more expensive
- 3B models = faster + cheaper but less capable
- 8B models = good balance of quality and speed




