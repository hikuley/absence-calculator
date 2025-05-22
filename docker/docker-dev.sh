#!/bin/bash

# Shell script to manage Docker operations for the 180-Day Rule Calculator
# Usage: 
#   ./docker-dev.sh start     - Start the containers
#   ./docker-dev.sh stop      - Stop the containers
#   ./docker-dev.sh deploy    - Build and start the containers
#   ./docker-dev.sh logs      - View container logs
#   ./docker-dev.sh redeploy  - Clean image and build again
#   ./docker-dev.sh db-backup - Backup PostgreSQL database
#   ./docker-dev.sh db-restore - Restore PostgreSQL database from backup

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

# Function to backup PostgreSQL database
db_backup() {
    echo "Backing up PostgreSQL database..."
    TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
    BACKUP_DIR="$PROJECT_DIR/backups"
    mkdir -p "$BACKUP_DIR"
    
    # Check if postgres container is running
    if ! docker-compose -f "$DOCKER_COMPOSE_FILE" ps | grep -q "postgres.*Up"; then
        echo "PostgreSQL container is not running. Starting it..."
        docker-compose -f "$DOCKER_COMPOSE_FILE" up -d postgres
        sleep 5  # Wait for PostgreSQL to start
    fi
    
    # Run pg_dump in the postgres container
    docker-compose -f "$DOCKER_COMPOSE_FILE" exec -T postgres pg_dump -U postgres absence_calculator > "$BACKUP_DIR/absence_calculator_$TIMESTAMP.sql"
    
    echo "Database backed up to $BACKUP_DIR/absence_calculator_$TIMESTAMP.sql"
}

# Function to restore PostgreSQL database from backup
db_restore() {
    echo "Restoring PostgreSQL database from backup..."
    BACKUP_DIR="$PROJECT_DIR/backups"
    
    # Check if backup directory exists
    if [ ! -d "$BACKUP_DIR" ]; then
        echo "Backup directory not found: $BACKUP_DIR"
        exit 1
    fi
    
    # List available backups
    BACKUPS=("$BACKUP_DIR"/*.sql)
    if [ ${#BACKUPS[@]} -eq 0 ]; then
        echo "No backup files found in $BACKUP_DIR"
        exit 1
    fi
    
    echo "Available backups:"
    for i in "${!BACKUPS[@]}"; do
        echo "$i: $(basename "${BACKUPS[$i]}")"
    done
    
    # Prompt for backup selection
    read -p "Enter the number of the backup to restore: " BACKUP_NUM
    if [ -z "${BACKUPS[$BACKUP_NUM]}" ]; then
        echo "Invalid backup number"
        exit 1
    fi
    
    BACKUP_FILE="${BACKUPS[$BACKUP_NUM]}"
    echo "Restoring from $BACKUP_FILE..."
    
    # Check if postgres container is running
    if ! docker-compose -f "$DOCKER_COMPOSE_FILE" ps | grep -q "postgres.*Up"; then
        echo "PostgreSQL container is not running. Starting it..."
        docker-compose -f "$DOCKER_COMPOSE_FILE" up -d postgres
        sleep 5  # Wait for PostgreSQL to start
    fi
    
    # Drop and recreate the database
    docker-compose -f "$DOCKER_COMPOSE_FILE" exec -T postgres psql -U postgres -c "DROP DATABASE IF EXISTS absence_calculator;"
    docker-compose -f "$DOCKER_COMPOSE_FILE" exec -T postgres psql -U postgres -c "CREATE DATABASE absence_calculator;"
    
    # Restore from backup
    cat "$BACKUP_FILE" | docker-compose -f "$DOCKER_COMPOSE_FILE" exec -T postgres psql -U postgres absence_calculator
    
    echo "Database restored successfully!"
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
    "db-backup")
        db_backup
        ;;
    "db-restore")
        db_restore
        ;;
    *)
        echo "Usage: $0 {start|stop|deploy|logs|redeploy|db-backup|db-restore}"
        echo "  start      - Start the containers"
        echo "  stop       - Stop the containers"
        echo "  deploy     - Build and start the containers"
        echo "  logs       - View container logs"
        echo "  redeploy   - Clean image and build again"
        echo "  db-backup  - Backup PostgreSQL database"
        echo "  db-restore - Restore PostgreSQL database from backup"
        exit 1
        ;;
esac 