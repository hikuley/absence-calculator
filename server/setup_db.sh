#!/bin/bash

# Load environment variables from .env file
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Create the database if it doesn't exist
echo "Creating database $DB_NAME if it doesn't exist..."
PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -tc "SELECT 1 FROM pg_database WHERE datname = '$DB_NAME'" | grep -q 1 || PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -p $DB_PORT -U $DB_USER -c "CREATE DATABASE $DB_NAME"

# Run database migrations
echo "Running database migrations..."
alembic upgrade head

# Migrate data from CSV to database
echo "Migrating data from CSV to database..."
python migrate_csv_to_db.py

echo "Database setup complete!"
