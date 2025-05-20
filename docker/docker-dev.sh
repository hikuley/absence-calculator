#!/bin/bash

# Shell script to manage Docker operations for the 180-Day Rule Calculator
# Usage: 
#   ./docker-dev.sh start   - Start the containers
#   ./docker-dev.sh stop    - Stop the containers
#   ./docker-dev.sh deploy  - Build and start the containers
#   ./docker-dev.sh logs    - View container logs
#   ./docker-dev.sh redeploy - Clean image and build again

# Configuration
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DOCKER_COMPOSE_FILE="$PROJECT_DIR/docker/docker-compose.yml"

# Function to check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        echo "Error: Docker is not running. Please start Docker and try again."
        exit 1
    fi
}

# Function to start containers
start() {
    echo "Starting containers..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" up -d
    echo "Containers started successfully!"
    echo "Frontend: http://localhost:8000"
    echo "Backend: http://localhost:5001"
}

# Function to stop containers
stop() {
    echo "Stopping containers..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" down
    echo "Containers stopped successfully!"
}

# Function to deploy (build and start) containers
deploy() {
    echo "Building and starting containers..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" up --build -d
    echo "Containers deployed successfully!"
    echo "Frontend: http://localhost:8000"
    echo "Backend: http://localhost:5001"
}

# Function to view logs
logs() {
    echo "Viewing container logs (press Ctrl+C to exit)..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" logs -f
}

# Function to clean and rebuild containers
redeploy() {
    echo "Cleaning containers and images..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" down --rmi all
    echo "Building containers from scratch..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" up --build -d
    echo "Containers cleaned and rebuilt successfully!"
    echo "Frontend: http://localhost:8000"
    echo "Backend: http://localhost:5001"
}

# Main script execution
check_docker

case "$1" in
    "start")
        start
        ;;
    "stop")
        stop
        ;;
    "deploy")
        deploy
        ;;
    "logs")
        logs
        ;;
    "redeploy")
        redeploy
        ;;
    *)
        echo "Usage: $0 {start|stop|deploy|logs|redeploy}"
        echo "  start    - Start the containers"
        echo "  stop     - Stop the containers"
        echo "  deploy   - Build and start the containers"
        echo "  logs     - View container logs"
        echo "  redeploy - Clean image and build again"
        exit 1
        ;;
esac 