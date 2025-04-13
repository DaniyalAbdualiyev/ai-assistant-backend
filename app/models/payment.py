from sqlalchemy import Column, Integer, Float, String, ForeignKey, DateTime
from app.database import Base
from datetime import datetime

class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    plan_id = Column(Integer, ForeignKey('subscription_plans.id'), nullable=False)
    amount = Column(Float, nullable=False)
    status = Column(String, nullable=False)
    transaction_id = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.now)

    def __repr__(self):
        return f"<Payment(user_id={self.user_id}, amount={self.amount}, status={self.status})>"