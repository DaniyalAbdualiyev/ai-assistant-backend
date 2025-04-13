from sqlalchemy import Column, Integer, String, Float, DateTime
from app.database import Base
from datetime import datetime

class SubscriptionPlan(Base):
    __tablename__ = "subscription_plans"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    features = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.now)

    def __repr__(self):
        return f"<SubscriptionPlan(name={self.name}, price={self.price})>"
    