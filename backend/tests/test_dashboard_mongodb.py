"""Writes only to an isolated throwaway test DB; dashboard reads are non-destructive."""
import asyncio
import os
from datetime import datetime, timezone
from uuid import uuid4

import pytest
from app.storage.mongodb import create_client
from app.intelligence.dashboard import DashboardService


def dt(day, hour=0):
    return datetime(2026, 10, day, hour, tzinfo=timezone.utc)


async def exercise():
    client = create_client()
    name = 'webintel_dashboard_test_' + uuid4().hex
    db = client[name]
    try:
        await db['documents'].insert_many([
            {'document_id': 'a' * 64, 'source_domain': 'example.com',
             'document_type': 'article', 'title': 'Data', 'content': 'Reliable data pipelines use validation.'},
            {'document_id': 'b' * 64, 'source_domain': 'other.com',
             'document_type': 'article', 'title': 'AI', 'content': 'AI helps teams.'},
        ])
        await db['document_revisions'].insert_many([
            {'revision_id': '1' * 64, 'document_id': 'a' * 64,
             'observed_at': dt(13, 8), 'content': 'Data'},
            {'revision_id': '2' * 64, 'document_id': 'a' * 64,
             'observed_at': dt(13, 12), 'content': 'Data version two'},
            {'revision_id': '3' * 64, 'document_id': 'b' * 64,
             'observed_at': dt(14, 8), 'content': 'AI'},
        ])
        await db['source_observations'].insert_one({
            'document_id': 'a' * 64, 'source_url': 'https://example.com/data',
            'extraction_method': 'scrapy', 'first_seen_at': dt(13),
            'last_seen_at': dt(14),
        })
        service = DashboardService(db)
        before = {key: await db[key].count_documents({}) for key in
                  ('documents', 'document_revisions', 'source_observations')}
        summary = await service.summary(as_of=dt(14, 12))
        assert summary['kpis']['document_count'] == 2
        assert summary['kpis']['revision_count'] == 3
        assert summary['kpis']['observed_document_count'] == 1
        assert summary['kpis']['coverage_ratio'] == 0.5
        assert summary['top_topics']
        domains = await service.domain_summary(as_of=dt(14, 12))
        assert domains['total_domains'] == 2
        activity = await service.revision_activity(start=dt(13), end=dt(15))
        assert activity['total_revisions'] == 3
        assert activity['series'][0]['revision_count'] == 2
        assert activity['series'][0]['unique_document_count'] == 1
        assert activity['series'][1]['revision_count'] == 1
        scoped = await service.revision_activity(start=dt(13), end=dt(15), source_domain='example.com')
        assert scoped['total_revisions'] == 2
        after = {key: await db[key].count_documents({}) for key in before}
        assert before == after
    finally:
        try:
            await client.drop_database(name)
        finally:
            await client.close()


@pytest.mark.skipif(os.getenv('WEBINTEL_RUN_MONGO_TESTS') != '1',
                    reason='MongoDB integration tests are opt-in')
def test_dashboard_mongodb_read_only():
    asyncio.run(exercise())
