
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.api.main import create_app
from app.api.schemas.crawl_jobs import CrawlJobCreate
from app.pipeline.run import validate_start_url


def test_default_job_payload():
    payload = CrawlJobCreate()

    assert payload.start_url == (
        "http://127.0.0.1:8766/"
    )
    assert payload.browser is False


def test_extra_fields_are_rejected():
    with pytest.raises(ValidationError):
        CrawlJobCreate(
            start_url="http://127.0.0.1:8766/",
            secret="unexpected",
        )


def test_local_url_is_allowed():
    assert validate_start_url(
        "http://127.0.0.1:8766/",
        allow_live=False,
    ) == "local"


@pytest.mark.parametrize(
    "url",
    [
        "http://127.0.0.1:27018/",
        "http://127.0.0.1:8766/admin",
        "http://localhost:8766/",
        "http://127.0.0.1:8766/?secret=1",
        "https://example.com/news/",
        "file:///etc/passwd",
    ],
)
def test_disallowed_urls(url):
    with pytest.raises(ValueError):
        validate_start_url(
            url,
            allow_live=False,
        )


def test_crawl_service_unavailable():
    app = create_app(connect_db=False)

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/crawl/jobs",
            json={
                "start_url":
                    "http://127.0.0.1:8766/",
            },
        )

    assert response.status_code == 503


def test_invalid_url_rejected_before_database():
    app = create_app(connect_db=False)

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/crawl/jobs",
            json={
                "start_url":
                    "https://example.com/news/",
            },
        )

    assert response.status_code == 422


def test_crawl_job_routes_in_openapi():
    app = create_app(connect_db=False)

    with TestClient(app) as client:
        response = client.get("/openapi.json")

    assert response.status_code == 200

    paths = response.json()["paths"]

    assert "/api/v1/crawl/jobs" in paths
    assert "/api/v1/crawl/jobs/{job_id}" in paths
