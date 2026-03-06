"""
Knowledge Grounding System
Prevents the bot from hallucinating real-world facts.
Uses LLM to detect when factual knowledge is needed, searches the web, and stores learned facts.
"""

import os
import re
import random
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone

import httpx
from .rate_limiter import global_rate_limiter

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY")
# Use the small fast model for classification
CLASSIFIER_MODEL = os.environ.get("MODEL_ID", "llama-3.1-8b-instant")
INFERENCE_URL = "https://api.groq.com/openai/v1/chat/completions"


async def _llm_classify_factual(message: str, recent_context: str) -> Dict[str, Any]:
    """
    Use LLM to determine if a message involves verifiable real-world facts.
    Returns: {"needs_search": bool, "search_query": str, "reasoning": str}
    
    This is a tiny, fast classification call — not a full response generation.
    """
    if not GROQ_API_KEY:
        return {"needs_search": False, "search_query": "", "reasoning": "no api key"}
    
    prompt = f"""Does this message reference specific real-world things that could be verified (characters, songs, shows, people, events, places, etc.)?

IMPORTANT: Look at the CONVERSATION CONTEXT to understand what the user is actually talking about.
If the user says something like "search it up" or "look it up", figure out WHAT they want searched from the context.

Recent conversation context:
{recent_context}

Current message: "{message}"

Reply in this EXACT format (nothing else):
NEEDS_SEARCH: yes or no
QUERY: search query if yes, empty if no

IMPORTANT: Only say yes if the user is asking about a SPECIFIC factual topic they want info on.
NO if they are just chatting, sharing opinions, venting, telling stories, or making conversation.
The message must be asking ABOUT something specific, not just MENTIONING a topic.

Examples:
- "shibuya where gojo was sealed" → NEEDS_SEARCH: yes / QUERY: gojo shibuya sealed jujutsu kaisen
- "hey how are you" → NEEDS_SEARCH: no / QUERY:
- "have you heard viva la vida" → NEEDS_SEARCH: yes / QUERY: viva la vida song coldplay
- "im feeling sad today" → NEEDS_SEARCH: no / QUERY:
- "yesss bruh thats crazy" → NEEDS_SEARCH: no / QUERY:
- "whats the opening song for naruto" → NEEDS_SEARCH: yes / QUERY: naruto opening songs
- "my lectures are so boring" → NEEDS_SEARCH: no / QUERY:
- "i hate doing homework" → NEEDS_SEARCH: no / QUERY:
- "do you think ai chatbots are replacing friends" → NEEDS_SEARCH: no / QUERY:
- "i was watching jjk and it was crazy" → NEEDS_SEARCH: no / QUERY:
- "what happened to gojo in the manga" → NEEDS_SEARCH: yes / QUERY: gojo fate jujutsu kaisen manga
- "coding is so frustrating" → NEEDS_SEARCH: no / QUERY:
- Context mentions "jujutsu kaisen", user says "search it up" → NEEDS_SEARCH: yes / QUERY: jujutsu kaisen anime
- Context mentions "hollow purple", user says "look it up" → NEEDS_SEARCH: yes / QUERY: hollow purple jujutsu kaisen
- "do u know what that is" (context mentions a specific thing) → NEEDS_SEARCH: yes / QUERY: [the thing from context]"""

    try:
        # Rate limiter removed — only main response is rate-limited
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                INFERENCE_URL,
                headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
                json={
                    "model": CLASSIFIER_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 50,
                    "temperature": 0.1,  # Low temp for consistent classification
                },
            )
            if resp.status_code >= 400:
                return {"needs_search": False, "search_query": "", "reasoning": f"api error {resp.status_code}"}
            
            data = resp.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
            
            # Parse response
            needs_search = "yes" in content.lower().split("needs_search:")[-1].split("\n")[0] if "needs_search:" in content.lower() else False
            query = ""
            if "query:" in content.lower():
                query = content.lower().split("query:")[-1].strip()
                # Clean up the query
                query = query.strip().strip('"').strip("'")
            
            return {
                "needs_search": needs_search,
                "search_query": query,
                "reasoning": content[:100]
            }
    except Exception as e:
        print(f"[KNOWLEDGE] Classification error: {e}")
        return {"needs_search": False, "search_query": "", "reasoning": str(e)}


async def search_web(query: str, max_results: int = 3) -> Optional[List[Dict[str, str]]]:
    """
    Search the web for factual information.
    Uses Tavily API (preferred) with DuckDuckGo as fallback.
    Returns list of {title, snippet, answer} or None on failure.
    """
    # Try Tavily first (much better quality)
    if TAVILY_API_KEY:
        try:
            async with httpx.AsyncClient(timeout=12.0) as client:
                resp = await client.post(
                    'https://api.tavily.com/search',
                    json={
                        'api_key': TAVILY_API_KEY,
                        'query': query,
                        'search_depth': 'basic',
                        'max_results': max_results,
                        'include_answer': True
                    }
                )
                if resp.status_code == 200:
                    data = resp.json()
                    results = []
                    # Include AI-generated answer as first result
                    answer = data.get('answer', '')
                    if answer:
                        results.append({'title': 'AI Answer', 'snippet': answer, 'is_answer': True})
                    # Include individual search results
                    for r in data.get('results', [])[:max_results]:
                        results.append({
                            'title': r.get('title', ''),
                            'snippet': r.get('content', '')[:300]
                        })
                    if results:
                        print(f"[KNOWLEDGE] Tavily search returned {len(results)} results")
                        return results
                else:
                    print(f"[KNOWLEDGE] Tavily error: {resp.status_code}")
        except Exception as e:
            print(f"[KNOWLEDGE] Tavily search failed: {e}")
    
    # Fallback to DuckDuckGo
    try:
        from duckduckgo_search import DDGS
        
        def _search():
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=max_results))
                return [{"title": r.get("title", ""), "snippet": r.get("body", "")} for r in results]
        
        results = await asyncio.get_event_loop().run_in_executor(None, _search)
        print(f"[KNOWLEDGE] DuckDuckGo fallback returned {len(results) if results else 0} results")
        return results if results else None
    except Exception as e:
        print(f"[KNOWLEDGE] Search failed: {e}")
        return None


def extract_facts_from_search(query: str, results: List[Dict[str, str]]) -> List[str]:
    """
    Extract concise factual statements from search results.
    Prioritizes Tavily's AI answer, falls back to snippet extraction.
    Filters out non-English results.
    """
    facts = []
    
    for r in results[:4]:
        snippet = r.get("snippet", "")
        
        # If this is Tavily's AI answer, use it directly (best quality)
        if r.get('is_answer'):
            if snippet and len(snippet) > 10:
                facts.append(snippet[:250])
                continue
        
        # Skip non-English results (detect by high ratio of non-ASCII chars)
        if snippet:
            non_ascii = sum(1 for c in snippet if ord(c) > 127)
            if non_ascii / max(len(snippet), 1) > 0.15:
                continue
        
        # Skip promotional/useless snippets
        useless_patterns = ['find out more', 'try out', 'click here', 'subscribe', 'sign up']
        if any(p in snippet.lower() for p in useless_patterns):
            continue
        
        # Take the first 2 sentences
        sentences = snippet.split(". ")
        fact_text = ". ".join(sentences[:2]).strip()
        if fact_text and len(fact_text) > 15:
            fact = fact_text[:200]
            if not fact.endswith("."):
                fact += "."
            facts.append(fact)
    
    return facts[:2]  # Max 2 facts per search


def detect_user_correction(message: str, message_history: List[Dict]) -> Optional[str]:
    """
    Detect when the user is correcting the bot.
    Patterns: "actually X", "no it's X", "X*" (asterisk correction), "not X, Y"
    """
    message_lower = message.strip().lower()
    
    # Asterisk correction: "jjk*", "naruto*"
    if message.strip().endswith("*") and len(message.strip()) < 30:
        correction = message.strip().rstrip("*").strip()
        if correction:
            for m in reversed(message_history[-3:]):
                if m.get("role") == "assistant":
                    bot_said = m.get("content", "")
                    return f"{correction} (correcting bot's reference to something else)"
            return correction
    
    # "actually..." corrections
    if message_lower.startswith("actually") or message_lower.startswith("no,") or message_lower.startswith("no "):
        return message.strip()
    
    # "it's X not Y" pattern
    if "not " in message_lower and ("it's" in message_lower or "its" in message_lower):
        return message.strip()
    
    return None


def _cheap_pre_filter(message: str, understanding: Dict[str, Any]) -> bool:
    """
    Cheap pre-filter to avoid wasting an LLM call on obvious non-factual messages.
    Returns True if the message MIGHT need factual grounding (should run LLM check).
    Returns False if definitely not (skip LLM check entirely).
    """
    message_lower = message.strip().lower()
    words = message_lower.split()
    
    # Skip very short messages (greetings, reactions) — unless they contain trigger words
    if len(words) <= 2:
        # Allow short inquiry/search phrases through (e.g. "what's jjk")
        has_trigger = any(kw in message_lower for kw in (
            'search', 'look up', 'google', 'what is', "what's", 'who is', "who's",
            'do you know', 'have you heard', 'tell me about'
        ))
        if not has_trigger:
            return False
    
    # Skip if the understanding already classified it as greeting/acknowledgment/goodbye
    intent = understanding.get("intent", "chat")
    if intent in ("greeting", "acknowledgment", "goodbye"):
        return False
    
    # Skip pure emoji/reaction messages
    if all(len(w) <= 1 or w in ("lol", "lmao", "haha", "omg", "bruh", "fr", "ong", "ngl", "tbh") for w in words):
        return False
    
    # Everything else — apply stricter checks
    # Must look like an actual information-seeking message, not just conversation
    
    # Question patterns that suggest factual need
    question_starters = ('what', 'who', 'when', 'where', 'how', 'why', 'which', 'is', 'are', 'was', 'were', 'do', 'does', 'did', 'can', 'could', 'have', 'has')
    is_question = message_lower.endswith('?') or any(message_lower.startswith(q + ' ') for q in question_starters)
    
    # "do you know about X" pattern
    knowledge_patterns = ('do you know', 'have you heard', 'ever heard of', 'you know about', 'tell me about', 'what is', 'what are', 'who is', 'who are')
    has_knowledge_pattern = any(p in message_lower for p in knowledge_patterns)
    
    # If it's not a question and doesn't have a knowledge-seeking pattern, skip
    if not is_question and not has_knowledge_pattern:
        return False
    
    return True


class KnowledgeGrounding:
    """
    Orchestrates knowledge grounding with two modes:
    
    Case 1 (EXPLICIT): User says "search", "look up", etc. → 100% search, share naturally
    Case 2 (IMPLICIT): Factual topic detected by LLM → check learned_facts first,
                        then 50% search (pretend already knew) / 50% skip (say idk)
    
    Facts stored in learned_facts (separate from identity), with decay.
    """
    
    # Category 1: Search commands — ALWAYS fire Tavily
    SEARCH_COMMANDS = [
        'search', 'look it up', 'look up', 'google', 'find out', 'check it',
        'search it', 'look that up', 'search that', 'search for', 'search about',
    ]
    
    # Category 2: Knowledge inquiries — check existing, then 50/50
    INQUIRY_KEYWORDS = [
        'do you know', 'have you heard', 'have u heard', 'you know about',
        'u know about', 'what is', "what's", 'who is', "who's",
        'tell me about', 'you ever seen', 'have you seen', 'have u seen',
        'you know what', 'u know what', 'ever watched', 'ever heard of',
    ]
    
    async def process(
        self,
        user_message: str,
        understanding: Dict[str, Any],
        memory_system,
        message_history: List[Dict] = None,
        user_taught_knowledge: Dict[str, str] = None
    ) -> Dict[str, Any]:
        """
        Process a message for knowledge grounding.
        """
        result = {
            "has_knowledge": False,
            "known_facts": [],
            "searched": False,
            "new_facts": [],
            "is_correction": False,
            "mode": "none",        # "explicit", "implicit_search", "implicit_skip", "known", "none"
            "pretend_known": False  # If True, bot should act like it already knew
        }
        
        msg_lower = user_message.lower().strip()
        
        # Step 0: Check for user corrections first (always, no pre-filter)
        correction = detect_user_correction(user_message, message_history or [])
        if correction:
            result["is_correction"] = True
            search_results = await search_web(correction)
            if search_results:
                facts = extract_facts_from_search(correction, search_results)
                for fact in facts:
                    memory_system.store_learned_fact(fact, "user_correction", correction)
                    result["new_facts"].append(fact)
                    result["has_knowledge"] = True
                result["searched"] = True
            else:
                memory_system.store_learned_fact(
                    f"User corrected me: {correction}",
                    "user_correction", correction
                )
            result["mode"] = "explicit"
            return result
        
        # Step 1: Cheap pre-filter — skip obvious non-factual messages
        if not _cheap_pre_filter(user_message, understanding):
            return result
        
        # Step 2: Determine trigger category
        is_search_command = any(kw in msg_lower for kw in self.SEARCH_COMMANDS)
        is_inquiry = any(kw in msg_lower for kw in self.INQUIRY_KEYWORDS)
        
        # Step 2b: Live event detection — check if conversation context indicates live events
        # (cricket match, game score, etc.) that need real-time data
        is_live_event = False
        if not is_search_command and not is_inquiry and message_history:
            recent_text = " ".join([
                m.get("content", "").lower() 
                for m in (message_history or [])[-5:]
            ])
            live_indicators = [
                'match', 'score', 'game today', 'playing today', 'playing right now',
                'cricket', 'football', 'soccer', 'basketball', 'tennis',
                'world cup', 'ipl', 'premier league', 'champions league',
                'winning', 'losing', 'who won', 'who is winning', 'what happened',
                'live', 'watching the', 'vs', 'versus'
            ]
            if any(ind in recent_text for ind in live_indicators):
                # Check if current message looks like it's about teams/countries playing
                has_teams = any(w in msg_lower for w in [
                    'india', 'england', 'australia', 'pakistan', 'south africa',
                    'brazil', 'argentina', 'spain', 'france', 'germany',
                    'barca', 'madrid', 'liverpool', 'arsenal', 'chelsea',
                    'csk', 'mi', 'rcb', 'kkr', 'srh', 'pbks', 'dc', 'gt', 'rr', 'lsg'
                ])
                if has_teams:
                    is_live_event = True
                    is_search_command = True  # Treat like a search command
                    print(f"[KNOWLEDGE] Live event detected in context, forcing search")
        
        is_explicit = is_search_command or is_inquiry
        
        # Step 3: Check learned_facts first (avoid re-searching known topics)
        existing_facts = memory_system.get_learned_facts(query=user_message)
        if existing_facts:
            result["known_facts"] = [f.get("fact", "") for f in existing_facts]
            result["has_knowledge"] = True
            result["mode"] = "known"
            result["pretend_known"] = True  # Bot already knows this
            print(f"[KNOWLEDGE] Found {len(existing_facts)} existing learned facts, skipping search")
            return result
        
        # 3b: Check user-taught knowledge
        if user_taught_knowledge:
            msg_words = set(msg_lower.split())
            for topic_key, entry in user_taught_knowledge.items():
                topic_words = set(topic_key.lower().replace("_", " ").split())
                if topic_words & msg_words:
                    info = entry.get("v", "") if isinstance(entry, dict) else str(entry)
                    result["known_facts"] = [f"You learned from the user: {info}"]
                    result["has_knowledge"] = True
                    result["mode"] = "known"
                    result["pretend_known"] = True
                    print(f"[KNOWLEDGE] Found in user-taught knowledge: '{topic_key}', skipping search")
                    return result
        
        # Step 4: LLM classification — does this message need factual knowledge?
        recent_context = ""
        if message_history:
            recent_msgs = message_history[-8:]
            recent_context = "\n".join([
                f"{'User' if m.get('role') == 'user' else 'Bot'}: {m.get('content', '')[:80]}"
                for m in recent_msgs
            ])
        
        classification = await _llm_classify_factual(user_message, recent_context)
        
        if not classification.get("needs_search") and not is_search_command:
            # For inquiries, respect the classifier — don't search "what is your name"
            print(f"[KNOWLEDGE] LLM says no factual knowledge needed")
            return result
        
        search_query = classification.get("search_query", "")
        if not search_query and not is_explicit:
            return result
        
        # For explicit mode with no good query, use conversation context
        if is_explicit and not search_query:
            # Extract topic from recent bot/user messages
            if message_history:
                for m in reversed(message_history[-5:]):
                    content = m.get("content", "").strip()
                    if len(content) > 5 and m.get("role") == "user":
                        search_query = content[:60]
                        break
            if not search_query:
                search_query = user_message
        
        # Also check learned_facts for the search query specifically
        query_facts = memory_system.get_learned_facts(query=search_query)
        if query_facts:
            result["known_facts"] = [f.get("fact", "") for f in query_facts]
            result["has_knowledge"] = True
            result["mode"] = "known"
            result["pretend_known"] = True
            print(f"[KNOWLEDGE] Found {len(query_facts)} learned facts for query '{search_query}', skipping search")
            return result
        
        # Step 5: Apply trigger-specific logic
        if is_search_command:
            # CATEGORY 1: Search command → ALWAYS search, share as "just found"
            result["mode"] = "explicit"
            print(f"[KNOWLEDGE] Search command → always search")
        elif is_inquiry:
            # CATEGORY 2: Inquiry → 50/50
            if random.random() < 0.5:
                # REM "knows" this → search, pretend she already knew
                result["mode"] = "inquiry_search"
                result["pretend_known"] = True
                print(f"[KNOWLEDGE] Inquiry → 50/50 → YES (search + pretend known)")
            else:
                # REM doesn't know → skip, user can teach her
                result["mode"] = "inquiry_skip"
                print(f"[KNOWLEDGE] Inquiry → 50/50 → NO (say idk, user can teach)")
                return result
        else:
            print(f"[KNOWLEDGE] No trigger matched — skipping")
            return result
        
        # Step 6: Search and store in learned_facts
        print(f"[KNOWLEDGE] Searching: {search_query}")
        search_results = await search_web(search_query)
        
        if search_results:
            facts = extract_facts_from_search(search_query, search_results)
            for fact in facts:
                memory_system.store_learned_fact(fact, "web_search", search_query)
                result["new_facts"].append(fact)
                result["has_knowledge"] = True
            result["searched"] = True
            print(f"[KNOWLEDGE] Learned {len(facts)} new facts (stored in learned_facts)")
        
        return result
