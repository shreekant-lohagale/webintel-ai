
from typing import Annotated
from uuid import UUID

from fastapi import (
    APIRouter,
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
):
    # API execution is deliberately limited to the
    # localhost article test fixture in this milestone.
    try:
        mode = validate_start_url(
            payload.start_url,
            allow_live=False,
        )

        if mode != "local":
            raise ValueError(
                "Only local test crawling is enabled"
            )

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
    summary="Get crawl-job status",
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
