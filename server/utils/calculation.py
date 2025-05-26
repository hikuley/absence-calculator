from datetime import datetime, timedelta
from typing import List, Tuple, Dict, Any

def calculate_180_day_rule(absence_periods: List[Tuple[datetime, datetime]], decision_date: datetime) -> Dict[str, Any]:
    """
    Calculate if the 180-day rule is satisfied for UK residency applications.
    
    The 180-day rule states that an applicant must not have spent more than 180 days
    outside the UK in any rolling 12-month period during the qualifying period.
    
    This 12-month period is not considered as fixed calendar years, but as periods 
    that slide back from the decision date.
    
    Args:
        absence_periods: List of tuples containing (start_date, end_date) of periods spent outside the UK
        decision_date: The date of decision
    
    Returns:
        Dictionary containing:
            - 'complies': Boolean indicating if the 180-day rule is satisfied
            - 'total_days_absent': Total days spent outside the UK
            - 'worst_period': The 12-month period with the highest number of absence days
            - 'worst_period_days': Number of days absent in the worst period
            - 'detailed_periods': Dictionary with dates as keys and absence days as values
    """
    # Calculate the start date of the 5-year qualifying period
    qualifying_start = decision_date - timedelta(days=5*365)
    # Convert absence periods to a list of individual days
    all_absence_days = []
    for start_date, end_date in absence_periods:
        # Skip periods outside the qualifying period
        if end_date < qualifying_start:
            continue
            
        # Adjust start date if before qualifying period
        if start_date < qualifying_start:
            start_date = qualifying_start
            
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
        period_key = f"{period_start.strftime('%Y-%m-%d')} to {period_end.strftime('%Y-%m-%d')}"
        detailed_periods[period_key] = days_absent_in_period
        
        # Update the worst period if this one has more absence days
        if days_absent_in_period > worst_period_days:
            worst_period_days = days_absent_in_period
            worst_period_start = period_start
            worst_period_end = period_end
    
    # Determine if the application complies with the 180-day rule
    # The rule states: must not have spent more than 180 days outside the UK 
    # in any rolling 12-month period during the 5-year qualifying period
    complies = worst_period_days <= 180
    
    # Format the worst period for the result
    worst_period = None
    if worst_period_start and worst_period_end:
        worst_period = f"{worst_period_start.strftime('%Y-%m-%d')} to {worst_period_end.strftime('%Y-%m-%d')}"
    
    # The frontend expects detailed_periods as an object with period strings as keys and day counts as values
    # We'll keep it as is, since the frontend's getDetailedPeriods function will convert it to the needed format
    
    # Return the results in the format expected by the frontend
    return {
        "decision_date": decision_date.strftime("%Y-%m-%d"),
        "qualifying_start": qualifying_start.strftime("%Y-%m-%d"),
        "total_days_absent": len(relevant_absence_days),
        "worst_period": worst_period,
        "worst_period_days": worst_period_days,
        "complies": complies,
        "detailed_periods": detailed_periods
    }
