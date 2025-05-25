"""
Database migration system for Absence Calculator using Tortoise ORM
"""
import os
import logging
import asyncio
import bcrypt
import uuid
from tortoise import Tortoise
from database import TORTOISE_ORM, init_db, close_db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database connection details
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "absence_calculator")

async def create_database_if_not_exists():
    """Create the database if it doesn't exist using asyncpg"""
    import asyncpg
    try:
        # Connect to the default postgres database
        conn = await asyncpg.connect(
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
            database="postgres"
        )
        
        # Check if the database exists
        exists = await conn.fetchval(f"SELECT 1 FROM pg_database WHERE datname = '{DB_NAME}'")
        
        if not exists:
            # Create the database
            await conn.execute(f"CREATE DATABASE {DB_NAME}")
            logger.info(f"Database {DB_NAME} created successfully")
        else:
            logger.info(f"Database {DB_NAME} already exists")
            
        await conn.close()
    except Exception as e:
        logger.error(f"Error creating database: {e}")
        raise

async def create_demo_user():
    """Create a demo user if it doesn't exist"""
    try:
        # Import here to avoid circular imports
        from models import User
        
        # Check if demo user exists
        demo_user = await User.filter(username="demo").first()
        
        if not demo_user:
            # Create demo user
            password_hash = bcrypt.hashpw("demo".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            await User.create(
                id=uuid.uuid4(),
                username="demo",
                email="demo@example.com",
                password_hash=password_hash
            )
            logger.info("Demo user created successfully")
        else:
            logger.info("Demo user demo already exists")
    except Exception as e:
        logger.error(f"Error creating demo user: {e}")
        raise

async def initialize_database():
    """Initialize the database with Tortoise ORM"""
    try:
        # Create database if it doesn't exist
        await create_database_if_not_exists()
        
        # Initialize Tortoise ORM
        await init_db()
        
        # Create demo user
        await create_demo_user()
        
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise
    finally:
        # Close Tortoise ORM connections
        await close_db()

# Function to run the async initialize_database function
def run_initialize_database():
    """Run the async initialize_database function"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(initialize_database())
    loop.close()

if __name__ == "__main__":
    run_initialize_database()
