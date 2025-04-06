from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, JSON
from app.database import Base
from datetime import datetime

class Integration(Base):
    __tablename__ = "integrations"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    platform = Column(String, nullable=False)  # e.g., "whatsapp", "instagram"
    credentials = Column(JSON)  # Store platform-specific credentials
    created_at = Column(DateTime, default=datetime.now)
    status = Column(String, default="active")

    def __repr__(self):
        return f"<Integration(id={self.id}, platform={self.platform}, user_id={self.user_id})>" 