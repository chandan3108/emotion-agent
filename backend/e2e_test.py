"""
End-to-End Test — Emotion Agent API

Tests all API endpoints against a running (or startable) FastAPI server.
Covers: health, XP, diary, timeline, stats, inside-jokes, patterns, chat, link flow.

Usage:
    # With server already running:
    python -m backend.e2e_test

    # Or from project root:
    cd /path/to/emotion-agent && python -m backend.e2e_test
"""

import sys
import json
import time
import sqlite3
from pathlib import Path

# Test config
BASE_URL = "http://localhost:8000"
TEST_USER = "e2e_test_user"


def _req(method: str, path: str, body: dict = None) -> dict:
    """Make HTTP request using urllib (no external deps)."""
    import urllib.request
    import urllib.error

    url = f"{BASE_URL}{path}"
    data = json.dumps(body).encode() if body else None
    headers = {"Content-Type": "application/json"} if body else {}

    req = urllib.request.Request(url, data=data, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        error_body = e.read().decode() if e.fp else ""
        return {"_error": True, "_status": e.code, "_body": error_body}
    except Exception as e:
        return {"_error": True, "_status": 0, "_body": str(e)}


def _pass(name: str):
    print(f"  ✅ {name}")
    return True


def _fail(name: str, reason: str):
    print(f"  ❌ {name}: {reason}")
    return False


def test_health():
    r = _req("GET", "/health")
    if r.get("status") == "healthy":
        return _pass("Health check")
    return _fail("Health check", f"Got: {r}")


def test_root():
    r = _req("GET", "/")
    if r.get("status") == "backend ok":
        return _pass("Root endpoint")
    return _fail("Root endpoint", f"Got: {r}")


def test_xp():
    r = _req("GET", f"/api/user/{TEST_USER}/xp")
    if r.get("_error"):
        return _fail("XP endpoint", r.get("_body", ""))
    if "total_xp" in r and "phase" in r:
        return _pass("XP endpoint")
    return _fail("XP endpoint", f"Missing fields. Keys: {list(r.keys())}")


def test_diary():
    r = _req("GET", f"/api/user/{TEST_USER}/diary")
    if r.get("_error"):
        return _fail("Diary endpoint", r.get("_body", ""))
    if "entries" in r:
        return _pass("Diary endpoint")
    return _fail("Diary endpoint", f"Missing 'entries'. Keys: {list(r.keys())}")


def test_timeline():
    r = _req("GET", f"/api/user/{TEST_USER}/timeline")
    if r.get("_error"):
        return _fail("Timeline endpoint", r.get("_body", ""))
    if "events" in r:
        return _pass("Timeline endpoint")
    return _fail("Timeline endpoint", f"Missing 'events'. Keys: {list(r.keys())}")


def test_stats():
    r = _req("GET", f"/api/user/{TEST_USER}/stats")
    if r.get("_error"):
        return _fail("Stats endpoint", r.get("_body", ""))
    if "total_messages" in r or "current_phase" in r:
        return _pass("Stats endpoint")
    return _fail("Stats endpoint", f"Keys: {list(r.keys())}")


def test_inside_jokes():
    r = _req("GET", f"/api/user/{TEST_USER}/inside-jokes")
    if r.get("_error"):
        return _fail("Inside jokes endpoint", r.get("_body", ""))
    if "jokes" in r:
        return _pass("Inside jokes endpoint")
    return _fail("Inside jokes endpoint", f"Keys: {list(r.keys())}")


def test_patterns():
    r = _req("GET", f"/api/user/{TEST_USER}/patterns")
    if r.get("_error"):
        return _fail("Patterns endpoint", r.get("_body", ""))
    if "patterns" in r:
        return _pass("Patterns endpoint")
    return _fail("Patterns endpoint", f"Keys: {list(r.keys())}")


def test_chat():
    r = _req("POST", f"/api/user/{TEST_USER}/chat", {"message": "Hello, this is an E2E test."})
    if r.get("_error"):
        return _fail("Chat endpoint", r.get("_body", ""))
    if "reply" in r and r["reply"]:
        return _pass(f"Chat endpoint (reply: {r['reply'][:60]}...)")
    return _fail("Chat endpoint", f"Missing or empty reply. Keys: {list(r.keys())}")


def test_link_flow():
    """Test the Discord link code flow end-to-end."""
    from backend.user_sync import generate_link_code, get_link_status

    # Step 1: Generate a code for a fake Discord user
    fake_discord_id = "999999999"
    code = generate_link_code(fake_discord_id)
    if not code or len(code) != 6:
        return _fail("Link flow", f"Bad code: {code}")

    # Step 2: Verify the code via API
    r = _req("POST", f"/api/user/{TEST_USER}/link", {"code": code})
    if r.get("_error"):
        return _fail("Link flow (verify)", r.get("_body", ""))
    if not r.get("success"):
        return _fail("Link flow (verify)", f"Not successful: {r}")

    # Step 3: Check link status
    r2 = _req("GET", f"/api/user/{TEST_USER}/link")
    if not r2.get("linked"):
        return _fail("Link flow (status)", f"Not linked: {r2}")

    return _pass(f"Link flow (code={code}, discord_id={fake_discord_id})")


def test_yap_mode():
    # 1. Start session
    start_payload = {"topic": "Quantum Physics"}
    r = _req("POST", f"/api/user/{TEST_USER}/games/yap/start", start_payload)
    if r.get("_error"):
        return _fail("Yap Mode (start)", r.get("_body", ""))
    
    session_id = r.get("session_id")
    greeting = r.get("greeting")
    facts = r.get("facts")
    
    if not session_id or not greeting or not isinstance(facts, list):
        return _fail("Yap Mode (start)", f"Invalid response: {r}")
        
    # 2. Chat
    chat_payload = {"message": "what is superposition?"}
    r2 = _req("POST", f"/api/user/{TEST_USER}/games/yap/chat", chat_payload)
    if r2.get("_error"):
        return _fail("Yap Mode (chat)", r2.get("_body", ""))
        
    response = r2.get("response")
    turn_count = r2.get("turn_count")
    finished = r2.get("finished")
    achievement_unlocked = r2.get("achievement_unlocked")
    
    if not response or turn_count != 1 or finished is not False or achievement_unlocked is not False:
        return _fail("Yap Mode (chat)", f"Invalid chat response: {r2}")
        
    return _pass("Yap Mode (start and chat endpoints)")


def test_rpg_mode():
    # 1. Get scenarios
    r = _req("GET", f"/api/user/{TEST_USER}/games/rpg/scenarios")
    if isinstance(r, dict) and r.get("_error"):
        return _fail("RPG Mode (scenarios)", r.get("_body", ""))
    if not isinstance(r, list) or len(r) == 0:
        return _fail("RPG Mode (scenarios)", f"Invalid response: {r}")
    
    scenario_id = r[0]["quest_id"]
    
    # 2. Start RPG session
    start_payload = {"scenario_id": scenario_id}
    r2 = _req("POST", f"/api/user/{TEST_USER}/games/rpg/start", start_payload)
    if r2.get("_error"):
        return _fail("RPG Mode (start)", r2.get("_body", ""))
    
    session_id = r2.get("session_id")
    title = r2.get("title")
    narrator_text = r2.get("narrator_text")
    rem_dialogue = r2.get("rem_dialogue")
    
    if not session_id or not title or not narrator_text or not rem_dialogue:
        return _fail("RPG Mode (start)", f"Invalid response: {r2}")
        
    # 3. Take a turn
    turn_payload = {"user_action": "Search the library"}
    r3 = _req("POST", f"/api/user/{TEST_USER}/games/rpg/turn", turn_payload)
    if r3.get("_error"):
        return _fail("RPG Mode (turn)", r3.get("_body", ""))
        
    current_location = r3.get("current_location")
    turn_count = r3.get("turn_count")
    finished = r3.get("finished")
    
    if not current_location or turn_count != 1 or finished is not False:
        return _fail("RPG Mode (turn)", f"Invalid turn response: {r3}")
        
    # 4. Start Jazz Club Betrayal (Hard scenario)
    jazz_scenario = next((s for s in r if s["quest_id"] == "jazz_club_betrayal"), None)
    if jazz_scenario:
        r4 = _req("POST", f"/api/user/{TEST_USER}/games/rpg/start", {"scenario_id": "jazz_club_betrayal"})
        if r4.get("_error"):
            return _fail("RPG Hard Mode (start)", r4.get("_body", ""))
        
        difficulty = r4.get("difficulty")
        consults = r4.get("rem_consultations_left")
        if difficulty != "hard" or consults != 2:
            return _fail("RPG Hard Mode (start response validation)", f"Invalid response: {r4}")
            
        # Try consulting Rem
        r5 = _req("POST", f"/api/user/{TEST_USER}/games/rpg/turn", {"user_action": "Ask Rem for help"})
        if r5.get("_error"):
            return _fail("RPG Hard Mode (consult)", r5.get("_body", ""))
            
        consults_after = r5.get("rem_consultations_left")
        if consults_after != 1:
            return _fail("RPG Hard Mode (consult tracking)", f"Expected 1 consult remaining, got: {consults_after}")
            
    return _pass("RPG Mode (scenarios, start, turn and hard-mode consult endpoints)")


def test_court_mode():
    # 1. Fetch scenarios
    r = _req("GET", f"/api/user/{TEST_USER}/games/court/scenarios")
    if isinstance(r, dict) and r.get("_error"):
        return _fail("Court Mode (scenarios)", r.get("_body", ""))
    
    if not isinstance(r, list) or len(r) == 0:
        return _fail("Court Mode (scenarios)", f"Invalid response: {r}")
        
    # 2. Start session
    payload = {"case_id": "gallery_theft"}
    r2 = _req("POST", f"/api/user/{TEST_USER}/games/court/start", payload)
    if isinstance(r2, dict) and r2.get("_error"):
        return _fail("Court Mode (start)", r2.get("_body", ""))
        
    session_id = r2.get("session_id")
    title = r2.get("title")
    phase = r2.get("phase")
    
    if not session_id or not title or phase != "briefing":
        return _fail("Court Mode (start response validation)", f"Invalid response: {r2}")
        
    # 3. Trigger call witness action
    r3 = _req("POST", f"/api/user/{TEST_USER}/games/court/action", {"action_type": "call_witness"})
    if isinstance(r3, dict) and r3.get("_error"):
        return _fail("Court Mode (call_witness action)", r3.get("_body", ""))
        
    if r3.get("phase") != "cross_examination":
        return _fail("Court Mode (phase progression)", f"Expected cross_examination phase, got: {r3.get('phase')}")
        
    return _pass("Court Mode (scenarios, start, action endpoints)")


def cleanup():
    """Remove test user state and link."""
    try:
        db_path = Path("state.db")
        if db_path.exists():
            conn = sqlite3.connect(db_path)
            # Clean up the web user state
            conn.execute("DELETE FROM user_state WHERE user_id = ?", (f"web_{TEST_USER}",))
            # Clean up the base user state if created directly
            conn.execute("DELETE FROM user_state WHERE user_id = ?", (TEST_USER,))
            # Clean up the linked discord state
            conn.execute("DELETE FROM user_state WHERE user_id = ?", ("discord_999999999",))
            conn.execute("DELETE FROM user_links WHERE web_user_id = ?", (TEST_USER,))
            conn.execute("DELETE FROM link_codes WHERE discord_id = ?", ("999999999",))
            conn.commit()
            conn.close()
            print("  🧹 Cleaned up test data")
    except Exception as e:
        print(f"  ⚠️  Cleanup warning: {e}")


def main():
    print(f"\n🧪 E2E Test — Emotion Agent API")
    print(f"   Target: {BASE_URL}")
    print(f"   User:   {TEST_USER}\n")

    # Check server is reachable
    r = _req("GET", "/")
    if r.get("_error"):
        print(f"❌ Server not reachable at {BASE_URL}")
        print(f"   Start it with: uvicorn backend.main:app --port 8000")
        sys.exit(1)

    tests = [
        test_health,
        test_root,
        test_xp,
        test_diary,
        test_timeline,
        test_stats,
        test_inside_jokes,
        test_patterns,
        test_chat,
        test_link_flow,
        test_yap_mode,
        test_rpg_mode,
        test_court_mode,
    ]

    passed = 0
    failed = 0

    for test_fn in tests:
        try:
            if test_fn():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            _fail(test_fn.__name__, str(e))
            failed += 1

    cleanup()

    print(f"\n{'='*40}")
    print(f"  Results: {passed} passed, {failed} failed, {passed + failed} total")
    print(f"{'='*40}\n")

    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
