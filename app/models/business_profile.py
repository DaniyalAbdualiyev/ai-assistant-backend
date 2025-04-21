from sqlalchemy import Column, Integer, String, JSON, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime
import uuid

# Forward references for relationships
from sqlalchemy.ext.declarative import declared_attr

class BusinessProfile(Base):
    __tablename__ = "business_profiles"

    id = Column(Integer, primary_key=True)
    unique_id = Column(String, unique=True, default=lambda: str(uuid.uuid4()), nullable=False)
    business_name = Column(String, nullable=False)
    business_type = Column(String, nullable=False)
    tone_preferences = Column(JSON, nullable=False)
    knowledge_base = Column(JSON, nullable=True)
    assistant_id = Column(Integer, ForeignKey("assistants.id", ondelete="CASCADE"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    assistant = relationship("AIAssistant", back_populates="business_profile")
    
    @declared_attr
    def analytics(cls):
        return relationship("ConversationAnalytics", back_populates="business_profile")
        
    @declared_attr
    def client_analytics(cls):
        return relationship("ClientAnalytics", back_populates="business_profile")