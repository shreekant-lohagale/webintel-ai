
import pytest
from fastapi.testclient import TestClient

from app.api.main import create_app
from app.api.security import (
    SubmissionLimiter,
    key_fingerprint,
)


def test_api_key_fingerprint_is_deterministic():
    assert key_fingerprint("secret") == (
        key_fingerprint("secret")
    )
    assert key_fingerprint("secret") != "secret"


def test_rate_limiter_allows_limited_requests():
    limiter = SubmissionLimiter(
        max_requests=2,
        window_seconds=60,
    )

    assert limiter.check("user-a") is True
    assert limiter.check("user-a") is True
    assert limiter.check("user-a") is False

    # Different identities have independent limits.
    assert limiter.check("user-b") is True


def test_missing_api_key_is_rejected(monkeypatch):
    monkeypatch.setenv(
        "WEBINTEL_API_KEY",
        "test-secret-key",
    )

    app = create_app(connect_db=False)

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/crawl/jobs",
            json={
                "start_url":
                    "http://127.0.0.1:8766/"
            },
        )

    assert response.status_code == 401


def test_invalid_api_key_is_rejected(monkeypatch):
    monkeypatch.setenv(
        "WEBINTEL_API_KEY",
        "test-secret-key",
    )

    app = create_app(connect_db=False)

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/crawl/jobs",
            headers={
                "X-API-Key": "wrong-key"
            },
            json={
                "start_url":
                    "http://127.0.0.1:8766/"
            },
        )

    assert response.status_code == 401


def test_correct_api_key_reaches_service(
    monkeypatch,
):
    monkeypatch.setenv(
        "WEBINTEL_API_KEY",
        "test-secret-key",
    )

    app = create_app(connect_db=False)

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/crawl/jobs",
            headers={
                "X-API-Key": "test-secret-key"
            },
            json={
                "start_url":
                    "http://127.0.0.1:8766/"
            },
        )

    # Authentication passed; service is intentionally
    # absent because connect_db=False.
    assert response.status_code == 503


def test_cancel_requires_api_key(monkeypatch):
    monkeypatch.setenv(
        "WEBINTEL_API_KEY",
        "test-secret-key",
    )

    app = create_app(connect_db=False)

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/crawl/jobs/"
            "11111111-1111-4111-8111-111111111111"
            "/cancel"
        )

    assert response.status_code == 401


def test_request_id_header(monkeypatch):
    monkeypatch.setenv("WEBINTEL_API_KEY", "")

    app = create_app(connect_db=False)

    with TestClient(app) as client:
        response = client.get(
            "/api/v1/health/live"
        )

    assert response.status_code == 200
    assert "X-Request-ID" in response.headers


def test_cancel_endpoint_in_openapi(monkeypatch):
    monkeypatch.setenv("WEBINTEL_API_KEY", "")

    app = create_app(connect_db=False)

    with TestClient(app) as client:
        response = client.get("/openapi.json")

    assert response.status_code == 200

    assert (
        "/api/v1/crawl/jobs/{job_id}/cancel"
        in response.json()["paths"]
    )
