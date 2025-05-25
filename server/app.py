from fastapi import FastAPI, HTTPException, Response, Request, Depends, Header, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, field_validator, ConfigDict, EmailStr
from typing import List, Optional, Dict, Any, Tuple, Union, cast, Annotated
import os
import uuid
import bcrypt
import jwt
from datetime import datetime, timedelta

# Import Tortoise ORM models and database functions
from tortoise.contrib.fastapi import register_tortoise
from database import TORTOISE_ORM, init_db, close_db
from models import User, AbsencePeriod, User_Pydantic, UserIn_Pydantic, Token_Pydantic, AbsencePeriod_Pydantic, AbsencePeriodIn_Pydantic
# Import the Token model with an alias to avoid naming conflicts
from models import Token as TokenModel

app = FastAPI(title="Absence Calculator API")

# Configure CORS to allow requests from any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# JWT Secret key
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key")

# Authentication dependency
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token_str = credentials.credentials
    try:
        # Verify the JWT token
        payload = jwt.decode(token_str, JWT_SECRET, algorithms=["HS256"])
        user_id = payload.get("sub")
        
        # Check if token exists in database
        db_token = await TokenModel.filter(token=token_str).first()
        if not db_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token or token expired",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Check if token is expired
        try:
            # Convert both to UTC for proper comparison
            current_time = datetime.now().replace(tzinfo=None)
            token_expiry = db_token.expires_at
            
            # If token_expiry has timezone info, convert to naive datetime
            if hasattr(token_expiry, 'tzinfo') and token_expiry.tzinfo:
                token_expiry = token_expiry.replace(tzinfo=None)
                
            if token_expiry < current_time:
                await db_token.delete()
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token expired",
                    headers={"WWW-Authenticate": "Bearer"}
                )
        except Exception as e:
            print(f"Token expiry check error: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token validation error",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Get user
        user = await User.get(id=user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Return user as dict for compatibility
        return {
            "id": str(user.id),
            "username": user.username,
            "email": user.email
        }
    except jwt.PyJWTError as e:
        print(f"JWT Error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except Exception as e:
        print(f"Authentication error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication error",
            headers={"WWW-Authenticate": "Bearer"}
        )

@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}

# Initialize Tortoise ORM on startup
@app.on_event("startup")
async def startup_db_client():
    try:
        await init_db()
        print("Backend server started successfully")
    except Exception as e:
        print(f"Error during startup: {e}")

# Close Tortoise ORM connections on shutdown
@app.on_event("shutdown")
async def shutdown_db_client():
    try:
        await close_db()
        print("Database connections closed")
    except Exception as e:
        print(f"Error during shutdown: {e}")

# Register Tortoise ORM with FastAPI
register_tortoise(
    app,
    config=TORTOISE_ORM,
    generate_schemas=True,
    add_exception_handlers=True,
)

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

# Note: read_absence_periods is now imported from db_helper
@app.get('/api/health')
def health_check():
    print("GET /api/health endpoint called")
    print("DEBUG: Health check endpoint called")
    return {"status": "healthy"}

@app.get('/api/absence-periods')
async def get_absence_periods(current_user: Dict = Depends(get_current_user)):
    # Get absence periods for the current user
    absence_periods = await AbsencePeriod.filter(user_id=current_user["id"])
    # Convert to dict for API response
    return [period.to_dict() for period in absence_periods]

# Define Pydantic models for request validation
class AbsencePeriodBase(BaseModel):
    model_config = ConfigDict(extra='ignore')
    
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

@app.post('/api/absence-periods', response_model=AbsencePeriodResponse)
async def create_absence_period(period: AbsencePeriodBase, current_user: Dict = Depends(get_current_user)):
    try:
        # Parse dates
        start_date = datetime.strptime(period.start_date, "%Y-%m-%d").date()
        end_date = datetime.strptime(period.end_date, "%Y-%m-%d").date()
        
        # Get user
        user = await User.get(id=current_user["id"])
        
        # Create absence period
        new_period = await AbsencePeriod.create(
            id=uuid.uuid4(),
            user=user,
            start_date=start_date,
            end_date=end_date
        )
        
        # Return the complete response
        return {
            "id": str(new_period.id),
            "start_date": period.start_date,
            "end_date": period.end_date
        }
    except Exception as e:
        print(f"Error creating absence period: {e}")
        raise HTTPException(status_code=500, detail="Failed to create absence period")

@app.put('/api/absence-periods/{period_id}', response_model=AbsencePeriodResponse)
async def update_absence_period_endpoint(period_id: str, period: AbsencePeriodBase, current_user: Dict = Depends(get_current_user)):
    try:
        # Convert string dates to datetime.date objects
        start_date = datetime.strptime(period.start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(period.end_date, '%Y-%m-%d').date()
        
        # Find the period and check ownership
        existing_period = await AbsencePeriod.filter(id=period_id, user_id=current_user['id']).first()
        if not existing_period:
            raise HTTPException(status_code=404, detail="Absence period not found or not owned by user")
        
        # Update the period
        existing_period.start_date = start_date
        existing_period.end_date = end_date
        await existing_period.save()
        
        return {"id": str(existing_period.id), "start_date": period.start_date, "end_date": period.end_date}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete('/api/absence-periods/{period_id}')
async def delete_absence_period_endpoint(period_id: str, current_user: Dict = Depends(get_current_user)):
    try:
        # Find the period and check ownership
        existing_period = await AbsencePeriod.filter(id=period_id, user_id=current_user['id']).first()
        if not existing_period:
            raise HTTPException(status_code=404, detail="Absence period not found or not owned by user")
        
        # Delete the period
        await existing_period.delete()
        
        return {"message": "Absence period deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class CalculationRequest(BaseModel):
    model_config = ConfigDict(extra='ignore')
    
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
async def calculate_rule(request: CalculationRequest, current_user: Dict = Depends(get_current_user)):
    try:
        # Get absence periods from database if not provided
        if request.absence_periods:
            periods = request.absence_periods
        else:
            # Get absence periods from database using Tortoise ORM
            db_periods = await AbsencePeriod.filter(user_id=current_user['id'])
            periods = [period.to_dict() for period in db_periods]
        
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

# User registration and authentication models
class UserCreate(BaseModel):
    model_config = ConfigDict(extra='ignore')
    
    username: str
    email: EmailStr
    password: str
    
    @field_validator('username')
    @classmethod
    def username_must_be_valid(cls, v):
        if len(v) < 3:
            raise ValueError('Username must be at least 3 characters')
        if not v.isalnum():
            raise ValueError('Username must contain only alphanumeric characters')
        return v
    
    @field_validator('password')
    @classmethod
    def password_must_be_strong(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        return v

class UserLogin(BaseModel):
    model_config = ConfigDict(extra='ignore')
    
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str

class UserResponse(BaseModel):
    id: str
    username: str
    email: str

# Authentication endpoints
@app.post('/api/signup', response_model=UserResponse)
async def signup(user: UserCreate):
    try:
        # Check if username already exists
        existing_user = await User.filter(username=user.username).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Username already exists")
        
        # Check if email already exists
        existing_email = await User.filter(email=user.email).first()
        if existing_email:
            raise HTTPException(status_code=400, detail="Email already exists")
        
        # Hash password
        password_hash = bcrypt.hashpw(user.password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Create new user
        new_user = await User.create(
            id=uuid.uuid4(),
            username=user.username,
            email=user.email,
            password_hash=password_hash
        )
        
        return {
            "id": str(new_user.id),
            "username": new_user.username,
            "email": new_user.email
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post('/api/login', response_model=TokenResponse)
async def login(user: UserLogin):
    try:
        # Find user by username
        db_user = await User.filter(username=user.username).first()
        if not db_user:
            print(f"User not found: {user.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Debug info
        print(f"Found user: {db_user.username}, checking password")
        print(f"Stored hash: {db_user.password_hash}")
        
        # Verify password
        try:
            password_matches = bcrypt.checkpw(
                user.password.encode('utf-8'), 
                db_user.password_hash.encode('utf-8')
            )
            print(f"Password match result: {password_matches}")
            
            if not password_matches:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid username or password",
                    headers={"WWW-Authenticate": "Bearer"}
                )
        except Exception as pwd_err:
            print(f"Password verification error: {pwd_err}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Password verification error",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Create JWT token
        expiration = datetime.now() + timedelta(hours=24)
        token_data = {
            "sub": str(db_user.id),
            "exp": expiration.timestamp()
        }
        token_str = jwt.encode(token_data, JWT_SECRET, algorithm="HS256")
        
        # Store token in database
        try:
            # Debug info
            print(f"Creating token for user_id: {db_user.id}, token: {token_str[:10]}...")
            
            # Create token with explicit fields
            token_id = uuid.uuid4()
            new_token = await TokenModel.create(
                id=token_id,
                user=db_user,
                token=token_str,
                expires_at=expiration
            )
            print(f"Token created successfully with ID: {new_token.id}")
        except Exception as token_err:
            print(f"Token creation error: {token_err}")
            import traceback
            traceback.print_exc()
            raise HTTPException(status_code=500, detail="Token creation error")
        
        return {"access_token": token_str, "token_type": "bearer"}
    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        print(f"Login error: {e}")
        raise HTTPException(status_code=500, detail="Authentication error")

@app.post('/api/logout')
async def logout(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        # Get token from header
        token_str = credentials.credentials
        
        # Find token in database
        token = await TokenModel.filter(token=token_str).first()
        if not token:
            raise HTTPException(status_code=400, detail="Invalid token")
        
        # Delete token
        await token.delete()
        
        return {"message": "Successfully logged out"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get('/api/me', response_model=UserResponse)
async def get_current_user_info(current_user: Dict = Depends(get_current_user)):
    return current_user

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=5001)
