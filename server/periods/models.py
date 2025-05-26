from pydantic import BaseModel, field_validator, ConfigDict
from typing import List, Optional, Dict
from datetime import datetime

class AbsencePeriodBase(BaseModel):
    model_config = ConfigDict(extra='ignore')
    start_date: str
    end_date: str
    
    @field_validator('start_date', 'end_date')
    def validate_date_format(cls, v):
        try:
            datetime.strptime(v, "%Y-%m-%d")
            return v
        except ValueError:
            raise ValueError("Date must be in format YYYY-MM-DD")
    
    @field_validator('end_date')
    def validate_end_date(cls, v, info):
        start_date = info.data.get('start_date')
        if start_date:
            try:
                start = datetime.strptime(start_date, "%Y-%m-%d")
                end = datetime.strptime(v, "%Y-%m-%d")
                if end < start:
                    raise ValueError("End date must be after start date")
            except ValueError as e:
                if "format" not in str(e):  # Only re-raise if it's our custom error
                    raise
        return v

class AbsencePeriodResponse(BaseModel):
    id: str
    start_date: str
    end_date: str

class CalculationRequest(BaseModel):
    model_config = ConfigDict(extra='ignore')
    decision_date: str
    absence_periods: Optional[List[Dict[str, str]]] = None
    
    @field_validator('decision_date')
    def validate_decision_date(cls, v):
        try:
            datetime.strptime(v, "%Y-%m-%d")
            return v
        except ValueError:
            raise ValueError("Decision date must be in format YYYY-MM-DD")
