from fastapi import FastAPI, HTTPException, Response, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, field_validator
from typing import List, Optional, Dict, Any, Tuple, Union
from typing_extensions import Annotated
import os
import uuid
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

# Import database and models
from database import get_db, engine, Base
from models import AbsencePeriod

app = FastAPI(title="Absence Calculator API")

# Configure CORS to allow requests from any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
def health_check():
    return {"status": "healthy"}

# Create database tables on startup
@app.on_event("startup")
def startup_db_client():
    try:
        Base.metadata.create_all(bind=engine)
        print("Database tables created successfully")
    except Exception as e:
        print(f"Error creating database tables: {e}")

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

def read_absence_periods(db: Session):
    try:
        print("DEBUG: Starting read_absence_periods function")
        print(f"DEBUG: Database engine URL: {db.bind.engine.url}")
        print("DEBUG: Executing query: AbsencePeriod.query.all()")
        db_periods = db.query(AbsencePeriod).all()
        print(f"DEBUG: Query executed, got {len(db_periods)} results")
        
        # Print raw database records for debugging
        for i, period in enumerate(db_periods):
            print(f"DEBUG: DB Record {i}: id={period.id}, start_date={period.start_date}, end_date={period.end_date}")
            
        absence_periods = [period.to_dict() for period in db_periods]
        print(f"Successfully read {len(absence_periods)} periods from database")
        if absence_periods:
            print(f"First period: {absence_periods[0]}")
        return absence_periods
    except Exception as e:
        import traceback
        print(f"Error reading from database: {e}")
        traceback.print_exc()
        return []

def write_absence_period(db: Session, period_data):
    try:
        db_period = AbsencePeriod.from_dict(period_data)
        db.add(db_period)
        db.commit()
        db.refresh(db_period)
        print(f"Successfully wrote period to database: {db_period.id}")
        return db_period.to_dict()
    except Exception as e:
        print(f"Error writing to database: {e}")
        db.rollback()
        return None

def update_absence_period(db: Session, period_id: str, period_data):
    try:
        db_period = db.query(AbsencePeriod).filter(AbsencePeriod.id == period_id).first()
        if not db_period:
            return None
            
        # Update fields
        db_period.start_date = datetime.strptime(period_data["start_date"], "%Y-%m-%d").date() if isinstance(period_data["start_date"], str) else period_data["start_date"]
        db_period.end_date = datetime.strptime(period_data["end_date"], "%Y-%m-%d").date() if isinstance(period_data["end_date"], str) else period_data["end_date"]
        
        db.commit()
        db.refresh(db_period)
        print(f"Successfully updated period in database: {db_period.id}")
        return db_period.to_dict()
    except Exception as e:
        print(f"Error updating database: {e}")
        db.rollback()
        return None

def delete_absence_period(db: Session, period_id: str):
    try:
        db_period = db.query(AbsencePeriod).filter(AbsencePeriod.id == period_id).first()
        if not db_period:
            return False
            
        db.delete(db_period)
        db.commit()
        print(f"Successfully deleted period from database: {period_id}")
        return True
    except Exception as e:
        print(f"Error deleting from database: {e}")
        db.rollback()
        return False

@app.get('/api/health')
def health_check():
    print("GET /api/health endpoint called")
    print("DEBUG: Health check endpoint called")
    return {"status": "healthy"}

@app.get('/api/absence-periods')
def get_absence_periods(db: Session = Depends(get_db)):
    print("GET /api/absence-periods endpoint called")
    absence_periods = read_absence_periods(db)
    print(f"Returning {len(absence_periods)} absence periods")
    return absence_periods

# Define Pydantic models for request validation
class AbsencePeriodBase(BaseModel):
    start_date: str
    end_date: str
    
    @field_validator('start_date', 'end_date')
    @classmethod
    def validate_date_format(cls, v):
        try:
            datetime.strptime(v, '%Y-%m-%d')
            return v
        except ValueError:
            raise ValueError('Invalid date format. Use YYYY-MM-DD')
    
    @field_validator('end_date')
    @classmethod
    def validate_end_date(cls, v, info):
        values = info.data
        if 'start_date' in values:
            start = datetime.strptime(values['start_date'], '%Y-%m-%d').date()
            end = datetime.strptime(v, '%Y-%m-%d').date()
            if end < start:
                raise ValueError('End date must be after start date')
        return v

class AbsencePeriodResponse(AbsencePeriodBase):
    id: str

@app.post('/api/absence-periods', status_code=201, response_model=AbsencePeriodResponse)
def create_absence_period(period: AbsencePeriodBase, db: Session = Depends(get_db)):
    # Create new period with unique ID
    new_period = {
        "id": str(uuid.uuid4()),
        "start_date": period.start_date,
        "end_date": period.end_date
    }
    
    # Write to database
    result = write_absence_period(db, new_period)
    if not result:
        raise HTTPException(status_code=500, detail="Failed to create absence period")
    
    return result

@app.put('/api/absence-periods/{period_id}', response_model=AbsencePeriodResponse)
def update_absence_period_endpoint(period_id: str, period: AbsencePeriodBase, db: Session = Depends(get_db)):
    # Update period in database
    period_data = {
        "start_date": period.start_date,
        "end_date": period.end_date
    }
    
    updated_period = update_absence_period(db, period_id, period_data)
    if not updated_period:
        raise HTTPException(status_code=404, detail="Absence period not found")
    
    return updated_period

@app.delete('/api/absence-periods/{period_id}')
def delete_absence_period_endpoint(period_id: str, db: Session = Depends(get_db)):
    # Delete period from database
    success = delete_absence_period(db, period_id)
    if not success:
        raise HTTPException(status_code=404, detail="Absence period not found")
    
    return {"message": "Absence period deleted successfully"}

class CalculationRequest(BaseModel):
    decision_date: str
    absence_periods: Optional[List[Dict[str, str]]] = None
    
    @field_validator('decision_date')
    @classmethod
    def validate_decision_date(cls, v):
        try:
            datetime.strptime(v, '%Y-%m-%d')
            return v
        except ValueError:
            raise ValueError('Invalid date format for decision_date. Use YYYY-MM-DD')

@app.post('/api/calculate')
def calculate_rule(request: CalculationRequest, db: Session = Depends(get_db)):
    try:
        # Get absence periods from database if not provided
        periods = request.absence_periods if request.absence_periods else read_absence_periods(db)
        
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
        decision_date_dt = request.decision_date
        if isinstance(decision_date_dt, str):
            decision_date_dt = datetime.strptime(decision_date_dt, '%Y-%m-%d')
        
        # Calculate the 180-day rule
        result = calculate_180_day_rule(absence_periods_list, decision_date_dt)
        
        # Add the qualifying start date to the result
        qualifying_start = decision_date_dt - timedelta(days=5*365)
        result["qualifying_start"] = qualifying_start.strftime('%Y-%m-%d')
        result["decision_date"] = decision_date_dt.strftime('%Y-%m-%d')
        
        return result
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=5001)
