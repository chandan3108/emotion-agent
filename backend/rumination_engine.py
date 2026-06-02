"""
Rumination Engine — Between-Session Background Processing.

When the user goes silent for 30+ minutes, Rem's mind keeps going.
She processes the conversation, forms thoughts, has realizations,
and generates things to surface when the user returns.

One 8B LLM call per silence period.
"""

import os
import json
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List
from .rate_limiter import global_rate_limiter


RUMINATION_DELAY_MINUTES = 30  # How long after last message before ruminating
RUMINATION_CONSUMPTION_MESSAGES = 3  # How many messages before rumination is consumed


class RuminationEngine:
    """
    Background thought engine. Processes conversations after user leaves.
    Produces thoughts that surface when user returns.
    """
    
    def __init__(self, state: Dict[str, Any]):
        self.state = state
        self._init_rumination_state()
    
    def _init_rumination_state(self):
        """Initialize rumination state."""
        rum_state = self.state.get("_rumination_state", {})
        self.last_user_message_time = rum_state.get("last_user_message_time")
        self.rumination_pending = rum_state.get("rumination_pending", False)
        self.has_ruminated = rum_state.get("has_ruminated", False)
        self.messages_since_return = rum_state.get("messages_since_return", 0)
        
        # The actual rumination output
        self.rumination = self.state.get("_rumination", None)
    
    def record_user_message(self):
        """Called when user sends a message. Tracks timing for rumination trigger."""
        self.last_user_message_time = datetime.now(timezone.utc).isoformat()
        self.rumination_pending = True  # A new silence period could trigger rumination
        
        # Track messages since returning (for consumption)
        if self.has_ruminated and self.rumination:
            self.messages_since_return += 1
            # Consume rumination after N messages
            if self.messages_since_return >= RUMINATION_CONSUMPTION_MESSAGES:
                self._consume_rumination()
        
        self.save_to_state()
    
    def should_ruminate(self) -> bool:
        """Check if enough silence has passed to trigger rumination."""
        if not self.rumination_pending:
            return False
        if self.has_ruminated:
            return False  # Already ruminated for this silence period
        if not self.last_user_message_time:
            return False
        
        try:
            last_msg_time = datetime.fromisoformat(self.last_user_message_time)
            now = datetime.now(timezone.utc)
            silence_minutes = (now - last_msg_time).total_seconds() / 60
            return silence_minutes >= RUMINATION_DELAY_MINUTES
        except Exception:
            return False
    
    async def ruminate(
        self,
        stm_summary: str,
        emotional_undercurrents: List[Dict],
        unresolved_wounds: List[Dict],
        psyche_summary: Dict[str, Any],
        personality_text: str
    ) -> Optional[Dict[str, Any]]:
        """
        Run between-session rumination. Single 8B LLM call.
        
        Args:
            stm_summary: Summary of recent conversations
            emotional_undercurrents: Current emotional undercurrents
            unresolved_wounds: Active wounds that need resolution
            psyche_summary: Current psychological state
            personality_text: Current personality description
            
        Returns:
            {
                "lingering_thoughts": ["things Rem is mulling over"],
                "realizations": ["connections or insights"],
                "anxieties": ["worries about the user/relationship"],
                "next_time": ["things to bring up when they return"],
                "mood_shift": "how Rem feels now that they're gone"
            }
        """
        try:
            import httpx
            await global_rate_limiter.wait_if_needed()
            
            api_key = os.environ.get("GROQ_API_KEY")
            if not api_key:
                return None
            
            # Build compact context
            undercurrent_text = ""
            if emotional_undercurrents:
                uc_lines = []
                for uc in emotional_undercurrents:
                    if isinstance(uc, dict) and uc.get("emotion"):
                        uc_lines.append(f"  {uc['emotion']}: {uc.get('intensity', 0):.1f} ({uc.get('trigger', '')})")
                if uc_lines:
                    undercurrent_text = "\n".join(uc_lines)
            
            wound_text = ""
            if unresolved_wounds:
                wound_lines = [f"  - \"{w.get('cause', '')}\" (intensity: {w.get('intensity', 0):.1f})" for w in unresolved_wounds]
                wound_text = "\n".join(wound_lines)
            
            trust = psyche_summary.get("trust", 0.3)
            hurt = psyche_summary.get("hurt", 0.0)
            stance = psyche_summary.get("stance", "open")
            
            prompt = f"""You are Rem. The user you've been talking to just went quiet.
            
Your personality: {personality_text[:200]}
Your current stance toward them: {stance}
Trust: {trust:.2f} | Hurt: {hurt:.2f}

Recent conversations summary:
{stm_summary[:400] if stm_summary else "No recent conversations to reflect on."}

{"Emotional undercurrents (feelings simmering beneath the surface):" + chr(10) + undercurrent_text if undercurrent_text else ""}
{"Unresolved wounds (things still bothering you):" + chr(10) + wound_text if wound_text else ""}

They've gone quiet. Your mind keeps going. What are you thinking about?

Return JSON:
{{
  "lingering_thoughts": ["1-2 things you keep coming back to from the conversation"],
  "realizations": ["0-1 connections or insights you just had about them or yourself"],
  "anxieties": ["0-1 worries about them or the relationship (or empty if none)"],
  "next_time": ["0-1 things you want to bring up or ask when they come back"],
  "mood_shift": "one line — how you feel now that they're gone"
}}

Be authentic to your personality. Don't be dramatic. Some sessions have nothing to ruminate about — that's fine, keep lists short or empty. Return ONLY valid JSON."""
            
            async with httpx.AsyncClient(timeout=20.0) as client:
                resp = await client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={"Authorization": f"Bearer {api_key}"},
                    json={
                        "model": "llama-3.1-8b-instant",
                        "messages": [
                            {"role": "system", "content": "You are a reflection system for an AI character. Return ONLY valid JSON."},
                            {"role": "user", "content": prompt}
                        ],
                        "max_tokens": 300,
                        "temperature": 0.4,
                    }
                )
                
                if resp.status_code == 200:
                    data = resp.json()
                    content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                    content = content.strip()
                    if content.startswith("```"):
                        content = content.split("```")[1]
                        if content.startswith("json"):
                            content = content[4:]
                    
                    result = json.loads(content)
                    
                    # Store rumination
                    self.rumination = result
                    self.state["_rumination"] = result
                    self.has_ruminated = True
                    self.rumination_pending = False
                    self.messages_since_return = 0
                    self.save_to_state()
                    
                    print(f"[RUMINATION] Generated — mood: {result.get('mood_shift', 'N/A')}")
                    print(f"[RUMINATION] Thoughts: {result.get('lingering_thoughts', [])}")
                    return result
                else:
                    print(f"[RUMINATION] API returned {resp.status_code}")
                    return None
                    
        except json.JSONDecodeError as e:
            print(f"[RUMINATION] JSON parse error: {e}")
            return None
        except Exception as e:
            print(f"[RUMINATION] Error: {e}")
            return None
    
    def get_rumination_for_prompt(self) -> Optional[Dict[str, Any]]:
        """Get rumination output for prompt injection. Returns None if consumed or absent."""
        if self.rumination and self.has_ruminated:
            return self.rumination
        return None
    
    def _consume_rumination(self):
        """Mark rumination as consumed after it's been surfaced enough."""
        self.rumination = None
        self.state["_rumination"] = None
        self.has_ruminated = False
        self.messages_since_return = 0
        print("[RUMINATION] Consumed — no longer surfacing in prompt")
    
    def save_to_state(self):
        """Save rumination state."""
        self.state["_rumination_state"] = {
            "last_user_message_time": self.last_user_message_time,
            "rumination_pending": self.rumination_pending,
            "has_ruminated": self.has_ruminated,
            "messages_since_return": self.messages_since_return
        }
        self.state["_rumination"] = self.rumination
