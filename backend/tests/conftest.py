import json
from pathlib import Path
import pytest
from rest_framework.test import APIClient
from tests.factories import UserFactory, CodaDocumentFactory, AlertFactory


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def test_user(db):
    return UserFactory(username="test_secops_user")


@pytest.fixture
def auth_client(api_client, test_user):
    api_client.force_authenticate(user=test_user)
    return api_client


@pytest.fixture
def sample_document(db):
    return CodaDocumentFactory(name="Confidential Executive Compensation")


@pytest.fixture
def sample_alert(db, sample_document):
    return AlertFactory(document=sample_document, title="Exposed OAuth Client Secret")


@pytest.fixture
def fixture_coda_docs():
    fixture_path = Path(__file__).parent / "fixtures" / "sample_coda_docs.json"
    with open(fixture_path, "r", encoding="utf-8") as f:
        return json.load(f)
