from backend.game_api import switch_session, SwitchSessionRequest
import asyncio

async def test_switch():
    # Mock user ID from the database
    user_id = "user_08e9206361fbd3dd"
    session_id = "sess_fc06fb4529e6c25e" # The Default Conversation session
    
    print(f"Testing switch_session to {session_id} for user {user_id}")
    payload = SwitchSessionRequest(session_id=session_id)
    
    try:
        res = await switch_session(payload, user_id=user_id)
        print("Success!", res)
    except Exception as e:
        print("Error during switch_session:", e)
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(test_switch())
