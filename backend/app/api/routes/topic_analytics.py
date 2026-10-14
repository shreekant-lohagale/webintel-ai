"""Read-only topic analysis routes. Registered under /api/v1."""
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.intelligence.topic_service import TopicService

router = APIRouter(prefix='/analytics/topics', tags=['Topic Intelligence'])


def get_topic_service(request: Request) -> TopicService:
    db = getattr(request.app.state, "mongodb_database", None)
    if db is None:
        raise HTTPException(503, "Analytics database unavailable")
    return TopicService(db)


TopicDep = Annotated[TopicService, Depends(get_topic_service)]
Domain = Annotated[str | None, Query(max_length=253, pattern=r'^[A-Za-z0-9.-]+$')]


@router.get('')
async def topics(
    service: TopicDep,
    source_domain: Domain = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    ngrams: Annotated[int, Query(ge=1, le=2)] = 1,
    max_documents: Annotated[int, Query(ge=1, le=1000)] = 1000,
):
    try:
        return await service.topics(domain=source_domain, limit=limit, ngrams=ngrams, max_documents=max_documents)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@router.get('/domains')
async def domain_topics(
    service: TopicDep,
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
    top_k: Annotated[int, Query(ge=1, le=100)] = 10,
    ngrams: Annotated[int, Query(ge=1, le=2)] = 1,
    max_documents: Annotated[int, Query(ge=1, le=1000)] = 1000,
):
    try:
        return await service.domains(limit=limit, top_k=top_k, ngrams=ngrams, max_documents=max_documents)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@router.get('/trends')
async def trend_topics(
    service: TopicDep,
    before_start: datetime,
    before_end: datetime,
    after_start: datetime,
    after_end: datetime,
    source_domain: Domain = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    ngrams: Annotated[int, Query(ge=1, le=2)] = 1,
    max_documents: Annotated[int, Query(ge=1, le=1000)] = 1000,
):
    try:
        return await service.trends(
            before_start=before_start, before_end=before_end,
            after_start=after_start, after_end=after_end,
            domain=source_domain, limit=limit, ngrams=ngrams,
            max_documents=max_documents,
        )
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
