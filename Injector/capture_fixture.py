import argparse
import json
import os
import string
from datetime import datetime, timezone
from pathlib import Path

import requests

from ingestion import DEFAULT_HOST, fetch_live_games, rapidapi_is_configured


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Capture a credential-free snapshot from the Steam RapidAPI."
    )
    parser.add_argument(
        "--output",
        default="data/rapidapi-steam-games.json",
        help="Path where the sanitized JSON snapshot will be written.",
    )
    return parser.parse_args()


def main():
    arguments = parse_arguments()
    if not rapidapi_is_configured(os.environ):
        raise SystemExit("RAPIDAPI_KEY is not configured")

    host = (os.getenv("RAPIDAPI_HOST") or DEFAULT_HOST).strip()
    games = fetch_live_games(
        session=requests.Session(),
        key=os.environ["RAPIDAPI_KEY"].strip(),
        host=host,
        letters=string.ascii_uppercase,
    )
    if len(games) < 200:
        raise SystemExit(
            f"Capture rejected: expected at least 200 unique games, received {len(games)}"
        )

    payload = {
        "metadata": {
            "provider": "RapidAPI",
            "api": "Steam",
            "listing": "https://rapidapi.com/psimavel/api/steam2",
            "host": host,
            "endpointPattern": f"https://{host}/search/{{letter}}/page/1",
            "letters": "A-Z",
            "capturedAt": datetime.now(timezone.utc).isoformat(),
            "credentialsIncluded": False,
            "recordCount": len(games),
        },
        "games": games,
    }
    output_path = Path(arguments.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Captured {len(games)} games from {host} into {output_path}")


if __name__ == "__main__":
    main()
