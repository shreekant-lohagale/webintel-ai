
import os
import time
from dataclasses import replace
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.api.config import get_settings
from app.api.main import create_app
from app.storage.mongodb import create_client


pytestmark = pytest.mark.skipif(
    os.getenv("WEBINTEL_RUN_MONGO_TESTS") != "1",
    reason="MongoDB integration tests are opt-in",
)


async def fake_crawler(job, database_name):
    if job.browser:
        raise RuntimeError("Simulated crawler failure")

    return {
        "database": database_name,
        "crawled_articles": 2,
        "mode": "test",
    }


def wait_for_job(client, job_id, expected, timeout=10):
    deadline = time.monotonic() + timeout

    while time.monotonic() < deadline:
        response = client.get(
            f"/api/v1/crawl/jobs/{job_id}"
        )

        assert response.status_code == 200

        job = response.json()

        if job["status"] == expected:
            return job

        if job["status"] in ("completed", "failed"):
            pytest.fail(
                f"Unexpected final state: {job}"
            )

        time.sleep(0.1)

    pytest.fail(
        f"Timed out waiting for status {expected}"
    )


def test_crawl_job_lifecycle():
    database_name = (
        "webintel_ai_jobs_test_"
        + uuid4().hex
    )

    settings = replace(
        get_settings(),
        mongodb_database=database_name,
    )

    app = create_app(
        settings=settings,
        connect_db=True,
        job_runner=fake_crawler,
    )

    # This test database has a unique generated name.
    # It never reuses the development database.
    try:
        with TestClient(app) as client:
            payload = {
                "start_url":
                    "http://127.0.0.1:8766/",
                "browser": False,
            }

            submitted = client.post(
                "/api/v1/crawl/jobs",
                json=payload,
            )

            assert submitted.status_code == 202

            created = submitted.json()
            job_id = created["job_id"]

            assert created["status"] in (
                "queued",
                "running",
                "completed",
            )

            completed = wait_for_job(
                client,
                job_id,
                "completed",
            )

            assert (
                completed["result"]["crawled_articles"]
                == 2
            )
            assert completed["error"] is None
            assert completed["started_at"] is not None
            assert completed["finished_at"] is not None

            listed = client.get(
                "/api/v1/crawl/jobs",
                params={"limit": 10},
            )

            assert listed.status_code == 200
            assert listed.json()["total"] >= 1

            invalid = client.post(
                "/api/v1/crawl/jobs",
                json={
                    "start_url":
                        "https://example.com/",
                },
            )

            assert invalid.status_code == 422

            # Trigger a controlled worker failure.
            failed_submission = client.post(
                "/api/v1/crawl/jobs",
                json={
                    "start_url":
                        "http://127.0.0.1:8766/",
                    "browser": True,
                },
            )

            assert failed_submission.status_code == 202

            failed = wait_for_job(
                client,
                failed_submission.json()["job_id"],
                "failed",
            )

            assert "Simulated crawler failure" in (
                failed["error"]
            )

            missing = client.get(
                "/api/v1/crawl/jobs/"
                + str(uuid4())
            )

            assert missing.status_code == 404

            malformed = client.get(
                "/api/v1/crawl/jobs/not-a-uuid"
            )

            assert malformed.status_code == 422

            assert client.get(
                "/api/v1/health/live"
            ).status_code == 200

    finally:
        # Always clean up the generated test database.
        import asyncio

        async def cleanup():
            mongo_client = create_client(
                settings.mongodb_uri
            )

            try:
                await mongo_client.drop_database(
                    database_name
                )
            finally:
                await mongo_client.close()

        asyncio.run(cleanup())
