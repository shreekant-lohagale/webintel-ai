
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_repository
from app.api.main import create_app
from app.processing.lineage import (
    make_observation,
    make_revision,
)
from app.processing.normalizer import normalize_article


STAMP = "2026-10-13T08:00:00+00:00"


def article(slug, title, content, tags):
    return normalize_article({
        "title": title,
        "content": content,
        "source_url": f"https://example.com/{slug}",
        "author": "Test Editor",
        "tags": tags,
        "scraped_at": STAMP,
    })


ARTICLES = [
    article(
        "ai",
        "AI Engineering",
        "Building reliable AI workflows.",
        ["AI", "Python"],
    ),
    article(
        "data",
        "Data Pipelines",
        "Building data processing systems.",
        ["Data", "Python"],
    ),
    article(
        "web",
        "Web Crawling",
        "Scrapy extracts public information.",
        ["Scrapy"],
    ),
]


class FakeRepository:

    async def search_documents(
        self,
        *,
        page=1,
        page_size=20,
        document_type=None,
        source_domain=None,
        tag=None,
        q=None,
    ):
        records = ARTICLES.copy()

        if document_type:
            records = [
                doc for doc in records
                if doc.document_type == document_type
            ]

        if source_domain:
            records = [
                doc for doc in records
                if doc.source_domain.lower()
                == source_domain.lower()
            ]

        if tag:
            records = [
                doc for doc in records
                if tag.casefold() in {
                    value.casefold()
                    for value in doc.tags
                }
            ]

        if q:
            term = q.strip().casefold()
            records = [
                doc for doc in records
                if term in doc.title.casefold()
                or term in doc.content.casefold()
            ]

        total = len(records)

        start = (page - 1) * page_size

        return records[start:start + page_size], total

    async def get_document(self, document_id):
        return next(
            (
                doc for doc in ARTICLES
                if doc.document_id == document_id
            ),
            None,
        )

    async def get_sources(self, document_id):
        document = await self.get_document(
            document_id
        )

        return (
            [make_observation(document)]
            if document
            else []
        )

    async def get_revisions(self, document_id):
        document = await self.get_document(
            document_id
        )

        return (
            [make_revision(document)]
            if document
            else []
        )


@pytest.fixture
def client():
    app = create_app(connect_db=False)

    app.dependency_overrides[get_repository] = (
        lambda: FakeRepository()
    )

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def test_document_listing(client):
    response = client.get("/api/v1/documents")

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 3
    assert len(data["items"]) == 3
    assert data["page"] == 1
    assert data["page_size"] == 20
    assert data["total_pages"] == 1
    assert data["has_next"] is False


def test_document_pagination(client):
    response = client.get(
        "/api/v1/documents",
        params={
            "page": 1,
            "page_size": 2,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 3
    assert data["total_pages"] == 2
    assert len(data["items"]) == 2
    assert data["has_next"] is True

    second = client.get(
        "/api/v1/documents",
        params={
            "page": 2,
            "page_size": 2,
        },
    ).json()

    assert len(second["items"]) == 1
    assert second["has_previous"] is True


def test_document_filtering(client):
    response = client.get(
        "/api/v1/documents",
        params={
            "document_type": "article",
            "source_domain": "example.com",
            "tag": "python",
            "q": "building",
        },
    )

    assert response.status_code == 200
    assert response.json()["total"] == 2


def test_empty_search(client):
    response = client.get(
        "/api/v1/documents",
        params={"q": "not-present-anywhere"},
    )

    assert response.status_code == 200
    assert response.json()["total"] == 0
    assert response.json()["items"] == []


def test_document_detail(client):
    document = ARTICLES[0]

    response = client.get(
        f"/api/v1/documents/{document.document_id}"
    )

    assert response.status_code == 200
    assert response.json()["document_id"] == (
        document.document_id
    )


def test_document_sources(client):
    document = ARTICLES[0]

    response = client.get(
        f"/api/v1/documents/{document.document_id}/sources"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert data["items"][0]["document_id"] == (
        document.document_id
    )


def test_document_revisions(client):
    document = ARTICLES[0]

    response = client.get(
        f"/api/v1/documents/{document.document_id}/revisions"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert data["items"][0]["content_hash"] == (
        document.content_hash
    )


def test_missing_document(client):
    missing_id = "a" * 64

    for suffix in (
        "",
        "/sources",
        "/revisions",
    ):
        response = client.get(
            f"/api/v1/documents/{missing_id}{suffix}"
        )

        assert response.status_code == 404
        assert response.json()["detail"] == (
            "Document not found"
        )


def test_invalid_parameters(client):
    invalid_queries = [
        {"page": 0},
        {"page_size": 0},
        {"page_size": 101},
        {"document_type": "invalid"},
    ]

    for params in invalid_queries:
        response = client.get(
            "/api/v1/documents",
            params=params,
        )

        assert response.status_code == 422

    response = client.get(
        "/api/v1/documents/not-a-valid-document-id"
    )

    assert response.status_code == 422


def test_document_openapi(client):
    response = client.get("/openapi.json")

    assert response.status_code == 200

    paths = response.json()["paths"]

    assert "/api/v1/documents" in paths
    assert "/api/v1/documents/{document_id}" in paths
    assert (
        "/api/v1/documents/{document_id}/sources"
        in paths
    )
    assert (
        "/api/v1/documents/{document_id}/revisions"
        in paths
    )
