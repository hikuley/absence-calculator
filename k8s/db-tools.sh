#!/bin/bash

# Script to manage PostgreSQL database operations in Kubernetes
# Usage:
#   ./db-tools.sh backup - Backup PostgreSQL database
#   ./db-tools.sh restore - Restore PostgreSQL database from backup
#   ./db-tools.sh migrate - Migrate data from CSV to PostgreSQL database
#   ./db-tools.sh shell - Open a PostgreSQL shell

# Check if kubectl is installed
if ! command -v kubectl &> /dev/null; then
    echo "Error: kubectl is not installed"
    exit 1
fi

# Function to get the PostgreSQL pod name
get_postgres_pod() {
    kubectl get pods -l app=postgres -o jsonpath="{.items[0].metadata.name}" 2>/dev/null
}

# Function to backup the database
backup_database() {
    echo "Backing up PostgreSQL database..."
    
    # Get the PostgreSQL pod name
    POSTGRES_POD=$(get_postgres_pod)
    
    if [ -z "$POSTGRES_POD" ]; then
        echo "Error: PostgreSQL pod not found. Make sure the application is running."
        exit 1
    fi
    
    # Create backup directory if it doesn't exist
    BACKUP_DIR="./k8s/backups"
    mkdir -p "$BACKUP_DIR"
    
    # Generate backup filename with timestamp
    TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
    BACKUP_FILE="$BACKUP_DIR/absence_calculator_$TIMESTAMP.sql"
    
    # Run pg_dump in the PostgreSQL pod
    echo "Running pg_dump in pod $POSTGRES_POD..."
    kubectl exec "$POSTGRES_POD" -- pg_dump -U postgres absence_calculator > "$BACKUP_FILE"
    
    if [ $? -eq 0 ]; then
        echo "Backup completed successfully: $BACKUP_FILE"
    else
        echo "Error: Backup failed"
        exit 1
    fi
}

# Function to restore the database
restore_database() {
    echo "Restoring PostgreSQL database..."
    
    # Get the PostgreSQL pod name
    POSTGRES_POD=$(get_postgres_pod)
    
    if [ -z "$POSTGRES_POD" ]; then
        echo "Error: PostgreSQL pod not found. Make sure the application is running."
        exit 1
    fi
    
    # Check if backup directory exists
    BACKUP_DIR="./k8s/backups"
    if [ ! -d "$BACKUP_DIR" ]; then
        echo "Error: Backup directory not found: $BACKUP_DIR"
        exit 1
    fi
    
    # List available backups
    BACKUPS=("$BACKUP_DIR"/*.sql)
    if [ ${#BACKUPS[@]} -eq 0 ] || [ ! -f "${BACKUPS[0]}" ]; then
        echo "Error: No backup files found in $BACKUP_DIR"
        exit 1
    fi
    
    echo "Available backups:"
    for i in "${!BACKUPS[@]}"; do
        echo "[$i] $(basename "${BACKUPS[$i]}")"
    done
    
    # Prompt for backup selection
    read -p "Enter the number of the backup to restore: " BACKUP_NUM
    if [ -z "${BACKUPS[$BACKUP_NUM]}" ] || [ ! -f "${BACKUPS[$BACKUP_NUM]}" ]; then
        echo "Error: Invalid backup selection"
        exit 1
    fi
    
    BACKUP_FILE="${BACKUPS[$BACKUP_NUM]}"
    echo "Restoring from $BACKUP_FILE..."
    
    # Drop and recreate the database
    echo "Dropping and recreating database..."
    kubectl exec "$POSTGRES_POD" -- psql -U postgres -c "DROP DATABASE IF EXISTS absence_calculator;"
    kubectl exec "$POSTGRES_POD" -- psql -U postgres -c "CREATE DATABASE absence_calculator;"
    
    # Restore from backup
    echo "Restoring database from backup..."
    cat "$BACKUP_FILE" | kubectl exec -i "$POSTGRES_POD" -- psql -U postgres absence_calculator
    
    if [ $? -eq 0 ]; then
        echo "Database restored successfully!"
    else
        echo "Error: Database restore failed"
        exit 1
    fi
}

# Function to migrate data from CSV to PostgreSQL
migrate_data() {
    echo "Migrating data from CSV to PostgreSQL database..."
    
    # Get the backend pod name
    BACKEND_POD=$(kubectl get pods -l app=backend -o jsonpath="{.items[0].metadata.name}" 2>/dev/null)
    
    if [ -z "$BACKEND_POD" ]; then
        echo "Error: Backend pod not found. Make sure the application is running."
        exit 1
    fi
    
    # Run migration script in the backend pod
    echo "Running migration script in pod $BACKEND_POD..."
    kubectl exec "$BACKEND_POD" -- bash -c "cd /app/server && python migrate_csv_to_db.py"
    
    if [ $? -eq 0 ]; then
        echo "Data migration completed successfully!"
    else
        echo "Error: Data migration failed"
        exit 1
    fi
}

# Function to open a PostgreSQL shell
open_shell() {
    echo "Opening PostgreSQL shell..."
    
    # Get the PostgreSQL pod name
    POSTGRES_POD=$(get_postgres_pod)
    
    if [ -z "$POSTGRES_POD" ]; then
        echo "Error: PostgreSQL pod not found. Make sure the application is running."
        exit 1
    fi
    
    # Open PostgreSQL shell
    echo "Connecting to PostgreSQL in pod $POSTGRES_POD..."
    kubectl exec -it "$POSTGRES_POD" -- psql -U postgres absence_calculator
}

# Main script
case "$1" in
    "backup")
        backup_database
        ;;
    "restore")
        restore_database
        ;;
    "migrate")
        migrate_data
        ;;
    "shell")
        open_shell
        ;;
    *)
        echo "Usage: $0 {backup|restore|migrate|shell}"
        echo "  backup  - Backup PostgreSQL database"
        echo "  restore - Restore PostgreSQL database from backup"
        echo "  migrate - Migrate data from CSV to PostgreSQL database"
        echo "  shell   - Open a PostgreSQL shell"
        exit 1
        ;;
esac
