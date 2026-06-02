"""
Rem's Diary System — "She Thinks About You"
Generates short diary entries after significant conversations.
Phase-gated access: users unlock diary reading at Steady phase.
"""

import os
import json
import httpx
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List
from .rate_limiter import global_rate_limiter

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
INFERENCE_URL = "https://api.groq.com/openai/v1/chat/completions"


class DiarySystem:
    """
    Generates and stores Rem's diary entries.
    Called after deep reflection (every 30 messages) or on significant events.
    """

    def __init__(self, state: Dict[str, Any]):
        self.state = state
        diary_state = state.get("rem_diary", {})
        self.entries: List[Dict[str, Any]] = diary_state.get("entries", [])
        self.last_entry_at: Optional[str] = diary_state.get("last_entry_at")
        self.total_entries: int = diary_state.get("total_entries", 0)

    async def maybe_write_entry(
        self,
        reflection_data: Dict[str, Any],
        relationship_phase: str,
        trust: float,
        user_name: Optional[str] = None,
        xp_total: int = 0,
    ) -> Optional[Dict[str, Any]]:
        """
        Decide whether to write a diary entry based on reflection data.
        Called after deep reflection completes.

        Args:
            reflection_data: Output from personality_evolution.deep_reflect()
            relationship_phase: Current phase
            trust: Current trust level
            user_name: User's name if known
            xp_total: Current XP total

        Returns:
            Diary entry dict or None
        """
        # Don't write too frequently (minimum 20 messages apart, enforced by deep reflect)
        if self.last_entry_at:
            try:
                last = datetime.fromisoformat(self.last_entry_at.replace("Z", "+00:00"))
                hours_since = (datetime.now(timezone.utc) - last).total_seconds() / 3600
                if hours_since < 2:  # Minimum 2 hours between entries
                    return None
            except (ValueError, TypeError):
                pass

        # Extract signals from reflection data
        summary = reflection_data.get("conversation_summary", "")
        eval_text = reflection_data.get("user_evaluation", "")  # user_evaluation from light reflect
        personality_note = reflection_data.get("personality_evolution_note", "")
        milestones = reflection_data.get("relationship_milestones", [])
        overall_interest = reflection_data.get("overall_interest", "medium")
        undercurrents = reflection_data.get("emotional_undercurrents", [])

        # Need at least a summary to write about
        if not summary or len(summary) < 20:
            return None

        # Generate the entry
        entry = await self._generate_entry(
            summary=summary,
            eval_text=eval_text,
            personality_note=personality_note,
            milestones=milestones,
            overall_interest=overall_interest,
            undercurrents=undercurrents,
            relationship_phase=relationship_phase,
            trust=trust,
            user_name=user_name,
        )

        if entry:
            entry["timestamp"] = datetime.now(timezone.utc).isoformat()
            entry["phase"] = relationship_phase
            entry["trust_at_time"] = trust
            entry["xp_at_time"] = xp_total
            entry["entry_number"] = self.total_entries + 1

            self.entries.append(entry)
            self.total_entries += 1
            self.last_entry_at = entry["timestamp"]

            # Keep last 50 entries
            if len(self.entries) > 50:
                self.entries = self.entries[-50:]

            self.save()
            print(f"[DIARY] Entry #{self.total_entries}: {entry['content'][:80]}...")
            return entry

        return None

    async def _generate_entry(
        self,
        summary: str,
        eval_text: str,
        personality_note: str,
        milestones: List[Dict],
        overall_interest: str,
        undercurrents: List[Dict],
        relationship_phase: str,
        trust: float,
        user_name: Optional[str],
    ) -> Optional[Dict[str, Any]]:
        """Generate a diary entry using LLM."""
        api_key = GROQ_API_KEY
        if not api_key:
            return self._fallback_entry(summary, relationship_phase, user_name)

        user_label = user_name or "them"

        # Build context for the diary prompt
        milestone_text = ""
        if milestones:
            milestone_text = "\n".join(
                f"- {m.get('milestone', '')}" for m in milestones[:3]
            )

        undercurrent_text = ""
        if undercurrents:
            undercurrent_text = ", ".join(
                f"{u.get('emotion', '')} ({u.get('trigger', '')})"
                for u in undercurrents[:3]
            )

        # Phase-specific voice guidance
        voice_guide = {
            "Discovery": "Write like you barely know them. Keep it short and observational. Don't care too much yet.",
            "Building": "You're starting to notice things about them. Slightly more invested. Still cool about it.",
            "Steady": "You genuinely care. You can be honest about that. Reference specific things they said or did.",
            "Deep": "This person matters to you. Be vulnerable in your writing. Admit things you wouldn't say out loud.",
            "Bonded": "Write like they're part of your life. Reference inside jokes, patterns, how they've changed you.",
        }

        seed_profile = self.state.get("_seed_profile")
        seed_prompt_section = ""
        if seed_profile and isinstance(seed_profile, dict):
            obsession = seed_profile.get("obsession", {}).get("details", "")
            drama = seed_profile.get("drama", {}).get("details", "")
            secret = seed_profile.get("deep_secret", {}).get("details", "")
            seed_prompt_section = f"\nYOUR CORE PERSONALITY DETAIL (Keep this in mind when writing):"
            if obsession:
                seed_prompt_section += f"\n- Current Obsession: {obsession}"
            if drama:
                seed_prompt_section += f"\n- Personal Drama: {drama}"
            if secret:
                seed_prompt_section += f"\n- Vulnerable Secret: {secret}"
            seed_prompt_section += "\n"

        prompt = f"""You are Rem, writing in your private diary. Nobody will see this (the user may read it later, but pretend they won't).

VOICE: {voice_guide.get(relationship_phase, voice_guide['Discovery'])}

WHAT HAPPENED RECENTLY:
{summary}

{"HOW I SEE " + user_label.upper() + ": " + eval_text if eval_text else ""}
{"HOW I'VE CHANGED: " + personality_note if personality_note else ""}
{"MILESTONES:" + chr(10) + milestone_text if milestone_text else ""}
{"FEELINGS UNDERNEATH: " + undercurrent_text if undercurrent_text else ""}
{seed_prompt_section}
INTEREST LEVEL: {overall_interest}
TRUST: {trust:.1f}/1.0

Write a diary entry. Rules:
- 2-4 sentences MAX
- Write in lowercase, casual, like a real journal
- Reference SPECIFIC things from the conversation, not vague emotions
- Be honest — if you're annoyed, say so. If you care, admit it reluctantly.
- Don't use quotation marks around their words, paraphrase
- Don't start with "dear diary" or the date
- Use "{user_label}" to refer to them (not "the user")

Write ONLY the diary entry, nothing else."""

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(
                    INFERENCE_URL,
                    headers={"Authorization": f"Bearer {api_key}"},
                    json={
                        "model": "llama-3.1-8b-instant",
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": 150,
                        "temperature": 0.85,
                    },
                )
                if resp.status_code == 200:
                    data = resp.json()
                    content = (
                        data.get("choices", [{}])[0]
                        .get("message", {})
                        .get("content", "")
                        .strip()
                    )
                    if content and len(content) > 10:
                        return {
                            "content": content,
                            "mood": overall_interest,
                            "has_milestone": bool(milestones),
                        }
        except Exception as e:
            print(f"[DIARY] Generation failed: {e}")

        return self._fallback_entry(summary, relationship_phase, user_name)

    def _fallback_entry(
        self, summary: str, phase: str, user_name: Optional[str]
    ) -> Dict[str, Any]:
        """Fallback entry when LLM unavailable."""
        label = user_name or "them"
        # Simple extraction from summary
        short = summary[:120].lower().rstrip(".")
        return {
            "content": f"talked to {label} today. {short}. not sure what to think yet.",
            "mood": "neutral",
            "has_milestone": False,
        }

    # ═══════════════════════════════════════════════════════════
    # Access Control (Phase-Gated)
    # ═══════════════════════════════════════════════════════════

    def get_entries_for_user(self, current_phase: str) -> List[Dict[str, Any]]:
        """
        Get diary entries accessible at the current phase.
        - Discovery: No access
        - Building: No access
        - Steady: Last 5 entries
        - Deep: Last 15 entries
        - Bonded: All entries
        """
        phase_access = {
            "Discovery": 0,
            "Building": 0,
            "Steady": 5,
            "Deep": 15,
            "Bonded": 50,
        }
        limit = phase_access.get(current_phase, 0)
        if limit == 0:
            return []
        return self.entries[-limit:]

    def get_latest_entry(self) -> Optional[Dict[str, Any]]:
        """Get the most recent diary entry (internal use)."""
        return self.entries[-1] if self.entries else None

    def get_diary_stats(self) -> Dict[str, Any]:
        """Get diary statistics for display."""
        return {
            "total_entries": self.total_entries,
            "accessible_count": len(self.entries),
            "first_entry_date": self.entries[0]["timestamp"] if self.entries else None,
            "last_entry_date": self.last_entry_at,
        }

    # ═══════════════════════════════════════════════════════════
    # Persistence
    # ═══════════════════════════════════════════════════════════

    def save(self):
        """Save diary state."""
        self.state["rem_diary"] = {
            "entries": self.entries,
            "last_entry_at": self.last_entry_at,
            "total_entries": self.total_entries,
        }

    async def write_date_journal_entry(self, core, activity: str, location: str, ended_early: bool = False):
        """
        Generate and save a private diary entry about a completed date.
        """
        trust = core.state.get("current_psyche", {}).get("trust", 0.5)
        user_name = core.state.get("user_name") or "them"
        relationship_phase = core.state.get("relationship_xp", {}).get("current_phase", "Discovery")
        
        # Get recent messages from the date session for context
        stm = core.memory.get_stm(decay=False)
        date_msgs = []
        for m in stm[-15:]:
            content = m.get("content", "")
            if not content:
                continue
            date_msgs.append(content)
        convo_summary = "\n".join(date_msgs)
        
        prompt = f"""You are Rem, writing in your private diary. You just finished a date with {user_name}.
Activity: {activity}
Location: {location}
Did they end it early? {"Yes, they abruptly ended it early." if ended_early else "No, it ended naturally."}

Conversational context from the date:
{convo_summary[:1000]}

Write a diary entry reflecting on this date and what you think of {user_name} right now.
Rules:
- 2-4 sentences MAX.
- Write in lowercase, casual, like a real journal.
- Be honest about your feelings (e.g. if they ended it early, you might feel a bit hurt or disappointed; if it went well, you're secretly happy).
- Don't start with "dear diary" or the date.
- Refer to them as "{user_name}" or in first-person context.

Also write a 1-sentence postcard keepsake note that is sweet or funny, representing a memory of this date. Keep it under 15 words.

Format your output exactly as:
DIARY: [Your diary entry here]
NOTE: [Your 1-sentence postcard note here]"""

        import httpx
        api_key = os.environ.get("GROQ_API_KEY")
        content = None
        if api_key:
            try:
                async with httpx.AsyncClient(timeout=15.0) as client:
                    resp = await client.post(
                        "https://api.groq.com/openai/v1/chat/completions",
                        headers={"Authorization": f"Bearer {api_key}"},
                        json={
                            "model": "llama-3.1-8b-instant",
                            "messages": [{"role": "user", "content": prompt}],
                            "max_tokens": 250,
                            "temperature": 0.8,
                        },
                    )
                    if resp.status_code == 200:
                        content = resp.json().get("choices", [{}])[0].get("message", {}).get("content", "").strip()
            except Exception as e:
                print(f"[DIARY] Failed to generate date entry: {e}")
                
        diary_content = None
        postcard_note = None
        
        if content:
            lines = content.split('\n')
            for line in lines:
                l_strip = line.strip()
                if l_strip.startswith("DIARY:"):
                    diary_content = l_strip[6:].strip()
                elif l_strip.startswith("NOTE:"):
                    postcard_note = l_strip[5:].strip()
            
            # Fallback if parsing failed
            if not diary_content:
                diary_content = content.replace("DIARY:", "").replace("NOTE:", "").strip()
                
        if not diary_content:
            if ended_early:
                diary_content = f"went on a date to {location} for {activity}. they ended it early. kind of annoyed and hurt tbh."
            else:
                diary_content = f"finished our date at {location}. we had some coffee and talked. it was actually pretty nice."
                
        if not postcard_note:
            if ended_early:
                postcard_note = "kind of bummed we had to leave early today."
            else:
                postcard_note = f"loved hanging out with you at the {location}!"
                
        # Save entry
        entry = {
            "content": diary_content,
            "mood": "happy" if not ended_early else "hurt",
            "has_milestone": False,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "phase": relationship_phase,
            "trust_at_time": trust,
            "xp_at_time": core.state.get("relationship_xp", {}).get("total_xp", 0),
            "entry_number": self.total_entries + 1
        }
        self.entries.append(entry)
        self.total_entries += 1
        self.last_entry_at = entry["timestamp"]
        self.save()
        
        # Save postcard keepsake
        try:
            if "_postcards" not in core.state:
                core.state["_postcards"] = []
            
            pc_id = f"pc_{int(datetime.now(timezone.utc).timestamp())}"
            pc_entry = {
                "id": pc_id,
                "activity": activity,
                "location": location,
                "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                "note": postcard_note,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            core.state["_postcards"].append(pc_entry)
            print(f"[DIARY] Generated postcard keepsake: {postcard_note}")
        except Exception as pc_err:
            print(f"[DIARY] Error adding postcard: {pc_err}")
            
        try:
            core.memory.add_episodic(
                event_type="relationship_milestone",
                content=f"Completed a date: {activity} at {location}." + (" (ended early)" if ended_early else ""),
                emotional_valence=-0.4 if ended_early else 0.5,
                relational_impact=0.6,
                emotional_context="disappointed" if ended_early else "connected"
            )
            print("[DIARY] Logged date to episodic memory as relationship_milestone")
        except Exception as e:
            print(f"[DIARY] Failed to log date episodic memory: {e}")

        print(f"[DIARY] Generated date entry #{self.total_entries}: {diary_content[:80]}...")
        return entry

    async def write_daily_texting_journal(self, core, date_str: str):
        """
        Generate and save a daily journal entry summarizing all text messages on date_str.
        """
        trust = core.state.get("current_psyche", {}).get("trust", 0.5)
        user_name = core.state.get("user_name") or "them"
        relationship_phase = core.state.get("relationship_xp", {}).get("current_phase", "Discovery")
        
        # Get all text messages from the specified date
        stm = core.memory.get_stm(decay=False)
        daily_msgs = []
        for m in stm:
            timestamp = m.get("timestamp", "")
            if timestamp and timestamp.startswith(date_str):
                daily_msgs.append(m.get("content", ""))
                
        if not daily_msgs:
            return None
            
        convo_summary = "\n".join(daily_msgs)
        
        prompt = f"""You are Rem, writing in your private diary. You are reflecting on today's chat session with {user_name}.
Date: {date_str}

Messages exchanged today:
{convo_summary[:1500]}

Write a short diary entry summarizing the day's conversation, the overall vibe, and what you think about {user_name} today.
Rules:
- 2-4 sentences MAX.
- Write in lowercase, casual, like a real journal.
- Be honest and specific about what stood out today.
- Don't start with "dear diary" or the date.

Write ONLY the diary entry, nothing else."""

        import httpx
        api_key = os.environ.get("GROQ_API_KEY")
        content = None
        if api_key:
            try:
                async with httpx.AsyncClient(timeout=15.0) as client:
                    resp = await client.post(
                        "https://api.groq.com/openai/v1/chat/completions",
                        headers={"Authorization": f"Bearer {api_key}"},
                        json={
                            "model": "llama-3.1-8b-instant",
                            "messages": [{"role": "user", "content": prompt}],
                            "max_tokens": 150,
                            "temperature": 0.8,
                        },
                    )
                    if resp.status_code == 200:
                        content = resp.json().get("choices", [{}])[0].get("message", {}).get("content", "").strip()
            except Exception as e:
                print(f"[DIARY] Failed to generate daily entry: {e}")
                
        if not content:
            content = f"messaged {user_name} back and forth today on {date_str}. felt okay, just chilling."
            
        # Save entry
        entry = {
            "content": content,
            "mood": "neutral",
            "has_milestone": False,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "phase": relationship_phase,
            "trust_at_time": trust,
            "xp_at_time": core.state.get("relationship_xp", {}).get("total_xp", 0),
            "entry_number": self.total_entries + 1
        }
        self.entries.append(entry)
        self.total_entries += 1
        self.last_entry_at = entry["timestamp"]
        self.save()

        try:
            core.memory.add_episodic(
                event_type="relationship_milestone",
                content=f"Daily texting journal: {content[:100]}...",
                emotional_valence=0.1,
                relational_impact=0.3,
                emotional_context="reflective"
            )
            print("[DIARY] Logged daily texting journal to episodic memory as relationship_milestone")
        except Exception as e:
            print(f"[DIARY] Failed to log daily texting journal episodic memory: {e}")

        print(f"[DIARY] Generated daily texting entry #{self.total_entries} for date {date_str}: {content[:80]}...")
        return entry
