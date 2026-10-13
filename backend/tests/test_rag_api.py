
from fastapi.testclient import TestClient

from app.api.main import create_app
from app.api.routes.ask import get_rag_service
from app.rag.provider import (
    LLMOutputError,
    LLMUnavailableError,
)
from app.rag.schemas import (
    AskRequest,
    AskResponse,
)


class FakeRAGService:
    async def ask(self, request: AskRequest):
        return AskResponse(
            question=request.question,
            status="abstained",
            answer=(
                "I don't have enough reliable evidence "
                "in the indexed sources to answer "
                "that question."
            ),
            claims=[],
            citations=[],
            retrieved_chunks=0,
            model="fake-model",
            abstention_reason=(
                "insufficient_retrieval_evidence"
            ),
        )


class FailingRAGService:
    def __init__(self, exception):
        self.exception = exception

    async def ask(self, request):
        raise self.exception


def test_ask_requires_database():
    app = create_app(connect_db=False)

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/ask",
            json={
                "question": "What is RAG?"
            },
        )

    assert response.status_code == 503


def test_ask_rejects_empty_question():
    app = create_app(connect_db=False)

    app.dependency_overrides[get_rag_service] = (
        lambda: FakeRAGService()
    )

    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/ask",
                json={
                    "question": ""
                },
            )

        assert response.status_code == 422

    finally:
        app.dependency_overrides.clear()


def test_ask_rejects_invalid_top_k():
    app = create_app(connect_db=False)

    app.dependency_overrides[get_rag_service] = (
        lambda: FakeRAGService()
    )

    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/ask",
                json={
                    "question": "What is AI?",
                    "top_k": 100,
                },
            )

        assert response.status_code == 422

    finally:
        app.dependency_overrides.clear()


def test_ask_with_injected_service():
    app = create_app(connect_db=False)

    app.dependency_overrides[get_rag_service] = (
        lambda: FakeRAGService()
    )

    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/ask",
                json={
                    "question": (
                        "What is a reliable pipeline?"
                    )
                },
            )

        assert response.status_code == 200
        assert response.json()["status"] == (
            "abstained"
        )

    finally:
        app.dependency_overrides.clear()


def test_llm_unavailable_returns_503():
    app = create_app(connect_db=False)

    app.dependency_overrides[get_rag_service] = (
        lambda: FailingRAGService(
            LLMUnavailableError()
        )
    )

    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/ask",
                json={"question": "Explain RAG"},
            )

        assert response.status_code == 503

    finally:
        app.dependency_overrides.clear()


def test_invalid_llm_output_returns_502():
    app = create_app(connect_db=False)

    app.dependency_overrides[get_rag_service] = (
        lambda: FailingRAGService(
            LLMOutputError()
        )
    )

    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/ask",
                json={"question": "Explain RAG"},
            )

        assert response.status_code == 502

    finally:
        app.dependency_overrides.clear()


def test_ask_in_openapi():
    app = create_app(connect_db=False)

    with TestClient(app) as client:
        response = client.get(
            "/openapi.json"
        )

    assert response.status_code == 200

    assert (
        "/api/v1/ask"
        in response.json()["paths"]
    )
