from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base
import datetime

class AIAssistant(Base):
    __tablename__ = "assistants"  # Changed from "ai_assistants" to "assistants"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    model = Column(String, nullable=False)
    language = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    user_id = Column(Integer, ForeignKey('users.id', ondelete="CASCADE"), nullable=False)

    # Relationships
    owner = relationship("User", back_populates="assistants")
    messages = relationship("Message", back_populates="assistant")