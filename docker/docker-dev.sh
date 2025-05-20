#!/bin/bash

# Script to manage Docker environment for Absence Calculator

# Configuration
DOCKER_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$DOCKER_DIR")"

# Function to display usage information
show_usage() {
    echo "Usage: $0 {start|stop|restart|logs|status}"
    echo "  start   - Start the Docker containers"
    echo "  stop    - Stop the Docker containers"
    echo "  restart - Restart the Docker containers"
    echo "  logs    - View container logs"
    echo "  status  - Check container status"
    exit 1
}

# Function to start containers
start_containers() {
    echo "Starting Docker containers..."
    cd "$DOCKER_DIR" || exit 1
    docker-compose up -d
    
    echo "Waiting for services to start..."
    sleep 3
    
    echo "Checking container status..."
    docker-compose ps
    
    echo ""
    echo "Absence Calculator is now running in Docker!"
    echo "Frontend: http://localhost:8000"
    echo "Backend API: http://localhost:5001/api"
    echo "Use './docker-dev.sh stop' to stop the containers."
}

# Function to stop containers
stop_containers() {
    echo "Stopping Docker containers..."
    cd "$DOCKER_DIR" || exit 1
    docker-compose down
    echo "All containers stopped."
}

# Function to view logs
view_logs() {
    echo "Viewing container logs (press Ctrl+C to exit)..."
    cd "$DOCKER_DIR" || exit 1
    docker-compose logs -f
}

# Function to check status
check_status() {
    echo "Checking container status..."
    cd "$DOCKER_DIR" || exit 1
    docker-compose ps
}

# Main script execution
case "$1" in
    start)
        start_containers
        ;;
    stop)
        stop_containers
        ;;
    restart)
        stop_containers
        start_containers
        ;;
    logs)
        view_logs
        ;;
    status)
        check_status
        ;;
    *)
        show_usage
        ;;
esac

exit 0
