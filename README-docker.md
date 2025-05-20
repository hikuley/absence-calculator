# Docker Deployment Guide for 180-Day Rule Calculator

This guide explains how to deploy the 180-Day Rule Calculator application using Docker and Docker Compose.

## Prerequisites

- Docker installed on your machine
- Docker Compose installed on your machine

## Deployment Steps

### 1. Prepare the Application

First, ensure you have the application code on your machine:

```bash
git clone <repository-url>
cd absence-calculator
```

### 2. Create Data Directory for Persistence

Create a directory for persistent data storage and copy the initial absence periods CSV file:

```bash
mkdir -p server/data
cp absence_periods.csv server/data/
```

### 3. Build and Start the Containers

Use Docker Compose to build and start the application containers:

```bash
docker-compose up --build -d
```

This command will:
- Build the Docker images for both frontend and backend
- Create and start the containers
- Set up networking between the containers
- Mount the data volume for persistence

### 4. Access the Application

Once the containers are running, you can access the application at:

- Frontend: http://localhost:8080
- Backend API: http://localhost:5001

### 5. Managing the Application

To check the status of your containers:

```bash
docker-compose ps
```

To view logs from the containers:

```bash
docker-compose logs
```

To view logs from a specific service:

```bash
docker-compose logs backend
docker-compose logs frontend
```

### 6. Stopping the Application

To stop the application while preserving data:

```bash
docker-compose down
```

To stop the application and remove all data:

```bash
docker-compose down -v
```

## Docker Compose Configuration

The `docker-compose.yml` file defines two services:

1. **Backend Service**:
   - Built from the `./server` directory
   - Exposes port 5001
   - Mounts a volume for data persistence
   - Sets environment variables for configuration

2. **Frontend Service**:
   - Built from the project root directory
   - Exposes port 8080
   - Depends on the backend service
   - Configured to communicate with the backend

## Troubleshooting

If you encounter issues with the deployment:

1. Check if the containers are running:
   ```bash
   docker-compose ps
   ```

2. View the logs for error messages:
   ```bash
   docker-compose logs
   ```

3. Ensure the data directory has the correct permissions:
   ```bash
   chmod -R 755 server/data
   ```

4. If the backend can't connect to the frontend, ensure the network is properly configured in the docker-compose.yml file.

5. If changes to the code are not reflected, rebuild the containers:
   ```bash
   docker-compose up --build -d
   ```
