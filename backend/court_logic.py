import os
import json
import random
from typing import List, Dict, Tuple
from .games_logic import call_groq

SCENARIOS_FILE = os.path.join(os.path.dirname(__file__), "court_scenarios.json")

def load_court_scenarios() -> List[dict]:
    if not os.path.exists(SCENARIOS_FILE):
        return []
    with open(SCENARIOS_FILE, "r") as f:
        return json.load(f)

async def initialize_court_session(case_id: str) -> dict:
    scenarios = load_court_scenarios()
    sc = next((s for s in scenarios if s["case_id"] == case_id), None)
    if not sc:
        raise ValueError(f"Court Case {case_id} not found")

    session = {
        "case_id": case_id,
        "title": sc["title"],
        "difficulty": sc["difficulty"],
        "client_name": sc["client_name"],
        "client_role": sc["client_role"],
        "client_bio": sc["client_bio"],
        "prosecutor_name": sc["prosecutor_name"],
        "judge_name": sc["judge_name"],
        "inventory": sc["initial_evidence"],
        "current_witness_idx": 0,
        "witnesses": sc["witnesses"],
        "recess_locations": sc["recess_locations"],
        "recess_searched": [],
        "strikes_left": 5,
        "jury_sentiment": 0,
        "discovered_contradictions": [],
        "rem_consults_left": 5,
        "rem_chat_history": [],
        "phase": "briefing",  # briefing, cross_examination, recess, closing, verdict
        "history": [],
        "finished": False,
        "verdict_result": None
    }

    # Generate dramatic GM intro and Rem greeting
    intro_prompt = f"""You are the Game Master narrating the opening of an Ace Attorney courtroom battle titled: "{sc['title']}".
The defendant is {sc['client_name']} ({sc['client_role']}). The prosecutor is {sc['prosecutor_name']}. The judge is {sc['judge_name']}.
Provide a brief dramatic opening setup in the courtroom, announcing the charges and the mood.
Then write a greeting from Rem (your co-counsel, a sarcastic 20-year-old psychology student) in all-lowercase.

Return ONLY a valid JSON object matching this exact structure:
{{
  "narrator_text": "dramatic courtroom opening...",
  "rem_dialogue": "rem's sarcastic lowercase advice/banter..."
}}"""

    res = await call_groq(intro_prompt, temperature=0.7, max_tokens=350, response_format="json_object")
    try:
        data = json.loads(res)
        session["history"].append({"role": "narrator", "speaker": sc["judge_name"], "content": data.get("narrator_text", "Court is now in session.")})
        session["history"].append({"role": "rem", "speaker": "rem", "content": data.get("rem_dialogue", "alright, let's keep this client out of jail.")})
    except Exception:
        session["history"].append({"role": "narrator", "speaker": sc["judge_name"], "content": f"The court is now in session for the trial of {sc['client_name']}. The prosecution is ready."})
        session["history"].append({"role": "rem", "speaker": "rem", "content": "pay attention to the testimonies. if something sounds off, we object."})

    return session

async def process_court_action(session: dict, action: dict) -> dict:
    """
    Processes interactive court moves:
    - action_type: 'call_witness', 'press', 'present_evidence', 'text_question', 'consult_rem'
    """
    action_type = action.get("action_type")
    scenarios = load_court_scenarios()
    sc = next((s for s in scenarios if s["case_id"] == session["case_id"]), None)
    if not sc:
        return session

    current_witness = session["witnesses"][session["current_witness_idx"]]

    if action_type == "call_witness":
        session["phase"] = "cross_examination"
        call_text = f"The prosecution calls {current_witness['name']} ({current_witness['role']}) to the stand. The witness takes the stand and delivers their testimony."
        session["history"].append({"role": "narrator", "speaker": "Court Clerk", "content": call_text})
        
        # Present testimony lines
        for idx, line in enumerate(current_witness["testimony"]):
            session["history"].append({"role": "testimony", "speaker": current_witness["name"], "content": f"Statement {idx + 1}: \"{line}\""})
        
        # Rem's brief tip
        session["history"].append({"role": "rem", "speaker": "rem", "content": f"let's check the testimony against our case file. we have {len(session['inventory'])} items of evidence."})

    elif action_type == "press":
        statement_idx = int(action.get("statement_idx", 0))
        statement_text = current_witness["testimony"][statement_idx]
        
        session["history"].append({"role": "user", "speaker": "Defense", "content": f"HOLD IT! (Pressing statement {statement_idx + 1}: \"{statement_text}\")"})
        
        # Check if this statement unlocks new evidence
        unlocked_evidence = current_witness.get("press_unlocks", {}).get(str(statement_idx))
        unlocked_log = ""
        
        if unlocked_evidence:
            ev_id = unlocked_evidence["evidence_id"]
            # Check if already in inventory
            if not any(item["id"] == ev_id for item in session["inventory"]):
                new_item = {
                    "id": ev_id,
                    "name": unlocked_evidence["name"],
                    "desc": unlocked_evidence["desc"]
                }
                session["inventory"].append(new_item)
                unlocked_log = f"\n\n[DISCOVERY: New Evidence Added to Case File: {new_item['name']}]"
                session["jury_sentiment"] = min(session["jury_sentiment"] + 10, 100)

        # Standard or dynamic press response
        reaction = current_witness.get("press_reactions", {}).get(str(statement_idx), "I stand by my statement.")
        witness_dialogue = f"{current_witness['name']}: \"{reaction}\""
        
        prompt = f"""You are co-counsel Rem in an Ace Attorney courtroom trial.
The player just pressed the witness {current_witness['name']} on statement: "{statement_text}"
The witness replied: "{reaction}"
Give a quick, sarcastic psychology student comment on this reply in lowercase. Keep it to 1 sentence.
"""
        rem_res = await call_groq(prompt, temperature=0.8, max_tokens=80)
        rem_comment = rem_res.strip().lower() if rem_res else "sounds like they are sweating."

        narrator_log = f"You press the witness on their statement. {witness_dialogue}{unlocked_log}"
        session["history"].append({"role": "narrator", "speaker": current_witness["name"], "content": narrator_log})
        session["history"].append({"role": "rem", "speaker": "rem", "content": rem_comment})

    elif action_type == "present_evidence":
        statement_idx = int(action.get("statement_idx", 0))
        evidence_id = action.get("evidence_id", "")
        statement_text = current_witness["testimony"][statement_idx]
        
        evidence_name = next((item["name"] for item in session["inventory"] if item["id"] == evidence_id), "Unknown Clue")
        session["history"].append({"role": "user", "speaker": "Defense", "content": f"OBJECTION! (Presenting {evidence_name} against Statement {statement_idx + 1}: \"{statement_text}\")"})
        
        # Check contradiction mapping
        contradiction = current_witness.get("contradictions", {}).get(str(statement_idx))
        is_correct = contradiction and contradiction["evidence_id"] == evidence_id
        
        if is_correct:
            session["jury_sentiment"] = min(session["jury_sentiment"] + 25, 100)
            session["discovered_contradictions"].append(f"{current_witness['id']}_{statement_idx}")
            
            narrator_text = contradiction["narrative"]
            session["history"].append({"role": "narrator", "speaker": "Judge", "content": narrator_text})
            
            # Advancing trial
            session["current_witness_idx"] += 1
            if session["current_witness_idx"] < len(session["witnesses"]):
                session["phase"] = "cross_examination"
                next_witness = session["witnesses"][session["current_witness_idx"]]
                session["history"].append({"role": "rem", "speaker": "rem", "content": f"nice job! that broke their alibi completely. now let's hear what {next_witness['name']} has to say."})
            else:
                # Check if we should go to recess or closing arguments
                if len(session["recess_locations"]) > 0 and len(session["recess_searched"]) < 1:
                    session["phase"] = "recess"
                    recess_text = "The witness stumbles off the stand in tears! The judge slams his gavel: 'Order! The defense has raised a significant point. We will take a 10-minute recess. You may investigate the gallery offices or backstage area to review details.'"
                    session["history"].append({"role": "narrator", "speaker": session["judge_name"], "content": recess_text})
                    session["history"].append({"role": "rem", "speaker": "rem", "content": "let's go search the rooms. we might find a vital clue."})
                else:
                    session["phase"] = "closing"
                    closing_text = "All witnesses have been cross-examined, and their alibis lie in pieces. The Judge commands: 'Both counselors will now present their closing arguments. Let the jury hear your final plea!'"
                    session["history"].append({"role": "narrator", "speaker": session["judge_name"], "content": closing_text})
                    session["history"].append({"role": "rem", "speaker": "rem", "content": "we have them cornered. write a strong closing plea to convince the jury."})
        else:
            # Penalty
            session["strikes_left"] -= 1
            session["jury_sentiment"] = max(session["jury_sentiment"] - 20, -100)
            
            mockery_prompt = f"""You are the arrogant prosecutor {session['prosecutor_name']} in an Ace Attorney courtroom trial.
The defense attorney just raised an objection presenting evidence '{evidence_name}' against statement '{statement_text}', which makes no sense and contains no contradiction.
Objection overruled! Deliver a quick, biting, sarcastic roast of the defense's foolish argument. Keep it under 2 sentences.
"""
            mock_res = await call_groq(mockery_prompt, temperature=0.8, max_tokens=100)
            prosecutor_roast = mock_res.strip() if mock_res else "That objection is completely irrelevant!"
            
            session["history"].append({"role": "narrator", "speaker": session["prosecutor_name"], "content": f"PROSECUTION: \"{prosecutor_roast}\""})
            session["history"].append({"role": "narrator", "speaker": session["judge_name"], "content": f"JUDGE: \"Objection overruled! The defense will refrain from baseless accusations. Strike inflicted.\""})
            session["history"].append({"role": "rem", "speaker": "rem", "content": "ouch, that hurt. let's be more careful. check the description of the evidence again."})
            
            if session["strikes_left"] <= 0:
                session["phase"] = "verdict"
                session["finished"] = True
                verdict_text = "The judge bangs his gavel multiple times. 'The defense has run out of credibility. I have heard enough. This court finds the defendant guilty as charged!'"
                session["history"].append({"role": "narrator", "speaker": session["judge_name"], "content": verdict_text})
                session["history"].append({"role": "rem", "speaker": "rem", "content": "well, that was a disaster. we got completely shut down. let's restart the trial."})
                session["verdict_result"] = {
                    "success": False,
                    "votes_guilty": 6,
                    "votes_not_guilty": 0,
                    "rationale": "The defense raised multiple baseless objections and was penalized out of court."
                }

    elif action_type == "text_question":
        question = action.get("question", "")
        session["history"].append({"role": "user", "speaker": "Defense", "content": f"Question: \"{question}\""})
        
        prompt = f"""You are witness '{current_witness['name']}' ({current_witness['role']}) in an Ace Attorney trial.
Bio: {current_witness['bio']}
Testimony Statements:
{json.dumps(current_witness['testimony'])}

Case Solution details:
- Defendant: {session['client_name']}
- True Culprit of Case: {'Mickey' if session['case_id'] == 'gallery_theft' else 'Dr. Evelyn Vance'}

The defense lawyer just asked you: "{question}"
Answer in character. Keep it brief (2-3 sentences). If you are the culprit or trying to frame someone, act evasive or defensive. If you are innocent, try to be helpful or react to the pressure. 
Also evaluate the question: if it is highly relevant and exposes cracks, include a slight nervous gesture (like sweating, wringing hands, or stuttering).

Return ONLY a JSON object:
{{
  "witness_reply": "your verbal response...",
  "gesture": "description of gesture (e.g. sweating slightly)...",
  "sentiment_shift": 5
}}"""
        res = await call_groq(prompt, temperature=0.7, max_tokens=250, response_format="json_object")
        try:
            data = json.loads(res)
            reply = data.get("witness_reply", "I have nothing to say to that.")
            gesture = data.get("gesture", "")
            shift = int(data.get("sentiment_shift", 0))
            # Limit shift to -5 to +10
            shift = max(-5, min(10, shift))
            session["jury_sentiment"] = max(-100, min(100, session["jury_sentiment"] + shift))
            
            log_text = f"{current_witness['name']}: \"{reply}\""
            if gesture:
                log_text = f"*{gesture}*\n{log_text}"
            
            session["history"].append({"role": "narrator", "speaker": current_witness["name"], "content": log_text})
        except Exception:
            session["history"].append({"role": "narrator", "speaker": current_witness["name"], "content": f"{current_witness['name']}: \"I don't see how that is relevant to my testimony.\""})

        # Rem co-counsel reaction
        rem_prompt = f"""You are Rem, co-counsel in an Ace Attorney trial.
The witness just replied: "{question}"
Give a quick 1-sentence comment in all-lowercase dry psychology student banter.
"""
        rem_comment = await call_groq(rem_prompt, temperature=0.8, max_tokens=80)
        session["history"].append({"role": "rem", "speaker": "rem", "content": rem_comment.strip().lower() if rem_comment else "well, that was an answer."})

    elif action_type == "consult_rem":
        if session.get("rem_consults_left", 5) <= 0:
            raise ValueError("You have run out of consultations with Rem for this trial!")
            
        session["rem_consults_left"] = session.get("rem_consults_left", 5) - 1
        user_question = action.get("question", "").strip()
        if not user_question:
            user_question = "Do you have any suggestions on this testimony?"
            
        prompt = f"""You are Rem, a 20-year-old psychology student acting as co-counsel in a courtroom trial.
Active Witness: {current_witness['name']}
Their Testimony:
{json.dumps(current_witness['testimony'])}

Case Clues in inventory:
{json.dumps(session['inventory'])}

The player (defense attorney) asked you this question: "{user_question}"

Based on the testimony and evidence, write a helpful, slightly sarcastic psychology advice line in all-lowercase. Highlight which statement sounds like a psychological projection or lie, or hint at which evidence we need to present or find. Respond directly to the player's question. Keep it to 1-2 sentences.
"""
        rem_advice = await call_groq(prompt, temperature=0.7, max_tokens=150)
        advice_text = rem_advice.strip().lower() if rem_advice else "let's look at the timestamps."
        
        if "rem_chat_history" not in session:
            session["rem_chat_history"] = []
        session["rem_chat_history"].append({"role": "user", "content": user_question})
        session["rem_chat_history"].append({"role": "rem", "content": advice_text})

    return session

async def process_recess_search(session: dict, room_id: str) -> dict:
    """
    Handles courthouse search during investigation recess.
    """
    scenarios = load_court_scenarios()
    sc = next((s for s in scenarios if s["case_id"] == session["case_id"]), None)
    if not sc:
        return session

    room = next((r for r in session["recess_locations"] if r["id"] == room_id), None)
    if not room:
        return session

    session["recess_searched"].append(room_id)
    search_log = f"You search the {room['name']}. {room['desc']}"
    session["history"].append({"role": "narrator", "speaker": "Investigation", "content": search_log})
    
    clue = room.get("clue")
    if clue:
        if not any(item["id"] == clue["id"] for item in session["inventory"]):
            session["inventory"].append(clue)
            session["history"].append({"role": "narrator", "speaker": "System", "content": f"[DISCOVERY: Added {clue['name']} to Case File!]"})
            session["history"].append({"role": "rem", "speaker": "rem", "content": "bingo! that's exactly what we need. let's head back to the courtroom and finish this."})
            
    # Automatically end recess and return to court (advance to next phase or closing)
    session["phase"] = "cross_examination"
    if session["current_witness_idx"] < len(session["witnesses"]):
        # Resume cross-examination
        next_witness = session["witnesses"][session["current_witness_idx"]]
        session["history"].append({"role": "narrator", "speaker": "Judge", "content": f"The recess concludes. The court recalls {next_witness['name']} to the stand."})
        # Present testimony lines
        for idx, line in enumerate(next_witness["testimony"]):
            session["history"].append({"role": "testimony", "speaker": next_witness["name"], "content": f"Statement {idx + 1}: \"{line}\""})
    else:
        # Go to closing
        session["phase"] = "closing"
        session["history"].append({"role": "narrator", "speaker": "Judge", "content": "The recess concludes. Both counselors will now present their closing arguments."})

    return session

async def evaluate_court_verdict(session: dict, closing_argument: str) -> dict:
    """
    Invokes the Judge and Jury LLM to evaluate the trial history, closing arguments,
    and final verdict.
    """
    scenarios = load_court_scenarios()
    sc = next((s for s in scenarios if s["case_id"] == session["case_id"]), None)
    
    # Success requires resolving all contradictions
    # Case 1 requires arthur_butler contradiction 2 (outage_log) and mickey_collector contradiction 3 (pawn_slip)
    # Case 2 requires evelyn_physician contradiction 3 (syringe_clue)
    success = False
    if session["case_id"] == "gallery_theft":
        success = "arthur_butler_2" in session["discovered_contradictions"] and "mickey_collector_3" in session["discovered_contradictions"]
    elif session["case_id"] == "velvet_poisoning":
        success = "evelyn_physician_3" in session["discovered_contradictions"]

    # Judge & Jury LLM Verdict Evaluation
    jury_sentiment = session["jury_sentiment"]
    prompt = f"""You are the Judge and Jury panel in a high-stakes courtroom battle drama.
Case Title: {session['title']}
Difficulty: {session['difficulty']}
Defendant: {session['client_name']} ({session['client_role']})

Trial History Stats:
- Strikes Left: {session['strikes_left']}/5
- Jury Sentiment Balance: {jury_sentiment} (-100 is fully Prosecution, +100 is fully Defense)
- Contradictions Discovered: {session['discovered_contradictions']}

Defense Closing Argument: "{closing_argument}"
Outcome Evaluation: {"SUCCESS (Defense successfully proved innocence and exposed the real culprit)" if success else "FAILURE (Defense failed to expose the core contradictions of the alibis)"}

Rules:
1. Generate the jury voting breakdown. There are 6 jurors. 
   - If SUCCESS: The jury vote should be heavily in favor of NOT GUILTY (e.g. 6-0 or 5-1 Not Guilty).
   - If FAILURE: The jury vote should be GUILTY (e.g. 5-1 or 6-0 Guilty).
2. Write the Judge's written verdict speech in detail, summarizing the facts of the crime, detailing what was discovered during the trial (or what was missed), evaluating the closing argument, and declaring the final verdict.
3. Write Rem's closing lowercase reaction to the verdict.

Return ONLY a valid JSON object matching this exact structure:
{{
  "verdict_text": "NOT GUILTY" or "GUILTY",
  "votes_not_guilty": 5,
  "votes_guilty": 1,
  "judge_decision": "the detailed judge summary and reasoning text...",
  "rem_dialogue": "rem's closing reaction comment..."
}}"""

    res = await call_groq(prompt, temperature=0.6, max_tokens=1000, response_format="json_object")
    try:
        data = json.loads(res)
        verdict = data.get("verdict_text", "NOT GUILTY" if success else "GUILTY")
        votes_ng = int(data.get("votes_not_guilty", 6 if success else 1))
        votes_g = int(data.get("votes_guilty", 0 if success else 5))
        judge_decision = data.get("judge_decision", "The court renders its decision.")
        rem_dialogue = data.get("rem_dialogue", "well, that's that.")
    except Exception:
        verdict = "NOT GUILTY" if success else "GUILTY"
        votes_ng = 6 if success else 1
        votes_g = 0 if success else 5
        judge_decision = f"After reviewing the evidence and alibis, the court finds the defendant {verdict}."
        rem_dialogue = "hell yeah, we won!" if success else "damn, let's try again."

    session["verdict_result"] = {
        "success": success,
        "verdict_text": verdict,
        "votes_not_guilty": votes_ng,
        "votes_guilty": votes_g,
        "judge_decision": judge_decision,
        "rem_dialogue": rem_dialogue
    }
    
    session["finished"] = True
    session["phase"] = "verdict"
    session["history"].append({"role": "narrator", "speaker": session["judge_name"], "content": f"VERDICT: {verdict} ({votes_ng} Not Guilty vs {votes_g} Guilty)"})
    session["history"].append({"role": "narrator", "speaker": session["judge_name"], "content": judge_decision})
    session["history"].append({"role": "rem", "speaker": "rem", "content": rem_dialogue})
    
    return session
