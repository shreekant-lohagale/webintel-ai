
import asyncio
import os
from uuid import uuid4

import pytest

from app.embeddings.indexer import (
    DocumentChunkIndexer,
    IndexConfig,
)
from app.retrieval.engine import (
    RetrievalEngine,
    SearchFilters,
)
from app.storage.mongodb import create_client


class FakeProvider:
    """
    Deterministic 3D vectors for testing.

    Avoids loading Sentence Transformers.
    """

    def encode(self, texts):
        results = []

        for text in texts:
            normalized = text.lower()

            if "python" in normalized:
                results.append([1.0, 0.0, 0.0])
            elif "database" in normalized:
                results.append([0.0, 1.0, 0.0])
            else:
                results.append([0.0, 0.0, 1.0])

        return results


def make_document(
    document_id,
    text,
    domain,
    document_type="article",
):
    return {
        "_id": document_id,
        "document_id": document_id,
        "document_type": document_type,
        "title": document_id,
        "content": text,
        "content_hash": document_id + "-hash",
        "source_url": (
            f"https://{domain}/{document_id}"
        ),
        "source_domain": domain,
    }


async def check_retrieval_integration():
    client = create_client()

    database_name = (
        "webintel_retrieval_test_"
        + uuid4().hex
    )

    database = client[database_name]

    config = IndexConfig(
        model_id="fake-model",
        model_revision="test",
        chunk_words=50,
        overlap_words=5,
        dimension=3,
    )

    provider = FakeProvider()

    indexer = DocumentChunkIndexer(
        database=database,
        provider=provider,
        config=config,
    )

    engine = RetrievalEngine(
        database=database,
        provider=provider,
        config=config,
    )

    try:
        await database["documents"].insert_many([
            make_document(
                "python-article",
                "Python programming helps automate workflows.",
                "example.com",
            ),
            make_document(
                "database-article",
                "Database indexing improves query retrieval.",
                "docs.example.com",
            ),
            make_document(
                "python-quote",
                "Python is useful for scripting.",
                "quotes.example.com",
                "quote",
            ),
        ])

        await indexer.ensure_indexes()
        summary = await indexer.index_all()

        assert summary["embedded"] == 3

        semantic = await engine.search(
            "python",
            mode="semantic",
            limit=3,
        )

        assert semantic[0]["document_id"] in {
            "python-article",
            "python-quote",
        }

        assert semantic[0]["semantic_score"] > 0.9

        keyword = await engine.search(
            "database",
            mode="keyword",
        )

        assert keyword[0]["document_id"] == (
            "database-article"
        )

        hybrid = await engine.search(
            "python",
            mode="hybrid",
            limit=3,
            filters=SearchFilters(
                document_type="article",
                source_domain="example.com",
            ),
        )

        assert len(hybrid) == 1

        result = hybrid[0]

        assert result["document_id"] == (
            "python-article"
        )

        assert result["source_url"] == (
            "https://example.com/python-article"
        )

        assert result["citation"]["chunk_id"] == (
            result["chunk_id"]
        )

        assert result["citation"]["source_url"] == (
            result["source_url"]
        )

        assert result["hybrid_score"] > 0

    finally:
        try:
            await client.drop_database(
                database_name
            )
        finally:
            await client.close()


@pytest.mark.skipif(
    os.getenv("WEBINTEL_RUN_MONGO_TESTS") != "1",
    reason="MongoDB integration tests are opt-in",
)
def test_retrieval_integration():
    asyncio.run(check_retrieval_integration())
