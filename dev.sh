#!/bin/bash

# Shell script to run and stop the 180-Day Rule Calculator servers
# Usage: 
#   ./dev.sh start  - Start PostgreSQL, backend and frontend servers
#   ./dev.sh restart - Restart all servers
#   ./dev.sh stop - Stop all servers
#   ./dev.sh init-db - Initialize database schema

# Configuration
BACKEND_PORT=5001
FRONTEND_PORT=8000
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVER_DIR="$PROJECT_DIR/server"
VENV_DIR="$SERVER_DIR/venv"
VENV_ACTIVATE="$VENV_DIR/bin/activate"
PID_FILE="$PROJECT_DIR/.server_pids"
LOGS_DIR="$PROJECT_DIR/logs"
BACKEND_LOG="$LOGS_DIR/backend.log"
FRONTEND_LOG="$LOGS_DIR/frontend.log"
PG_LOG="$LOGS_DIR/postgres.log"
# No CSV file needed anymore

# PostgreSQL configuration
PG_CONTAINER_NAME="absence-calculator-db"
PG_PORT=5432
PG_USER="postgres"
PG_PASSWORD="postgres"
PG_DB="absence_calculator"
PG_DATA_DIR="$PROJECT_DIR/.postgres_data"

# Function to check if a port is in use
is_port_in_use() {
    lsof -i :"$1" >/dev/null 2>&1
    return $?
}

# Function to check if Docker is installed and running
check_docker() {
    if ! command -v docker &> /dev/null; then
        echo "Error: Docker is not installed. Please install Docker first."
        echo "You can download Docker from https://www.docker.com/products/docker-desktop"
        return 1
    fi
    
    if ! docker info &> /dev/null; then
        echo "Warning: Docker daemon is not running. Please start Docker Desktop."
        echo "PostgreSQL database requires Docker to be running."
        echo "Start Docker Desktop and then run this script again."
        return 1
    fi
    
    return 0
}

# Function to check if the virtual environment exists and install required packages
check_venv() {
    # Check if virtual environment exists
    if [ ! -f "$VENV_ACTIVATE" ]; then
        echo "Virtual environment not found at $VENV_DIR"
        echo "Creating virtual environment..."
        python3 -m venv "$VENV_DIR"
    fi
    
    # Activate virtual environment
    source "$VENV_ACTIVATE"
    
    # Install required packages
    echo "Checking and installing required packages..."
    pip install --quiet fastapi uvicorn pydantic python-dateutil
    
    # Install Tortoise ORM and PostgreSQL dependencies
    echo "Installing Tortoise ORM and PostgreSQL dependencies..."
    pip install --quiet tortoise-orm asyncpg aerich python-dotenv PyJWT bcrypt
    
    # Check if packages are installed (without importing)
    if ! pip show tortoise-orm &>/dev/null || ! pip show asyncpg &>/dev/null; then
        echo "Error: Some required Tortoise ORM packages are missing. Please install them manually:"
        echo "source $VENV_ACTIVATE"
        echo "pip install tortoise-orm asyncpg aerich python-dotenv PyJWT bcrypt"
        exit 1
    fi
    
    echo "All required packages are installed."
}

# Function to ensure PostgreSQL container is available and running
ensure_postgres() {
    # Check if Docker is running
    if ! docker info &> /dev/null; then
        echo "Error: Docker is not running. Please start Docker first."
        return 1
    fi
    
    # Check if PostgreSQL container exists and is running
    if docker ps | grep -q "$PG_CONTAINER_NAME"; then
        echo "PostgreSQL container is already running."
        return 0
    fi
    
    echo "PostgreSQL container is not running. Starting it automatically..."
    
    # If container exists but is stopped, start it
    if docker ps -a | grep -q "$PG_CONTAINER_NAME"; then
        echo "Starting existing PostgreSQL container..."
        docker start "$PG_CONTAINER_NAME" > /dev/null
    else
        echo "Creating and starting new PostgreSQL container..."
        
        # Create data directory if it doesn't exist
        mkdir -p "$PG_DATA_DIR"
        
        # Run PostgreSQL container
        docker run -d \
            --name "$PG_CONTAINER_NAME" \
            -e POSTGRES_USER="$PG_USER" \
            -e POSTGRES_PASSWORD="$PG_PASSWORD" \
            -e POSTGRES_DB="$PG_DB" \
            -p "$PG_PORT:5432" \
            -v "$PG_DATA_DIR:/var/lib/postgresql/data" \
            postgres:15 > /dev/null
    fi
    
    # Wait for PostgreSQL to start
    echo "Waiting for PostgreSQL to start..."
    for i in {1..30}; do
        if docker exec "$PG_CONTAINER_NAME" pg_isready -U "$PG_USER" &> /dev/null; then
            echo "PostgreSQL is ready!"
            return 0
        fi
        echo -n "."
        sleep 1
    done
    
    echo "\nError: PostgreSQL failed to start within 30 seconds."
    return 1
}

# Function to start PostgreSQL container (for backward compatibility)
start_postgres() {
    ensure_postgres
    return $?
}

# Function to initialize database schema
initialize_database() {
    echo "Initializing database schema..."
    
    # Activate virtual environment
    source "$VENV_ACTIVATE"
    
    # Set environment variables for database connection
    export DB_USER="$PG_USER"
    export DB_PASSWORD="$PG_PASSWORD"
    export DB_HOST="localhost"
    export DB_PORT="$PG_PORT"
    export DB_NAME="$PG_DB"
    
    # Create database schema using Tortoise ORM
    cd "$SERVER_DIR"
    python -c "from migrations import run_initialize_database; run_initialize_database()" || {
        echo "Error: Failed to initialize database schema."
        return 1
    }
    
    echo "Database schema initialized successfully."
    return 0
}

# Function to start the backend server
start_backend() {
    echo "Starting backend server..."
    
    # Check if the backend server is already running
    if [ -f "$PID_FILE.backend" ]; then
        BACKEND_PID=$(cat "$PID_FILE.backend")
        if ps -p "$BACKEND_PID" > /dev/null; then
            echo "Backend server is already running (PID: $BACKEND_PID)."
            return 0
        fi
        rm "$PID_FILE.backend"
    fi
    
    # Check if the port is in use
    if is_port_in_use "$BACKEND_PORT"; then
        echo "Error: Port $BACKEND_PORT is already in use. Cannot start backend server."
        return 1
    fi
    
    # Ensure PostgreSQL is running before starting the backend
    ensure_postgres || {
        echo "Error: Cannot start backend server without PostgreSQL."
        return 1
    }
    
    # Create logs directory if it doesn't exist
    mkdir -p "$LOGS_DIR"
    
    # Activate virtual environment
    source "$VENV_ACTIVATE"
    
    # Set environment variables for database connection
    export DB_USER="$PG_USER"
    export DB_PASSWORD="$PG_PASSWORD"
    export DB_HOST="localhost"
    export DB_PORT="$PG_PORT"
    export DB_NAME="$PG_DB"
    
    # Start the backend server
    cd "$SERVER_DIR"
    nohup uvicorn app:app --host 0.0.0.0 --port "$BACKEND_PORT" > "$BACKEND_LOG" 2>&1 &
    BACKEND_PID=$!
    echo $BACKEND_PID > "$PID_FILE.backend"
    
    # Wait for the server to start
    echo "Waiting for backend server to start..."
    for i in {1..10}; do
        if curl -s http://localhost:$BACKEND_PORT/api/health > /dev/null; then
            echo "Backend server started successfully!"
            return 0
        fi
        echo -n "."
        sleep 1
    done
    
    echo "\nError: Backend server failed to start within 10 seconds."
    return 1
}

# Function to start the frontend server
start_frontend() {
    echo "Starting frontend server on port $FRONTEND_PORT..."
    
    # Check if port is already in use
    if is_port_in_use "$FRONTEND_PORT"; then
        echo "Port $FRONTEND_PORT is already in use. Stopping the existing server..."
        lsof -ti :"$FRONTEND_PORT" | xargs kill -9 2>/dev/null
        sleep 1
    fi
    
    # Create logs directory if it doesn't exist
    mkdir -p "$LOGS_DIR"
    
    # Start the HTTP server
    cd "$PROJECT_DIR/frontend" || exit 1
    python3 -m http.server "$FRONTEND_PORT" > "$FRONTEND_LOG" 2>&1 &
    FRONTEND_PID=$!
    
    echo "Frontend server started with PID: $FRONTEND_PID"
    echo "$FRONTEND_PID" > "$PID_FILE.frontend"
    
    # Wait for server to start
    echo "Waiting for frontend server to start..."
    sleep 2
}

# Function to open the browser
open_browser() {
    URL="http://localhost:$FRONTEND_PORT"
    echo "Opening browser at $URL"
    
    # Open browser based on OS
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        open "$URL"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        xdg-open "$URL" &> /dev/null || sensible-browser "$URL" &> /dev/null || x-www-browser "$URL" &> /dev/null || gnome-open "$URL" &> /dev/null
    elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
        # Windows
        start "$URL"
    else
        echo "Please open a browser and navigate to: $URL"
    fi
}

# Function to view logs
view_logs() {
    echo "Viewing server logs (press Ctrl+C to exit)..."
    
    # Check if logs directory exists
    if [ ! -d "$LOGS_DIR" ]; then
        echo "Logs directory not found. Have you started the servers?"
        mkdir -p "$LOGS_DIR"
        touch "$BACKEND_LOG" "$FRONTEND_LOG" "$PG_LOG"
    fi
    
    # Check if log files exist
    if [ ! -f "$BACKEND_LOG" ]; then
        echo "Backend log file not found. Creating empty file."
        touch "$BACKEND_LOG"
    fi
    
    if [ ! -f "$FRONTEND_LOG" ]; then
        echo "Frontend log file not found. Creating empty file."
        touch "$FRONTEND_LOG"
    fi
    
    if [ ! -f "$PG_LOG" ]; then
        echo "PostgreSQL log file not found. Creating empty file."
        touch "$PG_LOG"
    fi
    
    # Get PostgreSQL logs if container is running
    if docker ps | grep -q "$PG_CONTAINER_NAME"; then
        echo "Fetching PostgreSQL logs..."
        docker logs "$PG_CONTAINER_NAME" > "$PG_LOG" 2>&1
    fi
    
    # Display logs side by side if possible, otherwise use tail -f
    if command -v tmux &> /dev/null; then
        echo "Using tmux to display logs side by side. Press Ctrl+B then D to detach."
        tmux new-session "echo 'BACKEND LOG:'; echo '------------'; tail -f $BACKEND_LOG" \
            \; split-window "echo 'FRONTEND LOG:'; echo '-------------'; tail -f $FRONTEND_LOG" \
            \; split-window "echo 'POSTGRESQL LOG:'; echo '---------------'; tail -f $PG_LOG" \
            \; select-layout even-vertical
    else
        echo "BACKEND LOG:"
        echo "------------"
        tail -f "$BACKEND_LOG" & BACKEND_TAIL_PID=$!
        
        echo ""
        echo "FRONTEND LOG:"
        echo "-------------"
        tail -f "$FRONTEND_LOG" & FRONTEND_TAIL_PID=$!
        
        echo ""
        echo "POSTGRESQL LOG:"
        echo "---------------"
        tail -f "$PG_LOG" & PG_TAIL_PID=$!
        
        # Wait for user to press Ctrl+C
        trap "kill $BACKEND_TAIL_PID $FRONTEND_TAIL_PID $PG_TAIL_PID 2>/dev/null; exit" INT
        wait
    fi
}

# Function to stop PostgreSQL container
stop_postgres() {
    echo "Stopping PostgreSQL container..."
    
    # Check if Docker is running
    if ! docker info &> /dev/null; then
        echo "Docker is not running, no need to stop PostgreSQL container."
        return 0
    fi
    
    # Check if PostgreSQL container is running
    if docker ps | grep -q "$PG_CONTAINER_NAME"; then
        echo "Stopping PostgreSQL container..."
        docker stop "$PG_CONTAINER_NAME" > /dev/null
    else
        echo "PostgreSQL container is not running."
    fi
}

# Function to stop all servers
stop_servers() {
    echo "Stopping all servers..."
    
    # Stop backend server
    if [ -f "$PID_FILE.backend" ]; then
        BACKEND_PID=$(cat "$PID_FILE.backend")
        if ps -p "$BACKEND_PID" > /dev/null; then
            echo "Stopping backend server (PID: $BACKEND_PID)..."
            kill -9 "$BACKEND_PID" 2>/dev/null
        else
            echo "Backend server is not running."
        fi
        rm "$PID_FILE.backend"
    fi
    
    # Stop frontend server
    if [ -f "$PID_FILE.frontend" ]; then
        FRONTEND_PID=$(cat "$PID_FILE.frontend")
        if ps -p "$FRONTEND_PID" > /dev/null; then
            echo "Stopping frontend server (PID: $FRONTEND_PID)..."
            kill -9 "$FRONTEND_PID" 2>/dev/null
        else
            echo "Frontend server is not running."
        fi
        rm "$PID_FILE.frontend"
    fi
    
    # Alternative method to stop servers by port
    if is_port_in_use "$BACKEND_PORT"; then
        echo "Stopping any process using port $BACKEND_PORT..."
        lsof -ti :"$BACKEND_PORT" | xargs kill -9 2>/dev/null
    fi
    
    if is_port_in_use "$FRONTEND_PORT"; then
        echo "Stopping any process using port $FRONTEND_PORT..."
        lsof -ti :"$FRONTEND_PORT" | xargs kill -9 2>/dev/null
    fi
    
    # Stop PostgreSQL container
    stop_postgres
    
    echo "All servers stopped."
}

# Function to check PostgreSQL status
check_postgres_status() {
    echo "Checking PostgreSQL status..."
    
    if docker ps | grep -q "$PG_CONTAINER_NAME"; then
        echo "PostgreSQL container is running."
        if docker exec "$PG_CONTAINER_NAME" pg_isready -U "$PG_USER" &> /dev/null; then
            echo "PostgreSQL server is accepting connections."
            return 0
        else
            echo "PostgreSQL container is running but not accepting connections."
            return 1
        fi
    else
        echo "PostgreSQL container is not running."
        return 1
    fi
}

# Main script execution
# Only process the first argument
case "$1" in
    start)
        # First stop any existing servers
        stop_servers
        
        # Check requirements
        check_venv
        
        # Check if Docker is running
        if ! check_docker; then
            echo "Error: Cannot start servers without Docker running."
            exit 1
        fi
        
        # Ensure PostgreSQL is running
        ensure_postgres || exit 1
        
        # Initialize database schema
        initialize_database
        
        # Start application servers
        start_backend
        start_frontend
        open_browser
        
        echo ""
        echo "180-Day Rule Calculator is now running with PostgreSQL!"
        echo "PostgreSQL: localhost:$PG_PORT (container: $PG_CONTAINER_NAME)"
        echo "Backend server: http://localhost:$BACKEND_PORT"
        echo "Frontend interface: http://localhost:$FRONTEND_PORT"
        echo "Use './dev.sh stop' to stop all servers."
        ;;
    restart)
        # Stop any existing servers
        stop_servers
        
        # Check requirements
        check_venv
        
        # Check if Docker is running
        if ! check_docker; then
            echo "Error: Cannot restart servers without Docker running."
            exit 1
        fi
        
        # Ensure PostgreSQL is running
        ensure_postgres || exit 1
        
        # Initialize database schema
        initialize_database
        
        # Start application servers
        start_backend
        start_frontend
        open_browser
        
        echo ""
        echo "180-Day Rule Calculator has been restarted with PostgreSQL!"
        echo "PostgreSQL: localhost:$PG_PORT (container: $PG_CONTAINER_NAME)"
        echo "Backend server: http://localhost:$BACKEND_PORT"
        echo "Frontend interface: http://localhost:$FRONTEND_PORT"
        echo "Use './dev.sh stop' to stop all servers."
        ;;
    stop)
        stop_servers
        ;;
    logs)
        view_logs
        ;;
    init-db)
        check_venv
        
        # Check if Docker is running
        if ! check_docker; then
            echo "Error: Cannot initialize database without Docker running."
            exit 1
        fi
        
        ensure_postgres || exit 1
        initialize_database
        ;;
    pg-status)
        check_postgres_status
        ;;
    *)
        echo "Usage: $0 {start|restart|stop|logs|init-db|pg-status}"
        echo "  start     - Start PostgreSQL, backend, and frontend servers"
        echo "  restart   - Restart all servers"
        echo "  stop      - Stop all servers"
        echo "  logs      - View server logs (press Ctrl+C to exit)"
        echo "  init-db   - Initialize database schema"
        echo "  pg-status - Check PostgreSQL container status"
        exit 1
        ;;
esac

exit 0
