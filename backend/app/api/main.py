
import logging
import os
import time
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import APIRouter, FastAPI, Request

from app.api.config import Settings, get_settings
from app.api.routes.analytics import (
    router as analytics_router,
)
from app.api.routes.ask import (
    router as ask_router,
)
from app.api.routes.health import router as health_router
from app.api.routes.monitoring import router as monitoring_router
from app.api.routes.documents import (
    router as documents_router,
)
from app.api.routes.crawl_jobs import (
    router as crawl_jobs_router,
)
from app.api.routes.dashboard import router as dashboard_router
from app.api.routes.search import (
    router as search_router,
)
from app.api.routes.topic_analytics import (
    router as topic_analytics_router,
)
from app.api.security import SubmissionLimiter
from app.jobs.repository import CrawlJobRepository
from app.jobs.worker import (
    CrawlJobWorker,
    JobRunner,
    execute_crawl_job,
)
from app.observability.logging import configure_logging
from app.storage.mongodb import create_client
from app.storage.repository import MongoRepository


logger = configure_logging()


def create_app(
    settings: Settings | None = None,
    connect_db: bool = True,
    job_runner: JobRunner = execute_crawl_job,
) -> FastAPI:
    settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.mongodb_client = None
        app.state.mongodb_database = None
        app.state.repository = None
        app.state.jobs_repository = None
        app.state.crawl_worker = None

        limit = int(
            os.getenv(
                "WEBINTEL_RATE_LIMIT_PER_MINUTE",
                "10",
            )
        )

        app.state.submission_limiter = SubmissionLimiter(
            max_requests=max(1, min(limit, 10000))
        )

        if not connect_db:
            yield
            return

        client = create_client(
            uri=settings.mongodb_uri
        )

        worker = None

        try:
            await client.admin.command("ping")

            database = client[
                settings.mongodb_database
            ]

            repository = MongoRepository(database)
            await repository.ensure_indexes()

            jobs_repository = CrawlJobRepository(database)
            await jobs_repository.ensure_indexes()

            worker = CrawlJobWorker(
                repository=jobs_repository,
                database_name=settings.mongodb_database,
                runner=job_runner,
            )

            app.state.mongodb_client = client
            app.state.mongodb_database = database
            app.state.repository = repository
            app.state.jobs_repository = jobs_repository
            app.state.crawl_worker = worker

            await worker.start()
            yield

        finally:
            if worker is not None:
                await worker.stop()

            app.state.crawl_worker = None
            app.state.jobs_repository = None
            app.state.repository = None
            app.state.mongodb_database = None
            app.state.mongodb_client = None
            app.state.submission_limiter = None

            await client.close()

    application = FastAPI(
        title=settings.app_title,
        version=settings.app_version,
        debug=settings.debug,
        description=(
            "WebIntel AI document intelligence, "
            "web crawling and evidence-grounded retrieval."
        ),
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    @application.middleware("http")
    async def request_logging(
        request: Request,
        call_next,
    ):
        request_id = str(uuid4())
        started = time.perf_counter()

        try:
            response = await call_next(request)

        except Exception:
            logger.exception(
                "Unhandled API exception",
                extra={
                    "request_id": request_id,
                    "path": request.url.path,
                    "method": request.method,
                },
            )
            raise

        elapsed_ms = round(
            (time.perf_counter() - started) * 1000,
            2,
        )

        response.headers["X-Request-ID"] = request_id

        logger.info(
            "HTTP request",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": elapsed_ms,
            },
        )

        return response

    api_router = APIRouter(prefix="/api/v1")

    api_router.include_router(health_router)
    api_router.include_router(documents_router)
    api_router.include_router(crawl_jobs_router)
    api_router.include_router(search_router)
    api_router.include_router(ask_router)
    api_router.include_router(analytics_router)
    api_router.include_router(topic_analytics_router)
    api_router.include_router(monitoring_router)
    api_router.include_router(dashboard_router)

    application.include_router(api_router)

    @application.get(
        "/",
        tags=["Root"],
        summary="API information",
    )
    async def root():
        return {
            "name": settings.app_title,
            "version": settings.app_version,
            "api_prefix": "/api/v1",
            "documentation": "/docs",
        }

    return application


app = create_app()
