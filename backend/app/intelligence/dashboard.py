"""Read-only, bounded dashboard summaries and revision activity."""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Any

from app.intelligence.monitoring import MonitoringService
from app.intelligence.service import IntelligenceService
from app.intelligence.topic_service import TopicService


def aware_utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError('Time window must include a timezone offset')
    return value.astimezone(timezone.utc)


def date_buckets(start: datetime, end: datetime) -> list[str]:
    start, end = aware_utc(start), aware_utc(end)
    if not start < end:
        raise ValueError('start must be earlier than end')
    if end - start > timedelta(days=90):
        raise ValueError('Time window must not exceed 90 days')
    cursor = start.date()
    last = (end - timedelta(microseconds=1)).date()
    dates = []
    while cursor <= last:
        dates.append(cursor.isoformat())
        cursor += timedelta(days=1)
    return dates


class DashboardService:
    def __init__(self, database):
        self.database = database
        self.intelligence = IntelligenceService(database)
        self.topics = TopicService(database)
        self.monitoring = MonitoringService(database)

    async def summary(
        self, *, source_domain: str | None = None,
        as_of: datetime | None = None, top_k: int = 10,
        max_documents: int = 1000,
    ) -> dict[str, Any]:
        if not 1 <= top_k <= 30:
            raise ValueError('top_k must be between 1 and 30')
        if not 1 <= max_documents <= 1000:
            raise ValueError('max_documents must be between 1 and 1000')
        now = aware_utc(as_of) if as_of else datetime.now(timezone.utc)
        # For dashboard consistency, current-document count and all analytics
        # are based on the same bounded current-document snapshot.
        monitoring = await self.monitoring.overview(
            domain=source_domain, now=now, max_documents=max_documents
        )
        topic_report = await self.topics.topics(
            domain=source_domain, limit=top_k, max_documents=max_documents
        )
        query = {'source_domain': source_domain.lower()} if source_domain else {}
        docs = await self.database['documents'].find(
            query, {'_id': 0, 'document_id': 1, 'document_type': 1}
        ).sort('document_id', 1).limit(max_documents + 1).to_list(length=max_documents + 1)
        if len(docs) > max_documents:
            raise ValueError('Document sample exceeds max_documents')
        kinds = Counter(d.get('document_type') or 'unknown' for d in docs)
        # Counts of revisions/observations for scoped current document IDs.
        ids = sorted({d['document_id'] for d in docs if d.get('document_id')})
        revision_count = await self.database['document_revisions'].count_documents(
            {'document_id': {'$in': ids}}
        ) if ids else 0
        observation_count = await self.database['source_observations'].count_documents(
            {'document_id': {'$in': ids}}
        ) if ids else 0
        return {
            'as_of': now.isoformat(), 'source_domain': source_domain,
            'counting_unit': 'current_documents_bounded',
            'kpis': {
                'document_count': len(docs),
                'revision_count': revision_count,
                'source_observation_count': observation_count,
                'observed_document_count': monitoring['observed_document_count'],
                'unobserved_document_count': monitoring['unobserved_document_count'],
                'coverage_ratio': monitoring['coverage_ratio'],
                'documents_by_type': dict(sorted(kinds.items())),
                'freshness_status_counts': monitoring['status_counts'],
            },
            'top_topics': topic_report['terms'],
            'limitations': ['Current-document sample is bounded.',
                            'Observation age is not verified content freshness.',
                            'Topics are deterministic keyword frequencies, not semantic classifications.'],
        }

    async def revision_activity(
        self, *, start: datetime, end: datetime,
        source_domain: str | None = None, max_documents: int = 1000,
        max_revisions: int = 2000,
    ) -> dict[str, Any]:
        days = date_buckets(start, end)
        start, end = aware_utc(start), aware_utc(end)
        if not 1 <= max_documents <= 1000:
            raise ValueError('max_documents must be between 1 and 1000')
        if not 1 <= max_revisions <= 2000:
            raise ValueError('max_revisions must be between 1 and 2000')
        query = {'source_domain': source_domain.lower()} if source_domain else {}
        docs = await self.database['documents'].find(
            query, {'_id': 0, 'document_id': 1}
        ).sort('document_id', 1).limit(max_documents + 1).to_list(length=max_documents + 1)
        if len(docs) > max_documents:
            raise ValueError('Document sample exceeds max_documents')
        ids = sorted({d['document_id'] for d in docs if d.get('document_id')})
        counts = Counter()
        unique_docs: dict[str, set[str]] = {day: set() for day in days}
        if ids:
            cursor = self.database['document_revisions'].find(
                {'document_id': {'$in': ids},
                 'observed_at': {'$gte': start, '$lt': end}},
                {'_id': 0, 'revision_id': 1, 'document_id': 1, 'observed_at': 1},
            ).sort([('observed_at', 1), ('revision_id', 1)]).limit(max_revisions + 1)
            records = await cursor.to_list(length=max_revisions + 1)
            if len(records) > max_revisions:
                raise ValueError('Revision sample exceeds max_revisions; narrow the window')
            for record in records:
                observed = record['observed_at']
                # MongoDB/PyMongo frequently returns naive UTC on reads.
                if observed.tzinfo is None:
                    observed = observed.replace(tzinfo=timezone.utc)
                day = observed.astimezone(timezone.utc).date().isoformat()
                if day in unique_docs:
                    counts[day] += 1
                    unique_docs[day].add(record['document_id'])
        return {
            'source_domain': source_domain,
            'start': start.isoformat(), 'end': end.isoformat(),
            'counting_unit': 'revision_snapshots_by_observed_utc_day',
            'total_revisions': sum(counts.values()),
            'series': [
                {'date': day, 'revision_count': counts[day],
                 'unique_document_count': len(unique_docs[day])}
                for day in days
            ],
            'caution': 'Revision observation timestamps are not original publication or crawl-event times.',
        }

    async def domain_summary(self, *, as_of: datetime | None = None,
                             limit: int = 20, max_documents: int = 1000) -> dict:
        if not 1 <= limit <= 100:
            raise ValueError('limit must be 1..100')
        now = aware_utc(as_of) if as_of else datetime.now(timezone.utc)
        monitoring = await self.monitoring.domains(now=now, max_documents=max_documents)
        return {'as_of': now.isoformat(),
                'counting_unit': 'unique_current_document',
                'total_domains': len(monitoring['domains']),
                'domains': monitoring['domains'][:limit]}
