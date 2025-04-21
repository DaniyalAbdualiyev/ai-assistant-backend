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

class ClientAnalytics(Base):
    __tablename__ = "client_analytics"

    id = Column(Integer, primary_key=True, index=True)
    client_session_id = Column(String, nullable=False, index=True)
    assistant_id = Column(Integer, ForeignKey("assistants.id", ondelete="CASCADE"), nullable=False)
    business_profile_id = Column(Integer, ForeignKey("business_profiles.id", ondelete="CASCADE"), nullable=False)
    
    # Session metrics
    session_start = Column(DateTime, default=datetime.utcnow)
    session_end = Column(DateTime, nullable=True)
    message_count = Column(Integer, default=0)
    avg_response_time = Column(Float, nullable=True)  # in seconds
    
    # Client info (optional, for future use)
    client_ip = Column(String, nullable=True)
    client_device = Column(String, nullable=True)
    client_location = Column(String, nullable=True)
    
    # Relationships
    assistant = relationship("AIAssistant", back_populates="client_analytics")
    business_profile = relationship("BusinessProfile", back_populates="client_analytics")
