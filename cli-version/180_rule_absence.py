from datetime import datetime, timedelta
from typing import List, Tuple, Dict, Any
import csv
import os


def calculate_180_day_rule(absence_periods: List[Tuple[datetime, datetime]], decision_date: datetime = None) -> Dict[str, Any]:
    """
    Calculate if the 180-day rule is satisfied for UK residency applications.
    
    The 180-day rule states that an applicant must not have spent more than 180 days
    outside the UK in any rolling 12-month period during the qualifying period.
    
    This 12-month period is not considered as fixed calendar years, but as periods 
    that slide back from the decision date.
    
    Args:
        absence_periods: List of tuples containing (start_date, end_date) of periods spent outside the UK
        decision_date: The date of decision (defaults to current date if not provided)
    
    Returns:
        Dictionary containing:
            - 'complies': Boolean indicating if the 180-day rule is satisfied
            - 'total_days_absent': Total days spent outside the UK
            - 'worst_period': The 12-month period with the highest number of absence days
            - 'worst_period_days': Number of days absent in the worst period
            - 'detailed_periods': Dictionary with dates as keys and absence days as values
    """
    # If decision date is not provided, use current date
    if decision_date is None:
        decision_date = datetime.now()
    
    # Convert absence periods to a list of individual days
    all_absence_days = []
    for start_date, end_date in absence_periods:
        # Calculate the number of days in this period (excluding start and end dates)
        delta = (end_date - start_date).days - 1
        if delta > 0:  # Only process if there are days between start and end
            for i in range(1, delta + 1):  # Start from 1 to skip start_date, end before end_date
                day = start_date + timedelta(days=i)
                all_absence_days.append(day)
    
    # Sort the absence days
    all_absence_days.sort()
    
    # If no absences, return early
    if not all_absence_days:
        return {
            'complies': True,
            'total_days_absent': 0,
            'worst_period': None,
            'worst_period_days': 0,
            'detailed_periods': {}
        }
    
    # Calculate the start date of the 5-year qualifying period
    qualifying_start = decision_date - timedelta(days=5*365)
    
    # Filter out absence days before the qualifying period
    relevant_absence_days = [day for day in all_absence_days if day >= qualifying_start]
    
    # Initialize variables to track the worst 12-month period
    worst_period_start = None
    worst_period_end = None
    worst_period_days = 0
    detailed_periods = {}
    
    # Check each possible 12-month period by sliding back from the decision date
    for check_day in range((decision_date - qualifying_start).days + 1):
        # Define the current 12-month period we're checking
        period_end = decision_date - timedelta(days=check_day)
        period_start = period_end - timedelta(days=365)
        
        # Count days absent in this period
        days_absent_in_period = sum(1 for day in relevant_absence_days 
                                  if period_start <= day <= period_end)
        
        # Store the result for this period
        period_key = period_start.strftime('%Y-%m-%d') + ' to ' + period_end.strftime('%Y-%m-%d')
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
        'complies': complies,
        'total_days_absent': len(relevant_absence_days),
        'worst_period': worst_period,
        'worst_period_days': worst_period_days,
        'detailed_periods': detailed_periods
    }


def parse_date(date_str: str) -> datetime:
    """
    Parse a date string in the format 'YYYY-MM-DD' into a datetime object.
    
    Args:
        date_str: Date string in the format 'YYYY-MM-DD'
    
    Returns:
        datetime object
    """
    return datetime.strptime(date_str, '%Y-%m-%d')


def read_absence_periods_from_csv(csv_file_path: str) -> List[Tuple[datetime, datetime]]:
    """
    Read absence periods from a CSV file.
    
    The CSV file should have at least two columns:
    - start_date: Date when the person left the UK (not counted as absence)
    - end_date: Date when the person returned to the UK (not counted as absence)
    
    Args:
        csv_file_path: Path to the CSV file
        
    Returns:
        List of tuples containing (start_date, end_date) of periods spent outside the UK
    """
    if not os.path.exists(csv_file_path):
        raise FileNotFoundError(f"CSV file not found: {csv_file_path}")
        
    absence_periods = []
    
    with open(csv_file_path, 'r') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        
        # Check if required columns exist
        required_columns = ['start_date', 'end_date']
        if not all(column in csv_reader.fieldnames for column in required_columns):
            raise ValueError(f"CSV file must contain columns: {', '.join(required_columns)}")
        
        for row in csv_reader:
            try:
                start_date = parse_date(row['start_date'])
                end_date = parse_date(row['end_date'])
                
                # Validate dates (end date should be after start date)
                if end_date < start_date:
                    print(f"Warning: Skipping invalid date range: {row['start_date']} to {row['end_date']}")
                    continue
                    
                absence_periods.append((start_date, end_date))
            except ValueError as e:
                print(f"Warning: Skipping row due to date parsing error: {e}")
                continue
    
    return absence_periods


def example_usage():
    """
    Example of how to use the calculate_180_day_rule function.
    """
    # Check if the CSV file exists, otherwise use default example data
    csv_file_path = 'absence_periods.csv'
    
    try:
        # Try to read absence periods from CSV file
        absence_periods = read_absence_periods_from_csv(csv_file_path)
        print(f"Successfully read {len(absence_periods)} absence periods from {csv_file_path}")
    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}")
        print("Using default example data instead.")
        # Default example data
        absence_periods = [
            (parse_date('2023-01-10'), parse_date('2023-02-15')),  # 37 days
        ]
    
    # Set decision date
    decision_date = parse_date('2025-10-15')
    
    # Calculate the 180-day rule
    result = calculate_180_day_rule(absence_periods, decision_date)
    
    # Calculate the start date of the 5-year qualifying period
    qualifying_start = decision_date - timedelta(days=5*365)
    
    # Print the results
    print(f"Decision Date: {decision_date.strftime('%Y-%m-%d')}")
    print(f"Qualifying Period Start: {qualifying_start.strftime('%Y-%m-%d')}")
    print(f"Complies with 180-day rule: {result['complies']}")
    print(f"Total days absent in the qualifying period: {result['total_days_absent']}")
    print(f"Worst 12-month period: {result['worst_period']}")
    print(f"Days absent in worst period: {result['worst_period_days']}")
    print("\nDetailed breakdown of rolling 12-month periods:")
    
    # Sort the detailed periods by date for better readability
    sorted_periods = sorted(result['detailed_periods'].items(), 
                           key=lambda x: parse_date(x[0].split(' to ')[0]))
    
    # Filter periods to only show those within the 5-year qualifying period
    relevant_periods = []
    for period, days in sorted_periods:
        period_start = parse_date(period.split(' to ')[0])
        if period_start >= qualifying_start:
            relevant_periods.append((period, days))
    
    # Display only the relevant periods
    for period, days in relevant_periods:
        status = "✓" if days <= 180 else "✗"
        print(f"{period}: {days} days absent {status}")


def create_sample_csv():
    """
    Create a sample CSV file with absence periods data.
    """
    csv_file_path = 'absence_periods.csv'
    
    # Check if file already exists
    if os.path.exists(csv_file_path):
        print(f"Sample CSV file already exists: {csv_file_path}")
        return csv_file_path
    
    # Sample data
    sample_data = [
        {'start_date': '2023-01-10', 'end_date': '2023-02-15'},
        {'start_date': '2023-05-01', 'end_date': '2023-05-15'},
        {'start_date': '2023-08-20', 'end_date': '2023-09-10'},
        {'start_date': '2023-12-20', 'end_date': '2024-01-10'},
        {'start_date': '2024-03-01', 'end_date': '2024-03-31'},
        {'start_date': '2024-06-15', 'end_date': '2024-07-15'},
        {'start_date': '2024-11-01', 'end_date': '2024-12-31'},
    ]
    
    # Write to CSV
    with open(csv_file_path, 'w', newline='') as csv_file:
        fieldnames = ['start_date', 'end_date']
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        
        writer.writeheader()
        for row in sample_data:
            writer.writerow(row)
    
    print(f"Created sample CSV file: {csv_file_path}")
    return csv_file_path


def restore_sample_data():
    """
    Restore the sample CSV file with all example data.
    This is a utility function that can be called manually if needed.
    """
    # First check if the file exists
    csv_file_path = 'absence_periods.csv'
    if os.path.exists(csv_file_path):
        # Rename the existing file as backup
        backup_path = f"{csv_file_path}.bak"
        os.rename(csv_file_path, backup_path)
        print(f"Backed up existing file to {backup_path}")
    
    # Create a new sample file
    create_sample_csv()
    print("Sample data has been restored.")


if __name__ == "__main__":
    # Only create a sample CSV file if it doesn't exist
    if not os.path.exists('absence_periods.csv'):
        create_sample_csv()
    # Run the example
    example_usage()
