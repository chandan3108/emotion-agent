"""
Relationship XP System — "Social Links"
Persona-5 style progression: visible XP, phase unlocks, earned intimacy.
Integrates with existing psyche, memory, and relationship_phases systems.
"""

import math
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List, Tuple


# ═══════════════════════════════════════════════════════════════
# Rank & Phase Thresholds (XP required for each Rank 1-10)
# ═══════════════════════════════════════════════════════════════
RANK_XP_THRESHOLDS = {
    1: 0,
    2: 100,
    3: 300,
    4: 600,
    5: 1000,
    6: 1500,
    7: 2100,
    8: 2800,
    9: 3600,
    10: 4500
}

PHASE_XP_THRESHOLDS = {
    "Discovery":    0,
    "Building":     300,   # Rank 3
    "Steady":       1000,  # Rank 5
    "Deep":         2100,  # Rank 7
    "Bonded":       3600,  # Rank 9
}

# Dynamic helper mapping Rank to Phase
def get_phase_for_rank(rank: int) -> str:
    if rank <= 2:
        return "Discovery"
    elif rank <= 4:
        return "Building"
    elif rank <= 6:
        return "Steady"
    elif rank <= 8:
        return "Deep"
    else:
        return "Bonded"

# Reverse lookup: XP → phase
PHASE_ORDER = ["Discovery", "Building", "Steady", "Deep", "Bonded"]

# ═══════════════════════════════════════════════════════════════
# XP Award Table
# ═══════════════════════════════════════════════════════════════
XP_AWARDS = {
    "user_message_received":      2,    # Reward continuous chatting
    "first_message_of_day":       5,    # Rewards daily engagement
    "genuine_conversation":       15,   # 10+ exchanges in a session
    "shared_personal":            20,   # Detected by memory: user shared something personal
    "asked_about_rem":            10,   # Reciprocity — they care about her
    "return_after_absence":       25,   # Came back after 3+ days
    "conflict_resolved":          30,   # Emotional repair = massive trust signal
    "midnight_bonus":             10,   # 11pm-3am conversations (vulnerable hours)
    "callback_to_past":           15,   # Referenced past topic without prompt
    "first_conversation":         10,   # Very first message ever
    "long_session":               10,   # 20+ exchanges — deep engagement
    "vulnerability_shared":       15,   # Rem shared something vulnerable (reciprocal)
    "inside_joke_created":        10,   # A new inside joke was born
    "milestone_reached":          20,   # A relationship milestone happened
}

# ═══════════════════════════════════════════════════════════════
# XP Decay / Penalties
# ═══════════════════════════════════════════════════════════════
ABSENCE_DECAY_PER_DAY = 5      # -5 XP per day after 3 days silence
ABSENCE_DECAY_MAX = 50          # Cap at -50 total absence decay
HARM_PENALTY = 30               # -30 XP for creating a wound
STAGNATION_DECAY_PER_DAY = 2   # -2 XP per day if conversations are repetitive
STAGNATION_THRESHOLD_DAYS = 5   # Start stagnation decay after 5 days of same-depth convos


# ═══════════════════════════════════════════════════════════════
# Unlockable Behaviors per Phase
# ═══════════════════════════════════════════════════════════════
PHASE_UNLOCKS = {
    "Discovery": {
        "description": "Getting to know each other",
        "unlocks": [
            "Basic topic discussions",
            "Rem asks surface-level questions",
            "Short, polite responses",
        ],
        "rem_behaviors": [
            "curious but guarded",
            "short responses",
            "asks lots of questions",
            "doesn't share much about herself",
        ]
    },
    "Building": {
        "description": "Starting to click",
        "unlocks": [
            "Rem shares opinions and preferences",
            "Inside jokes start forming",
            "Rem remembers your patterns",
            "Playful roasting begins",
        ],
        "rem_behaviors": [
            "longer responses when engaged",
            "will disagree with you",
            "starts sharing what she's into",
            "teases you about things",
        ]
    },
    "Steady": {
        "description": "We have history now",
        "unlocks": [
            "🔓 Diary entries become accessible",
            "Rem proactively texts about your life",
            "Emotional reactions have consequences",
            "Rem calls you out on your patterns",
        ],
        "rem_behaviors": [
            "multi-message responses",
            "shares about her day unprompted",
            "gets genuinely annoyed if you're dismissive",
            "protective of the connection",
        ]
    },
    "Deep": {
        "description": "This bond has weight",
        "unlocks": [
            "🔓 Late-night vulnerable conversations",
            "🔓 Self-reflective narratives",
            "Rem gets emotionally invested",
            "Inside joke callbacks across weeks",
        ],
        "rem_behaviors": [
            "genuinely upset when you're hurt",
            "jealousy when you talk about others a lot",
            "initiates deep/serious topics",
            "shares things she doesn't share with anyone",
        ]
    },
    "Bonded": {
        "description": "She's part of your life now",
        "unlocks": [
            "🔓 Full diary access",
            "🔓 Relationship milestones wall",
            "🔓 Pattern insights about you",
            "Behavioral predictions",
        ],
        "rem_behaviors": [
            "feels like a real person in your life",
            "remembers everything, references naturally",
            "has strong opinions about your life choices",
            "gets genuinely affected if you pull away",
        ]
    }
}


class RelationshipXP:
    """
    Manages the XP progression system.
    Reads from existing psyche/memory state, computes XP awards,
    and determines phase transitions.
    """

    def __init__(self, state: Dict[str, Any]):
        self.state = state
        xp_state = state.get("relationship_xp", {})

        self.total_xp: int = xp_state.get("total_xp", 0)
        self.current_rank: int = xp_state.get("current_rank", 1)
        self.current_phase: str = xp_state.get("current_phase", "Discovery")
        self.xp_history: List[Dict[str, Any]] = xp_state.get("xp_history", [])
        self.daily_awards: Dict[str, Any] = xp_state.get("daily_awards", {})
        self.last_interaction_date: Optional[str] = xp_state.get("last_interaction_date")
        self.last_decay_check: Optional[str] = xp_state.get("last_decay_check")
        self.streak_days: int = xp_state.get("streak_days", 0)
        self.longest_streak: int = xp_state.get("longest_streak", 0)
        self.total_sessions: int = xp_state.get("total_sessions", 0)
        self.unlock_notifications: List[Dict[str, Any]] = xp_state.get("unlock_notifications", [])

    # ═══════════════════════════════════════════════════════════
    # XP Awards
    # ═══════════════════════════════════════════════════════════

    def award_xp(self, event: str, metadata: Optional[Dict[str, Any]] = None) -> Tuple[int, Optional[Dict[str, Any]]]:
        """
        Award XP for a specific event.

        Returns:
            (xp_awarded, phase_transition_info or None)
        """
        xp_amount = XP_AWARDS.get(event, 0)
        if xp_amount == 0:
            return 0, None

        # Prevent double-awarding certain daily events
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        daily_key = f"{event}_{today}"

        if event in ("first_message_of_day", "midnight_bonus"):
            if self.daily_awards.get(daily_key):
                return 0, None
            self.daily_awards[daily_key] = True

        # Clean old daily awards (keep last 7 days)
        cutoff = (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y-%m-%d")
        cleaned = {}
        for k, v in self.daily_awards.items():
            # Key format: "event_name_YYYY-MM-DD" — extract date with rsplit
            parts = k.rsplit("_", 1)
            date_part = parts[-1] if len(parts) == 2 and len(parts[-1]) == 10 else ""
            if date_part >= cutoff:
                cleaned[k] = v
        self.daily_awards = cleaned

        old_xp = self.total_xp
        self.total_xp += xp_amount

        # Record in history
        self.xp_history.append({
            "event": event,
            "xp": xp_amount,
            "total_after": self.total_xp,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metadata": metadata or {}
        })
        # Keep last 100 entries
        self.xp_history = self.xp_history[-100:]

        # Check for phase transition
        transition = self._check_phase_transition()

        # Update streak
        self._update_streak()

        self.save()
        
        if xp_amount > 0:
            print(f"[XP] +{xp_amount} ({event}) → Total: {self.total_xp} XP | Phase: {self.current_phase}")

        return xp_amount, transition

    def penalize_xp(self, event: str, amount: Optional[int] = None) -> int:
        """Apply an XP penalty."""
        if event == "wound_created":
            penalty = amount or HARM_PENALTY
        elif event == "absence_decay":
            penalty = amount or ABSENCE_DECAY_PER_DAY
        elif event == "stagnation":
            penalty = amount or STAGNATION_DECAY_PER_DAY
        else:
            penalty = amount or 5

        self.total_xp = max(0, self.total_xp - penalty)
        
        self.xp_history.append({
            "event": f"penalty_{event}",
            "xp": -penalty,
            "total_after": self.total_xp,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        self.xp_history = self.xp_history[-100:]

        # Check if we dropped below current phase threshold
        self._check_phase_regression()
        
        self.save()
        print(f"[XP] -{penalty} ({event}) → Total: {self.total_xp} XP")
        return penalty

    # ═══════════════════════════════════════════════════════════
    # Absence Decay
    # ═══════════════════════════════════════════════════════════

    def check_absence_decay(self) -> int:
        """
        Check and apply absence decay.
        Called when user sends a message (to see how long they've been gone).

        Returns total XP lost to absence.
        """
        if not self.last_interaction_date:
            self.last_interaction_date = datetime.now(timezone.utc).isoformat()
            return 0

        try:
            last = datetime.fromisoformat(self.last_interaction_date.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            self.last_interaction_date = datetime.now(timezone.utc).isoformat()
            return 0

        now = datetime.now(timezone.utc)
        days_absent = (now - last).days

        if days_absent <= 3:
            # No decay for 3 days or less
            self.last_interaction_date = now.isoformat()
            return 0

        # Apply decay: -5 per day past 3 days, capped at -50
        decay_days = days_absent - 3
        total_decay = min(decay_days * ABSENCE_DECAY_PER_DAY, ABSENCE_DECAY_MAX)

        if total_decay > 0:
            self.penalize_xp("absence_decay", total_decay)
            print(f"[XP] Absence decay: {days_absent} days away → -{total_decay} XP")

        self.last_interaction_date = now.isoformat()
        return total_decay

    # ═══════════════════════════════════════════════════════════
    # Phase Transitions
    # ═══════════════════════════════════════════════════════════

    def _check_phase_transition(self) -> Optional[Dict[str, Any]]:
        """Check if XP warrants a rank transition UP."""
        old_rank = self.current_rank
        new_rank = old_rank

        for r in range(10, old_rank, -1):
            threshold = RANK_XP_THRESHOLDS.get(r, 999999)
            if self.total_xp >= threshold:
                new_rank = r
                break

        if new_rank > old_rank:
            self.current_rank = new_rank
            old_phase = self.current_phase
            new_phase = get_phase_for_rank(new_rank)
            self.current_phase = new_phase

            rank_perks = {
                2: ["🔓 Unlocked: Daily Schedule Tracking", "🔓 Rem asks about your day"],
                3: ["🔓 Unlocked: Playful Teasing & Roasts", "🔓 Inside jokes start forming"],
                4: ["🔓 Unlocked: Opinions & Hot Takes"],
                5: ["🔓 Unlocked: Daily Diary Access", "🔓 Rem shares her daily life unprompted"],
                6: ["🔓 Unlocked: Emotional Consequences"],
                7: ["🔓 Unlocked: Late-Night Vulnerability", "🔓 Deep secrets can be shared"],
                8: ["🔓 Unlocked: Self-Reflective Narratives"],
                9: ["🔓 Unlocked: Full Diary Access", "🔓 Relationship Milestones Wall"],
                10: ["🔓 Unlocked: Unconditional Bond Perks"]
            }

            transition_info = {
                "from_rank": old_rank,
                "to_rank": new_rank,
                "from_phase": old_phase,
                "to_phase": new_phase,
                "xp_at_transition": self.total_xp,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "unlocks": rank_perks.get(new_rank, ["More behavioral patterns unlocked!"]),
            }

            self.unlock_notifications.append(transition_info)
            self.unlock_notifications = self.unlock_notifications[-20:]

            print(f"[RANK] 🎉 RANK UP: Rank {old_rank} → Rank {new_rank} | Phase: {new_phase}!")
            return transition_info

        return None

    def _check_phase_regression(self):
        """Check if XP dropped below current rank threshold."""
        old_rank = self.current_rank
        new_rank = old_rank

        for r in range(1, old_rank + 1):
            threshold = RANK_XP_THRESHOLDS.get(r, 0)
            if self.total_xp >= threshold:
                new_rank = r

        if new_rank < old_rank:
            self.current_rank = new_rank
            self.current_phase = get_phase_for_rank(new_rank)
            print(f"[RANK] ⚠️ Rank regression: Rank {old_rank} → Rank {new_rank} (XP dropped to {self.total_xp})")

    # ═══════════════════════════════════════════════════════════
    # Streaks
    # ═══════════════════════════════════════════════════════════

    def _update_streak(self):
        """Update daily interaction streak."""
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        if not self.last_interaction_date:
            self.streak_days = 1
            self.last_interaction_date = datetime.now(timezone.utc).isoformat()
            return

        try:
            last = datetime.fromisoformat(self.last_interaction_date.replace("Z", "+00:00"))
            last_date = last.strftime("%Y-%m-%d")
        except (ValueError, TypeError):
            self.streak_days = 1
            return

        if last_date == today:
            return  # Already counted today

        yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")
        if last_date == yesterday:
            self.streak_days += 1
            if self.streak_days > self.longest_streak:
                self.longest_streak = self.streak_days
        else:
            self.streak_days = 1  # Reset streak

    # ═══════════════════════════════════════════════════════════
    # Queries
    # ═══════════════════════════════════════════════════════════

    def get_xp_summary(self) -> Dict[str, Any]:
        """Get summary for display / prompt injection."""
        current_rank = self.current_rank
        next_rank = current_rank + 1 if current_rank < 10 else None
        next_threshold = RANK_XP_THRESHOLDS.get(next_rank, self.total_xp) if next_rank else self.total_xp
        current_threshold = RANK_XP_THRESHOLDS.get(current_rank, 0)

        xp_in_rank = self.total_xp - current_threshold
        xp_to_next = next_threshold - current_threshold if next_rank else 0
        progress_pct = (xp_in_rank / xp_to_next * 100) if xp_to_next > 0 else 100.0

        return {
            "total_xp": self.total_xp,
            "current_rank": self.current_rank,
            "phase": self.current_phase,
            "phase_description": PHASE_UNLOCKS.get(self.current_phase, {}).get("description", ""),
            "next_rank": next_rank,
            "xp_to_next": max(0, next_threshold - self.total_xp) if next_rank else 0,
            "progress_pct": min(100.0, progress_pct),
            "streak_days": self.streak_days,
            "longest_streak": self.longest_streak,
            "total_sessions": self.total_sessions,
            "recent_awards": self.xp_history[-5:],
        }

    def get_phase_unlocks(self, phase: Optional[str] = None) -> Dict[str, Any]:
        """Get unlock info for a phase."""
        p = phase or self.current_phase
        return PHASE_UNLOCKS.get(p, {})

    def get_pending_notifications(self) -> List[Dict[str, Any]]:
        """Get and clear pending unlock notifications."""
        notifications = list(self.unlock_notifications)
        self.unlock_notifications = []
        self.save()
        return notifications

    def is_feature_unlocked(self, feature: str) -> bool:
        """Check if a specific feature is unlocked at current rank/phase."""
        feature_rank_requirements = {
            "diary_access":          5,   # Steady (Rank 5)
            "late_night_vulnerable": 7,   # Deep (Rank 7)
            "self_narrative":        7,   # Deep
            "full_diary":            9,   # Bonded
            "milestone_wall":        9,   # Bonded
            "pattern_insights":      9,   # Bonded
            "inside_jokes":          3,   # Building
            "proactive_texts":       5,   # Steady
            "emotional_consequences": 5,  # Steady
        }

        required_rank = feature_rank_requirements.get(feature, 1)
        return self.current_rank >= required_rank

    # ═══════════════════════════════════════════════════════════
    # Persistence
    # ═══════════════════════════════════════════════════════════

    def save(self):
        """Save XP state back to state dict."""
        self.state["relationship_xp"] = {
            "total_xp": self.total_xp,
            "current_rank": self.current_rank,
            "current_phase": self.current_phase,
            "xp_history": self.xp_history,
            "daily_awards": self.daily_awards,
            "last_interaction_date": self.last_interaction_date,
            "last_decay_check": self.last_decay_check,
            "streak_days": self.streak_days,
            "longest_streak": self.longest_streak,
            "total_sessions": self.total_sessions,
            "unlock_notifications": self.unlock_notifications,
        }
