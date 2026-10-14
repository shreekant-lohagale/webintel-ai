"""Pure UTC observation-age calculations; not assertions about content truth."""
from datetime import datetime, timezone


def utc(value: datetime) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError('Expected timezone-aware datetime')
    return value.astimezone(timezone.utc)


def classify(last_seen: datetime | None, *, now: datetime, fresh_hours: int = 24, stale_hours: int = 168) -> dict:
    now = utc(now)
    if not (1 <= fresh_hours < stale_hours <= 87600):
        raise ValueError('Require 1 <= fresh_hours < stale_hours <= 87600')
    if last_seen is None:
        return {'status': 'unknown', 'age_hours': None, 'last_seen_at': None}
    last_seen = utc(last_seen)
    hours = (now - last_seen).total_seconds() / 3600
    if hours < 0:
        status = 'future_timestamp'
    elif hours <= fresh_hours:
        status = 'recently_observed'
    elif hours <= stale_hours:
        status = 'aging_observation'
    else:
        status = 'stale_observation'
    return {'status': status, 'age_hours': round(hours, 3), 'last_seen_at': last_seen.isoformat()}
