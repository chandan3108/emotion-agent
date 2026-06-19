import asyncio
import sys
import os
import unittest
from unittest.mock import AsyncMock, patch

# Add parent directory to path to import modules
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

from fastapi.testclient import TestClient
from backend.game_api import router, _get_core, ChatRequest
from fastapi import FastAPI

app = FastAPI()
app.include_router(router)

class TestBackendTimeouts(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.user_id = "test_timeout_user"

    @patch("backend.discord_bot.generate_response")
    async def test_chat_timeout_fallback(self, mock_generate):
        # Configure mock_generate to sleep for 12 seconds, exceeding the 8.0s timeout
        async def slow_generate(*args, **kwargs):
            await asyncio.sleep(12.0)
            return "This response should never be reached due to timeout", None
            
        mock_generate.side_effect = slow_generate

        # Call `/chat` endpoint using TestClient
        payload = {"message": "hello, are you there?"}
        
        # TestClient runs synchronously, which runs the event loop internally.
        # However, because FastAPI route calls the mock, TestClient will wait for the route to finish.
        # The route itself has an 8s timeout, so it should finish in ~8s and return a 200 with fallback text.
        print("[TEST] Sending message to trigger 8-second timeout...")
        import time
        start_time = time.time()
        
        response = self.client.post(f"/api/user/{self.user_id}/chat", json=payload)
        duration = time.time() - start_time
        print(f"[TEST] Request completed in {duration:.2f} seconds.")

        # Asserts
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("reply", data)
        self.assertIn("reply_parts", data)
        
        reply = data["reply"]
        print(f"[TEST] Rem's response: \"{reply}\"")
        
        fallbacks = [
            "sorry, my signal was acting up for a sec. what were you saying?",
            "ah sorry, i got a bit distracted. what was that again?",
            "sorry, my phone glitched out. say that again?",
            "sorry about that, my connection dropped. what did you say?",
            "hey, sorry! had a brief lag on my end. could you repeat that?"
        ]
        self.assertIn(reply, fallbacks)
        print("[TEST] Success: Returned a beautiful in-character fallback response under timeout!")

if __name__ == "__main__":
    unittest.main()
