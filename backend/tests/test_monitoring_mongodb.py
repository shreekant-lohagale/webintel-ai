import asyncio
import os
from datetime import datetime, timedelta, timezone
from uuid import uuid4
import pytest
from app.storage.mongodb import create_client
from app.intelligence.monitoring import MonitoringService

NOW = datetime(2026, 10, 14, 12, tzinfo=timezone.utc)

async def integration():
    client = create_client()
    name = 'webintel_monitoring_test_' + uuid4().hex
    db = client[name]
    try:
        await db['documents'].insert_many([
            {'_id': 'a', 'document_id': 'a', 'title': 'A', 'source_domain': 'example.com', 'document_type': 'article'},
            {'_id': 'b', 'document_id': 'b', 'title': 'B', 'source_domain': 'example.com', 'document_type': 'article'},
            {'_id': 'c', 'document_id': 'c', 'title': 'C', 'source_domain': 'other.org', 'document_type': 'quote'},
        ])
        await db['source_observations'].insert_many([
            {'_id':'o1', 'document_id':'a', 'source_url':'https://example.com/a', 'extraction_method':'scrapy', 'first_seen_at':NOW-timedelta(days=2), 'last_seen_at':NOW-timedelta(hours=2)},
            {'_id':'o2', 'document_id':'a', 'source_url':'https://example.com/a', 'extraction_method':'playwright', 'first_seen_at':NOW-timedelta(days=2), 'last_seen_at':NOW-timedelta(hours=3)},
            {'_id':'o3', 'document_id':'b', 'source_url':'https://example.com/b', 'extraction_method':'scrapy', 'first_seen_at':NOW-timedelta(days=20), 'last_seen_at':NOW-timedelta(days=10)},
        ])
        await db['document_revisions'].insert_many([
            {'_id':'r1', 'document_id':'a', 'observed_at':NOW},
            {'_id':'r2', 'document_id':'a', 'observed_at':NOW-timedelta(days=1)},
        ])
        before = {name: await db[name].find({}, {'_id':0}).sort('_id',1).to_list(length=None)
                  for name in ('documents','source_observations','document_revisions')}
        service = MonitoringService(db)
        overview = await service.overview(now=NOW)
        assert overview['document_count'] == 3
        assert overview['observed_document_count'] == 2
        assert overview['unobserved_document_count'] == 1
        assert overview['coverage_ratio'] == 0.6667
        assert overview['status_counts']['recently_observed'] == 1
        assert overview['status_counts']['stale_observation'] == 1
        assert overview['status_counts']['unknown'] == 1
        detail = await service.documents_status(now=NOW)
        a = next(x for x in detail['items'] if x['document_id'] == 'a')
        assert a['provenance_record_count'] == 2
        assert a['distinct_source_url_count'] == 1
        assert a['revision_count'] == 2
        assert a['extraction_methods'] == ['playwright', 'scrapy']
        domains = await service.domains(now=NOW)
        assert [d['source_domain'] for d in domains['domains']] == ['example.com','other.org']
        assert domains['domains'][0]['coverage_ratio'] == 1
        example = await service.overview(domain='example.com', now=NOW)
        assert example['document_count'] == 2
        after = {name: await db[name].find({}, {'_id':0}).sort('_id',1).to_list(length=None)
                 for name in ('documents','source_observations','document_revisions')}
        assert before == after
    finally:
        await client.drop_database(name)
        await client.close()

@pytest.mark.skipif(os.getenv('WEBINTEL_RUN_MONGO_TESTS') != '1', reason='MongoDB opt-in')
def test_monitoring_read_only_integration():
    asyncio.run(integration())
