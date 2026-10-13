
import os
from typing import Annotated
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Request,
    status,
)

from app.api.schemas.crawl_jobs import (
    CrawlJob,
    CrawlJobCreate,
    CrawlJobListResponse,
)
from app.api.security import require_api_key
from app.jobs.repository import CrawlJobRepository
from app.pipeline.run import validate_start_url


router = APIRouter(
    prefix="/crawl/jobs",
    tags=["Crawl Jobs"],
)


def get_jobs_repository(
    request: Request,
) -> CrawlJobRepository:
    repository = getattr(
        request.app.state,
        "jobs_repository",
        None,
    )

    if repository is None:
        raise HTTPException(
            status_code=503,
            detail="Crawl job service unavailable",
        )

    return repository


@router.post(
    "",
    response_model=CrawlJob,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Submit a crawl job",
)
async def submit_crawl_job(
    payload: CrawlJobCreate,
    request: Request,
    identity: Annotated[
        str,
        Depends(require_api_key),
    ],
):
    try:
        mode = validate_start_url(
            payload.start_url,
            allow_live=False,
        )

        if mode != "local":
            raise ValueError("Disallowed crawl source")

    except (ValueError, TypeError):
        raise HTTPException(
            status_code=422,
            detail=(
                "Only http://127.0.0.1:8766/ "
                "is permitted for crawl jobs"
            ),
        ) from None

    repository = get_jobs_repository(request)

    worker = getattr(
        request.app.state,
        "crawl_worker",
        None,
    )

    if worker is None:
        raise HTTPException(
            status_code=503,
            detail="Crawl worker unavailable",
        )

    limiter = getattr(
        request.app.state,
        "submission_limiter",
        None,
    )

    if limiter is not None and not limiter.check(identity):
        raise HTTPException(
            status_code=429,
            detail="Crawl submission rate limit exceeded",
        )

    max_queued = int(
        os.getenv(
            "WEBINTEL_MAX_QUEUED_JOBS",
            "20",
        )
    )

    max_queued = max(1, min(max_queued, 1000))

    if await repository.active_count() >= max_queued:
        raise HTTPException(
            status_code=429,
            detail="Crawl queue is full",
        )

    job = await repository.create(payload)
    worker.notify()

    return job


@router.get(
    "",
    response_model=CrawlJobListResponse,
    summary="List crawl jobs",
)
async def list_crawl_jobs(
    request: Request,
    limit: Annotated[
        int,
        Query(ge=1, le=100),
    ] = 20,
    skip: Annotated[
        int,
        Query(ge=0),
    ] = 0,
):
    repository = get_jobs_repository(request)

    items, total = await repository.list_jobs(
        limit=limit,
        skip=skip,
    )

    return CrawlJobListResponse(
        items=items,
        total=total,
        limit=limit,
        skip=skip,
    )


@router.get(
    "/{job_id}",
    response_model=CrawlJob,
    summary="Retrieve crawl-job status",
)
async def get_crawl_job(
    job_id: UUID,
    request: Request,
):
    repository = get_jobs_repository(request)

    job = await repository.get(job_id)

    if job is None:
        raise HTTPException(
            status_code=404,
            detail="Crawl job not found",
        )

    return job


@router.post(
    "/{job_id}/cancel",
    response_model=CrawlJob,
    summary="Cancel a queued or running crawl job",
)
async def cancel_crawl_job(
    job_id: UUID,
    request: Request,
    identity: Annotated[
        str,
        Depends(require_api_key),
    ],
):
    repository = get_jobs_repository(request)

    job = await repository.get(job_id)

    if job is None:
        raise HTTPException(
            status_code=404,
            detail="Crawl job not found",
        )

    if job.status in ("completed", "failed"):
        raise HTTPException(
            status_code=409,
            detail="Finished jobs cannot be cancelled",
        )

    if job.status == "cancelled":
        return job

    cancelled = await repository.cancel(job_id)

    if cancelled is None:
        raise HTTPException(
            status_code=404,
            detail="Crawl job not found",
        )

    if cancelled.status != "cancelled":
        raise HTTPException(
            status_code=409,
            detail="Job already reached a terminal state",
        )

    worker = getattr(
        request.app.state,
        "crawl_worker",
        None,
    )

    if worker is not None:
        worker.notify()

    return cancelled
