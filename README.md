# Log Pulse

A log ingestion and observability dashboard. Ingest structured log events via a REST API and explore them through a real-time filterable dashboard.

![Stack](https://img.shields.io/badge/backend-FastAPI-009688) ![Stack](https://img.shields.io/badge/frontend-Svelte%205-FF3E00) ![Stack](https://img.shields.io/badge/database-PostgreSQL%2016-336791)

---

## Architecture

```
┌─────────────────┐     HTTP      ┌─────────────────┐     SQL      ┌─────────────────┐
│   Svelte 5 +    │ ────────────► │   FastAPI +     │ ──────────► │   PostgreSQL 16  │
│   Vite          │               │   Python 3.12   │             │                  │
│   :5173         │               │   :8000         │             │   :5432          │
└─────────────────┘               └─────────────────┘             └─────────────────┘
```

All three services run as Docker containers orchestrated with Docker Compose. The frontend talks directly to the API; the API holds a connection pool to Postgres.

---

## Setup

**Requirements:** Docker Desktop

```bash
git clone https://github.com/full-Stack-Hacks/log-pulse.git
cd log-pulse
docker-compose up --build
```

That's it. On first run, Postgres initializes the schema from `db/init.sql` and the API container automatically seeds 100K rows of sample data — this takes about 30 seconds. The dashboard will be available at `http://localhost:5173` once seeding completes and you see `Application startup complete.` in the logs. Subsequent restarts detect the existing data and skip seeding.

| Service | URL |
|---|---|
| Dashboard | http://localhost:5173 |
| API | http://localhost:8000 |
| API docs | http://localhost:8000/docs |
| Postgres | localhost:5432 |

To stop everything: `docker-compose down`  
To wipe the database and start fresh: `docker-compose down -v`

---

## API

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Health check |
| `POST` | `/logs` | Ingest a log entry |
| `GET` | `/logs` | Query logs with filters + pagination |
| `GET` | `/logs/stats` | Count by level and service |
| `GET` | `/logs/timeline` | Hourly log counts for charting |

### `GET /logs` query parameters

| Param | Type | Description |
|---|---|---|
| `level` | string | Filter by level: `DEBUG`, `INFO`, `WARN`, `ERROR` |
| `service` | string | Filter by service name |
| `search` | string | Full-text search on message |
| `start` / `end` | ISO datetime | Time range filter |
| `limit` | int (max 500) | Page size, default 50 |
| `offset` | int | Pagination offset |

### `POST /logs` body

```json
{
  "level": "ERROR",
  "service": "auth-service",
  "message": "Login failed for user 42",
  "metadata": { "user_id": 42, "ip": "1.2.3.4" }
}
```

---

## Database Schema

```sql
CREATE TYPE log_level AS ENUM ('DEBUG', 'INFO', 'WARN', 'ERROR');

CREATE TABLE logs (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp   TIMESTAMPTZ NOT NULL DEFAULT now(),
    level       log_level NOT NULL,
    service     TEXT NOT NULL,
    message     TEXT NOT NULL,
    metadata    JSONB
);

CREATE INDEX idx_logs_timestamp ON logs (timestamp DESC);
CREATE INDEX idx_logs_level     ON logs (level);
```

---

## Performance

All dashboard queries measured against 100K rows with `EXPLAIN ANALYZE`:

| Query | Execution time |
|---|---|
| Fetch logs (no filter) | 1.4ms |
| Fetch logs (level filter) | 4ms |
| Count by level (stats) | 13ms |
| Timeline (24h buckets) | 18ms |

The `idx_logs_timestamp` index drives the main log fetch and timeline queries. The `idx_logs_level` index enables index-only scans for the stats aggregation.

---

## Design Decisions

**ENUM for log level** — rejects invalid values at the database layer rather than the application layer. Tradeoff: adding a new level requires a schema migration.

**JSONB for metadata** — allows arbitrary structured context per log (stack traces, request IDs, user IDs) without requiring schema changes for each new field. Tradeoff: querying inside metadata is slower than a dedicated column.

**psycopg2 connection pool** — keeps a pool of 10 reusable Postgres connections rather than opening a new connection per request. Simpler than an async driver (asyncpg) with negligible performance difference at this scale.

**Svelte 5 runes** — uses `$state`, `$derived`, and `$effect` throughout, the modern Svelte 5 reactivity model. The search input is debounced (300ms) to avoid hammering the API on every keystroke.

**Seed script as a one-off command** — intentionally not part of the container startup. Running it on every boot would wipe and repopulate the database, which is destructive in a real environment.

---

## Tradeoffs

- **No authentication** — the API is open. A production system would require API keys or JWT auth on every endpoint.
- **Offset-based pagination** — simple to implement but degrades at very high offsets. Cursor-based pagination (keying on `timestamp + id`) would be more efficient for deep pages.
- **Synchronous API** — FastAPI supports async handlers, but we use synchronous psycopg2. At higher concurrency, switching to asyncpg would improve throughput.
- **No log retention policy** — in production you'd want automatic deletion or archiving of logs older than N days to keep the table size manageable.

---

## What I'd Improve With More Time

- **Cursor-based pagination** for the log table to handle large offsets efficiently
- **Composite index on `(level, timestamp DESC)`** to speed up filtered queries at larger table sizes
- **Saved searches / bookmarks** so users can return to a specific filter combination
- **Log volume alerting** — notify when ERROR rate spikes above a threshold
- **Authentication** — API key per service for ingestion, user sessions for the dashboard

---

## Kubernetes

Manifests for all three services are in the `k8s/` directory. Before applying, build and push the images to a registry:

```bash
docker build -t your-registry/log-pulse-api:latest ./backend
docker push your-registry/log-pulse-api:latest

docker build -t your-registry/log-pulse-frontend:latest ./frontend
docker push your-registry/log-pulse-frontend:latest
```

Update the `image:` fields in `k8s/api.yaml` and `k8s/frontend.yaml` with your registry paths, then apply:

```bash
kubectl apply -f k8s/db.yaml
kubectl apply -f k8s/api.yaml
kubectl apply -f k8s/frontend.yaml
```

The database credentials are stored in a Kubernetes `Secret` defined in `k8s/db.yaml`. The frontend is exposed via `NodePort` on port `30573`. The API and database use `ClusterIP` and are internal to the cluster only.

---

## Project Structure

```
log-pulse/
├── backend/
│   ├── Dockerfile
│   ├── main.py          # FastAPI app and all endpoints
│   ├── seed.py          # 100K row seed script
│   └── requirements.txt
├── frontend/
│   ├── Dockerfile
│   ├── src/
│   │   ├── App.svelte
│   │   └── lib/
│   │       ├── api.js         # All fetch calls
│   │       ├── StatsBar.svelte
│   │       ├── Timeline.svelte
│   │       └── LogTable.svelte
│   └── package.json
├── db/
│   └── init.sql         # Schema and indexes
├── k8s/
│   ├── db.yaml          # Postgres deployment, PVC, and secret
│   ├── api.yaml         # FastAPI deployment
│   └── frontend.yaml    # Svelte deployment (NodePort)
└── docker-compose.yml
```
