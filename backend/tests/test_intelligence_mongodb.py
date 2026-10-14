
import asyncio
import os
from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.intelligence.service import IntelligenceService
from app.storage.mongodb import create_client


DOC_ID = "a" * 64
REV1 = "1" * 64
REV2 = "2" * 64


def timestamp(hour):
    return datetime(
        2026, 10, 14, hour,
        tzinfo=timezone.utc,
    )


async def run_integration():
    client = create_client()

    database_name = (
        "webintel_intelligence_test_"
        + uuid4().hex
    )

    db = client[database_name]
    service = IntelligenceService(db)

    try:
        await db["documents"].insert_one({
            "_id": DOC_ID,
            "document_id": DOC_ID,
            "document_type": "article",
            "title": "AI Report",
            "source_domain": "example.com",
            "content_hash": "hash-v2",
        })

        await db["document_revisions"].insert_many([
            {
                "_id": REV1,
                "revision_id": REV1,
                "document_id": DOC_ID,
                "title": "AI Report",
                "content": (
                    "AI systems process data."
                ),
                "content_hash": "hash-v1",
                "observed_at": timestamp(8),
            },
            {
                "_id": REV2,
                "revision_id": REV2,
                "document_id": DOC_ID,
                "title": "Updated AI Report",
                "content": (
                    "AI systems process data "
                    "using automation."
                ),
                "content_hash": "hash-v2",
                "observed_at": timestamp(9),
            },
        ])

        await db["source_observations"].insert_one({
            "_id": "observation1",
            "observation_id": "observation1",
            "document_id": DOC_ID,
            "source_url": (
                "https://example.com/report"
            ),
            "extraction_method": "scrapy",
            "content_hash": "hash-v2",
            "first_seen_at": timestamp(8),
            "last_seen_at": timestamp(9),
        })

        before = {
            "documents": await db[
                "documents"
            ].count_documents({}),
            "revisions": await db[
                "document_revisions"
            ].count_documents({}),
            "observations": await db[
                "source_observations"
            ].count_documents({}),
        }

        comparison = await service.compare(DOC_ID)

        assert comparison is not None
        assert comparison["content_changed"]
        assert comparison["title_changed"]
        assert comparison["added_words"] == 2
        assert comparison["removed_words"] == 0
        assert comparison["from_revision_id"] == REV1
        assert comparison["to_revision_id"] == REV2

        timeline = await service.timeline(DOC_ID)

        assert timeline["revision_count"] == 2
        assert timeline["change_count"] == 1

        overview = await service.overview()

        assert overview["document_count"] == 1
        assert overview["revision_count"] == 2
        assert (
            overview["source_observation_count"]
            == 1
        )

        sources = await service.source_statistics()

        assert sources["returned_count"] == 1
        assert sources["items"][0][
            "source_domain"
        ] == "example.com"

        after = {
            "documents": await db[
                "documents"
            ].count_documents({}),
            "revisions": await db[
                "document_revisions"
            ].count_documents({}),
            "observations": await db[
                "source_observations"
            ].count_documents({}),
        }

        assert before == after

        assert await db[
            "document_revisions"
        ].find_one({"_id": REV1}) is not None

        assert await db[
            "document_revisions"
        ].find_one({"_id": REV2}) is not None

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
def test_intelligence_mongodb_integration():
    asyncio.run(run_integration())
