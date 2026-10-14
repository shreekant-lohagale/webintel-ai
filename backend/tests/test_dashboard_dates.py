from datetime import datetime, timezone
import pytest
from app.intelligence.dashboard import aware_utc, date_buckets


def d(day, hour=0):
    return datetime(2026, 10, day, hour, tzinfo=timezone.utc)


def test_one_day_bucket():
    assert date_buckets(d(13), d(14)) == ['2026-10-13']


def test_partial_day_included():
    assert date_buckets(d(13, 12), d(14, 12)) == ['2026-10-13', '2026-10-14']


def test_end_is_exclusive():
    assert date_buckets(d(13), d(15)) == ['2026-10-13', '2026-10-14']


def test_equal_dates_rejected():
    with pytest.raises(ValueError):
        date_buckets(d(13), d(13))


def test_naive_date_rejected():
    with pytest.raises(ValueError):
        aware_utc(datetime(2026, 10, 13))


def test_too_long_rejected():
    with pytest.raises(ValueError):
        date_buckets(datetime(2026, 1, 1, tzinfo=timezone.utc), d(13))
