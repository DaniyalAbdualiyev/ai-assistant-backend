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
    duration = Column(Enum(DurationType), nullable=False, default=DurationType.monthly)
    duration_months = Column(Integer, nullable=False, default=1)  # Number of months (1 for monthly, 12 for yearly)
    created_at = Column(DateTime, default=datetime.now)

    def __repr__(self):
        return f"<SubscriptionPlan(name={self.name}, price={self.price})>"
    