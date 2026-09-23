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
    mock_task = MagicMock()
    mock_task.id = "mock-task-pytest-001"
    monkeypatch.setattr("scanner.tasks.run_full_scan.delay", MagicMock(return_value=mock_task))

    resp = auth_client.post("/api/scan/trigger/")
    assert resp.status_code == 202
    assert resp.data["task_id"] == "mock-task-pytest-001"
    assert UserActivityLog.objects.filter(action="SCAN_TRIGGERED").exists()


def test_fixture_json_loading(fixture_coda_docs):
    assert len(fixture_coda_docs) == 2
    assert fixture_coda_docs[0]["id"] == "doc_fixture_01"
