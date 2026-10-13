
import asyncio
import os
from uuid import uuid4

import pytest

from app.api.schemas.crawl_jobs import CrawlJobCreate
from app.jobs.repository import CrawlJobRepository
from app.jobs.worker import CrawlJobWorker
from app.storage.mongodb import create_client


pytestmark = pytest.mark.skipif(
    os.getenv("WEBINTEL_RUN_MONGO_TESTS") != "1",
    reason="MongoDB integration tests are opt-in",
)


async def wait_for_status(
    repository,
    job_id,
    expected,
    timeout=8,
):
    loop = asyncio.get_running_loop()
    deadline = loop.time() + timeout

    while loop.time() < deadline:
        job = await repository.get(job_id)

        if job and job.status == expected:
            return job

        await asyncio.sleep(0.05)

    raise AssertionError(
        f"Timed out waiting for {expected}"
    )


async def check_repository_cancel_logic():
    client = create_client()
    database_name = (
        "webintel_cancel_test_" + uuid4().hex
    )

    try:
        repository = CrawlJobRepository(
            client[database_name]
        )

        await repository.ensure_indexes()

        created = await repository.create(
            CrawlJobCreate()
        )

        assert created.status == "queued"

        cancelled = await repository.cancel(
            created.job_id
        )

        assert cancelled.status == "cancelled"
        assert cancelled.finished_at is not None

        # Cancelling again is idempotent.
        again = await repository.cancel(
            created.job_id
        )

        assert again.status == "cancelled"

        # Cancelled jobs cannot be claimed.
        assert await repository.claim_next() is None

        assert not await repository.complete(
            created.job_id,
            {"ok": True},
        )

        assert not await repository.fail(
            created.job_id,
            "Late error",
        )

    finally:
        try:
            await client.drop_database(database_name)
        finally:
            await client.close()


async def check_worker_cancels_running_job():
    client = create_client()
    database_name = (
        "webintel_worker_cancel_test_"
        + uuid4().hex
    )

    was_cancelled = asyncio.Event()

    async def slow_runner(job, name):
        try:
            await asyncio.sleep(60)
            return {"ok": True}
        except asyncio.CancelledError:
            was_cancelled.set()
            raise

    repository = CrawlJobRepository(
        client[database_name]
    )

    worker = CrawlJobWorker(
        repository=repository,
        database_name=database_name,
        runner=slow_runner,
        poll_seconds=0.05,
    )

    try:
        await repository.ensure_indexes()
        await worker.start()

        created = await repository.create(
            CrawlJobCreate()
        )

        worker.notify()

        await wait_for_status(
            repository,
            created.job_id,
            "running",
        )

        cancelled = await repository.cancel(
            created.job_id
        )

        assert cancelled.status == "cancelled"

        await asyncio.wait_for(
            was_cancelled.wait(),
            timeout=5,
        )

        stored = await repository.get(
            created.job_id
        )

        assert stored.status == "cancelled"
        assert stored.result is None

    finally:
        try:
            await worker.stop()
        finally:
            try:
                await client.drop_database(
                    database_name
                )
            finally:
                await client.close()


def test_queued_job_cancellation():
    asyncio.run(check_repository_cancel_logic())


def test_running_job_cancellation():
    asyncio.run(check_worker_cancels_running_job())
