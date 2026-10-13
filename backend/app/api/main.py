
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI

from app.api.config import Settings, get_settings
from app.api.routes.documents import (
    router as documents_router,
)
from app.api.routes.health import router as health_router
from app.storage.mongodb import create_client
from app.storage.repository import MongoRepository


def create_app(
    settings: Settings | None = None,
    connect_db: bool = True,
) -> FastAPI:
    """
    Application factory.

    connect_db=False is intended for isolated API
    foundation tests, not normal deployment.
    """

    settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # Initialize application state.
        app.state.mongodb_client = None
        app.state.mongodb_database = None
        app.state.repository = None

        if not connect_db:
            yield
            return

        client = create_client(
            uri=settings.mongodb_uri
        )

        try:
            # Fail startup if MongoDB cannot be reached.
            await client.admin.command("ping")

            database = client[
                settings.mongodb_database
            ]

            repository = MongoRepository(
                database
            )

            # Safe to call again: MongoDB retains
            # existing indexes.
            await repository.ensure_indexes()

            app.state.mongodb_client = client
            app.state.mongodb_database = database
            app.state.repository = repository

            yield

        finally:
            app.state.repository = None
            app.state.mongodb_database = None
            app.state.mongodb_client = None

            await client.close()

    application = FastAPI(
        title=settings.app_title,
        version=settings.app_version,
        debug=settings.debug,
        description=(
            "WebIntel AI provides document intelligence, "
            "web crawling and evidence-grounded retrieval."
        ),
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    api_router = APIRouter(
        prefix="/api/v1"
    )

    api_router.include_router(
        health_router
    )

    api_router.include_router(
        documents_router
    )

    application.include_router(
        api_router
    )

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
