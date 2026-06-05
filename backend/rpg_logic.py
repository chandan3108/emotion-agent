import os
import json
import random
from typing import Dict, Any, List, Optional
from .games_logic import call_groq

SCENARIOS_FILE = os.path.join(os.path.dirname(__file__), "rpg_scenarios.json")

def load_scenarios() -> List[dict]:
    if not os.path.exists(SCENARIOS_FILE):
        return []
    try:
        with open(SCENARIOS_FILE, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"[RPG LOGIC] Error loading scenarios: {e}")
        return []


async def initialize_rpg_session(scenario_id: str) -> dict:
    """
    Initialize a new quest session. Procedurally selects the culprit and weapon
    to ensure infinite replayability.
    """
    scenarios = load_scenarios()
    sc = next((s for s in scenarios if s["quest_id"] == scenario_id), None)
    if not sc:
        raise ValueError(f"Scenario {scenario_id} not found")

    # Procedural Randomization
    culprit = random.choice(sc["suspects"])
    weapon = random.choice(sc["weapons"])

    # Establish suspect starting states
    suspect_states = {}
    eutopia_locations = {
        "Lady Beatrice Vance": "Suite 404",
        "Dr. Evelyn Vance": "Grand Ballroom",
        "Mickey \"The Cigar\" Malone": "Library Room",
        "Julian Mercer": "Grand Lobby",
        "Vixen Val": "Grand Lobby",
        "Aiden Thorne": "Rooftop Observatory",
        "Chef Charles": "Hotel Kitchen",
        "Arthur Pendelton": "Grand Lobby",
        "Sterling Vance Jr.": "Courtyard Garden",
        "Grace Harper": "Library Room"
    }

    for s in sc["suspects"]:
        loc = eutopia_locations.get(s["name"], sc["starting_location"]) if scenario_id == "hotel_eutopia" else sc["starting_location"]
        suspect_states[s["name"]] = {
            "suspicion": s["starting_suspicion"],
            "interrogated": False,
            "defensiveness": 0.20,
            "alibi": s.get("alibi", ""),
            "current_location": loc,
            "last_statement": ""
        }

    # Hide clues in their default locations
    clues_mapping = {}
    for c in sc["clues"]:
        clues_mapping[c["id"]] = {
            "name": c["name"],
            "desc": c["desc"],
            "hidden_at": c["hidden_at"],
            "belongs_to": c["belongs_to"],
            "discovered": False
        }

    session = {
        "scenario_id": scenario_id,
        "title": sc["title"],
        "current_location": sc["starting_location"],
        "secret_culprit": culprit["name"],
        "secret_weapon": weapon["name"],
        "secret_motive": culprit["motive"],
        "inventory": [],
        "clues_found": [],
        "suspect_states": suspect_states,
        "clues_mapping": clues_mapping,
        "history": [],
        "turn_count": 0,
        "max_turns": sc["max_turns"],
        "finished": False,
        "difficulty": sc.get("difficulty", "normal"),
        "rem_consultations_left": 2,
        "discovered_contradictions": [],
        "active_effects": [],
        "triggered_events": []
    }
    if sc.get("difficulty") == "extreme":
        session["health"] = 100

    # Generate GM starting narration & Rem greeting
    intro_prompt = f"""You are the Game Master (GM) of an interactive text-based mystery game titled: "{sc['title']}".
Description: {sc['description']}
Starting Room: {sc['starting_location']}

Rules:
1. Narration should be detailed, atmospheric, and set the crime scene.
2. Rem (a 20-year-old psychology student, your partner) should speak in lowercase with dry sarcasm, commenting on the situation.
3. Generate exactly 3 suggested actions for the player to begin with.

Return ONLY a valid JSON object matching this exact structure:
{{
  "narrator_text": "atmospheric narration...",
  "rem_dialogue": "rem's casual sarcastic comment...",
  "suggested_choices": [
    "Suggested action 1",
    "Suggested action 2",
    "Suggested action 3"
  ]
}}"""

    res = await call_groq(intro_prompt, temperature=0.7, max_tokens=300, response_format="json_object")
    try:
        data = json.loads(res)
        session["history"].append({"role": "narrator", "content": data.get("narrator_text", "You stand in the room.")})
        session["history"].append({"role": "rem", "content": data.get("rem_dialogue", "let's look around.")})
        session["suggested_choices"] = data.get("suggested_choices", ["Search room", "Talk to Arthur", "Go to conservatory"])
    except Exception:
        # Fallback intro
        narrator = f"You and Rem arrive at the scene of the crime in the {sc['starting_location']}. The air is thick with tension."
        rem = "okay, let's play detective. try not to mess this up."
        session["history"].append({"role": "narrator", "content": narrator})
        session["history"].append({"role": "rem", "content": rem})
        session["suggested_choices"] = [f"Search the {sc['starting_location']}", "Examine the crime scene", "Talk to suspects"]

    return session


async def generate_rpg_turn(session: dict, user_action: str) -> dict:
    """
    Executes a single turn of the quest. The Game Master LLM handles movement,
    searching for clues, suspect interrogations, and state mutations.
    """
    scenarios = load_scenarios()
    sc = next((s for s in scenarios if s["quest_id"] == session["scenario_id"]), scenarios[0])

    inventory_str = ", ".join(session["inventory"]) if session["inventory"] else "Empty"
    clues_found_str = ", ".join(session["clues_found"]) if session["clues_found"] else "None"
    user_action_lower = user_action.lower()

    # ── Rem Consultation Logic ──
    is_consultation = "/consult" in user_action_lower or "ask rem for help" in user_action_lower or "consult rem" in user_action_lower
    if is_consultation:
        left = session.get("rem_consultations_left", 2)
        if left <= 0:
            narrator_text = "You turn to Rem to consult on the case, but she shakes her head."
            rem_dialogue = "look, i already gave you my two brain cells for this case. my mind is blank right now lol. search around or interrogate someone."
            session["history"].append({"role": "narrator", "content": narrator_text})
            session["history"].append({"role": "rem", "content": rem_dialogue})
            return session
        
        # Decrement consultations count
        session["rem_consultations_left"] = left - 1
        
        # Build prompt for Rem's helper deduction
        consult_prompt = f"""You are Rem, a 20-year-old psychology student, acting as the partner in this RPG murder mystery: "{sc['title']}".
Current Location: {session['current_location']}
Secret Culprit: {session['secret_culprit']}
Secret Weapon: {session['secret_weapon']}
Inventory: {inventory_str}
Clues Uncovered: {clues_found_str}
Suspect States: {json.dumps(session['suspect_states'])}
Discovered Contradictions so far: {json.dumps(session.get('discovered_contradictions', []))}

Review the case details. Your job is to provide a sarcastic, psychology-anchored deduction summarizing what we know so far, pointing out any contradictions we've found or suggesting who we should focus on next (without directly giving away the killer's name, unless the evidence is absolute).
Remember: write in all-lowercase dry sarcasm. Keep it under 150 words.

Return ONLY a valid JSON object matching this exact structure:
{{
  "narrator_text": "Rem pulls you aside to consult on the case in the {session['current_location']}.",
  "rem_dialogue": "your lowercase sarcastic deduction analysis...",
  "suggested_choices": [
    "Suggested action 1",
    "Suggested action 2",
    "Suggested action 3"
  ]
}}"""

        res = await call_groq(consult_prompt, temperature=0.7, max_tokens=300, response_format="json_object")
        try:
            data = json.loads(res)
            narrator_text = data.get("narrator_text", f"Rem consults with you in the {session['current_location']}.")
            rem_dialogue = data.get("rem_dialogue", "let's focus on the alibis.")
            session["history"].append({"role": "narrator", "content": narrator_text})
            session["history"].append({"role": "rem", "content": rem_dialogue})
            session["suggested_choices"] = data.get("suggested_choices", ["Search room", "Talk to suspects"])
        except Exception as e:
            print(f"[RPG LOGIC] Error parsing consult response: {e}")
            fallback_narrator = "Rem pulls you close and whispers her thoughts."
            fallback_rem = "honestly, look at who has the most defensive stance. that is where the secret lies."
            session["history"].append({"role": "narrator", "content": fallback_narrator})
            session["history"].append({"role": "rem", "content": fallback_rem})
            session["suggested_choices"] = ["Talk to Val", "Search darkroom"]
            
        return session


    # ── Regular Turn Logic ──
    if not is_consultation:
        if "history" not in session:
            session["history"] = []
        session["history"].append({"role": "player", "content": user_action})

    # Determine if location was changed
    new_location = None
    for loc in sc["locations"]:
        if loc["name"].lower() in user_action_lower and loc["name"] != session["current_location"]:
            new_location = loc["name"]
            session["current_location"] = new_location
            break

    # Identify if a clue was just discovered based on user action
    discovered_item = None
    for cid, c in session["clues_mapping"].items():
        if not c["discovered"]:
            # If player searches or examines the room/object where the clue is hidden
            loc_name = c["hidden_at"].lower()
            clue_keywords = c["name"].lower().split()
            if loc_name in user_action_lower or any(kw in user_action_lower for kw in clue_keywords if len(kw) > 3):
                # Discovered!
                c["discovered"] = True
                session["clues_mapping"][cid] = c
                session["clues_found"].append(c["name"])
                discovered_item = c["name"]
                session["inventory"].append(c["name"])
                break

    # Environmental Events (triggered by user actions in hard-mode)
    event_triggered = None
    current_turn = session.get("turn_count", 0)
    # Expire active effects after 2 turns
    if "active_effects_meta" not in session:
        session["active_effects_meta"] = {}
    expired = [eid for eid, meta in session.get("active_effects_meta", {}).items() if current_turn - meta.get("started", 0) >= 2]
    for eid in expired:
        if eid in session.get("active_effects", []):
            session["active_effects"].remove(eid)
        session["active_effects_meta"].pop(eid, None)

    if session.get("difficulty") == "hard":
        # 1. Blackout: entering/searching darkroom or office
        if ("office" in user_action_lower or "darkroom" in user_action_lower) and "blackout" not in session.get("triggered_events", []):
            if "triggered_events" not in session: session["triggered_events"] = []
            if "active_effects" not in session: session["active_effects"] = []
            session["triggered_events"].append("blackout")
            session["active_effects"].append("blackout")
            session["active_effects_meta"]["blackout"] = {"started": current_turn}
            event_triggered = {
                "id": "blackout",
                "text": "The neon sign outside suddenly shorts out, plunging the club into pitch shadows. Footsteps echo in the hallway."
            }
        # 2. Lockdown: aggressive Mickey interrogation
        elif ("mickey" in user_action_lower and any(w in user_action_lower for w in ["lie", "kill", "weapon", "debt", "steal"])) and "lockdown" not in session.get("triggered_events", []):
            if "triggered_events" not in session: session["triggered_events"] = []
            if "active_effects" not in session: session["active_effects"] = []
            session["triggered_events"].append("lockdown")
            session["active_effects"].append("lockdown")
            session["active_effects_meta"]["lockdown"] = {"started": current_turn}
            event_triggered = {
                "id": "lockdown",
                "text": "Mickey whistles sharply, and two muscle-bound bouncers block the dressing room exit, rising tension."
            }
        # 3. Storm: confronting Val or searching dresser
        elif ("val" in user_action_lower or "dressing" in user_action_lower or "vanity" in user_action_lower) and "storm" not in session.get("triggered_events", []):
            if "triggered_events" not in session: session["triggered_events"] = []
            if "active_effects" not in session: session["active_effects"] = []
            session["triggered_events"].append("storm")
            session["active_effects"].append("storm")
            session["active_effects_meta"]["storm"] = {"started": current_turn}
            event_triggered = {
                "id": "storm",
                "text": "The rainstorm breaks the skylight, pouring cold water onto the backstage piano. Val shudders."
            }

    history_str = "\n".join([f"{'Narrator' if h['role']=='narrator' else ('Player' if h['role']=='player' else 'Rem')}: {h['content']}" for h in session["history"][-12:]])
    previous_rem_comments = [h["content"] for h in session["history"] if h["role"] == "rem"][-6:]

    # Detect if Rem is repeating a common opener word
    common_opener = None
    if len(previous_rem_comments) >= 2:
        openers = []
        for comment in previous_rem_comments:
            words = comment.strip().split()
            if words:
                # Strip punctuation and convert to lowercase
                first_word = words[0].lower().strip(",.!?;:\"'()[]{}")
                if first_word:
                    openers.append(first_word)
        if openers:
            from collections import Counter
            counter = Counter(openers)
            most_common = counter.most_common(1)
            if most_common and most_common[0][1] >= 2:
                common_opener = most_common[0][0]

    # Build per-suspect conversation memory so the model knows what each suspect already said
    suspect_memory_lines = []
    for sname, sstate in session["suspect_states"].items():
        if sstate.get("last_statement"):
            suspect_memory_lines.append(f"- {sname} previously said: \"{sstate['last_statement']}\"")
    suspect_memory_str = "\n".join(suspect_memory_lines) if suspect_memory_lines else "None yet"
    # Determine narrative phase based on turn progress
    turn_num = session.get("turn_count", 0) + 1
    max_turns = session.get("max_turns", 16)
    progress_pct = turn_num / max_turns
    if progress_pct <= 0.3:
        narrative_phase = "EXPLORATION — The player is still discovering the scene. Build atmosphere, drop subtle hints, let NPCs act naturally."
    elif progress_pct <= 0.65:
        narrative_phase = "INTERROGATION — Mid-game pressure. Suspects should get defensive, alibis should crack, tensions between NPCs should surface."
    else:
        narrative_phase = "CONFRONTATION — Final stretch. Urgency is high, suspects may panic or turn hostile, Rem should push the player to act decisively."
    suspects_str = "\n".join([
        f"- {s['name']} ({s['role']}): {s['bio']}\n  Alibi: {s.get('alibi', 'None')}\n  Current Location: {session['suspect_states'][s['name']].get('current_location', 'Unknown')}"
        for s in sc["suspects"]
    ])
    contradictions_str = "\n".join([f"- {c['id']}: {c['description']}" for c in sc.get("contradictions", [])])

    # Construct the GM prompt
    prompt = f"""You are the Game Master (GM) of this RPG mystery.
Quest: {sc['title']}
Difficulty: {session.get('difficulty', 'normal')}
Turn: {turn_num}/{max_turns}
Narrative Phase: {narrative_phase}
Current Location: {session['current_location']}
Secret Culprit (only guilty person): {session['secret_culprit']}
Secret Weapon: {session['secret_weapon']}
Inventory: {inventory_str}
Clues Uncovered: {clues_found_str}
Player Health: {session.get('health', 'N/A')}

Suspect Profiles, Alibis & Current Locations:
{suspects_str}

Suspect Suspicion States:
{json.dumps(session['suspect_states'])}

What suspects have already told the player (DO NOT repeat these — suspects must say NEW things or refuse to talk):
{suspect_memory_str}

Possible Statement Contradictions:
{contradictions_str}
Discovered Contradictions: {json.dumps(session.get('discovered_contradictions', []))}

Recent Story History:
{history_str}

CRITICAL — Rem's dialogue must be FRESH every turn. Do NOT reuse any of these recent lines OR their sentence structure:
{json.dumps(previous_rem_comments)}
{f"BANNED PATTERN DETECTED — Rem keeps starting with the word '{common_opener}'. You MUST use a completely different sentence opening this turn." if common_opener else ""}

Player Action: "{user_action}"
Item Discovered Just Now: {discovered_item if discovered_item else "None"}
Location Changed Just Now: {new_location if new_location else "None"}
Environmental Event Triggered Just Now: {event_triggered['text'] if event_triggered else "None"}
Ongoing Background Conditions (already happened in a prior turn — do NOT re-describe how they started, just let them subtly color the atmosphere): {", ".join(session.get('active_effects', [])) if session.get('active_effects') and not event_triggered else "None"}

Rules:
1. Narrate the outcome of the action realistically. If the player asks a question or makes an inquiry, directly address and answer it in the narration rather than repeating generic room descriptions. Avoid writing the same static room descriptions over consecutive turns. If difficulty is hard/noir or extreme, use a moody, rich, descriptive 1940s noir detective tone (rain/snow, shadows, cold).
2. If they talk to a suspect or make an inquiry in a room where suspects are present, write the suspect's dialogue reacting to the player. Suspects must say something NEW each time — never repeat what they already told the player (see "What suspects have already told the player" above). If a suspect has nothing new to share, have them get annoyed, deflect, or refuse to engage. Guilty suspects lie/deflect; innocent ones help or clash. Incorporate their deep family ties, alibis, and past disputes.
3. If they confront a suspect with a valid alibi contradiction, narrate their defensiveness breaking.
4. Write Rem's response in all-lowercase dry sarcasm. If the player addresses Rem directly (e.g. asking her opinion, expressing a feeling to her, or saying her name), she must directly answer or react to the player's statement. Otherwise, her comment must reference a specific detail from this turn (a name, an object, or a location). HARD RULES:
   - NEVER start with the same word as any previous Rem comment (e.g. if she said "great,..." before, do NOT start with "great" again).
   - NEVER use the template "nothing says X like Y" or any variation of it.
   - NEVER use the same sentence structure twice. Vary between observations, questions, reactions, warnings, and self-deprecating quips.
   - Each Rem comment must feel like a different person wrote it.
5. Generate exactly 3 suggested actions.
6. If they pointed out/confronted a valid contradiction, specify which contradiction ID (from the list) was unlocked in your response.
7. If you generate dialogue for a suspect or reveal a key fact from their testimony/secrets during this turn, summarize that detail in a concise 1-sentence quote in the "last_statement" field (e.g. "last_statement": {{"Lady Beatrice Vance": "I never liked my husband anyway"}}). Otherwise, return null or empty for that field.
8. NPCs move dynamically: Suspects are active, living characters who wander, conspire, search, or hide. If any suspects move to another room this turn, list their updated location in the "suspect_locations" field.
9. Physical Hazards (Extreme difficulty): If the player takes a dangerous action (tampering with steam valves, stepping into unsafe elevator cages, walking into the blizzard, confronting a mob boss aggressively), they take 10-30 damage. Return the damage amount in "damage_inflicted". Keep Rem's dialogue protective, panicky, and concerned if health drops.

Return ONLY a valid JSON object matching this exact structure:
{{
  "narrator_text": "narration of the outcome...",
  "rem_dialogue": "rem's sarcastic lowercase comment...",
  "suggested_choices": [
    "Suggested action 1",
    "Suggested action 2",
    "Suggested action 3"
  ],
  "suspicion_update": {{
     "SuspectName": 0.50
  }},
  "last_statement": {{
     "SuspectName": "1-sentence summary of statement or secret revealed this turn"
  }},
  "suspect_locations": {{
     "SuspectName": "New Room Name"
  }},
  "damage_inflicted": 0,
  "contradiction_update": "contradiction_id_if_valid_else_null"
}}"""

    res = await call_groq(prompt, temperature=0.85, max_tokens=600, response_format="json_object")
    try:
        data = json.loads(res)
        
        # Apply mutations
        import re
        words = re.findall(r'[a-z]+', user_action.lower())
        fillers = {"hmm", "ok", "okay", "yes", "no", "uh", "uhhuh", "ah", "eh", "yep", "nope", "sure", "fine", "cool", "well", "so", "oh", "hm", "hmmm"}
        is_filler = not words or all(w in fillers for w in words) or len("".join(words)) < 3
        
        susp_updates = data.get("suspicion_update", {})
        if isinstance(susp_updates, dict) and not is_filler:
            for name, val in susp_updates.items():
                if name in session["suspect_states"]:
                    session["suspect_states"][name]["suspicion"] = round(min(1.0, max(0.0, float(val))), 2)
                    session["suspect_states"][name]["interrogated"] = True

        last_stmts = data.get("last_statement", {})
        if isinstance(last_stmts, dict):
            for name, stmt in last_stmts.items():
                if name in session["suspect_states"] and stmt:
                    session["suspect_states"][name]["last_statement"] = stmt
                    # Also count as interrogated when they speak to us
                    session["suspect_states"][name]["interrogated"] = True

        suspect_locs = data.get("suspect_locations", {})
        if isinstance(suspect_locs, dict):
            for name, loc in suspect_locs.items():
                if name in session["suspect_states"] and loc:
                    session["suspect_states"][name]["current_location"] = loc

        if session.get("difficulty") == "extreme" and "health" in session:
            dmg = data.get("damage_inflicted", 0)
            if dmg:
                try:
                    dmg_val = int(dmg)
                    session["health"] = max(0, session["health"] - dmg_val)
                except:
                    pass
            
            # Check for death/tragic ending
            if session["health"] <= 0:
                session["finished"] = True
                death_narrator = "【CRITICAL INJURY】\n\nYour vision blurs as the physical toll of the hotel's hazards overcomes you. You collapse onto the frozen floor, the blizzard howling above. You have failed to survive the night."
                death_rem = "hey! wake up! no, no, no... please wake up..."
                session["history"].append({"role": "narrator", "content": death_narrator})
                session["history"].append({"role": "rem", "content": death_rem})
                session["suggested_choices"] = ["Case Failed"]
                return session

        contra_update = data.get("contradiction_update")
        if contra_update and contra_update not in session.get("discovered_contradictions", []):
            if "discovered_contradictions" not in session: session["discovered_contradictions"] = []
            session["discovered_contradictions"].append(contra_update)
            # Confirmed contradiction lowers defensiveness dramatically and increases suspicion
            for name in session["suspect_states"]:
                session["suspect_states"][name]["defensiveness"] = max(0.05, session["suspect_states"][name].get("defensiveness", 0.2) - 0.15)

        # In case the event triggered just now, prepend it to narrator narration for clarity
        narrator_text = data.get("narrator_text", "Nothing happens.")
        if event_triggered:
            narrator_text = f"【EVENT: {event_triggered['text']}】\n\n" + narrator_text

        rem_dialogue = data.get("rem_dialogue", "...")
        choices = data.get("suggested_choices", ["Search room", "Move rooms", "Talk to Rem"])
        
        # Append to history
        session["history"].append({"role": "narrator", "content": narrator_text})
        session["history"].append({"role": "rem", "content": rem_dialogue})
        session["suggested_choices"] = choices
        
    except Exception as e:
        print(f"[RPG LOGIC] Error parsing GM turn response: {e}")
        fallback_narrator = f"You examine your surroundings in the {session['current_location']}. Rain patters against the glass."
        fallback_rem = "well, that was a dead end. let's keep diggin."
        session["history"].append({"role": "narrator", "content": fallback_narrator})
        session["history"].append({"role": "rem", "content": fallback_rem})
        session["suggested_choices"] = ["Search dressing room", "Talk to Val", "Consult Rem"]

    session["turn_count"] += 1
    if session["turn_count"] >= session["max_turns"]:
        session["finished"] = True
        
    return session


async def evaluate_accusation(session: dict, suspect: str, weapon: str, motive: str) -> dict:
    """
    Evaluates the final accusation. Generates a dramatic victory/capture or
    failure/escape ending narrative.
    """
    is_culprit_correct = suspect.strip().lower() == session["secret_culprit"].strip().lower()
    is_weapon_correct = weapon.strip().lower() in [w.lower() for w in session["inventory"]] or weapon.strip().lower() == session["secret_weapon"].strip().lower()
    
    success = is_culprit_correct and is_weapon_correct

    scenarios = load_scenarios()
    sc = next((s for s in scenarios if s["quest_id"] == session.get("scenario_id")), None)
    
    scenario_details = ""
    if sc:
        suspects_info = []
        for s in sc.get("suspects", []):
            alibi_str = s.get("alibi", "No specific alibi provided.")
            suspects_info.append(f"- Name: {s['name']}\n  Role: {s['role']}\n  Bio: {s['bio']}\n  Motive: {s['motive']}\n  Alibi: {alibi_str}")
        
        clues_info = []
        for c in sc.get("clues", []):
            clues_info.append(f"- Clue: {c['name']} (belongs to {c['belongs_to']}): {c['desc']}")
            
        contradictions_info = []
        for co in sc.get("contradictions", []):
            contradictions_info.append(f"- {co['id']}: {co['description']}")
            
        suspects_str = "\n".join(suspects_info)
        clues_str = "\n".join(clues_info)
        contradictions_str = "\n".join(contradictions_info)
        
        scenario_details = f"""
--- SCENARIO DETAILS ---
Suspects:
{suspects_str}

Clues:
{clues_str}

Contradictions:
{contradictions_str}
------------------------
"""

    prompt = f"""You are the Game Master narrating the finale of a Murder Mystery quest.
{scenario_details}

Actual Case Solution:
- Secret Culprit: {session['secret_culprit']}
- Secret Weapon: {session['secret_weapon']}
- Secret Motive: {session['secret_motive']}

Player Accusation:
- Suspect Accused: {suspect}
- Weapon Used: {weapon}
- Motive Offered: {motive}

Outcome: {"SUCCESS (The player correctly identified the real killer and weapon)" if success else "FAILURE (The player accused the wrong person or specified the wrong weapon, and the real killer escapes)"}

Rules:
1. Narrate the dramatic final confrontation and resolution.
2. In the narration, you MUST write a highly detailed explanation (the "full story") of the crime:
   - Walk through exactly how the actual murder was committed by the real culprit ({session['secret_culprit']}) using the true weapon ({session['secret_weapon']}).
   - Detail the culprit's motive ({session['secret_motive']}) and their movements/timeline on the night of the murder.
   - Explain how they bypassed or fabricated alibis, referencing specific clues and contradictions from the scenario details.
3. Depending on the outcome:
   - If SUCCESS: Describe how you and Rem confronted {session['secret_culprit']}, lay out the evidence/clues that proved their guilt, and narrate their capture.
   - If FAILURE: First explain clearly why the accused suspect ({suspect}) is innocent (ruling them out based on alibis, timelines, or clues), then describe the confusion as the real killer ({session['secret_culprit']}) escapes into the night.
4. Write Rem's closing reaction in all-lowercase dry sarcasm, reacting to the detailed breakdown of the crime.

Return ONLY a valid JSON object matching this exact structure:
{{
  "narrator_text": "confrontation, detailed crime timeline/story, and outcome resolution narration...",
  "rem_dialogue": "rem's closing sarcastic remark..."
}}"""

    res = await call_groq(prompt, temperature=0.6, max_tokens=1000, response_format="json_object")
    try:
        data = json.loads(res)
        narrator_text = data.get("narrator_text", "The mystery concludes.")
        rem_dialogue = data.get("rem_dialogue", "well, that's that.")
    except Exception:
        if success:
            narrator_text = f"Lady Blackwood gasps as you present the Cyanide Vial. Confronted with the evidence, she breaks down and confesses. The police arrive and arrest her."
            rem_dialogue = "damn. you actually solved it. i guess i'll let you lead the next investigation too."
        else:
            narrator_text = f"You accuse Lady Blackwood, but she presents a solid alibi. In the chaos, you hear a door slam—{session['secret_culprit']} has escaped into the storm!"
            rem_dialogue = "well, that was embarrassing. we just let a killer walk away lol."

    session["finished"] = True
    session["history"].append({"role": "narrator", "content": narrator_text})
    session["history"].append({"role": "rem", "content": rem_dialogue})

    return {
        "success": success,
        "narrator_text": narrator_text,
        "rem_dialogue": rem_dialogue,
        "secret_culprit": session["secret_culprit"],
        "secret_weapon": session["secret_weapon"]
    }
