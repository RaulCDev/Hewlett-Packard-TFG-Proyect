import json
import logging
import os
import time
from pathlib import Path

from kafka import KafkaProducer

from ingestion import chunk_games, select_game_source


logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
LOGGER = logging.getLogger("injector")
FIXTURE_PATH = Path(
    os.getenv(
        "RAPIDAPI_FIXTURE_PATH",
        str(Path(__file__).parent / "data" / "rapidapi-steam-games.json"),
    )
)


def connect_producer(attempts=30, retry_seconds=2):
    last_error = None
    for attempt in range(1, attempts + 1):
        try:
            return KafkaProducer(
                bootstrap_servers=["kafka:9092"],
                value_serializer=lambda value: json.dumps(value).encode("utf-8"),
            )
        except Exception as error:
            last_error = error
            LOGGER.warning("Kafka is not ready (attempt %s/%s)", attempt, attempts)
            time.sleep(retry_seconds)
    raise RuntimeError("Could not connect to Kafka") from last_error


def main():
    source, games = select_game_source(os.environ, FIXTURE_PATH)
    LOGGER.info("source=%s games=%s", source, len(games))
    games = [dict(game, dataSource=source) for game in games]

    producer = connect_producer()
    try:
        published = 0
        for batch in chunk_games(games, size=50):
            producer.send("games", batch).get(timeout=30)
            published += len(batch)
        producer.flush(timeout=30)
        LOGGER.info("published=%s", published)
    finally:
        producer.close(timeout=30)


if __name__ == "__main__":
    main()
