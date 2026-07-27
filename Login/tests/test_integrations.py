import unittest
from urllib.parse import parse_qs, urlparse

from Login.integrations import (
    build_google_authorization_url,
    google_identity_from_claims,
    google_integration_status,
    redact_oauth_callback_log,
)


class GoogleIntegrationStatusTests(unittest.TestCase):
    def test_lists_both_missing_credentials(self):
        self.assertEqual(
            google_integration_status({}),
            {
                "service": "google",
                "configured": False,
                "missingCredentials": [
                    "GOOGLE_CLIENT_ID",
                    "GOOGLE_CLIENT_SECRET",
                ],
            },
        )

    def test_accepts_complete_credentials(self):
        status = google_integration_status(
            {
                "GOOGLE_CLIENT_ID": "client.apps.googleusercontent.com",
                "GOOGLE_CLIENT_SECRET": "local-secret",
            }
        )

        self.assertTrue(status["configured"])
        self.assertEqual(status["missingCredentials"], [])

    def test_rejects_example_markers(self):
        status = google_integration_status(
            {
                "GOOGLE_CLIENT_ID": "replace-me",
                "GOOGLE_CLIENT_SECRET": "changeme",
            }
        )

        self.assertFalse(status["configured"])

    def test_builds_authorization_url_with_exact_callback_and_state(self):
        url = build_google_authorization_url(
            {
                "GOOGLE_CLIENT_ID": "client.apps.googleusercontent.com",
                "GOOGLE_CLIENT_SECRET": "local-secret",
            },
            redirect_uri="http://localhost:8081/api/login/callback",
            state="per-request-state",
        )

        parsed = urlparse(url)
        query = parse_qs(parsed.query)
        self.assertEqual(parsed.scheme, "https")
        self.assertEqual(parsed.netloc, "accounts.google.com")
        self.assertEqual(query["client_id"], ["client.apps.googleusercontent.com"])
        self.assertEqual(
            query["redirect_uri"],
            ["http://localhost:8081/api/login/callback"],
        )
        self.assertEqual(query["state"], ["per-request-state"])


class GoogleIdentityTests(unittest.TestCase):
    def test_uses_google_name_when_present(self):
        identity = google_identity_from_claims(
            {"email": "person@example.com", "name": "Example Person"}
        )

        self.assertEqual(identity["email"], "person@example.com")
        self.assertEqual(identity["name"], "Example Person")

    def test_uses_email_prefix_when_name_claim_is_absent(self):
        identity = google_identity_from_claims({"email": "person@example.com"})

        self.assertEqual(identity["name"], "person")

    def test_rejects_identity_without_email(self):
        with self.assertRaises(ValueError):
            google_identity_from_claims({"name": "Example Person"})


class OAuthLogRedactionTests(unittest.TestCase):
    def test_redacts_callback_query_parameters(self):
        access_log = (
            "GET /callback?state=private-state&code=private-code&scope=openid "
            "HTTP/1.1"
        )

        redacted = redact_oauth_callback_log(access_log)

        self.assertEqual(
            redacted,
            "GET /callback?<oauth-parameters-redacted> HTTP/1.1",
        )
        self.assertNotIn("private-state", redacted)
        self.assertNotIn("private-code", redacted)


if __name__ == "__main__":
    unittest.main()
