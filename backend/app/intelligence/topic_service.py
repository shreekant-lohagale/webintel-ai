"""Bounded, read-only topic analytics over existing MongoDB collections."""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone

from app.intelligence.topics import compare_windows, term_frequencies


MAX_DOCS = 1000
MAX_REVISIONS = 2000


def utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        raise ValueError('Window timestamps need an explicit timezone')
    return dt.astimezone(timezone.utc)


class TopicService:
    def __init__(self, database):
        self.documents = database['documents']
        self.revisions = database['document_revisions']

    async def _documents(self, *, domain: str | None, limit: int) -> list[dict]:
        if not 1 <= limit <= MAX_DOCS:
            raise ValueError('max_documents must be 1..1000')
        query = {'source_domain': domain.lower()} if domain else {}
        cursor = self.documents.find(
            query, {'_id': 0, 'document_id': 1, 'source_domain': 1, 'content': 1}
        ).sort('document_id', 1).limit(limit + 1)
        docs = await cursor.to_list(length=limit + 1)
        if len(docs) > limit:
            raise ValueError('Document sample limit exceeded; apply source_domain or increase max_documents')
        return docs

    async def topics(self, *, domain=None, limit=20, ngrams=1, max_documents=1000):
        docs = await self._documents(domain=domain, limit=max_documents)
        return {
            'source_domain': domain,
            'document_count': len(docs),
            'counting_unit': 'unique_current_document',
            'terms': term_frequencies(docs, top_k=limit, ngrams=ngrams),
        }

    async def domains(self, *, limit=10, top_k=10, ngrams=1, max_documents=1000):
        docs = await self._documents(domain=None, limit=max_documents)
        groups = defaultdict(list)
        for doc in docs:
            groups[doc.get('source_domain') or 'unknown'].append(doc)
        ordered = sorted(groups.items(), key=lambda kv: (-len(kv[1]), kv[0]))[:limit]
        return {
            'document_count': len(docs),
            'counting_unit': 'unique_current_document',
            'domains': [
                {'source_domain': domain, 'document_count': len(items),
                 'terms': term_frequencies(items, top_k=top_k, ngrams=ngrams)}
                for domain, items in ordered
            ],
        }

    async def trends(
        self, *, before_start: datetime, before_end: datetime,
        after_start: datetime, after_end: datetime, domain=None,
        limit=20, ngrams=1, max_documents=1000,
    ):
        b0, b1, a0, a1 = map(utc, [before_start, before_end, after_start, after_end])
        if not (b0 < b1 <= a0 < a1):
            raise ValueError('Require ordered non-overlapping UTC windows: before_start < before_end <= after_start < after_end')
        if (a1 - b0).days > 366:
            raise ValueError('Overall trend horizon must not exceed 366 days')

        # Domain membership comes from current document metadata; immutable revisions
        # contain no source_domain. This is explicitly a CURRENT-domain filter.
        docs = await self._documents(domain=domain, limit=max_documents)
        ids = [doc['document_id'] for doc in docs]
        if not ids:
            result = compare_windows([], [], top_k=limit, ngrams=ngrams)
        else:
            query = {
                'document_id': {'$in': ids},
                '$or': [
                    {'observed_at': {'$gte': b0, '$lt': b1}},
                    {'observed_at': {'$gte': a0, '$lt': a1}},
                ],
            }
            cursor = self.revisions.find(
                query, {'_id': 0, 'document_id': 1, 'revision_id': 1,
                        'observed_at': 1, 'content': 1}
            ).sort([('document_id', 1), ('observed_at', 1), ('revision_id', 1)]).limit(MAX_REVISIONS + 1)
            revisions = await cursor.to_list(length=MAX_REVISIONS + 1)
            if len(revisions) > MAX_REVISIONS:
                raise ValueError('Revision sample exceeds 2000; narrow time windows')
            before = [r for r in revisions if b0 <= utc_assume_db(r['observed_at']) < b1]
            after = [r for r in revisions if a0 <= utc_assume_db(r['observed_at']) < a1]
            result = compare_windows(before, after, top_k=limit, ngrams=ngrams)
        return {
            'source_domain': domain,
            'counting_unit': 'latest_revision_per_document_per_window',
            'before_start': b0.isoformat(), 'before_end': b1.isoformat(),
            'after_start': a0.isoformat(), 'after_end': a1.isoformat(),
            **result,
            'caution': 'Observed revision timestamps; frequencies depend on available sampled documents, not public popularity.',
        }


def utc_assume_db(dt: datetime) -> datetime:
    """PyMongo defaults to returning naive UTC datetimes."""
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt.astimezone(timezone.utc)
