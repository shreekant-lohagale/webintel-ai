
from datetime import datetime, timezone
from typing import Any

from pymongo import ASCENDING, DESCENDING

from app.processing.lineage import (
    DocumentRevision,
    SourceObservation,
)
from app.processing.schemas import WebDocument
from app.processing.cleaning import sha256_hash


def to_bson(model) -> dict[str, Any]:
    """Serialize Pydantic models into MongoDB-compatible data."""

    data = model.model_dump(mode="json")

    for field in (
        "scraped_at",
        "published_at",
        "first_seen_at",
        "last_seen_at",
        "observed_at",
    ):
        if data.get(field) is not None:
            data[field] = datetime.fromisoformat(
                data[field].replace("Z", "+00:00")
            )

    return data


def mongo_precision(dt: datetime) -> datetime:
    """Normalize datetime to MongoDB's millisecond precision."""

    if dt.tzinfo is None or dt.utcoffset() is None:
        dt = dt.replace(tzinfo=timezone.utc)

    dt = dt.astimezone(timezone.utc)

    return dt.replace(
        microsecond=(dt.microsecond // 1000) * 1000
    )


class MongoRepository:

    def __init__(self, database):
        self.db = database
        self.documents = database["documents"]
        self.observations = database["source_observations"]
        self.revisions = database["document_revisions"]
        self.links = database["similarity_links"]

    async def ensure_indexes(self) -> None:
        """Create indexes for efficient queries."""

        await self.documents.create_index(
            [("source_domain", ASCENDING)]
        )

        await self.documents.create_index(
            [
                ("document_type", ASCENDING),
                ("scraped_at", DESCENDING),
            ]
        )

        await self.documents.create_index(
            [("content_hash", ASCENDING)]
        )

        await self.observations.create_index(
            [
                ("document_id", ASCENDING),
                ("last_seen_at", DESCENDING),
            ]
        )

        await self.revisions.create_index(
            [
                ("document_id", ASCENDING),
                ("observed_at", DESCENDING),
            ]
        )

        await self.links.create_index(
            [("document_id_a", ASCENDING)]
        )

        await self.links.create_index(
            [("document_id_b", ASCENDING)]
        )

    async def upsert_document(
        self,
        document: WebDocument,
    ) -> bool:
        """
        Insert or update the latest document.

        MongoDB stores datetime values with millisecond precision.

        Returns:
            True  - document inserted or updated
            False - existing document is same age or newer
        """

        data = to_bson(document)
        data["_id"] = document.document_id

        incoming_timestamp = mongo_precision(
            document.scraped_at
        )

        data["scraped_at"] = incoming_timestamp

        previous = await self.documents.find_one(
            {"_id": document.document_id},
            {"scraped_at": 1},
        )

        if previous is not None:
            stored_timestamp = mongo_precision(
                previous["scraped_at"]
            )

            if stored_timestamp >= incoming_timestamp:
                return False

        await self.documents.replace_one(
            {"_id": document.document_id},
            data,
            upsert=True,
        )

        return True

    async def upsert_observation(
        self,
        observation: SourceObservation,
    ) -> None:
        """Preserve source provenance and observation time range."""

        data = to_bson(observation)

        data["_id"] = observation.observation_id

        first_seen = data.pop("first_seen_at")
        last_seen = data.pop("last_seen_at")

        await self.observations.update_one(
            {"_id": observation.observation_id},
            {
                "$setOnInsert": data,
                "$min": {
                    "first_seen_at": first_seen
                },
                "$max": {
                    "last_seen_at": last_seen
                },
            },
            upsert=True,
        )

    async def upsert_revision(
        self,
        revision: DocumentRevision,
    ) -> None:
        """Insert an immutable revision only once."""

        data = to_bson(revision)

        data["_id"] = revision.revision_id

        await self.revisions.update_one(
            {"_id": revision.revision_id},
            {
                "$setOnInsert": data
            },
            upsert=True,
        )

    async def upsert_similarity_link(
        self,
        link: dict,
    ) -> None:
        """Upsert a deterministic near-duplicate relationship."""

        first, second = sorted([
            link["document_id_a"],
            link["document_id_b"],
        ])

        if first == second:
            raise ValueError(
                "Similarity links require two different documents"
            )

        method = link["method"]
        score = float(link["similarity_score"])

        if not 0.0 <= score <= 1.0:
            raise ValueError(
                "similarity_score must be between 0 and 1"
            )

        link_id = sha256_hash(
            f"{first}\n{second}\n{method}"
        )

        data = {
            "_id": link_id,
            "document_id_a": first,
            "document_id_b": second,
            "method": method,
            "similarity_score": score,
        }

        await self.links.update_one(
            {"_id": link_id},
            {"$set": data},
            upsert=True,
        )

    async def get_document(
        self,
        document_id: str,
    ) -> WebDocument | None:
        """Retrieve one document by its stable ID."""

        record = await self.documents.find_one(
            {"_id": document_id}
        )

        if record is None:
            return None

        record.pop("_id", None)

        return WebDocument.model_validate(record)

    async def list_documents(
        self,
        limit: int = 20,
        skip: int = 0,
    ) -> list[WebDocument]:
        """List current documents with pagination."""

        if not 1 <= limit <= 100:
            raise ValueError(
                "limit must be between 1 and 100"
            )

        if skip < 0:
            raise ValueError(
                "skip cannot be negative"
            )

        cursor = (
            self.documents.find()
            .sort([
                ("scraped_at", DESCENDING),
                ("_id", ASCENDING),
            ])
            .skip(skip)
            .limit(limit)
        )

        records = await cursor.to_list(
            length=limit
        )

        for record in records:
            record.pop("_id", None)

        return [
            WebDocument.model_validate(record)
            for record in records
        ]

    async def search_documents(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        document_type: str | None = None,
        source_domain: str | None = None,
        tag: str | None = None,
        q: str | None = None,
    ) -> tuple[list[WebDocument], int]:
        """
        Search and paginate current documents.

        Returns:
            (documents, total_matching_documents)
        """
        import re

        if page < 1:
            raise ValueError("page must be at least 1")

        if not 1 <= page_size <= 100:
            raise ValueError(
                "page_size must be between 1 and 100"
            )

        filters: dict = {}

        if document_type:
            filters["document_type"] = document_type

        if source_domain:
            filters["source_domain"] = (
                source_domain.lower()
            )

        if tag:
            filters["tags"] = {
                "$regex": f"^{re.escape(tag)}$",
                "$options": "i",
            }

        if q:
            search_pattern = re.escape(q.strip())

            if search_pattern:
                filters["$or"] = [
                    {
                        "title": {
                            "$regex": search_pattern,
                            "$options": "i",
                        }
                    },
                    {
                        "content": {
                            "$regex": search_pattern,
                            "$options": "i",
                        }
                    },
                ]

        total = await self.documents.count_documents(
            filters
        )

        skip = (page - 1) * page_size

        cursor = (
            self.documents.find(filters)
            .sort([
                ("scraped_at", DESCENDING),
                ("_id", ASCENDING),
            ])
            .skip(skip)
            .limit(page_size)
        )

        records = await cursor.to_list(
            length=page_size
        )

        items = []

        for record in records:
            record.pop("_id", None)

            items.append(
                WebDocument.model_validate(record)
            )

        return items, total

    async def get_document_overview(
        self,
        document_id: str,
    ) -> dict | None:
        """
        Retrieve a document with provenance and
        revision counts.
        """

        document = await self.get_document(
            document_id
        )

        if document is None:
            return None

        source_count = (
            await self.observations.count_documents({
                "document_id": document_id
            })
        )

        revision_count = (
            await self.revisions.count_documents({
                "document_id": document_id
            })
        )

        return {
            "document": document,
            "source_count": source_count,
            "revision_count": revision_count,
        }

    async def get_sources(
        self,
        document_id: str,
    ) -> list[SourceObservation]:
        """Retrieve provenance records for a document."""

        cursor = self.observations.find(
            {"document_id": document_id}
        ).sort(
            "first_seen_at",
            ASCENDING,
        )

        records = await cursor.to_list(
            length=None
        )

        for record in records:
            record.pop("_id", None)

        return [
            SourceObservation.model_validate(record)
            for record in records
        ]

    async def get_revisions(
        self,
        document_id: str,
    ) -> list[DocumentRevision]:
        """Retrieve historical document versions."""

        cursor = self.revisions.find(
            {"document_id": document_id}
        ).sort(
            "observed_at",
            DESCENDING,
        )

        records = await cursor.to_list(
            length=None
        )

        for record in records:
            record.pop("_id", None)

        return [
            DocumentRevision.model_validate(record)
            for record in records
        ]

    async def counts(self) -> dict:
        """Return collection document counts."""

        return {
            "documents":
                await self.documents.count_documents({}),

            "source_observations":
                await self.observations.count_documents({}),

            "document_revisions":
                await self.revisions.count_documents({}),

            "similarity_links":
                await self.links.count_documents({}),
        }
