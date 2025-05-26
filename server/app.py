from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from tortoise.contrib.fastapi import register_tortoise
import os

# Import database configuration
from database import TORTOISE_ORM

# Import routers from modules
from auth import auth_router, AuthMiddleware
from periods import periods_router
from health import health_router, register_db_events

# Create FastAPI application
app = FastAPI(title="Absence Calculator API")

# Configure CORS to allow requests from any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add authentication middleware
app.add_middleware(AuthMiddleware)

# Include routers from modules
app.include_router(auth_router)
app.include_router(periods_router)
app.include_router(health_router)

# Register database event handlers
register_db_events(app)

# Register Tortoise ORM with FastAPI
register_tortoise(
    app,
    config=TORTOISE_ORM,
    generate_schemas=True,
    add_exception_handlers=True,
)

# Run the application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=5001)
