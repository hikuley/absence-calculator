FROM python:3.9-slim

WORKDIR /app

COPY server/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy server code
COPY server/ ./server/

# Ensure data directory exists
RUN mkdir -p /app/server/data

# Copy the absence_periods.csv file
COPY server/data/absence_periods.csv /app/server/data/

EXPOSE 5001

CMD ["uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "5001"] 