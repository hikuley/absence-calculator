from fastapi import Request, HTTPException, status

async def get_request_user(request: Request):
    """
    Dependency to get the current user from the request state.
    This user was already validated by the middleware.
    
    Args:
        request: The incoming request with user in state
        
    Returns:
        The user information
        
    Raises:
        HTTPException: If user is not in request state
    """
    if not hasattr(request.state, "user"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return request.state.user
