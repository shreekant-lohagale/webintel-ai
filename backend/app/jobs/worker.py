
import asyncio
import logging
from pathlib import Path
from typing import Awaitable, Callable

from app.api.schemas.crawl_jobs import CrawlJob
from app.jobs.repository import CrawlJobRepository
from app.pipeline.run import run_pipeline


logger = logging.getLogger("webintel.jobs")

BACKEND_ROOT = Path(__file__).resolve().parents[2]

JobRunner = Callable[
    [CrawlJob, str],
    Awaitable[dict],
]


async def execute_crawl_job(
    job: CrawlJob,
    database_name: str,
) -> dict:
    """
    Execute an approved crawl through the existing
    Scrapy → processing → MongoDB pipeline.
    """

    output_directory = (
        BACKEND_ROOT
        / "data"
        / "processed"
        / "jobs"
        / str(job.job_id)
    )

    report = await run_pipeline(
        start_url=job.start_url,
        browser=job.browser,
        allow_live=False,
        output_directory=output_directory,
        database_name=database_name,
    )

    return report


class CrawlJobWorker:
    def __init__(
        self,
        repository: CrawlJobRepository,
        database_name: str,
        runner: JobRunner = execute_crawl_job,
        poll_seconds: float = 1.0,
    ):
        self.repository = repository
        self.database_name = database_name
        self.runner = runner
        self.poll_seconds = poll_seconds

        self._task: asyncio.Task | None = None
        self._wake = asyncio.Event()

    async def start(self):
        if self._task is not None:
            raise RuntimeError("Worker already started")

        interrupted = (
            await self.repository.recover_interrupted()
        )

        if interrupted:
            logger.warning(
                "Marked %s interrupted jobs as failed",
                interrupted,
            )

        self._task = asyncio.create_task(
            self._run(),
            name="webintel-crawl-worker",
        )

    def notify(self):
        """Wake the worker after a new job is queued."""
        self._wake.set()

    async def stop(self):
        """
        Cancel the in-process worker.

        In-flight subprocess cancellation is not fully
        supervised yet; interrupted jobs are reconciled
        on the next application startup.
        """
        if self._task is None:
            return

        self._task.cancel()

        try:
            await self._task
        except asyncio.CancelledError:
            pass
        finally:
            self._task = None

    async def _run(self):
        while True:
            job = await self.repository.claim_next()

            if job is None:
                self._wake.clear()

                try:
                    await asyncio.wait_for(
                        self._wake.wait(),
                        timeout=self.poll_seconds,
                    )
                except asyncio.TimeoutError:
                    pass

                continue

            logger.info(
                "Starting crawl job %s",
                job.job_id,
            )

            try:
                result = await self.runner(
                    job,
                    self.database_name,
                )

                saved = await self.repository.complete(
                    job.job_id,
                    result,
                )

                if saved:
                    logger.info(
                        "Completed crawl job %s",
                        job.job_id,
                    )

            except asyncio.CancelledError:
                logger.warning(
                    "Worker cancelled during job %s",
                    job.job_id,
                )
                raise

            except Exception as exc:
                logger.exception(
                    "Crawl job %s failed",
                    job.job_id,
                )

                # Return a bounded generic error through API.
                # Detailed tracebacks stay in server logs.
                try:
                    await self.repository.fail(
                        job.job_id,
                        f"{type(exc).__name__}: {str(exc)[:350]}",
                    )
                except Exception:
                    logger.exception(
                        "Could not persist failure state"
                    )
