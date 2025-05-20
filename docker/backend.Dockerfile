FROM python:3.9-slim

WORKDIR /app

COPY server/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY server/ .

# Create data directory
RUN mkdir -p /app/data

# Set environment variable for the CSV file path
ENV CSV_FILE_PATH=/app/data/absence_periods.csv

# Expose the port the app runs on
EXPOSE 5001

# Command to run the application
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "5001"]
