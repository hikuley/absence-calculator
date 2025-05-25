FROM python:3.9-slim

WORKDIR /app

# Install PostgreSQL client dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    libpq-dev \
    gcc \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY server/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy server code
COPY server/ ./server/

# Create entrypoint script
RUN echo '#!/bin/bash\n\
echo "Waiting for PostgreSQL to start..."\n\
while ! pg_isready -h $DB_HOST -p $DB_PORT -U $DB_USER; do\n\
  sleep 1\n\
done\n\
\n\
echo "PostgreSQL started, running migrations..."\n\
cd /app/server && python -c "from models import run_schema_migration; run_schema_migration()"\n\
\n\
echo "Starting application..."\n\
cd /app/server && exec uvicorn app:app --host 0.0.0.0 --port 5001 --workers 1 "$@"\n\
' > /app/entrypoint.sh && chmod +x /app/entrypoint.sh

EXPOSE 5001

ENTRYPOINT ["/app/entrypoint.sh"]