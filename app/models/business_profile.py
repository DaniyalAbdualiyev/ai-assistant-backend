from sqlalchemy import Column, Integer, String, JSON, ForeignKey, DateTime, Text, Boolean
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime

class BusinessProfile(Base):
    __tablename__ = "business_profiles"

    id = Column(Integer, primary_key=True, index=True)
    business_name = Column(String, nullable=False)
    business_type = Column(String, nullable=False)
    business_description = Column(Text, nullable=True)
    industry = Column(String, nullable=True)
    target_audience = Column(JSON, nullable=True)  # Store as JSON array
    products_services = Column(JSON, nullable=True)  # Store as JSON array
    tone_preferences = Column(JSON, nullable=False)  # Store tone settings
    language = Column(String, nullable=False, default="en")
    knowledge_base = Column(JSON, nullable=True)  # Store processed knowledge base
    files = Column(JSON, nullable=True)  # Store file metadata
    whatsapp_number = Column(String, nullable=True)
    whatsapp_verified = Column(Boolean, default=False)
    instagram_username = Column(String, nullable=True)
    instagram_verified = Column(Boolean, default=False)
    assistant_id = Column(Integer, ForeignKey("assistants.id", ondelete="CASCADE"), nullable=False)
    phone_number = Column(String, unique=True, index=True, nullable=False)
    verified = Column(Boolean, default=False, nullable=False)
    verified_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    assistant = relationship("AIAssistant", back_populates="business_profile")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user = relationship("User", back_populates="business_profile")
    verification_codes = relationship("VerificationCode", back_populates="business_profile")
    
    def __repr__(self):
        return f"<BusinessProfile(id={self.id}, name={self.business_name}, type={self.business_type})>" 