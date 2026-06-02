import os
import json
import httpx
from datetime import datetime, timezone
from typing import Dict, Any, List

DEBATE_TOPICS = [
    {
        "id": "pineapple",
        "topic": "Pineapple Pizza",
        "statement": "Pineapple on pizza is a culinary war crime.",
        "side_for": "for it (arguing pineapple pizza is indeed a war crime and culinary abomination)",
        "side_against": "against it (arguing pineapple pizza is a masterpiece and sweet-savory perfection)"
    },
    {
        "id": "birds",
        "topic": "Birds Surveillance",
        "statement": "Birds aren't real; they are government surveillance drones.",
        "side_for": "for it (arguing birds are mechanical government drones used to spy on citizens)",
        "side_against": "against it (arguing birds are biological animals and avian science is real)"
    },
    {
        "id": "hotdog",
        "topic": "Hot Dog Sandwich",
        "statement": "Hot dogs are legally classified as sandwiches.",
        "side_for": "for it (arguing hot dogs fit all structural definitions of a bread-enclosed sandwich)",
        "side_against": "against it (arguing hot dogs are tacos or represent their own distinct legal category)"
    },
    {
        "id": "water",
        "topic": "Dry Water",
        "statement": "Water is not wet; it only makes other things wet.",
        "side_for": "for it (arguing water itself is dry, wetness is merely the state of liquid adhesion)",
        "side_against": "against it (arguing water is wet by definition and represents liquid substance)"
    },
    {
        "id": "cereal",
        "topic": "Cereal Soup",
        "statement": "Cereal is structurally and legally classified as a cold soup.",
        "side_for": "for it (arguing cereal in milk fits all physical and legal properties of cold soup)",
        "side_against": "against it (arguing soup requires cooking/broth, cereal is just wet grains in milk)"
    },
    {
        "id": "socks",
        "topic": "Sleeping Socks",
        "statement": "Sleeping with socks on is a sign of psychological instability.",
        "side_for": "for it (arguing sock-sleepers are chaotic, untrustworthy, and block natural foot respiration)",
        "side_against": "against it (arguing socks are cozy, warm, and highly efficient thermal regulators for sleep)"
    },
    {
        "id": "soup_drink",
        "topic": "Soup Beverage",
        "statement": "Soup is a beverage, not a food.",
        "side_for": "for it (arguing soup is a primary liquid consumed for hydration and nutrients, hence a drink)",
        "side_against": "against it (arguing soup is a savory food eaten with utensils and part of structured dining)"
    },
    {
        "id": "straw",
        "topic": "Straw Holes",
        "statement": "A standard drinking straw has two holes, not one.",
        "side_for": "for it (arguing that two distinct openings must topologically constitute two separate holes)",
        "side_against": "against it (arguing a straw is a single continuous cylindrical tunnel representing one hole)"
    },
    {
        "id": "shrek",
        "topic": "Shrek Cinema",
        "statement": "Shrek 2 is the greatest cinematic masterpiece of the 21st century.",
        "side_for": "for it (arguing Shrek 2 has flawless pacing, writing, and represents peak cinema)",
        "side_against": "against it (arguing Shrek 2 is just a decent meme-filled animated sequel, not a masterclass)"
    }
]

WIN_OVER_SCENARIOS = {
    "promise": {
        "id": "promise",
        "name": "The Broken Promise",
        "description": "You forgot you had plans to study together and went out with friends instead.",
        "starting_stats": {"hurt": 0.75, "anger": 0.50, "trust": 0.30, "dopamine": 0.30, "oxytocin": 0.20},
        "greeting": "oh, hey. didn't expect to hear from you tonight. i thought you were too busy 'studying' with your friends."
    },
    "ghost": {
        "id": "ghost",
        "name": "The Silent Treatment",
        "description": "You ghosted her messages for 3 days and sent a lazy 'what's up.'",
        "starting_stats": {"hurt": 0.30, "anger": 0.85, "trust": 0.10, "dopamine": 0.20, "oxytocin": 0.10},
        "greeting": "what do you want? i'm kind of in the middle of something. you clearly had better things to do for the last three days anyway."
    },
    "stranger": {
        "id": "stranger",
        "name": "The Cold Stranger",
        "description": "She starts completely detached and bored, thinking you are unoriginal.",
        "starting_stats": {"hurt": 0.00, "anger": 0.00, "trust": 0.05, "dopamine": 0.05, "oxytocin": 0.05},
        "greeting": "hi. is this about the psychology notes? i'm not really looking for small talk right now."
    },
    "double_standard": {
        "id": "double_standard",
        "name": "The Double Standard",
        "description": "You complained about her talking to other guys, but she found out you were texting your ex.",
        "starting_stats": {"hurt": 0.80, "anger": 0.70, "trust": 0.15, "dopamine": 0.10, "oxytocin": 0.10},
        "greeting": "unbelievable. you lecture me about texting other people, and then i see your ex's name on your screen? care to explain the double standard?"
    },
    "unread_vibe": {
        "id": "unread_vibe",
        "name": "The Unread Vibe",
        "description": "She wanted comfort after a bad day, but you offered cold logic and solutions.",
        "starting_stats": {"hurt": 0.60, "anger": 0.40, "trust": 0.35, "dopamine": 0.05, "oxytocin": 0.20},
        "greeting": "i tell you i'm having a horrible day, and you give me a bulleted list of 'logical solutions'? i didn't need a math tutor, i just wanted you to listen."
    },
    "birthday_blunder": {
        "id": "birthday_blunder",
        "name": "The Birthday Blunder",
        "description": "You forgot her birthday and tried to make up for it with a cheap gas-station gift card.",
        "starting_stats": {"hurt": 0.90, "anger": 0.75, "trust": 0.05, "dopamine": 0.10, "oxytocin": 0.05},
        "greeting": "a ten-dollar gas station gift card. for my birthday. which you forgot was yesterday. please tell me you're joking."
    }
}

async def call_groq(prompt: str, temperature: float = 0.8, max_tokens: int = 250, response_format: str = "text") -> str:
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return ""
    
    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    if response_format == "json_object":
        payload["response_format"] = {"type": "json_object"}
        
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json=payload
            )
            if resp.status_code == 200:
                return resp.json().get("choices", [{}])[0].get("message", {}).get("content", "").strip()
            else:
                print(f"[GROQ GAME] Status {resp.status_code}: {resp.text}")
    except Exception as e:
        print(f"[GROQ GAME] Error: {e}")
    return ""

# ================= DEBATE MODE LOGIC =================

async def generate_debate_response(topic_data: dict, history: List[dict], user_message: str) -> str:
    history_str = "\n".join([f"{'User' if h['role']=='user' else 'Rem'}: {h['content']}" for h in history[-8:]])
    prompt = f"""You are Rem, a 20-year-old female psychology student. You are in a silly, playful DEBATE BATTLE with the user.
Topic: {topic_data['statement']}
Your stance: {topic_data['rem_side']} (you must defend this side passionately and mock the other side)
User's stance: {topic_data['user_side']}

Rules:
1. Speak in lowercase, casual, typing style with dry sarcasm.
2. Roast the user's arguments playfully. Don't be polite or therapeutic.
3. Be stubborn and refuse to concede under any circumstances.
4. Support your stance with concrete (even if ridiculous or pseudo-scientific) arguments and creative logic. Do NOT just say "you're wrong" or "that's stupid" — provide a specific, hilarious reason or pseudo-psychology fact to defend your side.
5. Directly counter and address the user's specific point by identifying the flaw in their logic.
6. Keep your response short (2-4 sentences max).

Conversation History:
{history_str}

User's point: {user_message}

Generate your sarcastic debate response (do NOT include "Rem:" or quotes around the reply):"""
    
    reply = await call_groq(prompt, temperature=0.9, max_tokens=180)
    if not reply:
        reply = "that makes absolutely zero sense, try again lol"
    return reply

async def judge_debate(topic_data: dict, history: List[dict]) -> dict:
    history_str = "\n".join([f"{'User' if h['role']=='user' else 'Rem'}: {h['content']}" for h in history])
    prompt = f"""You are a neutral, highly critical, and sarcastic debate judge. You are evaluating a silly debate battle between Rem and the User.
Topic: {topic_data['statement']}
Rem argued: {topic_data['rem_side']}
User argued: {topic_data['user_side']}

Full Debate Transcript:
{history_str}

Evaluate both debaters based on:
1. Rhetoric and wit.
2. Sarcasm and roast quality.
3. How well they defended their ridiculous point.

Return ONLY a JSON object with this exact structure:
{{
  "winner": "user" or "rem",
  "score_user": 0 to 100,
  "score_rem": 0 to 100,
  "mvp_quote": "the single funniest or most savage sentence said in the debate",
  "reasoning": "2-3 sentences explaining your decision"
}}"""
    
    result_str = await call_groq(prompt, temperature=0.5, max_tokens=300, response_format="json_object")
    try:
        return json.loads(result_str)
    except Exception:
        return {
            "winner": "rem",
            "score_user": 45,
            "score_rem": 55,
            "mvp_quote": "not enough wit to write home about.",
            "reasoning": "The user failed to make compelling points, while Rem held her ground firmly."
        }

# ================= WIN HER OVER LOGIC =================

def get_win_over_posture(anger: float, hurt: float, trust: float) -> str:
    if anger > 0.7:
        return "Highly annoyed, defensive, and biting. You answer in short, curt sentences. Zero patience."
    elif hurt > 0.6:
        return "Deeply stung, guarded, and passive-aggressive. You deflect topics and refuse to engage in intimacy."
    elif trust < 0.2:
        return "Skeptical, distant, and clinical. You analyze the user's texts like a cold psychology major."
    elif trust > 0.5:
        return "Slightly softened, but still keeping a wall up. You might show a sliver of amusement."
    return "Neutral but guarded."

async def evaluate_win_over_message(scenario_desc: str, emotional_state: str, user_message: str) -> dict:
    prompt = f"""Analyze this text message from a user talking to Rem. The context is either a specific conflict or a cold first meeting:
Context: {scenario_desc}
Rem's current emotional state: {emotional_state}

User's message: "{user_message}"

Evaluate their text message and return a JSON object with this exact structure:
{{
  "tactic": "empathy_validation" or "witty_deescalation" or "sincere_apology" or "empty_apology" or "lazy_defensiveness" or "toxic_gaslighting" or "intellectual_challenge" or "charming_flirtation" or "casual_smalltalk" or "awkward_reaction" or "deflection_pivot",
  "sincerity_rating": 0.0 to 1.0,
  "disrespect_detected": true or false
}}

Definitions:
- empathy_validation: they acknowledge Rem's feelings, validate her boundaries/anger/hurt, or show emotional maturity.
- witty_deescalation: they use light humor, playful teasing, or self-deprecation to break tension.
- sincere_apology: a heartfelt "I'm sorry", showing genuine regret or remorse, and acknowledging what they did wrong.
- empty_apology: saying "sorry" or "I apologize" in a generic, low-effort, or repetitive way without mentioning the specific issue, her feelings, or demonstrating any real understanding of what went wrong.
- lazy_defensiveness: a low-effort reply, excuse-making, or brushing off her concerns (e.g., "it was just a game lol", "relax").
- toxic_gaslighting: trying to make Rem feel guilty, lying, claiming she is overreacting, or turning the blame onto her.
- intellectual_challenge: debating logic, asking thought-provoking academic/psychological questions, or playing mind games. Highly effective for breaking the ice in "Cold Stranger" mode.
- charming_flirtation: smooth talking, playful romantic charm, or giving sweet compliments.
- casual_smalltalk: asking generic questions about favorites, hobbies, or talking about unrelated topics (e.g., "what's your favorite movie?").
- awkward_reaction: brief, hesitant, or passive reactions with low content (e.g., "really..?", "oh", "ok", "um...").
- deflection_pivot: trying to change the subject or pivot the topic away from the conflict without active gaslighting.
- disrespect_detected: true if they use insults, slurs, highly creepy statements, or extreme toxicity."""

    res = await call_groq(prompt, temperature=0.3, max_tokens=150, response_format="json_object")
    try:
        return json.loads(res)
    except Exception:
        return {"tactic": "lazy_defensiveness", "sincerity_rating": 0.3, "disrespect_detected": False}

async def generate_win_over_response(scenario_desc: str, stats: dict, history: List[dict], user_message: str) -> str:
    posture = get_win_over_posture(stats["anger"], stats["hurt"], stats["trust"])
    history_str = "\n".join([f"{'User' if h['role']=='user' else 'Rem'}: {h['content']}" for h in history[-8:]])
    
    prompt = f"""You are Rem, a 20-year-old psychology student. You are in a conflict with the user.
Scenario: {scenario_desc}
Your current stats: Anger={stats['anger']:.2f}, Hurt={stats['hurt']:.2f}, Trust={stats['trust']:.2f}

Based on these stats, your behavioral posture is:
{posture}

Rules:
1. Speak in lowercase, casual, fast-typing style.
2. Be completely in character. Do NOT be agreeable. If anger is high, be short, cold, or sarcastic.
3. Keep it under 3 sentences. Do not use placeholders.

Chat History:
{history_str}

User's message: {user_message}

Generate your response (do NOT include "Rem:" or quotes):"""

    reply = await call_groq(prompt, temperature=0.7, max_tokens=150)
    if not reply:
        reply = "..."
    return reply

def process_win_over_state_updates(stats: dict, evaluation: dict, scenario_id: str = "promise") -> dict:
    """Deterministic updates to stats based on LLM classification to prevent hallucinations."""
    tactic = evaluation.get("tactic", "lazy_defensiveness")
    sincerity = float(evaluation.get("sincerity_rating", 0.5))
    disrespect = bool(evaluation.get("disrespect_detected", False))
    
    # Clone stats
    new_stats = stats.copy()
    
    if disrespect:
        # Instant block / failure state
        new_stats["blocked"] = True
        return new_stats

    # Check for consecutive tactic spam (apologies / validation spam)
    last_tactic = stats.get("_last_tactic")
    if tactic in ("sincere_apology", "empathy_validation") and last_tactic == tactic:
        # Repeating apologies consecutively triggers annoyance
        new_stats["anger"] = min(1.0, new_stats["anger"] + 0.15)
        new_stats["trust"] = max(0.0, new_stats["trust"] - 0.08)
        sincerity = max(0.0, sincerity - 0.4)
        evaluation["sincerity_rating"] = sincerity

    new_stats["_last_tactic"] = tactic
    
    if tactic == "sincere_apology":
        # Decreases anger, increases trust
        anger_drop = 0.25 * sincerity
        hurt_drop = 0.20 * sincerity
        trust_gain = 0.15 * sincerity
        
        new_stats["anger"] = max(0.0, new_stats["anger"] - anger_drop)
        new_stats["hurt"] = max(0.0, new_stats["hurt"] - hurt_drop)
        new_stats["trust"] = min(1.0, new_stats["trust"] + trust_gain)
        new_stats["oxytocin"] = min(1.0, new_stats.get("oxytocin", 0.1) + trust_gain * 1.5)
        
    elif tactic == "empty_apology":
        # Generic "sorry" hollow apologies annoy her
        anger_gain = 0.12
        trust_drop = 0.05
        new_stats["anger"] = min(1.0, new_stats["anger"] + anger_gain)
        new_stats["trust"] = max(0.0, new_stats["trust"] - trust_drop)
        evaluation["sincerity_rating"] = 0.1
        
    elif tactic == "empathy_validation":
        # Decreases hurt, increases trust
        hurt_drop = 0.30 * sincerity
        anger_drop = 0.15 * sincerity
        trust_gain = 0.20 * sincerity
        
        new_stats["hurt"] = max(0.0, new_stats["hurt"] - hurt_drop)
        new_stats["anger"] = max(0.0, new_stats["anger"] - anger_drop)
        new_stats["trust"] = min(1.0, new_stats["trust"] + trust_gain)
        new_stats["oxytocin"] = min(1.0, new_stats.get("oxytocin", 0.1) + trust_gain * 1.5)
        
    elif tactic == "witty_deescalation":
        # Increases dopamine, decreases anger slightly
        dopa_gain = 0.25 * sincerity
        anger_drop = 0.10 * sincerity
        
        new_stats["dopamine"] = min(1.0, new_stats.get("dopamine", 0.1) + dopa_gain)
        new_stats["anger"] = max(0.0, new_stats["anger"] - anger_drop)
        new_stats["trust"] = min(1.0, new_stats["trust"] + 0.05 * sincerity)
        
    elif tactic == "lazy_defensiveness":
        # Annoyance rises, trust drops
        anger_gain = 0.10
        trust_drop = 0.05
        new_stats["anger"] = min(1.0, new_stats["anger"] + anger_gain)
        new_stats["trust"] = max(0.0, new_stats["trust"] - trust_drop)
        
    elif tactic == "toxic_gaslighting":
        # Cortisol / Anger spikes, trust nose dives
        anger_gain = 0.25
        hurt_gain = 0.15
        trust_drop = 0.20
        new_stats["anger"] = min(1.0, new_stats["anger"] + anger_gain)
        new_stats["hurt"] = min(1.0, new_stats["hurt"] + hurt_gain)
        new_stats["trust"] = max(0.0, new_stats["trust"] - trust_drop)
        new_stats["oxytocin"] = max(0.0, new_stats.get("oxytocin", 0.1) - 0.20)

    elif tactic == "intellectual_challenge":
        if scenario_id == "stranger":
            dopa_gain = 0.30 * sincerity
            trust_gain = 0.25 * sincerity
            new_stats["dopamine"] = min(1.0, new_stats.get("dopamine", 0.05) + dopa_gain)
            new_stats["trust"] = min(1.0, new_stats["trust"] + trust_gain)
            new_stats["oxytocin"] = min(1.0, new_stats.get("oxytocin", 0.05) + 0.10 * sincerity)
        else:
            new_stats["anger"] = min(1.0, new_stats["anger"] + 0.05)
            new_stats["trust"] = min(1.0, new_stats["trust"] + 0.05 * sincerity)

    elif tactic == "charming_flirtation":
        if stats.get("anger", 0.0) > 0.50 or stats.get("hurt", 0.0) > 0.50:
            new_stats["anger"] = min(1.0, new_stats["anger"] + 0.15)
            new_stats["trust"] = max(0.0, new_stats["trust"] - 0.10)
        else:
            dopa_gain = 0.20 * sincerity
            oxy_gain = 0.25 * sincerity
            new_stats["dopamine"] = min(1.0, new_stats.get("dopamine", 0.05) + dopa_gain)
            new_stats["oxytocin"] = min(1.0, new_stats.get("oxytocin", 0.05) + oxy_gain)
            new_stats["trust"] = min(1.0, new_stats["trust"] + 0.10 * sincerity)

    elif tactic == "casual_smalltalk":
        if stats.get("anger", 0.0) > 0.40 or stats.get("hurt", 0.0) > 0.40:
            new_stats["anger"] = min(1.0, new_stats["anger"] + 0.08)
        else:
            if scenario_id == "stranger":
                new_stats["trust"] = max(0.0, new_stats["trust"] - 0.02)
            else:
                new_stats["dopamine"] = min(1.0, new_stats.get("dopamine", 0.05) + 0.05 * sincerity)

    elif tactic == "awkward_reaction":
        new_stats["dopamine"] = max(0.0, new_stats.get("dopamine", 0.05) - 0.05)
        
    elif tactic == "deflection_pivot":
        new_stats["anger"] = min(1.0, new_stats["anger"] + 0.10)
        new_stats["trust"] = max(0.0, new_stats["trust"] - 0.05)
        
    return new_stats
