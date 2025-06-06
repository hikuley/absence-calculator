from tortoise import fields, models, Tortoise
from tortoise.contrib.pydantic import pydantic_model_creator
import uuid
import asyncio
import os
from datetime import datetime, timedelta, date

class User(models.Model):
    """User model for authentication"""
    id = fields.UUIDField(pk=True)
    username = fields.CharField(max_length=50, unique=True)
    email = fields.CharField(max_length=255, unique=True)
    password_hash = fields.CharField(max_length=255)
    created_at = fields.DatetimeField(auto_now_add=True)
    
    # Define reverse relationships
    tokens: fields.ReverseRelation["Token"]
    absence_periods: fields.ReverseRelation["AbsencePeriod"]
    
    class Meta:
        table = "users"
    
    def __str__(self):
        return f"{self.username} ({self.email})"
    
    @classmethod
    async def create_user(cls, username, email, password_hash):
        """Create a new user with hashed password"""
        return await cls.create(id=uuid.uuid4(), username=username, email=email, password_hash=password_hash)

class Token(models.Model):
    """Token model for JWT authentication"""
    id = fields.UUIDField(pk=True)
    user = fields.ForeignKeyField('models.User', related_name='tokens', on_delete=fields.CASCADE)
    token = fields.CharField(max_length=255, index=True)
    expires_at = fields.DatetimeField()
    created_at = fields.DatetimeField(auto_now_add=True)
    
    class Meta:
        table = "tokens"
    
    def __str__(self):
        return f"Token for {self.user.username} (expires: {self.expires_at})"
    
    @classmethod
    async def create_token(cls, user, token, expires_at):
        """Create a new token for a user"""
        return await cls.create(id=uuid.uuid4(), user=user, token=token, expires_at=expires_at)

class AbsencePeriod(models.Model):
    """Absence period model for tracking time away"""
    id = fields.UUIDField(pk=True)
    start_date = fields.DateField()
    end_date = fields.DateField()
    user = fields.ForeignKeyField('models.User', related_name='absence_periods', on_delete=fields.CASCADE)
    created_at = fields.DatetimeField(auto_now_add=True)
    
    class Meta:
        table = "absence_periods"
    
    def __str__(self):
        return f"Absence: {self.start_date} to {self.end_date} for {self.user.username}"
    
    @classmethod
    async def create_period(cls, user, start_date, end_date):
        """Create a new absence period for a user"""
        return await cls.create(id=uuid.uuid4(), user=user, start_date=start_date, end_date=end_date)
    
    def to_dict(self):
        """Convert model to dictionary for API response"""
        return {
            "id": str(self.id),
            "start_date": self.start_date.strftime("%Y-%m-%d") if isinstance(self.start_date, (datetime, date)) else self.start_date,
            "end_date": self.end_date.strftime("%Y-%m-%d") if isinstance(self.end_date, (datetime, date)) else self.end_date,
            "user_id": str(self.user_id)
        }

# Create Pydantic models for API validation and serialization
User_Pydantic = pydantic_model_creator(User, name="User", exclude=("password_hash",))
UserIn_Pydantic = pydantic_model_creator(User, name="UserIn", exclude_readonly=True, exclude=("id", "created_at"))
Token_Pydantic = pydantic_model_creator(Token, name="Token")
AbsencePeriod_Pydantic = pydantic_model_creator(AbsencePeriod, name="AbsencePeriod")
AbsencePeriodIn_Pydantic = pydantic_model_creator(AbsencePeriod, name="AbsencePeriodIn", exclude_readonly=True, exclude=("id", "created_at", "user_id"))


# Database migration utilities
async def ensure_schema_consistency():
    """Ensure database schema is consistent with models"""
    # Get connection
    conn = Tortoise.get_connection("default")
    
    try:
        # Check for columns in absence_periods table
        query_columns = """
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'absence_periods'
        """
        result_columns = await conn.execute_query(query_columns)
        columns = [row[0] for row in result_columns[1]]
        print(f"Existing columns in absence_periods: {columns}")
        
        # Check for created_at column
        if 'created_at' not in columns:
            print("Adding created_at column to absence_periods table...")
            await conn.execute_script("""
            ALTER TABLE absence_periods 
            ADD COLUMN created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            """)
            print("created_at column added successfully!")
        
        # Check for user_id column
        if 'user_id' not in columns:
            # If we have a 'user_id' column but it's named differently
            if any(col.endswith('_id') for col in columns):
                user_col = next((col for col in columns if col.endswith('_id')), None)
                if user_col and user_col != 'user_id':
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
    except Exception as e:
        print(f"Error ensuring schema consistency: {e}")


def run_schema_migration():
    """Run the schema migration function"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
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
    
    async def _run_migration():
        # Connect to the database
        await Tortoise.init(config=TORTOISE_ORM)
        
        # Generate schemas for any missing tables
        await Tortoise.generate_schemas()
        
        # Ensure schema consistency
        await ensure_schema_consistency()
        
        # Close the connection
        await Tortoise.close_connections()
    
    # Run the migration
    loop.run_until_complete(_run_migration())
    loop.close()


# Run migration if this file is executed directly
if __name__ == "__main__":
    print("Running database schema migration...")
    run_schema_migration()
    print("Migration complete!")

