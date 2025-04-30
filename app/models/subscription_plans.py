from sqlalchemy import Column, Integer, String, Float, DateTime, Enum
from app.database import Base
from datetime import datetime
import enum

class DurationType(enum.Enum):
    monthly = "monthly"
    yearly = "yearly"
    
    def __str__(self):
        return self.value

class SubscriptionPlan(Base):
    __tablename__ = "subscription_plans"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    features = Column(String, nullable=False)
    # Commented out due to missing columns in database
    # duration = Column(Enum(DurationType), nullable=False, default=DurationType.monthly)
    # duration_months = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, default=datetime.now)

    # Add properties to maintain compatibility with existing code
    @property
    def duration(self):
        # Default to monthly if no duration info in database
        return DurationType.monthly
        
    @property
    def duration_months(self):
        # Default to 1 month
        return 1

    def __repr__(self):
        return f"<SubscriptionPlan(name={self.name}, price={self.price})>"
    