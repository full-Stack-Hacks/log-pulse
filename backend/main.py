import json
import os
from contextlib import asynccontextmanager, contextmanager
from datetime import datetime, timedelta, timezone
from typing import Optional

import psycopg2
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from psycopg2.extras import RealDictCursor
from psycopg2.pool import SimpleConnectionPool
from pydantic import BaseModel

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql://logpulse:logpulse@localhost:5432/logpulse"
)

pool: SimpleConnectionPool | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global pool
    pool = SimpleConnectionPool(1, 10, DATABASE_URL)
    yield
    pool.closeall()


app = FastAPI(title="Log Pulse API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@contextmanager
def get_conn():
    conn = pool.getconn()
    try:
        yield conn
    finally:
        pool.putconn(conn)


class LogCreate(BaseModel):
    level: str
    service: str
    message: str
    metadata: Optional[dict] = None


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/logs", status_code=201)
def create_log(log: LogCreate):
    with get_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                INSERT INTO logs (level, service, message, metadata)
                VALUES (%s::log_level, %s, %s, %s)
                RETURNING id, timestamp, level, service, message, metadata
                """,
                (log.level, log.service, log.message, json.dumps(log.metadata) if log.metadata else None),
            )
            conn.commit()
            row = dict(cur.fetchone())
            row["timestamp"] = row["timestamp"].isoformat()
            return row


@app.get("/logs")
def get_logs(
    level: Optional[str] = None,
    service: Optional[str] = None,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    search: Optional[str] = None,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    conditions = []
    params = []

    if level:
        conditions.append("level = %s::log_level")
        params.append(level)
    if service:
        conditions.append("service = %s")
        params.append(service)
    if start:
        conditions.append("timestamp >= %s")
        params.append(start)
    if end:
        conditions.append("timestamp <= %s")
        params.append(end)
    if search:
        conditions.append("message ILIKE %s")
        params.append(f"%{search}%")

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

    with get_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                f"SELECT id, timestamp, level, service, message, metadata "
                f"FROM logs {where} ORDER BY timestamp DESC LIMIT %s OFFSET %s",
                params + [limit, offset],
            )
            rows = cur.fetchall()

            cur.execute(f"SELECT COUNT(*) as total FROM logs {where}", params)
            total = cur.fetchone()["total"]

    items = []
    for row in rows:
        r = dict(row)
        r["timestamp"] = r["timestamp"].isoformat()
        items.append(r)

    return {"total": total, "items": items}


@app.get("/logs/stats")
def get_stats():
    with get_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT level, COUNT(*) as count FROM logs GROUP BY level ORDER BY level"
            )
            by_level = {row["level"]: int(row["count"]) for row in cur.fetchall()}

            cur.execute(
                "SELECT service, COUNT(*) as count FROM logs GROUP BY service ORDER BY count DESC"
            )
            by_service = [
                {"service": row["service"], "count": int(row["count"])}
                for row in cur.fetchall()
            ]

    return {"by_level": by_level, "by_service": by_service}


@app.get("/logs/timeline")
def get_timeline(hours: int = Query(24, ge=1, le=168)):
    start = datetime.now(timezone.utc) - timedelta(hours=hours)
    with get_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT
                    date_trunc('hour', timestamp) AS bucket,
                    level,
                    COUNT(*) AS count
                FROM logs
                WHERE timestamp >= %s
                GROUP BY bucket, level
                ORDER BY bucket
                """,
                (start,),
            )
            rows = cur.fetchall()

    return [
        {"bucket": row["bucket"].isoformat(), "level": row["level"], "count": int(row["count"])}
        for row in rows
    ]
