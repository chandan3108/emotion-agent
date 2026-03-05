"""
Identity Fact Extractor
Extracts and stores core identity facts (name, job, location, preferences, etc.) immediately.
Unlike pattern detection which requires repetition, identity facts are stored with high confidence from first mention.
"""

import os
import json
from typing import Dict, Any, List, Optional
import httpx
from .rate_limiter import global_rate_limiter

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
HF_TOKEN = GROQ_API_KEY  # Alias for compatibility
MODEL_ID = os.environ.get("MODEL_ID", "llama-3.1-8b-instant")
INFERENCE_URL = "https://api.groq.com/openai/v1/chat/completions"


class IdentityExtractor:
    """
    Extracts identity facts from user messages using LLM.
    Stores high-confidence facts immediately (names, jobs, etc.).
    """
    
    def __init__(self):
        self.has_llm = bool(HF_TOKEN)
    
    async def extract_identity_facts(self, user_message: str, understanding: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract identity facts from user message.
        
        Returns:
            List of identity facts: [{"fact": str, "confidence": float, "category": str}, ...]
        """
        if not self.has_llm:
            return self._heuristic_extract(user_message)
        
        prompt = self._build_extraction_prompt(user_message, understanding)
        
        try:
            # Rate limiter removed — only main response is rate-limited
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(
                    INFERENCE_URL,
                    headers={"Authorization": f"Bearer {HF_TOKEN}"},
                    json=prompt,
                )
                
                if resp.status_code >= 400:
                    return self._heuristic_extract(user_message)
                
                data = resp.json()
                choices = data.get("choices", [])
                if choices:
                    content = choices[0].get("message", {}).get("content", "")
                    return self._parse_facts(content, user_message)
        except Exception as e:
            print(f"[WARNING] Identity extraction error: {e}")
        
        return self._heuristic_extract(user_message)
    
    def _build_extraction_prompt(self, user_message: str, understanding: Dict[str, Any]) -> Dict[str, Any]:
        """Build prompt for identity fact extraction."""
        
        intent = understanding.get("intent", "chat")
        sincerity = understanding.get("sincerity", 0.7)
        
        system_prompt = """You are an identity fact extractor. Extract factual information about the user from their message.

IDENTITY CATEGORIES:
- name: Full name, first name, nickname, what they prefer to be called
- job: Occupation, profession, work role, career
- location: City, country, state, where they live
- age: Age or age range
- education: School, university, degree, major
- preferences: Likes, dislikes, favorite things (food, music, hobbies, etc.)
- relationships: Family members, partner status, close relationships
- background: Cultural background, nationality, languages spoken
- traits: Personal characteristics, skills, abilities

EXTRACTION RULES:
1. Only extract FACTS (things that are objectively true about the user)
2. Do NOT extract opinions, feelings, or temporary states
3. For names: Extract if explicitly stated ("My name is X", "I'm X", "Call me X")
4. High confidence (0.9+) for explicit statements ("My name is John", "I work as a doctor")
5. Lower confidence (0.6-0.8) for implied facts (inferred from context)
6. Return empty array if no identity facts found

EXAMPLES:
- "My name is Chandan" → [{"fact": "User's name is Chandan", "confidence": 0.95, "category": "name"}]
- "I'm a software engineer" → [{"fact": "User works as a software engineer", "confidence": 0.9, "category": "job"}]
- "I live in New York" → [{"fact": "User lives in New York", "confidence": 0.9, "category": "location"}]
- "I love pizza" → [{"fact": "User likes pizza", "confidence": 0.7, "category": "preferences"}]
- "I'm 25 years old" → [{"fact": "User is 25 years old", "confidence": 0.95, "category": "age"}]
- "hey how's it going" → [] (no identity facts)

Return ONLY valid JSON object with a "facts" array in this format:
{
  "facts": [
    {"fact": "string (normalized fact)", "confidence": 0.0-1.0, "category": "string"},
    ...
  ]
}

Be precise and conservative - only extract clear, explicit identity facts."""
        
        return {
            "model": MODEL_ID,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"User message: {user_message}\nIntent: {intent}, Sincerity: {sincerity:.2f}\n\nExtract identity facts."}
            ],
            "max_tokens": 300,
            "temperature": 0.3,  # Low temperature for factual extraction
            "response_format": {"type": "json_object"}
        }
    
    def _parse_facts(self, content: str, original_message: str) -> List[Dict[str, Any]]:
        """Parse identity facts from LLM response."""
        try:
            # Try to extract JSON
            if "{" in content and "}" in content:
                json_start = content.find("{")
                json_end = content.rfind("}") + 1
                json_str = content[json_start:json_end]
                parsed = json.loads(json_str)
                
                # Handle both array and object formats
                if isinstance(parsed, list):
                    facts = parsed
                elif isinstance(parsed, dict):
                    # Check if facts are in a key
                    facts = parsed.get("facts", parsed.get("identity_facts", []))
                    if not isinstance(facts, list):
                        facts = []
                else:
                    facts = []
                
                # Validate and normalize facts
                validated_facts = []
                for fact in facts:
                    if isinstance(fact, dict):
                        fact_text = fact.get("fact", "").strip()
                        confidence = max(0.0, min(1.0, fact.get("confidence", 0.7)))
                        category = fact.get("category", "general").strip().lower()
                        
                        if fact_text and confidence >= 0.6:  # Only accept facts with decent confidence
                            validated_facts.append({
                                "fact": fact_text,
                                "confidence": confidence,
                                "category": category
                            })
                
                return validated_facts
        except Exception as e:
            print(f"[WARNING] Failed to parse identity facts: {e}")
        
        return self._heuristic_extract(original_message)
    
    def _heuristic_extract(self, user_message: str) -> List[Dict[str, Any]]:
        """Heuristic fallback for identity extraction (simple patterns)."""
        facts = []
        message_lower = user_message.lower()
        
        # Name patterns - ONLY explicit name statements
        # Be very strict to avoid false positives
        name_patterns = [
            ("my name is ", "name"),
            ("i'm called ", "name"),
            ("call me ", "name"),
        ]
        
        # Also check "i am X" / "im X" / "i'm X" patterns (common intros)
        # But only if X looks like a proper name (capitalized, not a common adjective)
        intro_patterns = [
            ("i am ", "name"),
            ("im ", "name"),
            ("i'm ", "name"),
        ]
        
        for pattern, category in name_patterns:
            if pattern in message_lower:
                parts = message_lower.split(pattern, 1)
                if len(parts) > 1:
                    name_candidate = parts[1].strip().split()[0] if parts[1].strip() else ""
                    name_candidate = name_candidate.strip(".,!?;:")
                    
                    non_names = ["a", "an", "the", "tired", "good", "fine", "ok", "okay", 
                                "happy", "sad", "bored", "hungry", "busy", "here", "done", 
                                "back", "student", "person", "human", "bot", "ai"]
                    
                    if name_candidate and len(name_candidate) > 1 and name_candidate not in non_names:
                        original_parts = user_message.split(pattern.rstrip(), 1)
                        if len(original_parts) > 1:
                            original_name = original_parts[1].strip().split()[0].strip(".,!?;:") if original_parts[1].strip() else ""
                            facts.append({
                                "fact": f"User's name is {original_name}",
                                "confidence": 0.9,
                                "category": category
                            })
                            break
        
        # Try intro patterns only if no name found from explicit patterns
        if not any(f.get("category") == "name" for f in facts):
            for pattern, category in intro_patterns:
                if pattern in message_lower:
                    parts = message_lower.split(pattern, 1)
                    if len(parts) > 1:
                        candidate = parts[1].strip().split()[0] if parts[1].strip() else ""
                        candidate = candidate.strip(".,!?;:")
                        
                        # For "i am X" patterns, X must be capitalized in original AND not a common word
                        non_names = ["a", "an", "the", "tired", "good", "fine", "ok", "okay",
                                    "happy", "sad", "bored", "hungry", "busy", "here", "done",
                                    "back", "student", "person", "human", "bot", "ai", "not",
                                    "so", "very", "too", "really", "just", "going", "doing",
                                    "feeling", "having", "trying", "looking", "thinking",
                                    "sorry", "sure", "interested", "confused", "new", "from"]
                        
                        if candidate and len(candidate) > 1 and candidate not in non_names:
                            # Check original capitalization — names are capitalized
                            original_parts = user_message.split(pattern.rstrip(), 1)
                            if len(original_parts) > 1:
                                original_word = original_parts[1].strip().split()[0].strip(".,!?;:") if original_parts[1].strip() else ""
                                if original_word and original_word[0].isupper():
                                    facts.append({
                                        "fact": f"User's name is {original_word}",
                                        "confidence": 0.85,
                                        "category": category
                                    })
                                    break
        
        # Job patterns - require "a/an" after pattern to avoid false matches
        # e.g. "i am a student" works, but "i am tired" doesn't
        job_patterns = [
            ("i work as a ", "job"),
            ("i work as an ", "job"),
            ("i'm a ", "job"),
            ("i'm an ", "job"),
            ("i am a ", "job"),
            ("i am an ", "job"),
            ("my job is ", "job"),
        ]
        
        for pattern, category in job_patterns:
            if pattern in message_lower:
                parts = user_message.lower().split(pattern, 1)
                if len(parts) > 1:
                    job_part = parts[1].strip().split()[0:3]  # Take first few words
                    if job_part:
                        job = " ".join(job_part).strip(".,!?;:")
                        # Validate it's actually a job/role, not an adjective
                        non_jobs = ["tired", "good", "fine", "ok", "okay", "happy", "sad", 
                                    "bored", "hungry", "busy", "here", "done", "back"]
                        if job and len(job) > 2 and job.split()[0].lower() not in non_jobs:
                            facts.append({
                                "fact": f"User is a {job}",
                                "confidence": 0.85,
                                "category": category
                            })
                            break
        
        return facts

