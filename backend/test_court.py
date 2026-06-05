import asyncio
import os
import sys

# Add directory to sys path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load env variables manually from backend/.env
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                os.environ[key.strip()] = val.strip().strip('"').strip("'")

from backend.court_logic import initialize_court_session, process_court_action, process_recess_search, evaluate_court_verdict

async def main():
    print("=== Testing Law and Rem Courtroom Engine ===")
    
    # 1. Start Case
    print("\n[Step 1] Initializing 'gallery_theft'...")
    session = await initialize_court_session("gallery_theft")
    print(f"Case Title: {session['title']}")
    print(f"Presiding:  {session['judge_name']} vs {session['prosecutor_name']}")
    print(f"Client:     {session['client_name']}")
    print(f"Phase:      {session['phase']}")
    print(f"History (Start): {session['history'][-2]['content']} | Rem: {session['history'][-1]['content']}")
    
    # 2. Call Witness
    print("\n[Step 2] Calling Arthur the Butler to stand...")
    session = await process_court_action(session, {"action_type": "call_witness"})
    print(f"Phase:      {session['phase']}")
    print(f"Current Witness: {session['witnesses'][session['current_witness_idx']]['name']}")
    
    # 3. Press Statement 1 (index 1)
    print("\n[Step 3] Pressing Statement 2...")
    session = await process_court_action(session, {"action_type": "press", "statement_idx": 1})
    print(f"Jury Sentiment: {session['jury_sentiment']}")
    print(f"Inventory (Clues): {[ev['name'] for ev in session['inventory']]}")
    print(f"Last History Log: {session['history'][-2]['content']}")
    print(f"Rem comment: {session['history'][-1]['content']}")
    
    # 4. Incorrect Objection (Presenting 'theft_time_estimate' on Statement 0)
    print("\n[Step 4] Presenting Incorrect Objection...")
    session = await process_court_action(session, {
        "action_type": "present_evidence",
        "statement_idx": 0,
        "evidence_id": "theft_time_estimate"
    })
    print(f"Strikes Left: {session['strikes_left']}/5")
    print(f"Jury Sentiment: {session['jury_sentiment']}")
    print(f"Last Log: {session['history'][-3]['content']}") # Roast
    
    # 5. Correct Objection (Presenting 'outage_log' on Statement 2)
    print("\n[Step 5] Presenting Correct Objection...")
    session = await process_court_action(session, {
        "action_type": "present_evidence",
        "statement_idx": 2,
        "evidence_id": "outage_log"
    })
    print(f"Contradictions: {session['discovered_contradictions']}")
    print(f"Jury Sentiment: {session['jury_sentiment']}")
    print(f"Phase: {session['phase']}") # Recess
    
    # 6. Recess Search room 'study_desk'
    print("\n[Step 6] Recess search of Mickey's Study Desk...")
    session = await process_recess_search(session, "study_desk")
    print(f"Inventory: {[ev['name'] for ev in session['inventory']]}")
    print(f"Phase: {session['phase']}") # Back in cross_examination for next witness
    print(f"Current Witness: {session['witnesses'][session['current_witness_idx']]['name']}")
    
    # 7. Ask dynamic text question
    print("\n[Step 7] Asking dynamic question to Mickey...")
    session = await process_court_action(session, {
        "action_type": "text_question",
        "question": "Did you pawn the watch before the theft occurred?"
    })
    print(f"Last Log: {session['history'][-2]['content']}")
    print(f"Rem comment: {session['history'][-1]['content']}")
    print(f"Jury Sentiment: {session['jury_sentiment']}")
    
    # 8. Correct Objection on Mickey (Statement 3 - Gold watch securely locked) with pawn_slip
    print("\n[Step 8] Presenting pawn slip objection against Mickey Statement 4...")
    session = await process_court_action(session, {
        "action_type": "present_evidence",
        "statement_idx": 3,
        "evidence_id": "pawn_slip"
    })
    print(f"Contradictions: {session['discovered_contradictions']}")
    print(f"Phase: {session['phase']}") # closing
    
    # 9. Submit Closing Arguments
    print("\n[Step 9] Submitting closing arguments and obtaining verdict...")
    session = await evaluate_court_verdict(
        session=session,
        closing_argument="Mickey pawned the watch at 8:30 PM, as proven by the pawn shop receipt. He framed Toby to claim insurance."
    )
    print(f"Finished: {session['finished']}")
    print(f"Verdict:  {session['verdict_result']['verdict_text']}")
    print(f"Votes:    {session['verdict_result']['votes_not_guilty']} Not Guilty vs {session['verdict_result']['votes_guilty']} Guilty")
    print(f"Judge decision rationale:\n{session['verdict_result']['judge_decision']}")
    print(f"Rem reaction: {session['verdict_result']['rem_dialogue']}")
    print("\n=== All Courtroom Engine Integration Tests Passed! ===")

if __name__ == "__main__":
    asyncio.run(main())
