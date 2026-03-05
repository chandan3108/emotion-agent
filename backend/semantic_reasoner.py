"""
Semantic Reasoner - LLM-Native Understanding
Replaces hardcoded keyword matching with genuine semantic understanding.
This is where the AI actually *thinks* about what the user means.
"""

import os
import json
import random
from typing import Dict, Any, Optional, List
import httpx
from .rate_limiter import global_rate_limiter

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
HF_TOKEN = GROQ_API_KEY  # Alias for compatibility
MODEL_ID = os.environ.get("MODEL_ID", "llama-3.1-8b-instant")
INFERENCE_URL = "https://api.groq.com/openai/v1/chat/completions"


class SemanticReasoner:
    """
    Uses LLM to understand messages semantically instead of keyword matching.
    This creates genuine understanding, not pattern matching.
    """
    
    def __init__(self):
        self.has_llm = bool(HF_TOKEN)
    
    async def understand_message(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Use LLM to understand the semantic meaning of a message.
        Returns: intent, events, sincerity, subtext, emotional_truth
        """
        if not self.has_llm:
            # Fallback to simple heuristic if no LLM
            return self._heuristic_understanding(message)
        
        # Build understanding prompt
        prompt = self._build_understanding_prompt(message, context)
        
        try:
            # Rate limiter removed — only main response is rate-limited
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    INFERENCE_URL,
                    headers={"Authorization": f"Bearer {HF_TOKEN}"},
                    json=prompt,
                )
                
                if resp.status_code >= 400:
                    return self._heuristic_understanding(message)
                
                data = resp.json()
                choices = data.get("choices", [])
                if choices:
                    content = choices[0].get("message", {}).get("content", "")
                    return self._parse_understanding(content, message)
        except Exception:
            pass
        
        return self._heuristic_understanding(message)
    
    def _build_understanding_prompt(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Build prompt for semantic understanding."""
        
        psyche = context.get("psyche_state", {})
        recent_memories = context.get("recent_memories", [])
        
        system_prompt = """You are a semantic understanding system. Analyze user messages to extract:
1. Intent (chat, question, request, complaint, vulnerability, joke, etc.)
2. Events (promises, conflicts, confessions, achievements, etc.)
3. Sincerity (0-1, how genuine/authentic the message feels)
4. Subtext (what they're really saying beneath the words)
5. Emotional truth (actual emotion vs stated emotion)
6. Complexity (0.0-1.0): How much cognitive processing this message requires
   - 0.0-0.3: Simple (greetings, acknowledgments, short responses) - minimal processing needed
   - 0.3-0.6: Standard (normal conversation, questions, requests) - standard processing
   - 0.6-0.8: Complex (deep questions, emotional content, conflicts) - enhanced processing
   - 0.8-1.0: Critical (conflicts, hurt, major decisions) - full QMAS + deep reasoning
7. Topic (main subject: work, hobbies, personal, emotions, entertainment, etc.)
8. Emotional tone (overall feeling: positive, neutral, negative, anxious, excited, etc.)

Be nuanced. "I'm fine" can mean different things. Sarcasm exists. People mask emotions.
Consider: message length, emotional depth, subtext complexity, relationship implications.
Return ONLY valid JSON in this format:
{
  "intent": "string",
  "events": [{"type": "string", "content": "string", "confidence": 0.0-1.0}],
  "sincerity": 0.0-1.0,
  "subtext": "string",
  "emotional_truth": {"emotion": "string", "intensity": 0.0-1.0, "masked": true/false},
  "complexity": 0.0-1.0,
  "topic": "string",
  "emotional_tone": "string"
}"""
        
        context_str = ""
        if psyche:
            context_str += f"Current relationship state: trust={psyche.get('trust', 0.7):.2f}, hurt={psyche.get('hurt', 0.0):.2f}\n"
        if recent_memories:
            context_str += f"Recent context: {recent_memories[-1].get('content', '')[:100]}...\n"
        
        return {
            "model": MODEL_ID,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"{context_str}User message: {message}"}
            ],
            "max_tokens": 300,
            "temperature": 0.7,  # Some creativity in understanding
            "response_format": {"type": "json_object"}
        }
    
    def _parse_understanding(self, content: str, original_message: str) -> Dict[str, Any]:
        """Parse LLM understanding response."""
        try:
            # Try to extract JSON
            if "{" in content and "}" in content:
                json_start = content.find("{")
                json_end = content.rfind("}") + 1
                json_str = content[json_start:json_end]
                parsed = json.loads(json_str)
                
                # Validate and return (include complexity - LLM-determined)
                return {
                    "intent": parsed.get("intent", "chat"),
                    "events": parsed.get("events", []),
                    "sincerity": max(0.0, min(1.0, parsed.get("sincerity", 0.7))),
                    "subtext": parsed.get("subtext", ""),
                    "emotional_truth": parsed.get("emotional_truth", {
                        "emotion": "neutral",
                        "intensity": 0.5,
                        "masked": False
                    }),
                    "complexity": max(0.0, min(1.0, parsed.get("complexity", 0.5))),  # LLM-determined complexity
                    "topic": parsed.get("topic", "general"),
                    "emotional_tone": parsed.get("emotional_tone", "neutral")
                }
        except Exception:
            pass
        
        return self._heuristic_understanding(original_message)
    
    def _heuristic_understanding(self, message: str) -> Dict[str, Any]:
        """Fallback heuristic understanding - infers intent without LLM."""
        message_lower = message.lower()
        words = message_lower.split()
        
        # Intent detection - infer from message characteristics
        intent = "chat"
        
        # Greeting patterns (inferred, not hardcoded)
        greeting_words = ["hi", "hey", "hello", "sup", "yo", "wassup", "whats", "what's", "wsg", "wsp", "gn", "gng"]
        if any(word in words[:2] for word in greeting_words) or len(words) <= 2:
            intent = "greeting"
        
        # Question detection
        if "?" in message or any(word in words for word in ["how", "what", "why", "when", "where", "who"]):
            intent = "question"
        
        # Request detection
        if any(word in message_lower for word in ["please", "can you", "could you", "help", "need"]):
            intent = "request"
        
        # Apology detection
        if any(word in message_lower for word in ["sorry", "apologize", "my fault", "my bad"]):
            intent = "apology"
        
        # Acknowledgment detection
        if any(word in words for word in ["ok", "okay", "k", "kk", "yes", "yeah", "yep", "yup", "no", "nope", "thanks", "ty", "thx"]):
            intent = "acknowledgment"
        
        # Goodbye detection
        if any(word in message_lower for word in ["bye", "goodbye", "see ya", "cya", "later"]):
            intent = "goodbye"
        
        # Events (minimal, but better than nothing)
        events = []
        if any(word in message_lower for word in ["promise", "will", "going to", "commit"]):
            events.append({
                "type": "promise",
                "content": message,
                "confidence": 0.5
            })
        
        # Estimate complexity heuristically
        # Very short messages are always simple (no need for LLM understanding)
        word_count = len(words)
        complexity = 0.3  # Default to standard
        
        if word_count <= 3:
            # Very short messages are simple regardless of content
            complexity = 0.2
        elif intent in ["greeting", "acknowledgment", "thanks", "goodbye"]:
            complexity = 0.2  # Simple
        elif intent == "question" and word_count > 5:
            # Only longer questions need deeper understanding
            complexity = 0.5
        elif any(word in message_lower for word in ["conflict", "hurt", "angry", "upset", "disappointed", "betrayed", "lied"]):
            complexity = 0.8  # Complex/critical - emotional content
        
        # Heuristic topic detection
        topic = "general"
        if any(word in message_lower for word in ["work", "job", "boss", "career", "office", "company"]):
            topic = "work"
        elif any(word in message_lower for word in ["movie", "music", "game", "book", "hobby", "play"]):
            topic = "entertainment"
        elif any(word in message_lower for word in ["feel", "sad", "happy", "angry", "love", "hate"]):
            topic = "emotions"
        elif any(word in message_lower for word in ["family", "friend", "mom", "dad", "sister"]):
            topic = "personal"
        
        # Heuristic emotional tone detection
        emotional_tone = "neutral"
        if any(word in message_lower for word in ["happy", "excited", "great", "awesome", "love"]):
            emotional_tone = "positive"
        elif any(word in message_lower for word in ["sad", "angry", "hate", "terrible", "awful"]):
            emotional_tone = "negative"
        elif any(word in message_lower for word in ["worried", "anxious", "nervous", "scared"]):
            emotional_tone = "anxious"
        
        return {
            "intent": intent,
            "events": events,
            "sincerity": 0.7,  # Default moderate
            "subtext": "",
            "emotional_truth": {
                "emotion": "neutral",
                "intensity": 0.5,
                "masked": False
            },
            "complexity": complexity,
            "topic": topic,  # Improved heuristic
            "emotional_tone": emotional_tone  # Improved heuristic
        }


class StochasticBehavior:
    """
    Adds human-like randomness and unpredictability.
    Humans aren't deterministic - neither should the AI be.
    """
    
    @staticmethod
    def add_response_variance(base_value: float, variance: float = 0.15) -> float:
        """
        Add random variance to make behavior less predictable.
        Humans have natural variation in their responses.
        """
        noise = random.gauss(0, variance)
        return max(0.0, min(1.0, base_value + noise))
    
    @staticmethod
    def should_remember_this(memory_salience: float, base_probability: float = 0.7) -> bool:
        """
        Sometimes humans remember things unexpectedly.
        Sometimes they forget important things.
        This adds organic unpredictability.
        """
        # Higher salience = more likely to remember, but not guaranteed
        remember_prob = base_probability * (0.5 + memory_salience)
        
        # Add some randomness (humans are inconsistent)
        remember_prob = StochasticBehavior.add_response_variance(remember_prob, 0.2)
        
        return random.random() < remember_prob
    
    @staticmethod
    def get_response_delay(base_delay: float, mood: Dict[str, float]) -> float:
        """
        Human response times vary based on mood and randomness.
        Excited = faster, thoughtful = slower, but with natural variation.
        """
        # Mood affects base delay
        excitement = mood.get("excitement", 0.3)
        energy = mood.get("energy", 0.5)
        
        # Excited/energetic = faster responses
        speed_multiplier = 0.7 + 0.3 * (1 - (excitement + energy) / 2)
        
        # Add randomness (humans don't respond at exact intervals)
        variance = random.gauss(0, base_delay * 0.3)
        
        return max(0.0, base_delay * speed_multiplier + variance)
    
    @staticmethod
    def should_use_memory(memory: Dict[str, Any], context_relevance: float) -> bool:
        """
        Humans don't always reference relevant memories.
        Sometimes they bring up random things.
        Sometimes they forget to mention important context.
        """
        # Base probability from relevance
        prob = context_relevance
        
        # Add randomness (humans are inconsistent)
        prob = StochasticBehavior.add_response_variance(prob, 0.25)
        
        # Sometimes humans remember things that aren't obviously relevant
        if random.random() < 0.1:  # 10% chance of "random" memory
            return True
        
        return random.random() < prob
    
    @staticmethod
    def get_emotional_reaction_variance(base_reaction: float) -> float:
        """
        Human emotional reactions aren't perfectly consistent.
        Same situation can feel different on different days.
        """
        # Add day-to-day variance
        variance = random.gauss(0, 0.15)
        return max(0.0, min(1.0, base_reaction + variance))
    
    @staticmethod
    def should_initiate_conversation(initiative_score: float) -> bool:
        """
        Humans don't always message when they "should".
        Sometimes they're impulsive, sometimes they hold back.
        """
        # Base probability
        prob = initiative_score
        
        # Add impulsivity randomness (humans are unpredictable)
        impulsivity = random.gauss(0, 0.2)
        prob = max(0.0, min(1.0, prob + impulsivity))
        
        # Sometimes humans message even when score is low (impulsivity)
        if random.random() < 0.05:  # 5% chance of "impulsive" message
            return True
        
        return random.random() < prob

