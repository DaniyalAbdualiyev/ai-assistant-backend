from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime

class WhatsAppIntegration(Base):
    __tablename__ = "whatsapp_integrations"

    id = Column(Integer, primary_key=True, index=True)
    phone_number_id = Column(String, nullable=False, unique=True)
    display_phone_number = Column(String, nullable=False)
    business_profile_id = Column(Integer, ForeignKey("business_profiles.id", ondelete="CASCADE"), nullable=False)
    assistant_id = Column(Integer, ForeignKey("assistants.id", ondelete="CASCADE"), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    business_profile = relationship("BusinessProfile")
    assistant = relationship("AIAssistant")
