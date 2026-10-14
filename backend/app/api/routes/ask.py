
import asyncio
import os
from typing import Annotated

from dotenv import load_dotenv
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
)

from app.api.routes.search import (
    get_config,
    get_embedding_provider,
)
from app.rag.provider import (
    GroqProvider,
    LLMOutputError,
    LLMUnavailableError,
)
from app.rag.schemas import AskRequest, AskResponse
from app.rag.service import RAGService
from app.retrieval.engine import RetrievalEngine


router = APIRouter(
    prefix="/ask",
    tags=["RAG"],
)


def enforce_inference_rate_limit(request: Request) -> None:
    """Apply a bounded local-process cost guard before RAG work."""
    limiter = getattr(request.app.state, "inference_limiter", None)
    identity = request.client.host if request.client else "unknown"
    if limiter is not None and not limiter.check(identity):
        raise HTTPException(
            status_code=429,
            detail="Inference rate limit exceeded",
            headers={"Retry-After": "60"},
        )


async def get_rag_service(
    request: Request,
) -> RAGService:
    database = getattr(
        request.app.state,
        "mongodb_database",
        None,
    )

    if database is None:
        raise HTTPException(
            status_code=503,
            detail="RAG database unavailable",
        )

    load_dotenv()

    config = get_config()

    provider = await asyncio.to_thread(
        get_embedding_provider,
        config.model_id,
        config.model_revision,
    )

    retrieval = RetrievalEngine(
        database=database,
        provider=provider,
        config=config,
    )

    llm = GroqProvider()

    return RAGService(
        retrieval=retrieval,
        llm=llm,
        model_name=llm.model,
        min_cosine=float(
            os.getenv(
                "WEBINTEL_RAG_MIN_COSINE",
                "0.20",
            )
        ),
    )


@router.post(
    "",
    response_model=AskResponse,
    summary="Ask an evidence-grounded question",
    dependencies=[Depends(enforce_inference_rate_limit)],
)
async def ask_question(
    payload: AskRequest,
    service: Annotated[
        RAGService,
        Depends(get_rag_service),
    ],
):
    try:
        return await service.ask(payload)

    except LLMUnavailableError:
        raise HTTPException(
            status_code=503,
            detail="LLM provider is unavailable",
        ) from None

    except LLMOutputError:
        raise HTTPException(
            status_code=502,
            detail="LLM returned an invalid response",
        ) from None
