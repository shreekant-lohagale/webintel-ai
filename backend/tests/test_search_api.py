
from fastapi.testclient import TestClient

from app.api.main import create_app


def test_search_without_database_returns_503():
    app = create_app(connect_db=False)

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/search",
            json={
                "query": "AI workflows",
                "mode": "hybrid",
            },
        )

    assert response.status_code == 503


def test_search_rejects_empty_query():
    app = create_app(connect_db=False)

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/search",
            json={
                "query": "",
            },
        )

    assert response.status_code == 422


def test_search_rejects_invalid_mode():
    app = create_app(connect_db=False)

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/search",
            json={
                "query": "AI",
                "mode": "unsupported",
            },
        )

    assert response.status_code == 422


def test_search_rejects_invalid_limit():
    app = create_app(connect_db=False)

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/search",
            json={
                "query": "AI",
                "limit": 100,
            },
        )

    assert response.status_code == 422


def test_search_route_appears_in_openapi():
    app = create_app(connect_db=False)

    with TestClient(app) as client:
        response = client.get("/openapi.json")

    assert response.status_code == 200
    assert (
        "/api/v1/search"
        in response.json()["paths"]
    )
