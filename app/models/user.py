from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.orm import relationship, declared_attr
from app.database import Base
import datetime

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    is_admin = Column(Boolean, default=False, nullable=True)

    @declared_attr
    def assistants(cls):
        return relationship("AIAssistant", back_populates="user", cascade="all, delete-orphan")
    
    @declared_attr
    def subscriptions(cls):
        return relationship("UserSubscription", back_populates="user")
    
    @declared_attr
    def messages(cls):
        return relationship("Message", back_populates="user", cascade="all, delete-orphan")