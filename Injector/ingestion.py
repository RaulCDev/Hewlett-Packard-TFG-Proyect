import json
import string
from pathlib import Path


EXAMPLE_VALUES = {"replace-me", "changeme"}
DEFAULT_HOST = "steam2.p.rapidapi.com"


def rapidapi_is_configured(environ):
    value = (environ.get("RAPIDAPI_KEY") or "").strip()
    return bool(value) and value.lower() not in EXAMPLE_VALUES


def _valid_games(payload):
    if not isinstance(payload, list):
        raise ValueError("RapidAPI response is not a game list")

    games_by_id = {}
    for game in payload:
        if isinstance(game, dict) and game.get("appId") and game.get("title"):
            normalized = dict(game)
            normalized["appId"] = str(normalized["appId"])
            games_by_id[normalized["appId"]] = normalized
    return list(games_by_id.values())


def load_fixture(path):
    fixture_path = Path(path)
    payload = json.loads(fixture_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("metadata"), dict):
        raise ValueError("RapidAPI fixture metadata is missing")
    if payload["metadata"].get("credentialsIncluded") is not False:
        raise ValueError("RapidAPI fixture credential marker is invalid")
    games = _valid_games(payload.get("games"))
    if not games:
        raise ValueError("RapidAPI fixture contains no valid games")
    return games


def fetch_live_games(session, key, host=DEFAULT_HOST, letters=string.ascii_uppercase):
    games_by_id = {}
    for letter in letters:
        response = session.get(
            f"https://{host}/search/{letter}/page/1",
            headers={
                "X-RapidAPI-Key": key,
                "X-RapidAPI-Host": host,
            },
            timeout=20,
        )
        response.raise_for_status()
        for game in _valid_games(response.json()):
            games_by_id[game["appId"]] = game
    if not games_by_id:
        raise ValueError("RapidAPI returned no valid games")
    return list(games_by_id.values())


def select_game_source(
    environ,
    fixture_path,
    session=None,
    letters=string.ascii_uppercase,
):
    if not rapidapi_is_configured(environ):
        return "fixture", load_fixture(fixture_path)

    if session is None:
        import requests

        session = requests.Session()

    try:
        games = fetch_live_games(
            session=session,
            key=environ["RAPIDAPI_KEY"].strip(),
            host=(environ.get("RAPIDAPI_HOST") or DEFAULT_HOST).strip(),
            letters=letters,
        )
        return "rapidapi", games
    except (OSError, RuntimeError, ValueError):
        return "fixture", load_fixture(fixture_path)


def chunk_games(games, size=50):
    if size < 1:
        raise ValueError("Chunk size must be positive")
    for index in range(0, len(games), size):
        yield games[index : index + size]
