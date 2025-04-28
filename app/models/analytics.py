from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime

# Import these to avoid circular imports but don't use them directly
import app.models.assistant
import app.models.business_profile

class ConversationAnalytics(Base):
    __tablename__ = "conversation_analytics"

    id = Column(Integer, primary_key=True, index=True)
    assistant_id = Column(Integer, ForeignKey("assistants.id", ondelete="CASCADE"), nullable=False)
    business_profile_id = Column(Integer, ForeignKey("business_profiles.id", ondelete="CASCADE"), nullable=False)
    
    # Conversation metrics
    total_conversations = Column(Integer, default=0)
    total_messages = Column(Integer, default=0)
    avg_response_time = Column(Float, default=0.0)  # in seconds
    
    # Time metrics
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    date = Column(DateTime, default=datetime.utcnow)  # For daily analytics
    
    # Relationships
    assistant = relationship("AIAssistant", back_populates="analytics")
    business_profile = relationship("BusinessProfile", back_populates="analytics")
