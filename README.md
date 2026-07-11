# HPE CDS Full Stack Reference Project

End-to-end reference application built with Next.js, Flask, Spring Cloud Eureka and Zuul, Kafka, MongoDB, and Docker Compose.

## Local configuration

1. Create a local `.env` file from `.env.example`.
2. Replace every placeholder with a newly generated credential.
3. Start the stack with `docker compose up --build`.

The `.env` file and local MongoDB data are intentionally excluded from Git. Never commit real credentials.
