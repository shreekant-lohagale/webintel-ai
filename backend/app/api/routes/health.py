
from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel


router = APIRouter(
    prefix="/health",
    tags=["Health"],
)


class LiveResponse(BaseModel):
    status: str
    service: str


class ReadyResponse(BaseModel):
    status: str
    database: str


@router.get(
    "/live",
    response_model=LiveResponse,
    summary="Application liveness",
)
async def liveness():
    """
    Liveness confirms the FastAPI process is running.
    It does not depend on MongoDB availability.
    """

    return LiveResponse(
        status="alive",
        service="webintel-ai",
    )


@router.get(
    "/ready",
    response_model=ReadyResponse,
    summary="MongoDB readiness",
)
async def readiness(request: Request):
    """
    Readiness checks whether the shared MongoDB client
    can communicate with the database server.
    """

    client = getattr(
        request.app.state,
        "mongodb_client",
        None,
    )

    database = getattr(
        request.app.state,
        "mongodb_database",
        None,
    )

    if client is None or database is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not initialized",
        )

    try:
        await client.admin.command("ping")
    except Exception:
        # Do not expose MongoDB credentials or
        # connection strings through HTTP responses.
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not ready",
        ) from None

    return ReadyResponse(
        status="ready",
        database=database.name,
    )
