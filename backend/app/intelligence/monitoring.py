"""Read-only, bounded monitoring analytics over existing MongoDB collections."""
from collections import Counter, defaultdict
from datetime import datetime, timezone

from app.intelligence.freshness import classify, utc


class MonitoringService:
    def __init__(self, database):
        self.documents = database['documents']
        self.observations = database['source_observations']
        self.revisions = database['document_revisions']

    async def _snapshot(self, *, domain=None, now=None, fresh_hours=24, stale_hours=168, max_documents=1000):
        now = utc(now or datetime.now(timezone.utc))
        if not 1 <= max_documents <= 1000:
            raise ValueError('max_documents must be from 1 to 1000')
        # Validate thresholds even for an empty collection.
        classify(None, now=now, fresh_hours=fresh_hours, stale_hours=stale_hours)
        query = {'source_domain': domain.lower()} if domain else {}
        docs = await self.documents.find(
            query, {'_id': 0, 'document_id': 1, 'title': 1, 'source_domain': 1, 'document_type': 1}
        ).sort('document_id', 1).limit(max_documents + 1).to_list(length=max_documents + 1)
        if len(docs) > max_documents:
            raise ValueError('Document sample exceeds max_documents; filter by source_domain or increase limit')
        ids = [d['document_id'] for d in docs if d.get('document_id')]
        by_id = {d['document_id']: d for d in docs if d.get('document_id')}
        if not ids:
            return now, [], {}, {}
        cursor = await self.observations.aggregate([
            {'$match': {'document_id': {'$in': ids}}},
            {'$group': {'_id': '$document_id', 'last_seen_at': {'$max': '$last_seen_at'},
                        'first_seen_at': {'$min': '$first_seen_at'},
                        'observation_count': {'$sum': 1},
                        'source_urls': {'$addToSet': '$source_url'},
                        'methods': {'$addToSet': '$extraction_method'}}},
        ])
        obs = {r['_id']: r for r in await cursor.to_list(length=len(ids))}
        # A count of immutable revisions is not a crawl-event count.
        cursor = await self.revisions.aggregate([
            {'$match': {'document_id': {'$in': ids}}},
            {'$group': {'_id': '$document_id', 'revision_count': {'$sum': 1}}},
        ])
        revisions = {r['_id']: r['revision_count'] for r in await cursor.to_list(length=len(ids))}
        items = []
        for doc_id, doc in by_id.items():
            entry = obs.get(doc_id, {})
            assessment = classify(entry.get('last_seen_at'), now=now,
                                  fresh_hours=fresh_hours, stale_hours=stale_hours)
            items.append({
                'document_id': doc_id,
                'title': doc.get('title'),
                'source_domain': doc.get('source_domain') or 'unknown',
                'document_type': doc.get('document_type'),
                **assessment,
                'first_seen_at': utc(entry['first_seen_at']).isoformat() if entry.get('first_seen_at') else None,
                'provenance_record_count': entry.get('observation_count', 0),
                'distinct_source_url_count': len(set(x for x in entry.get('source_urls', []) if x)),
                'extraction_methods': sorted(x for x in entry.get('methods', []) if x),
                'revision_count': revisions.get(doc_id, 0),
            })
        items.sort(key=lambda x: x['document_id'])
        return now, items, obs, revisions

    async def overview(self, *, domain=None, now=None, fresh_hours=24, stale_hours=168, max_documents=1000):
        now, items, _, _ = await self._snapshot(domain=domain, now=now, fresh_hours=fresh_hours,
                                               stale_hours=stale_hours, max_documents=max_documents)
        statuses = Counter(item['status'] for item in items)
        covered = sum(item['provenance_record_count'] > 0 for item in items)
        return {'as_of': now.isoformat(), 'source_domain': domain,
                'counting_unit': 'unique_current_document',
                'document_count': len(items), 'observed_document_count': covered,
                'unobserved_document_count': len(items) - covered,
                'coverage_ratio': round(covered / len(items), 4) if items else None,
                'status_counts': {key: statuses[key] for key in
                                  ('recently_observed', 'aging_observation', 'stale_observation', 'future_timestamp', 'unknown')},
                'fresh_hours': fresh_hours, 'stale_hours': stale_hours,
                'caution': 'Observation age is not verified content freshness. Provenance records are not crawl events.'}

    async def documents_status(self, *, domain=None, status=None, limit=20, now=None,
                               fresh_hours=24, stale_hours=168, max_documents=1000):
        if not 1 <= limit <= 100:
            raise ValueError('limit must be between 1 and 100')
        now, items, _, _ = await self._snapshot(domain=domain, now=now, fresh_hours=fresh_hours,
                                               stale_hours=stale_hours, max_documents=max_documents)
        matches = [x for x in items if status is None or x['status'] == status]
        matches.sort(key=lambda x: (x['last_seen_at'] is not None, x['last_seen_at'] or '', x['document_id']))
        return {'as_of': now.isoformat(), 'total_matching': len(matches), 'limit': limit,
                'items': matches[:limit]}

    async def domains(self, *, now=None, fresh_hours=24, stale_hours=168, max_documents=1000):
        now, items, _, _ = await self._snapshot(now=now, fresh_hours=fresh_hours,
                                               stale_hours=stale_hours, max_documents=max_documents)
        domains = defaultdict(list)
        for item in items:
            domains[item['source_domain']].append(item)
        result = []
        for domain, group in domains.items():
            statuses = Counter(x['status'] for x in group)
            covered = sum(x['provenance_record_count'] > 0 for x in group)
            seen = [x['last_seen_at'] for x in group if x['last_seen_at']]
            result.append({'source_domain': domain, 'document_count': len(group),
                           'observed_document_count': covered,
                           'coverage_ratio': round(covered / len(group), 4),
                           'latest_observed_at': max(seen) if seen else None,
                           'status_counts': {key: statuses[key] for key in
                                             ('recently_observed', 'aging_observation', 'stale_observation', 'future_timestamp', 'unknown')}})
        result.sort(key=lambda x: (-x['document_count'], x['source_domain']))
        return {'as_of': now.isoformat(), 'counting_unit': 'unique_current_document', 'domains': result}
