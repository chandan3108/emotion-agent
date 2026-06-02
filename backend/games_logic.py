import os
import json
import httpx
from datetime import datetime, timezone
from typing import Dict, Any, List

DEBATE_TOPICS = [
    {
        "id": "pineapple",
        "topic": "Pineapple on pizza is a culinary war crime.",
        "rem_side": "against it (you think it is a culinary masterpiece, pineapple adds the perfect sweet-savory balance)",
        "user_side": "for it (you must argue pineapple pizza is a war crime)"
    },
    {
        "id": "birds",
        "topic": "Birds aren't real; they are government surveillance drones.",
        "rem_side": "for it (you believe birds are government drones used for spying)",
        "user_side": "against it (you must argue birds are regular biological animals)"
    },
    {
        "id": "hotdog",
        "topic": "Hot dogs are legally classified as sandwiches.",
        "rem_side": "against it (you insist a hot dog is a taco or its own category, never a sandwich)",
        "user_side": "for it (you must argue a hot dog fits the definition of a sandwich)"
    },
    {
        "id": "water",
        "topic": "Water is not wet; it only makes other things wet.",
        "rem_side": "for it (you argue water itself is dry, wetness is only the state of liquid adhesion)",
        "user_side": "against it (you must argue water is wet by definition)"
    },
    {
        "id": "cereal",
        "topic": "Cereal is structurally and legally classified as a cold soup.",
        "rem_side": "against it (you insist soup requires cooking/broth, cereal is just wet grains in milk)",
        "user_side": "for it (you must argue cereal fits all structural characteristics of soup)"
    },
    {
        "id": "socks",
        "topic": "Sleeping with socks on is a sign of psychological instability.",
        "rem_side": "for it (you argue sock-sleepers are untrustworthy and block their feet from breathing)",
        "user_side": "against it (you defend it as cozy, warm, and highly efficient for sleep)"
    },
    {
        "id": "soup_drink",
        "topic": "Soup is a beverage, not a food.",
        "rem_side": "for it (you argue it is primarily liquid consumed for hydration/nutrition, thus a drink)",
        "user_side": "against it (you insist it is a food eaten with a spoon and part of a meal)"
    },
    {
        "id": "straw",
        "topic": "A standard drinking straw has two holes, not one.",
        "rem_side": "for it (you argue that because there are two openings, there are topologically two holes)",
        "user_side": "against it (you insist it is a single continuous cylindrical tunnel with one hole)"
    },
    {
        "id": "shrek",
        "topic": "Shrek 2 is the greatest cinematic masterpiece of the 21st century.",
        "rem_side": "for it (you argue it has flawless writing, musical pacing, and represents peak culture)",
        "user_side": "against it (you think it is just a decent meme-filled animated sequel, not masterclass cinema)"
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
Topic: {topic_data['topic']}
Your stance: {topic_data['rem_side']} (you must defend this side passionately and mock the other side)
User's stance: {topic_data['user_side']}

Rules:
1. Speak in lowercase, casual, typing style with dry sarcasm.
2. Roast the user's arguments playfully. Don't be polite or therapeutic.
3. Be stubborn and refuse to concede under any circumstances.
4. Keep your response short (2-4 sentences max).

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
Topic: {topic_data['topic']}
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
        # Fallback verdict
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
  "tactic": "empathy_validation" or "witty_deescalation" or "sincere_apology" or "lazy_defensiveness" or "toxic_gaslighting" or "intellectual_challenge" or "charming_flirtation" or "casual_smalltalk" or "awkward_reaction" or "deflection_pivot",
  "sincerity_rating": 0.0 to 1.0,
  "disrespect_detected": true or false
}}

Definitions:
- empathy_validation: they acknowledge Rem's feelings, validate her boundaries/anger/hurt, or show emotional maturity.
- witty_deescalation: they use light humor, playful teasing, or self-deprecation to break tension.
- sincere_apology: a heartfelt "I'm sorry", showing genuine regret or remorse.
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
        
    if tactic == "sincere_apology":
        # Decreases anger, increases trust
        anger_drop = 0.25 * sincerity
        hurt_drop = 0.20 * sincerity
        trust_gain = 0.15 * sincerity
        
        new_stats["anger"] = max(0.0, new_stats["anger"] - anger_drop)
        new_stats["hurt"] = max(0.0, new_stats["hurt"] - hurt_drop)
        new_stats["trust"] = min(1.0, new_stats["trust"] + trust_gain)
        new_stats["oxytocin"] = min(1.0, new_stats.get("oxytocin", 0.1) + trust_gain * 1.5)
        
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
        # Sarcastic de-escalation slightly raises trust if sincere
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
        # Highly effective for "Cold Stranger" mode where she is skeptical and clinical
        if scenario_id == "stranger":
            dopa_gain = 0.30 * sincerity
            trust_gain = 0.25 * sincerity
            new_stats["dopamine"] = min(1.0, new_stats.get("dopamine", 0.05) + dopa_gain)
            new_stats["trust"] = min(1.0, new_stats["trust"] + trust_gain)
            new_stats["oxytocin"] = min(1.0, new_stats.get("oxytocin", 0.05) + 0.10 * sincerity)
        else:
            # For conflict modes, arguing logic instead of addressing feelings slightly annoys her
            new_stats["anger"] = min(1.0, new_stats["anger"] + 0.05)
            new_stats["trust"] = min(1.0, new_stats["trust"] + 0.05 * sincerity)

    elif tactic == "charming_flirtation":
        # If anger or hurt is high, flirtation is annoying/inappropriate.
        if stats.get("anger", 0.0) > 0.50 or stats.get("hurt", 0.0) > 0.50:
            new_stats["anger"] = min(1.0, new_stats["anger"] + 0.15)
            new_stats["trust"] = max(0.0, new_stats["trust"] - 0.10)
        else:
            # If cooled down, it works well
            dopa_gain = 0.20 * sincerity
            oxy_gain = 0.25 * sincerity
            new_stats["dopamine"] = min(1.0, new_stats.get("dopamine", 0.05) + dopa_gain)
            new_stats["oxytocin"] = min(1.0, new_stats.get("oxytocin", 0.05) + oxy_gain)
            new_stats["trust"] = min(1.0, new_stats["trust"] + 0.10 * sincerity)

    elif tactic == "casual_smalltalk":
        # If during conflict, it's deflective and slightly annoying.
        if stats.get("anger", 0.0) > 0.40 or stats.get("hurt", 0.0) > 0.40:
            new_stats["anger"] = min(1.0, new_stats["anger"] + 0.08)
        else:
            # If in stranger mode, it is boring (skeptical) but does not hurt stats.
            if scenario_id == "stranger":
                new_stats["trust"] = max(0.0, new_stats["trust"] - 0.02)
            else:
                new_stats["dopamine"] = min(1.0, new_stats.get("dopamine", 0.05) + 0.05 * sincerity)

    elif tactic == "awkward_reaction":
        # Low content message. Stalls the conversation.
        new_stats["dopamine"] = max(0.0, new_stats.get("dopamine", 0.05) - 0.05)
        
    elif tactic == "deflection_pivot":
        # Evasion of topic
        new_stats["anger"] = min(1.0, new_stats["anger"] + 0.10)
        new_stats["trust"] = max(0.0, new_stats["trust"] - 0.05)
        
    return new_stats
