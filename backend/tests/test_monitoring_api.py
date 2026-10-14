from fastapi.testclient import TestClient
from app.api.main import create_app
from app.api.routes.monitoring import get_monitoring_service

class Fake:
    async def overview(self, **kwargs):
        return {'document_count': 2, 'coverage_ratio': 0.5}
    async def documents_status(self, **kwargs):
        return {'total_matching': 1, 'items': []}
    async def domains(self, **kwargs):
        return {'domains': []}

def app_with_fake():
    app = create_app(connect_db=False)
    app.dependency_overrides[get_monitoring_service] = lambda: Fake()
    return app

def test_no_database_503():
    with TestClient(create_app(connect_db=False)) as c:
        assert c.get('/api/v1/analytics/monitoring/overview').status_code == 503

def test_overview():
    with TestClient(app_with_fake()) as c:
        r = c.get('/api/v1/analytics/monitoring/overview')
        assert r.status_code == 200
        assert r.json()['coverage_ratio'] == 0.5

def test_documents():
    with TestClient(app_with_fake()) as c:
        assert c.get('/api/v1/analytics/monitoring/documents?status=unknown').status_code == 200

def test_domains():
    with TestClient(app_with_fake()) as c:
        assert c.get('/api/v1/analytics/monitoring/domains').status_code == 200

def test_invalid_limit():
    with TestClient(app_with_fake()) as c:
        assert c.get('/api/v1/analytics/monitoring/documents?limit=101').status_code == 422

def test_invalid_status():
    with TestClient(app_with_fake()) as c:
        assert c.get('/api/v1/analytics/monitoring/documents?status=outdated').status_code == 422

def test_openapi():
    with TestClient(app_with_fake()) as c:
        paths = c.get('/openapi.json').json()['paths']
        assert '/api/v1/analytics/monitoring/overview' in paths
