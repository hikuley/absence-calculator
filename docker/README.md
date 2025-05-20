# Docker Deployment Guide

This guide explains how to deploy the 180-Day Rule Calculator application using Docker.

## Prerequisites

- Docker installed on your system
- Docker Compose installed on your system

## Directory Structure

```
.
├── docker/
│   ├── backend/
│   │   └── Dockerfile
│   ├── frontend/
│   │   └── Dockerfile
│   ├── docker-compose.yml
│   ├── docker-dev.sh
│   └── README.md
├── server/
│   └── data/
│       └── absence_periods.csv
└── frontend/
```

## Quick Start

We provide a convenient script `docker-dev.sh` to manage Docker operations:

```bash
# Make the script executable (first time only)
chmod +x docker/docker-dev.sh

# Deploy the application (build and start)
./docker/docker-dev.sh deploy

# Start the containers (if already built)
./docker/docker-dev.sh start

# Stop the containers
./docker/docker-dev.sh stop

# View container logs
./docker/docker-dev.sh logs
```

## Manual Deployment Steps

If you prefer to run Docker commands directly:

1. Make sure you have the required CSV file in place:
   ```
   server/data/absence_periods.csv
   ```

2. From the project root directory, run:
   ```bash
   docker-compose -f docker/docker-compose.yml up --build
   ```

   This will:
   - Build both frontend and backend containers
   - Start the services
   - Make the application available at http://localhost:8000

3. To stop the services:
   ```bash
   docker-compose -f docker/docker-compose.yml down
   ```

## Service Details

- Frontend: Available at http://localhost:8000
- Backend API: Available at http://localhost:5001

## Data Persistence

The CSV file is mounted as a volume, so any changes made to the data will persist even after container restarts.

## Troubleshooting

If you encounter any issues:

1. Check if the ports 8000 and 5001 are available on your system
2. Ensure the CSV file exists in the correct location
3. Check the container logs:
   ```bash
   ./docker/docker-dev.sh logs
   ```
   or
   ```bash
   docker-compose -f docker/docker-compose.yml logs
   ```

## Development

For development purposes, you can use the `dev.sh` script instead of Docker. The Docker setup is primarily intended for production deployment. 