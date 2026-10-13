
from typing import Annotated, Literal

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Path,
    Query,
    status,
)

from app.api.dependencies import get_repository
from app.api.schemas.documents import (
    DocumentListResponse,
    DocumentSourcesResponse,
    DocumentRevisionsResponse,
)
from app.processing.schemas import WebDocument
from app.storage.repository import MongoRepository


router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
)

RepositoryDep = Annotated[
    MongoRepository,
    Depends(get_repository),
]

DocumentId = Annotated[
    str,
    Path(
        pattern=r"^[0-9a-f]{64}$",
        description="SHA-256 document identifier",
    ),
]


async def ensure_document_exists(
    repository: MongoRepository,
    document_id: str,
) -> WebDocument:
    """Retrieve a document or raise HTTP 404."""

    document = await repository.get_document(
        document_id
    )

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    return document


@router.get(
    "",
    response_model=DocumentListResponse,
    summary="List and filter documents",
)
async def list_documents(
    repository: RepositoryDep,
    page: Annotated[
        int,
        Query(ge=1),
    ] = 1,
    page_size: Annotated[
        int,
        Query(ge=1, le=100),
    ] = 20,
    document_type: Literal[
        "article", "quote"
    ] | None = None,
    source_domain: Annotated[
        str | None,
        Query(min_length=1, max_length=253),
    ] = None,
    tag: Annotated[
        str | None,
        Query(min_length=1, max_length=100),
    ] = None,
    q: Annotated[
        str | None,
        Query(min_length=1, max_length=200),
    ] = None,
):
    """Retrieve current documents with optional filters."""

    items, total = await repository.search_documents(
        page=page,
        page_size=page_size,
        document_type=document_type,
        source_domain=source_domain,
        tag=tag,
        q=q,
    )

    total_pages = (
        (total + page_size - 1) // page_size
    )

    return DocumentListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_previous=page > 1,
    )


@router.get(
    "/{document_id}",
    response_model=WebDocument,
    summary="Retrieve a document",
    responses={
        404: {"description": "Document not found"},
    },
)
async def get_document(
    document_id: DocumentId,
    repository: RepositoryDep,
):
    return await ensure_document_exists(
        repository,
        document_id,
    )


@router.get(
    "/{document_id}/sources",
    response_model=DocumentSourcesResponse,
    summary="Get document provenance",
    responses={
        404: {"description": "Document not found"},
    },
)
async def get_document_sources(
    document_id: DocumentId,
    repository: RepositoryDep,
):
    await ensure_document_exists(
        repository,
        document_id,
    )

    sources = await repository.get_sources(
        document_id
    )

    return DocumentSourcesResponse(
        document_id=document_id,
        total=len(sources),
        items=sources,
    )


@router.get(
    "/{document_id}/revisions",
    response_model=DocumentRevisionsResponse,
    summary="Get document revision history",
    responses={
        404: {"description": "Document not found"},
    },
)
async def get_document_revisions(
    document_id: DocumentId,
    repository: RepositoryDep,
):
    await ensure_document_exists(
        repository,
        document_id,
    )

    revisions = await repository.get_revisions(
        document_id
    )

    return DocumentRevisionsResponse(
        document_id=document_id,
        total=len(revisions),
        items=revisions,
    )
