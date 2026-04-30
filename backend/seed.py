import os
import random
import json
from datetime import datetime, timedelta, timezone

import psycopg2
from psycopg2.extras import execute_values

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql://logpulse:logpulse@localhost:5432/logpulse"
)

SERVICES = [
    "auth-service",
    "api-gateway",
    "payments-service",
    "user-service",
    "notification-service",
]

LEVELS = ["DEBUG", "INFO", "WARN", "ERROR"]
LEVEL_WEIGHTS = [0.10, 0.60, 0.20, 0.10]

MESSAGES = {
    "DEBUG": [
        "Cache miss for key {key}",
        "Processing request {request_id}",
        "Connection pool size: {size}",
        "Query took {latency}ms",
    ],
    "INFO": [
        "User {user_id} logged in successfully",
        "Request completed in {latency}ms",
        "Payment processed for order {order_id}",
        "Email sent to user {user_id}",
        "Health check passed",
        "Session created for user {user_id}",
        "Order {order_id} status updated",
        "User {user_id} logged out",
    ],
    "WARN": [
        "High latency detected: {latency}ms",
        "Retry attempt {attempt} for request {request_id}",
        "Memory usage at {percent}%",
        "Rate limit approaching for user {user_id}",
        "Slow query detected ({latency}ms)",
    ],
    "ERROR": [
        "Failed to process payment for order {order_id}",
        "Database connection timeout",
        "Authentication failed for user {user_id}",
        "Request {request_id} failed after {attempt} retries",
        "Unexpected nil reference in handler",
        "Failed to send email to user {user_id}",
    ],
}


def make_message(level):
    template = random.choice(MESSAGES[level])
    return template.format(
        key=f"key_{random.randint(1, 1000)}",
        request_id=f"req_{random.randint(100000, 999999)}",
        size=random.randint(1, 50),
        user_id=random.randint(1, 10000),
        latency=random.randint(1, 5000),
        order_id=f"ord_{random.randint(100000, 999999)}",
        attempt=random.randint(1, 5),
        percent=random.randint(70, 99),
    )


def make_metadata(level):
    if level == "ERROR":
        return {
            "request_id": f"req_{random.randint(100000, 999999)}",
            "stack_trace": (
                f"Traceback (most recent call last):\n"
                f"  File 'app.py', line {random.randint(10, 500)}\n"
                f"RuntimeError: {random.choice(['connection refused', 'timeout', 'unexpected nil'])}"
            ),
        }
    elif level == "WARN":
        return {
            "latency_ms": random.randint(500, 5000),
            "threshold_ms": 500,
        }
    elif level == "INFO":
        return {"request_id": f"req_{random.randint(100000, 999999)}"}
    else:
        return None


def seed(total=100_000, batch_size=1_000):
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    now = datetime.now(timezone.utc)
    window_seconds = 30 * 24 * 3600

    print(f"Seeding {total:,} rows in batches of {batch_size:,}...")

    batch = []
    for i in range(1, total + 1):
        level = random.choices(LEVELS, weights=LEVEL_WEIGHTS)[0]
        timestamp = now - timedelta(seconds=random.randint(0, window_seconds))
        service = random.choice(SERVICES)
        message = make_message(level)
        metadata = make_metadata(level)

        batch.append((timestamp, level, service, message, json.dumps(metadata) if metadata else None))

        if len(batch) == batch_size:
            execute_values(
                cur,
                "INSERT INTO logs (timestamp, level, service, message, metadata) VALUES %s",
                batch,
            )
            conn.commit()
            print(f"  {i:,} / {total:,}", end="\r")
            batch = []

    if batch:
        execute_values(
            cur,
            "INSERT INTO logs (timestamp, level, service, message, metadata) VALUES %s",
            batch,
        )
        conn.commit()

    cur.close()
    conn.close()
    print(f"\nDone. {total:,} rows inserted.")


if __name__ == "__main__":
    seed()
