import json
import tempfile
import unittest
from pathlib import Path

from Injector.ingestion import chunk_games, select_game_source


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


class FakeSession:
    def __init__(self, payload):
        self.payload = payload
        self.calls = []

    def get(self, url, headers, timeout):
        self.calls.append((url, headers, timeout))
        return FakeResponse(self.payload)


class IngestionSourceTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.fixture_path = Path(self.temporary_directory.name) / "games.json"
        self.fixture_games = [
            {
                "appId": "10",
                "title": "Counter-Strike",
                "url": "https://store.steampowered.com/app/10",
                "imgUrl": "https://example.test/10.jpg",
                "released": "1 Nov, 2000",
            }
        ]
        self.fixture_path.write_text(
            json.dumps(
                {
                    "metadata": {
                        "provider": "RapidAPI",
                        "api": "Steam",
                        "host": "steam2.p.rapidapi.com",
                        "credentialsIncluded": False,
                    },
                    "games": self.fixture_games,
                }
            ),
            encoding="utf-8",
        )

    def tearDown(self):
        self.temporary_directory.cleanup()

    def test_missing_key_uses_fixture_without_http_call(self):
        session = FakeSession([])

        source, games = select_game_source(
            {}, self.fixture_path, session=session, letters=("A",)
        )

        self.assertEqual(source, "fixture")
        self.assertEqual(games, self.fixture_games)
        self.assertEqual(session.calls, [])

    def test_configured_key_uses_live_response(self):
        live_games = [dict(self.fixture_games[0], appId="20")]
        session = FakeSession(live_games)

        source, games = select_game_source(
            {
                "RAPIDAPI_KEY": "local-key",
                "RAPIDAPI_HOST": "steam2.p.rapidapi.com",
            },
            self.fixture_path,
            session=session,
            letters=("A",),
        )

        self.assertEqual(source, "rapidapi")
        self.assertEqual(games, live_games)

    def test_invalid_live_payload_uses_fixture(self):
        session = FakeSession({"message": "Invalid API key"})

        source, games = select_game_source(
            {"RAPIDAPI_KEY": "invalid-key"},
            self.fixture_path,
            session=session,
            letters=("A",),
        )

        self.assertEqual(source, "fixture")
        self.assertEqual(games, self.fixture_games)

    def test_chunks_preserve_all_games(self):
        games = [dict(self.fixture_games[0], appId=str(index)) for index in range(5)]

        chunks = list(chunk_games(games, size=2))

        self.assertEqual([len(chunk) for chunk in chunks], [2, 2, 1])
        self.assertEqual([game for chunk in chunks for game in chunk], games)

    def test_committed_fixture_is_large_unique_and_secret_free(self):
        fixture_path = (
            Path(__file__).resolve().parents[1]
            / "data"
            / "rapidapi-steam-games.json"
        )
        payload = json.loads(fixture_path.read_text(encoding="utf-8"))
        games = payload["games"]

        self.assertGreaterEqual(len(games), 200)
        self.assertEqual(len({game["appId"] for game in games}), len(games))
        self.assertEqual(payload["metadata"]["recordCount"], len(games))
        self.assertFalse(payload["metadata"]["credentialsIncluded"])
        serialized = json.dumps(payload).lower()
        for secret_name in (
            "x-rapidapi-key",
            "google_client_secret",
            "authorization",
        ):
            self.assertNotIn(secret_name, serialized)


if __name__ == "__main__":
    unittest.main()
