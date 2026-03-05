"""
Daily Life Simulator — Generates REM's daily schedule using LLM.

One LLM call per day (cheap 8B model). Stored in state.
Provides consistent "what am I doing right now" context for the system prompt.

The schedule is a LOOSE PLAN — it can be overridden when:
- The user makes plans with REM (e.g., "let's talk at 9")
- REM is actively chatting (conversation overrides scheduled activity)
"""

import os
import json
import httpx
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List

# IST timezone (UTC+5:30)
IST = timezone(timedelta(hours=5, minutes=30))


GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
INFERENCE_URL = "https://api.groq.com/openai/v1/chat/completions"
SCHEDULE_MODEL = "llama-3.1-8b-instant"  # Cheap model for schedule generation

# REM's core identity — these anchor the schedule
REM_IDENTITY = {
    "occupation": "college student",
    "major": "psychology",
    "living": "lives at home",
    "commute": "about 30 min commute to college",
}

# Weekday college anchor — only this is fixed
WEEKDAY_COLLEGE = {"start": "08:30", "end": "13:00", "activity": "at college, psychology classes"}


def _get_schedule_prompt(day_of_week: str, mood: Dict[str, float], is_weekend: bool, upcoming_events: list = None) -> str:
    """Build the prompt for daily schedule generation."""
    
    anchor_text = ""
    if not is_weekend:
        anchor_text = f"""
FIXED ANCHOR (do NOT override):
- 08:30 to 13:00: She's at college, psychology classes. Add details about what she's doing there but she IS at college during this time.
- Include commute to and from college (~30 min each way)."""
    else:
        anchor_text = "\nIt's the weekend — no college. She could sleep in, go out, or do nothing all day."
    
    # Pass raw mood values — let the LLM interpret them naturally
    mood_block = "\n".join(f"  {k}: {v:.2f}" for k, v in mood.items()) if mood else "  unknown"
    
    # Upcoming events from conversation
    events_block = ""
    if upcoming_events:
        events_text = "\n".join(
            f"  - {e.get('event', '?')} ({e.get('when', '?')}) — {e.get('impact', '')}"
            for e in upcoming_events
        )
        events_block = f"""\n\nUPCOMING EVENTS (mentioned in recent conversations — incorporate these into the schedule):
{events_text}
If an event is TODAY, it MUST appear in the schedule. Adjust other activities around it realistically.
If an event is tomorrow or later, it might affect today's mood/prep (e.g., studying the night before an exam)."""
    
    return f"""You are generating a realistic daily schedule for a 20-year-old college girl named Rem who lives at home.

Today is {day_of_week}.
{anchor_text}

Her current emotional state (0-1 scale):
{mood_block}{events_block}

Use her emotional state to naturally influence what kind of day she has — you decide how.
Some days are active, some are lazy. Some have spontaneous plans, some don't. Be unpredictable.

Rules:
- REALISTIC and MESSY — real 20-year-olds have lots of dead time, phone scrolling, and unplanned hours
- NOT a productivity schedule — she's a person, not a planner
- Include spontaneous stuff sometimes (random errands, going out with a friend, binge-watching, snack runs)
- Transitions matter (getting ready, commute, settling in, winding down)
- Vague activities are fine ("in my room", "doing nothing", "scrolling")
- Cover roughly 06:00 to 02:00 (sleeps ~02:00 to 07:00-ish, varies)
- Activity descriptions should be SHORT and casual — how a real person describes their day (under 10 words)
- Make it feel like a REAL, slightly chaotic human day

Output ONLY a valid JSON array, no other text:
[{{"start": "HH:MM", "end": "HH:MM", "activity": "short casual description"}}]"""


async def generate_daily_schedule(state: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    Generate REM's daily schedule. Called once per day.
    Uses cheap 8B model (~500 tokens total).
    """
    now = datetime.now(IST)
    day_of_week = now.strftime("%A")
    is_weekend = day_of_week in ("Saturday", "Sunday")
    
    # Pass raw mood values directly to the LLM
    mood = state.get("mood", {})
    
    # Get upcoming events (synced from personality_evolution by cognitive_core)
    upcoming_events = state.get("_upcoming_events", [])
    
    # Auto-expire events older than 7 days
    if upcoming_events:
        now = datetime.now(IST)
        valid_events = []
        for evt in upcoming_events:
            added_at = evt.get("added_at", "")
            if added_at:
                try:
                    evt_time = datetime.fromisoformat(added_at.replace("Z", "+00:00"))
                    age_days = (now - evt_time.astimezone(IST)).days
                    if age_days <= 7:
                        valid_events.append(evt)
                    else:
                        print(f"[DAILY LIFE] Expired event: {evt.get('event')} (added {age_days} days ago)")
                except Exception:
                    valid_events.append(evt)  # Keep if can't parse date
            else:
                valid_events.append(evt)
        upcoming_events = valid_events
        # Write back cleaned events
        state["_upcoming_events"] = valid_events
    
    prompt = _get_schedule_prompt(day_of_week, mood, is_weekend, upcoming_events)
    
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                INFERENCE_URL,
                headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
                json={
                    "model": SCHEDULE_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 700,
                    "temperature": 1.0,  # Max variety — every day is different
                },
            )
            
            if resp.status_code >= 400:
                print(f"[DAILY LIFE] Schedule generation failed: {resp.status_code}")
                return _fallback_schedule(is_weekend)
            
            data = resp.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
            
            # Parse JSON from response (handle markdown code blocks)
            if "```" in content:
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
                content = content.strip()
            
            schedule = json.loads(content)
            
            if not isinstance(schedule, list) or len(schedule) < 3:
                print(f"[DAILY LIFE] Invalid schedule format, using fallback")
                return _fallback_schedule(is_weekend)
            
            # Log the generated schedule
            print(f"[DAILY LIFE] Generated {len(schedule)}-block schedule for {day_of_week}:")
            for block in schedule:
                print(f"  {block.get('start','??')}-{block.get('end','??')}: {block.get('activity','?')}")
            
            return schedule
            
    except json.JSONDecodeError as e:
        print(f"[DAILY LIFE] JSON parse error: {e}")
        return _fallback_schedule(is_weekend)
    except Exception as e:
        print(f"[DAILY LIFE] Schedule generation error: {e}")
        return _fallback_schedule(is_weekend)


def _fallback_schedule(is_weekend: bool) -> List[Dict[str, str]]:
    """Fallback schedule if LLM fails. Minimal and vague."""
    if is_weekend:
        return [
            {"start": "06:00", "end": "10:00", "activity": "sleeping in"},
            {"start": "10:00", "end": "12:00", "activity": "woke up, being lazy"},
            {"start": "12:00", "end": "15:00", "activity": "just chilling at home"},
            {"start": "15:00", "end": "18:00", "activity": "doing random stuff"},
            {"start": "18:00", "end": "21:00", "activity": "evening, relaxing"},
            {"start": "21:00", "end": "02:00", "activity": "in my room, winding down"},
        ]
    else:
        return [
            {"start": "06:00", "end": "07:30", "activity": "sleeping"},
            {"start": "07:30", "end": "08:30", "activity": "getting ready for college"},
            {"start": "08:30", "end": "13:00", "activity": "at college"},
            {"start": "13:00", "end": "14:00", "activity": "heading home"},
            {"start": "14:00", "end": "17:00", "activity": "home, just chilling"},
            {"start": "17:00", "end": "20:00", "activity": "doing nothing productive"},
            {"start": "20:00", "end": "22:00", "activity": "in my room, relaxing"},
            {"start": "22:00", "end": "02:00", "activity": "in bed, scrolling"},
        ]


def get_current_activity(state: Dict[str, Any]) -> str:
    """
    Get REM's current activity from today's schedule.
    Checks for overrides first, then falls back to scheduled activity.
    """
    schedule_data = state.get("_daily_schedule", {})
    
    # Check for overrides (plans made with user)
    overrides = schedule_data.get("overrides", [])
    now = datetime.now(IST)
    current_time = now.strftime("%H:%M")
    
    for override in overrides:
        start = override.get("start", "")
        end = override.get("end", "")
        if start <= current_time < end:
            return override.get("activity", "")
    
    # Normal schedule lookup
    schedule = schedule_data.get("schedule", [])
    if not schedule:
        return ""
    
    for block in schedule:
        start = block.get("start", "00:00")
        end = block.get("end", "23:59")
        
        # Handle midnight rollover (e.g., 23:00 → 02:00)
        if end < start:
            # Block crosses midnight
            if current_time >= start or current_time < end:
                return block.get("activity", "just chilling")
        else:
            if start <= current_time < end:
                return block.get("activity", "just chilling")
    
    # If between 02:00-06:00, assume sleeping
    if 2 <= now.hour < 6:
        return "sleeping"
    
    return "just chilling"


def get_upcoming_activities(state: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    Get current activity + next 2 scheduled blocks.
    Returns list of: [{"time": "19:00-20:00", "activity": "dinner", "status": "now|next|later"}]
    """
    schedule_data = state.get("_daily_schedule", {})
    schedule = schedule_data.get("schedule", [])
    if not schedule:
        return []
    
    now = datetime.now(IST)
    current_time = now.strftime("%H:%M")
    
    # Find current block index
    current_idx = None
    for i, block in enumerate(schedule):
        start = block.get("start", "00:00")
        end = block.get("end", "23:59")
        if start <= current_time < end:
            current_idx = i
            break
    
    if current_idx is None:
        # Past all scheduled blocks — probably late night
        return [{"time": "now", "activity": "just chilling / winding down", "status": "now"}]
    
    result = []
    for offset, status in [(0, "now"), (1, "next"), (2, "later")]:
        idx = current_idx + offset
        if idx < len(schedule):
            block = schedule[idx]
            result.append({
                "time": f"{block.get('start', '??')}-{block.get('end', '??')}",
                "activity": block.get("activity", "???"),
                "status": status,
            })
    
    return result


def override_schedule(state: Dict[str, Any], start: str, end: str, activity: str):
    """
    Override a time block in today's schedule.
    Used when the user makes plans with REM.
    
    Args:
        state: The bot's state dict
        start: Start time "HH:MM"
        end: End time "HH:MM"  
        activity: What REM will be doing instead
    """
    schedule_data = state.get("_daily_schedule", {})
    if "overrides" not in schedule_data:
        schedule_data["overrides"] = []
    
    # Remove any existing override that overlaps
    schedule_data["overrides"] = [
        o for o in schedule_data["overrides"]
        if not (o.get("start", "") < end and o.get("end", "") > start)
    ]
    
    schedule_data["overrides"].append({
        "start": start,
        "end": end,
        "activity": activity,
        "created_at": datetime.now(IST).isoformat()
    })
    
    state["_daily_schedule"] = schedule_data
    print(f"[DAILY LIFE] Schedule override: {start}-{end} = {activity}")


def get_upcoming_schedule(state: Dict[str, Any], hours_ahead: int = 4) -> List[Dict[str, str]]:
    """
    Get the next few hours of schedule (for context in prompt).
    Useful so the bot can mention "I have to go soon" or "nothing planned later".
    """
    schedule_data = state.get("_daily_schedule", {})
    schedule = schedule_data.get("schedule", [])
    overrides = schedule_data.get("overrides", [])
    
    now = datetime.now(IST)
    current_time = now.strftime("%H:%M")
    
    # Calculate end time
    end_hour = (now.hour + hours_ahead) % 24
    end_time = f"{end_hour:02d}:{now.minute:02d}"
    
    upcoming = []
    
    # Merge schedule and overrides, overrides take priority
    for block in schedule:
        start = block.get("start", "00:00")
        end = block.get("end", "23:59")
        
        # Check if this block is in the upcoming window  
        if end > current_time and start < end_time:
            # Check if overridden
            overridden = any(
                o.get("start", "") <= start and o.get("end", "") >= end
                for o in overrides
            )
            if not overridden:
                upcoming.append(block)
    
    # Add relevant overrides
    for override in overrides:
        start = override.get("start", "")
        end = override.get("end", "")
        if end > current_time and start < end_time:
            upcoming.append(override)
    
    # Sort by start time
    upcoming.sort(key=lambda x: x.get("start", ""))
    
    return upcoming


async def ensure_daily_schedule(state: Dict[str, Any]) -> str:
    """
    Ensure today's schedule exists. Generate if needed.
    Returns the current activity.
    Called from the pipeline on each message.
    """
    now = datetime.now(IST)
    today = now.strftime("%Y-%m-%d")
    
    schedule_data = state.get("_daily_schedule", {})
    stored_date = schedule_data.get("date", "")
    
    if stored_date == today and schedule_data.get("schedule"):
        # Already have today's schedule
        return get_current_activity(state)
    
    # New day — generate fresh schedule (clears yesterday's overrides too)
    print(f"[DAILY LIFE] Generating new schedule for {today}")
    schedule = await generate_daily_schedule(state)
    
    state["_daily_schedule"] = {
        "date": today,
        "schedule": schedule,
        "overrides": [],  # Fresh overrides for new day
        "generated_at": now.isoformat()
    }
    
    return get_current_activity(state)


async def evaluate_plan_request(
    state: Dict[str, Any],
    user_message: str,
    psyche_state: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """
    Detect if user is proposing future plans and decide if REM adjusts.
    
    Uses a cheap LLM call to:
    1. Detect if the message contains a plan/time proposal
    2. Check what REM has scheduled at that time
    3. Decide based on relationship state whether to accept/decline/negotiate
    
    Returns None if no plan detected, or a dict with the decision.
    """
    # Quick pre-filter — skip if message doesn't look like a plan
    plan_indicators = [
        "let's ", "lets ", "wanna ", "want to ", "can we ", "how about ",
        "tonight", "later today", "meet up", "call me", "talk at",
        "hang out", "come over", "o'clock", " pm", " am",
        "at 7", "at 8", "at 9", "at 10", "at 11", "at 12",
        "around ", "should we", "free at", "free tonight", "free later"
    ]
    msg_lower = user_message.lower()
    if not any(indicator in msg_lower for indicator in plan_indicators):
        return None
    
    # Get schedule context
    schedule_data = state.get("_daily_schedule", {})
    schedule = schedule_data.get("schedule", [])
    if not schedule:
        return None
    
    # Get relationship metrics
    trust = psyche_state.get("trust", 0.5)
    engagement = psyche_state.get("engagement", 0.5)
    phase = psyche_state.get("relationship_phase", "Discovery")
    hurt = psyche_state.get("hurt", 0.0)
    
    # Build schedule summary for LLM (only future blocks)
    now = datetime.now(IST)
    schedule_text = "\n".join(
        f"  {b.get('start','?')}-{b.get('end','?')}: {b.get('activity','?')}"
        for b in schedule
        if b.get("end", "00:00") > now.strftime("%H:%M")
    )
    
    prompt = f"""Analyze this message from a user chatting with Rem (a college girl):

Message: "{user_message}"

Question 1: Is the user proposing or suggesting a specific future plan/activity/time to do something together?
If NO, respond with just: {{"detected": false}}
If YES, continue:

Rem's remaining schedule today:
{schedule_text}

Rem's relationship with this person:
- Trust: {trust:.2f} (0=stranger, 1=deep trust)
- Engagement: {engagement:.2f} (0=bored, 1=very interested)  
- Phase: {phase}
- Hurt: {hurt:.2f}

Based on her relationship with this person and what she has planned, would Rem:
- "accept": adjust her schedule for them (high trust/engagement, or nothing important planned)
- "decline": say no / make an excuse (low trust, or something important planned, or just not feeling it)
- "maybe": be noncommittal, say she'll see (medium trust, or unsure)

Respond ONLY with valid JSON:
{{"detected": true, "proposed_time": "HH:MM", "proposed_end": "HH:MM", "proposed_activity": "what they want to do", "conflicts_with": "what Rem has planned at that time or empty string", "decision": "accept/decline/maybe", "reasoning": "brief 1-line reason from Rem's perspective"}}"""

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                INFERENCE_URL,
                headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
                json={
                    "model": SCHEDULE_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 200,
                    "temperature": 0.7,
                },
            )
            
            if resp.status_code >= 400:
                return None
            
            data = resp.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
            
            # Parse JSON
            if "```" in content:
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
                content = content.strip()
            
            result = json.loads(content)
            
            if not result.get("detected"):
                return None
            
            # If accepted, apply the override
            if result.get("decision") == "accept":
                proposed_start = result.get("proposed_time", "")
                proposed_end = result.get("proposed_end", "")
                activity = result.get("proposed_activity", "hanging out with user")
                
                if proposed_start and proposed_end:
                    override_schedule(state, proposed_start, proposed_end, activity)
            
            print(f"[DAILY LIFE] Plan evaluation: {result.get('decision', '?')} — {result.get('reasoning', '?')}")
            return result
            
    except Exception as e:
        print(f"[DAILY LIFE] Plan evaluation error: {e}")
        return None
