"""
Script to update the database schema for the Absence Calculator application.
This script adds the missing created_at column to the absence_periods table.
"""
import asyncio
import os
from tortoise import Tortoise

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

async def update_schema():
    """Update the database schema to add missing columns"""
    # Connect to the database
    await Tortoise.init(config=TORTOISE_ORM)
    
    # Get connection
    conn = Tortoise.get_connection("default")
    
    try:
        # 1. Check if created_at column exists
        query_created_at = """
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'absence_periods' AND column_name = 'created_at'
        """
        result_created_at = await conn.execute_query(query_created_at)
        
        # If created_at column doesn't exist, add it
        if not result_created_at[1]:
            print("Adding created_at column to absence_periods table...")
            await conn.execute_script("""
            ALTER TABLE absence_periods 
            ADD COLUMN created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            """)
            print("created_at column added successfully!")
        else:
            print("created_at column already exists in absence_periods table.")
        
        # 2. Check the column name for the user relationship
        query_columns = """
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'absence_periods'
        """
        result_columns = await conn.execute_query(query_columns)
        columns = [row[0] for row in result_columns[1]]
        print(f"Existing columns in absence_periods: {columns}")
        
        # Check for user_id column
        if 'user_id' not in columns:
            # If we have a 'user_id' column but it's named differently
            if any(col.endswith('_id') for col in columns):
                user_col = next((col for col in columns if col.endswith('_id')), None)
                if user_col:
                    print(f"Renaming column {user_col} to user_id...")
                    await conn.execute_script(f"""
                    ALTER TABLE absence_periods 
                    RENAME COLUMN {user_col} TO user_id
                    """)
                    print("Column renamed successfully!")
            else:
                print("Adding user_id column to absence_periods table...")
                await conn.execute_script("""
                ALTER TABLE absence_periods 
                ADD COLUMN user_id UUID REFERENCES users(id) ON DELETE CASCADE
                """)
                print("user_id column added successfully!")
        else:
            print("user_id column already exists in absence_periods table.")
    except Exception as e:
        print(f"Error updating schema: {e}")
    finally:
        # Close the connection
        await Tortoise.close_connections()

def run_update():
    """Run the update_schema function"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(update_schema())
    loop.close()

if __name__ == "__main__":
    run_update()
