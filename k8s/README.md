# Kubernetes Deployment Guide

This guide explains how to deploy the Absence Calculator application using Kubernetes locally with Minikube.

## Prerequisites

- Docker
- Minikube
- kubectl
- Bash shell

## Quick Start

1. Start the application:
```bash
# Normal start (uses cached images if available)
./k8s/dev.sh start

# Force rebuild of Docker images from scratch
./k8s/dev.sh start --rebuild
```

2. Check application status:
```bash
./k8s/dev.sh status
```

3. View application logs:
```bash
# Show current logs
./k8s/dev.sh logs

# Follow logs in real-time
./k8s/dev.sh logs --follow
```

4. Stop the application:
```bash
./k8s/dev.sh stop
```

## Accessing the Application

Once the application is running, you can access it at:
- Frontend: http://localhost:8000
- Backend API: http://localhost:5001/api

## Deployment Process

The `dev.sh` script handles the entire deployment process:

1. **Environment Setup**:
   - Starts Minikube if not running
   - Creates necessary data directories
   - Configures Docker daemon for Minikube

2. **Image Building**:
   - Builds backend image using `k8s/backend/Dockerfile`
   - Builds frontend image using `k8s/frontend/Dockerfile`
   - Uses Minikube's Docker daemon for building
   - Supports `--rebuild` flag to force rebuild from scratch

3. **Kubernetes Deployment**:
   - Deploys backend service and deployment
   - Deploys frontend service and deployment
   - Waits for pods to be ready with detailed status

4. **Port Forwarding**:
   - Sets up port forwarding for both services
   - Runs in the background for persistent access
   - Logs are stored in `/tmp/absence-calculator/`

## Troubleshooting

### Check Application Status
```bash
./k8s/dev.sh status
```
This will show if the application is running and provide access URLs.

### View Application Logs
```bash
# Show current logs
./k8s/dev.sh logs

# Follow logs in real-time
./k8s/dev.sh logs --follow
```
This will show:
- Frontend application logs
- Backend application logs
- Port forwarding logs

### Check Pod Status
```bash
kubectl get pods
```

### Check Services
```bash
kubectl get services
```

### Common Issues

1. **Port Forwarding Issues**:
   - Check if ports 8000 and 5001 are available
   - Verify port forwarding status in `/tmp/absence-calculator/`
   - Restart the application if needed

2. **Pod Issues**:
   - Check pod status with `kubectl get pods`
   - View detailed pod information with `kubectl describe pod <pod-name>`
   - Check pod logs for specific errors

3. **Image Pull Issues**:
   - Ensure Minikube is running
   - Verify Docker daemon configuration
   - Check image build logs
   - Try rebuilding images with `./k8s/dev.sh start --rebuild`

## Cleanup

To completely stop and clean up the application:
```bash
./k8s/dev.sh stop
```

This will:
- Stop all port forwarding
- Delete Kubernetes resources
- Stop Minikube
- Clean up PID files and logs

## Development Notes

- The application runs in the background after starting
- Port forwarding processes are managed automatically
- Status can be checked at any time using the status command
- All logs are stored in `/tmp/absence-calculator/` for debugging
- Use `--rebuild` flag when you need to rebuild Docker images from scratch
- Use `logs` command to view application and port forwarding logs 