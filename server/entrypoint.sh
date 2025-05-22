#!/bin/bash

echo "Waiting for PostgreSQL to start..."
while ! pg_isready -h $DB_HOST -p $DB_PORT -U $DB_USER; do
  sleep 1
done

echo "PostgreSQL started, running migrations..."
alembic upgrade head

echo "Migrating data from CSV to database..."
python migrate_csv_to_db.py

echo "Starting application..."
exec uvicorn app:app --host 0.0.0.0 --port 5001 "$@"
