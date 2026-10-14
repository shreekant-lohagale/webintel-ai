"""Read-only monitoring endpoints, registered below /api/v1."""
from datetime import datetime
from typing import Annotated, Literal
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from app.intelligence.monitoring import MonitoringService

router = APIRouter(prefix='/analytics/monitoring', tags=['Source Monitoring'])

def get_monitoring_service(request: Request) -> MonitoringService:
    db = getattr(request.app.state, 'mongodb_database', None)
    if db is None:
        raise HTTPException(status_code=503, detail='Analytics database unavailable')
    return MonitoringService(db)

Service = Annotated[MonitoringService, Depends(get_monitoring_service)]
Domain = Annotated[str | None, Query(max_length=253, pattern=r'^[A-Za-z0-9.-]+$')]
Status = Literal['recently_observed', 'aging_observation', 'stale_observation', 'future_timestamp', 'unknown']

@router.get('/overview')
async def monitoring_overview(service: Service, source_domain: Domain = None,
                              as_of: datetime | None = None,
                              fresh_hours: Annotated[int, Query(ge=1, le=87599)] = 24,
                              stale_hours: Annotated[int, Query(ge=2, le=87600)] = 168,
                              max_documents: Annotated[int, Query(ge=1, le=1000)] = 1000):
    try:
        return await service.overview(domain=source_domain, now=as_of, fresh_hours=fresh_hours,
                                      stale_hours=stale_hours, max_documents=max_documents)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc

@router.get('/documents')
async def monitoring_documents(service: Service, source_domain: Domain = None,
                               status: Status | None = None,
                               as_of: datetime | None = None,
                               fresh_hours: Annotated[int, Query(ge=1, le=87599)] = 24,
                               stale_hours: Annotated[int, Query(ge=2, le=87600)] = 168,
                               max_documents: Annotated[int, Query(ge=1, le=1000)] = 1000,
                               limit: Annotated[int, Query(ge=1, le=100)] = 20):
    try:
        return await service.documents_status(domain=source_domain, status=status,
                                              now=as_of, fresh_hours=fresh_hours,
                                              stale_hours=stale_hours, max_documents=max_documents, limit=limit)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc

@router.get('/domains')
async def monitoring_domains(service: Service, as_of: datetime | None = None,
                             fresh_hours: Annotated[int, Query(ge=1, le=87599)] = 24,
                             stale_hours: Annotated[int, Query(ge=2, le=87600)] = 168,
                             max_documents: Annotated[int, Query(ge=1, le=1000)] = 1000):
    try:
        return await service.domains(now=as_of, fresh_hours=fresh_hours,
                                     stale_hours=stale_hours, max_documents=max_documents)
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
