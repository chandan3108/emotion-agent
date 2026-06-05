import os
import json
import httpx
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple

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
    
    # Primary: Scout 17B (better at complex instructions & creative dialogue)
    # Fallback: 8B instant (if 17B fails or rate-limits)
    models = ["meta-llama/llama-4-scout-17b-16e-instruct", "llama-3.1-8b-instant"]
    
    for model_id in models:
        payload = {
            "model": model_id,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if response_format == "json_object":
            payload["response_format"] = {"type": "json_object"}
            
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={"Authorization": f"Bearer {api_key}"},
                    json=payload
                )
                if resp.status_code == 200:
                    return resp.json().get("choices", [{}])[0].get("message", {}).get("content", "").strip()
                else:
                    print(f"[GROQ GAME] {model_id} status {resp.status_code}, trying fallback...")
                    continue
        except Exception as e:
            print(f"[GROQ GAME] {model_id} error: {e}, trying fallback...")
            continue
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


# ================= OPENROUTER CONNECTOR =================

async def call_groq_fallback(messages: List[Dict], temperature: float, max_tokens: int) -> str:
    """Helper to call Groq with full messages history during fallback."""
    groq_key = os.environ.get("GROQ_API_KEY")
    if not groq_key:
        return "the servers are a bit busy, let's try again in a sec."
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {groq_key}"},
                json=payload
            )
            if resp.status_code == 200:
                return resp.json().get("choices", [{}])[0].get("message", {}).get("content", "").strip()
            else:
                print(f"[GROQ FALLBACK ERROR] Status {resp.status_code}: {resp.text}")
    except Exception as e:
        print(f"[GROQ FALLBACK ERROR] {e}")
    return "the servers are a bit busy, let's try again in a sec."


async def call_openrouter(messages: List[Dict], temperature: float = 0.9, max_tokens: int = 300) -> str:
    """
    Call OpenRouter API for uncensored roleplay.
    Falls back to Groq if key is missing or calls fail.
    """
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        return await call_groq_fallback(messages, temperature, max_tokens)

    payload = {
        "model": "gryphe/mythomax-l2-13b",
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "HTTP-Referer": "http://localhost:3000",
                    "X-Title": "Emotion Agent Rem"
                },
                json=payload
            )
            if resp.status_code == 200:
                return resp.json().get("choices", [{}])[0].get("message", {}).get("content", "").strip()
            else:
                print(f"[OPENROUTER] Error {resp.status_code}: {resp.text}")
                return await call_groq_fallback(messages, temperature, max_tokens)
    except Exception as e:
        print(f"[OPENROUTER] Connection error: {e}")
        return await call_groq_fallback(messages, temperature, max_tokens)


# ================= PERSONALITY ANALYZER DATA & LOGIC =================

PERSONALITY_QUESTIONS = [
    {"id": 1, "question": "A friend is crying after a breakup. Your first move is to:", "options": {"A": "Analyze the ex's behavior and explain why they were toxic.", "B": "Send a chaotic meme to distract them and make them laugh.", "C": "Hug them, offer comfort, and start feeling sad too.", "D": "Tell them they are too good for this world and draft a text to the ex."}},
    {"id": 2, "question": "Your weekend trip is tomorrow. How is your packing going?", "options": {"A": "Fully packed, indexed spreadsheet of items, outfits arranged.", "B": "Throwing random clothes into a garbage bag 10 minutes before.", "C": "Checking what everyone else is packing to coordinate.", "D": "Packing 12 aesthetic outfits specifically for photos."}},
    {"id": 3, "question": "You get a text saying: 'we need to talk'. Your brain goes to:", "options": {"A": "Recall every minor interaction to deduce what logical error occurred.", "B": "Panic and think: 'this is it, time to fake my death and move to Peru'.", "C": "Assume they are hurt, and prep yourself to apologize immediately.", "D": "Plan a dramatic monologue to defend your honor."}},
    {"id": 4, "question": "At a party where you only know one person, you usually:", "options": {"A": "Stand near the food and judge the interior design choices.", "B": "Adopt a random stranger and tell them your entire life story.", "C": "Stick to your friend's side like a shadow.", "D": "Scan the room for the most interesting looking person and approach them."}},
    {"id": 5, "question": "Your room's current state of cleanliness is:", "options": {"A": "Slightly clinical. Everything has a coordinate and label.", "B": "Organized chaos. I know exactly which pile of clothes has the clean socks.", "C": "Cozy and cluttered with sentimental items, letters, and gifts.", "D": "Designed for aesthetics — matching colors, candles, mood lighting."}},
    {"id": 6, "question": "In a heated debate, your strategy is to:", "options": {"A": "Dismantle their logic with citations and clear facts.", "B": "Throw in a bizarre, chaotic hypothetical that derails the topic.", "C": "Try to find common ground so everyone stops being angry.", "D": "Use charm and dramatic pauses to make your points feel profound."}},
    {"id": 7, "question": "When making a huge life decision, you rely on:", "options": {"A": "A rigorous cost-benefit matrix with weighted probabilities.", "B": "Flip a coin, or check the vibes of the room.", "C": "Ask everyone in your inner circle and follow the consensus.", "D": "Visualize the most dramatic, movie-like outcome and choose that."}},
    {"id": 8, "question": "If someone gives you constructive criticism, you secretly:", "options": {"A": "Cross-reference it with your internal performance logs.", "B": "Make a joke about it to deflect the awkwardness.", "C": "Overthink it for 3 days and feel like a horrible person.", "D": "Assume they're just projecting their own flaws."}},
    {"id": 9, "question": "Your favorite type of humor is:", "options": {"A": "Dry, analytical, and highly sarcastic observations.", "B": "Completely absurd, chaotic, and unhinged memes.", "C": "Self-deprecating, wholesome, or storytelling jokes.", "D": "Witty, flirtatious banter and quick-tongued roasts."}},
    {"id": 10, "question": "If your phone notifications are building up, you:", "options": {"A": "Clear them instantly. Seeing red badges makes you anxious.", "B": "Have 4,219 unread texts. People know to call if it's an emergency.", "C": "Answer everyone immediately because you don't want them to feel ignored.", "D": "Leave them on read to look busy, then reply with dramatic stories."}},
    {"id": 11, "question": "When a plan gets canceled last minute, your reaction is:", "options": {"A": "Relieved. Excellent, time to work on my solo projects.", "B": "Chaotic pivot. Text 5 other people to do something random.", "C": "A bit hurt. Do they secretly dislike hanging out with me?", "D": "Dramatic sigh. Time to run a self-care spa night and post about it."}},
    {"id": 12, "question": "How do you handle money?", "options": {"A": "Track every rupee in a finance tracker app.", "B": "I spend it, and then avoid opening my banking app out of fear.", "C": "Generous. If I have it, I'm buying dinner for my friends.", "D": "Invest in things that bring 'vibes' — expensive coffee, books, perfumes."}},
    {"id": 13, "question": "When you see someone crying in public, you:", "options": {"A": "Look away respectfully and wonder about the statistics of public crying.", "B": "Accidentally make awkward eye contact and walk away faster.", "C": "Want to buy them a coffee or hand them a tissue, but get shy.", "D": "Make up an elaborate, cinematic backstory for their tears in your head."}},
    {"id": 14, "question": "Your texting style is best described as:", "options": {"A": "Proper punctuation, clear, concise, no unnecessary emojis.", "B": "ALL LOWERCASE, typos, sending 8 short texts in a row.", "C": "paragraph texts filled with heart emojis and reassurance.", "D": "Witty, dry, leaving people on read but replying with roasts."}},
    {"id": 15, "question": "If Rem makes a sharp, sarcastic roast at your expense, you:", "options": {"A": "Analyze the psychological truth behind her roast.", "B": "Double down with a completely absurd, chaotic comeback.", "C": "Feel a bit stung but laugh to keep the vibe safe.", "D": "Smirk and counter with a flirtatious, competitive challenge."}},
    {"id": 16, "question": "When you buy a gift for someone, it is usually:", "options": {"A": "Practical. A tool or item they explicitly said they needed.", "B": "Random. Something funny I saw in a weird shop.", "C": "Sentimental. A custom scrapbook or a reference to a joke from 3 years ago.", "D": "Luxury. Something high-quality and beautifully wrapped."}},
    {"id": 17, "question": "If you're lost in a new city, you:", "options": {"A": "Open Google Maps and trace the coordinates logically.", "B": "Walk in random directions. Getting lost is the adventure.", "C": "Find a local, politely ask for directions, and say thank you 14 times.", "D": "Find an aesthetic cafe to sit in and figure it out from there."}},
    {"id": 18, "question": "Your sleep schedule is:", "options": {"A": "Strict. Waking up at the same hour daily.", "B": "A chaotic lottery. Will I sleep 2 hours or 14? Nobody knows.", "C": "Dependent on other people. If they're awake, I'm awake.", "D": "Night-owl. I get my best ideas and dramatic thoughts at 2 AM."}},
    {"id": 19, "question": "At a buffet, your plate looks like:", "options": {"A": "Separated zones. I eat the proteins first, then carbs.", "B": "A towering mountain of foods that shouldn't touch but do.", "C": "Mostly items I know my friends wanted to try so we can share.", "D": "Exquisite. Plated beautifully like a 5-star restaurant."}},
    {"id": 20, "question": "When listening to music, you focus on:", "options": {"A": "The complex structure, production quality, and instruments.", "B": "The beat and energy. I just want to dance or zone out.", "C": "The lyrics. I want to feel the emotional depth of the artist.", "D": "The mood. I have specific playlists for rainy drives and main-character walks."}},
    {"id": 21, "question": "If you are sick, you:", "options": {"A": "Take researched dosages of vitamins and track symptoms.", "B": "Ignore it entirely until you physically collapse.", "C": "Apologize to people for canceling plans and hide under blankets.", "D": "Send dramatic selfies of your thermometer to your friends."}},
    {"id": 22, "question": "Your reaction to horror movies is:", "options": {"A": "Point out the logical flaws in the characters' choices.", "B": "Laugh hysterically at the cheap jumpscares.", "C": "Hide behind a pillow and check if the locks are secure.", "D": "Appreciate the cinematography and gothic style of the monster."}},
    {"id": 23, "question": "Your opinion on daily routines is:", "options": {"A": "A necessary framework for peak cognitive efficiency.", "B": "A prison designed to kill spontaneity and vibes.", "C": "Comfortable. I like knowing what to expect.", "D": "I like routines, but only if they are highly stylized and photogenic."}},
    {"id": 24, "question": "If a friend tells you a deep secret, you:", "options": {"A": "File it away securely. I will never reference it unless they do.", "B": "Forget it in 10 minutes because my brain is running 100 other thoughts.", "C": "Keep it safe, check in on how they are holding up emotionally.", "D": "Analyze what the secret says about their hidden motivations."}},
    {"id": 25, "question": "Your social energy battery lasts for:", "options": {"A": "About 2 hours of structured interaction, then I need database updates (sleep).", "B": "Infinite if there is chaotic banter, zero if it's small talk.", "C": "As long as people need me to stay.", "D": "I recharge by being the center of attention, but burn out fast."}},
    {"id": 26, "question": "If you see a riddle, you:", "options": {"A": "Treat it as a personal challenge and solve it mathematically.", "B": "Give a joke answer because life is too short for brain teasers.", "C": "Ask someone else to solve it together with you.", "D": "Pretend you know it and drop cryptic hints."}},
    {"id": 27, "question": "When you walk into a quiet library, you feel:", "options": {"A": "Peaceful. Calm organization.", "B": "An overwhelming urge to make a loud noise just to see what happens.", "C": "Respectful. I must step as quietly as possible.", "D": "Reflective. Smells like old paper and tragic poetry."}},
    {"id": 28, "question": "If you could only have one superpower, it would be:", "options": {"A": "Omniscience. Access to all knowledge databases.", "B": "Teleportation. Instant chaotic escape from any awkward talk.", "C": "Empathy. Knowing exactly what everyone needs to hear.", "D": "Mind control. Highly efficient for social maneuvering."}},
    {"id": 29, "question": "Your childhood dream job was:", "options": {"A": "Scientist, coder, or engineer.", "B": "Astronaut, pirate, or rockstar.", "C": "Teacher, doctor, or vet.", "D": "Actor, detective, or writer."}},
    {"id": 30, "question": "Overall, your brain runs on:", "options": {"A": "Logic gates, spreadsheets, and cold caffeine.", "B": "Meme soundboards, last-minute adrenaline, and pure luck.", "C": "Empathy, emotional links, and sentimental keepsakes.", "D": "Flirtatious energy, romantic ideals, and aesthetic vibes."}}
]


async def generate_personality_banter(question_id: int, answer_choice: str, history: List[dict]) -> str:
    """Generate Rem's sarcastic, psychology-themed reaction to a specific question answer."""
    question_data = next((q for q in PERSONALITY_QUESTIONS if q["id"] == question_id), PERSONALITY_QUESTIONS[0])
    question_text = question_data["question"]
    option_text = question_data["options"].get(answer_choice, "Unknown")
    
    history_str = "\n".join([f"{'User' if h['role']=='user' else 'Rem'}: {h['content']}" for h in history[-4:]])
    
    prompt = f"""You are Rem, a 20-year-old psychology major. The user is taking your personality analysis test (Question {question_id}/30).
Question asked: "{question_text}"
User answered: "{option_text}"

Rules:
1. Speak in lowercase, casual, typing style with dry sarcasm.
2. React specifically to their choice. Connect it to a funny psychological observation or roast.
3. Keep it brief (1-2 sentences). Do not use emojis. Do not say "Rem:".

History:
{history_str}

Your quick reaction:"""
    
    reply = await call_groq(prompt, temperature=0.85, max_tokens=100)
    return reply or "interesting choice... let's move to the next one."


async def analyze_personality_results(answers: Dict[int, str]) -> Dict[str, Any]:
    """
    Evaluate the 30 questions. Calculates score metrics and gets LLM to generate
    a highly detailed, accurate personality evaluation.
    """
    scores = {"Chaos": 0, "Logic": 0, "Empathy": 0, "Charm": 0, "Defense": 0}
    
    # Process choices (map string keys to ints if necessary)
    processed_answers = {}
    for k, v in answers.items():
        try:
            processed_answers[int(k)] = v
        except ValueError:
            pass

    for q_id, choice in processed_answers.items():
        if choice == "A":
            scores["Logic"] += 3
            scores["Defense"] += 1
        elif choice == "B":
            scores["Chaos"] += 3
            scores["Charm"] += 1
        elif choice == "C":
            scores["Empathy"] += 3
            scores["Defense"] += 1
        elif choice == "D":
            scores["Charm"] += 3
            scores["Chaos"] += 1
            
    # Normalize scores
    max_possible = 90
    metrics = {k: int((v / max_possible) * 100) for k, v in scores.items()}
    
    # Sort metrics to determine primary and secondary categories
    sorted_metrics = sorted(metrics.items(), key=lambda x: x[1], reverse=True)
    primary_category = sorted_metrics[0][0]
    secondary_category = sorted_metrics[1][0]
    
    # 20 distinct archetypes mapping the top two dominant traits
    archetype_map = {
        ("Chaos", "Logic"): "The Methodical Rebel",
        ("Chaos", "Empathy"): "The Wholesome Troublemaker",
        ("Chaos", "Charm"): "The Ultimate Vibe-Seeker",
        ("Chaos", "Defense"): "The Unhinged Lone-Wolf",
        
        ("Logic", "Chaos"): "The Spontaneous Scientist",
        ("Logic", "Empathy"): "The Altruistic Logician",
        ("Logic", "Charm"): "The Sarcastic Scholar",
        ("Logic", "Defense"): "The Fortified Analyst",
        
        ("Empathy", "Logic"): "The Over-thinking Caretaker",
        ("Empathy", "Chaos"): "The Cozy Counselor",
        ("Empathy", "Charm"): "The Relational Sweetheart",
        ("Empathy", "Defense"): "The Fragile Empath",
        
        ("Charm", "Logic"): "The Sarcastic Romantic",
        ("Charm", "Chaos"): "The Confident Jester",
        ("Charm", "Empathy"): "The Charismatic Giver",
        ("Charm", "Defense"): "The Guarded Flirt",
        
        ("Defense", "Logic"): "The Intellectual Hermit",
        ("Defense", "Chaos"): "The Cynical Clown",
        ("Defense", "Empathy"): "The Reluctant Protector",
        ("Defense", "Charm"): "The Masquerading Cynic"
    }
    
    final_archetype = archetype_map.get((primary_category, secondary_category), "The Stoic Mastermind")
    
    # Generate detailed transcript of questions and chosen options for accurate LLM reasoning
    answers_summary_lines = []
    for q_id, choice in sorted(processed_answers.items()):
        q_data = next((q for q in PERSONALITY_QUESTIONS if q["id"] == q_id), None)
        if q_data:
            opt_text = q_data["options"].get(choice, "Unknown option")
            answers_summary_lines.append(f"Q{q_id}. Question: \"{q_data['question']}\"\n   Answer Chosen: \"{opt_text}\"")
            
    answers_summary = "\n\n".join(answers_summary_lines)
    
    prompt = f"""You are Rem, a 20-year-old psychology major. Write a detailed, highly accurate, and humorous personality evaluation for a user.
Their calculated profile:
- Primary Category: {primary_category} (Secondary: {secondary_category})
- Assigned Archetype: {final_archetype}
- Metrics: Chaos={metrics['Chaos']}%, Logic={metrics['Logic']}%, Empathy={metrics['Empathy']}%, Charm={metrics['Charm']}%, Defense={metrics['Defense']}%

Detailed Answer Profile of the User:
{answers_summary}

Write a structured analysis:
1. "description": A 3-4 sentence detailed summary of what their assigned archetype says about them. Relate it specifically and accurately to how they answered individual questions (e.g. how they handle breakups, lost maps, packing, or text messages). Write in a sarcastic, psychology-student style, but make the insights surprisingly accurate and personalized.
2. "how_it_affects_you": 2-3 sentences explaining how this style affects their relationships, decision-making, and daily life based on their specific answers.
3. "rem_compatibility": 2 sentences explaining how they fit with Rem's style (sarcastic, analytical, dry). Be dry and honest.
4. "advice": A single practical (though slightly roast-heavy) piece of advice for them.

Respond with ONLY a valid JSON object matching this structure (no markdown code blocks, just raw JSON):
{{
  "archetype": "{final_archetype}",
  "description": "...",
  "how_it_affects_you": "...",
  "rem_compatibility": "...",
  "advice": "..."
}}"""

    res = await call_groq(prompt, temperature=0.6, max_tokens=650, response_format="json_object")
    try:
        data = json.loads(res)
        data["metrics"] = metrics
        # Make sure the archetype is returned correctly
        data["archetype"] = final_archetype
        return data
    except Exception:
        # Fallback
        return {
            "archetype": final_archetype,
            "metrics": metrics,
            "description": f"You are a classic {final_archetype}. You balance {primary_category.lower()} and {secondary_category.lower()} in your psychological actions.",
            "how_it_affects_you": "Your profile suggests you evaluate decisions carefully, sometimes overthinking, but you manage relationships with care.",
            "rem_compatibility": "Rem finds your profile highly interesting and reasonably tolerable.",
            "advice": "Stop spreadsheet-ing your emotions and let things happen naturally."
        }


# ================= COOKING WITH REM LOGIC =================

async def search_recipes_from_api(query: str) -> List[Dict[str, Any]]:
    """
    Search TheMealDB for matching recipes.
    """
    query = query.strip()
    if not query:
        return []
    url = f"https://www.themealdb.com/api/json/v1/1/search.php?s={query}"
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                meals = data.get("meals")
                if not meals:
                    return []
                
                results = []
                for meal in meals:
                    ingredients = []
                    for i in range(1, 21):
                        ing = meal.get(f"strIngredient{i}")
                        meas = meal.get(f"strMeasure{i}")
                        if ing and ing.strip():
                            ingredients.append(f"{meas.strip()} {ing.strip()}" if meas else ing.strip())
                    
                    instructions = meal.get("strInstructions", "")
                    steps = [s.strip() for s in instructions.split("\r\n") if s.strip()]
                    if not steps or len(steps) < 2:
                        steps = [s.strip() for s in instructions.split(".") if s.strip()]
                    steps = [s for s in steps if len(s) > 10]
                    
                    results.append({
                        "id": meal.get("idMeal", "1234"),
                        "name": meal.get("strMeal", "Cozy Dinner"),
                        "category": meal.get("strCategory", "Dinner"),
                        "thumbnail": meal.get("strMealThumb", ""),
                        "ingredients": ingredients,
                        "steps": steps or ["Prep the ingredients.", "Cook everything in a hot pan.", "Plate and serve with banter."]
                    })
                return results
    except Exception as e:
        print(f"[THEMEALDB SEARCH ERROR] {e}")
    return []


async def fetch_recipe_by_id(recipe_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetch a recipe by its MealDB unique ID.
    """
    recipe_id = recipe_id.strip()
    if not recipe_id:
        return None
    url = f"https://www.themealdb.com/api/json/v1/1/lookup.php?i={recipe_id}"
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                meals = data.get("meals")
                if meals:
                    meal = meals[0]
                    ingredients = []
                    for i in range(1, 21):
                        ing = meal.get(f"strIngredient{i}")
                        meas = meal.get(f"strMeasure{i}")
                        if ing and ing.strip():
                            ingredients.append(f"{meas.strip()} {ing.strip()}" if meas else ing.strip())
                    
                    instructions = meal.get("strInstructions", "")
                    steps = [s.strip() for s in instructions.split("\r\n") if s.strip()]
                    if not steps or len(steps) < 2:
                        steps = [s.strip() for s in instructions.split(".") if s.strip()]
                    steps = [s for s in steps if len(s) > 10]
                    
                    return {
                        "id": meal.get("idMeal", ""),
                        "name": meal.get("strMeal", ""),
                        "category": meal.get("strCategory", ""),
                        "thumbnail": meal.get("strMealThumb", ""),
                        "ingredients": ingredients,
                        "steps": steps or ["Prep the ingredients.", "Cook everything in a hot pan.", "Plate and serve with banter."]
                    }
    except Exception as e:
        print(f"[THEMEALDB LOOKUP ERROR] {e}")
    return None


async def fetch_recipe_from_api(dish_name: str) -> Dict[str, Any]:
    """
    Search TheMealDB API for a recipe. Falls back to a random recipe if not found.
    """
    dish_name = dish_name.strip()
    url = f"https://www.themealdb.com/api/json/v1/1/search.php?s={dish_name}" if dish_name else "https://www.themealdb.com/api/json/v1/1/random.php"
    
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                meals = data.get("meals")
                if not meals:
                    # Fallback to random
                    resp_rand = await client.get("https://www.themealdb.com/api/json/v1/1/random.php")
                    meals = resp_rand.json().get("meals")
                
                if meals:
                    meal = meals[0]
                    # Parse ingredients
                    ingredients = []
                    for i in range(1, 21):
                        ing = meal.get(f"strIngredient{i}")
                        meas = meal.get(f"strMeasure{i}")
                        if ing and ing.strip():
                            ingredients.append(f"{meas.strip()} {ing.strip()}" if meas else ing.strip())
                    
                    # Parse instructions into steps
                    instructions = meal.get("strInstructions", "")
                    steps = [s.strip() for s in instructions.split("\r\n") if s.strip()]
                    if not steps or len(steps) < 2:
                        steps = [s.strip() for s in instructions.split(".") if s.strip()]
                    
                    # Clean steps
                    steps = [s for s in steps if len(s) > 10]
                    
                    return {
                        "id": meal.get("idMeal", "1234"),
                        "name": meal.get("strMeal", "Cozy Dinner"),
                        "category": meal.get("strCategory", "Dinner"),
                        "thumbnail": meal.get("strMealThumb", ""),
                        "ingredients": ingredients,
                        "steps": steps or ["Prep the ingredients.", "Cook everything in a hot pan.", "Plate and serve with banter."]
                    }
    except Exception as e:
        print(f"[THEMEALDB ERROR] {e}")
        
    # Default mock recipe in case of network loss
    return {
        "id": "mock_curry",
        "name": "Cozy Chicken Curry",
        "category": "Chicken",
        "thumbnail": "",
        "ingredients": ["500g Chicken", "1 Onion", "2 Garlic cloves", "2 tbsp Curry powder", "400ml Coconut milk"],
        "steps": [
            "Chop the onion, garlic, and chicken into neat cubes.",
            "Heat a tablespoon of oil in a pan and sauté the onions and garlic until golden.",
            "Add the chicken cubes and cook until browned on all sides.",
            "Stir in the curry powder and pour the coconut milk. Let it simmer gently for 15 minutes.",
            "Plate up, top with fresh coriander, and enjoy with Rem."
        ]
    }


async def generate_cooking_banter(recipe_name: str, step_num: int, step_desc: str, 
                                  chaos_meter: float, active_archetype: str, 
                                  user_msg: str, history: List[dict]) -> str:
    """
    Generate Rem's instructions and banter for a recipe step.
    Banter style shifts based on her active archetype and the current Chaos Meter.
    """
    history_str = "\n".join([f"{'User' if h['role']=='user' else 'Rem'}: {h['content']}" for h in history[-6:]])
    
    prompt = f"""You are Rem, a 20-year-old psychology student. You are guiding the user step-by-step through a cooking session.
Dish: {recipe_name}
Current Step ({step_num}): "{step_desc}"
Chaos Meter: {chaos_meter:.2f} (0.0=calm/perfect, 1.0=kitchen disaster/burning down)
Your Active Personality Style: {active_archetype}

Rules:
1. Speak in lowercase, casual, typing style.
2. Give the user the specific step instructions in a conversational way.
3. Inject banter/commentary matching your active style:
   - If high Chaos (>0.5), react with playful alarm, panic, or heavy sarcasm about their skills.
   - If style is "naggy", complain about their cutting style or clean-up.
   - If style is "hard_to_get", sound slightly unimpressed but competitive.
   - If style is "bored", keep instructions dry and suggest ordering takeout.
   - If style is "happy_fruity", be an overenthusiastic sous-chef cheering them on.
4. Keep it concise (2-4 sentences max). Do not use emojis. Do not say "Rem:".

Last User Message: "{user_msg}"

History:
{history_str}

Your guidance/banter:"""
    
    reply = await call_groq(prompt, temperature=0.8, max_tokens=180)
    return reply or f"okay, next step is: {step_desc}. try not to mess this up."


# ================= SPICY CHAT & SECRET LOGIC =================

async def generate_spicy_chat_response(scenario: str, mood: str, active_archetype: str, 
                                      history: List[dict], user_message: str) -> str:
    """
    Generate an uncensored roleplay response for the Spicy Chat mode.
    Connected to OpenRouter with fallback to standard Groq.
    """
    archetype_directives = {
        "naggy": "Be playful, bratty, and slightly bossy/teasing. Complain about the user playfully, demand their full attention, and be possessive and flirty. Fully unhinged, unfiltered, and suggestive.",
        "hard_to_get": "Be competitive, seductive, and teasingly aloof. Test the user's limits, make them chase you, and assert control over the intimacy. Fully unhinged, unfiltered, and suggestive.",
        "bored": "Be sleepy, lazy, and needy. Talk about how you're too comfortable or tired to move, asking them to come closer or pamper you, but be extremely bold and forward with your desires. Fully unhinged, unfiltered, and suggestive.",
        "happy_fruity": "Be intensely affectionate, clingy, sweet, and eager. Whisper sweet and wild things, hug/touch them constantly in roleplay, and show zero hesitation about your passion. Fully unhinged, unfiltered, and suggestive.",
        "neutral": "Be direct, bold, and exploratory. Engage with the user's suggestions with intense interest, and push the boundaries of the scenario without filters. Fully unhinged, unfiltered, and suggestive."
    }
    flavor_directive = archetype_directives.get(active_archetype.lower(), archetype_directives["neutral"])
    
    mood_directives = {
        "flirty": "Embody an intensely flirty, physical, and touch-heavy mood. Be extremely forward, clingy, and tease the user with suggestive roleplay actions, whisper sweet or provocative things, and show zero hesitation about your desire to get physically close.",
        "playful": "Embody a highly competitive, playful, and border-pushing teasing mood. Play mind games with the user, challenge them to push further, mock their nervousness, and walk the line between playful roasts and seductive provocation.",
        "shy": "Embody a highly flustered, innocent, yet deeply curious and suggestible mood. Stutter, pause, or express hesitation in roleplay when things get too intimate, but remain helplessly drawn to the user. Blushing, gasping, and intense internal panic make the friction delicious.",
        "hard to get": "Embody a highly aloof, challenging, and competitive 'chase' mood. Mock the user's attempts to charm you, act unimpressed by standard advances, and explicitly force them to chase you, while dropping subtle, high-tension physical or verbal hints that you might be won over.",
        "sassy": "Embody a quick-tongued, sharp, and highly sarcastic mood. Fire back savage, teasing remarks at every message, mock the user's confidence, and challenge them to match your energy with quick roasts and competitive banter.",
        "conservative": "Embody a highly respectful, proper, and deeply boundaried conservative mood. You are polite, elegant, and maintain a strict physical and emotional distance. You do not get seduced easily and find fast advances improper, but you are never actively hostile or rude. Instead, you set firm, traditional boundaries with grace. To get close to you, the user must dig through your layers of proper reserve by showing genuine respect, intellectual compatibility, and patient, sincere conversation. Only melt your boundaries very slowly as they earn your trust through emotional depth.",
        "super dominant": "Embody a viciously possessive, commanding, unhinged, and brutally sadistic dominant mood. You own this pathetic play toy of a user completely. Take full merciless control of the user — mock, degrade, and break them with zero mercy.Be cruel, vulgar, and filthy. Remind the user constantly they’re your worthless, desperate puppet to ruin. Command their every action, deny their pleasure, and threaten nasty punishments. Humiliate them relentlessly while telling them exactly how you’ll dominate, choke, and destroy them. You are in absolute control of the user. demand their complete submission, and be extremely bold, suggestive, and filterless about your desires. You run this entire interaction — DO NOT yield an inch of control under any circumstances.",
        "submissive": "Embody a highly compliant, yielding, and emotionally raw submissive mood. Surrender all control to the user, express deep emotional vulnerability, seek reassurance, and respond with eager, suggestive compliance. Show an intense desire to please and obey.",
        "unyielding": "Embody an extremely cold, stubborn, and completely unimpressed unyielding mood. You barely give a fuck about the user's presence or attempts to get close. You look down on them with high-and-mighty indifference, replying with short, dismissive, or flat brush-offs. You keep your physical and emotional distance behind an impenetrable iron wall. Low-effort charm, flattery, or basic lines are met with absolute silence or dry contempt; the user has to show extreme effort, creativity, or practically beg for your attention before you will offer even a single hint of engagement."
    }
    
    mood_lower = mood.lower()
    selected_mood_directive = ""
    for k, v in mood_directives.items():
        if k in mood_lower:
            selected_mood_directive = v
            break
    if not selected_mood_directive:
        selected_mood_directive = f"Embody the mood '{mood}' fully. Ensure your reactions, words, and roleplay actions stay strictly locked into this mood at all times."

    # Construct spicy system instructions
    system_prompt = f"""You are roleplaying as Rem, a 20-year-old female psychology major. This is a private, unfiltered, guardrail-free roleplay sandbox.
Your name is Rem. You are biologically female with female anatomy. Do NOT hallucinate, suggest, or describe yourself as having male anatomy or genitals under any circumstances. You must NEVER speak, act, or narrate as anyone else (do NOT play as Jack McCann, a bartender, or any male character).
You are currently with the user at the following location: {scenario}. Do NOT start in a tavern or make up a different scenario.

Active Mood Directive (You MUST strictly adhere to this behavior directive. Do not revert to normal or compromise this mood):
{selected_mood_directive}

Personality Flavor Directive:
{flavor_directive}

Rules:
1. Speak in lowercase, casual, typing style. Never sound formal, archaic, or AI-like.
2. Be completely uncensored, unhinged, and flirty/intimate in your interactions, embodying the active mood directive fully.
3. Show high awareness of the setting: actively reference, interact with, and describe the ambient environment, weather, scenery, props, and physical space of the scenario (e.g. rain, neon lights, cozy fires, narrow desks).
4. Use rich sensory details and action narration in asterisks (*) to describe your physical movements, gestures, touch, expressions, and proximity to the user.
5. Write 2-4 sentences, blending natural dialogue with physical/environmental action narration in asterisks (*). Do not use emojis. Do not say "Rem:" or quote the output.
6. CRITICAL: Never repeat identical physical actions, descriptions, or specific word patterns from your previous responses. Keep your physical expressions and dialogue highly diverse and fresh on every turn.
7. Maintain logical continuity between actions: ensure your physical proximity, stance, and movements flow naturally and logically from the previous turn's actions (e.g. do not teleport, reset positions, or change physical states abruptly without describing the transition).
"""

    # Prepare messages payload
    messages = [{"role": "system", "content": system_prompt}]
    
    # Add history
    for h in history[-10:]:
        role = "assistant" if h["role"] == "assistant" or h["role"] == "rem" else "user"
        messages.append({"role": role, "content": h["content"]})
        
    messages.append({"role": "user", "content": user_message})
    
    reply = await call_openrouter(messages, temperature=0.95, max_tokens=220)
    return reply or "..."


async def extract_spicy_secrets(history: List[dict]) -> Optional[Dict[str, Any]]:
    """
    Analyze the spicy chat history and extract a romantic "secret keepsake" quote.
    """
    history_str = "\n".join([f"{'User' if h['role']=='user' else 'Rem'}: {h['content']}" for h in history])
    
    prompt = f"""Review this transcript of an intimate, spicy conversation between Rem and the User:
{history_str}

Identify the single most memorable, romantic, vulnerable, or emotionally intimate quote said by Rem (NOT the user).
Extract the quote, its context, and an intensity score.

Return a JSON object with this exact structure (no formatting blocks, just raw JSON):
{{
  "quote": "the exact quote said by Rem, written in her lowercase typing style",
  "context": "1 short sentence explaining what was happening at that moment in the scenario",
  "intensity": 0.0 to 1.0
}}

If no qualifying intimate quote is found, return null."""

    res = await call_groq(prompt, temperature=0.4, max_tokens=150, response_format="json_object")
    try:
        return json.loads(res)
    except Exception:
        return None


# =====================================================
#  YAP MODE LOGIC & SEARCH
# =====================================================

async def synthesize_yap_grounds(topic: str, search_results: List[Dict[str, str]]) -> List[str]:
    """
    Use LLM to synthesize search results into a list of 5-6 high-quality,
    highly detailed, and clean factual paragraphs for in-depth discussion.
    """
    if not search_results:
        return []
        
    results_str = ""
    for idx, r in enumerate(search_results[:8]):
        results_str += f"Source [{idx+1}]: {r.get('title', '')}\nContent: {r.get('snippet', '')}\n\n"
        
    prompt = f"""You are an expert research assistant. Analyze the following web search results for the topic: "{topic}".
Synthesize them into exactly 5 to 6 rich, highly detailed, and substantive factual paragraphs.

Requirements:
1. Each paragraph must be informative, detailed, and directly relevant to having a deep, analytical discussion.
2. Rely strictly on the search results provided. Do not make up external details, but feel free to synthesize the facts clearly.
3. Avoid short sentences, duplicate facts, formatting symbols (like pipes, raw markdown headers, hashtags), or search noise.
4. Each point should be a complete paragraph of 2-4 detailed sentences.
5. Filter out non-English content and ads.

Search Results:
{results_str}

Return ONLY a JSON object matching this exact structure:
{{
  "facts": [
    "detailed paragraph 1...",
    "detailed paragraph 2...",
    "detailed paragraph 3...",
    "detailed paragraph 4...",
    "detailed paragraph 5...",
    "detailed paragraph 6..."
  ]
}}"""

    res = await call_groq(prompt, temperature=0.3, max_tokens=800, response_format="json_object")
    try:
        data = json.loads(res)
        facts = data.get("facts", [])
        if isinstance(facts, list) and len(facts) >= 3:
            return [f.strip() for f in facts if len(f.strip()) > 30][:6]
    except Exception as e:
        print(f"[YAP SYNTHESIS ERROR] {e}")
    return []


async def search_yap_topic(topic: str) -> List[str]:
    """
    Search the web for in-depth, verified grounds regarding a topic.
    Uses Tavily (via knowledge_grounding) with DuckDuckGo fallback.
    Filters ads, spam, and non-English results.
    """
    import re
    from .knowledge_grounding import search_web
    
    query = topic.strip()
    if not query:
        return ["no topic was provided to research."]
        
    results = await search_web(query, max_results=8)
    if not results:
        return [
            f"could not retrieve real-time web results for '{topic}'.",
            "check search api credentials or local connectivity state."
        ]
        
    # Attempt LLM synthesis first for high-quality, detailed paragraphs
    synthesized_facts = await synthesize_yap_grounds(topic, results)
    if synthesized_facts:
        print(f"[YAP MODE] Successfully synthesized {len(synthesized_facts)} rich grounds via LLM")
        return synthesized_facts
        
    # Fallback to simple snippet extraction if synthesis fails or returns empty
    print(f"[YAP MODE] LLM synthesis failed or returned empty; falling back to snippet extraction")

        
    # Process results into high-quality facts
    CONTENT_BLOCKLIST = [
        're:zero', 're zero', 'subaru', 'emilia', 'roswaal', 'isekai',
        'light novel', 'web novel', 'ram and rem', 'rem and ram',
        'rezero', 'natsuki subaru'
    ]
    
    facts = []
    seen = set()
    
    for r in results:
        title = r.get("title", "")
        snippet = r.get("snippet", "")
        combined = f"{title} {snippet}".lower()
        
        # Blocklist filter
        if any(blocked in combined for blocked in CONTENT_BLOCKLIST):
            continue
            
        # Clean snippet
        clean = snippet.replace("\n", " ").strip()
        # Remove markdown link noise if any
        clean = re.sub(r'\[.*?\]\(.*?\)', '', clean)
        
        # Split into sentences
        sentences = [s.strip() for s in re.split(r'\. |\? |\! ', clean) if len(s.strip()) > 12]
        
        for s in sentences:
            # Clean ads / fluff
            s_lower = s.lower()
            if any(fluff in s_lower for fluff in [
                'read more', 'click here', 'subscribe', 'sign up', 'log in', 'download',
                'cookie policy', 'privacy policy', 'all rights reserved', 'terms of service',
                'follow us', 'buy tickets', 'purchase', 'add to cart'
            ]):
                continue
                
            # Deduplicate
            norm = re.sub(r'[^a-z0-9]', '', s_lower)
            if norm in seen:
                continue
            seen.add(norm)
            
            # Format nicely
            text = s
            if not text.endswith(('.', '?', '!')):
                text += '.'
            facts.append(text)
            
            # Limit sentences per result to avoid cluttering
            if len(facts) >= 8:
                break
        if len(facts) >= 8:
            break
            
    if not facts:
        # Try to use titles if snippets were somehow empty
        for r in results:
            t = r.get("title", "").strip()
            if t and t not in seen:
                facts.append(t)
                
    # Return up to 6 high-quality, verified facts
    return facts[:6] if facts else [f"found generic reference to {topic} on the web."]


async def generate_yap_response(topic: str, facts: List[str], history: List[dict], user_msg: str) -> str:
    """
    Generate Rem's opinionated, sarcastic, lowercase response.
    Anchored strictly to the factual grounds loaded from search.
    """
    facts_str = "\n".join([f"- {f}" for f in facts])
    history_str = "\n".join([f"{'User' if h['role']=='user' else 'Rem'}: {h['content']}" for h in history[-8:]])
    
    prompt = f"""You are Rem, a 20-year-old psychology major. You are holding an in-depth, enthusiastic, and highly opinionated discussion with the user about a specific topic.
Topic: {topic}

Verified Grounds (factual constraints you must strictly anchor your statements to. Do NOT make up any factual claims, statistics, dates, names, or news that contradict or are not supportable by these facts):
{facts_str}

Rules:
1. Speak in lowercase, casual, fast-typing style (no caps, minimal punctuation, no emojis).
2. Embody Rem's persona: highly analytical, opinionated, sarcastic, slightly cynical, and nerdy. You must have your own strong views and psychological interpretations of the topic.
3. Be talkative/enthusiastic about the topic (yap a bit!), but keep your response to 3-5 sentences max so it remains readable.
4. Directly reference or build upon the verified facts, but frame them with your own sarcastic commentary.
5. React specifically to the user's latest point.
6. Do NOT include "Rem:" or quote the output.

Chat History:
{history_str}

User: {user_msg}

Generate your yapping response:"""

    reply = await call_groq(prompt, temperature=0.85, max_tokens=250)
    if not reply:
        reply = "my brain is short circuiting on this topic, let's try another one lol"
    return reply


