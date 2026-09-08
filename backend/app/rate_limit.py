"""A small in-memory rate limiter.

Deliberately not a library: this deployment is a single container on one
box, so a dict and a lock are enough. Two consequences worth knowing —
the counters reset when the app restarts, and they are not shared if you
ever run more than one worker or replica. At that point this needs to
move to Redis or the database.
"""

import threading
import time
from collections import defaultdict


class RateLimiter:
    def __init__(self, max_attempts: int, window_seconds: int):
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds

        self._hits: dict[str, list[float]] = defaultdict(list)
        # Endpoints run in a threadpool, so the dict needs guarding.
        self._lock = threading.Lock()

    def _prune(self, key: str, now: float) -> list[float]:
        cutoff = now - self.window_seconds

        recent = [hit for hit in self._hits[key] if hit > cutoff]
        self._hits[key] = recent

        return recent

    def check(self, key: str) -> int | None:
        """Record an attempt. Returns None if allowed, or the number of
        seconds until the next attempt is permitted."""
        now = time.time()

        with self._lock:
            recent = self._prune(key, now)

            if len(recent) >= self.max_attempts:
                oldest = recent[0]
                return max(1, int(oldest + self.window_seconds - now))

            self._hits[key].append(now)

            return None

    def reset(self, key: str) -> None:
        """Called after a success, so a legitimate user who mistyped a
        few times isn't locked out by their own correct login."""
        with self._lock:
            self._hits.pop(key, None)

    def clear(self) -> None:
        with self._lock:
            self._hits.clear()


# Per IP: enough headroom for a shared office address, tight enough that
# guessing passwords in bulk is impractical.
login_ip_limiter = RateLimiter(max_attempts=20, window_seconds=15 * 60)

# Per username: an attacker spreading attempts across many addresses
# still can't hammer one account.
login_user_limiter = RateLimiter(max_attempts=6, window_seconds=15 * 60)

# Registration is rarer than login, so it can be stricter — but not so
# strict that a few colleagues behind one office address can't sign up.
register_ip_limiter = RateLimiter(max_attempts=10, window_seconds=60 * 60)


def clear_all() -> None:
    """Reset every limiter. Used by the test suite: the counters live in
    the process, so without this one test's attempts leak into the
    next and unrelated tests start failing with 429."""
    for limiter in (
        login_ip_limiter,
        login_user_limiter,
        register_ip_limiter,
    ):
        limiter.clear()


def client_ip(request) -> str:
    """The caller's address as seen from outside.

    Behind Caddy, request.client.host is the proxy's container IP — the
    same value for every visitor — so limiting on it would lock out the
    whole internet at once. Caddy sets X-Forwarded-For, and it is the
    only thing in front of the app, so the first entry is trustworthy
    here. It would NOT be if the app were exposed directly.
    """
    forwarded = request.headers.get("x-forwarded-for")

    if forwarded:
        return forwarded.split(",")[0].strip()

    return request.client.host if request.client else "unknown"
