from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
import jwt
from datetime import datetime
import os
from typing import List

from models import User, Token as TokenModel
from .dependencies import JWT_SECRET

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp

class AuthMiddleware(BaseHTTPMiddleware):
    """Middleware for JWT authentication at the request level"""
    
    def __init__(self, app: ASGIApp, exempt_paths: List[str] = None):
        """
        Initialize the middleware with paths that don't require authentication
        
        Args:
            app: The ASGI application
            exempt_paths: List of API paths that don't require authentication
        """
        super().__init__(app)
        self.exempt_paths = exempt_paths or [
            "/api/login",
            "/api/signup",
            "/api/health",
            "/docs",
            "/redoc",
            "/openapi.json"
        ]
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint):
        """
        Process the request and validate JWT token if needed
        
        Args:
            request: The incoming request
            call_next: The next middleware or endpoint handler
        
        Returns:
            The response from the next handler or an error response
        """
        # Always allow preflight requests (OPTIONS) to pass through for CORS
        if request.method == "OPTIONS":
            return await call_next(request)
            
        # Skip authentication for exempt paths
        if any(request.url.path.startswith(path) for path in self.exempt_paths):
            return await call_next(request)
        
        # Get authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Authorization header missing"},
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Check if it's a Bearer token
        try:
            scheme, token = auth_header.split()
            if scheme.lower() != "bearer":
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Invalid authentication scheme"},
                    headers={"WWW-Authenticate": "Bearer"}
                )
        except ValueError:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Invalid authorization header format"},
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Validate the token
        try:
            # Verify the JWT token
            payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
            user_id = payload.get("sub")
            
            # Check if token exists in database
            db_token = await TokenModel.filter(token=token).first()
            if not db_token:
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Invalid token or token expired"},
                    headers={"WWW-Authenticate": "Bearer"}
                )
            
            # Check if token is expired
            current_time = datetime.now().replace(tzinfo=None)
            token_expiry = db_token.expires_at
            
            # If token_expiry has timezone info, convert to naive datetime
            if hasattr(token_expiry, 'tzinfo') and token_expiry.tzinfo:
                token_expiry = token_expiry.replace(tzinfo=None)
                
            if token_expiry < current_time:
                await db_token.delete()
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Token expired"},
                    headers={"WWW-Authenticate": "Bearer"}
                )
            
            # Get user
            user = await User.get(id=user_id)
            if not user:
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "User not found"},
                    headers={"WWW-Authenticate": "Bearer"}
                )
            
            # Add user to request state
            request.state.user = {
                "id": str(user.id),
                "username": user.username,
                "email": user.email
            }
            
            # Continue with the request
            return await call_next(request)
            
        except jwt.PyJWTError:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Invalid token"},
                headers={"WWW-Authenticate": "Bearer"}
            )
        except Exception as e:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": f"Authentication error: {str(e)}"},
                headers={"WWW-Authenticate": "Bearer"}
            )
