from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from datetime import datetime
import os

from models import User, Token as TokenModel

# Security
security = HTTPBearer()

# JWT Secret key
JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key")

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Dependency for authenticating users with JWT tokens.
    Verifies the token and returns the current user.
    """
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
