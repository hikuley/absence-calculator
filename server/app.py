from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from tortoise.contrib.fastapi import register_tortoise
import os

# Import database configuration
from database import TORTOISE_ORM, init_db, close_db

# Import routers from modules
from auth import auth_router
from periods import periods_router

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

# Include routers from modules
app.include_router(auth_router)
app.include_router(periods_router)

# Health check endpoint
@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}

# Initialize Tortoise ORM on startup
@app.on_event("startup")
async def startup_db_client():
    await init_db()

# Close Tortoise ORM connections on shutdown
@app.on_event("shutdown")
async def shutdown_db_client():
    await close_db()

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
