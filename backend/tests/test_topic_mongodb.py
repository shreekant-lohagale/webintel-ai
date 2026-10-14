import asyncio
import os
from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.intelligence.topic_service import TopicService
from app.storage.mongodb import create_client


def ts(day):
    return datetime(2026, 10, day, tzinfo=timezone.utc)


async def exercise():
    client = create_client()
    name = 'webintel_topics_test_' + uuid4().hex
    db = client[name]
    try:
        await db['documents'].insert_many([
            {'document_id': 'd1', 'source_domain': 'example.com', 'content': 'python pipelines'},
            {'document_id': 'd2', 'source_domain': 'other.com', 'content': 'cloud systems'},
        ])
        await db['document_revisions'].insert_many([
            {'revision_id': 'r1', 'document_id': 'd1', 'observed_at': ts(1), 'content': 'python pipelines'},
            {'revision_id': 'r2', 'document_id': 'd1', 'observed_at': ts(3), 'content': 'cloud pipelines'},
            {'revision_id': 'r3', 'document_id': 'd2', 'observed_at': ts(1), 'content': 'cloud systems'},
            {'revision_id': 'r4', 'document_id': 'd2', 'observed_at': ts(3), 'content': 'cloud cloud systems'},
        ])
        before = {
            'documents': await db['documents'].count_documents({}),
            'revisions': await db['document_revisions'].count_documents({}),
        }
        svc = TopicService(db)
        result = await svc.topics()
        assert result['document_count'] == 2
        assert {x['term'] for x in result['terms']} >= {'python', 'cloud'}
        domains = await svc.domains()
        assert len(domains['domains']) == 2
        trends = await svc.trends(before_start=ts(1), before_end=ts(2), after_start=ts(3), after_end=ts(4))
        lookup = {x['term']: x for x in trends['terms']}
        assert lookup['python']['status'] == 'disappeared'
        assert lookup['cloud']['delta'] == 1
        scoped = await svc.trends(before_start=ts(1), before_end=ts(2), after_start=ts(3), after_end=ts(4), domain='example.com')
        assert scoped['before_document_count'] == 1
        assert scoped['after_document_count'] == 1
        after = {
            'documents': await db['documents'].count_documents({}),
            'revisions': await db['document_revisions'].count_documents({}),
        }
        assert before == after
    finally:
        try:
            await client.drop_database(name)
        finally:
            await client.close()


@pytest.mark.skipif(os.getenv('WEBINTEL_RUN_MONGO_TESTS') != '1', reason='MongoDB integration tests are opt-in')
def test_topics_mongodb_non_destructive():
    asyncio.run(exercise())
