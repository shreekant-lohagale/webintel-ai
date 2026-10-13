
import asyncio
import json
import logging
import os
import signal
import sys
from pathlib import Path
from typing import Awaitable, Callable

from app.api.schemas.crawl_jobs import CrawlJob
from app.jobs.execute_job import RESULT_MARKER
from app.jobs.repository import CrawlJobRepository


logger = logging.getLogger("webintel.jobs")

BACKEND_ROOT = Path(__file__).resolve().parents[2]

JobRunner = Callable[
    [CrawlJob, str],
    Awaitable[dict],
]


async def terminate_process_tree(
    process: asyncio.subprocess.Process,
) -> None:
    """
    Terminate a subprocess and its descendants.

    Intended for a single local worker.
    """

    if process.returncode is not None:
        return

    if os.name == "nt":
        killer = await asyncio.create_subprocess_exec(
            "taskkill",
            "/PID",
            str(process.pid),
            "/T",
            "/F",
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )

        try:
            await asyncio.wait_for(
                killer.wait(),
                timeout=10,
            )
        except asyncio.TimeoutError:
            killer.kill()
            await killer.wait()

    else:
        try:
            os.killpg(
                process.pid,
                signal.SIGKILL,
            )
        except ProcessLookupError:
            pass

    try:
        await asyncio.wait_for(
            process.wait(),
            timeout=10,
        )
    except asyncio.TimeoutError:
        if process.returncode is None:
            process.kill()

        await process.wait()


async def execute_crawl_job(
    job: CrawlJob,
    database_name: str,
) -> dict:
    """
    Execute the pipeline in a supervised subprocess.

    Cancelling this coroutine terminates the child
    process tree rather than abandoning the crawl.
    """

    command = [
        sys.executable,
        "-m",
        "app.jobs.execute_job",
        "--job-id",
        str(job.job_id),
        "--database",
        database_name,
    ]

    if job.browser:
        command.append("--browser")

    kwargs = {}

    if os.name != "nt":
        kwargs["start_new_session"] = True

    process = await asyncio.create_subprocess_exec(
        *command,
        cwd=BACKEND_ROOT,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        **kwargs,
    )

    timeout_seconds = int(
        os.getenv(
            "WEBINTEL_CRAWL_TIMEOUT_SECONDS",
            "120",
        )
    )

    timeout_seconds = max(
        10,
        min(timeout_seconds, 600),
    )

    try:
        stdout, stderr = await asyncio.wait_for(
            process.communicate(),
            timeout=timeout_seconds,
        )

    except asyncio.TimeoutError:
        await terminate_process_tree(process)

        raise RuntimeError(
            "Crawler exceeded execution timeout"
        ) from None

    except asyncio.CancelledError:
        # Shield cleanup against repeated cancellation.
        await asyncio.shield(
            terminate_process_tree(process)
        )
        raise

    if process.returncode != 0:
        logger.error(
            "Crawler subprocess failed: job_id=%s "
            "exit_code=%s",
            job.job_id,
            process.returncode,
        )

        raise RuntimeError(
            "Crawler subprocess failed"
        )

    output = stdout.decode(
        "utf-8",
        errors="replace",
    )

    for line in reversed(output.splitlines()):
        if line.startswith(RESULT_MARKER):
            return json.loads(
                line[len(RESULT_MARKER):]
            )

    raise RuntimeError(
        "Crawler did not return a result report"
    )


class CrawlJobWorker:

    def __init__(
        self,
        repository: CrawlJobRepository,
        database_name: str,
        runner: JobRunner = execute_crawl_job,
        poll_seconds: float = 0.5,
    ):
        self.repository = repository
        self.database_name = database_name
        self.runner = runner
        self.poll_seconds = poll_seconds

        self._task: asyncio.Task | None = None
        self._active_runner: asyncio.Task | None = None
        self._wake = asyncio.Event()

    async def start(self):
        if self._task is not None:
            raise RuntimeError("Worker already started")

        interrupted = (
            await self.repository.recover_interrupted()
        )

        if interrupted:
            logger.warning(
                "Recovered %s interrupted jobs",
                interrupted,
            )

        self._task = asyncio.create_task(
            self._run(),
            name="webintel-crawl-worker",
        )

    def notify(self):
        self._wake.set()

    async def stop(self):
        if self._task is None:
            return

        self._task.cancel()

        try:
            await self._task
        except asyncio.CancelledError:
            pass
        finally:
            self._task = None

    async def _execute(self, job: CrawlJob):
        self._active_runner = asyncio.create_task(
            self.runner(
                job,
                self.database_name,
            )
        )

        try:
            while not self._active_runner.done():
                try:
                    await asyncio.wait_for(
                        asyncio.shield(self._active_runner),
                        timeout=self.poll_seconds,
                    )
                except asyncio.TimeoutError:
                    pass

                if self._active_runner.done():
                    break

                latest = await self.repository.get(
                    job.job_id
                )

                if latest and latest.status == "cancelled":
                    logger.info(
                        "Cancelling running job %s",
                        job.job_id,
                    )

                    self._active_runner.cancel()

                    try:
                        await self._active_runner
                    except asyncio.CancelledError:
                        pass

                    return

            result = await self._active_runner

            saved = await self.repository.complete(
                job.job_id,
                result,
            )

            if saved:
                logger.info(
                    "Completed job %s",
                    job.job_id,
                )

        except asyncio.CancelledError:
            if (
                self._active_runner
                and not self._active_runner.done()
            ):
                self._active_runner.cancel()

                try:
                    await self._active_runner
                except asyncio.CancelledError:
                    pass

            raise

        except Exception:
            logger.exception(
                "Job execution failed: %s",
                job.job_id,
            )

            await self.repository.fail(
                job.job_id,
                "Crawler execution failed",
            )

        finally:
            self._active_runner = None

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

            await self._execute(job)
