
import json
from pathlib import Path

import pytest

from app.scrapers.scrapy_crawler.reliability import (
    calculate_backoff,
    RETRYABLE_STATUSES,
)


RESULT_FILE = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "raw"
    / "resilient_results.json"
)


def test_exponential_backoff():
    assert calculate_backoff(1) == 1.0
    assert calculate_backoff(2) == 2.0
    assert calculate_backoff(3) == 4.0
    assert calculate_backoff(4) == 8.0


def test_backoff_cap():
    assert calculate_backoff(6) == 10.0


def test_retry_after():
    assert calculate_backoff(
        attempt=1,
        retry_after="2",
    ) == 2.0


def test_retry_after_never_shortens_delay():
    assert calculate_backoff(
        attempt=3,
        retry_after="1",
    ) == 4.0


def test_retry_after_exceeds_budget():
    assert calculate_backoff(
        attempt=1,
        max_delay=10.0,
        retry_after="120",
    ) == -1.0


def test_invalid_attempt():
    with pytest.raises(ValueError):
        calculate_backoff(0)


def test_retryable_statuses():
    assert 429 in RETRYABLE_STATUSES
    assert 503 in RETRYABLE_STATUSES
    assert 500 in RETRYABLE_STATUSES
    assert 403 not in RETRYABLE_STATUSES


def test_exported_results():
    if not RESULT_FILE.exists():
        pytest.skip("Run resilient spider first")

    records = json.loads(
        RESULT_FILE.read_text(encoding="utf-8")
    )

    assert len(records) == 2

    scenarios = {
        record["scenario"] for record in records
    }

    assert scenarios == {"unstable", "limited"}

    for record in records:
        assert record["http_status"] == 200
        assert record["title"]
        assert record["source_url"]
