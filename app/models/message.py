from sqlalchemy import Column, Integer, String, ForeignKey, DateTime , Float
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True)
    assistant_id = Column(Integer, ForeignKey("assistants.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    user_query = Column(String, nullable=False)
    ai_response = Column(String,nullable=True)
    timestamp = Column(DateTime, default=datetime.now)
    sentiment_score = Column(Float,nullable=True)

    assistant = relationship("AIAssistant", back_populates="messages")
    user = relationship("User", back_populates="messages")

    