# Portable Compose and Optional Credentials Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the complete application start with Docker Compose on a clean machine, preserve live Google OAuth and RapidAPI integrations, and provide explicit credential modals plus a real local RapidAPI dataset when credentials are absent.

**Architecture:** Keep the existing Next.js, Flask, Spring Cloud, Kafka and MongoDB services. Make external integrations report a stable configuration status, move RapidAPI source selection into testable Python functions, and let the frontend render one reusable modal from those status responses. Repair container builds and startup ordering without replacing the original distributed architecture.

**Tech Stack:** Docker Compose, Next.js 13/React 18/TypeScript/Tailwind, Flask/Python 3.9, Spring Boot/Java 11, Kafka, MongoDB, Python `unittest`, Vitest and Testing Library.

## Global Constraints

- `docker compose up --build` must work when no `.env` file exists.
- `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` and `RAPIDAPI_KEY` remain optional external credentials.
- `RAPIDAPI_HOST` defaults to exactly `steam2.p.rapidapi.com`.
- Google development callback remains exactly `http://localhost:8081/api/login/callback`.
- Browser entry points remain frontend `3000`, gateway `8081` and Eureka `8761`.
- No credential value or sensitive request header may be logged, committed, returned to the browser or stored in the fixture.
- The RapidAPI fixture must come from real responses fetched with the owner's local key and contain at least 200 unique games.
- Keep Kafka, Eureka, Zuul, MongoDB and all existing microservices.
- Every production-code behavior change follows red-green-refactor; configuration and generated fixture changes are verified with deterministic validation commands.

## File responsibility map

- `docker-compose.yml`: portable defaults, service graph, health conditions, ports and networks.
- `*/Dockerfile`: reproducible service images with pinned base-image families.
- `Login/integrations.py`: Google credential detection and public status payload.
- `Login/app.py`: local login plus guarded Google OAuth endpoints and health endpoint.
- `Injector/ingestion.py`: RapidAPI requests, fixture loading, validation, batching and source selection.
- `Injector/capture_fixture.py`: reproducible, secret-safe export of real RapidAPI responses.
- `Injector/data/rapidapi-steam-games.json`: committed real response snapshot and provenance metadata.
- `Injector/app.py`: retrying Kafka producer entry point.
- `Consumidor_Base/normalization.py`: validate and normalize game records before persistence.
- `Consumidor_Base/app.py`: persistence endpoint and health endpoint.
- `Datos/integrations.py`: public RapidAPI configuration status.
- `Datos/app.py`: games API, status and health endpoints, corrected ranking field.
- `front-next/src/components/CredentialModal.tsx`: accessible modal reused by Google and RapidAPI.
- `front-next/src/lib/api.ts`: gateway base URL and safe JSON response parsing.
- `front-next/src/types/game.ts`: shared game and integration-status types.
- `front-next/src/pages/login.tsx`: guarded Google popup flow.
- `front-next/src/pages/home.tsx`: fallback status notification and typed game rendering.
- `README.md`: complete startup, credentials, architecture, demo and troubleshooting guide.

---

### Task 1: Portable container configuration

**Files:**
- Modify: `docker-compose.yml`
- Modify: `.env.example`
- Modify: `Gateway_CDS/Dockerfile`
- Modify: `Eureka_CDS/Dockerfile`
- Modify: `Login/Dockerfile`
- Modify: `Datos/Dockerfile`
- Modify: `Injector/Dockerfile`
- Modify: `Consumidor/Dockerfile`
- Modify: `Consumidor_Base/Dockerfile`
- Modify: `front-next/Dockerfile`
- Modify: `front-next/package.json`

**Interfaces:**
- Consumes: the ports and service names declared in the approved design.
- Produces: a Compose model that resolves with no `.env`, internal development defaults, blank optional external credentials, and health-aware dependencies used by later tasks.

- [ ] **Step 1: Prove the current Compose model rejects a missing `.env`**

Run from a temporary copy without `.env`:

```powershell
docker compose config
```

Expected: non-zero exit mentioning a required variable such as `MONGO_INITDB_ROOT_USERNAME`, `GOOGLE_CLIENT_ID` or `RAPIDAPI_KEY`.

- [ ] **Step 2: Replace required substitutions with explicit development defaults**

Use these exact substitution rules in `docker-compose.yml`:

```yaml
MONGO_INITDB_ROOT_USERNAME: "${MONGO_INITDB_ROOT_USERNAME:-gameshop}"
MONGO_INITDB_ROOT_PASSWORD: "${MONGO_INITDB_ROOT_PASSWORD:-gameshop-development-password}"
JWT_SECRET_KEY: "${JWT_SECRET_KEY:-gameshop-development-jwt-secret-change-me}"
GOOGLE_CLIENT_ID: "${GOOGLE_CLIENT_ID:-}"
GOOGLE_CLIENT_SECRET: "${GOOGLE_CLIENT_SECRET:-}"
RAPIDAPI_KEY: "${RAPIDAPI_KEY:-}"
RAPIDAPI_HOST: "${RAPIDAPI_HOST:-steam2.p.rapidapi.com}"
```

Pass RapidAPI variables to both `injector` and `datos`. Remove global `container_name` entries, replace the host bind for MongoDB with a named `mongo-data` volume, correct Datos to `4001:4001`, and remove source bind mounts from application services.

Pin the infrastructure images to `mongo:7.0.14`, `confluentinc/cp-zookeeper:7.6.1` and `confluentinc/cp-kafka:7.6.1`. Replace `.env.example` with safe development defaults for MongoDB/JWT and blank values for `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` and `RAPIDAPI_KEY` so it exercises fallback mode.

- [ ] **Step 3: Make each image reproducible**

Build both Java services in multi-stage Dockerfiles using Maven and run their jars with Java 11:

```dockerfile
FROM maven:3.9-eclipse-temurin-11 AS build
WORKDIR /workspace
COPY pom.xml .
COPY src ./src
RUN mvn -B -DskipTests package

FROM eclipse-temurin:11-jre-jammy
WORKDIR /app
COPY --from=build /workspace/target/*.jar app.jar
ENTRYPOINT ["java", "-jar", "/app/app.jar"]
```

Use `python:3.9-slim-bookworm` for Flask/Kafka services, install requirements before copying source, and expose the real service port. Use `node:18-bookworm-slim`, `npm ci`, and this frontend command:

```json
"dev": "next dev --hostname 0.0.0.0"
```

- [ ] **Step 4: Add healthchecks and health-aware dependencies**

MongoDB must pass `mongosh --quiet --eval "db.adminCommand('ping').ok"`; Kafka must pass `kafka-topics --bootstrap-server localhost:9092 --list`; Eureka, Login, Datos and Consumidor Base must pass HTTP health checks. Use `condition: service_healthy` only for direct startup prerequisites and keep both `gateway` and `kafka` networks where cross-network calls require them.

- [ ] **Step 5: Verify configuration without secrets**

Run:

```powershell
docker compose config --quiet
docker compose build eureka gateway front-next
```

Expected: both commands exit 0 without creating `.env` and without unresolved-variable warnings.

- [ ] **Step 6: Commit the portable container baseline**

```powershell
git add docker-compose.yml .env.example Gateway_CDS/Dockerfile Eureka_CDS/Dockerfile Login/Dockerfile Datos/Dockerfile Injector/Dockerfile Consumidor/Dockerfile Consumidor_Base/Dockerfile front-next/Dockerfile front-next/package.json
git commit -m "build: make compose configuration portable"
```

---

### Task 2: Optional Google OAuth backend

**Files:**
- Create: `Login/integrations.py`
- Create: `Login/tests/test_integrations.py`
- Create: `Login/tests/test_google_routes.py`
- Modify: `Login/app.py`
- Modify: `Login/requirements.txt`

**Interfaces:**
- Consumes: `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` from the process environment.
- Produces: `missing_google_credentials(environ) -> list[str]`, `google_integration_status(environ) -> dict`, GET `/user/login/google`, and GET `/health`.

- [ ] **Step 1: Write failing credential-detection tests**

Create tests containing these behaviors:

```python
def test_google_status_lists_both_missing_values(self):
    status = google_integration_status({})
    self.assertEqual(status, {
        "service": "google",
        "configured": False,
        "missingCredentials": ["GOOGLE_CLIENT_ID", "GOOGLE_CLIENT_SECRET"],
    })

def test_google_status_accepts_complete_credentials(self):
    status = google_integration_status({
        "GOOGLE_CLIENT_ID": "client.apps.googleusercontent.com",
        "GOOGLE_CLIENT_SECRET": "local-secret",
    })
    self.assertTrue(status["configured"])
    self.assertEqual(status["missingCredentials"], [])

def test_example_markers_are_not_credentials(self):
    status = google_integration_status({
        "GOOGLE_CLIENT_ID": "replace-me",
        "GOOGLE_CLIENT_SECRET": "replace-me",
    })
    self.assertFalse(status["configured"])
```

- [ ] **Step 2: Run the tests and confirm RED**

Run:

```powershell
python -m unittest discover -s Login/tests -v
```

Expected: import failure because `Login/integrations.py` does not exist.

- [ ] **Step 3: Implement the pure Google status functions**

Treat whitespace, empty strings and the exact markers `replace-me` and `changeme` as missing. Return only credential names, never values. Keep all payload keys and casing exactly as asserted above.

- [ ] **Step 4: Write failing route tests**

Use Flask's test client and a patched environment to assert:

```python
response = client.get("/user/login/google")
self.assertEqual(response.status_code, 503)
self.assertEqual(response.get_json()["service"], "google")
self.assertNotIn("link", response.get_json())
```

With both credentials present, assert status 200 and that the decoded query string contains `client_id`, `scope=openid email profile`, the exact callback URI and a non-empty per-request `state`.

- [ ] **Step 5: Guard the OAuth routes and make startup optional**

Change module-level credential access to `os.getenv`. The login route must return the status object with HTTP 503 when incomplete. Generate `state` with `secrets.token_urlsafe(32)`, store it in the Flask session, validate it in `/callback`, and return a controlled 400 response for missing code, state mismatch, token exchange failure or absent `id_token`. Configure Flask's session secret from `JWT_SECRET_KEY`.

Add:

```python
@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"})
```

- [ ] **Step 6: Run Login tests and commit**

```powershell
python -m unittest discover -s Login/tests -v
git add Login/app.py Login/integrations.py Login/tests Login/requirements.txt
git commit -m "feat: handle missing Google credentials"
```

Expected: all Login tests pass and no test output contains either test secret value.

---

### Task 3: Real RapidAPI fixture and source selection

**Files:**
- Create: `Injector/ingestion.py`
- Create: `Injector/capture_fixture.py`
- Create: `Injector/tests/test_ingestion.py`
- Create: `Injector/data/rapidapi-steam-games.json`
- Modify: `Injector/app.py`

**Interfaces:**
- Consumes: optional `RAPIDAPI_KEY`, `RAPIDAPI_HOST`, an HTTP session and fixture path.
- Produces: `rapidapi_is_configured(environ) -> bool`, `load_fixture(path) -> list[dict]`, `fetch_live_games(session, key, host, letters) -> list[dict]`, `select_game_source(...) -> tuple[str, list[dict]]`, and `chunk_games(games, size=50)`.

- [ ] **Step 1: Write failing source-selection tests**

Cover these exact outcomes with temporary JSON files and a fake HTTP session:

```python
source, games = select_game_source({}, fixture_path, session=fake_session)
self.assertEqual(source, "fixture")
self.assertEqual(games, fixture_games)
self.assertEqual(fake_session.calls, [])

source, games = select_game_source({
    "RAPIDAPI_KEY": "local-key",
    "RAPIDAPI_HOST": "steam2.p.rapidapi.com",
}, fixture_path, session=fake_session)
self.assertEqual(source, "rapidapi")
self.assertGreater(len(games), 0)
```

Also assert that dictionaries containing API error messages, HTML responses and non-list payloads cause fallback selection instead of Kafka publication.

- [ ] **Step 2: Run the tests and confirm RED**

```powershell
python -m unittest discover -s Injector/tests -v
```

Expected: import failure because `Injector/ingestion.py` does not exist.

- [ ] **Step 3: Implement validation, live fetching and fallback loading**

Use endpoint format `https://{host}/search/{letter}/page/1`, `requests.get(..., timeout=20)`, `response.raise_for_status()`, and headers containing the key only in memory. Deduplicate by string `appId`, reject records without `appId` or `title`, and return the fixture if live fetching raises `requests.RequestException`, `ValueError` or returns no valid games.

The fixture loader must require this top-level structure:

```json
{
  "metadata": {
    "provider": "RapidAPI",
    "api": "Steam",
    "host": "steam2.p.rapidapi.com",
    "credentialsIncluded": false
  },
  "games": []
}
```

- [ ] **Step 4: Implement the secret-safe capture command**

`capture_fixture.py` must accept `--output`, read credentials from environment only, query A through Z, deduplicate games, add an ISO-8601 UTC capture timestamp and the queried endpoint pattern, and refuse to write fewer than 200 valid unique records. It must print only record counts, host and output path.

- [ ] **Step 5: Capture the real dataset using the owner's local `.env`**

Run without printing the environment:

```powershell
docker compose run --rm --no-deps --volume ./Injector:/app injector python capture_fixture.py --output /app/data/rapidapi-steam-games.json
```

Expected: exit 0, at least 200 unique games, and `credentialsIncluded` equals `false`. The credentials originate solely from the user's local RapidAPI subscription stored in `.env`; they are not sourced from the project or generated by Codex.

- [ ] **Step 6: Make Injector publish either source with bounded retries**

Replace import-time sleeps and the A-Z loop with `main()`. Retry Kafka connection up to 30 times with 2-second intervals, publish `chunk_games(games, 50)`, call `future.get(timeout=30)`, flush, close, and exit 0 after the one-time seed. Log `source=rapidapi` or `source=fixture` and counts only.

- [ ] **Step 7: Validate the fixture and run GREEN tests**

Add assertions that the committed file has at least 200 unique `appId` values, contains no keys matching `key`, `secret`, `authorization` or `credential` except boolean `credentialsIncluded`, and each game has the required fields.

Run:

```powershell
python -m unittest discover -s Injector/tests -v
git grep -n -i -E "x-rapidapi-key|client_secret" -- Injector/data/rapidapi-steam-games.json
```

Expected: tests pass and `git grep` produces no output.

- [ ] **Step 8: Commit the ingestion feature**

```powershell
git add Injector/app.py Injector/ingestion.py Injector/capture_fixture.py Injector/tests Injector/data/rapidapi-steam-games.json
git commit -m "feat: add RapidAPI dataset fallback"
```

---

### Task 4: Persist normalized games and expose integration status

**Files:**
- Create: `Consumidor_Base/normalization.py`
- Create: `Consumidor_Base/tests/test_normalization.py`
- Create: `Datos/integrations.py`
- Create: `Datos/tests/test_integrations.py`
- Create: `Datos/tests/test_formatting.py`
- Modify: `Consumidor_Base/app.py`
- Modify: `Datos/app.py`

**Interfaces:**
- Consumes: RapidAPI-shaped game dictionaries and optional `RAPIDAPI_KEY`.
- Produces: `normalize_game(game) -> dict | None`, GET `/integration-status`, GET `/health` on both Flask services, and consistent sorting by `reviewPercentage`.

- [ ] **Step 1: Write failing normalization and status tests**

Assert these exact behaviors:

```python
normalized = normalize_game({
    "appId": "730",
    "title": "Counter-Strike 2",
    "reviewSummary": "Very Positive (87%)",
})
self.assertEqual(normalized["reviewPercentage"], 87)
self.assertIsNone(normalize_game({"title": "Missing id"}))

status = rapidapi_integration_status({})
self.assertEqual(status, {
    "service": "rapidapi",
    "configured": False,
    "source": "fixture",
    "missingCredentials": ["RAPIDAPI_KEY"],
})
```

With a non-placeholder key, assert `configured: true`, `source: "rapidapi"` and an empty missing list.

- [ ] **Step 2: Run the tests and confirm RED**

```powershell
python -m unittest discover -s Consumidor_Base/tests -v
python -m unittest discover -s Datos/tests -v
```

Expected: both suites fail because the new modules do not exist.

- [ ] **Step 3: Implement normalization and idempotent persistence**

Make `normalize_game` copy its input, reject missing `appId` or `title`, parse the first `NN%` into integer `reviewPercentage`, and use `None` if absent. In `/save_games`, normalize the incoming list and upsert each valid game by `appId` with `$setOnInsert`; return counts for inserted, skipped and received records.

- [ ] **Step 4: Implement public status and health routes**

`GET /integration-status` must return `rapidapi_integration_status(os.environ)` without authentication. Add `GET /health` returning `{"status": "ok"}` to Datos and Consumidor Base. Change the games query sort key from `porcentaje_votos` to `reviewPercentage`.

- [ ] **Step 5: Run GREEN tests and commit**

```powershell
python -m unittest discover -s Consumidor_Base/tests -v
python -m unittest discover -s Datos/tests -v
git add Consumidor_Base/app.py Consumidor_Base/normalization.py Consumidor_Base/tests Datos/app.py Datos/integrations.py Datos/tests
git commit -m "feat: expose data source and normalize games"
```

Expected: all tests pass.

---

### Task 5: Accessible credential modals and typed frontend

**Files:**
- Create: `front-next/src/components/CredentialModal.tsx`
- Create: `front-next/src/components/CredentialModal.test.tsx`
- Create: `front-next/src/lib/api.ts`
- Create: `front-next/src/types/game.ts`
- Create: `front-next/src/test/setup.ts`
- Create: `front-next/vitest.config.ts`
- Modify: `front-next/package.json`
- Modify: `front-next/package-lock.json`
- Modify: `front-next/src/pages/login.tsx`
- Modify: `front-next/src/pages/home.tsx`
- Modify: `front-next/src/pages/favorites.tsx`
- Modify: `front-next/src/pages/register.tsx`
- Modify: `front-next/src/pages/inicio_exitoso_google.tsx`

**Interfaces:**
- Consumes: backend payload `{service, configured, source?, missingCredentials}` and OAuth payload `{link}`.
- Produces: `CredentialModalProps`, typed `Game` and `IntegrationStatus`, `apiUrl(path)`, and user-visible Google/RapidAPI dialogs.

- [ ] **Step 1: Install and configure the frontend test harness**

Add scripts and pinned dev dependencies compatible with Node 18:

```json
"test": "vitest run",
"test:watch": "vitest",
"@testing-library/jest-dom": "6.1.5",
"@testing-library/react": "14.0.0",
"@testing-library/user-event": "14.5.1",
"jsdom": "22.1.0",
"vitest": "0.34.6"
```

Configure `environment: 'jsdom'`, the `@/` alias, globals, and `src/test/setup.ts` importing `@testing-library/jest-dom`.

- [ ] **Step 2: Write failing modal behavior tests**

Render the dialog with `missingCredentials={["RAPIDAPI_KEY"]}` and assert role `dialog`, title, description and credential text. Verify `userEvent.keyboard('{Escape}')`, the “Entendido” button and a backdrop click each call `onClose`. Verify a click inside the panel does not close it.

- [ ] **Step 3: Run the modal test and confirm RED**

```powershell
Set-Location front-next
npm test -- CredentialModal.test.tsx
```

Expected: import failure because the component does not exist.

- [ ] **Step 4: Implement the reusable modal**

Use a fixed full-screen backdrop with `z-50`, center the panel, set `role="dialog"`, `aria-modal="true"`, label and description ids, close on Escape and backdrop, and focus the close button on open. Restore focus to `returnFocusRef` on close.

Use these exact titles:

```text
Credenciales de Google necesarias
Datos locales de RapidAPI en uso
```

- [ ] **Step 5: Write failing login and home integration tests**

For Login, mock `fetch` to return HTTP 503 with the Google status payload, click “Iniciar sesión con Google”, assert the Google modal appears and `window.open` is not called. For Home, mock `/integration-status` with `source: "fixture"`, mock authenticated data calls with empty arrays, and assert the RapidAPI modal appears while the page heading remains rendered.

- [ ] **Step 6: Implement safe API and page integrations**

Define:

```typescript
export const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8081/api';
export const apiUrl = (path: string) => `${API_BASE_URL}/${path.replace(/^\/+/, '')}`;
```

Login must inspect `response.ok` before reading `link`, show the modal for `configured: false`, report network and popup-blocking errors inline, add one named message listener, accept only `window.location.origin`, then remove it after success or popup closure.

Home must fetch `/data/integration-status` once on mount and show the RapidAPI modal when `source === 'fixture'`. Closing the modal must not prevent game, search or favorite requests.

- [ ] **Step 7: Add shared types and remove TypeScript build errors**

Define `Game` with string fields matching the backend and optional nullable price/review fields. Type all React state arrays, event parameters, `gameId` arguments and caught errors in the changed pages. In the popup callback, guard `window.opener` and send only to `window.location.origin`.

- [ ] **Step 8: Run frontend tests, lint and production build**

```powershell
Set-Location front-next
npm test
npm run lint
npm run build
```

Expected: all tests pass, lint has no errors and Next creates a production build without TypeScript errors.

- [ ] **Step 9: Commit the frontend feature**

```powershell
git add front-next/package.json front-next/package-lock.json front-next/vitest.config.ts front-next/src
git commit -m "feat: show optional credential modals"
```

---

### Task 6: End-to-end verification and operating documentation

**Files:**
- Modify: `README.md`
- Create: `docs/architecture.md`
- Create: `docs/demo-guide.md`
- Create: `docs/troubleshooting.md`

**Interfaces:**
- Consumes: all service commands, payloads and ports established by Tasks 1-5.
- Produces: a repeatable clean-machine workflow, architecture explanation, credential links, demo script and fault diagnosis.

- [ ] **Step 1: Start from the credential-free configuration**

Temporarily run with an environment file that leaves all external variables blank, without reading or changing the user's real `.env`:

```powershell
docker compose --env-file .env.example down --volumes --remove-orphans
docker compose --env-file .env.example up --build --detach
docker compose --env-file .env.example ps
```

Expected: all long-running services become healthy, Injector exits 0 after seeding, and no service enters a restart loop.

- [ ] **Step 2: Verify the fallback API flow**

Create a local user through the gateway, obtain its JWT, then request games and status:

```text
POST http://localhost:8081/api/login/user/register
POST http://localhost:8081/api/login/user/login
GET  http://localhost:8081/api/data/integration-status
GET  http://localhost:8081/api/data/games
```

Expected: status reports `source: fixture`; login returns a JWT; games returns a non-empty JSON list. Browser verification at `http://localhost:3000/login` must show the Google modal on its button and the RapidAPI modal on Home while games remain visible.

- [ ] **Step 3: Verify configured integration selection without exposing values**

With the user's real `.env`, run:

```powershell
docker compose up --build --detach --force-recreate login injector datos
docker compose logs --no-log-prefix injector
```

Expected: Injector logs `source=rapidapi` and a positive record count without logging request headers. GET `/api/login/user/login/google` returns HTTP 200 and a Google authorization URL whose query contains the configured client id. Do not print the client secret or RapidAPI key.

- [ ] **Step 4: Run the complete automated verification suite**

```powershell
python -m unittest discover -s Login/tests -v
python -m unittest discover -s Injector/tests -v
python -m unittest discover -s Consumidor_Base/tests -v
python -m unittest discover -s Datos/tests -v
Set-Location front-next
npm test
npm run lint
npm run build
Set-Location ..
docker compose config --quiet
docker compose ps
```

Expected: every command exits 0; Compose reports the long-running services healthy.

- [ ] **Step 5: Write user-facing documentation**

README must contain: prerequisites, one-command credential-free startup, optional `.env`, first-start timing, URLs, shutdown and reset commands, and links to the detailed documents.

`docs/architecture.md` must explain the request and ingestion paths. `docs/demo-guide.md` must provide a timed video sequence covering local registration/login, fallback modal, games, search, favorites and Google button behavior. `docs/troubleshooting.md` must map unhealthy containers, occupied ports, OAuth redirect mismatch, Google test users, RapidAPI subscription errors, empty MongoDB and rebuilds to exact diagnostic commands.

Include these credential sources:

- Google clients: `https://console.cloud.google.com/auth/clients`
- Google branding: `https://console.cloud.google.com/auth/branding`
- RapidAPI Steam API: `https://rapidapi.com/psimavel/api/steam2`
- RapidAPI subscription: `https://rapidapi.com/psimavel/api/steam2/pricing`

State explicitly that the fixture was fetched from `steam2.p.rapidapi.com` using the project owner's local RapidAPI key and that no credentials are included.

- [ ] **Step 6: Check documentation and repository hygiene**

```powershell
git diff --check
git status --short
git grep -n -i -E "X-RapidAPI-Key:|GOOGLE_CLIENT_SECRET=[^$]|RAPIDAPI_KEY=[^$]" -- . ':!docs/superpowers/plans/*'
```

Expected: no whitespace errors, only intended files in status, and no committed secret values.

- [ ] **Step 7: Commit documentation**

```powershell
git add README.md docs/architecture.md docs/demo-guide.md docs/troubleshooting.md
git commit -m "docs: document startup and demo workflows"
```

- [ ] **Step 8: Final acceptance audit**

Re-read `docs/superpowers/specs/2026-07-25-optional-credentials-and-compose-design.md` and check all eight acceptance scenarios against fresh command output and browser observations. Report any external Google consent or RapidAPI account restriction separately from application failures.
