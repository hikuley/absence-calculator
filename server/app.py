from flask import Flask, jsonify, request
from flask_cors import CORS
import csv
import os
import uuid
from datetime import datetime, timedelta

app = Flask(__name__)

# Configure CORS to allow requests from any origin
cors = CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

# Add CORS headers to all responses
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

# Handle OPTIONS requests explicitly
@app.route('/api/calculate', methods=['OPTIONS'])
def options_calculate():
    response = app.make_default_options_response()
    return response

@app.route('/api/absence-periods', methods=['OPTIONS'])
def options_absence_periods():
    response = app.make_default_options_response()
    return response

@app.route('/api/absence-periods/<string:period_id>', methods=['OPTIONS'])
def options_absence_period(period_id):
    response = app.make_default_options_response()
    return response

# Define the path to the CSV file
CSV_FILE_PATH = os.environ.get('CSV_FILE_PATH', 'absence_periods.csv')

# Ensure the directory for the CSV file exists
csv_dir = os.path.dirname(CSV_FILE_PATH)
if csv_dir and not os.path.exists(csv_dir):
    print(f"Creating directory: {csv_dir}")
    os.makedirs(csv_dir, exist_ok=True)

# Ensure the CSV file exists
if not os.path.exists(CSV_FILE_PATH):
    print(f"CSV file not found at {CSV_FILE_PATH}, creating a new one")
    with open(CSV_FILE_PATH, 'w', newline='') as csvfile:
        fieldnames = ['id', 'start_date', 'end_date']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

# Function to calculate the 180-day rule
def calculate_180_day_rule(absence_periods, decision_date):
    """
    Calculate if the 180-day rule is satisfied based on absence periods.
    
    Args:
        absence_periods: List of tuples (start_date, end_date) representing periods of absence
        decision_date: The date of the decision
        
    Returns:
        Dictionary with calculation results
    """
    # Calculate the start date of the 5-year qualifying period
    qualifying_start = decision_date - timedelta(days=5*365)
    
    # Convert absence periods to a list of individual days
    all_absence_days = []
    for start_date, end_date in absence_periods:
        # Calculate the number of days in this period (excluding start and end dates)
        delta = (end_date - start_date).days - 1
        
        if delta > 0:
            for i in range(1, delta + 1):
                day = start_date + timedelta(days=i)
                all_absence_days.append(day)
    
    # Sort the absence days
    all_absence_days.sort()
    
    # If no absences, return early
    if len(all_absence_days) == 0:
        return {
            "complies": True,
            "total_days_absent": 0,
            "worst_period": None,
            "worst_period_days": 0,
            "detailed_periods": {}
        }
    
    # Filter out absence days before the qualifying period
    relevant_absence_days = [day for day in all_absence_days if day >= qualifying_start]
    
    # Initialize variables to track the worst 12-month period
    worst_period_start = None
    worst_period_end = None
    worst_period_days = 0
    detailed_periods = {}
    
    # Check each possible 12-month period by sliding back from the decision date
    total_days = (decision_date - qualifying_start).days + 1
    
    for check_day in range(total_days):
        # Define the current 12-month period we're checking
        period_end = decision_date - timedelta(days=check_day)
        period_start = period_end - timedelta(days=365) + timedelta(days=1)
        
        # Count days absent in this period
        days_absent_in_period = sum(1 for day in relevant_absence_days 
                                  if period_start <= day <= period_end)
        
        # Store the result for this period
        period_key = f"{period_start.strftime('%Y-%m-%d')} to {period_end.strftime('%Y-%m-%d')}"
        detailed_periods[period_key] = days_absent_in_period
        
        # Update the worst period if this one has more absence days
        if days_absent_in_period > worst_period_days:
            worst_period_days = days_absent_in_period
            worst_period_start = period_start
            worst_period_end = period_end
    
    # Determine if the application complies with the 180-day rule
    complies = worst_period_days <= 180
    
    # Format the worst period for the result
    worst_period = None
    if worst_period_start and worst_period_end:
        worst_period = f"{worst_period_start.strftime('%Y-%m-%d')} to {worst_period_end.strftime('%Y-%m-%d')}"
    
    return {
        "complies": complies,
        "total_days_absent": len(relevant_absence_days),
        "worst_period": worst_period,
        "worst_period_days": worst_period_days,
        "detailed_periods": detailed_periods
    }

def read_absence_periods():
    absence_periods = []
    try:
        with open(CSV_FILE_PATH, 'r', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                absence_periods.append(row)
    except Exception as e:
        print(f"Error reading CSV file: {e}")
    return absence_periods

def write_absence_periods(absence_periods):
    try:
        with open(CSV_FILE_PATH, 'w', newline='') as csvfile:
            fieldnames = ['id', 'start_date', 'end_date']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for period in absence_periods:
                writer.writerow(period)
        return True
    except Exception as e:
        print(f"Error writing to CSV file: {e}")
        return False

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"}), 200

@app.route('/api/absence-periods', methods=['GET'])
def get_absence_periods():
    absence_periods = read_absence_periods()
    return jsonify(absence_periods)

@app.route('/api/absence-periods', methods=['POST'])
def create_absence_period():
    data = request.json
    
    # Validate input
    if not data or 'start_date' not in data or 'end_date' not in data:
        return jsonify({"error": "Start date and end date are required"}), 400
    
    # Parse dates
    try:
        start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
        end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
    except ValueError:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400
    
    # Validate dates
    if end_date < start_date:
        return jsonify({"error": "End date must be after start date"}), 400
    
    # Get existing periods
    absence_periods = read_absence_periods()
    
    # Create new period with unique ID
    new_period = {
        "id": str(uuid.uuid4()),
        "start_date": data['start_date'],
        "end_date": data['end_date']
    }
    
    # Add to periods and write to CSV
    absence_periods.append(new_period)
    write_absence_periods(absence_periods)
    
    return jsonify(new_period), 201

@app.route('/api/absence-periods/<string:period_id>', methods=['PUT'])
def update_absence_period(period_id):
    data = request.json
    
    # Validate input
    if not data or 'start_date' not in data or 'end_date' not in data:
        return jsonify({"error": "Start date and end date are required"}), 400
    
    # Parse dates
    try:
        start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
        end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
    except ValueError:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400
    
    # Validate dates
    if end_date < start_date:
        return jsonify({"error": "End date must be after start date"}), 400
    
    # Get existing periods
    absence_periods = read_absence_periods()
    
    # Find and update the period
    for i, period in enumerate(absence_periods):
        if period["id"] == period_id:
            absence_periods[i]["start_date"] = data['start_date']
            absence_periods[i]["end_date"] = data['end_date']
            # Write updated periods to CSV
            write_absence_periods(absence_periods)
            return jsonify(absence_periods[i])
    
    return jsonify({"error": "Absence period not found"}), 404

@app.route('/api/absence-periods/<string:period_id>', methods=['DELETE'])
def delete_absence_period(period_id):
    # Get existing periods
    absence_periods = read_absence_periods()
    
    # Find and remove the period
    for i, period in enumerate(absence_periods):
        if period["id"] == period_id:
            absence_periods.pop(i)
            # Write updated periods to CSV
            write_absence_periods(absence_periods)
            return jsonify({"message": "Absence period deleted successfully"})
    
    return jsonify({"error": "Absence period not found"}), 404

@app.route('/api/calculate', methods=['POST'])
def calculate_rule():
    try:
        data = request.json
        
        # Validate input
        if not data or 'decision_date' not in data:
            return jsonify({"error": "Decision date is required"}), 400
        
        # Get absence periods from CSV if not provided
        periods = data.get('absence_periods', read_absence_periods())
        
        # Convert to the format expected by the calculate_180_day_rule function
        absence_periods_list = []
        for p in periods:
            start_date = p["start_date"]
            end_date = p["end_date"]
            
            # Convert string dates to datetime
            if isinstance(start_date, str):
                start_date = datetime.strptime(start_date, '%Y-%m-%d')
            if isinstance(end_date, str):
                end_date = datetime.strptime(end_date, '%Y-%m-%d')
                
            absence_periods_list.append((start_date, end_date))
        
        # Convert decision date to datetime
        decision_date_dt = data['decision_date']
        if isinstance(decision_date_dt, str):
            decision_date_dt = datetime.strptime(decision_date_dt, '%Y-%m-%d')
        
        # Calculate the 180-day rule
        result = calculate_180_day_rule(absence_periods_list, decision_date_dt)
        
        # Add the qualifying start date to the result
        qualifying_start = decision_date_dt - timedelta(days=5*365)
        result["qualifying_start"] = qualifying_start.strftime('%Y-%m-%d')
        result["decision_date"] = decision_date_dt.strftime('%Y-%m-%d')
        
        return jsonify(result)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5001, debug=True)
