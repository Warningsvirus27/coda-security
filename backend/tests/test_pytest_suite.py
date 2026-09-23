from unittest.mock import MagicMock
import pytest
from core.models import Alert, CodaDocument, UserActivityLog


@pytest.mark.django_db
def test_pytest_document_creation_fixture(sample_document):
    assert sample_document.id is not None
    assert "Compensation" in sample_document.name
    assert sample_document.days_since_update >= 0


@pytest.mark.django_db
def test_pytest_alert_fixture_and_stats(auth_client, sample_alert):
    resp = auth_client.get("/api/alerts/stats/")
    assert resp.status_code == 200
    assert resp.data["total_alerts"] >= 1


@pytest.mark.django_db
def test_pytest_activity_logging_on_scan_trigger(auth_client, monkeypatch):
    from core.models import ScanConfig
    config = ScanConfig.get_config()
    config.coda_api_token = "test-token-pytest"
    config.save()

    mock_task = MagicMock()
    mock_task.id = "mock-task-pytest-001"
    monkeypatch.setattr("scanner.tasks.run_full_scan.delay", MagicMock(return_value=mock_task))

    resp = auth_client.post("/api/scan/trigger/")
    assert resp.status_code == 202
    assert resp.data["task_id"] == "mock-task-pytest-001"
    assert UserActivityLog.objects.filter(action="SCAN_TRIGGERED").exists()


@pytest.mark.django_db
def test_sync_and_scan_require_coda_api_token(auth_client):
    from core.models import ScanConfig
    config = ScanConfig.get_config()
    config.coda_api_token = ""
    config.save()

    resp_sync = auth_client.post("/api/documents/sync/")
    assert resp_sync.status_code == 400
    assert "No Coda API key configured" in resp_sync.data["error"]

    resp_scan = auth_client.post("/api/scan/trigger/")
    assert resp_scan.status_code == 400
    assert "No Coda API key configured" in resp_scan.data["error"]


@pytest.mark.django_db
def test_user_activity_logs_scoped_to_logged_in_user(auth_client):
    from django.contrib.auth.models import User
    other_user = User.objects.create_user(username="other_user", password="password123")
    UserActivityLog.objects.create(user=other_user, username="other_user", action="LOGOUT", description="Other logged out")

    # Current user from auth_client
    resp = auth_client.get("/api/auth/activities/")
    assert resp.status_code == 200
    usernames = [item["username"] for item in resp.data["results"]]
@pytest.mark.django_db
def test_validate_coda_token_with_real_coda_whoami_response(auth_client, monkeypatch):
    """Real Coda v1 API returns {name, loginId, type, id} without any 'valid' key."""
    from unittest.mock import MagicMock
    real_coda_response = {
        "id": "u-12345",
        "type": "user",
        "name": "Jane Security",
        "loginId": "jane@example.com",
    }
    monkeypatch.setattr("scanner.coda_client.CodaClient._request", MagicMock(return_value=real_coda_response))

    resp = auth_client.post("/api/config/validate-token/", {"token": "Bearer real-coda-token-123"})
    assert resp.status_code == 200
    assert resp.data["valid"] is True
    assert "Jane Security" in resp.data["message"]
    assert resp.data["user"]["name"] == "Jane Security"
    assert resp.data["user"]["email"] == "jane@example.com"


@pytest.mark.django_db
def test_validate_coda_token_invalid_returns_400(auth_client, monkeypatch):
    from unittest.mock import MagicMock
    from scanner.coda_client import CodaAPIError

    def mock_request(*args, **kwargs):
        raise CodaAPIError("API error 401: Unauthorized", status_code=401)

    monkeypatch.setattr("scanner.coda_client.CodaClient._request", mock_request)

    resp = auth_client.post("/api/config/validate-token/", {"token": "invalid-token"})
    assert resp.status_code == 400
    assert resp.data["valid"] is False
    assert "Authentication failed with Coda API" in resp.data["message"]


def test_fixture_json_loading(fixture_coda_docs):
    assert len(fixture_coda_docs) == 2
    assert fixture_coda_docs[0]["id"] == "doc_fixture_01"


