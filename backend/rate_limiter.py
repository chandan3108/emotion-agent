"""
Centralized Rate Limiter for all LLM API calls.

Every module that calls Groq (or any LLM API) must import and use this
shared limiter so that ALL calls are counted against a single budget.

Usage:
    from .rate_limiter import global_rate_limiter
    await global_rate_limiter.wait_if_needed()
"""

import time
import asyncio


class RateLimiter:
    """
    Token-bucket style rate limiter.
    Tracks call timestamps and enforces a max calls-per-minute window.
    """

    def __init__(self, calls_per_minute: int = 8):
        self.calls_per_minute = calls_per_minute
        self.call_times: list[float] = []
        self._lock = asyncio.Lock()

    async def wait_if_needed(self):
        """Wait if we've exhausted our per-minute budget."""
        async with self._lock:
            now = time.time()
            # Prune calls older than 60 s
            self.call_times = [t for t in self.call_times if now - t < 60]

            if len(self.call_times) >= self.calls_per_minute:
                oldest = min(self.call_times)
                wait_time = 60 - (now - oldest) + 0.5  # small safety margin
                if wait_time > 0:
                    print(
                        f"[RATE LIMIT] {len(self.call_times)}/{self.calls_per_minute} calls in window — "
                        f"waiting {wait_time:.1f}s"
                    )
                    await asyncio.sleep(wait_time)

            self.call_times.append(time.time())


# ── Singleton ────────────────────────────────────────────────────────
# 8 calls / 60 s keeps us safely under Groq free-tier limits even when
# background tasks and the main response call overlap.
global_rate_limiter = RateLimiter(calls_per_minute=8)
