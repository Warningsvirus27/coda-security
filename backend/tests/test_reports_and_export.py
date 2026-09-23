from django.test import TestCase
from rest_framework.test import APIClient
from core.models import Alert, CodaDocument, ExportHistory
from tests.factories import UserFactory, CodaDocumentFactory, AlertFactory


class ReportExportTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = UserFactory(username="compliance_officer")
        self.client.force_authenticate(user=self.user)

        self.doc = CodaDocumentFactory(name="Audit Target Document")
        self.alert = AlertFactory(document=self.doc, severity=Alert.Severity.CRITICAL)

    def test_export_html_report(self):
        resp = self.client.post("/api/reports/export/", {
            "format": "html",
            "title": "Q3 Exposure Audit",
            "options": {"category": "all", "include_audit_trail": True},
        }, format="json")

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp["Content-Type"], "text/html; charset=utf-8")
        self.assertIn("SecureCoda", resp.content.decode("utf-8"))

        # Verify ExportHistory created
        history = ExportHistory.objects.filter(format="html").first()
        self.assertIsNotNone(history)
        self.assertEqual(history.title, "Q3 Exposure Audit")

    def test_export_pdf_report(self):
        resp = self.client.post("/api/reports/export/", {
            "format": "pdf",
            "title": "Executive Compliance Summary",
            "options": {"category": "all"},
        }, format="json")

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp["Content-Type"], "application/pdf")
        self.assertTrue(len(resp.content) > 100)
        self.assertTrue(resp.content.startswith(b"%PDF"))

    def test_re_export_with_saved_options(self):
        # 1. Create a historical record with custom options
        history_record = ExportHistory.objects.create(
            user=self.user,
            title="Custom Sensitivity Preset",
            format="html",
            options={"category": "sensitive_table", "severity": "critical"},
        )

        # 2. Call re-export endpoint
        resp = self.client.post(f"/api/reports/{history_record.id}/re-export/", {
            "format": "pdf",
        }, format="json")

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp["Content-Type"], "application/pdf")
        self.assertTrue(resp.content.startswith(b"%PDF"))

        # Check that a new history record was added reflecting the re-export
        self.assertEqual(ExportHistory.objects.count(), 2)

    def test_export_history_list(self):
        ExportHistory.objects.create(user=self.user, title="Run 1", format="html")
        ExportHistory.objects.create(user=self.user, title="Run 2", format="pdf")

        resp = self.client.get("/api/reports/history/")
        self.assertEqual(resp.status_code, 200)
        self.assertGreaterEqual(len(resp.data), 2)
