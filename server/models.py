from tortoise import fields, models
from tortoise.contrib.pydantic import pydantic_model_creator
import uuid
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
