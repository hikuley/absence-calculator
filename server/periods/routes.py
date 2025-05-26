from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict
import uuid
from datetime import datetime

from models import AbsencePeriod, User
from auth.dependencies import get_current_user
from .models import AbsencePeriodBase, AbsencePeriodResponse, CalculationRequest
from utils.calculation import calculate_180_day_rule

router = APIRouter(prefix="/api", tags=["absence_periods"])

@router.get('/absence-periods', response_model=List[Dict])
async def get_absence_periods(current_user: Dict = Depends(get_current_user)):
    """Get all absence periods for the current user"""
    user = await User.get(id=current_user["id"])
    periods = await AbsencePeriod.filter(user=user)
    return [period.to_dict() for period in periods]

@router.post('/absence-periods', response_model=AbsencePeriodResponse)
async def create_absence_period(period: AbsencePeriodBase, current_user: Dict = Depends(get_current_user)):
    """Create a new absence period for the current user"""
    try:
        # Parse dates
        start_date = datetime.strptime(period.start_date, "%Y-%m-%d").date()
        end_date = datetime.strptime(period.end_date, "%Y-%m-%d").date()
        
        # Get user
        user = await User.get(id=current_user["id"])
        
        # Create period
        new_period = await AbsencePeriod.create(
            id=uuid.uuid4(),
            user=user,
            start_date=start_date,
            end_date=end_date
        )
        
        # Return response
        return {
            "id": str(new_period.id),
            "start_date": new_period.start_date.strftime("%Y-%m-%d"),
            "end_date": new_period.end_date.strftime("%Y-%m-%d")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put('/absence-periods/{period_id}')
async def update_absence_period_endpoint(period_id: str, period: AbsencePeriodBase, current_user: Dict = Depends(get_current_user)):
    """Update an existing absence period"""
    try:
        # Parse dates
        start_date = datetime.strptime(period.start_date, "%Y-%m-%d").date()
        end_date = datetime.strptime(period.end_date, "%Y-%m-%d").date()
        
        # Get period
        db_period = await AbsencePeriod.filter(id=period_id).first()
        if not db_period:
            raise HTTPException(status_code=404, detail="Period not found")
        
        # Check if period belongs to user
        if str(db_period.user_id) != current_user["id"]:
            raise HTTPException(status_code=403, detail="Not authorized to update this period")
        
        # Update period
        db_period.start_date = start_date
        db_period.end_date = end_date
        await db_period.save()
        
        return {"message": "Period updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete('/absence-periods/{period_id}')
async def delete_absence_period_endpoint(period_id: str, current_user: Dict = Depends(get_current_user)):
    """Delete an absence period"""
    try:
        # Get period
        period = await AbsencePeriod.filter(id=period_id).first()
        if not period:
            raise HTTPException(status_code=404, detail="Period not found")
        
        # Check if period belongs to user
        if str(period.user_id) != current_user["id"]:
            raise HTTPException(status_code=403, detail="Not authorized to delete this period")
        
        # Delete period
        await period.delete()
        
        return {"message": "Period deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post('/calculate')
async def calculate_rule(request: CalculationRequest, current_user: Dict = Depends(get_current_user)):
    """Calculate the 180-day rule based on absence periods"""
    try:
        # Parse decision date
        decision_date = datetime.strptime(request.decision_date, "%Y-%m-%d").date()
        
        # Get absence periods
        absence_periods = []
        
        if request.absence_periods:
            # Use provided absence periods
            for period in request.absence_periods:
                start_date = datetime.strptime(period["start_date"], "%Y-%m-%d").date()
                end_date = datetime.strptime(period["end_date"], "%Y-%m-%d").date()
                absence_periods.append((start_date, end_date))
        else:
            # Get periods from database
            user = await User.get(id=current_user["id"])
            db_periods = await AbsencePeriod.filter(user=user)
            
            for period in db_periods:
                absence_periods.append((period.start_date, period.end_date))
        
        # Calculate the rule
        result = calculate_180_day_rule(absence_periods, decision_date)
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
