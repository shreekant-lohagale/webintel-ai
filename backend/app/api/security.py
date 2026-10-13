
import hashlib
import hmac
import os
from collections import defaultdict, deque
from datetime import datetime, timezone
from threading import Lock
from time import monotonic

from fastapi import Header, HTTPException, status


def configured_api_key() -> str:
    return os.getenv("WEBINTEL_API_KEY", "").strip()


def key_fingerprint(key: str) -> str:
    return hashlib.sha256(
        key.encode("utf-8")
    ).hexdigest()[:16]


def require_api_key(
    x_api_key: str | None = Header(default=None),
) -> str:
    """
    Protect crawl write operations.

    Empty configured key preserves the existing
    localhost development behavior.
    """

    expected = configured_api_key()

    if not expected:
        return "local-development"

    if not x_api_key or not hmac.compare_digest(
        x_api_key, expected
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    return key_fingerprint(expected)


class SubmissionLimiter:
    """
    In-memory per-key sliding-window limiter.

    Suitable for one local API process.
    """

    def __init__(
        self,
        max_requests: int = 10,
        window_seconds: int = 60,
    ):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._history = defaultdict(deque)
        self._lock = Lock()

    def check(self, identity: str) -> bool:
        now = monotonic()

        with self._lock:
            history = self._history[identity]

            while (
                history
                and now - history[0]
                >= self.window_seconds
            ):
                history.popleft()

            if len(history) >= self.max_requests:
                return False

            history.append(now)
            return True
