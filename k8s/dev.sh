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
    echo "Starting port forwarding..."
    
    # Create PID file directory if it doesn't exist
    mkdir -p /tmp/absence-calculator
    
    # Start frontend port forwarding in background
    kubectl port-forward service/frontend 8000:8000 > /tmp/absence-calculator/frontend.log 2>&1 &
    echo $! > /tmp/absence-calculator/frontend.pid
    
    # Start backend port forwarding in background
    kubectl port-forward service/backend 5001:5001 > /tmp/absence-calculator/backend.log 2>&1 &
    echo $! > /tmp/absence-calculator/backend.pid
    
    # Wait a moment for port forwarding to start
    sleep 2
    
    # Check if port forwarding is working
    if ! kill -0 $(cat /tmp/absence-calculator/frontend.pid) 2>/dev/null || ! kill -0 $(cat /tmp/absence-calculator/backend.pid) 2>/dev/null; then
        echo "Error: Failed to start port forwarding"
        stop_port_forwarding
        return 1
    fi
    
    echo "Port forwarding started successfully"
    return 0
}

# Function to stop port forwarding
stop_port_forwarding() {
    echo "Stopping port forwarding..."
    if [ -f /tmp/absence-calculator/frontend.pid ]; then
        kill $(cat /tmp/absence-calculator/frontend.pid) 2>/dev/null
        rm /tmp/absence-calculator/frontend.pid
    fi
    if [ -f /tmp/absence-calculator/backend.pid ]; then
        kill $(cat /tmp/absence-calculator/backend.pid) 2>/dev/null
        rm /tmp/absence-calculator/backend.pid
    fi
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

    # Create data directory in minikube
    echo "Creating data directory in minikube..."
    minikube ssh "sudo mkdir -p /server/data && sudo chmod 777 /server/data"

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

    # Apply Kubernetes configurations
    echo "Applying Kubernetes configurations..."
    kubectl apply -f k8s/backend-deployment.yaml
    kubectl apply -f k8s/frontend-deployment.yaml
    
    # Wait for pods to be ready with detailed status
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
    *)
        echo "Usage: $0 {start [--rebuild]|stop|status}"
        exit 1
        ;;
esac 