from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import bcrypt
import jwt
import uuid
from datetime import datetime, timedelta
import os

from models import User, Token as TokenModel
from .models import UserCreate, UserLogin, TokenResponse, UserResponse
from .dependencies import get_current_user, JWT_SECRET

router = APIRouter(prefix="/api", tags=["authentication"])

@router.post('/signup', response_model=UserResponse)
async def signup(user: UserCreate):
    """Register a new user"""
    try:
        # Check if username already exists
        existing_user = await User.filter(username=user.username).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Username already exists")
        
        # Check if email already exists
        existing_email = await User.filter(email=user.email).first()
        if existing_email:
            raise HTTPException(status_code=400, detail="Email already exists")
        
        # Hash the password
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

@router.post('/login', response_model=TokenResponse)
async def login(user: UserLogin):
    """Login a user and return a JWT token"""
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

@router.post('/logout')
async def logout(credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())):
    """Logout a user by invalidating their token"""
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

@router.get('/me', response_model=UserResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get the current authenticated user's information"""
    return current_user
