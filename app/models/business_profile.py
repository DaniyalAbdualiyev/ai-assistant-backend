from sqlalchemy import Column, Integer, String, JSON, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime

class BusinessProfile(Base):
    __tablename__ = "business_profiles"

    id = Column(Integer, primary_key=True)
    business_name = Column(String, nullable=False)
    business_type = Column(String, nullable=False)
    tone_preferences = Column(JSON, nullable=False)
    knowledge_base = Column(JSON, nullable=True)
    assistant_id = Column(Integer, ForeignKey("assistants.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship with Assistant
    assistant = relationship("AIAssistant", back_populates="business_profile") 