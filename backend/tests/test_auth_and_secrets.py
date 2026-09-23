import json
from unittest.mock import MagicMock, patch
from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient

from core.models import UserActivityLog
from core.secrets_manager import SecretsManager


class SecretsManagerTestCase(TestCase):
    def tearDown(self):
        sm = SecretsManager()
        sm.reload()

    def test_secrets_manager_local_json(self):
        sm = SecretsManager()
        sm.reload()
        val = sm.get("DJANGO_DEBUG")
        self.assertIsNotNone(val)

    @patch("boto3.client")
    def test_secrets_manager_aws_fallback(self, mock_boto_client):
        mock_client_instance = MagicMock()
        mock_client_instance.get_secret_value.return_value = {
            "SecretString": json.dumps({"MOCK_KEY": "AWS_SECRET_VALUE"})
        }
        mock_boto_client.return_value = mock_client_instance

        with patch.dict("os.environ", {"SECRETS_SOURCE": "AWS", "AWS_SECRETS_MANAGER_NAME": "test/sec"}):
            sm = SecretsManager()
            sm.reload()
            self.assertEqual(sm.get("MOCK_KEY"), "AWS_SECRET_VALUE")


class AuthAndActivityLogTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_user_registration_and_activity_logging(self):
        response = self.client.post("/api/auth/register/", {
            "username": "testsecops",
            "email": "secops@metronlabs.com",
            "password": "SecurePassword123!",
            "first_name": "Security",
            "last_name": "Admin",
        }, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.data.get("authenticated"))
        self.assertEqual(response.data["user"]["username"], "testsecops")

        # Verify UserActivityLog was created
        log_entry = UserActivityLog.objects.filter(action="USER_REGISTER").first()
        self.assertIsNotNone(log_entry)
        self.assertEqual(log_entry.username, "testsecops")

    def test_user_login_success_and_logout(self):
        user = User.objects.create_user(
            username="analyst1",
            email="analyst@metronlabs.com",
            password="AnalystPassword123!",
        )

        # Login with email
        login_resp = self.client.post("/api/auth/login/", {
            "email": "analyst@metronlabs.com",
            "password": "AnalystPassword123!",
        }, format="json")
        self.assertEqual(login_resp.status_code, 200)
        self.assertTrue(login_resp.data.get("authenticated"))

        # Check me
        me_resp = self.client.get("/api/auth/me/")
        self.assertEqual(me_resp.status_code, 200)
        self.assertTrue(me_resp.data.get("authenticated"))

        # Logout
        logout_resp = self.client.post("/api/auth/logout/")
        self.assertEqual(logout_resp.status_code, 200)

        # Verify activity logs
        self.assertTrue(UserActivityLog.objects.filter(action="USER_LOGIN").exists())
        self.assertTrue(UserActivityLog.objects.filter(action="USER_LOGOUT").exists())

    def test_google_sso_endpoint(self):
        response = self.client.post("/api/auth/google/", {
            "email": "googlesso@company.com",
            "name": "Google User",
            "google_id": "google-oauth2-10928374",
        }, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data.get("authenticated"))
        self.assertEqual(response.data["user"]["email"], "googlesso@company.com")
        self.assertTrue(UserActivityLog.objects.filter(action="GOOGLE_SSO_LOGIN").exists())
