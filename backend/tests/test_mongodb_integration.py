
import asyncio
import os
from uuid import uuid4

import pytest

from app.processing.cleaning import sha256_hash
from app.processing.lineage import (
    make_observation,
    make_revision,
)
from app.processing.normalizer import normalize_article
from app.storage.mongodb import create_client
from app.storage.repository import MongoRepository


pytestmark = pytest.mark.skipif(
    os.getenv("WEBINTEL_RUN_MONGO_TESTS") != "1",
    reason="Set WEBINTEL_RUN_MONGO_TESTS=1 to run MongoDB integration tests",
)


def make_article(url, content, timestamp):
    return normalize_article({
        "title": "AI Research",
        "content": content,
        "source_url": url,
        "scraped_at": timestamp,
        "tags": ["AI"],
    })


async def exercise_repository():
    client = create_client()

    # Use a separate database for integration testing.
    database = client["webintel_ai_m3_test"]
    repository = MongoRepository(database)

    suffix = uuid4().hex
    url = f"https://example.com/test/{suffix}"

    first = make_article(
        url,
        "First version of the research article.",
        "2026-10-13T08:00:00+00:00",
    )

    updated = make_article(
        url,
        "Updated version with new research findings.",
        "2026-10-13T09:00:00+00:00",
    )

    # Test sub-millisecond timestamp precision.
    precise = make_article(
        f"https://example.com/test/precision-{suffix}",
        "Timestamp precision regression test.",
        "2026-10-13T10:00:00.123456+00:00",
    )

    document_ids = {
        first.document_id,
        precise.document_id,
    }

    observation_ids = set()
    revision_ids = set()
    link_ids = set()

    try:
        # Verify database connectivity.
        await client.admin.command("ping")
        await repository.ensure_indexes()

        # ==========================================
        # TEST 1: DOCUMENT INSERTION & IDEMPOTENCY
        # ==========================================

        assert await repository.upsert_document(first)

        # Reprocessing the exact same document is a no-op.
        assert not await repository.upsert_document(first)

        # Updated content with a newer timestamp is stored.
        assert await repository.upsert_document(updated)

        # Older crawls cannot overwrite newer versions.
        assert not await repository.upsert_document(first)

        # ==========================================
        # TEST 2: MONGODB TIMESTAMP PRECISION
        # ==========================================

        assert await repository.upsert_document(precise)

        # MongoDB stores milliseconds rather than
        # Python's full microsecond precision.
        #
        # Importing the identical high-precision timestamp
        # must NOT trigger another document update.
        assert not await repository.upsert_document(precise)

        stored_precise = await repository.get_document(
            precise.document_id
        )

        assert stored_precise is not None
        assert stored_precise.content == precise.content

        # Stored timestamp should have millisecond precision.
        assert (
            stored_precise.scraped_at.microsecond
            == 123000
        )

        # ==========================================
        # TEST 3: PROVENANCE & REVISION IDEMPOTENCY
        # ==========================================

        for article in [first, updated]:
            observation = make_observation(article)
            revision = make_revision(article)

            observation_ids.add(
                observation.observation_id
            )
            revision_ids.add(
                revision.revision_id
            )

            # Repeated upserts must not create duplicates.
            await repository.upsert_observation(observation)
            await repository.upsert_observation(observation)

            await repository.upsert_revision(revision)
            await repository.upsert_revision(revision)

        # ==========================================
        # TEST 4: DOCUMENT RETRIEVAL
        # ==========================================

        stored = await repository.get_document(
            first.document_id
        )

        assert stored is not None
        assert stored.document_id == first.document_id
        assert stored.content == updated.content

        sources = await repository.get_sources(
            first.document_id
        )

        revisions = await repository.get_revisions(
            first.document_id
        )

        assert len(sources) == 2
        assert len(revisions) == 2

        assert {
            item.content_hash
            for item in revisions
        } == {
            first.content_hash,
            updated.content_hash,
        }

        # ==========================================
        # TEST 5: SIMILARITY LINK IDEMPOTENCY
        # ==========================================

        other_id = sha256_hash(
            f"other:{suffix}"
        )

        link = {
            "document_id_a": first.document_id,
            "document_id_b": other_id,
            "method": "word_jaccard_3",
            "similarity_score": 0.91,
        }

        first_id, second_id = sorted([
            first.document_id,
            other_id,
        ])

        link_id = sha256_hash(
            f"{first_id}\n{second_id}\nword_jaccard_3"
        )

        link_ids.add(link_id)

        await repository.upsert_similarity_link(link)
        await repository.upsert_similarity_link(link)

        links = await repository.links.find({
            "_id": link_id
        }).to_list(length=10)

        assert len(links) == 1
        assert links[0]["similarity_score"] == 0.91

        # ==========================================
        # TEST 6: DOCUMENT LISTING
        # ==========================================

        listed = await repository.list_documents(
            limit=100
        )

        assert any(
            item.document_id == first.document_id
            for item in listed
        )

        assert any(
            item.document_id == precise.document_id
            for item in listed
        )

        # ==========================================
        # TEST 7: INVALID PAGINATION
        # ==========================================

        with pytest.raises(ValueError):
            await repository.list_documents(limit=0)

        with pytest.raises(ValueError):
            await repository.list_documents(limit=101)

        with pytest.raises(ValueError):
            await repository.list_documents(skip=-1)

    finally:
        # Remove only records created by this test.
        # Do not drop the entire test database.

        try:
            if link_ids:
                await repository.links.delete_many({
                    "_id": {"$in": list(link_ids)}
                })

            if observation_ids:
                await repository.observations.delete_many({
                    "_id": {"$in": list(observation_ids)}
                })

            if revision_ids:
                await repository.revisions.delete_many({
                    "_id": {"$in": list(revision_ids)}
                })

            await repository.documents.delete_many({
                "_id": {"$in": list(document_ids)}
            })

        finally:
            await client.close()


def test_repository_integration():
    asyncio.run(exercise_repository())
