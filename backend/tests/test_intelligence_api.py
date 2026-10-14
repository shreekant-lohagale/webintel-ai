
from fastapi.testclient import TestClient

from app.api.main import create_app
from app.api.routes.analytics import (
    get_intelligence_service,
)


VALID_ID = "a" * 64


class FakeIntelligenceService:
    async def overview(self):
        return {
            "document_count": 2,
            "revision_count": 3,
            "source_observation_count": 2,
            "source_domain_count": 1,
            "documents_by_type": {
                "article": 2
            },
        }

    async def source_statistics(self, limit=20):
        return {
            "items": [{
                "source_domain": "example.com",
                "document_count": 2,
                "article_count": 2,
                "quote_count": 0,
            }],
            "returned_count": 1,
            "limit": limit,
        }

    async def timeline(
        self,
        document_id,
        max_revisions=200,
    ):
        if document_id != VALID_ID:
            return None
        return {
            "document_id": document_id,
            "revision_count": 2,
            "change_count": 1,
            "history": [],
        }

    async def compare(
        self,
        document_id,
        from_revision_id=None,
        to_revision_id=None,
    ):
        if document_id != VALID_ID:
            return None
        return {
            "document_id": document_id,
            "content_changed": True,
            "added_words": 2,
        }


def make_test_app():
    app = create_app(connect_db=False)
    app.dependency_overrides[
        get_intelligence_service
    ] = lambda: FakeIntelligenceService()
    return app


def test_analytics_requires_database():
    app = create_app(connect_db=False)

    with TestClient(app) as client:
        response = client.get(
            "/api/v1/analytics/overview"
        )

    assert response.status_code == 503


def test_overview_endpoint():
    app = make_test_app()

    with TestClient(app) as client:
        response = client.get(
            "/api/v1/analytics/overview"
        )

    assert response.status_code == 200
    assert response.json()["document_count"] == 2


def test_sources_endpoint():
    app = make_test_app()

    with TestClient(app) as client:
        response = client.get(
            "/api/v1/analytics/sources?limit=5"
        )

    assert response.status_code == 200
    assert response.json()["returned_count"] == 1


def test_invalid_source_limit():
    app = make_test_app()

    with TestClient(app) as client:
        response = client.get(
            "/api/v1/analytics/sources?limit=101"
        )

    assert response.status_code == 422


def test_timeline_endpoint():
    app = make_test_app()

    with TestClient(app) as client:
        response = client.get(
            f"/api/v1/analytics/documents/"
            f"{VALID_ID}/changes"
        )

    assert response.status_code == 200
    assert response.json()["change_count"] == 1


def test_compare_endpoint():
    app = make_test_app()

    with TestClient(app) as client:
        response = client.get(
            f"/api/v1/analytics/documents/"
            f"{VALID_ID}/compare"
        )

    assert response.status_code == 200
    assert response.json()["added_words"] == 2


def test_document_not_found():
    app = make_test_app()

    with TestClient(app) as client:
        response = client.get(
            f"/api/v1/analytics/documents/"
            f"{'b' * 64}/changes"
        )

    assert response.status_code == 404


def test_invalid_document_id():
    app = make_test_app()

    with TestClient(app) as client:
        response = client.get(
            "/api/v1/analytics/documents/invalid/changes"
        )

    assert response.status_code == 422


def test_analytics_routes_in_openapi():
    app = make_test_app()

    with TestClient(app) as client:
        response = client.get("/openapi.json")

    paths = response.json()["paths"]

    assert "/api/v1/analytics/overview" in paths
    assert "/api/v1/analytics/sources" in paths
    assert (
        "/api/v1/analytics/documents/"
        "{document_id}/compare"
    ) in paths
