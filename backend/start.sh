#!/bin/sh

echo "Checking if database needs seeding..."

COUNT=$(psql "$DATABASE_URL" -tAc "SELECT COUNT(*) FROM logs;")

if [ "$COUNT" -eq "0" ]; then
  echo "Database is empty, seeding..."
  python seed.py
else
  echo "Database already has $COUNT rows, skipping seed."
fi

echo "Starting API server..."
exec uvicorn main:app --host 0.0.0.0 --port 8000 --reload
