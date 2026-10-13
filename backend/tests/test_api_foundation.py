
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.api.config import Settings
from app.api.dependencies import get_repository
from app.api.main import create_app


def test_settings():
    settings = Settings(
        app_title="WebIntel Test API",
        app_version="0.1-test",
        debug=False,
        mongodb_uri="mongodb://127.0.0.1:27018",
        mongodb_database="webintel_test",
    )

    assert settings.app_title == "WebIntel Test API"
    assert settings.app_version == "0.1-test"
    assert settings.mongodb_database == "webintel_test"


def test_root_endpoint():
    app = create_app(connect_db=False)

    with TestClient(app) as client:
        response = client.get("/")

    assert response.status_code == 200

    data = response.json()

    assert data["api_prefix"] == "/api/v1"
    assert data["documentation"] == "/docs"


def test_liveness_endpoint():
    app = create_app(connect_db=False)

    with TestClient(app) as client:
        response = client.get("/api/v1/health/live")

    assert response.status_code == 200
    assert response.json() == {
        "status": "alive",
        "service": "webintel-ai",
    }


def test_readiness_without_database():
    app = create_app(connect_db=False)

    with TestClient(app) as client:
        response = client.get("/api/v1/health/ready")

    assert response.status_code == 503
    assert response.json() == {
        "detail": "Database not initialized"
    }


def test_repository_dependency_without_database():
    app = create_app(connect_db=False)

    @app.get("/test/repository")
    def repository_probe(
        repository=Depends(get_repository),
    ):
        return {"status": "connected"}

    with TestClient(app) as client:
        response = client.get("/test/repository")

    assert response.status_code == 503
    assert response.json() == {
        "detail": "Database service unavailable"
    }


def test_openapi_documentation():
    app = create_app(connect_db=False)

    with TestClient(app) as client:
        docs_response = client.get("/docs")
        schema_response = client.get("/openapi.json")

    assert docs_response.status_code == 200
    assert schema_response.status_code == 200

    schema = schema_response.json()

    assert "/api/v1/health/live" in schema["paths"]
    assert "/api/v1/health/ready" in schema["paths"]
