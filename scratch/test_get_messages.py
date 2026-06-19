from backend.game_api import get_messages
import asyncio

async def test_get_messages():
    user_id = "user_08e9206361fbd3dd"
    session_id = "sess_fc06fb4529e6c25e"
    
    print(f"Testing get_messages for session {session_id} for user {user_id}")
    try:
        res = await get_messages(session_id=session_id, user_id=user_id)
        print("Success! Message count:", len(res.messages))
        for m in res.messages[:3]:
            print(f"  [{m.role}]: {m.content[:50]}...")
    except Exception as e:
        print("Error during get_messages:", e)
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(test_get_messages())
