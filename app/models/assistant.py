from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base
import datetime
# Forward references for relationships
from sqlalchemy.ext.declarative import declared_attr

class AIAssistant(Base):
    __tablename__ = "assistants"  # Changed from "ai_assistants" to "assistants"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    model = Column(String, nullable=False)
    language = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    user_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"), nullable=False)

    # Relationships
    user = relationship("User", back_populates="assistants")
    messages = relationship("Message", back_populates="assistant")
    business_profile = relationship("BusinessProfile", back_populates="assistant", uselist=False)
    
    @declared_attr
    def analytics(cls):
        return relationship("ConversationAnalytics", back_populates="assistant")