"""Aggregated frontend-ready intelligence dashboard APIs."""
from datetime import datetime
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from app.intelligence.dashboard import DashboardService

router = APIRouter(prefix='/analytics/dashboard', tags=['Dashboard Analytics'])

def get_dashboard_service(request: Request) -> DashboardService:
    database = getattr(request.app.state, 'mongodb_database', None)
    if database is None:
        raise HTTPException(status_code=503, detail='Analytics database unavailable')
    return DashboardService(database)

Service = Annotated[DashboardService, Depends(get_dashboard_service)]
Domain = Annotated[str | None, Query(max_length=253, pattern=r'^[A-Za-z0-9.-]+$')]

@router.get('/summary')
async def dashboard_summary(
    service: Service, source_domain: Domain = None, as_of: datetime | None = None,
    top_k: Annotated[int, Query(ge=1, le=30)] = 10,
    max_documents: Annotated[int, Query(ge=1, le=1000)] = 1000,
):
    try:
        return await service.summary(source_domain=source_domain, as_of=as_of,
                                     top_k=top_k, max_documents=max_documents)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

@router.get('/revision-activity')
async def dashboard_revision_activity(
    service: Service, start: datetime, end: datetime, source_domain: Domain = None,
    max_documents: Annotated[int, Query(ge=1, le=1000)] = 1000,
    max_revisions: Annotated[int, Query(ge=1, le=2000)] = 2000,
):
    try:
        return await service.revision_activity(start=start, end=end,
            source_domain=source_domain, max_documents=max_documents,
            max_revisions=max_revisions)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

@router.get('/domains')
async def dashboard_domains(
    service: Service, as_of: datetime | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    max_documents: Annotated[int, Query(ge=1, le=1000)] = 1000,
):
    try:
        return await service.domain_summary(as_of=as_of, limit=limit,
                                             max_documents=max_documents)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
