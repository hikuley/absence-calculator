#!/bin/bash

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if minikube is running
check_minikube() {
    if ! minikube status | grep -q "Running"; then
        echo "Error: minikube is not running"
        return 1
    fi
    return 0
}

# Function to check if Docker daemon is properly configured
check_docker_daemon() {
    if ! docker info >/dev/null 2>&1; then
        echo "Error: Docker daemon is not accessible"
        return 1
    fi
    return 0
}

# Function to wait for pods with detailed status
wait_for_pods() {
    local app=$1
    local timeout=300
    local start_time=$(date +%s)
    
    echo "Waiting for $app pods to be ready..."
    while true; do
        if kubectl get pods -l app=$app | grep -q "Running"; then
            echo "$app pods are ready!"
            return 0
        fi
        
        local current_time=$(date +%s)
        local elapsed=$((current_time - start_time))
        
        if [ $elapsed -gt $timeout ]; then
            echo "Error: Timeout waiting for $app pods"
            kubectl describe pods -l app=$app
            kubectl logs -l app=$app
            return 1
        fi
        
        echo "Waiting for $app pods... ($elapsed/$timeout seconds)"
        kubectl get pods -l app=$app
        sleep 5
    done
}

# Function to start port forwarding
start_port_forwarding() {
    # Create logs directory if it doesn't exist
    mkdir -p /tmp/absence-calculator
    
    # Stop any existing port forwarding
    stop_port_forwarding
    
    # Wait for pods to be fully ready before starting port forwarding
    echo "Ensuring all pods are fully ready before starting port forwarding..."
    
    # Function to wait for pod readiness with timeout
    wait_for_pod_ready() {
        local app_label=$1
        local max_attempts=30
        local attempt=1
        local ready=false
        
        echo "Waiting for $app_label pod to be fully ready..."
        
        while [ $attempt -le $max_attempts ] && [ "$ready" = "false" ]; do
            # Get pod name
            local pod_name=$(kubectl get pods -l app=$app_label -o jsonpath="{.items[0].metadata.name}" 2>/dev/null)
            
            # Check if pod exists
            if [ -z "$pod_name" ]; then
                echo "Attempt $attempt/$max_attempts: No $app_label pod found yet, waiting..."
                sleep 5
                attempt=$((attempt+1))
                continue
            fi
            
            # Check pod status
            local pod_status=$(kubectl get pod $pod_name -o jsonpath="{.status.phase}" 2>/dev/null)
            local container_ready=$(kubectl get pod $pod_name -o jsonpath="{.status.containerStatuses[0].ready}" 2>/dev/null)
            
            if [ "$pod_status" = "Running" ] && [ "$container_ready" = "true" ]; then
                echo "$app_label pod $pod_name is ready!"
                ready=true
                echo "$pod_name" > "/tmp/absence-calculator/${app_label}_pod_name"
            else
                echo "Attempt $attempt/$max_attempts: $app_label pod status: $pod_status, container ready: $container_ready"
                sleep 5
                attempt=$((attempt+1))
            fi
        done
        
        if [ "$ready" = "false" ]; then
            echo "Error: $app_label pod did not become ready after $max_attempts attempts"
            return 1
        fi
        
        return 0
    }
    
    # Wait for both frontend and backend pods to be ready
    wait_for_pod_ready "frontend" || return 1
    wait_for_pod_ready "backend" || return 1
    
    # Get pod names from saved files
    FRONTEND_POD=$(cat /tmp/absence-calculator/frontend_pod_name 2>/dev/null)
    BACKEND_POD=$(cat /tmp/absence-calculator/backend_pod_name 2>/dev/null)
    
    # Function to start port forwarding with retries
    start_port_forward() {
        local pod_name=$1
        local local_port=$2
        local pod_port=$3
        local log_file=$4
        local pid_file=$5
        local max_attempts=3
        local attempt=1
        
        while [ $attempt -le $max_attempts ]; do
            echo "Attempt $attempt/$max_attempts: Starting port forwarding for $pod_name on port $local_port:$pod_port"
            
            # Kill any existing processes using the port
            lsof -ti:$local_port | xargs kill -9 2>/dev/null || true
            
            # Start port forwarding
            kubectl port-forward pod/$pod_name $local_port:$pod_port > $log_file 2>&1 &
            local pid=$!
            echo $pid > $pid_file
            
            # Wait for port forwarding to establish
            echo "Waiting for port forwarding to establish..."
            sleep 5
            
            # Check if port forwarding is working
            if lsof -i:$local_port | grep -q LISTEN; then
                echo "Port forwarding for $pod_name on port $local_port:$pod_port is working!"
                return 0
            else
                echo "Port forwarding for $pod_name on port $local_port:$pod_port failed to establish"
                kill $pid 2>/dev/null || true
                attempt=$((attempt+1))
                sleep 2
            fi
        done
        
        echo "Error: Failed to establish port forwarding for $pod_name after $max_attempts attempts"
        return 1
    }
    
    # Start port forwarding for frontend and backend
    echo "Starting port forwarding for frontend..."
    start_port_forward "$FRONTEND_POD" 8000 8000 "/tmp/absence-calculator/frontend.log" "/tmp/absence-calculator/frontend.pid" || {
        echo "Warning: Could not establish frontend port forwarding, trying service instead"
        kubectl port-forward service/frontend 8000:8000 > /tmp/absence-calculator/frontend.log 2>&1 &
        echo $! > /tmp/absence-calculator/frontend.pid
    }
    
    echo "Starting port forwarding for backend..."
    start_port_forward "$BACKEND_POD" 5001 5001 "/tmp/absence-calculator/backend.log" "/tmp/absence-calculator/backend.pid" || {
        echo "Warning: Could not establish backend port forwarding, trying service instead"
        kubectl port-forward service/backend 5001:5001 > /tmp/absence-calculator/backend.log 2>&1 &
        echo $! > /tmp/absence-calculator/backend.pid
    }
    
    # Wait a moment for port forwarding to start
    sleep 5
    
    # Check if processes are running
    FRONTEND_PID=$(cat /tmp/absence-calculator/frontend.pid 2>/dev/null)
    BACKEND_PID=$(cat /tmp/absence-calculator/backend.pid 2>/dev/null)
    
    if ! ps -p $FRONTEND_PID > /dev/null || ! ps -p $BACKEND_PID > /dev/null; then
        echo "Warning: One or more port forwarding processes failed to start"
        echo "Frontend PID: $FRONTEND_PID, Backend PID: $BACKEND_PID"
        echo "Continuing anyway..."
    fi
    
    echo "Port forwarding started"
    echo "Frontend: http://localhost:8000"
    echo "Backend API: http://localhost:5001/api"
    return 0
}

# Function to stop port forwarding
stop_port_forwarding() {
    echo "Stopping port forwarding..."
    
    # Kill frontend port forwarding process if running
    if [ -f /tmp/absence-calculator/frontend.pid ]; then
        PID=$(cat /tmp/absence-calculator/frontend.pid 2>/dev/null)
        if [ ! -z "$PID" ]; then
            kill $PID 2>/dev/null || kill -9 $PID 2>/dev/null
        fi
        rm -f /tmp/absence-calculator/frontend.pid
    fi
    
    # Kill backend port forwarding process if running
    if [ -f /tmp/absence-calculator/backend.pid ]; then
        PID=$(cat /tmp/absence-calculator/backend.pid 2>/dev/null)
        if [ ! -z "$PID" ]; then
            kill $PID 2>/dev/null || kill -9 $PID 2>/dev/null
        fi
        rm -f /tmp/absence-calculator/backend.pid
    fi
    
    # Ensure all kubectl port-forward processes are stopped
    pkill -f "kubectl port-forward" 2>/dev/null || true
    
    # Clean up log files
    rm -f /tmp/absence-calculator/frontend.log /tmp/absence-calculator/backend.log
}

# Function to check application status
check_status() {
    if [ ! -f /tmp/absence-calculator/frontend.pid ] || [ ! -f /tmp/absence-calculator/backend.pid ]; then
        echo "Application is not running"
        return 1
    fi

    if ! kill -0 $(cat /tmp/absence-calculator/frontend.pid) 2>/dev/null || ! kill -0 $(cat /tmp/absence-calculator/backend.pid) 2>/dev/null; then
        echo "Application is not running properly"
        return 1
    fi

    echo "Application is running"
    echo "Frontend: http://localhost:8000"
    echo "Backend API: http://localhost:5001/api"
    return 0
}

# Function to show logs
show_logs() {
    local follow=$1
    
    echo "=== Frontend Logs ==="
    if [ "$follow" = "true" ]; then
        kubectl logs -f -l app=frontend
    else
        kubectl logs -l app=frontend
    fi
    
    echo -e "\n=== Backend Logs ==="
    if [ "$follow" = "true" ]; then
        kubectl logs -f -l app=backend
    else
        kubectl logs -l app=backend
    fi
    
    echo -e "\n=== Port Forwarding Logs ==="
    if [ -f /tmp/absence-calculator/frontend.log ]; then
        echo "Frontend Port Forwarding:"
        cat /tmp/absence-calculator/frontend.log
    fi
    
    if [ -f /tmp/absence-calculator/backend.log ]; then
        echo "Backend Port Forwarding:"
        cat /tmp/absence-calculator/backend.log
    fi
}

# Function to build Docker images
build_images() {
    local rebuild=$1
    
    echo "Building Docker images..."
    
    if [ "$rebuild" = "true" ]; then
        echo "Forcing rebuild of all images..."
        docker build --no-cache -t absence-calculator-backend:latest -f k8s/backend/Dockerfile .
        if [ $? -ne 0 ]; then
            echo "Error: Failed to build backend image"
            return 1
        fi

        docker build --no-cache -t absence-calculator-frontend:latest -f k8s/frontend/Dockerfile .
        if [ $? -ne 0 ]; then
            echo "Error: Failed to build frontend image"
            return 1
        fi
    else
        docker build -t absence-calculator-backend:latest -f k8s/backend/Dockerfile .
        if [ $? -ne 0 ]; then
            echo "Error: Failed to build backend image"
            return 1
        fi

        docker build -t absence-calculator-frontend:latest -f k8s/frontend/Dockerfile .
        if [ $? -ne 0 ]; then
            echo "Error: Failed to build frontend image"
            return 1
        fi
    fi
    
    return 0
}

# Check if kubectl is installed
if ! command_exists kubectl; then
    echo "Error: kubectl is not installed"
    exit 1
fi

# Check if minikube is installed
if ! command_exists minikube; then
    echo "Error: minikube is not installed"
    exit 1
fi

# Function to start the application
start() {
    local rebuild=false
    
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --rebuild)
                rebuild=true
                shift
                ;;
            *)
                echo "Unknown option: $1"
                exit 1
                ;;
        esac
    done

    echo "Starting the application..."

    # Start minikube if not running
    if ! minikube status | grep -q "Running"; then
        echo "Starting minikube..."
        minikube start
    fi
    
    # Ensure PostgreSQL data directory exists
    PG_DATA_DIR="/Users/halilibrahimkuley/ws/absence-calculator/.postgres_data"
    echo "Ensuring PostgreSQL data directory exists: $PG_DATA_DIR"
    mkdir -p "$PG_DATA_DIR"
    chmod -R 777 "$PG_DATA_DIR"

    # Configure Docker daemon
    echo "Configuring Docker daemon..."
    eval $(minikube docker-env)
    
    # Verify Docker daemon is accessible
    if ! check_docker_daemon; then
        echo "Error: Failed to configure Docker daemon"
        exit 1
    fi

    # Build Docker images
    if ! build_images $rebuild; then
        exit 1
    fi

    # Switch back to host Docker daemon
    eval $(minikube docker-env -u)

    # Delete existing deployments if they exist
    echo "Cleaning up existing deployments..."
    kubectl delete -f k8s/backend-deployment.yaml 2>/dev/null
    kubectl delete -f k8s/frontend-deployment.yaml 2>/dev/null
    kubectl delete -f k8s/postgres-deployment.yaml 2>/dev/null
    # No need to delete PersistentVolumeClaim as we're using hostPath

    # Apply Kubernetes configurations
    echo "Applying Kubernetes configurations..."
    kubectl apply -f k8s/postgres-deployment.yaml
    echo "Waiting for PostgreSQL to be ready..."
    sleep 5
    kubectl apply -f k8s/backend-deployment.yaml
    kubectl apply -f k8s/frontend-deployment.yaml
    
    # Wait for pods to be ready with detailed status
    if ! wait_for_pods "postgres"; then
        echo "Error: PostgreSQL pods failed to become ready"
        exit 1
    fi
    
    if ! wait_for_pods "backend"; then
        echo "Error: Backend pods failed to become ready"
        exit 1
    fi

    if ! wait_for_pods "frontend"; then
        echo "Error: Frontend pods failed to become ready"
        exit 1
    fi

    # Start port forwarding
    if ! start_port_forwarding; then
        echo "Error: Failed to start port forwarding"
        exit 1
    fi
    
    # Show PostgreSQL connection information
    echo "PostgreSQL database is available inside the cluster at: postgres:5432"

    echo "Application is running in the background!"
    echo "Frontend: http://localhost:8000"
    echo "Backend API: http://localhost:5001/api"
    echo "Use './k8s/dev.sh status' to check the application status"
    echo "Use './k8s/dev.sh stop' to stop the application"
}

# Function to stop the application
stop() {
    echo "Stopping the application..."
    
    # Stop port forwarding
    stop_port_forwarding
    
    # Delete Kubernetes resources
    kubectl delete -f k8s/frontend-deployment.yaml 2>/dev/null
    kubectl delete -f k8s/backend-deployment.yaml 2>/dev/null
    kubectl delete -f k8s/postgres-deployment.yaml 2>/dev/null

    # Stop minikube
    minikube stop

    echo "Application stopped"
}

# Main script
case "$1" in
    "start")
        shift
        start "$@"
        ;;
    "stop")
        stop
        ;;
    "status")
        check_status
        ;;
    "logs")
        shift
        if [ "$1" = "--follow" ]; then
            show_logs true
        else
            show_logs false
        fi
        ;;
    *)
        echo "Usage: $0 {start [--rebuild]|stop|status|logs [--follow]}"
        exit 1
        ;;
esac 