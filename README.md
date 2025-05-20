# 180-Day Rule Calculator

A Python-based web application for calculating compliance with the UK's 180-day residency rule.

## Quick Development Setup

This project includes a convenient development script (`dev.sh`) that simplifies running the application:

```bash
# Start both frontend and backend servers
./dev.sh start

# Stop all running servers
./dev.sh stop

# Restart the servers (stop and then start)
./dev.sh restart
```

The script automatically:
- Starts the backend Flask server on port 5001
- Starts a frontend HTTP server on port 8000
- Opens your default browser to http://localhost:8000
- Provides proper error handling and process management

## Overview

This application helps users track their absence periods from the UK and calculate whether they comply with the 180-day rule for residency applications. The rule states that applicants must not have spent more than 180 days outside the UK in any 12-month period during the 5-year qualifying period.

## Features

- Add and remove absence periods with start and end dates
- Calculate compliance with the 180-day rule based on a decision date
- View detailed results including:
  - Total days absent in the qualifying period
  - Worst 12-month period with the highest number of absence days
  - Detailed breakdown of all rolling 12-month periods
- CSV file storage for persistence of absence periods
- Modal view for displaying all 12-month periods
- Visual chart displaying absence days over a 5-year period
- Update functionality for existing absence periods

## Project Structure


- `server/app.py`: Flask backend server with the 180-day rule calculation logic
- `server/update_csv.py`: Utility script to update the CSV file with data from the original source
- `server/requirements.txt`: Python dependencies
- `index.html`: Standalone HTML/JavaScript frontend for the application
- `absence_periods.csv`: CSV file used as a database to store absence periods

## Quick Start Guide

### Prerequisites

- Python 3.6 or higher
- Web browser (Chrome, Firefox, Safari, etc.)

### Step 1: Set Up the Python Environment

1. Clone or download this repository to your local machine

2. Open a terminal and navigate to the project directory

3. Create a virtual environment:
   ```bash
   python3 -m venv venv
   ```

4. Activate the virtual environment:
   - On macOS/Linux:
     ```bash
     source venv/bin/activate
     ```
   - On Windows:
     ```bash
     venv\Scripts\activate
     ```

5. Install the required dependencies:
   ```bash
   cd server
   pip install -r requirements.txt
   ```

### Step 2: Start the Backend Server

1. From the project root directory, with the virtual environment activated, run:
   ```bash
   cd server
   python app.py
   ```

2. You should see output indicating that the Flask server is running on http://localhost:5001

### Step 3: Start the Frontend Server

1. Open a new terminal window and navigate to the project directory

2. Start a simple HTTP server to serve the HTML file:
   ```bash
   python3 -m http.server 8000
   ```

3. You should see output indicating that the server is running on port 8000

### Step 4: Access the Application

1. Open your web browser and navigate to:
   ```
   http://localhost:8000
   ```

2. The 180-Day Rule Calculator interface should load, showing any existing absence periods and calculation results

## Using the Application

### Adding Absence Periods

1. In the left panel, enter a start date (when you left the UK)
2. Enter an end date (when you returned to the UK)
3. Click the "Add Period" button
4. The period will be added to the list below and saved to the CSV file

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
2. The period will be removed from both the UI and the CSV file

## API Endpoints

The backend provides the following RESTful API endpoints:

- `GET /api/absence-periods`: Get all absence periods
- `POST /api/absence-periods`: Add a new absence period
- `DELETE /api/absence-periods/<id>`: Delete an absence period
- `POST /api/calculate`: Calculate the 180-day rule compliance

## Data Storage

The application uses a CSV file (`absence_periods.csv`) to store absence periods with the following structure:
- `id`: Unique identifier for each absence period
- `start_date`: The date when the person left the UK (not counted as absence)
- `end_date`: The date when the person returned to the UK (not counted as absence)

## Calculation Logic

The application implements the following logic for the 180-day rule calculation:
1. Calculates the 5-year qualifying period before the decision date
2. Excludes both start and end dates from absence calculations (only days between are counted)
3. Identifies the worst 12-month period with the highest number of absence days
4. Determines compliance based on whether you've spent more than 180 days outside the UK in any 12-month period

## Updating the CSV Data

If you want to import data from another CSV file, you can use the `update_csv.py` script:

```bash
cd server
python update_csv.py
```

This script will copy data from `home_task/absence_periods.csv` to the root `absence_periods.csv` file, adding random UUIDs for each entry.

## Troubleshooting

### Server Port Already in Use

If you see an error like "Address already in use" when starting the Flask server:

1. Find the process using the port:
   ```bash
   lsof -i :5001
   ```

2. Kill the process:
   ```bash
   kill -9 <PID>
   ```

3. Try starting the server again

### CORS Issues

If you encounter CORS errors in the browser console, ensure that:

1. The Flask server is running with CORS enabled (already configured in app.py)
2. You're accessing the frontend via an HTTP server, not directly opening the HTML file

### Data Not Showing Up

If your absence periods aren't appearing:

1. Check that the `absence_periods.csv` file exists in the project root
2. Ensure it has the correct format with `id`, `start_date`, and `end_date` columns
3. Verify that the Flask server is running and accessible
