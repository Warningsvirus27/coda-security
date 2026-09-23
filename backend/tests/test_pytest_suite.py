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
    assert "other_user" not in usernames


def test_fixture_json_loading(fixture_coda_docs):
    assert len(fixture_coda_docs) == 2
    assert fixture_coda_docs[0]["id"] == "doc_fixture_01"

