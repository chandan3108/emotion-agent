"""
Human-like messaging utilities for R.E.M.
Handles message splitting, typos, emoji reactions, and timing.
"""

import random
import re
import asyncio
from typing import List, Tuple, Optional

# ========== EMOJI REACTION MAPPING ==========

VIBE_EMOJI_MAP = {
    "playful": ["😏", "💀", "😂", "🙄", "😭"],
    "warm": ["❤️", "🥰", "☺️", "🫶"],
    "vulnerable": ["🥺", "💙", "🫂"],
    "tense": ["😐", "😤", "🫠"],
    "neutral": [],  # No reaction for neutral
}

# Probability of reacting with an emoji (per message)
REACTION_PROBABILITY = 0.30


async def maybe_react(message, emotional_vibe: str):
    """
    Maybe add an emoji reaction to the user's message before responding.
    Uses the emotional_vibe from pre-assessment to choose appropriate emoji.
    """
    if not emotional_vibe or emotional_vibe == "neutral":
        return
    if random.random() > REACTION_PROBABILITY:
        return
    
    emojis = VIBE_EMOJI_MAP.get(emotional_vibe.lower(), [])
    if not emojis:
        return
    
    try:
        emoji = random.choice(emojis)
        await message.add_reaction(emoji)
        # Small pause after reacting — like "reading then reacting then typing"
        await asyncio.sleep(random.uniform(0.3, 1.0))
    except Exception:
        pass  # Never crash over a reaction


# ========== MESSAGE SPLITTING ==========

# Words/phrases that make natural split points when they START a segment
SPLIT_STARTERS = [
    "wait ", "but ", "also ", "okay ", "like ", "ngl ", "tbh ",
    "actually ", "honestly ", "lowkey ", "no but ", "okay but ",
]


def smart_split(text: str, max_parts: int = 3) -> List[str]:
    """
    Split a response into multiple chunks like a real texter.
    Returns 1-3 parts. Shorter messages stay as one.
    """
    text = text.strip()
    
    # Don't split short messages
    if len(text) < 45:
        return [text]
    
    # 45% chance to split (not every message)
    if random.random() > 0.45:
        return [text]
    
    parts = []
    
    # Strategy 1: Split on sentence boundaries
    # Look for ". " followed by a new sentence
    sentences = re.split(r'(?<=[.!?])\s+', text)
    
    if len(sentences) >= 2:
        # Group sentences into 2-3 chunks
        if len(sentences) == 2:
            parts = sentences
        elif len(sentences) >= 3:
            # Split roughly evenly
            mid = len(sentences) // 2
            parts = [
                " ".join(sentences[:mid]),
                " ".join(sentences[mid:])
            ]
            # Maybe split the second part too
            if len(sentences) >= 4 and random.random() < 0.4:
                mid2 = len(sentences[mid:]) // 2
                second_half = sentences[mid:]
                parts = [
                    " ".join(sentences[:mid]),
                    " ".join(second_half[:mid2]),
                    " ".join(second_half[mid2:])
                ]
    
    # Strategy 2: Split on natural break words ("but", "also", "wait")
    if len(parts) <= 1:
        text_lower = text.lower()
        for starter in SPLIT_STARTERS:
            # Find the starter in the middle of the text (not at the very beginning)
            search_start = max(15, len(text) // 4)  # Don't split too early
            pos = text_lower.find(starter, search_start)
            if pos > 0:
                part1 = text[:pos].rstrip(" ,")
                part2 = text[pos:]
                if len(part1) > 10 and len(part2) > 10:
                    parts = [part1, part2]
                    break
    
    # Fallback: return as-is
    if len(parts) <= 1:
        return [text]
    
    # Clean up parts
    cleaned = [p.strip() for p in parts if p.strip()]
    return cleaned[:max_parts]


# ========== TYPING DELAY ==========

def calculate_typing_delay(text: str, is_first: bool = True) -> float:
    """
    Calculate a realistic typing delay based on text length.
    First message: slightly longer (reading + thinking + typing).
    Follow-up chunks: shorter (already typing).
    """
    char_count = len(text)
    
    if is_first:
        # Base: 30ms per char + thinking time
        base = char_count * 0.03 + random.uniform(0.5, 1.5)
        return max(1.5, min(base, 6.0))
    else:
        # Follow-up chunk: faster, you're already in typing mode
        base = char_count * 0.025 + random.uniform(0.3, 0.8)
        return max(0.8, min(base, 3.5))


# ========== TYPOS + SELF-CORRECTION ==========

# Probability of introducing a typo (per message)
TYPO_PROBABILITY = 0.05


def introduce_typo(text: str) -> Tuple[str, Optional[str]]:
    """
    Introduce a plausible typo by swapping two adjacent letters.
    Returns (typo'd text, original_word) or (original text, None) if no typo made.
    """
    words = text.split()
    # Find candidate words: 4+ letters, alphabetic, not the first word
    candidates = [
        (i, w) for i, w in enumerate(words) 
        if len(w) >= 4 and w.isalpha() and i > 0
    ]
    
    if not candidates:
        return text, None
    
    idx, word = random.choice(candidates)
    
    # Swap two adjacent chars in the second half of the word
    char_list = list(word.lower())
    pos = random.randint(max(1, len(char_list) // 2), len(char_list) - 2)
    char_list[pos], char_list[pos + 1] = char_list[pos + 1], char_list[pos]
    typo_word = "".join(char_list)
    
    # Only use if it actually changed something
    if typo_word == word.lower():
        return text, None
    
    words[idx] = typo_word
    return " ".join(words), word.lower()


async def send_with_human_touch(channel, message_obj, response_text: str, 
                                 emotional_vibe: str = "neutral",
                                 skip_reaction: bool = False):
    """
    Send a response with human-like behavior:
    1. Maybe react with emoji first
    2. Maybe introduce a typo + correction
    3. Split into multiple messages with typing delays
    
    This is the main entry point — replaces channel.send(response).
    """
    # Step 1: Emoji reaction (before typing)
    if not skip_reaction:
        await maybe_react(message_obj, emotional_vibe)
    
    # Step 2: Decide typo vs normal
    if random.random() < TYPO_PROBABILITY and len(response_text) > 30:
        typo_text, original_word = introduce_typo(response_text)
        if original_word:
            # Send typo'd version
            async with channel.typing():
                await asyncio.sleep(calculate_typing_delay(typo_text, is_first=True))
            await channel.send(typo_text)
            
            # Pause, then send correction
            await asyncio.sleep(random.uniform(1.0, 2.5))
            await channel.send(f"{original_word}*")
            return
    
    # Step 3: Split and send with delays
    parts = smart_split(response_text)
    
    for i, part in enumerate(parts):
        delay = calculate_typing_delay(part, is_first=(i == 0))
        async with channel.typing():
            await asyncio.sleep(delay)
        await channel.send(part)
        
        # Small gap between multi-message parts
        if i < len(parts) - 1:
            await asyncio.sleep(random.uniform(0.3, 0.6))
