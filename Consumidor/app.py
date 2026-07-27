import json
import logging
import time

import requests
from kafka import KafkaConsumer
from kafka.errors import KafkaError


logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
LOGGER = logging.getLogger("consumer")


def connect_consumer(attempts=30, retry_seconds=2):
    last_error = None
    for attempt in range(1, attempts + 1):
        try:
            return KafkaConsumer(
                "games",
                bootstrap_servers=["kafka:9092"],
                auto_offset_reset="earliest",
                enable_auto_commit=False,
                group_id="greenlake-checker-group",
                value_deserializer=lambda value: json.loads(value.decode("utf-8")),
            )
        except KafkaError as error:
            last_error = error
            LOGGER.warning("Kafka is not ready (attempt %s/%s)", attempt, attempts)
            time.sleep(retry_seconds)
    raise RuntimeError("Could not connect to Kafka") from last_error


def main():
    consumer = connect_consumer()
    try:
        for message in consumer:
            response = requests.post(
                "http://consumidor-base:4002/save_games",
                json=message.value,
                timeout=30,
            )
            response.raise_for_status()
            consumer.commit()
            LOGGER.info("persisted_batch=%s", len(message.value))
    finally:
        consumer.close()


if __name__ == "__main__":
    main()
