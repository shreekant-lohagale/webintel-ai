
from datetime import datetime, timezone
from uuid import UUID, uuid4

from pymongo import ASCENDING, DESCENDING, ReturnDocument

from app.api.schemas.crawl_jobs import (
    CrawlJob,
    CrawlJobCreate,
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class CrawlJobRepository:
    def __init__(self, database):
        self.collection = database["crawl_jobs"]

    async def ensure_indexes(self):
        await self.collection.create_index(
            [
                ("status", ASCENDING),
                ("created_at", ASCENDING),
            ]
        )

        await self.collection.create_index(
            [("created_at", DESCENDING)]
        )

    @staticmethod
    def decode(record) -> CrawlJob | None:
        if record is None:
            return None

        data = dict(record)
        data["job_id"] = data.pop("_id")
        return CrawlJob.model_validate(data)

    async def create(
        self,
        request: CrawlJobCreate,
    ) -> CrawlJob:
        job_id = str(uuid4())

        record = {
            "_id": job_id,
            "start_url": request.start_url,
            "browser": request.browser,
            "status": "queued",
            "created_at": utc_now(),
            "started_at": None,
            "finished_at": None,
            "error": None,
            "result": None,
        }

        await self.collection.insert_one(record)
        return self.decode(record)

    async def get(
        self,
        job_id: UUID | str,
    ) -> CrawlJob | None:
        record = await self.collection.find_one(
            {"_id": str(job_id)}
        )

        return self.decode(record)

    async def list_jobs(
        self,
        limit: int = 20,
        skip: int = 0,
    ) -> tuple[list[CrawlJob], int]:
        if not 1 <= limit <= 100:
            raise ValueError("limit must be between 1 and 100")

        if skip < 0:
            raise ValueError("skip cannot be negative")

        total = await self.collection.count_documents({})

        cursor = (
            self.collection.find()
            .sort([
                ("created_at", DESCENDING),
                ("_id", DESCENDING),
            ])
            .skip(skip)
            .limit(limit)
        )

        records = await cursor.to_list(length=limit)

        return [
            self.decode(record)
            for record in records
        ], total

    async def claim_next(self) -> CrawlJob | None:
        """
        Atomically claim one queued job.

        A job cannot be claimed twice concurrently.
        """

        record = await self.collection.find_one_and_update(
            {"status": "queued"},
            {
                "$set": {
                    "status": "running",
                    "started_at": utc_now(),
                    "finished_at": None,
                    "error": None,
                }
            },
            sort=[
                ("created_at", ASCENDING),
                ("_id", ASCENDING),
            ],
            return_document=ReturnDocument.AFTER,
        )

        return self.decode(record)

    async def complete(
        self,
        job_id: UUID | str,
        result: dict,
    ) -> bool:
        updated = await self.collection.update_one(
            {
                "_id": str(job_id),
                "status": "running",
            },
            {
                "$set": {
                    "status": "completed",
                    "finished_at": utc_now(),
                    "result": result,
                    "error": None,
                }
            },
        )

        return updated.modified_count == 1

    async def fail(
        self,
        job_id: UUID | str,
        error: str,
    ) -> bool:
        updated = await self.collection.update_one(
            {
                "_id": str(job_id),
                "status": "running",
            },
            {
                "$set": {
                    "status": "failed",
                    "finished_at": utc_now(),
                    "error": error[:500],
                    "result": None,
                }
            },
        )

        return updated.modified_count == 1

    async def recover_interrupted(self) -> int:
        """
        Mark jobs left running by a previous process as failed.

        This is appropriate for the single-process local
        worker. A distributed deployment requires leases.
        """

        updated = await self.collection.update_many(
            {"status": "running"},
            {
                "$set": {
                    "status": "failed",
                    "finished_at": utc_now(),
                    "error": (
                        "Execution interrupted by server restart"
                    ),
                    "result": None,
                }
            },
        )

        return updated.modified_count
