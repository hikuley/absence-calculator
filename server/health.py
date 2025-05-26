from fastapi import APIRouter
from database import init_db, close_db

# Create a router for health-related endpoints
health_router = APIRouter(tags=["health"])

# Health check endpoint
@health_router.get("/api/health")
async def health_check():
    """Health check endpoint to verify the API is running"""
    return {"status": "healthy"}

# Database event handlers
async def startup_db_client():
    """Initialize Tortoise ORM on application startup"""
    await init_db()

async def shutdown_db_client():
    """Close Tortoise ORM connections on application shutdown"""
    await close_db()

# Function to register events with the FastAPI app
def register_db_events(app):
    """Register database startup and shutdown events with the FastAPI app"""
    app.add_event_handler("startup", startup_db_client)
    app.add_event_handler("shutdown", shutdown_db_client)
