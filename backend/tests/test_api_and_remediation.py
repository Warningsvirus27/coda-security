from datetime import timedelta
from unittest.mock import MagicMock, patch
from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from core.models import Alert, AuditLog, CodaDocument, ScanConfig, UserActivityLog


class ConfigAndRemediationTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="remediator",
            email="remediator@metronlabs.com",
            password="Password123!",
        )
        self.client.force_authenticate(user=self.user)

        self.doc = CodaDocument.objects.create(
            doc_id="doc-test-101",
            name="Confidential Employee Payroll",
            owner_email="hr@metronlabs.com",
            created_at=timezone.now() - timedelta(days=120),
            updated_at=timezone.now() - timedelta(days=100),
            is_published=False,
            sharing_mode="org",
        )

        self.alert = Alert.objects.create(
            document=self.doc,
            category=Alert.Category.SENSITIVE_TABLE,
            severity=Alert.Severity.CRITICAL,
            status=Alert.Status.OPEN,
            title="Exposed SSN in Table Row",
            description="Found Social Security Number pattern in column TaxID.",
            metadata={
                "table_id": "tbl_payroll",
                "row_id": "row_9918",
                "column_name": "TaxID",
            },
            fingerprint="test-fingerprint-ssn-1",
        )

    def test_get_and_update_scan_config_timeframe(self):
        # 1. Get config
        resp = self.client.get("/api/config/")
        self.assertEqual(resp.status_code, 200)

        # 2. Update timeframe to 48 hours
        put_resp = self.client.put("/api/config/", {
            "unused_threshold_value": 48,
            "unused_threshold_unit": "hours",
            "scan_interval_minutes": 30,
        }, format="json")
        self.assertEqual(put_resp.status_code, 200)
        self.assertEqual(put_resp.data["unused_threshold_value"], 48)
        self.assertEqual(put_resp.data["unused_threshold_unit"], "hours")

        # 3. Check Slack status endpoint
        slack_resp = self.client.get("/api/config/slack-status/")
        self.assertEqual(slack_resp.status_code, 200)
        self.assertEqual(slack_resp.data["status"], "PENDING")

    @patch("scanner.coda_client.CodaClient.whoami")
    def test_validate_token_endpoint(self, mock_whoami):
        mock_whoami.return_value = {
            "valid": True,
            "user": {"name": "Admin Tester", "userEmail": "admin@coda.io"},
        }
        resp = self.client.post("/api/config/validate-token/", {
            "token": "valid-test-coda-token-12345",
        }, format="json")
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.data["valid"])

    def test_alerts_list_and_stats(self):
        # List alerts
        list_resp = self.client.get("/api/alerts/")
        self.assertEqual(list_resp.status_code, 200)
        self.assertGreaterEqual(len(list_resp.data.get("results", list_resp.data)), 1)

        # Stats
        stats_resp = self.client.get("/api/alerts/stats/")
        self.assertEqual(stats_resp.status_code, 200)
        self.assertIn("critical_alerts", stats_resp.data)
        self.assertGreaterEqual(stats_resp.data["critical_alerts"], 1)

    @patch("scanner.coda_client.CodaClient.update_row")
    def test_remediation_redact_row_action(self, mock_update_row):
        mock_update_row.return_value = {"id": "row_9918"}

        resp = self.client.post("/api/remediation/execute/", {
            "alert_id": str(self.alert.id),
            "action_name": "redact_row",
        }, format="json")

        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.data["success"])

        # Refresh alert
        self.alert.refresh_from_db()
        self.assertEqual(self.alert.status, Alert.Status.RESOLVED)
        self.assertEqual(self.alert.resolved_by_user, self.user)

        # Check AuditLog
        audit = AuditLog.objects.filter(alert=self.alert).first()
        self.assertIsNotNone(audit)
        self.assertEqual(audit.action_type, "redact_row")
        self.assertEqual(audit.user, self.user)
        self.assertTrue(audit.success)
