from sqlalchemy import Column, Integer, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship, declared_attr
from app.database import Base
from datetime import datetime, timedelta

class UserSubscription(Base):
    __tablename__ = "user_subscriptions"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    plan_id = Column(Integer, ForeignKey('subscription_plans.id'), nullable=False)
    payment_id = Column(Integer, ForeignKey('payments.id'), nullable=False)
    start_date = Column(DateTime, default=datetime.utcnow)
    end_date = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    @declared_attr
    def user(cls):
        return relationship("User", back_populates="subscriptions")
    
    @declared_attr
    def plan(cls):
        return relationship("SubscriptionPlan")
    
    @declared_attr
    def payment(cls):
        return relationship("Payment")

    def __repr__(self):
        return f"<UserSubscription(user_id={self.user_id}, plan_id={self.plan_id}, active={self.is_active})>"
    
    @property
    def is_valid(self):
        """Check if subscription is active and not expired"""
        return self.is_active and datetime.utcnow() <= self.end_date
