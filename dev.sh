#!/bin/bash

# Shell script to run and stop the 180-Day Rule Calculator servers
# Usage: 
#   ./dev.sh start  - Start both backend and frontend servers
#   ./dev.sh restart - Restart both backend and frontend servers
#   ./dev.sh stop - Stop both servers

# Configuration
BACKEND_PORT=5001
FRONTEND_PORT=8000
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVER_DIR="$PROJECT_DIR/server"
VENV_DIR="$PROJECT_DIR/venv"
VENV_ACTIVATE="$VENV_DIR/bin/activate"
PID_FILE="$PROJECT_DIR/.server_pids"
LOGS_DIR="$PROJECT_DIR/logs"
BACKEND_LOG="$LOGS_DIR/backend.log"
FRONTEND_LOG="$LOGS_DIR/frontend.log"
CSV_FILE_PATH="$PROJECT_DIR/server/data/absence_periods.csv"

# Function to check if a port is in use
is_port_in_use() {
    lsof -i :"$1" >/dev/null 2>&1
    return $?
}

# Function to check if the virtual environment exists
check_venv() {
    if [ ! -f "$VENV_ACTIVATE" ]; then
        echo "Virtual environment not found at $VENV_DIR"
        echo "Please set up the virtual environment first:"
        echo "python3 -m venv $VENV_DIR"
        echo "source $VENV_ACTIVATE"
        echo "pip install flask flask-cors"
        exit 1
    fi
}

# Function to start the backend server
start_backend() {
    echo "Starting backend server on port $BACKEND_PORT..."
    
    # Check if port is already in use
    if is_port_in_use "$BACKEND_PORT"; then
        echo "Port $BACKEND_PORT is already in use. Stopping the existing server..."
        lsof -ti :"$BACKEND_PORT" | xargs kill -9 2>/dev/null
        sleep 1
    fi
    
    # Create logs directory if it doesn't exist
    mkdir -p "$LOGS_DIR"
    
    # Start the Flask server
    source "$VENV_ACTIVATE"
    cd "$SERVER_DIR" || exit 1
    CSV_FILE_PATH="$CSV_FILE_PATH" python3 app.py > "$BACKEND_LOG" 2>&1 &
    BACKEND_PID=$!
    
    echo "Backend server started with PID: $BACKEND_PID"
    echo "$BACKEND_PID" > "$PID_FILE.backend"
    
    # Wait for server to start
    echo "Waiting for backend server to start..."
    sleep 3
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
    cd "$PROJECT_DIR" || exit 1
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
        touch "$BACKEND_LOG" "$FRONTEND_LOG"
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
    
    # Display logs side by side if possible, otherwise use tail -f
    if command -v tmux &> /dev/null; then
        echo "Using tmux to display logs side by side. Press Ctrl+B then D to detach."
        tmux new-session "echo 'BACKEND LOG:'; echo '------------'; tail -f $BACKEND_LOG" \; split-window "echo 'FRONTEND LOG:'; echo '-------------'; tail -f $FRONTEND_LOG" \; select-layout even-vertical
    else
        echo "BACKEND LOG:"
        echo "------------"
        tail -f "$BACKEND_LOG" & BACKEND_TAIL_PID=$!
        
        echo ""
        echo "FRONTEND LOG:"
        echo "-------------"
        tail -f "$FRONTEND_LOG" & FRONTEND_TAIL_PID=$!
        
        # Wait for user to press Ctrl+C
        trap "kill $BACKEND_TAIL_PID $FRONTEND_TAIL_PID 2>/dev/null; exit" INT
        wait
    fi
}

# Function to stop the servers
stop_servers() {
    echo "Stopping servers..."
    
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
    
    echo "All servers stopped."
}

# Main script execution
# Only process the first argument
case "$1" in
    start)
        # First stop any existing servers
        stop_servers
        
        # Then start new servers
        check_venv
        start_backend
        start_frontend
        open_browser
        
        echo ""
        echo "180-Day Rule Calculator is now running!"
        echo "Backend server: http://localhost:$BACKEND_PORT"
        echo "Frontend interface: http://localhost:$FRONTEND_PORT"
        echo "Use './dev.sh stop' to stop the servers."
        ;;
    restart)
        # Stop any existing servers
        stop_servers
        
        # Then start new servers
        check_venv
        start_backend
        start_frontend
        open_browser
        
        echo ""
        echo "180-Day Rule Calculator has been restarted!"
        echo "Backend server: http://localhost:$BACKEND_PORT"
        echo "Frontend interface: http://localhost:$FRONTEND_PORT"
        echo "Use './dev.sh stop' to stop the servers."
        ;;
    stop)
        stop_servers
        ;;
    logs)
        view_logs
        ;;
    *)
        echo "Usage: $0 {start|restart|stop|logs}"
        echo "  start   - Start both backend and frontend servers"
        echo "  restart - Restart both backend and frontend servers"
        echo "  stop    - Stop both servers"
        echo "  logs    - View server logs (press Ctrl+C to exit)"
        exit 1
        ;;
esac

exit 0
