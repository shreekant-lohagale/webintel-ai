
import asyncio
import os
from functools import lru_cache

from fastapi import (
    APIRouter,
    HTTPException,
    Request,
)

from app.api.schemas.search import (
    SearchRequest,
    SearchResponse,
)
from app.embeddings.indexer import IndexConfig
from app.embeddings.model import (
    EMBEDDING_DIMENSION,
    SentenceTransformerProvider,
)
from app.retrieval.engine import (
    RetrievalEngine,
    SearchFilters,
)


router = APIRouter(
    prefix="/search",
    tags=["Search"],
)


@lru_cache(maxsize=4)
def get_embedding_provider(
    model_id: str,
    revision: str,
):
    return SentenceTransformerProvider(
        model_id=model_id,
        revision=revision,
        batch_size=16,
    )


def get_config():
    return IndexConfig(
        model_id=os.getenv(
            "WEBINTEL_EMBEDDING_MODEL",
            "sentence-transformers/all-MiniLM-L6-v2",
        ),
        model_revision=os.getenv(
            "WEBINTEL_EMBEDDING_REVISION",
            "main",
        ),
        chunk_words=int(os.getenv(
            "WEBINTEL_CHUNK_WORDS", "120"
        )),
        overlap_words=int(os.getenv(
            "WEBINTEL_CHUNK_OVERLAP", "25"
        )),
        dimension=EMBEDDING_DIMENSION,
    )


@router.post(
    "",
    response_model=SearchResponse,
    summary="Search indexed WebIntel documents",
)
async def search(
    payload: SearchRequest,
    request: Request,
):
    database = getattr(
        request.app.state,
        "mongodb_database",
        None,
    )

    if database is None:
        raise HTTPException(
            status_code=503,
            detail="Search database unavailable",
        )

    try:
        config = get_config()

        # Avoid blocking the FastAPI event loop while
        # the local PyTorch model initializes.
        provider = await asyncio.to_thread(
            get_embedding_provider,
            config.model_id,
            config.model_revision,
        )

        engine = RetrievalEngine(
            database=database,
            provider=provider,
            config=config,
        )

        results = await engine.search(
            query=payload.query,
            mode=payload.mode,
            limit=payload.limit,
            filters=SearchFilters(
                document_type=payload.document_type,
                source_domain=payload.source_domain,
            ),
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    return SearchResponse(
        query=payload.query,
        mode=payload.mode,
        count=len(results),
        results=results,
    )
