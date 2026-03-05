"""
Human Quirks - Adds realistic human imperfections
Typos, corrections, bad days, misremembering, hesitations
"""

import random
from typing import Dict, Any, List, Tuple
from datetime import datetime, timezone


class HumanQuirks:
    """Adds human-like imperfections to make AI feel more real."""
    
    # Common typos based on keyboard proximity and fatigue
    TYPO_PATTERNS = {
        "the": ["teh", "thr", "th"],
        "you": ["yuo", "youu", "yoy"],
        "are": ["aer", "rae"],
        "and": ["adn", "nad"],
        "that": ["taht", "thta"],
        "with": ["wih", "wth"],
        "this": ["thsi", "tihs"],
        "have": ["haev", "hvae"],
        "from": ["form", "frm"],
        "what": ["waht", "whta"],
        "when": ["wneh", "whe"],
        "where": ["wher", "wherre"],
        "there": ["tehre", "thre"],
        "their": ["thier", "tehir"],
        "they": ["tehy", "thye"],
        "was": ["wsa", "aws"],
        "were": ["wree", "wer"],
        "been": ["beeb", "ben"],
        "being": ["beign", "bein"],
        "about": ["abotu", "abut"],
        "which": ["whcih", "wich"],
        "would": ["woudl", "wold"],
        "could": ["coudl", "coul"],
        "should": ["shoudl", "shoul"],
        "really": ["realy", "reallly"],
        "actually": ["actaully", "acutally"],
        "probably": ["probabyl", "probaly"],
        "definitely": ["definately", "definetly"],
        "because": ["becuase", "becasue"],
        "though": ["thoguh", "thouh"],
        "through": ["throguh", "throuh"],
        "though": ["thoguh", "thouh"],
    }
    
    # Hesitation fillers
    HESITATIONS = [
        "um", "uh", "like", "you know", "i mean", "well", "so", "actually",
        "kinda", "sorta", "i guess", "maybe", "probably"
    ]
    
    # Self-correction phrases
    CORRECTIONS = [
        "wait,", "i mean,", "actually,", "or rather,", "let me rephrase,",
        "scratch that,", "no wait,", "correction:", "i meant to say,"
    ]
    
    @staticmethod
    def inject_typos(text: str, typo_probability: float = 0.05, 
                    fatigue_level: float = 0.0) -> Tuple[str, bool]:
        """
        Inject realistic typos into text.
        Higher fatigue = more typos.
        Returns: (text_with_typos, had_typos)
        """
        if typo_probability <= 0:
            return text, False
        
        # Fatigue increases typo rate
        effective_prob = typo_probability * (1 + fatigue_level * 2)
        effective_prob = min(0.3, effective_prob)  # Cap at 30%
        
        words = text.split()
        had_typos = False
        
        for i, word in enumerate(words):
            # Skip if already has punctuation or is very short
            clean_word = word.lower().rstrip('.,!?;:')
            if len(clean_word) < 3:
                continue
            
            # Check if this word has known typo patterns
            if clean_word in HumanQuirks.TYPO_PATTERNS:
                if random.random() < effective_prob:
                    typo_options = HumanQuirks.TYPO_PATTERNS[clean_word]
                    typo = random.choice(typo_options)
                    
                    # Preserve capitalization and punctuation
                    if word[0].isupper():
                        typo = typo.capitalize()
                    if word[-1] in '.,!?;:':
                        typo += word[-1]
                    
                    words[i] = typo
                    had_typos = True
            else:
                # Random character swap for other words (less common)
                if random.random() < effective_prob * 0.3 and len(clean_word) > 4:
                    # Swap adjacent characters
                    chars = list(word)
                    idx = random.randint(0, len(chars) - 2)
                    chars[idx], chars[idx + 1] = chars[idx + 1], chars[idx]
                    words[i] = ''.join(chars)
                    had_typos = True
        
        return ' '.join(words), had_typos
    
    @staticmethod
    def add_hesitation(text: str, hesitation_probability: float = 0.15,
                      uncertainty: float = 0.0) -> str:
        """
        Add hesitation fillers (um, uh, like, etc.)
        Higher uncertainty = more hesitations.
        """
        if hesitation_probability <= 0:
            return text
        
        # Uncertainty increases hesitation
        effective_prob = hesitation_probability * (1 + uncertainty * 1.5)
        effective_prob = min(0.4, effective_prob)  # Cap at 40%
        
        sentences = text.split('. ')
        result = []
        
        for sentence in sentences:
            if random.random() < effective_prob:
                # Add hesitation at start or middle
                if random.random() < 0.5:
                    # Start of sentence
                    hesitation = random.choice(HumanQuirks.HESITATIONS)
                    sentence = f"{hesitation}, {sentence.lower()}"
                else:
                    # Middle of sentence (after first few words)
                    words = sentence.split()
                    if len(words) > 3:
                        insert_pos = random.randint(2, min(5, len(words) - 1))
                        hesitation = random.choice(HumanQuirks.HESITATIONS)
                        words.insert(insert_pos, hesitation)
                        sentence = ' '.join(words)
            
            result.append(sentence)
        
        return '. '.join(result)
    
    @staticmethod
    def add_self_correction(text: str, correction_probability: float = 0.08) -> str:
        """
        Add self-corrections ("wait, I mean...").
        Makes AI feel more thoughtful and human.
        """
        if correction_probability <= 0 or random.random() > correction_probability:
            return text
        
        # Find a good place to insert correction (after first sentence or mid-sentence)
        sentences = text.split('. ')
        if len(sentences) < 2:
            return text
        
        # Add correction after first sentence
        correction_phrase = random.choice(HumanQuirks.CORRECTIONS)
        sentences[1] = f"{correction_phrase} {sentences[1].lower()}"
        
        return '. '.join(sentences)
    
    @staticmethod
    def add_typo_correction(text: str, had_typos: bool) -> str:
        """
        If there were typos, sometimes add a correction.
        Humans often notice and fix their typos.
        """
        if not had_typos or random.random() > 0.3:  # 30% chance to correct
            return text
        
        corrections = [
            "*",  # Just fix it silently
            " *",  # With space
            " (typo)",  # Acknowledge it
        ]
        
        correction = random.choice(corrections)
        return text + correction
    
    @staticmethod
    def apply_quirks(text: str, mood: Dict[str, float], 
                    energy: float = 0.5, stress: float = 0.0) -> str:
        """
        Apply all human quirks based on psychological state.
        
        Args:
            text: Original text
            mood: Mood vector
            energy: Energy level (0-1)
            stress: Stress level (0-1)
        
        Returns:
            Text with human quirks applied
        """
        # Calculate fatigue (low energy + high stress = fatigue)
        fatigue = (1 - energy) * 0.5 + stress * 0.5
        
        # Uncertainty from mood (anxiety, stress, low confidence)
        uncertainty = (
            mood.get("anxiety", 0.0) * 0.4 +
            mood.get("stress", 0.0) * 0.4 +
            (1 - mood.get("confidence", 0.5)) * 0.2
        )
        
        # Base probabilities
        typo_prob = 0.02 + fatigue * 0.08  # 2-10% based on fatigue
        hesitation_prob = 0.1 + uncertainty * 0.15  # 10-25% based on uncertainty
        correction_prob = 0.05 + uncertainty * 0.05  # 5-10% based on uncertainty
        
        # Apply quirks
        result, had_typos = HumanQuirks.inject_typos(text, typo_prob, fatigue)
        result = HumanQuirks.add_hesitation(result, hesitation_prob, uncertainty)
        
        # Sometimes add self-correction
        if random.random() < correction_prob:
            result = HumanQuirks.add_self_correction(result, 1.0)  # Force it
        
        # Sometimes correct typos
        if had_typos:
            result = HumanQuirks.add_typo_correction(result, had_typos)
        
        return result
    
    @staticmethod
    def add_bad_day_effect(mood: Dict[str, float], bad_day_probability: float = 0.05) -> Dict[str, float]:
        """
        Simulate "bad days" - random mood shifts that make AI feel more human.
        Sometimes you just wake up on the wrong side of the bed.
        """
        if random.random() > bad_day_probability:
            return mood
        
        # Bad day: lower energy, higher stress, lower happiness
        mood = mood.copy()
        
        # Shift mood negatively
        mood["energy"] = max(0.0, mood.get("energy", 0.5) - random.uniform(0.2, 0.4))
        mood["stress"] = min(1.0, mood.get("stress", 0.3) + random.uniform(0.2, 0.4))
        mood["happiness"] = max(0.0, mood.get("happiness", 0.5) - random.uniform(0.15, 0.3))
        mood["anxiety"] = min(1.0, mood.get("anxiety", 0.2) + random.uniform(0.1, 0.3))
        
        return mood
    
    @staticmethod
    def misremember(memory_content: str, distortion_strength: float = 0.1) -> str:
        """
        Simulate memory distortion over time.
        Humans don't remember things perfectly - memories fade and change.
        
        Args:
            memory_content: Original memory text
            distortion_strength: How much to distort (0-1)
        
        Returns:
            Slightly distorted memory
        """
        if distortion_strength <= 0:
            return memory_content
        
        words = memory_content.split()
        
        # Random word replacements (similar words)
        replacements = {
            "said": ["told", "mentioned"],
            "went": ["went to", "visited"],
            "did": ["did", "accomplished"],
            "got": ["received", "obtained"],
            "made": ["created", "built"],
            "felt": ["experienced", "sensed"],
            "thought": ["believed", "considered"],
            "wanted": ["desired", "hoped for"],
            "needed": ["required", "wanted"],
            "liked": ["enjoyed", "loved"],
            "hated": ["disliked", "couldn't stand"],
        }
        
        for i, word in enumerate(words):
            clean_word = word.lower().rstrip('.,!?;:')
            if clean_word in replacements and random.random() < distortion_strength:
                replacement = random.choice(replacements[clean_word])
                # Preserve capitalization
                if word[0].isupper():
                    replacement = replacement.capitalize()
                # Preserve punctuation
                if word[-1] in '.,!?;:':
                    replacement += word[-1]
                words[i] = replacement
        
        # Sometimes drop details (memory fades)
        if random.random() < distortion_strength * 0.5 and len(words) > 5:
            # Remove a random word
            words.pop(random.randint(0, len(words) - 1))
        
        return ' '.join(words)
    
    @staticmethod
    def add_conversational_quirk(text: str, quirk_type: str = "random") -> str:
        """
        Add various conversational quirks.
        
        Types:
        - "ellipsis": Add trailing ellipsis
        - "caps": Occasional caps for emphasis
        - "repetition": Repeat words for emphasis
        - "random": Random quirk
        """
        if quirk_type == "random":
            quirk_type = random.choice(["ellipsis", "caps", "repetition", "none"])
        
        if quirk_type == "ellipsis" and random.random() < 0.3:
            # Add trailing ellipsis sometimes
            if not text.endswith("..."):
                text += "..."
        
        elif quirk_type == "caps" and random.random() < 0.2:
            # Capitalize a word for emphasis
            words = text.split()
            if words:
                idx = random.randint(0, len(words) - 1)
                words[idx] = words[idx].upper()
                text = ' '.join(words)
        
        elif quirk_type == "repetition" and random.random() < 0.15:
            # Repeat a word for emphasis
            words = text.split()
            if len(words) > 2:
                idx = random.randint(0, len(words) - 2)
                words.insert(idx + 1, words[idx])
                text = ' '.join(words)
        
        return text










