
from collections import Counter
from datetime import datetime, timezone
from typing import Any

from app.intelligence.changes import compare_revisions


def to_iso(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    return value


class IntelligenceService:
    def __init__(self, database):
        self.documents = database["documents"]
        self.revisions = database["document_revisions"]
        self.observations = database[
            "source_observations"
        ]

    async def document_exists(
        self,
        document_id: str,
    ) -> bool:
        record = await self.documents.find_one(
            {"document_id": document_id},
            {"_id": 1},
        )
        return record is not None

    async def load_revisions(
        self,
        document_id: str,
        max_revisions: int = 200,
    ) -> list[dict]:
        if not 2 <= max_revisions <= 200:
            raise ValueError(
                "max_revisions must be 2 to 200"
            )

        records = await (
            self.revisions.find({
                "document_id": document_id
            })
            .sort([
                ("observed_at", 1),
                ("revision_id", 1),
            ])
            .limit(max_revisions + 1)
            .to_list(length=max_revisions + 1)
        )

        if len(records) > max_revisions:
            raise ValueError(
                "Revision limit exceeded; "
                "use a smaller scoped dataset"
            )

        return records

    async def compare(
        self,
        document_id: str,
        from_revision_id: str | None = None,
        to_revision_id: str | None = None,
    ) -> dict | None:
        if not await self.document_exists(document_id):
            return None

        if (from_revision_id is None) != (
            to_revision_id is None
        ):
            raise ValueError(
                "Provide both revision IDs or neither"
            )

        if from_revision_id is not None:
            versions = await (
                self.revisions.find({
                    "document_id": document_id,
                    "revision_id": {
                        "$in": [
                            from_revision_id,
                            to_revision_id,
                        ]
                    },
                })
                .to_list(length=3)
            )

            indexed = {
                item["revision_id"]: item
                for item in versions
            }

            if (
                from_revision_id not in indexed
                or to_revision_id not in indexed
            ):
                raise LookupError(
                    "Revision not found"
                )

            before = indexed[from_revision_id]
            after = indexed[to_revision_id]

        else:
            versions = await (
                self.revisions.find({
                    "document_id": document_id
                })
                .sort([
                    ("observed_at", -1),
                    ("revision_id", -1),
                ])
                .limit(2)
                .to_list(length=2)
            )

            if len(versions) < 2:
                raise LookupError(
                    "At least two revisions are required"
                )

            after, before = versions

        result = compare_revisions(before, after)

        result["from_observed_at"] = to_iso(
            result["from_observed_at"]
        )
        result["to_observed_at"] = to_iso(
            result["to_observed_at"]
        )

        return result

    async def timeline(
        self,
        document_id: str,
        max_revisions: int = 200,
    ) -> dict | None:
        if not await self.document_exists(document_id):
            return None

        versions = await self.load_revisions(
            document_id,
            max_revisions=max_revisions,
        )

        history = []

        for before, after in zip(
            versions,
            versions[1:],
        ):
            comparison = compare_revisions(
                before,
                after,
                max_changes=5,
            )

            history.append({
                "from_revision_id": (
                    before["revision_id"]
                ),
                "to_revision_id": (
                    after["revision_id"]
                ),
                "observed_at": to_iso(
                    after["observed_at"]
                ),
                "title_changed": comparison[
                    "title_changed"
                ],
                "content_changed": comparison[
                    "content_changed"
                ],
                "added_words": comparison[
                    "added_words"
                ],
                "removed_words": comparison[
                    "removed_words"
                ],
                "similarity_ratio": comparison[
                    "similarity_ratio"
                ],
                "change_summary": comparison[
                    "change_summary"
                ],
            })

        return {
            "document_id": document_id,
            "revision_count": len(versions),
            "change_count": len(history),
            "history": history,
        }

    async def overview(self) -> dict:
        document_count = await (
            self.documents.count_documents({})
        )

        revision_count = await (
            self.revisions.count_documents({})
        )

        observation_count = await (
            self.observations.count_documents({})
        )

        domains = await self.documents.distinct(
            "source_domain"
        )

        cursor = await self.documents.aggregate([
            {
                "$group": {
                    "_id": "$document_type",
                    "count": {"$sum": 1},
                }
            },
            {"$sort": {"_id": 1}},
        ])
        by_type = await cursor.to_list(length=None)

        return {
            "document_count": document_count,
            "revision_count": revision_count,
            "source_observation_count": (
                observation_count
            ),
            "source_domain_count": len(
                [x for x in domains if x]
            ),
            "documents_by_type": {
                str(item["_id"]): item["count"]
                for item in by_type
            },
        }

    async def source_statistics(
        self,
        limit: int = 20,
    ) -> dict:
        if not 1 <= limit <= 100:
            raise ValueError(
                "limit must be between 1 and 100"
            )

        pipeline = [
            {
                "$group": {
                    "_id": "$source_domain",
                    "document_count": {
                        "$sum": 1
                    },
                    "article_count": {
                        "$sum": {
                            "$cond": [
                                {
                                    "$eq": [
                                        "$document_type",
                                        "article",
                                    ]
                                },
                                1,
                                0,
                            ]
                        }
                    },
                    "quote_count": {
                        "$sum": {
                            "$cond": [
                                {
                                    "$eq": [
                                        "$document_type",
                                        "quote",
                                    ]
                                },
                                1,
                                0,
                            ]
                        }
                    },
                }
            },
            {
                "$sort": {
                    "document_count": -1,
                    "_id": 1,
                }
            },
            {"$limit": limit},
        ]

        cursor = await self.documents.aggregate(pipeline)
        groups = await cursor.to_list(
            length=limit
        )

        return {
            "items": [
                {
                    "source_domain": (
                        group["_id"] or "unknown"
                    ),
                    "document_count": group[
                        "document_count"
                    ],
                    "article_count": group[
                        "article_count"
                    ],
                    "quote_count": group[
                        "quote_count"
                    ],
                }
                for group in groups
            ],
            "returned_count": len(groups),
            "limit": limit,
        }
