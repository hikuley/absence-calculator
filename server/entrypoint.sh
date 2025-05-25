#!/bin/bash

echo "Waiting for PostgreSQL to start..."
while ! pg_isready -h $DB_HOST -p $DB_PORT -U $DB_USER; do
  sleep 1
done

echo "PostgreSQL started, initializing database..."
python -c "import asyncio; from migrations import initialize_database; asyncio.run(initialize_database())"

echo "Database initialization complete."

echo "Starting application..."
exec uvicorn app:app --host 0.0.0.0 --port 5001 "$@"
