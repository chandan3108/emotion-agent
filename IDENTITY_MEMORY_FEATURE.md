# Identity Memory Feature - Core Details Storage

## What Was Added

I've implemented identity fact extraction so the system can remember core details about you **immediately**, including:

- **Names** (e.g., "My name is Chandan")
- **Jobs/Occupations** (e.g., "I work as a software engineer")
- **Location** (e.g., "I live in New York")
- **Age** (e.g., "I'm 25 years old")
- **Education** (e.g., "I study computer science at MIT")
- **Preferences** (e.g., "I love pizza", "I enjoy hiking")
- **Relationships** (e.g., "I have two siblings")
- **Background** (e.g., "I'm from India")
- **Traits** (e.g., "I'm good at programming")

## How It Works

### 1. **Identity Fact Extractor** (`backend/identity_extractor.py`)

New class that uses LLM to extract identity facts from user messages:

- **LLM-based extraction**: Uses semantic understanding to identify identity facts
- **Categories**: Names, jobs, location, age, education, preferences, relationships, background, traits
- **Confidence scoring**: Assigns confidence (0.0-1.0) based on explicitness
- **Fallback**: Heuristic extraction if LLM unavailable

### 2. **Immediate Storage** (`backend/cognitive_core.py`)

Identity facts are stored **immediately** (no waiting for 14+ days, 8+ occurrences):

- **Names**: Stored immediately with confidence ≥ 0.6 (elevated to 0.85 minimum)
- **Other facts**: Stored immediately with confidence ≥ 0.75
- **Duplicate detection**: Checks existing identity memory to avoid duplicates
- **Confidence updates**: If same fact appears with higher confidence, updates existing

### 3. **Integration**

- **Runs before pattern detection**: Identity facts are extracted first
- **Non-blocking**: If extraction fails, processing continues (graceful degradation)
- **No conflicts**: Works alongside routine pattern detection (handles different types of facts)

## Storage Location

Identity facts are stored in **Identity Memory**:

```
state["memory_hierarchy"]["identity"] = [
  {
    "identity_id": "i1234567890",
    "fact": "User's name is Chandan",
    "confidence": 0.95,
    "promoted_at": "2024-01-15T10:30:00Z",
    "evidence_count": 1,
    "contradictions": 0
  },
  ...
]
```

## Examples

### Name Introduction
**User says:** "My name is Chandan"

**Extracted:**
```json
{
  "fact": "User's name is Chandan",
  "confidence": 0.95,
  "category": "name"
}
```

**Stored:** ✅ Immediately in identity memory with confidence 0.95

### Job Introduction
**User says:** "I work as a software engineer"

**Extracted:**
```json
{
  "fact": "User works as a software engineer",
  "confidence": 0.9,
  "category": "job"
}
```

**Stored:** ✅ Immediately in identity memory with confidence 0.9

### Location
**User says:** "I live in San Francisco"

**Extracted:**
```json
{
  "fact": "User lives in San Francisco",
  "confidence": 0.9,
  "category": "location"
}
```

**Stored:** ✅ Immediately in identity memory with confidence 0.9

## Benefits

1. **Immediate recall**: Core details remembered right away, not after weeks of repetition
2. **High confidence**: Names and explicit facts stored with high confidence (0.85-0.95)
3. **No duplicates**: System checks for existing facts to avoid duplicates
4. **Persistent**: Stored in identity memory (doesn't expire like STM)
5. **LLM-powered**: Uses semantic understanding, not just keyword matching

## Usage

Just tell the AI your details naturally:

- "My name is Chandan"
- "I'm a student studying computer science"
- "I live in Bangalore, India"
- "I'm 23 years old"
- "I love playing guitar"

The system will extract and store these facts immediately!

## Technical Details

- **File**: `backend/identity_extractor.py`
- **Integration**: `backend/cognitive_core.py` (in `_update_memory` method)
- **Storage**: `backend/memory.py` (via `promote_to_identity` method)
- **LLM Model**: Uses same model as semantic reasoner (Llama-3.2-3B-Instruct)
- **Timeout**: 15 seconds (non-blocking, continues if fails)

## Status

✅ **Fully implemented and integrated**
✅ **Ready to use**
✅ **No breaking changes** (works alongside existing pattern detection)

