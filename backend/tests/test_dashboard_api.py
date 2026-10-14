from fastapi.testclient import TestClient
from app.api.main import create_app
from app.api.routes.dashboard import get_dashboard_service


class FakeDashboardService:
    async def summary(self, **kwargs):
        return {'kpis': {'document_count': 2}, 'top_topics': []}

    async def revision_activity(self, **kwargs):
        return {'total_revisions': 3, 'series': []}

    async def domain_summary(self, **kwargs):
        return {'domains': [{'source_domain': 'example.com'}]}


def app_with_fake():
    app = create_app(connect_db=False)
    app.dependency_overrides[get_dashboard_service] = lambda: FakeDashboardService()
    return app


def test_no_database_returns_503():
    with TestClient(create_app(connect_db=False)) as client:
        assert client.get('/api/v1/analytics/dashboard/summary').status_code == 503


def test_summary_ok():
    with TestClient(app_with_fake()) as client:
        r = client.get('/api/v1/analytics/dashboard/summary')
        assert r.status_code == 200
        assert r.json()['kpis']['document_count'] == 2


def test_domains_ok():
    with TestClient(app_with_fake()) as client:
        assert client.get('/api/v1/analytics/dashboard/domains').status_code == 200


def test_activity_ok():
    with TestClient(app_with_fake()) as client:
        r = client.get('/api/v1/analytics/dashboard/revision-activity', params={
            'start': '2026-10-13T00:00:00Z', 'end': '2026-10-15T00:00:00Z'})
        assert r.status_code == 200 and r.json()['total_revisions'] == 3


def test_missing_time_is_422():
    with TestClient(app_with_fake()) as client:
        assert client.get('/api/v1/analytics/dashboard/revision-activity').status_code == 422


def test_invalid_limit_is_422():
    with TestClient(app_with_fake()) as client:
        assert client.get('/api/v1/analytics/dashboard/summary?top_k=100').status_code == 422


def test_bad_domain_is_422():
    with TestClient(app_with_fake()) as client:
        assert client.get('/api/v1/analytics/dashboard/summary?source_domain=bad@domain').status_code == 422


def test_openapi_registered():
    with TestClient(app_with_fake()) as client:
        paths = client.get('/openapi.json').json()['paths']
        assert '/api/v1/analytics/dashboard/summary' in paths
        assert '/api/v1/analytics/dashboard/revision-activity' in paths
        assert '/api/v1/analytics/dashboard/domains' in paths
