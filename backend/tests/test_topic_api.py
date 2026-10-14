from fastapi.testclient import TestClient
from app.api.main import create_app
from app.api.routes.topic_analytics import get_topic_service


class FakeTopicService:
    async def topics(self, **kw):
        return {'terms': [{'term': 'pipeline', 'document_frequency': 1}], 'document_count': 1}
    async def domains(self, **kw):
        return {'domains': [{'source_domain': 'example.com', 'document_count': 1, 'terms': []}]}
    async def trends(self, **kw):
        return {'before_document_count': 1, 'after_document_count': 1, 'terms': []}


def app_with_fake():
    app = create_app(connect_db=False)
    app.dependency_overrides[get_topic_service] = lambda: FakeTopicService()
    return app


def test_no_db_is_503():
    with TestClient(create_app(connect_db=False)) as c:
        assert c.get('/api/v1/analytics/topics').status_code == 503


def test_topic_response():
    with TestClient(app_with_fake()) as c:
        r = c.get('/api/v1/analytics/topics?limit=5')
        assert r.status_code == 200 and r.json()['terms'][0]['term'] == 'pipeline'


def test_domain_response():
    with TestClient(app_with_fake()) as c:
        assert c.get('/api/v1/analytics/topics/domains').status_code == 200


def test_trend_response():
    with TestClient(app_with_fake()) as c:
        r = c.get('/api/v1/analytics/topics/trends', params={
            'before_start': '2026-10-01T00:00:00Z', 'before_end': '2026-10-02T00:00:00Z',
            'after_start': '2026-10-02T00:00:00Z', 'after_end': '2026-10-03T00:00:00Z',
        })
        assert r.status_code == 200


def test_missing_window_is_422():
    with TestClient(app_with_fake()) as c:
        assert c.get('/api/v1/analytics/topics/trends').status_code == 422


def test_invalid_params_422():
    with TestClient(app_with_fake()) as c:
        assert c.get('/api/v1/analytics/topics?ngrams=3').status_code == 422
        assert c.get('/api/v1/analytics/topics?limit=0').status_code == 422


def test_registered_in_openapi():
    with TestClient(app_with_fake()) as c:
        paths = c.get('/openapi.json').json()['paths']
        assert '/api/v1/analytics/topics' in paths
        assert '/api/v1/analytics/topics/trends' in paths
