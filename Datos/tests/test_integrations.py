import unittest

from Datos.integrations import merge_runtime_source, rapidapi_integration_status


class RapidApiIntegrationStatusTests(unittest.TestCase):
    def test_uses_fixture_when_key_is_missing(self):
        self.assertEqual(
            rapidapi_integration_status({}),
            {
                "service": "rapidapi",
                "configured": False,
                "source": "fixture",
                "missingCredentials": ["RAPIDAPI_KEY"],
            },
        )

    def test_uses_live_source_when_key_is_configured(self):
        status = rapidapi_integration_status({"RAPIDAPI_KEY": "local-key"})

        self.assertTrue(status["configured"])
        self.assertEqual(status["source"], "rapidapi")
        self.assertEqual(status["missingCredentials"], [])

    def test_runtime_fixture_reports_provider_failure_when_key_exists(self):
        status = merge_runtime_source(
            rapidapi_integration_status({"RAPIDAPI_KEY": "local-key"}),
            "fixture",
        )

        self.assertTrue(status["configured"])
        self.assertEqual(status["source"], "fixture")
        self.assertEqual(status["fallbackReason"], "live_api_unavailable")


if __name__ == "__main__":
    unittest.main()
