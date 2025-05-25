# Absence Calculator

A comprehensive application for calculating compliance with the UK's 180-day residency rule, with multiple deployment options and PostgreSQL database integration.

## Overview

This application helps users track their absence periods from the UK and calculate whether they comply with the 180-day rule for residency applications. The rule states that applicants must not have spent more than 180 days outside the UK in any 12-month period during the 5-year qualifying period.

The application now features a robust PostgreSQL database backend for reliable data persistence, replacing the previous CSV-based storage system while maintaining backward compatibility.

## Features

### Core Functionality
- Add, update, and remove absence periods with start and end dates
- Calculate compliance with the 180-day rule based on a decision date
- View detailed results including:
  - Total days absent in the qualifying period
  - Worst 12-month period with the highest number of absence days
  - Detailed breakdown of all rolling 12-month periods
- Modal view for displaying all 12-month periods
- Visual chart displaying absence days over a 5-year period

### Database Integration
- PostgreSQL database storage for reliable data persistence

- Tortoise ORM for async database interactions
- Automatic schema generation and management
- Backward compatibility with CSV data format

### Deployment Options
- Standard development setup with PostgreSQL integration
- Docker containerized deployment with multi-container orchestration
- Kubernetes deployment for production environments
- Comprehensive deployment scripts for each environment

### DevOps Features
- Automated database backup and restore functionality
- Health check endpoints for monitoring
- Container health probes for reliability
- Persistent volume storage for data durability
- Logging and monitoring capabilities

## Deployment Options

### 1. Standard Development Setup

For local development with Python, PostgreSQL, and a simple HTTP server.

#### Prerequisites

- Python 3.9+
- Docker (for PostgreSQL container)
- Web browser

#### Features

- Automatic virtual environment setup and dependency installation
- PostgreSQL container management (start, stop, status)
- Automatic data migration from CSV to PostgreSQL
- Integrated logging for all components

#### Usage

```bash
# Start PostgreSQL, backend, and frontend servers
./dev.sh start

# Stop all running servers
./dev.sh stop

# Restart all servers
./dev.sh restart

# View logs from all components
./dev.sh logs

# Run database migration manually
./dev.sh migrate

# Check PostgreSQL status
./dev.sh pg-status
```

The script automatically:
- Starts a PostgreSQL container for data storage
- Creates and initializes database tables
- Starts the backend FastAPI server on port 5001
- Starts a frontend HTTP server on port 8000
- Opens your default browser to http://localhost:8000

### 2. Docker Deployment

For containerized deployment using Docker and Docker Compose. This setup includes PostgreSQL database for data persistence.

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

# Clean images and rebuild from scratch
./docker/docker-dev.sh redeploy
```

The Docker setup includes:
- PostgreSQL database container for data persistence
- Backend FastAPI service connected to PostgreSQL
- Frontend Nginx server

Access the application at:
- Frontend: http://localhost:8000
- Backend API: http://localhost:5001/api

The first time the application starts, it will automatically:
1. Create the necessary database tables


### 3. Kubernetes Deployment

For production-ready deployment using Kubernetes. This setup includes PostgreSQL with persistent volume for data storage.

```bash
# Normal start (uses cached images if available)
./k8s/dev.sh start

# Force rebuild of Docker images from scratch
./k8s/dev.sh start --rebuild

# Check application status
./k8s/dev.sh status

# View application logs
./k8s/dev.sh logs

# Follow logs in real-time
./k8s/dev.sh logs --follow

# Stop the application
./k8s/dev.sh stop
```

Access the application at:
- Frontend: http://localhost:8080
- Backend API: http://localhost:5001/api

## Project Structure

```
.
├── absence_periods.csv       # CSV database for absence periods (legacy format)
├── dev.sh                    # Development script for standard setup with PostgreSQL
├── docker/                   # Docker deployment files
│   ├── backend/              # Backend Dockerfile and config
│   │   └── Dockerfile        # Backend Docker configuration with PostgreSQL support
│   ├── frontend/             # Frontend Dockerfile and Nginx config
│   ├── docker-compose.yml    # Docker Compose configuration with PostgreSQL service
│   ├── docker-dev.sh         # Docker management script
│   └── README.md             # Docker-specific documentation
├── frontend/                 # Frontend static files
│   ├── index.html            # Main HTML file
│   ├── css/                  # CSS stylesheets
│   └── js/                   # JavaScript files
├── k8s/                      # Kubernetes deployment files
│   ├── backend/              # Backend K8s Dockerfile
│   ├── frontend/             # Frontend K8s Dockerfile
│   ├── backend-deployment.yaml  # Backend K8s deployment
│   ├── frontend-deployment.yaml # Frontend K8s deployment
│   ├── postgres-deployment.yaml # PostgreSQL K8s deployment
│   ├── configmap.yaml        # Environment variables
│   ├── pvc.yaml              # Persistent volume claim for PostgreSQL
│   ├── dev.sh                # K8s deployment script
│   ├── db-tools.sh           # Database management tools for K8s
│   └── README.md             # K8s-specific documentation
├── server/                   # Backend server files
│   ├── app.py                # FastAPI application
│   ├── database.py           # Database connection and configuration
│   ├── models.py             # Tortoise ORM models for database tables
│   ├── data/                 # Data directory
│   ├── migrations.py         # Database initialization and demo data creation
│   └── requirements.txt      # Python dependencies including PostgreSQL
└── .postgres_data/          # Local PostgreSQL data directory (created by dev.sh)
```

## Standard Setup Instructions

### Prerequisites

- Python 3.9 or higher
- Docker (for PostgreSQL container)
- Web browser (Chrome, Firefox, Safari, etc.)

### Step 1: Clone the Repository

```bash
git clone <repository-url>
cd absence-calculator
```

### Step 2: Start the Application

The enhanced development script handles everything automatically:

```bash
./dev.sh start
```

This will:
1. Set up a Python virtual environment if needed
2. Install all required dependencies including PostgreSQL packages
3. Start a PostgreSQL container
4. Create and initialize database tables
5. Start the backend server
6. Start the frontend server
7. Open your browser to http://localhost:8000

### Step 3: Using the Application

1. Add absence periods using the form
2. Set a decision date
3. Calculate compliance with the 180-day rule
4. View detailed results and visualizations

### Step 4: Stopping the Application

```bash
./dev.sh stop
```

This will stop all components including the PostgreSQL container.

### Advanced Usage

#### Database Migration





#### Viewing Logs

To view logs from all components:

```bash
./dev.sh logs
```

#### Checking PostgreSQL Status

```bash
./dev.sh pg-status
```

## Docker Deployment Instructions

### Prerequisites

- Docker installed on your system
- Docker Compose installed on your system

### Deployment Steps

1. Use the provided script:
   ```bash
   ./docker/docker-dev.sh deploy
   ```

2. Access the application at http://localhost:8000

### Data Persistence

The application now uses PostgreSQL for data persistence with the following features:

- PostgreSQL database for reliable data storage
- Automatic data migration from CSV to PostgreSQL
- Persistent volume storage in Docker and Kubernetes
- Backward compatibility with CSV data format
- Database backup and restore capabilities

In the Docker setup, PostgreSQL data is stored in a named volume. In Kubernetes, a PersistentVolumeClaim is used for data storage. In the standard setup, data is stored in a local directory managed by the Docker container.

## Kubernetes Deployment Instructions

### Prerequisites

- Docker
- Minikube or another Kubernetes cluster
- kubectl
- Bash shell

### Deployment Steps

1. Start the application:
   ```bash
   ./k8s/dev.sh start
   ```

2. Check the deployment status:
   ```bash
   ./k8s/dev.sh status
   ```

3. Access the application at:
   - Frontend: http://localhost:8080
   - Backend API: http://localhost:5001/api

### Kubernetes Features

- PostgreSQL deployment with persistent storage
- Database migration and initialization on startup
- Dedicated namespace for isolation
- Health check probes (readiness, liveness, startup)
- Persistent volume claims for data storage
- ConfigMap for environment variables
- Horizontal Pod Autoscalers for scalability
- Monitoring script for deployment status
- Database management tools (backup, restore, migrate, shell)
- Improved port forwarding mechanism

## Using the Application

### Adding Absence Periods

1. In the left panel, enter a start date (when you left the UK)
2. Enter an end date (when you returned to the UK)
3. Click the "Add Period" button
4. The period will be added to the list below and saved to the PostgreSQL database
5. Changes are persisted even if the application is restarted

### Setting the Decision Date

1. In the left panel, under "Decision Date", select your application decision date
2. The default is set to the current date

### Calculating Compliance

1. After adding periods and setting the decision date, click the "Calculate" button
2. The results will be displayed in the right panel, showing:
   - Whether you comply with the 180-day rule
   - The qualifying period start date
   - Total days absent
   - The worst 12-month period and its absence days
   - A table of the first 10 rolling 12-month periods

### Viewing All Periods

1. If you have more than 10 rolling 12-month periods, a "Show All Periods" button will appear
2. Click this button to open a modal window showing all periods

### Deleting Absence Periods

1. In the absence periods list, click the "Delete" button next to the period you want to remove
2. The period will be removed from both the UI and the PostgreSQL database
3. Changes are immediately persisted to ensure data consistency

## API Endpoints

The backend provides the following RESTful API endpoints:

- `GET /api/absence-periods`: Get all absence periods
- `POST /api/absence-periods`: Add a new absence period
- `DELETE /api/absence-periods/<id>`: Delete an absence period
- `POST /api/calculate`: Calculate the 180-day rule compliance

## Calculation Logic

The application implements the following logic for the 180-day rule calculation:
1. Calculates the 5-year qualifying period before the decision date
2. Excludes both start and end dates from absence calculations (only days between are counted)
3. Identifies the worst 12-month period with the highest number of absence days
4. Determines compliance based on whether you've spent more than 180 days outside the UK in any 12-month period

## Troubleshooting

### Standard Setup Issues

If you see an error like "Address already in use" when starting the Flask server:

1. Find the process using the port:
   ```bash
   lsof -i :5001
   ```

2. Kill the process:
   ```bash
   kill -9 <PID>
   ```

### Docker Issues

1. Check if the ports 8000 and 5001 are available on your system
2. Ensure the required files exist in the correct locations
3. Check the container logs:
   ```bash
   ./docker/docker-dev.sh logs
   ```

### Kubernetes Issues

1. Check pod status:
   ```bash
   kubectl get pods
   ```

2. View detailed pod information:
   ```bash
   kubectl describe pod <pod-name>
   ```

3. Check application logs:
   ```bash
   ./k8s/dev.sh logs
   ```

4. For port forwarding issues, verify if ports 8080 and 5001 are available

### CORS Issues

If you encounter CORS errors in the browser console, ensure that:

1. The Flask server is running with CORS enabled (already configured in app.py)
2. You're accessing the frontend via an HTTP server, not directly opening the HTML file

### Data Not Showing Up

If your absence periods aren't appearing:


1. Verify that the FastAPI server is running and accessible
2. Check the database connection settings
