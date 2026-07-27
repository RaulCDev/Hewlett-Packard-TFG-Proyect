import unittest

from Consumidor_Base.normalization import normalize_game


class GameNormalizationTests(unittest.TestCase):
    def test_extracts_review_percentage(self):
        normalized = normalize_game(
            {
                "appId": "730",
                "title": "Counter-Strike 2",
                "reviewSummary": "Very Positive (87%)",
            }
        )

        self.assertEqual(normalized["reviewPercentage"], 87)

    def test_rejects_game_without_app_id(self):
        self.assertIsNone(normalize_game({"title": "Missing id"}))

    def test_does_not_mutate_input(self):
        original = {"appId": "730", "title": "Counter-Strike 2"}

        normalize_game(original)

        self.assertNotIn("reviewPercentage", original)


if __name__ == "__main__":
    unittest.main()
