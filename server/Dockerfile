FROM python:3.8-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir flask==1.1.2 flask-cors==3.0.10 python-dateutil==2.8.2 werkzeug==1.0.1 Jinja2==2.11.3 itsdangerous==1.1.0 MarkupSafe==1.1.1

# Copy application code
COPY . .

# Create directory for data
RUN mkdir -p /app/data

# Expose port
EXPOSE 5001

# Run the application
CMD ["python", "app.py"]
