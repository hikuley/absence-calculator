FROM python:3.9-slim

WORKDIR /app

# Configure apt to be more resilient to temporary network issues
RUN echo 'Acquire::Retries "3";' > /etc/apt/apt.conf.d/80retries \
    && mkdir -p /etc/apt/apt.conf.d/

# Install PostgreSQL client dependencies with retry mechanism and DNS options
RUN for i in 1 2 3 4 5; do \
      echo "Attempt $i to install packages..." \
      && apt-get update -y \
      && apt-get install -y --no-install-recommends \
        postgresql-client \
        libpq-dev \
        gcc \
        ca-certificates \
      && apt-get clean \
      && rm -rf /var/lib/apt/lists/* \
      && break \
      || { echo "Attempt $i failed! Retrying in 15 seconds..."; sleep 15; }; \
    done

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