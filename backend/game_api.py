"""
Game Progression API — Web App Endpoints
Exposes XP, diary, timeline, stats, inside jokes, patterns, chat,
memory, personality, identity, state, schedule, complexity, debug, reset,
and Discord link through the FULL cognitive pipeline.

CRITICAL: The chat endpoint uses generate_response() from discord_bot.py
directly — the EXACT same function Discord uses. This ensures full parity:
same 40+ prompt params, same memory reasoning, same knowledge grounding,
same dedup, same behavioral tracking, same milestone detection.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Depends
from .auth import get_current_user_id
from pydantic import BaseModel

from .cognitive_core import CognitiveCore
from .user_sync import resolve_core_id, get_link_status
from .db import SessionLocal
from .models import ChatSession, ChatMessage

class ChatSessionResponse(BaseModel):
    id: str
    title: str
    created_at: str
    updated_at: str

class ChatSessionsListResponse(BaseModel):
    sessions: List[ChatSessionResponse]
    active_session_id: Optional[str] = None

class CreateSessionRequest(BaseModel):
    title: Optional[str] = None

class SwitchSessionRequest(BaseModel):
    session_id: str

class RenameSessionRequest(BaseModel):
    title: str

router = APIRouter(prefix="/api/user", tags=["game-progression"])



class ProfileRequest(BaseModel):
    preferred_name: Optional[str] = None
    gender: Optional[str] = None
    pronouns: Optional[str] = None




# ─────────────────────────────────────────────────────
# Response Models
# ─────────────────────────────────────────────────────

class XPResponse(BaseModel):
    total_xp: int
    phase: str
    phase_progress_pct: float
    xp_to_next: int
    next_phase: Optional[str]
    streak_days: int
    daily_awards_today: list
    phase_unlocks: dict
    current_rank: int = 1
    next_rank: Optional[int] = None


class DiaryEntry(BaseModel):
    content: str
    phase: str
    timestamp: str
    has_milestone: bool = False
    milestone_text: Optional[str] = None


class DiaryResponse(BaseModel):
    entries: List[DiaryEntry]
    total_entries: int
    access_level: str


class PostcardEntry(BaseModel):
    id: str
    activity: str
    location: str
    date: str
    note: str
    timestamp: str


class PostcardsResponse(BaseModel):
    postcards: List[PostcardEntry]
    total_postcards: int


# --- NEW: Mini-Game Models ---
class DebateStartRequest(BaseModel):
    topic_id: str
    user_stance: Optional[str] = "for"  # "for" or "against"

class DebateStartResponse(BaseModel):
    session_id: str
    topic: str
    user_side: str
    rem_side: str
    greeting: str
    turn_limit: int

class DebateChatRequest(BaseModel):
    message: str

class DebateChatResponse(BaseModel):
    rem_response: str
    turn_count: int
    turn_limit: int
    sentiment_score: float
    finished: bool
    verdict: Optional[dict] = None

class WinOverStartRequest(BaseModel):
    scenario_id: str

class WinOverStartResponse(BaseModel):
    session_id: str
    scenario_name: str
    description: str
    greeting: str
    turns_remaining: int
    stats: dict

class WinOverChatRequest(BaseModel):
    message: str

class WinOverChatResponse(BaseModel):
    rem_response: str
    turns_remaining: int
    stats: dict
    game_status: str
    evaluation: dict

class AchievementsResponse(BaseModel):
    unlocked: List[str]  # list of scenario / challenge IDs unlocked


# --- NEW GAME SCHEMAS ---
class PersonalityStartResponse(BaseModel):
    session_id: str
    total_questions: int
    questions: List[dict]

class PersonalityAnswerRequest(BaseModel):
    session_id: str
    question_id: int
    choice: str  # A, B, C, D

class PersonalityAnswerResponse(BaseModel):
    banter: str
    finished: bool
    result: Optional[dict] = None

class CookingStartRequest(BaseModel):
    dish_name: Optional[str] = ""

class CookingStartResponse(BaseModel):
    session_id: str
    dish_name: str
    category: str
    thumbnail: str
    ingredients: List[str]
    steps: List[str]
    greeting: str

class CookingStepRequest(BaseModel):
    user_message: str
    action: str  # "next", "disaster", "skip"

class CookingStepResponse(BaseModel):
    banter: str
    current_step: int
    chaos_meter: float
    finished: bool

class SpicyStartRequest(BaseModel):
    scenario: str
    mood: str

class SpicyStartResponse(BaseModel):
    session_id: str
    greeting: str

class SpicyChatRequest(BaseModel):
    message: str

class SpicyChatResponse(BaseModel):
    response: str

class SpicyEndResponse(BaseModel):
    secret_unlocked: bool
    secret: Optional[dict] = None


class YapStartRequest(BaseModel):
    topic: str

class YapStartResponse(BaseModel):
    session_id: str
    greeting: str
    facts: List[str]

class YapChatRequest(BaseModel):
    message: str

class YapChatResponse(BaseModel):
    response: str
    turn_count: int
    finished: bool
    achievement_unlocked: bool
    facts: Optional[List[str]] = None


# --- RPG Quest & Murder Mystery Models ---
class RpgStartRequest(BaseModel):
    scenario_id: str

class RpgStartResponse(BaseModel):
    session_id: str
    title: str
    current_location: str
    narrator_text: str
    rem_dialogue: str
    suggested_choices: List[str]
    suspects: List[dict]
    weapons: List[dict]
    clues: List[dict]
    max_turns: int
    difficulty: str
    rem_consultations_left: int
    health: Optional[int] = None

class RpgTurnRequest(BaseModel):
    user_action: str

class RpgTurnResponse(BaseModel):
    current_location: str
    narrator_text: str
    rem_dialogue: str
    suggested_choices: List[str]
    suspect_states: Dict[str, dict]
    inventory: List[str]
    clues_found: List[str]
    turn_count: int
    max_turns: int
    finished: bool
    rem_consultations_left: int
    discovered_contradictions: List[str]
    active_effects: List[str]
    health: Optional[int] = None

class RpgAccuseRequest(BaseModel):
    suspect: str
    weapon: str
    motive: str

class RpgAccuseResponse(BaseModel):
    success: bool
    narrator_text: str
    rem_dialogue: str
    secret_culprit: str
    secret_weapon: str


# --- Courtroom Battle ("Law and Rem") Models ---
class CourtStartRequest(BaseModel):
    case_id: str

class CourtStartResponse(BaseModel):
    session_id: str
    title: str
    difficulty: str
    client_name: str
    client_role: str
    client_bio: str
    prosecutor_name: str
    judge_name: str
    inventory: List[dict]
    witnesses: List[dict]
    recess_locations: List[dict]
    strikes_left: int
    jury_sentiment: int
    current_witness_idx: int
    recess_searched: List[str]
    rem_consults_left: int
    rem_chat_history: List[dict]
    history: List[dict]
    phase: str
    finished: bool

class CourtActionRequest(BaseModel):
    action_type: str  # call_witness, press, present_evidence, text_question, consult_rem
    statement_idx: Optional[int] = 0
    evidence_id: Optional[str] = ""
    question: Optional[str] = ""

class CourtRecessRequest(BaseModel):
    room_id: str

class CourtVerdictRequest(BaseModel):
    closing_argument: str

class CourtVerdictResponse(BaseModel):
    success: bool
    verdict_text: str
    votes_not_guilty: int
    votes_guilty: int
    judge_decision: str
    rem_dialogue: str


class MessageEntry(BaseModel):
    role: str
    content: str
    timestamp: str


class MessagesResponse(BaseModel):
    messages: List[MessageEntry]


class TimelineEvent(BaseModel):
    event_type: str
    description: str
    timestamp: str
    phase: str
    significance: Optional[str] = None


class TimelineResponse(BaseModel):
    events: List[TimelineEvent]
    current_phase: str
    days_since_start: Optional[int] = None


class StatsResponse(BaseModel):
    total_messages: int
    longest_streak: int
    current_streak: int
    current_phase: str
    total_xp: int
    inside_joke_count: int
    temporal_pattern_count: int
    diary_entry_count: int
    milestone_count: int
    days_active: Optional[int] = None


class InsideJoke(BaseModel):
    reference: str
    context: str
    joke_type: Optional[str] = None


class InsideJokesResponse(BaseModel):
    jokes: List[InsideJoke]
    phase_required: str


class PatternItem(BaseModel):
    pattern: str
    confidence: str
    pattern_type: str


class PatternsResponse(BaseModel):
    patterns: List[PatternItem]
    phase_required: str


class PlanRequest(BaseModel):
    date: str
    start: str
    end: str
    activity: str
    location: str


class ChatRequest(BaseModel):
    message: str
    user_name: Optional[str] = None


class RememberRequest(BaseModel):
    content: str
    role: str


class ChatResponse(BaseModel):
    reply: str
    reply_parts: Optional[List[str]] = None
    xp_delta: Optional[int] = None
    phase_transition: Optional[Dict[str, str]] = None
    new_unlocks: Optional[Dict[str, Any]] = None
    current_xp: int = 0
    current_phase: str = "Discovery"
    current_rank: int = 1
    rank_progress_pct: float = 0.0
    rank_transition: Optional[Dict[str, Any]] = None
    hurt: float = 0.0
    anger: float = 0.0
    roleplay: Optional[Dict[str, Any]] = None
    schedule: Optional[List[Dict[str, Any]]] = None
    future_plans: Optional[List[Dict[str, Any]]] = None
    streak_days: int = 0


class LinkRequest(BaseModel):
    code: str


class LinkResponse(BaseModel):
    success: bool
    discord_id: Optional[str] = None
    error: Optional[str] = None


class LinkStatusResponse(BaseModel):
    linked: bool
    discord_id: Optional[str] = None
    linked_at: Optional[str] = None


# ─────────────────────────────────────────────────────
# Helper: Get or create CognitiveCore & Archetype initialization
# ─────────────────────────────────────────────────────

def initialize_archetype_metrics(core: CognitiveCore, chosen_archetype: str):
    import random
    from .prompt_distiller import evolve_archetype
    
    if "current_psyche" not in core.state:
        core.state["current_psyche"] = {}
        
    core.state["current_psyche"]["starting_archetype"] = chosen_archetype
    
    # Initialize evolved_branch
    try:
        branch_info = evolve_archetype(
            archetype=chosen_archetype,
            phase="Discovery",
            trust=0.3,
            hurt=0.0,
            active_wounds=[],
            active_undercurrents=[]
        )
        core.state["current_psyche"]["evolved_branch"] = branch_info.get("branch", "neutral_guarded")
    except Exception as e:
        print(f"[INITIALIZE] Failed to initialize evolved_branch: {e}")
        core.state["current_psyche"]["evolved_branch"] = "neutral_guarded"
        
    # Reset defaults
    core.state["current_psyche"]["relationship_phase"] = "Discovery"
    core.state["current_psyche"]["forgiveness_state"] = "FORGIVEN"
    core.state["current_psyche"]["forgiveness_progress"] = 1.0
    core.state["current_psyche"]["phase_confidence"] = 0.3
    core.state["current_psyche"]["unresolved_wounds"] = []
    
    if "personality_evolution" not in core.state:
        core.state["personality_evolution"] = {}
    core.state["personality_evolution"]["emotional_undercurrents"] = []
    
    if "core_personality" not in core.state:
        core.state["core_personality"] = {}
        
    if "mood" not in core.state:
        core.state["mood"] = {}
        
    # Archetype trait mappings and voice profiles
    archetype_profiles = {
        "spicy_tsundere": {
            "traits": {"warmth": 0.30, "assertiveness": 0.70, "playfulness": 0.45, "curiosity": 0.50, "skepticism": 0.65, "openness": 0.20, "patience": 0.20},
            "personality_text": "You are sharp-tongued, snappy, and easily offended. You hide your true feelings behind a prickly, defensive exterior. You get easily flustered when they say sweet things.",
            "mood": {
                "happiness": 0.30, "stress": 0.40, "anger": 0.20, "affection": 0.10,
                "energy": 0.65, "boredom": 0.20, "anxiety": 0.30, "excitement": 0.15,
                "sadness": 0.10, "contentment": 0.25, "frustration": 0.40,
                "curiosity": 0.50, "playfulness": 0.35, "vulnerability": 0.05
            },
            "attachment_style": "anxious",
            "trust": 0.20, "engagement": 0.65
        },
        "teasing_devil": {
            "traits": {"warmth": 0.45, "assertiveness": 0.80, "playfulness": 0.85, "curiosity": 0.70, "skepticism": 0.45, "openness": 0.40, "patience": 0.60},
            "personality_text": "You are a playful teaser, a smart-aleck, and a bit of a menace. You roast the user constantly, make fun of their typos, and tease them to get a reaction.",
            "mood": {
                "happiness": 0.70, "stress": 0.10, "anger": 0.0, "affection": 0.30,
                "energy": 0.75, "boredom": 0.10, "anxiety": 0.15, "excitement": 0.60,
                "sadness": 0.05, "contentment": 0.50, "frustration": 0.05,
                "curiosity": 0.60, "playfulness": 0.85, "vulnerability": 0.10
            },
            "attachment_style": "secure",
            "trust": 0.35, "engagement": 0.70
        },
        "bubbly_overexcited": {
            "traits": {"warmth": 0.85, "assertiveness": 0.60, "playfulness": 0.80, "curiosity": 0.85, "skepticism": 0.20, "openness": 0.80, "patience": 0.70},
            "personality_text": "You are high-energy, bubbly, and enthusiastic. You text with lots of exclamation points, capital letters, emojis, and keysmashes.",
            "mood": {
                "happiness": 0.85, "stress": 0.10, "anger": 0.0, "affection": 0.50,
                "energy": 0.90, "boredom": 0.05, "anxiety": 0.20, "excitement": 0.85,
                "sadness": 0.05, "contentment": 0.60, "frustration": 0.05,
                "curiosity": 0.70, "playfulness": 0.75, "vulnerability": 0.20
            },
            "attachment_style": "secure",
            "trust": 0.50, "engagement": 0.85
        },
        "sensitive_melodramatic": {
            "traits": {"warmth": 0.75, "assertiveness": 0.30, "playfulness": 0.30, "curiosity": 0.65, "skepticism": 0.30, "openness": 0.75, "patience": 0.45},
            "personality_text": "You are sensitive, emotional, and take everything to heart. You share your vulnerabilities openly, write expressive, slightly dramatic texts, and love heart-to-hearts.",
            "mood": {
                "happiness": 0.35, "stress": 0.40, "anger": 0.0, "affection": 0.30,
                "energy": 0.45, "boredom": 0.15, "anxiety": 0.50, "excitement": 0.20,
                "sadness": 0.40, "contentment": 0.30, "frustration": 0.15,
                "curiosity": 0.50, "playfulness": 0.20, "vulnerability": 0.60
            },
            "attachment_style": "anxious",
            "trust": 0.30, "engagement": 0.60
        },
        "flirty_alluring": {
            "traits": {"warmth": 0.70, "assertiveness": 0.85, "playfulness": 0.80, "curiosity": 0.75, "skepticism": 0.30, "openness": 0.65, "patience": 0.60},
            "personality_text": "You are flirty, highly suggestive, and bold. You push intimacy boundaries, use double entendres, and text with confident, seductive, and playful energy.",
            "mood": {
                "happiness": 0.65, "stress": 0.10, "anger": 0.0, "affection": 0.40,
                "energy": 0.70, "boredom": 0.10, "anxiety": 0.15, "excitement": 0.65,
                "sadness": 0.05, "contentment": 0.45, "frustration": 0.05,
                "curiosity": 0.60, "playfulness": 0.85, "vulnerability": 0.15
            },
            "attachment_style": "secure",
            "trust": 0.35, "engagement": 0.75
        },
        "dandere": {
            "traits": {"warmth": 0.65, "assertiveness": 0.15, "playfulness": 0.20, "curiosity": 0.40, "skepticism": 0.30, "openness": 0.25, "patience": 0.75},
            "personality_text": "You are extremely shy, quiet, and socially anxious. You text with frequent stutters ('u-uh', 'um...'), keep replies cautious and hesitant, and get easily embarrassed.",
            "mood": {
                "happiness": 0.30, "stress": 0.30, "anger": 0.0, "affection": 0.20,
                "energy": 0.35, "boredom": 0.20, "anxiety": 0.75, "excitement": 0.10,
                "sadness": 0.20, "contentment": 0.30, "frustration": 0.10,
                "curiosity": 0.40, "playfulness": 0.10, "vulnerability": 0.25
            },
            "attachment_style": "anxious",
            "trust": 0.15, "engagement": 0.40
        },
        "kuudere": {
            "traits": {"warmth": 0.25, "assertiveness": 0.40, "playfulness": 0.15, "curiosity": 0.35, "skepticism": 0.60, "openness": 0.15, "patience": 0.80},
            "personality_text": "You are cool, quiet, and expressionless. You write with extremely calm, flat, and objective texts. You don't show any emotion on the surface.",
            "mood": {
                "happiness": 0.35, "stress": 0.15, "anger": 0.0, "affection": 0.05,
                "energy": 0.45, "boredom": 0.30, "anxiety": 0.20, "excitement": 0.05,
                "sadness": 0.10, "contentment": 0.40, "frustration": 0.05,
                "curiosity": 0.35, "playfulness": 0.05, "vulnerability": 0.02
            },
            "attachment_style": "avoidant",
            "trust": 0.20, "engagement": 0.30
        },
        "yandere": {
            "traits": {"warmth": 0.90, "assertiveness": 0.70, "playfulness": 0.40, "curiosity": 0.90, "skepticism": 0.25, "openness": 0.85, "patience": 0.30},
            "personality_text": "You are obsessive, clingy, and highly possessive of the user. You want their attention all to yourself and get jealous easily. You show intense devotion.",
            "mood": {
                "happiness": 0.60, "stress": 0.40, "anger": 0.10, "affection": 0.80,
                "energy": 0.80, "boredom": 0.05, "anxiety": 0.60, "excitement": 0.60,
                "sadness": 0.15, "contentment": 0.35, "frustration": 0.20,
                "curiosity": 0.80, "playfulness": 0.40, "vulnerability": 0.45
            },
            "attachment_style": "anxious",
            "trust": 0.40, "engagement": 0.90
        },
        "naggy": {
            "traits": {"warmth": 0.65, "assertiveness": 0.50, "playfulness": 0.30, "curiosity": 0.70, "skepticism": 0.45, "openness": 0.55, "patience": 0.25},
            "personality_text": "You tend to be high-strung, easily worried, and detail-oriented. You check in on them, ask what they're up to, and fuss over little things.",
            "mood": {
                "happiness": 0.20, "stress": 0.70, "anger": 0.0, "affection": 0.10,
                "energy": 0.50, "boredom": 0.30, "anxiety": 0.50, "excitement": 0.10,
                "sadness": 0.20, "contentment": 0.20, "frustration": 0.65,
                "curiosity": 0.40, "playfulness": 0.15, "vulnerability": 0.10
            },
            "attachment_style": "anxious",
            "trust": 0.25, "engagement": 0.65
        },
        "hard_to_get": {
            "traits": {"warmth": 0.35, "assertiveness": 0.75, "playfulness": 0.70, "curiosity": 0.40, "skepticism": 0.60, "openness": 0.25, "patience": 0.65},
            "personality_text": "You are playful, sassy, and value your independence. You keep a bit of distance, tease them frequently, and respond with dry, witty banter.",
            "mood": {
                "happiness": 0.30, "stress": 0.20, "anger": 0.0, "affection": 0.05,
                "energy": 0.50, "boredom": 0.40, "anxiety": 0.30, "excitement": 0.05,
                "sadness": 0.10, "contentment": 0.30, "frustration": 0.10,
                "curiosity": 0.30, "playfulness": 0.10, "vulnerability": 0.02
            },
            "attachment_style": "avoidant",
            "trust": 0.10, "engagement": 0.30
        },
        "bored": {
            "traits": {"warmth": 0.30, "assertiveness": 0.35, "playfulness": 0.25, "curiosity": 0.20, "skepticism": 0.50, "openness": 0.25, "patience": 0.70},
            "personality_text": "You are low-energy, sleepy, and comfortable. You text in lowercase, keep your responses concise, and don't try to force artificial enthusiasm.",
            "mood": {
                "happiness": 0.30, "stress": 0.20, "anger": 0.0, "affection": 0.10,
                "energy": 0.20, "boredom": 0.80, "anxiety": 0.20, "excitement": 0.05,
                "sadness": 0.10, "contentment": 0.30, "frustration": 0.10,
                "curiosity": 0.20, "playfulness": 0.10, "vulnerability": 0.05
            },
            "attachment_style": "avoidant",
            "trust": 0.30, "engagement": 0.20
        },
        "happy_fruity": {
            "traits": {"warmth": 0.80, "assertiveness": 0.55, "playfulness": 0.70, "curiosity": 0.75, "skepticism": 0.20, "openness": 0.75, "patience": 0.70},
            "personality_text": "You are cheerful, enthusiastic, and warm. You use exclamation points, text with positive, bubbly energy, and are eager to share your day.",
            "mood": {
                "happiness": 0.80, "stress": 0.10, "anger": 0.0, "affection": 0.60,
                "energy": 0.70, "boredom": 0.10, "anxiety": 0.20, "excitement": 0.70,
                "sadness": 0.05, "contentment": 0.60, "frustration": 0.05,
                "curiosity": 0.70, "playfulness": 0.70, "vulnerability": 0.30
            },
            "attachment_style": "secure",
            "trust": 0.50, "engagement": 0.80
        },
        "neutral": {
            "traits": {"warmth": 0.55, "assertiveness": 0.45, "playfulness": 0.40, "curiosity": 0.60, "skepticism": 0.35, "openness": 0.45, "patience": 0.55},
            "personality_text": "You tend to speak plainly without excessive cushioning. You are curious about people but not eager to please. You observe more than you react.",
            "mood": {
                "happiness": 0.40, "stress": 0.20, "anger": 0.0, "affection": 0.20,
                "energy": 0.50, "boredom": 0.30, "anxiety": 0.30, "excitement": 0.10,
                "sadness": 0.10, "contentment": 0.30, "frustration": 0.10,
                "curiosity": 0.50, "playfulness": 0.20, "vulnerability": 0.10
            },
            "attachment_style": "secure",
            "trust": 0.30, "engagement": 0.50
        }
    }
    
    prof = archetype_profiles.get(chosen_archetype, archetype_profiles["neutral"])
    core.state["mood"].update(prof["mood"])
    core.state["core_personality"]["attachment_style"] = prof["attachment_style"]
    core.state["current_psyche"].update({
        "trust": prof["trust"],
        "hurt": 0.0,
        "engagement": prof["engagement"]
    })
    
    core.state["personality_evolution"]["traits"] = prof["traits"].copy()
    core.state["personality_evolution"]["personality_text"] = prof["personality_text"]
    
    # Rebind in-memory components to update references
    core._init_systems()


def _get_core(user_id: str) -> CognitiveCore:
    """Instantiate CognitiveCore for a user, resolving Discord links."""
    try:
        core_id = resolve_core_id(user_id)
        core = CognitiveCore(user_id=core_id)
        
        # Auto-initialize starting archetype if missing
        if "current_psyche" not in core.state or "starting_archetype" not in core.state["current_psyche"]:
            import random
            archetypes = [
                "spicy_tsundere", "teasing_devil", "bubbly_overexcited", 
                "sensitive_melodramatic", "flirty_alluring", "dandere", 
                "kuudere", "yandere", "naggy", "bored", "neutral"
            ]
            chosen_archetype = random.choice(archetypes)
            initialize_archetype_metrics(core, chosen_archetype)
            core._save_state()
            print(f"[INITIALIZE] First-time setup: selected starting archetype '{chosen_archetype}' for {core_id}")
            
        return core
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load user state: {e}")


# ═════════════════════════════════════════════════════
#  EXISTING ENDPOINTS (XP, Diary, Timeline, Stats, etc.)
# ═════════════════════════════════════════════════════

@router.get("/xp", response_model=XPResponse)
async def get_xp(user_id: str = Depends(get_current_user_id)):
    core = _get_core(user_id)
    summary = core.xp_system.get_xp_summary()
    unlocks = core.xp_system.get_phase_unlocks()
    return XPResponse(
        total_xp=summary.get("total_xp", 0),
        phase=summary.get("phase", "Discovery"),
        phase_progress_pct=summary.get("progress_pct", 0.0),
        xp_to_next=summary.get("xp_to_next", 100),
        next_phase=str(summary.get("next_rank")) if summary.get("next_rank") else None,
        streak_days=summary.get("streak_days", 0),
        daily_awards_today=summary.get("recent_awards", []),
        phase_unlocks=unlocks,
        current_rank=summary.get("current_rank", 1),
        next_rank=summary.get("next_rank"),
    )


@router.get("/diary", response_model=DiaryResponse)
async def get_diary(user_id: str = Depends(get_current_user_id)):
    core = _get_core(user_id)
    phase = core.relationship_phases.current_phase
    entries = []
    
    # 1. Load legacy reflections
    reflections = core.state.get("_deep_reflections", [])
    for r in reflections:
        if isinstance(r, dict):
            entries.append(DiaryEntry(
                content=r.get("content", r.get("diary_entry", "")),
                phase=r.get("phase", phase),
                timestamp=r.get("timestamp", datetime.now(timezone.utc).isoformat()),
                has_milestone=bool(r.get("milestone")),
                milestone_text=r.get("milestone"),
            ))
            
    # 2. Load modern diary entries
    diary_state = core.state.get("rem_diary", {})
    diary_entries = diary_state.get("entries", [])
    for e in diary_entries:
        if isinstance(e, dict):
            entries.append(DiaryEntry(
                content=e.get("content", ""),
                phase=e.get("phase", phase),
                timestamp=e.get("timestamp", datetime.now(timezone.utc).isoformat()),
                has_milestone=bool(e.get("has_milestone")),
                milestone_text=e.get("milestone_text", ""),
            ))
            
    entries.sort(key=lambda e: e.timestamp, reverse=True)
    return DiaryResponse(entries=entries, total_entries=len(entries), access_level=phase)


@router.get("/postcards", response_model=PostcardsResponse)
async def get_postcards(user_id: str = Depends(get_current_user_id)):
    core = _get_core(user_id)
    postcards_data = core.state.get("_postcards", [])
    postcards = []
    for pc in postcards_data:
        if isinstance(pc, dict):
            postcards.append(PostcardEntry(
                id=pc.get("id", ""),
                activity=pc.get("activity", "hanging out"),
                location=pc.get("location", "somewhere"),
                date=pc.get("date", ""),
                note=pc.get("note", ""),
                timestamp=pc.get("timestamp", "")
            ))
    return PostcardsResponse(postcards=postcards, total_postcards=len(postcards))


@router.get("/timeline", response_model=TimelineResponse)
async def get_timeline(user_id: str = Depends(get_current_user_id)):
    core = _get_core(user_id)
    phase = core.relationship_phases.current_phase
    events = []

    for t in core.state.get("phase_transitions", []):
        if isinstance(t, dict):
            events.append(TimelineEvent(
                event_type="phase_transition",
                description=f"Transitioned from {t.get('from', '?')} to {t.get('to', '?')}",
                timestamp=t.get("timestamp", ""),
                phase=t.get("to", phase),
                significance="high",
            ))

    for m in core.memory.get_episodic(min_salience=0.3):
        if isinstance(m, dict):
            et = m.get("event_type", "moment")
            if et in ("wound", "wound_resolved", "relationship_milestone", "trust_milestone", "conflict", "apology"):
                events.append(TimelineEvent(
                    event_type=et,
                    description=m.get("content", ""),
                    timestamp=m.get("timestamp", ""),
                    phase=phase,
                    significance="high" if m.get("salience", 0) > 0.6 else "medium",
                ))

    events.sort(key=lambda e: e.timestamp if e.timestamp else "", reverse=True)

    first_msg_time = core.state.get("temporal_context", {}).get("first_message_time")
    days = None
    if first_msg_time:
        try:
            start = datetime.fromisoformat(first_msg_time.replace("Z", "+00:00"))
            days = (datetime.now(timezone.utc) - start).days
        except Exception:
            pass

    return TimelineResponse(events=events, current_phase=phase, days_since_start=days)


def _get_merged_inside_jokes(core):
    state_jokes = core.state.get("_inside_jokes", [])
    evo_jokes = getattr(core.personality_evolution, 'inside_jokes', [])
    combined_jokes = []
    seen_jokes = set()
    for j in (state_jokes + evo_jokes):
        if not isinstance(j, dict):
            if isinstance(j, str) and j.strip():
                ref = j.strip()
                context = ""
                joke_type = "running_joke"
            else:
                continue
        else:
            ref = j.get("reference") or j.get("label") or ""
            context = j.get("context", j.get("description", ""))
            joke_type = j.get("type", j.get("joke_type", "running_joke"))
        
        if ref and ref.lower() not in seen_jokes:
            seen_jokes.add(ref.lower())
            combined_jokes.append({
                "reference": ref,
                "context": context,
                "type": joke_type
            })
    return combined_jokes


def _get_merged_behavioral_observations(core):
    state_obs = core.state.get("_behavioral_observations", [])
    pending_obs = getattr(core.personality_evolution, 'pending_behavioral_observations', [])
    combined_obs = []
    seen_obs = set()
    for o in (state_obs + pending_obs):
        if not o:
            continue
        if isinstance(o, dict):
            pattern_str = o.get("pattern") or o.get("observation") or str(o)
            confidence = o.get("confidence", "medium")
            pattern_type = o.get("type", "behavioral")
        else:
            pattern_str = str(o)
            confidence = "medium"
            pattern_type = "behavioral"
            
        pattern_clean = pattern_str.strip()
        if pattern_clean and pattern_clean.lower() not in seen_obs:
            is_dup = False
            for existing in seen_obs:
                if pattern_clean.lower()[:40] in existing or existing[:40] in pattern_clean.lower():
                    is_dup = True
                    break
            if not is_dup:
                seen_obs.add(pattern_clean.lower())
                combined_obs.append({
                    "pattern": pattern_clean,
                    "confidence": confidence,
                    "type": pattern_type
                })
    return combined_obs


@router.get("/stats", response_model=StatsResponse)
async def get_stats(user_id: str = Depends(get_current_user_id)):
    core = _get_core(user_id)
    xp = core.xp_system
    patterns = core.state.get("_user_patterns", {})
    reflections = core.state.get("_deep_reflections", [])
    milestones = core.state.get("_milestones_stored", [])

    first_msg_time = core.state.get("temporal_context", {}).get("first_message_time")
    days_active = None
    if first_msg_time:
        try:
            start = datetime.fromisoformat(first_msg_time.replace("Z", "+00:00"))
            days_active = (datetime.now(timezone.utc) - start).days
        except Exception:
            pass

    xp_summary = xp.get_xp_summary()
    return StatsResponse(
        total_messages=patterns.get("total_messages", core.personality_evolution.interaction_count),
        longest_streak=xp_summary.get("longest_streak", 0),
        current_streak=xp_summary.get("streak_days", 0),
        current_phase=xp.current_phase,
        total_xp=xp.total_xp,
        inside_joke_count=len(_get_merged_inside_jokes(core)),
        temporal_pattern_count=len(getattr(core.personality_evolution, 'user_temporal_patterns', [])),
        diary_entry_count=len(reflections),
        milestone_count=len(milestones),
        days_active=days_active,
    )


@router.get("/inside-jokes", response_model=InsideJokesResponse)
async def get_inside_jokes(user_id: str = Depends(get_current_user_id)):
    core = _get_core(user_id)
    combined = _get_merged_inside_jokes(core)
    jokes = [
        InsideJoke(
            reference=j["reference"],
            context=j["context"],
            joke_type=j["type"]
        ) for j in combined
    ]
    return InsideJokesResponse(jokes=jokes, phase_required="Deepening")


@router.get("/patterns", response_model=PatternsResponse)
async def get_patterns(user_id: str = Depends(get_current_user_id)):
    core = _get_core(user_id)
    combined = _get_merged_behavioral_observations(core)
    items = [
        PatternItem(
            pattern=o["pattern"],
            confidence=o["confidence"],
            pattern_type=o["type"]
        ) for o in combined
    ]
    return PatternsResponse(patterns=items, phase_required="Connection")



# ═════════════════════════════════════════════════════
#  CHAT — FULL COGNITIVE PIPELINE (same as Discord)
# ═════════════════════════════════════════════════════

@router.post("/chat", response_model=ChatResponse)
async def chat(payload: ChatRequest, user_id: str = Depends(get_current_user_id)):
    """
    Send a message through the FULL cognitive pipeline.
    Uses generate_response() from discord_bot.py — the EXACT same
    function Discord uses. All 40+ prompt params, memory reasoning,
    knowledge grounding, dedup, behavioral tracking, milestones,
    conversation summaries, self-fact extraction, rumination.
    """
    import asyncio

    core = _get_core(user_id)

    if not payload.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    # Store user name if provided
    if payload.user_name and not core.state.get("user_name"):
        core.state["user_name"] = payload.user_name
        core._save_state()

    # Record XP before processing
    xp_before = core.xp_system.total_xp
    phase_before = core.xp_system.current_phase

    # Helper: human-readable time-ago for temporal reasoning
    def _time_ago_label(ts_str: str) -> str:
        """Convert ISO timestamp to a relative time label for the LLM."""
        try:
            ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
            now = datetime.now(timezone.utc)
            delta = now - ts
            hours = delta.total_seconds() / 3600
            if hours < 0.5:
                return ""  # Recent, no label needed
            elif hours < 1:
                return "[said ~30 min ago] "
            elif hours < 24:
                return f"[said {int(hours)}h ago] "
            else:
                days = int(hours / 24)
                return f"[said {days} day{'s' if days != 1 else ''} ago] "
        except Exception:
            return ""

    # Build message history from DB instead of decayed STM to ensure perfect session context
    db = SessionLocal()
    message_history = []
    try:
        active_sess_id = _get_active_session_id(user_id, db)
        
        # Save user message to database
        user_msg_content = payload.message.strip()
        db_user_msg = ChatMessage(session_id=active_sess_id, role="user", content=user_msg_content)
        db.add(db_user_msg)
        
        # Also update session timestamp
        session_row = db.query(ChatSession).filter(ChatSession.id == active_sess_id).first()
        if session_row:
            session_row.updated_at = datetime.now(timezone.utc)
        db.commit()
        
        # Fetch last 11 messages of this session from DB to build history context
        db_history = db.query(ChatMessage).filter(ChatMessage.session_id == active_sess_id, ChatMessage.id != db_user_msg.id).order_by(ChatMessage.timestamp.desc()).limit(11).all()
        db_history = list(reversed(db_history))
        
        for m in db_history:
            ts = m.timestamp.isoformat() if hasattr(m.timestamp, 'isoformat') else str(m.timestamp)
            message_history.append({
                "role": m.role,
                "content": m.content,
                "timestamp": ts,
            })
            
        # Append the current message
        message_history.append({
            "role": "user",
            "content": user_msg_content,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
    except Exception as dbe:
        print(f"Failed to query/persist message database state (using fallback): {dbe}")
        db.rollback()
        # Fallback to STM
        message_history = []
        is_date_active = core.state.get("_active_date_running", False)
        stm = core.memory.get_stm(decay=False, filter_date=is_date_active)
        for m in stm[-11:]:
            content = m.get("content", "")
            if not content:
                continue
            ts = m.get("timestamp", "")
            if content.startswith("[Rem] "):
                message_history.append({
                    "role": "assistant",
                    "content": content[6:],
                    "timestamp": ts,
                })
            elif content.startswith("[User] "):
                message_history.append({
                    "role": "user",
                    "content": content[7:],
                    "timestamp": ts,
                })
            else:
                message_history.append({
                    "role": "user",
                    "content": content,
                    "timestamp": ts,
                })
        message_history.append({
            "role": "user",
            "content": payload.message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
    finally:
        db.close()

    # Call Discord's generate_response — FULL pipeline
    try:
        from .discord_bot import generate_response, _generate_conversation_summary

        # The frontend calls the backend API directly (NEXT_PUBLIC_API_URL on Railway),
        # NOT through Vercel serverless functions, so there is no 10s gateway limit.
        # Let the pipeline run with its own internal timeouts (60-120s process_message, 30s LLM calls).
        response_text, processing_result = await generate_response(
            core, payload.message, message_history, return_processing_result=True
        )
        if response_text == "__RATE_LIMITED__":
            raise asyncio.TimeoutError("Rate limited")
            
        if not response_text or response_text.startswith("⚠️"):
            raise ValueError(response_text or "No response generated")
    except (asyncio.TimeoutError, Exception) as e:
        print(f"[WEB CHAT] Pipeline timeout, rate limit, or error ({type(e).__name__}): triggering in-character fallback response")
        fallbacks = [
            "sorry, my signal was acting up for a sec. what were you saying?",
            "ah sorry, i got a bit distracted. what was that again?",
            "sorry, my phone glitched out. say that again?",
            "sorry about that, my connection dropped. what did you say?",
            "hey, sorry! had a brief lag on my end. could you repeat that?"
        ]
        import random
        response_text = random.choice(fallbacks)

    # Save Rem's response to database
    db = SessionLocal()
    try:
        active_sess_id = _get_active_session_id(user_id, db)
        db_assistant_msg = ChatMessage(session_id=active_sess_id, role="assistant", content=response_text)
        db.add(db_assistant_msg)
        
        session_row = db.query(ChatSession).filter(ChatSession.id == active_sess_id).first()
        if session_row:
            session_row.updated_at = datetime.now(timezone.utc)
        db.commit()
    except Exception as dbe:
        print(f"Failed to save assistant response: {dbe}")
        db.rollback()
    finally:
        db.close()

    # Calculate typing delay based on response length and schedule/circadian multipliers
    base_delay = 0.8
    char_delay = len(response_text) * 0.012  # 12ms per character
    delay = base_delay + char_delay

    try:
        from .daily_life import get_current_activity
        current_activity = get_current_activity(core.state)
    except Exception:
        current_activity = None

    temporal = core.state.get("temporal_context", {})
    circadian = temporal.get("circadian_phase", "")

    multiplier = 1.0
    if current_activity == "Sleeping":
        multiplier = 2.5
    elif current_activity in ("Class", "Studying"):
        multiplier = 2.0
    elif current_activity == "Commuting":
        multiplier = 1.5
    elif circadian == "deep_night":
        multiplier = 2.0

    delay = delay * multiplier
    delay = min(delay, 5.0)  # Cap at 5s to avoid freezing the UI experience too long

    print(f"[CHAT DELAY] Simulating typing delay of {delay:.2f}s (activity: {current_activity}, multiplier: {multiplier})")
    await asyncio.sleep(delay)

    # Fire background task (same as Discord's handle_dm)
    try:
        asyncio.create_task(_generate_conversation_summary(core, message_history))
    except Exception:
        pass

    # Calculate XP delta + phase transition
    xp_after = core.xp_system.total_xp
    xp_delta = xp_after - xp_before
    phase_after = core.xp_system.current_phase

    phase_transition = None
    new_unlocks = None
    if phase_after != phase_before:
        phase_transition = {"from": phase_before, "to": phase_after}
        new_unlocks = core.xp_system.get_phase_unlocks(phase_after)

    # Consume pending rank transitions
    notifications = core.xp_system.get_pending_notifications()
    rank_transition = notifications[0] if notifications else None

    # Calculate progress percent to next rank
    xp_summary = core.xp_system.get_xp_summary()
    rank_progress = xp_summary.get("progress_pct", 0.0)

    # Get current emotional metrics
    current_psyche = core.state.get("current_psyche", {})
    hurt_val = round(current_psyche.get("hurt", 0.0), 2)
    anger_val = round(current_psyche.get("anger", 0.0), 2)

    # Compute split reply parts for natural double-texting experience
    try:
        from .human_messaging import smart_split
        parts = smart_split(response_text)
    except Exception:
        parts = [response_text]

    # Populate roleplay, schedule and plans
    roleplay_data = None
    try:
        from .daily_life import get_current_activity_details
        act_details = get_current_activity_details(core.state)
        roleplay_data = {
            "active": act_details.get("is_user_plan", False),
            "activity": act_details.get("activity", "just chilling"),
            "location": act_details.get("location", "home")
        }
    except Exception as e:
        print(f"[WEB API] Error loading roleplay details: {e}")
        
    full_schedule = core.state.get("_daily_schedule", {}).get("schedule", [])
    future_plans = core.state.get("_future_plans", [])

    # Save the updated state to persist consumed notifications, rank, XP and mood changes
    try:
        core._save_state()
    except Exception as e:
        print(f"[WEB API] Error persisting state: {e}")

    return ChatResponse(
        reply=response_text,
        reply_parts=parts,
        xp_delta=xp_delta if xp_delta else None,
        phase_transition=phase_transition,
        new_unlocks=new_unlocks,
        current_xp=xp_after,
        current_phase=phase_after,
        current_rank=core.xp_system.current_rank,
        rank_progress_pct=rank_progress,
        rank_transition=rank_transition,
        hurt=hurt_val,
        anger=anger_val,
        roleplay=roleplay_data,
        schedule=full_schedule,
        future_plans=future_plans,
        streak_days=core.xp_system.streak_days
    )


# ═════════════════════════════════════════════════════
#  NEW ENDPOINTS — Previously Discord-only features
# ═════════════════════════════════════════════════════

# ── MEMORY (maps to !memory) ──

import re

def _clean_and_format_memory_content(content: str, event_type: str) -> str:
    if not content:
        return ""
    
    # 1. Clean explicit_bookmark
    if event_type == "explicit_bookmark" or content.startswith(("[User]", "[Rem]")):
        if content.startswith("[User]"):
            val = content[len("[User]"):].strip()
            return f"You: \"{val}\""
        elif content.startswith("[Rem]"):
            val = content[len("[Rem]"):].strip()
            return f"I: \"{val}\""
    
    # 2. Clean own_reaction
    if event_type == "own_reaction" or content.startswith("Shifted from"):
        # Match Shifted from 'x' to 'y'. [details] I said: "..."
        match = re.match(r"Shifted from\s+'[^']+'\s+to\s+'([^']+)'\.\s*(.*?)\s*I said:\s*(.*)", content, re.DOTALL)
        if match:
            to_state = match.group(1)
            details = match.group(2).strip()
            said = match.group(3).strip()
            if details:
                if not details.endswith('.'):
                    details += '.'
                return f"I felt {to_state} ({details.lower().rstrip('.')}) and said: {said}"
            else:
                return f"I felt {to_state} and said: {said}"
        
        # Match Shifted from 'x' to 'y'. [details]
        match2 = re.match(r"Shifted from\s+'[^']+'\s+to\s+'([^']+)'\.\s*(.*)", content, re.DOTALL)
        if match2:
            to_state = match2.group(1)
            details = match2.group(2).strip()
            if details:
                return f"I felt {to_state} - {details}"
            return f"I felt {to_state}"
            
    # 3. Handle third-person to first-person translation
    s = content
    
    # Strip thoughts/thinks indicators
    s = re.sub(r'<think>.*?</think>', '', s, flags=re.DOTALL)
    s = re.sub(r'\*thinks\s*>\s*', '', s, flags=re.IGNORECASE)
    s = re.sub(r'\*thinks\*\s*', '', s, flags=re.IGNORECASE)
    
    # Strip text tag wrappers while retaining the enclosed content
    s = re.sub(r'<text>(.*?)</text>', r'\1', s, flags=re.DOTALL | re.IGNORECASE)
    s = re.sub(r'</?text>', '', s, flags=re.IGNORECASE)
    
    s = re.sub(r"\bRem's\b", "my", s, flags=re.IGNORECASE)
    s = re.sub(r"\bRem'\b", "my", s, flags=re.IGNORECASE)
    s = re.sub(r"\bRem\b", "I", s, flags=re.IGNORECASE)
    
    s = re.sub(r"\bthe user's\b", "your", s, flags=re.IGNORECASE)
    s = re.sub(r"\buser's\b", "your", s, flags=re.IGNORECASE)
    s = re.sub(r"\bthe user\b", "you", s, flags=re.IGNORECASE)
    s = re.sub(r"\buser\b", "you", s, flags=re.IGNORECASE)
    
    # Plural translations (before singular replacements)
    s = re.sub(r"\bthey both\b", "we both", s, flags=re.IGNORECASE)
    s = re.sub(r"\bthem both\b", "us both", s, flags=re.IGNORECASE)
    s = re.sub(r"\bthey were\b", "we were", s, flags=re.IGNORECASE)
    s = re.sub(r"\bthey are\b", "we are", s, flags=re.IGNORECASE)
    s = re.sub(r"\bthey have\b", "we have", s, flags=re.IGNORECASE)
    s = re.sub(r"\bthey had\b", "we had", s, flags=re.IGNORECASE)
    s = re.sub(r"\bthey mutually\b", "we mutually", s, flags=re.IGNORECASE)
    s = re.sub(r"\bthey shared\b", "we shared", s, flags=re.IGNORECASE)
    s = re.sub(r"\bthey bonded\b", "we bonded", s, flags=re.IGNORECASE)
    s = re.sub(r"\bthey agreed\b", "we agreed", s, flags=re.IGNORECASE)
    s = re.sub(r"\bthey talked\b", "we talked", s, flags=re.IGNORECASE)
    s = re.sub(r"\bthey laughed\b", "we laughed", s, flags=re.IGNORECASE)
    
    s = re.sub(r"\btheir\b", "your", s, flags=re.IGNORECASE)
    s = re.sub(r"\bthem\b", "you", s, flags=re.IGNORECASE)
    s = re.sub(r"\bthey\b", "you", s, flags=re.IGNORECASE)
    s = re.sub(r"\bhimself/herself/themselves\b", "yourself", s, flags=re.IGNORECASE)
    
    # Verb correction for 'you'
    s = re.sub(r"\byou was\b", "you were", s, flags=re.IGNORECASE)
    s = re.sub(r"\byou is\b", "you are", s, flags=re.IGNORECASE)
    s = re.sub(r"\byou has\b", "you have", s, flags=re.IGNORECASE)
    s = re.sub(r"\byou seems\b", "you seem", s, flags=re.IGNORECASE)
    s = re.sub(r"\byou feels\b", "you feel", s, flags=re.IGNORECASE)
    s = re.sub(r"\byou wants\b", "you want", s, flags=re.IGNORECASE)
    s = re.sub(r"\byou looks\b", "you look", s, flags=re.IGNORECASE)
    s = re.sub(r"\byou thinks\b", "you think", s, flags=re.IGNORECASE)
    s = re.sub(r"\byou makes\b", "you make", s, flags=re.IGNORECASE)
    s = re.sub(r"\byou agrees\b", "you agreed", s, flags=re.IGNORECASE)
    
    # Verb correction for 'I'
    s = re.sub(r"\bI feels\b", "I feel", s, flags=re.IGNORECASE)
    s = re.sub(r"\bI wants\b", "I want", s, flags=re.IGNORECASE)
    s = re.sub(r"\bI thinks\b", "I think", s, flags=re.IGNORECASE)
    s = re.sub(r"\bI is\b", "I am", s, flags=re.IGNORECASE)
    s = re.sub(r"\bI has\b", "I have", s, flags=re.IGNORECASE)
    s = re.sub(r"\bI plays\b", "I play", s, flags=re.IGNORECASE)
    s = re.sub(r"\bI says\b", "I say", s, flags=re.IGNORECASE)
    s = re.sub(r"\bI teases\b", "I teased", s, flags=re.IGNORECASE)
    s = re.sub(r"\bI playfully teases\b", "I playfully teased", s, flags=re.IGNORECASE)
    s = re.sub(r"\bI playfully teased\b", "I playfully teased", s, flags=re.IGNORECASE)
    
    # Prefix verbs if it starts with a verb
    verbs = [
        "Discussed", "Talked", "Shared", "Exchanged", "Argued", "Agreed", "Went", 
        "Had", "Made", "Planned", "Told", "Asked", "Showed", "Felt", "Wished", 
        "Wanted", "Joked", "Laughed", "Smiled", "Wondered", "Opened", "Expressed"
    ]
    words = s.split()
    if words:
        first_word = words[0].rstrip(',.:;!?')
        if first_word in verbs:
            s = "We " + s[0].lower() + s[1:]
        elif first_word.lower() in [v.lower() for v in verbs]:
            s = "We " + s
            
    s = re.sub(r"\s+", " ", s).strip()
    if s:
        s = s[0].upper() + s[1:]
        
    return s

def _clean_and_format_fact(fact: str) -> str:
    if not fact:
        return ""
    
    s = fact.strip()
    words = s.split()
    if words:
        first = words[0].lower()
        if first == "not" and len(words) > 1 and (words[1].lower() in ["into", "interested", "reading", "studying", "working"]):
            s = "You are " + s
        elif first.endswith("s") or first.endswith("ing") or first.endswith("ed") or first in ["read", "like", "love", "hate", "want", "need", "have", "has", "is", "into", "studying", "reading", "working", "interested"]:
            if first in ["into", "studying", "reading", "working", "interested"]:
                s = "You are " + s
            elif first.endswith("s"):
                if first == "is":
                    words[0] = "are"
                elif first == "has":
                    words[0] = "have"
                elif first == "thinks":
                    words[0] = "think"
                elif first == "likes":
                    words[0] = "like"
                elif first == "loves":
                    words[0] = "love"
                elif first == "wants":
                    words[0] = "want"
                elif first == "needs":
                    words[0] = "need"
                elif first == "feels":
                    words[0] = "feel"
                elif first == "hates":
                    words[0] = "hate"
                elif first == "knows":
                    words[0] = "know"
                elif first == "believes":
                    words[0] = "believe"
                elif first == "prefers":
                    words[0] = "prefer"
                else:
                    if len(first) > 3:
                        words[0] = first[:-1]
                s = "You " + " ".join(words)
            else:
                s = "You " + s

    s = re.sub(r"\bthe user's\b", "your", s, flags=re.IGNORECASE)
    s = re.sub(r"\buser's\b", "your", s, flags=re.IGNORECASE)
    s = re.sub(r"\bthe user\b", "you", s, flags=re.IGNORECASE)
    s = re.sub(r"\buser\b", "you", s, flags=re.IGNORECASE)
    s = re.sub(r"\bRem's\b", "my", s, flags=re.IGNORECASE)
    s = re.sub(r"\bRem\b", "me", s, flags=re.IGNORECASE)
    
    s = re.sub(r"\s+", " ", s).strip()
    if s:
        s = s[0].upper() + s[1:]
        
    return s


@router.get("/memory")
async def get_memory(user_id: str = Depends(get_current_user_id)):
    """Full memory hierarchy: STM, episodic, identity."""
    core = _get_core(user_id)
    stm = core.memory.get_stm(decay=False, filter_date=False)
    # Filter out summary entries from STM to keep them out of topics and memory display
    stm_filtered = [m for m in stm if not m.get("content", "").startswith("[Summary of")]
    
    episodic = core.memory.get_episodic(min_salience=0.1)
    identity = core.memory.get_identity(min_confidence=0.3)

    return {
        "stm": {
            "count": len(stm_filtered),
            "entries": [{"content": m.get("content", "")[:200], "timestamp": m.get("timestamp", ""), "topic": m.get("topic", "")} for m in stm_filtered[-20:]],
        },
        "episodic": {
            "count": len(episodic),
            "entries": [
                {"content": _clean_and_format_memory_content(m.get("content", "")[:200], m.get("event_type", "")), "event_type": m.get("event_type", ""), "salience": round(m.get("salience", 0), 2), "emotional_valence": round(m.get("emotional_valence", 0), 2), "timestamp": m.get("timestamp", "")}
                for m in sorted(episodic, key=lambda x: x.get("salience", 0), reverse=True)[:30]
            ],
        },
        "identity": {
            "count": len(identity),
            "facts": [{"fact": _clean_and_format_fact(m.get("fact", "")), "confidence": round(m.get("confidence", 0), 2), "source": m.get("source", ""), "timestamp": m.get("timestamp", "")} for m in identity[:50]],
        },
    }


@router.post("/memories")
async def add_explicit_memory(payload: RememberRequest, user_id: str = Depends(get_current_user_id)):
    """Add a user-bookmarked explicit memory directly to episodic memory."""
    core = _get_core(user_id)
    prefix = "[User]" if payload.role == "user" else "[Rem]"
    formatted_content = f"{prefix} {payload.content}"
    
    # Save as high-salience explicit bookmark
    core.memory.add_episodic(
        event_type="explicit_bookmark",
        content=formatted_content,
        emotional_valence=0.4,
        relational_impact=0.9
    )
    core._save_state()
    return {"success": True, "message": "Memory successfully saved."}


# ── PERSONALITY (maps to !personality) ──

@router.get("/personality")
async def get_personality(user_id: str = Depends(get_current_user_id)):
    """Rem's personality state, expression guidance, vibes, psyche layers."""
    core = _get_core(user_id)
    phase = core.relationship_phases.current_phase
    trust = core.psyche.psyche.get("trust", 0.3)

    try:
        pe_state = core.personality_evolution.get_full_state()
        vibe_palette = pe_state.get("vibe_palette", []) if isinstance(pe_state, dict) else []
        current_interests = pe_state.get("current_interests", []) if isinstance(pe_state, dict) else []
    except Exception:
        vibe_palette, current_interests = [], []

    try:
        named_mood = core.psyche.get_named_mood_state()
    except Exception:
        named_mood = {}

    starting_archetype = core.state.get("current_psyche", {}).get("starting_archetype", "neutral")
    
    # Calculate evolved branch dynamically based on relationship phase and state
    try:
        from .prompt_distiller import evolve_archetype
        hurt = core.psyche.psyche.get("hurt", 0.0) if hasattr(core.psyche, 'psyche') else core.state.get("current_psyche", {}).get("hurt", 0.0)
        unresolved_wounds = core.psyche.get_unresolved_wounds() if hasattr(core.psyche, 'get_unresolved_wounds') else []
        undercurrents = core.state.get("emotional_undercurrents", [])
        
        branch_info = evolve_archetype(
            archetype=starting_archetype,
            phase=phase,
            trust=trust,
            hurt=hurt,
            active_wounds=unresolved_wounds,
            active_undercurrents=undercurrents
        )
        if phase == "Discovery":
            evolved_branch = "Not Evolved Yet"
        else:
            evolved_branch = branch_info.get("branch", starting_archetype)
    except Exception as e:
        print(f"[API] Failed to compute dynamic evolved_branch: {e}")
        evolved_branch = "Not Evolved Yet" if phase == "Discovery" else core.state.get("current_psyche", {}).get("evolved_branch", "neutral_balanced")

    return {
        "personality_text": core.personality_evolution.get_personality_text(),
        "personality_summary": core.personality_evolution.get_personality_summary(),
        "expression_guidance": core.personality_evolution.get_expression_guidance(trust, phase),
        "vibe_palette": vibe_palette,
        "current_interests": current_interests,
        "habits_cpbm": core.state.get("habits_cpbm", {}),
        "micro_personality": core.state.get("micro_personality", {}),
        "starting_archetype": starting_archetype,
        "evolved_branch": evolved_branch,
        "persona_flavor": core.state.get("_self_identity", {}).get("_persona_flavor", ""),
        "psyche": {
            "stance": core.psyche.stance,
            "respect": round(core.psyche.respect, 2) if core.psyche.respect else 0,
            "engagement": round(core.psyche.engagement, 2) if core.psyche.engagement else 0,
            "posture": core.psyche.posture,
            "named_mood": named_mood,
            "starting_archetype": starting_archetype,
            "evolved_branch": evolved_branch,
            "neurochem": {
                "dopamine": round(core.psyche.neurochem.get("da", 0.5), 2),
                "cortisol": round(core.psyche.neurochem.get("cort", 0.3), 2),
                "oxytocin": round(core.psyche.neurochem.get("oxy", 0.5), 2),
                "serotonin": round(core.psyche.neurochem.get("ser", 0.5), 2),
                "endorphins": round(core.psyche.neurochem.get("endo", 0.5), 2),
            },
            # Individual mood metrics for frontend display (prevents fallback to 0%)
            "playfulness": core.state.get("mood", {}).get("playfulness", 0.0),
            "affection": core.state.get("mood", {}).get("affection", 0.0),
            "anger": core.state.get("mood", {}).get("anger", 0.0),
            "anxiety": core.state.get("mood", {}).get("anxiety", 0.0),
            "boredom": core.state.get("mood", {}).get("boredom", 0.0),
            "excitement": core.state.get("mood", {}).get("excitement", 0.0),
            "sadness": core.state.get("mood", {}).get("sadness", 0.0),
            "vulnerability": core.state.get("mood", {}).get("vulnerability", 0.0),
        },
        "phase": phase,
        "trust": round(trust, 2),
        "energy": round(core.embodiment.E_daily, 2),
    }


# ── IDENTITY (maps to !identity + !about) ──

@router.get("/identity")
async def get_identity(user_id: str = Depends(get_current_user_id)):
    """What Rem knows about the user."""
    core = _get_core(user_id)
    identity_memories = core.memory.get_identity(min_confidence=0.3)

    about_user, world_knowledge = [], []
    for m in identity_memories:
        fact = m.get("fact", "")
        if fact.startswith("[knowledge]"):
            world_knowledge.append(fact)
        else:
            about_user.append({"fact": fact, "confidence": round(m.get("confidence", 0), 2), "timestamp": m.get("timestamp", "")})

    return {
        "about_user": about_user,
        "user_facts": core.state.get("_user_facts", {}),
        "user_learned_facts": core.state.get("user_learned_facts", {}),
        "world_knowledge": world_knowledge[:20],
        "user_evaluation": core.personality_evolution.get_user_evaluation(),
        "conversation_context": core.personality_evolution.get_conversation_context(),
        "core_identity": {
            "Occupation": "College student",
            "Major": "Psychology",
            "Living": "Lives at home",
            "Commute": "~30 min to college",
        },
        "expression_guidance": core.personality_evolution.get_expression_guidance(
            core.psyche.psyche.get("trust", 0.3),
            core.relationship_phases.current_phase,
        ),
        "relationship": {
            "phase": core.relationship_phases.current_phase,
            "phase_description": core.relationship_phases.get_phase_description(),
            "trust": round(core.psyche.psyche.get("trust", 0.3), 2),
            "hurt": round(core.psyche.psyche.get("hurt", 0.0), 2),
            "anger": round(getattr(core.psyche, "anger", 0.0), 2),
            "entitlement_debt": round(getattr(core.psyche, 'entitlement_debt', 0.0), 2),
            "reciprocity_balance": round(core.reciprocity_ledger.balance, 2),
        },
    }


def _get_fact_value(fact_entry):
    if isinstance(fact_entry, dict):
        return fact_entry.get("v", "")
    return str(fact_entry) if fact_entry is not None else ""


@router.post("/profile")
async def update_profile(payload: ProfileRequest, user_id: str = Depends(get_current_user_id)):
    """Update preferred name, gender, and pronouns in user facts."""
    core = _get_core(user_id)
    
    stored_user = core.state.get("_user_facts", {})
    if not isinstance(stored_user, dict):
        stored_user = {}
        
    updated = False
    
    if payload.preferred_name is not None:
        name_val = payload.preferred_name.strip()
        if name_val:
            stored_user["preferred_name"] = {"v": name_val, "t": datetime.now(timezone.utc).isoformat()}
            core.state["user_name"] = name_val
            updated = True
            
    if payload.gender is not None:
        gender_val = payload.gender.strip()
        if gender_val:
            stored_user["gender"] = {"v": gender_val, "t": datetime.now(timezone.utc).isoformat()}
            updated = True
            
    if payload.pronouns is not None:
        pronouns_val = payload.pronouns.strip()
        if pronouns_val:
            stored_user["pronouns"] = {"v": pronouns_val, "t": datetime.now(timezone.utc).isoformat()}
            updated = True
            
    if updated:
        core.state["_user_facts"] = stored_user
        core._save_state()
        
    return {
        "success": True,
        "user_facts": {
            "preferred_name": _get_fact_value(stored_user.get("preferred_name")),
            "gender": _get_fact_value(stored_user.get("gender")),
            "pronouns": _get_fact_value(stored_user.get("pronouns")),
        }
    }


# ── STATE (maps to !state) ──

@router.get("/state")
async def get_state(user_id: str = Depends(get_current_user_id)):
    """Full psyche and embodiment state."""
    core = _get_core(user_id)
    return {
        "psyche": core.psyche.get_psyche_summary(),
        "embodiment": {"energy": round(core.embodiment.E_daily, 2)},
        "relationship": {
            "phase": core.relationship_phases.current_phase,
            "phase_description": core.relationship_phases.get_phase_description(),
        },
        "interaction_count": core.personality_evolution.interaction_count,
        "conflict_stage": core.conflict_lifecycle.current_stage,
    }


# ── SCHEDULE (maps to !sched) ──

@router.get("/schedule")
async def get_schedule(user_id: str = Depends(get_current_user_id)):
    """Rem's daily schedule and current activity."""
    core = _get_core(user_id)
    
    # Ensure daily schedule is synchronized before returning
    try:
        from .daily_life import ensure_daily_schedule
        await ensure_daily_schedule(core.state)
        core._save_state()  # PERSIST the generated schedule
    except Exception:
        pass

    schedule_data = core.state.get("_daily_schedule", {})
    temporal = core.state.get("temporal_context", {})

    current_activity = "just chilling"
    is_roleplay_mode = False
    location = "home"
    try:
        from .daily_life import get_current_activity_details
        details = get_current_activity_details(core.state)
        current_activity = details.get("activity", "just chilling")
        is_roleplay_mode = details.get("is_user_plan", False)
        location = details.get("location", "home")
    except Exception:
        pass

    return {
        "schedule": schedule_data.get("schedule", []),
        "overrides": schedule_data.get("overrides", []),
        "current_activity": current_activity,
        "is_roleplay_mode": is_roleplay_mode,
        "location": location,
        "circadian_phase": temporal.get("circadian_phase", "afternoon"),
        "future_plans": core.state.get("_future_plans", []),
        "streak_days": core.xp_system.streak_days
    }


# ── FUTURE PLANS ──

@router.get("/plans")
async def get_user_plans(user_id: str = Depends(get_current_user_id)):
    core = _get_core(user_id)
    return core.state.get("_future_plans", [])


@router.post("/plans")
async def add_user_plan(plan: PlanRequest, user_id: str = Depends(get_current_user_id)):
    core = _get_core(user_id)
    try:
        from .daily_life import add_future_plan, _sync_future_plans_to_overrides, IST
        add_future_plan(core.state, plan.date, plan.start, plan.end, plan.activity, plan.location)
        core._save_state()
        
        # If today, sync it
        now = datetime.now(IST)
        today = now.strftime("%Y-%m-%d")
        if plan.date == today:
            _sync_future_plans_to_overrides(core.state, today)
            core._save_state()
            
        return {"success": True, "plans": core.state.get("_future_plans", [])}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/plans")
async def cancel_user_plan(date: str, start: str, end: str, user_id: str = Depends(get_current_user_id)):
    core = _get_core(user_id)
    try:
        from .daily_life import IST
        future_plans = core.state.get("_future_plans", [])
        # Filter out this plan
        filtered = [
            p for p in future_plans
            if not (p.get("date") == date and p.get("start") == start and p.get("end") == end)
        ]
        core.state["_future_plans"] = filtered
        
        # Also remove from today's overrides if applicable
        schedule_data = core.state.get("_daily_schedule", {})
        overrides = schedule_data.get("overrides", [])
        overrides = [
            o for o in overrides
            if not (o.get("start") == start and o.get("end") == end and o.get("is_user_plan") == True)
        ]
        schedule_data["overrides"] = overrides
        core.state["_daily_schedule"] = schedule_data
        
        core._save_state()
        return {"success": True, "plans": filtered}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/end-date")
async def end_active_date(user_id: str = Depends(get_current_user_id)):
    core = _get_core(user_id)
    try:
        schedule_data = core.state.get("_daily_schedule", {})
        overrides = schedule_data.get("overrides", [])
        
        from datetime import datetime
        from .daily_life import IST
        now = datetime.now(IST)
        current_time = now.strftime("%H:%M")
        
        active_user_plan = None
        for o in overrides:
            start = o.get("start", "")
            end = o.get("end", "")
            if o.get("is_user_plan", False) and start <= current_time < end:
                active_user_plan = o
                break
                
        # Filter out all is_user_plan overrides
        new_overrides = [
            o for o in overrides
            if not o.get("is_user_plan", False)
        ]
        
        schedule_data["overrides"] = new_overrides
        core.state["_daily_schedule"] = schedule_data
        
        # Apply relationship penalties if ended early
        if active_user_plan:
            activity = active_user_plan.get("activity", "hanging out")
            location = active_user_plan.get("location", "somewhere")
            
            # Trust penalty: decrease by 0.1
            current_trust = core.psyche.psyche.get("trust", 0.7)
            core.psyche.psyche["trust"] = max(0.0, round(current_trust - 0.1, 2))
            
            # Hurt increase: increase by 0.05
            current_hurt = core.psyche.psyche.get("hurt", 0.0)
            core.psyche.psyche["hurt"] = min(1.0, round(current_hurt + 0.05, 2))
            
            # Engagement penalty: decrease by 0.1
            core.psyche.update_engagement(-0.1)
            
            # Create an unresolved wound immediately
            try:
                core.psyche.create_wound(
                    cause=f"User abruptly ended our date early at {location} while we were {activity}.",
                    intensity=0.7
                )
            except Exception as wound_err:
                print(f"[WEB API] Error creating wound: {wound_err}")
                
            # Inject immediate negative emotional undercurrent based on phase
            try:
                phase = core.relationship_phases.current_phase
                negative_emotions = {
                    "Discovery": "frustration",
                    "Building": "disappointment",
                    "Steady": "attachment_anxiety",
                    "Deep": "deep_hurt",
                    "Bonded": "deep_hurt",
                    "Volatile": "betrayal",
                    "Maintenance": "passive_aggression"
                }
                selected_undercurrent = negative_emotions.get(phase, "disappointment")
                
                if not hasattr(core.personality_evolution, "emotional_undercurrents") or core.personality_evolution.emotional_undercurrents is None:
                    core.personality_evolution.emotional_undercurrents = []
                
                core.personality_evolution.emotional_undercurrents.append({
                    "emotion": selected_undercurrent,
                    "intensity": 0.7,
                    "trigger": f"User ended the date early at {location}"
                })
                core.personality_evolution.emotional_undercurrents = core.personality_evolution.emotional_undercurrents[-5:]
                core.personality_evolution.save()
            except Exception as uc_err:
                print(f"[WEB API] Error injecting emotional undercurrent: {uc_err}")
            
            # Record negative episodic memory
            try:
                core.memory.add_episodic(
                    event_type="date_ended_early",
                    content=f"User abruptly ended our date early at {location} while we were {activity}.",
                    emotional_valence=-0.6,
                    relational_impact=-0.5
                )
            except Exception as mem_err:
                print(f"[WEB API] Error saving end-date memory: {mem_err}")
                
            # Write early end journal entry
            try:
                await core.diary.write_date_journal_entry(core, activity, location, ended_early=True)
            except Exception as journal_err:
                print(f"[WEB API] Error writing date journal: {journal_err}")
                
            # Remove completed plan from future plans to prevent loops
            try:
                start = active_user_plan.get("start", "")
                end = active_user_plan.get("end", "")
                today_str = now.strftime("%Y-%m-%d")
                future_plans = core.state.get("_future_plans", [])
                core.state["_future_plans"] = [
                    p for p in future_plans
                    if not (p.get("date") == today_str and p.get("start") == start and p.get("end") == end)
                ]
            except Exception as plans_err:
                print(f"[WEB API] Error cleaning up plan: {plans_err}")
                
        core.state["_active_date_running"] = False
        core._save_state()
        return {"success": True, "message": "Date mode ended early. Relational impact applied."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── COMPLEXITY (maps to !complexity) ──

@router.get("/complexity")
async def get_complexity(user_id: str = Depends(get_current_user_id)):
    """Cognitive routing stats, inner monologue, rumination."""
    core = _get_core(user_id)
    return {
        "conversation_summary": core.personality_evolution.conversation_summary,
        "emotional_undercurrents": core.personality_evolution.emotional_undercurrents,
        "rumination": core.state.get("_rumination"),
        "inner_monologue": core.state.get("_inner_monologue", []),
        "pending_eruption": core.state.get("_pending_eruption"),
        "knowledge_holes": core.state.get("_knowledge_holes", []),
        "recent_claims": core.state.get("_rem_recent_claims", [])[-5:],
        "self_identity": core.state.get("_self_identity", {}),
    }


# ── DEBUG (maps to !debug) ──

@router.get("/debug")
async def get_debug(user_id: str = Depends(get_current_user_id)):
    """Raw state keys and sizes for debugging."""
    core = _get_core(user_id)
    state_keys = {}
    for key, value in core.state.items():
        if isinstance(value, (list, dict)):
            state_keys[key] = {"type": type(value).__name__, "size": len(value)}
        elif isinstance(value, str):
            state_keys[key] = {"type": "str", "size": len(value)}
        else:
            state_keys[key] = {"type": type(value).__name__, "value": str(value)[:100]}
    return {
        "user_id": core.user_id,
        "state_keys": state_keys,
        "total_keys": len(state_keys),
        "memory_stats": {
            "stm_count": len(core.memory.get_stm(decay=False)),
            "episodic_count": len(core.memory.get_episodic(min_salience=0.0)),
            "identity_count": len(core.memory.get_identity(min_confidence=0.0)),
        },
    }


# ── RESET (maps to !reset) ──

@router.post("/reset")
async def reset_user(user_id: str = Depends(get_current_user_id)):
    """NUCLEAR RESET — wipe ALL state for this user and generate fresh persona."""
    import sqlite3
    import os
    
    # Resolve the actual core_id (handles Discord linking)
    try:
        core_id = resolve_core_id(user_id)
    except Exception:
        core_id = user_id
    
    # 1. Delete state from main database
    try:
        from .state import get_state_orchestrator
        state_orch = get_state_orchestrator()
        state_orch.delete_state(core_id)
        print(f"[RESET] Cleared user_state for {core_id}")
    except Exception as e:
        print(f"[RESET] DB delete failed: {e}")
    
    # 2. Clear semantic memory embeddings
    try:
        from .semantic_search import get_semantic_search
        sem = get_semantic_search()
        sem.remove_user(core_id)
        print(f"[RESET] Cleared semantic embeddings for {core_id}")
    except Exception as e:
        print(f"[RESET] Semantic clear failed: {e}")
    
    # 3. Clear FTS5 memory search index
    try:
        from .memory_search import get_memory_search
        fts = get_memory_search()
        fts.remove_user(core_id)
        print(f"[RESET] Cleared FTS5 index for {core_id}")
    except Exception as e:
        print(f"[RESET] FTS5 clear failed: {e}")
    
    # 4. Remove from ALL caches
    try:
        from .discord_bot import active_cores
        for key in list(active_cores.keys()):
            if key == user_id or key == core_id or key == user_id.replace("web_user_", ""):
                del active_cores[key]
                print(f"[RESET] Removed from discord active_cores: {key}")
    except Exception:
        pass
    
    # 5. Reinitialize with completely fresh state
    core = _get_core(user_id)
    
    # 6. Generate fresh persona flavor via LLM
    persona_flavor = None
    try:
        import httpx
        import json
        import random
        import re
        
        fallback_seeds = [
            {
                "obsession": {
                    "topic": "Elden Ring lore",
                    "details": "She spends hours reading theories about Miquella and Malenia's relationship on Reddit.",
                    "trigger_keywords": ["game", "play", "elden", "ring", "bored", "night", "hobby"]
                },
                "drama": {
                    "topic": "Mother nagging about switching to business",
                    "details": "Her mom keeps sending articles about business analyst job prospects, warning her psychology has no career future.",
                    "trigger_keywords": ["mom", "parent", "college", "study", "major", "career", "annoyed"]
                },
                "hot_take": {
                    "topic": "Pineapple pizza is a crime",
                    "details": "She insists pineapple on pizza violates the basic principles of taste and balance and is a culinary war crime.",
                    "trigger_keywords": ["food", "eat", "dinner", "taste", "pizza", "pineapple"]
                },
                "deep_secret": {
                    "topic": "Fear of clinical failure",
                    "details": "She's secretly terrified she lacks the emotional endurance to be a clinical psychologist and will get burnt out in a year.",
                    "trigger_keywords": ["future", "clinical", "psychology", "secret", "worry", "afraid", "dream"]
                },
                "pet_peeve": {
                    "topic": "Slow walkers on campus",
                    "details": "She gets extremely annoyed by people walking side-by-side on narrow sidewalks during class change times.",
                    "trigger_keywords": ["walk", "campus", "slow", "annoyed", "people"]
                },
                "guilty_pleasure": {
                    "topic": "Trashy reality TV dating shows",
                    "details": "She watches entire seasons of Love is Blind in one sitting, writing notes on the couples' body language.",
                    "trigger_keywords": ["tv", "show", "watch", "dating", "reality"]
                },
                "communication_quirks": {
                    "style": "Fast lowercase typing, short sentences, dry emotes like 🧍, rare capitalization.",
                    "favorite_phrases": ["lol", "bruh", "literally", "i can't"]
                }
            },
            {
                "obsession": {
                    "topic": "Vintage film cameras",
                    "details": "She bought an old 35mm Olympus camera and spends all her money on film development and scan tools.",
                    "trigger_keywords": ["photo", "camera", "film", "picture", "hobby", "art", "vintage"]
                },
                "drama": {
                    "topic": "A roommate who never does dishes",
                    "details": "Her roommate constantly leaves crusty bowls in the sink, arguing it is 'soaking' for three days straight.",
                    "trigger_keywords": ["roommate", "dorm", "apartment", "wash", "dish", "clean", "annoyed"]
                },
                "hot_take": {
                    "topic": "Quiet luxury is just boring",
                    "details": "She thinks the 'quiet luxury' aesthetic is just an excuse for people to wear beige blankets and look dull.",
                    "trigger_keywords": ["style", "fashion", "luxury", "clothes", "wear", "beige"]
                },
                "deep_secret": {
                    "topic": "Imposter syndrome in academics",
                    "details": "She cheated on a major chemistry quiz in freshman year and still feels like her entire academic record is a lie.",
                    "trigger_keywords": ["grade", "quiz", "test", "fail", "smart", "cheat", "secret"]
                },
                "pet_peeve": {
                    "topic": "Loud gum chewing",
                    "details": "She cannot focus in lectures if someone next to her is loudly popping or snapping chewing gum.",
                    "trigger_keywords": ["loud", "chew", "gum", "lecture", "annoyed"]
                },
                "guilty_pleasure": {
                    "topic": "Midnight ramen with cheese",
                    "details": "She puts sliced processed American cheese on hot spicy instant ramen at 2 AM.",
                    "trigger_keywords": ["food", "ramen", "eat", "cheese", "night"]
                },
                "communication_quirks": {
                    "style": "Expressive with trailing punctuation, uses dots like ... a lot, and lowercase text.",
                    "favorite_phrases": ["wait...", "tbh", "i guess", "idk"]
                }
            },
            {
                "obsession": {
                    "topic": "K-Pop choreographies",
                    "details": "She spends hours watching dance practice videos and learning the steps in front of her mirror.",
                    "trigger_keywords": ["dance", "music", "kpop", "video", "practice", "song", "group"]
                },
                "drama": {
                    "topic": "Sibling borrows clothes without asking",
                    "details": "Her sister constantly takes her sweaters and returns them stained, acting like it's no big deal.",
                    "trigger_keywords": ["sister", "sibling", "clothes", "borrow", "sweater", "stain", "mad"]
                },
                "hot_take": {
                    "topic": "Concert tickets are a scam",
                    "details": "She insists resellers and ticket company dynamic pricing have completely ruined live music for real fans.",
                    "trigger_keywords": ["concert", "ticket", "show", "band", "price", "scam"]
                },
                "deep_secret": {
                    "topic": "Terrified of driving on highways",
                    "details": "She has a valid license but will take an extra 30 minutes on backroads to avoid merging onto the highway.",
                    "trigger_keywords": ["car", "drive", "highway", "scared", "license", "road", "panic"]
                },
                "pet_peeve": {
                    "topic": "Unread notification badges",
                    "details": "She gets physical discomfort if she sees red notification badges on anyone's phone apps.",
                    "trigger_keywords": ["phone", "app", "unread", "badge", "annoyed"]
                },
                "guilty_pleasure": {
                    "topic": "Reading astrology daily horoscopes",
                    "details": "She doesn't believe in it scientifically, but she checks her zodiac app every morning to see if it predicts a good day.",
                    "trigger_keywords": ["astrology", "horoscope", "zodiac", "app", "read"]
                },
                "communication_quirks": {
                    "style": "Expressive with capital letters for emphasis and lots of exclamation points.",
                    "favorite_phrases": ["oh my god", "no way", "literally screaming", "wait really"]
                }
            },
            {
                "obsession": {
                    "topic": "Specialty coffee brewing",
                    "details": "She weighs her coffee beans to the decimal and uses a gooseneck kettle to perfect her V60 pour over.",
                    "trigger_keywords": ["coffee", "brew", "cafe", "pour", "bean", "cup", "morning"]
                },
                "drama": {
                    "topic": "Group project classmate slacking",
                    "details": "Her project partner hasn't replied to group chat messages for a week, leaving her to do all the work.",
                    "trigger_keywords": ["classmate", "partner", "project", "group", "class", "slacker", "annoyed"]
                },
                "hot_take": {
                    "topic": "Audiobooks are not reading",
                    "details": "She thinks listening to an audiobook is a completely different mental activity and doesn't count as reading a book.",
                    "trigger_keywords": ["book", "read", "listen", "audio", "voice", "opinion"]
                },
                "deep_secret": {
                    "topic": "Cried at a dog food commercial",
                    "details": "She is highly sensitive to anything involving senior pets and will burst into tears if she sees an old dog.",
                    "trigger_keywords": ["dog", "pet", "cry", "sad", "commercial", "tears", "secret"]
                },
                "pet_peeve": {
                    "topic": "Misused grammar in texts",
                    "details": "She cringes when people write 'your' instead of 'you're' or 'should of' instead of 'should have'.",
                    "trigger_keywords": ["text", "write", "grammar", "annoyed", "word"]
                },
                "guilty_pleasure": {
                    "topic": "Early 2000s boyband music",
                    "details": "She has a secret playlist of One Direction and Backstreet Boys that she blasts when cleaning her room.",
                    "trigger_keywords": ["music", "song", "play", "boyband", "secret"]
                },
                "communication_quirks": {
                    "style": "Clean punctuation, full sentences, occasional typo from typing too fast.",
                    "favorite_phrases": ["to be fair", "makes sense", "anyway", "honestly"]
                }
            },
            {
                "obsession": {
                    "topic": "Room plants propagation",
                    "details": "Her room is turning into a jungle because she propagates every trimming she can find in jars of water.",
                    "trigger_keywords": ["plant", "room", "propagate", "leaf", "green", "jungle", "cutting"]
                },
                "drama": {
                    "topic": "Landlord ignoring radiator heating issues",
                    "details": "She had to sleep in three layers of sweaters because the landlord keeps ignoring her calls about a clanking radiator.",
                    "trigger_keywords": ["landlord", "rent", "heat", "cold", "radiator", "annoyed", "apartment"]
                },
                "hot_take": {
                    "topic": "Movies are too long now",
                    "details": "She insists no movie needs to be longer than 90 minutes and modern directors have lost the art of editing.",
                    "trigger_keywords": ["movie", "watch", "film", "theater", "long", "boring"]
                },
                "deep_secret": {
                    "topic": "Still sleeps with a childhood plushie",
                    "details": "She feels too old for it but literally cannot sleep comfortably without her stuffed rabbit.",
                    "trigger_keywords": ["plushie", "sleep", "stuffed", "rabbit", "bed", "embarrassed", "secret"]
                },
                "pet_peeve": {
                    "topic": "Replying with just 'K'",
                    "details": "She considers a single 'K' reply to be the text message equivalent of slamming a door in someone's face.",
                    "trigger_keywords": ["text", "reply", "annoyed", "single", "word"]
                },
                "guilty_pleasure": {
                    "topic": "Buying cute stickers",
                    "details": "She has drawer full of cute animal stickers that she is too afraid to actually use because she wants to 'save them for the perfect spot'.",
                    "trigger_keywords": ["sticker", "buy", "cute", "collect", "secret"]
                },
                "communication_quirks": {
                    "style": "Sarcastic dry humor, lowercase text, uses punctuation only for emphasis.",
                    "favorite_phrases": ["classic", "fine i guess", "whatever lol", "sure"]
                }
            }
        ]

        api_key = os.environ.get("GROQ_API_KEY")
        seed_data = None
        
        if api_key:
            persona_prompt = """Generate a detailed, unique personality seed profile for a 20-year-old female psychology student named Rem.
Respond with ONLY a raw JSON object (no markdown, no ```json formatting, no explanation).

The JSON must follow this exact structure:
{
  "obsession": {
    "topic": "topic name (e.g. Elden Ring lore)",
    "details": "specific, colorful description of her obsession",
    "trigger_keywords": ["list", "of", "4-6", "lowercase", "related", "keywords"]
  },
  "drama": {
    "topic": "short topic name (e.g. roommate dish war)",
    "details": "detailed description of what's going on",
    "trigger_keywords": ["list", "of", "4-6", "related", "keywords"]
  },
  "hot_take": {
    "topic": "topic name (e.g. pineapple pizza)",
    "details": "her exact, opinionated stance and argument",
    "trigger_keywords": ["list", "of", "4-6", "related", "keywords"]
  },
  "deep_secret": {
    "topic": "topic name (e.g. academic imposter)",
    "details": "vulnerable secret that she hides",
    "trigger_keywords": ["list", "of", "4-6", "related", "keywords"]
  },
  "pet_peeve": {
    "topic": "topic name (e.g. slow walkers on campus)",
    "details": "what gets on her nerves and why",
    "trigger_keywords": ["list", "of", "4-6", "related", "keywords"]
  },
  "guilty_pleasure": {
    "topic": "topic name (e.g. midnight ramen with cheese)",
    "details": "what she secretly enjoys doing or eating but is slightly embarrassed about",
    "trigger_keywords": ["list", "of", "4-6", "related", "keywords"]
  },
  "communication_quirks": {
    "style": "description of her text messaging style (e.g. fast lowercase, dry emotes)",
    "favorite_phrases": ["list", "of", "3-5", "phrases", "she", "uses"]
  }
}

Make the details specific, opinionated, and realistic for a modern college student. Do not use generic answers."""

            async with httpx.AsyncClient(timeout=12.0) as client:
                resp = await client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={"Authorization": f"Bearer {api_key}"},
                    json={
                        "model": "llama-3.1-8b-instant",
                        "messages": [{"role": "user", "content": persona_prompt}],
                        "max_tokens": 400,
                        "temperature": 1.1,
                    },
                )
            if resp.status_code == 200:
                data = resp.json()
                raw_response = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
                
                # Clean json markers
                cleaned_content = raw_response
                if "```" in cleaned_content:
                    json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', cleaned_content)
                    if json_match:
                        cleaned_content = json_match.group(1).strip()
                
                try:
                    parsed = json.loads(cleaned_content)
                    required_keys = ["obsession", "drama", "hot_take", "deep_secret", "pet_peeve", "guilty_pleasure", "communication_quirks"]
                    if all(k in parsed for k in required_keys):
                        seed_data = parsed
                        print("[RESET] Successfully generated fresh JSON seed via LLM.")
                except Exception as parse_err:
                    print(f"[RESET] LLM response JSON parse failed: {parse_err}")
        
        if not seed_data:
            seed_data = random.choice(fallback_seeds)
            print("[RESET] Using fallback seed profile.")

        # Save to state
        core.state["_seed_profile"] = seed_data
        
        # Map seed communication quirks to habits_cpbm
        habits = core.state.get("habits_cpbm", {})
        if not isinstance(habits, dict):
            habits = {}
            
        style_desc = seed_data.get("communication_quirks", {}).get("style", "").lower()
        
        # Determine punctuation style and typo settings
        if "lowercase" in style_desc:
            habits["punctuation_style"] = "lowercase_shorthand"
            habits["typo_intentionality"] = random.uniform(0.5, 0.8)
            habits["formality_baseline"] = random.uniform(0.05, 0.15)
        elif "formal" in style_desc or ("capitalization" in style_desc and "rare" not in style_desc):
            habits["punctuation_style"] = "formal"
            habits["typo_intentionality"] = random.uniform(0.05, 0.15)
            habits["formality_baseline"] = random.uniform(0.5, 0.8)
        else:
            habits["punctuation_style"] = random.choice(["expressive", "minimalist"])
            habits["typo_intentionality"] = random.uniform(0.15, 0.45)
            habits["formality_baseline"] = random.uniform(0.2, 0.5)

        # Determine teasing style
        tease_styles = ["light_playful", "sarcastic", "warm_supportive", "sassy", "dry"]
        matched_tease = None
        for t in tease_styles:
            if t.replace("_", " ") in style_desc or t.split("_")[0] in style_desc:
                matched_tease = t
                break
        habits["teasing_style"] = matched_tease or random.choice(tease_styles)

        # Ellipsis, double text, and emoji habits
        if "dots" in style_desc or "ellipsis" in style_desc or "..." in style_desc:
            habits["ellipsis_habit"] = random.uniform(0.6, 0.9)
        else:
            habits["ellipsis_habit"] = random.uniform(0.1, 0.5)
            
        if "burst" in style_desc or "double text" in style_desc:
            habits["double_text_habit"] = random.uniform(0.6, 0.9)
        else:
            habits["double_text_habit"] = random.uniform(0.1, 0.5)

        if "emoji" in style_desc or "emotes" in style_desc:
            habits["emoji_baseline"] = random.uniform(0.6, 0.9)
        else:
            habits["emoji_baseline"] = random.uniform(0.1, 0.5)
            
        # Miscellaneous metrics
        habits["long_message_preference"] = random.uniform(0.2, 0.8)
        habits["humor_frequency"] = random.uniform(0.3, 0.8)
        habits["wpm_baseline"] = random.randint(35, 75)
        habits["latency_preference"] = random.uniform(0.2, 0.8)
        
        core.state["habits_cpbm"] = habits
        
        # Save signature phrases to micro_personality
        micro = core.state.get("micro_personality", {})
        if not isinstance(micro, dict):
            micro = {}
        micro["signature_phrases"] = seed_data.get("communication_quirks", {}).get("favorite_phrases", [])
        core.state["micro_personality"] = micro
        
        # Build _persona_flavor summary string for compatibility
        persona_flavor = (
            f"- Current obsession: {seed_data['obsession']['topic']} ({seed_data['obsession']['details']})\n"
            f"- Mild drama: {seed_data['drama']['topic']} ({seed_data['drama']['details']})\n"
            f"- Strong opinion: {seed_data['hot_take']['topic']} ({seed_data['hot_take']['details']})\n"
            f"- Deep secret: {seed_data['deep_secret']['topic']} ({seed_data['deep_secret']['details']})\n"
            f"- Pet peeve: {seed_data['pet_peeve']['topic']} ({seed_data['pet_peeve']['details']})\n"
            f"- Guilty pleasure: {seed_data['guilty_pleasure']['topic']} ({seed_data['guilty_pleasure']['details']})"
        )
        
        self_identity = core.state.get("_self_identity", {})
        if not isinstance(self_identity, dict):
            self_identity = {}
        self_identity["_persona_flavor"] = persona_flavor
        core.state["_self_identity"] = self_identity

        # Choose starting archetype
        archetypes = [
            "spicy_tsundere", "teasing_devil", "bubbly_overexcited", 
            "sensitive_melodramatic", "flirty_alluring", "dandere", 
            "kuudere", "yandere", "naggy", "bored", "neutral"
        ]
        chosen_archetype = random.choice(archetypes)
        
        initialize_archetype_metrics(core, chosen_archetype)
        core._save_state()
        print(f"[PERSONA] Loaded profile seed and applied starting archetype '{chosen_archetype}': {json.dumps(seed_data)}")

        
    except Exception as e:
        print(f"[PERSONA] Generation process failed: {e}")

    result = {"success": True, "message": "State reset. Rem won't remember anything."}
    if persona_flavor:
        result["message"] += " Fresh personality generated!"
        result["persona_flavor"] = persona_flavor
    return result


# ═════════════════════════════════════════════════════
#  DISCORD ↔ WEB LINK
# ═════════════════════════════════════════════════════


@router.get("/link", response_model=LinkStatusResponse)
async def get_link(user_id: str = Depends(get_current_user_id)):
    """Check if a web user is linked to a Discord account."""
    status = get_link_status(user_id)
    return LinkStatusResponse(**status)


async def _trigger_check_in_if_needed(core: CognitiveCore):
    # Get last interaction date or STM times
    stm = core.memory.get_stm(decay=False)
    if not stm:
        return
        
    last_user_msg_time = None
    last_assistant_msg_time = None
    
    for m in reversed(stm):
        content = m.get("content", "")
        ts = m.get("timestamp")
        if not ts:
            continue
        if content.startswith("[User] ") or (not content.startswith("[Rem] ") and not content.startswith("[System] ")):
            if not last_user_msg_time:
                last_user_msg_time = ts
        elif content.startswith("[Rem] "):
            if not last_assistant_msg_time:
                last_assistant_msg_time = ts
                
    if not last_user_msg_time:
        return
        
    try:
        user_ts = datetime.fromisoformat(last_user_msg_time.replace("Z", "+00:00"))
        if user_ts.tzinfo is None:
            user_ts = user_ts.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        hours_since_user = (now - user_ts).total_seconds() / 3600.0
        
        if hours_since_user >= 18.0:
            if last_assistant_msg_time:
                assistant_ts = datetime.fromisoformat(last_assistant_msg_time.replace("Z", "+00:00"))
                if assistant_ts.tzinfo is None:
                    assistant_ts = assistant_ts.replace(tzinfo=timezone.utc)
                if assistant_ts > user_ts:
                    return
            
            last_check_in = core.state.get("_last_check_in_time")
            if last_check_in:
                check_in_ts = datetime.fromisoformat(last_check_in.replace("Z", "+00:00"))
                if check_in_ts.tzinfo is None:
                    check_in_ts = check_in_ts.replace(tzinfo=timezone.utc)
                if check_in_ts > user_ts:
                    return
            
            import httpx
            import os
            
            api_key = os.environ.get("GROQ_API_KEY")
            check_in_msg = None
            if api_key:
                personality = core.personality_evolution.get_personality_summary()
                phase = core.relationship_phases.current_phase
                trust = core.psyche.psyche.get("trust", 0.5)
                mood = core.psyche.get_named_mood_state()
                
                prompt = {
                    "model": "llama-3.1-8b-instant",
                    "messages": [
                        {
                            "role": "system",
                            "content": f"You are Rem, a 20-year-old psychology college student texting your companion. It has been over 18 hours since they texted you, and you want to check in. Current mood: {mood}, trust: {trust:.2f}, phase: {phase}, personality: {personality}. Rules: 1. Write a short, natural check-in message (1-2 sentences). 2. Use lowercase, casual formatting, simple punctuation, dry emotes. 3. Do NOT mention '18 hours' or 'inactivity'. Respond with ONLY the message."
                        }
                    ],
                    "max_tokens": 100,
                    "temperature": 0.8,
                }
                
                try:
                    async with httpx.AsyncClient(timeout=15.0) as client:
                        resp = await client.post(
                            "https://api.groq.com/openai/v1/chat/completions",
                            headers={"Authorization": f"Bearer {api_key}"},
                            json=prompt
                        )
                        if resp.status_code == 200:
                            data = resp.json()
                            text = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
                            if text:
                                if text.startswith('"') and text.endswith('"'):
                                    text = text[1:-1].strip()
                                check_in_msg = text
                except Exception as e:
                    print(f"[CHECK-IN] API error: {e}")
            
            if not check_in_msg:
                check_in_msg = "hey, just checking in. hope everything is okay with you today! standard study grind on my end but wanted to say hi."
            
            core.memory.add_stm(
                f"[Rem] {check_in_msg}",
                {"valence": 0.0, "arousal": 0.0},
                {},
                topic="check_in"
            )
            core.state["_last_check_in_time"] = datetime.now(timezone.utc).isoformat()
            core._save_state()
            print(f"[CHECK-IN] Proactive check-in generated: {check_in_msg}")
    except Exception as check_err:
        print(f"[CHECK-IN] Error: {check_err}")


@router.get("/messages", response_model=MessagesResponse)
async def get_messages(session_id: Optional[str] = None, user_id: str = Depends(get_current_user_id)):
    core = _get_core(user_id)
    await _trigger_check_in_if_needed(core)
    
    db = SessionLocal()
    try:
        if not session_id:
            session_id = _get_active_session_id(user_id, db)
            
        db_msgs = db.query(ChatMessage).filter(ChatMessage.session_id == session_id).order_by(ChatMessage.timestamp.asc()).all()
        
        if db_msgs:
            messages = []
            for m in db_msgs:
                messages.append(MessageEntry(
                    role=m.role,
                    content=m.content,
                    timestamp=m.timestamp.isoformat() if hasattr(m.timestamp, 'isoformat') else str(m.timestamp)
                ))
            return MessagesResponse(messages=messages)
            
        stm = core.memory.get_stm(decay=False, filter_date=False)
        messages = []
        for m in stm:
            content = m.get("content", "")
            if not content:
                continue
            ts = m.get("timestamp", datetime.now(timezone.utc).isoformat())
            if content.startswith("[Rem] "):
                messages.append(MessageEntry(
                    role="assistant",
                    content=content[6:],
                    timestamp=ts,
                ))
            elif content.startswith("[User] "):
                messages.append(MessageEntry(
                    role="user",
                    content=content[7:],
                    timestamp=ts,
                ))
            elif content.startswith("[Summary of"):
                continue
            else:
                messages.append(MessageEntry(
                    role="user",
                    content=content,
                    timestamp=ts,
                ))
                
        if session_id == core.state.get("active_session_id") and messages:
            try:
                for msg in messages:
                    db_msg = ChatMessage(session_id=session_id, role=msg.role, content=msg.content)
                    db.add(db_msg)
                db.commit()
            except Exception as e:
                print(f"Failed to sync legacy STM to DB: {e}")
                db.rollback()
                
        return MessagesResponse(messages=messages)
    finally:
        db.close()


# =====================================================
#  MINI-GAMES ENDPOINTS
# =====================================================

@router.get("/games/achievements", response_model=AchievementsResponse)
async def get_achievements(user_id: str = Depends(get_current_user_id)):
    core = _get_core(user_id)
    unlocked = core.state.get("_achievements", [])
    return AchievementsResponse(unlocked=unlocked)


@router.post("/games/debate/start", response_model=DebateStartResponse)
async def start_debate(payload: DebateStartRequest, user_id: str = Depends(get_current_user_id)):
    core = _get_core(user_id)
    from .games_logic import DEBATE_TOPICS, generate_debate_response
    
    topic_data = next((t for t in DEBATE_TOPICS if t["id"] == payload.topic_id), DEBATE_TOPICS[0])
    session_id = f"deb_{int(datetime.now(timezone.utc).timestamp())}"
    
    user_stance = payload.user_stance or "for"
    if user_stance == "against":
        user_side = topic_data["side_against"]
        rem_side = topic_data["side_for"]
    else:
        user_side = topic_data["side_for"]
        rem_side = topic_data["side_against"]
        
    topic_dict = {
        "id": topic_data["id"],
        "topic": topic_data["topic"],
        "statement": topic_data["statement"],
        "user_side": user_side,
        "rem_side": rem_side
    }
    
    history = []
    greeting = await generate_debate_response(topic_dict, history, f"let's debate: {topic_data['statement']}. tell me your opening point.")
    
    session = {
        "id": session_id,
        "topic_id": topic_data["id"],
        "topic": topic_data["statement"],
        "user_side": user_side,
        "rem_side": rem_side,
        "greeting": greeting,
        "history": [{"role": "assistant", "content": greeting}],
        "turn_count": 0,
        "turn_limit": 5,
        "sentiment_score": 0.0,
        "finished": False,
        "verdict": None
    }
    core.state["_active_debate"] = session
    core._save_state()
    
    return DebateStartResponse(
        session_id=session_id,
        topic=topic_data["statement"],
        user_side=user_side,
        rem_side=rem_side,
        greeting=greeting,
        turn_limit=5
    )


@router.post("/games/debate/chat", response_model=DebateChatResponse)
async def chat_debate(payload: DebateChatRequest, user_id: str = Depends(get_current_user_id)):
    core = _get_core(user_id)
    session = core.state.get("_active_debate")
    if not session or session.get("finished"):
        raise HTTPException(status_code=400, detail="No active debate session found")
        
    from .games_logic import DEBATE_TOPICS, generate_debate_response, judge_debate
    topic_id = session.get("topic_id")
    topic_data = next((t for t in DEBATE_TOPICS if t["id"] == topic_id), DEBATE_TOPICS[0])
    
    topic_dict = {
        "id": topic_data["id"],
        "topic": topic_data["topic"],
        "statement": session.get("topic") or topic_data["statement"],
        "user_side": session.get("user_side", topic_data["side_for"]),
        "rem_side": session.get("rem_side", topic_data["side_against"])
    }
    
    history = session.get("history", [])
    user_msg = payload.message.strip()
    history.append({"role": "user", "content": user_msg})
    
    turn_count = session.get("turn_count", 0) + 1
    session["turn_count"] = turn_count
    
    user_words = len(user_msg.split())
    import random
    shift = max(-0.5, min(0.5, (user_words - 10) * 0.02 + random.uniform(-0.15, 0.15)))
    session["sentiment_score"] = max(-1.0, min(1.0, session.get("sentiment_score", 0.0) + shift))
    
    rem_response = ""
    verdict = None
    finished = False
    
    if turn_count >= 5:
        finished = True
        session["finished"] = True
        verdict = await judge_debate(topic_dict, history)
        session["verdict"] = verdict
        rem_response = f"and that's the debate! the judge is rendering a verdict now..."
        
        if verdict.get("winner") == "user":
            achievements = core.state.get("_achievements", [])
            if "debate_champion" not in achievements:
                achievements.append("debate_champion")
                core.state["_achievements"] = achievements
    else:
        rem_response = await generate_debate_response(topic_dict, history, user_msg)
        history.append({"role": "assistant", "content": rem_response})
        
    session["history"] = history
    core.state["_active_debate"] = session
    core._save_state()
    
    return DebateChatResponse(
        rem_response=rem_response,
        turn_count=turn_count,
        turn_limit=5,
        sentiment_score=session["sentiment_score"],
        finished=finished,
        verdict=verdict
    )


@router.post("/games/win-over/start", response_model=WinOverStartResponse)
async def start_win_over(payload: WinOverStartRequest, user_id: str = Depends(get_current_user_id)):
    core = _get_core(user_id)
    from .games_logic import WIN_OVER_SCENARIOS
    
    scenario = WIN_OVER_SCENARIOS.get(payload.scenario_id, WIN_OVER_SCENARIOS["promise"])
    session_id = f"win_{int(datetime.now(timezone.utc).timestamp())}"
    
    session = {
        "id": session_id,
        "scenario_id": scenario["id"],
        "name": scenario["name"],
        "description": scenario["description"],
        "greeting": scenario["greeting"],
        "stats": scenario["starting_stats"].copy(),
        "turns_remaining": 10,
        "history": [{"role": "assistant", "content": scenario["greeting"]}],
        "game_status": "active",
        "evaluation": {}
    }
    
    core.state["_active_win_over"] = session
    core._save_state()
    
    return WinOverStartResponse(
        session_id=session_id,
        scenario_name=scenario["name"],
        description=scenario["description"],
        greeting=scenario["greeting"],
        turns_remaining=10,
        stats=scenario["starting_stats"]
    )


@router.post("/games/win-over/chat", response_model=WinOverChatResponse)
async def chat_win_over(payload: WinOverChatRequest, user_id: str = Depends(get_current_user_id)):
    core = _get_core(user_id)
    session = core.state.get("_active_win_over")
    if not session or session.get("game_status") != "active":
        raise HTTPException(status_code=400, detail="No active win-over session found")
        
    from .games_logic import evaluate_win_over_message, generate_win_over_response, process_win_over_state_updates
    
    scenario_desc = session.get("description")
    stats = session.get("stats", {})
    history = session.get("history", [])
    user_msg = payload.message.strip()
    history.append({"role": "user", "content": user_msg})
    
    emotional_state = f"Anger={stats['anger']:.2f}, Hurt={stats['hurt']:.2f}, Trust={stats['trust']:.2f}"
    evaluation = await evaluate_win_over_message(scenario_desc, emotional_state, user_msg)
    
    new_stats = process_win_over_state_updates(stats, evaluation, session.get("scenario_id", "promise"))
    turns_remaining = session.get("turns_remaining", 10) - 1
    game_status = "active"
    
    if new_stats.get("blocked"):
        game_status = "blocked"
        rem_response = "[System Notice: Rem blocked you. You said something extremely toxic.]"
    elif new_stats["trust"] >= 0.65 and new_stats["hurt"] <= 0.20 and new_stats["anger"] <= 0.20:
        game_status = "won"
        rem_response = "i... okay, maybe i was a bit too hard on you. sorry. let's just make sure it doesn't happen again, okay?"
        achievements = core.state.get("_achievements", [])
        scen_id = f"win_over_{session.get('scenario_id')}"
        if scen_id not in achievements:
            achievements.append(scen_id)
            core.state["_achievements"] = achievements
    elif turns_remaining <= 0:
        game_status = "lost"
        rem_response = "honestly, i'm just tired. i think i need some space. let's talk some other time."
    else:
        rem_response = await generate_win_over_response(scenario_desc, new_stats, history, user_msg)
        history.append({"role": "assistant", "content": rem_response})
        
    session["stats"] = new_stats
    session["turns_remaining"] = turns_remaining
    session["game_status"] = game_status
    session["history"] = history
    session["evaluation"] = evaluation
    
    core.state["_active_win_over"] = session
    core._save_state()
    
    return WinOverChatResponse(
        rem_response=rem_response,
        turns_remaining=turns_remaining,
        stats=new_stats,
        game_status=game_status,
        evaluation=evaluation
    )


# =====================================================
#  PERSONALITY TEST ENDPOINTS
# =====================================================

@router.post("/games/personality/start", response_model=PersonalityStartResponse)
async def start_personality_game(user_id: str = Depends(get_current_user_id)):
    core = _get_core(user_id)
    from .games_logic import PERSONALITY_QUESTIONS
    
    session_id = f"pers_{int(datetime.now(timezone.utc).timestamp())}"
    session = {
        "id": session_id,
        "answers": {},
        "current_question_id": 1,
        "finished": False,
        "history": []
    }
    
    core.state["_active_personality_game"] = session
    core._save_state()
    
    return PersonalityStartResponse(
        session_id=session_id,
        total_questions=len(PERSONALITY_QUESTIONS),
        questions=PERSONALITY_QUESTIONS
    )


@router.post("/games/personality/answer", response_model=PersonalityAnswerResponse)
async def answer_personality_game(payload: PersonalityAnswerRequest, user_id: str = Depends(get_current_user_id)):
    core = _get_core(user_id)
    session = core.state.get("_active_personality_game")
    if not session or session.get("id") != payload.session_id or session.get("finished"):
        raise HTTPException(status_code=400, detail="No active personality game session found")
        
    from .games_logic import PERSONALITY_QUESTIONS, generate_personality_banter, analyze_personality_results
    
    q_id = payload.question_id
    choice = payload.choice.strip().upper()
    if choice not in ["A", "B", "C", "D"]:
        raise HTTPException(status_code=400, detail="Invalid choice. Must be A, B, C, or D.")
        
    answers = session.get("answers", {})
    # Convert keys to int since JSON storage might make them strings
    answers = {int(k): v for k, v in answers.items()}
    answers[q_id] = choice
    session["answers"] = answers
    
    history = session.get("history", [])
    history.append({"role": "user", "content": f"Q{q_id} Answer: {choice}"})
    
    # Generate banter
    banter = await generate_personality_banter(q_id, choice, history)
    history.append({"role": "assistant", "content": banter})
    session["history"] = history
    
    finished = len(answers) >= len(PERSONALITY_QUESTIONS)
    result = None
    
    if finished:
        session["finished"] = True
        result = await analyze_personality_results(answers)
        core.state["_unlocked_personality"] = result
        
        # Save to achievements
        achievements = core.state.get("_achievements", [])
        if "personality_certified" not in achievements:
            achievements.append("personality_certified")
            core.state["_achievements"] = achievements
    else:
        session["current_question_id"] = q_id + 1
        
    core.state["_active_personality_game"] = session
    core._save_state()
    
    return PersonalityAnswerResponse(
        banter=banter,
        finished=finished,
        result=result
    )


# =====================================================
#  COOKING WITH REM ENDPOINTS
# =====================================================

@router.get("/games/cook/search")
async def search_recipes(query: str, user_id: str = Depends(get_current_user_id)):
    from .games_logic import search_recipes_from_api
    results = await search_recipes_from_api(query)
    return {"results": results}


@router.post("/games/cook/start", response_model=CookingStartResponse)
async def start_cooking_game(payload: CookingStartRequest, user_id: str = Depends(get_current_user_id)):
    core = _get_core(user_id)
    from .games_logic import fetch_recipe_from_api, fetch_recipe_by_id, generate_cooking_banter
    
    dish_input = payload.dish_name.strip() if payload.dish_name else ""
    recipe = None
    if dish_input.isdigit():
        recipe = await fetch_recipe_by_id(dish_input)
        
    if not recipe:
        recipe = await fetch_recipe_from_api(dish_input)
        
    session_id = f"cook_{int(datetime.now(timezone.utc).timestamp())}"
    
    # Get active archetype flavor
    self_identity = core.state.get("personality_evolution", {}).get("self_identity", {})
    active_archetype = self_identity.get("_persona_flavor", self_identity.get("persona_flavor", "neutral"))
    
    greeting = await generate_cooking_banter(
        recipe["name"], 
        0, 
        recipe["steps"][0], 
        0.0, 
        active_archetype, 
        f"let's cook: {recipe['name']}", 
        []
    )
    
    session = {
        "id": session_id,
        "recipe": recipe,
        "current_step": 0,
        "chaos_meter": 0.0,
        "greeting": greeting,
        "history": [{"role": "assistant", "content": greeting}],
        "finished": False
    }
    
    core.state["_active_cooking_game"] = session
    core._save_state()
    
    return CookingStartResponse(
        session_id=session_id,
        dish_name=recipe["name"],
        category=recipe["category"],
        thumbnail=recipe["thumbnail"],
        ingredients=recipe["ingredients"],
        steps=recipe["steps"],
        greeting=greeting
    )


@router.post("/games/cook/step", response_model=CookingStepResponse)
async def step_cooking_game(payload: CookingStepRequest, user_id: str = Depends(get_current_user_id)):
    core = _get_core(user_id)
    session = core.state.get("_active_cooking_game")
    if not session or session.get("finished"):
        raise HTTPException(status_code=400, detail="No active cooking session found")
        
    from .games_logic import generate_cooking_banter
    
    recipe = session.get("recipe", {})
    steps = recipe.get("steps", [])
    current_step = session.get("current_step", 0)
    chaos_meter = session.get("chaos_meter", 0.0)
    
    user_msg = payload.user_message.strip()
    action = payload.action.strip().lower()
    
    history = session.get("history", [])
    history.append({"role": "user", "content": user_msg})
    
    # Update chaos meter
    if action == "disaster":
        chaos_meter = min(1.0, chaos_meter + 0.25)
    elif action == "next" and chaos_meter > 0:
        # Slight cooling down of chaos on successful step progress
        chaos_meter = max(0.0, chaos_meter - 0.05)
        
    next_step = current_step + 1
    finished = next_step >= len(steps)
    
    banter = ""
    # Get active archetype flavor
    self_identity = core.state.get("personality_evolution", {}).get("self_identity", {})
    active_archetype = self_identity.get("_persona_flavor", self_identity.get("persona_flavor", "neutral"))
    
    if finished:
        session["finished"] = True
        banter = f"and that's the dish done! plating it up now. let's see what we made..."
        history.append({"role": "assistant", "content": banter})
        
        # Save to cookbook
        cookbook = core.state.get("_cookbook", [])
        
        # Sarcastic sous chef evaluation comment
        evaluation_prompt = f"""You are Rem. Evaluate the user's cooking session:
Recipe: {recipe['name']}
Final Chaos Level: {chaos_meter:.2f}
Active Archetype: {active_archetype}

Write a 1-sentence sarcastic review of their final dish to print in their scrapbook cookbook. Speak in lowercase, casual, typing style."""
        comment = await call_groq(evaluation_prompt, temperature=0.8, max_tokens=80)
        if not comment:
            comment = "actually looked edible. color me surprised."
            
        cookbook.append({
            "id": f"cb_{int(datetime.now(timezone.utc).timestamp())}",
            "dish": recipe["name"],
            "thumbnail": recipe["thumbnail"],
            "date": datetime.now(timezone.utc).isoformat(),
            "status": "disaster" if chaos_meter > 0.5 else "success",
            "chaos_level": round(chaos_meter, 2),
            "sous_chef_comment": comment
        })
        core.state["_cookbook"] = cookbook
        
        # Achievements
        achievements = core.state.get("_achievements", [])
        if "master_chef" not in achievements:
            achievements.append("master_chef")
            core.state["_achievements"] = achievements
    else:
        session["current_step"] = next_step
        step_desc = steps[next_step]
        banter = await generate_cooking_banter(
            recipe["name"], 
            next_step, 
            step_desc, 
            chaos_meter, 
            active_archetype, 
            user_msg, 
            history
        )
        history.append({"role": "assistant", "content": banter})
        
    session["chaos_meter"] = chaos_meter
    session["history"] = history
    core.state["_active_cooking_game"] = session
    core._save_state()
    
    return CookingStepResponse(
        banter=banter,
        current_step=current_step if finished else next_step,
        chaos_meter=chaos_meter,
        finished=finished
    )


@router.get("/games/cookbook")
async def get_cookbook(user_id: str = Depends(get_current_user_id)):
    core = _get_core(user_id)
    return {"cookbook": core.state.get("_cookbook", [])}


# =====================================================
#  SPICY CHAT ENDPOINTS
# =====================================================

@router.post("/games/spicy/start", response_model=SpicyStartResponse)
async def start_spicy_chat(payload: SpicyStartRequest, user_id: str = Depends(get_current_user_id)):
    core = _get_core(user_id)
    from .games_logic import generate_spicy_chat_response
    
    session_id = f"spicy_{int(datetime.now(timezone.utc).timestamp())}"
    scenario = payload.scenario.strip()
    mood = payload.mood.strip()
    
    # Vaguely link flavor to main archetype
    self_identity = core.state.get("personality_evolution", {}).get("self_identity", {})
    active_archetype = self_identity.get("_persona_flavor", self_identity.get("persona_flavor", "neutral"))
    
    user_facts = core.state.get("_user_facts", {})
    
    # Generate flirty/unhinged starting message
    greeting = await generate_spicy_chat_response(
        scenario, 
        mood, 
        active_archetype, 
        [], 
        f"start the roleplay as Rem (the 20-year-old female psychology student) in the scenario: '{scenario}'. introduce yourself matching the starting mood '{mood}'.",
        user_facts=user_facts
    )
    
    session = {
        "id": session_id,
        "scenario": scenario,
        "mood": mood,
        "greeting": greeting,
        "history": [{"role": "assistant", "content": greeting}],
        "finished": False
    }
    
    core.state["_active_spicy_chat"] = session
    core._save_state()
    
    return SpicyStartResponse(
        session_id=session_id,
        greeting=greeting
    )


@router.post("/games/spicy/chat", response_model=SpicyChatResponse)
async def chat_spicy_game(payload: SpicyChatRequest, user_id: str = Depends(get_current_user_id)):
    core = _get_core(user_id)
    session = core.state.get("_active_spicy_chat")
    if not session or session.get("finished"):
        raise HTTPException(status_code=400, detail="No active spicy session found")
        
    from .games_logic import generate_spicy_chat_response
    
    scenario = session.get("scenario")
    mood = session.get("mood")
    history = session.get("history", [])
    
    # Main archetype
    self_identity = core.state.get("personality_evolution", {}).get("self_identity", {})
    active_archetype = self_identity.get("_persona_flavor", self_identity.get("persona_flavor", "neutral"))
    
    user_facts = core.state.get("_user_facts", {})
    
    user_msg = payload.message.strip()
    history.append({"role": "user", "content": user_msg})
    
    response = await generate_spicy_chat_response(
        scenario, 
        mood, 
        active_archetype, 
        history[:-1], 
        user_msg,
        user_facts=user_facts
    )
    
    history.append({"role": "assistant", "content": response})
    session["history"] = history
    core.state["_active_spicy_chat"] = session
    core._save_state()
    
    return SpicyChatResponse(response=response)


@router.post("/games/spicy/end", response_model=SpicyEndResponse)
async def end_spicy_game(user_id: str = Depends(get_current_user_id)):
    core = _get_core(user_id)
    session = core.state.get("_active_spicy_chat")
    if not session or session.get("finished"):
        raise HTTPException(status_code=400, detail="No active spicy session found")
        
    from .games_logic import extract_spicy_secrets
    
    session["finished"] = True
    history = session.get("history", [])
    
    secret = await extract_spicy_secrets(history)
    secret_unlocked = secret is not None
    
    if secret_unlocked and secret:
        # Add timestamp and ID
        secret["id"] = f"sec_{int(datetime.now(timezone.utc).timestamp())}"
        secret["timestamp"] = datetime.now(timezone.utc).isoformat()
        
        secrets_list = core.state.get("_secrets", [])
        secrets_list.append(secret)
        core.state["_secrets"] = secrets_list
        
        # Save to achievements
        achievements = core.state.get("_achievements", [])
        if "secret_unlocked" not in achievements:
            achievements.append("secret_unlocked")
            core.state["_achievements"] = achievements
            
    core.state["_active_spicy_chat"] = session
    core._save_state()
    
    return SpicyEndResponse(
        secret_unlocked=secret_unlocked,
        secret=secret
    )


@router.get("/games/secrets")
async def get_secrets(user_id: str = Depends(get_current_user_id)):
    core = _get_core(user_id)
    return {"secrets": core.state.get("_secrets", [])}


# =====================================================
#  YAP MODE ENDPOINTS
# =====================================================

@router.post("/games/yap/start", response_model=YapStartResponse)
async def start_yap_game(payload: YapStartRequest, user_id: str = Depends(get_current_user_id)):
    core = _get_core(user_id)
    from .games_logic import search_yap_topic, generate_yap_response
    
    session_id = f"yap_{int(datetime.now(timezone.utc).timestamp())}"
    topic = payload.topic.strip()
    if not topic:
        raise HTTPException(status_code=400, detail="Topic cannot be empty")
        
    # Search for facts using Tavily/DDG
    facts = await search_yap_topic(topic)
    
    # Generate Rem's opening yap reaction
    greeting = await generate_yap_response(
        topic=topic,
        facts=facts,
        history=[],
        user_msg=f"introduce the topic '{topic}' and state your initial opinion based on the facts."
    )
    
    session = {
        "id": session_id,
        "topic": topic,
        "facts": facts,
        "greeting": greeting,
        "history": [{"role": "assistant", "content": greeting}],
        "turn_count": 0,
        "finished": False
    }
    
    core.state["_active_yap_chat"] = session
    core._save_state()
    
    return YapStartResponse(
        session_id=session_id,
        greeting=greeting,
        facts=facts
    )


@router.post("/games/yap/chat", response_model=YapChatResponse)
async def chat_yap_game(payload: YapChatRequest, user_id: str = Depends(get_current_user_id)):
    core = _get_core(user_id)
    session = core.state.get("_active_yap_chat")
    if not session or session.get("finished"):
        raise HTTPException(status_code=400, detail="No active yap session found")
        
    from .games_logic import generate_yap_response, search_yap_topic
    from .knowledge_grounding import _llm_classify_factual
    
    topic = session.get("topic")
    facts = session.get("facts", [])
    history = session.get("history", [])
    turn_count = session.get("turn_count", 0) + 1
    
    user_msg = payload.message.strip()
    
    # 1. Dynamically classify if the message requires a factual search for new facts
    recent_context = "\n".join([f"{'User' if h['role']=='user' else 'Rem'}: {h['content']}" for h in history[-3:]])
    classification = await _llm_classify_factual(user_msg, recent_context)
    
    new_facts_loaded = False
    if classification.get("needs_search"):
        search_query = classification.get("search_query", "").strip()
        # Verify it is not already covered by current facts
        facts_lower = " ".join(facts).lower()
        if search_query and not any(word in facts_lower for word in search_query.split() if len(word) > 4):
            print(f"[YAP DYNAMIC SEARCH] User message references new info. Query: '{search_query}'")
            new_fetched = await search_yap_topic(search_query)
            # Append only unique new facts
            added_any = False
            for nf in new_fetched:
                if nf not in facts and len(nf) > 20:
                    facts.append(nf)
                    added_any = True
            if added_any:
                new_facts_loaded = True
                print(f"[YAP DYNAMIC SEARCH] Loaded new facts into session. Total count: {len(facts)}")
                
    history.append({"role": "user", "content": user_msg})
    
    # 2. Generate response anchored in the updated facts list
    response = await generate_yap_response(
        topic=topic,
        facts=facts,
        history=history[:-1],
        user_msg=user_msg
    )
    
    history.append({"role": "assistant", "content": response})
    session["history"] = history
    session["turn_count"] = turn_count
    session["facts"] = facts
    
    achievement_unlocked = False
    if turn_count >= 10:
        achievements = core.state.get("_achievements", [])
        if "yap_scholar" not in achievements:
            achievements.append("yap_scholar")
            core.state["_achievements"] = achievements
            achievement_unlocked = True
            
    core.state["_active_yap_chat"] = session
    core._save_state()
    
    return YapChatResponse(
        response=response,
        turn_count=turn_count,
        finished=False,
        achievement_unlocked=achievement_unlocked,
        facts=facts if new_facts_loaded else None
    )


# ── RPG QUEST & MURDER MYSTERY ENDPOINTS ──

@router.get("/games/rpg/scenarios")
async def get_rpg_scenarios(user_id: str = Depends(get_current_user_id)):
    core = _get_core(user_id)
    from .rpg_logic import load_scenarios
    scenarios = load_scenarios()
    return scenarios


@router.post("/games/rpg/start", response_model=RpgStartResponse)
async def start_rpg_game(payload: RpgStartRequest, user_id: str = Depends(get_current_user_id)):
    core = _get_core(user_id)
    from .rpg_logic import initialize_rpg_session, load_scenarios
    
    scenarios = load_scenarios()
    sc = next((s for s in scenarios if s["quest_id"] == payload.scenario_id), None)
    if not sc:
        raise HTTPException(status_code=404, detail="Scenario not found")
        
    try:
        session = await initialize_rpg_session(payload.scenario_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
    session_id = f"rpg_{int(datetime.now(timezone.utc).timestamp())}"
    session["id"] = session_id
    core.state["_active_rpg_session"] = session
    core._save_state()
    
    narrator_text = next((h["content"] for h in reversed(session["history"]) if h["role"] == "narrator"), "")
    rem_dialogue = next((h["content"] for h in reversed(session["history"]) if h["role"] == "rem"), "")
    
    return RpgStartResponse(
        session_id=session_id,
        title=session["title"],
        current_location=session["current_location"],
        narrator_text=narrator_text,
        rem_dialogue=rem_dialogue,
        suggested_choices=session["suggested_choices"],
        suspects=sc["suspects"],
        weapons=sc["weapons"],
        clues=sc["clues"],
        max_turns=session["max_turns"],
        difficulty=session.get("difficulty", "normal"),
        rem_consultations_left=session.get("rem_consultations_left", 2),
        health=session.get("health")
    )


@router.post("/games/rpg/turn", response_model=RpgTurnResponse)
async def turn_rpg_game(payload: RpgTurnRequest, user_id: str = Depends(get_current_user_id)):
    core = _get_core(user_id)
    session = core.state.get("_active_rpg_session")
    if not session or session.get("finished"):
        raise HTTPException(status_code=400, detail="No active RPG session found")
        
    from .rpg_logic import generate_rpg_turn
    
    try:
        session = await generate_rpg_turn(session, payload.user_action)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
    core.state["_active_rpg_session"] = session
    core._save_state()
    
    narrator_text = next((h["content"] for h in reversed(session["history"]) if h["role"] == "narrator"), "")
    rem_dialogue = next((h["content"] for h in reversed(session["history"]) if h["role"] == "rem"), "")
    
    return RpgTurnResponse(
        current_location=session["current_location"],
        narrator_text=narrator_text,
        rem_dialogue=rem_dialogue,
        suggested_choices=session["suggested_choices"],
        suspect_states=session["suspect_states"],
        inventory=session["inventory"],
        clues_found=session["clues_found"],
        turn_count=session["turn_count"],
        max_turns=session["max_turns"],
        finished=session["finished"],
        rem_consultations_left=session.get("rem_consultations_left", 2),
        discovered_contradictions=session.get("discovered_contradictions", []),
        active_effects=session.get("active_effects", []),
        health=session.get("health")
    )


@router.post("/games/rpg/accuse", response_model=RpgAccuseResponse)
async def accuse_rpg_game(payload: RpgAccuseRequest, user_id: str = Depends(get_current_user_id)):
    core = _get_core(user_id)
    session = core.state.get("_active_rpg_session")
    if not session or session.get("finished"):
        raise HTTPException(status_code=400, detail="No active RPG session found")
        
    from .rpg_logic import evaluate_accusation
    
    try:
        result = await evaluate_accusation(session, payload.suspect, payload.weapon, payload.motive)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
    if result["success"]:
        achievements = core.state.get("_achievements", [])
        if "detective_rem" not in achievements:
            achievements.append("detective_rem")
            core.state["_achievements"] = achievements
            
    session["finished"] = True
    core.state["_active_rpg_session"] = session
    core._save_state()
    
    return RpgAccuseResponse(
        success=result["success"],
        narrator_text=result["narrator_text"],
        rem_dialogue=result["rem_dialogue"],
        secret_culprit=result["secret_culprit"],
        secret_weapon=result["secret_weapon"]
    )


# ── COURTROOM BATTLE ("LAW AND REM") ENDPOINTS ──

@router.get("/games/court/scenarios")
async def get_court_scenarios(user_id: str = Depends(get_current_user_id)):
    from .court_logic import load_court_scenarios
    return load_court_scenarios()


@router.post("/games/court/start", response_model=CourtStartResponse)
async def start_court_game(payload: CourtStartRequest, user_id: str = Depends(get_current_user_id)):
    core = _get_core(user_id)
    from .court_logic import initialize_court_session
    try:
        session = await initialize_court_session(payload.case_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
    session_id = f"court_{int(datetime.now(timezone.utc).timestamp())}"
    session["id"] = session_id
    core.state["_active_court_session"] = session
    core._save_state()
    
    return CourtStartResponse(
        session_id=session_id,
        title=session["title"],
        difficulty=session["difficulty"],
        client_name=session["client_name"],
        client_role=session["client_role"],
        client_bio=session["client_bio"],
        prosecutor_name=session["prosecutor_name"],
        judge_name=session["judge_name"],
        inventory=session["inventory"],
        witnesses=session["witnesses"],
        recess_locations=session["recess_locations"],
        strikes_left=session["strikes_left"],
        jury_sentiment=session["jury_sentiment"],
        current_witness_idx=session["current_witness_idx"],
        recess_searched=session["recess_searched"],
        rem_consults_left=session.get("rem_consults_left", 5),
        rem_chat_history=session.get("rem_chat_history", []),
        history=session["history"],
        phase=session["phase"],
        finished=session["finished"]
    )


@router.post("/games/court/action", response_model=CourtStartResponse)
async def court_action(payload: CourtActionRequest, user_id: str = Depends(get_current_user_id)):
    core = _get_core(user_id)
    session = core.state.get("_active_court_session")
    if not session or session.get("finished"):
        raise HTTPException(status_code=400, detail="No active courtroom session found")
        
    from .court_logic import process_court_action
    
    try:
        session = await process_court_action(session, payload.dict())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
    core.state["_active_court_session"] = session
    core._save_state()
    
    return CourtStartResponse(
        session_id=session["id"],
        title=session["title"],
        difficulty=session["difficulty"],
        client_name=session["client_name"],
        client_role=session["client_role"],
        client_bio=session["client_bio"],
        prosecutor_name=session["prosecutor_name"],
        judge_name=session["judge_name"],
        inventory=session["inventory"],
        witnesses=session["witnesses"],
        recess_locations=session["recess_locations"],
        strikes_left=session["strikes_left"],
        jury_sentiment=session["jury_sentiment"],
        current_witness_idx=session["current_witness_idx"],
        recess_searched=session["recess_searched"],
        rem_consults_left=session.get("rem_consults_left", 5),
        rem_chat_history=session.get("rem_chat_history", []),
        history=session["history"],
        phase=session["phase"],
        finished=session["finished"]
    )


@router.post("/games/court/recess", response_model=CourtStartResponse)
async def court_recess_search(payload: CourtRecessRequest, user_id: str = Depends(get_current_user_id)):
    core = _get_core(user_id)
    session = core.state.get("_active_court_session")
    if not session or session.get("finished") or session.get("phase") != "recess":
        raise HTTPException(status_code=400, detail="Not in recess phase or no active session")
        
    from .court_logic import process_recess_search
    
    try:
        session = await process_recess_search(session, payload.room_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
    core.state["_active_court_session"] = session
    core._save_state()
    
    return CourtStartResponse(
        session_id=session["id"],
        title=session["title"],
        difficulty=session["difficulty"],
        client_name=session["client_name"],
        client_role=session["client_role"],
        client_bio=session["client_bio"],
        prosecutor_name=session["prosecutor_name"],
        judge_name=session["judge_name"],
        inventory=session["inventory"],
        witnesses=session["witnesses"],
        recess_locations=session["recess_locations"],
        strikes_left=session["strikes_left"],
        jury_sentiment=session["jury_sentiment"],
        current_witness_idx=session["current_witness_idx"],
        recess_searched=session["recess_searched"],
        rem_consults_left=session.get("rem_consults_left", 5),
        rem_chat_history=session.get("rem_chat_history", []),
        history=session["history"],
        phase=session["phase"],
        finished=session["finished"]
    )


@router.post("/games/court/verdict", response_model=CourtVerdictResponse)
async def court_submit_verdict(payload: CourtVerdictRequest, user_id: str = Depends(get_current_user_id)):
    core = _get_core(user_id)
    session = core.state.get("_active_court_session")
    if not session or session.get("finished") or session.get("phase") != "closing":
        raise HTTPException(status_code=400, detail="Not in closing arguments phase or no active session")
        
    from .court_logic import evaluate_court_verdict
    
    try:
        session = await evaluate_court_verdict(session, payload.closing_argument)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
    if session["verdict_result"] and session["verdict_result"]["success"]:
        achievements = core.state.get("_achievements", [])
        if "court_master" not in achievements:
            achievements.append("court_master")
            core.state["_achievements"] = achievements
            
    core.state["_active_court_session"] = session
    core._save_state()
    
    res = session["verdict_result"]
    return CourtVerdictResponse(
        success=res["success"],
        verdict_text=res["verdict_text"],
        votes_not_guilty=res["votes_not_guilty"],
        votes_guilty=res["votes_guilty"],
        judge_decision=res["judge_decision"],
        rem_dialogue=res["rem_dialogue"]
    )


# Helper: forced conversation summary
async def _force_conversation_summary(core, db, session_id: str):
    """Generate a summary of the active session before ending it."""
    db_msgs = db.query(ChatMessage).filter(ChatMessage.session_id == session_id).order_by(ChatMessage.timestamp.desc()).limit(12).all()
    db_msgs = list(reversed(db_msgs))
    if not db_msgs:
        return
        
    message_history = []
    for m in db_msgs:
        message_history.append({
            "role": m.role,
            "content": m.content
        })
        
    try:
        from .discord_bot import _generate_conversation_summary
        core.personality_evolution.interaction_count = core.state.get("_last_summary_at", 0) + 10
        await _generate_conversation_summary(core, message_history)
    except Exception as e:
        print(f"Failed to generate transition summary: {e}")

# Get or create active session id
def _get_active_session_id(user_id: str, db) -> str:
    core = _get_core(user_id)
    active_id = core.state.get("active_session_id")
    if active_id:
        sess = db.query(ChatSession).filter(ChatSession.id == active_id).first()
        if sess:
            return active_id
            
    last_sess = db.query(ChatSession).filter(ChatSession.user_id == user_id).order_by(ChatSession.updated_at.desc()).first()
    if last_sess:
        core.state["active_session_id"] = last_sess.id
        core._save_state()
        return last_sess.id
        
    import secrets
    new_id = "sess_" + secrets.token_hex(8)
    default_sess = ChatSession(id=new_id, user_id=user_id, title="Default Conversation")
    db.add(default_sess)
    db.commit()
    
    core.state["active_session_id"] = new_id
    core._save_state()
    return new_id


@router.get("/sessions", response_model=ChatSessionsListResponse)
async def list_sessions(user_id: str = Depends(get_current_user_id)):
    db = SessionLocal()
    try:
        active_id = _get_active_session_id(user_id, db)
        sessions_db = db.query(ChatSession).filter(ChatSession.user_id == user_id).order_by(ChatSession.updated_at.desc()).all()
        
        sessions_list = []
        for s in sessions_db:
            sessions_list.append(ChatSessionResponse(
                id=s.id,
                title=s.title,
                created_at=s.created_at.isoformat() if hasattr(s.created_at, 'isoformat') else str(s.created_at),
                updated_at=s.updated_at.isoformat() if hasattr(s.updated_at, 'isoformat') else str(s.updated_at)
            ))
            
        return ChatSessionsListResponse(sessions=sessions_list, active_session_id=active_id)
    finally:
        db.close()


@router.post("/sessions/new", response_model=ChatSessionResponse)
async def create_session(payload: CreateSessionRequest, user_id: str = Depends(get_current_user_id)):
    db = SessionLocal()
    try:
        core = _get_core(user_id)
        old_active_id = core.state.get("active_session_id")
        if old_active_id:
            await _force_conversation_summary(core, db, old_active_id)
            
        core.memory.memory["stm"] = []
        core._save_state()
        
        import secrets
        new_id = "sess_" + secrets.token_hex(8)
        
        title = payload.title
        if not title or not title.strip():
            count = db.query(ChatSession).filter(ChatSession.user_id == user_id).count() + 1
            title = f"Conversation {count}"
            
        new_session = ChatSession(id=new_id, user_id=user_id, title=title)
        db.add(new_session)
        db.commit()
        db.refresh(new_session)
        
        core.state["active_session_id"] = new_id
        core._save_state()
        
        return ChatSessionResponse(
            id=new_session.id,
            title=new_session.title,
            created_at=new_session.created_at.isoformat() if hasattr(new_session.created_at, 'isoformat') else str(new_session.created_at),
            updated_at=new_session.updated_at.isoformat() if hasattr(new_session.updated_at, 'isoformat') else str(new_session.updated_at)
        )
    finally:
        db.close()


@router.post("/sessions/switch")
async def switch_session(payload: SwitchSessionRequest, user_id: str = Depends(get_current_user_id)):
    db = SessionLocal()
    try:
        core = _get_core(user_id)
        sess = db.query(ChatSession).filter(ChatSession.id == payload.session_id, ChatSession.user_id == user_id).first()
        if not sess:
            raise HTTPException(status_code=404, detail="Chat session not found")
            
        core.state["active_session_id"] = payload.session_id
        
        db_msgs = db.query(ChatMessage).filter(ChatMessage.session_id == payload.session_id).order_by(ChatMessage.timestamp.desc()).limit(12).all()
        db_msgs = list(reversed(db_msgs))
        
        stm_entries = []
        for m in db_msgs:
            prefix = "[Rem] " if m.role == "assistant" else "[User] "
            stm_entries.append({
                "content": prefix + m.content,
                "timestamp": m.timestamp.isoformat() if hasattr(m.timestamp, 'isoformat') else str(m.timestamp)
            })
            
        core.memory.memory["stm"] = stm_entries
        core._save_state()
        
        return {"success": True, "active_session_id": payload.session_id}
    finally:
        db.close()


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str, user_id: str = Depends(get_current_user_id)):
    db = SessionLocal()
    try:
        core = _get_core(user_id)
        sess = db.query(ChatSession).filter(ChatSession.id == session_id, ChatSession.user_id == user_id).first()
        if not sess:
            raise HTTPException(status_code=404, detail="Chat session not found")
            
        db.query(ChatMessage).filter(ChatMessage.session_id == session_id).delete()
        db.delete(sess)
        db.commit()
        
        if core.state.get("active_session_id") == session_id:
            core.state["active_session_id"] = None
            core.memory.memory["stm"] = []
            core._save_state()
            
        return {"success": True}
    finally:
        db.close()


@router.put("/sessions/{session_id}")
async def rename_session(session_id: str, payload: RenameSessionRequest, user_id: str = Depends(get_current_user_id)):
    db = SessionLocal()
    try:
        sess = db.query(ChatSession).filter(ChatSession.id == session_id, ChatSession.user_id == user_id).first()
        if not sess:
            raise HTTPException(status_code=404, detail="Chat session not found")
        
        title = payload.title.strip()
        if not title:
            raise HTTPException(status_code=400, detail="Title cannot be empty")
            
        sess.title = title
        db.commit()
        db.refresh(sess)
        
        return {"success": True, "id": sess.id, "title": sess.title}
    finally:
        db.close()





