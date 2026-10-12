
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

RETRYABLE_STATUSES = {429, 500, 502, 503, 504}


def calculate_backoff(
    attempt: int,
    base_delay: float = 1.0,
    max_delay: float = 10.0,
    retry_after: str | None = None,
) -> float:

    if attempt < 1:
        raise ValueError("Attempt must be >= 1")

    delay = min(
        max_delay,
        base_delay * (2 ** (attempt - 1))
    )

    if retry_after:
        try:
            server_delay = float(retry_after)
        except ValueError:
            try:
                retry_date = parsedate_to_datetime(retry_after)

                if retry_date.tzinfo is None:
                    retry_date = retry_date.replace(
                        tzinfo=timezone.utc
                    )

                server_delay = (
                    retry_date - datetime.now(timezone.utc)
                ).total_seconds()
            except (TypeError, ValueError, OverflowError):
                return delay

        server_delay = max(0.0, server_delay)

        # If the server demands more than our waiting
        # budget, defer rather than retry prematurely.
        if server_delay > max_delay:
            return -1.0

        delay = max(delay, server_delay)

    return delay
