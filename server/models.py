from sqlalchemy import Column, String, Date
from sqlalchemy.ext.declarative import declarative_base
from database import Base
import uuid
from datetime import datetime

class AbsencePeriod(Base):
    __tablename__ = "absence_periods"

    id = Column(String, primary_key=True, index=True)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)

    @classmethod
    def from_dict(cls, data):
        """Create an AbsencePeriod instance from a dictionary"""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            start_date=datetime.strptime(data["start_date"], "%Y-%m-%d").date() if isinstance(data["start_date"], str) else data["start_date"],
            end_date=datetime.strptime(data["end_date"], "%Y-%m-%d").date() if isinstance(data["end_date"], str) else data["end_date"]
        )
    
    def to_dict(self):
        """Convert AbsencePeriod instance to a dictionary"""
        return {
            "id": self.id,
            "start_date": self.start_date.strftime("%Y-%m-%d") if self.start_date else None,
            "end_date": self.end_date.strftime("%Y-%m-%d") if self.end_date else None
        }
