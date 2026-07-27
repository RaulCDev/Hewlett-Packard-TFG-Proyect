import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from ingestion import _valid_games


PUBLIC_FIELDS = (
    "appId",
    "title",
    "url",
    "imgUrl",
    "released",
    "reviewSummary",
    "price",
    "reviewPercentage",
)


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Build the credential-free RapidAPI fallback from a games-only Mongo export."
    )
    parser.add_argument("input", help="Path to the games-only mongoexport JSON array.")
    parser.add_argument("output", help="Path to the fallback JSON file to create.")
    return parser.parse_args()


def sanitize_games(payload):
    public_games = []
    for game in payload:
        if not isinstance(game, dict):
            continue
        sanitized = {field: game[field] for field in PUBLIC_FIELDS if field in game}
        if isinstance(sanitized.get("price"), str):
            sanitized["price"] = sanitized["price"].strip()
        public_games.append(sanitized)
    return sorted(_valid_games(public_games), key=lambda game: game["title"].casefold())


def main():
    arguments = parse_arguments()
    source_path = Path(arguments.input)
    output_path = Path(arguments.output)
    games = sanitize_games(json.loads(source_path.read_text(encoding="utf-8")))
    if len(games) < 200:
        raise SystemExit(
            f"Fixture rejected: expected at least 200 unique games, received {len(games)}"
        )

    payload = {
        "metadata": {
            "provider": "RapidAPI",
            "api": "Steam2",
            "listing": "https://rapidapi.com/psimavel/api/steam2",
            "host": "steam2.p.rapidapi.com",
            "endpointPattern": "https://steam2.p.rapidapi.com/search/{term}/page/{page}",
            "source": "Historical project MongoDB snapshot from git commit 8042bd0",
            "sourcePeriod": "2023",
            "exportedAt": datetime.now(timezone.utc).isoformat(),
            "credentialsIncluded": False,
            "recordCount": len(games),
        },
        "games": games,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Built fallback with {len(games)} games at {output_path}")


if __name__ == "__main__":
    main()
