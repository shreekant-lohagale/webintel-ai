from datetime import datetime, timedelta, timezone
import pytest
from app.intelligence.freshness import classify

NOW = datetime(2026, 10, 14, 12, tzinfo=timezone.utc)

def test_recent():
    assert classify(NOW - timedelta(hours=2), now=NOW)['status'] == 'recently_observed'
def test_recent_boundary():
    assert classify(NOW - timedelta(hours=24), now=NOW)['status'] == 'recently_observed'
def test_aging():
    assert classify(NOW - timedelta(hours=48), now=NOW)['status'] == 'aging_observation'
def test_stale():
    assert classify(NOW - timedelta(days=8), now=NOW)['status'] == 'stale_observation'
def test_missing():
    assert classify(None, now=NOW)['status'] == 'unknown'
def test_future():
    assert classify(NOW + timedelta(minutes=5), now=NOW)['status'] == 'future_timestamp'
def test_naive_rejected():
    with pytest.raises(ValueError):
        classify(datetime(2026, 10, 14), now=NOW)
def test_invalid_threshold():
    with pytest.raises(ValueError):
        classify(None, now=NOW, fresh_hours=168, stale_hours=24)
