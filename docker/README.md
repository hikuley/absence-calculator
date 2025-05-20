# Docker Setup for Absence Calculator

This directory contains Docker configuration files for running the Absence Calculator application in containers.

## Structure

- `backend.Dockerfile`: Dockerfile for the Python FastAPI backend service
- `frontend.Dockerfile`: Dockerfile for the frontend service using Nginx
- `docker-compose.yml`: Docker Compose configuration to orchestrate both services
- `nginx.conf`: Custom Nginx configuration for the frontend service

## Prerequisites

- Docker and Docker Compose installed on your system
- No other services running on ports 5001 and 8000

## Usage

### Starting the Application

From the project root directory, run:

```bash
cd docker
docker-compose up -d
```

This will:
1. Build the Docker images for both frontend and backend
2. Start the containers in detached mode
3. Map the necessary ports (backend: 5001, frontend: 8000)
4. Set up volume mapping for persistent data storage

### Accessing the Application

- Frontend: http://localhost:8000
- Backend API: http://localhost:5001/api

### Stopping the Application

```bash
cd docker
docker-compose down
```

### Viewing Logs

```bash
# View logs from all services
docker-compose logs

# View logs from a specific service
docker-compose logs backend
docker-compose logs frontend

# Follow logs in real-time
docker-compose logs -f
```

## Data Persistence

The application data (absence_periods.csv) is stored in a Docker volume that persists between container restarts. The data is mapped from the host's `server/data` directory to the container's `/app/data` directory.

## Troubleshooting

If you encounter issues:

1. Check if the containers are running:
   ```bash
   docker-compose ps
   ```

2. Check container logs for errors:
   ```bash
   docker-compose logs
   ```

3. Ensure no other services are using ports 5001 and 8000

4. Rebuild the containers if needed:
   ```bash
   docker-compose build --no-cache
   docker-compose up -d
   ```
