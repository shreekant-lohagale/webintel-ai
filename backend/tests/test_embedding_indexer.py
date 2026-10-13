
import asyncio
import hashlib
import os
from uuid import uuid4

import pytest

from app.embeddings.indexer import (
    DocumentChunkIndexer,
    IndexConfig,
)
from app.embeddings.model import (
    validate_vectors,
)
from app.storage.mongodb import create_client


class FakeEmbeddingProvider:
    def __init__(self, dimension=8):
        self.dimension = dimension
        self.total_texts = 0

    def encode(self, texts):
        self.total_texts += len(texts)

        results = []

        for text in texts:
            digest = hashlib.sha256(
                text.encode("utf-8")
            ).digest()

            results.append([
                (digest[i] / 255.0)
                for i in range(self.dimension)
            ])

        return results


def sample_document(
    content: str,
    content_hash: str,
):
    return {
        "_id": "sample-document",
        "document_id": "sample-document",
        "document_type": "article",
        "title": "WebIntel AI Test",
        "content": content,
        "content_hash": content_hash,
        "source_url": (
            "https://example.com/article"
        ),
        "source_domain": "example.com",
    }


def test_config_key_is_stable():
    config = IndexConfig(
        model_id="fake-model",
        model_revision="test-1",
        chunk_words=5,
        overlap_words=1,
        dimension=8,
    )

    assert config.key == config.key


def test_changed_config_changes_key():
    first = IndexConfig(
        model_id="fake-model",
        model_revision="test-1",
        dimension=8,
    )

    second = IndexConfig(
        model_id="fake-model",
        model_revision="test-2",
        dimension=8,
    )

    assert first.key != second.key


def test_invalid_embedding_dimension():
    with pytest.raises(ValueError):
        validate_vectors(
            [[0.1, 0.2]],
            expected_count=1,
            dimension=8,
        )


async def check_incremental_indexing():
    client = create_client()

    database_name = (
        "webintel_embedding_test_"
        + uuid4().hex
    )

    database = client[database_name]

    provider = FakeEmbeddingProvider(
        dimension=8
    )

    config = IndexConfig(
        model_id="fake-model",
        model_revision="test-1",
        chunk_words=5,
        overlap_words=1,
        dimension=8,
    )

    indexer = DocumentChunkIndexer(
        database=database,
        provider=provider,
        config=config,
        batch_size=2,
    )

    first_document = sample_document(
        content=(
            "web intelligence systems collect "
            "and process reliable public information"
        ),
        content_hash="revision-1",
    )

    try:
        await database["documents"].insert_one(
            first_document
        )

        await indexer.ensure_indexes()

        first = await indexer.index_all()

        assert first["documents"] == 1
        assert first["embedded"] > 0
        assert first["reused"] == 0

        first_embeddings = (
            provider.total_texts
        )

        # Unchanged run must reuse all embeddings.
        second = await indexer.index_all()

        assert second["embedded"] == 0
        assert second["reused"] == first["chunks"]

        assert (
            provider.total_texts
            == first_embeddings
        )

        # New content hash creates a new revision.
        updated_content = (
            "updated intelligence systems now "
            "include validated sources and "
            "evidence grounded analysis"
        )

        await database["documents"].update_one(
            {"_id": "sample-document"},
            {
                "$set": {
                    "content": updated_content,
                    "content_hash": "revision-2",
                }
            },
        )

        third = await indexer.index_all()

        assert third["embedded"] > 0
        assert third["deleted"] > 0

        current = await database[
            "document_chunks"
        ].find({
            "document_id": "sample-document",
            "config_key": config.key,
        }).to_list(length=None)

        assert len(current) == third["chunks"]

        assert all(
            item["content_hash"] == "revision-2"
            for item in current
        )

        # The current document remains unchanged by
        # embedding indexing.
        source = await database[
            "documents"
        ].find_one({
            "_id": "sample-document"
        })

        assert source["content"] == updated_content

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
def test_incremental_mongodb_indexing():
    asyncio.run(check_incremental_indexing())
