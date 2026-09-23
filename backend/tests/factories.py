import uuid
import factory
from django.contrib.auth.models import User
from django.utils import timezone
from faker import Faker
from core.models import Alert, AuditLog, CodaDocument, ScanConfig

fake = Faker()


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f"analyst_{n}_{uuid.uuid4().hex[:6]}")
    email = factory.LazyAttribute(lambda o: f"{o.username}@metronlabs.com")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    is_active = True


class CodaDocumentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CodaDocument

    doc_id = factory.Sequence(lambda n: f"doc_{n}_{uuid.uuid4().hex[:8]}")
    name = factory.Faker("catch_phrase")
    owner_email = factory.Faker("company_email")
    created_at = factory.LazyFunction(timezone.now)
    updated_at = factory.LazyFunction(timezone.now)
    is_published = False
    sharing_mode = "private"
    browser_link = factory.LazyAttribute(lambda o: f"https://coda.io/d/{o.doc_id}")


class AlertFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Alert

    document = factory.SubFactory(CodaDocumentFactory)
    category = Alert.Category.SENSITIVE_TABLE
    severity = Alert.Severity.CRITICAL
    status = Alert.Status.OPEN
    title = factory.Faker("sentence", nb_words=6)
    description = factory.Faker("text", max_nb_chars=120)
    metadata = factory.LazyFunction(lambda: {
        "table_id": "tbl_credentials",
        "row_id": "row_9912",
        "column_name": "API_Key",
        "masked_value": "sk_live_••••9921",
    })
    fingerprint = factory.Sequence(lambda n: f"fingerprint_{n}_{uuid.uuid4().hex}")


class AuditLogFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = AuditLog

    alert = factory.SubFactory(AlertFactory)
    user = factory.SubFactory(UserFactory)
    action_type = "redact_row"
    performed_by = factory.LazyAttribute(lambda o: o.user.username)
    details = factory.LazyFunction(lambda: {"column": "API_Key", "action": "redact"})
    success = True
