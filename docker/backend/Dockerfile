FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY server/ ./server/

EXPOSE 5001

CMD ["uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "5001"] 