from tortoise import Tortoise
import os

# Get database connection details from environment variables
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "absence_calculator")

# Tortoise ORM database URL
DATABASE_URL = f"postgres://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Tortoise ORM models configuration
TORTOISE_ORM = {
    "connections": {"default": DATABASE_URL},
    "apps": {
        "models": {
            "models": ["models"],
            "default_connection": "default",
        },
    },
}

# Initialize Tortoise ORM
async def init_db():
    """Initialize the Tortoise ORM with the database connection"""
    await Tortoise.init(config=TORTOISE_ORM)
    # Generate schemas if needed
    await Tortoise.generate_schemas()

# Close Tortoise ORM connection
async def close_db():
    """Close the Tortoise ORM connection"""
    await Tortoise.close_connections()
