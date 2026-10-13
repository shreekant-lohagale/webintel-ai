
import os

import pytest
from fastapi.testclient import TestClient

from app.api.config import get_settings
from app.api.main import create_app


pytestmark = pytest.mark.skipif(
    os.getenv("WEBINTEL_RUN_MONGO_TESTS") != "1",
    reason=(
        "Set WEBINTEL_RUN_MONGO_TESTS=1 "
        "to run MongoDB integration tests"
    ),
)


def test_api_mongodb_lifecycle():
    settings = get_settings()

    app = create_app(
        settings=settings,
        connect_db=True,
    )

    # Entering the context triggers FastAPI lifespan.
    with TestClient(app) as client:
        assert app.state.mongodb_client is not None
        assert app.state.mongodb_database is not None
        assert app.state.repository is not None

        response = client.get(
            "/api/v1/health/ready"
        )

        assert response.status_code == 200

        assert response.json() == {
            "status": "ready",
            "database": settings.mongodb_database,
        }

        response = client.get(
            "/api/v1/health/live"
        )

        assert response.status_code == 200

    # Exiting the context triggers lifespan shutdown.
    assert app.state.mongodb_client is None
    assert app.state.mongodb_database is None
    assert app.state.repository is None
