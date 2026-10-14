
from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Path,
    Query,
    Request,
)

from app.intelligence.service import IntelligenceService


router = APIRouter(
    prefix="/analytics",
    tags=["Intelligence Analytics"],
)

DocumentId = Annotated[
    str,
    Path(pattern=r"^[0-9a-f]{64}$"),
]


def get_intelligence_service(
    request: Request,
) -> IntelligenceService:
    database = getattr(
        request.app.state,
        "mongodb_database",
        None,
    )

    if database is None:
        raise HTTPException(
            status_code=503,
            detail="Analytics database unavailable",
        )

    return IntelligenceService(database)


ServiceDep = Annotated[
    IntelligenceService,
    Depends(get_intelligence_service),
]


@router.get(
    "/overview",
    summary="Get intelligence overview",
)
async def analytics_overview(
    service: ServiceDep,
):
    return await service.overview()


@router.get(
    "/sources",
    summary="Get source-domain statistics",
)
async def analytics_sources(
    service: ServiceDep,
    limit: Annotated[
        int,
        Query(ge=1, le=100),
    ] = 20,
):
    return await service.source_statistics(
        limit=limit
    )


@router.get(
    "/documents/{document_id}/changes",
    summary="Get chronological document changes",
)
async def document_changes(
    document_id: DocumentId,
    service: ServiceDep,
    max_revisions: Annotated[
        int,
        Query(ge=2, le=200),
    ] = 200,
):
    try:
        result = await service.timeline(
            document_id,
            max_revisions=max_revisions,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Document not found",
        )

    return result


@router.get(
    "/documents/{document_id}/compare",
    summary="Compare document revision snapshots",
)
async def compare_document(
    document_id: DocumentId,
    service: ServiceDep,
    from_revision_id: Annotated[
        str | None,
        Query(pattern=r"^[0-9a-f]{64}$"),
    ] = None,
    to_revision_id: Annotated[
        str | None,
        Query(pattern=r"^[0-9a-f]{64}$"),
    ] = None,
):
    try:
        result = await service.compare(
            document_id,
            from_revision_id=from_revision_id,
            to_revision_id=to_revision_id,
        )

    except LookupError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Document not found",
        )

    return result
